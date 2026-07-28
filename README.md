# RAAML 1.1 on SysML v2 preservation project

This repository develops and tests a community proposal for carrying the
official RAAML 1.1 definitions through SysML v2 without losing a defined set
of source facts.

The project is deliberately narrower than RAAML 2.0. Version 0.1 covers the
17 official RAAML 1.1 profile and library definition files. It does not claim
support for arbitrary user-authored RAAML models.

## Current status

**Draft Community Proposal v0.1. No fact-preserving transformation has yet
been demonstrated.**

The implementation may claim a fact-preserving round trip only after the
validation and publication gates in the reference implementation plan pass.

Milestone 0 passed on 2026-07-27. The repository
verifies the 17 official RAAML definition files and the complete standards
baseline, loads `CoreRAAML.xmi` and `CoreRAAMLLib.xmi` through a pinned UML
environment, parses representative OCL through an AST, and validates paired
positive/negative SysML v2 fixtures. The clean Linux and offline,
digest-pinned-container gates passed for commit `77cfaff`. This is toolchain
evidence, not transformation evidence.

Milestone 1 passed on 2026-07-28. The repository now has versioned raw and
canonical fact schemas, deterministic extraction from all 17 official
definition files, an independent corpus audit, concrete golden records and
mutation tests, and full-corpus OCL parsing and source-name resolution. The
Linux host and offline container produced byte-identical canonical facts at
commit `cc7714d`. This establishes the source baseline; it still does not
demonstrate a SysML v2 round trip.

## Foundation and fact-baseline quick start

Python 3.14.4 is the tested orchestration runtime. On macOS Apple silicon:

```text
./raaml sources fetch
./raaml sources verify
./raaml tooling bootstrap
./raaml tests unit
./raaml tests milestone-0
./raaml facts extract --all --check-determinism
./raaml oracle audit --all
./raaml validate-ocl --all
./raaml tests milestone-1
./raaml transformation surface
./raaml transformation properties
./raaml transformation audit
./raaml validate-v2 fixtures/milestone-0/minimal-valid.sysml
./raaml validate-v1 sources/cache/CoreRAAML.xmi
./raaml validate-v1 sources/cache/CoreRAAMLLib.xmi
./raaml validate-ocl fixtures/milestone-0/ocl-valid.txt
```

Only `sources fetch` uses the network. Third-party inputs and tool binaries
remain ignored. See the ADRs for exact versions and known limitations.

## Documents

| Document | Purpose |
| --- | --- |
| [`proposal/community-proposal-v0.1.md`](proposal/community-proposal-v0.1.md) | Short formal proposal and claim boundary |
| [`proposal/normative-encoding-v0.1.md`](proposal/normative-encoding-v0.1.md) | Detailed preservation contract and mapping rules |
| [`docs/executive-summary.md`](docs/executive-summary.md) | Higher-level explanation |
| [`docs/reference-implementation-plan.md`](docs/reference-implementation-plan.md) | Evidence plan, milestones, and release gates |
| [`docs/milestone-0-evidence.md`](docs/milestone-0-evidence.md) | Frozen foundation evidence and claim boundary |
| [`docs/milestone-1-evidence.md`](docs/milestone-1-evidence.md) | Frozen source-fact baseline and reproducibility evidence |
| [`docs/milestone-1-coverage.md`](docs/milestone-1-coverage.md) | Fact-category coverage, golden examples, and negative cases |
| [`docs/milestone-2-transformation-analysis.md`](docs/milestone-2-transformation-analysis.md) | In-progress comparison with the official SysML v1-to-v2 transformation |
| [`analysis/corpus-transformation-surface-v0.1.json`](analysis/corpus-transformation-surface-v0.1.json) | Reproducible inventory of SysML v1 applications that select specialized transformation rules |
| [`analysis/property-transformation-surface-v0.1.json`](analysis/property-transformation-surface-v0.1.json) | Total official-rule classification of all 267 UML Properties |
| [`analysis/transformation-matrix-v0.1.json`](analysis/transformation-matrix-v0.1.json) | Machine-checkable rule classifications, citations, and test obligations |

## Repository boundary

This is a standalone community project. It must not depend on M45 product
code, databases, authentication, or deployment infrastructure. Its public
boundary will be a deterministic command-line interface operating on files
and producing SysML v2 text, JSON preservation records, reconstructed XMI,
structured diagnostics, and conformance reports.

Other products may consume versioned releases of the command-line tool or its
published artifacts without becoming part of this repository.

## Source material

Official OMG specifications, XMI files, icons, and other third-party material
are not licensed by this repository. They are not committed here unless a
separate rights review permits redistribution. See
[`THIRD_PARTY_MATERIALS.md`](THIRD_PARTY_MATERIALS.md) and
[`sources/README.md`](sources/README.md).

## Licensing

Original software is intended to be licensed under Apache-2.0. Original
proposal text, documentation, and schemas are intended to be licensed under
CC-BY-4.0. Third-party material is excluded. See [`LICENSE`](LICENSE) and
[`NOTICE`](NOTICE).
