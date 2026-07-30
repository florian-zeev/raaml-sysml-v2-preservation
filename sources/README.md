# Standards source material

Official standards artifacts are not committed to this repository until an
item-specific rights review permits redistribution.

`standards.lock.json` records authoritative locations,
exact versions, OMG file identifiers where applicable, byte sizes, SHA-256
digests, local filenames, normative or informative status, and redistribution
status.

Locally supplied files belong in `sources/cache/`. The directory is ignored
except for its placeholder. Verification must occur before any file is parsed
as an accepted standards input.

Source acquisition must always be explicit. Parsing, validation, tests, and
conformance commands must not fetch files implicitly.

To acquire all currently locked files explicitly:

```text
./raaml sources fetch
```

This is the only source command that uses the network. It downloads to a
temporary file, enforces the locked maximum byte size, verifies SHA-256 and
exact size, and then renames the file into the ignored cache. It refuses to
overwrite an existing unverified file.

To verify the locked RAAML 1.1 definition files:

```text
./raaml sources verify --collection raaml-1.1-definitions
```

The command performs no network access. It rejects missing files, changed
sizes or hashes, symbolic links, unsafe filenames, duplicate lock identities,
and malformed lock entries. A machine-readable report is written under
`reports/diagnostics/`.

To verify the complete current lock, including UML/SysML reference models and
the validator tool distributions:

```text
./raaml sources verify
```
