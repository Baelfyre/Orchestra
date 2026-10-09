# Spec Kitty-Derived Orchestra Phase 3 Compatibility and Security Matrix

## Status
```text
COMPATIBILITY AND SECURITY MATRIX
DESIGN ACCEPTED AND MERGED (PR #210, SHA 1629eaf3cd3f156f8913f84c9229666257a3145a)
PHASE 3B IMPLEMENTED AND MERGED (PR #212, SHA fa1e052d82301e70a5869258c3fc6af765163353)
PHASE 3C IMPLEMENTED AND MERGED (PR #214, REVIEWED HEAD 646111325e6de7c5d31915789fdc22a644125b7b, MERGE COMMIT 6bce297c7469f9c08ce41308cbb993cc863ac540)
PHASE 3D EXACT-HEAD VALIDATION COMPLETE
PHASE 3E REVIEW AND MERGE COMPLETE
NOT RELEASED
POLICY NOT ACTIVATED
VERDICT: PHASE_3_COMPLETE_MERGED_NOT_RELEASED
```

## 1. Overview
This document specifies the compatibility and security assessment matrix for the implemented Phase 3 capabilities (`OrchestraWorktreeContract` and `OrchestraStatusProjection`) across operating systems, Python runtimes, host adapters, Git environments, and safety boundaries.

---

## 2. Platform & OS Support Matrix

| Dimension | Target Variant | Assessment Status | Notes & Security Boundaries |
|---|---|---|---|
| Python Runtime | Python 3.11 (3.11.9) | `VALIDATED_TARGET` | Standard local development baseline. Zero PyPI dependencies. |
| Python Runtime | Python 3.12 | `VALIDATED_TARGET` | CI target platform. |
| Python Runtime | Python 3.13 | `DECLARED_TARGET` | Repository declared matrix target. |
| Python Runtime | Python 3.14+ | `FORWARD_COMPATIBILITY_TARGET` | Requires revision-specific validation when adopted. |
| Operating System | Windows 11 (Win32 x86_64) | `VALIDATED_TARGET` | Primary local environment. Path normalization handles drive letters, backslashes, UNC paths, junctions, and case-insensitive collisions safely. |
| Operating System | Linux (Ubuntu 24.04) | `VALIDATED_TARGET` | Primary CI runner platform. Standard POSIX path semantics. |
| Operating System | macOS (Darwin) | `VALIDATED_TARGET` | CI runner platform. Case-preserving path checks. |

---

## 3. Host Adapter Capability Matrix

| Adapter Name | Directory Path | Worktree Support | Status Projection Support | Notes |
|---|---|---|---|---|
| Codex Adapter | `adapters/codex/` | `OPTIONAL` | `SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`). Installed parity remains separately validated. |
| Antigravity Adapter | `adapters/antigravity/` | `OPTIONAL` | `SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`). Installed import verification remains a host-local action. |
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
| Detached HEAD | Allowed with explicit base SHA | Reports detached identity | Exact SHA recorded |
| Dirty working tree | Fails teardown (`DIRTY_WORKTREE_BLOCK`) | Reports dirty paths | Zero automatic deletion of dirty files |
| Path traversal (`..`) | Fail closed (`PATH_OUTSIDE_AUTHORIZED_PARENT`) | Path normalized before display | Path confinement strictly enforced |
| Shallow clone / no origin | Base SHA check against available local identity | Reports unavailable remote identity as unknown | No remote network calls forced |
| Multiple remotes | Uses verified repository identity | Discovers named remotes | No hardcoded single-remote authority |
| Unborn branch (empty repo) | Rejects creation without an approved commit | Reports unborn state | Base SHA required |
| Read-only filesystem | Fail closed on creation | Projection remains read-only | No write attempts forced by projection |
| Git binary unavailable | Fail closed (`GIT_NOT_FOUND`) | Returns unknown state | Graceful fallback without crash |
| Locked worktrees | Fail closed (`WORKTREE_LOCKED`) | Reports available lock evidence | Prevents force removal of locked trees |
| Submodules present | Detects and preserves submodule boundaries | Reports top-level repository status | Distinct repositories are not recursively removed |
| Nested repositories | Rejects unsafe nested boundaries | Reports top-level repository status | Root-confinement checks prevent containment breach |
| Symlinks / junction points | Resolves canonical destinations before confinement checks | Displays normalized canonical path | Link traversal and authorized-parent escape fail closed |
| State change during release | Fails two-phase fingerprint verification | Not applicable | TOCTOU mutation blocks removal |
| Status inspection failure | Fails closed before removal | Reports unknown when applicable | No cleanup on incomplete evidence |

---

## 5. Security & Privacy Controls
1. **Zero Secret Leakage:** Status projection redacts credentials embedded in Git remote URLs.
2. **Subprocess Isolation:** Git commands use explicit argument arrays, bounded execution, and repository/path confinement; no `shell=True` execution is required.
3. **Explicit Cleanup Boundaries:** Worktree teardown is strictly `EXPLICIT_HOST_ACTION_ONLY`. Orchestra does not automatically delete dirty, user-created, unrelated, or identity-mismatched worktrees or branches.
4. **Revision-Specific Evidence:** Compatibility and validation claims bind to the reviewed implementation revision. A later release candidate requires fresh exact-head validation.
5. **Release Boundary:** Merged implementation does not imply publication, deployment, installed-host refresh, or policy activation.
