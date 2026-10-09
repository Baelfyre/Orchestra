# Documentation and System Reconciliation Guide

## Purpose

Use this guide when Scribe must determine whether documentation, specification, implementation, validation evidence, and research claims still describe the same system state.

Reconciliation is evidence comparison. Scribe does not unilaterally decide architecture, implementation, data semantics, security policy, QA conclusions, UI behavior, or governance approval.

## Three Scribe working modes

### `SPEC_TO_SYSTEM`

Documentation and approved specification lead the workflow.

Typical flow:

`Problem -> Domain Narrative -> Objectives -> Stakeholders -> Scope / Constraints -> Requirements -> Acceptance Criteria -> Specialist Models / Architecture -> Implementation -> Validation -> As-Built Documentation`

Scribe owns the documented problem/domain/requirements representation. Technical decisions remain with the appropriate specialist.

### `SYSTEM_TO_DOCS`

Current system evidence leads the documentation reconstruction.

Typical flow:

`Repository / Runtime / Config / Tests / UI / Records -> Specialist Verification -> Scribe Reconstruction -> Domain Narrative -> Supported Requirements / Capabilities -> Verified Technical Description -> As-Built / Research Documentation`

Explicitly distinguish:

- observed behavior;
- inferred purpose;
- historical intent;
- current implementation;
- validated behavior;
- unresolved assumptions.

Never present inferred intent as established fact.

### `RECONCILE`

Continuously compare:

`INTENT <-> SPECIFICATION <-> IMPLEMENTATION <-> VALIDATION <-> DOCUMENTATION / RESEARCH CLAIMS`

Neither documentation nor code is automatically authoritative without context. Authority depends on the type of fact, current evidence, and applicable governance.

## Drift classifications

Use project-native vocabulary when available. Otherwise these documentation-facing classifications are supported:

- `DOC_DRIFT`: documentation or a documented claim conflicts with current verified implementation/evidence.
- `IMPLEMENTATION_DRIFT`: current implementation conflicts with an approved specification or requirement without a verified supersession/change record.
- `MISSING_EVIDENCE`: a claim cannot be verified with available evidence.
- `UNRESOLVED`: evidence conflicts or correction direction is not established.
- `SUPERSEDED`: an older artifact has been explicitly replaced.
- `DEPRECATED`: still present but no longer recommended/current.
- `NOT_APPLICABLE`: intentionally outside the artifact/project scope.

Do not use drift labels as authorization to modify code or policy.

## Evidence precedence by fact type

Do not use one universal source-of-truth rule. Prefer the owner for the fact being reconciled:

- implementation/source behavior: current verified source/runtime evidence;
- architecture boundaries: Clockwork-reviewed architecture evidence;
- persistence/data semantics: Chronicler-reviewed evidence;
- security/privacy controls: Cipher-reviewed evidence;
- UI/UX behavior: Cloak-reviewed source/rendered evidence as applicable;
- test/validation claims: Overseer or current validation evidence;
- legal/compliance/IP interpretation: applicable governance authority;
- business requirements/acceptance: approved requirements/governance evidence;
- formal diagrams: Weaver for notation plus the owning domain specialist for semantics;
- documentation representation and traceability: Scribe.

Recency alone is not authority.

## Reconciliation procedure

1. **Freeze comparison scope**: identify the document, system revision, environment, and claims under review.
2. **Inventory evidence**: source files, configuration, schemas, tests, runtime records, screenshots, specialist outputs, approved requirements, and historical records.
3. **Classify each claim**: observed, approved, inferred, historical, validated, unresolved, or not applicable.
4. **Trace both directions**: claim to evidence and evidence back to requirement/objective when available.
5. **Detect drift**: compare specification, implementation, validation, and documentation.
6. **Assign ownership**: route unresolved technical truth to the owning specialist rather than deciding it inside Scribe.
7. **Record disposition**: documentation correction, implementation correction, supersession, missing evidence, human decision, or no change.
8. **Re-verify after correction**: update the reconciliation record only after the changed evidence exists.

## Reconciliation matrix

| Item | Intended / Approved | Current Implementation | Validation Evidence | Documentation | Disposition | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

Suggested dispositions:

- `ALIGNED`;
- `DOC_UPDATE_REQUIRED`;
- `IMPLEMENTATION_REVIEW_REQUIRED`;
- `VALIDATION_REQUIRED`;
- `SPECIALIST_REENTRY_REQUIRED`;
- `GOVERNANCE_DECISION_REQUIRED`;
- `SUPERSEDED`;
- `NOT_APPLICABLE`.

## As-built rule

As-built documentation describes current verified implementation and limitations. It must not silently preserve planned behavior that was never implemented or validated.

If the project still needs planned/target-state documentation, keep target-state and as-built sections explicitly separate.

## Historical-intent rule

Commit history, issue history, old specifications, and prior documentation can establish historical intent but do not automatically establish current behavior.

When history and current source differ:

- record historical intent;
- record current implementation;
- identify whether a superseding decision exists;
- avoid declaring either side defective until the appropriate owner or governance record establishes the expected state.

## Quality checks

A reconciliation is complete only when:

- the compared revision/environment is identified;
- every material claim has a disposition;
- unresolved conflicts remain visible;
- downstream specialist ownership is preserved;
- no failed/skipped/not-run validation is represented as passed;
- no planned feature is represented as implemented;
- target-state and as-built state are separated where both exist;
- corrections are traced to the evidence that justified them.
