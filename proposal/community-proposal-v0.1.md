# Preserving RAAML 1.1 definitions in SysML v2

## Draft Community Proposal v0.1

**Author:** Florian Wolf, M45 Engineering
**Status:** Draft for community review; not an OMG specification or submission
**Intended document license:** Creative Commons Attribution 4.0 International (CC BY 4.0), subject to separate review of third-party material
**Planned reference-implementation license:** Apache License 2.0

## Abstract

RAAML 1.1 gives safety and reliability concepts a precise form that software can inspect. A hazard, unsafe control action, fault-tree gate, or assurance claim is not merely text on a diagram. It has a type, properties, and defined links to other parts of the system model.

The difficulty is that RAAML 1.1 was built for SysML v1, while SysML v2 is built on different underlying rules. In SysML v1, RAAML concepts are UML stereotypes applied to elements such as classes, properties, and signals. SysML v2 uses KerML and metadata definitions instead. A v1 stereotype therefore cannot simply be copied into a v2 model. Someone must decide what it becomes, and that decision can lose information.

This paper proposes a conservative way to carry the 17 official RAAML 1.1 definition files—nine profiles and eight libraries—through SysML v2. Each RAAML definition receives a useful v2 form. A separate preservation record keeps the v1 facts that this form does not express clearly enough on its own. Information that belongs to the whole source file, such as imports and OCL constraints, is stored once in a JSON manifest beside the v2 model.

Version 0.1 defines what must be preserved and how to test it. It does not yet claim that the proposed transformation works. It does not cover arbitrary user models, and it does not attempt to design RAAML 2.0. The next step is an open reference implementation that converts the official files to v2, converts them back, and reports every fact that changed or disappeared.

## 1. The problem

RAAML 1.1 supports STPA, FTA, FMEA, RBD, GSN, ISO 26262 analysis, and security analysis. Its profiles connect those analyses to the SysML model of the system being studied. This lets a tool distinguish a typed safety concept from an informal label.

Why move this work to SysML v2 at all? For an existing, long-running program, remaining on SysML v1 may be the right choice. SysML v1 is widely used, and this proposal does not argue that organizations should abandon working tools or validated processes.

The need arises when a program, supplier, or tool begins using SysML v2. SysML v2 is now a formal OMG standard, and new tools, training, and engineering programs are beginning to build around it. If the system architecture moves to v2 while the safety analysis remains in a separate v1 environment, the connections between system elements, hazards, failure modes, controls, assurance claims, and evidence become harder to maintain. Teams may duplicate the models or create local translations. Different local translations can preserve different facts and gradually make the same RAAML concept mean different things in different tools.

SysML v2 also defines a standard textual notation. SysML v1 models can be stored as textual XMI, but those files are commonly verbose, tool-dependent, and unstable under ordinary editing: a small model change may produce a large file diff that is difficult for a person to review. A stable textual representation makes established version-control practices more practical for systems and safety models. Engineers can review a focused change, connect it to a requirement or approval, run automated checks, and identify the exact model version to which an analysis applies.

Git can provide a practical foundation for tamper-evident model history because stored objects are identified by hashes of their contents and each commit refers to its parent history. Changing an earlier artifact changes the identifiers built from it. Git alone is not tamper-proof: a party with enough control can replace the published history. Safety or certification use therefore also requires controls such as signed release tags, protected branches, independent retention of baseline identifiers, controlled access, and explicit approval records.

SysML v2 changes the machinery underneath the language. SysML v1 extends UML; SysML v2 is built on KerML. In practical terms, they use different kinds of model elements, different extension mechanisms, and different file structures. A UML stereotype that extends `Class`, `Property`, or `Signal` has no automatic one-to-one replacement in SysML v2.

SysML v1 will not disappear as SysML v2 adoption grows. Companies, suppliers, tools, and certification processes will move at different speeds. For some time, the same program may need both. We therefore need a way to carry the existing RAAML 1.1 definitions into SysML v2 without pretending that we have already designed their final v2 replacements.

This proposal asks one narrow question:

> Can we represent the official RAAML 1.1 definitions in SysML v2 and later reconstruct the same defined set of v1 facts?

It does not ask what the best native RAAML for SysML v2 should look like. That is a larger standards question.

## 2. What this proposal adds

The proposal adds five things:

1. **A clear boundary.** Version 0.1 covers the 17 official RAAML 1.1 definition files. It does not quietly extend its claim to every model a user might create.
2. **A written list of facts that must survive.** “Lossless” means nothing unless the document states exactly what counts as information.
3. **A two-part representation.** The chosen v2 element makes the definition usable in v2. A preservation record keeps the v1 details that the chosen element cannot express by itself.
4. **A safe treatment of OCL.** The original constraint text, its owner, and the elements it constrains are preserved. The proposal does not declare a v2 constraint equivalent without proving it.
5. **A repeatable test.** An implementation must extract the facts before and after the round trip and show the differences.

The companion specification, `normative-encoding-v0.1.md`, contains the complete field definitions, mapping tables, and reconstruction rules.

## 3. Background

### 3.1 RAAML 1.1

The OMG published formal RAAML 1.1 in December 2025. The standard includes official machine-readable profiles and libraries for CoreRAAML, GeneralRAAML, STPA, FTA, FMEA, RBD, GSN, ISO 26262, and GeneralRAAMLSecurity.

In SysML v1, a profile adds specialized meanings to existing UML elements. For example, a stereotype can say that a particular UML Class represents a hazard, or that a Property plays the role of a controller. The library files provide the classes, associations, enumerations, Ports, and connectors used by those profiles.

### 3.2 SysML v2 and KerML

The OMG published formal SysML 2.0 and KerML 1.0 in September 2025. KerML defines the basic concepts on which SysML v2 is built, much as UML provides the foundation used by SysML v1. Because the foundations differ, the two languages do not store or extend models in the same way.

SysML v2 includes metadata definitions, definitions and usages, standard libraries, textual notation, and new interchange formats. Its formal publication also includes a general transformation from SysML v1 to SysML v2. Before mapping begins, the reference implementation will compare every transformation rule needed by the RAAML corpus with that official transformation and publish where it reuses, specializes, supplements, or deliberately differs from it.

### 3.3 The wider tool problem

This is one example of a wider problem: engineering work is spread across specialized tools that will continue to exist.

CASCaRA is working on a common way to connect and inspect engineering information across such tools. Digital-certification groups such as EUROCAE WG-136 are examining how regulations and certification work can become easier to navigate electronically. This proposal does not solve either problem. It addresses one small but difficult boundary within them: carrying a standardized safety vocabulary from one modeling-language generation to another without hiding what changed.

## 4. Exact scope

### 4.1 Included in version 0.1

The source consists of:

- nine profile files: CoreRAAML, GeneralRAAML, STPA, FTA, FMEA, RBD, GSN, ISO26262, and GeneralRAAMLSecurity;
- eight library files: CoreRAAMLLib, GeneralRAAMLLib, STPALib, FTALib, FMEALib, RBDLib, ISO26262Lib, and GeneralRAAMLSecurityLib.

The test includes these facts:

- profile and package names, URIs, comments, imports, profile applications, and namespace information;
- stereotypes, the UML elements they extend, inheritance, properties, comments, icons, and OCL constraints;
- library classes, properties, Ports, connectors, enumerations, AssociationClasses, and ordinary associations;
- stereotype applications already contained in the official library files;
- every reference needed to identify the owner, type, or target of one of those facts.

Here, “official” or “normative” means that the file is part of the machine-readable RAAML 1.1 material published by the OMG.

### 4.2 Not included in version 0.1

Version 0.1 does not promise to preserve:

- RAAML models created by users;
- models created directly in SysML v2;
- the original XMI IDs, whitespace, or ordering of unrelated XML elements;
- diagram layout;
- identical behavior in every OCL engine;
- a native RAAML 2.0 design.

It also makes no claim of approval or endorsement by OMG, EUROCAE, CASCaRA, or any other group.

## 5. What “preserved” means

For each source file, the implementation first extracts a standard list of facts. It then performs the proposed conversion to SysML v2, converts the result back to v1 XMI, and extracts the same kind of list again.

If `facts(x)` means “the facts extracted from file `x`,” the required test is:

```text
facts(reverse(forward(source))) = facts(source)
```

This is not a comparison of XML text. Two files can use different IDs or spacing and still describe the same in-scope facts.

The proposal does not yet call the mapping a bijection. That stronger word would require a clearly defined set of allowed v2 inputs and proof that conversion in the opposite direction also returns each of them unchanged. Version 0.1 tests only the official v1 files through the v2 form generated by this proposal.

### 5.1 How facts are compared

Some facts are unordered. For example, two sets of generalizations are equal if they contain the same resolved targets. Other facts are ordered. Enumeration literals, connector ends, and association member ends must appear in the same sequence.

Values also keep their kind. The number `1`, the string `"1"`, and an enumeration literal named `1` are not treated as the same value. A cross-file reference is compared by the element it identifies, not merely by the text of a temporary ID.

### 5.2 Why a manifest is needed

Not every source fact belongs naturally on one v2 definition. A profile name, an import, or a package-level comment belongs to the file as a whole. OCL constraints also need stable ownership and context.

Each generated v2 file therefore has a JSON preservation manifest beside it. The manifest records:

- which source file this is;
- whether it defines a profile or a library;
- its profile or package name and URI;
- comments, imports, profile applications, and namespace information;
- OCL constraints and the information needed to resolve their references.

The manifest is required. It is part of the representation, not merely background information about where the model came from. Version 0.1 chooses one JSON form so that two implementations can be compared without first deciding whether two different sidecar formats mean the same thing.

## 6. How the mapping works

### 6.1 Stereotypes become metadata definitions

Each RAAML stereotype becomes a SysML v2 metadata definition. The mapper chooses a primary v2 form based on the UML elements that the stereotype extends and on its inheritance chain.

The chosen form does not replace the source facts. It is the part a v2 tool works with directly. The preservation record holds the original UML bases, generalizations, properties, extension ends, icons, and OCL references needed to reconstruct the v1 definition.

### 6.2 Choosing one v2 form when several seem possible

The same input must lead to the same choice. Representative rules are:

- a stereotype based on UML `Property` becomes an appropriate v2 usage;
- when a stereotype extends `Signal`, `Class`, and `DataType`, `Signal` takes precedence and the primary form is an `ItemDefinition`;
- a Class-based stereotype that inherits from the SysML v1 `Block` stereotype becomes a `PartDefinition`;
- `CoreRAAML::Situation` and its descendants become `OccurrenceDefinition`s;
- relationship stereotypes keep their exact RAAML identity even when v2 has a nearby relationship concept.

The important point is simple: choosing one form must not erase the other source facts.

### 6.3 Library elements

Version 0.1 maps every UML library Class conservatively to a v2 `Definition`. It does not guess that a class is an occurrence merely because its name sounds like one.

Enumerations become v2 enum definitions. Ordinary UML Associations and UML AssociationClasses both use connection-oriented v2 forms, but each carries a different marker so the reverse mapper knows which UML element to rebuild.

The source files contain 40 ordinary library associations, 65 Ports, 94 owned connectors, and one AssociationClass. These counts are checks, not rules. The implementation must discover them from the files rather than assume them.

### 6.4 OCL constraints

OCL constraints can refer to UML-specific features such as `base_Class` and can inspect all instances of a type. A SysML v2 constraint is not automatically equivalent.

Version 0.1 therefore keeps the original OCL text, its owner, the elements it constrains, and its comments. It also gives each constraint an owner-qualified key. This is necessary because `CoreRAAML` contains two different constraints named `ClientIsSituation`; their different owners are what distinguish them.

A pinned OCL 2.4 parser must list and resolve the RAAML names used inside each expression. That lets the test detect a constraint whose text survived but whose referenced element disappeared. This is a syntax and reference check, not proof that the constraint evaluates identically in every OCL engine. A generated v2 constraint may be useful, but it is an additional view, not a replacement for the source OCL.

### 6.5 Stable generated IDs

The reverse mapper must create new XMI IDs because the original tool-generated IDs are intentionally not preserved. It computes them with SHA-256 from stable inputs such as the source file, owner, element kind, and local name.

This makes references repeatable: the same inputs produce the same ID. It does not make the whole XML file byte-for-byte identical. That would also require fixed rules for namespace declarations, element order, attribute order, escaping, whitespace, and line endings.

## 7. Cases that make the problem harder than it first appears

The official files contain several useful tests:

- STPA `ControlAction` and `Feedback` each extend `Signal`, `Class`, and `DataType`.
- Concrete FTA gate and event stereotypes inherit their UML bases instead of declaring them again.
- FTA `TransferIn` extends `Property` without also extending `Class`.
- `LossScenario::base_Class` uses a different version of the UML URI from nearby definitions.
- An ISO 26262 ExtensionEnd has a name that does not match its stereotype.
- GSN combines Element-based abstract stereotypes with Class-based concrete descendants and makes extensive use of icons and OCL.
- Some association member ends are owned by the association; others are Properties owned by a Class. Treating them all as association-owned would change the model.
- OCL names are not unique enough to identify constraints without their owners.

These details do not all carry deep safety meaning. Some are simply part of the source model. But if the proposal claims to reconstruct that model, it must preserve them or explicitly exclude them.

## 8. How the proposal will be tested

The planned open-source implementation has four stages:

1. Read each official v1 XMI file and extract its fact list.
2. Produce SysML v2 definitions and a preservation manifest.
3. Parse that v2 output and reconstruct v1 XMI.
4. Extract the reconstructed fact list and compare it with the original.

### 8.1 What the report must show

For every file and every fact category, the report will show:

- how many source facts were found;
- how many reconstructed facts were found;
- which facts are equal;
- which facts changed, disappeared, appeared unexpectedly, or could not be resolved;
- which parser and standard versions were used.

The test fails on any missing, additional, changed, or unresolved in-scope fact.

### 8.2 Additional test cases

The official files are not enough by themselves. Small test files should also cover duplicate names under different owners, cross-file references, URI variants, inherited bases, association-end ownership, Ports, connector roles, missing manifests, and deliberately unsupported inputs.

Supported inputs must survive. Unsupported inputs must fail clearly. They must never be accepted while silently losing data.

### 8.3 Testing the SysML v2 text

Every generated SysML v2 file must parse with a named, documented implementation. Testing with a second implementation is preferable. One parser accepting a file proves only that the file is acceptable to that parser; it does not by itself prove that another tool will read it the same way.

## 9. Limits of the evidence

### The official files are not every possible model

The 17 files contain many useful cases, but they do not contain every legal UML profile structure or every value a user could place in a RAAML model. Passing this test does not prove support for arbitrary user models.

### Tools may disagree

UML and SysML v1 tools may tolerate or write profile details differently. The proposal must say which differences matter and which are merely file formatting. It must not erase a difference simply because one tool ignores it.

### Preserved OCL may still evaluate differently

Keeping the same OCL text and references does not prove that every OCL engine will evaluate it identically. Text-and-reference preservation and behavior are separate claims.

### A faithful encoding may not be pleasant native v2

The safest way to preserve an old definition may not be the cleanest way to design a new one. Version 0.1 chooses compatibility. A future native RAAML for SysML v2 may make different choices.

### Standards will continue to change

Each release must name the exact RAAML, SysML, KerML, and OCL versions it supports. A result for one version cannot silently become a claim about another.

## 10. Open project and community review

The proposal should live in a neutral public repository. The repository should contain public issues, versioned documents and schemas, repeatable test reports, contribution guidance, and a clear record of design decisions.

Original documentation is intended to use CC BY 4.0. Implementation code is intended to use Apache-2.0. OMG specifications, official XMI files, icons, and other third-party material are not relicensed by this project; their use and redistribution need a separate review.

M45 Engineering may author and maintain the first version without making the format proprietary. The useful outcome is a common compatibility layer that others can inspect, criticize, and implement independently.

Reviewers should challenge concrete questions:

- Is the fact list complete for the official definitions?
- Which recorded details carry meaning, and which only help reproduce a file?
- Are the chosen v2 forms useful as well as reversible?
- How should this work use the official general SysML-v1-to-v2 transformation?
- Which ideas could help a future native RAAML-on-v2 standard, and which should remain only compatibility machinery?

## 11. Conclusion

RAAML 1.1 and SysML v2 use different foundations. Similar names do not guarantee equivalent model elements, and details that look unimportant may still be needed to rebuild the source.

This draft defines a limited, testable goal: carry the 17 official RAAML 1.1 definition files through a SysML v2 representation and recover the same listed facts. It explains what must be stored, how difficult cases are handled, and what evidence an implementation must publish.

The immediate goal is review, not standard status. The next milestone is an open implementation that either passes the test or shows exactly where the proposal is wrong.

## References

1. Object Management Group, [Risk Analysis and Assessment Modeling Language 1.1](https://www.omg.org/spec/RAAML/1.1), December 2025.
2. Object Management Group, [Systems Modeling Language 2.0](https://www.omg.org/spec/SysML/2.0), September 2025.
3. Object Management Group, [Kernel Modeling Language 1.0](https://www.omg.org/spec/KerML/1.0), September 2025.
4. Object Management Group, [Unified Modeling Language 2.5.1](https://www.omg.org/spec/UML/2.5.1), December 2017.
5. Object Management Group, [Object Constraint Language 2.4](https://www.omg.org/spec/OCL/2.4), February 2014.
6. Object Management Group, [XML Metadata Interchange 2.5.1](https://www.omg.org/spec/XMI/2.5.1), June 2015.
7. National Institute of Standards and Technology, [FIPS PUB 180-4: Secure Hash Standard](https://doi.org/10.6028/NIST.FIPS.180-4), August 2015.
8. GfSE and project partners, [CASCaRA](https://cascara.gfse.org/).
9. EUROCAE, [Working Groups](https://www.eurocae.net/working-groups/).
