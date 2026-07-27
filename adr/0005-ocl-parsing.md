# ADR 0005: OCL parsing

**Status:** Accepted for Milestone 0; full-corpus resolution remains Milestone 1
**Date:** 2026-07-27

## Decision

Use Eclipse OCL Classic Ecore `3.22.0.v20240902-1518`, bundled in the pinned
validator distribution, for OCL parsing and AST traversal.

The adapter parses in a typed context and obtains referenced classifiers,
properties, operations, and iterators from the OCL AST. It does not use regular
expressions to infer names. The Milestone 0 fixture exercises navigation,
`allInstances()`, and `closure(...)`; a malformed expression must fail.

Version 0.1 parses and resolves names but does not evaluate constraints or
claim behavioral equivalence between OCL engines. RAAML source strings labeled
`OCL`, `OCL2.0`, or equivalent remain verbatim preserved facts.

## Consequences

- Milestone 1 must construct each real owning namespace and prove that every
  required name from every official expression resolves.
- Parser acceptance is reported separately from evaluation, which is not part
  of v0.1 conformance.

## Verification

```text
./raaml validate-ocl fixtures/milestone-0/ocl-valid.txt
./raaml validate-ocl fixtures/milestone-0/ocl-invalid.txt
```
