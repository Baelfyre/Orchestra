# Spec Kitty-Derived Orchestra Phase 3 Capability Assessment

## Status
```text
CAPABILITY ASSESSMENT
DESIGN ACCEPTED AND MERGED (PR #210, SHA 1629eaf3cd3f156f8913f84c9229666257a3145a)
RUNTIME NOT IMPLEMENTED
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: DESIGN_ACCEPTED_MERGED
```

## 1. Executive Summary
This document records the Candidate Phase 3A capability assessment for the two deferred concepts derived from the Spec Kitty pattern review: `OrchestraWorktreeContract` and `OrchestraStatusProjection`.

Both concepts address verified architectural gaps in Orchestra:
1. `OrchestraWorktreeContract`: Establishes an optional, host-capability-dependent contract for negotiating, creating, verifying base SHAs, and safely cleaning up isolated Git worktrees during parallel unit execution.
2. `OrchestraStatusProjection`: Establishes a read-only, deterministic status projection CLI and JSON schema that unifies live Git state, project state, contract implementation status, and revision-matched validation results into a single surface.

Both concepts are **PROMOTED FOR DESIGN AND IMPLEMENTATION PLANNING** (`PROMOTE_FOR_DESIGN`). No runtime code, scripts, adapters, or tests are modified during Candidate Phase 3A.

---

## 2. Canonical Baseline & Source Inventory
- **Baseline Repository:** `C:\conductor` (`origin/main` at `0eebe7d7b65708c61c22d9f31c2ea50189407727`).
- **Phase 2 Baseline:** Merged PR #208 (`feat(runtime): add governed phase execution contracts` at `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`) and PR #209 (`docs: synchronize Spec Kitty Phase 2 post-merge state` at `0eebe7d7b65708c61c22d9f31c2ea50189407727`).
- **Inspected Sources:** `PROJECT_STATE.md`, `PROJECT_CONTEXT.md`, `SESSION_HANDOFF.md`, `DECISION_LOG.md`, `CHANGELOG.md`, `ROADMAP.md`, `SPEC_KITTY_DERIVED_UPGRADE_ROADMAP.md`, `SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`, `PORTABLE_ADAPTER_PROTOCOL.md`, `AUTHORITY_CAPABILITY_CONTRACTS.md`, `PROMOTION_05_WORKTREE_ISOLATION.md`, `orchestra_runtime/`, `scripts/`, `adapters/`, `tests/`.

---

## 3. Current-State Gap Audit

### 3.1 Worktree Support Audit
- **Existing Support:** Manual worktree creation under `.tmp/` or `.agents/worktrees/` is documented and used in development workflows (`CANONICAL_DOCUMENTED_ONLY`). Preflight checks run clean inside worktrees (`CANONICAL`).
- **Verified Gap:** Orchestra lacks a standardized, machine-readable contract for host adapters to declare worktree support (`worktree_supported`), verify worktree base SHAs against unit plans, restrict path traversal, and safely negotiate cleanup without risky wildcard deletions.
- **Classification:** `PARTIAL` / `AD_HOC`.

### 3.2 Status & Projection Support Audit
- **Existing Support:** Project state (`PROJECT_STATE.md`), context (`PROJECT_CONTEXT.md`), session handoffs (`SESSION_HANDOFF.md`), and validation scripts (`preflight_sync_check.py`, `governance_check.py`) provide prose and script outputs (`CANONICAL_SOURCE` / `VALIDATION_RESULT`).
- **Verified Gap:** Orchestra lacks a single, read-only status projection CLI (`orchestra_status` / `python -m orchestra_runtime.status`) that deterministically combines Git facts, unreleased-main state, contract implementation statuses, and revision-matched validation into human-readable terminal output and structured JSON.
- **Classification:** `DERIVED_DISPERSED` / `VERIFIED_GAP`.

---

## 4. Capability 1: `OrchestraWorktreeContract` Assessment

### 4.1 Boundary & Principles
- **Optional & Host-Dependent:** Worktree isolation is an optional execution optimization for multi-unit or parallel agent workflows. It MUST NOT be mandatory for single-agent or lightweight execution.
- **Non-Authorizing:** Worktree creation or existence does NOT grant execution, merge, release, or policy mutation authority.
- **Canonical Owner:** **Ponytail** (Implementation and Navigation Specialist). Ponytail owns repository navigation, targeted file changes, Git worktree operations, and safe workspace boundaries.
- **Secondary Consumers:** Conductor (routing), Arbiter (transition verification), Overseer (evidence validation), Host Adapters (capability declaration).

### 4.2 Security & Invariants
- **Invariant:** No automatic cleanup may delete a worktree, branch, or files unless Orchestra can prove that the exact resource was created under the current authorized execution identity and cleanup authority is explicitly present.
- **Path Confinement:** Worktrees must be located within authorized parent directories (`.tmp/` or `.orchestra/worktrees/`) inside or parallel to the repository root. Path traversal (`..`), drive root escape, or UNC path injection is strictly prohibited.
- **Cleanup Strategy:** `EXPLICIT_HOST_ACTION_ONLY` with advisory checks. Destructive automatic deletion of dirty or user-created worktrees is prohibited.

### 4.3 Disposition
- **Disposition:** `PROMOTE_FOR_DESIGN` / `PROMOTE_FOR_IMPLEMENTATION_PLANNING`.

---

## 5. Capability 2: `OrchestraStatusProjection` Assessment

### 5.1 Boundary & Principles
- **Read-Only:** The status projection NEVER mutates repository state, Git refs, or governance policy.
- **Derived Fact Model:** The projection derives status exclusively from live Git facts, canonical prose files, and current validation command outputs. It is NEVER a primary source of truth.
- **Canonical Owner:** **Scribe** (Documentation and Knowledge Transfer Specialist). Scribe owns status summary formats, state projection schemas, and knowledge base alignment.
- **Secondary Consumers:** Conductor (routing context), Arbiter (continuity validation), Overseer (release readiness check), Ponytail (CLI implementation).

### 5.2 Source Precedence
1. **Git Facts** (refs, HEAD SHA, porcelain status) override prose branch claims.
2. **Canonical Prose** (`PROJECT_STATE.md`, `PROJECT_CONTEXT.md`) provide project lifecycle stage and active software task.
3. **Revision-Matched Validation Results** provide test and governance check status.
4. **Missing or Conflicting Data** outputs `UNKNOWN` or explicit conflict markers. It NEVER infers success or reconciles silently.

### 5.3 Disposition
- **Disposition:** `PROMOTE_FOR_DESIGN` / `PROMOTE_FOR_IMPLEMENTATION_PLANNING`.

---

## 6. Cross-Concept Comparison & Recommended Sequence

| Dimension | OrchestraWorktreeContract | OrchestraStatusProjection |
|---|---|---|
| Verified Gap | Absence of typed host worktree negotiation | Absence of unified read-only status CLI/JSON |
| Canonical Owner | Ponytail | Scribe |
| Primary Risk | Path traversal & unsafe worktree cleanup | False authority perception or stale prose |
| Mutation Potential | Workspace creation / teardown (low/controlled) | Zero (strictly read-only) |
| Recommended Priority | Priority 2 (Phase 3C) | Priority 1 (Phase 3B) |
| Disposition | `PROMOTE_FOR_DESIGN` | `PROMOTE_FOR_DESIGN` |

### Recommended Candidate Phase 3 Implementation Sequence
- **Phase 3A:** Read-only capability selection, ownership, architecture, compatibility, security, and implementation planning (`DESIGN_COMPLETE`).
- **Phase 3B:** `OrchestraStatusProjection` model, serializer, CLI renderer, and unit tests.
- **Phase 3C:** `OrchestraWorktreeContract` model, validator, base SHA checker, and unit tests.
- **Phase 3D:** Consolidated behavior, governance, security, packaging, and compatibility validation.
- **Phase 3E:** Maintainer review, commit, push, PR, and merge gates.

---

## 7. Out-of-Scope Items
- `OrchestraProviderContract` (separate unscheduled concept).
- Cross-session correlation persistence or SQLite event databases.
- Automatic merge, automatic branch deletion, or automatic policy mutation.
- Background daemons, web dashboards, or RPC network services.

---

## 8. Post-Review Findings & Implementation Constraints

From the immutable-head maintainer review of PR #210 (reviewed head `3d8b14a`):

- **Blocking Findings:** 0
- **Non-Blocking Findings (1):**
  - **F-003 (`docs/project/ORCHESTRA_WORKTREE_CONTRACT.md`):** `ADVISORY_SAFE_SUBSET` in `cleanup_policy` schema lacks prose definition. Must be defined in prose or removed from schema before Phase 3C implementation.
- **Advisory Findings (3):**
  - **F-001 (`docs/project/ORCHESTRA_STATUS_PROJECTION.md`):** Expand explicit edge-case coverage (multiple remotes, unborn branch, read-only filesystem, Git binary unavailable, worktree checkout) in Phase 3B planning.
  - **F-002 (`docs/project/ORCHESTRA_WORKTREE_CONTRACT.md`):** Address locked worktrees, nested repositories, submodules, and race conditions in Phase 3C planning.
  - **F-004 (`docs/project/SPEC_KITTY_DERIVED_PHASE_3_COMPATIBILITY_AND_SECURITY_MATRIX.md`):** Acknowledge JetBrains, Zed, and Neovim adapter matrix status.
