# Requirements Traceability Guide

## Purpose

Use this guide when Scribe must document requirements and preserve traceability between project intent, technical design, implementation, validation evidence, and documented claims.

Scribe owns the **traceability record and requirements prose**. Scribe does not independently approve business scope, make architecture decisions, design persistence, implement code, or declare validation success.

## Requirement Record

Use a stable identifier when the project benefits from explicit traceability. A practical record may include:

| Field | Purpose |
|---|---|
| ID | Stable requirement identifier |
| Statement | What is required |
| Source | Stakeholder, approved document, issue, research need, regulation, or other source |
| Rationale | Why the requirement exists |
| Priority | Optional project-specific priority |
| Acceptance criteria | Observable criteria for acceptance where applicable |
| Dependencies | Related requirements or prerequisites |
| Constraints | Technical, operational, policy, time, cost, or external constraints |
| Status | Proposed, approved, planned, implemented, validated, deprecated, superseded, unresolved, or project-specific equivalent |
| Design / model links | Verified architecture, model, or decision references |
| Implementation links | Files, modules, commits, endpoints, migrations, or other implementation evidence |
| Verification links | Tests, checks, reviews, benchmarks, evaluation records, or other validation evidence |
| Claim links | Documentation or research claims supported by the requirement and its evidence |

Delete fields that do not apply. Do not create empty ceremony for small projects.

## Lifecycle Discipline

Never infer a stronger state from a weaker one.

Do not perform these promotions without evidence:

```text
PROPOSED -> APPROVED
APPROVED -> IMPLEMENTED
PLANNED -> IMPLEMENTED
IMPLEMENTED -> VALIDATED
FAILED -> PASSED
SKIPPED -> PASSED
NOT_RUN -> PASSED
ASSUMED -> VERIFIED
```

When the available evidence cannot establish the correct state, use `MISSING_EVIDENCE` or `UNRESOLVED` rather than guessing.

## Bidirectional Traceability

Trace forward when planning or reviewing delivery:

```text
Problem / Need
  -> Objective
  -> Requirement
  -> Domain Concept / Use Case
  -> Design Decision / Model
  -> Implementation
  -> Test / Evaluation
  -> Evidence
  -> Documented Claim
```

Trace backward when auditing an implemented system or a claim:

```text
Documented Claim
  -> Evidence
  -> Test / Evaluation
  -> Implementation
  -> Design / Model
  -> Requirement
  -> Objective
  -> Problem / Need
```

Not every project requires every link. Record `NOT_APPLICABLE` where a relationship legitimately does not exist.

## Traceability Matrices

### Requirement Traceability Matrix

```markdown
| Requirement | Source | Rationale | Status | Design / Model | Implementation | Verification | Evidence | Drift / Gap |
|---|---|---|---|---|---|---|---|---|
```

### Problem-to-Objective Matrix

```markdown
| Problem / Need | Impact | Objective | Requirement IDs | Evidence / Source | Status |
|---|---|---|---|---|---|
```

### Implementation-to-Claim Matrix

```markdown
| Implementation Evidence | Requirement | Validation Evidence | Documented Claim | Claim Status | Gap |
|---|---|---|---|---|---|
```

Use the smallest matrix that answers the task.

## Drift Detection

Scribe should surface, not silently repair, these conditions:

- `ORPHANED_REQUIREMENT`: approved requirement has no planned or implemented realization and no explicit deferral.
- `UNDOCUMENTED_IMPLEMENTATION`: implementation exists without a traceable requirement, decision, or documented rationale where one is expected.
- `VALIDATION_GAP`: implementation is claimed as validated without qualifying evidence.
- `DOC_DRIFT`: documentation describes behavior, status, version, or design that no longer matches reviewed evidence.
- `IMPLEMENTATION_DRIFT`: implementation diverges from an approved requirement, design, or policy.
- `UNSUPPORTED_CLAIM`: a documented or research claim lacks sufficient evidence.
- `SUPERSEDED_REFERENCE`: a requirement, design, or evidence record points to an obsolete authority without an explicit historical purpose.

A drift finding is not automatically a defect in the implementation. The approved specification may itself be stale or superseded. Route the conflict to the owning specialist or governance layer when authority is unclear.

## Requirements Quality Review

When Scribe reviews requirement wording, check for documentation quality without taking over approval authority:

- identifiable source and rationale where useful;
- one understandable intent per requirement where practical;
- terminology consistent with the domain glossary;
- measurable or observable acceptance criteria when the requirement is verifiable;
- dependencies and constraints stated rather than hidden;
- no implementation status inflation;
- no unsupported claim that a requirement is satisfied.

The Steward remains the owner for business alignment, scope governance, and acceptance-criteria governance where that role applies.

## Specialist Handoffs

- The Steward: business alignment, scope, requirement governance, acceptance criteria governance.
- Clockwork: architectural realization and technical boundaries.
- Chronicler: persistence and data-model realization.
- Weaver: formal model and diagram realization.
- Cipher: security/privacy requirements and controls.
- Cloak: UX/UI requirements and interaction behavior.
- Overseer: test strategy, verification evidence, validation conclusions.
- Implementation specialist: code realization.

Scribe maintains the documented links after those specialists establish the underlying technical facts.

## Reference Foundation

This guide is original Orchestra guidance and does not reproduce proprietary standards text.

- ISO/IEC/IEEE 29148 is used as a reference family for requirements engineering, requirements information, and lifecycle relationships.
- NASA Systems Engineering Handbook material is used as a public primary reference for unique requirement identification, verification matrices, and traceability practices.
- NASA software-engineering guidance explicitly treats bidirectional traceability as a way to connect requirements with design, implementation, and verification and to expose missing or unoriginated functionality.
