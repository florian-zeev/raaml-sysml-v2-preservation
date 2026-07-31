# Validation report for `v0.9.0-rc.3`

**Status:** Passed

**Date:** 2026-07-31

**Signed candidate:** `v0.9.0-rc.3`

## Evidence identity

The signed tag points to the exact source state tested by both the successful
pre-tag run and the clean tag-triggered run:

| Field | Value |
| --- | --- |
| Signed tag | `v0.9.0-rc.3` |
| Candidate commit | [`87ba4930dbd112d2b04f979d7e67f9b7e6c5254f`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/87ba4930dbd112d2b04f979d7e67f9b7e6c5254f) |
| Successful immediate pre-tag run | [GitHub Actions run 30633213467](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30633213467) |
| Pre-tag container image ID | `sha256:f2e1989b34662662dbce2458d0b73037fd7a129a0a981a2170446c3b627f8a7b` |
| Clean tag-triggered run | [GitHub Actions run 30634149648](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30634149648) |
| Tag-triggered container image ID | `sha256:a00a6b83908eec6b9a9b830d461c798c49f263bc9d4da7081e1958f1d3bc7443` |
| Target platform | `linux/amd64` |

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

## Result

The clean tag-triggered run reported:

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

The candidate also passed the automated conservative-publication
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

The source-only archive produced from the candidate commit was inspected
before signing. Its 120-file list exactly matched the tracked files at the
candidate commit. It contained no official RAAML corpus, generated SysML v2
corpus, preservation manifests, reconstructed XMI, specification PDFs, tool
archives, release directories, or CI artifacts. Its SHA-256 was:

```text
4ad4b572e95d456790b8e58d38605ec276b5fd0de76414ac43d08da03deaf2e2
```

## Supplemental SysML v2 interoperability observation

After `v0.9.0-rc.2` was signed, the exact generated SysML v2 text was opened
with Sensmetry Syside Editor 0.10.3. It reported no problems after active
validation had been confirmed with a deliberate negative smoke test. The
recorded file hash matches the unchanged reference SysML v2 text hash above.

This was a manual, maintainer-operated observation. It was not automated, was
not performed by an independent reviewer, and does not establish semantic
equivalence across tools. See
[`syside-editor-check-v0.9.0-rc.2.md`](syside-editor-check-v0.9.0-rc.2.md).

## Signed candidate

The annotated tag points exactly to the successful candidate commit. Verify
it with:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.3
```

The verified maintainer signing identity is:

```text
Signer:      florian@zeev.tech
Fingerprint: SHA256:YO5/2TLch9cNypEqm5q7fPhzWUBz977jHjWp2AcdgFo
```

## What the evidence supports

Within the defined fact contract, the signed-candidate evidence
supports the claim that both project implementations preserve the normative
RAAML 1.1 definition corpus through the proposed SysML v2 representation and
back.

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
