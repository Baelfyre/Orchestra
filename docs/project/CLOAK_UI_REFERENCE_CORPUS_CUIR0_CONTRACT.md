# Cloak UI Reference Corpus — CUIR-0 Governance and Intake Contract

Status: `CUIR_0_IMPLEMENTED_CANDIDATE`

Plan ID: `CLOAK_UI_REFERENCE_CORPUS_V1`

Phase: `CUIR-0`

Canonical planning source: `docs/project/CLOAK_UI_REFERENCE_CORPUS_PLAN.md`

Machine policy: `machine/governance/cloak-ui-reference-corpus-policy.v1.json`

Source-record schema: `machine/schemas/cloak-ui-reference-source-record.v1.schema.json`

Policy schema: `machine/schemas/cloak-ui-reference-corpus-policy.v1.schema.json`

## Purpose

CUIR-0 freezes the governance and intake rules for the Cloak UI Reference Corpus before broad repository inventory or pattern extraction begins.

This unit does **not** inventory the current `Nazia-99` repositories, pin individual corpus repositories, execute external projects, ingest source into Cloak, or promote any pattern into supported behavior. Those activities begin only in later governed CUIR phases.

The governing invariant is:

```text
REFERENCE TO PATTERN OR LOGIC != COPYING SOURCE CODE
PUBLIC REPOSITORY != AUTOMATIC REUSE PERMISSION
DESIGN INSPIRATION != SOURCE OWNERSHIP
```

## CUIR-0 eligibility contract

A source is eligible to proceed toward CUIR-1 classification only when all of the following hold:

1. the source is publicly visible at the time of inspection;
2. the repository or artifact has material UI, UX, icon, interaction, layout, responsive, visual-hierarchy, accessibility, or frontend-pattern relevance;
3. repository identity is unambiguous;
4. each repository is licensed and classified independently rather than inheriting a license from an account or neighboring repository;
5. a retained source is pinned to an exact source revision before deep CUIR-2 analysis;
6. relevant provenance evidence can be retained without mirroring the full repository;
7. no external execution is required to establish the intended static evidence.

The historical approximate repository count is not an intake constant:

```text
UI_CORPUS_ACCOUNT = Nazia-99
UI_CORPUS_COUNT = DISCOVER_AT_CUIR_1
```

CUIR-0 therefore contains no hard-coded repository count and no inventory result.

## Corpus separation

### UI reference corpus

Initial account:

```text
Nazia-99
```

Default treatment:

```text
PATTERN_REFERENCE_FIRST
```

The default purpose is concept-level pattern study, not source acquisition.

### Icon reference corpus

The icon corpus remains a separate asset-oriented sub-corpus:

- `simple-icons/simple-icons`
- `tabler/tabler-icons`
- `lucide-icons/lucide`

Their current license assertions remain planning inputs until CUIR-1 pins exact repository revisions and authoritative license evidence. CUIR-0 does not convert those planning assertions into fresh empirical license evidence.

## Reuse classifications

Every retained source or asset must receive exactly one of these dispositions:

### `REFERENCE_ONLY`

Concepts, patterns, behavior, layout techniques, or general logic may be studied. Original source expression and assets are not copied.

### `REUSE_WITH_NOTICE`

Direct reuse or modification may occur only after a verified permissive license and applicable notice obligations are recorded for the pinned source revision.

### `REUSE_WITH_RIGHTS_REVIEW`

Copyright permission may exist, but trademark, brand, patent, asset-origin, or other rights require separate review before the intended use.

### `PROHIBITED`

The source or asset must not be used when provenance, licensing, rights, integrity, or safety cannot establish an acceptable basis for the intended use.

## Fail-closed licensing matrix

| Evidence state | Pattern study | Direct reuse |
| --- | --- | --- |
| Verified permissive license | Allowed within recorded scope | Only under `REUSE_WITH_NOTICE` or separately reviewed rights classification |
| No license detected | `REFERENCE_ONLY` | `PROHIBITED` |
| License scope ambiguous | `REFERENCE_ONLY` | `PROHIBITED` |
| Copyright permission exists but other rights are unresolved | Concept-level study allowed when provenance is adequate | `PROHIBITED` until rights review completes |
| Provenance or integrity is unacceptable | `PROHIBITED` | `PROHIBITED` |

A public repository is never treated as permission to copy.

## Source-record contract

Each retained CUIR source record must include at minimum:

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

The machine schema also requires a record identifier and schema version.

For a missing license, use an explicit evidence state such as `NONE_DETECTED`; do not omit the license field. For ambiguous license scope, use an explicit state such as `AMBIGUOUS`. Either state limits the record to `REFERENCE_ONLY` or `PROHIBITED`.

For retained `Nazia-99` UI pattern records, attribution must name `Nazia-99` and the specific repository. Account-level attribution alone is insufficient.

If the upstream repository changes after the pinned revision, the previous record remains historical and the changed revision requires a new or explicitly refreshed record.

## External-code non-execution rule

CUIR corpus analysis is static by default. During CUIR-0 and subsequent static corpus analysis:

```text
RUN_EXTERNAL_BUILD_SCRIPTS = FALSE
INSTALL_EXTERNAL_PROJECT_DEPENDENCIES = FALSE
EXECUTE_EXTERNAL_APPLICATION_CODE = FALSE
EXECUTE_UNKNOWN_REPOSITORY_SCRIPTS = FALSE
```

Permitted evidence collection includes repository metadata, source text inspection, asset inspection, documentation review, structure analysis, and authoritative license/provenance files.

A screenshot, demo, or generated output does not itself establish ownership or reuse rights.

## Data minimization and evidence rules

CUIR records must retain the smallest evidence set needed to establish provenance, relevance, and licensing decisions.

Required behavior:

- retain exact repository identity and pinned revision;
- retain only relevant source paths or artifact identifiers;
- retain authoritative license evidence or an explicit absence/ambiguity check;
- retain concept-level pattern summaries by default;
- retain required attribution or license notices;
- retain what was learned or reused and what was deliberately not copied.

Prohibited behavior:

- mirroring an entire repository merely for corpus storage;
- retaining unrelated assets or source files;
- treating corpus size as evidence of specialist quality;
- automatically injecting all retained patterns into Cloak context.

## Specialist ownership and handoff

### Artificer

Owns source intake, repository pinning, static-inspection boundaries, license/provenance evidence collection, and external-source records.

Artificer cannot approve its own findings for implementation.

### Cloak

Owns UI/UX interpretation, pattern taxonomy, pattern selection, icon suitability, accessibility/user consequences, and provenance-aware design recommendations.

Cloak receives no code implementation authority from the corpus.

### Governor

Owns licensing/governance review when reuse obligations or rights are ambiguous or material.

### Clockwork

Owns architecture and component-boundary decisions when a pattern affects shared frontend architecture or ownership.

### Ponytail

Owns separately authorized implementation of Orchestra-native or project-native changes.

### Overseer

Owns evaluation evidence, regression evidence, and readiness verification.

### Arbiter

Owns evidence-based disposition between governed CUIR phases.

## Authority boundary

CUIR-0 grants no authority for:

- external code execution;
- automatic corpus ingestion;
- code implementation;
- automatic provider routing or fallback;
- direct provider API integration;
- credential/settings mutation;
- installed-integration refresh;
- Registry mutation;
- merge or release;
- deployment or production mutation;
- policy/ruleset activation or bypass;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.

The machine policy encodes the CUIR-specific authority fields as constant `false` values.

## CUIR-0 exit gate

CUIR-0 is ready for closeout only when:

1. the machine governance policy validates against its schema;
2. the source-record schema contains the required provenance fields;
3. missing or ambiguous licenses cannot authorize direct reuse;
4. repository-count discovery remains deferred to CUIR-1;
5. account-wide license inference is disabled;
6. external execution remains prohibited;
7. data-minimization rules prevent full-repository mirroring by default;
8. Artificer/Cloak/Governor/Clockwork/Ponytail/Overseer/Arbiter ownership boundaries are preserved;
9. tests demonstrate the contract fails closed for malformed source revisions, missing provenance fields, and invalid reuse claims.

Passing CUIR-0 authorizes only the next bounded inventory/classification phase defined by the canonical plan:

```text
CUIR-1 = CURRENT_INVENTORY_AND_LICENSE_PROVENANCE_CLASSIFICATION
```

It does not authorize CUIR-2 static pattern extraction until CUIR-1 establishes the retained corpus and exact revision/license evidence.
