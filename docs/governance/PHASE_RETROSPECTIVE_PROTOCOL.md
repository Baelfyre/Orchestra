# Orchestra Phase Retrospective Protocol Specification

> [!NOTE]
> **Status:** DESIGN SPECIFICATION ONLY
> **Implementation Status:** NOT IMPLEMENTED | NOT RELEASED
> **Canonical Owner:** Overseer (QA, Validation & Release Readiness Specialist)
> **Requirement Level:** `CONDITIONALLY_REQUIRED` (Triggered for delegated execution phases with >1 unit combined with remediation cycles, capacity/evidence waits, human escalations, or non-completed terminal results)
> **Replacement Effect:** `replacement_effect: none` (Does NOT replace session handoffs, post-merge records, decision logs, or evidence packets)
> **Retention Classification:** `MIXED_RETENTION_MODEL` (Sanitized retrospectives committed to repository when authorized; sensitive findings held in restricted evidence storage)

---

## 1. Purpose & Scope

The `OrchestraPhaseRetrospective` protocol defines a structured, source-backed post-phase evidence artifact captured upon completing an authorized delegated execution phase under `DELEGATED_EXECUTION_POLICY.md`.

It provides a normalized synthesis of execution outcomes, remediation cycles (`AUTO_REMEDIATE_AND_REVALIDATE`), capacity pauses (`WAIT_FOR_CAPACITY`), human escalations (`ESCALATE_HUMAN`), and validation findings across bounded delegated child runs and approved internal units.

---

## 2. Non-Goals & Invariants

### 2.1 Non-Goals
- It does **NOT** grant execution, merge, release, or deployment authority.
- It does **NOT** automatically mutate governance policy or the Pattern Catalog.
- It does **NOT** replace, rewrite, or supersede canonical records (`ExecutionEvidencePacket`, `TransitionDecisionRecord`, `ApprovedUnitPlan`, `PROJECT_STATE.md`, `DECISION_LOG.md`).
- It does **NOT** introduce new lifecycle states or Arbiter transition dispositions.

### 2.2 Core Invariants
1. **Advisory Closeout Evidence Invariant:** Retrospective findings summarize execution history for human maintainers and policy tuning. They do NOT automatically grant authority or alter project state.
2. **Replacement Effect Invariant (`replacement_effect: none`):** Existing handoff records, post-merge state files, and decision logs remain authoritative continuity references. A retrospective normalizes learning without replacing canonical records.
3. **Single Canonical Owner Invariant:** Overseer is the single canonical owner of the retrospective protocol. Downstream roles (Arbiter, Steward, Scribe) do not become co-owners.
4. **Source Provenance Invariant:** Every retrospective metric and finding MUST cite its canonical source record (`ExecutionResult`, `TransitionDecisionRecord`, `ExecutionEvidencePacket`, `ApprovedUnitPlan`).

---

## 3. Closeout Record Inventory & Gap Analysis

The protocol accounts for all existing canonical closeout and continuity records in Orchestra:

| Existing Record | Canonical Owner | Provenance Status | Primary Purpose | Retrospective Relationship |
|---|---|---|---|---|
| `DelegatedExecutionEnvelope` | Steward | `PRESENT_CANONICAL` | Delegated execution boundaries | Referenced (`execution_envelope_ref`) |
| `ApprovedUnitPlan` | Steward | `PRESENT_CANONICAL` | Planned unit definitions & scope | Referenced (`phase_id`, `unit_count`) |
| `ExecutionEvidencePacket` | Overseer | `PRESENT_CANONICAL` | Git working tree & patch digests | Cited (`evidence_fingerprint`) |
| `TransitionDecisionRecord` | Arbiter | `PRESENT_CANONICAL` | Transition dispositions | Source for remediation & escalation counts |
| `RuntimeAuditEvent` | Chronicler | `PRESENT_CANONICAL` | Event stream audit records | Source for execution timing & correlation |
| `session handoff` | Ponytail / Tuner | `PRESENT_CANONICAL` | Transient session continuity notes | Source input for synthesis (`replacement_effect: none`) |
| `post-merge state` | Tuner | `PRESENT_CANONICAL` | Post-merge repository state | Source input for synthesis (`replacement_effect: none`) |
| `validation report` | Overseer | `PRESENT_CANONICAL` | Stage 1 & 2 validation proof | Source for validation failure counts |
| `security finding` | Cipher | `PRESENT_CANONICAL` | Threat review & security findings | Source for security finding references |
| `DECISION_LOG.md` | Steward | `PRESENT_CANONICAL` | Historical decision log | Preserved intact (DO NOT UPDATE) |
| `CHANGELOG.md` | Steward | `PRESENT_CANONICAL` | Change history & release log | Preserved intact (DO NOT UPDATE) |
| `PROJECT_STATE.md` | Steward | `PRESENT_CANONICAL` | Active release & branch state | Preserved intact (DO NOT UPDATE) |

### 3.1 Verified Retrospective Gaps
1. **Gap 1 (Aggregate Remediation Metrics):** Synthesizing repeated Arbiter `AUTO_REMEDIATE_AND_REVALIDATE` cycles across multi-unit delegated execution phases (`VERIFIED_GAP`).
2. **Gap 2 (Capacity Pause & Evidence Stale Impact):** Quantifying time and cycle impact of `WAIT_FOR_CAPACITY` and `WAIT_FOR_EVIDENCE` pauses (`VERIFIED_GAP`).
3. **Gap 3 (Human Escalation Root Causes):** Capturing explicit causes and resolution paths for `ESCALATE_HUMAN` dispositions before phase closeout (`VERIFIED_GAP`).

---

## 4. Requirement Level & Deterministic Triggers

### 4.1 Requirement Level
- **`CONDITIONALLY_REQUIRED`:** A retrospective artifact is required before phase closeout when any deterministic trigger condition is met.
- **`ADVISORY`:** For simple single-unit execution phases without remediation or escalation, a retrospective remains optional and advisory.

### 4.2 Deterministic Trigger Conditions
A retrospective is triggered when a delegated phase includes >1 planned unit AND any of the following material signals occur:
1. **Remediation Cycles:** One or more Arbiter `AUTO_REMEDIATE_AND_REVALIDATE` dispositions occurred.
2. **Human Escalation:** One or more Arbiter `ESCALATE_HUMAN` dispositions occurred.
3. **Capacity / Evidence Waits:** One or more `WAIT_FOR_CAPACITY` or `WAIT_FOR_EVIDENCE` events occurred.
4. **Non-Completed Terminal Outcome:** The phase terminates in canonical state `FAILED`, `BLOCKED`, `CANCELLED`, or `TIMED_OUT`.
5. **Maintainer / Release Request:** Explicit maintainer request or release-bound phase gate requirement.

---

## 5. Creation Boundary & Terminal-State Semantics

- **Creation Boundary:** The retrospective is produced at the defined closeout boundary by the designated producer (Overseer or phase validation boundary) when trigger conditions are satisfied, prior to final maintainer closeout review.
- **Canonical Terminal States:**
  - `COMPLETED`: Produces a final retrospective upon successful completion of all planned units.
  - `FAILED`, `BLOCKED`, `CANCELLED`, `TIMED_OUT`: Produces a **partial retrospective** explicitly marking incomplete units and failed gates. Partial retrospectives MUST NOT convert a failed or blocked phase into a completed phase.
  - `WAITING`: Non-terminal state. Does NOT trigger a final retrospective (uses transient session handoffs or checkpoints).
- **Arbiter STOP Disposition:** Arbiter `STOP` is an Arbiter transition disposition, NOT a phase lifecycle state. When Arbiter emits `STOP`, the retrospective records `transition_decision_ref` and transcribes the resulting canonical phase state (`BLOCKED` or `FAILED`).

---

## 6. Retrospective Schema & Field Definitions

Total Schema Fields: **16 fields** (12 required, 4 optional).

| Field Name | Type | Required/Optional | Provenance Source | Description |
|---|---|---|---|---|
| `schema_version` | String | **Required** | Protocol Metadata | Fixed version string (`"1.0.0"`). |
| `retrospective_id` | String | **Required** | Derived Key | Phase-scoped derived key (`"retro-<phase_id>-<created_at>"`). |
| `phase_id` | String | **Required** | `ApprovedUnitPlan.phase_id` | Associated delegated phase identifier. |
| `execution_envelope_ref` | String | **Required** | `DelegatedExecutionEnvelope.id` | Reference to governing delegated execution envelope. |
| `phase_status` | String | **Required** | Canonical phase state | Canonical terminal phase status (`"COMPLETED"`, `"FAILED"`, `"BLOCKED"`, `"CANCELLED"`, `"TIMED_OUT"`). |
| `total_units_planned` | Integer | **Required** | `ApprovedUnitPlan.unit_count` | Number of planned execution units. |
| `units_accepted` | Integer | **Required** | `CoordinationContract.accepted_units` | Count of verified and accepted units. |
| `remediation_cycle_count` | Integer | **Required** | `TransitionDecisionRecord` log | Total count of `AUTO_REMEDIATE_AND_REVALIDATE` dispositions. |
| `capacity_wait_count` | Integer | **Required** | `TransitionDecisionRecord` log | Total count of `WAIT_FOR_CAPACITY` dispositions. |
| `human_escalation_count` | Integer | **Required** | `TransitionDecisionRecord` log | Total count of `ESCALATE_HUMAN` dispositions. |
| `evidence_fingerprint` | String | **Required** | `ExecutionEvidencePacket` | SHA-256 digest of final working tree evidence packet. |
| `created_at` | String | **Required** | Retrospective Metadata | ISO-8601 UTC creation timestamp string. |
| `correlation_id` | String | Optional | `RuntimeAuditEvent.correlation_id` | Associated RFC 9562 UUIDv7 correlation string (if present). |
| `outcome_summary` | String | Optional | Overseer synthesis | Neutral human-readable summary of phase accomplishments or blockers. |
| `known_limitations` | Array | Optional | Overseer synthesis | Documented technical debt or unresolved non-blocking items. |
| `follow_up_candidates` | Array | Optional | Overseer recommendations | Proposed future task candidates requiring separate human authorization. |

---

## 7. Recovery & Completeness Behavior

- **Retrospective Completeness Metadata:** If required evidence records are unreadable or missing, the retrospective sets `completeness: PARTIAL` and `reason_code: INCOMPLETE_EVIDENCE`. This metadata does NOT alter the canonical phase lifecycle state.
- **Evidence Recovery:**
  - `WAIT_FOR_EVIDENCE`: Used when missing evidence can be recovered deterministically within the authorized execution phase.
  - `ESCALATE_HUMAN`: Used when evidence is unrecoverable, an exception is requested, or policy is ambiguous.
- **Emergency Recovery:** Emergency maintainer interventions may defer retrospective creation, but a follow-up task MUST be recorded to complete retrospective evidence post-recovery.

---

## 8. Security, Privacy, and Retention

- **Retention Model:** `MIXED_RETENTION_MODEL`.
  - Sanitized, non-sensitive retrospectives may be committed to repository storage when explicitly authorized.
  - Security-sensitive, proprietary, client, or secret details MUST NOT be written to public Git history. Restricted findings are referenced via secure IDs rather than embedded.
- **Secrets & Credentials:** Raw API keys, tokens, passwords, and private keys MUST be redacted before retrospective synthesis.
- **Path Sanitization:** File references MUST use repository-relative paths.
