# Milestone 6 full conformance

**Status:** Implementation complete; clean-environment evidence pending

**Date:** 2026-07-29

## Result

The local Milestone 6 gate reconstructs all 17 official RAAML 1.1 definition
files and compares the canonical engineering facts in every reconstructed
file with the facts in its verified source. The comparison reports:

- 17 source and 17 reconstructed artifacts;
- zero missing, added, or changed canonical facts;
- identical source and reconstructed fact counts in every category;
- zero errors from the mandatory SysML v2 validator;
- zero errors from the mandatory SysML v1 validator; and
- 36 passing positive and negative adversarial cases.

The common source and reconstructed canonical-fact SHA-256 is:

```text
5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967
```

These are local results. This document must not mark Milestone 6 as passed
until the Linux host and offline, digest-pinned container produce
byte-identical Milestone 6 reports in GitHub Actions.

## Command

```text
./raaml tests milestone-6
```

The command writes:

- `reports/conformance/milestone-6.json`, the machine-readable conformance
  report; and
- `reports/conformance/milestone-6-comparison.json`, both complete canonical
  fact sets, per-artifact and per-category counts, and the exact difference
  list; and
- `reports/diagnostics/tests-milestone-6.json`, structured command
  diagnostics.

## Equality gate

The gate evaluates:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

for each of the 17 verified files. The report includes source and
reconstructed counts for every artifact and every fact category. A mismatch
fails the command and the underlying comparison records its exact missing,
added, and changed paths.

## Adversarial coverage

The suite checks the difficult cases named by the reference implementation
plan:

- repeated local and constraint names under different owners;
- ambiguous same-name siblings under one owner;
- cross-artifact references, inherited bases, URI variants, multi-ended
  associations, Properties, Ports, connectors, roles, and `partWithPort`;
- explicit multiplicity/default presence and large icon payloads;
- missing, altered, mismatched, and schema-invalid manifests;
- unresolved local and external references;
- unsupported property kinds;
- DTDs, external entities, XInclude, unpinned network references, file
  references, traversal, symlinks, malformed XML, and input resource limits;
  and
- injected identifier collisions and the absence of partial output after
  rejection.

Every negative case declares its expected structured diagnostic. A case
fails if it is accepted or produces a different diagnostic.

## Claim boundary

This milestone supports a narrow claim: the reference implementation
preserves the defined canonical facts of the 17 official RAAML 1.1 profile
and library definition files through its SysML v2 representation and back.

It does not establish:

- byte-for-byte XMI reproduction;
- support for arbitrary user-authored RAAML instance models;
- preservation of facts outside the v0.1 fact contract;
- conformance with a future normative RAAML-on-SysML-v2 standard;
- certification suitability;
- interoperability with every commercial SysML v1 or SysML v2 tool; or
- independent reproduction by another person or organization.
