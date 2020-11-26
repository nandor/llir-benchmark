# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import os
import subprocess
import json

from collections import defaultdict



def benchmark_size(switches, root, output):
  """Finds the code size of all applications in all switches."""

  files = set()
  for switch in switches:
    bin_dir = os.path.join(root, switch, 'bin')
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
      bin_path = os.path.join(root, switch, 'bin', name)
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

  parent = os.path.abspath(os.path.join(output, os.pardir))
  if not os.path.exists(parent):
    os.makedirs(parent)
  with open(output, 'w') as f:
    f.write(json.dumps(sizes, sort_keys=True, indent=2))
