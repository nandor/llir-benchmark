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

from sklearn import linear_model, datasets
from collections import defaultdict
from tqdm import tqdm

import macro
import micro

ROOT=os.path.dirname(os.path.realpath(__file__))
OPAMROOT=os.path.join(ROOT, '_opam')
RESULT=os.path.join(ROOT, '_result')
CPU_COUNT=multiprocessing.cpu_count()

# List of all packages to install.
PACKAGES=[
  "dune", "js_of_ocaml", "diy", "hevea", "cmitomli", "hxd", "rml", "odoc",
  "ucaml", "ppxfind", "ocamlmod", "camlp4", "menhir", "minilight", "yojson",
  "lwt", "uuidm", "react", "ocplib-endian", "sexplib0", "ctypes", "zarith",
  "jsonm", "cpdf", "nbcodec", "tyxml"
]

# List of all switches to evaluate.
SWITCHES=[
  #("4.07.1+static", (['-cc', 'musl-clang'], 'musl-clang', 'ar')),
  ("4.07.1+llir+O0", (['--target', 'llir', '-O0'], 'llir-gcc', 'llir-ar')),
  ("4.07.1+llir+O1", (['--target', 'llir', '-O1'], 'llir-gcc', 'llir-ar')),
  ("4.07.1+llir+O2", (['--target', 'llir', '-O2'], 'llir-gcc', 'llir-ar')),
  #("4.07.1+llir+O3", (['--target', 'llir', '-O3'], 'llir-gcc', 'llir-ar')),
  #("4.07.1+static+lto", (['-cc', 'musl-clang', '-lto'], 'musl-clang', 'ar')),
  ("4.07.1+llir+O0+lto", (['--target', 'llir', '-O0', '-lto'], 'llir-gcc', 'llir-ar')),
  ("4.07.1+llir+O1+lto", (['--target', 'llir', '-O1', '-lto'], 'llir-gcc', 'llir-ar')),
  ("4.07.1+llir+O2+lto", (['--target', 'llir', '-O2', '-lto'], 'llir-gcc', 'llir-ar')),
  #("4.07.1+llir+O3+lto", (['--target', 'llir', '-O3', '-lto'], 'llir-gcc', 'llir-ar')),
]

# opam file to generate for the compiler versions.
OPAM="""opam-version: "2.0"
version: "4.07.1+llir"
synopsis: "4.07.1 with the LLIR backend"
maintainer: "n@ndor.email"
authors: "n@ndor.email"
homepage: "https://github.com/nandor/llir-ocaml"
bug-reports: "https://github.com/nandor/llir-ocaml/issues"
dev-repo: "git+file://{0}/ocaml#master"
depends: [
  "ocaml" {{ = "4.07.1" & post }}
  "base-unix" {{post}}
  "base-bigarray" {{post}}
  "base-threads" {{post}}
]
conflict-class: "ocaml-core-compiler"
flags: compiler
build: [
  [
    "./configure"
      "--prefix" prefix
      "-no-debugger" "-no-instrumented-runtime" "-no-cfi"
      "-no-debug-runtime" "-no-graph" "-fPIC" "-flambda"
      "-no-shared-libs"
      {1}
  ]
  [ make "world" "-j%{{jobs}}%"]
  [ make "world.opt" "-j%{{jobs}}%"]
]
install: [make "install"]
url {{
  src: "git+file://{0}/ocaml#master"
}}
"""


def opam(*args, **kwargs):
  """Run the opam process and capture its output."""

  env = os.environ.copy()
  env['OPAMROOT'] = OPAMROOT
  env['PATH'] = '{prefix}/dist/bin:{prefix}/dist/musl/bin:{path}'.format(
      prefix=os.getenv('PREFIX'),
      path=os.getenv('PATH')
  )
  if 'cc' in kwargs:
    env['CC'] = kwargs['cc']
  if 'ar' in kwargs:
    env['AR'] = kwargs['ar']
  if 'prefix' in kwargs:
    env['CFLAGS'] = '{cflags} -I{prefix}/include'.format(
      cflags=env.get('CFLAGS', ''),
      prefix=kwargs['prefix']
    )
    env['LDFLAGS'] = '{ldflags} -L{prefix}/lib'.format(
      ldflags=env.get('LDFLAGS', ''),
      prefix=kwargs['prefix']
    )

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


def dune(jb, target):
  opam(
      'exec',
      '--',
      'dune',
      'build',
      '-j', str(jb),
      '--profile=release',
      '--workspace=dune-workspace',
      target
  )


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


def install(switches, jb):
  """Installs the switches and the required packages."""

  # Set up the workspace file.
  with open(os.path.join(ROOT, 'dune-workspace'), 'w') as f:
    f.write('(lang dune 2.0)\n')
    for switch, _ in switches:
      f.write('(context (opam (switch {0}) (name {0})))\n'.format(switch))

  # Set up the opam files for the switches.
  pkg_dir = os.path.join(ROOT, 'dependencies', 'packages', 'ocaml-base-compiler')
  for switch, (args, _, _) in switches:
    ver_dir = os.path.join(pkg_dir, 'ocaml-base-compiler.{}'.format(switch))
    if not os.path.exists(ver_dir):
      os.makedirs(ver_dir)
    with open(os.path.join(ver_dir, 'opam'), 'w') as f:
      f.write(OPAM.format(os.getenv('PREFIX'), ' '.join('"{}"'.format(a) for a in args)))

  # Set up opam and the custom repository.
  opam(
      'init',
      '--bare',
      '--no-setup',
      '--no-opamrc',
      '--disable-sandboxing',
      os.path.join(ROOT, 'dependencies')
  )
  opam('update')

  # Install all compilers.
  for switch, _ in switches:
    if switch not in opam('switch', 'list'):
      opam(
          'switch',
          'create',
          '--keep-build-dir',
          '--yes',
          '-j', str(jb),
          switch,
          'ocaml-base-compiler.{}'.format(switch)
      )

  # Install all packages.
  for switch, (_, cc, ar) in switches:
    opam(
        'install',
        '--switch={}'.format(switch),
        '--keep-build-dir',
        '--yes',
        '-j', str(jb),
        *PACKAGES,
        cc=cc,
        ar=ar,
        prefix=os.path.join(OPAMROOT, switch)
    )

  # Build all benchmarks.
  dune(jb, '@build_macro')
  dune(jb, '@build_micro')


def benchmark_size(switches):
  """Finds the code size of all applications in all switches."""
  files = set()
  for switch, _ in switches:
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
    for switch, _ in switches:
      bin_path = os.path.join(OPAMROOT, switch, 'bin', name)
      proc = subprocess.Popen(['size', bin_path], stdout=subprocess.PIPE)
      stdout, _ = proc.communicate()
      if proc.returncode != 0:
        continue
      text, data = [int(t) for t in str(stdout.decode('ascii')).split('\n')[1].split('\t')[:2]]
      sizes[name][switch] = text

  if not os.path.exists(RESULT):
    os.makedirs(RESULT)
  with open(os.path.join(RESULT, 'size'), 'w') as f:
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

    cwd = os.path.join(ROOT, '_build', switch, 'macro', bench.group)
    if not os.path.exists(cwd):
      os.makedirs(cwd)

    task = subprocess.Popen([
          'taskset',
          '--cpu-list',
          str(cpu),
          exe
        ] + [arg.format(bin=bin_dir) for arg in args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    child_pid, status, rusage = os.wait4(task.pid, 0)

    if status == 0:
      result = (rusage.ru_utime, rusage.ru_maxrss)
  except:
    pass

  return bench, switch, args, result


def benchmark_macro(switches, n, jt):
  """Runs performance benchmarks."""

  all_tests = []
  for _, bench, (switch, _) in itertools.product(range(n), macro.BENCHMARKS, switches):
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

  if not os.path.exists(RESULT):
    os.makedirs(RESULT)
  with open(os.path.join(RESULT, 'macro'), 'w') as f:
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
  for bench, (switch, _) in tqdm(all_tests):

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

  if not os.path.exists(RESULT):
    os.makedirs(RESULT)
  with open(os.path.join(RESULT, 'micro'), 'w') as f:
    f.write(json.dumps(perf, sort_keys=True, indent=2))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='GenM OCaml benchmark suite')
  parser.add_argument('-n', type=int, default=5, action='store')
  parser.add_argument('-jb', type=int, default=CPU_COUNT - 1, action='store')
  parser.add_argument('-jt', type=int, default=CPU_COUNT - 1, action='store')
  parser.add_argument('-nr', type=int, default=1, action='store')
  args = parser.parse_args()

  # Raise stack limit to 128Mb.
  stack_size = 128 * 1024 * 1024
  resource.setrlimit(resource.RLIMIT_STACK, (stack_size, stack_size))

  # Prepare switch names.
  switches = []
  for name, flags in SWITCHES:
    for i in range(0, args.nr):
      switches.append(('{}-{}'.format(name, i), flags))

  # Build and run.
  install(switches, args.jb)
  benchmark_size(switches)
  benchmark_macro(switches, args.n, args.jt)
  benchmark_micro(switches)
