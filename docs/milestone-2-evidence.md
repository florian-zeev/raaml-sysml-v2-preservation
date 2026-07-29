# Milestone 2 evidence

**Status:** Passed

**Date:** 2026-07-29

**Evidence commit:** [`5a2bef457a01335c0223f6d63c136df5a26a3397`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/5a2bef457a01335c0223f6d63c136df5a26a3397)

**Clean-environment run:** [GitHub Actions run 30375042025](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30375042025)

## Result

Milestone 2 passed on the GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.
The host and the pinned, offline Linux container produced byte-identical
transformation-surface reports.

The clean run:

- verified all 41 locked standards and tool artifacts;
- audited every machine-rule citation against the pinned official SysML
  v1-to-v2 transformation model;
- required all 35 rows in the version 0.1 transformation matrix to be
  resolved;
- classified all 263 root-level SysML v1 stereotype applications that select
  specialized transformation rules;
- classified all 267 UML Properties;
- classified all 60 constraint OpaqueExpressions;
- validated the selected metadata, occurrence, part, constraint, and
  enumeration carriers with the pinned SysML v2 implementation;
- ran 72 dependency-free unit and security tests;
- repeated the complete gate inside the container with networking disabled;
- compared the host and container transformation reports byte for byte.

The workflow completed successfully in 3 minutes 38 seconds.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `5a2bef457a01335c0223f6d63c136df5a26a3397` |
| Built image ID | `sha256:b860b75cf12e9450718c326a35264688be901ac5ea5e3430eb1aa757f472d459` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container report comparison | Byte-identical |
| Transformation matrix rows | `35` |
| Open transformation rows | `0` |
| Properties classified | `267` |
| Constraint OpaqueExpressions classified | `60` |
| OCL expressions parsed and resolved | `33` |

The image was not pushed to a registry. Verified third-party source and tool
archives were mounted read-only and were not included in the image.

## Frozen mapping decisions

Milestone 2 resolves the target carrier and preservation behavior for every
construct exercised by the official RAAML 1.1 definition corpus. Most rows
reuse or specialize the official SysML v1-to-v2 transformation and supplement
it with source facts needed for reversal.

Two deliberate deviations are explicit:

- A UML Enumeration with SysML v1 ValueType applied uses an
  `EnumerationDefinition`, preserving the ordered literals and recording the
  ValueType application for reversal.
- The unlabeled FMEALib `RPNCalculation` expression is preserved without
  inventing a language or claiming a faithful native textual representation.

The normative details, official clauses, machine-rule identities, reasons,
and test obligations are in
`analysis/transformation-matrix-v0.1.json` and
`docs/milestone-2-transformation-analysis.md`.

## What this proves

Milestone 2 proves that version 0.1 has a complete and reproducible design for
mapping the in-scope official RAAML definitions onto validated SysML v2
carriers while retaining the additional facts required by the preservation
contract. The automated audit fails if a row is open or a cited official
machine rule is absent.

It also proves that the corpus-wide transformation inventory and the complete
Property and constraint classifications are deterministic across the Linux
host and the offline container.

## What this does not prove

The forward mapper and reverse reconstructor have not yet demonstrated a
round trip. Milestone 2 resolves what they must do; the later implementation
and comparison milestones must prove that they do it.

The selected native SysML v2 carriers do not by themselves prove behavioral
equivalence of OCL or JavaScript constraints. The authoritative preservation
record retains the source expressions, languages, ownership, and reviewable
diagnostics.

The clean run is independent of the maintainer's local environment, but it is
not yet an independent reproduction by another person or organization.
