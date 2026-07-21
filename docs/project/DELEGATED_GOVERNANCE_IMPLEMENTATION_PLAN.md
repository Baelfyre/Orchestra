# Delegated Governance Implementation Plan

This document records the multi-phase implementation plan for Orchestra's
delegated autonomous governance. Only Phase A is authorized in the current
implementation batch.

---

## Overview

The goal is to enable Orchestra to execute approved, bounded phases of work
autonomously, without requiring a human approval relay for each internal unit,
while preserving all governance, authority, capability, validation, lifecycle,
audit, and Dagger safeguards.

Target behavior:

```
Human approves one bounded phase envelope
  ->  Orchestra executes approved internal units
  ->  Focused validation runs after each unit
  ->  Ordinary in-scope defects are corrected and revalidated automatically
  ->  Accepted units are checkpointed
  ->  The next approved unit begins automatically
  ->  Missing evidence or capacity creates a resumable waiting state
  ->  Genuine intent, scope, policy, authority, safety, or external-action
      decisions escalate to a human
  ->  Prohibited or unsafe work stops
```

Governing rule:

```
No transition outside delegated authority.
```

---

## Phase A - Contract Design (Current Batch)

**Authorization:** Local contract-design implementation. No commit, push, pull
request, merge, tag, release, deployment, or production action authorized.

**Status:** Implemented locally on branch
`docs/delegated-autonomous-governance-phase-a`.

**Scope:**

- `docs/governance/DELEGATED_EXECUTION_POLICY.md` (new) - canonical delegated
  execution policy: envelopes, unit plans, evidence packets, transition decision
  records, transition precedence, automatic remediation, focused and phase
  validation, baseline lineage, checkpointing, capacity waiting, external-action
  authority, legacy fallback, and phase state machine.
- `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md` (modified) - additive
  reference section listing the six transition dispositions, the
  decision-versus-disposition separation, automatic progression requirements,
  and the fail-closed rule. Full contract delegated to policy document.
- `docs/governance/GOVERNANCE_LAYER.md` (modified) - phase-level delegated
  governance section, governance specialist re-entry triggers, canonical policy
  reference, phase implementation status table, and corrected enforcement
  limitation that distinguishes route-level from phase-level enforcement.
- `docs/governance/GOVERNANCE_REVIEW_FLOW.md` (modified) - target delegated
  execution flow section, clearly labeled as Phase B target, not yet active.
- `scripts/validate_governance_protocol_consistency.py` (modified) - additive
  checks for the new delegated execution contracts.
- `tests/behavior/test_governance_protocol_consistency.py` (modified) - new
  positive and negative test cases for the delegated execution contracts.
- `docs/project/DELEGATED_GOVERNANCE_IMPLEMENTATION_PLAN.md` (new) - this file.
- `CHANGELOG.md`, `DECISION_LOG.md`, `PROJECT_STATE.md`, `SESSION_HANDOFF.md`
  (modified) - state file synchronization.

**Non-goals of Phase A:**

- Instruction-level autonomous loop behavior in role skills or adapters.
- Phase B, C, D, or E work.
- Runtime enforcement or typed runtime models.
- Any commit, push, pull request, merge, release, deployment, or
  infrastructure action.

---

## Phase B - Instruction-Level Autonomous Loop (Implemented & Locally Validated)

**Status:** Phase B instruction-level behavior implemented and locally validated; remote and host reliability remain pending until separately authorized.


**Planned scope:**

Update the following files to consume delegated phase dispositions, produce
structured evidence packets, and loop autonomously within an authorized envelope:

```
skills/conductor/SKILL.md
skills/arbiter/SKILL.md
skills/arbiter/OUTPUT_FORMATS.md
skills/the-steward/SKILL.md
skills/the-steward/OUTPUT_FORMATS.md
skills/the-governor/SKILL.md
skills/the-governor/OUTPUT_FORMATS.md
skills/overseer/SKILL.md (where necessary)
docs/routing/EXECUTION_MODES_POLICY.md
ROUTING_MAP.md
SKILL_INDEX.md
AGENTS.md
behavior fixtures affected by canonical contracts
adapter parity validation
```

**Dependencies:**

- Phase A contracts accepted and merged.
- Separate human authorization for Phase B scope.

---

## Phase C - Host Reliability Evaluation (Not Yet Authorized)

**Status:** Not started. Requires Phase B completion and separate authorization.

**Planned scope:**

Validate whether supported hosts (Antigravity, Claude Code, Codex, etc.)
reliably:

- Preserve the execution envelope across context boundaries.
- Transfer evidence packets automatically.
- Consume Arbiter dispositions correctly.
- Loop safely without dropped state.
- Checkpoint and resume from a valid capacity handoff.
- Avoid repeated owner relay that requires human re-approval.

---

## Phase D - Optional Typed Runtime Enforcement (Not Yet Authorized)

**Status:** Not started. Requires Phase B and C evaluation and separate
authorization.

**Planned scope (conditional on authorization):**

Add typed runtime models for:

```
DelegatedExecutionEnvelope
ApprovedUnitPlan
ExecutionEvidencePacket
TransitionDecisionRecord
AuditEvent
LifecycleIntegration
AdversarialEnforcementTests
```

This phase is optional. Phase A contracts and Phase B instruction-level behavior
may be sufficient without runtime enforcement.

---

## Phase E - Release Preparation (Not Yet Authorized)

**Status:** Not started. Requires Phase A-D decisions and separate authorization.

**Scope:**

Commit, push, pull request, merge, tag, GitHub Release, marketplace publication,
and deployment remain separately governed and are not authorized in Phases A-D.

---

## Non-Goals

The following are explicitly out of scope for all phases:

- Weakening governance, authority, capabilities, validation, lifecycle, audit,
  or Dagger safeguards.
- Enabling automatic commits, pushes, or production mutations without explicit
  per-action standing authority.
- Creating competing governance definitions outside the canonical documents.
- Runtime enforcement before Phase D authorization.

---

## Migration and Backward Compatibility

Phase A and B changes must be backward compatible. Legacy hosts that do not
implement delegated phase behavior continue to use the existing manual pause
path. Unknown or absent dispositions fail closed and never default to automatic
continuation.

Phase D typed runtime models, if authorized, must not change the behavior of
existing non-delegated execution paths.

---

## Validation Strategy

| Phase | Validation Gate |
|---|---|
| Phase A | Governance protocol consistency validator; behavior test suite; strict governance; prompt-load budget; exact-scope audit |
| Phase B | Instruction-level behavior fixtures; adapter parity; behavior runner |
| Phase C | Host-specific reliability evaluation protocol (defined in Phase C planning) |
| Phase D | Typed runtime tests; adversarial enforcement tests; runtime coverage gate |
| Phase E | Full release readiness gate per `RELEASE_GATES.md` and `APP_RELEASE_COMPLIANCE_GATE.md` |

---

## Authorization Boundaries

| Action | Authorized in Phase A | Authorization Required |
|---|---|---|
| Create/modify docs/governance/DELEGATED_EXECUTION_POLICY.md | Yes | Phase A approval |
| Modify GOVERNANCE_DECISION_PROTOCOL.md | Yes (additive only) | Phase A approval |
| Modify GOVERNANCE_LAYER.md | Yes (additive only) | Phase A approval |
| Modify GOVERNANCE_REVIEW_FLOW.md | Yes (additive only) | Phase A approval |
| Modify validator scripts and behavior tests | Yes (additive only) | Phase A approval |
| Modify state files (CHANGELOG, DECISION_LOG, PROJECT_STATE, SESSION_HANDOFF) | Yes | Phase A approval |
| Modify role skills (conductor, arbiter, etc.) | No | Phase B authorization |
| Modify routing or adapter files | No | Phase B authorization |
| Typed runtime models | No | Phase D authorization |
| Commit, push, pull request, merge, release | No | Phase E authorization |
