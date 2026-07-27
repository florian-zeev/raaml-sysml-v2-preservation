# RAAML-on-SysML-v2 reference implementation and evidence plan

**Status:** Draft execution plan; implementation must not begin beyond Milestone 0 until its decisions and gates pass

**Purpose:** Produce reproducible evidence for the Draft Community Proposal v0.1

**Scope:** The 17 official RAAML 1.1 definition files only; arbitrary user models remain outside the conformance claim

## 1. Outcome and claim boundary

Build a neutral open-source implementation that tests whether the Draft Community Proposal v0.1 can carry the defined facts in the 17 official RAAML 1.1 definition files through a SysML v2 representation and reconstruct the same facts in SysML v1 XMI.

The required property is:

```text
canonicalFacts(reverse(forward(source))) == canonicalFacts(source)
```

This is a **fact-preserving round trip over a defined corpus**. It is not:

- byte-for-byte XMI identity;
- proof that every possible RAAML user model is supported;
- proof that preserved OCL has the same behavior in every OCL engine;
- proof of a two-way bijection over arbitrary SysML v2 models;
- RAAML 2.0 or an OMG specification;
- evidence that Git, by itself, makes an engineering process tamper-proof.

The implementation provides evidence for the proposal. It must never change the preservation contract silently merely to make a failing test pass. A change to the contract, schemas, or mapping rules requires a versioned proposal change and a recorded design decision.

## 2. Public project and licensing

**Repository name:** `raaml-sysml-v2-preservation`

**Repository:** A separate public repository from the M45 product runtime

**Governance:** Independent community project initially maintained by Florian Wolf / M45 Engineering

**Code license:** Apache License 2.0

**Original documentation and schemas:** Creative Commons Attribution 4.0 International

**Third-party inputs:** Not redistributed unless their rights have been reviewed and documented

Create the separate neutral repository before Milestone 0 begins. The standards lock, ADRs, validator adapters, smoke tests, implementation, and evidence history belong there from their first commit. The M45 repository may retain proposal drafts and links, but it must not become the temporary implementation repository.

The public repository must use neutral names and contain `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, and a third-party-materials policy from its first public release.

The official OMG XMI files, specifications, icons, and other third-party material are not automatically covered by the project licenses. Until redistribution is confirmed, the public repository must contain a verified downloader or instructions for supplying the files locally, not copies of the files.

### 2.1 Repository bootstrap and source of truth

Bootstrap the project in this order:

1. create the standalone local repository and establish its neutral directory structure;
2. copy the proposal documents under neutral filenames and record their source commit in `PROVENANCE.md`;
3. add the license texts, `NOTICE`, contribution rules, security policy, and third-party-materials policy;
4. add an incomplete `standards.lock.json` without pretending that unverified hashes or rights decisions are settled;
5. commit this documentation-only foundation;
6. create the public `florian-zeev/raaml-sysml-v2-preservation` repository and push the reviewed foundation;
7. conduct all Milestone 0 toolchain experiments and implementation work in the public repository.

The public repository becomes the source of truth when the foundation commit is published. The M45 repository may retain historical drafts and internal publication notes, but later changes to the public proposal, schemas, implementation, and evidence must originate here.

Do not use a Git submodule or import M45 code. The implementation boundary is a standalone command-line interface over files. A product may later consume a pinned release, container, package, or published artifact without sharing the implementation repository's internal modules.

## 3. Standards and toolchain baseline

The project must pin exact artifacts rather than refer only to a standard by its common name.

The initial standards baseline is:

- RAAML 1.1 and its 17 official profile/library XMI files;
- SysML 2.0 formal language specification;
- SysML 2.0 formal v1-to-v2 transformation specification;
- the normative `SysMLv1Tov2.xmi` transformation model, OMG file ID `ptc/25-04-10`;
- KerML 1.0;
- UML 2.5.1;
- SysML 1.6 for the RAAML source profiles;
- OCL 2.4;
- XMI 2.5.1.

Before implementation, `standards.lock.json` must record for every input:

- standard name and version;
- OMG file ID where applicable;
- authoritative URL;
- retrieval date;
- exact SHA-256 digest and byte size;
- local filename;
- whether the artifact may be redistributed;
- the reason for treating it as normative, informative, or tool-specific.

The candidate mandatory v2 validator is the official SysML v2 Pilot Implementation. Milestone 0 must pin an exact release, commit, standard-library set, and container digest. “Latest” is forbidden in tests and reports.

The v2 validation adapter must report separately:

1. lexical and syntax errors;
2. import and standard-library loading errors;
3. name-resolution and linking errors;
4. type and multiplicity errors;
5. SysML/KerML model-validation errors.

A file passes only when all five categories contain zero errors. Merely producing an abstract syntax tree is not a pass.

At least one automated UML/SysML v1 loader or validator must also be pinned. “If available” is not sufficient for the final claim. If no suitable automated v1 loader can be established during Milestone 0, implementation pauses and the proposal must either narrow its claim or select another validation approach.

An OCL 2.4 parser must also be pinned. It is required to parse the stored expressions, extract referenced names using OCL syntax rather than text matching, and resolve those names in the owning profile's visible namespace. The parser is not required to evaluate the constraints for version 0.1 conformance.

The transformation implementation and the official v2 validator may use different languages. The mapper should not be forced into the official parser's internal architecture. The parser and v1 loader are accessed through small adapters with documented inputs, outputs, versions, and exit codes.

## 4. Repository shape

```text
raaml-sysml-v2-preservation/
├── README.md
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── standards.lock.json
├── proposal/
│   ├── community-proposal-v0.1.md
│   └── normative-encoding-v0.1.md
├── adr/
│   ├── 0001-toolchain.md
│   ├── 0002-canonical-fact-identity.md
│   ├── 0003-v2-validation.md
│   ├── 0004-v1-validation.md
│   ├── 0005-ocl-parsing.md
│   └── 0006-secure-xml-and-resolution.md
├── schemas/
│   ├── canonical-raaml-facts.schema.json
│   ├── preservation-manifest.schema.json
│   ├── conformance-report.schema.json
│   └── diagnostics.schema.json
├── sources/
│   ├── README.md
│   ├── catalog.xml            # pinned URI-to-local-artifact resolution
│   └── cache/                 # ignored unless redistribution is approved
├── oracle/
│   ├── expected-counts.json
│   ├── golden-facts/
│   ├── coverage-matrix.md
│   └── audit/                 # independent of production extractor
├── src/
│   ├── extract-v1-facts/
│   ├── canonicalize-facts/
│   ├── forward-to-v2/
│   ├── validate-v2/
│   ├── reverse-to-v1/
│   ├── validate-v1/
│   └── compare-facts/
├── fixtures/
│   ├── adversarial/
│   ├── unsupported/
│   └── expected-diagnostics/
├── examples/
│   └── stpa-walkthrough/      # illustrative; outside v0.1 conformance
├── generated/                 # reproducible outputs or release artifacts
├── reports/
│   └── conformance/
├── tooling/
│   ├── v2-validator/
│   ├── v1-validator/
│   ├── ocl-parser/
│   └── container/
└── .github/workflows/
    ├── test.yml
    └── reproduce.yml
```

Generated artifacts must state whether they are committed release evidence or ignored local build output. CI must fail when committed generated evidence is stale.

## 5. Executable interface

Milestone 0 chooses the language and build system and records the decision in `adr/0001-toolchain.md`. The decision must include installation commands, lockfiles, supported platforms, dependency versions, and why the choice can handle XML/XMI without losing the source distinctions required by the proposal.

Whatever implementation language is chosen, the project exposes these stable logical commands:

```text
sources fetch             # explicit network operation; never runs implicitly
sources verify            # verify every byte against standards.lock.json
schemas validate          # validate schemas and every schema-governed artifact
facts extract --all       # source XMI -> raw and canonical fact documents
oracle audit              # independent audit; imports no production extractor code
validate-ocl --all        # parse OCL and resolve referenced RAAML names
tests unit                # focused tests for canonicalization and mapping rules
tests adversarial         # negative, ambiguity, corruption, and collision tests
forward --all             # source facts -> v2 files + manifests
validate-v2 --all         # full pinned-parser validation
reverse --all             # v2 files + manifests -> reconstructed v1 XMI
validate-v1 --all         # load and validate reconstructed v1 artifacts
compare --all             # canonical source facts vs reconstructed facts
conformance --all         # complete offline pipeline after source verification
reproduce                 # clean-environment build of the published report
```

Every command must:

- return `0` only on success and nonzero on any unsupported, unresolved, invalid, or changed required fact;
- write structured diagnostics that validate against `diagnostics.schema.json`;
- keep generated timestamps, temporary directories, checkout locations, and other run-environment paths out of canonical output;
- preserve a machine-specific path when that path is itself an in-scope source fact, such as a verbatim `uml:Image@location` value;
- identify the schema, source, standard, parser, and implementation versions in reports;
- never fetch from the network unless the user explicitly runs `sources fetch`.

`standards.lock.json` is the sole authoritative source manifest. Other reports may copy its values for readability, but they must not define a second set of expected URLs or hashes.

### 5.1 Secure XML and reference handling

All XML/XMI inputs are treated as untrusted until `sources verify` confirms their digest. Adversarial and future user-supplied files remain untrusted even when local.

The XML layer must:

- disable DTD processing, external general entities, external parameter entities, and XInclude;
- reject entity-expansion constructs instead of partially processing them;
- perform no implicit HTTP, HTTPS, or filesystem retrieval while parsing;
- resolve known UML, SysML, RAAML, and related references only through the pinned local catalog;
- reject `file:` references, path traversal, symlink escapes, and paths outside the verified source/cache roots unless a specific test fixture explicitly permits one;
- enforce documented maximum input bytes, XML nesting depth, attribute count/size, text-node size, and total expanded content;
- treat timeouts, resource-limit violations, unsupported encodings, and malformed XML as structured failures;
- preserve raw href and `uml:Image@location` strings as data without dereferencing them.

Security fixtures must prove that external-entity access, XInclude, network retrieval, local-file retrieval, path traversal, symlink escape, and resource-exhaustion payloads fail without reading the target resource or producing accepted output.

## 6. Canonical fact model and equality

JSON Schema defines allowed structure, but not equality. The project therefore defines both a raw extracted representation and a canonical representation.

### 6.1 Required canonicalization rules

- Every document contains an explicit `schemaVersion`.
- Names, comments, OCL bodies, URIs, icon content, and other preserved strings are compared as logical strings emitted by the XML parser. They are not trimmed, case-folded, or Unicode-normalized.
- Canonical JSON is UTF-8 with LF line endings and a final newline.
- Object keys use a fixed ordering in serialized release artifacts.
- Collections declared unordered by the proposal are sorted by a documented composite identity key before serialization.
- Collections declared ordered—such as enumeration literals, connector ends, association member ends, and OCL body lines—retain their defined order.
- Absence is distinct from an explicit default when the preservation contract records presence. A schema default must never make an absent source value appear explicitly present.
- Resolved references contain both their canonical target identity and any raw URI/href that the contract preserves.
- Duplicate unordered facts are compared as multisets, not collapsed into sets.
- Floating-point parsing is forbidden for values that must round-trip lexically. Such values remain tagged strings unless the contract explicitly defines numeric normalization.

### 6.2 Identity rules

`adr/0002-canonical-fact-identity.md` must define an identity key for every fact category before the extractor is implemented.

An identity key may not depend on:

- a tool-generated XMI ID that the preservation contract excludes;
- an absolute local path;
- a network retrieval order;
- unrelated XML sibling order.

The detailed encoding currently uses an ordinal in `syntheticOwnedId`. The ADR must state exactly which ordered source relationship supplies that ordinal. If same-kind, same-name siblings under one owner have no in-scope ordering or other distinguishing fact, v0.1 must reject that case as unsupported rather than assign an unstable identity. Any resulting change to the encoding specification must be made before mapping begins.

## 7. Independent oracle and coverage

Using the same extractor before and after the round trip can hide an extractor bug. The project therefore requires an oracle that does not import or call production extraction code.

The oracle consists of:

1. **Independent corpus audit.** Small, read-only XPath or equivalent queries compute counts and selected relationships directly from the XMI files.
2. **Golden facts.** Manually reviewed expected records cover every fact category and every known difficult case.
3. **Coverage matrix.** Each preservation requirement points to at least one official source example, one golden record, and one automated test.
4. **Mutation check.** During development, intentionally disabling extraction for each top-level fact category must make either the oracle or a golden test fail.

The oracle is frozen and reviewed before the forward mapper is completed. Updating expected results requires a visible review explaining whether the source changed, the preservation contract changed, or the old expectation was wrong.

Counts alone are not sufficient. For example, two incorrect references can preserve a count. Golden facts must include resolved target identities, ownership, ordering, value kinds, and presence/absence where relevant.

## 8. OCL policy

Version 0.1 requires preservation of:

- the original OCL text and language representation;
- the owning element;
- constrained-element references;
- comments;
- owner-qualified constraint identity;
- resolvability of the RAAML names extracted from the expression.

Parsing is required: `referencedNames` must come from a pinned OCL 2.4 parser, and all recorded names must resolve in both the source and rebuilt v1 namespace. Text searching is not an acceptable substitute.

Version 0.1 does not require constraint evaluation and does not claim behavioral equivalence across OCL engines. Evaluation may be published as additional evidence, but it must be reported separately from fact preservation. Before implementation, the proposal, detailed encoding, schemas, and this plan must use the same wording on this boundary.

## 9. Milestone 0 — Prove the foundations and freeze decisions

### Deliverables

- `standards.lock.json` and the source acquisition/rights policy;
- a pinned official SysML v2 validator adapter;
- a pinned automated UML/SysML v1 loader or validator adapter;
- a pinned OCL 2.4 parser adapter;
- a minimal v2 file exercising packages, metadata definitions, annotations, datatypes, arrays, references, connections, comments, and imports;
- a minimal v1 profile/library XMI that the selected v1 validator loads;
- a verified load of the real `CoreRAAML.xmi` and `CoreRAAMLLib.xmi` files through the selected v1 environment and pinned local reference catalog;
- documented secure XML/parser settings and resource limits;
- `adr/0001-toolchain.md` through `adr/0006-secure-xml-and-resolution.md`;
- exact bootstrap, test, and CI commands;
- a decision on whether the second v2 parser is mandatory or additional evidence.

### Exit criteria

- a clean environment can install or start all tools from pinned definitions;
- `sources verify` rejects a deliberately changed source byte;
- the minimal v2 fixture passes syntax, linking, name resolution, type checking, and model validation;
- a malformed v2 fixture fails with structured diagnostics;
- the minimal v1 fixture loads and an invalid reference fails;
- verified `CoreRAAML.xmi` and `CoreRAAMLLib.xmi` load without implicit network access, and their required external references resolve through the pinned local catalog;
- representative RAAML OCL containing navigation, `.allInstances()`, and `closure(...)` parses, exposes referenced names, and rejects a malformed expression;
- DTD, external-entity, XInclude, network/file retrieval, traversal, symlink-escape, and resource-exhaustion fixtures fail safely with structured diagnostics;
- no command depends on an unpinned `latest` release;
- the toolchain ADR selects the implementation language and build system;
- the rights policy states what third-party material may be acquired, cached, or committed before any such material enters the project workflow.

No production mapper work begins until this milestone passes.

## 10. Milestone 1 — Define facts, identity, and the independent baseline

### Deliverables

- versioned JSON Schemas covering every fact in the preservation contract;
- canonicalization and equality implementation;
- identity ADR covering every fact category;
- repeatable extraction from all 17 official XMI files;
- resolved targets for references between files;
- independent corpus-audit queries;
- expected counts and golden facts;
- coverage matrix linking requirements to source examples and tests;
- explicit failures for unsupported or unresolved input.

### Exit criteria

- every required source fact produces a schema-valid raw and canonical record;
- two extractions of the same verified inputs are byte-identical;
- extraction on two clean supported environments is byte-identical;
- duplicate `CoreRAAML::ClientIsSituation` constraints remain distinct by owner;
- every fact category has a golden example and a negative test;
- production counts match the independent audit;
- selected resolved relationships match the manually reviewed golden facts;
- every OCL expression parses and every required `referencedNames` entry resolves in the source namespace;
- removing any top-level extraction category causes a test failure;
- no forward or reverse mapping code is used to create the oracle.

## 11. Milestone 2 — Analyze the official SysML v1-to-v2 transformation

### Deliverables

- a rule-by-rule matrix for the UML/SysML constructs used by the 17 RAAML files;
- citations to the relevant transformation clauses and machine-readable rules;
- for each proposal rule: `reuse`, `specialize`, `supplement`, or `deviate`;
- a written reason and test obligation for every supplement or deviation;
- resolved updates to the proposal and detailed encoding.

### Exit criteria

- no mapping rule needed by the corpus remains classified `unknown`;
- every deliberate difference from the official transformation is visible in the proposal;
- the standards contributors reviewing the project can reproduce the comparison from the pinned transformation artifacts;
- schemas and mapping tables are frozen as version `0.1` before the vertical slice.

## 12. Milestone 3 — Thin vertical slice

Implement one complete path before expanding across the corpus.

### Required slice

- `CoreRAAML` and `CoreRAAMLLib`;
- `GeneralRAAML` and `GeneralRAAMLLib`, including `GeneralRAAML::Undeveloped` to exercise `base_Element`, an SVG icon payload, and verbatim source `location` preservation;
- the STPA definitions needed to exercise `Situation`, `ControlStructure`, `Controller`, `ControlAction`, and at least one official library stereotype application;
- at least one OCL constraint;
- one cross-file reference;
- one icon payload;
- one association or connector case.

### Deliverables

- source extraction;
- v2 definitions and preservation manifests;
- full v2 validation;
- reconstructed v1 XMI;
- v1 loading/validation;
- canonical fact comparison;
- readable and machine-readable reports.

### Exit criteria

- the complete slice passes every stage without manual file editing;
- all generated outputs are deterministic;
- corrupting the manifest, removing a target, or changing one ordered value produces the expected failure;
- the report identifies every tool and source digest;
- problems found in the slice update the proposal before full-corpus expansion.

## 13. Milestone 4 — Generate and validate the full v2 corpus

### Deliverables

- generated metadata definitions used to preserve RAAML;
- one schema-valid preservation manifest per source file;
- generated v2 definitions for every in-scope declaration in all 17 files;
- complete parser diagnostics stored with the build report;
- deterministic formatting and import resolution.

### Exit criteria

- all generated files pass all five v2 validation categories with the pinned implementation;
- all imports resolve from pinned local libraries without network access;
- generating twice produces byte-identical v2 and JSON outputs;
- no proposal or specification snippet remains unlabeled pseudocode;
- if a second parser is part of the chosen release gate, its results are reported separately rather than merged with the mandatory validator.

If no second parser is available, the report must say **not tested with a second implementation**. It must not imply interoperability beyond the named validator.

## 14. Milestone 5 — Reverse map and validate v1

### Deliverables

- reconstruction of all profile and library XMIs;
- stable IDs for top-level and owned elements;
- regenerated imports, references, properties, Ports, connectors, associations, constraints, icons, and normative library applications;
- v1 loader diagnostics;
- clear failures for ID collisions and unresolved references.

### Exit criteria

- every rebuilt file is well-formed XML;
- every internal reference resolves;
- every external URL-plus-fragment reference resolves through the pinned catalog to the intended definition;
- every rebuilt artifact loads in the mandatory v1 environment with zero required validation errors;
- the reverse mapper never retrieves a reference over the network during conformance testing;
- an injected fake hash provider produces a deterministic collision and proves that collision detection stops the build;
- original MagicDraw IDs are neither required nor claimed to be preserved.

## 15. Milestone 6 — Full conformance and adversarial suite

Adversarial fixtures are written alongside the relevant schema and mapping work; this milestone runs and publishes the complete suite.

### Required fixtures

- duplicate local names under different owners;
- duplicate constraint names under different owners;
- unsupported same-kind, same-name siblings under one owner if identity is ambiguous;
- cross-profile and cross-library generalizations;
- inherited versus locally owned bases;
- URI variants;
- multi-ended associations;
- Properties versus Ports;
- connector roles and `partWithPort` references;
- absent versus explicitly present multiplicities and defaults;
- missing, altered, mismatched, and schema-invalid manifests;
- unresolved local and external references;
- DTDs, external entities, XInclude, implicit network/file retrieval, path traversal, and symlink escape;
- excessive XML depth, attribute/text size, and entity-expansion/resource-exhaustion attempts;
- injected ID collisions;
- large icon payloads;
- constructs deliberately outside v0.1.

### Deliverables

- source and reconstructed canonical facts;
- comparison across every fact category;
- human-readable and machine-readable reports;
- per-file and per-category source/reconstructed counts;
- exact lists of missing, added, changed, duplicate, and unresolved facts;
- expected diagnostics for every negative fixture.

### Exit criteria

```text
canonicalFacts(reverse(forward(x))) == canonicalFacts(x)
```

for each of the 17 verified official files.

The test fails on any missing, additional, changed, duplicate, ambiguous, or unresolved in-scope fact. Unsupported inputs must fail before output is presented as valid. A failure may remain in a draft release, but the report must show it and the paper must not claim conformance.

## 16. Milestone 7 — Reproducibility, diff evidence, and engineering walkthrough

### Deliverables

- container or equivalent clean-environment reproduction;
- CI that runs source verification, extraction, the OCL parser, oracle audit, all tests, the required v2 and v1 validators, and conformance;
- a release report containing source hashes, schema versions, tool versions, container digest, Git commit, and clean/dirty state;
- a signed release tag and a checksum file for published artifacts;
- a controlled one-fact input change with the resulting deterministic v2 and manifest diff;
- a small STPA engineering walkthrough showing why the preserved definitions matter.

The STPA walkthrough is illustrative and outside the v0.1 conformance claim unless a later proposal explicitly adds user models. The existing lightweight wheel-brake example may provide source material, but it is not accepted as evidence until rewritten against the generated definitions and validated by the pinned parser.

### Exit criteria

- `reproduce` creates the published reports from a clean checkout without manual edits;
- after verified sources are present, the conformance run succeeds with network access disabled;
- repeated clean runs produce identical canonical facts, v2 files, manifests, rebuilt XMI, and machine-readable reports except for explicitly separated run metadata;
- the controlled change produces only deterministic, explained changes; no broad semantic-diff claim is made from one example;
- the walkthrough passes the pinned v2 validator;
- an independent person can follow the documented commands, or the paper explicitly states that reproduction has so far been performed only by the project team.

## 17. Release progression

### `v0.1-design`

- proposal, encoding, schemas, standards lock, oracle design, and ADRs open for review;
- parser and v1-loader smoke tests pass;
- no fact-preservation claim.

### `v0.2-corpus`

- source fact extractor, independent oracle, coverage matrix, and corpus inventory published;
- generated syntax work may be incomplete;
- no round-trip claim.

### `v0.3-vertical-slice`

- CoreRAAML/STPA slice passes forward mapping, both validators, reversal, and comparison;
- remaining corpus gaps are public.

### `v0.9-conformance-candidate`

- full pipeline and adversarial suite;
- all 17 files produce published comparison results;
- external technical review requested;
- any failure remains visible.

### `v1.0`

- all required checks pass for all 17 files;
- exact supported versions and limitations are frozen;
- clean-environment reproduction passes;
- paper claims match the linked report exactly;
- rights review permits publication of every distributed artifact.

Independent external reproduction is a paper-quality goal. If it has not occurred by `v1.0`, both the release and paper must say so plainly.

## 18. Community review targets

Seek feedback from:

- RAAML and SysML v2 standards contributors;
- CASCaRA participants working to connect information across engineering tools;
- digital-regulation and certification practitioners, including relevant EUROCAE participants;
- safety-analysis tool vendors;
- industrial users operating mixed v1/v2 and multi-tool environments;
- OCL, UML profile, XMI, and model-transformation specialists.

The review request asks concrete questions:

1. Does the preservation contract include every fact needed to rebuild the official definitions?
2. Which details carry engineering meaning, which support file exchange, and which are artifacts of one tool?
3. Are the selected v2 forms useful as well as reversible?
4. Does the reuse/deviation matrix apply the official v1-to-v2 transformation correctly?
5. Are the oracle and coverage matrix independent enough to detect extractor omissions?
6. Which parts should inform a future native RAAML-on-v2 standard, and which should remain compatibility machinery?

## 19. Publication gate

The paper may say **demonstrates a fact-preserving round trip over the official RAAML 1.1 definitions** only when:

- Milestones 0 through 7 pass;
- the exact conformance report and release are linked;
- the report names all parsers, validators, standards, schemas, and source digests;
- no required error is hidden or downgraded;
- the paper states that the result covers the 17 official definition files, not arbitrary RAAML models;
- third-party rights have been reviewed for every published artifact.

The paper may say that SysML v2 text **enables practical text-based review and version control** only after deterministic generation is demonstrated. It must not claim that text alone guarantees a meaningful semantic diff.

The paper may describe Git history as **tamper-evident under stated controls**, not tamper-proof. Release evidence must identify who or what retains the trusted tag or checksum and which controls—such as signed tags, protected branches, and independently retained baselines—are actually used.

The word **bijection** remains prohibited unless the project later defines the allowed v2 input space and demonstrates the reverse property for every allowed class of v2 input.

## 20. Required validation commands before implementation is considered complete

The selected toolchain must provide exact, documented equivalents of:

```text
sources verify
schemas validate
facts extract --all --check-determinism
oracle audit
validate-ocl --all
tests unit
tests adversarial
forward --all
validate-v2 --all
reverse --all
validate-v1 --all
compare --all
conformance --all --offline
reproduce --clean
```

No release gate may depend on an undocumented manual correction. Manual inspection may supplement these commands, but it cannot replace them.
