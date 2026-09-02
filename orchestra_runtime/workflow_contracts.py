from __future__ import annotations

from typing import Iterable

from .domain.orchestration.workflow import WORKFLOW_SANITY_SCHEMA_VERSION, WorkflowSanityReceipt
from .governance_kernel import ArbiterKernelResult
from .machine_contracts import (
    command_route_record,
    governance_required_specialists,
)
from .models import RouteDecision, ValidationResult


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
