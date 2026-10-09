
# Orchestra Status Projection Specification

## Status
```text
DESIGN SPECIFICATION & RUNTIME MODEL
PHASE 3B IMPLEMENTED AND MERGED (PR #212)
REVIEWED HEAD: 2a6c7ea8db16ce73d66fae566672f3681094b0f7
MERGE COMMIT: fa1e052d82301e70a5869258c3fc6af765163353
MERGED AT: 2026-08-04T21:34:29Z
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: IMPLEMENTED_AND_MERGED
```

## 1. Overview
This document specifies the `OrchestraStatusProjection`, a read-only, deterministic status projection CLI and JSON schema that unifies live Git state, project state, contract implementation status, and revision-matched validation results into a single surface.

---

## 2. Canonical Ownership & Responsibilities
- **Canonical Owner:** **Scribe** (Documentation and Knowledge Transfer Specialist).
- **Responsibility:** Owns status summary formats, state projection schemas, knowledge base alignment, and presentation formats.
- **Implementation Specialist:** **Ponytail** (Implementation and Navigation Specialist).
- **Downstream Roles:** Conductor (routing context), Arbiter (continuity validation), Overseer (release readiness check).

---

## 3. Core Architectural Principles
1. **Strictly Read-Only:** The status projection NEVER mutates repository files, Git refs, or governance policy.
2. **Derived Fact Model:** The projection derives status exclusively from live Git facts, canonical prose files, and current validation command outputs. It is NEVER a primary source of truth.
3. **No False Authority Invariant:** Status projection outputs summarize state; they do NOT grant execution, merge, release, or policy mutation authority.
4. **Fail-Closed Reporting:** Missing canonical data reports `null` or explicit `unknown_fields` paths. Conflicting sources are explicitly highlighted under `diagnostics.conflicts` rather than silently reconciled.

---

## 4. Source Precedence Hierarchy
1. **Git Facts** (refs, HEAD SHA, porcelain status) override prose branch claims.
2. **Canonical Prose** (`PROJECT_STATE.md`, `PROJECT_CONTEXT.md`, `SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`) provide project lifecycle stage and active software task.
3. **Revision-Matched Validation Results** provide test and governance check status (only accepted when validation revision matches current HEAD SHA).
4. **Historical Handoffs** provide non-authoritative historical evidence only.

---

## 5. Contract Schema & Wire Format (Reconciled Phase 3B Schema)

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
    "validation",
    "diagnostics"
  ],
  "properties": {
    "projection_version": { "type": "string", "const": "1.0" },
    "timestamp": { "type": "string" },
    "git": {
      "type": "object",
      "required": ["is_git_repo", "current_branch", "head_sha", "is_clean"],
      "properties": {
        "is_git_repo": { "type": "boolean" },
        "current_branch": { "type": ["string", "null"] },
        "head_sha": { "type": ["string", "null"] },
        "is_clean": { "type": ["boolean", "null"] },
        "staged_count": { "type": ["integer", "null"] },
        "modified_count": { "type": ["integer", "null"] },
        "untracked_count": { "type": ["integer", "null"] },
        "ahead_count": { "type": ["integer", "null"] },
        "behind_count": { "type": ["integer", "null"] },
        "selected_remote": { "type": ["string", "null"] },
        "selected_main_ref": { "type": ["string", "null"] },
        "selected_main_sha": { "type": ["string", "null"] },
        "remote_names": { "type": "array", "items": { "type": "string" } },
        "is_shallow": { "type": ["boolean", "null"] },
        "is_worktree": { "type": ["boolean", "null"] },
        "worktree_path_redacted": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "project": {
      "type": "object",
      "required": ["current_release", "active_phase", "policy_integrated"],
      "properties": {
        "current_release": { "type": ["string", "null"] },
        "active_phase": { "type": ["string", "null"] },
        "policy_integrated": { "type": ["boolean", "null"] }
      },
      "additionalProperties": false
    },
    "contracts": {
      "type": "object",
      "properties": {
        "runtime_envelope": { "type": ["string", "null"] },
        "correlation_id": { "type": ["string", "null"] },
        "phase_retrospective": { "type": ["string", "null"] },
        "approved_unit_plan_extension": { "type": ["string", "null"] },
        "worktree_contract": { "type": ["string", "null"] },
        "status_projection": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "validation": {
      "type": "object",
      "properties": {
        "evidence_revision": { "type": ["string", "null"] },
        "revision_match": { "type": ["boolean", "null"] },
        "governance_check": { "type": ["string", "null"] },
        "preflight_sync": { "type": ["string", "null"] },
        "runtime_test_count": { "type": ["integer", "null"] },
        "runtime_coverage": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "diagnostics": {
      "type": "object",
      "required": ["unknown_fields", "conflicts", "warnings"],
      "properties": {
        "unknown_fields": { "type": "array", "items": { "type": "string" } },
        "conflicts": { "type": "array", "items": { "type": "string" } },
        "warnings": { "type": "array", "items": { "type": "string" } }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 6. CLI Execution & Exit Code Semantics
- **Command:** `python -m orchestra_runtime.status` or `python scripts/orchestra_status.py`.
- **Options:**
  - `--repo PATH`: Path to target repository (default: current directory `.`).
  - `--json`: Format output as deterministic UTF-8 JSON.
  - `--quiet`: Suppress output and return execution status code only.
- **Exit Codes:**
  - `0`: Projection executed successfully and status output formatted cleanly (or suppressed with `--quiet`).
  - `1`: Invalid arguments, missing Git binary, or unrecoverable command failure.
- Exit codes report command execution success only; they do NOT create governance authority or merge readiness.

---

## 7. Design Contradiction Resolutions (Phase 3B)

1. **C-01 (Typed Unknowns):** Typed fields use `null` when data is missing, and field paths are collected in `diagnostics.unknown_fields`.
2. **C-02 (Remote Selection):** `selected_remote` names the active remote (preferring `origin`, falling back to first lexicographical remote if `origin` is absent).
3. **C-03 (Edge Case Schema Expansion):** Schema explicitly models `is_git_repo`, `is_shallow`, `is_worktree`, `remote_names`, and `worktree_path_redacted`.
4. **C-04 (Revision-Matched Validation):** `validation.revision_match` explicitly verifies `evidence_revision == head_sha`. Mismatches report `false` and generate a diagnostic warning.
5. **C-05 (Strict Read-Only Execution):** Status CLI collects existing facts without executing test runners, validators, or network operations.
6. **C-06 (Determinism & Injected Clock):** Builder accepts injectable timestamp (`now: datetime`) and command runner for byte-identical unit testing.
7. **C-07 (Path Privacy & Redaction):** Worktree paths are normalized and redacted to relative paths or bounded labels (e.g. `[worktree: <branch>]`). Credentials in remote URLs are strictly redacted.

---

## 8. Maintainer Audit Finding Closures (Phase 3B Revision)

1. **F-001 (Lazy Package Exports):** Replaced eager `from .status import ...` in `orchestra_runtime/__init__.py` with module-level `__getattr__` and `__dir__` lazy exports so `python -m orchestra_runtime.status` runs without `runpy` `sys.modules` pre-import warnings.
2. **F-002 (Strict Runtime Model Validation):** Added `__post_init__` validation across all status dataclasses (`StatusDiagnostic`, `GitStatus`, `ProjectStatus`, `ContractStatus`, `ValidationStatus`, `DiagnosticsStatus`, `OrchestraStatusProjection`) enforcing non-negative integer counts, valid ISO-8601 UTC timestamps, exact version string constants (`"1.0"`), and valid hex SHAs.
3. **F-003 (NUL-Delimited Porcelain Parsing):** Switched status collector from line-delimited `git status --porcelain=v1` to NUL-delimited `-z` parsing (`git status --porcelain=v1 -z --untracked-files=all`), safely handling filenames containing spaces, tabs, quotes, or non-ASCII characters.
4. **F-004 (Focused Coverage Gate):** Expanded `tests/runtime/test_status_projection.py` to 28 unit tests, raising focused statement coverage of `orchestra_runtime/status.py` to 91% and branch coverage to 91%.
