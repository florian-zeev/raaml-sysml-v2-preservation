# External review guide

## Purpose

This repository contains a Draft Community Proposal v0.1 for preserving the
normative RAAML 1.1 definitions through a SysML v2 representation. It is not
an OMG specification, a proposal for a new version of RAAML, or a claim that
arbitrary user-authored RAAML models are supported.

The most useful review is not “does this look plausible?” It is:

> Does the stated fact boundary capture the information needed to preserve the
> 17 official RAAML 1.1 definition files, and does the evidence support the
> claims made within that boundary?

For installation and command-by-command reproduction instructions, start with
[`GETTING_STARTED.md`](../GETTING_STARTED.md).

## Suggested reading order

1. [`executive-summary.md`](executive-summary.md) — the motivation and result
   in plain language.
2. [`community-proposal-v0.1.md`](../proposal/community-proposal-v0.1.md) —
   the paper and its claim boundary.
3. [`normative-encoding-v0.1.md`](../proposal/normative-encoding-v0.1.md) —
   the detailed encoding and reverse-mapping rules.
4. [`validation-report-v0.9.0-rc.3.md`](validation-report-v0.9.0-rc.3.md) —
   the signed candidate identity, results, and limitations.

## What the candidate demonstrates

At signed candidate tag `v0.9.0-rc.3`:

- all 17 normative RAAML 1.1 definition artifacts were mapped to the proposed
  v2 representation and reconstructed as v1 artifacts;
- the before-and-after canonical fact comparison found zero differences;
- all 343 generated native v2 targets passed the pinned v2 validator;
- all 17 reconstructed v1 artifacts passed the pinned v1 validation;
- all 33 OCL expressions were parsed and their referenced names resolved;
- 36 adversarial cases passed;
- the native TypeScript implementation reproduced the canonical hash,
  generated SysML v2 hash, and zero-difference round trip; and
- a clean Linux host and an offline pinned container produced byte-identical
  49-file release directories.

## What the candidate does not demonstrate

- support for arbitrary user-authored RAAML models;
- behavioral equivalence of source OCL and any native v2 constraint;
- acceptance by a second SysML v2 implementation;
- independent reproduction by someone outside the project;
- that the proposed encoding is the best design for a future native RAAML on
  SysML v2;
- permission to redistribute all third-party source material.

The automated candidate evidence still relies on one pinned SysML v2
validator. A post-`rc.2`-tag manual check found no reported problems when the
exact generated text was opened with Sensmetry Syside Editor 0.10.3. That
maintainer-operated observation is recorded separately in
[`syside-editor-check-v0.9.0-rc.2.md`](syside-editor-check-v0.9.0-rc.2.md).

## Questions for reviewers

### RAAML specialists

- Is any normative fact in the 17 official artifacts missing from the
  preservation contract?
- Does the contract preserve distinctions that matter to RAAML tools?
- Does it preserve any file detail that should instead be explicitly
  non-normative?

### SysML v2 and KerML specialists

- Are the chosen native v2 forms useful and understandable?
- Where does the encoding depart unnecessarily from the official SysML v1 to
  v2 transformation?
- Which preservation fields should remain compatibility metadata, and which
  should have a more direct v2 expression?

### Tool implementers

- Can the candidate be reproduced from the signed tag?
- Are any rules dependent on behavior found only in the pinned validators?
- Are diagnostics clear enough to prevent silent information loss?
- Can another implementation produce the same canonical facts and stable IDs?

### Safety, assurance, and certification practitioners

- Is the evidence precise enough to support a review or migration decision?
- Which additional provenance, baseline, signature, or approval records would
  be needed in a controlled engineering environment?
- Are the stated non-goals and limits easy to find and difficult to
  misinterpret?

## Verify the signed candidate

From a checkout containing the tag:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.3
```

The complete reproduction identity, tag target, and verified signature are
recorded in
[`validation-report-v0.9.0-rc.3.md`](validation-report-v0.9.0-rc.3.md).

## Reproduce from a source-only review package

The source-only review package intentionally contains no Git history, official
standards files, tool archives, generated corpus, or reconstructed XMI.

On a clean machine with Docker configured for `linux/amd64`, run:

```text
./review-reproduce
```

The command builds the pinned container, uses it to fetch each locked input
from its recorded authoritative URL, verifies every size and SHA-256, and then
disables networking for the reproduction itself. No host Python or Java
installation is required. A passing run creates:

- `review-evidence/review-result.json` — aggregate conformance results;
- `review-evidence/review-diagnostics.json` — command diagnostics.

The reviewer should report:

- the SHA-256 of the source archive received;
- host operating system and architecture;
- Docker version;
- whether emulation was used for `linux/amd64`;
- the complete `review-result.json`;
- any setup issue or manual intervention.

The expected canonical fact SHA-256 is
`5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967`.
The result must report zero canonical differences, zero v1 validation errors,
zero v2 validation errors, and zero failed adversarial cases.

## Publication gates still open

Before the repository and paper are presented as a public release:

1. pass `./raaml publication audit` and the complete validation workflow for
   the exact `v0.9.0-rc.3` source state;
2. inspect the source-only archive produced from that exact commit;
3. retain the manual Syside limitation explicitly; and
4. create and validate the signed `v0.9.0-rc.3` tag without publishing
   generated-corpus artifacts.

Independent reproduction and specialist review remain explicit open evidence
items, but they do not block publication of a clearly labeled Draft Community
Proposal v0.1.
