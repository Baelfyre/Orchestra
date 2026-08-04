# Spec Kitty-Derived Orchestra Phase 3 Implementation Plan

## Status
```text
IMPLEMENTATION PLAN
PHASE 3A MERGED (PR #210, SHA 1629eaf3cd3f156f8913f84c9229666257a3145a)
PHASE 3B IMPLEMENTED AND MERGED (PR #212, REVIEWED HEAD 2a6c7ea8db16ce73d66fae566672f3681094b0f7, MERGE COMMIT fa1e052d82301e70a5869258c3fc6af765163353)
PHASE 3C NOT STARTED
IMPLEMENTATION AUTHORITY NOT GRANTED BY THIS DOCUMENT
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: PHASE_3B_IMPLEMENTED_MERGED_PHASE_3C_NOT_STARTED
```

## Purpose
This document specifies the technical implementation plan for executing the Candidate Phase 3 Spec Kitty-derived capabilities (`OrchestraStatusProjection` and `OrchestraWorktreeContract`) within Orchestra.

---

## Subphase Sequencing & Scope

### Phase 3A: Deferred-Capability Selection & Design Baseline (`DESIGN_ACCEPTED_MERGED`)
- Read-only repository assessment, capability selection, ownership assignment, security analysis, compatibility definition, and implementation planning.
- Design package accepted and merged through PR #210 (`1629eaf3cd3f156f8913f84c9229666257a3145a`). Zero runtime code, script, adapter, test, or policy edits performed.

### Phase 3B: `OrchestraStatusProjection` Implementation (`IMPLEMENTED_AND_MERGED` via PR #212)
- Implementation of `OrchestraStatusProjection` typed model (`orchestra_runtime/status.py`), JSON serializer, and CLI renderer (`scripts/orchestra_status.py` / `python -m orchestra_runtime.status`).
- Unit tests in `tests/runtime/test_status_projection.py`.
- **Mandatory Edge Case Coverage (from PR #210 review finding F-001):**
  - Multiple remotes, no origin remote, unborn branch
  - Detached HEAD, shallow clone, CI detached checkout
  - Git binary unavailable, not a Git repository
  - Read-only filesystem, worktree checkout
  - Dirty repository, conflicting canonical files, malformed canonical prose

### Phase 3C: `OrchestraWorktreeContract` Implementation (`PLANNED` / `NOT_STARTED`)
- Implementation of `OrchestraWorktreeContract` typed model (`orchestra_runtime/worktree.py`), path confinement validator, base SHA checker, and host adapter metadata integration.
- Unit tests in `tests/runtime/test_worktree_contract.py`.
- **Mandatory Scope & Finding Requirements (from PR #210 review findings F-002, F-003):**
  - Define or remove `ADVISORY_SAFE_SUBSET` from `cleanup_policy` schema in prose before implementation begins. Must not permit automatic destructive cleanup.
  - Coverage for locked worktrees, nested repositories, submodules
  - Creation races, cleanup races, case-insensitive path collisions

### Phase 3D: Consolidated Validation & Safety Audit (`PLANNED`)
- Consolidated behavior, governance, security, packaging, and backward-compatibility validation across all direct scripts, behavior suite, and runtime tests.

### Phase 3E: Maintainer Review, PR & Merge (`PLANNED`)
- Maintainer code review, commit authorization, push authorization, remote verification, and PR merge.

---

## Non-Goals
- Executing runtime code edits, test edits, script edits, or adapter edits during Phase 3A.
- Making worktree isolation mandatory for single-agent or lightweight execution.
- Granting execution, merge, release, or policy mutation authority based on worktree status or status projection.
- Introducing background daemons, web dashboards, SQLite event stores, or network services.

---

## Human Authorization Gates
1. **Candidate Phase 3A Gate:** Maintainer review and authorization of documentation-only design package.
2. **Candidate Phase 3B Gate:** Maintainer authorization before launching Phase 3B code edits.
3. **Candidate Phase 3C Gate:** Maintainer authorization before launching Phase 3C code edits.
4. **Candidate Phase 3E Gate:** Maintainer review, commit, push, and PR merge authorization.
