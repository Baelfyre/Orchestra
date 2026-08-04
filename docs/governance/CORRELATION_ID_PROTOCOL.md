# Orchestra Correlation ID Protocol Specification

> [!NOTE]
> **Status:** DESIGN SPECIFICATION ONLY
> **Implementation Status:** NOT IMPLEMENTED | NOT RELEASED
> **Canonical Owner:** Chronicler (Data Persistence & Audit Logging Specialist)
> **Selected Wire Format:** RFC 9562 UUIDv7 (Time-Ordered 128-bit UUID)
> **Selected Disposition:** `ADOPT_OPTIONAL_UUIDV7_WITH_IMPLEMENTATION_STRATEGY_UNRESOLVED`
> **Implementation Strategy:** `implementation_strategy_not_yet_selected`
> **Dependency Authority:** `external_dependency_not_currently_authorized`
> **Security & Privacy Status:** `DESIGN_RISK_ASSESSED` (`ACCEPTABLE_WITH_CONTROLS`)

---

## 1. Purpose & Scope

The `OrchestraCorrelationID` protocol defines a standard time-ordered correlation identifier for linking root runs, bounded delegated child runs, background tasks, and continuation sessions across Orchestra runtime records.

It populates the optional `correlation_id` header field reserved in `OrchestraRuntimeEnvelope`, `RuntimeAuditEvent`, and `ExecutionEvidencePacket`.

---

## 2. Non-Goals & Invariants

### 2.1 Non-Goals
- It does **NOT** replace canonical identity records (`run_id`, `parent_run_id`, `phase_id`, `unit_id`, `decision_id`, `working_tree_fingerprint`).
- It does **NOT** grant execution, merge, release, or deployment authority.
- It does **NOT** prove evidence freshness or working tree integrity.
- It does **NOT** authorize external PyPI dependencies (e.g. `ulid-py` is rejected).

### 2.2 Core Invariants
1. **Non-Authorizing Linkage Invariant:** A matching `correlation_id` links related records for audit and trace querying, but does NOT grant capability or override governance gates.
2. **Canonical Identity Precedence Invariant:** Specific run, phase, unit, and evidence identities remain canonical. In case of conflict, `run_id`, `phase_id`, `unit_id`, and `working_tree_fingerprint` win over `correlation_id`.
3. **No External PyPI Dependency Invariant:** External PyPI correlation libraries are not authorized. Format generation strategy MUST be evaluated during the runtime implementation phase.
4. **Optional & Additive Invariant:** `correlation_id` is an optional field. Missing `correlation_id` values MUST NOT invalidate an otherwise valid canonical record.

---

## 3. Existing Identity Inventory & Gap Analysis

The protocol accounts for all existing canonical identities in Orchestra:

| Existing Identity | Canonical Owner | Provenance Status | Scope | Primary Purpose |
|---|---|---|---|---|
| `run_id` | Clockwork | `PRESENT_CANONICAL` | Single run | Unique subagent or specialist run identifier |
| `parent_run_id` | Clockwork | `PRESENT_CANONICAL` | Child run link | Parent subagent run reference |
| `collaboration_session_id` | Chronicler | `PRESENT_CANONICAL` | CLI session | Single multi-turn CLI session tracking |
| `phase_id` | Steward | `PRESENT_CANONICAL` | Delegated phase | Delegated phase envelope reference |
| `unit_id` | Steward | `PRESENT_CANONICAL` | Unit plan | Approved execution unit reference |
| `working_tree_fingerprint` | Overseer | `PRESENT_CANONICAL` | Evidence packet | SHA-256 digest of Git working tree state |
| `decision_id` | Steward / Governor | `PRESENT_CANONICAL` | Governance record | Unique authority or governance decision reference |
| `approved_base_sha` | Overseer | `PRESENT_CANONICAL` | Git baseline | Base commit SHA for delegated envelope |
| `current_commit_sha` | Overseer | `PRESENT_CANONICAL` | Git state | HEAD commit SHA at execution time |
| `staged_patch_hash` | Overseer | `PRESENT_CANONICAL` | Git diff | Hash of staged working tree changes |
| `tracked_patch_hash` | Overseer | `PRESENT_CANONICAL` | Git diff | Hash of tracked working tree changes |
| `artifact_lifecycle_records` | Overseer | `PRESENT_CANONICAL` | Artifact state | Fingerprints of generated artifacts |
| `schema_version` (envelope) | Clockwork | `PROPOSED_NOT_IMPLEMENTED` | Envelope metadata | Machine envelope serialization version |

### 3.1 Verified Correlation Gaps
1. **Gap 1 (Cross-Session Linkage):** Linking root runs across disconnected continuation sessions lacks a unified correlation header (`VERIFIED_GAP`).
2. **Gap 2 (Pipeline Traceability):** Associating machine envelopes, audit events, and evidence packets from the same root task lacks a common header (`VERIFIED_GAP`).
3. **Gap 3 (Resume Correlation):** Re-associating resumed executions following capacity waits or human escalations (`VERIFIED_GAP`).

---

## 4. Selected Wire Format: RFC 9562 UUIDv7

### 4.1 Wire Format Specification
- **Format:** 128-bit RFC 9562 UUIDv7 string in standard 8-4-4-4-12 hex format (e.g. `018c3f2a-7b00-7000-8000-000000000001`).
- **Structure:**
  - 48 bits: Unix epoch timestamp in milliseconds.
  - 4 bits: Version bit (`0111` for UUIDv7).
  - 12 bits: Sub-millisecond sequence / random bits.
  - 2 bits: Variant bits (`10` for RFC 4122/9562 variant).
  - 62 bits: Cryptographically strong pseudo-random bits.

### 4.2 Runtime Compatibility & Implementation Strategy
- **Python Stdlib Support:** Native `uuid.uuid7()` was added to Python stdlib in version **3.14**.
- **Python Floor:** Python versions 3.11/3.12/3.13 stdlib `uuid` module provide `uuid1()`, `uuid3()`, `uuid4()`, `uuid5()`, but NOT native `uuid7()`.
- **Implementation Strategy:** `implementation_strategy_not_yet_selected`. Selection of the specific generator implementation strategy (native Python 3.14+ stdlib vs project-owned stdlib builder vs deferred generator) is explicitly deferred to the runtime implementation phase. No external PyPI dependencies are authorized.

---

## 5. Sortability & Monotonicity Semantics

- **Chronological Sortability:** UUIDv7 timestamp prefix supports coarse chronological sorting at millisecond resolution across logs and audit streams.
- **Same-Millisecond Monotonicity:** Strict same-millisecond generation order is **NOT** guaranteed unless a specific monotonic generator is implemented and validated. No monotonic generator is approved in Phase 1C/1C.1.
- **Causality & Transition Authority:** Canonical lifecycle states, parent-child run linkages (`parent_run_id`), phase unit sequence numbers, and evidence records remain authoritative for execution causality and transition ordering. Correlation identifiers MUST NOT be used to infer causal sequence.

---

## 6. Generation & Propagation Boundaries

### 6.1 Creation Boundary
- **Root Operations:** A new `correlation_id` is generated at the trusted root execution boundary by trusted runtime composition.
- **Host / Adapter Inputs:** Caller-provided or host-provided correlation values are treated as **untrusted metadata** until checked and validated against canonical continuation evidence. Unvalidated caller inputs MUST NOT overwrite trusted correlation values.

### 6.2 Propagation Rules
- **Bounded Delegated Child Runs:** Inherit parent `correlation_id` alongside `parent_run_id`.
- **Retry and Remediation:** Preserve `correlation_id` ONLY when the logical operation remains the same, authorized scope is unchanged, and execution is linked to the same canonical unit or operation.
- **Wait and Resume Cycles:** Preserve `correlation_id` ONLY when waiting and resume records are canonically linked, the authorized envelope remains valid, and no material scope change occurred.
- **Human Escalation:** Preserve `correlation_id` ONLY when the human decision resolves missing intent for the same logical task within the same approved execution envelope. A materially changed scope, new task request, or new execution envelope MUST receive a new `correlation_id`.
- **Parallel Units:** Parallel execution units executing under the same `ApprovedUnitPlan` share the root `correlation_id` while preserving distinct `unit_id` values.

---

## 7. Security, Privacy, and Metadata Leakage

- **Privacy Assessment:** `SECURITY_AND_PRIVACY_STATUS: DESIGN_RISK_ASSESSED` (`ACCEPTABLE_WITH_CONTROLS`).
- **Metadata Disclosure:** UUIDv7 exposes creation-time metadata through its 48-bit timestamp field. The protocol treats this as a known metadata-disclosure risk rather than secret leakage.
- **Required Privacy Controls:**
  1. Avoid unnecessary external publication or cross-tenant reuse.
  2. Scope log retention according to project evidence policy.
  3. Do NOT use correlation IDs as authentication or authorization tokens.
  4. Do NOT derive user identity, repository paths, or secret material from correlation timestamps.
  5. Enforce regex validation pattern: `^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`. Malformed values MUST be safely omitted or rejected.
