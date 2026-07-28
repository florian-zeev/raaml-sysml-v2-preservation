# ADR 0005: OCL parsing

**Status:** Accepted and implemented for Milestones 0 and 1

**Date:** 2026-07-27

## Decision

Use Eclipse OCL Classic Ecore `3.22.0.v20240902-1518`, bundled in the pinned
validator distribution, for OCL parsing and AST traversal.

The adapter parses in a typed Ecore context and obtains referenced classifiers,
properties, operations, and iterators from the OCL AST. It does not use regular
expressions to infer names. The Milestone 0 fixture exercises navigation,
`allInstances()`, and `closure(...)`; a malformed expression must fail.

For the official corpus, the adapter constructs a parser scaffold from the
extracted declaration and property names. The Python validation layer then
checks every type and property reported by the AST against the independently
constructed source catalog. Missing and ambiguous type names and missing
property names are errors.

This proves that each stored OCL expression parses and that the type and
property names surfaced by AST traversal resolve in the extracted source
namespace. The scaffold does not reproduce the complete UML type system, so
this gate does not prove static type conformance, evaluation results, or
behavioral equivalence.

Version 0.1 parses and resolves names but does not evaluate constraints or
claim behavioral equivalence between OCL engines. RAAML source strings labeled
`OCL`, `OCL2.0`, or equivalent remain verbatim preserved facts.

## Consequences

- Milestone 1 validates all 33 source bodies labeled as OCL. The other 26
  stored bodies are labeled JavaScript and remain preserved facts rather than
  OCL parser inputs.
- Parser acceptance is reported separately from evaluation, which is not part
  of v0.1 conformance.

## Verification

```text
./raaml validate-ocl fixtures/milestone-0/ocl-valid.txt
./raaml validate-ocl fixtures/milestone-0/ocl-invalid.txt
./raaml validate-ocl --all
```
