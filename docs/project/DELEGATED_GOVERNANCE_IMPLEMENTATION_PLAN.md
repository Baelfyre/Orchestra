# Delegated Governance Implementation Plan

This document records the multi-phase implementation plan for Orchestra's
delegated autonomous governance. Phase A contracts are canonical. Phase B
instruction-level behavior is complete, merged and canonical through PR #190 on `main`.
Phase A contracts are merged. Phase B is merged and canonical through PR #190. Phase C repository contract is complete through PR #225. Accepted R7 evidence is `VERIFIED / RECONCILED LOCALLY`; the repository simulation remains `PENDING_LOCAL_HOST_VALIDATION` with empty live records by design. Phase D overlap reconciliation is complete through PR #226. No additional Phase D runtime implementation is justified for v1.2.0. `v1.2.0 has not been released or deployed` was the pre-R8 state; `v1.2.0` is now published, with deployment and policy activation unperformed.

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

## Phase B - Instruction-Level Autonomous Loop (Complete, Merged via PR #190)

**Status:** Phase B instruction-level behavior is complete and merged into `main` through PR #190 at merge commit `d37a2f7b31543efacf7a5e81c3f4d08c12da017d`. Remote and host reliability remain pending until separately authorized.


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

## Phase C - Host Reliability Evaluation

**Repository contract status:** Complete and merged through PR #225.

**Live installed-host status:** `VERIFIED_RECONCILED_LOCALLY` in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`. Repository CI and the simulation fixture remain repository evidence only; Claude Code active runtime continuity is not claimed because its maturity remains `SCAFFOLD_ONLY`.

**Evaluated scope:**

Validate whether supported hosts (Antigravity, Claude Code, Codex, etc.)
reliably:

- Preserve the execution envelope across context boundaries.
- Transfer evidence packets automatically.
- Consume Arbiter dispositions correctly.
- Loop safely without dropped state.
- Checkpoint and resume from a valid capacity handoff.
- Avoid repeated owner relay that requires human re-approval.

---

## Phase D - Runtime Overlap Reconciliation

**Status:** Complete and merged through PR #226.

**Verdict:** `NO_DUPLICATE_RUNTIME_EXTENSION_REQUIRED` for v1.2.0.

The reconciliation in `docs/project/DELEGATED_PHASE_D_RUNTIME_OVERLAP_ASSESSMENT.md` found that existing trusted authority, capability, delegation, lifecycle, runtime-envelope, `ApprovedUnitPlan`, audit, Tuner coordination, status/worktree, and cross-layer contracts already satisfy the material runtime requirements.

`ExecutionEvidencePacket`, `TransitionDecisionRecord`, `CheckpointRecord`, and `CapacityHandoffRecord` remain governance/evidence artifacts unless a concrete missing runtime consumer is established.

Additional Phase D runtime implementation for v1.2.0 is **not required**.

---

## Phase E - Release Preparation

**Status:** R6-R8 and GA-0 through GA-7 are complete. Tag and GitHub Release `v1.2.0` are `PUBLISHED_VERIFIED` at `4f3c45f6d1e5f290aca108ddf5810c1b18f1dc76`.

**Clean replay continuation:**

```text
R5   autonomous merge-readiness hardening â€” merged through PR #227
R5B  delegated governance state reconciliation â€” current bounded remediation
R6   release-candidate repository preparation
R7   live installed-host validation and reconciliation - MERGED_VERIFIED
GA-0..GA-7  governed autonomy profiles - MERGED_VERIFIED; release evidence refreshed
R8   annotated tag and GitHub Release - PUBLISHED_VERIFIED
```

Commit, push, pull request, merge, tag, GitHub Release, marketplace publication,
and deployment remain separately governed. R5B does not authorize release or publication.

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
