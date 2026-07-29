# Milestone 4 full SysML v2 corpus

**Status:** Passes locally; clean Linux/container run pending

**Date started:** 2026-07-29

## Purpose

Milestone 4 expands the validated Milestone 3 mechanism from a six-artifact
vertical slice to all 17 official RAAML 1.1 profile and library definition
files.

The output is one deterministic SysML v2 corpus model and one
integrity-protected preservation manifest for each source file. Keeping one
manifest per source artifact avoids treating the 17 files as one anonymous
blob and gives the reverse mapper a defined source boundary for Milestone 5.

## Generated output

```text
generated/milestone-4/forward/
├── raaml-full-corpus.sysml
└── manifests/
    ├── CoreRAAML.preservation.json
    ├── CoreRAAMLLib.preservation.json
    └── ...15 more manifests
```

The generated SysML v2 model contains:

- 94 RAAML stereotype metadata definitions;
- 143 library occurrence definitions;
- 40 ordinary association connection definitions;
- one association-class connection definition;
- five enumeration definitions with their ordered literals;
- 60 constraint definition carriers;
- four preservation metadata definitions;
- validated preservation metadata annotations on all 143 library class
  carriers and all 41 association/association-class carriers;
- one locally loaded standard-library import; and
- typed connection ends wherever the source association-end types resolve
  within the corpus.

This yields 283 source declaration carriers and 60 constraint carriers, for
343 source-bound native targets in total.

Each manifest:

- names exactly one locked source artifact;
- records its locked SHA-256 digest;
- carries that artifact's complete canonical preservation facts;
- lists every native target for that artifact by canonical identity and fully
  qualified SysML v2 name;
- records the generated SysML v2 filename and digest; and
- protects the complete payload with its own SHA-256 digest.

The single v2 digest shared by the 17 manifests binds every source boundary to
the exact same generated corpus model.

## Commands

Generate the corpus:

```text
./raaml forward --milestone-4
```

Run the complete Milestone 4 gate:

```text
./raaml tests milestone-4
```

The gate generates the corpus twice and compares all 18 outputs byte for
byte. It validates every manifest and per-source canonical fact payload,
checks the exact source/declaration/constraint/target counts, and passes the
full SysML v2 model through the mandatory pinned validator.

## Local result

The local gate currently reports:

- 17 source artifacts;
- 17 schema-valid preservation manifests;
- 283 source declarations;
- 60 constraint carriers;
- 343 source-bound native targets;
- 18 deterministic generated files; and
- zero errors in lexical/syntax, import/library, name-resolution/linking,
  type/multiplicity, and model-validation categories.

Complete parser diagnostics are stored in the machine-readable build report
at `reports/conformance/milestone-4.json`.

The mandatory pinned SysML v2 implementation is the only parser used for this
gate. The report therefore states: **not tested with a second
implementation**.

## Claim boundary

Milestone 4 proves that the complete in-scope corpus can be represented by
deterministic, parser-valid SysML v2 declaration carriers alongside
schema-valid, integrity-protected preservation records.

It does not yet prove a full-corpus round trip. The preservation manifests
remain authoritative for source details that are not represented faithfully
by the native carrier view. Milestone 5 must consume all 17 manifests,
reconstruct all 17 v1 artifacts, and pass the mandatory v1 loader before the
project can advance that claim.
