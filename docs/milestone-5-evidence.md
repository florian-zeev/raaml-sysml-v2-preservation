# Milestone 5 evidence

**Status:** Passed

**Date:** 2026-07-29

**Evidence commit:** [`bb4098a8628a2b74099e2e19d1ecc651fa505e7a`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/bb4098a8628a2b74099e2e19d1ecc651fa505e7a)

**Clean-environment run:** [GitHub Actions run 30463169639](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30463169639)

## Result

Milestone 5 passed on the GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.
The host and the pinned container, running with networking disabled, produced
byte-identical full-corpus reverse-mapping reports.

The clean run:

- verified all 42 locked source and tool artifacts;
- consumed all 17 integrity-protected preservation manifests and their shared
  SysML v2 corpus model;
- reconstructed all 17 RAAML 1.1 profile and library definition files;
- produced well-formed XML with unique deterministic `_raaml_` identifiers;
- loaded and validated the complete reconstructed corpus in one pinned v1
  environment with zero required validation errors;
- reconstructed the corpus twice with byte-identical output;
- rejected an injected deterministic identifier collision before writing
  partial output;
- reproduced the complete result in the offline container; and
- compared the host and container reports byte for byte.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `bb4098a8628a2b74099e2e19d1ecc651fa505e7a` |
| Built image ID | `sha256:04b6c216cb641af9f15d9bed28cb6bca58ccbdebb5513ecc749176cf2029aefd` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container report comparison | Byte-identical |
| Reconstructed artifacts | `17` |
| SysML v1 validation errors | `0` |
| Deterministic collision gate | Passed |

The image was not pushed to a registry. Verified third-party sources and
tools were mounted read-only and were not included in the image.

## What this proves

The complete in-scope RAAML 1.1 definition corpus can be reconstructed
deterministically from the generated SysML v2 model and its preservation
manifests. Every reconstructed artifact loads in the named mandatory v1
environment without required validation errors. The result is reproducible
on the Linux host and inside the offline pinned container.

## What this does not prove

Milestone 5 does not yet prove exact canonical fact equality between every
official source file and its reconstructed counterpart. That full-corpus
comparison and the complete adversarial suite are Milestone 6 work.

The reconstructed corpus was not tested with a second SysML v1
implementation. Original MagicDraw identifiers are neither required nor
claimed to be preserved.

The clean run is independent of the maintainer's local environment, but it is
not yet an independent reproduction by another person or organization.
