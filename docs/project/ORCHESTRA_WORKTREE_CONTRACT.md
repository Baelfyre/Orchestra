# Orchestra Worktree Contract Specification

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
This document specifies the `OrchestraWorktreeContract`, an optional, host-capability-dependent contract for negotiating, initializing, verifying, and safely releasing isolated Git worktrees for execution units within Orchestra.

---

## 2. Canonical Ownership & Responsibilities
- **Canonical Owner:** **Ponytail** (Implementation and Navigation Specialist).
- **Responsibility:** Owns codebase navigation, targeted file changes, Git worktree operations, path confinement validation, and safe workspace boundaries.
- **Secondary Consumers:** Conductor (routing context), Arbiter (transition verification), Overseer (evidence validation), Host Adapters (capability declaration).

---

## 3. Core Architectural Principles
1. **Optional & Host-Dependent:** Worktree isolation is an optional host capability (`worktree_supported: true/false`). It MUST NOT be mandatory for single-agent or lightweight execution.
2. **Non-Authorizing:** Worktree creation or existence does NOT grant execution, merge, release, or policy mutation authority.
3. **Strict Path Confinement:** Worktrees must be created only within authorized parent paths (`.tmp/` or `.orchestra/worktrees/`) inside or relative to the repository root. Path traversal (`..`), drive root escape, or UNC path injection is strictly prohibited.
4. **No Destructive Cleanup Invariant:** No automatic cleanup may delete a worktree, branch, or files unless Orchestra can prove that the exact resource was created under the current authorized execution identity and cleanup authority is explicitly present.

---

## 4. Contract Schema & Wire Format

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OrchestraWorktreeContract",
  "type": "object",
  "required": [
    "contract_version",
    "unit_id",
    "worktree_path",
    "worktree_branch",
    "approved_base_sha",
    "isolation_status"
  ],
  "properties": {
    "contract_version": { "type": "string", "const": "1.0" },
    "unit_id": { "type": "string" },
    "worktree_path": { "type": "string" },
    "worktree_branch": { "type": "string" },
    "approved_base_sha": { "type": "string" },
    "isolation_status": {
      "type": "string",
      "enum": ["INITIALIZED", "ACTIVE", "RELEASED", "FAILED_CLEANUP", "STALE_ORPHANED"]
    },
    "correlation_id": { "type": ["string", "null"] },
    "is_clean_at_start": { "type": "boolean" },
    "cleanup_policy": {
      "type": "string",
      "enum": ["EXPLICIT_HOST_ACTION_ONLY", "ADVISORY_SAFE_SUBSET"],
      "default": "EXPLICIT_HOST_ACTION_ONLY"
    }
  },
  "additionalProperties": false
}
```

---

## 5. Security & Path Security Rules
- **Canonical Path Resolution:** All paths are resolved to absolute canonical paths via Python `pathlib.Path.resolve()`.
- **Prefix Traversal Check:** `worktree_path` must satisfy `resolved_worktree_path.is_relative_to(authorized_parent_dir)`.
- **Preflight Verification:** `python scripts/preflight_sync_check.py` must run clean inside the initialized worktree prior to unit execution.
- **Dirty Worktree Protection:** If a worktree contains dirty uncommitted changes at teardown, cleanup fails closed (`FAILED_CLEANUP`) and requires manual maintainer intervention.

---

## 6. Adapter Capability Integration
Host adapters declare worktree support in adapter metadata:
```json
{
  "adapter_name": "codex",
  "capabilities": {
    "worktree_supported": true,
    "worktree_isolation_mode": "OPTIONAL"
  }
}
```
If `worktree_supported` is `false`, execution falls back gracefully to standard single-workspace execution.
