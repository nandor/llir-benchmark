# This file is part of the llir-benchmark project
# Licensing information can be found in the LICENSE file
# (C) 2020 Nandor Licker. All rights reserved.

import os
import subprocess
import sys
import packages



# Path to build the switches in.
ROOT=os.path.dirname(os.path.realpath(__file__))
OPAMROOT=os.path.join(ROOT, '_opam')



# Enumeration of supported targets.
CPUS = {
  'i686': [],
  'amd64': ['generic', 'zen2', 'skylake', 'tremont'],
  'arm64': ['cortex-a72'],
  'riscv': ['sifive-u74'],
  'power': ['pwr8', 'pwr9']
}
# Enumeration of custom configurations.
CONFIG = {
  'no-code-layout': {
    'LLIR_OPT_DISABLED': 'code-layout'
  },
  'no-eliminate-tags': {
    'LLIR_OPT_DISABLED': 'eliminate-tags'
  }
}

# Enumeration of opt levels.
OPT = ['O0', 'O1', 'O2', 'O3', 'O4', 'Os']

# Pinned packages.
PINS=[
  ('zarith', '1.12+llir'),
  ('zarith-freestanding', '1.12+llir'),
  ('mirage-crypto', '0.10.2+llir'),
  ('nocrypto', '0.5.4-2+llir'),
  ('core', 'v0.14.1'),
  ('conf-libssl', '3+llir')
]

# Switches with root packages.
SWITCHES = {}
PACKAGES = {}
PINNED = {}

for arch, cpus in CPUS.items():
  SWITCHES[f'{arch}+ref'] = [
    f'ocaml-variants.4.11.1.master',
    f'arch-{arch}'
  ]
  PACKAGES[f'{arch}+ref'] = packages.CORE_PACKAGES
  PINNED[f'{arch}+ref'] = PINS

  SWITCHES[f'{arch}+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}'
  ]
  PACKAGES[f'{arch}+llir'] = packages.CORE_PACKAGES
  PINNED[f'{arch}+llir'] = PINS

  SWITCHES[f'{arch}+tezos+ref'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
    'rust'
  ]
  PACKAGES[f'{arch}+tezos+ref'] = packages.TEZOS_PACKAGES
  PINNED[f'{arch}+tezos+ref'] = PINS

  SWITCHES[f'{arch}+tezos+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
    'rust'
  ]
  PACKAGES[f'{arch}+tezos+llir'] = packages.TEZOS_PACKAGES
  PINNED[f'{arch}+tezos+llir'] = PINS

  for cfg, _ in CONFIG.items():
    SWITCHES[f'{arch}+ref+{cfg}'] = [
        f'ocaml-variants.4.11.1.master',
        f'arch-{arch}'
    ]

  for opt in OPT:
    SWITCHES[f'{arch}+llir+{opt}'] = [
        f'ocaml-variants.4.11.1.master+llir',
        f'arch-{arch}',
        f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+llir+{opt}'] = packages.CORE_PACKAGES
    PINNED[f'{arch}+llir+{opt}'] = PINS

    SWITCHES[f'{arch}+tezos+llir+{opt}'] = [
        f'ocaml-variants.4.11.1.master+llir',
        f'arch-{arch}',
        f'llir-config.{opt}',
        'rust'
    ]
    PACKAGES[f'{arch}+tezos+llir+{opt}'] = packages.TEZOS_PACKAGES
    PINNED[f'{arch}+tezos+llir+{opt}'] = PINS

    for cpu in cpus:
      SWITCHES[f'{arch}+llir+{opt}+{cpu}'] = [
          f'ocaml-variants.4.11.1.master+llir',
          f'arch-{arch}',
          f'llir-config.{opt}'
      ]
      PACKAGES[f'{arch}+llir+{opt}+{cfg}'] = packages.CORE_PACKAGES
      PINNED[f'{arch}+llir+{opt}+{cfg}'] = PINS

    for cfg, _ in CONFIG.items():
      SWITCHES[f'{arch}+llir+{opt}+{cfg}'] = [
          f'ocaml-variants.4.11.1.master+llir',
          f'arch-{arch}',
          f'llir-config.{opt}+{cfg}'
      ]
      PACKAGES[f'{arch}+llir+{opt}+{cfg}'] = packages.CORE_PACKAGES
      PINNED[f'{arch}+llir+{opt}+{cfg}'] = PINS

for arch in ['amd64', 'arm64']:
  SWITCHES[f'{arch}+mirage+ref'] = [
    f'ocaml-variants.4.11.1.master',
    f'arch-{arch}',
  ]
  PACKAGES[f'{arch}+mirage+ref'] = packages.MIRAGE_PACKAGES
  PINNED[f'{arch}+mirage+ref'] = PINS

  SWITCHES[f'{arch}+mirage+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
  ]
  PACKAGES[f'{arch}+mirage+llir'] = packages.MIRAGE_PACKAGES
  PINNED[f'{arch}+mirage+llir'] = PINS

  for opt in OPT:
    SWITCHES[f'{arch}+mirage+llir+{opt}'] = [
      f'ocaml-variants.4.11.1.master+llir',
      f'arch-{arch}',
      f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+mirage+llir+{opt}'] = packages.MIRAGE_PACKAGES
    PINNED[f'{arch}+mirage+llir+{opt}'] = PINS



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

CONFIG_TEMPLATE=\
'''
opam-version: "2.0"
maintainer: "n@ndor.email"
homepage: "https://github.com/nandor/llir-opt"
bug-reports: "https://github.com/nandor/llir-opam-repository/issues"
authors: ["Nandor Licker" "Timothy M. Jones"]
license: "MIT"
setenv: [[LLIR_OPT_O = "-{}"] {} ]
synopsis: "LLIR Configuration"
description: "This package overrides configuration options for llir-opt"
flags: conf
'''

def install(switches, repository, jb, test, apps):
  """Installs the switches and the required packages."""

  # Create the repository with custom LLIR configs.
  os.makedirs(os.path.join(ROOT, '_repo'), exist_ok=True)
  repo = os.path.join(ROOT, '_repo', 'repo')
  if not os.path.exists(repo):
    with open(repo, 'w') as f:
      f.write('opam-version: "2.0"')

  for opt in OPT:
    for cfg, envs in CONFIG.items():
      path = os.path.join(
          ROOT,
          '_repo',
          'packages',
          'llir-config',
          f'llir-config.{opt}+{cfg}'
      )
      os.makedirs(path, exist_ok=True)
      with open(os.path.join(path, 'opam'), 'w') as f:
        f.write(CONFIG_TEMPLATE.format(
          opt,
          ''.join(f'[{key} = "{val}"]' for key, val in envs.items())
        ))

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
      '--disable-sandboxing'
  ])

  # Create all the switches.
  for switch in switches:
    if switch not in opam(['switch', 'list'], capture=True):
      opam([
          'switch',
          'create',
          switch,
          '--yes',
          '--empty',
          '--repos',
          'config=file://{},llir={},default'.format(
              os.path.join(ROOT, '_repo'),
              repository
          )
      ])
  opam(['update'])

  # Pin LLIR packages.
  for switch in switches:
    for pkg, version in PINNED[switch]:
      opam([
          'pin',
          'add',
          pkg,
          version,
          '--switch={}'.format(switch),
          '--no-action'
      ])

  # Install the compilers.
  for switch in switches:
    opam([
        'install',
        '--switch={}'.format(switch),
        '-j', str(jb),
        '--yes'
    ] + (['--with-test'] if test else []) + SWITCHES[switch])

  if apps:
    # Install all packages.
    for switch in switches:
      if PACKAGES[switch]:
        opam(['switch', switch])
        opam(
            [
              'install',
             '--switch={}'.format(switch),
              '-j', str(jb),
              '--yes',
            ] + (['--with-test'] if test else []) + PACKAGES[switch],
            prefix=os.path.join(OPAMROOT, switch)
        )


def build(switches, jb, macro, micro):
  """Build all benchmarks."""
  switch = switches[0]
  for group in macro + micro:
    kind, target = group.target.split(':')
    if kind == 'opam':
      _dune(jb, switch, target)
      continue
    raise Exception('Unknown target: {}'.format(group.target))
