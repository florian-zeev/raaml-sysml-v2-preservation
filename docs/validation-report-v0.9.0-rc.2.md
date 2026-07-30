# Validation report for `v0.9.0-rc.2`

**Status:** Candidate prepared; signed-tag identity pending

**Date:** 2026-07-30

**Candidate:** `v0.9.0-rc.2`

**TypeScript evidence commit:** [`0cc1623cb8eb738ea5d65ee35446cf81d21f89d7`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/0cc1623cb8eb738ea5d65ee35446cf81d21f89d7)

**TypeScript evidence run:** [GitHub Actions run 30562180377](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30562180377)

The exact signed tag target, tag-triggered clean run, and container image ID
will be added after the candidate tag has passed its clean validation run.

## Claim tested

The candidate tests one bounded claim:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

Here, `x` is one of the 17 normative RAAML 1.1 profile or library definition
files published by the OMG. `canonicalFacts` is the fact contract defined in
[`fact-contract-v0.1.md`](fact-contract-v0.1.md). The comparison concerns
model facts, not byte-for-byte XMI reproduction.

## Implementations tested

The repository contains two implementations of the bounded transformation:

1. the Python reference command-line implementation; and
2. a native TypeScript library that runs directly in Node.js.

The TypeScript implementation does not invoke Python, Java, Docker, or a
separate service at runtime. It reads the same locked 17-file corpus and
performs its own XML parsing, fact extraction, canonicalization, forward
mapping, manifest construction, reverse reconstruction, and equality check.

The implementations are maintained by the same project, and the TypeScript
version was developed as a port of the Python rules. Their agreement is
cross-language implementation evidence, not an external independent
reproduction.

The TypeScript implementation is also not a second SysML v2 validator. The
generated SysML v2 text still has acceptance evidence from one pinned SysML v2
implementation.

## Clean validation pipeline

The clean GitHub Actions gate:

1. verifies the locked standards, tools, and source inputs;
2. runs the complete Python extraction, mapping, reconstruction, validator,
   equality, and adversarial pipeline;
3. installs the TypeScript package from its exact lockfile;
4. runs the native TypeScript security and full-corpus conformance tests;
5. builds the digest-identified validation container;
6. repeats the Python evidence pipeline with networking disabled; and
7. compares the 49-file host and container release directories byte for byte.

## Result

| Measure | Result |
| --- | ---: |
| Official source artifacts | 17 |
| Preservation manifests | 17 |
| Reconstructed artifacts | 17 |
| Generated native v2 targets | 343 |
| SysML v2 validation errors | 0 |
| SysML v1 validation errors | 0 |
| Canonical fact differences | 0 |
| OCL expressions parsed and resolved | 33 |
| Transformation matrix rows | 35 |
| Open transformation rows | 0 |
| Adversarial cases | 36 |
| Failed adversarial cases | 0 |
| TypeScript security and conformance tests | 9 passed / 0 failed |
| TypeScript canonical equality gate | Passed |
| Release files covered by `SHA256SUMS` | 49 |
| Host/container release comparison | Byte-identical |

The Python and TypeScript implementations both produced the canonical source
fact SHA-256:

```text
5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967
```

The TypeScript implementation also produced the reference SysML v2 text
SHA-256:

```text
f9fc79f0fc8c8fb1a816edaec5913513a3a58d3c44f492eb952193ace54e2268
```

## TypeScript dependency boundary

The native implementation has one direct runtime dependency: `saxes` 6.0.0,
a namespace-aware XML parser. The lockfile also contains its `xmlchars`
dependency. Neither package implements RAAML, SysML, canonical identities,
the preservation manifest, or either transformation direction.

The project code supplies the protocol-specific extraction, secure reference
policy, canonical fact contract, mapping, reconstruction, and equality gate.

## What the result supports

Within the defined fact contract, the result supports the claim that both
project implementations preserve the normative RAAML 1.1 definition corpus
through the proposed SysML v2 representation and back.

It also shows that an application can execute the mapping natively in
TypeScript without operating the Python reference implementation as a
runtime service.

## What the result does not support

The candidate does not establish:

- byte-for-byte XMI reproduction;
- support for arbitrary user-authored RAAML models;
- preservation of facts outside the v0.1 contract;
- behavioral equivalence of source OCL and a native v2 constraint;
- acceptance by a second SysML v1 or SysML v2 implementation;
- independent reproduction by a person outside the project;
- conformance with a future normative RAAML-on-SysML-v2 standard;
- certification suitability;
- OMG endorsement; or
- permission to redistribute all third-party source material.

The complete `v0.9.0-rc.1` evidence remains available in
[`validation-report-v0.9.0-rc.1.md`](validation-report-v0.9.0-rc.1.md).
