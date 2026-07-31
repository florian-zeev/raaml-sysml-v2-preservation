# Manual Syside Editor check for `v0.9.0-rc.2`

**Status:** Passed

**Date:** 2026-07-31

**Operator:** Project maintainer

**Relationship to candidate:** Post-tag observation; not part of the immutable
`v0.9.0-rc.2` candidate or its clean tagged-candidate run

## Purpose

The signed candidate validated its generated SysML v2 text with the pinned
OMG SysML v2 Pilot Implementation. This check asks a narrower additional
question:

> Does a separately developed SysML v2 implementation accept the exact
> generated candidate text without reporting a problem?

## Input identity

| Field | Value |
| --- | --- |
| Signed candidate | `v0.9.0-rc.2` |
| Candidate commit | `381e1f5c68347f84ba0bbd2243f3e36fe915ccfa` |
| File | `raaml-full-corpus.sysml` |
| SHA-256 | `f9fc79f0fc8c8fb1a816edaec5913513a3a58d3c44f492eb952193ace54e2268` |

The file was generated from the verified locked corpus with:

```text
./raaml forward \
  --milestone-4 \
  --output-dir="$HOME/Desktop/raaml-rc2-second-parser"
```

The resulting SHA-256 matched the value asserted by the native TypeScript
conformance test and recorded in the candidate validation report.

## Tool and environment

| Field | Value |
| --- | --- |
| Second implementation | Sensmetry Syside Editor |
| Extension identifier | `sensmetry.syside-editor` |
| Syside Editor version | `0.10.3` |
| Visual Studio Code version | `1.131.0` |
| Operating system | macOS 26.5.2, build `25F84` |
| Architecture | `arm64` |

Syside Editor is separate from the OMG SysML v2 Pilot Implementation used by
the mandatory repository validator.

## Procedure

1. Opened the directory containing only the generated full-corpus model and
   its 17 preservation manifests in Visual Studio Code.
2. Opened `raaml-full-corpus.sysml` in SysML language mode and allowed the
   Syside language server to initialize.
3. Saved the unchanged file and opened the Problems panel.
4. Observed no reported problems for the candidate file.
5. Created a separate `syside-smoke-test.sysml` file containing a reference to
   an undefined `MissingType`.
6. Saved the smoke-test file and observed that Syside reported the deliberate
   problem.
7. Deleted the smoke-test file and confirmed that the unchanged candidate file
   still produced no reported problems.

The negative smoke test establishes that the absence of candidate diagnostics
was not merely caused by an inactive extension.

## Result

Syside Editor 0.10.3 reported no problems for the exact generated
`raaml-full-corpus.sysml` candidate text.

A screenshot captured the candidate file in SysML language mode with the
Problems panel stating “No problems have been detected in the workspace.” The
screenshot was retained outside the repository; its SHA-256 is:

```text
b9d4ade56afb1443431e6e8a5595dcc2512fe57970f0408f00cd18cb761e68b2
```

## Claim boundary

This result is evidence that a second SysML v2 implementation accepted the
generated candidate text in an interactive editor.

It is not:

- part of the signed `v0.9.0-rc.2` evidence;
- an automated or machine-readable conformance result;
- an independent external reproduction;
- proof that the two implementations construct identical internal models;
- proof of cross-tool semantic equivalence;
- a test of reverse reconstruction in Syside; or
- a substitute for a future pinned command-line interoperability gate.

The next stronger check would pin a second implementation and run it
automatically against the candidate output with structured diagnostics.
