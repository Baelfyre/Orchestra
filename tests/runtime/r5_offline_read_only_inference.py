"""TEST_ONLY in-memory broker and snapshot-only specialist engine for R5."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from types import MappingProxyType
from time import monotonic

from orchestra_runtime.application.ports.specialist_execution import (
    ReadOnlyWorkspace,
    ReviewChangeStatus,
    SpecialistReviewChange,
)
from orchestra_runtime.domain.execution.operation_contracts import (
    DEFENSIVE_SECURITY_REVIEW,
    ReadOnlySpecialistExecutionRequest,
    SpecialistReviewResult,
    SpecialistReviewStatus,
)
from orchestra_runtime.interfaces import IReadOnlySpecialistExecutionEngine
from orchestra_runtime.specialist_execution import _review_snapshot_digest


TEST_ONLY_REPOSITORY_IDENTITY = "TEST_ONLY:r5-offline-synthetic"
MAX_TEST_FILES = 32
MAX_TEST_PATH_BYTES = 256
MAX_TEST_TASK_INPUT_BYTES = 4096
MAX_TEST_FILE_BYTES = 8192
MAX_TEST_TOTAL_BYTES = 16384
MAX_TEST_OUTPUT_BYTES = 4096
MAX_TEST_RESPONSE_SECONDS = 2.0
TEST_ONLY_CONCLUSION = (
    "TEST_ONLY: OFFLINE_STUB_NO_INFERENCE; no security judgment or authorization is made."
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_BROKER_FIELDS = frozenset({"request", "workspace"})
_RESPONSE_FIELDS = frozenset(
    {
        "request_id",
        "request_digest",
        "workspace_snapshot_digest",
        "status",
        "conclusion",
        "findings",
        "evidence_refs",
    }
)


def _json_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _content_digest(content: str | None) -> str | None:
    if content is None:
        return None
    return sha256(content.encode("utf-8", errors="strict")).hexdigest()


def _content_digests(
    changes: tuple[SpecialistReviewChange, ...],
) -> tuple[tuple[str, str | None, str | None], ...]:
    return tuple(
        (change.path, _content_digest(change.base_content), _content_digest(change.current_content))
        for change in changes
    )


def _inventory_digest(
    changes: tuple[SpecialistReviewChange, ...],
    content_digests: tuple[tuple[str, str | None, str | None], ...],
) -> str:
    return _json_digest(
        {
            "schema": "TEST_ONLY:r5-snapshot-inventory.v1",
            "changes": [
                {
                    "path": change.path,
                    "status": change.status.value,
                    "previous_path": change.previous_path,
                }
                for change in changes
            ],
            "content_digests": [list(item) for item in content_digests],
        }
    )


def _snapshot_identity(
    repository_identity: str,
    base_sha: str,
    commit_sha: str,
    tree_sha: str,
) -> dict[str, str]:
    return {
        "repository_identity": repository_identity,
        "base_sha": base_sha,
        "head_sha": commit_sha,
        "tree_sha": tree_sha,
    }


@dataclass(frozen=True, slots=True)
class TrustedTestSnapshot:
    """Test-only IDs are syntax-checked; no Git identity or commit-tree proof is made."""

    repository_identity: str
    base_sha: str
    commit_sha: str
    tree_sha: str
    changes: tuple[SpecialistReviewChange, ...]
    inventory_digest: str
    content_digests: tuple[tuple[str, str | None, str | None], ...]
    workspace_snapshot_digest: str

    def __post_init__(self) -> None:
        if self.repository_identity != TEST_ONLY_REPOSITORY_IDENTITY:
            raise ValueError("TEST_ONLY snapshot identity must remain synthetic")
        for name in ("base_sha", "commit_sha", "tree_sha"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _GIT_SHA.fullmatch(value):
                raise ValueError(f"TEST_ONLY {name} must be a full lowercase Git SHA")
        if not isinstance(self.changes, tuple) or not self.changes or len(self.changes) > MAX_TEST_FILES:
            raise ValueError("TEST_ONLY snapshot changes must be a bounded nonempty tuple")
        if any(type(change) is not SpecialistReviewChange for change in self.changes):
            raise ValueError("TEST_ONLY snapshot changes must use SpecialistReviewChange")
        ordered = tuple(sorted(self.changes, key=lambda change: change.path.encode("utf-8")))
        if ordered != self.changes or len({change.path for change in self.changes}) != len(self.changes):
            raise ValueError("TEST_ONLY snapshot changes must have unique sorted paths")
        inventory_paths: set[str] = set()
        total_bytes = 0
        for change in self.changes:
            for path in (change.path, change.previous_path):
                if path is not None:
                    encoded_path = path.encode("utf-8", errors="strict")
                    if len(encoded_path) > MAX_TEST_PATH_BYTES:
                        raise ValueError("TEST_ONLY snapshot path exceeds its byte limit")
                    if path in inventory_paths:
                        raise ValueError("TEST_ONLY snapshot paths collide")
                    inventory_paths.add(path)
            for content in (change.base_content, change.current_content):
                if content is not None:
                    content_bytes = content.encode("utf-8", errors="strict")
                    if len(content_bytes) > MAX_TEST_FILE_BYTES:
                        raise ValueError("TEST_ONLY snapshot file exceeds its byte limit")
                    total_bytes += len(content_bytes)
        if len(inventory_paths) > MAX_TEST_FILES or total_bytes > MAX_TEST_TOTAL_BYTES:
            raise ValueError("TEST_ONLY snapshot inventory exceeds its bound")

        expected_content_digests = _content_digests(self.changes)
        if self.content_digests != expected_content_digests:
            raise ValueError("TEST_ONLY content digests do not match snapshot content")
        if (
            not isinstance(self.inventory_digest, str)
            or not _SHA256.fullmatch(self.inventory_digest)
            or self.inventory_digest != _inventory_digest(self.changes, expected_content_digests)
        ):
            raise ValueError("TEST_ONLY inventory digest does not match snapshot inventory")
        expected_snapshot_digest = _review_snapshot_digest(
            self.changes,
            _snapshot_identity(self.repository_identity, self.base_sha, self.commit_sha, self.tree_sha),
        )
        if (
            not isinstance(self.workspace_snapshot_digest, str)
            or not _SHA256.fullmatch(self.workspace_snapshot_digest)
            or self.workspace_snapshot_digest != expected_snapshot_digest
        ):
            raise ValueError("TEST_ONLY snapshot digest does not match commit, tree, and content")


def make_trusted_test_snapshot(
    changes: tuple[SpecialistReviewChange, ...],
    *,
    base_sha: str,
    commit_sha: str,
    tree_sha: str,
) -> TrustedTestSnapshot:
    """Build a deterministic fixture using the existing runtime digest algorithm."""
    ordered = tuple(sorted(changes, key=lambda change: change.path.encode("utf-8")))
    content_digests = _content_digests(ordered)
    return TrustedTestSnapshot(
        TEST_ONLY_REPOSITORY_IDENTITY,
        base_sha,
        commit_sha,
        tree_sha,
        ordered,
        _inventory_digest(ordered, content_digests),
        content_digests,
        _review_snapshot_digest(
            ordered,
            _snapshot_identity(TEST_ONLY_REPOSITORY_IDENTITY, base_sha, commit_sha, tree_sha),
        ),
    )


class InMemoryReadOnlyWorkspace:
    """TEST_ONLY workspace with the existing read-only protocol and no provider."""

    __slots__ = ("__files", "__changes")

    def __init__(self, snapshot: TrustedTestSnapshot) -> None:
        if type(snapshot) is not TrustedTestSnapshot:
            raise TypeError("TEST_ONLY workspace requires TrustedTestSnapshot")
        self.__files = MappingProxyType(
            {
                change.path: change.current_content
                for change in snapshot.changes
                if change.current_content is not None
            }
        )
        self.__changes = snapshot.changes

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]:
        if not isinstance(relative_path, str) or "\\" in relative_path:
            raise ValueError("TEST_ONLY path must be normalized relative text")
        if relative_path:
            if relative_path.startswith("/") or any(part in {"", ".", ".."} for part in relative_path.split("/")):
                raise ValueError("TEST_ONLY path must be normalized relative text")
            prefix = f"{relative_path}/"
            return tuple(path for path in self.__files if path == relative_path or path.startswith(prefix))
        return tuple(self.__files)

    def read_text(self, relative_path: str, *, max_bytes: int) -> str:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ValueError("TEST_ONLY max_bytes must be a positive integer")
        if not isinstance(relative_path, str) or "\\" in relative_path:
            raise ValueError("TEST_ONLY path must be normalized relative text")
        if relative_path.startswith("/") or any(part in {"", ".", ".."} for part in relative_path.split("/")):
            raise ValueError("TEST_ONLY path must be normalized relative text")
        try:
            content = self.__files[relative_path]
        except KeyError as exc:
            raise ValueError("TEST_ONLY path is outside the in-memory snapshot") from exc
        if len(content.encode("utf-8", errors="strict")) > min(max_bytes, MAX_TEST_FILE_BYTES):
            raise ValueError("TEST_ONLY file exceeds requested byte limit")
        return content

    def list_changes(self) -> tuple[SpecialistReviewChange, ...]:
        return self.__changes


class DeterministicInMemoryReviewBroker:
    """TEST_ONLY exact-field broker; it never interprets source text as authority.

    The two-second check detects late synchronous returns; it cannot cancel work.
    """

    __slots__ = ("__snapshot",)

    def __init__(self, snapshot: TrustedTestSnapshot) -> None:
        if type(snapshot) is not TrustedTestSnapshot:
            raise TypeError("TEST_ONLY broker requires TrustedTestSnapshot")
        self.__snapshot = snapshot

    def review(self, payload: Mapping[str, object]) -> SpecialistReviewResult:
        started = monotonic()
        if type(payload) is not dict or frozenset(payload) != _BROKER_FIELDS:
            raise ValueError("TEST_ONLY broker accepts only request and workspace fields")
        request = self._assert_request_scope(payload["request"])
        workspace = payload["workspace"]
        if type(workspace) is not InMemoryReadOnlyWorkspace or not isinstance(workspace, ReadOnlyWorkspace):
            raise ValueError("TEST_ONLY broker requires the in-memory ReadOnlyWorkspace")

        changes = workspace.list_changes()
        if changes != self.__snapshot.changes:
            raise ValueError("TEST_ONLY workspace changes do not match trusted input")
        expected_paths = tuple(
            change.path for change in self.__snapshot.changes if change.current_content is not None
        )
        if workspace.list_paths() != expected_paths:
            raise ValueError("TEST_ONLY workspace inventory does not match trusted input")
        for path in expected_paths:
            expected = next(change.current_content for change in changes if change.path == path)
            if workspace.read_text(path, max_bytes=MAX_TEST_FILE_BYTES) != expected:
                raise ValueError("TEST_ONLY workspace content is stale or mismatched")

        observed_digests = _content_digests(changes)
        if (
            observed_digests != self.__snapshot.content_digests
            or _inventory_digest(changes, observed_digests) != self.__snapshot.inventory_digest
            or _review_snapshot_digest(
                changes,
                _snapshot_identity(
                    self.__snapshot.repository_identity,
                    self.__snapshot.base_sha,
                    self.__snapshot.commit_sha,
                    self.__snapshot.tree_sha,
                ),
            )
            != request.workspace_snapshot_digest
        ):
            raise ValueError("TEST_ONLY snapshot digests do not match request and content")

        response = {
            "request_id": request.request_id,
            "request_digest": request.request_digest,
            "workspace_snapshot_digest": request.workspace_snapshot_digest,
            "status": SpecialistReviewStatus.INCONCLUSIVE.value,
            "conclusion": TEST_ONLY_CONCLUSION,
            "findings": [],
            "evidence_refs": list(self._snapshot_evidence_refs(request, changes)),
        }
        result = self.decode_response(request, response)
        if monotonic() - started > MAX_TEST_RESPONSE_SECONDS:
            raise ValueError("TEST_ONLY broker response exceeded its wall-clock deadline")
        return result

    def decode_response(
        self,
        request: ReadOnlySpecialistExecutionRequest,
        response: object,
    ) -> SpecialistReviewResult:
        """Validate the closed synthetic response shape before constructing a result."""
        request = self._assert_request_scope(request)
        if type(response) is not dict:
            raise ValueError("TEST_ONLY broker response must be an object")
        try:
            encoded_response = json.dumps(
                response,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("TEST_ONLY broker response is malformed") from exc
        if len(encoded_response) > MAX_TEST_OUTPUT_BYTES:
            raise ValueError("TEST_ONLY broker result exceeds its byte limit")
        if frozenset(response) != _RESPONSE_FIELDS:
            raise ValueError("TEST_ONLY broker response fields are invalid")
        if (
            response["request_id"] != request.request_id
            or response["request_digest"] != request.request_digest
            or response["workspace_snapshot_digest"] != request.workspace_snapshot_digest
        ):
            raise ValueError("TEST_ONLY broker response binding is stale or mismatched")
        if (
            response["status"] != SpecialistReviewStatus.INCONCLUSIVE.value
            or response["conclusion"] != TEST_ONLY_CONCLUSION
            or type(response["findings"]) is not list
            or response["findings"]
        ):
            raise ValueError("TEST_ONLY broker response cannot contain inference or authority")
        evidence_refs = response["evidence_refs"]
        if (
            type(evidence_refs) is not list
            or not evidence_refs
            or len(evidence_refs) > MAX_TEST_FILES
            or any(not isinstance(ref, str) for ref in evidence_refs)
            or len(set(evidence_refs)) != len(evidence_refs)
        ):
            raise ValueError("TEST_ONLY broker evidence refs are malformed")
        if any(
            ref not in self._snapshot_evidence_refs(request, self.__snapshot.changes)
            for ref in evidence_refs
        ):
            raise ValueError("TEST_ONLY evidence ref is outside the request snapshot inventory")

        result = SpecialistReviewResult.create(
            request,
            SpecialistReviewStatus.INCONCLUSIVE,
            TEST_ONLY_CONCLUSION,
            tuple(evidence_refs),
            (),
        )
        encoded_result = json.dumps(
            result.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        if len(encoded_result) > MAX_TEST_OUTPUT_BYTES:
            raise ValueError("TEST_ONLY broker result exceeds its byte limit")
        result.assert_matches(request)
        return result

    def _assert_request_scope(self, request: object) -> ReadOnlySpecialistExecutionRequest:
        if (
            not isinstance(request, ReadOnlySpecialistExecutionRequest)
            or type(request) is not ReadOnlySpecialistExecutionRequest
        ):
            raise ValueError("TEST_ONLY broker requires ReadOnlySpecialistExecutionRequest")
        if (
            request.operation_id != DEFENSIVE_SECURITY_REVIEW.operation_id
            or request.specialist != "cipher"
            or request.command_name != "security-check"
        ):
            raise ValueError("TEST_ONLY broker accepts only the fixed defensive review request")
        if len(request.task_input.encode("utf-8", errors="strict")) > MAX_TEST_TASK_INPUT_BYTES:
            raise ValueError("TEST_ONLY task input exceeds its byte limit")
        if request.workspace_snapshot_digest != self.__snapshot.workspace_snapshot_digest:
            raise ValueError("TEST_ONLY request snapshot is stale or mismatched")
        return request

    @staticmethod
    def _snapshot_evidence_refs(
        request: ReadOnlySpecialistExecutionRequest,
        changes: tuple[SpecialistReviewChange, ...],
    ) -> tuple[str, ...]:
        refs = []
        for change in changes:
            if change.current_content is not None:
                side = "current"
                path = change.path
                content_digest = _content_digest(change.current_content)
            else:
                side = "base"
                path = change.previous_path or change.path
                content_digest = _content_digest(change.base_content)
            refs.append(
                f"request:{request.request_id}:{request.request_digest}:"
                f"snapshot:{request.workspace_snapshot_digest}:{side}:{path}:sha256:{content_digest}"
            )
        return tuple(refs)


class SyntheticSnapshotOnlyEngine(IReadOnlySpecialistExecutionEngine):
    """TEST_ONLY engine receiving an in-memory view in the ordinary Python process.

    This fixture has no provider, network, credential, or filesystem code. It does
    not establish process isolation or restrict ambient Python process capabilities.
    """

    __slots__ = ("__broker",)

    def __init__(self, broker: DeterministicInMemoryReviewBroker) -> None:
        if type(broker) is not DeterministicInMemoryReviewBroker:
            raise TypeError("TEST_ONLY engine requires DeterministicInMemoryReviewBroker")
        self.__broker = broker

    def execute_read_only(
        self,
        request: ReadOnlySpecialistExecutionRequest,
        workspace: ReadOnlyWorkspace,
    ) -> SpecialistReviewResult:
        return self.__broker.review({"request": request, "workspace": workspace})
