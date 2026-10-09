# Cloak UI Reference Corpus Upgrade Plan

Status: `FINALIZED_PLANNING_NOT_IMPLEMENTED`

Plan ID: `CLOAK_UI_REFERENCE_CORPUS_V1`

Phase family: `CUIR`

Canonical planning owner: Orchestra

Primary specialist: Cloak

External-source intake owner: Artificer

## Purpose

Upgrade Cloak from a primarily rule-and-checklist-driven UI/UX specialist into a provenance-aware pattern intelligence specialist that can study a broad external UI reference corpus, recognize useful design and interaction patterns, and apply those patterns as Orchestra-native guidance without silently copying source code or assets.

This plan preserves the previously approved `CLOAK_UI_REFERENCE_CORPUS` direction and makes it a durable Orchestra planning artifact so it cannot depend on chat history or an external continuity tracker for survival.

## Source-of-truth and continuity rule

This document is the canonical human planning source for the Cloak UI Reference Corpus upgrade until a later governed implementation record explicitly supersedes it.

Padayon or any other continuity system may mirror:

- plan ID;
- canonical path;
- current phase/status;
- exact Orchestra revision;
- latest evidence/receipt pointers.

A continuity mirror must not independently redefine the corpus, licensing rules, phase order, reuse permissions, or implementation authority.

```text
ORCHESTRA_PLAN != PADAYON_PROJECTION
PADAYON_PROJECTION != ORCHESTRA_AUTHORITY
STALE_CONTINUITY_STATE != SOURCE_REALITY
```

## Historical recovery

The approved preimplementation reminder defined the next Cloak work as:

```text
CLOAK_UI_REFERENCE_CORPUS
```

Initial external UI corpus:

```text
https://github.com/Nazia-99
```

The prior observation was approximately 140 public repositories with substantial UI, CSS, and design content. The repository count must never be hard-coded as a canonical fact. `CUIR-1` must inventory the exact eligible repository set from current source reality.

The original provenance rule remains mandatory:

```text
REFERENCE TO PATTERN OR LOGIC != COPYING SOURCE CODE
PUBLIC REPOSITORY != AUTOMATIC REUSE PERMISSION
DESIGN INSPIRATION != SOURCE OWNERSHIP
```

## Corpus classes

### 1. UI reference corpus

Initial source account:

```text
Nazia-99
```

Purpose:

- design composition patterns;
- layout systems;
- responsive techniques;
- interaction patterns;
- component behavior;
- visual hierarchy;
- navigation and information architecture;
- state presentation;
- CSS and frontend implementation concepts;
- accessibility-relevant UI behavior when evidence exists.

Default treatment:

```text
PATTERN_REFERENCE_FIRST
```

Each repository must be evaluated independently for relevance, provenance, and license. Account ownership does not imply a shared license across repositories.

For repositories with no verified reuse license:

- study general design patterns;
- study interaction concepts;
- study component behavior;
- study layout techniques;
- study general implementation logic and concepts;

but:

```text
DO NOT COPY ORIGINAL SOURCE CODE
DO NOT COPY ASSETS
DO NOT SUBSTANTIALLY REPRODUCE IMPLEMENTATION
```

Explicit acknowledgement of `Nazia-99` and the specific source repository is mandatory for retained pattern records.

For a repository with a verified permissive license, direct reuse is not automatic. CUIR must first record the exact license, covered artifact, required notices, source revision, and why direct reuse is preferable to an Orchestra-native implementation.

### 2. Icon reference corpus

The icon corpus is a separate sub-corpus because it contains reusable design assets rather than only UI-layout inspiration.

#### `simple-icons/simple-icons`

Observed repository license: `CC0-1.0`.

Treatment:

```text
CATEGORY = BRAND_ICONS
COPYRIGHT_REUSE = PERMITTED
TRADEMARK_OR_OTHER_BRAND_RIGHTS = NOT_CLEARED_BY_CC0
DEFAULT_REUSE_CLASS = REUSE_WITH_RIGHTS_REVIEW
```

CC0 permits broad copyright reuse, modification, and redistribution, including commercial use. It does not waive trademark or patent rights. Brand icons therefore require a separate trademark/brand-context review when their use could imply affiliation, sponsorship, endorsement, or misuse of a protected mark.

#### `tabler/tabler-icons`

Observed repository license: `MIT`.

Treatment:

```text
CATEGORY = GENERAL_UI_ICONS
DIRECT_REUSE = PERMITTED_WITH_NOTICE
MODIFICATION = PERMITTED_WITH_NOTICE
COMMERCIAL_USE = PERMITTED_WITH_NOTICE
DEFAULT_REUSE_CLASS = REUSE_WITH_NOTICE
```

Required license/copyright notices must be preserved when the license requires them for copied or substantial portions.

#### `lucide-icons/lucide`

Observed primary repository license: `ISC`.

The repository license also identifies a Feather-derived subset under `MIT`.

Treatment:

```text
CATEGORY = GENERAL_UI_ICONS
PRIMARY_LICENSE = ISC
FEATHER_DERIVED_SUBSET = MIT
DIRECT_REUSE = PERMITTED_WITH_APPLICABLE_NOTICE
MODIFICATION = PERMITTED_WITH_APPLICABLE_NOTICE
COMMERCIAL_USE = PERMITTED_WITH_APPLICABLE_NOTICE
DEFAULT_REUSE_CLASS = REUSE_WITH_NOTICE
```

CUIR must preserve the applicable notice and must retain the Feather/MIT distinction for icons listed by the Lucide license as Feather-derived.

## Reuse classification

Every retained external source or asset must receive one of these dispositions:

### `REFERENCE_ONLY`

Use concepts, patterns, or general logic only. Do not copy source expression or assets.

Typical cases:

- no license detected;
- license scope unclear;
- direct reuse is unnecessary;
- source is useful as inspiration but should remain decoupled from Orchestra.

### `REUSE_WITH_NOTICE`

Direct reuse or modification is allowed by a verified permissive license, subject to all required copyright/license notices and any artifact-specific obligations.

Typical cases:

- MIT;
- ISC;
- another separately reviewed permissive license with equivalent applicable permissions.

### `REUSE_WITH_RIGHTS_REVIEW`

Copyright licensing permits reuse, but trademark, brand, patent, asset-origin, or other rights may still constrain the intended use.

Typical case:

- CC0 brand/logo assets from Simple Icons.

### `PROHIBITED`

Do not use the source or asset when provenance, licensing, rights, integrity, or safety cannot establish an acceptable basis for the intended use.

## Required source record

No external pattern or reusable asset becomes Cloak knowledge solely because it was discovered.

Each retained source record must identify at minimum:

```text
repository
owner
source_revision
source_paths_or_artifact_ids
source_category
license_identifier
license_evidence
reuse_classification
attribution_or_notice_requirements
pattern_or_asset_summary
what_was_learned_or_reused
what_was_not_copied
review_owner
```

If a repository or artifact changes after the pinned revision, the old evidence remains historical and the new revision requires a new or explicitly refreshed record.

## Phase sequence

### CUIR-0 - Corpus governance and intake contract

Goal: freeze the corpus rules before broad inspection.

Required outputs:

- eligibility criteria;
- source-record shape;
- license/reuse classifications;
- provenance and attribution rules;
- external-code non-execution rule;
- data-minimization and evidence rules;
- fail-closed treatment for missing/ambiguous licenses;
- role ownership and handoff rules.

No external implementation is copied during CUIR-0.

### CUIR-1 - Current inventory and license/provenance classification

Goal: establish the exact eligible corpus from current GitHub source reality.

Required actions:

- inventory current eligible public repositories under `Nazia-99`;
- do not hard-code the historical repository count;
- pin each retained repository to an exact source revision before deeper pattern extraction;
- classify each repository license independently;
- inventory the icon corpus separately;
- pin `simple-icons/simple-icons`, `tabler/tabler-icons`, and `lucide-icons/lucide` to exact revisions;
- capture authoritative license files and relevant artifact-specific licensing distinctions;
- exclude repositories or artifacts whose provenance/rights cannot support the intended treatment.

CUIR-1 is inventory and classification, not mass source ingestion.

### CUIR-2 - Static pattern and asset analysis

Goal: extract useful design intelligence without executing external projects.

Permitted:

- static source inspection;
- static asset inspection;
- documentation review;
- structure/layout analysis;
- component and interaction concept analysis;
- license/provenance verification.

Not permitted:

- running external build scripts;
- installing external project dependencies merely to inspect the corpus;
- executing external application code;
- executing unknown repository scripts;
- treating screenshots or generated demos as evidence of rights ownership.

Pattern findings must be concept-level unless direct reuse has already been explicitly classified as allowed.

### CUIR-3 - Orchestra-native normalization

Goal: convert raw findings into a small reusable Cloak pattern vocabulary rather than carrying hundreds of repository-specific fragments into model context.

Normalize findings into categories such as:

- navigation;
- layout;
- responsive composition;
- forms;
- feedback and status;
- destructive actions;
- data-dense surfaces;
- cards and content grouping;
- empty/loading/error states;
- accessibility and focus;
- visual hierarchy;
- icon semantics;
- icon selection and consistency;
- brand-icon handling.

Each normalized pattern must preserve source references and reuse classification while removing unnecessary source-specific implementation detail.

### CUIR-4 - Cloak Pattern Intelligence integration

Goal: make the normalized corpus useful through progressive disclosure rather than injecting the entire corpus into every Cloak task.

Cloak should be able to:

1. identify the UI/UX problem class;
2. retrieve the smallest relevant normalized pattern set;
3. distinguish project-native requirements from external inspiration;
4. prefer existing project components/tokens/assets when appropriate;
5. identify when a reusable icon asset is license-compatible;
6. produce provenance-aware recommendations;
7. hand implementation to Ponytail/Clockwork rather than silently implementing outside its role.

The integration must not grant learned patterns execution, authority, merge, release, deployment, or policy rights.

### CUIR-5 - Controlled applied evaluation

Goal: determine whether the corpus materially improves Cloak output rather than assuming that a larger reference library is beneficial.

Use representative UI tasks and compare the upgraded path against the existing Cloak baseline on measurable criteria such as:

- requirement coverage;
- useful pattern retrieval;
- design consistency;
- project-native reuse;
- accessibility coverage;
- responsive coverage;
- unsupported invention rate;
- provenance correctness;
- license/reuse correctness;
- unnecessary context load;
- source-copying violations;
- implementation handoff quality.

A larger corpus is not itself evidence of improved specialist quality.

### CUIR-6 - Adoption and closeout

Goal: decide which corpus capabilities become supported Cloak behavior.

Possible outcomes may include:

```text
ADOPT
ADOPT_OPTIONAL
REVISE_AND_RETEST
REJECT_OR_RETIRE
```

Any adoption decision must preserve source provenance, license obligations, progressive disclosure, and Orchestra authority boundaries.

## Specialist ownership

### Artificer

Owns:

- source intake;
- pinned repository identity;
- static inspection boundary;
- license and provenance evidence collection;
- external-pattern records.

Artificer does not approve its own findings for implementation.

### Cloak

Owns:

- UI/UX interpretation;
- pattern taxonomy;
- pattern selection;
- icon-design suitability;
- accessibility/user-facing consequences;
- provenance-aware design recommendations.

Cloak does not gain code implementation authority from the corpus.

### Governor

Owns licensing/governance review when reuse obligations or rights are ambiguous or material.

### Clockwork

Owns architecture and component-boundary decisions when a pattern affects frontend architecture or shared component ownership.

### Ponytail

Owns separately authorized implementation of Orchestra-native or project-native changes.

### Overseer

Owns evaluation evidence, regression evidence, and readiness verification.

### Arbiter

Owns evidence-based transition disposition between governed CUIR phases.

## Current sequencing

The P2.2B VS Code multi-harness/provider qualification unit remains the immediate active bounded unit.

After P2.2B reaches its deterministic qualification and live-evidence checkpoint, the next planned specialist-evolution lane is:

```text
CUIR-0
  -> CUIR-1
  -> CUIR-2
  -> CUIR-3
  -> CUIR-4
  -> CUIR-5
  -> CUIR-6
```

If live VS Code/provider evidence requires a local interactive user session, CUIR work may advance within its own governed scope while that external evidence is pending. Provider routing policy must not treat CUIR progress as provider qualification evidence.

## Explicit non-goals

This plan does not authorize:

- automatic provider routing;
- provider fallback;
- direct provider API integration;
- credential changes;
- installed-integration refresh;
- release or tag movement;
- deployment or production mutation;
- policy/ruleset activation or bypass;
- branch deletion;
- force push or history rewrite;
- automatic ingestion of every discovered repository;
- execution of external repository code;
- copying source from unlicensed repositories;
- ignoring attribution or license notices because a repository is public;
- treating CC0 brand icons as a blanket trademark license;
- automatic promotion of discovered patterns into Cloak.

## Final planning disposition

```text
CLOAK_UI_REFERENCE_CORPUS_V1 = FINALIZED_PLANNING_NOT_IMPLEMENTED
UI_CORPUS_INITIAL_ACCOUNT = Nazia-99
UI_CORPUS_COUNT = DISCOVER_AT_CUIR_1
ICON_CORPUS = simple-icons/simple-icons;tabler/tabler-icons;lucide-icons/lucide
UNLICENSED_UI_SOURCE_DEFAULT = REFERENCE_ONLY
MIT_OR_ISC_DIRECT_REUSE = PERMITTED_WITH_APPLICABLE_NOTICE
CC0_BRAND_ICON_REUSE = COPYRIGHT_PERMITTED_RIGHTS_REVIEW_REQUIRED
EXTERNAL_CODE_EXECUTION = PROHIBITED_DURING_CORPUS_ANALYSIS
PADAYON_ROLE = MIRROR_CONTINUITY_ONLY
NEXT_AFTER_P2_2B_EVIDENCE_CHECKPOINT = CUIR_0
```
