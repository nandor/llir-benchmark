#!/usr/bin/env python3

import collections
import os
import subprocess
import sys
import json



# List of all packages to install.
PACKAGES=[
  "dune", "js_of_ocaml", "diy", "hevea", "cmitomli", "hxd", "rml", "odoc", 
  "ucaml", "ppxfind", "ocamlmod", "camlp4", "menhir", "minilight", "yojson", 
  "lwt", "uuidm", "react", "ocplib-endian", "sexplib0", "ctypes",
]

# List of all switches to evaluate.
SWITCHES=[
  ("4.07.1+static", []),
  ("4.07.1+genm+O0", ['--target', 'genm', '-O0']),
  ("4.07.1+genm+O1", ['--target', 'genm', '-O1']),
  ("4.07.1+genm+O2", ['--target', 'genm', '-O2']),
  ("4.07.1+genm+O3", ['--target', 'genm', '-O3'])
]

# opam file to generate for the compiler versions.
OPAM="""opam-version: "2.0"
version: "4.07.1+genm"
synopsis: "4.07.01 with the genm backend"
maintainer: "n@ndor.email"
authors: "n@ndor.email"
homepage: "https://github.com/nandor/ocaml-genm"
bug-reports: "https://github.com/nandor/ocaml-genm/issues"
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

ROOT=os.path.dirname(os.path.realpath(__file__))
OPAMROOT=os.path.join(ROOT, '_opam')
BUILD=os.path.join(ROOT, '_build')
RESULT=os.path.join(ROOT, '_result')

def opam(*args):
  """Run the opam process and capture its output."""

  env = os.environ.copy()
  env['OPAMROOT'] = OPAMROOT
  env['OCAMLRUNPARAM'] = 's=2000000'

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
    

def install():
  """Installs the switches and the required packages."""

  # Set up the workspace file.
  with open(os.path.join(ROOT, 'dune-workspace'), 'w') as f:
    f.write('(lang dune 2.0)\n')
    for switch, _ in SWITCHES:
      f.write('(context (opam (switch {0}) (name {0})))\n'.format(switch))
  
  # Set up the opam files for the switches.
  pkg_dir = os.path.join(ROOT, 'dependencies', 'packages', 'ocaml-base-compiler')
  for switch, args in SWITCHES:
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
  for switch, _ in SWITCHES:
    if switch not in opam('switch', 'list'):
      opam(
          'switch', 
          'create', 
          '--yes', 
          switch, 
          'ocaml-base-compiler.{}'.format(switch)
      )

  # Install all packages.
  for switch, _ in SWITCHES:
    opam('install', '--switch={}'.format(switch), '--yes', *PACKAGES)

  # Build all benchmarks.
  opam(
      'exec', 
      '--', 
      'dune', 
      'build', 
      '--profile=release', 
      '--workspace=dune-workspace', 
      '@buildbench'
  )


def benchmark_size():
  """Finds the code size of all applications in all switches."""
  files = set()
  for switch, _ in SWITCHES:
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

  sizes = collections.defaultdict(dict)
  for name in files:
    for switch, _ in SWITCHES:
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


class Benchmark(object):
  """Class to describe and run a benchmark."""

  def __init__(self, name, exe=None, args=[]):
    """Configures a benchmark."""
    self.name = name
    self.exe = exe if exe else 'benchmarks/{0}/{0}.exe'.format(name)
    self.args = args

  def run(self, switch):
    """Runs a benchmark."""
    
    exe = os.path.join(BUILD, switch, self.exe)
    pid = os.spawnvp(os.P_NOWAIT, exe, [exe] + self.args)
    child_pid, status, rusage = os.wait4(pid, 0)
    assert status == 0
    print(self.name, switch, rusage.ru_utime, rusage.ru_maxrss)


BENCHMARKS=[
  Benchmark(
    name='bdd', 
    args=['26']
  ),
  Benchmark(
    name='durand_kerner_aberth',
    exe='benchmarks/numerical-analysis/durand_kerner_aberth.exe',
    args=['100']
  ),
  Benchmark(
    name='fft',
    exe='benchmarks/numerical-analysis/fft.exe',
    args=['1_048_576']
  ),
  Benchmark(
    name='levinson_durbin',
    exe='benchmarks/numerical-analysis/levinson_durbin.exe',
    args=['10_000']
  ),
  Benchmark(
    name='lu_decomposition',
    exe='benchmarks/numerical-analysis/lu_decomposition.exe',
  ),
  Benchmark(
    name='naive_multilayer',
    exe='benchmarks/numerical-analysis/naive_multilayer.exe',
  ),
  Benchmark(
    name='qr_decomposition',
    exe='benchmarks/numerical-analysis/qr_decomposition.exe',
  ),
  Benchmark(
    name='alloc', 
    exe='benchmarks/simple-tests/alloc.exe', 
    args=['400_000']
  ),
  Benchmark(
    name='morestacks',
    exe='benchmarks/simple-tests/morestacks.exe',
    args=['1_000']
  ),
]

def benchmark_perf():
  """Runs performance benchmarks."""

  for benchmark in BENCHMARKS:
    for switch, _ in SWITCHES:
      benchmark.run(switch)


if __name__ == '__main__':
  install()
  benchmark_size()
  benchmark_perf()
