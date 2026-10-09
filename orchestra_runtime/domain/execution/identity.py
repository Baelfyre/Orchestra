from __future__ import annotations

from dataclasses import dataclass

from .correlation import validate_correlation_id


@dataclass(frozen=True, slots=True)
class RunIdentity:
    """Immutable execution-domain run identity."""

    run_id: str
    parent_run_id: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        run_id = self.run_id.strip()
        parent_run_id = self.parent_run_id.strip() if self.parent_run_id else None
        if not run_id:
            raise ValueError("run_id must be non-empty")
        if parent_run_id == run_id:
            raise ValueError("parent_run_id must differ from run_id")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        if self.correlation_id is not None:
            cid = validate_correlation_id(self.correlation_id)
            object.__setattr__(self, "correlation_id", cid)

    def to_dict(self) -> dict[str, str | None]:
        data: dict[str, str | None] = {"run_id": self.run_id, "parent_run_id": self.parent_run_id}
        if self.correlation_id is not None:
            data["correlation_id"] = self.correlation_id
        return data
