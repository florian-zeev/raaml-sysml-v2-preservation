# Preserving RAAML 1.1 definitions in SysML v2

This repository contains a community proposal and reference implementation
for carrying the 17 normative RAAML 1.1 definition files through SysML v2
without losing a defined set of source facts.

The project does not define a new version of RAAML or redesign RAAML for
native SysML v2 use. Its narrower purpose is to preserve the normative RAAML
1.1 definitions, and it does not claim support for arbitrary user-authored
RAAML models.

## Result

The signed candidate `v0.9.0-rc.1` completed the full 17-file round trip with:

- zero differences in the defined canonical fact set;
- zero errors from the pinned SysML v1 and SysML v2 validators;
- all 33 source OCL expressions parsed and name-resolved;
- 36 adversarial cases passed;
- 343 source identities bound to generated native v2 targets; and
- byte-identical 49-file release directories from a clean Linux host and an
  offline pinned container.

The candidate supports a bounded preservation claim:

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

It does not establish interoperability with a second SysML v2
implementation, independent external reproduction, behavioral equivalence of
OCL, certification suitability, or permission to redistribute all
third-party source material.

The repository remains private while the third-party rights review is
completed.

## Start here

| Document | Purpose |
| --- | --- |
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | Exact first-time setup, reproduction, and integration instructions |
| [`docs/executive-summary.md`](docs/executive-summary.md) | Plain-language motivation and result |
| [`proposal/community-proposal-v0.1.md`](proposal/community-proposal-v0.1.md) | Draft paper and claim boundary |
| [`proposal/normative-encoding-v0.1.md`](proposal/normative-encoding-v0.1.md) | Detailed preservation and reconstruction rules |
| [`docs/validation-report-v0.9.0-rc.1.md`](docs/validation-report-v0.9.0-rc.1.md) | Consolidated validation, reproducibility, and signed evidence |
| [`docs/third-party-rights-audit.md`](docs/third-party-rights-audit.md) | Publication boundary and remaining permission request |
| [`docs/external-review-guide.md`](docs/external-review-guide.md) | Reviewer questions and remaining publication gates |
| [`docs/fact-contract-v0.1.md`](docs/fact-contract-v0.1.md) | Canonical fact identity and comparison contract |
| [`docs/transformation-analysis-v0.1.md`](docs/transformation-analysis-v0.1.md) | Comparison with the official SysML v1-to-v2 transformation |

Machine-readable transformation analysis is under [`analysis/`](analysis/).
Architecture decisions are under [`adr/`](adr/).

## Reproduce the signed candidate

Python 3.14.4 is the tested orchestration runtime. Only `sources fetch` uses
the network.

```text
./raaml sources fetch
./raaml sources verify
./raaml tooling bootstrap
./raaml reproduce --clean \
  --container-digest sha256:<container-image-id> \
  --release-tag v0.9.0-rc.1 \
  --output-dir generated/release-candidate
```

The release command verifies the full forward mapping, reverse mapping,
canonical comparison, validators, adversarial suite, controlled diff, and
STPA walkthrough. It creates `RELEASE.json` and `SHA256SUMS` in the output
directory.

Verify the candidate tag:

```text
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=.github/allowed_signers \
    tag -v v0.9.0-rc.1
```

See the [validation report](docs/validation-report-v0.9.0-rc.1.md) for the
expected commit, container image, canonical fact hash, and signature
fingerprint.

## Independent clean-room reproduction

A reviewer working from a source-only archive does not have the repository's
Git history or signed tags. For that case, install Docker with
`linux/amd64` support, then run:

```text
./review-reproduce
```

This command builds the digest-pinned validation container, uses that container
to fetch the locked official inputs, and then runs the semantic reproduction
in a second container with networking disabled. It checks the expected
canonical hash, zero fact differences, both validators, and the adversarial
suite. No host Python or Java installation is required.

The command writes only the aggregate reviewer result and diagnostics to the
ignored `review-evidence/` directory. It does not retain the generated SysML
v2 corpus, preservation manifests, reconstructed XMI, or full comparison
record. Reviewers should return `review-result.json` together with their
platform and Docker version.

## Repository boundary

This is a standalone community project. It does not depend on M45 product
code, databases, authentication, or deployment infrastructure. Other tools
may consume versioned releases without becoming part of this repository.

The public interface is a deterministic command-line tool operating on files
and producing SysML v2 text, JSON preservation records, reconstructed XMI,
structured diagnostics, and conformance reports.

## Source material

Official OMG specifications, XMI files, icons, and other third-party material
are not licensed by this repository. They are not committed unless a separate
rights review permits redistribution. See
[`THIRD_PARTY_MATERIALS.md`](THIRD_PARTY_MATERIALS.md) and
[`sources/README.md`](sources/README.md).

## Licensing

Original software is licensed under Apache-2.0. Original proposal text,
documentation, and schemas are licensed under CC-BY-4.0. Third-party material
is excluded. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
