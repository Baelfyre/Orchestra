# UIX-2 Design-Source Preservation Workflow

Status: `UIX_2_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `c331634dc63fbebb86ca07274c06262d5b52a50d`

UIX-1 contract: `machine/schemas/ui-design-contract.schema.json`

Machine workflow: `machine/ui/design-source-preservation-workflow.v1.json`

Preservation report schema: `machine/schemas/design-source-preservation-report.schema.json`

## Purpose

UIX-2 freezes the pre-implementation design-source preservation protocol that Cloak will later consume during specialist integration. It prevents a model from jumping from a screenshot, Figma node, Storybook story, or project design system directly into implementation without first identifying source evidence, resolving project-native mappings, preserving known tokens/components/assets, and reporting unresolved evidence.

UIX-2 is a contract and deterministic evidence layer. It does not implement a Figma client, Code Connect adapter, Storybook adapter, browser adapter, target-project UI, or runtime routing change.

## Workflow

The machine workflow requires this exact intake sequence:

```text
VERIFY_SOURCE_IDENTITY
  -> INVENTORY_DESIGN_EVIDENCE
  -> RESOLVE_PROJECT_NATIVE_MAPPINGS
  -> PRESERVE_TOKENS_COMPONENTS_ASSETS
  -> REPORT_UNRESOLVED_EVIDENCE
  -> ISSUE_PRE_IMPLEMENTATION_HANDOFF
```

Implementation may not be treated as ready merely because a source artifact exists. The intake report must establish what is confirmed, what maps to the target project, what requires approved adaptation, and what remains unresolved.

## Source identity

The UIX-2 report supports the same provider classifications frozen by UIX-1:

- `FIGMA`
- `PROJECT_NATIVE`
- `STORYBOOK`
- `SCREENSHOT`
- `REFERENCE_IMAGE`
- `OTHER_STRUCTURED`
- `NONE`

Figma is optional. Project-native component documentation and token systems are valid first-class evidence. Screenshots and reference images may supply useful visual evidence but remain weaker than structured component/token evidence and never become authority.

## Preservation precedence

UIX-2 freezes this precedence:

```text
EXACT_SUPPLIED_OR_PROJECT_EVIDENCE
  > EXISTING_PROJECT_COMPONENT
  > SEMANTIC_TOKEN_MAPPING
  > APPROVED_ADAPTATION
  > UNRESOLVED_NO_GUESS
```

The precedence means:

1. preserve exact supplied/project evidence when it exists;
2. resolve an existing project-native component before creating an equivalent;
3. preserve semantic token intent instead of copying arbitrary raw values;
4. use an adaptation only when its reason and explicit approval are recorded;
5. when evidence is insufficient, report `UNRESOLVED` rather than fabricate certainty.

## Evidence inventory

Each evidence item records:

- evidence kind: token, component, layout, theme, asset, or accessibility;
- stable subject reference;
- target location in the UI Design Contract;
- source reference;
- evidence confidence;
- preservation disposition;
- reason/approval when adaptation or inference is involved.

`INFERRED_WITH_EXPLICIT_APPROVAL` and `ADAPT_WITH_APPROVAL` are fail-closed and require an explicit approval reference.

## Component preservation

Component mappings use the UIX-1 project mapping semantics:

- `EXACT`
- `ADAPTED`
- `NONE`
- `UNRESOLVED`

`EXACT` and `ADAPTED` require a concrete target project component. `ADAPTED` also requires a reason and approval reference.

The preservation report records source component identity, target project component, variant coverage, state coverage, and missing states. Missing states remain visible rather than being hidden by a visually similar implementation.

## Token preservation

UIX-2 does not copy raw design values blindly. The required rule is semantic preservation first:

- identify source token intent;
- map to an existing project semantic token where possible;
- retain source reference and confidence;
- do not create arbitrary one-off values merely to mimic a screenshot;
- use approved adaptation or unresolved evidence when no reliable mapping exists.

UIX-3 will own profile/theme registry semantics. UIX-2 does not prematurely define a universal aesthetic vocabulary.

## Asset preservation

Asset dispositions are:

- `EXACT_PROJECT_ASSET`
- `EXISTING_PROJECT_MATCH`
- `APPROVED_SUBSTITUTE`
- `UNRESOLVED`

Known assets must be preserved or mapped to an existing verified project asset. A substitute requires both a reason and explicit approval. An unresolved asset must not be silently replaced with a generated icon, logo, illustration, font, or image.

Governor review remains required when adoption, redistribution, licensing, or IP consequences exist. UIX-2 does not perform that review or grant adoption authority.

## Unresolved evidence

Every unresolved item records:

- subject reference;
- reason;
- required resolution;
- blocking classification.

Blocking classifications are:

```text
IMPLEMENTATION_BLOCKING
VALIDATION_BLOCKING
NON_BLOCKING
```

If any item is `IMPLEMENTATION_BLOCKING`, the report cannot claim `READY_FOR_IMPLEMENTATION`. It must fail closed to:

```text
BLOCKED_UNRESOLVED_EVIDENCE
```

with at least one explicit blocker.

This is the main UIX-2 anti-hallucination boundary: uncertainty remains visible and cannot be converted into implementation readiness by prose confidence.

## Handoff states

The report supports:

- `READY_FOR_ARCHITECTURE_REVIEW`
- `READY_FOR_IMPLEMENTATION`
- `BLOCKED_UNRESOLVED_EVIDENCE`

These statuses describe evidence readiness only. They do not grant authority.

Ownership remains:

- Cloak: design-source evidence and preservation requirements;
- Clockwork: architecture/component boundary review;
- Ponytail: authorized implementation;
- Overseer: rendered/browser/accessibility evidence;
- Arbiter: transition disposition;
- Governor: adoption/IP/license review when applicable.

## Deterministic validation

UIX-2 adds deterministic coverage proving:

1. the workflow record validates against its Draft 2020-12 schema;
2. Figma is optional and project-native evidence remains valid;
3. exact project evidence/project components/semantic tokens precede approved adaptation;
4. invalid fixtures with implementation-blocking unresolved evidence cannot claim implementation readiness;
5. adaptation or inference without explicit approval is rejected;
6. implementation-blocking unresolved evidence becomes valid only after the handoff is explicitly blocked;
7. workflow/report/tool evidence cannot create implementation authority.

## Non-goals

UIX-2 does not:

- modify `skills/cloak/**` yet;
- modify routing or specialist authority;
- modify Codex or other adapter copies;
- implement Figma or Code Connect ingestion;
- install Storybook, Playwright, axe, token tools, or component libraries;
- mutate a Figma file or target project;
- perform visual comparison;
- create UI code;
- authorize dependency adoption;
- authorize release, deployment, policy activation, marketplace publication, or production mutation.

Those concerns remain with later UIX phases and existing governance.

## Exit condition

UIX-2 is ready for canonicalization only when its machine workflow, schemas, fixtures, tests, documentation, and required discovery/changelog parity pass the complete exact-head Orchestra validation matrix. UIX-3 remains a separate next unit after independent canonical readback.
