# Milestone 1 coverage matrix

**Status:** Milestone 1 implementation complete; clean-environment evidence pending

The frozen expected values live in
[`oracle/corpus-baseline-v0.1.json`](../oracle/corpus-baseline-v0.1.json).
Production extraction uses `xml.etree.ElementTree`. The independent audit uses
Expat events and does not import `raaml_preservation.facts`.

The common negative test
`FactExtractionTests.test_removing_each_counted_category_is_detected` removes
one fact from each counted category. The schema-removal test independently
proves that deleting an entire required artifact category is rejected.

| Category | Raw schema path | Canonical schema path | Independent audit | Golden evidence |
|---|---|---|---|---|
| Profile | `artifact.packages[Profile]` | same, with `id` | `profiles = 9` | Core Profile name, URI, and `RAAMLC` prefix |
| Package and nesting | `artifact.packages[Package]` | same, with qualified `packagePath` | `packages = 15` | `ISO26262::RequirementManagement::SafetyGoal` path |
| Stereotype | `artifact.declarations[Stereotype]` | same, with owner-qualified `id` | `stereotypes = 94` | `CoreRAAML::Situation` |
| Base property | `declaration.properties[isBase=true]` | same, with resolved type | included in `properties = 267` | `Situation::base_Class -> UML::Class` |
| Extension / ExtensionEnd | `declaration.extensions` / `extension.ownedEnds` | same, with structural IDs | `extensions = 84`, `extensionEnds = 84` | `Situation::extension_Situation` |
| Generalization | `declaration.generalizations` | same, with resolved target and source form | declaration counts plus selected audit facts | `Situation -> SysML::Block`; both `RiskRealization` parents |
| Property | `declaration.properties` and `ownedEnds` | same, with resolved links | `properties = 267` | RiskRealization end types and redefine counts |
| Port | `property.kind = Port` | same | `ports = 65` and 4/16/45 library split | library split in baseline |
| Icon | `declaration.icons` | same | `images = 22` | corpus count baseline |
| Constraint | `declaration.constraints` | same, with owner-qualified ID | `constraints = 60` | two `ClientIsSituation` owners remain distinct |
| Library Class | `artifact.declarations[Class]` | same | `classes = 143` | corpus count baseline |
| Connector / ConnectorEnd | `declaration.connectors` / ordered `ends` | same, with structural Connector ID | `connectors = 94` and 4/21/69 split | library split in baseline |
| Enumeration / literal | `declaration[Enumeration].literals` | same; literal array remains ordered | `enumerations = 5`, `enumerationLiterals = 35` | `Exposure = [E0,E1,E2,E3,E4]` |
| AssociationClass | `declaration[AssociationClass]` | same | `associationClasses = 1` | `STPALib::RiskRealization`, member-end order and redefine counts |
| Ordinary Association | `declaration[Association]` | same; anonymous declarations use structural IDs | `associations = 40` plus per-library split | all 40 IDs unique without XMI IDs |
| Machinery | `artifact.machinery` | same, with resolved targets and structural ID | source category queries; count is not a proposal headline count | Core metamodel/package imports and library ProfileApplications are schema-required |
| Namespace prefix | `artifact.namespaces` | same | direct XML `mofext:Tag` query | Core URI maps to `RAAMLC` |
| RAAML stereotype application | `artifact.applications` | same, with resolved target | `raamlApplications = 108` | corpus count baseline |
| Comment | every owning record's `comments` | same, with resolved annotations | `comments = 431` | corpus count baseline |
| External support type | raw `href` reference | stable external qualified identity | preflight requires locked document URL | RBD time property resolves through pinned SysML 1.6 ISO 80000 artifact |

## Ordering checks

- Enumeration literals: checked by the ISO 26262 `Exposure` golden fact.
- Association and AssociationClass member ends: checked by
  `RiskRealization`.
- Connector ends: retained as arrays and covered by deterministic double
  extraction and selected golden records.
- OCL language and body lines: retained as ordered arrays. All 33 bodies
  labeled as OCL parse with Eclipse OCL Classic Ecore
  `3.22.0.v20240902-1518`; all type and property names reported by AST traversal
  resolve without ambiguity against the extracted source catalog. The 26
  JavaScript-labeled bodies are preserved but are not sent to the OCL parser.

## Identity checks

- Named declarations are qualified by artifact, recursive package path, kind,
  and name.
- The 40 ordinary Associations have 40 unique canonical identities although
  30 have no name.
- Duplicate `ClientIsSituation` constraints remain distinct under
  `Violates` and `RelevantTo`.
- Canonical output contains neither `sourceHandle` nor `sourceValue`.
- A missing local target fails with `FACT_REFERENCE_UNRESOLVED`.

## OCL boundary and negative cases

The corpus OCL gate proves parsing and AST-based type/property name resolution.
It does not prove full UML static typing, evaluate constraints, or claim
behavioral equivalence across OCL engines. Unit tests require explicit failure
for an unresolved type, ambiguous type, unresolved property, and parser
diagnostic. The Milestone 0 invalid fixture separately proves malformed OCL is
rejected.

## Remaining publication evidence

The implementation gate is complete locally. Milestone 1 evidence is published
only after the same commit passes CI in the pinned Linux container and the
canonical output produced there is byte-identical to the host-runner output.
