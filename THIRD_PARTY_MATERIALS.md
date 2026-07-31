# Third-party materials policy

The project documents and tests compatibility with standards and
machine-readable artifacts published by the Object Management Group and
possibly other third parties.

Project licenses cover only original work contributed to this repository.
They do not grant rights to RAAML, SysML, UML, KerML, OCL, XMI, official XMI
files, specification text, icons, standard libraries, validator
implementations, or other third-party material.

Until an item-specific rights review permits redistribution:

- do not commit the third-party artifact;
- record its authoritative location, version, digest, byte size, and rights
  status in `standards.lock.json`;
- require the user to supply it locally or use an explicitly invoked,
  rights-compliant acquisition process;
- store it only in the ignored `sources/cache/` directory;
- never treat a local cache as project-owned source.

Current policy decisions:

- official OMG XMI remains ignored and uncommitted;
- the SysML v2 Pilot Implementation and Temurin archives remain ignored and
  uncommitted;
- canonical fact extractions, generated SysML v2 representations,
  preservation manifests, and reconstructed XMI derived from official RAAML
  definitions are not retained as downloadable CI or release artifacts until
  their redistribution status is resolved;
- `sources fetch` is an explicit user action and never runs as a side effect of
  parsing, testing, validation, or bootstrap;
- downloaded bytes must match `standards.lock.json` before use;
- the repository distributes original adapter source, not the third-party
  binaries or standards files.

The project has selected a conservative source-only publication boundary.
Complete generated outputs derived from the official corpus remain local even
if the repository becomes public. Project licenses apply only to original
expression; they do not relicense third-party names, facts, text, models, or
other material that may appear in limited source-grounded analysis.

A public release must enumerate every distributed third-party item and the
basis on which it is distributed.

The current audit, publisher decision, and hosted-output cleanup are recorded
in `docs/third-party-rights-audit.md` and
`docs/public-release-checklist.md`.
