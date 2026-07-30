# Milestone 7 reproducibility and release evidence

**Status:** Implementation complete; clean-environment evidence and signed
candidate tag pending

**Candidate tag:** `v0.9.0-rc.1`

## Purpose

Milestone 6 proved the preservation claim. Milestone 7 packages the evidence
so another person can inspect and reproduce it without reconstructing the
project's development history.

The stable command is:

```text
./raaml reproduce \
  --clean \
  --container-digest sha256:<64 lowercase hexadecimal digits> \
  --release-tag v0.9.0-rc.1 \
  --output-dir generated/release-candidate
```

The command never downloads anything. The locked sources and pinned tools
must already be present and verified.

## Release directory

The command creates a new output directory atomically and refuses to replace
an existing path. It contains:

- raw and canonical source facts;
- the independent corpus audit and OCL result;
- the generated full-corpus SysML v2 model and all 17 preservation manifests;
- all 17 reconstructed SysML v1 artifacts;
- mandatory v1 and v2 validator reports;
- the full source/reconstructed comparison and adversarial-case report;
- a controlled one-fact v2 and manifest diff;
- the combined, validator-checked STPA walkthrough;
- `RELEASE.json`, containing source, schema, tool, Git, container, and result
  identity; and
- `SHA256SUMS`, covering every other file in the directory.

`RELEASE.json` records whether the source tree was clean or dirty.
`reproduce --clean` fails before producing output if Git reports a dirty
checkout. A container source tree without `.git` must receive the exact
commit and source state through its pinned build metadata.

## Controlled diff

The illustrative diff changes exactly one canonical input fact:

```text
FTALib::HouseEventProbability::NOT_OCCUR
    becomes
FTALib::HouseEventProbability::DOES_NOT_OCCUR
```

The command records the deterministic unified diff of the SysML v2 model and
the affected preservation manifest. This demonstrates focused behavior for
one controlled example. It does not support a general claim that every
semantic change will always produce a small textual diff.

The official locked source is never changed. The mutation is applied to a
copy of the canonical forward-mapper input.

## STPA walkthrough

The wheel-brake walkthrough imports the generated `STPA` package and applies
the generated `ControlStructure`, `Controller`, and `ControlAction`
definitions to a small model. The release gate combines the fragment with the
generated RAAML definitions and requires the mandatory SysML v2 validator to
accept the complete model.

The walkthrough shows how the preserved definitions can be used. It is an
illustrative user model and remains outside the v0.1 conformance claim over
the 17 official definition files.

## Clean-environment gate

CI:

1. builds the digest-identified Linux container from a clean commit;
2. runs `reproduce --clean` on the Linux host;
3. runs the same command inside the container with networking disabled;
4. compares the entire release directories recursively;
5. retains the private release candidate for 30 days; and
6. fails on any byte difference.

The release report explicitly says that independent reproduction by a person
outside the project has not yet occurred.

## Signed tag boundary

The candidate tag must not be created before the clean-environment gate
passes. After it passes, the project will:

1. freeze the successful commit and run identity;
2. create a cryptographically signed annotated tag `v0.9.0-rc.1`;
3. verify the tag signature;
4. retain the tag and `SHA256SUMS` through the chosen release channel; and
5. record the signer and verification method without exposing private key
   material.

Publication remains subject to the third-party rights review.
