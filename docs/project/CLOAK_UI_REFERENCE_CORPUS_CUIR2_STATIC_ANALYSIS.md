# Cloak UI Reference Corpus CUIR-2 Static Analysis

## Status

`CUIR-2 = STATIC_ANALYSIS_CANDIDATE_PENDING_CANONICALIZATION`

Date: `2026-08-31`

Source baseline:

`8211dd39cbdd6210495a2a82c756b6feb9fb9cee`

CUIR-1 prerequisite:

`CUIR_1_CANONICAL_MERGED_VERIFIED`

## Purpose

CUIR-2 performs the bounded static source, asset, and documentation analysis authorized by the Cloak UI Reference Corpus plan. It extracts concept-level UI, interaction, information-hierarchy, accessibility, and icon-suitability findings from the 23 exact-revision sources retained by canonical CUIR-1.

CUIR-2 does not normalize those findings into the CUIR-3 taxonomy and does not implement any pattern in Orchestra or a downstream project.

## Frozen analysis boundary

CUIR-2 analyzes only the source records already admitted by CUIR-1:

- 20 retained `Nazia-99` UI references.
- Simple Icons.
- Tabler Icons.
- Lucide.

No additional repository was admitted during this phase and no retained source revision was refreshed.

The analysis remained static-only:

- no external build scripts were run;
- no external project dependencies were installed;
- no external application or repository script was executed;
- no external repository was mirrored;
- no automatic ingestion was introduced;
- no reference-only source code, SVG path data, image asset, package content, or generated output was copied into Orchestra.

## Evidence model

Machine-readable findings are recorded in:

`machine/provenance/cloak-ui-reference-cuir2.v1.json`

Each analysis record in the three bounded machine batches is validated against:

`machine/schemas/cloak-ui-reference-analysis-record.v1.schema.json`

The CUIR-2 index lists the three batch files. Every analysis record binds back to one canonical CUIR-1 source record and preserves:

- exact repository identity;
- exact pinned source revision;
- inherited source category;
- inherited reuse classification;
- inspected static paths;
- concept-level candidate patterns;
- interaction states where present;
- accessibility observations;
- non-copying and non-execution boundaries from the CUIR-2 index.

The human phase record below carries the fuller interpretation, including information hierarchy, responsive observations where actually inspected, implementation cautions, and later-normalization guidance.

## UI reference findings

| Source | Static paths inspected | Concept-level findings | Accessibility or implementation caution |
| --- | --- | --- | --- |
| Expandable Glassmorphism Sidebar Menu UI | `index.html`, CSS, JS | Collapsible navigation, active destination, secondary utilities, account anchor | Prefer native links/buttons; motion must not carry selected state alone |
| Neumorphic Login Form | HTML, CSS | Shared login/sign-up surface, credential grouping, recovery/remember actions | Replace script-only div/anchor controls with native semantics |
| File Upload UI | HTML, JS | File identity, numeric progress, explicit completion | Expose asynchronous status changes programmatically |
| Animated Bottom Navigation Bar | HTML | Compact mutually exclusive destination state | Icon-only controls need accessible names and non-motion selected state |
| Invoice UI | HTML | Summary, entity statuses, aggregate payment progress, contextual actions | Keep status and financial values explicit in text |
| Premium Glassmorphism Calendar UI | HTML, JS | Month navigation, Today recovery, selected-date confirmation | Date cells should be keyboard-operable controls |
| Notification Stack UI | HTML, JS | Repeated notification anatomy, temporal metadata, stack ordering | Scroll motion should be optional and reduced-motion aware |
| Animated Action Menu | HTML | Labeled overflow trigger and secondary action list | Menu items need interactive semantics; destructive actions need distinction |
| Animated Progress Button | HTML, JS | Start, progress, pause/resume, completion lifecycle | Progress/control meaning must not depend on animation library behavior |
| Animated Password Toggle with SVG Eyes | HTML | Explicit Show/Hide password state with decorative feedback | Preserve the native labeled input and textual toggle |
| Multi-Step Form | HTML, JS | Step progress, local validation, review, consent, submitting, success | Associate errors and step state with accessible form semantics |
| Weather App UI | HTML | Current conditions, supporting metrics, forecast sequence | Keep textual weather values even when icons are present |
| Glassmorphism Pricing Card | HTML | Offer summary, feature checklist, single primary action | Treat glow/glass treatment as presentation only |
| Neomorphic Accordion | HTML | Single-open settings disclosure | Use disclosure buttons and expanded-state semantics |
| Custom Radio Buttons | HTML | Styled native single-choice controls | Keep visual state synchronized with native checked state |
| Premium Todo List UI | HTML | Empty state, task completion, collection count, delete action | Completion should use a native control; destructive icons need names |
| Input Field Text Animation | HTML | Animated/floating field-name treatment | Preserve explicit label-to-input relationships |
| E-commerce Product Card | HTML | Price, fulfillment context, product identity, tags, order action | Use a real navigation/action target and keep image alt text |
| CSS Profile Card | HTML | Identity, role, description, social actions, project action | Social icons need explicit action semantics and names |
| SVG Subscription Form | HTML | Email capture, validation error, success, decorative character feedback | Placeholder is not a label; decorative animation must remain nonessential |

These findings describe interaction and information patterns, not a visual-style mandate. CUIR-2 does not canonize glassmorphism, neumorphism, glow effects, hover effects, or animation as Orchestra design defaults.

## Icon-source findings

### Simple Icons

Static inspection covered `README.md`, `DISCLAIMER.md`, and `data/simple-icons.json` at the CUIR-1 pinned revision.

The useful pattern is rights-aware brand-icon metadata: brand title, source, optional guidelines, and optional per-icon license information can be reviewed before a brand icon is selected.

The repository-level CC0 treatment is not sufficient by itself to clear trademark, logo, publicity, patent, or other brand rights. CUIR-2 therefore preserves the CUIR-1 `REUSE_WITH_RIGHTS_REVIEW` classification and authorizes no brand icon reuse.

### Tabler Icons

Static inspection covered `README.md` and the pinned `icons/` directory structure.

The useful pattern is a consistent general-purpose icon system with outline and filled families, a common 24 by 24 grid, and documented SVG/framework delivery surfaces.

CUIR-2 preserves the CUIR-1 `REUSE_WITH_NOTICE` classification but copies no icon artifact and adopts no dependency.

### Lucide

Static inspection covered `README.md` and the pinned `icons/` directory structure.

The useful pattern is a general-purpose, non-brand icon source with paired SVG and JSON artifacts and multiple delivery packages. Lucide explicitly separates itself from brand-logo sourcing.

CUIR-2 preserves the CUIR-1 `REUSE_WITH_NOTICE` classification and the existing ISC versus Feather-derived MIT subset distinction. No icon artifact or package is adopted.

## Cross-source findings for later CUIR-3 normalization

CUIR-2 records the following as candidate findings only:

1. Useful design intelligence often resides in state models and information hierarchy rather than in visual styling.
2. Navigation, form progression, progress, selection, dense information display, and action hierarchy recur across otherwise unrelated examples.
3. Native semantic controls are inconsistent across the corpus. Later normalization should preserve useful interaction concepts while rejecting generic clickable-div regressions.
4. Motion can reinforce state but should not be the only active, progress, error, or completion signal.
5. Brand icon sourcing must remain separate from general UI icon sourcing because the rights and notice obligations differ.

These are not yet the canonical CUIR-3 pattern taxonomy.

## Authority boundary

CUIR-2 does not authorize:

- CUIR-3 normalization;
- source or asset copying from reference-only records;
- external code execution;
- external dependency installation;
- automatic ingestion;
- runtime integration;
- Orchestra-native or downstream UI implementation;
- automatic provider routing or fallback;
- release or tag publication;
- deployment or production mutation;
- policy or ruleset activation, mutation, or bypass;
- branch deletion;
- force push or history rewrite;
- destructive cleanup.

A later implementation phase remains separately governed and must use Orchestra-native or project-native code rather than copied reference-only material.
