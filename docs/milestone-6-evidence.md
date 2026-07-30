# Milestone 6 evidence

**Status:** Passed

**Date:** 2026-07-30

**Evidence commit:** [`81791c68d8f9783fdf0b4b099e6dd828bec6acb3`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/81791c68d8f9783fdf0b4b099e6dd828bec6acb3)

**Clean-environment run:** [GitHub Actions run 30467855996](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30467855996)

## Result

Milestone 6 passed on the GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.
The Linux host and the digest-pinned container, running with networking
disabled, produced byte-identical conformance and complete comparison
reports.

The clean run:

- verified the locked standards and tool inputs;
- extracted the canonical facts from all 17 official RAAML 1.1 definition
  files;
- generated and validated the complete SysML v2 corpus;
- reconstructed and validated all 17 SysML v1 artifacts;
- found zero canonical fact differences across every artifact and fact
  category;
- passed all 36 positive and negative adversarial cases;
- produced complete source and reconstructed fact sets with an empty exact
  difference list; and
- compared the host and offline-container reports byte for byte.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `81791c68d8f9783fdf0b4b099e6dd828bec6acb3` |
| Built image ID | `sha256:94a536ed465f7d6aae6a1b5302c6566400d259420895d4ea6c2c554299c41124` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container report comparison | Byte-identical |
| Source and reconstructed artifacts | `17` / `17` |
| Canonical fact differences | `0` |
| SysML v1 validation errors | `0` |
| SysML v2 validation errors | `0` |
| Adversarial cases | `36` |
| Failed adversarial cases | `0` |

The image was not pushed to a registry. Verified third-party sources and
tools were mounted read-only and were not included in the image.

## What this proves

For the defined v0.1 fact contract and the 17 verified official RAAML 1.1
profile and library definition files:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

The clean run also proves that this result and the published machine-readable
reports are reproducible between the Linux host and the offline,
digest-pinned container at the evidence commit.

## What this does not prove

Milestone 6 does not establish:

- byte-for-byte XMI reproduction;
- support for arbitrary user-authored RAAML models;
- preservation of facts outside the v0.1 contract;
- conformance with a future normative RAAML-on-SysML-v2 standard;
- certification suitability;
- interoperability with every commercial SysML implementation; or
- independent reproduction by a person outside the project.

Those limits remain explicit in the proposal and the Milestone 6 conformance
document.
