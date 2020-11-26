# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import os
import subprocess
import sys



# Path to build the switches in.
ROOT=os.path.dirname(os.path.realpath(__file__))
OPAMROOT=os.path.join(ROOT, '_opam')



# Enumeration of supported targets.
CPUS = {
  'x86_64': ['zen2', 'skylake', 'tremont'],
  'arm64': ['cortex-a72'],
  'riscv': ['sifive-u74'],
  'power': ['pwr8', 'pwr9']
}

# Switches with root packages.
SWITCHES = {}
for arch, cpus in CPUS.items():
  SWITCHES[f'{arch}+ref'] = [f'ocaml-variants-{arch}.4.11.1.master']
  SWITCHES[f'{arch}+llir'] = [f'ocaml-variants-{arch}.4.11.1.master+llir']
  for opt in ['O0', 'O1', 'O2', 'O3', 'O4']:
    SWITCHES[f'{arch}+llir+{opt}'] = [
        f'ocaml-variants-{arch}.4.11.1.master+llir',
        f'llir-config.{opt}'
    ]
    for cpu in cpus:
      SWITCHES[f'{arch}+llir+{opt}+{cpu}'] = [
          f'ocaml-variants-{arch}.4.11.1.master+llir',
          f'llir-config.{opt}+{cpu}'
      ]

# List of all packages to install.
PACKAGES=[
  "coq", "menhir", "compcert", "ocamlgraph", "cpdf", "minilight", "yojson",
  "base", "stdio", "dune", "camlzip", "zarith", "ocplib-simplex", "diy",
  "ocamlmod", "sexplib0", "odoc", "hevea", "cmitomli", "alcotest", "biniou",
  "bigstringaf", "result", "angstrom", "hxd", "cppo", "csexp", "easy-format",
  "gmp", "ocaml-syntax-shims", "ounit2", "ppxlib", "re", "zlib", "jsonm",
  "uuidm", "ocplib-endian", "lwt", "fix", "why3", "tyxml", "nbcodec", "react",
  "rml", "uucp", "atdgen", "atdj", "atds", "camlp5", "ppxfind", "ucaml",
  "ocamlformat", "js_of_ocaml", "ppx_deriving", "ppx_tools", "frama-c",
  "alt-ergo-free", "camlp4", "num", "fraplib", "cubicle", "uri", "irmin",
  "irmin-mem", "irmin-test", "stringext", "bos", "base64", "digestif",
  "eqaf", "crowbar", "metrics-unix", "reason", "reanalyze"
]

def opam(args, capture=False, silent=False, cwd=None, **kwargs):
  """Run the opam process and capture its output."""

  env = os.environ.copy()
  env['OPAMROOT'] = OPAMROOT
  if capture:
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
  else:
    proc = subprocess.Popen(
        ['opam'] + list(args),
        stdout=subprocess.DEVNULL if silent else None,
        stderr=subprocess.DEVNULL if silent else None,
        env=env,
        cwd=cwd
    )
    child_pid, status, rusage = os.wait4(proc.pid, 0)
    if status != 0:
      print('"opam {}" failed:\n'.format(' '.join(args)))
      sys.exit(proc.returncode)
    return rusage.ru_utime


def _dune(jb, switch, target):
  opam([
      'exec',
      '--switch={}'.format(switch),
      '--',
      'dune',
      'build',
      '-j', str(jb),
      '--profile=release',
      '--workspace=dune-workspace',
      target
  ])


def install(switches, repository, jb, test):
  """Installs the switches and the required packages."""

  # Set up the workspace file.
  with open(os.path.join(ROOT, 'dune-workspace'), 'w') as f:
    f.write('(lang dune 2.0)\n')
    for switch in switches:
      f.write('(context (opam (switch {0}) (name {0})))\n'.format(switch))

  # Set up opam and the custom repository.
  opam([
      'init',
      '--bare',
      '--no-setup',
      '--no-opamrc',
      '--disable-sandboxing',
      repository
  ])
  opam(['update'])

  # Create all the switches.
  for switch in switches:
    if switch not in opam(['switch', 'list'], capture=True):
      opam([
          'switch',
          'create',
          '--yes',
          '-j', str(jb),
          switch,
          '--empty',
      ])

  # Install the compilers.
  for switch in switches:
    opam([
        'install',
        '--switch={}'.format(switch),
        '--yes'
    ] + (['--with-test'] if test else []) + SWITCHES[switch])

  # Install all packages.
  for switch in switches:
    opam(
        [
          'install',
          '--switch={}'.format(switch),
          '--yes',
          '-j', str(jb),
        ] + (['--with-test'] if test else []) + PACKAGES,
        prefix=os.path.join(OPAMROOT, switch)
    )

  # Build all benchmarks.
  switch = switches[0]
  _dune(jb, switch, '@build_macro')
  _dune(jb, switch, '@build_micro')
  _dune(jb, switch, '@build_compcert')
  _dune(jb, switch, '@build_frama_c')
