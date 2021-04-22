#!/usr/bin/env python3

import json
import textwrap
import statistics
import scipy.stats
import sys

arch = sys.argv[1]

with open('_result/macro.json', 'r') as f:
  data = json.loads(f.read())

def independent(t0, t1):
  if len(t0) < 2 or len(t1) < 2:
    return True
  _, p = scipy.stats.ttest_ind(t0, t1)
  return p < 0.01

def stdev(ts):
  if len(ts) < 2: return 0.0
  return statistics.stdev(ts)

for bench, runs in data.items():
  def get_times(key): return [t for t, _ in runs[key]]

  keys = sorted(runs.keys() - [f'{arch}+ref'])
  times = ''
  ref_times = get_times(f'{arch}+ref')
  ref_mean = statistics.mean(ref_times)
  times += '{:6.2f}/{:5.3f}'.format(ref_mean, stdev(ref_times))

  for key in keys:
    key_times = get_times(key)
    dev_mean = statistics.mean(key_times)
    times += '   {:6.2f}/{:5.3f}'.format(dev_mean, stdev(key_times))

    if independent(ref_times, key_times):
      if ref_mean == 0.0:
        times += '        '
      else:
        f = dev_mean / ref_mean * 100 - 100
        times += '{:>8}'.format('{:+5.2f}'.format(f))
    else:
      times += ' ' * 8

  if len(bench) > 60:
    bench = bench[:60] + '...'
  print('{} {}'.format(bench.ljust(60), times))
