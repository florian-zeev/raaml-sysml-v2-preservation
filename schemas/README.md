# Schemas

All schemas use JSON Schema draft 2020-12 and reject undeclared fields.

- `raw-raaml-facts.schema.json` defines the source-shaped extraction surface.
- `canonical-raaml-facts.schema.json` defines the deterministic comparison
  surface after identity construction and reference resolution.
- `diagnostics.schema.json` defines command diagnostics.
- `standards-lock.schema.json` defines the pinned source/tool lock.
- `corpus-transformation-surface.schema.json` defines the SysML v1
  applications that select specialized official transformation rules.
- `property-transformation-surface.schema.json` defines the total,
  mutually exclusive official-rule classification of all corpus Properties.
- `constraint-transformation-surface.schema.json` defines the split between
  labeled and unlabeled constraint OpaqueExpressions.
- `transformation-matrix.schema.json` defines the reproducible Milestone 2
  comparison with the official SysML v1-to-v2 transformation.
- `preservation-manifest.schema.json` defines the integrity-protected
  Milestone 3 slice payload and the per-source Milestone 4 full-corpus
  payloads carried alongside the native v2 view.
- `roundtrip-report.schema.json` defines the machine-readable before/after
  canonical fact comparison.
- `milestone-4-build-report.schema.json` defines the deterministic
  full-corpus generation, manifest, validator, and interoperability evidence.
- `milestone-5-build-report.schema.json` defines deterministic full-corpus
  v1 reconstruction, stable-ID policy, collision rejection, and v1 loader
  evidence.

The fact schemas implement
[`docs/milestone-1-fact-contract.md`](../docs/milestone-1-fact-contract.md).
They are part of the conformance contract, not merely documentation for one
extractor.
