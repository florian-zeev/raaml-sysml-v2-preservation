# Milestone 2 transformation analysis

**Status:** In progress

**Date started:** 2026-07-28

## Purpose

Milestone 2 compares the RAAML preservation proposal with the official SysML
v1-to-v2 transformation before mapper code is written. The comparison has two
separate questions:

1. What v2 element does the official transformation create?
2. What additional source facts must this project retain to reconstruct the
   official RAAML 1.1 files exactly within the v0.1 preservation contract?

The preservation layer should supplement the official transformation where
the official target does not retain enough information for reversal. It should
deviate only when the official target cannot serve the proposal's stated
purpose, and every deviation must have a written reason and test obligation.

## Normative inputs

| Input | OMG identity | Locked SHA-256 |
| --- | --- | --- |
| SysML v1 to SysML v2 Transformation, SysML 2.0 Part 2 | `formal/26-03-03` | `64366027dfef1ab630f741884695a68471939fcf68c3c7d874790d2c86ea518c` |
| Machine-readable transformation model | `ptc/25-04-10` | `093359439fb62cb3a9b1e89fd850ac4ac0b4bbe135b4b54f7861492722cc8459` |

The files are acquired and verified through `standards.lock.json`. They are
not committed or redistributed by this project.

## Corpus surface that requires a decision

The frozen Milestone 1 baseline contains:

| Source construct | Count |
| --- | ---: |
| Profiles | 9 |
| Nested packages | 15 |
| Stereotypes | 94 |
| Library classes | 143 |
| Enumerations / literals | 5 / 35 |
| Associations / AssociationClasses | 40 / 1 |
| Properties / Ports | 267 / 65 |
| Connectors | 94 |
| Constraints | 60 |
| Generalizations | 219 |
| Extensions / ExtensionEnds | 84 / 84 |
| Comments / images | 431 / 22 |
| Metamodel references / package imports / profile applications | 9 / 9 / 8 |
| Normative RAAML stereotype applications | 108 |

This list is the minimum transformation surface. A mapping decision that is
not exercised by one of these categories is outside the v0.1 corpus claim.

## Classification meanings

- **Reuse:** Apply the official rule without changing its semantic target.
- **Specialize:** Apply a more specific official rule because the source meets
  its filter, such as a SysML v1 Block rather than a plain UML Class.
- **Supplement:** Apply the official rule and retain additional source facts
  in the preservation representation.
- **Deviate:** Deliberately choose a different v2 target or behavior.
- **Open:** The evidence is not yet sufficient to classify the row.

## Initial rule matrix

The machine-rule identifiers below are XMI IDs in the pinned
`SysMLv1Tov2.xmi`.

| RAAML source construct | Official transformation | Clause / machine rule | Initial classification | Preservation consequence |
| --- | --- | --- | --- | --- |
| UML Profile | Package | 7.7.9.3.21; `Mappings-UML4SysML-Packages-Profile_Mapping` | Supplement | Reuse the Package target; retain profile identity, URI, comments, and namespace-prefix facts needed for reversal. |
| UML Package | Package, including URI metadata when present | 7.7.9.3.11; `Mappings-UML4SysML-Packages-Package_Mapping` | Supplement | Reuse package nesting and URI mapping; retain source presence and artifact identity. |
| UML PackageImport | NamespaceImport | 7.7.9.3.12; `Mappings-UML4SysML-Packages-PackageImport_Mapping` | Supplement | Reuse the import; retain the exact source reference form and target identity. |
| UML MetamodelReference | Underlying PackageImport behavior | 7.7.9.3.12 plus the source stereotype | Open | Determine whether the official stereotype-processing rules preserve the distinction or whether the manifest must do so alone. |
| UML ProfileApplication | Not mapped | 7.7.9.1-7.7.9.2, Tables 12-13 | Supplement | Preserve each profile application and target in the manifest so it can be reconstructed. |
| UML Stereotype | MetadataDefinition | 7.7.9.3.24; `Mappings-UML4SysML-Packages-StereotypeMetadataDefinition_Mapping` | Supplement | The MetadataDefinition is the normative v2 carrier. Retain source bases, extension details, generalizations, properties, icons, constraints, and comments for reversal. |
| UML Extension / ExtensionEnd | Handled in the Stereotype mapping context | 7.7.9.1-7.7.9.2, Tables 12-13; stereotype occurrence rules 7.7.9.3.26-34 | Supplement | Reuse the official annotation-target machinery; retain exact base-property ownership, multiplicity, ExtensionEnd name, and href spelling. |
| UML Generalization | Subclassification | 7.7.4.2.12; `Mappings-UML4SysML-Classification-Generalization_Mapping` | Supplement | Reuse Subclassification; retain local-versus-external reference form and exact target identity. |
| UML Class in a RAAML library | OccurrenceDefinition | 7.7.12.2.10; `Mappings-UML4SysML-StructuredClassifiers-Class_Mapping` | Open - likely reuse | The current proposal's generic `Definition`/`def` carrier conflicts with the official rule and does not yet identify executable generic textual syntax. Resolve before the vertical slice. |
| SysML v1 Block application | PartDefinition | 7.8.4.3.3; `Mappings-SysMLv1-Blocks-Block_Mapping` | Specialize | Use the Block rule when the actual source Class has Block applied. Do not infer Block application only from a RAAML stereotype's inheritance graph. |
| UML Enumeration | EnumerationDefinition | 7.7.10.2.11; `Mappings-UML4SysML-SimpleClassifiers-Enumeration_Mapping` | Supplement | Reuse the definition; retain literal order and exact source ownership. |
| UML EnumerationLiteral | EnumerationUsage | 7.7.10.2.12; `Mappings-UML4SysML-SimpleClassifiers-EnumerationLiteral_Mapping` | Supplement | Reuse the usage and preserve ordered membership. |
| UML AssociationClass | ConnectionDefinition | 7.7.12.2.1; `Mappings-UML4SysML-StructuredClassifiers-AssociationClass_Mapping` | Supplement | Reuse the connection target; retain the Class facet, parent kinds, owned-end facts, and an explicit AssociationClass discriminator. |
| UML Association | ConnectionDefinition | 7.7.12.2.2 and 7.7.12.2.20; `AssociationCommon_Mapping`, `ConnectorType_Mapping` | Supplement | Reuse the connection target; retain association ownership, ordered member ends, navigability, multiplicity presence, and an Association discriminator. |
| UML Property | AttributeUsage, OccurrenceUsage, Feature, or association-end Feature depending on source shape | 7.7.4.2.35-38; 7.7.10.2.1-5; 7.7.12.2.30-35 | Open | Build a corpus decision table from type, aggregation, association ownership, and redefinition/subsetting. Do not use the proposal's shorter three-row table until it is checked against every official filter. |
| UML Port | PortUsage | 7.7.12.2.36-37; `Port_Mapping`, `PortUntyped_Mapping` | Supplement | All 51 typed and 14 untyped corpus Ports have an official target. Retain original type reference, multiplicity presence, and Port-versus-Property identity. |
| UML Connector | ConnectionUsage | 7.7.12.2.14; `Mappings-UML4SysML-StructuredClassifiers-Connector_Mapping` | Supplement | Reuse ConnectionUsage; retain ordered ends, role, `partWithPort`, visibility, and source ownership. |
| UML ConnectorEnd | Feature-based connector-end mappings | 7.7.12.2.15-19 | Supplement | Reuse the official end representation; preserve the exact ordered source-end records for reversal. |
| UML Comment | Comment plus Annotation | 7.7.6.2.2-4; `Comment_Mapping`, `CommentAnnotation_Mapping`, `CommentOwnership_Mapping` | Supplement | Reuse Comment/Annotation; retain exact body, owner, and all annotated-element references. |
| UML Constraint | ConstraintDefinition plus AssertConstraintUsage | 7.7.6.2.5-8; `Constraint_Mapping`, `ConstraintUsage_Mapping` | Open - likely supplement | Generate the official v2 view, but keep the original constraint store authoritative for reversal until behavioral equivalence is demonstrated. |
| UML OpaqueExpression used by a constraint | CalculationUsage and language/body specification | 7.7.14.3.18 and 7.7.14.3.31; `OpaqueExpression_Mapping`, `OpaqueExpressionSpecification_Mapping` | Open - likely supplement | Check whether the official output retains every language/body line and ordering fact. Preserve the source expression regardless. |
| UML Image | Not mapped; mapping not specified | 7.7.9.1-7.7.9.2, Tables 12-13 | Supplement | Store format, location, encoding, and content in the preservation representation. Do not invent a normative native-v2 icon mapping. |
| RAAML stereotype application in a library | Official arbitrary-stereotype processing is partly implementation-specific | 7.2.2 Helper `getAppliedStereotypes`; stereotype occurrence rules 7.7.9.3.26-34 | Open | Determine the exact official target for the 108 applications and whether tagged values survive. The manifest remains required until this is proven. |
| Namespace prefix / MagicDraw `mofext:Tag` | No direct rule identified | No machine rule identified | Supplement | Preserve as artifact metadata; do not present it as native SysML v2 semantics. |
| Exact URL spelling, XMI ownership, explicit-default presence, icon bytes, and source IDs | Not preservation goals of the general semantic transformation | Cross-cutting | Supplement | Keep only the facts included by the v0.1 preservation contract. Original MagicDraw XMI IDs remain excluded. |

## First material findings

### 1. The proposal's generic library `Definition` is not yet defensible

The official `Class_Mapping` target is `OccurrenceDefinition`. The current
proposal says a UML library Class becomes a generic `Definition` or textual
`def`, but it does not identify a concrete generic SysML v2 textual production
that has been validated by the pinned parser.

The likely correction is to reuse `OccurrenceDefinition` for plain UML
Classes, then apply more specific official SysML v1 rules when the actual
source element meets their filters. This decision remains open until its
effect on RAAML library properties and associations is checked.

### 2. A RAAML stereotype is first a MetadataDefinition

The official transformation does not choose `PartDefinition`,
`OccurrenceDefinition`, or `ItemDefinition` as the primary replacement for a
UML Stereotype. It maps the Stereotype to a `MetadataDefinition` and handles
its extensions in that context.

The proposal's base-metaclass precedence table may still be useful for
constraining what the metadata may annotate or for generating optional
domain-oriented views. It should not replace the official stereotype mapping
without an explicit deviation.

### 3. The preservation manifest remains necessary

The official transformation explicitly leaves Images and ProfileApplications
unmapped. It also does not aim to retain every XMI-level distinction needed for
the proposed reverse reconstruction, such as exact href spelling, explicit
default presence, ExtensionEnd names, or association-end ownership.

The manifest is therefore not a competing transformation. It is the
supplement that makes the narrower round-trip preservation claim testable.

### 4. OCL should have two clearly separated roles

The official transformation maps a UML Constraint and its OpaqueExpression to
native v2 constraint/calculation elements. The proposal currently retains OCL
in a sidecar and treats a native v2 constraint as optional.

Milestone 2 must decide whether the forward mapper always emits the official
native view while also retaining the exact source constraint. Emitting both
would follow the official transformation without claiming that the native
constraint behaves identically to the original OCL.

## Reproduction commands

After acquiring the locked inputs:

```text
./raaml sources verify
pdftotext -layout \
  sources/cache/SysML-2.0-Transformation.pdf \
  tmp/pdfs/SysML-2.0-Transformation.txt
```

Relevant machine rules can be located by XMI ID in
`sources/cache/SysMLv1Tov2.xmi`. The final Milestone 2 gate will automate that
check and fail if a cited rule is absent from the pinned model.

## Work remaining

1. Derive the complete Property decision table from the official filters and
   classify every one of the 332 Property/Port records.
2. Resolve how the official transformation represents arbitrary RAAML
   stereotype applications and tagged values.
3. Resolve MetamodelReference and namespace-prefix treatment.
4. Decide the Class carrier and remove generic shorthand that cannot be
   validated as SysML v2 text.
5. Decide whether the native Constraint/Calculation view is mandatory.
6. Turn this matrix into a machine-readable artifact whose rule IDs are checked
   against the pinned XMI.
7. Update the community proposal and normative encoding only after no row
   remains `Open`.
