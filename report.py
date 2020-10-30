#!/usr/bin/env python3 

import json
import textwrap
import statistics
import scipy.stats



with open('_result/macro', 'r') as f:
  data = json.loads(f.read())


for bench, runs in data.items():
  def get_times(key): return [t for t, _ in runs[key]]

  keys = sorted(runs.keys() - ['ref'])
  times = ''
  ref_times = get_times('ref')
  ref_mean = statistics.mean(ref_times)
  times += '{:6.2f}/{:5.3f}'.format(ref_mean, statistics.stdev(ref_times))

  for key in keys:
    key_times = get_times(key)
    dev_mean = statistics.mean(key_times)
    times += '   {:6.2f}/{:5.3f}'.format(dev_mean, statistics.stdev(key_times))

    _, p = scipy.stats.ttest_ind(ref_times, key_times)
    if p < 0.01:
      f = dev_mean / ref_mean * 100 - 100
      times += '{:>8}'.format('{:+5.2f}'.format(f))
    else:
      times += ' ' * 8
  
  if len(bench) > 27:
    bench = bench[:27] + '...'
  print('{} {}'.format(bench.ljust(30), times))
