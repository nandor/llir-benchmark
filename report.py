#!/usr/bin/env python3 

import json
import textwrap
import statistics



with open('_result/macro', 'r') as f:
  data = json.loads(f.read())

for bench, runs in data.items():
  print(bench)
  for switch, times in runs.items():
    print('\t{}: {}'.format(switch, statistics.mean((t for t, _ in times))))
