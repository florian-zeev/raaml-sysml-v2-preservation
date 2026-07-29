# Milestone 4 evidence

**Status:** Passed

**Date:** 2026-07-29

**Evidence commit:** [`5f3131c6ed0d5d2d98af16637a9c998020a3a3a1`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/5f3131c6ed0d5d2d98af16637a9c998020a3a3a1)

**Clean-environment run:** [GitHub Actions run 30441288705](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30441288705)

## Result

Milestone 4 passed on the GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.
The host and the pinned container, running with networking disabled, produced
byte-identical full-corpus build reports.

The clean run:

- verified all 41 locked source and tool artifacts;
- generated a native SysML v2 corpus view for all 17 official RAAML
  definition files;
- generated one schema-valid preservation manifest per source file;
- represented all 283 in-scope declarations and 60 constraint carriers;
- bound 343 canonical source identities to qualified native targets;
- validated the generated model with zero errors in all five mandatory SysML
  v2 validation categories;
- reproduced the complete result in the offline container; and
- compared the host and container reports byte for byte.

## Reproducibility identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `5f3131c6ed0d5d2d98af16637a9c998020a3a3a1` |
| Built image ID | `sha256:cd560fc09d02e47076e835e2d9e429bcf78fcaa85fd24986d1005ee478022894` |
| Canonical fact SHA-256 | `5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967` |
| Host/container report comparison | Byte-identical |
| Source artifacts | `17` |
| Preservation manifests | `17` |
| Native targets | `343` |
| SysML v2 validation errors | `0` |

The image was not pushed to a registry. Verified third-party sources and
tools were mounted read-only and were not included in the image.

## What this proves

The complete in-scope RAAML 1.1 definition corpus has deterministic,
parser-valid native SysML v2 carriers and integrity-protected per-source
preservation manifests. The result is reproducible on the Linux host and
inside the offline pinned container.

## What this does not prove

Milestone 4 does not prove a fact-preserving round trip for all 17 files. The
full reverse mapping, v1 loading, and exact source-versus-reconstructed fact
comparison remain Milestone 5 and Milestone 6 work.

The generated corpus was not tested with a second SysML v2 implementation.
The mandatory build report states this explicitly.

The clean run is independent of the maintainer's local environment, but it is
not yet an independent reproduction by another person or organization.
