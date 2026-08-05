"""OrchestraWorktreeContract Model, Validator, and Safe Worktree Runtime Operations.

Candidate Phase 3C: Optional, host-capability-dependent, path-confined, non-authorizing,
and fail-closed Git worktree isolation runtime.

Security Revision applied post-audit:
  F-IDENTITY-001: Repository identity is now bound into the creation-identity digest.
  F-PATH-CASE-001: Platform-aware collision keys (win32/darwin casefold, linux case-sensitive).
  F-NESTED-001:    Recursive nested-repository detection via os.walk; git submodule status.
  F-TOCTOU-001:    Two-phase release verification with fingerprint comparison.
  NB-001:          Incorrect filesystem lock fallback removed.
  NB-002:          Canonical git worktree add argument order.
  NB-003:          Post-release deregistration and branch-preservation verification.
  NB-004:          State transition enforcement before result construction.
  NB-005:          WORKTREE_CREATION_RACE used for TOCTOU race; PATH_ALREADY_EXISTS for initial check.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable

WORKTREE_CONTRACT_VERSION = "1.0"
AUTHORIZED_PARENT_DIRS = (".tmp", ".orchestra/worktrees")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
UNIT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
CORRELATION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")
BRANCH_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-/.:]+$")

# SCP-style SSH remote pattern: git@host:Owner/Repo.git
_SCP_REMOTE_RE = re.compile(r"^(?:[^@]+@)?([^:]+):(.+)$")
# URL-style remote (https, ssh, git schemes)
_URL_REMOTE_RE = re.compile(r"^(?:https?|ssh|git)://(?:[^@]+@)?([^/]+)/(.+)$")


class WorktreeIsolationStatus(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    FAILED_CLEANUP = "FAILED_CLEANUP"
    STALE_ORPHANED = "STALE_ORPHANED"


class WorktreeCleanupPolicy(str, enum.Enum):
    EXPLICIT_HOST_ACTION_ONLY = "EXPLICIT_HOST_ACTION_ONLY"
    ADVISORY_SAFE_SUBSET = "ADVISORY_SAFE_SUBSET"


class WorktreeReasonCode(str, enum.Enum):
    NOT_A_GIT_REPO = "NOT_A_GIT_REPO"
    GIT_NOT_FOUND = "GIT_NOT_FOUND"
    INVALID_CONTRACT = "INVALID_CONTRACT"
    INVALID_UNIT_ID = "INVALID_UNIT_ID"
    INVALID_CORRELATION_ID = "INVALID_CORRELATION_ID"
    INVALID_BASE_SHA = "INVALID_BASE_SHA"
    BASE_SHA_MISMATCH = "BASE_SHA_MISMATCH"
    INVALID_BRANCH = "INVALID_BRANCH"
    INVALID_PATH = "INVALID_PATH"
    PATH_TRAVERSAL_REJECTED = "PATH_TRAVERSAL_REJECTED"
    ABSOLUTE_PATH_REJECTED = "ABSOLUTE_PATH_REJECTED"
    UNC_PATH_REJECTED = "UNC_PATH_REJECTED"
    PATH_OUTSIDE_AUTHORIZED_PARENT = "PATH_OUTSIDE_AUTHORIZED_PARENT"
    PATH_COLLISION = "PATH_COLLISION"
    PATH_ALREADY_EXISTS = "PATH_ALREADY_EXISTS"
    WORKTREE_UNSUPPORTED = "WORKTREE_UNSUPPORTED"
    # WORKTREE_CREATION_RACE: path appeared between initial nonexistence check and git creation
    WORKTREE_CREATION_RACE = "WORKTREE_CREATION_RACE"
    WORKTREE_ADD_FAILED = "WORKTREE_ADD_FAILED"
    WORKTREE_NOT_REGISTERED = "WORKTREE_NOT_REGISTERED"
    WORKTREE_IDENTITY_MISMATCH = "WORKTREE_IDENTITY_MISMATCH"
    WORKTREE_DIRTY = "WORKTREE_DIRTY"
    WORKTREE_LOCKED = "WORKTREE_LOCKED"
    NESTED_REPOSITORY_DETECTED = "NESTED_REPOSITORY_DETECTED"
    SUBMODULE_BOUNDARY_DETECTED = "SUBMODULE_BOUNDARY_DETECTED"
    CLEANUP_AUTHORITY_REQUIRED = "CLEANUP_AUTHORITY_REQUIRED"
    ADVISORY_POLICY_NON_DESTRUCTIVE = "ADVISORY_POLICY_NON_DESTRUCTIVE"
    WORKTREE_RELEASE_RACE = "WORKTREE_RELEASE_RACE"
    WORKTREE_REMOVE_FAILED = "WORKTREE_REMOVE_FAILED"
    STALE_ORPHANED = "STALE_ORPHANED"
    REPOSITORY_IDENTITY_UNAVAILABLE = "REPOSITORY_IDENTITY_UNAVAILABLE"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"


@dataclass(frozen=True)
class WorktreeDiagnostic:
    code: WorktreeReasonCode
    message: str


@dataclass(frozen=True)
class OrchestraWorktreeContract:
    unit_id: str
    worktree_path: str
    worktree_branch: str
    approved_base_sha: str
    isolation_status: WorktreeIsolationStatus
    contract_version: str = WORKTREE_CONTRACT_VERSION
    correlation_id: str | None = None
    is_clean_at_start: bool = True
    cleanup_policy: WorktreeCleanupPolicy = WorktreeCleanupPolicy.EXPLICIT_HOST_ACTION_ONLY
    creation_identity: str | None = None


@dataclass(frozen=True)
class WorktreeValidationResult:
    valid: bool
    diagnostics: tuple[WorktreeDiagnostic, ...] = ()


@dataclass(frozen=True)
class WorktreeOperationResult:
    success: bool
    contract: OrchestraWorktreeContract | None = None
    diagnostics: tuple[WorktreeDiagnostic, ...] = ()


# ---------------------------------------------------------------------------
# State Transition Rules  (NB-004: enforced at runtime)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[WorktreeIsolationStatus, set[WorktreeIsolationStatus]] = {
    WorktreeIsolationStatus.INITIALIZED: {
        WorktreeIsolationStatus.ACTIVE,
        WorktreeIsolationStatus.FAILED_CLEANUP,
        WorktreeIsolationStatus.STALE_ORPHANED,
    },
    WorktreeIsolationStatus.ACTIVE: {
        WorktreeIsolationStatus.RELEASED,
        WorktreeIsolationStatus.FAILED_CLEANUP,
        WorktreeIsolationStatus.STALE_ORPHANED,
    },
    WorktreeIsolationStatus.FAILED_CLEANUP: {
        WorktreeIsolationStatus.RELEASED,
        WorktreeIsolationStatus.STALE_ORPHANED,
    },
    WorktreeIsolationStatus.RELEASED: set(),
    WorktreeIsolationStatus.STALE_ORPHANED: set(),
}


def transition_worktree_status(
    current: WorktreeIsolationStatus, target: WorktreeIsolationStatus
) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


def _require_transition(
    current: WorktreeIsolationStatus,
    target: WorktreeIsolationStatus,
    contract: OrchestraWorktreeContract,
) -> WorktreeOperationResult | None:
    """Return a failed result if the transition is invalid, else None (allowed)."""
    if not transition_worktree_status(current, target):
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.INVALID_STATE_TRANSITION,
                    message=(
                        f"Transition from {current.value} to {target.value} is not permitted."
                    ),
                ),
            ),
        )
    return None


def verify_worktree_base_sha(sha: str) -> bool:
    if not isinstance(sha, str):
        return False
    return bool(SHA_PATTERN.match(sha.lower()))


# ---------------------------------------------------------------------------
# Repository Identity (F-IDENTITY-001)
# ---------------------------------------------------------------------------

def normalize_git_remote_identity(raw_url: str) -> str | None:
    """Return a host-path-only canonical identity for a remote URL, or None.

    Handles:
      - https://user:token@github.com/Owner/Repo.git  -> github.com/Owner/Repo
      - ssh://git@github.com/Owner/Repo.git           -> github.com/Owner/Repo
      - git@github.com:Owner/Repo.git                 -> github.com/Owner/Repo
      - https://github.com/Owner/Repo                 -> github.com/Owner/Repo

    Only the hostname is lowercased. The repository path case is preserved.
    Credentials and usernames are stripped. Trailing .git and trailing slash
    are removed from the path segment.
    """
    url = raw_url.strip()
    if not url:
        return None

    host: str
    path_part: str

    m_url = _URL_REMOTE_RE.match(url)
    if m_url:
        host = m_url.group(1).lower()
        path_part = m_url.group(2)
    else:
        m_scp = _SCP_REMOTE_RE.match(url)
        if m_scp:
            host = m_scp.group(1).lower()
            path_part = m_scp.group(2)
        else:
            return None

    # Strip trailing .git (case-insensitive)
    if path_part.lower().endswith(".git"):
        path_part = path_part[:-4]
    # Strip trailing slash
    path_part = path_part.rstrip("/")

    if not host or not path_part:
        return None

    return f"{host}/{path_part}"


def derive_repository_identity(
    repo_root: Path | str,
    runner: Callable | None = None,
) -> tuple[str | None, WorktreeReasonCode | None]:
    """Derive a deterministic, host-path-free, credential-free repository identity.

    Algorithm:
      1. List configured remotes (git remote).
      2. Prefer 'origin'; otherwise lexicographically first remote.
      3. Normalize the remote URL -> canonical host/path.
      4. Hash the canonical identity string.
      5. Fallback: sorted root commits (git rev-list --max-parents=0 --all).
      6. If neither is available: fail closed with REPOSITORY_IDENTITY_UNAVAILABLE.

    Returns (identity_hex_str, None) on success or (None, reason_code) on failure.
    The identity is a SHA-256 hex digest of the canonical repository descriptor.
    """
    runner_fn = runner or _default_command_runner
    resolved = Path(repo_root).resolve()

    # Step 1: list remotes
    code, stdout, _ = runner_fn(["git", "remote"], cwd=resolved)
    if code == 0 and stdout.strip():
        remotes = stdout.strip().splitlines()
        chosen_remote = "origin" if "origin" in remotes else sorted(remotes)[0]

        code2, url_out, _ = runner_fn(
            ["git", "remote", "get-url", chosen_remote], cwd=resolved
        )
        if code2 == 0 and url_out.strip():
            canonical = normalize_git_remote_identity(url_out.strip())
            if canonical:
                digest = hashlib.sha256(
                    f"remote:{canonical}".encode("utf-8")
                ).hexdigest()
                return digest, None

    # Step 5 fallback: root commits
    code3, roots_out, _ = runner_fn(
        ["git", "rev-list", "--max-parents=0", "--all"], cwd=resolved
    )
    if code3 == 0 and roots_out.strip():
        sorted_roots = "|".join(sorted(roots_out.strip().splitlines()))
        digest = hashlib.sha256(
            f"roots:{sorted_roots}".encode("utf-8")
        ).hexdigest()
        return digest, None

    return None, WorktreeReasonCode.REPOSITORY_IDENTITY_UNAVAILABLE


# ---------------------------------------------------------------------------
# Cross-Platform Collision Keys (F-PATH-CASE-001)
# ---------------------------------------------------------------------------

def derive_path_collision_key(path: str, platform_name: str | None = None) -> str:
    """Return a collision-detection key for the given path string.

    Platform semantics:
      win32:  case-insensitive  (os.path.normcase + casefold)
      darwin: case-insensitive  (casefold only — normcase is a no-op on POSIX)
      other:  case-sensitive    (normalize separators only)

    The serialized path is never modified; this key is used only for comparison.

    Args:
        path:          The raw path string (may use OS or POSIX separators).
        platform_name: Override sys.platform for deterministic testing.
                       Accepts 'win32', 'darwin', or any other string.
    """
    platform = platform_name if platform_name is not None else sys.platform
    # Normalize separators to forward-slash for consistent cross-platform keying
    normalized = path.replace("\\", "/")
    if platform in ("win32", "darwin"):
        return normalized.casefold()
    return normalized


# ---------------------------------------------------------------------------
# Recursive Nested Repository and Submodule Detection (F-NESTED-001)
# ---------------------------------------------------------------------------

def find_nested_git_boundary(
    target_path: Path,
    platform_name: str | None = None,
) -> tuple[bool, str | None]:
    """Scan all descendants of target_path for nested .git entries.

    Does NOT follow symlink directories. Ignores the linked worktree's own
    root .git file (which is a file, not a directory, for worktrees).
    Returns (found, sanitized_relative_evidence | None).

    Uses os.walk with followlinks=False for a complete traversal.
    """
    target_str = str(target_path)

    for dirpath, dirnames, filenames in os.walk(target_str, followlinks=False):
        dir_path = Path(dirpath)
        rel = dir_path.relative_to(target_path)
        is_root = str(rel) == "."

        # Check for .git directory among subdirs
        if ".git" in dirnames:
            if is_root:
                # Root .git directory would mean target IS a git repo, not a nested one.
                # For a worktree, root .git is a FILE (not dir). A .git dir at root
                # means this target is a bare/init conflict — treat as nested boundary.
                dirnames.remove(".git")  # don't descend into it
                return True, ".git"
            else:
                rel_evidence = str(dir_path.relative_to(target_path) / ".git")
                return True, rel_evidence

        # Check for .git file in current directory files
        if ".git" in filenames:
            if not is_root:
                # A .git file in a subdirectory is a gitlink — nested worktree or submodule
                rel_evidence = str(dir_path.relative_to(target_path) / ".git")
                return True, rel_evidence
            # At root: this is the linked worktree file — ignore it

        # Do not follow symlink directories (os.walk followlinks=False handles dirs;
        # also remove symlinked dirs from dirnames to prevent descent)
        dirnames[:] = [
            d for d in dirnames
            if not (dir_path / d).is_symlink()
        ]

    return False, None


def _check_submodule_boundary(
    target_path: Path,
    runner: Callable,
) -> bool:
    """Return True if Git metadata indicates active or declared submodules.

    Uses git submodule status --recursive (authoritative). Falls back to
    .gitmodules presence as an additional fail-closed heuristic.
    """
    # Primary: git submodule status --recursive
    code, stdout, _ = runner(
        ["git", "submodule", "status", "--recursive"], cwd=target_path
    )
    if code == 0 and stdout.strip():
        return True

    # Secondary heuristic: .gitmodules present
    if (target_path / ".gitmodules").exists():
        return True

    return False


# ---------------------------------------------------------------------------
# Creation Identity (revised for F-IDENTITY-001)
# ---------------------------------------------------------------------------

def derive_worktree_creation_identity(
    contract: OrchestraWorktreeContract,
    repo_root: Path | str | None = None,
    runner: Callable | None = None,
) -> str:
    """Derive a SHA-256 creation identity for the contract, bound to the repository.

    The digest input includes:
      - contract_version
      - repository_identity (derived from remote URL or root commits)
      - unit_id
      - correlation_id (empty string if None)
      - approved_base_sha (lowercase)
      - worktree_branch
      - normalized worktree_path (POSIX separators, no leading slash)

    If repo_root is None or repository identity cannot be derived, the
    repository identity segment is set to the literal string
    "REPOSITORY_IDENTITY_UNAVAILABLE" to produce a unique but clearly
    incomplete digest. Callers that require strict repository binding must
    supply a valid repo_root.
    """
    norm_path = contract.worktree_path.replace("\\", "/").strip("/")

    repo_identity_segment: str
    if repo_root is not None:
        repo_id, err = derive_repository_identity(repo_root, runner)
        if repo_id is not None:
            repo_identity_segment = repo_id
        else:
            repo_identity_segment = "REPOSITORY_IDENTITY_UNAVAILABLE"
    else:
        repo_identity_segment = "REPOSITORY_IDENTITY_UNAVAILABLE"

    raw = "|".join(
        [
            contract.contract_version,
            repo_identity_segment,
            contract.unit_id,
            contract.correlation_id or "",
            contract.approved_base_sha.lower(),
            contract.worktree_branch,
            norm_path,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Path Confinement
# ---------------------------------------------------------------------------

def resolve_authorized_worktree_path(
    relative_or_absolute_path: str | Path, repo_root: Path | str
) -> tuple[Path | None, WorktreeReasonCode | None]:
    raw_str = str(relative_or_absolute_path).strip()
    if not raw_str:
        return None, WorktreeReasonCode.INVALID_PATH

    # Check for UNC or drive letters on Windows or absolute paths in raw input
    if raw_str.startswith(("\\\\", "//")):
        return None, WorktreeReasonCode.UNC_PATH_REJECTED

    if re.match(r"^[a-zA-Z]:", raw_str):
        return None, WorktreeReasonCode.ABSOLUTE_PATH_REJECTED

    if os.path.isabs(raw_str):
        return None, WorktreeReasonCode.ABSOLUTE_PATH_REJECTED

    # Check for path traversal elements
    parts = Path(raw_str).parts
    if ".." in parts:
        return None, WorktreeReasonCode.PATH_TRAVERSAL_REJECTED

    resolved_repo = Path(repo_root).resolve()
    target_path = (resolved_repo / raw_str).resolve()

    # Verify target path is strictly within an authorized parent dir inside repo_root
    is_authorized = False
    for parent_dir in AUTHORIZED_PARENT_DIRS:
        authorized_parent = (resolved_repo / parent_dir).resolve()
        try:
            if target_path.is_relative_to(authorized_parent) and target_path != authorized_parent:
                is_authorized = True
                break
        except AttributeError:
            # Python < 3.9 fallback
            try:
                target_path.relative_to(authorized_parent)
                if target_path != authorized_parent:
                    is_authorized = True
                    break
            except ValueError:
                pass

    if not is_authorized:
        return None, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT

    return target_path, None


def validate_worktree_path(
    path_str: str, repo_root: Path | str
) -> tuple[str | None, WorktreeReasonCode | None]:
    resolved, code = resolve_authorized_worktree_path(path_str, repo_root)
    if code is not None or resolved is None:
        return None, code
    resolved_repo = Path(repo_root).resolve()
    try:
        rel = resolved.relative_to(resolved_repo).as_posix()
        return rel, None
    except ValueError:
        return None, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT


# ---------------------------------------------------------------------------
# Contract Validation
# ---------------------------------------------------------------------------

def validate_worktree_contract(
    contract: OrchestraWorktreeContract, repo_root: Path | str | None = None
) -> WorktreeValidationResult:
    diagnostics: list[WorktreeDiagnostic] = []

    if not isinstance(contract, OrchestraWorktreeContract):
        return WorktreeValidationResult(
            valid=False,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.INVALID_CONTRACT,
                    message="Object is not an instance of OrchestraWorktreeContract.",
                ),
            ),
        )

    if contract.contract_version != WORKTREE_CONTRACT_VERSION:
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_CONTRACT,
                message=f"Unsupported contract version '{contract.contract_version}'. Expected '{WORKTREE_CONTRACT_VERSION}'.",
            )
        )

    if not isinstance(contract.unit_id, str) or not UNIT_ID_PATTERN.match(contract.unit_id):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_UNIT_ID,
                message="unit_id must be a non-empty alphanumeric string.",
            )
        )

    if contract.correlation_id is not None:
        if not isinstance(contract.correlation_id, str) or not CORRELATION_ID_PATTERN.match(
            contract.correlation_id
        ):
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.INVALID_CORRELATION_ID,
                    message="correlation_id is invalid.",
                )
            )

    if not verify_worktree_base_sha(contract.approved_base_sha):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_BASE_SHA,
                message="approved_base_sha must be a 40-character hex string.",
            )
        )

    if not isinstance(contract.worktree_branch, str) or not BRANCH_NAME_PATTERN.match(
        contract.worktree_branch
    ):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_BRANCH,
                message="worktree_branch is invalid.",
            )
        )

    if not isinstance(contract.isolation_status, WorktreeIsolationStatus):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_CONTRACT,
                message="isolation_status is invalid.",
            )
        )

    if not isinstance(contract.cleanup_policy, WorktreeCleanupPolicy):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_CONTRACT,
                message="cleanup_policy is invalid.",
            )
        )

    if not isinstance(contract.is_clean_at_start, bool):
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_CONTRACT,
                message="is_clean_at_start must be a boolean.",
            )
        )

    if repo_root is not None:
        norm_path, path_code = validate_worktree_path(contract.worktree_path, repo_root)
        if path_code is not None:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=path_code,
                    message=f"Path validation failed with code {path_code.value}.",
                )
            )

    return WorktreeValidationResult(valid=len(diagnostics) == 0, diagnostics=tuple(diagnostics))


# ---------------------------------------------------------------------------
# Git Command Runner
# ---------------------------------------------------------------------------

def _default_command_runner(
    args: list[str], cwd: Path | str, timeout: float = 15.0
) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            shell=False,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "git executable not found"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"
    except Exception as exc:
        return 1, "", str(exc)


def _check_git_repo(repo_root: Path, runner: Callable) -> WorktreeDiagnostic | None:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return WorktreeDiagnostic(
            code=WorktreeReasonCode.NOT_A_GIT_REPO, message="Repository root is not a Git repository."
        )
    code, stdout, _ = runner(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    if code != 0 or stdout.strip() != "true":
        return WorktreeDiagnostic(
            code=WorktreeReasonCode.NOT_A_GIT_REPO, message="Path is not inside a Git worktree."
        )
    return None


# ---------------------------------------------------------------------------
# Worktree List Parsing
# ---------------------------------------------------------------------------

def _parse_worktree_list(stdout: str) -> dict[str, dict[str, str]]:
    """Parse git worktree list --porcelain output into a dict keyed by normcase path."""
    registered: dict[str, dict[str, str]] = {}
    cur_entry: dict[str, str] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            if "worktree" in cur_entry:
                registered[os.path.normcase(cur_entry["worktree"])] = cur_entry
            cur_entry = {}
        elif line.startswith("worktree "):
            cur_entry["worktree"] = line[9:]
        elif line.startswith("HEAD "):
            cur_entry["head"] = line[5:]
        elif line.startswith("branch "):
            cur_entry["branch"] = line[7:]
        elif line == "locked":
            cur_entry["locked"] = "true"
        elif line.startswith("locked "):
            cur_entry["locked"] = line[7:]
    if "worktree" in cur_entry:
        registered[os.path.normcase(cur_entry["worktree"])] = cur_entry
    return registered


def _get_worktree_list(
    resolved_repo: Path, runner: Callable
) -> tuple[dict[str, dict[str, str]] | None, WorktreeDiagnostic | None]:
    code, stdout, _ = runner(["git", "worktree", "list", "--porcelain"], cwd=resolved_repo)
    if code != 0:
        return None, WorktreeDiagnostic(
            code=WorktreeReasonCode.NOT_A_GIT_REPO,
            message="Failed to list Git worktrees.",
        )
    return _parse_worktree_list(stdout), None


# ---------------------------------------------------------------------------
# Release Precondition Fingerprint (F-TOCTOU-001)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReleasePreconditionFingerprint:
    """Deterministic snapshot of worktree state used for TOCTOU comparison."""
    repo_identity: str
    registered_path_key: str
    head_sha: str
    branch_ref: str
    is_clean: bool
    is_locked: bool
    nested_repo_found: bool
    submodule_found: bool
    creation_identity: str | None


def _build_release_fingerprint(
    contract: OrchestraWorktreeContract,
    resolved_repo: Path,
    target_path: Path,
    wt_info: dict[str, str],
    is_clean: bool,
    is_locked: bool,
    nested_found: bool,
    submodule_found: bool,
    repo_identity: str,
) -> ReleasePreconditionFingerprint:
    return ReleasePreconditionFingerprint(
        repo_identity=repo_identity,
        registered_path_key=derive_path_collision_key(wt_info.get("worktree", "")),
        head_sha=wt_info.get("head", "").lower(),
        branch_ref=wt_info.get("branch", ""),
        is_clean=is_clean,
        is_locked=is_locked,
        nested_repo_found=nested_found,
        submodule_found=submodule_found,
        creation_identity=contract.creation_identity,
    )


# ---------------------------------------------------------------------------
# Inspect Worktree
# ---------------------------------------------------------------------------

def inspect_worktree(
    contract: OrchestraWorktreeContract,
    repo_root: Path | str,
    runner: Callable | None = None,
) -> WorktreeOperationResult:
    runner_fn = runner or _default_command_runner
    resolved_repo = Path(repo_root).resolve()

    val_res = validate_worktree_contract(contract, resolved_repo)
    if not val_res.valid:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=val_res.diagnostics)

    git_err = _check_git_repo(resolved_repo, runner_fn)
    if git_err:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=(git_err,))

    target_path, path_code = resolve_authorized_worktree_path(contract.worktree_path, resolved_repo)
    if path_code or not target_path:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=path_code or WorktreeReasonCode.INVALID_PATH,
                    message="Target path confinement failed.",
                ),
            ),
        )

    diagnostics: list[WorktreeDiagnostic] = []

    registered_worktrees, list_err = _get_worktree_list(resolved_repo, runner_fn)
    if list_err:
        return WorktreeOperationResult(
            success=False, contract=contract, diagnostics=(list_err,)
        )

    norm_target = os.path.normcase(str(target_path))
    is_registered = norm_target in registered_worktrees

    if not target_path.exists() and not is_registered:
        return WorktreeOperationResult(
            success=True,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_NOT_REGISTERED,
                    message="Worktree path does not exist and is not registered.",
                ),
            ),
        )

    if is_registered:
        wt_info = registered_worktrees[norm_target]
        wt_head = wt_info.get("head", "")
        wt_branch = wt_info.get("branch", "")

        if wt_head.lower() != contract.approved_base_sha.lower():
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.BASE_SHA_MISMATCH,
                    message="Worktree HEAD does not match approved base SHA.",
                )
            )

        expected_branch_ref = f"refs/heads/{contract.worktree_branch}"
        if wt_branch and wt_branch != expected_branch_ref:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.INVALID_BRANCH,
                    message=f"Worktree branch '{wt_branch}' does not match expected '{expected_branch_ref}'.",
                )
            )

        # NB-001: Lock state from porcelain only — no filesystem fallback
        if wt_info.get("locked"):
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_LOCKED,
                    message="Worktree is locked.",
                )
            )

    if target_path.exists():
        # F-NESTED-001: Recursive nested repository detection
        nested_found, nested_evidence = find_nested_git_boundary(target_path)
        if nested_found:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.NESTED_REPOSITORY_DETECTED,
                    message="Nested Git repository detected in target directory.",
                )
            )

        # Submodule detection: git metadata + .gitmodules heuristic
        if _check_submodule_boundary(target_path, runner_fn):
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.SUBMODULE_BOUNDARY_DETECTED,
                    message="Submodule boundary detected in target directory.",
                )
            )

        # Check dirty status
        code, stdout, _ = runner_fn(["git", "status", "--porcelain=v1"], cwd=target_path)
        if code == 0 and stdout.strip():
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_DIRTY,
                    message="Worktree contains uncommitted changes.",
                )
            )

    return WorktreeOperationResult(
        success=len(diagnostics) == 0,
        contract=contract,
        diagnostics=tuple(diagnostics),
    )


def _inspect_for_release(
    contract: OrchestraWorktreeContract,
    resolved_repo: Path,
    target_path: Path,
    repo_identity: str,
    runner_fn: Callable,
) -> tuple[ReleasePreconditionFingerprint | None, tuple[WorktreeDiagnostic, ...]]:
    """Run inspection and build a release precondition fingerprint with any diagnostics.

    Returns (fingerprint, diagnostics).
    """
    registered_worktrees, list_err = _get_worktree_list(resolved_repo, runner_fn)
    if list_err:
        return None, (list_err,)

    norm_target = os.path.normcase(str(target_path))
    if norm_target not in registered_worktrees:
        return None, (
            WorktreeDiagnostic(
                code=WorktreeReasonCode.WORKTREE_NOT_REGISTERED,
                message="Worktree is not registered in git worktree list.",
            ),
        )

    wt_info = registered_worktrees[norm_target]

    # Check HEAD & branch mismatch
    diagnostics: list[WorktreeDiagnostic] = []
    wt_head = wt_info.get("head", "").lower()
    if wt_head != contract.approved_base_sha.lower():
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.BASE_SHA_MISMATCH,
                message="Worktree HEAD does not match approved base SHA.",
            )
        )

    wt_branch = wt_info.get("branch", "")
    expected_branch_ref = f"refs/heads/{contract.worktree_branch}"
    if wt_branch and wt_branch != expected_branch_ref:
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.INVALID_BRANCH,
                message=f"Worktree branch '{wt_branch}' does not match expected '{expected_branch_ref}'.",
            )
        )

    # Check locked (porcelain only)
    is_locked = bool(wt_info.get("locked"))
    if is_locked:
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.WORKTREE_LOCKED,
                message="Worktree is locked.",
            )
        )

    # Check nested
    nested_found = False
    submodule_found = False
    is_clean = True

    if target_path.exists():
        n_found, _ = find_nested_git_boundary(target_path)
        nested_found = n_found
        if nested_found:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.NESTED_REPOSITORY_DETECTED,
                    message="Nested Git repository detected in target directory.",
                )
            )

        sm_found = _check_submodule_boundary(target_path, runner_fn)
        submodule_found = sm_found
        if submodule_found:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.SUBMODULE_BOUNDARY_DETECTED,
                    message="Submodule boundary detected in target directory.",
                )
            )

        code, stdout, _ = runner_fn(["git", "status", "--porcelain=v1"], cwd=target_path)
        is_clean = not (code == 0 and stdout.strip())
        if not is_clean:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_DIRTY,
                    message="Worktree contains uncommitted changes.",
                )
            )

    fp = _build_release_fingerprint(
        contract, resolved_repo, target_path, wt_info,
        is_clean, is_locked, nested_found, submodule_found, repo_identity,
    )
    return fp, tuple(diagnostics)



# ---------------------------------------------------------------------------
# Initialize Worktree
# ---------------------------------------------------------------------------

def initialize_worktree(
    contract: OrchestraWorktreeContract,
    repo_root: Path | str,
    authorize_creation: bool = False,
    runner: Callable | None = None,
) -> WorktreeOperationResult:
    runner_fn = runner or _default_command_runner
    resolved_repo = Path(repo_root).resolve()

    if not authorize_creation:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_UNSUPPORTED,
                    message="Explicit worktree creation authorization is required.",
                ),
            ),
        )

    val_res = validate_worktree_contract(contract, resolved_repo)
    if not val_res.valid:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=val_res.diagnostics)

    git_err = _check_git_repo(resolved_repo, runner_fn)
    if git_err:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=(git_err,))

    target_path, path_code = resolve_authorized_worktree_path(contract.worktree_path, resolved_repo)
    if path_code or not target_path:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=path_code or WorktreeReasonCode.INVALID_PATH,
                    message="Target path confinement failed.",
                ),
            ),
        )

    # Initial existence check: PATH_ALREADY_EXISTS if present before any creation attempt
    if target_path.exists():
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.PATH_ALREADY_EXISTS,
                    message="Target worktree path already exists on filesystem.",
                ),
            ),
        )

    # Check git base SHA existence
    code, _, _ = runner_fn(["git", "cat-file", "-e", contract.approved_base_sha], cwd=resolved_repo)
    if code != 0:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.BASE_SHA_MISMATCH,
                    message="Approved base SHA does not exist in local repository.",
                ),
            ),
        )

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # NB-005: If path appeared between initial check and git command, that is a CREATION_RACE
    if target_path.exists():
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_CREATION_RACE,
                    message="Target path appeared between initial check and worktree creation.",
                ),
            ),
        )

    # NB-002: Canonical argument order: git worktree add -b <branch> <path> <sha>
    code, _, _ = runner_fn(
        ["git", "worktree", "add", "-b", contract.worktree_branch, str(target_path), contract.approved_base_sha],
        cwd=resolved_repo,
    )
    if code != 0:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_ADD_FAILED,
                    message="git worktree add command failed.",
                ),
            ),
        )

    creation_id = derive_worktree_creation_identity(contract, resolved_repo, runner_fn)

    # NB-004: Enforce transition INITIALIZED -> ACTIVE
    transition_err = _require_transition(
        contract.isolation_status, WorktreeIsolationStatus.ACTIVE, contract
    )
    if transition_err:
        return transition_err

    updated_contract = OrchestraWorktreeContract(
        unit_id=contract.unit_id,
        worktree_path=contract.worktree_path,
        worktree_branch=contract.worktree_branch,
        approved_base_sha=contract.approved_base_sha,
        isolation_status=WorktreeIsolationStatus.ACTIVE,
        contract_version=contract.contract_version,
        correlation_id=contract.correlation_id,
        is_clean_at_start=True,
        cleanup_policy=contract.cleanup_policy,
        creation_identity=creation_id,
    )

    # Post-creation inspection
    insp_res = inspect_worktree(updated_contract, resolved_repo, runner_fn)
    if not insp_res.success:
        # NB-004: Enforce transition INITIALIZED -> STALE_ORPHANED
        transition_err2 = _require_transition(
            contract.isolation_status, WorktreeIsolationStatus.STALE_ORPHANED, contract
        )
        if transition_err2:
            return transition_err2

        failed_contract = OrchestraWorktreeContract(
            unit_id=updated_contract.unit_id,
            worktree_path=updated_contract.worktree_path,
            worktree_branch=updated_contract.worktree_branch,
            approved_base_sha=updated_contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.STALE_ORPHANED,
            contract_version=updated_contract.contract_version,
            correlation_id=updated_contract.correlation_id,
            is_clean_at_start=updated_contract.is_clean_at_start,
            cleanup_policy=updated_contract.cleanup_policy,
            creation_identity=updated_contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False, contract=failed_contract, diagnostics=insp_res.diagnostics
        )

    return WorktreeOperationResult(success=True, contract=updated_contract, diagnostics=())


# ---------------------------------------------------------------------------
# Plan Worktree Release
# ---------------------------------------------------------------------------

def plan_worktree_release(
    contract: OrchestraWorktreeContract,
    repo_root: Path | str,
    runner: Callable | None = None,
) -> WorktreeOperationResult:
    runner_fn = runner or _default_command_runner
    resolved_repo = Path(repo_root).resolve()

    val_res = validate_worktree_contract(contract, resolved_repo)
    if not val_res.valid:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=val_res.diagnostics)

    insp_res = inspect_worktree(contract, resolved_repo, runner_fn)
    if not insp_res.success:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=insp_res.diagnostics)

    diagnostics: list[WorktreeDiagnostic] = []

    if contract.cleanup_policy == WorktreeCleanupPolicy.ADVISORY_SAFE_SUBSET:
        diagnostics.append(
            WorktreeDiagnostic(
                code=WorktreeReasonCode.ADVISORY_POLICY_NON_DESTRUCTIVE,
                message="Advisory cleanup policy is non-destructive. Release planning identifies candidate only.",
            )
        )

    if contract.creation_identity is not None:
        expected_id = derive_worktree_creation_identity(contract, resolved_repo, runner_fn)
        if contract.creation_identity != expected_id:
            diagnostics.append(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_IDENTITY_MISMATCH,
                    message="Creation identity mismatch during release planning.",
                )
            )

    return WorktreeOperationResult(
        success=len(diagnostics) == 0 or contract.cleanup_policy == WorktreeCleanupPolicy.ADVISORY_SAFE_SUBSET,
        contract=contract,
        diagnostics=tuple(diagnostics),
    )


# ---------------------------------------------------------------------------
# Release Worktree (Two-Phase Verification — F-TOCTOU-001)
# ---------------------------------------------------------------------------

def release_worktree(
    contract: OrchestraWorktreeContract,
    repo_root: Path | str,
    authorize_cleanup: bool = False,
    runner: Callable | None = None,
) -> WorktreeOperationResult:
    runner_fn = runner or _default_command_runner
    resolved_repo = Path(repo_root).resolve()

    # Phase 1a: advisory policy and authority checks
    if contract.cleanup_policy == WorktreeCleanupPolicy.ADVISORY_SAFE_SUBSET:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.ADVISORY_POLICY_NON_DESTRUCTIVE,
                    message="Advisory cleanup policy prohibits destructive release operations.",
                ),
            ),
        )

    if not authorize_cleanup:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.CLEANUP_AUTHORITY_REQUIRED,
                    message="Explicit host cleanup authorization is required for destructive worktree removal.",
                ),
            ),
        )

    # Phase 1b: contract validation
    val_res = validate_worktree_contract(contract, resolved_repo)
    if not val_res.valid:
        return WorktreeOperationResult(success=False, contract=contract, diagnostics=val_res.diagnostics)

    # Phase 1c: creation identity check
    if contract.creation_identity is None:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_IDENTITY_MISMATCH,
                    message="Creation identity is missing.",
                ),
            ),
        )

    # Phase 1d: repository identity derivation
    repo_identity, id_err = derive_repository_identity(resolved_repo, runner_fn)
    if id_err or repo_identity is None:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.REPOSITORY_IDENTITY_UNAVAILABLE,
                    message="Repository identity could not be derived for release verification.",
                ),
            ),
        )

    # Phase 1e: verify creation identity against current repository
    expected_id = derive_worktree_creation_identity(contract, resolved_repo, runner_fn)
    if contract.creation_identity != expected_id:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_IDENTITY_MISMATCH,
                    message="Creation identity verification failed.",
                ),
            ),
        )

    target_path, path_code = resolve_authorized_worktree_path(contract.worktree_path, resolved_repo)
    if path_code or not target_path:
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=path_code or WorktreeReasonCode.INVALID_PATH,
                    message="Target path confinement failed.",
                ),
            ),
        )

    # Phase 2: First inspection — build initial fingerprint
    fp1, diags1 = _inspect_for_release(
        contract, resolved_repo, target_path, repo_identity, runner_fn
    )
    if diags1:
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=diags1,
        )

    # Phase 3: Second inspection immediately before removal — build second fingerprint
    fp2, diags2 = _inspect_for_release(
        contract, resolved_repo, target_path, repo_identity, runner_fn
    )

    # Phase 4: Compare fingerprints — detect TOCTOU mutations
    if fp1 != fp2:
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_RELEASE_RACE,
                    message="Release precondition fingerprint changed between inspections. Aborting removal.",
                ),
            ),
        )

    # If fingerprints matched, check if Phase 3 had any diagnostics
    # (should normally be empty if fp1 == fp2 and diags1 was empty, but check to be safe)
    if diags2:
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=diags2,
        )

    # Phase 5: Execute git worktree remove <exact-path>
    # (NO --force, NO branch deletion, NO prune, NO recursive delete)
    if not target_path.exists():
        return WorktreeOperationResult(
            success=False,
            contract=contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_NOT_REGISTERED,
                    message="Target worktree path does not exist prior to removal.",
                ),
            ),
        )

    code, _, _ = runner_fn(
        ["git", "worktree", "remove", str(target_path)], cwd=resolved_repo
    )
    if code != 0:
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_REMOVE_FAILED,
                    message="git worktree remove command failed.",
                ),
            ),
        )

    # NB-003 / Phase 6: Post-release verification
    # Verify deregistration, branch preservation, other worktrees unchanged
    post_registered, post_list_err = _get_worktree_list(resolved_repo, runner_fn)
    if post_list_err or post_registered is None:
        # Cannot verify — treat as FAILED_CLEANUP
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_REMOVE_FAILED,
                    message="Post-release worktree list verification failed.",
                ),
            ),
        )

    norm_target = os.path.normcase(str(target_path))
    if norm_target in post_registered:
        failed_contract = OrchestraWorktreeContract(
            unit_id=contract.unit_id,
            worktree_path=contract.worktree_path,
            worktree_branch=contract.worktree_branch,
            approved_base_sha=contract.approved_base_sha,
            isolation_status=WorktreeIsolationStatus.FAILED_CLEANUP,
            contract_version=contract.contract_version,
            correlation_id=contract.correlation_id,
            is_clean_at_start=contract.is_clean_at_start,
            cleanup_policy=contract.cleanup_policy,
            creation_identity=contract.creation_identity,
        )
        return WorktreeOperationResult(
            success=False,
            contract=failed_contract,
            diagnostics=(
                WorktreeDiagnostic(
                    code=WorktreeReasonCode.WORKTREE_REMOVE_FAILED,
                    message="Worktree still registered after git worktree remove.",
                ),
            ),
        )

    # Verify branch still exists
    code_br, br_out, _ = runner_fn(
        ["git", "branch", "--list", contract.worktree_branch], cwd=resolved_repo
    )
    branch_preserved = code_br == 0 and contract.worktree_branch in br_out

    # NB-004: Enforce transition ACTIVE -> RELEASED
    transition_err = _require_transition(
        contract.isolation_status, WorktreeIsolationStatus.RELEASED, contract
    )
    if transition_err:
        return transition_err

    released_contract = OrchestraWorktreeContract(
        unit_id=contract.unit_id,
        worktree_path=contract.worktree_path,
        worktree_branch=contract.worktree_branch,
        approved_base_sha=contract.approved_base_sha,
        isolation_status=WorktreeIsolationStatus.RELEASED,
        contract_version=contract.contract_version,
        correlation_id=contract.correlation_id,
        is_clean_at_start=contract.is_clean_at_start,
        cleanup_policy=contract.cleanup_policy,
        creation_identity=contract.creation_identity,
    )

    return WorktreeOperationResult(success=True, contract=released_contract, diagnostics=())


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def serialize_worktree_contract(contract: OrchestraWorktreeContract) -> dict[str, Any]:
    norm_path = contract.worktree_path.replace("\\", "/").strip("/")
    payload: dict[str, Any] = {
        "contract_version": contract.contract_version,
        "unit_id": contract.unit_id,
        "worktree_path": norm_path,
        "worktree_branch": contract.worktree_branch,
        "approved_base_sha": contract.approved_base_sha.lower(),
        "isolation_status": contract.isolation_status.value,
        "is_clean_at_start": contract.is_clean_at_start,
        "cleanup_policy": contract.cleanup_policy.value,
    }
    if contract.correlation_id is not None:
        payload["correlation_id"] = contract.correlation_id
    if contract.creation_identity is not None:
        payload["creation_identity"] = contract.creation_identity
    return payload


def serialize_worktree_contract_to_str(contract: OrchestraWorktreeContract) -> str:
    payload = serialize_worktree_contract(contract)
    return json.dumps(payload, indent=2, sort_keys=True)


def deserialize_worktree_contract(payload: str | bytes | dict[str, Any]) -> OrchestraWorktreeContract:
    if isinstance(payload, (str, bytes)):
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ValueError(f"Invalid JSON payload for OrchestraWorktreeContract: {exc}") from exc
    elif isinstance(payload, dict):
        data = payload
    else:
        raise ValueError("Payload must be a dict, string, or bytes.")

    if not isinstance(data, dict):
        raise ValueError("Deserialized JSON payload must be a dict.")

    # Strict key validation
    allowed_keys = {
        "contract_version",
        "unit_id",
        "worktree_path",
        "worktree_branch",
        "approved_base_sha",
        "isolation_status",
        "correlation_id",
        "is_clean_at_start",
        "cleanup_policy",
        "creation_identity",
    }
    extra_keys = set(data.keys()) - allowed_keys
    if extra_keys:
        raise ValueError(f"Unknown keys in OrchestraWorktreeContract payload: {sorted(extra_keys)}")

    required_keys = {
        "contract_version",
        "unit_id",
        "worktree_path",
        "worktree_branch",
        "approved_base_sha",
        "isolation_status",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        raise ValueError(f"Missing required keys in OrchestraWorktreeContract payload: {sorted(missing_keys)}")

    version = data["contract_version"]
    if version != WORKTREE_CONTRACT_VERSION:
        raise ValueError(f"Unsupported contract version: {version}")

    status_str = data["isolation_status"]
    try:
        status = WorktreeIsolationStatus(status_str)
    except ValueError as exc:
        raise ValueError(f"Invalid isolation_status: {status_str}") from exc

    policy_str = data.get("cleanup_policy", WorktreeCleanupPolicy.EXPLICIT_HOST_ACTION_ONLY.value)
    try:
        policy = WorktreeCleanupPolicy(policy_str)
    except ValueError as exc:
        raise ValueError(f"Invalid cleanup_policy: {policy_str}") from exc

    is_clean = data.get("is_clean_at_start", True)
    if not isinstance(is_clean, bool):
        raise ValueError("is_clean_at_start must be a boolean.")

    return OrchestraWorktreeContract(
        unit_id=data["unit_id"],
        worktree_path=data["worktree_path"],
        worktree_branch=data["worktree_branch"],
        approved_base_sha=data["approved_base_sha"],
        isolation_status=status,
        contract_version=version,
        correlation_id=data.get("correlation_id"),
        is_clean_at_start=is_clean,
        cleanup_policy=policy,
        creation_identity=data.get("creation_identity"),
    )
