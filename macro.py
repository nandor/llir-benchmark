"""
This file is part of the llir-benchmark project.
(C) 2020 Nandor Licker. All rights reserved.
"""

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

class Group(object):
  def __init__(self, target, tests):
    self.target = target
    self.tests = tests

ALMABENCH = [Group('opam:@build_macro', [
  Macro(group='almabench', name='almabench', args=[['10']]),
])]

BDD = [Group('opam:@build_macro', [
  Macro(group='bdd', name='bdd', args=[['26']]),
])]

BENCHMARKSGAME = [Group('opam:@build_macro', [
  Macro(group='benchmarksgame', name='binarytrees5', args=[['20']]),
  Macro(group='benchmarksgame', name='fannkuchredux2', args=[['11']]),
  Macro(group='benchmarksgame', name='fannkuchredux', args=[['11']]),
  Macro(group='benchmarksgame', name='fasta3', args=[['10_000_000']]),
  Macro(group='benchmarksgame', name='fasta6', args=[['10_000_000']]),
  Macro(group='benchmarksgame', name='knucleotide'),
  Macro(group='benchmarksgame', name='mandelbrot6', args=[['4000']]),
  Macro(group='benchmarksgame', name='nbody', args=[['100000000']]),
  Macro(group='benchmarksgame', name='pidigits5', args=[['7000']]),
  Macro(group='benchmarksgame', name='regexredux2'),
  Macro(group='benchmarksgame', name='revcomp2'),
  Macro(group='benchmarksgame', name='spectralnorm2', args=[['2000']]),
])]

CHAMENEOS = [Group('opam:@build_macro', [
  Macro(group='chameneos', name='chameneos_redux_lwt', args=[['2000000']]),
])]

KB = [Group('opam:@build_macro', [
  Macro(group='kb', name='kb', args=[['200']]),
  Macro(group='kb', name='kb_no_exc', args=[['200']]),
])]

LEXIFY = [Group('opam:@build_macro', [
  Macro(group='lexifi-g2pp', name='main', args=[[]])
])]

NUMERICAL_ANALYSIS = [Group('opam:@build_macro', [
  Macro(group='numerical-analysis', name='durand_kerner_aberth', args=[
    ['100', '50']
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
])]

MENHIR = [Group('opam:@build_macro', [
  Macro(group='menhir', name='menhir', exe='menhir', args=[
    ['-v', '--table', 'sysver.mly'],
    ['ocaml.mly', '--list-errors', '-la', '2', '--no-stdlib', '--lalr'],
    ['-v', '-t', 'keywords.mly', 'sql-parser.mly', '--base', 'sql-parser']
  ]),
])]

SIMPLE_TESTS = [Group('opam:@build_macro', [
  Macro(group='simple-tests', name='alloc', args=[
    ['1_000_000']
  ]),
  Macro(group='simple-tests', name='morestacks', args=[
    ['1_000']
  ]),
  Macro(group='simple-tests', name='stress', args=[
    ["1", "10", "100_000"],
    ["10000", "10", "100_000"],
    ["100000", "10", "100_000"],
    ["1", "25", "100_000"],
    ["10000", "25", "100_000"],
    ["100000", "25", "100_000"],
    ["1", "50", "100_000"],
    ["10000", "50", "100_000"],
    ["100000", "50", "100_000"],
    ["1", "75", "100_000"],
    ["10000", "75", "100_000"],
    ["100000", "75", "100_000"],
    ["1", "100", "100_000"],
    ["10000", "100", "100_000"],
    ["100000", "100", "100_000"],
  ]),
  Macro(group='simple-tests', name='capi', args=[
    ["test_no_args_alloc", "1_000_000_000"],
    ["test_no_args_noalloc", "1_000_000_000"],
    ["test_few_args_alloc", "1_000_000_000"],
    ["test_few_args_noalloc", "1_000_000_000"],
    ["test_many_args_alloc", "1_000_000_000"],
    ["test_many_args_noalloc", "1_000_000_000"],
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
    ["100000", "200"],
    ["10000", "10_000"],
    ["1000", "200_000"],
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
])]

STDLIB_STACK = [Group('opam:@build_stdlib_stack', [
  Macro(group='stdlib', name='stack_bench', args=[
    ["stack_fold", "10_000_000"],
    ["stack_push_pop", "500_000_000"],
  ])
])]

STDLIB_ARRAY = [Group('opam:@build_stdlib_array', [
  Macro(group='stdlib', name='array_bench', args=[
    ["array_forall", "1000", "1_000_000"],
    ["array_fold", "1000", "1_000_000"],
    ["array_iter", "1000", "1_000_000"],
  ])
])]

STDLIB_BYTES = [Group('opam:@build_stdlib_bytes', [
  Macro(group='stdlib', name='bytes_bench', args=[
    ["bytes_get", "200_000_000"],
    ["bytes_sub", "200_000_000"],
    ["bytes_blit", "50_000_000"],
    ["bytes_concat", "20_000_000"],
    ["bytes_iter", "10_000_000"],
    ["bytes_map", "10_000_000"],
    ["bytes_trim", "20_500_000"],
    ["bytes_index", "10_000_000"],
    ["bytes_contains", "100_000_000"],
    ["bytes_uppercase_ascii", "1_000_000"],
    ["bytes_set", "1_000_000_000"],
    ["bytes_cat", "1_000_000_000"],
  ])
])]

STDLIB_SET = [Group('opam:@build_stdlib_set', [
  Macro(group='stdlib', name='set_bench', args=[
    ["set_fold", "1000000"],
    ["set_add_rem", "20000000"],
    ["set_mem", "50000000"],
  ])
])]

STDLIB_HASHTBL = [Group('opam:@build_stdlib_hashtbl', [
  Macro(group='stdlib', name='hashtbl_bench', args=[
    ["int_replace1", "100_000"],
    ["int_find1", "200_000"],
    ["caml_hash_int", "200_000"],
    ["caml_hash_tuple", "100_000"],
    ["int_replace2", "100_000"],
    ["int_find2", "500_000"],
    ["hashtbl_iter", "200_000"],
    ["hashtbl_fold", "200_000"],
    ["hashtbl_add_resizing", "4_000_000"],
    ["hashtbl_add_sized", "6_000_000"],
    ["hashtbl_add_duplicate", "2_000_000"],
    ["hashtbl_remove", "40_000_000"],
    ["hashtbl_find", "60_000_000"],
    ["hashtbl_filter_map", "100_000"],
  ])
])]

STDLIB_STR = [Group('opam:@build_stdlib_str', [
  Macro(group='stdlib', name='str_bench', args=[
    ["str_regexp", "1000000"],
    ["str_string_match", "50000000"],
    ["str_search_forward", "5000000"],
    ["str_string_partial_match", "250_000_000"],
    ["str_global_replace", "1000000"],
    ["str_split", "2000000"],
  ])
])]

STDLIB_PERVASIVES = [Group('opam:@build_stdlib_pervasives', [
  Macro(group='stdlib', name='pervasives_bench', args=[
    ["pervasives_equal_lists", "1000000000"],
    ["pervasives_compare_lists", "100000000"],
    ["pervasives_equal_ints", "1000000000"],
    ["pervasives_compare_ints", "1000000000"],
    ["pervasives_equal_floats", "1000000000"],
    ["pervasives_compare_floats", "200000000"],
    ["pervasives_equal_strings", "20000000"],
    ["pervasives_compare_strings", "20000000"],
  ])
])]

STDLIB_MAP = [Group('opam:@build_stdlib_map', [
  Macro(group='stdlib', name='map_bench', args=[
    ["map_iter", "50_000"],
    ["map_add", "1_000_000"],
    ["map_add_duplicate", "1000000"],
    ["map_remove", "10_000_000"],
    ["map_fold", "50_000"],
    ["map_for_all", "50_000"],
    ["map_find", "10_000_000"],
    ["map_map", "10_000"],
  ])
])]

STDLIB_BIG_ARRAY = [Group('opam:@build_stdlib_big_array', [
  Macro(group='stdlib', name='big_array_bench', args=[
    ["big_array_int_rev", "1024", "200_000"],
    ["big_array_int32_rev", "1024", "200_000"],
  ])
])]

STDLIB_STRING = [Group('opam:@build_stdlib_string', [
  Macro(group='stdlib', name='string_bench', args=[
    ["string_get", "50_000_000"],
    ["string_sub", "50000000"],
    ["string_blit", "25000000"],
    ["string_concat", "20000000"],
    ["string_map", "20000000"],
    ["string_trim", "100_000_000"],
    ["string_index", "250_000_000"],
    ["string_contains", "250_000_000"],
    ["string_uppercase_ascii", "1000000"],
    ["string_split_on_char", "500000"],
    ["string_compare", "100_000"],
    ["string_equal", "25000"],
  ])
])]

STDLIB=\
  STDLIB_STACK+\
  STDLIB_ARRAY+\
  STDLIB_BYTES+\
  STDLIB_SET+\
  STDLIB_HASHTBL+\
  STDLIB_STR+\
  STDLIB_PERVASIVES+\
  STDLIB_MAP+\
  STDLIB_BIG_ARRAY+\
  STDLIB_STRING

STDLIB_STATIC_STACK = [Group('opam:@build_stdlib_stack', [
  Macro(group='stdlib-static', name='stack_bench', args=[
    ["stack_fold", "10_000_000"],
    ["stack_push_pop", "500_000_000"],
  ])
])]

STDLIB_STATIC_ARRAY = [Group('opam:@build_stdlib_array', [
  Macro(group='stdlib-static', name='array_bench', args=[
    ["array_forall", "1000", "1_000_000"],
    ["array_fold", "1000", "1_000_000"],
    ["array_iter", "1000", "1_000_000"],
  ])
])]

STDLIB_STATIC_BYTES = [Group('opam:@build_stdlib_bytes', [
  Macro(group='stdlib-static', name='bytes_bench', args=[
    ["bytes_get", "200_000_000"],
    ["bytes_sub", "200_000_000"],
    ["bytes_blit", "50_000_000"],
    ["bytes_concat", "20_000_000"],
    ["bytes_iter", "10_000_000"],
    ["bytes_map", "10_000_000"],
    ["bytes_trim", "20_500_000"],
    ["bytes_index", "10_000_000"],
    ["bytes_contains", "100_000_000"],
    ["bytes_uppercase_ascii", "1_000_000"],
    ["bytes_set", "1_000_000_000"],
    ["bytes_cat", "1_000_000_000"],
  ])
])]

STDLIB_STATIC_SET = [Group('opam:@build_stdlib_set', [
  Macro(group='stdlib-static', name='set_bench', args=[
    ["set_fold", "1000000"],
    ["set_add_rem", "20000000"],
    ["set_mem", "50000000"],
  ])
])]

STDLIB_STATIC_HASHTBL = [Group('opam:@build_stdlib_hashtbl', [
  Macro(group='stdlib-static', name='hashtbl_bench', args=[
    ["int_replace1", "100_000"],
    ["int_find1", "200_000"],
    ["caml_hash_int", "200_000"],
    ["caml_hash_tuple", "100_000"],
    ["int_replace2", "100_000"],
    ["int_find2", "500_000"],
    ["hashtbl_iter", "200_000"],
    ["hashtbl_fold", "200_000"],
    ["hashtbl_add_resizing", "4_000_000"],
    ["hashtbl_add_sized", "6_000_000"],
    ["hashtbl_add_duplicate", "2_000_000"],
    ["hashtbl_remove", "40_000_000"],
    ["hashtbl_find", "60_000_000"],
    ["hashtbl_filter_map", "100_000"],
  ])
])]

STDLIB_STATIC_STR = [Group('opam:@build_stdlib_str', [
  Macro(group='stdlib-static', name='str_bench', args=[
    ["str_regexp", "1000000"],
    ["str_string_match", "50000000"],
    ["str_search_forward", "5000000"],
    ["str_string_partial_match", "250_000_000"],
    ["str_global_replace", "1000000"],
    ["str_split", "2000000"],
  ])
])]

STDLIB_STATIC_PERVASIVES = [Group('opam:@build_stdlib_pervasives', [
  Macro(group='stdlib-static', name='pervasives_bench', args=[
    ["pervasives_equal_lists", "1000000000"],
    ["pervasives_compare_lists", "100000000"],
    ["pervasives_equal_ints", "1000000000"],
    ["pervasives_compare_ints", "1000000000"],
    ["pervasives_equal_floats", "1000000000"],
    ["pervasives_compare_floats", "200000000"],
    ["pervasives_equal_strings", "20000000"],
    ["pervasives_compare_strings", "20000000"],
  ])
])]

STDLIB_STATIC_MAP = [Group('opam:@build_stdlib_map', [
  Macro(group='stdlib-static', name='map_bench', args=[
    ["map_iter", "50_000"],
    ["map_add", "1_000_000"],
    ["map_add_duplicate", "1000000"],
    ["map_remove", "10_000_000"],
    ["map_fold", "50_000"],
    ["map_for_all", "50_000"],
    ["map_find", "10_000_000"],
    ["map_map", "10_000"],
  ])
])]

STDLIB_STATIC_BIG_ARRAY = [Group('opam:@build_stdlib_big_array', [
  Macro(group='stdlib-static', name='big_array_bench', args=[
    ["big_array_int_rev", "1024", "200_000"],
    ["big_array_int32_rev", "1024", "200_000"],
  ])
])]

STDLIB_STATIC_STRING = [Group('opam:@build_stdlib_string', [
  Macro(group='stdlib-static', name='string_bench', args=[
    ["string_get", "50_000_000"],
    ["string_sub", "50000000"],
    ["string_blit", "25000000"],
    ["string_concat", "20000000"],
    ["string_map", "20000000"],
    ["string_trim", "100_000_000"],
    ["string_index", "250_000_000"],
    ["string_contains", "250_000_000"],
    ["string_uppercase_ascii", "1000000"],
    ["string_split_on_char", "500000"],
    ["string_compare", "100_000"],
    ["string_equal", "25000"],
  ])
])]

STDLIB_STATIC=\
  STDLIB_STATIC_STACK+\
  STDLIB_STATIC_ARRAY+\
  STDLIB_STATIC_BYTES+\
  STDLIB_STATIC_SET+\
  STDLIB_STATIC_HASHTBL+\
  STDLIB_STATIC_STR+\
  STDLIB_STATIC_PERVASIVES+\
  STDLIB_STATIC_MAP+\
  STDLIB_STATIC_BIG_ARRAY+\
  STDLIB_STATIC_STRING

STDLIB=STDLIB+STDLIB_STATIC

SEQUENCE = [Group('opam:@build_macro', [
  Macro(group='sequence', name='sequence_cps', args=[['10000']])
])]

YOJSON = [Group('opam:@build_macro', [
  Macro(group='yojson', name='ydump', args=[['-c', 'sample.json']])
])]

ZARITH = [Group('opam:@build_macro', [
  Macro(group='zarith', name='zarith_fact', args=[['40', '4_000_000']]),
  Macro(group='zarith', name='zarith_fib',  args=[['Z', '42']]),
  Macro(group='zarith', name='zarith_pi',   args=[['6000']]),
  Macro(group='zarith', name='zarith_tak',  args=[['Z', '5000']]),
])]

MINILIGHT = [Group('opam:@build_macro', [
  Macro(group='minilight', name='minilight', exe='minilight-ocaml', args=[
    ['roomfront.ml.txt']
  ])
])]

JS_OF_OCAML = [Group('opam:@build_macro', [
  Macro(group='js_of_ocaml', name='js_of_ocaml', exe='js_of_ocaml', args=[
    ['{bin}/coqtop.byte', '-o', 'out.js'],
    ['{bin}/frama-c.byte', '-o', 'out.js'],
    ['{bin}/ocamlopt.byte', '-o', 'out.js'],
    ['{bin}/ocamllex.byte', '-o', 'out.js'],
    ['{bin}/ocamlprof.byte', '-o', 'out.js'],
    ['{bin}/ocamldep.byte', '-o', 'out.js']
  ])
])]

JSONM = [Group('opam:@build_macro', [
  Macro(group='jsonm', name='jsonm', exe='jsontrip', args=[
    ['sample.json']
  ])
])]

CPDF = [Group('opam:@build_macro', [
  Macro(group='cpdf', name='cpdf', exe='cpdf', args=[
    ['-merge', 'PDFReference16.pdf_toobig', 'metro_geo.pdf', '-o', '/dev/null'],
    ['scale-to-fit', 'a4landscape', '-twoup', 'PDFReference16.pdf_toobig', '-o', '/dev/null'],
    ['-squeeze', 'PDFReference16.pdf_toobig', '-o', '/dev/null'],
    ['-blacktext', 'metro_geo.pdf', '-o', '/dev/null'],
  ])
])]

NBCODEC = [Group('opam:@build_macro', [
  Macro(group='nbcodec', name='nbcodec', exe='setrip', args=[
    ['-enc', '-rseed', '1067894368', '-maxd', '10', '-maxl', '55']
  ])
])]

LLIR = [Group('opam:@build_llir', [
  Macro(group='llir', name='fft', args=['1024'])
])]

COQ = [Group('opam:@build_coq', [
  Macro(group='coq', name='coq', exe='coqc', args=[
    ['Explode.v'],
    ['AbstractInterpretation.v'],
    ['BasicSyntax.v']
  ]),
  Macro(group='coq', name='coqchk', exe='coqchk', args=[
    ['Coq.PArith.BinPos'],
    ['Int']
  ])
])]

COMPCERT = [Group('opam:@build_compcert', [
  Macro(group='compcert', name='compcert', exe='ccomp', args=[
    ['sqlite3.i', '-fbitfields', '-fstruct-passing', '-c', '-S']
  ])
])]

ALT_ERGO = [Group('opam:@build_macro', [
  Macro(group='alt-ergo', name='alt-ergo', exe='alt-ergo', args=[
    ['fill.why'],
    ['yyll.why'],
    ['ggjj.why'],
  ])
])]

FRAMA_C = [Group('opam:@build_frama_c', [
  Macro(group='frama-c', name='frama-c', exe='frama-c', args=[
    [
      '-slevel', '1000000000',
      '-no-results',
      '-no-val-show-progress',
      't.i',
      '-val',
    ]
  ])
])]

OCAMLC = [Group('opam:@build_macro', [
  Macro(group='ocamlc', name='ocamlc', exe='ocamlc.opt', args=[
    [ 'pairs.ml' ],
    [ 'large.ml' ]
  ])
])]

OCAMLFORMAT = [Group('opam:@build_macro', [
  Macro(group='ocamlformat', name='ocamlformat', exe='ocamlformat', args=[
    [ '--enable-outside-detected-project', 'large.ml' ]
  ])
])]

CUBICLE = [Group('opam:@build_macro', [
  Macro(group='cubicle', name='cubicle', exe='cubicle', args=[
    [ 'german_pfs.cub' ],
    [ 'szymanski_at.cub' ]
  ])
])]

IRMIN = [Group('opam:@build_irmin', [
  Macro(group='irmin', name='irmin_mem_rw', args=[
    [ '10_000', '50_000', '80', '100_000_000' ],
    [ '10_000', '50_000', '20', '100_000_000' ]
  ]),
  Macro(group='irmin', name='layers', args=[
    [ '-n', '500' ],
    [ '-n', '150' ]
  ]),
  Macro(group='irmin', name='main', args=[
    [ '-n', '100' ],
    [ '-n', '500' ]
  ])
])]

THREAD_LWT = [Group('opam:@build_macro', [
  Macro(group='thread-lwt', name='thread_ring_lwt_mvar', args=[
    [ '20_000' ],
  ]),
  Macro(group='thread-lwt', name='thread_ring_lwt_stream', args=[
    [ '20_000' ],
  ])
])]

VALET = [Group('opam:@build_macro', [
  Macro(group='valet', name='test_lwt', args=[
    [ '200' ],
  ])
])]

CRYPTO = [Group('opam:@build_crypto', [
  Macro(group='crypto', name='ed25519_hacl', args=[['4000']]),
  Macro(group='crypto', name='ed25519_hacl_external', args=[['4000']]),
  Macro(group='crypto', name='ed25519_sodium', args=[['20000']]),
  Macro(group='crypto', name='p256_hacl', args=[['500']]),
  Macro(group='crypto', name='p256_hacl_ctypes', args=[['500']]),
  Macro(group='crypto', name='p256_hacl_external', args=[['500']]),
  Macro(group='crypto', name='p256_uecc', args=[['4000']]),
])]

VEC = [Group('opam:@build_vec', [
  Macro(group='vec', name='integer_dot', args=[['10_000_000']])
])]

BOXROOT=[Group('opam:@build_boxroot', [
  Macro(group='boxroot/benchmarks', name='globroots', args=[
    { 'N': '500_000', 'REF': 'gc' },
    { 'N': '500_000', 'REF': 'boxroot' },
    { 'N': '500_000', 'REF': 'ocaml' },
    { 'N': '500_000', 'REF': 'global' },
    { 'N': '500_000', 'REF': 'generational' },
  ]),
  Macro(group='boxroot/benchmarks', name='local_roots', args=[
    { 'N':    '1', 'ROOT': 'local' },
    { 'N':    '2', 'ROOT': 'local' },
    { 'N':    '5', 'ROOT': 'local' },
    { 'N':   '10', 'ROOT': 'local' },
    { 'N':  '100', 'ROOT': 'local' },
    { 'N': '1000', 'ROOT': 'local' },
    { 'N':    '1', 'ROOT': 'boxroot' },
    { 'N':    '2', 'ROOT': 'boxroot' },
    { 'N':    '5', 'ROOT': 'boxroot' },
    { 'N':   '10', 'ROOT': 'boxroot' },
    { 'N':  '100', 'ROOT': 'boxroot' },
    { 'N': '1000', 'ROOT': 'boxroot' },
    { 'N':    '1', 'ROOT': 'generational' },
    { 'N':    '2', 'ROOT': 'generational' },
    { 'N':    '5', 'ROOT': 'generational' },
    { 'N':   '10', 'ROOT': 'generational' },
    { 'N':  '100', 'ROOT': 'generational' },
    { 'N': '1000', 'ROOT': 'generational' },
  ]),
  Macro(group='boxroot/benchmarks', name='perm_count', args=[
    {
      'N': '10',
      'CHOICE': 'persistent',
      'REF': ref
    } for ref in ['gc', 'boxroot', 'ocaml', 'global', 'generational']
  ]),
  Macro(group='boxroot/benchmarks', name='synthetic', args=[
    {
      'N': '8',
      'SMALL_ROOTS': '10_000',
      'LARGE_ROOTS': '20',
      'SMALL_ROOT_PROMOTION_RATE': '0.2',
      'LARGE_ROOT_PROMOTION_RATE': '1',
      'ROOT_SURVIVAL_RATE': '0.99',
      'GC_PROMOTION_RATE': '0.1',
      'GC_SURVIVAL_RATE': '0.5',
      'REF': ref
    } for ref in ['gc', 'boxroot', 'ocaml', 'global', 'generational']
  ]),
])]

MEDIUM =\
  ALMABENCH+\
  BDD+\
  BENCHMARKSGAME+\
  CHAMENEOS+\
  KB+\
  NUMERICAL_ANALYSIS+\
  MENHIR+\
  SIMPLE_TESTS+\
  STDLIB+\
  STDLIB_STATIC+\
  YOJSON+\
  ZARITH+\
  MINILIGHT+\
  JSONM+\
  CPDF+\
  NBCODEC+\
  LLIR+\
  FRAMA_C+\
  CUBICLE+\
  LEXIFY+\
  IRMIN+\
  THREAD_LWT+\
  VALET

TOOLS=COQ + COMPCERT + ALT_ERGO + OCAMLC + JS_OF_OCAML + OCAMLFORMAT

ALL=MEDIUM + TOOLS + CRYPTO


LARGE=\
  ALT_ERGO + COMPCERT + COQ + CPDF + CUBICLE + FRAMA_C + JS_OF_OCAML + \
  MENHIR + MINILIGHT + NBCODEC + OCAMLC + OCAMLFORMAT
