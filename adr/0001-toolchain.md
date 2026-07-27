# ADR 0001: orchestration and adapter toolchain

**Status:** Accepted for Milestone 0

**Date:** 2026-07-27

## Decision

Use dependency-free Python 3.14.4 for the repository CLI, source verification,
secure XML preflight, report orchestration, and archive bootstrap. Use Java 21
for narrow adapters over the official SysML v2 Pilot Implementation
distribution and its bundled Eclipse UML and OCL runtimes.

The stable entry point is `./raaml`. Java implementation classes remain behind
the adapter boundary and return JSON. Mapping code in later milestones is not
required to use Java or the pilot implementation's internal object model.

No Python package installation is required. The checked-in Java source is
compiled against a verified, ignored upstream distribution by:

```text
./raaml sources verify
./raaml tooling bootstrap
```

The Milestone 0 tested platforms are macOS on Apple silicon and the
`ubuntu-24.04` GitHub-hosted runner on x86-64. Both use pinned Eclipse Temurin
21.0.11+10 archives. The GitHub Actions workflow pins action revisions by
commit, fetches only locked inputs, and runs the same repository commands as a
local checkout.

The Milestone 0 container uses the official
`python:3.14.4-slim-bookworm` OCI index pinned at:

```text
sha256:fc74d22ffd0d5ac395a4b7bdda75a4539758862c49ebf3005647084631e63789
```

It targets `linux/amd64`, contains only original project material plus the
pinned Python base, and excludes source/tool caches and generated output. The
verified standards inputs and tool archives are mounted read-only. CI exercises
the resulting container with networking disabled and records its
content-addressed image ID against the Git commit.

The image is not pushed to a registry during private incubation. A published
container digest and registry retention policy remain release work, not
Milestone 0 validation prerequisites.

The clean workflow and offline container gate passed at commit
`77cfaffda1d95fb7cc4a1a63f32d6132bd6588cc`. The built image ID was
`sha256:cd3a9f8d2a8a37d160df0f672fa9706b86e6f88f6cca737ace4f7844b0a45aa7`.

## Why

- Python's standard library is sufficient for deterministic orchestration,
  hashing, JSON, guarded archive extraction, and XML preflight.
- The official v2 implementation requires Java 21.
- One verified upstream distribution contains the v2 parser, its matching
  libraries, Eclipse UML, and Eclipse OCL. Small adapters avoid making the
  project depend on its internal architecture.
- The normal build does not depend on Maven, Eclipse update sites, or a
  mutable `latest` URL.

## Rejected alternatives

- Building the pilot implementation from source for every run. The pinned
  source tag builds, but its Maven/Tycho target currently follows floating
  Eclipse repositories. That is useful provenance evidence, not a
  reproducible normal bootstrap.
- Adding a Python XML, UML, or OCL package before its behavior on the real
  corpus is proven.
- Implementing the mapper inside the interactive SysML kernel.

## Consequences

- The ignored tool and source caches are large.
- Java adapter source is reviewable and versioned; upstream binaries are
  verified but not committed.
- Supporting another platform requires an additional pinned JDK artifact,
  not an unversioned system Java assumption.
- The currently supported combinations are macOS/arm64 and Linux/x86-64.

## Verification

```text
./raaml tests unit
./raaml sources verify
./raaml tooling bootstrap
./raaml tooling build-adapters

docker build --pull --no-cache --platform linux/amd64 \
  --tag raaml-preservation:milestone-0 .
```
