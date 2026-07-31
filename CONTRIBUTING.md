# Contributing

This project welcomes technical review and implementation contributions.

## Current phase

The project has a signed reference candidate and is open for community review.
Contributions should reproduce, challenge, or improve the stated
preservation contract without broadening its claims silently. Start with the
[`external review guide`](docs/external-review-guide.md) and
[`validation report`](docs/validation-report-v0.9.0-rc.3.md).

## Contribution rules

- Keep the project independent of M45 product code and infrastructure.
- Do not commit official OMG files or other third-party material unless the
  repository documents permission to redistribute the exact material.
- Do not broaden the conformance claim beyond the 17 named RAAML 1.1
  definition files without a versioned proposal change.
- Add or update tests when changing a schema, preservation rule, identity
  rule, or transformation rule.
- Keep generated outputs deterministic.
- Record important technical decisions in `adr/`.
- Use US spelling in project documentation.

Contributions are accepted under the license that applies to the modified
file. By submitting a contribution, you confirm that you have the right to
provide it under that license.

## Pull requests

Changes to `main` must use a pull request and pass the required validation and
code-scanning checks. Use a focused branch, complete the pull-request
template, and keep unrelated changes separate.

External workflow runs require maintainer approval. The maintainer will review
the proposed diff, especially changes under `.github/workflows/`, before
allowing the workflow to execute.
