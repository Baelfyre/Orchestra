from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...shared.canonicalization import receipt_digest


WORKFLOW_SANITY_SCHEMA_VERSION = "orchestra.workflow-sanity.v1"


def _nonempty(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


@dataclass(frozen=True, slots=True)
class WorkflowSanityReceipt:
    command_name: str
    route_id: str
    specialist_id: str
    governance_required: bool
    validation_status: str
    validation_rules: tuple[str, ...]
    arbiter_disposition: str | None
    arbiter_reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    execution_order: tuple[str, ...]
    schema_version: str = WORKFLOW_SANITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != WORKFLOW_SANITY_SCHEMA_VERSION:
            raise ValueError(f"unsupported workflow sanity schema {self.schema_version!r}")
        object.__setattr__(self, "command_name", _nonempty(self.command_name, "command_name"))
        object.__setattr__(self, "route_id", _nonempty(self.route_id, "route_id"))
        object.__setattr__(self, "specialist_id", _nonempty(self.specialist_id, "specialist_id"))
        object.__setattr__(self, "validation_status", _nonempty(self.validation_status, "validation_status"))
        if not isinstance(self.governance_required, bool):
            raise TypeError("governance_required must be bool")
        if self.arbiter_disposition is not None:
            object.__setattr__(
                self,
                "arbiter_disposition",
                _nonempty(self.arbiter_disposition, "arbiter_disposition"),
            )
        for field_name in (
            "validation_rules",
            "arbiter_reason_codes",
            "evidence_refs",
            "execution_order",
        ):
            values = getattr(self, field_name)
            if not isinstance(values, tuple):
                raise TypeError(f"{field_name} must be a tuple")
            cleaned = tuple(_nonempty(value, field_name) for value in values)
            if field_name == "execution_order" and not cleaned:
                raise ValueError("execution_order must not be empty")
            object.__setattr__(self, field_name, cleaned)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command_name": self.command_name,
            "route_id": self.route_id,
            "specialist_id": self.specialist_id,
            "governance_required": self.governance_required,
            "validation_status": self.validation_status,
            "validation_rules": list(self.validation_rules),
            "arbiter_disposition": self.arbiter_disposition,
            "arbiter_reason_codes": list(self.arbiter_reason_codes),
            "evidence_refs": list(self.evidence_refs),
            "execution_order": list(self.execution_order),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


__all__ = ["WORKFLOW_SANITY_SCHEMA_VERSION", "WorkflowSanityReceipt"]
