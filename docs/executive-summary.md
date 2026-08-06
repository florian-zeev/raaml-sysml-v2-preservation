# Why RAAML 1.1 needs a preservation path into SysML v2

**Status:** Blog article draft accompanying the Draft Community Proposal v0.1
**Author:** Florian Wolf

RAAML gives safety and reliability concepts a precise form that software can inspect. A hazard, unsafe control action, fault-tree gate, or assurance claim is not just text on a diagram. It has a type, properties, and defined links to other parts of the system model. RAAML covers methods including STPA, fault trees, FMEA, reliability block diagrams, GSN assurance cases, ISO 26262 analysis, and security analysis.

The OMG published [RAAML 1.1](https://www.omg.org/spec/RAAML/1.1) in December 2025 for the SysML v1 generation. In that language, RAAML concepts are UML stereotypes applied to elements such as classes, properties, and signals.

SysML v2 is built differently. It uses KerML as its foundation and metadata definitions as its extension mechanism. It cannot directly load a SysML v1 profile or attach a UML stereotype. A translation must decide what each v1 definition becomes in v2, and a careless decision can discard information that a v1 tool still needs.

This community proposal explores a deliberately conservative answer: preserve first, redesign later.

The source-only proposal, implementations, tests, and signed candidate are
[public on GitHub](https://github.com/florian-zeev/raaml-sysml-v2-preservation).
The current evidence baseline is the
[`v0.9.0-rc.3` pre-release](https://github.com/florian-zeev/raaml-sysml-v2-preservation/releases/tag/v0.9.0-rc.3).

## Why move beyond SysML v1?

For many existing programs, there is no immediate reason to leave SysML v1. It is widely used, long-running programs depend on it, and moving a validated engineering process merely because a newer standard exists would create cost and risk.

The problem begins when new programs, suppliers, or tools adopt SysML v2. SysML v2 is now a formal OMG standard, and the surrounding tool and training ecosystem is developing around it. If a program describes its system in v2 but must keep its RAAML safety analysis in a separate v1 tool, it splits two bodies of information that need to remain connected. The links from system elements to hazards, failure modes, controls, assurance claims, and evidence then depend on duplicate data or custom integrations. If every organization invents its own translation, those translations will not necessarily preserve the same meaning.

SysML v2 offers another practical advantage: a standard textual notation. A SysML v1 model may also be serialized as text through XMI, but that text is usually verbose and shaped by the tool that wrote it. A small engineering change can cause a large, noisy XMI diff. SysML v2 text is intended to make models easier for people and software to inspect, compare, generate, and exchange.

Useful text diffs make ordinary version-control workflows possible. A team can review a model change, connect it to a requirement or approval, run automated checks, and tie a safety analysis to an exact model version. Git adds content-addressed history: changing an artifact changes its identifier, and changing an earlier commit changes the history built upon it. This makes unnoticed alteration difficult once trusted parties retain the original baseline identifier.

Git is not tamper-proof. A repository owner can rewrite history and present the replacement as canonical. Certification-grade use needs additional controls, such as signed release tags, protected branches, controlled identities, immutable or independently retained baselines, and explicit approval records. With those controls, Git can provide a strong existing foundation for tamper-evident engineering history.

The reason for this proposal is therefore not that every organization should migrate immediately. It is that when a system model moves to SysML v2, its safety meaning should be able to move with it.

## The proposal is a compatibility layer, not a redesign of RAAML

A future OMG effort to define RAAML directly for SysML v2 should be free to choose the v2 elements, notation, libraries, and analysis behavior that best express its meaning. Those choices belong in an open standards process.

This proposal has a narrower job. It asks whether the 17 official RAAML 1.1 definition files—nine profiles and eight libraries—can pass through SysML v2 while retaining a written, testable list of v1 facts. Here, “official” means that the file is part of the machine-readable material published by the OMG.

Those facts include:

- stereotype names, inheritance, whether a stereotype is abstract, the kinds of UML elements it extends, and its extension ends;
- stereotype properties, types, multiplicities, defaults, subset/redefinition links, comments, and icons;
- OCL bodies and their owning and constrained elements;
- library classes, enumerations, AssociationClasses, and plain associations;
- Ports, connectors, connector ends, imports, profile applications, and namespace metadata;
- stereotype applications that occur inside the official library files.

The proposal does not cover RAAML models created by users. At signed candidate
tag `v0.9.0-rc.3`, the Python reference implementation and
native TypeScript implementation passed the defined round-trip test for all 17 official files
with zero differences in the specified fact set. That is a result within a
deliberately narrow boundary, not proof that arbitrary RAAML models can be
converted safely.

## Why a simple one-to-one rewrite is not enough

Many RAAML definitions do not have one obvious v2 replacement.

For example, the STPA `ControlAction` stereotype can be applied to three
different kinds of UML element: `Signal`, `Class`, and `DataType`. In this
proposal it remains one metadata definition. The preservation record must keep
all three permitted UML bases and their extension relationships so that the
reverse mapper can rebuild the source definition.

FTA adds a different problem. Concrete gate and event stereotypes inherit their `base_*` properties rather than declaring them again. Adding those bases to every subtype during reconstruction would create declarations that are not present in the official profile.

Other details look unimportant until the tool tries to rebuild the v1 definition:

- an ExtensionEnd name that differs from the stereotype name;
- an older UML URI used by one declaration;
- SVG icon data and locations;
- a UML AssociationClass that must remain distinguishable from a plain association;
- 65 library Ports and 94 owned connectors;
- two distinct OCL constraints in `CoreRAAML` that share the name `ClientIsSituation` but have different owners.

The v2 representation therefore needs two parts: a useful v2 element and a record of the v1 details that element cannot express by itself.

## The core pattern

Each official RAAML stereotype becomes a SysML v2 metadata definition. The metadata records the v1 facts that the chosen v2 form does not express clearly enough on its own.

Conceptually:

```text
RAAML 1.1 stereotype
    ↓
SysML v2 metadata definition
    + original base-metaclass set
    + original generalizations
    + properties and multiplicities
    + extension-end identities
    + icon and OCL references
    + other preservation fields
```

Information that belongs to the whole source file—its profile name, URI, comments, imports, profile applications, namespace values, and OCL records—is stored once in a JSON manifest beside the v2 model. It is not copied onto every definition.

The generated full-corpus SysML v2 text is accepted by the mandatory pinned
SysML v2 implementation with zero errors in all five validation categories.
The reverse mapper also reconstructed all 17 v1 files with zero canonical
fact differences. After the candidate was signed, Sensmetry Syside Editor
0.10.3 also reported no problems for the exact generated text in a manual
maintainer-operated check. No outside team has yet reproduced the result.

## Choosing a useful v2 carrier without discarding the source

The proposal separates stereotype definitions from library elements.

Every RAAML stereotype becomes a SysML v2 `MetadataDefinition`. The kinds of
UML element it may annotate remain part of the preserved source facts; they do
not turn the stereotype itself into an item, part, or occurrence definition.
A tool may derive domain-oriented views, but those views are not the
authoritative preservation carrier.

Library elements use the native structural form selected by the source:

| RAAML v1 source element | Primary v2 carrier | Preserved separately |
| --- | --- | --- |
| UML stereotype extending one or several metaclasses | `MetadataDefinition` | all locally declared bases, Extensions, properties, and inheritance |
| Plain UML library Class | `OccurrenceDefinition` | original class identity, properties, connectors, and relationships |
| UML Class with SysML v1 `Block` applied | `PartDefinition` | the original application and its values |
| UML Class with `ConstraintBlock` applied | `ConstraintDefinition` | the original application and its values |
| UML Association or AssociationClass | connection definition with a source-kind marker | class/link identity, ends, ownership, properties, and inheritance |
| UML Enumeration | enumeration definition | literal order and any `ValueType` application |

The native carrier makes the element usable in v2. The preservation record
lets the tool rebuild and test the original v1 facts.

## OCL is preserved, not translated by assertion

The official RAAML profiles contain OCL constraints that inspect UML-specific features such as `base_*` properties and all instances of a type. A SysML v2 `constraint def` does not automatically perform the same check.

Version 0.1 therefore preserves:

- the original OCL text and language/body representation;
- its owner and constrained elements;
- comments and an owner-qualified identity;
- names referenced by the expression, extracted and resolved by a pinned OCL 2.4 parser.

Parsing and name resolution are required; evaluating the constraint is outside the version 0.1 conformance claim. A v2 constraint may later be generated as an additional view. It cannot replace the original OCL until tests show that both constraints mean and do the same thing.

## The pass-or-fail test

The rebuilt XMI does not need the source file's spacing, XML element order, or MagicDraw-assigned IDs. It must contain the same facts listed by the proposal.

The test is:

```text
official RAAML XMI
    ↓ extract facts
standard source fact list
    ↓ forward map
SysML v2 definitions + preservation manifests
    ↓ reverse map
reconstructed RAAML XMI
    ↓ extract facts
standard reconstructed fact list
    ↓ compare
no listed fact is missing, added, unresolved, or changed
```

The signed candidate reports:

| Measure | Result |
| --- | ---: |
| Official files mapped and reconstructed | 17 |
| Canonical fact differences | 0 |
| Generated native v2 targets | 343 |
| OCL expressions parsed and resolved | 33 |
| Adversarial tests | 36 passed, 0 failed |
| Native TypeScript canonical equality gate | Passed |
| Release files reproduced on host and offline container | 49, byte-identical |

Stable generated IDs make links repeatable, but stable IDs do not make the
surrounding XML byte-for-byte identical. The
[validation report](validation-report-v0.9.0-rc.3.md) records the current
evidence and identifies the exact signed commit, containers, CI runs, and
verification command.

## Where this fits in the wider digital-engineering transition

The proposal is intentionally narrow, but the underlying problem is broader.

[CASCaRA](https://cascara.gfse.org/) is working on a common way to connect engineering information held in different specialized tools. Digital-certification initiatives such as EUROCAE WG-136 are examining how people can navigate regulations, evidence, and certification work electronically. RAAML provides typed links between safety analyses and the system being analyzed.

This proposal does not solve those larger problems. It provides one smaller but necessary capability: a tool can say exactly which standardized safety facts crossed from SysML v1 to v2 and test whether any changed.

That can support:

- tool vendors experimenting with RAAML-aware SysML v2 workflows;
- standards contributors checking migration choices against the existing official files;
- engineering organizations that cannot switch every tool and partner simultaneously;
- future regulator or assurance views that must show where a fact came from and which element it refers to.

## References

- Object Management Group, [Risk Analysis and Assessment Modeling Language 1.1](https://www.omg.org/spec/RAAML/1.1), December 2025.
- Object Management Group, [Systems Modeling Language 2.0](https://www.omg.org/spec/SysML/2.0), September 2025.
- Object Management Group, [Kernel Modeling Language 1.0](https://www.omg.org/spec/KerML/1.0), September 2025.
- Object Management Group, [Object Constraint Language 2.4](https://www.omg.org/spec/OCL/2.4), February 2014.
- GfSE and project partners, [CASCaRA](https://cascara.gfse.org/).
- EUROCAE, [WG-136: Digital Regulations and Certification Framework](https://www.eurocae.net/new-working-group-wg-136-digital-regulations-and-certification-framework/).
- Source repository and signed candidate, [RAAML SysML v2 preservation](https://github.com/florian-zeev/raaml-sysml-v2-preservation).
- Reference implementations, [Validation report for `v0.9.0-rc.3`](validation-report-v0.9.0-rc.3.md).
