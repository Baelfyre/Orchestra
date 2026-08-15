from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable


SOURCE_STATE_RECEIPT_SCHEMA_VERSION = "1.0.0"
VALIDATION_EXECUTION_RECEIPT_SCHEMA_VERSION = "1.0.0"

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class EvidenceMismatchError(ValueError):
    """Raised when a human/agent claim disagrees with machine-bound evidence."""


def _clean_nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(ord(ch) < 32 for ch in cleaned):
        raise ValueError(f"{field_name} must not contain control characters")
    return cleaned


def normalize_git_sha(value: str, field_name: str = "git_sha") -> str:
    cleaned = _clean_nonempty(value, field_name).lower()
    if not _GIT_SHA_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be an exact 40-character hexadecimal Git object id")
    return cleaned


def normalize_sha256(value: str, field_name: str = "sha256") -> str:
    cleaned = _clean_nonempty(value, field_name).lower()
    if not _SHA256_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be an exact 64-character hexadecimal SHA-256 digest")
    return cleaned


def normalize_timestamp(value: str, field_name: str = "timestamp") -> str:
    cleaned = _clean_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an RFC3339/ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize supported JSON data deterministically for hashing and transport."""
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical Orchestra JSON: {exc}") from exc
    return payload.encode("utf-8")


def receipt_digest(value: Any) -> str:
    """Return a stable SHA-256 identity over canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _validate_repository(value: str) -> str:
    cleaned = _clean_nonempty(value, "repository")
    if not _REPOSITORY_RE.fullmatch(cleaned):
        raise ValueError("repository must use 'owner/name' form")
    return cleaned


def _validate_optional_positive_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer when provided")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive when provided")
    return value


@dataclass(frozen=True, slots=True)
class SourceStateReceipt:
    """Machine-bound source-repository identity used for canonical promotion checks."""

    repository: str
    canonical_branch: str
    live_canonical_sha: str
    verification_timestamp: str
    verification_method: str
    pull_request_number: int | None = None
    exact_pr_head: str | None = None
    merge_or_squash_sha: str | None = None
    tree_sha: str | None = None
    schema_version: str = SOURCE_STATE_RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SOURCE_STATE_RECEIPT_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported source-state receipt schema_version '{self.schema_version}'"
            )
        object.__setattr__(self, "repository", _validate_repository(self.repository))
        object.__setattr__(self, "canonical_branch", _clean_nonempty(self.canonical_branch, "canonical_branch"))
        object.__setattr__(self, "live_canonical_sha", normalize_git_sha(self.live_canonical_sha, "live_canonical_sha"))
        object.__setattr__(self, "verification_timestamp", normalize_timestamp(self.verification_timestamp, "verification_timestamp"))
        object.__setattr__(self, "verification_method", _clean_nonempty(self.verification_method, "verification_method"))
        object.__setattr__(self, "pull_request_number", _validate_optional_positive_int(self.pull_request_number, "pull_request_number"))

        if self.exact_pr_head is not None:
            object.__setattr__(self, "exact_pr_head", normalize_git_sha(self.exact_pr_head, "exact_pr_head"))
        if self.merge_or_squash_sha is not None:
            object.__setattr__(self, "merge_or_squash_sha", normalize_git_sha(self.merge_or_squash_sha, "merge_or_squash_sha"))
        if self.tree_sha is not None:
            object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))

        if self.pull_request_number is not None and self.exact_pr_head is None:
            raise ValueError("exact_pr_head is required when pull_request_number is provided")
        if self.exact_pr_head is not None and self.pull_request_number is None:
            raise ValueError("pull_request_number is required when exact_pr_head is provided")
        if self.merge_or_squash_sha is not None:
            if self.pull_request_number is None:
                raise ValueError("pull_request_number is required when merge_or_squash_sha is provided")
            if self.merge_or_squash_sha != self.live_canonical_sha:
                raise EvidenceMismatchError(
                    "merge_or_squash_sha must equal live_canonical_sha for a canonical closeout receipt"
                )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "canonical_branch": self.canonical_branch,
            "live_canonical_sha": self.live_canonical_sha,
            "verification_timestamp": self.verification_timestamp,
            "verification_method": self.verification_method,
        }
        if self.pull_request_number is not None:
            data["pull_request_number"] = self.pull_request_number
        if self.exact_pr_head is not None:
            data["exact_pr_head"] = self.exact_pr_head
        if self.merge_or_squash_sha is not None:
            data["merge_or_squash_sha"] = self.merge_or_squash_sha
        if self.tree_sha is not None:
            data["tree_sha"] = self.tree_sha
        return data

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())

    def assert_canonical_sha(self, claimed_sha: str) -> None:
        candidate = normalize_git_sha(claimed_sha, "claimed_sha")
        if candidate != self.live_canonical_sha:
            raise EvidenceMismatchError(
                f"claimed canonical SHA '{candidate}' does not match source receipt '{self.live_canonical_sha}'"
            )

    def assert_pr_head(self, claimed_sha: str) -> None:
        if self.exact_pr_head is None:
            raise EvidenceMismatchError("source receipt does not contain an exact PR head")
        candidate = normalize_git_sha(claimed_sha, "claimed_pr_head")
        if candidate != self.exact_pr_head:
            raise EvidenceMismatchError(
                f"claimed PR head '{candidate}' does not match source receipt '{self.exact_pr_head}'"
            )


@dataclass(frozen=True, slots=True)
class ValidationExecutionReceipt:
    """Exact command result whose authoritative verdict is derived from exit_code."""

    command_id: str
    command: tuple[str, ...]
    exit_code: int
    started_at: str
    finished_at: str
    stdout_sha256: str
    stderr_sha256: str
    head_before: str | None = None
    head_after: str | None = None
    evidence_ref: str | None = None
    schema_version: str = VALIDATION_EXECUTION_RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VALIDATION_EXECUTION_RECEIPT_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported validation receipt schema_version '{self.schema_version}'"
            )
        object.__setattr__(self, "command_id", _clean_nonempty(self.command_id, "command_id"))
        if not isinstance(self.command, tuple) or not self.command:
            raise ValueError("command must be a non-empty tuple of argument strings")
        normalized_command = tuple(_clean_nonempty(part, "command argument") for part in self.command)
        object.__setattr__(self, "command", normalized_command)

        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise TypeError("exit_code must be an integer")

        started = normalize_timestamp(self.started_at, "started_at")
        finished = normalize_timestamp(self.finished_at, "finished_at")
        if datetime.fromisoformat(finished.replace("Z", "+00:00")) < datetime.fromisoformat(started.replace("Z", "+00:00")):
            raise ValueError("finished_at must not precede started_at")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "finished_at", finished)
        object.__setattr__(self, "stdout_sha256", normalize_sha256(self.stdout_sha256, "stdout_sha256"))
        object.__setattr__(self, "stderr_sha256", normalize_sha256(self.stderr_sha256, "stderr_sha256"))

        if self.head_before is not None:
            object.__setattr__(self, "head_before", normalize_git_sha(self.head_before, "head_before"))
        if self.head_after is not None:
            object.__setattr__(self, "head_after", normalize_git_sha(self.head_after, "head_after"))
        if self.evidence_ref is not None:
            object.__setattr__(self, "evidence_ref", _clean_nonempty(self.evidence_ref, "evidence_ref"))

    @property
    def verdict(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"

    @property
    def exact_state_preserved(self) -> bool | None:
        if self.head_before is None or self.head_after is None:
            return None
        return self.head_before == self.head_after

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "verdict": self.verdict,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }
        if self.head_before is not None:
            data["head_before"] = self.head_before
        if self.head_after is not None:
            data["head_after"] = self.head_after
        if self.evidence_ref is not None:
            data["evidence_ref"] = self.evidence_ref
        return data

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())

    def assert_claimed_verdict(self, claimed_verdict: str) -> None:
        claimed = _clean_nonempty(claimed_verdict, "claimed_verdict").upper()
        if claimed not in {"PASS", "FAIL"}:
            raise ValueError("claimed_verdict must be PASS or FAIL")
        if claimed != self.verdict:
            raise EvidenceMismatchError(
                f"claimed verdict '{claimed}' conflicts with exit-code-derived verdict '{self.verdict}'"
            )


def build_validation_execution_receipt(
    *,
    command_id: str,
    command: Iterable[str],
    exit_code: int,
    started_at: str,
    finished_at: str,
    stdout: bytes | str = b"",
    stderr: bytes | str = b"",
    head_before: str | None = None,
    head_after: str | None = None,
    evidence_ref: str | None = None,
) -> ValidationExecutionReceipt:
    def _as_bytes(value: bytes | str, field_name: str) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        raise TypeError(f"{field_name} must be bytes or str")

    stdout_bytes = _as_bytes(stdout, "stdout")
    stderr_bytes = _as_bytes(stderr, "stderr")
    return ValidationExecutionReceipt(
        command_id=command_id,
        command=tuple(command),
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
        stdout_sha256=hashlib.sha256(stdout_bytes).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr_bytes).hexdigest(),
        head_before=head_before,
        head_after=head_after,
        evidence_ref=evidence_ref,
    )
