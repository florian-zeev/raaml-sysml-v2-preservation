# ADR 0002: canonical fact identity

**Status:** Accepted for the v0.1 corpus contract
**Date:** 2026-07-27

## Decision

Identify facts from preserved engineering structure, never from original XMI
IDs, local paths, retrieval order, or unrelated XML sibling order.

The identity roots are:

- artifact: locked artifact identity;
- top-level declaration: artifact + declaration kind + declared name;
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

The `ordinal` used by `syntheticOwnedId` is the one-based position among
same-kind, same-name children in a relationship that the preservation contract
declares ordered. It is not general XML child order. If same-kind, same-name
siblings cannot be distinguished by an in-scope ordered relationship or
another preserved fact, v0.1 rejects the input as ambiguous.

Names containing the `::` field separator are unsupported in v0.1. A
synthetic-ID collision stops the run.

## Consequences

- The original MagicDraw XMI IDs are deliberately excluded.
- Milestone 1 schemas must carry enough owner, kind, ordering, and resolved
  target information to implement every key above.
- Every fact category needs an ambiguity and collision test before mapping.

## Verification required in Milestone 1

- two extractions of the verified corpus are byte-identical;
- same local names under different owners remain distinct;
- duplicate owner-qualified constraints remain distinct;
- ambiguous same-owner siblings fail;
- an injected hash collision fails.
