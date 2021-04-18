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
  'i686': [],
  'amd64': ['zen2', 'skylake', 'tremont'],
  'arm64': ['cortex-a72'],
  'riscv': ['sifive-u74'],
  'power': ['pwr8', 'pwr9']
}

# Enumeration of opt levels.
OPT = ['O0', 'O1', 'O2', 'O3', 'O4', 'Os']

# List of all packages to install.
CORE_PACKAGES=[
  "alcotest", "alt-ergo-free", "angstrom", "atdgen", "atdj", "atds", "base",
  "base64", "bheap", "bigstringaf", "biniou", "bos", "camlp4", "camlp5",
  "camlzip", "cmitomli", "compcert", "coq=8.13.0+llir", "cpdf", "cppo", "crowbar", 
  "csexp",
  "cstruct", "cstruct-sexp", "cstruct-unix", "cubicle", "digestif", "diy",
  "domain-name", "dune", "duration", "easy-format", "eqaf", "fix", "frama-c",
  "fraplib", "gmp", "hevea", "hxd", "io-page", "ipaddr", "irmin-test",
  "js_of_ocaml", "jsonm", "lru", "macaddr", "menhir",
  "metrics-unix", "minilight", "nbcodec", "num", "ocaml-syntax-shims",
  "ocamlformat", "ocamlgraph", "ocamlmod",
  "odoc", "ounit2", "ptime", "randomconv", "re", "react", "reason", "result",
  "rml", "sexplib", "sexplib0", "stdio", "stringext", "tyxml", "ucaml",  "uri",
  "uucp",  "uuidm", "why3", "yojson", "zarith", "zlib", "irmin", "index",
  "repr", "memtrace", "irmin-pack>=2.4.0",
  "ppx_deriving_yojson", "ppx_repr",
  "ocplib-endian", "ocplib-simplex",
  "lwt", "lwt-dllist", "hacl", "hacl-star", "sodium"
]

# List of mirage-specific packages.
MIRAGE_PACKAGES=[
  "alcotest", "arp", "asn1-combinators", "astring", "benchmark", "bheap",
  "bigarray-compat", "charrua", "charrua-server", "charrua-unix",
  "conduit", "conduit-mirage", "conf-pkg-config", "cstruct", "crunch",
  "cstruct-sexp", "cstruct-unix", "diet", "dns", "dns-client", "domain-name",
  "dune", "dune-configurator", "duration", "eqaf", "ethernet", "fiat-p256",
  "fmt", "functoria", "functoria-runtime", "hex", "hkdf", "io-page", "ipaddr",
  "ipaddr-cstruct", "ipaddr-sexp", "ke", "libseccomp", "logs", "lru",
  "lwt", "lwt-dllist", "lwt-canceler", "lwt-watcher", "lwt-exit",
  "macaddr", "macaddr-cstruct", "macaddr-sexp", "magic-mime",
  "mirage", "mirage-block", "mirage-block-unix", "mirage-bootvar-unix",
  "mirage-channel", "mirage-clock", "mirage-clock-unix", "mirage-console",
  "mirage-console-unix", "mirage-crypto", "mirage-device", "mirage-flow",
  "mirage-fs", "mirage-kv", "mirage-kv-mem", "mirage-logs", "mirage-net",
  "mirage-net-unix", "mirage-profile", "mirage-protocols", "mirage-random",
  "mirage-random-test", "mirage-runtime", "mirage-stack", "mirage-time",
  "mirage-time-unix", "mirage-types", "mirage-types-lwt", "mirage-vnetif",
  "opam-depext", "ounit", "parse-argv", "pcap-format", "ptime",
  "randomconv", "rresult", "sexplib", "shared-memory-ring",
  "shared-memory-ring-lwt", "stdlib-shims", "solo5-bindings-hvt", "tcpip",
  "tuntap", "vchan", "xenstore", "yojson", "gmp-freestanding",
  "zarith-freestanding", "mirage-crypto-pk", "cohttp", "cohttp-mirage",
  "dns", "irmin-pack", "irmin-mem", "memtrace", "react",
  "irmin-layers",
  "resto-directory", "resto-cohttp-server", "resto-cohttp-client",
  "resto-cohttp-self-serving-client", "ocp-ocamlres",
]

# List of tezos-specific packages.
TEZOS_PACKAGES=[
  "irmin-layers", "irmin-pack=2.4.0", "result",
  "resto-directory", "resto-cohttp-server", "resto-cohttp-client",
  "resto-cohttp-self-serving-client", "ocp-ocamlres",
  "hacl-star",
  "ff=0.4.0",
  "ppx_inline_test", "ppx_cstruct", "ppx_repr",
  "data-encoding", "ezjsonm", "ringo", "secp256k1-internal",
  "tar-unix", "camlzip", "rust",
  "lwt-exit", "lwt-canceler", "lwt-watcher",  "lwt_log", "lwt-watcher",
  "tls=0.11.1",
  "librustzcash",
  "sodium",
  "ocaml-vec"
]

# Pinned packages.
CORE_PINNED=[
  ('zarith', '1.12+llir'),
  ('zarith-freestanding', '1.12+llir'),
  ('mirage-crypto', '0.9.0+llir'),
  ('nocrypto', '0.5.4-2+llir'),
  ('core', 'v0.14.1')
]
MIRAGE_PINNED=[
  ('zarith', '1.12+llir'),
  ('zarith-freestanding', '1.12+llir'),
  ('mirage-crypto', '0.9.0+llir'),
  ('nocrypto', '0.5.4-2+llir'),
  ('core', 'v0.14.1')
]
TEZOS_PINNED=[
  ('zarith', '1.12+llir'),
  ('zarith-freestanding', '1.12+llir'),
  ('mirage-crypto', '0.8.0+llir'),
  ('nocrypto', '0.5.4-2+llir'),
  ('core', 'v0.14.1')
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
  PACKAGES[f'{arch}+ref'] = CORE_PACKAGES
  PINNED[f'{arch}+ref'] = CORE_PINNED

  SWITCHES[f'{arch}+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}'
  ]
  PACKAGES[f'{arch}+llir'] = CORE_PACKAGES
  PINNED[f'{arch}+llir'] = CORE_PINNED

  SWITCHES[f'{arch}+tezos+ref'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
    'rust'
  ]
  PACKAGES[f'{arch}+tezos+ref'] = TEZOS_PACKAGES
  PINNED[f'{arch}+tezos+ref'] = TEZOS_PINNED

  SWITCHES[f'{arch}+tezos+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
    'rust'
  ]
  PACKAGES[f'{arch}+tezos+llir'] = TEZOS_PACKAGES
  PINNED[f'{arch}+tezos+llir'] = TEZOS_PINNED

  for opt in OPT:
    SWITCHES[f'{arch}+llir+{opt}'] = [
        f'ocaml-variants.4.11.1.master+llir',
        f'arch-{arch}',
        f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+llir+{opt}'] = CORE_PACKAGES
    PINNED[f'{arch}+llir+{opt}'] = CORE_PINNED

    SWITCHES[f'{arch}+tezos+llir+{opt}'] = [
        f'ocaml-variants.4.11.1.master+llir',
        f'arch-{arch}',
        f'llir-config.{opt}',
        'rust'
    ]
    PACKAGES[f'{arch}+tezos+llir+{opt}'] = TEZOS_PACKAGES
    PINNED[f'{arch}+tezos+llir+{opt}'] = TEZOS_PINNED

    for cpu in cpus:
      SWITCHES[f'{arch}+llir+{opt}+{cpu}'] = [
          f'ocaml-variants.4.11.1.master+llir',
          f'arch-{arch}',
          f'llir-config.{opt}'
      ]

for arch in ['amd64', 'arm64']:
  SWITCHES[f'{arch}+mirage+ref'] = [
    f'ocaml-variants.4.11.1.master',
    f'arch-{arch}',
  ]
  PACKAGES[f'{arch}+mirage+ref'] = MIRAGE_PACKAGES
  PINNED[f'{arch}+mirage+ref'] = MIRAGE_PINNED

  SWITCHES[f'{arch}+mirage+llir'] = [
    f'ocaml-variants.4.11.1.master+llir',
    f'arch-{arch}',
  ]
  PACKAGES[f'{arch}+mirage+llir'] = MIRAGE_PACKAGES
  PINNED[f'{arch}+mirage+llir'] = MIRAGE_PINNED

  for opt in OPT:
    SWITCHES[f'{arch}+mirage+llir+{opt}'] = [
      f'ocaml-variants.4.11.1.master+llir',
      f'arch-{arch}',
      f'llir-config.{opt}'
    ]
    PACKAGES[f'{arch}+mirage+llir+{opt}'] = MIRAGE_PACKAGES
    PINNED[f'{arch}+mirage+llir+{opt}'] = MIRAGE_PINNED



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


def install(switches, repository, jb, test, apps):
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
          '--repos', 'llir={},default'.format(repository)
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
