# Orchestra Status Projection Specification

## Status
```text
DESIGN SPECIFICATION
DESIGN ONLY
RUNTIME NOT IMPLEMENTED
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: READY_FOR_PHASE_3A_MAINTAINER_REVIEW
```

## 1. Overview
This document specifies the `OrchestraStatusProjection`, a read-only, deterministic status projection CLI and JSON schema that unifies live Git state, project state, contract implementation status, and revision-matched validation results into a single surface.

---

## 2. Canonical Ownership & Responsibilities
- **Canonical Owner:** **Scribe** (Documentation and Knowledge Transfer Specialist).
- **Responsibility:** Owns status summary formats, state projection schemas, knowledge base alignment, and presentation formats.
- **Secondary Consumers:** Conductor (routing context), Arbiter (continuity validation), Overseer (release readiness check), Ponytail (CLI implementation).

---

## 3. Core Architectural Principles
1. **Strictly Read-Only:** The status projection NEVER mutates repository files, Git refs, or governance policy.
2. **Derived Fact Model:** The projection derives status exclusively from live Git facts, canonical prose files, and current validation command outputs. It is NEVER a primary source of truth.
3. **No False Authority Invariant:** Status projection outputs summarize state; they do NOT grant execution, merge, release, or policy mutation authority.
4. **Fail-Closed Reporting:** Missing canonical data outputs `UNKNOWN`. Conflicting sources are explicitly highlighted rather than silently reconciled.

---

## 4. Source Precedence Hierarchy
1. **Git Facts** (refs, HEAD SHA, porcelain status) override prose branch claims.
2. **Canonical Prose** (`PROJECT_STATE.md`, `PROJECT_CONTEXT.md`) provide project lifecycle stage and active software task.
3. **Revision-Matched Validation Results** provide test and governance check status.
4. **Historical Handoffs** provide non-authoritative historical evidence only.

---

## 5. Contract Schema & Wire Format

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OrchestraStatusProjection",
  "type": "object",
  "required": [
    "projection_version",
    "timestamp",
    "git",
    "project",
    "contracts",
    "validation"
  ],
  "properties": {
    "projection_version": { "type": "string", "const": "1.0" },
    "timestamp": { "type": "string" },
    "git": {
      "type": "object",
      "required": ["current_branch", "head_sha", "origin_main_sha", "is_clean", "ahead_count", "behind_count"],
      "properties": {
        "current_branch": { "type": "string" },
        "head_sha": { "type": "string" },
        "origin_main_sha": { "type": "string" },
        "is_clean": { "type": "boolean" },
        "staged_count": { "type": "integer" },
        "modified_count": { "type": "integer" },
        "untracked_count": { "type": "integer" },
        "ahead_count": { "type": "integer" },
        "behind_count": { "type": "integer" }
      }
    },
    "project": {
      "type": "object",
      "required": ["current_release", "active_phase", "policy_integrated"],
      "properties": {
        "current_release": { "type": "string" },
        "active_phase": { "type": "string" },
        "policy_integrated": { "type": "boolean" }
      }
    },
    "contracts": {
      "type": "object",
      "properties": {
        "runtime_envelope": { "type": "string" },
        "correlation_id": { "type": "string" },
        "phase_retrospective": { "type": "string" },
        "approved_unit_plan_extension": { "type": "string" },
        "worktree_contract": { "type": "string" },
        "status_projection": { "type": "string" }
      }
    },
    "validation": {
      "type": "object",
      "properties": {
        "governance_check": { "type": "string" },
        "preflight_sync": { "type": "string" },
        "runtime_test_count": { "type": "integer" },
        "runtime_coverage": { "type": "string" }
      }
    }
  },
  "additionalProperties": false
}
```

---

## 6. CLI Execution & Exit Code Semantics
- **Command:** `python -m orchestra_runtime.status` or `python scripts/orchestra_status.py`.
- **Options:** `--json` for machine-readable JSON output; `--quiet` for minimal exit code check.
- **Exit Codes:**
  - `0`: Projection executed successfully and status output formatted cleanly.
  - `1`: Invalid arguments or failed subprocess execution.
- Exit codes report command execution success only; they do NOT create governance authority or merge readiness.
