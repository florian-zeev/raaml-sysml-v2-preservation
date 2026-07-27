# Contributing

This project welcomes technical review and implementation contributions.

## Current phase

The project is in the design and evidence-planning phase. Before production
mapping code begins, Milestone 0 in
[`docs/reference-implementation-plan.md`](docs/reference-implementation-plan.md)
must establish the pinned standards, validators, OCL parser, source policy,
secure XML behavior, and reproducible toolchain.

## Contribution rules

- Keep the project independent of M45 product code and infrastructure.
- Do not commit official OMG files or other third-party material unless the
  repository documents permission to redistribute the exact material.
- Do not broaden the conformance claim beyond the 17 named RAAML 1.1
  definition files without a versioned proposal change.
- Add or update tests when changing a schema, preservation rule, identity
  rule, or transformation rule.
- Keep generated outputs deterministic.
- Record important technical decisions in `adr/`.
- Use US spelling in project documentation.

Contributions are accepted under the license that applies to the modified
file. By submitting a contribution, you confirm that you have the right to
provide it under that license.
