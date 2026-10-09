from __future__ import annotations

# @codebase_provenance_JEO
# @codebase_rights_JEO

from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit

from .errors import RuntimeContractError, RuntimeInitializationError
from .application.ports.specialist_execution import (
    ReadOnlyWorkspace,
    ReadOnlyWorkspaceProvider,
    ReadOnlyWorkspaceSource,
    ReviewChangeStatus,
    SpecialistReviewChange,
)
from .domain.execution.operation_contracts import (
    DEFENSIVE_REVIEW_HOST_PROFILE_ID,
    DEFENSIVE_SECURITY_REVIEW,
    OperationKind,
    ReadOnlySpecialistExecutionRequest,
    SpecialistReviewResult,
)
from .interfaces import (
    IIDEAdapter,
    IReadOnlySpecialistExecutionEngine,
    ISpecialistExecutionEngine,
    ISkillRegistry,
)
from .lifecycle import LifecycleState
from .models import ContextPackage, OperationGovernanceContext, RouteDecision, ValidationResult
from .services import (
    ContextAssembler,
    RuntimeComposition,
    RuntimeExecutor,
    RuntimeOperationResult,
    _stable_id,
)


SPECIALIST_EXECUTION_REQUEST_VERSION = "orchestra.specialist-execution-request.v1"
SPECIALIST_EXECUTION_RECEIPT_VERSION = "orchestra.specialist-execution-receipt.v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
REVIEW_SNAPSHOT_MAX_FILES = 10000
REVIEW_SNAPSHOT_MAX_FILE_BYTES = 16 * 1024 * 1024
REVIEW_SNAPSHOT_MAX_TOTAL_BYTES = 128 * 1024 * 1024


class SpecialistExecutionMode(str, Enum):
    DETERMINISTIC_TEST_ENGINE = "DETERMINISTIC_TEST_ENGINE"
    HOST_NATIVE = "HOST_NATIVE"


class SpecialistExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class SpecialistSideEffectClass(str, Enum):
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    FILE_MUTATION = "FILE_MUTATION"
    EXTERNAL_MUTATION = "EXTERNAL_MUTATION"
    UNKNOWN = "UNKNOWN"


class SpecialistExecutionContractError(RuntimeContractError):
    pass


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SpecialistExecutionContractError(
            f"{field_name} must be non-empty",
            "INVALID_SPECIALIST_EXECUTION_CONTRACT",
            {"field": field_name},
        )
    return text


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _git_output(project_root: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _git_bytes(project_root: Path, *arguments: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _repository_identity(remote_url: str | None) -> str | None:
    if not remote_url:
        return None
    host = ""
    path = remote_url
    if "://" in remote_url:
        parsed = urlsplit(remote_url)
        if parsed.scheme.casefold() == "file" or not parsed.hostname:
            return None
        host = parsed.netloc.rsplit("@", 1)[-1]
        path = parsed.path
    elif re.match(r"^(?:[^@/]+@)?[^:/]+:.+$", remote_url) and not re.match(
        r"^[a-zA-Z]:[\\/]", remote_url
    ):
        host, path = remote_url.rsplit(":", 1)
        host = host.rsplit("@", 1)[-1]
    raw_segments = path.replace("\\", "/").split("/")
    if any(part in {".", ".."} for part in raw_segments):
        return None
    segments = [part for part in raw_segments if part]
    if not host or not segments:
        return None
    segments[-1] = re.sub(r"\.git$", "", segments[-1], flags=re.IGNORECASE)
    repo_path = "/".join(segments)
    identity = f"{host.casefold()}/{repo_path}"
    return identity or None


def _repository_snapshot_identity(project_root: Path) -> dict[str, str | None]:
    remote_url = _git_output(project_root, "config", "--get", "remote.origin.url")
    commit_info = _git_output(project_root, "show", "-s", "--format=%H%n%T", "HEAD")
    base = _git_output(project_root, "merge-base", "HEAD", "origin/main")
    commit_lines = commit_info.splitlines() if commit_info else ()
    head, tree = commit_lines if len(commit_lines) == 2 else (None, None)
    return {
        "repository_identity": _repository_identity(remote_url),
        "base_sha": base.lower() if base and GIT_SHA_PATTERN.fullmatch(base.lower()) else None,
        "head_sha": head.lower() if head and GIT_SHA_PATTERN.fullmatch(head.lower()) else None,
        "tree_sha": tree.lower() if tree and GIT_SHA_PATTERN.fullmatch(tree.lower()) else None,
    }


def _verified_repository_root(project_root: Path) -> Path:
    root_text = _git_output(project_root, "rev-parse", "--show-toplevel")
    if root_text is None:
        raise SpecialistExecutionContractError(
            "defensive review requires a Git repository root",
            "SNAPSHOT_IDENTITY_UNAVAILABLE",
        )
    try:
        root = Path(root_text).resolve(strict=True)
    except OSError as exc:
        raise SpecialistExecutionContractError(
            "defensive review repository root could not be resolved",
            "SNAPSHOT_IDENTITY_UNAVAILABLE",
        ) from exc
    if not root.is_dir():
        raise SpecialistExecutionContractError(
            "defensive review repository root is not a directory",
            "SNAPSHOT_IDENTITY_UNAVAILABLE",
        )
    return root


def _require_repository_snapshot_identity(project_root: Path) -> dict[str, str]:
    identity = _repository_snapshot_identity(project_root)
    if (
        not identity.get("repository_identity")
        or any(
            not isinstance(identity.get(field), str)
            or not GIT_SHA_PATTERN.fullmatch(identity[field] or "")
            for field in ("base_sha", "head_sha", "tree_sha")
        )
    ):
        raise SpecialistExecutionContractError(
            "defensive review requires repository, base, head, and tree identity",
            "SNAPSHOT_IDENTITY_UNAVAILABLE",
        )
    return {key: str(value) for key, value in identity.items()}


@dataclass(frozen=True, slots=True)
class _CandidateChange:
    path: str
    status: ReviewChangeStatus
    previous_path: str | None = None


def _repository_review_inventory(
    project_root: Path,
    base_sha: str,
) -> tuple[_CandidateChange, ...]:
    changed = _git_bytes(
        project_root,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        base_sha,
        "--",
    )
    untracked = _git_bytes(
        project_root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    )
    if changed is None or untracked is None:
        raise SpecialistExecutionContractError(
            "trusted host could not determine the candidate review inventory",
            "SNAPSHOT_BINDING_FAILED",
        )

    inventory: list[_CandidateChange] = []
    seen_paths: set[str] = set()

    def add_change(change: _CandidateChange) -> None:
        paths = (change.path,) if change.previous_path is None else (change.previous_path, change.path)
        if len(set(paths)) != len(paths) or any(path in seen_paths for path in paths):
            raise SpecialistExecutionContractError(
                "Git returned duplicate paths in the candidate review inventory",
                "SNAPSHOT_BINDING_FAILED",
            )
        seen_paths.update(paths)
        inventory.append(change)

    try:
        changed_parts = [part for part in changed.split(b"\x00") if part]
        index = 0
        while index < len(changed_parts):
            status = changed_parts[index].decode("ascii", errors="strict")
            index += 1
            if status in {"A", "D", "M", "T"}:
                if index >= len(changed_parts):
                    raise SpecialistExecutionContractError(
                        "Git returned a malformed candidate review inventory",
                        "SNAPSHOT_BINDING_FAILED",
                    )
                path = _normalize_review_path(changed_parts[index].decode("utf-8", errors="strict"))
                index += 1
                mapped_status = {
                    "A": ReviewChangeStatus.ADDED,
                    "D": ReviewChangeStatus.DELETED,
                    "M": ReviewChangeStatus.MODIFIED,
                    "T": ReviewChangeStatus.MODIFIED,
                }[status]
                add_change(_CandidateChange(path, mapped_status))
            elif re.fullmatch(r"R[0-9]{1,3}", status):
                if index + 1 >= len(changed_parts):
                    raise SpecialistExecutionContractError(
                        "Git returned a malformed candidate rename",
                        "SNAPSHOT_BINDING_FAILED",
                    )
                previous_path = _normalize_review_path(changed_parts[index].decode("utf-8", errors="strict"))
                path = _normalize_review_path(changed_parts[index + 1].decode("utf-8", errors="strict"))
                index += 2
                add_change(_CandidateChange(path, ReviewChangeStatus.RENAMED, previous_path))
            else:
                raise SpecialistExecutionContractError(
                    "candidate review contains an unsupported Git change state",
                    "SNAPSHOT_BINDING_FAILED",
                )

        for raw_path in untracked.split(b"\x00"):
            if raw_path:
                path = _normalize_review_path(raw_path.decode("utf-8", errors="strict"))
                add_change(_CandidateChange(path, ReviewChangeStatus.ADDED))
    except UnicodeDecodeError as exc:
        raise SpecialistExecutionContractError(
            "candidate review paths must be valid UTF-8",
            "SNAPSHOT_BINDING_FAILED",
        ) from exc

    if len(inventory) > REVIEW_SNAPSHOT_MAX_FILES:
        raise SpecialistExecutionContractError(
            "candidate review inventory exceeds the bounded snapshot size",
            "READ_ONLY_WORKSPACE_SNAPSHOT_TOO_LARGE",
        )
    return tuple(
        sorted(
            inventory,
            key=lambda item: (
                item.path.encode("utf-8", errors="strict"),
                (item.previous_path or "").encode("utf-8", errors="strict"),
            ),
        )
    )


def _normalize_review_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise SpecialistExecutionContractError(
            "review workspace returned an invalid relative path",
            "INVALID_READ_ONLY_WORKSPACE_PATH",
        )
    path = value.replace("\\", "/")
    if path.startswith("/") or re.match(r"^[a-zA-Z]:", path):
        raise SpecialistExecutionContractError(
            "review workspace paths must be relative",
            "INVALID_READ_ONLY_WORKSPACE_PATH",
        )
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SpecialistExecutionContractError(
            "review workspace paths must be normalized and traversal-free",
            "INVALID_READ_ONLY_WORKSPACE_PATH",
        )
    return "/".join(parts)


def _repository_git_blob_bytes(project_root: Path, base_sha: str, path: str) -> bytes:
    object_spec = f"{base_sha}:{path}"
    if _git_output(project_root, "cat-file", "-t", object_spec) != "blob":
        raise SpecialistExecutionContractError(
            "candidate base evidence must be a Git text blob",
            "SNAPSHOT_BINDING_FAILED",
            {"path": path},
        )
    size_text = _git_output(project_root, "cat-file", "-s", object_spec)
    try:
        size = int(size_text) if size_text is not None else -1
    except ValueError:
        size = -1
    if size < 0:
        raise SpecialistExecutionContractError(
            "trusted host could not determine candidate base evidence size",
            "SNAPSHOT_BINDING_FAILED",
            {"path": path},
        )
    if size > REVIEW_SNAPSHOT_MAX_FILE_BYTES:
        raise SpecialistExecutionContractError(
            "candidate base evidence exceeds the bounded snapshot size",
            "READ_ONLY_WORKSPACE_SNAPSHOT_TOO_LARGE",
            {"path": path},
        )
    content = _git_bytes(project_root, "cat-file", "blob", object_spec)
    if content is None or len(content) != size:
        raise SpecialistExecutionContractError(
            "trusted host could not materialize candidate base evidence",
            "SNAPSHOT_BINDING_FAILED",
            {"path": path},
        )
    return content


def _repository_file_bytes(project_root: Path, path: str) -> bytes:
    candidate_path = project_root
    for part in path.split("/"):
        candidate_path = candidate_path / part
        if candidate_path.is_symlink():
            raise SpecialistExecutionContractError(
                "candidate review paths cannot traverse symbolic links",
                "SNAPSHOT_BINDING_FAILED",
            )
    try:
        resolved = candidate_path.resolve(strict=True)
        resolved.relative_to(project_root)
    except (OSError, ValueError) as exc:
        raise SpecialistExecutionContractError(
            "candidate review path is missing or outside the verified repository",
            "SNAPSHOT_BINDING_FAILED",
        ) from exc
    if not resolved.is_file():
        raise SpecialistExecutionContractError(
            "candidate review paths must identify regular files",
            "SNAPSHOT_BINDING_FAILED",
        )
    try:
        with resolved.open("rb") as source:
            content = source.read(REVIEW_SNAPSHOT_MAX_FILE_BYTES + 1)
    except OSError as exc:
        raise SpecialistExecutionContractError(
            "candidate review content must be readable",
            "SNAPSHOT_BINDING_FAILED",
            {"cause": type(exc).__name__},
        ) from exc
    if len(content) > REVIEW_SNAPSHOT_MAX_FILE_BYTES:
        raise SpecialistExecutionContractError(
            "candidate review file exceeds the bounded snapshot size",
            "READ_ONLY_WORKSPACE_SNAPSHOT_TOO_LARGE",
        )
    return content


def _repository_path_exists(project_root: Path, path: str) -> bool:
    candidate_path = project_root
    try:
        for part in path.split("/"):
            if not any(entry.name == part for entry in candidate_path.iterdir()):
                return False
            candidate_path = candidate_path / part
        candidate_path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError as exc:
        raise SpecialistExecutionContractError(
            "candidate path state could not be verified",
            "SNAPSHOT_BINDING_FAILED",
            {"path": path, "cause": type(exc).__name__},
        ) from exc
    return True


def _decode_review_bytes(content: bytes, path: str) -> str:
    try:
        return content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SpecialistExecutionContractError(
            "candidate review content must be valid UTF-8 text",
            "SNAPSHOT_BINDING_FAILED",
            {"path": path},
        ) from exc


def _review_snapshot_digest(
    changes: tuple[SpecialistReviewChange, ...],
    repository_identity: Mapping[str, str],
) -> str:
    hasher = sha256()

    def append(value: bytes) -> None:
        hasher.update(len(value).to_bytes(8, "big"))
        hasher.update(value)

    append(b"orchestra.specialist-review-snapshot.v3")
    append(
        json.dumps(
            dict(repository_identity),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    )
    append(len(changes).to_bytes(8, "big"))
    for change in changes:
        append(change.status.value.encode("ascii"))
        append(change.path.encode("utf-8", errors="strict"))
        append(b"\x01" if change.previous_path is not None else b"\x00")
        if change.previous_path is not None:
            append(change.previous_path.encode("utf-8", errors="strict"))
        for content in (change.base_content, change.current_content):
            append(b"\x01" if content is not None else b"\x00")
            if content is not None:
                append(content.encode("utf-8", errors="strict"))
    return hasher.hexdigest()


def _raise_snapshot_drift(path: str | None = None) -> None:
    details = {"path": path} if path is not None else None
    raise SpecialistExecutionContractError(
        "repository candidate changed while the review snapshot was materialized",
        "SNAPSHOT_DRIFT_DETECTED",
        details,
    )


def _assert_snapshot_stable(
    repository_root: Path,
    repository_identity: Mapping[str, str],
    inventory: tuple[_CandidateChange, ...],
    frozen_current_bytes: Mapping[str, bytes],
) -> None:
    for change in inventory:
        if change.status is ReviewChangeStatus.DELETED:
            try:
                exists = _repository_path_exists(repository_root, change.path)
            except SpecialistExecutionContractError as exc:
                _raise_snapshot_drift(change.path)
                raise AssertionError("unreachable") from exc
            if exists:
                _raise_snapshot_drift(change.path)
            continue
        if change.status is ReviewChangeStatus.RENAMED and change.previous_path is not None:
            try:
                source_exists = _repository_path_exists(repository_root, change.previous_path)
            except SpecialistExecutionContractError as exc:
                _raise_snapshot_drift(change.previous_path)
                raise AssertionError("unreachable") from exc
            if source_exists:
                _raise_snapshot_drift(change.previous_path)
        try:
            current_bytes = _repository_file_bytes(repository_root, change.path)
        except SpecialistExecutionContractError as exc:
            _raise_snapshot_drift(change.path)
            raise AssertionError("unreachable") from exc
        if current_bytes != frozen_current_bytes.get(change.path):
            _raise_snapshot_drift(change.path)

    try:
        current_identity = _require_repository_snapshot_identity(repository_root)
        current_inventory = _repository_review_inventory(repository_root, repository_identity["base_sha"])
    except SpecialistExecutionContractError as exc:
        _raise_snapshot_drift()
        raise AssertionError("unreachable") from exc
    if current_identity != repository_identity or current_inventory != inventory:
        _raise_snapshot_drift()


def _create_host_read_only_snapshot(
    provider: ReadOnlyWorkspaceProvider,
    project_root: Path,
) -> tuple[_ReadOnlyWorkspaceFacade, str]:
    repository_root = _verified_repository_root(project_root)
    repository_identity = _require_repository_snapshot_identity(repository_root)
    inventory = _repository_review_inventory(repository_root, repository_identity["base_sha"])
    expected_paths = tuple(
        sorted(
            (change.path for change in inventory if change.status is not ReviewChangeStatus.DELETED),
            key=lambda path: path.encode("utf-8", errors="strict"),
        )
    )
    try:
        source = provider.for_review(repository_root, expected_paths)
    except Exception as exc:
        raise SpecialistExecutionContractError(
            "trusted host could not open the candidate review workspace",
            "READ_ONLY_WORKSPACE_SNAPSHOT_FAILED",
            {"cause": type(exc).__name__},
        ) from exc
    if not isinstance(source, ReadOnlyWorkspaceSource):
        raise SpecialistExecutionContractError(
            "workspace provider did not return the bounded source API",
            "INVALID_READ_ONLY_WORKSPACE",
        )
    try:
        source_root = Path(source.repository_root).resolve(strict=True)
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise SpecialistExecutionContractError(
            "workspace provider did not bind content to a verified repository root",
            "SNAPSHOT_BINDING_FAILED",
        ) from exc
    if source_root != repository_root:
        raise SpecialistExecutionContractError(
            "workspace provider root does not match the verified repository root",
            "SNAPSHOT_BINDING_FAILED",
        )
    try:
        paths = source.list_paths()
    except Exception as exc:
        raise SpecialistExecutionContractError(
            "trusted host could not enumerate review content",
            "READ_ONLY_WORKSPACE_SNAPSHOT_FAILED",
            {"cause": type(exc).__name__},
        ) from exc
    if not isinstance(paths, tuple) or len(paths) > REVIEW_SNAPSHOT_MAX_FILES:
        raise SpecialistExecutionContractError(
            "review workspace returned an invalid or oversized path list",
            "INVALID_READ_ONLY_WORKSPACE_DATA",
        )
    normalized_paths = tuple((_normalize_review_path(path), path) for path in paths)
    source_paths = {path for path, _source_path in normalized_paths}
    if len(source_paths) != len(normalized_paths):
        raise SpecialistExecutionContractError(
            "review workspace paths must be unique after normalization",
            "INVALID_READ_ONLY_WORKSPACE_DATA",
        )
    if source_paths != set(expected_paths):
        raise SpecialistExecutionContractError(
            "workspace provider inventory does not match the complete host review scope",
            "SNAPSHOT_BINDING_FAILED",
        )
    changes: list[SpecialistReviewChange] = []
    frozen_current_bytes: dict[str, bytes] = {}
    total_bytes = 0
    source_paths_by_name = dict(normalized_paths)
    ordered_changes = sorted(
        inventory,
        key=lambda change: change.path.encode("utf-8", errors="strict"),
    )
    for candidate_change in ordered_changes:
        base_content: str | None = None
        if candidate_change.status is not ReviewChangeStatus.ADDED:
            base_path = candidate_change.previous_path or candidate_change.path
            base_bytes = _repository_git_blob_bytes(
                repository_root,
                repository_identity["base_sha"],
                base_path,
            )
            base_content = _decode_review_bytes(base_bytes, base_path)
            total_bytes += len(base_bytes)

        current_content: str | None = None
        if candidate_change.status is not ReviewChangeStatus.DELETED:
            path = candidate_change.path
            repository_bytes = _repository_file_bytes(repository_root, path)
            try:
                provider_bytes = source.read_bytes(
                    source_paths_by_name[path],
                    max_bytes=REVIEW_SNAPSHOT_MAX_FILE_BYTES,
                )
            except Exception as exc:
                raise SpecialistExecutionContractError(
                    "trusted host could not snapshot review content",
                    "READ_ONLY_WORKSPACE_SNAPSHOT_FAILED",
                    {"cause": type(exc).__name__},
                ) from exc
            if not isinstance(provider_bytes, bytes):
                raise SpecialistExecutionContractError(
                    "review workspace returned invalid byte data",
                    "INVALID_READ_ONLY_WORKSPACE_DATA",
                )
            if provider_bytes != repository_bytes:
                try:
                    latest_bytes = _repository_file_bytes(repository_root, path)
                except SpecialistExecutionContractError as exc:
                    _raise_snapshot_drift(path)
                    raise AssertionError("unreachable") from exc
                if latest_bytes != repository_bytes:
                    _raise_snapshot_drift(path)
                raise SpecialistExecutionContractError(
                    "workspace provider content does not match the verified repository",
                    "SNAPSHOT_BINDING_FAILED",
                    {"path": path},
                )
            current_content = _decode_review_bytes(repository_bytes, path)
            frozen_current_bytes[path] = repository_bytes
            total_bytes += len(repository_bytes)

        if total_bytes > REVIEW_SNAPSHOT_MAX_TOTAL_BYTES:
            raise SpecialistExecutionContractError(
                "review workspace exceeds the bounded snapshot size",
                "READ_ONLY_WORKSPACE_SNAPSHOT_TOO_LARGE",
            )
        changes.append(
            SpecialistReviewChange(
                path=candidate_change.path,
                status=candidate_change.status,
                previous_path=candidate_change.previous_path,
                base_content=base_content,
                current_content=current_content,
            )
        )

    snapshot = tuple(changes)
    _assert_snapshot_stable(repository_root, repository_identity, inventory, frozen_current_bytes)
    digest = _review_snapshot_digest(snapshot, repository_identity)
    files = tuple(
        (change.path, change.current_content)
        for change in snapshot
        if change.current_content is not None
    )
    return _ReadOnlyWorkspaceFacade(files, snapshot), digest


def _sorted_unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized = tuple(str(item).strip() for item in values if str(item).strip())
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True, slots=True)
class SpecialistExecutionConstraint:
    source: str
    key: str
    kind: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        source = _text(self.source, "constraint source").upper()
        if source not in {"AUTHORITY", "CAPABILITY"}:
            raise SpecialistExecutionContractError(
                "constraint source must be AUTHORITY or CAPABILITY",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"source": source},
            )
        key = _text(self.key, "constraint key").casefold()
        kind = _text(self.kind, "constraint kind").upper()
        if kind not in {"EXACT", "ALLOWED_SET"}:
            raise SpecialistExecutionContractError(
                "constraint kind is unsupported",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"kind": kind},
            )
        values = _sorted_unique(self.values)
        if not values or (kind == "EXACT" and len(values) != 1):
            raise SpecialistExecutionContractError(
                "constraint values do not match the declared kind",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"key": key},
            )
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "values", values)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "key": self.key,
            "kind": self.kind,
            "values": list(self.values),
        }


@dataclass(frozen=True, slots=True)
class SpecialistExecutionRequest:
    request_version: str
    request_id: str
    request_digest: str
    run_id: str
    parent_run_id: str | None
    correlation_id: str | None
    adapter_name: str
    command_name: str
    specialist: str
    project_root: str
    skill_source_path: str
    skill_source_digest: str
    task_input: str
    authority_decision_ref: str
    capability_decision_ref: str
    governance_status: str
    evaluated_governance_rules: tuple[str, ...]
    execution_constraints: tuple[SpecialistExecutionConstraint, ...]
    execution_mode: SpecialistExecutionMode

    def __post_init__(self) -> None:
        if self.request_version != SPECIALIST_EXECUTION_REQUEST_VERSION:
            raise SpecialistExecutionContractError(
                "unsupported specialist execution request version",
                "UNSUPPORTED_SPECIALIST_EXECUTION_REQUEST_VERSION",
            )
        for field_name in (
            "request_id",
            "run_id",
            "adapter_name",
            "command_name",
            "specialist",
            "project_root",
            "skill_source_path",
            "authority_decision_ref",
            "capability_decision_ref",
            "governance_status",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        digest = str(self.request_digest).strip().casefold()
        skill_digest = str(self.skill_source_digest).strip().casefold()
        if not SHA256_PATTERN.fullmatch(digest):
            raise SpecialistExecutionContractError(
                "request_digest must be a SHA-256 digest",
                "INVALID_REQUEST_DIGEST",
            )
        if not SHA256_PATTERN.fullmatch(skill_digest):
            raise SpecialistExecutionContractError(
                "skill_source_digest must be a SHA-256 digest",
                "INVALID_SKILL_SOURCE_DIGEST",
            )
        task_input = str(self.task_input)
        if not task_input.strip():
            raise SpecialistExecutionContractError(
                "task_input must be non-empty",
                "EMPTY_SPECIALIST_TASK_INPUT",
            )
        rules = _sorted_unique(self.evaluated_governance_rules)
        constraints = tuple(
            sorted(
                tuple(self.execution_constraints),
                key=lambda item: (item.source, item.key, item.kind, item.values),
            )
        )
        if len({(item.source, item.key) for item in constraints}) != len(constraints):
            raise SpecialistExecutionContractError(
                "execution constraints must be unique per source/key",
                "DUPLICATE_SPECIALIST_EXECUTION_CONSTRAINT",
            )
        mode = SpecialistExecutionMode(self.execution_mode)
        parent_run_id = str(self.parent_run_id).strip() if self.parent_run_id else None
        correlation_id = str(self.correlation_id).strip() if self.correlation_id else None
        object.__setattr__(self, "request_digest", digest)
        object.__setattr__(self, "skill_source_digest", skill_digest)
        object.__setattr__(self, "task_input", task_input)
        object.__setattr__(self, "evaluated_governance_rules", rules)
        object.__setattr__(self, "execution_constraints", constraints)
        object.__setattr__(self, "execution_mode", mode)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        object.__setattr__(self, "correlation_id", correlation_id)
        if self.request_digest != self.compute_digest():
            raise SpecialistExecutionContractError(
                "request digest does not match request payload",
                "REQUEST_DIGEST_MISMATCH",
            )
        expected_id = f"specialist-request.{self.request_digest[:24]}"
        if self.request_id != expected_id:
            raise SpecialistExecutionContractError(
                "request identifier does not match request digest",
                "REQUEST_IDENTITY_MISMATCH",
            )

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        parent_run_id: str | None,
        correlation_id: str | None,
        adapter_name: str,
        command_name: str,
        specialist: str,
        project_root: str,
        skill_source_path: str,
        skill_source_digest: str,
        task_input: str,
        authority_decision_ref: str,
        capability_decision_ref: str,
        governance_status: str,
        evaluated_governance_rules: tuple[str, ...],
        execution_constraints: tuple[SpecialistExecutionConstraint, ...],
        execution_mode: SpecialistExecutionMode,
    ) -> SpecialistExecutionRequest:
        payload = {
            "request_version": SPECIALIST_EXECUTION_REQUEST_VERSION,
            "run_id": str(run_id).strip(),
            "parent_run_id": str(parent_run_id).strip() if parent_run_id else None,
            "correlation_id": str(correlation_id).strip() if correlation_id else None,
            "adapter_name": str(adapter_name).strip(),
            "command_name": str(command_name).strip(),
            "specialist": str(specialist).strip(),
            "project_root": str(project_root).strip(),
            "skill_source_path": str(skill_source_path).strip(),
            "skill_source_digest": str(skill_source_digest).strip().casefold(),
            "task_input": str(task_input),
            "authority_decision_ref": str(authority_decision_ref).strip(),
            "capability_decision_ref": str(capability_decision_ref).strip(),
            "governance_status": str(governance_status).strip(),
            "evaluated_governance_rules": list(_sorted_unique(evaluated_governance_rules)),
            "execution_constraints": [
                item.to_dict()
                for item in sorted(
                    tuple(execution_constraints),
                    key=lambda item: (item.source, item.key, item.kind, item.values),
                )
            ],
            "execution_mode": SpecialistExecutionMode(execution_mode).value,
        }
        request_digest = _digest(payload)
        return cls(
            request_version=SPECIALIST_EXECUTION_REQUEST_VERSION,
            request_id=f"specialist-request.{request_digest[:24]}",
            request_digest=request_digest,
            run_id=payload["run_id"],
            parent_run_id=payload["parent_run_id"],
            correlation_id=payload["correlation_id"],
            adapter_name=payload["adapter_name"],
            command_name=payload["command_name"],
            specialist=payload["specialist"],
            project_root=payload["project_root"],
            skill_source_path=payload["skill_source_path"],
            skill_source_digest=payload["skill_source_digest"],
            task_input=payload["task_input"],
            authority_decision_ref=payload["authority_decision_ref"],
            capability_decision_ref=payload["capability_decision_ref"],
            governance_status=payload["governance_status"],
            evaluated_governance_rules=tuple(payload["evaluated_governance_rules"]),
            execution_constraints=tuple(execution_constraints),
            execution_mode=SpecialistExecutionMode(payload["execution_mode"]),
        )

    def digest_payload(self) -> dict[str, object]:
        return {
            "request_version": self.request_version,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "correlation_id": self.correlation_id,
            "adapter_name": self.adapter_name,
            "command_name": self.command_name,
            "specialist": self.specialist,
            "project_root": self.project_root,
            "skill_source_path": self.skill_source_path,
            "skill_source_digest": self.skill_source_digest,
            "task_input": self.task_input,
            "authority_decision_ref": self.authority_decision_ref,
            "capability_decision_ref": self.capability_decision_ref,
            "governance_status": self.governance_status,
            "evaluated_governance_rules": list(self.evaluated_governance_rules),
            "execution_constraints": [item.to_dict() for item in self.execution_constraints],
            "execution_mode": self.execution_mode.value,
        }

    def compute_digest(self) -> str:
        return _digest(self.digest_payload())

    def to_dict(self) -> dict[str, object]:
        return {
            "request_version": self.request_version,
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            **self.digest_payload() | {},
        }


@dataclass(frozen=True, slots=True)
class SpecialistExecutionReceipt:
    receipt_version: str
    receipt_id: str
    request_id: str
    request_digest: str
    run_id: str
    adapter_name: str
    command_name: str
    specialist: str
    engine_id: str
    engine_version: str
    host_execution_id: str
    status: SpecialistExecutionStatus
    reason_code: str
    output: str
    evidence_refs: tuple[str, ...]
    side_effect_class: SpecialistSideEffectClass
    host_identity: str | None = None
    sandbox_identity: str | None = None
    approval_policy_identity: str | None = None
    artifact_refs: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    started_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if self.receipt_version != SPECIALIST_EXECUTION_RECEIPT_VERSION:
            raise SpecialistExecutionContractError(
                "unsupported specialist execution receipt version",
                "UNSUPPORTED_SPECIALIST_EXECUTION_RECEIPT_VERSION",
            )
        for field_name in (
            "receipt_id",
            "request_id",
            "run_id",
            "adapter_name",
            "command_name",
            "specialist",
            "engine_id",
            "engine_version",
            "host_execution_id",
            "reason_code",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        digest = str(self.request_digest).strip().casefold()
        if not SHA256_PATTERN.fullmatch(digest):
            raise SpecialistExecutionContractError(
                "receipt request_digest must be a SHA-256 digest",
                "INVALID_REQUEST_DIGEST",
            )
        object.__setattr__(self, "request_digest", digest)
        object.__setattr__(self, "status", SpecialistExecutionStatus(self.status))
        object.__setattr__(self, "side_effect_class", SpecialistSideEffectClass(self.side_effect_class))
        object.__setattr__(self, "output", str(self.output))
        object.__setattr__(self, "evidence_refs", _sorted_unique(self.evidence_refs))
        object.__setattr__(self, "artifact_refs", _sorted_unique(self.artifact_refs))
        object.__setattr__(self, "changed_paths", _sorted_unique(self.changed_paths))
        for field_name in (
            "host_identity",
            "sandbox_identity",
            "approval_policy_identity",
            "started_at",
            "completed_at",
        ):
            value = getattr(self, field_name)
            object.__setattr__(self, field_name, str(value).strip() if value else None)

    def assert_matches(
        self,
        request: SpecialistExecutionRequest,
        *,
        engine_id: str,
        engine_version: str,
    ) -> None:
        comparisons = (
            ("request_id", self.request_id, request.request_id, "REQUEST_IDENTITY_MISMATCH"),
            ("request_digest", self.request_digest, request.request_digest, "REQUEST_DIGEST_MISMATCH"),
            ("run_id", self.run_id, request.run_id, "RUN_IDENTITY_MISMATCH"),
            ("adapter_name", self.adapter_name, request.adapter_name, "ADAPTER_IDENTITY_MISMATCH"),
            ("command_name", self.command_name, request.command_name, "COMMAND_IDENTITY_MISMATCH"),
            ("specialist", self.specialist, request.specialist, "SPECIALIST_IDENTITY_MISMATCH"),
            ("engine_id", self.engine_id, str(engine_id).strip(), "ENGINE_IDENTITY_MISMATCH"),
            ("engine_version", self.engine_version, str(engine_version).strip(), "ENGINE_VERSION_MISMATCH"),
        )
        for field_name, actual, expected, reason_code in comparisons:
            if actual != expected:
                raise SpecialistExecutionContractError(
                    f"specialist execution receipt {field_name} does not match the request boundary",
                    reason_code,
                    {"field": field_name},
                )
        if request.execution_mode is SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE:
            if self.side_effect_class is not SpecialistSideEffectClass.NONE or self.changed_paths:
                raise SpecialistExecutionContractError(
                    "deterministic specialist execution receipts cannot report side effects",
                    "DETERMINISTIC_ENGINE_SIDE_EFFECT_REJECTED",
                )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "receipt_version": self.receipt_version,
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            "run_id": self.run_id,
            "adapter_name": self.adapter_name,
            "command_name": self.command_name,
            "specialist": self.specialist,
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "host_execution_id": self.host_execution_id,
            "status": self.status.value,
            "reason_code": self.reason_code,
            "output": self.output,
            "evidence_refs": list(self.evidence_refs),
            "side_effect_class": self.side_effect_class.value,
            "artifact_refs": list(self.artifact_refs),
            "changed_paths": list(self.changed_paths),
        }
        for field_name in (
            "host_identity",
            "sandbox_identity",
            "approval_policy_identity",
            "started_at",
            "completed_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                data[field_name] = value
        return data


@dataclass(frozen=True, slots=True)
class _PendingExecutionInput:
    adapter: IIDEAdapter
    prompt: str
    metadata: Mapping[str, object]


class _ReadOnlyWorkspaceFacade:
    """Immutable host-created content view with only list and read operations."""

    __slots__ = ("__files", "__changes")

    def __init__(
        self,
        files: tuple[tuple[str, str], ...],
        changes: tuple[SpecialistReviewChange, ...],
    ) -> None:
        self.__files = MappingProxyType(dict(files))
        self.__changes = changes

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]:
        if not relative_path:
            return tuple(self.__files)
        normalized = _normalize_review_path(relative_path)
        prefix = f"{normalized}/"
        return tuple(path for path in self.__files if path == normalized or path.startswith(prefix))

    def read_text(self, relative_path: str, *, max_bytes: int) -> str:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
            raise SpecialistExecutionContractError(
                "read-only workspace max_bytes must be a positive integer",
                "INVALID_READ_ONLY_WORKSPACE_LIMIT",
            )
        path = _normalize_review_path(relative_path)
        try:
            text = self.__files[path]
        except KeyError as exc:
            raise SpecialistExecutionContractError(
                "requested path is outside the immutable review snapshot",
                "READ_ONLY_WORKSPACE_PATH_UNAVAILABLE",
            ) from exc
        if len(text.encode("utf-8", errors="strict")) > max_bytes:
            raise SpecialistExecutionContractError(
                "requested content exceeds max_bytes",
                "READ_ONLY_WORKSPACE_CONTENT_TOO_LARGE",
            )
        return text

    def list_changes(self) -> tuple[SpecialistReviewChange, ...]:
        return self.__changes


class SpecialistRuntimeExecutor(RuntimeExecutor):
    """Opt-in typed specialist execution attachment over the existing trusted runtime gates.

    The base RuntimeExecutor remains unchanged. This subclass binds the task input to an
    executor-local ContextVar before entering the existing runtime. The configured engine
    is called only from the existing post-activation operation boundary, so routing,
    authority, capability, governance, coordination, and lifecycle activation remain
    owned by RuntimeExecutor.
    """

    def __init__(
        self,
        skill_registry: ISkillRegistry,
        router,
        governance,
        context_assembler: ContextAssembler,
        composition: RuntimeComposition,
        *,
        execution_engine: ISpecialistExecutionEngine | IReadOnlySpecialistExecutionEngine | None = None,
        execution_mode: SpecialistExecutionMode = SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
        read_only_workspace_provider: ReadOnlyWorkspaceProvider | None = None,
    ) -> None:
        if execution_engine is not None and not isinstance(execution_engine, (ISpecialistExecutionEngine, IReadOnlySpecialistExecutionEngine)):
            raise RuntimeInitializationError(
                "specialist execution engine must implement an operation-specific engine boundary",
                "INVALID_SPECIALIST_EXECUTION_ENGINE",
            )
        if execution_engine is None and SpecialistExecutionMode(execution_mode) is SpecialistExecutionMode.HOST_NATIVE:
            raise RuntimeInitializationError(
                "HOST_NATIVE execution requires an explicit execution engine",
                "ENGINE_NOT_CONFIGURED",
            )
        if read_only_workspace_provider is not None and not isinstance(read_only_workspace_provider, ReadOnlyWorkspaceProvider):
            raise RuntimeInitializationError(
                "read-only workspace provider must expose bounded read methods",
                "INVALID_READ_ONLY_WORKSPACE_PROVIDER",
            )
        self._read_only_workspace_provider = read_only_workspace_provider
        self._execution_engine = execution_engine
        self._execution_mode = SpecialistExecutionMode(execution_mode)
        self._execution_skill_registry = skill_registry
        self._execution_context_assembler = context_assembler
        self._pending_execution: ContextVar[_PendingExecutionInput | None] = ContextVar(
            f"orchestra-specialist-execution-{id(self)}",
            default=None,
        )
        super().__init__(
            skill_registry,
            router,
            governance,
            context_assembler,
            composition,
            operation=self._execute_specialist if execution_engine is not None else None,
        )

    @property
    def execution_engine(self) -> ISpecialistExecutionEngine | IReadOnlySpecialistExecutionEngine | None:
        return self._execution_engine

    @property
    def execution_mode(self) -> SpecialistExecutionMode:
        return self._execution_mode

    def _operation_governance_context(self, decision, binding) -> OperationGovernanceContext | None:
        context = super()._operation_governance_context(decision, binding)
        if (
            context is not None
            and decision.command_name.casefold() == "security-check"
            and decision.skill_slug.casefold() == "cipher"
            and context.operation_contract == DEFENSIVE_SECURITY_REVIEW
            and self._pending_execution.get() is not None
            and isinstance(self._execution_engine, IReadOnlySpecialistExecutionEngine)
            and not isinstance(self._execution_engine, ISpecialistExecutionEngine)
            and isinstance(self._read_only_workspace_provider, ReadOnlyWorkspaceProvider)
        ):
            return OperationGovernanceContext(
                context.operation_contract,
                DEFENSIVE_REVIEW_HOST_PROFILE_ID,
            )
        return context

    def execute(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        metadata: dict | None = None,
        *,
        coordination_session=None,
    ):
        if self._execution_engine is None:
            return super().execute(
                adapter,
                prompt,
                metadata,
                coordination_session=coordination_session,
            )
        token = self._pending_execution.set(
            _PendingExecutionInput(adapter, str(prompt), dict(metadata or {}))
        )
        try:
            return super().execute(
                adapter,
                prompt,
                metadata,
                coordination_session=coordination_session,
            )
        finally:
            self._pending_execution.reset(token)

    def execute_delegated(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        resolution,
        metadata: dict | None = None,
        *,
        coordination_session=None,
    ):
        if self._execution_engine is None:
            return super().execute_delegated(
                adapter,
                prompt,
                resolution,
                metadata,
                coordination_session=coordination_session,
            )
        token = self._pending_execution.set(
            _PendingExecutionInput(adapter, str(prompt), dict(metadata or {}))
        )
        try:
            return super().execute_delegated(
                adapter,
                prompt,
                resolution,
                metadata,
                coordination_session=coordination_session,
            )
        finally:
            self._pending_execution.reset(token)

    def _execute_specialist(
        self,
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> RuntimeOperationResult:
        pending = self._pending_execution.get()
        if pending is None or self._execution_engine is None:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution boundary was not configured",
                "ENGINE_NOT_CONFIGURED",
            )
        try:
            request = self._build_request(pending, adapter_name, decision, validation)
            binding = self.composition.policy.binding_for(decision.command_name, decision.skill_slug)
            contract = binding.operation_contract if binding is not None else None
            if contract is not None and contract.kind is OperationKind.DEFENSIVE_SECURITY_REVIEW:
                return self._execute_read_only_review(request, contract)
            elif contract is not None and contract.kind is OperationKind.SECURITY_SENSITIVE_EXECUTION:
                raise SpecialistExecutionContractError(
                    "protected execution requires a separately governed authorization path",
                    "TRUSTED_GOVERNANCE_AUTHORITY_REQUIRED",
                )
            elif decision.command_name.casefold() == "security-check" or decision.skill_slug.casefold() == "cipher":
                raise SpecialistExecutionContractError(
                    "Cipher execution requires a registered operation contract",
                    "MISSING_CIPHER_OPERATION_CONTRACT",
                )
            else:
                if not isinstance(self._execution_engine, ISpecialistExecutionEngine):
                    raise SpecialistExecutionContractError(
                        "engine does not implement the selected operation boundary",
                        "SPECIALIST_ENGINE_CAPABILITY_REQUIRED",
                    )
                receipt = self._execution_engine.execute(request)
            if not isinstance(receipt, SpecialistExecutionReceipt):
                raise SpecialistExecutionContractError(
                    "specialist execution engine returned an invalid receipt type",
                    "MALFORMED_EXECUTION_RECEIPT",
                )
            receipt.assert_matches(
                request,
                engine_id=self._execution_engine.engine_id,
                engine_version=self._execution_engine.engine_version,
            )
            state = {
                SpecialistExecutionStatus.COMPLETED: LifecycleState.COMPLETED,
                SpecialistExecutionStatus.FAILED: LifecycleState.FAILED,
                SpecialistExecutionStatus.CANCELLED: LifecycleState.CANCELLED,
                SpecialistExecutionStatus.TIMED_OUT: LifecycleState.TIMED_OUT,
            }[receipt.status]
            refs = _sorted_unique(
                (
                    f"specialist-request:{request.request_id}",
                    f"specialist-request-digest:{request.request_digest}",
                    f"specialist-receipt:{receipt.receipt_id}",
                    *receipt.evidence_refs,
                )
            )
            return RuntimeOperationResult(state, receipt.output, receipt.reason_code, refs)
        except RuntimeContractError as exc:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution contract failed closed",
                exc.reason_code,
                (type(exc).__name__,),
            )
        except Exception as exc:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution engine failed",
                "SPECIALIST_ENGINE_EXCEPTION",
                (type(exc).__name__,),
            )

    def _execute_read_only_review(self, request: SpecialistExecutionRequest, contract) -> RuntimeOperationResult:
        engine = self._execution_engine
        provider = self._read_only_workspace_provider
        if not isinstance(engine, IReadOnlySpecialistExecutionEngine):
            raise SpecialistExecutionContractError(
                "engine does not implement the read-only review boundary",
                "READ_ONLY_ENGINE_CAPABILITY_REQUIRED",
            )
        if isinstance(engine, ISpecialistExecutionEngine):
            raise SpecialistExecutionContractError(
                "defensive review cannot use an effectful specialist engine",
                "EFFECTFUL_ENGINE_REJECTED_FOR_REVIEW",
            )
        if provider is None:
            raise SpecialistExecutionContractError(
                "a trusted read-only workspace provider is required",
                "READ_ONLY_WORKSPACE_UNAVAILABLE",
            )
        workspace, snapshot_digest = _create_host_read_only_snapshot(
            provider,
            Path(request.project_root),
        )
        review_request_digest = _digest(
            {
                "request_digest": request.request_digest,
                "operation_id": contract.operation_id,
                "workspace_snapshot_digest": snapshot_digest,
            }
        )
        review_request = ReadOnlySpecialistExecutionRequest(
            request_id=request.request_id,
            request_digest=review_request_digest,
            workspace_snapshot_digest=snapshot_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            operation_id=contract.operation_id,
            task_input=request.task_input,
        )
        review = engine.execute_read_only(
            review_request,
            workspace,
        )
        if not isinstance(review, SpecialistReviewResult):
            raise SpecialistExecutionContractError(
                "read-only engine returned an invalid specialist review result",
                "MALFORMED_SPECIALIST_REVIEW_RESULT",
            )
        try:
            review.assert_matches(review_request)
        except ValueError as exc:
            raise SpecialistExecutionContractError(
                "specialist review result does not match its request",
                "SPECIALIST_REVIEW_RESULT_MISMATCH",
            ) from exc
        refs = _sorted_unique(
            (
                f"specialist-request:{request.request_id}",
                f"specialist-request-digest:{request.request_digest}",
                f"specialist-review:{review.review_id}",
                f"specialist-review-digest:{review.review_digest}",
                *review.evidence_refs,
            )
        )
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            json.dumps(review.to_dict(), sort_keys=True, ensure_ascii=True),
            f"SPECIALIST_REVIEW_{review.status.value}",
            refs,
        )

    def _build_request(
        self,
        pending: _PendingExecutionInput,
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> SpecialistExecutionRequest:
        binding = self.composition.policy.binding_for(decision.command_name, decision.skill_slug)
        if binding is None:
            raise SpecialistExecutionContractError(
                "specialist execution request requires the trusted runtime binding",
                "MISSING_RUNTIME_BINDING",
            )
        context: ContextPackage = self._execution_context_assembler.assemble(
            pending.adapter,
            pending.prompt,
            dict(pending.metadata),
        )
        skill = self._execution_skill_registry.get_skill(decision.skill_slug)
        if skill is None:
            raise SpecialistExecutionContractError(
                "specialist execution request cannot resolve the selected skill",
                "SPECIALIST_IDENTITY_MISMATCH",
            )
        project_root = Path(context.project_root).resolve()
        skill_path = Path(skill.skill_path).resolve()
        try:
            relative_skill_path = skill_path.relative_to(project_root).as_posix()
        except ValueError as exc:
            raise SpecialistExecutionContractError(
                "selected specialist source is outside the project root",
                "UNTRUSTED_SPECIALIST_SOURCE_PATH",
            ) from exc
        if not skill_path.is_file():
            raise SpecialistExecutionContractError(
                "selected specialist source is unavailable",
                "SPECIALIST_SOURCE_UNAVAILABLE",
            )
        constraints = tuple(
            SpecialistExecutionConstraint("AUTHORITY", item.key, item.kind.value, item.values)
            for item in binding.authority_constraints
        ) + tuple(
            SpecialistExecutionConstraint("CAPABILITY", item.key, item.kind.value, item.values)
            for item in binding.capability_constraints
        )
        authority_decision_ref = _stable_id(
            "authority-decision",
            {
                "run_id": self.composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "scope_id": self.composition.root_authority.scope_id,
            },
        )
        capability_decision_ref = _stable_id(
            "capability-decision",
            {
                "run_id": self.composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "manifest_id": self.composition.capability_manifest.manifest_id,
            },
        )
        return SpecialistExecutionRequest.create(
            run_id=self.composition.run_identity.run_id,
            parent_run_id=self.composition.run_identity.parent_run_id,
            correlation_id=self.composition.run_identity.correlation_id,
            adapter_name=adapter_name,
            command_name=decision.command_name,
            specialist=decision.skill_slug,
            project_root=str(project_root),
            skill_source_path=relative_skill_path,
            skill_source_digest=sha256(skill_path.read_bytes()).hexdigest(),
            task_input=pending.prompt,
            authority_decision_ref=authority_decision_ref,
            capability_decision_ref=capability_decision_ref,
            governance_status=validation.status,
            evaluated_governance_rules=validation.evaluated_rules,
            execution_constraints=constraints,
            execution_mode=self._execution_mode,
        )
