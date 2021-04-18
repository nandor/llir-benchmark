# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import os
import subprocess
import itertools
import random
import multiprocessing
import json

import tqdm
import build

from collections import defaultdict



CPU_COUNT=multiprocessing.cpu_count()



class Chdir(object):
  """Helper to temporarily change the working dir."""

  def __init__(self, new_path):
    self.saved_path = os.getcwd()
    self.new_path = new_path

  def __enter__(self):
    os.chdir(self.new_path)

  def __exit__(self, type, value, traceback):
    os.chdir(self.saved_path)



def _run_macro_test(test):
  """Helper to run a single test."""

  cpu = multiprocessing.current_process()._identity[0] % CPU_COUNT

  result = None
  error = None
  try:
    bench, switch, args, root = test
    exe = os.path.join(root, bench.exe.format(switch))
    bin_dir = os.path.join(root, '_opam', switch, 'bin')
    lib_dir = os.path.join(root, '_opam', switch, 'lib')

    cwd = os.path.join(root, '_build', switch, 'macro', bench.group)
    if not os.path.exists(cwd):
      os.makedirs(cwd)

    env={}
    for line in build.opam(['env', '--switch', switch], capture=True).split('\n'):
      if not line.strip(): continue
      k, v = line.split(';')[0].strip().split('=')
      env[k] = v[1:-1]

    exe_args = []
    if isinstance(args, dict):
      for k, v in args.items():
        env[k] = v
    else:
        exe_args = [arg.format(bin=bin_dir, lib=lib_dir) for arg in args]
    
    task = subprocess.Popen([
          'taskset',
          '--cpu-list',
          str(cpu),
          exe
        ] + exe_args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )
    child_pid, status, rusage = os.wait4(task.pid, 0)
    if status == 0:
      result = (rusage.ru_utime, rusage.ru_maxrss)
  except Exception as e:
    error = repr(e)

  return bench, switch, args, result, error


def benchmark_macro(benchmarks, switches, n, jt, root, output):
  """Runs performance benchmarks."""

  all_tests = []
  for _, bench, switch in itertools.product(range(n), benchmarks, switches):
    for test in bench.tests:
      for args in test.args:
        all_tests.append((test, switch, args, root))
  random.shuffle(all_tests)

  pool = multiprocessing.Pool(jt)
  perf = defaultdict(lambda: defaultdict(list))
  failed = []
  tests = pool.imap_unordered(_run_macro_test, all_tests)
  for bench, switch, args, r, e in tqdm.tqdm(tests, total=len(all_tests)):
    if e:
      failed.append((bench.exe.format(switch), ' '.join(args), e))
      continue
    if isinstance(args, dict):
      name = '_'.join(v for k, v in args.items())
    else:
      name = '_'.join(args)
    perf["{}.{}".format(bench.name, name)][switch].append(r)
  pool.close()
  pool.join()

  for name, args, reason in failed:
    print(f'Failed to run {name} {args}:\n {reason}')

  parent = os.path.abspath(os.path.join(output, os.pardir))
  if not os.path.exists(parent):
    os.makedirs(parent)
  with open(output, 'w') as f:
    f.write(json.dumps(perf, sort_keys=True, indent=2))


def _run_micro_test(exe):
  """Runs a micro benchmark and captures its output."""

  p = subprocess.Popen(
      [exe, "--longer", "--stabilize-gc", '--time-quota', '60'],
      stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL
  )
  out, _ = p.communicate()
  if p.returncode != 0:
    print("Failed to run {}".format(exe))
    return ""
  return out.decode("utf-8")


def _fit(samples):
  import numpy
  from sklearn.linear_model import RANSACRegressor

  x = numpy.array([x for x, _ in samples])
  y = numpy.array([y for _, y in samples])

  ransac = RANSACRegressor(residual_threshold=10000)
  ransac.fit(x.reshape(-1, 1), y.reshape(-1, 1))
  return ransac.estimator_.coef_[0][0]


def benchmark_micro(benchmarks, switches, output):
  """Runs microbenchmarks."""

  perf = defaultdict(dict)
  all_tests = list(itertools.product(benchmarks, switches))
  for bench, switch in tqdm.tqdm(all_tests):
    for test in bench.tests:
      micro_dir = os.path.abspath(os.path.join(output, os.pardir, 'log'))
      bench_log = os.path.join(micro_dir, '{}.{}'.format(test.name, switch))
      if not os.path.exists(micro_dir):
        os.makedirs(micro_dir)

    result = _run_micro_test(bench.exe.format(switch))
    with open(bench_log, 'w') as f:
      f.write(result)

    lines = [l.strip() for l in result.split('\n') if l.strip()]

    data = defaultdict(list)
    test = None
    for line in lines:
      if 'name' in line:
        test = line.split(':')[1].strip().replace(' ', '_')
        continue
      runs, _, nanos, _, _, _, _, _, _ = line.split(' ')
      data[test].append((float(runs), float(nanos)))
    for test, ratios in data.items():
      bench_name = '{}.{}'.format(bench.name, test)
      perf[bench_name][switch] = _fit(list(ratios))

  parent = os.path.abspath(os.path.join(output, os.pardir))
  if not os.path.exists(parent):
    os.makedirs(parent)
  with open(output, 'w') as f:
    f.write(json.dumps(perf, sort_keys=True, indent=2))
