# Maintainer Decision Brief: Spec Kitty Pattern Review (Phase 0 Rerun)

## Executive Summary
This brief summarizes the Candidate Phase 0 rerun findings of **The Artificer** pattern review of `Priivacy-ai/spec-kitty` (commit `8466727ebbbc01fcaf43575657c9b1b9553784d9`, v3.2.6) against Orchestra's clean canonical baseline (`317c9449b2c6d264d0e826f229808439f1549ceb`).

The review evaluated Spec Kitty's spec-driven development, work package model, git worktree isolation, event correlation, and retrospective learning against Orchestra's governance model, delegated execution policy, The Tuner coordination runtime, and evidence identity protocols.

---

## 1. Recommended Concepts for Design Promotion (Rescoped)

1. **`OrchestraRuntimeEnvelope` (Machine-Readable Response Envelopes)**
   - *Scope:* Standardized JSON output envelope for specialist packets and Arbiter transition decisions.
   - *Value:* Eliminates non-deterministic markdown parsing errors across LLM adapters.
   - *Recommendation:* `PROCEED_WITH_RESCOPING`

2. **`OrchestraCorrelationID` (Cross-Run Audit Trail Correlation)**
   - *Scope:* Monotonically sortable ULID header added to `RuntimeAuditEvent` and `ExecutionEvidencePacket`.
   - *Value:* Enables end-to-end trace correlation across subagent sessions without external dependencies.
   - *Recommendation:* `PROCEED_WITH_RESCOPING`

3. **`OrchestraPhaseRetrospective` (Structured Post-Phase Retrospective Protocol)**
   - *Scope:* Mandatory retrospective evidence artifact required before final phase closeout under `DELEGATED_EXECUTION_POLICY.md`.
   - *Value:* Captures systemic failure patterns, capacity waits, and human escalations for governance tuning.
   - *Recommendation:* `PROCEED_WITH_RESCOPING`

4. **`OrchestraUnitRecord` (Work Package Model Adaptation)**
   - *Scope:* Machine-readable unit record extension extending `ApprovedUnitPlan` & `CoordinationContract`.
   - *Value:* Improves multi-turn unit tracking without creating duplicate state files.
   - *Recommendation:* `PROMOTE_AS_EXTENSION`

---

## 2. Deferred / Optional Concepts

1. **`OrchestraWorktreeContract` (Unit Worktree Isolation)**
   - *Recommendation:* `ADAPT_LATER` (Host-dependent capability; optional for multi-agent adapters).
2. **`OrchestraStatusProjection` (Read-Only Status Script)**
   - *Recommendation:* `ADAPT_LATER` (Read-only status summary CLI tool; non-blocking).

---

## 3. Rejected Concepts

1. **External Workflow State as Merge Authority** (`REJECT_CONFLICT`)
   - *Reason:* In Orchestra, workflow state transition is NOT authority. Merging/releasing requires explicit human authorization or approved delegated execution envelopes.
2. **Standalone Manual Doctrine Packs** (`REJECT_DUPLICATE`)
   - *Reason:* Duplicating canonical policy markdown into separate doctrine packs creates dual sources of truth and policy drift. Canonical policy MUST remain in `docs/governance/` and `skills/`.
3. **Collapsing Governance Signals into Task Lanes** (`REJECT_CONFLICT`)
   - *Reason:* Orchestra governance signals (`PHASE_READY_FOR_HUMAN_REVIEW`, Arbiter dispositions) represent safety gates, not simple task lanes.

---

## 4. Key Preflight & Baseline Verification Facts

- **Local Branch:** `design/spec-kitty-derived-contracts`
- **Current HEAD:** `317c9449b2c6d264d0e826f229808439f1549ceb` (Aligned with `origin/main`)
- **Preflight Check:** `PROCEED` (Clean working tree)
- **Stash Resolution:** `stash@{0}` contains Issue #204 work that is `ALREADY_CANONICAL` on `main` via PR #207 (commit `6a6d172`). No stashed material needs to be restored.
- **Spec Kitty Source Commit:** Pinned to exact SHA `8466727ebbbc01fcaf43575657c9b1b9553784d9`.

---

## 5. Required Specialist Assignments for Next Phase

- **Clockwork:** Design `OrchestraRuntimeEnvelope` JSON schema and provider boundary.
- **Steward:** Align `OrchestraUnitRecord` with `DELEGATED_EXECUTION_POLICY.md`.
- **Overseer:** Define `OrchestraPhaseRetrospective` schema and evidence validation gates.
- **Chronicler:** Define `OrchestraCorrelationID` persistence and log format.

---

## 6. Implementation Authorization Request

> [!IMPORTANT]
> **No code implementation is authorized or performed during Phase 0.**
> Maintainers are requested to authorize Phase 1A (Architecture Ownership and Contract Placement) for the 4 promoted concepts.
