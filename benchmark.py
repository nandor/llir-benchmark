#!/usr/bin/env python3

import contextlib
import itertools
import json
import multiprocessing
import os
import random
import subprocess
import sys

from collections import defaultdict
from tqdm import tqdm



# List of all packages to install.
PACKAGES=[
  "dune", "js_of_ocaml", "diy", "hevea", "cmitomli", "hxd", "rml", "odoc",
  "ucaml", "ppxfind", "ocamlmod", "camlp4", "menhir", "minilight", "yojson",
  "lwt", "uuidm", "react", "ocplib-endian", "sexplib0", "ctypes",
]

# List of all switches to evaluate.
SWITCHES=[
  ("4.07.1+static", []),
  #("4.07.1+genm+O0", ['--target', 'genm', '-O0']),
  #("4.07.1+genm+O1", ['--target', 'genm', '-O1']),
  #("4.07.1+genm+O2", ['--target', 'genm', '-O2']),
  #("4.07.1+genm+O3", ['--target', 'genm', '-O3']),
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

  sizes = defaultdict(dict)
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


class Chdir(object):
  """Helper to temporarily change the working dir."""

  def __init__(self, new_path):
    self.saved_path = os.getcwd()
    self.new_path = new_path

  def __enter__(self):
    os.chdir(self.new_path)

  def __exit__(self, type, value, traceback):
    os.chdir(self.saved_path)


class Macro(object):
  """Class to describe and run a benchmark."""

  def __init__(self, group, name, exe=None, args=[[]]):
    """Configures a benchmark."""

    self.group = group
    self.name = name
    if exe:
      self.exe = '_opam/{{0}}/bin/{0}'.format(exe)
    else:
      self.exe = '_build/{{0}}/macro/{0}/{1}.exe'.format(group, name)
    self.args = args


ALMABENCH = [
  Macro(group='almabench', name='almabench', args=[['10']]),
]

BDD = [
  Macro(group='bdd', name='bdd', args=[['26']]),
]

BENCHMARKSGAME = [
  Macro(group='benchmarksgame', name='binarytrees5', args=[['20']]),
  Macro(group='benchmarksgame', name='fannkuchredux2', args=[['11']]),
  Macro(group='benchmarksgame', name='fannkuchredux', args=[['11']]),
  Macro(group='benchmarksgame', name='fasta3'),
  Macro(group='benchmarksgame', name='fasta6'),
  Macro(group='benchmarksgame', name='knucleotide'),
  Macro(group='benchmarksgame', name='mandelbrot6', args=[['4000']]),
  Macro(group='benchmarksgame', name='nbody', args=[['100000000']]),
  ##Macro(group='benchmarksgame', name='pidigits5'),
  Macro(group='benchmarksgame', name='regexredux2'),
  Macro(group='benchmarksgame', name='revcomp2'),
  Macro(group='benchmarksgame', name='spectralnorm2'),
]

CHAMENEOS = [
  Macro(group='chameneos', name='chameneos_redux_lwt', args=[['600000']]),
]

KB = [
  Macro(group='kb', name='kb', args=[[]]),
  Macro(group='kb', name='kb_no_exc', args=[[]]),
]

NUMERICAL_ANALYSIS = [
  Macro(group='numerical-analysis', name='durand_kerner_aberth', args=[
    ['100']
  ]),
  Macro(group='numerical-analysis', name='fft', args=[
    ['1_048_576']
  ]),
  Macro(group='numerical-analysis', name='levinson_durbin', args=[
    ['10_000']
  ]),
  Macro(group='numerical-analysis', name='lu_decomposition', args=[
    []
  ]),
  Macro(group='numerical-analysis', name='naive_multilayer', args=[
    []
  ]),
  Macro(group='numerical-analysis', name='qr_decomposition', args=[
    []
  ]),
]

MENHIR = [
  Macro(
      group='menhir',
      name='menhir',
      exe='menhir',
      args=[
        ['-v', '--table', 'sysver.mly']
      ]
  )
]

SIMPLE_TESTS = [
  Macro(group='simple-tests', name='alloc', args=[
    ['400_000']
  ]),
  Macro(group='simple-tests', name='morestacks', args=[
    ['1_000']
  ]),
  Macro(group='simple-tests', name='stress', args=[
    ["1", "10"],
    ["10000", "10"],
    ["100000", "10"],
    ["1", "25"],
    ["10000", "25"],
    ["100000", "25"],
    ["1", "50"],
    ["10000", "50"],
    ["100000", "50"],
    ["1", "75"],
    ["10000", "75"],
    ["100000", "75"],
    ["1", "100"],
    ["10000", "100"],
    ["100000", "100"],
  ]),
  Macro(group='simple-tests', name='capi', args=[
    ["test_no_args_alloc", "200_000_000"],
    ["test_no_args_noalloc", "200_000_000"],
    ["test_few_args_alloc", "200_000_000"],
    ["test_few_args_noalloc", "200_000_000"],
    ["test_many_args_alloc", "200_000_000"],
    ["test_many_args_noalloc", "200_000_000"],
  ]),
  Macro(group='simple-tests', name='stacks', args=[
    ["100000", "ints-small"],
    ["20000", "ints-large"],
    ["100000", "floats-small"],
    ["20000", "floats-large"],
  ]),
  Macro(group='simple-tests', name='weakretain', args=[
    ["25", "1000"],
    ["25", "100000"],
    ["25", "10000000"],
    ["50", "1000"],
    ["50", "100000"],
    ["50", "10000000"],
    ["75", "1000"],
    ["75", "100000"],
    ["75", "10000000"],
    ["100", "1000"],
    ["100", "100000"],
    ["100", "10000000"],
  ]),
  Macro(group='simple-tests', name='lazylist', args=[
    ["100000", "100"],
    ["10000", "1000"],
    ["1000", "10000"],
  ]),
  Macro(group='simple-tests', name='lists', args=[
    ["int", "1"],
    ["int", "10000"],
    ["int", "100000"],
    ["float", "1"],
    ["float", "10000"],
    ["float", "100000"],
    ["int-tuple", "1"],
    ["int-tuple", "10000"],
    ["int-tuple", "100000"],
    ["float-tuple", "1"],
    ["float-tuple", "10000"],
    ["float-tuple", "100000"],
    ["string", "1"],
    ["string", "10000"],
    ["string", "100000"],
    ["record", "1"],
    ["record", "10000"],
    ["record", "100000"],
    ["float-array", "1"],
    ["float-array", "10000"],
    ["float-array", "100000"],
    ["int-array", "1"],
    ["int-array", "10000"],
    ["int-array", "100000"],
    ["int-option-array", "1"],
    ["int-option-array", "10000"],
    ["int-option-array", "100000"],
  ]),
  Macro(group='simple-tests', name='finalise', args=[
    ["10"],
    ["20"],
    ["30"],
    ["40"],
    ["50"],
    ["60"],
    ["70"],
    ["80"],
    ["90"],
    ["100"],
  ]),
]

STDLIB = [
  Macro(group='stdlib', name='stack_bench', args=[
    ["stack_fold", "2500000"],
    ["stack_push_pop", "100000000"],
  ]),
  Macro(group='stdlib', name='array_bench', args=[
    ["array_forall", "1000", "100000"],
    ["array_fold", "1000", "100000"],
    ["array_iter", "1000", "100000"],
  ]),

  Macro(group='stdlib', name='bytes_bench', args=[
    ["bytes_get", "100000000"],
    ["bytes_sub", "100000000"],
    ["bytes_blit", "2500000"],
    ["bytes_concat", "2000000"],
    ["bytes_iter", "1000000"],
    ["bytes_map", "1000000"],
    ["bytes_trim", "2500000"],
    ["bytes_index", "10000000"],
    ["bytes_contains", "100000000"],
    ["bytes_uppercase_ascii", "1000000"],
    ["bytes_set", "1000000000"],
    ["bytes_cat", "1000000000"],
  ]),
  Macro(group='stdlib', name='set_bench', args=[
    #["set_fold", "1000000"],
    ["set_add_rem", "20000000"],
    ["set_mem", "50000000"],
  ]),
  Macro(group='stdlib', name='hashtbl_bench', args=[
    ["int_replace1", "10000"],
    ["int_find1", "20000"],
    ["caml_hash_int", "200000"],
    ["caml_hash_tuple", "100000"],
    ["int_replace2", "100000"],
    ["int_find2", "300000"],
    ["hashtbl_iter", "200000"],
    ["hashtbl_fold", "200000"],
    ["hashtbl_add_resizing", "4000000"],
    ["hashtbl_add_sized", "6000000"],
    ["hashtbl_add_duplicate", "2000000"],
    ["hashtbl_remove", "4000000"],
    ["hashtbl_find", "6000000"],
    ["hashtbl_filter_map", "100000"],
  ]),
  Macro(group='stdlib', name='string_bench', args=[
    ["string_get", "50000000"],
    ["string_sub", "50000000"],
    ["string_blit", "25000000"],
    ["string_concat", "20000000"],
    ["string_iter", "1000000"],
    ["string_map", "20000000"],
    ["string_trim", "1000000"],
    ["string_index", "25000000"],
    ["string_contains", "25000000"],
    ["string_uppercase_ascii", "1000000"],
    ["string_split_on_char", "500000"],
    ["string_compare", "10000"],
    ["string_equal", "25000"],
  ]),
  Macro(group='stdlib', name='str_bench', args=[
    ["str_regexp", "1000000"],
    ["str_string_match", "50000000"],
    #["str_search_forward", "5000000"],
    ["str_string_partial_match", "25000000"],
    ["str_global_replace", "1000000"],
    ["str_split", "2000000"],
  ]),
  Macro(group='stdlib', name='pervasives_bench', args=[
    ["pervasives_equal_lists", "1000000000"],
    ["pervasives_compare_lists", "100000000"],
    ["pervasives_equal_ints", "1000000000"],
    ["pervasives_compare_ints", "1000000000"],
    ["pervasives_equal_floats", "1000000000"],
    ["pervasives_compare_floats", "200000000"],
    ["pervasives_equal_strings", "20000000"],
    ["pervasives_compare_strings", "20000000"],
  ]),
  Macro(group='stdlib', name='map_bench', args=[
    ["map_iter", "10000"],
    ["map_add", "1000000"],
    ["map_add_duplicate", "1000000"],
    ["map_remove", "1000000"],
    ["map_fold", "10000"],
    ["map_for_all", "10000"],
    ["map_find", "1000000"],
    ["map_map", "10000"],
  ]),
  Macro(group='stdlib', name='big_array_bench', args=[
    ["big_array_int_rev", "1024", "50000"],
    ["big_array_int32_rev", "1024", "50000"],
  ])
]

SEQUENCE = [
  Macro(group='sequence', name='sequence_cps', args=[['10000']])
]

YOJSON = [
  Macro(group='yojson', name='ydump', args=[['-c', 'sample.json']])
]

MACRO_BENCHMARKS =\
  ALMABENCH +\
  BDD +\
  BENCHMARKSGAME +\
  CHAMENEOS +\
  KB +\
  NUMERICAL_ANALYSIS +\
  MENHIR +\
  SIMPLE_TESTS +\
  STDLIB +\
  YOJSON


def _run_test(test):
  """Helper to run a single test."""
  result = None
  try:
    bench, switch, args = test
    exe = os.path.join(ROOT, bench.exe.format(switch))
    with Chdir(os.path.join(ROOT, '_build', switch, 'macro', bench.group)):
      task = subprocess.Popen(
          [exe] + args,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL
      )
      child_pid, status, rusage = os.wait4(task.pid, 0)

    if status == 0:
      result = (rusage.ru_utime, rusage.ru_maxrss)
  except:
    pass

  return bench, switch, args, result


def benchmark_macro(n):
  """Runs performance benchmarks."""

  all_tests = []
  for _, bench, (switch, _) in itertools.product(range(n), MACRO_BENCHMARKS, SWITCHES):
    for args in bench.args:
      all_tests.append((bench, switch, args))
  random.shuffle(all_tests)

  pool = multiprocessing.Pool(int(multiprocessing.cpu_count() * 0.75))
  perf = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
  failed = []
  for bench, switch, args, r in tqdm(pool.imap_unordered(_run_test, all_tests), total=len(all_tests)):
    if not r:
      failed.append((bench.exe.format(switch), ' '.join(args)))
      continue
    perf[bench.name]['_'.join(args)][switch].append(r)
  pool.close()
  pool.join()

  for name, args in failed:
    print('Failed to run {} {}'.format(name, args))

  if not os.path.exists(RESULT):
    os.makedirs(RESULT)
  with open(os.path.join(RESULT, 'macro'), 'w') as f:
    f.write(json.dumps(perf, sort_keys=True, indent=2))


MICRO_BENCHMARKS=[]


def benchmark_micro(n):
  """Runs microbenchmarks."""
  pass

if __name__ == '__main__':
  install()
  #benchmark_size()
  #benchmark_macro(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
  benchmark_micro(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
