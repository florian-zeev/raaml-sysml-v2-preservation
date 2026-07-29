# Milestone 3 thin vertical slice

**Status:** Passed

**Date started:** 2026-07-29

## Purpose

Milestone 3 is the first executable test of the preservation proposal. It
maps a bounded part of the official RAAML 1.1 corpus to SysML v2, reconstructs
v1 XMI from the v2 model and its preservation manifest, and compares the
canonical source facts with the reconstructed facts.

This is deliberately a thin slice. It tests the architecture before the
mapper expands to all 17 definition files.

## Included artifacts

The slice contains:

- all definitions in `CoreRAAML.xmi` and `CoreRAAMLLib.xmi`;
- all definitions in `GeneralRAAML.xmi` and `GeneralRAAMLLib.xmi`;
- `ControlStructure`, `Controller`, and `ControlAction` from `STPA.xmi`;
- `Loss` and its official Core `Situation` application from `STPALib.xmi`.

Together these exercise:

- a metadata definition with `base_Element`;
- the `Undeveloped` SVG payload, format, and verbatim Windows source location;
- OCL constraints;
- cross-file generalizations and imports;
- a normative library stereotype application;
- a stereotype with three UML bases;
- ordinary UML Associations with ordered member ends;
- native SysML v2 metadata, occurrence, connection, and constraint carriers.

## Executed pipeline

```text
six source artifacts
  -> canonical source facts
  -> native SysML v2 model + integrity-protected manifest
  -> pinned SysML v2 validation
  -> deterministic v1 XMI reconstruction
  -> pinned UML loading and validation of all six artifacts
  -> canonical reconstructed facts
  -> exact fact comparison
```

The manifest binds to the exact generated SysML v2 bytes and lists every
required native target. Reverse reconstruction fails if the v2 model is
changed or a required target is removed. The v2 model is therefore a required
input, not an optional illustration beside a backup of the source facts.

The native connection definitions use typed ends derived from the source
Association member ends when their types are available in the slice.

## Commands

Run the complete gate:

```text
./raaml tests milestone-3
```

Run the stages separately:

```text
./raaml forward --milestone-3
./raaml validate-v2 generated/milestone-3/forward/raaml-milestone-3.sysml
./raaml reverse \
  --manifest generated/milestone-3/forward/preservation-manifest.json \
  --v2 generated/milestone-3/forward/raaml-milestone-3.sysml
./raaml compare \
  --manifest generated/milestone-3/forward/preservation-manifest.json \
  --reconstructed-dir generated/milestone-3/reconstructed
```

## Local result

The local gate currently reports:

- six reconstructed and independently loaded v1 artifacts;
- zero SysML v2 validation errors;
- zero canonical fact differences;
- identical source and reconstructed fact digest
  `b9915225771b6600008164a0394da3bf3841834d26c15bea6c227b6572e272da`;
- deterministic forward outputs;
- rejection of a corrupt manifest;
- rejection of a removed native v2 target;
- detection of a changed ordered Association member end.

The machine-readable report is written to
`reports/conformance/milestone-3.json`. It identifies every locked input
digest and the v1/v2 adapter versions. Generated reports remain ignored local
build output until a release-evidence decision freezes them.

The clean Linux and offline-container gate passed at commit
`29018cf93e0238e9fb0f31809ad140644e790183`.

## Claim boundary

This result does not yet establish a fact-preserving round trip for all 17
official RAAML definition files. It demonstrates the mechanism only for the
six-artifact slice above.

The preservation manifest remains authoritative for source facts that have no
faithful native SysML v2 representation. Native v2 declarations and typed
connection ends provide the model-facing view; the manifest supplies the
additional information needed for exact reconstruction.
