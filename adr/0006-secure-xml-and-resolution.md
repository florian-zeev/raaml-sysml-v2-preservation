# ADR 0006: secure XML and reference resolution

**Status:** Accepted for Milestone 0

**Date:** 2026-07-27

## Decision

Treat every XML/XMI file as untrusted even after digest verification. Run a
dependency-free Expat preflight before the Java v1 loader and permit external
model references only when their document URL is present in
`standards.lock.json`.

The preflight:

- rejects DTDs, entity declarations, external entities, and XInclude;
- performs no entity or XInclude expansion;
- rejects `file:` URLs, absolute filesystem paths, path traversal, unknown URI
  schemes, and unpinned HTTP(S) documents;
- rejects symbolic-link inputs;
- limits input to 10 MiB, nesting to 256, attributes per element to 256,
  attributes per element to 1 MiB, and total character data to 32 MiB.

Known catalog URLs may use the historical `http` spelling found in the
official files or their authoritative `https` spelling. Both resolve only to
verified local bytes. Values such as `uml:Image@location` remain data and are
not dereferenced.

When an authoritative URL no longer serves its published bytes, a lock entry
may include a separate HTTPS `acquisitionUrl`. The authoritative URL remains
the model identity and the acquisition URL is only a byte-retrieval location.
The retrieved bytes must still match the locked size and SHA-256 digest. The
SysML 1.6 ISO 80000 library uses an immutable Internet Archive snapshot for
this reason; the OMG machine-readable-file index identifies the source as
`ptc/18-10-06`.

The Java loader receives only the preflighted file and preloaded local catalog.
Network fetching is never a validation fallback.

## Consequences

- Larger future inputs require a reviewed limit change.
- The preflight is a security boundary; the downstream EMF loader is not
  trusted to enforce these policies itself.
- Archive extraction independently rejects traversal and links.

## Verification

`./raaml tests unit` covers DTD/entity, XInclude, unpinned network references,
file references, traversal, symlinks, byte limits, and depth limits. Further
adversarial resource-exhaustion variants remain part of the full Milestone 0
fixture set.
