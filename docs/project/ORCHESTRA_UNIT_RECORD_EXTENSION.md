# Orchestra Unit Record Extension Specification

> [!NOTE]
> **Status:** DESIGN SPECIFICATION ONLY
> **Implementation Status:** NOT INTEGRATED INTO DELEGATED_EXECUTION_POLICY | NOT IMPLEMENTED | NOT RELEASED
> **Canonical Owner:** The Steward (Scope Authority & Schema Owner)
> **Secondary Consumer:** Conductor (Execution Routing)
> **Validation Owner:** Overseer (QA & Validation)
> **Continuity Consumer:** Arbiter (Transition Continuity)
> **Primary Disposition:** `EXTEND_APPROVED_UNIT_PLAN` (Schema Extension embedded in `ApprovedUnitPlan`)
> **Retention Classification:** `REPOSITORY_TRACKED_WHEN_SANITIZED` (Sanitized unit plans tracked in repository; sensitive authority details referenced)
> **Compatibility Status:** `DESIGN_COMPATIBILITY_ASSESSED` | `COMPATIBILITY_INTENT_DOCUMENTED`
> **Forbidden Architecture:** Standalone competing unit-state files (e.g. `.orchestra/units/`) are strictly **REJECTED**.

---

## 1. Purpose & Scope

The `OrchestraUnitRecord` is a machine-readable JSON schema extension embedded inside `ApprovedUnitPlan` (`docs/governance/DELEGATED_EXECUTION_POLICY.md`).

It provides a deterministic machine representation for approved unit boundaries (`scope_ref`), assigned specialist roles (`responsible_specialist`), repository path restrictions (`allowed_paths`), predecessor dependencies (`dependency_unit_ids`), and validation requirements, enabling LLM machine adapters and automated validation scripts to parse unit plan boundaries without parsing Markdown text.

---

## 2. Non-Goals & Invariants

### 2.1 Non-Goals
- It is **NOT** a standalone file or competing state authority (standalone `.orchestra/units/` files are REJECTED).
- It does **NOT** record mutable execution status (`IN_PROGRESS`, `COMPLETED`, `FAILED`) inside the plan. Mutable state remains strictly in `orchestra_runtime/coordination.py` (`CoordinationContract` / `UnitExecutionState`).
- It does **NOT** grant execution, merge, release, or deployment authority.
- It does **NOT** replace `ExecutionEvidencePacket` or `TransitionDecisionRecord`.

### 2.2 Core Invariants
1. **Single Source of Truth Invariant:** `ApprovedUnitPlan` remains the single canonical source of truth for approved unit definitions. This extension embeds machine-readable JSON structures within the approved plan document.
2. **Immutable Definition Invariant:** Fields in `OrchestraUnitRecord` represent immutable approved definitions. Once execution begins, unit boundaries, path restrictions, and validation requirements MUST NOT be mutated without formal re-approval.
3. **Non-Authorizing Schema Invariant:** Unit record fields describe boundaries and references; they do NOT grant new capability or override delegated execution envelopes. Execution authority binds strictly through `execution_envelope_ref` (`DelegatedExecutionEnvelope`).
4. **Canonical Scope Invariant:** Canonical scope binds via `scope_ref` (referencing approved unit scope or envelope section). Path restrictions (`allowed_paths`) narrow file-mutation boundaries but do NOT create scope or grant file authority (`scope_ref != authority grant`, `allowed_paths != authority grant`).
5. **Clean Separation of Concerns:** Mutable execution state, evidence digests, and Arbiter transition decisions MUST remain in their respective canonical records (`coordination.py`, `ExecutionEvidencePacket`, `TransitionDecisionRecord`).

---

## 3. Unit Class Compatibility & Non-File Units

The unit extension explicitly supports both file-mutation units and non-file unit classes:

| Unit Class Category | `scope_ref` Requirement | `allowed_paths` Applicability | Write Authority | Example Unit Type |
|---|---|---|---|---|
| `FILE_MUTATION` | **Required** | **Conditionally Required** (Must specify target paths) | Bound via envelope | Refactoring code, adding features, editing scripts |
| `READ_ONLY_REPOSITORY_REVIEW` | **Required** | **Optional** (Read boundary reference) | None | Code audit, security review, PR inspection |
| `ARCHITECTURE_OR_DESIGN` | **Required** | **Optional / Not Applicable** | None | Contract design, architectural mapping |
| `GOVERNANCE_OR_COMPLIANCE_REVIEW` | **Required** | **Optional / Not Applicable** | None | Licensing check, policy compliance |
| `VALIDATION_OR_EVIDENCE_REVIEW` | **Required** | **Optional / Not Applicable** | None | Evidence packet verification, test analysis |
| `DOCUMENTATION` | **Required** | **Conditionally Required** (Doc paths) | Bound via envelope | Updating user guides, design docs |
| `NON_FILE_RUNTIME_OPERATION` | **Required** | **Optional / Omitted** | Bound via envelope | Background service check, environment check |

- **Non-File Rule:** An omitted `allowed_paths` field for non-file units MUST NEVER be interpreted as broad file authority. It signifies that file mutation is NOT authorized for that unit.

---

## 4. Path Validation Contract

Where repository path restrictions apply (`allowed_paths`, `prohibited_paths`):
1. **Repository-Relative Normalization:** All paths MUST use repository-relative forward-slash syntax (e.g. `orchestra_runtime/models.py`).
2. **Path Traversal Guard:** Absolute paths, drive-letter escapes (`C:\`), parent traversal (`../`), and symlink escapes MUST be rejected during plan validation.
3. **Source of Truth Protection:** Edits targeting persistent runtime mirrors (e.g. `.agents/`), temporary directories, or caches MUST be rejected.
4. **Non-Authorizing Property:** Path validation narrows already-authorized repository operations; it does NOT grant file-system authority.

---

## 5. Canonical Dependency Eligibility

- **Predecessor Eligibility Rule:** A hard predecessor dependency listed in `dependency_unit_ids` is satisfied ONLY when current canonical coordination, evidence, checkpoint, and transition records establish that the predecessor reached the required **accepted state** under `DELEGATED_EXECUTION_POLICY.md` (e.g. accepted checkpoint or canonical transition evidence).
- **Execution Completion Insufficiency:** Execution completion alone does NOT satisfy a dependency. A predecessor that executed but failed validation, remained unaccepted, became stale, or received a non-continuation disposition DOES NOT satisfy a dependency.
- **Non-Authorizing Dependencies:** Dependency satisfaction is a necessary routing condition for Conductor, but does NOT grant execution or merge authority.
- **Circular Dependency Guard:** Circular dependencies between unit records are invalid and MUST be rejected by Overseer validation during plan review.

---

## 6. Unit Revision Justification & Semantics

- **Revision Justification:** `unit_revision` (e.g. `"rev-1"`) differentiates post-approval plan amendments within the same `execution_envelope_ref` and `unit_id`. Stale evidence tied to `rev-1` MUST NOT validate a replacement `rev-2` unit definition.
- **Revision Semantics:** Initial value is normalized to `"rev-1"`. Increment is managed through The Steward-owned planning boundary upon re-approval. `unit_revision` becomes immutable once unit execution begins.

---

## 7. Unit Record Extension Schema (`json:orchestra-unit-record`)

When embedded inside `ApprovedUnitPlan` markdown documents, the unit record extension is serialized as a JSON code block using tag `json:orchestra-unit-record`:

```json:orchestra-unit-record
{
  "schema_version": "1.0.0",
  "unit_id": "unit-01-core-models",
  "unit_revision": "rev-1",
  "unit_name": "Core Models Infrastructure",
  "phase_id": "phase-01-architecture",
  "execution_envelope_ref": "env-20260803-01",
  "scope_ref": "sec-04-approved-scope",
  "responsible_specialist": "clockwork",
  "objective": "Define core typed dataclasses for coordination runtime.",
  "allowed_paths": [
    "orchestra_runtime/models.py"
  ],
  "prohibited_paths": [
    "docs/governance/",
    "tests/"
  ],
  "dependency_unit_ids": [],
  "expected_outputs": [
    "orchestra_runtime/models.py"
  ],
  "validation_requirements": [
    "python scripts/governance_check.py --strict"
  ],
  "governance_decision_ref": "gov-dec-20260722-01"
}
```

---

## 8. Schema Field Definitions & Provenance

Total Schema Fields: **15 fields** (11 universally required, 1 conditionally required, 3 optional).

| Field Name | Type | Requirement Level | Provenance Source | Description |
|---|---|---|---|---|
| `schema_version` | String | **Universally Required** | Extension Metadata | Fixed semantic version string (`"1.0.0"`). |
| `unit_id` | String | **Universally Required** | `ApprovedUnitPlan` | Unique unit identifier within the phase (e.g. `"unit-01-core-models"`). |
| `unit_revision` | String | **Universally Required** | `ApprovedUnitPlan` | Immutable plan revision string (e.g. `"rev-1"`). Scoped to `execution_envelope_ref` + `unit_id`. |
| `unit_name` | String | **Universally Required** | `ApprovedUnitPlan` | Descriptive human-readable unit name. |
| `phase_id` | String | **Universally Required** | `ApprovedUnitPlan.phase_id` | Associated delegated phase identifier. |
| `execution_envelope_ref` | String | **Universally Required** | `DelegatedExecutionEnvelope.id` | Governing delegated execution envelope reference (root execution authority source). |
| `scope_ref` | String | **Universally Required** | `ApprovedUnitPlan` | Canonical scope reference to approved unit scope or section in governing envelope. |
| `responsible_specialist` | String | **Universally Required** | `ApprovedUnitPlan` | Assigned specialist responsibility role (`"ponytail"`, `"clockwork"`, `"cloak"`). |
| `objective` | String | **Universally Required** | `ApprovedUnitPlan` | Primary objective statement. |
| `expected_outputs` | Array[String] | **Universally Required** | `ApprovedUnitPlan` | List of expected file/artifact outputs. |
| `validation_requirements` | Array[String] | **Universally Required** | `ApprovedUnitPlan` | List of required validation commands/scripts. |
| `allowed_paths` | Array[String] | **Conditionally Required** | `ApprovedUnitPlan` | Allowed repository path restrictions (Required for `FILE_MUTATION`; omitted for non-file units). |
| `prohibited_paths` | Array[String] | Optional | `ApprovedUnitPlan` | Explicitly forbidden path boundaries. |
| `dependency_unit_ids` | Array[String] | Optional | `ApprovedUnitPlan` | Predecessor unit IDs required to be accepted before starting. |
| `governance_decision_ref` | String | Optional | Governance Review | Reference to Governor/Steward review decision (does NOT grant execution authority). |

---

## 9. Machine Validation & Deterministic Recovery

- **Validation Reason Codes:** An invalid or unparseable `json:orchestra-unit-record` block results in `validation_result: INVALID` and `reason_code: INVALID_UNIT_PLAN`.
- **Deterministic Schema Defects:** Deterministic schema or syntax defects are rejected and returned to The Steward-owned planning boundary for correction.
- **Human Escalation:** Missing maintainer intent, material scope change, policy conflict, or required new authority triggers `ESCALATE_HUMAN`.
- **Post-Approval Immutability:** Once an `ApprovedUnitPlan` is authorized, embedded `OrchestraUnitRecord` blocks MUST NOT be edited in-place during execution.

---

## 10. Security, Privacy, and Retention

- **Retention Classification:** `REPOSITORY_TRACKED_WHEN_SANITIZED` / `MIXED_RETENTION_MODEL`.
- **Sanitized Unit Definitions:** Sanitized unit plan definitions are tracked in repository storage. Sensitive authority or capability details MUST be referenced via opaque identifiers rather than embedded directly in public Git history.

---

## 11. Future Policy Integration & Compatibility Boundary

- **Phase 1F Policy Boundary:** Phase 1F (Cross-Document Synchronization) will synchronize accepted design decisions into repository history, roadmap, state references, and future integration sequencing. Phase 1F does NOT integrate the schema into runtime behavior and does NOT make the extension mandatory in `DELEGATED_EXECUTION_POLICY.md`.
- **Compatibility Strategy:** `COMPATIBILITY_INTENT_DOCUMENTED`. Legacy `ApprovedUnitPlan` documents without embedded JSON blocks remain valid under legacy schema rules. The extension applies only when its schema version tag (`json:orchestra-unit-record`) is explicitly declared.
