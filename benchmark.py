#!/usr/bin/env -S python3 -B

import random
import argparse
import contextlib
import itertools
import math
import numpy as np
import json
import multiprocessing
import os
import subprocess
import sys
import statistics
import resource
import time

from sklearn import linear_model, datasets
from collections import defaultdict
from tqdm import tqdm

import macro
import micro

ROOT=os.path.dirname(os.path.realpath(__file__))
OPAMROOT=os.path.join(ROOT, '_opam')
RESULT=os.path.join(ROOT, '_result')
CPU_COUNT=multiprocessing.cpu_count()

SIZE_PATH = os.path.join(RESULT, 'size')
MACRO_PATH = os.path.join(RESULT, 'macro')
MICRO_PATH = os.path.join(RESULT, 'micro')
BUILD_TIME_PATH = os.path.join(RESULT, 'build')

# Enumeration of supported targets.
CPUS = {
  'x86_64': ['zen2', 'skylake', 'tremont'],
  'arm64': ['cortex-a72'],
  'riscv64': ['sifive-u74'],
  'ppc64': ['pwr8', 'pwr9']
}

# Switches with root packages.
SWITCHES = {}
for arch, cpus in CPUS.items():
  SWITCHES[f'{arch}+ref'] = [f'ocaml-variants-{arch}.4.11.1.master']
  SWITCHES[f'{arch}+llir'] = [f'ocaml-variants-{arch}.4.11.1.master+llir']
  for opt in ['O0', 'O1', 'O2', 'O3', 'O4']:
    SWITCHES[f'{arch}+llir+{opt}'] = [
        f'ocaml-variants-{arch}.4.11.1.master+llir',
        f'llir-config.{opt}'
    ]
    for cpu in cpus:
      SWITCHES[f'{arch}+llir+{opt}+{cpu}'] = [
          f'ocaml-variants-{arch}.4.11.1.master+llir',
          f'llir-config.{opt}+{cpu}'
      ]

# List of all packages to install.
PACKAGES=[
  "coq", "menhir", "compcert", "ocamlgraph", "cpdf", "minilight", "yojson",
  "base", "stdio", "dune", "camlzip", "zarith", "ocplib-simplex", "diy",
  "ocamlmod", "sexplib0", "odoc", "hevea", "cmitomli", "alcotest", "biniou",
  "bigstringaf", "result", "angstrom", "hxd", "cppo", "csexp", "easy-format",
  "gmp", "ocaml-syntax-shims", "ounit2", "ppxlib", "re", "zlib", "jsonm",
  "uuidm", "ocplib-endian", "lwt", "fix", "why3", "tyxml", "nbcodec", "react",
  "rml", "uucp", "atdgen", "atdj", "atds", "camlp5", "ppxfind", "ucaml",
  "ocamlformat", "js_of_ocaml", "ppx_deriving", "ppx_tools", "frama-c",
  "alt-ergo-free", "camlp4", "num", "fraplib", "cubicle", "uri", "irmin",
  "irmin-mem", "irmin-test", "stringext", "bos", "base64", "digestif",
  "eqaf", "crowbar", "metrics-unix", "reason", "reanalyze"
]

# Path to the default repository.
REPOSITORY='git+https://github.com/nandor/llir-opam-repository'

def opam(args, capture=False, silent=False, cwd=None, **kwargs):
  """Run the opam process and capture its output."""

  env = os.environ.copy()
  env['OPAMROOT'] = OPAMROOT
  if capture:
    proc = subprocess.Popen(
        ['opam'] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print('"opam {}" failed:\n'.format(' '.join(args)))
        print(stderr.decode('utf-8'))
        sys.exit(1)

    return stdout.decode('utf-8')
  else:
    proc = subprocess.Popen(
        ['opam'] + list(args),
        stdout=subprocess.DEVNULL if silent else None,
        stderr=subprocess.DEVNULL if silent else None,
        env=env,
        cwd=cwd
    )
    child_pid, status, rusage = os.wait4(proc.pid, 0)
    if status != 0:
      print('"opam {}" failed:\n'.format(' '.join(args)))
      sys.exit(proc.returncode)
    return rusage.ru_utime


def dune(jb, switch, target):
  opam([
      'exec',
      '--switch={}'.format(switch),
      '--',
      'dune',
      'build',
      '-j', str(jb),
      '--profile=release',
      '--workspace=dune-workspace',
      target
  ])


def run_command(*args, **kwargs):
  """Runs a command."""

  proc = subprocess.Popen(
      list(args),
      stdout=subprocess.DEVNULL,
      stderr=subprocess.PIPE,
      **kwargs
  )

  _, stderr = proc.communicate()
  if proc.returncode != 0:
      print('"opam {}" failed:\n'.format(' '.join(args)))
      print(stderr.decode('utf-8'))
      sys.exit(1)


def install(switches, repository, jb):
  """Installs the switches and the required packages."""

  # Set up the workspace file.
  with open(os.path.join(ROOT, 'dune-workspace'), 'w') as f:
    f.write('(lang dune 2.0)\n')
    for switch in switches:
      f.write('(context (opam (switch {0}) (name {0})))\n'.format(switch))

  # Set up opam and the custom repository.
  opam([
      'init',
      '--bare',
      '--no-setup',
      '--no-opamrc',
      '--disable-sandboxing',
      repository
  ])
  opam(['update'])

  # Create all the switches.
  for switch in switches:
    if switch not in opam(['switch', 'list'], capture=True):
      opam([
          'switch',
          'create',
          '--yes',
          '-j', str(jb),
          switch,
          '--empty',
      ])

  # Install the compilers.
  for switch in switches:
    opam([
        'install',
        '--switch={}'.format(switch),
        '--with-test',
        '--yes'
    ] + SWITCHES[switch])

  # Install all packages.
  for switch in switches:
    opam(
        [
          'install',
          '--switch={}'.format(switch),
          '--yes',
          '-j', str(jb),
          '--with-test'
        ] + PACKAGES,
        prefix=os.path.join(OPAMROOT, switch)
    )

  # Build all benchmarks.
  switch = switches[0]
  dune(jb, switch, '@build_macro')
  dune(jb, switch, '@build_micro')
  dune(jb, switch, '@build_compcert')
  dune(jb, switch, '@build_frama_c')


def benchmark_size(switches):
  """Finds the code size of all applications in all switches."""

  if os.path.exists(SIZE_PATH):
    return

  files = set()
  for switch in switches:
    bin_dir = os.path.join(OPAMROOT, switch, 'bin')
    if os.path.isdir(bin_dir):
      for name in os.listdir(bin_dir):
        bin_path = os.path.join(bin_dir, name)
        if not os.access(bin_path, os.X_OK):
          continue
        if os.path.islink(bin_path):
          continue
        with open(bin_path, 'rb') as f:
          if f.read(4)[1:].decode('ascii') != 'ELF':
            continue
        files.add(name)

  sizes = defaultdict(dict)
  for name in files:
    for switch in switches:
      bin_path = os.path.join(OPAMROOT, switch, 'bin', name)
      proc = subprocess.Popen(
          ['readelf', '-S', bin_path],
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE
      )
      stdout, _ = proc.communicate()
      if proc.returncode != 0:
        continue
      lines = stdout.decode('ascii').split('\n')[5:-6]
      for lh, lv in zip(lines, lines[1:]):
        if '.text' not in lh: continue
        sizes[name][switch] = int(lv.strip().split(' ')[0], 16)

  with open(SIZE_PATH, 'w') as f:
    f.write(json.dumps(sizes, sort_keys=True, indent=2))


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
  try:
    bench, switch, args = test
    exe = os.path.join(ROOT, bench.exe.format(switch))
    bin_dir = os.path.join(ROOT, '_opam', switch, 'bin')
    lib_dir = os.path.join(ROOT, '_opam', switch, 'lib')

    cwd = os.path.join(ROOT, '_build', switch, 'macro', bench.group)
    if not os.path.exists(cwd):
      os.makedirs(cwd)

    env={}
    for line in opam(['env', '--switch', switch], capture=True).split('\n'):
      if not line.strip(): continue
      k, v = line.split(';')[0].strip().split('=')
      env[k] = v[1:-1]

    task = subprocess.Popen([
          'taskset',
          '--cpu-list',
          str(cpu),
          exe
        ] + [arg.format(bin=bin_dir, lib=lib_dir) for arg in args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )
    child_pid, status, rusage = os.wait4(task.pid, 0)

    if status == 0:
      result = (rusage.ru_utime, rusage.ru_maxrss)
  except:
    pass

  return bench, switch, args, result


def benchmark_macro(benchmarks, switches, n, jt):
  """Runs performance benchmarks."""

  all_tests = []
  for _, bench, switch in itertools.product(range(n), benchmarks, switches):
    for args in bench.args:
      all_tests.append((bench, switch, args))
  random.shuffle(all_tests)

  pool = multiprocessing.Pool(jt)
  perf = defaultdict(lambda: defaultdict(list))
  failed = []
  for bench, switch, args, r in tqdm(pool.imap_unordered(_run_macro_test, all_tests), total=len(all_tests)):
    if not r:
      failed.append((bench.exe.format(switch), ' '.join(args)))
      continue
    perf["{}.{}".format(bench.name, '_'.join(args))][switch].append(r)
  pool.close()
  pool.join()

  for name, args in failed:
    print('Failed to run {} {}'.format(name, args))

  with open(MACRO_PATH, 'w') as f:
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
  x = np.array([x for x, _ in samples])
  y = np.array([y for _, y in samples])

  ransac = linear_model.RANSACRegressor(residual_threshold=10000)
  ransac.fit(x.reshape(-1, 1), y.reshape(-1, 1))
  return ransac.estimator_.coef_[0][0]


def benchmark_micro(switches):
  """Runs microbenchmarks."""

  perf = defaultdict(dict)
  all_tests = list(itertools.product(micro.BENCHMARKS, switches))
  for bench, switch in tqdm(all_tests):
    micro_dir = os.path.join(RESULT, 'log')
    bench_log = os.path.join(micro_dir, '{}.{}'.format(bench.name, switch))
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

  with open(MICRO_PATH, 'w') as f:
    f.write(json.dumps(perf, sort_keys=True, indent=2))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='GenM OCaml benchmark suite')
  parser.add_argument(
      '-n',
      type=int,
      default=1,
      action='store',
      help='number of repetitions for macro tests'
  )
  parser.add_argument(
      '-jb',
      type=int,
      default=max(1, CPU_COUNT - 1),
      action='store',
      help='number of threads to build with'
  )
  parser.add_argument(
      '-jt',
      type=int,
      default=1,
      action='store',
      help='number of threads to test with'
  )
  parser.add_argument(
      '-macro',
      type=str,
      action='store',
      default=None,
      choices=[n for n in dir(macro) if not n.startswith('__') and n != 'Macro'],
      help='benchmark to run'
  )
  parser.add_argument(
      '-repository',
      type=str,
      action='store',
      default=REPOSITORY,
      help='path to the LLIR opam repository'
  )
  parser.add_argument(
      '-switches',
      type=str,
      default='ref,llir+O0',
      help='comma-separated list of switches to run (ref, llir, llir+On)'
  )
  parser.add_argument('-time-build', default=False, action='store_true')
  parser.add_argument('-micro', default=False, action='store_true')
  args = parser.parse_args()

  # Raise stack limit to 128Mb.
  stack_size = 128 * 1024 * 1024
  resource.setrlimit(resource.RLIMIT_STACK, (stack_size, stack_size))

  # Create output dir, if it does not exist.
  if not os.path.exists(RESULT):
    os.makedirs(RESULT)

  # Build and run.
  switches = args.switches.split(',')
  install(switches, args.repository, args.jb)
  benchmark_size(switches)
  if args.macro:
    benchmark_macro(getattr(macro, args.macro), switches, args.n, args.jt)
  if args.micro:
    benchmark_micro(switches)
