# Validation report for `v0.9.0-rc.3`

**Status:** Candidate prepared; exact-commit validation and signed-tag identity pending

**Date:** 2026-07-31

**Candidate:** `v0.9.0-rc.3`

## Current state

This report is part of the source state being prepared for `v0.9.0-rc.3`.
The candidate commit, its immediate successful pre-tag run, the signed tag,
and the clean tag-triggered run do not exist yet. They must be recorded here
only after the exact source state passes the complete workflow.

The latest successful preparation baseline before this publication-document
update is:

| Field | Value |
| --- | --- |
| Preparation commit | [`0585cdaab493c158797c6973e9a6855a6bdca237`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/0585cdaab493c158797c6973e9a6855a6bdca237) |
| Preparation run | [GitHub Actions run 30631038284](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30631038284) |
| Preparation container image ID | `sha256:ff959fa2313aa1a3e070e1fff29fedd89fa58f21258c8cee2fc625ef9fc82e4c` |

That run is evidence for the preceding source state. It is not the final
`v0.9.0-rc.3` identity.

## Claim tested

The candidate tests one bounded claim:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

Here, `x` is one of the 17 normative RAAML 1.1 profile or library definition
files published by the OMG. `canonicalFacts` is the fact contract defined in
[`fact-contract-v0.1.md`](fact-contract-v0.1.md). The comparison concerns
model facts, not byte-for-byte XMI reproduction.

## Implementations

The repository contains:

1. the Python reference command-line implementation; and
2. a native TypeScript library that runs directly in Node.js.

The TypeScript implementation does not invoke Python, Java, Docker, or a
separate service at runtime. It independently performs XML parsing, fact
extraction, canonicalization, forward mapping, manifest construction, reverse
reconstruction, and equality checking against the same locked inputs and
contract.

Both implementations are maintained by this project, and the TypeScript
version is a port of the Python rules. Agreement between them is useful
cross-language evidence, but it is not an external independent reproduction.

## Most recent complete preparation result

The successful preparation run reported:

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
| Native TypeScript canonical equality gate | Passed |
| Release files covered by `SHA256SUMS` | 49 |
| Host/container release comparison | Byte-identical |

The Python and TypeScript implementations produced the canonical source fact
SHA-256:

```text
5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967
```

The TypeScript implementation produced the reference SysML v2 text SHA-256:

```text
f9fc79f0fc8c8fb1a816edaec5913513a3a58d3c44f492eb952193ace54e2268
```

## Publication-boundary evidence

The preparation baseline also passed the automated conservative-publication
audit. The repository records that:

- official standards files and generated full-corpus outputs are excluded
  from the source-only publication package;
- the workflow does not upload generated artifacts, create releases, publish
  packages, or push containers;
- historical hosted workflow artifacts were manually inspected and removed;
- no GitHub Release or published package existed; and
- the only identified Actions cache contained npm dependencies, not generated
  RAAML outputs.

The manual decisions and their limits are recorded in
[`third-party-rights-audit.md`](third-party-rights-audit.md) and
[`public-release-checklist.md`](public-release-checklist.md). They are a
publisher decision, not an external legal opinion or permission from the OMG.

## Supplemental SysML v2 interoperability observation

After `v0.9.0-rc.2` was signed, the exact generated SysML v2 text was opened
with Sensmetry Syside Editor 0.10.3. It reported no problems after active
validation had been confirmed with a deliberate negative smoke test. The
recorded file hash matches the unchanged reference SysML v2 text hash above.

This was a manual, maintainer-operated observation. It was not automated, was
not performed by an independent reviewer, and does not establish semantic
equivalence across tools. See
[`syside-editor-check-v0.9.0-rc.2.md`](syside-editor-check-v0.9.0-rc.2.md).

## Identity to record after validation and signing

Before this report may be marked **Passed**, replace the pending values below
with evidence from the exact candidate commit and tag-triggered workflow:

| Field | Value |
| --- | --- |
| Signed tag | Pending: `v0.9.0-rc.3` |
| Candidate commit | Pending |
| Successful immediate pre-tag run | Pending |
| Clean tag-triggered run | Pending |
| Tag-triggered container image ID | Pending |
| Target platform | Expected: `linux/amd64` |
| Canonical fact SHA-256 | Expected: `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| TypeScript SysML v2 SHA-256 | Expected: `f9fc79f0fc8c8fb1a816edaec5913513a3a58d3c44f492eb952193ace54e2268` |
| Release files | Expected: `49` |
| Host/container comparison | Expected: byte-identical |

The tag must point exactly to the successful candidate commit. After it is
created, verify it with:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.3
```

The expected maintainer signing identity is:

```text
Signer:      florian@zeev.tech
Fingerprint: SHA256:YO5/2TLch9cNypEqm5q7fPhzWUBz977jHjWp2AcdgFo
```

## What the evidence supports

Within the defined fact contract, the successful preparation evidence
supports the claim that both project implementations preserve the normative
RAAML 1.1 definition corpus through the proposed SysML v2 representation and
back. The exact `v0.9.0-rc.3` claim remains pending until the candidate commit
and tag-triggered run pass.

## What the evidence does not support

The evidence does not establish:

- byte-for-byte XMI reproduction;
- support for arbitrary user-authored RAAML models;
- preservation of facts outside the v0.1 contract;
- behavioral equivalence of source OCL and a native v2 constraint;
- independent reproduction by a person outside the project;
- external RAAML or SysML v2 specialist review;
- cross-tool semantic equivalence;
- conformance with a future normative RAAML-on-SysML-v2 standard;
- certification suitability;
- OMG endorsement; or
- permission to redistribute all third-party source material.

The signed `v0.9.0-rc.1` and `v0.9.0-rc.2` evidence remains available in
[`validation-report-v0.9.0-rc.1.md`](validation-report-v0.9.0-rc.1.md) and
[`validation-report-v0.9.0-rc.2.md`](validation-report-v0.9.0-rc.2.md).
