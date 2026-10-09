"""OrchestraStatusProjection runtime model, collector, serializer, renderer, and CLI.

Provides a strictly read-only, derived, deterministic, fail-closed status surface
unifying live Git facts, canonical project facts, contract implementation status,
and revision-matched validation evidence.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Optional, Sequence

STATUS_PROJECTION_VERSION = "1.0"
VALID_DIAGNOSTIC_SEVERITIES = ("UNKNOWN", "CONFLICT", "WARNING")
VALID_KNOWN_FIELD_PREFIXES = ("git.", "project.", "contracts.", "validation.")


def _validate_bool(name: str, value: Any, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool, got {type(value).__name__}")


def _validate_non_negative_int(name: str, value: Any, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def _validate_string(name: str, value: Any, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{name} cannot be empty")


def _validate_sha(name: str, value: Any, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str, got {type(value).__name__}")
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", value):
        raise ValueError(f"{name} must be a valid hex SHA (7-64 chars), got {value!r}")


def _normalize_string_tuple(name: str, raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        raise TypeError(f"{name} must be a sequence of str, got str")
    if not isinstance(raw, (tuple, list)):
        raise TypeError(f"{name} must be a tuple or list of str, got {type(raw).__name__}")
    res: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Items in {name} must be non-empty strings, got {item!r}")
        if item not in res:
            res.append(item)
    return tuple(sorted(res))


@dataclass(frozen=True)
class StatusDiagnostic:
    severity: str
    message: str
    field_path: Optional[str] = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_DIAGNOSTIC_SEVERITIES:
            raise ValueError(
                f"severity must be one of {VALID_DIAGNOSTIC_SEVERITIES}, got {self.severity!r}"
            )
        _validate_string("message", self.message, nullable=False)
        _validate_string("field_path", self.field_path, nullable=True)


@dataclass(frozen=True)
class GitStatus:
    is_git_repo: bool
    current_branch: Optional[str] = None
    head_sha: Optional[str] = None
    is_clean: Optional[bool] = None
    staged_count: Optional[int] = None
    modified_count: Optional[int] = None
    untracked_count: Optional[int] = None
    ahead_count: Optional[int] = None
    behind_count: Optional[int] = None
    selected_remote: Optional[str] = None
    selected_main_ref: Optional[str] = None
    selected_main_sha: Optional[str] = None
    remote_names: tuple[str, ...] = ()
    is_shallow: Optional[bool] = None
    is_worktree: Optional[bool] = None
    worktree_path_redacted: Optional[str] = None

    def __post_init__(self) -> None:
        _validate_bool("is_git_repo", self.is_git_repo, nullable=False)
        _validate_string("current_branch", self.current_branch, nullable=True)
        _validate_sha("head_sha", self.head_sha, nullable=True)
        _validate_bool("is_clean", self.is_clean, nullable=True)
        _validate_non_negative_int("staged_count", self.staged_count, nullable=True)
        _validate_non_negative_int("modified_count", self.modified_count, nullable=True)
        _validate_non_negative_int("untracked_count", self.untracked_count, nullable=True)
        _validate_non_negative_int("ahead_count", self.ahead_count, nullable=True)
        _validate_non_negative_int("behind_count", self.behind_count, nullable=True)
        _validate_string("selected_remote", self.selected_remote, nullable=True)
        _validate_string("selected_main_ref", self.selected_main_ref, nullable=True)
        _validate_sha("selected_main_sha", self.selected_main_sha, nullable=True)

        norm_remotes = _normalize_string_tuple("remote_names", self.remote_names)
        object.__setattr__(self, "remote_names", norm_remotes)

        _validate_bool("is_shallow", self.is_shallow, nullable=True)
        _validate_bool("is_worktree", self.is_worktree, nullable=True)
        _validate_string("worktree_path_redacted", self.worktree_path_redacted, nullable=True)

        if self.selected_remote and norm_remotes and self.selected_remote not in norm_remotes:
            raise ValueError(
                f"selected_remote {self.selected_remote!r} must be in remote_names {norm_remotes}"
            )
        if self.selected_main_ref and not self.selected_remote:
            raise ValueError("selected_main_ref cannot exist without selected_remote")
        if (
            self.is_clean is not None
            and self.staged_count is not None
            and self.modified_count is not None
            and self.untracked_count is not None
        ):
            calc_clean = (
                self.staged_count == 0
                and self.modified_count == 0
                and self.untracked_count == 0
            )
            if self.is_clean != calc_clean:
                raise ValueError(
                    f"is_clean ({self.is_clean}) does not match count sums (calculated {calc_clean})"
                )


@dataclass(frozen=True)
class ProjectStatus:
    current_release: Optional[str] = None
    active_phase: Optional[str] = None
    policy_integrated: Optional[bool] = None

    def __post_init__(self) -> None:
        _validate_string("current_release", self.current_release, nullable=True)
        _validate_string("active_phase", self.active_phase, nullable=True)
        _validate_bool("policy_integrated", self.policy_integrated, nullable=True)


@dataclass(frozen=True)
class ContractStatus:
    runtime_envelope: Optional[str] = None
    correlation_id: Optional[str] = None
    phase_retrospective: Optional[str] = None
    approved_unit_plan_extension: Optional[str] = None
    worktree_contract: Optional[str] = None
    status_projection: Optional[str] = None

    def __post_init__(self) -> None:
        for f_name in (
            "runtime_envelope",
            "correlation_id",
            "phase_retrospective",
            "approved_unit_plan_extension",
            "worktree_contract",
            "status_projection",
        ):
            _validate_string(f_name, getattr(self, f_name), nullable=True)


@dataclass(frozen=True)
class ValidationStatus:
    evidence_revision: Optional[str] = None
    revision_match: Optional[bool] = None
    governance_check: Optional[str] = None
    preflight_sync: Optional[str] = None
    runtime_test_count: Optional[int] = None
    runtime_coverage: Optional[str] = None

    def __post_init__(self) -> None:
        _validate_sha("evidence_revision", self.evidence_revision, nullable=True)
        _validate_bool("revision_match", self.revision_match, nullable=True)
        _validate_string("governance_check", self.governance_check, nullable=True)
        _validate_string("preflight_sync", self.preflight_sync, nullable=True)
        _validate_non_negative_int("runtime_test_count", self.runtime_test_count, nullable=True)
        _validate_string("runtime_coverage", self.runtime_coverage, nullable=True)

        if self.runtime_coverage is not None:
            m = re.match(r"^(\d+(?:\.\d+)?)%?$", self.runtime_coverage.strip())
            if not m:
                raise ValueError(
                    f"runtime_coverage must be a valid percentage string, got {self.runtime_coverage!r}"
                )
            val = float(m.group(1))
            if val < 0.0 or val > 100.0:
                raise ValueError(
                    f"runtime_coverage percentage must be between 0 and 100, got {val}"
                )


@dataclass(frozen=True)
class DiagnosticsStatus:
    unknown_fields: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        norm_unk = _normalize_string_tuple("unknown_fields", self.unknown_fields)
        norm_conf = _normalize_string_tuple("conflicts", self.conflicts)
        norm_warn = _normalize_string_tuple("warnings", self.warnings)

        object.__setattr__(self, "unknown_fields", norm_unk)
        object.__setattr__(self, "conflicts", norm_conf)
        object.__setattr__(self, "warnings", norm_warn)


@dataclass(frozen=True)
class OrchestraStatusProjection:
    projection_version: str
    timestamp: str
    git: GitStatus
    project: ProjectStatus
    contracts: ContractStatus
    validation: ValidationStatus
    diagnostics: DiagnosticsStatus

    def __post_init__(self) -> None:
        if self.projection_version != STATUS_PROJECTION_VERSION:
            raise ValueError(
                f"projection_version must be {STATUS_PROJECTION_VERSION!r}, got {self.projection_version!r}"
            )
        _validate_string("timestamp", self.timestamp, nullable=False)

        try:
            if not (self.timestamp.endswith("Z") or "+00:00" in self.timestamp):
                raise ValueError("timestamp must be in UTC (end with Z or +00:00)")
            datetime.datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except Exception as err:
            raise ValueError(f"timestamp must be a valid ISO-8601 UTC string: {err}")

        if not isinstance(self.git, GitStatus):
            raise TypeError(f"git must be a GitStatus, got {type(self.git).__name__}")
        if not isinstance(self.project, ProjectStatus):
            raise TypeError(f"project must be a ProjectStatus, got {type(self.project).__name__}")
        if not isinstance(self.contracts, ContractStatus):
            raise TypeError(
                f"contracts must be a ContractStatus, got {type(self.contracts).__name__}"
            )
        if not isinstance(self.validation, ValidationStatus):
            raise TypeError(
                f"validation must be a ValidationStatus, got {type(self.validation).__name__}"
            )
        if not isinstance(self.diagnostics, DiagnosticsStatus):
            raise TypeError(
                f"diagnostics must be a DiagnosticsStatus, got {type(self.diagnostics).__name__}"
            )


CommandRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def default_command_runner(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
        encoding="utf-8",
        errors="replace",
    )


def redact_url_credentials(text: str) -> str:
    """Redact embedded credentials in URLs (e.g. https://user:token@github.com)."""
    return re.sub(r"https?://([^:@\s]+):([^@\s]+)@", "https://***:***@", text)


def _parse_porcelain_v1_z(raw_bytes: bytes) -> tuple[int, int, int, bool]:
    """Parse NUL-delimited porcelain v1 output into (staged, modified, untracked, is_clean)."""
    records = raw_bytes.split(b"\x00")
    staged = 0
    modified = 0
    untracked = 0

    idx = 0
    entry_count = 0
    while idx < len(records):
        entry = records[idx]
        if not entry:
            idx += 1
            continue

        entry_count += 1
        # Decode status code (first 2 bytes) safely
        if len(entry) >= 2:
            try:
                status_code = entry[:2].decode("ascii", errors="ignore")
                x, y = status_code[0], status_code[1]
                if x == "?":
                    untracked += 1
                else:
                    if x not in (" ", "?"):
                        staged += 1
                    if y not in (" ", "?"):
                        modified += 1

                # If entry represents rename (R) or copy (C), next NUL item is the target path
                if x in ("R", "C") or y in ("R", "C"):
                    idx += 1  # skip target path
            except Exception:
                pass
        idx += 1

    is_clean = (entry_count == 0)
    return staged, modified, untracked, is_clean


def collect_git_status(
    repo_path: Path,
    command_runner: Optional[CommandRunner] = None,
) -> tuple[GitStatus, list[str], list[str]]:
    runner = command_runner or default_command_runner
    warnings: list[str] = []
    unknown_fields: list[str] = []

    try:
        res = runner(["git", "rev-parse", "--is-inside-work-tree"], repo_path)
        if res.returncode != 0 or res.stdout.strip() != "true":
            return (
                GitStatus(is_git_repo=False),
                ["git.current_branch", "git.head_sha", "git.is_clean", "git.selected_remote"],
                [],
            )
    except (FileNotFoundError, PermissionError):
        warnings.append("Git executable unavailable or access denied.")
        return (
            GitStatus(is_git_repo=False),
            ["git.current_branch", "git.head_sha", "git.is_clean", "git.selected_remote"],
            warnings,
        )
    except subprocess.TimeoutExpired:
        warnings.append("Git command timed out checking repository status.")
        return (
            GitStatus(is_git_repo=False),
            ["git.current_branch", "git.head_sha", "git.is_clean", "git.selected_remote"],
            warnings,
        )

    # HEAD SHA and branch
    head_sha: Optional[str] = None
    current_branch: Optional[str] = None

    rev_res = runner(["git", "rev-parse", "HEAD"], repo_path)
    if rev_res.returncode == 0:
        head_sha = rev_res.stdout.strip()
    else:
        current_branch = "unborn"
        unknown_fields.append("git.head_sha")

    if current_branch is None:
        sym_res = runner(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], repo_path)
        if sym_res.returncode == 0:
            current_branch = sym_res.stdout.strip()
        else:
            if head_sha:
                short_sha = head_sha[:7]
                current_branch = f"(HEAD detached at {short_sha})"
            else:
                current_branch = "(unknown)"

    # Worktree check
    is_worktree: Optional[bool] = None
    worktree_path_redacted: Optional[str] = None
    c_dir_res = runner(["git", "rev-parse", "--git-common-dir"], repo_path)
    g_dir_res = runner(["git", "rev-parse", "--git-dir"], repo_path)
    if c_dir_res.returncode == 0 and g_dir_res.returncode == 0:
        c_dir = Path(c_dir_res.stdout.strip()).resolve()
        g_dir = Path(g_dir_res.stdout.strip()).resolve()
        if c_dir != g_dir:
            is_worktree = True
            worktree_path_redacted = f"[worktree: {current_branch}]"
        else:
            is_worktree = False

    # Shallow check
    is_shallow: Optional[bool] = None
    shal_res = runner(["git", "rev-parse", "--is-shallow-repository"], repo_path)
    if shal_res.returncode == 0:
        is_shallow = shal_res.stdout.strip() == "true"

    # Status porcelain -z (NUL-delimited safe parsing)
    staged_count: Optional[int] = None
    modified_count: Optional[int] = None
    untracked_count: Optional[int] = None
    is_clean: Optional[bool] = None

    stat_res = runner(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], repo_path)
    if stat_res.returncode == 0:
        raw_bytes = stat_res.stdout.encode("utf-8") if isinstance(stat_res.stdout, str) else stat_res.stdout
        staged_count, modified_count, untracked_count, is_clean = _parse_porcelain_v1_z(raw_bytes)

    # Remotes
    remote_names: tuple[str, ...] = ()
    rem_res = runner(["git", "remote"], repo_path)
    if rem_res.returncode == 0:
        rem_lines = [r.strip() for r in rem_res.stdout.splitlines() if r.strip()]
        remote_names = tuple(sorted(rem_lines))

    selected_remote: Optional[str] = None
    selected_main_ref: Optional[str] = None
    selected_main_sha: Optional[str] = None
    ahead_count: Optional[int] = None
    behind_count: Optional[int] = None

    if remote_names:
        if "origin" in remote_names:
            selected_remote = "origin"
        else:
            selected_remote = remote_names[0]

        ref_candidate = f"{selected_remote}/main"
        show_res = runner(["git", "rev-parse", "--verify", ref_candidate], repo_path)
        if show_res.returncode == 0:
            selected_main_ref = ref_candidate
            selected_main_sha = show_res.stdout.strip()

            if head_sha:
                counts_res = runner(
                    ["git", "rev-list", "--left-right", "--count", f"HEAD...{ref_candidate}"],
                    repo_path,
                )
                if counts_res.returncode == 0:
                    parts = counts_res.stdout.strip().split()
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        ahead_count = int(parts[0])
                        behind_count = int(parts[1])
        else:
            unknown_fields.extend(["git.selected_main_ref", "git.selected_main_sha"])
    else:
        unknown_fields.extend(["git.selected_remote", "git.selected_main_ref", "git.selected_main_sha"])

    if ahead_count is None:
        unknown_fields.extend(["git.ahead_count", "git.behind_count"])

    git_status = GitStatus(
        is_git_repo=True,
        current_branch=current_branch,
        head_sha=head_sha,
        is_clean=is_clean,
        staged_count=staged_count,
        modified_count=modified_count,
        untracked_count=untracked_count,
        ahead_count=ahead_count,
        behind_count=behind_count,
        selected_remote=selected_remote,
        selected_main_ref=selected_main_ref,
        selected_main_sha=selected_main_sha,
        remote_names=remote_names,
        is_shallow=is_shallow,
        is_worktree=is_worktree,
        worktree_path_redacted=worktree_path_redacted,
    )
    return git_status, unknown_fields, warnings


def collect_project_status(repo_path: Path) -> tuple[ProjectStatus, list[str], list[str]]:
    unknown_fields: list[str] = []
    conflicts: list[str] = []

    current_release: Optional[str] = None
    active_phase: Optional[str] = None
    policy_integrated: Optional[bool] = None

    state_file = repo_path / "PROJECT_STATE.md"
    if state_file.is_file():
        try:
            content = state_file.read_text(encoding="utf-8")
            rel_m = re.search(r"-\s*\*\*Current Public Release:\*\*\s*`([^`]+)`", content)
            if rel_m:
                current_release = rel_m.group(1).strip()
            task_m = re.search(r"-\s*\*\*Next Active Software Task:\*\*\s*(.+)", content)
            if task_m:
                active_phase = task_m.group(1).strip()
        except Exception:
            unknown_fields.extend(["project.current_release", "project.active_phase"])

    context_file = repo_path / "PROJECT_CONTEXT.md"
    if context_file.is_file():
        try:
            content = context_file.read_text(encoding="utf-8")
            if "DELEGATED_EXECUTION_POLICY.md" in content:
                policy_integrated = True
            else:
                policy_integrated = False
        except Exception:
            unknown_fields.append("project.policy_integrated")

    if current_release is None:
        unknown_fields.append("project.current_release")
    if active_phase is None:
        unknown_fields.append("project.active_phase")
    if policy_integrated is None:
        unknown_fields.append("project.policy_integrated")

    return ProjectStatus(
        current_release=current_release,
        active_phase=active_phase,
        policy_integrated=policy_integrated,
    ), unknown_fields, conflicts


def collect_contract_status(repo_path: Path) -> tuple[ContractStatus, list[str]]:
    unknown_fields: list[str] = []
    c_file = repo_path / "docs" / "project" / "SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md"

    contracts: dict[str, Optional[str]] = {
        "runtime_envelope": None,
        "correlation_id": None,
        "phase_retrospective": None,
        "approved_unit_plan_extension": None,
        "worktree_contract": None,
        "status_projection": None,
    }

    if c_file.is_file():
        try:
            content = c_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            for line in lines:
                if not line.startswith("|"):
                    continue
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) < 8:
                    continue
                c_name = parts[0].replace("*", "").strip()
                des_status = parts[6].replace("`", "").strip()
                imp_status = parts[7].replace("`", "").strip()

                st_val = f"{des_status} / {imp_status}"

                if "OrchestraRuntimeEnvelope" in c_name:
                    contracts["runtime_envelope"] = st_val
                elif "OrchestraCorrelationID" in c_name:
                    contracts["correlation_id"] = st_val
                elif "OrchestraPhaseRetrospective" in c_name:
                    contracts["phase_retrospective"] = st_val
                elif "OrchestraUnitRecord" in c_name:
                    contracts["approved_unit_plan_extension"] = st_val
                elif "OrchestraStatusProjection" in c_name:
                    contracts["status_projection"] = st_val
                elif "OrchestraWorktreeContract" in c_name:
                    contracts["worktree_contract"] = st_val
        except Exception:
            pass

    for k, v in contracts.items():
        if v is None:
            unknown_fields.append(f"contracts.{k}")

    return ContractStatus(
        runtime_envelope=contracts["runtime_envelope"],
        correlation_id=contracts["correlation_id"],
        phase_retrospective=contracts["phase_retrospective"],
        approved_unit_plan_extension=contracts["approved_unit_plan_extension"],
        worktree_contract=contracts["worktree_contract"],
        status_projection=contracts["status_projection"],
    ), unknown_fields


def reconcile_validation_status(
    head_sha: Optional[str],
    evidence: Optional[Any] = None,
) -> tuple[ValidationStatus, list[str], list[str]]:
    unknown_fields: list[str] = []
    warnings: list[str] = []

    if evidence is None:
        unknown_fields.extend([
            "validation.evidence_revision",
            "validation.governance_check",
            "validation.preflight_sync",
            "validation.revision_match",
            "validation.runtime_coverage",
            "validation.runtime_test_count",
        ])
        return ValidationStatus(), unknown_fields, warnings

    ev_rev = getattr(evidence, "revision", None) or getattr(evidence, "head_sha", None)
    rev_match = bool(head_sha and ev_rev and head_sha == ev_rev)

    if not rev_match:
        warnings.append(
            f"Validation evidence revision ({ev_rev}) does not match current HEAD ({head_sha})."
        )

    val_status = ValidationStatus(
        evidence_revision=str(ev_rev) if ev_rev else None,
        revision_match=rev_match,
        governance_check=getattr(evidence, "governance_check", None),
        preflight_sync=getattr(evidence, "preflight_sync", None),
        runtime_test_count=getattr(evidence, "runtime_test_count", None),
        runtime_coverage=getattr(evidence, "runtime_coverage", None),
    )
    return val_status, unknown_fields, warnings


def build_status_projection(
    repo_path: Path,
    now: Optional[datetime.datetime] = None,
    command_runner: Optional[CommandRunner] = None,
    validation_evidence: Optional[Any] = None,
) -> OrchestraStatusProjection:
    repo_path = repo_path.resolve()
    dt = now or datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        raise ValueError("now timestamp must be timezone-aware (UTC)")
    ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    git_st, git_unk, git_warn = collect_git_status(repo_path, command_runner=command_runner)
    proj_st, proj_unk, proj_conf = collect_project_status(repo_path)
    cont_st, cont_unk = collect_contract_status(repo_path)
    val_st, val_unk, val_warn = reconcile_validation_status(
        git_st.head_sha, validation_evidence
    )

    all_unknowns = tuple(sorted(set(git_unk + proj_unk + cont_unk + val_unk)))
    all_conflicts = tuple(sorted(set(proj_conf)))
    all_warnings = tuple(sorted(set(git_warn + val_warn)))

    diagnostics = DiagnosticsStatus(
        unknown_fields=all_unknowns,
        conflicts=all_conflicts,
        warnings=all_warnings,
    )

    return OrchestraStatusProjection(
        projection_version=STATUS_PROJECTION_VERSION,
        timestamp=ts,
        git=git_st,
        project=proj_st,
        contracts=cont_st,
        validation=val_st,
        diagnostics=diagnostics,
    )


def serialize_status_projection(projection: OrchestraStatusProjection) -> dict[str, Any]:
    return {
        "projection_version": projection.projection_version,
        "timestamp": projection.timestamp,
        "git": {
            "is_git_repo": projection.git.is_git_repo,
            "current_branch": projection.git.current_branch,
            "head_sha": projection.git.head_sha,
            "is_clean": projection.git.is_clean,
            "staged_count": projection.git.staged_count,
            "modified_count": projection.git.modified_count,
            "untracked_count": projection.git.untracked_count,
            "ahead_count": projection.git.ahead_count,
            "behind_count": projection.git.behind_count,
            "selected_remote": projection.git.selected_remote,
            "selected_main_ref": projection.git.selected_main_ref,
            "selected_main_sha": projection.git.selected_main_sha,
            "remote_names": list(projection.git.remote_names),
            "is_shallow": projection.git.is_shallow,
            "is_worktree": projection.git.is_worktree,
            "worktree_path_redacted": projection.git.worktree_path_redacted,
        },
        "project": {
            "current_release": projection.project.current_release,
            "active_phase": projection.project.active_phase,
            "policy_integrated": projection.project.policy_integrated,
        },
        "contracts": {
            "runtime_envelope": projection.contracts.runtime_envelope,
            "correlation_id": projection.contracts.correlation_id,
            "phase_retrospective": projection.contracts.phase_retrospective,
            "approved_unit_plan_extension": projection.contracts.approved_unit_plan_extension,
            "worktree_contract": projection.contracts.worktree_contract,
            "status_projection": projection.contracts.status_projection,
        },
        "validation": {
            "evidence_revision": projection.validation.evidence_revision,
            "revision_match": projection.validation.revision_match,
            "governance_check": projection.validation.governance_check,
            "preflight_sync": projection.validation.preflight_sync,
            "runtime_test_count": projection.validation.runtime_test_count,
            "runtime_coverage": projection.validation.runtime_coverage,
        },
        "diagnostics": {
            "unknown_fields": list(projection.diagnostics.unknown_fields),
            "conflicts": list(projection.diagnostics.conflicts),
            "warnings": list(projection.diagnostics.warnings),
        },
    }


def serialize_status_projection_to_str(projection: OrchestraStatusProjection) -> str:
    data = serialize_status_projection(projection)
    return json.dumps(data, indent=2, ensure_ascii=False)


def render_status_projection(projection: OrchestraStatusProjection) -> str:
    lines = [
        "========================================",
        "          ORCHESTRA STATUS              ",
        "========================================",
        f"Projection Version: {projection.projection_version}",
        f"Timestamp:          {projection.timestamp}",
        "",
        "--- Git Status ---",
        f"Is Git Repo:        {projection.git.is_git_repo}",
    ]
    if projection.git.is_git_repo:
        lines.extend([
            f"Current Branch:     {projection.git.current_branch or 'null'}",
            f"HEAD SHA:           {projection.git.head_sha or 'null'}",
            f"Working Tree Clean: {projection.git.is_clean}",
            f"Staged / Mod / Untr:{projection.git.staged_count} / {projection.git.modified_count} / {projection.git.untracked_count}",
            f"Ahead / Behind:     {projection.git.ahead_count} / {projection.git.behind_count}",
            f"Selected Remote:    {projection.git.selected_remote or 'null'}",
            f"Remote Main SHA:    {projection.git.selected_main_sha or 'null'}",
            f"Remotes Discovered: {', '.join(projection.git.remote_names) if projection.git.remote_names else 'none'}",
            f"Is Shallow:         {projection.git.is_shallow}",
            f"Is Worktree:        {projection.git.is_worktree}",
        ])

    lines.extend([
        "",
        "--- Project Status ---",
        f"Current Release:    {projection.project.current_release or 'null'}",
        f"Active Task / Phase:{projection.project.active_phase or 'null'}",
        f"Policy Integrated:  {projection.project.policy_integrated}",
        "",
        "--- Contracts Status ---",
        f"Runtime Envelope:   {projection.contracts.runtime_envelope or 'null'}",
        f"Correlation ID:     {projection.contracts.correlation_id or 'null'}",
        f"Phase Retrospective:{projection.contracts.phase_retrospective or 'null'}",
        f"Approved Unit Plan: {projection.contracts.approved_unit_plan_extension or 'null'}",
        f"Status Projection:  {projection.contracts.status_projection or 'null'}",
        f"Worktree Contract:  {projection.contracts.worktree_contract or 'null'}",
        "",
        "--- Validation Evidence ---",
        f"Evidence Revision:  {projection.validation.evidence_revision or 'null'}",
        f"Revision Match:     {projection.validation.revision_match}",
        f"Governance Check:   {projection.validation.governance_check or 'null'}",
        f"Preflight Sync:     {projection.validation.preflight_sync or 'null'}",
        f"Runtime Test Count: {projection.validation.runtime_test_count}",
        f"Runtime Coverage:   {projection.validation.runtime_coverage or 'null'}",
    ])

    if projection.diagnostics.unknown_fields:
        lines.extend(["", "--- Unknown Fields ---"])
        for u in projection.diagnostics.unknown_fields:
            lines.append(f"  - {u}")

    if projection.diagnostics.conflicts:
        lines.extend(["", "--- Conflicts ---"])
        for c in projection.diagnostics.conflicts:
            lines.append(f"  - {c}")

    if projection.diagnostics.warnings:
        lines.extend(["", "--- Warnings ---"])
        for w in projection.diagnostics.warnings:
            lines.append(f"  - {w}")

    lines.append("========================================")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra_status",
        description="Render Orchestra Status Projection CLI",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output deterministic UTF-8 JSON",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output and return exit code 0 on success",
    )

    args = parser.parse_args(argv)
    repo_path = Path(args.repo)

    if not repo_path.exists():
        if not args.quiet:
            sys.stderr.write(f"Error: Repository path {args.repo!r} does not exist\n")
        return 1

    try:
        projection = build_status_projection(repo_path)
    except Exception as exc:
        if not args.quiet:
            sys.stderr.write(f"Error building status projection: {exc}\n")
        return 1

    if not projection.git.is_git_repo and projection.diagnostics.warnings:
        if any("Git executable unavailable" in w for w in projection.diagnostics.warnings):
            if not args.quiet:
                sys.stderr.write("Git executable unavailable.\n")
            return 1

    if not args.quiet:
        if args.json:
            print(serialize_status_projection_to_str(projection))
        else:
            print(render_status_projection(projection))

    return 0


if __name__ == "__main__":
    sys.exit(main())
