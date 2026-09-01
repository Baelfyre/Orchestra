# Cloak UI Reference Corpus - CUIR-3 Orchestra-Native Normalization

Status: `CUIR_3_NORMALIZATION_CANDIDATE_PENDING_CANONICALIZATION`

Plan ID: `CLOAK_UI_REFERENCE_CORPUS_V1`

Phase: `CUIR-3`

Canonical planning source: `docs/project/CLOAK_UI_REFERENCE_CORPUS_PLAN.md`

Machine catalog: `machine/knowledge/cloak-ui-reference-cuir3.v1.json`

Pattern schema: `machine/schemas/cloak-ui-normalized-pattern.v1.schema.json`

Validation surface: `tests/runtime/test_cloak_ui_reference_corpus_cuir3.py`

## Purpose

CUIR-3 converts the canonical CUIR-2 static-analysis findings into a small Orchestra-native pattern vocabulary for Cloak.

The phase reduces repository-specific detail while preserving the evidence needed to understand where each normalized pattern came from, what reuse classification still applies, and which accessibility constraints must override inaccessible mechanisms observed in the reference corpus.

CUIR-3 is knowledge normalization only. It does not wire the vocabulary into Cloak runtime, task classification, progressive disclosure, automatic retrieval, provider routing, implementation, release, deployment, or policy activation. Those integration questions begin no earlier than CUIR-4.

## Canonical input

CUIR-3 is bound to the already verified CUIR-2 implementation and lifecycle closeout:

```text
CUIR-2 canonical implementation:
298f7be98b4d2c55cb48f98c0ddeafaf848e53b0
TREE=50bfea14a68096bb7c507bb0db8e81ff5a050065

CUIR-2 lifecycle closeout:
24d356ec5d6aa16e1f80ccdbd04a0e00c9fe0e5a
TREE=c6034dec375f8dc62554fbc957833bd85c8249de
```

The input contains exactly 23 CUIR-2 analysis records:

- 20 `Nazia-99` UI references, all retained as `REFERENCE_ONLY`;
- `simple-icons/simple-icons`, retained as `REUSE_WITH_RIGHTS_REVIEW`;
- `tabler/tabler-icons`, retained as `REUSE_WITH_NOTICE`;
- `lucide-icons/lucide`, retained as `REUSE_WITH_NOTICE`.

No source revision was refreshed for CUIR-3. No new repository was inspected.

## Normalization rule

The normalization invariant is:

```text
SOURCE-SPECIFIC FINDING -> ORCHESTRA-NATIVE CONCEPT
ORCHESTRA-NATIVE CONCEPT != COPIED SOURCE EXPRESSION
NORMALIZED KNOWLEDGE != IMPLEMENTATION AUTHORITY
```

CUIR-3 merges findings when their behavioral meaning is equivalent at the guidance level. It keeps them separate when interaction semantics, accessibility obligations, destructive-action risk, or reuse/rights classifications differ materially.

Visual treatments such as glassmorphism or neumorphism are not normalized as requirements. The useful part is the underlying state, hierarchy, selection, progress, disclosure, or information model.

## Normalized taxonomy

The candidate taxonomy contains 12 category families and 15 normalized patterns.

| Category | Normalized patterns |
| --- | --- |
| Navigation and destination state | Destination state navigation; Contextual navigation and shortcuts |
| Forms and input | Authentication and multi-step form flow; Semantic field and control state |
| Selection and disclosure | Selection and disclosure state |
| Feedback, status, and progress | Operation progress lifecycle; Outcome feedback and empty state; Explicit state labels and metadata |
| Action hierarchy | Action priority and destructive separation |
| Data and summary | Dense summary and status hierarchy |
| Cards and content grouping | Content summary card and call to action |
| Collection and sequence | Ordered collection and temporal sequence |
| Accessibility and semantics | Semantic control accessibility baseline |
| Motion and state emphasis | Motion as secondary state feedback |
| General UI icons | General UI icon system |
| Brand icon rights | Brand icon traceability and rights |

The taxonomy is intentionally smaller than the original CUIR-2 candidate-pattern set. It is designed to support later progressive disclosure without injecting dozens of repository-specific pattern names into every Cloak task.

## Pattern normalization decisions

### Navigation

CUIR-2 separately recorded collapsible side navigation, compact bottom navigation, active destination feedback, secondary navigation, calendar navigation, and a today shortcut.

CUIR-3 keeps two broader concerns:

1. **Destination state navigation** - the current destination remains explicit even when navigation changes density or presentation.
2. **Contextual navigation and shortcuts** - secondary or temporal shortcuts remain subordinate to the primary navigation model and must make their resulting context clear.

The reference implementations' use of clickable list items or unlabeled icon controls is not promoted.

### Forms and controls

Login/signup switching, multi-step forms, password visibility, radio selection, animated field labels, and subscription validation all expose useful state models.

CUIR-3 separates:

- **Authentication and multi-step form flow**, for task grouping, current step/mode, local validation, and predictable transitions;
- **Semantic field and control state**, for labels, native control semantics, selection/toggle state, error, and success feedback.

Generic click-target substitutes, placeholder-only field naming, and missing control labels are treated as defects, not reusable patterns.

### Selection and disclosure

Calendar selection, single-open accordion behavior, and radio selection are normalized into **Selection and disclosure state**.

The common principle is explicit selected/expanded state with a predictable path back to an unselected or collapsed state. Native button or radio semantics take precedence over the generic div mechanisms seen in some references.

### Progress and outcomes

File upload, aggregate invoice progress, progress-button state, and multi-step form progress are normalized into **Operation progress lifecycle**.

Completion, empty state, validation error, and success are normalized separately as **Outcome feedback and empty state** because a terminal or no-content outcome communicates a different user need from an in-progress state.

Small identity, time, status, progress, and state labels across upload, invoice, notification, password, forecast, and subscription references become **Explicit state labels and metadata**.

### Action hierarchy

Secondary authentication actions, overflow actions, primary pricing actions, profile/social actions, and destructive grouping are normalized into **Action priority and destructive separation**.

Destructive actions remain a stronger risk class than ordinary secondary actions. The normalized guidance therefore requires meaningful separation and appropriate confirmation or recovery treatment rather than treating all menu items as equivalent.

### Data and summary hierarchy

Invoice summaries, weather summaries, and commerce product context are normalized into **Dense summary and status hierarchy**.

The reusable idea is a primary summary followed by supporting metrics, per-entity state, fulfillment context, or other secondary facts with a stable reading order.

### Cards and content grouping

Pricing, commerce, and profile references become **Content summary card and call to action**.

CUIR-3 deliberately removes their source-specific decorative styling and retains only the information grouping and action hierarchy.

### Collections and sequences

Notifications, forecast sequences, and task collections become **Ordered collection and temporal sequence**.

The normalized guidance retains item anatomy, meaningful ordering, temporal or completion metadata, and an explicit empty state when appropriate.

### Accessibility baseline

CUIR-2 recorded both good and weak semantic practices. CUIR-3 therefore contains an explicit **Semantic control accessibility baseline** rather than silently normalizing the observed implementation mechanics.

The baseline rejects:

- clickable `div` or `li` replacements when a native link, button, input, radio, checkbox, or disclosure control fits;
- unlabeled icon-only controls;
- placeholder-only field naming;
- missing programmatic selected/expanded state when the interaction requires it.

The corpus can teach a state model without teaching the accessibility defect used to implement it.

### Motion

Animated navigation, notification stacks, progress controls, password state, and animated fields become **Motion as secondary state feedback**.

Motion may reinforce change, but the same state must remain understandable with animation disabled. Substantial non-essential motion requires reduced-motion treatment.

## Icon normalization

### General UI icons

Tabler and Lucide remain `REUSE_WITH_NOTICE`.

Their normalized pattern covers:

- consistent icon vocabulary;
- consistent geometry or stroke treatment;
- semantic role before decoration;
- informative versus decorative accessibility handling;
- applicable notice preservation when material is directly reused.

Lucide's source-level licensing distinction for Feather-derived material remains governed by the CUIR-1 provenance record. CUIR-3 does not flatten that evidence into a new blanket license claim.

### Brand icons

Simple Icons remains `REUSE_WITH_RIGHTS_REVIEW` and is intentionally not merged into the general UI icon pattern.

The normalized pattern preserves:

- brand source traceability;
- brand-guideline linkage;
- accessible identity handling;
- separate trademark, affiliation, sponsorship, endorsement, and other brand-rights review.

CC0 copyright treatment is not a blanket trademark license.

## 23-record coverage

All 23 canonical CUIR-2 analysis IDs are referenced by at least one normalized pattern. No CUIR-2 analysis record is silently dropped and no unknown analysis ID is introduced.

The machine catalog records the complete promoted analysis-ID set and leaves `not_promoted_analysis_ids` empty.

A source may support more than one normalized pattern. This is intentional because a single reference can provide evidence about navigation, semantics, motion, state labels, or action hierarchy simultaneously.

## Evidence count

`evidence_count` is not a quality score.

It is the deterministic number of unique CUIR-2 analysis records supporting a normalized pattern. CUIR-3 does not infer confidence, popularity, superiority, or universal design validity from that count.

## Reuse and provenance preservation

Every normalized pattern points back to:

- one or more canonical CUIR-2 `analysis_id` values;
- the corresponding canonical CUIR-1 source-record paths;
- the inherited reuse classification or classifications.

CUIR-3 does not widen permissions:

```text
REFERENCE_ONLY remains REFERENCE_ONLY
REUSE_WITH_NOTICE remains REUSE_WITH_NOTICE
REUSE_WITH_RIGHTS_REVIEW remains REUSE_WITH_RIGHTS_REVIEW
```

No direct reuse is authorized by the normalization catalog itself.

## CUIR-4 handoff boundary

CUIR-4 is the separately governed integration phase.

CUIR-3 does **not** implement:

- automatic pattern retrieval;
- task-to-pattern classification;
- progressive-disclosure loading;
- skill-file injection;
- adapter integration;
- context-loading logic;
- runtime lookup code;
- automatic provider routing or fallback.

CUIR-4 may later decide how Cloak retrieves the smallest relevant normalized pattern set for a task. That later phase must preserve the provenance, accessibility, licensing, and non-authorizing semantics established here.

## Authority boundary

CUIR-3 creates normalized reference knowledge only.

It does not grant:

- implementation authority;
- runtime execution authority;
- provider execution authority;
- merge authority;
- release authority;
- deployment authority;
- policy activation authority;
- destructive-action authority.

The final candidate invariant is:

```text
CUIR3_NORMALIZED_KNOWLEDGE = GUIDANCE_EVIDENCE
CUIR3_NORMALIZED_KNOWLEDGE != RUNTIME_INTEGRATION
CUIR3_NORMALIZED_KNOWLEDGE != EXECUTION_AUTHORITY
CUIR4_STARTED = false
```
