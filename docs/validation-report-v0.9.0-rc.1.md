# Validation report for `v0.9.0-rc.1`

**Status:** Passed

**Date:** 2026-07-30

**Signed candidate:** `v0.9.0-rc.1`

**Evidence commit:** [`3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea)

**Clean-environment run:** [GitHub Actions run 30526460693](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30526460693)

## Claim tested

The candidate tests one bounded claim:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

Here, `x` is one of the 17 normative RAAML 1.1 profile or library definition
files published by the OMG. `canonicalFacts` is the fact contract defined in
[`fact-contract-v0.1.md`](fact-contract-v0.1.md). The comparison is about
model facts, not byte-for-byte XMI reproduction.

## Test pipeline

The clean release gate:

1. verifies the locked standards, tools, and source inputs;
2. extracts raw and canonical facts from all 17 source artifacts;
3. checks the extraction against an independent corpus audit;
4. parses and resolves the names in all source OCL expressions;
5. generates the complete SysML v2 view and 17 preservation manifests;
6. validates the v2 output with the pinned SysML v2 implementation;
7. reconstructs all 17 SysML v1/UML artifacts;
8. validates the reconstructed artifacts with the pinned v1 environment;
9. compares every canonical source and reconstructed fact;
10. runs positive and negative adversarial cases;
11. validates an illustrative STPA wheel-brake model;
12. records a controlled one-fact textual diff;
13. creates a checksummed release directory; and
14. repeats the process in an offline pinned container and compares the two
    release directories byte for byte.

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
| STPA walkthrough validation errors | 0 |
| Release files covered by `SHA256SUMS` | 49 |
| Host/container release comparison | Byte-identical |

The canonical source fact list has SHA-256:

```text
5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967
```

## Source corpus measured

The deterministic source baseline contains:

| Fact category | Count |
| --- | ---: |
| Profiles | 9 |
| Packages | 15 |
| Stereotypes | 94 |
| Classes | 143 |
| Enumerations | 5 |
| Enumeration literals | 35 |
| Associations | 40 |
| AssociationClasses | 1 |
| Properties | 267 |
| Ports | 65 |
| Connectors | 94 |
| Constraints | 60 |
| Extensions | 84 |
| Extension ends | 84 |
| Comments | 431 |
| Images | 22 |
| RAAML stereotype applications | 108 |

Counts alone are not the preservation test. The canonical baseline also
records identities, ownership, inheritance, ordered values, references,
imports, multiplicities, defaults, expressions, and source-specific details.

## Transformation analysis

The machine-checkable transformation matrix contains 35 resolved rows and no
open mapping decisions. It classifies all 267 UML Properties and all 60
constraint `OpaqueExpression` instances. The detailed rationale and its
relationship to the official SysML v1-to-v2 transformation are in
[`transformation-analysis-v0.1.md`](transformation-analysis-v0.1.md) and the
JSON reports under [`analysis/`](../analysis/).

Two deviations are deliberately explicit:

- a UML Enumeration with the SysML v1 `ValueType` stereotype uses an
  `EnumerationDefinition`, while its ordered literals and source application
  are retained for reversal; and
- the FMEALib `RPNCalculation` expression has no source language label, so the
  mapper preserves it without inventing a language or claiming a faithful
  native textual representation.

## Adversarial coverage

The 36 cases cover:

- repeated names under different owners and ambiguous same-name siblings;
- cross-artifact references, inherited bases, URI variants, association-end
  ownership, Properties, Ports, connectors, roles, and `partWithPort`;
- explicit multiplicity and default presence and large icon payloads;
- missing, altered, mismatched, and schema-invalid manifests;
- unresolved local and external references and unsupported property kinds;
- DTDs, external entities, XInclude, unpinned network or file references,
  traversal, symlinks, malformed XML, and resource limits; and
- injected deterministic-ID collisions and the absence of partial output
  after rejection.

Every negative case declares the structured diagnostic it expects. A case
fails if the input is accepted or if it produces a different diagnostic.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea` |
| Container image ID | `sha256:d2b56f8de243f9336dc8838232bfcabadd4f4a4572a116686a2ae50e563486e3` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Release files | `49` |
| Host/container comparison | Byte-identical |

The container ran with networking disabled. Locked third-party sources and
tools were mounted read-only and were not included in the image.

The stable reproduction command is:

```text
./raaml reproduce \
  --clean \
  --container-digest sha256:<64 lowercase hexadecimal digits> \
  --release-tag v0.9.0-rc.1 \
  --output-dir generated/release-candidate
```

The command does not download inputs. The locked sources and tools must
already be present and verified.

## Signed candidate

The annotated tag `v0.9.0-rc.1` points exactly to the evidence commit. It was
signed with the maintainer's Ed25519 SSH key:

```text
Signer:      florian@zeev.tech
Fingerprint: SHA256:YO5/2TLch9cNypEqm5q7fPhzWUBz977jHjWp2AcdgFo
```

Verify it from a checkout containing the tag:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.1
```

## Important finding during development

An earlier reconstruction checkpoint loaded all 17 rebuilt artifacts in the
pinned v1 environment but omitted 94 UML connectors. The later exact fact
comparison found the omission. Connector reconstruction was added before the
signed candidate, which then reported zero fact differences.

This finding is worth preserving because it shows why parser or loader
acceptance is not enough. A file can be valid and still be incomplete.

## What the result supports

Within the defined fact contract, the signed candidate supports the claim
that the reference implementation preserves the normative RAAML 1.1
definition corpus through its SysML v2 representation and back.

## What the result does not support

The candidate does not establish:

- byte-for-byte XMI reproduction;
- support for arbitrary user-authored RAAML models;
- preservation of facts outside the v0.1 contract;
- behavioral equivalence of source OCL and a native v2 constraint;
- acceptance by a second SysML v1 or SysML v2 implementation;
- conformance with a future normative RAAML-on-SysML-v2 standard;
- certification suitability;
- independent reproduction by a person outside the project; or
- permission to redistribute all third-party source material.

The complete development sequence remains available in Git history. This
report replaces the milestone-by-milestone status documents in the current
publication tree.
