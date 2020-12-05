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

# Enumeration of opt levels.
OPT = ['O0', 'O1', 'O2', 'O3', 'O4']

# List of all packages to install.
CORE_PACKAGES=[
  "alcotest", "alt-ergo-free", "angstrom", "atdgen", "atdj", "atds", "base",
  "base64", "bheap", "bigstringaf", "biniou", "bos", "camlp4", "camlp5",
  "camlzip", "cmitomli", "compcert", "coq", "cpdf", "cppo", "crowbar", "csexp",
  "cstruct", "cstruct-sexp", "cstruct-unix", "cubicle", "digestif", "diy",
  "domain-name", "dune", "duration", "easy-format", "eqaf", "fix", "frama-c",
  "fraplib", "gmp", "hevea", "hxd", "io-page", "ipaddr", "irmin", "irmin-mem",
  "irmin-test", "js_of_ocaml", "jsonm", "lru", "lwt", "lwt-dllist", "macaddr",
  "menhir", "metrics-unix", "minilight", "nbcodec", "num", "ocaml-syntax-shims",
  "ocamlformat", "ocamlgraph", "ocamlmod", "ocplib-endian", "ocplib-simplex",
  "odoc", "ounit2", "pcap-format", "ppx_cstruct", "ppx_deriving", "ppx_tools",
  "ppxfind", "ppxlib", "ptime", "randomconv", "re", "react", "reanalyze",
  "reason", "result", "rml", "sexplib", "sexplib0", "stdio", "stringext",
  "tcpip","tuntap", "tyxml", "ucaml", "uri", "uucp", "uuidm", "why3",
  "xenstore", "yojson", "zarith", "zlib",
]

# List of mirage-specific packages.
MIRAGE_PACKAGES=[
  "alcotest", "arp", "asn1-combinators", "astring", "benchmark", "bheap",
  "bigarray-compat", "charrua", "charrua-server", "charrua-unix",
  "conduit", "conduit-mirage", "conf-pkg-config", "cstruct", "crunch",
  "cstruct-sexp", "cstruct-unix", "diet", "dns", "dns-client", "domain-name",
  "dune", "dune-configurator", "duration", "eqaf", "ethernet", "fiat-p256",
  "fmt", "functoria", "functoria-runtime", "hex", "hkdf", "io-page", "ipaddr",
  "ipaddr-cstruct", "ipaddr-sexp", "ke", "libseccomp", "logs", "lru", "lwt",
  "lwt-dllist", "macaddr", "macaddr-cstruct", "macaddr-sexp", "magic-mime",
  "mirage", "mirage-block", "mirage-block-unix", "mirage-bootvar-unix",
  "mirage-channel", "mirage-clock", "mirage-clock-unix", "mirage-console",
  "mirage-console-unix", "mirage-crypto", "mirage-device", "mirage-flow",
  "mirage-fs", "mirage-kv", "mirage-kv-mem", "mirage-logs", "mirage-net", 
  "mirage-net-unix", "mirage-profile", "mirage-protocols", "mirage-random", 
  "mirage-random-test", "mirage-runtime", "mirage-stack", "mirage-time", 
  "mirage-time-unix", "mirage-types", "mirage-types-lwt", "mirage-vnetif", 
  "opam-depext", "ounit", "parse-argv", "pcap-format", "ppx_cstruct", "ptime", 
  "randomconv", "rresult", "sexplib", "shared-memory-ring", 
  "shared-memory-ring-lwt", "stdlib-shims", "tcpip", "tuntap", "vchan", 
  "xenstore", "yojson"
]

# Switches with root packages.
SWITCHES = {}
PACKAGES = {}

for arch, cpus in CPUS.items():
  SWITCHES[f'{arch}+ref'] = [f'ocaml-variants-{arch}.4.11.1.master']
  PACKAGES[f'{arch}+ref'] = CORE_PACKAGES
  SWITCHES[f'{arch}+llir'] = [f'ocaml-variants-{arch}.4.11.1.master+llir']
  PACKAGES[f'{arch}+llir'] = CORE_PACKAGES
  for opt in OPT:
    SWITCHES[f'{arch}+llir+{opt}'] = [
        f'ocaml-variants-{arch}.4.11.1.master+llir',
        f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+llir+{opt}'] = CORE_PACKAGES
    for cpu in cpus:
      SWITCHES[f'{arch}+llir+{opt}+{cpu}'] = [
          f'ocaml-variants-{arch}.4.11.1.master+llir',
          f'llir-config.{opt}+{cpu}'
      ]

for arch in ['x86_64']:
  SWITCHES[f'{arch}+mirage+ref'] = [
    f'ocaml-variants-{arch}.4.11.1.master'
  ]
  PACKAGES[f'{arch}+mirage+ref'] = MIRAGE_PACKAGES

  SWITCHES[f'{arch}+mirage+llir'] = [
    f'ocaml-variants-{arch}.4.11.1.master+llir'
  ]
  PACKAGES[f'{arch}+mirage+llir'] = MIRAGE_PACKAGES

  for opt in OPT:
    SWITCHES[f'{arch}+mirage+llir+{opt}'] = [
      f'ocaml-variants-{arch}.4.11.1.master+llir',
      f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+mirage+llir+{opt}'] = MIRAGE_PACKAGES



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
        ] + (['--with-test'] if test else []) + PACKAGES[switch],
        prefix=os.path.join(OPAMROOT, switch)
    )

  # Build all benchmarks.
  switch = switches[0]
  _dune(jb, switch, '@build_macro')
  _dune(jb, switch, '@build_micro')
  _dune(jb, switch, '@build_compcert')
  _dune(jb, switch, '@build_frama_c')
