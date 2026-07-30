# ADR 0002: canonical fact identity

**Status:** Accepted for the v0.1 corpus contract

**Date:** 2026-07-27

## Decision

Identify facts from preserved engineering structure, never from original XMI
IDs, local paths, retrieval order, or unrelated XML sibling order.

The identity roots are:

- artifact: locked artifact identity;
- named package member: artifact + qualified package path + declaration kind +
  declared name;
- anonymous package member: artifact + qualified package path + declaration
  kind + canonical structural digest + duplicate ordinal;
- owned element: artifact + owner qualified identity + element kind + local
  name;
- OCL constraint: owner qualified identity + constraint name;
- stereotype application: stereotype identity + target identity + occurrence
  within the source relationship that owns the applications;
- reference: identity of the referring fact + reference role + resolved target
  identity.

Ordered values retain their source-defined order. This includes enumeration
literals, connector ends, association member ends, and OCL body lines.
Unordered values are sorted by their full composite identity and compared as
multisets.

An anonymous package member's structural digest is computed from its complete
canonical fact record after references have been resolved to canonical
identities. Self-owned ends are represented by their ordered, owner-local
identity while the digest is computed, so the definition is not circular.
`duplicate ordinal` is assigned only after byte-sorting otherwise identical
canonical records. Identical records therefore behave as a multiset and do not
inherit source package order. If another preserved fact distinguishes between
two otherwise identical anonymous declarations, v0.1 rejects the input as
ambiguous rather than consulting XMI IDs.

The `ordinal` used by `syntheticOwnedId` is the one-based position among
same-kind, same-name children in a relationship that the preservation contract
declares ordered. It is not general XML child order. Missing names are
represented explicitly, not replaced with an invented name. If same-kind,
same-name siblings cannot be distinguished by an in-scope ordered relationship
or another preserved fact, v0.1 rejects the input as ambiguous.

Package membership is recursive. For example, a declaration inside a package
owned by a profile includes both the profile and nested-package segments in its
qualified package path.

Names containing the `::` field separator are unsupported in v0.1. A
synthetic-ID collision stops the run.

## Consequences

- The original MagicDraw XMI IDs are deliberately excluded.
- The fact schemas must carry enough owner, kind, ordering, and resolved
  target information to implement every key above.
- The 30 unnamed ordinary Associations, 94 unnamed Connectors, 27 unnamed
  Constraints, and 37 unnamed Properties in the locked corpus cannot be keyed
  by a guessed label.
- Every fact category needs an ambiguity and collision test before mapping.

## Verification

- two extractions of the verified corpus are byte-identical;
- same local names under different owners remain distinct;
- duplicate owner-qualified constraints remain distinct;
- unnamed declarations remain distinct without preserving XMI IDs or package
  sibling order;
- ambiguous same-owner siblings fail;
- an injected hash collision fails.
