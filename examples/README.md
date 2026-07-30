# Examples

Examples are illustrative unless the proposal explicitly includes them in a
versioned conformance claim. The planned STPA walkthrough is outside the v0.1
claim over the 17 official definition files.

`stpa-walkthrough/wheel-brake.sysml` is a small user-model fragment that
imports the generated STPA definitions and applies `ControlStructure`,
`Controller`, and `ControlAction`. The `reproduce` command combines it with
the generated definitions and validates the result with the pinned mandatory
SysML v2 validator. It remains illustrative and is not part of the v0.1
round-trip conformance scope.
