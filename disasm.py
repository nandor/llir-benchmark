# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import os
import size
import subprocess
import sys
import re
import json
import tqdm
import multiprocessing

from collections import defaultdict



def canonical_arg_x86_64(arg):
  try:
    int(arg)
    return 'IMM'
  except:
    if arg == 'SYMBOL': return arg
    if arg in ',()': return arg
    if arg in ['%rsp', '%esp']: return 'SP'
    if arg.startswith('*'): arg = arg[1:]
    if arg.startswith('<'): return 'ADDR'
    if arg.startswith('$'): return 'IMM'
    if arg.startswith('-'): return 'IMM'
    if arg.startswith('0x'): return 'IMM'
    if arg.startswith('%r'): return 'REG_64'
    if arg.startswith('%e'): return 'REG_32'
    if arg.startswith('%x'): return 'REG_XMM'
    if arg.startswith('%') and arg[-1] in 'lh': return 'REG_8'
    if arg.startswith('%'): return 'REG_16'
    return arg

def canonical_arg_aarch64(arg):
  try:
    int(arg)
    return 'IMM'
  except:
    if arg in '[]': return ''
    if arg in ',()!': return arg
    if arg == 'SYMBOL': return arg
    if arg.startswith('x'): return 'REG_64'
    if arg.startswith('h'): return 'REG_16'
    if arg.startswith('w'): return 'REG_32'
    if arg.startswith('s'): return 'REG_F32'
    if arg.startswith('d'): return 'REG_F64'
    if arg.startswith('q'): return 'REG_F128'
    if arg.startswith('v'): return 'REG_VEC'
    if arg.startswith('{'): return 'RANGE'
    if arg in ['sp']: return 'SP'
    if arg.startswith('#'): return 'IMM'
    if arg in ['lsl', 'lsr', 'asr', 'sxtw', 'uxtb', 'uxtw', 'uxth', 'ror']: return 'OP'
    if arg in ['eq', 'ne', 'lt', 'gt', 'le', 'ge', 'cc', 'cs', 'mi', 'hi', 'ls', 'pl']: return 'CC'
    raise Exception(arg)

def canonical_arg_riscv64(arg):
  try:
    int(arg)
    return 'IMM'
  except:
    if arg.startswith('0x'): return 'IMM'
    if arg in ',()': return arg
    if arg == 'SYMBOL': return arg
    if arg in ['gp', 'sp', 'ra', 'zero']: return 'REG'
    if arg in ['t0', 't1', 't2', 't3', 't4', 't5', 't6']: return 'REG'
    if arg in ['ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'ft6', 'ft7', 'ft8', 'ft9', 'ft10', 'ft11']: return 'REG'
    if arg in ['fs0', 'fs1', 'fs2', 'fs3', 'fs4', 'fs5', 'fs6', 'fs7', 'fs8', 'fs9', 'fs10', 'fs11']: return 'REG'
    if arg in ['s0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11']: return 'REG'
    if arg in ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7']: return 'REG'
    if arg in ['fa0', 'fa1', 'fa2', 'fa3', 'fa4', 'fa5', 'fa6', 'fa7']: return 'REG'
    if arg in ['rtz']: return 'RM'
    raise Exception(arg)

canonical_arch = {
  'x86_64': 'x86_64',
  'arm64': 'aarch64',
  'riscv': 'riscv64',
  'power': 'powerpc64le',
}

canonical_arg = {
  'x86_64': canonical_arg_x86_64,
  'riscv64': canonical_arg_riscv64,
  #'power': canonical_arg_power,
  'aarch64': canonical_arg_aarch64
}

def disassemble(objdump, arch, bin_path):
  """Disassemble a single binary and identify all of its functions."""

  p = subprocess.Popen([
      objdump,
      '-d',
      bin_path,
      '--no-show-raw-insn',
      '--no-addresses'
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  )

  asm, stderr = p.communicate()
  if p.returncode != 0:
    print(f"Failed to diasssemble {bin_path}:\n{stderr}")
    sys.exit(-1)

  count = {}
  for line in asm.split(b'\n\n'):
    content = []
    for l in line.split(b'\n'):
      l = l.decode('utf-8').strip()
      if not l: continue
      if 'Disassembly' in l: continue
      content.append(l)
    if not content:
      continue

    addr = content[0]
    func = addr[1:-2]
    if func in ['_PROCEDURE_LINKAGE_TABLE_']:
      continue
    for l in content[1:]:
      if arch == 'x86_64' or arch == 'riscv64':
        l = l.strip().split('#')[0]
      if arch == 'aarch64':
        l = l.strip().split('//')[0]
      l = re.sub('<[^>]*>', 'SYMBOL', l)
      op, *args = [t for t in l.replace('\t',' ').split(' ') if t]
      if op in ['data16', '.word']:
        continue
      if args:
        final_args = []
        for arg in args:
          tokens = re.split('(,|\\(|\\)|<|>|\\[|\\])', arg)
          for token in tokens:
            final_args.append(canonical_arg[arch](token))
        args = final_args
      else:
        args = []
      inst = '{} {}'.format(op, ''.join(args)).strip()
      if not func in count:
        count[func] = {}
      if not inst in count[func]:
        count[func][inst] = 0
      count[func][inst] += 1

  return bin_path, count


def _disassemble(arg):
  objdump, arch, bin_path = arg
  try:
    return disassemble(objdump, arch, bin_path)
  except Exception as e:
    print(repr(e))
  return None

def benchmark_insts(switches, root, output):
  """Disassembles all binaries in the bin folder of the switch."""

  opam = os.path.join(root, '_opam')

  files = []
  pool = multiprocessing.Pool(multiprocessing.cpu_count())
  for switch in switches:
    arch = canonical_arch[switch.split('+')[0]]
    objdump = os.path.join(
        opam,
        switch,
        'bin',
        f'{arch}-unknown-linux-gnu-objdump'
    )

    for name in sorted(size.find_all_binaries(opam, switch)):
      bin_path = os.path.join(opam, switch, 'bin', name)
      files.append((objdump, arch, bin_path))

    for parent, _, dir_files in os.walk(os.path.join(root, '_build', switch)):
      for f in dir_files:
        bin_path = os.path.join(parent, f)
        if size.is_elf_binary(bin_path):
          files.append((objdump, arch, bin_path))

  disasm = {}
  jobs = pool.imap_unordered(_disassemble, files)
  for result in tqdm.tqdm(jobs, total=len(files)):
    if result:
      bin_path, data = result
      disasm[bin_path[len(root) + 1:].replace('/', '_')] = data

  if not os.path.exists(output):
    os.makedirs(output)
  for name, data in disasm.items():
    with open(os.path.join(output, f'{name}.json'), 'w') as f:
      f.write(json.dumps(data, sort_keys=True, indent=2))
