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

A container image and digest are intentionally not selected yet. The clean
Linux workflow proves the Milestone 0 tool bootstrap, but it does not satisfy
the later clean-container reproduction gate. A container must be pinned and
run before the first public conformance release.

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
```
