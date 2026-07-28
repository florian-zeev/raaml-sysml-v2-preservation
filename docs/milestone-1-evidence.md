# Milestone 1 evidence

**Status:** Passed

**Date:** 2026-07-28

**Evidence commit:** [`cc7714d2f06acaa990ee880a6e6cf52ea2fa2f73`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/cc7714d2f06acaa990ee880a6e6cf52ea2fa2f73)

**Clean-environment run:** [GitHub Actions run 30360860939](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30360860939)

## Result

Milestone 1 passed on macOS/arm64 and on the GitHub-hosted
`ubuntu-24.04` Linux/x86-64 runner. The canonical fact document produced on
the Linux host and inside the pinned, offline Linux container was
byte-identical.

The clean run:

- verified all 41 locked standards and tool artifacts;
- extracted raw and canonical facts from all 17 official RAAML 1.1 definition
  files;
- validated both fact documents against their versioned JSON Schemas;
- repeated extraction and required byte-identical output;
- matched production counts against the independent Expat-based corpus audit;
- checked manually reviewed golden records and category mutations;
- parsed and resolved all 33 source bodies labeled as OCL;
- ran 50 dependency-free unit and security tests;
- reran the complete gate inside the container with networking disabled;
- compared the host and container canonical fact documents byte for byte.

The workflow completed successfully in 2 minutes 54 seconds.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `cc7714d2f06acaa990ee880a6e6cf52ea2fa2f73` |
| Built image ID | `sha256:54a5f17a2affff3796a8377dee57153a91d2a3179eba88f68b2775a70eaff278` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container comparison | Byte-identical |
| OCL expressions parsed and resolved | `33` |

The image was not pushed to a registry. Verified third-party source and tool
archives were mounted read-only and were not included in the image.

## Frozen corpus counts

| Fact category | Count |
| --- | ---: |
| Profiles | 9 |
| Packages | 15 |
| Stereotypes | 94 |
| Classes | 143 |
| Enumerations | 5 |
| Enumeration literals | 35 |
| Associations | 40 |
| AssociationClasses | 1 |
| Properties | 267 |
| Ports | 65 |
| Connectors | 94 |
| Constraints | 60 |
| Extensions | 84 |
| Extension ends | 84 |
| Comments | 431 |
| Images | 22 |
| RAAML stereotype applications | 108 |

Counts are only one part of the evidence. The frozen baseline also contains
concrete relationships, ordered values, identities, external targets, and
representative records for ports, connectors, icons, comments, machinery,
stereotype applications, and ordinary associations.

## What this proves

Milestone 1 defines an executable preservation contract for the 17 official
RAAML 1.1 definition files. It proves that the locked source corpus can be
extracted into schema-valid, deterministic canonical facts and checked against
an independent audit, manually reviewed examples, negative mutations, and a
pinned OCL parser.

It also establishes stable source identities without depending on original
MagicDraw XMI IDs. In particular, the two `ClientIsSituation` constraints
remain distinct by owner, and all 40 ordinary associations have distinct
canonical identities.

## What this does not prove

No forward SysML v1-to-v2 transformation or reverse transformation has been
implemented. This milestone therefore does not prove that RAAML survives a
SysML v2 round trip.

The OCL gate proves parsing and AST-based name resolution in the source
namespace. It does not evaluate the constraints, reproduce the full UML static
type system, or prove behavioral equivalence across OCL engines.

The clean run is independent of the maintainer's local environment, but it is
not yet an independent reproduction by another person or organization.
