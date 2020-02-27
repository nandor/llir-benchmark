"""
This file is part of the llir-benchmark project.
(C) 2020 Nandor Licker. All rights reserved.
"""

class Micro(object):
  def __init__(self, name):
    self.name = name
    self.exe = '_build/{{0}}/micro/{0}/{0}.exe'.format(name)


BENCHMARKS=[
  Micro('almabench'),
  Micro('bdd'),
  Micro('bigarray_rev'),
  Micro('boyer'),
  Micro('fft'),
  Micro('fibonacci'),
  Micro('format'),
  Micro('hamming'),
  Micro('kahan_sum'),
  Micro('kb'),
  Micro('lens'),
  Micro('list'),
  Micro('nucleic'),
  Micro('num_analysis'),
  Micro('sequence'),
  Micro('sieve'),
  Micro('vector_functor'),
]
