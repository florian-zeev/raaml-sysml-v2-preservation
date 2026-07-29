# Milestone 5 full-corpus reverse mapping

**Status:** Passed

**Date started:** 2026-07-29

## Purpose

Milestone 5 consumes the 17 integrity-protected manifests and the shared
SysML v2 model produced by Milestone 4. It reconstructs the 17 RAAML 1.1
profile and library XMI files and checks that a pinned SysML v1 environment
can load the reconstructed corpus without required validation errors.

This milestone tests reconstruction and loadability. Milestone 6 performs the
complete source-versus-reconstructed canonical fact comparison.

## Command

Run the complete gate:

```text
./raaml tests milestone-5
```

Use the reverse mapper directly:

```text
./raaml forward --milestone-4
./raaml reverse \
  --manifest-dir generated/milestone-4/forward/manifests \
  --v2 generated/milestone-4/forward/raaml-full-corpus.sysml \
  --output-dir generated/milestone-5/reconstructed
```

## Local result

The local gate:

- verified all 17 manifests against their payload digests, locked source
  identities, and one shared SysML v2 digest;
- reconstructed all 17 source artifacts twice with byte-identical output;
- preserved the package trees used by FTA, RBD, and ISO 26262 artifacts;
- produced 17 well-formed XML artifacts with unique deterministic
  `_raaml_` identifiers;
- loaded every reconstructed artifact with the mandatory pinned v1 adapter;
- reported zero required v1 validation errors;
- injected a constant fake hash provider, observed
  `SYNTHETIC_ID_COLLISION`, and wrote no partial output.

The machine-readable local report is
`reports/conformance/milestone-5.json`.

The clean Linux and offline-container gate passed at commit
`bb4098a8628a2b74099e2e19d1ecc651fa505e7a`. The host and container produced
byte-identical Milestone 5 reports. See
[Milestone 5 evidence](milestone-5-evidence.md).

## Complete SysML 1.6 reference chain

Full-corpus loading exposed a missing transitive reference input. The official
SysML 1.6 ISO 80000 library refers to the SysML 1.6 QUDV model. QUDV is an
informative machine-readable artifact identified by OMG file
`ptc/18-10-05`.

The official logical URL remains recorded as:

```text
https://www.omg.org/spec/SysML/20181001/QUDV.xmi
```

That URL currently returns 404. The lock therefore records an archived
snapshot of that exact official URL as the acquisition URL. The bytes remain
uncommitted, must match the locked size and SHA-256 digest, and are loaded
only from the verified local cache. The complete source lock now contains 42
artifacts.

## Identifier policy

Reconstruction does not require or claim preservation of original MagicDraw
IDs. Top-level and owned elements receive deterministic SHA-256-derived
identifiers. Collision detection runs before any reconstructed file is
written.

This preserves stable identity for repeated reconstruction without confusing
tool-specific source handles with normative RAAML identity.

## Claim boundary

Milestone 5 proves deterministic full-corpus reconstruction and successful
loading in the named mandatory v1 environment. It does not yet prove:

- exact canonical fact equality for all 17 source/reconstructed pairs;
- absence of every possible unsupported or adversarial input;
- interoperability with a second SysML v1 implementation;
- preservation of diagram layout or other out-of-scope tool data.

Those claims remain subject to Milestone 6 and later release gates.
