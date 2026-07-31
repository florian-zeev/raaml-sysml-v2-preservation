# Public-release checklist

**Publication route:** Conservative source-only community proposal

**Status:** Repository safeguards pass; two manual publication blockers remain

**Last reviewed:** July 31, 2026

This checklist controls the first public visibility of the repository. It is
an engineering release checklist, not legal advice. Independent reproduction
and specialist review are valuable follow-up evidence, but they do not block
publication of a clearly labeled draft.

## Chosen publication boundary

The public repository may contain:

- original implementation source and tests;
- original schemas, mapping rules, analysis, and proposal text;
- project-authored synthetic fixtures and examples;
- authoritative source locations, versions, byte sizes, and hashes;
- aggregate validation results and signed-candidate identities; and
- instructions that let each user obtain and validate the official inputs
  locally.

The public repository and its hosted downloads must not contain:

- official OMG XMI, PDFs, icons, or standard-library files;
- downloaded validator, JDK, or other third-party archives;
- raw or canonical fact sets generated from the complete official corpus;
- the generated full-corpus SysML v2 model;
- full-corpus preservation manifests;
- reconstructed RAAML SysML v1/UML XMI;
- comparison reports containing those source and reconstructed facts; or
- release bundles containing any of the preceding material.

## Automated repository gate

Run from a full Git checkout:

```text
./raaml publication audit
```

The command checks:

- every path currently tracked by Git;
- every path named by an object reachable from any local Git ref;
- required ignore rules for caches and generated evidence;
- the validation workflow's read-only repository permission; and
- known artifact, release, package, and container-publishing mechanisms.

The command runs in CI before official inputs are downloaded. It writes only
an ignored diagnostic summary. It does not inspect the contents of GitHub's
hosted Actions storage, releases, packages, or caches, and it does not make a
legal judgment about source-grounded facts or examples in original project
documents.

## Completed repository checks

- [x] Official standards files and tool archives are ignored.
- [x] No official XMI, specification PDF, generated corpus, preservation
      manifest, or reconstructed XMI is tracked in the current Git index.
- [x] No path for those materials appears in reachable Git history.
- [x] The only committed XMI files are three small project-authored validator
      fixtures.
- [x] The Docker build context excludes local caches, generated evidence,
      release directories, reviewer evidence, and container evidence.
- [x] The current workflow does not upload artifacts, create releases, push
      containers, or request package-write permission.
- [x] CI runs `./raaml publication audit` before downloading official inputs.
- [x] `NOTICE`, `LICENSE`, and `THIRD_PARTY_MATERIALS.md` limit project
      licenses to original work and exclude third-party material.
- [x] The proposal states that it is independent, non-normative, and not an
      OMG specification, submission, or endorsement.

## Manual blockers before changing repository visibility

### 1. Decide the treatment of limited source-grounded material

The proposal, transformation analysis, and independent oracle contain RAAML
names, technical relationships, aggregate counts, source locations, and
hashes of selected source text. They do not contain the complete generated
corpus, but the automated gate cannot provide legal clearance for them.

The manual review must cover at least:

| Path | Source-grounded material to assess |
| --- | --- |
| `proposal/normative-encoding-v0.1.md` | Named RAAML mapping examples, source locations, relationships, and preservation rules |
| `proposal/community-proposal-v0.1.md` | Aggregate corpus and validation results |
| `docs/transformation-analysis-v0.1.md` | Named edge cases and comparisons with official transformation rules |
| `docs/fact-contract-v0.1.md` | Corpus fact categories and identity examples |
| `analysis/*.json` | Corpus-derived classifications and official transformation-rule identifiers |
| `oracle/corpus-baseline-v0.1.json` | Aggregate counts, selected technical identifiers, relationships, and source-text hashes |
| `standards.lock.json` | Official filenames, URLs, versions, sizes, and hashes |
| `src/`, `typescript/src/`, and `tests/` | Selected filenames and technical identifiers required for extraction and verification |
| `examples/` | References to the generated compatibility-library namespace |

Before public visibility, obtain either:

- written permission or clarification from the relevant rights holder; or
- a qualified legal review confirming the narrower package and required
  notices; or
- a further reduction of the committed samples to a boundary the publisher
  is prepared to release.

Record the decision and exact notices in
[`third-party-rights-audit.md`](third-party-rights-audit.md), `NOTICE`, and
`THIRD_PARTY_MATERIALS.md`.

### 2. Remove hosted historical outputs

Earlier private workflow runs retained downloadable release bundles before
artifact upload was removed from CI. Before making the repository public:

1. Open the repository's **Actions** page on GitHub.
2. Inspect every run that shows an **Artifacts** section.
3. Delete each retained artifact, or delete the complete run if its logs also
   expose material that should not become public.
4. Check the repository's **Releases**, **Packages**, and **Caches** pages and
   remove any generated-corpus output.
5. Confirm that no run visible to a future public reader offers a generated
   release bundle for download.
6. Record the date, operator, and result below.

[GitHub documents](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts)
that artifacts can be deleted before expiry and that deleting a workflow run
also deletes its associated artifacts. Deletion is permanent.

**Hosted-output inspection record:** Not yet completed.

## Final publication sequence

After both manual blockers above are closed:

1. Run `./raaml publication audit` from a clean checkout.
2. Run the complete validation workflow and confirm it passes.
3. Review the public file list from a source-only archive.
4. Create a new signed release candidate; do not move `v0.9.0-rc.1` or
   `v0.9.0-rc.2`.
5. Confirm that the candidate does not create a downloadable generated-corpus
   artifact.
6. Change repository visibility to public.
7. Publish the paper and blog article as **Draft Community Proposal v0.1**.
8. Invite independent reproduction and domain-specialist review as the next
   evidence phase.

## Claims allowed at first publication

The first public draft may say that the repository has maintainer-operated,
reproducible validation evidence and a manual second-implementation syntax
check. It must continue to say that independent reproduction and external
technical review remain open.

Do not describe the proposal as independently validated, community-approved,
an OMG submission, a standard, or a new version of RAAML.
