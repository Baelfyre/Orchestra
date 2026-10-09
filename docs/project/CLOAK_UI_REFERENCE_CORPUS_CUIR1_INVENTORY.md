# CLOAK UI Reference Corpus - CUIR-1 Inventory and Per-Repository Provenance

## Purpose

This record captures the CUIR-1 live-source inventory snapshot for the Cloak UI reference corpus.

CUIR-1 is inventory and provenance classification only. It does not execute external projects, install their dependencies, copy their source code or assets, implement Cloak UI changes, or begin CUIR-2 static pattern analysis.

The canonical machine evidence for this snapshot is:

`machine/provenance/cloak-ui-reference-cuir1.v1.json`

Every retained source record in that file conforms to:

`machine/schemas/cloak-ui-reference-source-record.v1.schema.json`

## Verified Orchestra baseline

CUIR-1 was prepared from Orchestra `main` at:

`85c6b38e574e2355d67f35b768b9432dc26de358`

The live baseline matched the preceding CUIR-0 handoff before the CUIR-1 branch was created.

## Nazia-99 discovery snapshot

GitHub live repository discovery for `user:Nazia-99` on 2026-08-31 produced:

- page 1: 100 unique public repositories;
- page 2: 44 unique public repositories;
- page 3: 0 repositories;
- total unique public repository identities: 144.

The machine record stores all 144 identities and a SHA-256 digest of the sorted repository identity list. The count is a dated snapshot, not a permanent account-wide constant. A later refresh must rediscover the live count.

## Retention policy

Account membership alone does not make a repository part of the canonical Cloak reference corpus.

CUIR-1 retained a source only when the repository was:

1. public;
2. non-empty at repository-metadata screening;
3. relevant to a generalizable UI or application pattern;
4. functionally distinct enough to add value after redundancy screening;
5. pinnable to an exact 40-character revision; and
6. classifiable under the CUIR-0 license/provenance rules.

Repositories not retained remain in the discovery inventory only. They receive no license inference, reuse classification, or copying authority from CUIR-1.

The screening result is:

- 20 retained Nazia-99 UI-reference repositories;
- 124 discovered but not retained repositories;
- 3 separately governed icon-corpus repositories;
- 23 schema-valid retained source records in total.

The non-retained account set is grouped by explicit screening reason in the machine record. Reasons include empty repository metadata, non-UI media, decorative or scene-only material, brand/media-specific examples not needed for a general pattern, and redundant or lower-priority variants.

## Retained Nazia-99 functional coverage

The retained source set covers distinct concept-level areas for later static analysis:

- expandable sidebar and persistent navigation;
- bottom navigation;
- authentication/login form composition;
- file upload interaction;
- invoice/document layout;
- stacked notifications;
- multi-step forms;
- general e-commerce product cards;
- input-field label/focus behavior;
- calendar application surfaces;
- task-list application surfaces;
- weather/dashboard layout;
- accordion/disclosure controls;
- action-progress feedback;
- radio selection;
- password visibility controls;
- pricing-card hierarchy;
- subscription form composition;
- profile-card hierarchy; and
- compact action menus.

These labels describe the CUIR-1 curation purpose only. Detailed pattern extraction belongs to CUIR-2.

## Nazia-99 rights treatment

For every retained Nazia-99 repository, GitHub repository metadata reported `license=null` during CUIR-1 inspection while the repository was pinned to an exact revision.

CUIR-1 therefore records:

`license_identifier = AMBIGUOUS`

and:

`reuse_classification = REFERENCE_ONLY`

This is deliberately conservative. Repository metadata showing `license=null` is not treated as proof that no license text exists anywhere in the repository. It also does not authorize direct source-code or asset reuse.

Every retained Nazia-99 record requires attribution to both:

- `Nazia-99`; and
- the specific source repository.

No source code, assets, generated output, or external dependency content was copied or executed.

## Separate icon corpus

### simple-icons/simple-icons

Pinned revision:

`e3d830c3b553bb657df7389b673d1d78abf5159b`

CUIR-1 treatment:

- source category: `BRAND_ICONS`;
- license: `CC0-1.0`;
- reuse classification: `REUSE_WITH_RIGHTS_REVIEW`.

The pinned license applies CC0 1.0 copyright treatment while explicitly preserving trademark and other rights considerations. Brand-icon reuse therefore requires a separate rights review.

### tabler/tabler-icons

Pinned revision:

`5a0fe38e97784d94279ce4eb1bf85f9a91bf027e`

CUIR-1 treatment:

- source category: `GENERAL_UI_ICONS`;
- license: `MIT`;
- reuse classification: `REUSE_WITH_NOTICE`.

Applicable MIT copyright and permission notices must be preserved with reused material.

### lucide-icons/lucide

Pinned revision:

`796dad298f8d78c5da204c3e62a5ed93c2bfcd1e`

CUIR-1 treatment:

- source category: `GENERAL_UI_ICONS`;
- primary license: `ISC`;
- reuse classification: `REUSE_WITH_NOTICE`.

The pinned license separately identifies a Feather-derived subset under MIT. CUIR-1 preserves that ISC versus Feather/MIT distinction at artifact/subset level.

## External execution boundary

The machine record fixes all of the following to `false`:

- running external build scripts;
- installing external project dependencies;
- executing external application code;
- executing unknown scripts;
- mirroring an entire external repository;
- automatic ingestion.

CUIR-1 used static repository identity, metadata, revision, and license evidence only.

## Parallel provider lane

The VS Code provider-observation lane remains separate.

CUIR-1 does not create live provider evidence and does not authorize:

- automatic multi-provider routing;
- automatic provider fallback;
- direct provider API use; or
- routing-policy activation.

Live VS Code provider observations remain `PENDING_USER_ASSISTED`.

## Phase boundary

This inventory does not start CUIR-2.

CUIR-2 may begin only after CUIR-1 completes the active Orchestra validation, review, signed-materialization/canonicalization process, and the resulting canonical source state is verified.
