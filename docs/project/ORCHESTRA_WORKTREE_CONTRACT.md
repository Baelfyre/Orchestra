# Orchestra Worktree Contract Specification

## Status
```text
DESIGN SPECIFICATION ACCEPTED (PR #210, SHA 1629eaf3cd3f156f8913f84c9229666257a3145a)
RUNTIME IMPLEMENTED (Phase 3C)
IMMUTABLE REVIEW AND BOUNDED REMEDIATION COMPLETE
MERGED THROUGH PR #214
REVIEWED HEAD 646111325e6de7c5d31915789fdc22a644125b7b
MERGE COMMIT 6bce297c7469f9c08ce41308cbb993cc863ac540
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: IMPLEMENTED_MERGED_NOT_RELEASED
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
- **`ADVISORY_SAFE_SUBSET` Cleanup Policy Definition:** `ADVISORY_SAFE_SUBSET` permits reporting cleanup candidates and performing non-destructive verification only. It MUST NOT remove a worktree, delete a branch, delete files, prune administrative metadata, or mutate Git state. Any destructive cleanup remains strictly `EXPLICIT_HOST_ACTION_ONLY` with exact creation-identity proof and explicit maintainer authority.

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

---

## 7. Mandatory Phase 3C Edge-Case Requirements

The merged Phase 3C implementation handles the following edge cases deterministically:

1. **Locked Worktrees:** If a worktree contains a `.git/worktrees/<id>/locked` file, cleanup fails closed (`WORKTREE_LOCKED`) and requires explicit manual unlock before teardown.
2. **Nested Repositories & Submodules:** Submodules and nested `.git` directories within a worktree tree are detected; cleanup does not recursively delete distinct Git repositories.
3. **Creation & Teardown Race Conditions:** Worktree directory creation verifies non-existence before invocation and handles concurrent allocation attempts safely.
4. **Case-Insensitive Collision Handling:** On Windows and macOS, worktree path comparison accounts for case-preserving case-insensitive filesystem collisions.
