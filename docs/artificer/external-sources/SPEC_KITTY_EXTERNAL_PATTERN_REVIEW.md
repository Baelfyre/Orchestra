# Spec Kitty External Pattern Review for Orchestra

## Document Metadata

- **Reviewer Role:** The Artificer
- **Target Repository:** `C:\conductor` (https://github.com/Baelfyre/Orchestra)
- **External Pattern Source:** `https://github.com/Priivacy-ai/spec-kitty`
- **External Source Commit SHA:** `8466727ebbbc01fcaf43575657c9b1b9553784d9` (Timestamp: 2026-08-02T07:50:53Z, Release: 3.2.6)
- **Operating Mode:** `READ_ONLY_BASELINE_RECONCILIATION`
- **Review Timestamp:** 2026-08-03T07:56:30+08:00
- **Status:** Candidate Phase 0 Rerun Complete (No runtime code modified, baseline clean)

---

## 1. Orchestra Baseline

- **Repository:** `C:\conductor`
- **Canonical Branch:** `design/spec-kitty-derived-contracts`
- **Local HEAD:** `317c9449b2c6d264d0e826f229808439f1549ceb`
- **Remote `origin/main`:** `317c9449b2c6d264d0e826f229808439f1549ceb`
- **Current Public Release:** `v1.1.2` (Published July 14, 2026)
- **Unreleased Main Runtime Status:** Contains merged PRs #190, #191, #197, #198, #200, #201, #206, #207 (Delegated Phase B post-merge sync, The Tuner Phases 1-4, Issue #204 Codex Tuner portable export).
- **Canonical Documents Reviewed:**
  - `README.md` & `AGENTS.md`
  - `PROJECT_STATE.md` & `PROJECT_CONTEXT.md`
  - `docs/governance/DELEGATED_EXECUTION_POLICY.md`
  - `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md`
  - `docs/governance/GOVERNANCE_REVIEW_FLOW.md`
  - `docs/governance/EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md`
  - `docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md`
  - `docs/routing/EXECUTION_MODES_POLICY.md`
  - `docs/routing/TUNER_PHASE_4_POST_MERGE_STATE.md`
  - `docs/project/AUTHORITY_CAPABILITY_CONTRACTS.md`
  - `docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md`
  - `docs/project/PORTABLE_ADAPTER_PROTOCOL.md`
  - `docs/project/ROADMAP.md`

---

## 2. External Repository Baseline (Spec Kitty)

- **Repository:** `https://github.com/Priivacy-ai/spec-kitty`
- **Default Branch:** `main`
- **Exact Commit SHA:** `8466727ebbbc01fcaf43575657c9b1b9553784d9`
- **Current Package Release Version:** `3.2.6` (Package `spec-kitty-cli` on PyPI)
- **License:** `MIT License`
- **Development Status:** `4 - Beta`
- **Primary Language:** `Python 3.11+`
- **Core Runtime Boundaries:** `src/kernel`, `src/glossary`, `src/mission_runtime`, `src/runtime`, `src/specify_cli`, `src/doctrine`, `src/charter`
- **Public Extension Boundaries:** `packs/built-in`, PyPI dependencies `spec-kitty-events >= 6.0.0`, `spec-kitty-tracker >= 0.4`
- **Governance Model:** Terminology Canon and Doctrine packs (`packs/built-in`, `.kittify/config.yaml`, mission charters)
- **Workflow State Model:** `spec -> plan -> tasks -> next -> review -> accept -> merge` with WP lane transitions (`planned`, `in_progress`, `for_review`, `approved`, `done`)
- **Worktree Model:** `.worktrees/<wp_id>` isolated per work package
- **Audit Model:** Local JSONL event trail (`spec-kitty-events`), ULID correlation identifiers

---

## 3. Reassessed Assessment Areas against Current `main`

### 3.1 Work Package Model
Spec Kitty uses explicit work packages (`kitty-specs/<mission>/work-packages/`) with defined lifecycle lanes, explicit dependency trees, per-unit status records, and acceptance criteria.
- **Orchestra Baseline on `main`:** `orchestra_runtime/coordination.py` manages `CoordinationContract` and `UnitExecutionState`. `DELEGATED_EXECUTION_POLICY.md` defines `ApprovedUnitPlan`.
- **Reassessed Adaptation:** `PROMOTE_AS_EXTENSION` – Extend `ApprovedUnitPlan` / `CoordinationContract` unit references directly rather than creating a separate standalone unit state file.

### 3.2 Per-Unit Git Worktree Isolation
Spec Kitty enforces git worktree isolation (`.worktrees/<wp_id>`) per work package to prevent branch pollution.
- **Orchestra Assessment:** Worktree isolation is an optional host/adapter execution mechanism. Mandating worktree creation in core Orchestra would break lightweight executions and local single-agent workflows.
- **Proposed Adaptation:** Declare `OrchestraWorktreeContract` as a host/adapter-level capability (`HOST_CAPABILITY_DEPENDENT` / `OPTIONAL`).

### 3.3 External Orchestrator Boundary
Spec Kitty maintains a clear boundary between host CLI commands and external tracker/event services via versioned Python module contracts.
- **Orchestra Gap:** Orchestra has `PORTABLE_ADAPTER_PROTOCOL.md` and adapter layers, but lacks a formal machine-facing execution provider interface separating workflow state host from routing/governance provider logic.
- **Proposed Adaptation:** Define `OrchestraProviderContract` as a formal machine interface for host adapters.

### 3.4 Machine-Readable Response Envelopes
Spec Kitty uses deterministic JSON response envelopes (`contract_version`, `command`, `timestamp`, `correlation_id`, `success`, `error_code`, `data`).
- **Orchestra Gap:** Orchestra relies primarily on markdown text blocks (`TransitionDecisionRecord`, packet outputs) for specialist communication and Arbiter decisions. Markdown parsing across diverse LLM hosts can introduce non-deterministic errors.
- **Proposed Adaptation:** Implement an optional machine-readable JSON schema (`OrchestraRuntimeEnvelope`) for specialist execution outputs and transition decisions.

### 3.5 Workflow Transition API
Spec Kitty provides explicit transition commands (`specify`, `plan`, `tasks`, `next`, `review`, `accept`, `merge`).
- **Orchestra Analysis:** Orchestra's lifecycle relies on governance signals (`PHASE_READY_FOR_HUMAN_REVIEW`) and Arbiter dispositions (`AUTO_CONTINUE`, `AUTO_REMEDIATE_AND_REVALIDATE`, `WAIT_FOR_EVIDENCE`, `WAIT_FOR_CAPACITY`, `ESCALATE_HUMAN`, `STOP`). Collapsing these into Spec Kitty's workflow state machine is REJECTED because Orchestra's governance signals represent continuity & safety gates, not simple task lanes.

### 3.6 Invocation and Evidence Trails
Spec Kitty logs machine-local events into JSONL files using ULID correlation IDs and explicit links to artifacts and commits.
- **Orchestra Baseline on `main`:** `scripts/evidence_identity.py` provides `working_tree_fingerprint` & `collaboration_session_id`. `orchestra_runtime/coordination.py` tracks session event logs.
- **Reassessed Adaptation:** Rescope `OrchestraCorrelationID` to merge as an optional ULID header on `RuntimeAuditEvent` and `ExecutionEvidencePacket` (`PROCEED_WITH_RESCOPING`).

### 3.7 Versioned Doctrine / Governance Packs
Spec Kitty packages governance rules as portable doctrine packs (`packs/built-in`).
- **Orchestra Conflict:** Duplicating Orchestra's canonical policy files into portable doctrine packs creates dual sources of truth. Canonical policy MUST remain in `docs/governance/` and `skills/`.
- **Proposed Adaptation:** REJECT standalone manual doctrine packs. Allow generated adapter rule bundles *only* when derived dynamically from canonical markdown during export scripts (e.g. `adapters/codex/export-codex-skills.ps1`).

### 3.8 Retrospective Learning
Spec Kitty requires a mandatory retrospective (`retrospective.md`) upon mission completion to record successes, failures, repeated remediations, capacity interruptions, and governance conflicts.
- **Orchestra Gap:** Orchestra uses informal closeout notes, but lacks a structured, required post-phase retrospective schema for delegated phase execution.
- **Proposed Adaptation:** Implement `OrchestraPhaseRetrospective` as an advisory post-phase evidence artifact required before final phase closeout.

---

## 4. Summary of Adaptations & Non-Goals

- **Promoted for Design (Rescoped):**
  1. `OrchestraUnitRecord` (Extension of `ApprovedUnitPlan` & `CoordinationContract`)
  2. `OrchestraRuntimeEnvelope` (Structured JSON machine envelope)
  3. `OrchestraCorrelationID` (Rescoped ULID correlation header for `RuntimeAuditEvent` & `ExecutionEvidencePacket`)
  4. `OrchestraPhaseRetrospective` (Structured post-phase retrospective evidence)
- **Deferred / Optional:**
  1. `OrchestraWorktreeContract` (Host-dependent worktree isolation)
  2. `OrchestraStatusProjection` (Read-only status CLI script)
- **Rejected Patterns:**
  1. External workflow state as authority (violates Orchestra governance invariants)
  2. Manual standalone doctrine packs (violates single source of truth invariant)
  3. Merging governance signals with task lanes (violates Arbiter authority model)
