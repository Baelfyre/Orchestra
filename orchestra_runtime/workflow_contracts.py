from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .evidence import receipt_digest
from .governance_kernel import ArbiterKernelResult
from .machine_contracts import (
    command_route_record,
    governance_required_specialists,
)
from .models import RouteDecision, ValidationResult

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


def build_workflow_sanity_receipt(
    route: RouteDecision,
    validation: ValidationResult,
    *,
    arbiter_result: ArbiterKernelResult | None = None,
    evidence_refs: Iterable[str] = (),
) -> WorkflowSanityReceipt:
    if not isinstance(route, RouteDecision):
        raise TypeError("route must be RouteDecision")
    if not isinstance(validation, ValidationResult):
        raise TypeError("validation must be ValidationResult")
    if arbiter_result is not None and not isinstance(arbiter_result, ArbiterKernelResult):
        raise TypeError("arbiter_result must be ArbiterKernelResult")

    expected = command_route_record(route.command_name)
    if expected["specialist"] != route.skill_slug:
        raise ValueError(
            f"runtime route {route.skill_slug!r} disagrees with machine contract "
            f"{expected['specialist']!r} for {route.command_name!r}"
        )
    expected_governance = route.skill_slug in governance_required_specialists()
    if route.governance_required is not expected_governance:
        raise ValueError(
            f"runtime governance_required={route.governance_required!r} disagrees with "
            f"machine policy for specialist {route.skill_slug!r}"
        )

    normalized_evidence = tuple(dict.fromkeys(str(item).strip() for item in evidence_refs if str(item).strip()))
    order = ["ROUTING", "SPECIALIST_RESOLUTION", "GOVERNANCE_VALIDATION"]
    disposition = None
    reason_codes: tuple[str, ...] = ()
    if arbiter_result is not None:
        order.append("ARBITER_KERNEL")
        disposition = arbiter_result.disposition.value
        reason_codes = tuple(code.value for code in arbiter_result.reason_codes)

    return WorkflowSanityReceipt(
        command_name=route.command_name,
        route_id=expected["route_id"],
        specialist_id=route.skill_slug,
        governance_required=route.governance_required,
        validation_status=validation.status,
        validation_rules=tuple(validation.evaluated_rules),
        arbiter_disposition=disposition,
        arbiter_reason_codes=reason_codes,
        evidence_refs=normalized_evidence,
        execution_order=tuple(order),
    )
