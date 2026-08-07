# Delegated Governance Implementation Plan

This document records the current multi-phase implementation state for Orchestra's delegated autonomous governance.

## Current Status

```text
Phase A: COMPLETE_MERGED
Phase B: COMPLETE_MERGED
Phase C repository contract: COMPLETE_MERGED_REPLAY_PR225
Phase C live installed-host evidence: PENDING_LOCAL_HOST_VALIDATION
Phase D overlap reconciliation: COMPLETE_MERGED_REPLAY_PR226
Phase D new runtime extension: NOT_REQUIRED
Phase E / release preparation: PENDING_R5_R6_R7
Current public release: v1.1.2
Target release: v1.2.0
```

The governing rule remains:

```text
No transition outside delegated authority.
```

## Objective

Enable Orchestra to execute approved, bounded phases autonomously without requiring a human relay for each internal unit while preserving governance, authority, capability, validation, lifecycle, audit, evidence freshness, and external-action safeguards.

Target flow:

```text
bounded authorized phase
  -> approved internal unit
  -> focused validation
  -> bounded remediation when deterministic and in scope
  -> complete revalidation after remediation
  -> checkpoint
  -> next approved unit
  -> wait on missing evidence or capacity
  -> human escalation for unresolved intent/policy/authority decisions
  -> stop on prohibited or unsafe conditions
```

## Phase A — Contract Design

**Status:** `COMPLETE_MERGED`

Canonical outcomes include:

- `docs/governance/DELEGATED_EXECUTION_POLICY.md`;
- delegated execution envelopes and approved-unit plans;
- execution evidence packets;
- transition decision records and six transition dispositions;
- remediation limits and transition precedence;
- checkpoint and capacity-handoff semantics;
- external-action authority default-deny behavior;
- fail-closed legacy-host behavior;
- governance protocol consistency validation.

## Phase B — Instruction-Level Autonomous Loop

**Status:** `COMPLETE_MERGED`

Merged through PR #190 with post-merge synchronization through PR #191.

Implemented surfaces include Conductor, Arbiter, Steward, Governor, Overseer, routing, execution modes, canonical output formats, delegated trace fixtures, and Codex export/reference parity.

Phase B does not itself prove host continuity or grant unrestricted external-action authority.

## Phase C — Host Reliability Evaluation

### Repository-verifiable contract

**Status:** `COMPLETE_MERGED_REPLAY_PR225`

Clean replay PR #225 implements deterministic repository-level validation for:

- Codex same-host reset/resume;
- Antigravity same-host reset/resume;
- Codex-to-Antigravity portable handoff;
- capacity waits;
- stale repository or runtime identity;
- incomplete checkpoints;
- scaffold-only receiving hosts;
- authority expansion attempts;
- duplicate checkpoint consumption and side-effect replay.

The replay corrected malformed SHA fixture evidence before merge and required a completely fresh all-green validation matrix after remediation.

Canonical protocol:

- `docs/validation/DELEGATED_HOST_RELIABILITY_PROTOCOL.md`
- `docs/validation/checklists/DELEGATED_HOST_RELIABILITY_CHECKLIST.md`
- `scripts/validate_delegated_host_reliability_contract.py`

### Live installed-host validation

**Status:** `PENDING_LOCAL_HOST_VALIDATION`

Repository CI does not establish actual installed-host continuity. R7 must still produce evidence for the applicable installed Codex and Antigravity reset/resume and portable-handoff scenarios, plus Claude Code packaging/compatibility without overstating runtime maturity.

This live evidence does not block R5/R6 repository preparation, but it remains a publication gate for `v1.2.0` under the clean replay.

## Phase D — Typed Runtime Enforcement Reconciliation

**Status:** `COMPLETE_MERGED_REPLAY_PR226`

The original Phase D plan predated later trusted-runtime, Tuner, Spec Kitty, status/worktree, and cross-layer implementations. Clean replay PR #226 therefore performed an overlap assessment before any new runtime model was added.

Result:

```text
PARTIALLY_SATISFIED_REQUIRES_BOUNDED_EXTENSION = 0
NEW_DUPLICATE_RUNTIME_MODELS_REQUIRED = false
```

Already satisfied by current runtime/governance:

- trusted authority and capability enforcement;
- bounded delegation;
- lifecycle control;
- runtime envelopes;
- correlation identity;
- `ApprovedUnitPlan`;
- deterministic audit/retrospective evidence;
- Tuner coordination and evidence freshness;
- status/worktree contracts;
- cross-layer integrity profiles;
- repository-level host continuity contract.

`ExecutionEvidencePacket`, `TransitionDecisionRecord`, `CheckpointRecord`, and `CapacityHandoffRecord` remain governance/evidence artifacts unless a concrete missing runtime consumer demonstrates the need for an additional typed authoritative model.

## Phase E — Release Preparation

**Status:** `PENDING`

The release sequence is now represented by replay phases:

```text
R5  cleanup + autonomous merge-readiness hardening
R6  README + changelog + version + v1.2.0 release candidate
R7  live installed-host validation
R8  tag/GitHub Release only from independently verified release state
```

`v1.2.0` must not be tagged or published while R7 remains unresolved.

## Autonomous Merge Safety

The first autonomous finalization experiment proved that platform mergeability is not sufficient governance evidence. R5 introduces `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md` and executable regressions.

Once canonical, every autonomous/delegated merge must require:

- green canonical baseline before phase start;
- exact current PR head SHA;
- all minimum required checks present;
- every required check completed and successful on that head;
- changelog freshness when significant paths changed;
- no unresolved blocker;
- immediate head re-read before merge;
- expected-head merge guard where supported;
- independent post-merge verification before state advances.

Missing or pending evidence is `WAIT_FOR_EVIDENCE`, not pass.

## Non-Goals

The following remain out of scope unless separately justified:

- weakening governance, authority, capabilities, validation, lifecycle, audit, or Dagger safeguards;
- converting repository simulation into fabricated live-host evidence;
- persistent collaboration storage, SQLite, migrations, RPC, daemons, or host-process orchestration for `v1.2.0`;
- duplicate runtime authority models without a proven consumer gap;
- production mutation or deployment without explicit release/deployment authority.

## Compatibility

Non-delegated execution paths remain compatible. Legacy or scaffold-only hosts fail closed when delegated continuation cannot be proven. Unknown or absent dispositions never default to `AUTO_CONTINUE`.

## Validation Strategy

| Phase | Required validation |
| --- | --- |
| A | governance protocol consistency, behavior, strict governance, prompt budget, exact scope |
| B | delegated behavior fixtures, adapter parity, behavior runner |
| C repository | host reliability validator, runtime regressions, governance, behavior, native Windows/Ubuntu/macOS |
| C live | installed-host reset/resume and portable-handoff evidence |
| D | overlap assessment first; runtime/adversarial tests only if a real extension is justified |
| R5 | autonomous merge-readiness regressions, governance, behavior, runtime, native Windows/Ubuntu/macOS |
| R6 | full release-readiness and version/package parity |
| R7 | installed-host parity/continuity matrix |
| R8 | independently verified release publication and post-release state |
