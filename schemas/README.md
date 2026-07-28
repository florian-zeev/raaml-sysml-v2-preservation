# Schemas

All schemas use JSON Schema draft 2020-12 and reject undeclared fields.

- `raw-raaml-facts.schema.json` defines the source-shaped extraction surface.
- `canonical-raaml-facts.schema.json` defines the deterministic comparison
  surface after identity construction and reference resolution.
- `diagnostics.schema.json` defines command diagnostics.
- `standards-lock.schema.json` defines the pinned source/tool lock.

The fact schemas implement
[`docs/milestone-1-fact-contract.md`](../docs/milestone-1-fact-contract.md).
They are part of the conformance contract, not merely documentation for one
extractor.
