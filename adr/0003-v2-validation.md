# ADR 0003: SysML v2 validation

**Status:** Accepted

**Date:** 2026-07-27

## Decision

Use the official SysML v2 Pilot Implementation release `2026-04`, version
`0.59.0`, as the mandatory v2 validator for the SysML 2.0 proposal.

Pinned evidence:

- source tag: `2026-04`;
- source commit: `20897e3122f2c2f8b29389745f0caaaeb7c6e21a`;
- release archive: `jupyter-sysml-kernel-0.59.0.zip`;
- archive SHA-256:
  `1ef7e89abebbc008c5c2707f8b2f34630b3ab971de7b38f6d0240da6f461a828`;
- bundled JAR SHA-256:
  `7d6f1f2d555ddde2538a2b4f726709ba261567aa6c7eb172ad7db762d01efbaf`;
- bundled `sysml.library` set: 95 regular files;
- deterministic library-manifest SHA-256:
  `a6c1313bf46075b034bfc588324cb883b916076aae2b7008c5a80b854284d8d1`;
- Java: 21.

The library-manifest digest is calculated by sorting all paths relative to
`sysml.library`, writing each relative path, a tab, and that file's SHA-256
digest followed by LF, and hashing the resulting UTF-8 byte stream. The
verified release archive remains the acquisition unit; the manifest identifies
the exact standard-library set inside it.

The adapter invokes `SysMLInteractive.process`, which parses and runs Xtext
`CheckMode.ALL`. It reports error counts separately for:

1. lexical and syntax;
2. import and library loading;
3. name resolution and linking;
4. type and multiplicity;
5. model validation.

A file passes only when all five counts are zero.

The next pilot release, `2026-05`, moved to KerML 1.1 and SysML 2.1 Beta 1.
It is not silently substituted for the formal SysML 2.0 baseline.

## Second parser

A second v2 implementation is additional evidence, not a v0.1 mandatory
gate. Reports must state **not tested with a second implementation** until one
is pinned and exercised.

## Known limitation

The upstream interactive API prints library-loading progress. The Python
adapter isolates the final JSON report and does not treat console text as
validation evidence.

## Verification

```text
./raaml validate-v2 fixtures/milestone-0/minimal-valid.sysml
./raaml validate-v2 fixtures/milestone-0/minimal-invalid.sysml
```
