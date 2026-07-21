# Governance Decision Protocol

This document is canonical shared governance decision contract for Orchestra.
Load it only when governance decision must be produced, interpreted, or enforced.
Do not load it for ordinary route classification.

## Shared Decision Model

Canonical values and shared meanings:

- `APPROVED`: Required governance review passed; work may proceed to the next governed stage subject to any stated constraints.
- `ADVISORY_ONLY`: Non-blocking guidance was provided; exploration may continue without satisfying required actions first.
- `REVISION_REQUIRED`: Identified changes or missing evidence must be addressed before the governed transition may proceed.
- `BLOCKED`: Work cannot proceed through the governed transition until the blocking condition is resolved and reviewed again.
- `NOT_APPLICABLE`: This governance review does not apply to the request and creates no additional gate.

These values define generic pipeline meaning only.
Specialists may add role-specific nuance without redefining shared meanings.

## Shared Compact Output Contract

Canonical compact fields:

- `REVIEWER`
- `PROJECT_CONTEXT`
- `DECISION`
- `REASON`
- `RISKS`
- `REQUIRED_ACTIONS`

Specialists may add role-specific fields in their own output formats.

## Shared Gate Contract

- Conductor stops on `BLOCKED`.
- Conductor pauses on `REVISION_REQUIRED`.
- Conductor pauses on `human_review_required: true`.
- Conductor pauses on Arbiter `HOLD` or `BLOCKED`.
- Execution specialists cannot bypass governance.
- Governance authorities produce decisions and constraints, not implementation.

## Canonical Separation of Concerns

| Specialist | Governance Decision Ownership | Technical Review Ownership | Execution Ownership | Routing Ownership | Validation Ownership | Continuity Ownership |
| --- | --- | --- | --- | --- | --- | --- |
| `the-steward` | Business alignment, scope, requirements, acceptance criteria, SDLC sufficiency | None | None | None | None | None |
| `the-governor` | Legal, regulatory, licensing, privacy-obligation, IP, compliance governance | None | None | None | None | None |
| `arbiter` | Continuation and transition governance | Validation-state interpretation | None | None | Merge, handoff, source-of-truth evidence gating | Handoff, branch, merge, source-of-truth, unresolved validation |
| `conductor` | None | None | None | Route and sequence selection only | None | Pause routing when Arbiter gate unresolved |
| `cipher` | None | Technical security, privacy-control, authorization, secrets, threat review | None | None | Security evidence inputs only | None |
| `overseer` | None | QA strategy, validation planning, test evidence review | None | None | Test execution planning and validation evidence | None |
| `clockwork` | None | Architecture, layering, service boundaries, refactor structure | None | None | Architecture evidence inputs only | None |
| `chronicler` | None | Database and persistence semantics, schema, migrations, ORM behavior | None | None | Persistence evidence inputs only | None |
| `cloak` | None | UI/UX, accessibility, responsive layout, interaction design | None | None | UX evidence inputs only | None |
| `scribe` | None | Documentation quality only when asked | Documentation production and editing | None | Documentation evidence inputs only | None |
| `ponytail` | None | None | Implementation only after design and governance are ready | None | Local implementation validation only | None |
| `dagger` | None | Controlled destructive-path and resilience review | Guarded destructive simulation only | None | Guardrail evidence only | None |
| `weaver` | None | Diagram and visual-model notation | Diagram production | None | Diagram evidence inputs only | None |
| Other execution specialists | None | Domain-specific technical review inside their scope | Domain execution inside their scope | None | Domain evidence inputs only | None |

Clarifications:

- Governor owns legal, regulatory, licensing, privacy-obligation, and IP governance.
- Cipher owns technical security and privacy-control analysis.
- Steward owns business alignment, scope, requirements, acceptance criteria, and required SDLC artifact sufficiency.
- Scribe produces and edits documentation but does not decide business alignment.
- Arbiter owns continuity, source-of-truth, branch, handoff, and merge-readiness decisions.
- Overseer owns QA strategy, test execution planning, and validation evidence.
- Clockwork owns architecture and layering.
- Chronicler owns database and persistence semantics.
- Ponytail owns implementation only after design and governance are ready.
- Conductor owns routing and sequencing only.

## Delegated Execution Transition Dispositions

`docs/governance/DELEGATED_EXECUTION_POLICY.md` is the canonical contract for envelopes, dispositions, evidence, remediation, checkpointing, capacity, authority, invalidation, and fallback.

### Decision Versus Disposition Separation

Governance decision asks if work is acceptable; transition disposition asks what workflow does next.

```
Governance decision:
  Is the work acceptable under the applicable governance review?

Transition disposition:
  What may the workflow do next under the active envelope?
```

An `APPROVED` governance decision does not authorize automatic continuation without valid evidence and boundary checks.

### Transition Disposition Values

Additive values defined in `DELEGATED_EXECUTION_POLICY.md`:

- `AUTO_CONTINUE` - Unit accepted; next approved unit begins.
- `AUTO_REMEDIATE_AND_REVALIDATE` - Deterministic in-scope defect corrected and revalidated.
- `WAIT_FOR_EVIDENCE` - Required evidence missing or stale; execution pauses until produced.
- `WAIT_FOR_CAPACITY` - Host capacity limit reached; resumable checkpoint produced.
- `ESCALATE_HUMAN` - Requires human intent, policy, authority, or compliance resolution.
- `STOP` - Unsafe, prohibited, or authority-invalid condition; execution halts.

### Automatic Progression Requirements

Requires valid envelope, current evidence, no stop/escalation condition, and no scope expansion. Prompt text and adapter metadata cannot create or expand an envelope.

### Fail-Closed Rule

Unknown, malformed, missing, or unsupported transition dispositions must fail closed and produce `ESCALATE_HUMAN`. Never default to automatic continuation.
