# Milestone 0 evidence

**Status:** Passed

**Date:** 2026-07-27

**Evidence commit:** [`77cfaffda1d95fb7cc4a1a63f32d6132bd6588cc`](https://github.com/florian-zeev/raaml-sysml-v2-preservation/commit/77cfaffda1d95fb7cc4a1a63f32d6132bd6588cc)

**Clean-environment run:** [GitHub Actions run 30285573469](https://github.com/florian-zeev/raaml-sysml-v2-preservation/actions/runs/30285573469)

## Result

The Milestone 0 foundation gates passed on macOS/arm64 and on the
GitHub-hosted `ubuntu-24.04` Linux/x86-64 runner.

The clean Linux run:

- verified all 40 locked standards and tool artifacts;
- bootstrapped the pinned Linux JDK and official SysML v2 validator;
- built the Java adapters;
- validated the project schemas;
- ran the dependency-free unit and security suite;
- ran all nine paired Milestone 0 adapter cases;
- built the container from the digest-pinned Python base;
- mounted verified third-party inputs read-only;
- reran the full gate inside the container with networking disabled.

The workflow completed successfully in 2 minutes 33 seconds.

## Container identity

| Field | Value |
| --- | --- |
| Target platform | `linux/amd64` |
| Git commit | `77cfaffda1d95fb7cc4a1a63f32d6132bd6588cc` |
| Base OCI index digest | `sha256:fc74d22ffd0d5ac395a4b7bdda75a4539758862c49ebf3005647084631e63789` |
| Built image ID | `sha256:cd3a9f8d2a8a37d160df0f672fa9706b86e6f88f6cca737ace4f7844b0a45aa7` |

The image was not pushed to a registry. It contains original project material
and the pinned Python base, but excludes standards files, RAAML XMI, validator
archives, source and tool caches, generated reports, and Git history.

## What this proves

Milestone 0 proves that the selected parsers, validators, loaders, source lock,
security boundary, and clean execution environment work together on the
foundation fixtures and the required real Core RAAML files.

## What this does not prove

No forward transformation, reverse transformation, canonical fact comparison,
or fact-preserving round trip has been implemented yet. This result therefore
does not support a claim that RAAML 1.1 has already been preserved through a
SysML v2 round trip.

The run is independent of the maintainer's local machine, but it is not yet an
external reproduction by an independent person or organization.
