# Spec Kitty-Derived Orchestra Phase 3 Implementation Plan

## Status
```text
IMPLEMENTATION PLAN
IMPLEMENTATION NOT STARTED
POLICY NOT INTEGRATED
NOT RELEASED
VERDICT: READY_FOR_PHASE_3A_MAINTAINER_REVIEW
```

## Purpose
This document specifies the technical implementation plan for executing the Candidate Phase 3 Spec Kitty-derived capabilities (`OrchestraStatusProjection` and `OrchestraWorktreeContract`) within Orchestra.

---

## Subphase Sequencing & Scope

### Phase 3A: Deferred-Capability Selection & Design Baseline (`DESIGN_COMPLETE`)
- Read-only repository assessment, capability selection, ownership assignment, security analysis, compatibility definition, and implementation planning.
- Zero runtime code, script, adapter, test, or policy edits.

### Phase 3B: `OrchestraStatusProjection` Implementation (`PLANNED`)
- Implementation of `OrchestraStatusProjection` typed model (`orchestra_runtime/status.py`), JSON serializer, and CLI renderer (`scripts/orchestra_status.py` / `python -m orchestra_runtime.status`).
- Unit tests in `tests/runtime/test_status_projection.py`.

### Phase 3C: `OrchestraWorktreeContract` Implementation (`PLANNED`)
- Implementation of `OrchestraWorktreeContract` typed model (`orchestra_runtime/worktree.py`), path confinement validator, base SHA checker, and host adapter metadata integration.
- Unit tests in `tests/runtime/test_worktree_contract.py`.

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
