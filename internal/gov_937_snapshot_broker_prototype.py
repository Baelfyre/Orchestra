"""Synthetic-only snapshot broker feasibility prototype; never runtime-wired."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import unicodedata
from typing import Mapping


PROTOTYPE_VERSION = "orchestra.gov-937.snapshot-broker.v1"
NON_AUTHORIZING_MODE = "TEST_ONLY_NON_AUTHORIZING"
SYNTHETIC_ROOT_MARKER = ".orchestra-synthetic-only"
SYNTHETIC_ROOT_MARKER_CONTENT = b"orchestra.gov-937.synthetic-fixture.v1"
MAX_FILES = 4
MAX_FILE_BYTES = 4096
MAX_TOTAL_BYTES = 12288
MAX_OUTPUT_BYTES = 2048
MAX_ASSESSMENT_SECONDS = 0.05
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SECRET_MARKER = b"TEST_SECRET_"


class BrokerRejected(ValueError):
    """A bounded failure code that never includes candidate content."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def _path(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise BrokerRejected("INVALID_PATH")
    if unicodedata.normalize("NFC", value) != value:
        raise BrokerRejected("NON_CANONICAL_PATH")
    parts = value.split("/")
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise BrokerRejected("INVALID_PATH")
    if ":" in parts[0]:
        raise BrokerRejected("INVALID_PATH")
    return value


def _path_keys(paths: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(_path(item) for item in paths)
    keys = tuple(unicodedata.normalize("NFC", item).casefold() for item in normalized)
    if len(set(keys)) != len(keys):
        raise BrokerRejected("PATH_NORMALIZATION_COLLISION")
    return normalized


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


@dataclass(frozen=True, slots=True)
class SyntheticCandidateIdentity:
    repository_id: str
    base_digest: str
    head_digest: str
    tree_digest: str
    approved_file_digests: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.repository_id, str) or not self.repository_id.startswith("synthetic://gov-937/"):
            raise BrokerRejected("NON_SYNTHETIC_CANDIDATE")
        if not all(_valid_sha(value) for value in (self.base_digest, self.head_digest, self.tree_digest)):
            raise BrokerRejected("INVALID_CANDIDATE_IDENTITY")
        paths = tuple(path for path, _ in self.approved_file_digests)
        _path_keys(paths)
        if not paths or len(paths) > MAX_FILES:
            raise BrokerRejected("INVALID_ALLOWLIST")
        if paths != tuple(sorted(paths, key=lambda item: item.encode("utf-8"))):
            raise BrokerRejected("INVALID_ALLOWLIST")
        if any(not _valid_sha(digest) for _, digest in self.approved_file_digests):
            raise BrokerRejected("INVALID_ALLOWLIST")

    def to_dict(self) -> dict[str, object]:
        return {
            "repository_id": self.repository_id,
            "base_digest": self.base_digest,
            "head_digest": self.head_digest,
            "tree_digest": self.tree_digest,
            "approved_file_digests": [
                {"path": path, "sha256": digest}
                for path, digest in self.approved_file_digests
            ],
        }


def make_synthetic_candidate_identity(
    repository_id: str,
    base_content: bytes,
    tree_files: Mapping[str, bytes],
    approved_paths: tuple[str, ...],
) -> SyntheticCandidateIdentity:
    """Build fixture identity from host-known synthetic bytes, never from a client root."""
    if not isinstance(base_content, bytes) or any(
        not isinstance(path, str) or not isinstance(content, bytes)
        for path, content in tree_files.items()
    ):
        raise BrokerRejected("INVALID_CANDIDATE_IDENTITY")
    paths = _path_keys(tuple(tree_files))
    if paths != tuple(sorted(paths, key=lambda item: item.encode("utf-8"))):
        paths = tuple(sorted(paths, key=lambda item: item.encode("utf-8")))
    files = {path: tree_files[path] for path in paths}
    approved = tuple(sorted(_path_keys(approved_paths), key=lambda item: item.encode("utf-8")))
    if not set(approved).issubset(files):
        raise BrokerRejected("INVALID_CANDIDATE_IDENTITY")
    tree_digest = _digest(_canonical_bytes([
        {"path": path, "sha256": _digest(content)} for path, content in files.items()
    ]))
    base_digest = _digest(base_content)
    head_digest = _digest(_canonical_bytes({"base_digest": base_digest, "tree_digest": tree_digest}))
    approved_digests = tuple((path, _digest(files[path])) for path in approved)
    return SyntheticCandidateIdentity(repository_id, base_digest, head_digest, tree_digest, approved_digests)


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    path: str
    content: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class SnapshotEnvelope:
    schema_version: str
    mode: str
    request_id: str
    request_digest: str
    candidate: SyntheticCandidateIdentity
    runtime_identity_digest: str
    requested_paths: tuple[str, ...]
    files: tuple[SnapshotFile, ...]
    manifest_digest: str
    content_digest: str
    snapshot_digest: str


@dataclass(frozen=True, slots=True)
class MockFinding:
    path: str
    message: str
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class MockAssessmentResult:
    schema_version: str
    mode: str
    classification: str
    test_only: bool
    request_id: str
    request_digest: str
    snapshot_digest: str
    findings: tuple[MockFinding, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "classification": self.classification,
            "test_only": self.test_only,
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            "snapshot_digest": self.snapshot_digest,
            "findings": [
                {
                    "path": finding.path,
                    "message": finding.message,
                    "evidence_sha256": finding.evidence_sha256,
                    "classification": "TEST_ONLY",
                }
                for finding in self.findings
            ],
        }


def _stat_key(info: os.stat_result) -> tuple[int, ...]:
    return (
        int(info.st_dev), int(info.st_ino), int(info.st_mode), int(info.st_size),
        int(info.st_mtime_ns), int(info.st_nlink),
        int(getattr(info, "st_file_attributes", 0)),
    )


def _reject_reparse(info: os.stat_result) -> None:
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    if stat.S_ISLNK(info.st_mode) or int(getattr(info, "st_file_attributes", 0)) & reparse_flag:
        raise BrokerRejected("SYMLINK_OR_REPARSE_POINT")


def _read_fixture_file(root: Path, relative_path: str, limit: int) -> bytes:
    parts = _path(relative_path).split("/")
    parent = root
    final_path: Path | None = None
    for index, part in enumerate(parts):
        try:
            entries = tuple(parent.iterdir())
        except OSError:
            raise BrokerRejected("SNAPSHOT_UNAVAILABLE") from None
        names = tuple(entry.name for entry in entries)
        keys = tuple(unicodedata.normalize("NFC", name).casefold() for name in names)
        if len(set(keys)) != len(keys):
            raise BrokerRejected("PATH_NORMALIZATION_COLLISION")
        matches = tuple(entry for entry in entries if entry.name == part)
        if len(matches) != 1:
            raise BrokerRejected("SNAPSHOT_PATH_NOT_FOUND")
        final_path = matches[0]
        try:
            info = os.lstat(final_path)
        except OSError:
            raise BrokerRejected("SNAPSHOT_UNAVAILABLE") from None
        _reject_reparse(info)
        last = index == len(parts) - 1
        if last:
            if not stat.S_ISREG(info.st_mode):
                raise BrokerRejected("NOT_REGULAR_FILE")
            if info.st_nlink != 1:
                raise BrokerRejected("HARDLINK_ALIAS")
            before = _stat_key(info)
        elif not stat.S_ISDIR(info.st_mode):
            raise BrokerRejected("NOT_DIRECTORY")
        else:
            parent = final_path
    assert final_path is not None
    flags = os.O_RDONLY | int(getattr(os, "O_BINARY", 0)) | int(getattr(os, "O_NOFOLLOW", 0))
    try:
        descriptor = os.open(final_path, flags)
    except OSError:
        raise BrokerRejected("SNAPSHOT_UNAVAILABLE") from None
    try:
        opened = os.fstat(descriptor)
        _reject_reparse(opened)
        if _stat_key(opened) != before or not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise BrokerRejected("SNAPSHOT_CHANGED_DURING_READ")
        chunks: list[bytes] = []
        size = 0
        while size <= limit:
            chunk = os.read(descriptor, min(1024, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        content = b"".join(chunks)
        if len(content) > limit:
            raise BrokerRejected("FILE_TOO_LARGE")
        after = os.fstat(descriptor)
        current_path = os.lstat(final_path)
        _reject_reparse(current_path)
        if _stat_key(after) != before or _stat_key(current_path) != before:
            raise BrokerRejected("SNAPSHOT_CHANGED_DURING_READ")
        return content
    except OSError:
        raise BrokerRejected("SNAPSHOT_UNAVAILABLE") from None
    finally:
        os.close(descriptor)


def _validate_content(content: bytes) -> None:
    if b"\x00" in content:
        raise BrokerRejected("BINARY_CONTENT")
    try:
        content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise BrokerRejected("UNSUPPORTED_ENCODING") from None
    if _SECRET_MARKER in content:
        raise BrokerRejected("SYNTHETIC_SECRET_MARKER")


def _envelope_digests(
    candidate: SyntheticCandidateIdentity,
    runtime_identity_digest: str,
    paths: tuple[str, ...],
    files: tuple[SnapshotFile, ...],
) -> tuple[str, str, str, str, str]:
    manifest_digest = _digest(_canonical_bytes({
        "candidate": candidate.to_dict(),
        "requested_paths": list(paths),
        "files": [{"path": item.path, "sha256": item.sha256} for item in files],
    }))
    content_hasher = sha256()
    for item in files:
        path_bytes = item.path.encode("utf-8")
        content_hasher.update(len(path_bytes).to_bytes(8, "big"))
        content_hasher.update(path_bytes)
        content_hasher.update(len(item.content).to_bytes(8, "big"))
        content_hasher.update(item.content)
    content_digest = content_hasher.hexdigest()
    request_digest = _digest(_canonical_bytes({
        "schema_version": PROTOTYPE_VERSION,
        "mode": NON_AUTHORIZING_MODE,
        "candidate": candidate.to_dict(),
        "runtime_identity_digest": runtime_identity_digest,
        "requested_paths": list(paths),
        "manifest_digest": manifest_digest,
        "content_digest": content_digest,
    }))
    request_id = f"snapshot-request.{request_digest[:24]}"
    snapshot_digest = _digest(_canonical_bytes({
        "request_id": request_id,
        "request_digest": request_digest,
        "manifest_digest": manifest_digest,
        "content_digest": content_digest,
    }))
    return manifest_digest, content_digest, request_digest, request_id, snapshot_digest


class SyntheticSnapshotProducer:
    """Host-created producer pinned to a marker-bearing temporary fixture root."""

    def __init__(
        self,
        synthetic_root: Path,
        candidate: SyntheticCandidateIdentity,
        runtime_identity_digest: str,
    ) -> None:
        if type(candidate) is not SyntheticCandidateIdentity:
            raise BrokerRejected("INVALID_CANDIDATE_IDENTITY")
        if not _valid_sha(runtime_identity_digest):
            raise BrokerRejected("INVALID_RUNTIME_IDENTITY")
        root_arg = Path(synthetic_root)
        try:
            root_info = os.lstat(root_arg)
            _reject_reparse(root_info)
            if not stat.S_ISDIR(root_info.st_mode):
                raise BrokerRejected("NOT_SYNTHETIC_DIRECTORY")
            self._root = root_arg.resolve(strict=True)
        except OSError:
            raise BrokerRejected("NOT_SYNTHETIC_DIRECTORY") from None
        self._candidate = candidate
        self._runtime_identity_digest = runtime_identity_digest
        self._allowlist = tuple(path for path, _ in candidate.approved_file_digests)
        try:
            marker = _read_fixture_file(self._root, SYNTHETIC_ROOT_MARKER, 64)
        except BrokerRejected:
            raise BrokerRejected("NOT_SYNTHETIC_FIXTURE_ROOT") from None
        if marker != SYNTHETIC_ROOT_MARKER_CONTENT:
            raise BrokerRejected("NOT_SYNTHETIC_FIXTURE_ROOT")

    def build(self, requested_paths: tuple[str, ...]) -> SnapshotEnvelope:
        try:
            marker = _read_fixture_file(self._root, SYNTHETIC_ROOT_MARKER, 64)
        except BrokerRejected:
            raise BrokerRejected("NOT_SYNTHETIC_FIXTURE_ROOT") from None
        if marker != SYNTHETIC_ROOT_MARKER_CONTENT:
            raise BrokerRejected("NOT_SYNTHETIC_FIXTURE_ROOT")
        if not isinstance(requested_paths, tuple) or not requested_paths or len(requested_paths) > MAX_FILES:
            raise BrokerRejected("INVALID_REQUESTED_PATHS")
        paths = _path_keys(requested_paths)
        if paths != tuple(sorted(paths, key=lambda item: item.encode("utf-8"))):
            raise BrokerRejected("NON_CANONICAL_REQUEST_ORDER")
        if not set(paths).issubset(self._allowlist):
            raise BrokerRejected("PATH_NOT_ALLOWLISTED")
        expected = dict(self._candidate.approved_file_digests)
        files: list[SnapshotFile] = []
        total = 0
        for path in paths:
            content = _read_fixture_file(self._root, path, MAX_FILE_BYTES)
            _validate_content(content)
            file_digest = _digest(content)
            if file_digest != expected[path]:
                raise BrokerRejected("CANDIDATE_CONTENT_MISMATCH")
            total += len(content)
            if total > MAX_TOTAL_BYTES:
                raise BrokerRejected("SNAPSHOT_TOO_LARGE")
            files.append(SnapshotFile(path, content, file_digest))
        frozen_files = tuple(files)
        manifest, content, request, request_id, snapshot = _envelope_digests(
            self._candidate, self._runtime_identity_digest, paths, frozen_files
        )
        return SnapshotEnvelope(
            PROTOTYPE_VERSION, NON_AUTHORIZING_MODE, request_id, request,
            self._candidate, self._runtime_identity_digest, paths, frozen_files,
            manifest, content, snapshot,
        )


class DeterministicMockAssessmentEngine:
    """In-memory deterministic fixture scanner with no tool or provider surface."""

    async def assess(self, snapshot: SnapshotEnvelope) -> MockAssessmentResult:
        findings = tuple(
            MockFinding(
                item.path,
                "TEST_ONLY: synthetic marker detected; this is not Cipher review.",
                item.sha256,
            )
            for item in snapshot.files
            if b"TEST_ONLY_INTENTIONAL_FINDING" in item.content
        )
        return MockAssessmentResult(
            PROTOTYPE_VERSION,
            NON_AUTHORIZING_MODE,
            "TEST_ONLY",
            True,
            snapshot.request_id,
            snapshot.request_digest,
            snapshot.snapshot_digest,
            findings,
        )


class SnapshotOnlyBroker:
    """Verifies a synthetic envelope, then calls only its private deterministic mock."""

    def __init__(self, candidate: SyntheticCandidateIdentity, runtime_identity_digest: str) -> None:
        if type(candidate) is not SyntheticCandidateIdentity:
            raise BrokerRejected("INVALID_CANDIDATE_IDENTITY")
        if not _valid_sha(runtime_identity_digest):
            raise BrokerRejected("INVALID_RUNTIME_IDENTITY")
        self._candidate = candidate
        self._runtime_identity_digest = runtime_identity_digest
        self._allowlist = tuple(path for path, _ in candidate.approved_file_digests)
        self._expected_digests = dict(candidate.approved_file_digests)
        self._engine: DeterministicMockAssessmentEngine | None = DeterministicMockAssessmentEngine()
        self._seen_requests: set[str] = set()

    def _validate_snapshot(self, snapshot: SnapshotEnvelope) -> None:
        if type(snapshot) is not SnapshotEnvelope or type(snapshot.candidate) is not SyntheticCandidateIdentity:
            raise BrokerRejected("INVALID_SNAPSHOT")
        if snapshot.schema_version != PROTOTYPE_VERSION or snapshot.mode != NON_AUTHORIZING_MODE:
            raise BrokerRejected("INVALID_SNAPSHOT_MODE")
        if snapshot.candidate != self._candidate:
            raise BrokerRejected("CANDIDATE_IDENTITY_MISMATCH")
        if snapshot.runtime_identity_digest != self._runtime_identity_digest:
            raise BrokerRejected("RUNTIME_IDENTITY_MISMATCH")
        if not isinstance(snapshot.requested_paths, tuple) or not isinstance(snapshot.files, tuple):
            raise BrokerRejected("INVALID_SNAPSHOT")
        paths = _path_keys(snapshot.requested_paths)
        if not paths or paths != tuple(sorted(paths, key=lambda item: item.encode("utf-8"))):
            raise BrokerRejected("INVALID_SNAPSHOT_PATHS")
        if not set(paths).issubset(self._allowlist) or len(paths) > MAX_FILES or len(paths) != len(snapshot.files):
            raise BrokerRejected("PATH_NOT_ALLOWLISTED")
        total = 0
        for path, item in zip(paths, snapshot.files, strict=True):
            if type(item) is not SnapshotFile or item.path != path or not isinstance(item.content, bytes):
                raise BrokerRejected("INVALID_SNAPSHOT_FILE")
            if len(item.content) > MAX_FILE_BYTES:
                raise BrokerRejected("FILE_TOO_LARGE")
            _validate_content(item.content)
            actual_digest = _digest(item.content)
            if not _valid_sha(item.sha256) or actual_digest != item.sha256:
                raise BrokerRejected("FILE_DIGEST_MISMATCH")
            if actual_digest != self._expected_digests[path]:
                raise BrokerRejected("CANDIDATE_CONTENT_MISMATCH")
            total += len(item.content)
            if total > MAX_TOTAL_BYTES:
                raise BrokerRejected("SNAPSHOT_TOO_LARGE")
        manifest, content, request, request_id, snapshot_digest = _envelope_digests(
            snapshot.candidate,
            snapshot.runtime_identity_digest,
            paths,
            snapshot.files,
        )
        if (manifest, content, request, request_id, snapshot_digest) != (
            snapshot.manifest_digest,
            snapshot.content_digest,
            snapshot.request_digest,
            snapshot.request_id,
            snapshot.snapshot_digest,
        ):
            raise BrokerRejected("SNAPSHOT_DIGEST_MISMATCH")

    async def assess(self, snapshot: SnapshotEnvelope) -> MockAssessmentResult:
        if self._engine is None:
            raise BrokerRejected("MOCK_ENGINE_UNAVAILABLE")
        self._validate_snapshot(snapshot)
        if snapshot.request_id in self._seen_requests:
            raise BrokerRejected("REQUEST_REPLAY")
        self._seen_requests.add(snapshot.request_id)
        try:
            result = await asyncio.wait_for(
                self._engine.assess(snapshot), timeout=MAX_ASSESSMENT_SECONDS
            )
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            raise BrokerRejected("ASSESSMENT_TIMEOUT") from None
        except Exception:
            raise BrokerRejected("ASSESSMENT_FAILED") from None
        if type(result) is not MockAssessmentResult:
            raise BrokerRejected("MALFORMED_ASSESSMENT_RESULT")
        if (
            result.schema_version != PROTOTYPE_VERSION
            or result.mode != NON_AUTHORIZING_MODE
            or result.classification != "TEST_ONLY"
            or result.test_only is not True
            or result.request_id != snapshot.request_id
            or result.request_digest != snapshot.request_digest
            or result.snapshot_digest != snapshot.snapshot_digest
            or type(result.findings) is not tuple
        ):
            raise BrokerRejected("ASSESSMENT_RESULT_BINDING_MISMATCH")
        file_digests = {item.path: item.sha256 for item in snapshot.files}
        seen_findings: set[tuple[str, str, str]] = set()
        for finding in result.findings:
            if (
                type(finding) is not MockFinding
                or not isinstance(finding.path, str)
                or not isinstance(finding.message, str)
                or not finding.message.strip()
                or not _valid_sha(finding.evidence_sha256)
            ):
                raise BrokerRejected("MALFORMED_FINDING")
            if finding.path not in file_digests or finding.evidence_sha256 != file_digests[finding.path]:
                raise BrokerRejected("FINDING_EVIDENCE_MISMATCH")
            key = (finding.path, finding.message, finding.evidence_sha256)
            if key in seen_findings:
                raise BrokerRejected("DUPLICATE_FINDING")
            seen_findings.add(key)
        if len(_canonical_bytes(result.to_dict())) > MAX_OUTPUT_BYTES:
            raise BrokerRejected("ASSESSMENT_OUTPUT_TOO_LARGE")
        return result
