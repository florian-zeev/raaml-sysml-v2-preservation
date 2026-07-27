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

## Documents

| Document | Purpose |
| --- | --- |
| [`proposal/community-proposal-v0.1.md`](proposal/community-proposal-v0.1.md) | Short formal proposal and claim boundary |
| [`proposal/normative-encoding-v0.1.md`](proposal/normative-encoding-v0.1.md) | Detailed preservation contract and mapping rules |
| [`docs/executive-summary.md`](docs/executive-summary.md) | Higher-level explanation |
| [`docs/reference-implementation-plan.md`](docs/reference-implementation-plan.md) | Evidence plan, milestones, and release gates |

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
