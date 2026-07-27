# Standards source material

Official standards artifacts are not committed to this repository until an
item-specific rights review permits redistribution.

Milestone 0 will populate `standards.lock.json` with authoritative locations,
exact versions, OMG file identifiers where applicable, byte sizes, SHA-256
digests, local filenames, normative or informative status, and redistribution
status.

Locally supplied files belong in `sources/cache/`. The directory is ignored
except for its placeholder. Verification must occur before any file is parsed
as an accepted standards input.

Source acquisition must always be explicit. Parsing, validation, tests, and
conformance commands must not fetch files implicitly.
