# Milestone 7 evidence

**Status:** Passed

**Date:** 2026-07-30

**Evidence commit:** [`3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea)

**Clean-environment run:** [GitHub Actions run 30526460693](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30526460693)

**Signed candidate tag:** `v0.9.0-rc.1`

## Result

Milestone 7 passed on the GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.
The host and the digest-identified container, running with networking
disabled, produced release directories that compared byte for byte.

The clean run:

- ran the complete Milestones 0 through 7 workflow;
- verified the locked standards and tool inputs;
- reproduced the complete forward and reverse mapping;
- retained zero canonical fact differences and 36 passing adversarial cases;
- generated a 49-file release directory;
- verified every entry in `SHA256SUMS`;
- validated the illustrative STPA wheel-brake walkthrough;
- reproduced the controlled one-fact v2 and manifest diff;
- compared the complete host and offline-container release directories; and
- retained the private release-candidate artifact for 30 days.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `3e2bb9fa6c8165bb0fab581619ebb60c8b6e2aea` |
| Built image ID | `sha256:d2b56f8de243f9336dc8838232bfcabadd4f4a4572a116686a2ae50e563486e3` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container release comparison | Byte-identical |
| Release artifacts covered by `SHA256SUMS` | `49` |
| Canonical fact differences | `0` |
| Adversarial cases | `36` |
| Failed adversarial cases | `0` |
| OCL expressions parsed and resolved | `33` |
| STPA walkthrough validation errors | `0` |
| Controlled input facts changed | `1` |

## Signed tag

The annotated tag `v0.9.0-rc.1` points exactly to the evidence commit above.
It was signed with the repository maintainer's Ed25519 SSH key:

```text
Signer:      florian@zeev.tech
Fingerprint: SHA256:YO5/2TLch9cNypEqm5q7fPhzWUBz977jHjWp2AcdgFo
```

The tag message records the Actions run, container image ID, canonical fact
hash, and release-artifact count.

Verify it from a checkout of the current repository:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.1
```

The expected output begins:

```text
Good "git" signature for florian@zeev.tech
```

The public verification key is stored in `.github/allowed_signers`. Private
key material is not part of the repository.

## What this proves

At the signed candidate commit, a clean Linux host and the offline pinned
container independently executed the repository workflow and produced
byte-identical release artifacts. The candidate tag binds that commit and its
recorded evidence to the maintainer's signing identity.

## What this does not prove

This is a conformance candidate, not a normative RAAML-on-SysML-v2 standard.
It does not expand the v0.1 fact scope or establish support for arbitrary
user-authored RAAML models. The STPA walkthrough and controlled diff remain
illustrative.

No person outside the project has yet independently reproduced the release.
The release candidate and eventual paper must continue to state that
limitation until an external reproduction is recorded.

Publication also remains subject to the third-party rights review.
