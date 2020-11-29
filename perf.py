# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import itertools
import subprocess
import os

import tqdm
import build



def benchmark_macro(benchmarks, switches, root, output):
  """Run a macro benchmark under perf and gather a profile."""

  all_tests = []
  for bench, switch in itertools.product(benchmarks, switches):
    for args in bench.args:
      all_tests.append((bench, switch, args))

  env={}
  for line in build.opam(['env', '--switch', switch], capture=True).split('\n'):
    if not line.strip(): continue
    k, v = line.split(';')[0].strip().split('=')
    env[k] = v[1:-1]

  for bench, switch, args in tqdm.tqdm(all_tests):
    exe = os.path.join(root, bench.exe.format(switch))
    bin_dir = os.path.join(root, '_opam', switch, 'bin')
    lib_dir = os.path.join(root, '_opam', switch, 'lib')

    cwd = os.path.join(root, '_build', switch, 'macro', bench.group)

    if not os.path.exists(cwd):
      os.makedirs(cwd)

    parent = os.path.join(output, switch)
    if not os.path.exists(parent):
      os.makedirs(parent)

    name = os.path.join(
        parent,
        "{}.{}".format(bench.name, '_'.join(args).replace('/', '_')
    ))

    if os.path.exists(name):
      continue

    p = subprocess.Popen([
          'perf',
          'record',
          '-o',
          name,
          '--',
          exe
        ] + [arg.format(bin=bin_dir, lib=lib_dir) for arg in args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env
    )
    _, stderr = p.communicate()
    p.wait()
    if p.returncode != 0:
      print(f"Failed to run {exe} with {' '.join(args)}:\n{stderr}")
      return ""
