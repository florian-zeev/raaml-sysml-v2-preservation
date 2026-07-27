# Tooling adapters

Milestone 0 uses dependency-free Python 3.14.4 for orchestration and narrow
Java adapters over the pinned official SysML v2 Pilot Implementation
distribution.

The ignored cache layout after bootstrap is:

```text
tooling/cache/
├── sysml-0.59.0/sysml/
│   ├── jupyter-sysml-kernel-0.59.0-all.jar
│   └── sysml.library/
└── temurin-21/
    ├── Contents/Home/   # macOS arm64
    └── bin/             # Linux x86-64
```

Only the layout for the current platform is present in a given checkout.

Acquire and verify the locked archives and standards inputs, then bootstrap:

```text
./raaml sources fetch
./raaml sources verify
./raaml tooling bootstrap
```

`sources fetch` is the only command above that uses the network. The other
commands are offline. Existing files with the wrong size or hash are never
overwritten.

The adapter commands are:

```text
./raaml validate-v2 MODEL.sysml
./raaml validate-v1 MODEL.xmi
./raaml validate-ocl EXPRESSION.txt
./raaml tests milestone-0
```

They return zero only on success and write JSON diagnostics below
`reports/diagnostics/`. See ADRs 0003 through 0006 for the pinned versions,
validation meaning, UML namespace compatibility view, and XML security
boundary.
