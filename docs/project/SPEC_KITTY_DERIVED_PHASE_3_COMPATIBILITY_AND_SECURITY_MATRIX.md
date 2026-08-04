# Spec Kitty-Derived Orchestra Phase 3 Compatibility and Security Matrix

## Status
```text
COMPATIBILITY AND SECURITY MATRIX
DESIGN ACCEPTED AND MERGED (PR #210, SHA 1629eaf3cd3f156f8913f84c9229666257a3145a)
PHASE 3B IMPLEMENTED AND MERGED (PR #212, SHA fa1e052d82301e70a5869258c3fc6af765163353)
PHASE 3C RUNTIME NOT IMPLEMENTED
NOT RELEASED
VERDICT: PHASE_3B_IMPLEMENTED_MERGED_PHASE_3C_NOT_STARTED
```

## 1. Overview
This document specifies the compatibility and security assessment matrix for Candidate Phase 3 capabilities (`OrchestraWorktreeContract` and `OrchestraStatusProjection`) across operating systems, Python runtimes, host adapters, Git environments, and safety boundaries.

---

## 2. Platform & OS Support Matrix

| Dimension | Target Variant | Assessment Status | Notes & Security Boundaries |
|---|---|---|---|
| Python Runtime | Python 3.11 (3.11.9) | `DESIGN_TARGET` | Standard local development baseline. Zero PyPI dependencies. |
| Python Runtime | Python 3.12 | `DESIGN_TARGET` | CI target platform. |
| Python Runtime | Python 3.13 | `DESIGN_TARGET` | Repository declared matrix target. |
| Python Runtime | Python 3.14+ | `DESIGN_TARGET` | Forward compatibility target. |
| Operating System | Windows 11 (Win32 x86_64) | `DESIGN_TARGET` | Primary local environment. Path normalization handles drive letters, backslashes, and UNC paths safely. |
| Operating System | Linux (Ubuntu 24.04) | `DESIGN_TARGET` | Primary CI runner platform. Standard POSIX path semantics. |
| Operating System | macOS (Darwin) | `DESIGN_TARGET` | CI runner platform. Case-preserving path checks. |

---

## 3. Host Adapter Capability Matrix

| Adapter Name | Directory Path | Worktree Support | Status Projection Support | Notes |
|---|---|---|---|---|
| Codex Adapter | `adapters/codex/` | `OPTIONAL` | `SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`). |
| Antigravity Adapter | `adapters/antigravity/` | `OPTIONAL` | `SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`). |
| Gemini Adapter | `adapters/gemini/` | `SCAFFOLD_ONLY` | `SUPPORTED` | Scaffold adapter; read-only status projection supported. |
| Cursor Adapter | `adapters/cursor/` | `SCAFFOLD_ONLY` | `SUPPORTED` | Scaffold adapter; read-only status projection supported. |
| Windsurf Adapter | `adapters/windsurf/` | `SCAFFOLD_ONLY` | `SUPPORTED` | Scaffold adapter; read-only status projection supported. |
| Claude Adapter | `adapters/claude/` | `SCAFFOLD_ONLY` | `SUPPORTED` | Scaffold adapter; read-only status projection supported. |
| VSCode Adapter | `adapters/vscode/` | `SCAFFOLD_ONLY` | `SUPPORTED` | Scaffold adapter; read-only status projection supported. |
| JetBrains Adapter | `adapters/jetbrains/` | `NOT_APPLICABLE` | `SCAFFOLD_ONLY` | Scaffold adapter; target for future adapter graduation. |
| Zed Adapter | `adapters/zed/` | `NOT_APPLICABLE` | `SCAFFOLD_ONLY` | Scaffold adapter; target for future adapter graduation. |
| Neovim Adapter | `adapters/neovim/` | `NOT_APPLICABLE` | `SCAFFOLD_ONLY` | Scaffold adapter; target for future adapter graduation. |

---

## 4. Git Environment Edge-Case Matrix

| Git Environment Scenario | Worktree Contract Behavior | Status Projection Behavior | Security / Invariant Protection |
|---|---|---|---|
| Standard Git repo | Allowed (`worktree add`) | Normal status projection | Path confinement verified |
| Non-Git directory | Fail closed (`NOT_A_GIT_REPO`) | Returns `is_git_repo: false`, status `UNKNOWN` | No subprocess errors leaked |
| Detached HEAD | Allowed with explicit base SHA | Returns `current_branch: "(HEAD detached at ...)"` | Exact SHA recorded |
| Dirty working tree | Fails teardown (`DIRTY_WORKTREE_BLOCK`) | Reports `dirty_count > 0` | Zero automatic deletion of dirty files |
| Path traversal (`..`) | Fail closed (`PATH_TRAVERSAL_REJECTED`) | Path normalized before display | Path confinement strictly enforced |
| Shallow clone / no origin | Base SHA check against local HEAD | `origin_main_sha: "UNKNOWN"` | No remote network calls forced |
| Multiple remotes | Resolves `origin` or fallback remote | Discovers and reports all named remotes | No hardcoded single remote assumption |
| Unborn branch (empty repo) | Rejects creation (`UNBORN_BRANCH`) | Reports `current_branch: "master/main (unborn)"` | Base SHA required |
| Read-only filesystem | Fail closed on creation (`EACCES`) | Operates in read-only mode successfully | No write attempts forced by projection |
| Git binary unavailable | Fail closed (`GIT_NOT_FOUND`) | Returns `is_git_repo: false`, status `UNKNOWN` | Graceful fallback without crash |
| Locked worktrees (`.git/worktrees/.../locked`) | Fail closed (`WORKTREE_LOCKED`) | Reports `worktree_locked: true` | Prevents force removal of locked trees |
| Submodules present | Ignores submodule paths | Reports top-level repo status only | Submodule trees excluded from confinement |
| Nested repositories | Rejects creation inside child repo | Reports top-level repo status | Root-confinement check prevents nested containment breach |
| Symlinks / junction points | Resolved to realpath before check | Normalized canonical path displayed | Traversal via symlinks prevented |

---

## 5. Security & Privacy Controls
1. **Zero Secret Leakage:** Status projection redacts credentials embedded in Git remote URLs (e.g. `https://token@github.com/...` -> `https://***@github.com/...`).
2. **Subprocess Isolation:** All Git commands executed via `run_command` or Python `subprocess.run` use explicit array arguments (no `shell=True`), timeout bounds (10s), and strict path confinement.
3. **Explicit Cleanup Boundaries:** Worktree contract teardown is strictly `EXPLICIT_HOST_ACTION_ONLY`. Orchestra MUST NOT perform automatic destructive cleanup of dirty worktrees, user-created worktrees, or untracked state.
