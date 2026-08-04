# Orchestra Runtime Envelope Specification

> [!NOTE]
> **Status:** DESIGN SPECIFICATION ONLY
> **Implementation Status:** NOT IMPLEMENTED | NOT RELEASED
> **Canonical Owner:** Clockwork (Engineering & Code Structure Specialist)
> **Target Schema Version:** `1.0.0`

---

## 1. Purpose & Scope

The `OrchestraRuntimeEnvelope` is a derived, deterministic, machine-readable JSON serialization profile designed for LLM adapters (Codex, Claude Code, Antigravity/Gemini), automated test drivers, and external host orchestrators.

It provides a non-ambiguous machine representation of specialist execution outputs, Arbiter transition decisions, and audit events without requiring consumers to parse human-readable Markdown prose.

---

## 2. Non-Goals & Core Invariants

### 2.1 Non-Goals
- It is **NOT** a new runtime execution engine or state machine.
- It does **NOT** grant execution, merge, release, or deployment authority.
- It does **NOT** replace human-readable Markdown summaries.
- It does **NOT** introduce new lifecycle states or Arbiter transition dispositions.

### 2.2 Core Invariants
1. **Non-Authorizing Projection Invariant:** Envelope presence or `status: COMPLETED` does NOT grant capability or override governance envelopes.
2. **Canonical-Record Precedence Invariant:** Canonical runtime models (`ExecutionResult`, `TransitionDecisionRecord`, `RuntimeAuditEvent`) remain authoritative. If an envelope conflicts with canonical records, the envelope is invalid.
3. **No Prose Parsing Invariant:** Machine consumers MUST rely exclusively on structured machine fields (`message_type`, `status`, `reason_code`, `disposition`). Machine logic MUST NOT parse text in `summary`.
4. **Standalone Machine Representation Invariant:** The canonical machine representation of an envelope is a standalone UTF-8 JSON object. Markdown text is an optional human-readable presentation layer that may include a non-authoritative rendered copy. Machine consumers MUST use the standalone JSON payload directly rather than scraping Markdown text or fenced blocks.
5. **Additive Compatibility Invariant:** Consumers MUST ignore unrecognized optional fields for forward additive compatibility.
6. **Redaction & Minimization Invariant:** Envelopes MUST NOT embed secrets, credentials, prompt text, or raw client data.

---

## 3. Canonical Transport & Presentation Protocol

### 3.1 Canonical Machine Transport
The canonical machine representation of an `OrchestraRuntimeEnvelope` is a standalone UTF-8 JSON payload transmitted over structured RPC, file, or API channels.

### 3.2 Optional Human-Readable Presentation
Markdown text emitted during CLI or chat sessions may optionally embed a non-authoritative, rendered copy of the envelope inside a Markdown fenced code block (e.g. using tag `json:orchestra-envelope`) for human inspection or logging display. This presentation copy is purely informational; machine consumers MUST NOT rely on scraping Markdown text or fenced code blocks for machine decisions.

---

## 4. Message-Type Discriminated Union

The envelope supports three discriminated `message_type` variants:

### 4.1 Variant: `execution_result`
- **Purpose:** Emitted by specialists upon completing an assigned execution operation.
- **Canonical Source:** `ExecutionResult` in `orchestra_runtime/models.py`.
- **Required Fields:** `schema_version`, `message_type`, `timestamp`, `run_id`, `specialist`, `operation`, `status`, `reason_code`.
- **Optional Fields:** `parent_run_id`, `authority_decision_ref`, `capability_decision_ref`, `governance_decision_ref`, `evidence_fingerprint`, `correlation_id`, `summary`, `data`.
- **Prohibited Fields:** `disposition`, `event_type`, `collaboration_session_id`.

### 4.2 Variant: `transition_decision`
- **Purpose:** Emitted by Arbiter or Conductor when evaluating a phase or unit transition.
- **Canonical Source:** `TransitionDecisionRecord` in `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md` & `orchestra_runtime/coordination.py`.
- **Required Fields:** `schema_version`, `message_type`, `timestamp`, `run_id`, `specialist`, `operation`, `disposition`, `reason_code`.
- **Optional Fields:** `phase_id`, `unit_id`, `governance_decision_ref`, `evidence_fingerprint`, `correlation_id`, `summary`, `data`.
- **Prohibited Fields:** `status`, `event_type`, `collaboration_session_id`.

### 4.3 Variant: `audit_event`
- **Purpose:** Retained as a serialization profile for event-stream logging and auditing (`RETAIN_AS_VARIANT`).
- **Canonical Source:** `RuntimeAuditEvent` in `orchestra_runtime/models.py`.
- **Required Fields:** `schema_version`, `message_type`, `timestamp`, `run_id`, `specialist`, `event_type`, `details`.
- **Optional Fields:** `parent_run_id`, `collaboration_session_id`, `correlation_id`, `summary`.
- **Prohibited Fields:** `status`, `disposition`, `operation`.

---

## 5. Field Definitions & Provenance Matrix

| Field Name | Type | Variant Applicability | Required/Optional | Provenance & Source Field | Description |
|---|---|---|---|---|---|
| `schema_version` | String | All variants | **Required** | Envelope Metadata | Fixed semantic version string (e.g. `"1.0.0"`). |
| `message_type` | String | All variants | **Required** | Envelope Metadata | Discriminated union key: `"execution_result"`, `"transition_decision"`, `"audit_event"`. |
| `timestamp` | String | All variants | **Required** | `ExecutionResult.timestamp` / `AuditEvent.timestamp` | ISO-8601 UTC timestamp string. |
| `run_id` | String | All variants | **Required** | `ExecutionResult.run_id` / `AuditEvent.run_id` | Subagent or specialist execution run identifier. |
| `specialist` | String | All variants | **Required** | `ExecutionResult.specialist` / `AuditEvent.specialist` | Canonical specialist name (e.g. `"ponytail"`, `"clockwork"`, `"arbiter"`). |
| `operation` | String | `execution_result`, `transition_decision` | **Required** | `ExecutionResult.operation` | Operational action name (e.g. `"file_edit"`, `"phase_gate_check"`). |
| `status` | String | `execution_result` | **Required** | `ExecutionResult.status` | Canonical execution status: `"COMPLETED"`, `"FAILED"`, `"CANCELLED"`, `"TIMED_OUT"`, `"BLOCKED"`, `"WAITING"`. |
| `disposition` | String | `transition_decision` | **Required** | `TransitionDecisionRecord.disposition` | Arbiter transition disposition (`"AUTO_CONTINUE"`, `"AUTO_REMEDIATE_AND_REVALIDATE"`, `"WAIT_FOR_EVIDENCE"`, `"WAIT_FOR_CAPACITY"`, `"ESCALATE_HUMAN"`, `"STOP"`). |
| `reason_code` | String | `execution_result`, `transition_decision` | **Required** | `TransitionDecisionRecord.reason_code` | Upper-case symbolic reason code (e.g. `"IMPLEMENTATION_SUCCESS"`, `"VALIDATION_FAILURE"`). |
| `event_type` | String | `audit_event` | **Required** | `RuntimeAuditEvent.event_type` | Canonical audit event type string. |
| `details` | Object | `audit_event` | **Required** | `RuntimeAuditEvent.details` | Structured audit event details object. |
| `parent_run_id` | String | `execution_result`, `audit_event` | Optional | `AuditEvent.parent_run_id` | Parent run identifier for nested subagent executions. Omitted if root. |
| `collaboration_session_id` | String | `audit_event` | Optional | `RuntimeAuditEvent.collaboration_session_id` | Coordination session identifier string. |
| `phase_id` | String | `transition_decision` | Optional | `TransitionDecisionRecord.phase_id` | Current delegated phase identifier. |
| `unit_id` | String | `transition_decision` | Optional | `TransitionDecisionRecord.unit_id` | Current unit plan identifier. |
| `authority_decision_ref` | String | `execution_result` | Optional | `AuthorityDecisionRecord.decision_id` | Reference identifier for associated Steward/Governor authority decision. |
| `capability_decision_ref` | String | `execution_result` | Optional | `CapabilityDecisionRecord.decision_id` | Reference identifier for associated capability evaluation. |
| `governance_decision_ref` | String | `execution_result`, `transition_decision` | Optional | `GovernanceDecisionRecord.decision_id` | Reference identifier for associated governance review record. |
| `evidence_fingerprint` | String | `execution_result`, `transition_decision` | Optional | `ExecutionEvidencePacket.working_tree_fingerprint` | SHA-256 digest of associated Git working tree evidence. |
| `correlation_id` | String | All variants | Optional | `RuntimeAuditEvent.correlation_id` | Reserved field location for cross-session correlation identifier. *Format selection deferred to Phase 1C.* |
| `summary` | String | All variants | Optional | `ExecutionResult.summary` | Non-authoritative human-readable text summary. |
| `data` | Object | `execution_result`, `transition_decision` | Optional | `ExecutionResult.details` | Non-authoritative structured execution details. |

---

## 6. Arbiter Disposition Terminology

The `disposition` field carried by a `transition_decision` variant records an Arbiter transition disposition:

- **`AUTO_CONTINUE`:** Indicates that Arbiter determined the next already-approved internal unit may begin under the current delegated execution envelope and current evidence. **It does NOT create authority, widen scope, approve an external action, or authorize merge, release, or deployment.**
- **`AUTO_REMEDIATE_AND_REVALIDATE`:** Indicates Arbiter routed the execution to a remediation specialist following a validation check.
- **`WAIT_FOR_EVIDENCE` / `WAIT_FOR_CAPACITY`:** Indicates execution is paused pending evidence availability or capacity reset.
- **`ESCALATE_HUMAN`:** Indicates execution requires human review before proceeding.
- **`STOP`:** Indicates execution is halted due to a blocked gate or policy failure.

---

## 7. Omission, Nullability, and Compatibility Rules

1. **Optional Fields:** Omitted when not applicable. Explicit `null` values MUST NOT be used as a substitute for field omission.
2. **Empty Collections:** Represented as `[]` for arrays and `{}` for objects when present.
3. **Unknown Additive Fields:** Consumers MUST ignore unrecognized optional fields during parsing for additive compatibility.
4. **Unknown Schema Version / Message Type:** Consumers MUST fail closed if `schema_version` major version is unsupported or `message_type` is unrecognized.

---

## 8. Security, Privacy, and Redaction

- **Secrets & Credentials:** Raw API keys, tokens, passwords, and private SSH keys MUST be redacted before envelope creation.
- **Log Minimization:** Envelopes MUST NOT contain full file diffs or raw terminal stdout/stderr streams. File changes MUST be represented by artifact path lists and SHA-256 content digests.

---

## 9. Illustrative Examples (Orchestra-Native)

### 9.1 Example: `execution_result` (Ponytail Implementation)

```json
{
  "schema_version": "1.0.0",
  "message_type": "execution_result",
  "timestamp": "2026-08-03T08:00:00Z",
  "run_id": "run-20260803-ponytail-001",
  "specialist": "ponytail",
  "operation": "targeted_code_edit",
  "status": "COMPLETED",
  "reason_code": "IMPLEMENTATION_SUCCESS",
  "evidence_fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "summary": "Targeted refactoring completed cleanly with 0 lint errors.",
  "data": {
    "files_changed": [
      "orchestra_runtime/models.py"
    ]
  }
}
```

### 9.2 Example: `transition_decision` (Arbiter Phase Gate)

```json
{
  "schema_version": "1.0.0",
  "message_type": "transition_decision",
  "timestamp": "2026-08-03T08:05:00Z",
  "run_id": "run-20260803-arbiter-002",
  "specialist": "arbiter",
  "operation": "delegated_phase_transition_check",
  "disposition": "AUTO_CONTINUE",
  "reason_code": "PHASE_GATE_CLEARANCE",
  "phase_id": "delegated-phase-b",
  "governance_decision_ref": "gov-dec-20260722-phase-b",
  "evidence_fingerprint": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284ddd200126d9069e",
  "summary": "Arbiter determined next already-approved unit may begin under current delegated execution envelope."
}
```

### 9.3 Example: `audit_event` (Chronicler Audit Stream)

```json
{
  "schema_version": "1.0.0",
  "message_type": "audit_event",
  "timestamp": "2026-08-03T08:10:00Z",
  "run_id": "run-20260803-chronicler-003",
  "specialist": "chronicler",
  "event_type": "COORDINATION_SIGNAL_RECORDED",
  "collaboration_session_id": "session-20260803-01",
  "details": {
    "signal_name": "unit_completion_verified"
  }
}
```

---

## 10. Failure & Design Compatibility Matrix

- **Compatibility Status:** `DESIGN_COMPATIBILITY_ASSESSED` (The design is intended to permit additive adoption alongside current human-readable output, but actual host and adapter compatibility remains unverified until implementation and integration tests exist.)

| Condition | Consumer Action | Fail Mode | Canonical Source Required |
|---|---|---|---|
| Unsupported `schema_version` major | Reject envelope | Fail Closed | Yes |
| Unrecognized `message_type` | Reject envelope | Fail Closed | Yes |
| Missing variant-required field | Reject envelope | Fail Closed | Yes |
| Unrecognized optional field | Ignore field, parse remainder | Fail Open (Additive) | Yes |
| Conflict between envelope & Git evidence | Reject envelope as stale | Fail Closed | Yes (`ExecutionEvidencePacket` wins) |
| Missing `disposition` on `transition_decision` | Reject envelope | Fail Closed | Yes |
