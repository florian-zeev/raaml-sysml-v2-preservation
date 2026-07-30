# RAAML 1.1 on SysML v2 preservation project

This repository develops and tests a community proposal for carrying the
official RAAML 1.1 definitions through SysML v2 without losing a defined set
of source facts.

The project is deliberately narrower than RAAML 2.0. Version 0.1 covers the
17 official RAAML 1.1 profile and library definition files. It does not claim
support for arbitrary user-authored RAAML models.

## Current status

**Draft Community Proposal v0.1. Milestone 6 now demonstrates exact canonical
fact equality across the full 17-file round trip, zero errors from both
mandatory validators, and 36 passing adversarial cases. The Linux host and
offline container produced byte-identical reports.**

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

Milestone 2 passed on 2026-07-29. The repository now has a complete,
machine-checkable transformation matrix with 35 resolved rows and no open
mapping decisions. It classifies all 267 UML Properties and all 60 constraint
OpaqueExpressions, validates the selected SysML v2 textual carriers, and
reproduces the analysis byte for byte on the Linux host and in the offline
container at commit `5a2bef4`. This closes the transformation design analysis;
it still does not demonstrate a SysML v2 round trip.

Milestone 3 passed on 2026-07-29. The thin slice covers all Core and General
definitions plus selected STPA definitions and a normative library
application. The Linux host and offline container generated and validated the
same SysML v2 view, reconstructed and loaded six v1 XMI artifacts, and found
zero canonical fact differences at commit `29018cf`.

Milestone 4 passed on 2026-07-29. It generates one parser-valid SysML v2
corpus model containing all 283 in-scope declarations and 60 constraint
carriers, plus one schema-valid preservation manifest for each of the 17
source files. The Linux host and offline container produced byte-identical
evidence, and the mandatory validator reported zero errors in all five
validation categories at commit `5f3131c`.

Milestone 5 passed on 2026-07-29. It reconstructs all 17 v1 profile and
library artifacts deterministically, preserves multi-package artifact
structure, and loads every rebuilt artifact in the mandatory pinned v1
environment with zero required validation errors. Its injected fake-hash
test proves that an ID collision stops reconstruction before partial output
is written. The Linux host and offline container produced byte-identical
evidence at commit `bb4098a`.

Milestone 6 passed on 2026-07-30. It compares every canonical fact category
across every source and reconstructed artifact, reports zero differences,
and passes 36 explicit positive and negative adversarial cases. The Linux
host and offline container produced byte-identical conformance and complete
comparison reports at commit `81791c6`.

Milestone 7 passed on 2026-07-30. The `reproduce` command builds a
checksummed release directory containing the complete generated corpus,
reconstructed artifacts, reports, controlled one-fact diff, and validated
STPA walkthrough. The host and offline container produced byte-identical
49-file release directories at commit `3e2bb9f`, which is bound by the signed
candidate tag `v0.9.0-rc.1`.

## Foundation and transformation-analysis quick start

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
./raaml tests milestone-3
./raaml tests milestone-4
./raaml tests milestone-5
./raaml tests milestone-6
./raaml reproduce --clean \
  --container-digest sha256:<container-image-id> \
  --release-tag v0.9.0-rc.1
./raaml transformation surface
./raaml transformation properties
./raaml transformation constraints
./raaml transformation audit --require-resolved
./raaml validate-v2 fixtures/milestone-0/minimal-valid.sysml
./raaml validate-v2 fixtures/milestone-2/resolved-carriers.sysml
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
| [`docs/milestone-2-evidence.md`](docs/milestone-2-evidence.md) | Frozen transformation-analysis and reproducibility evidence |
| [`docs/milestone-2-transformation-analysis.md`](docs/milestone-2-transformation-analysis.md) | Resolved comparison with the official SysML v1-to-v2 transformation |
| [`docs/milestone-3-vertical-slice.md`](docs/milestone-3-vertical-slice.md) | Scope, pipeline, local result, and claim boundary for the thin vertical slice |
| [`docs/milestone-4-full-corpus.md`](docs/milestone-4-full-corpus.md) | Full-corpus generation, per-source manifests, validation evidence, and claim boundary |
| [`docs/milestone-4-evidence.md`](docs/milestone-4-evidence.md) | Frozen clean-environment evidence and claim boundary for full-corpus v2 generation |
| [`docs/milestone-5-reverse-mapping.md`](docs/milestone-5-reverse-mapping.md) | Full-corpus v1 reconstruction, stable-ID collision gate, loader evidence, and claim boundary |
| [`docs/milestone-6-conformance.md`](docs/milestone-6-conformance.md) | Full-corpus fact equality, adversarial coverage, reports, and claim boundary |
| [`docs/milestone-6-evidence.md`](docs/milestone-6-evidence.md) | Frozen clean-environment evidence and claim boundary for full-corpus conformance |
| [`docs/milestone-7-reproducibility.md`](docs/milestone-7-reproducibility.md) | Deterministic release directory, controlled diff, STPA walkthrough, and signed-tag boundary |
| [`docs/milestone-7-evidence.md`](docs/milestone-7-evidence.md) | Frozen clean-environment, checksum, container, and signed-tag evidence |
| [`analysis/corpus-transformation-surface-v0.1.json`](analysis/corpus-transformation-surface-v0.1.json) | Reproducible inventory of SysML v1 applications that select specialized transformation rules |
| [`analysis/property-transformation-surface-v0.1.json`](analysis/property-transformation-surface-v0.1.json) | Total official-rule classification of all 267 UML Properties |
| [`analysis/constraint-transformation-surface-v0.1.json`](analysis/constraint-transformation-surface-v0.1.json) | Total split of all 60 constraint OpaqueExpressions by official mapping fidelity |
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
