# ADR 0004: UML and SysML v1 loading

**Status:** Accepted with a documented compatibility adapter
**Date:** 2026-07-27

## Decision

Use Eclipse UML2 `5.5.0.v20221116-1811`, bundled in the pinned SysML pilot
distribution, to load and validate UML/SysML v1 artifacts. Resolve the verified
UML 2.5.1, SysML 1.6, and RAAML files only from the pinned local catalog.

## UML 2.5.1 namespace compatibility

RAAML 1.1 uses the UML 2.5.1 namespace and references dated `20161101`.
The bundled Eclipse loader's OMG interchange adapter recognizes the UML 2.5
`20131001` namespace. The adapter therefore performs an in-memory validation
view with two explicit changes:

1. replace only the UML namespace and UML standard-document URI date
   `20161101` with `20131001`;
2. for an untyped external `href`, resolve the target from the pinned local
   catalog and add its concrete UML `xmi:type` to the in-memory view.

The verified source bytes are never changed. Extraction and round-trip
comparison must operate on the original bytes and preserve their original
URIs. The adaptation exists only at the loader boundary and must be reported
with validation results.

This is preferable to calling a generic XML parse a UML validation pass. It is
also a limitation: the project has not demonstrated that every UML 2.5.1
feature is equivalent under the namespace view. The v0.1 claim is restricted
to the 17 official RAAML definition files.

## Validation behavior

The adapter:

- preloads verified UML, PrimitiveTypes, StandardProfile, and SysML resources;
- defines and registers the CoreRAAML profile before loading its library;
- disables implicit acquisition by using only catalog resources;
- resolves all proxies;
- treats resource errors, unresolved proxies, and model diagnostics at error
  severity as failure.

## Verification

```text
./raaml validate-v1 fixtures/milestone-0/minimal-v1-profile.xmi
./raaml validate-v1 fixtures/milestone-0/minimal-v1-library.xmi
./raaml validate-v1 fixtures/milestone-0/minimal-v1-invalid-reference.xmi
./raaml validate-v1 sources/cache/CoreRAAML.xmi
./raaml validate-v1 sources/cache/CoreRAAMLLib.xmi
```
