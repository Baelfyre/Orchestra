"""Host capabilities for bounded defensive review."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class ReviewChangeStatus(str, Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    RENAMED = "RENAMED"


@dataclass(frozen=True, slots=True)
class SpecialistReviewChange:
    """Immutable, host-created evidence for one candidate path change."""

    path: str
    status: ReviewChangeStatus
    previous_path: str | None = None
    base_content: str | None = None
    current_content: str | None = None

    def __post_init__(self) -> None:
        status = ReviewChangeStatus(self.status)
        if not _is_normalized_relative_path(self.path):
            raise ValueError("review change path must be normalized and relative")
        if self.previous_path is not None and not _is_normalized_relative_path(self.previous_path):
            raise ValueError("review change previous_path must be normalized and relative")
        if self.previous_path == self.path:
            raise ValueError("renamed review change must identify distinct paths")
        if any(content is not None and not isinstance(content, str) for content in (self.base_content, self.current_content)):
            raise ValueError("review change content must be text")
        if (status is ReviewChangeStatus.RENAMED) != (self.previous_path is not None):
            raise ValueError("only renamed review changes require previous_path")
        if status is ReviewChangeStatus.ADDED and (self.base_content is not None or self.current_content is None):
            raise ValueError("added review changes require only current content")
        if status is ReviewChangeStatus.MODIFIED and (
            self.base_content is None or self.current_content is None
        ):
            raise ValueError("modified review changes require base and current content")
        if status is ReviewChangeStatus.DELETED and (
            self.base_content is None or self.current_content is not None
        ):
            raise ValueError("deleted review changes require only base content")
        if status is ReviewChangeStatus.RENAMED and (
            self.base_content is None or self.current_content is None
        ):
            raise ValueError("renamed review changes require before and after content")
        object.__setattr__(self, "status", status)


def _is_normalized_relative_path(path: str) -> bool:
    return bool(
        isinstance(path, str)
        and "\x00" not in path
        and path
        and "\\" not in path
        and not path.startswith("/")
        and not (len(path) > 1 and path[1] == ":")
        and not any(part in {"", ".", ".."} for part in path.split("/"))
    )


@runtime_checkable
class ReadOnlyWorkspace(Protocol):
    """Read-only content and change manifest exposed to a defensive reviewer."""

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]: ...

    def read_text(self, relative_path: str, *, max_bytes: int) -> str: ...

    def list_changes(self) -> tuple[SpecialistReviewChange, ...]: ...


@runtime_checkable
class ReadOnlyWorkspaceSource(Protocol):
    """Provider API used only by the trusted host to copy current candidate bytes."""

    @property
    def repository_root(self) -> Path | str: ...

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]: ...

    def read_bytes(self, relative_path: str, *, max_bytes: int) -> bytes: ...


@runtime_checkable
class ReadOnlyWorkspaceProvider(Protocol):
    """Trusted host source for review content; identity is computed by Orchestra."""

    def for_review(
        self,
        repository_root: Path,
        expected_paths: tuple[str, ...],
    ) -> ReadOnlyWorkspaceSource: ...
