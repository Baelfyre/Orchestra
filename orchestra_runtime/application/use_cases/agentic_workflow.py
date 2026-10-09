from __future__ import annotations

from typing import Any, Iterable, Mapping

from ...domain.adaptive import (
    TaskProfile,
    build_selection_trace,
    derive_task_profile,
    minimum_task_audit_depth,
    parse_authority_view,
    select_agentic_workflow,
)
from ...domain.adaptive.agentic_workflow import (
    _build_candidate_freshness_binding,
    _resolve_assurance_requirement_union,
)
from ...domain.adaptive.intake import _reconcile_task_profile_claim
from ...domain.orchestration.execution_efficiency import validate_execution_budget


def _validate_registry(
    specialist_registry: Mapping[str, Any],
    authority_slugs: set[str],
) -> None:
    raw_specialists = specialist_registry.get("specialists")
    if not isinstance(raw_specialists, list):
        raise TypeError("specialist registry specialists must be a list")
    registry_slugs = {
        str(item.get("slug", "")).strip().casefold()
        for item in raw_specialists
        if isinstance(item, Mapping)
    }
    if registry_slugs != authority_slugs:
        raise ValueError(
            "authority view and canonical specialist registry must have identical specialist sets"
        )


def _plan(
    *,
    task: TaskProfile,
    specialist_authority_view: Mapping[str, Any],
    specialist_registry: Mapping[str, Any],
    execution_budget: Mapping[str, Any],
    source: str,
    matched_signals: Iterable[dict[str, object]] = (),
    derivation_reasons: Iterable[str] = (),
    risk_reconciliation: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    authorities = parse_authority_view(specialist_authority_view)
    budget = validate_execution_budget(execution_budget)
    _validate_registry(specialist_registry, set(authorities))

    profile, critic = select_agentic_workflow(task, authorities, budget)
    risk_depth_floor = minimum_task_audit_depth(task)
    task_risk_floor = {
        "source": "TASK_PROFILE_RISK_LEVEL",
        "risk_level": task.risk_level,
        "audit_depth": risk_depth_floor,
        "targeted_verification_required": risk_depth_floor != "LIGHT",
    }
    requirement_union = _resolve_assurance_requirement_union(task_risk_floor)
    if risk_reconciliation is None:
        risk_reconciliation = {
            "declared_profile_risk": task.risk_level,
            "derived_prompt_risk": None,
            "resolved_risk": task.risk_level,
            "resolution": "DECLARED_PROFILE_ONLY",
            "profile_claims_untrusted": True,
        }
    parallel_peak = max((len(group) for group in profile.parallel_groups), default=1)
    trace = build_selection_trace(
        task=task,
        profile=profile,
        source=source,
        matched_signals=matched_signals,
        derivation_reasons=derivation_reasons,
    )
    return {
        "task_profile": task.to_dict(),
        "task_profile_source": source,
        "assurance_plan": {
            "schema_version": "orchestra.agentic-assurance-plan.v2",
            "composition_contract": "machine/adaptive/evidence-gated-decision-hierarchy.v1.json",
            "composition_contract_version": "orchestra.evidence-gated-decision-hierarchy.v1",
            "risk_level": task.risk_level,
            "risk_reconciliation": dict(risk_reconciliation),
            "task_risk_floor": task_risk_floor,
            "requirement_resolution_state": requirement_union["resolution_state"],
            "resolved_assurance_requirements": requirement_union[
                "resolved_assurance_requirements"
            ],
            "known_requirement_union": requirement_union["known_requirement_union"],
            "requirement_sources": requirement_union["required_sources"],
            "available_requirement_sources": requirement_union["available_sources"],
            "unresolved_requirement_sources": requirement_union["unresolved_sources"],
            "targeted_verification_required": requirement_union[
                "targeted_verification_required"
            ],
            "candidate_freshness": _build_candidate_freshness_binding(None),
            "assessor_may_self_verify": False,
            "evidence_sufficiency_owner": (
                "overseer"
                if requirement_union["targeted_verification_required"] is not False
                else None
            ),
            "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
            "may_authorize": False,
            "is_authorization_source": False,
        },
        "workflow_profile": profile.to_dict(),
        "critic_contract": None if critic is None else critic.to_dict(),
        "selection_trace": trace,
        "telemetry": {
            "specialist_count": len(profile.required_specialists),
            "pattern_count": len(profile.selected_patterns),
            "parallel_specialist_peak": parallel_peak,
            "max_parallel_specialists": profile.max_parallel_specialists,
            "human_gate_required": profile.human_gate_required,
            "topology_effective": profile.topology_effective,
            "reentry_specialist_count": len(task.reentry_specialists),
            "task_profile_source": source,
        },
        "authority_rule": "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION",
    }


def plan_agentic_workflow(
    *,
    task_profile: Mapping[str, Any],
    specialist_authority_view: Mapping[str, Any],
    specialist_registry: Mapping[str, Any],
    execution_budget: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an execution-effective topology from an explicit structured TaskProfile."""

    task = TaskProfile.from_mapping(task_profile)
    return _plan(
        task=task,
        specialist_authority_view=specialist_authority_view,
        specialist_registry=specialist_registry,
        execution_budget=execution_budget,
        source="STRUCTURED_TASK_PROFILE",
        derivation_reasons=("STRUCTURED_TASK_PROFILE_ACCEPTED",),
    )


def plan_agentic_workflow_from_intake(
    *,
    prompt: str,
    metadata: Mapping[str, Any],
    current_source_identity: str,
    derivation_policy: Mapping[str, Any],
    specialist_authority_view: Mapping[str, Any],
    specialist_registry: Mapping[str, Any],
    execution_budget: Mapping[str, Any],
    task_profile_claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive a TaskProfile from ordinary intake and build the authority-safe topology."""

    derivation = derive_task_profile(
        prompt=prompt,
        metadata=metadata,
        current_source_identity=current_source_identity,
        policy=derivation_policy,
    )
    task = derivation.task_profile
    source = "DERIVED_INTAKE"
    reasons = list(derivation.derivation_reasons)
    if task_profile_claim is None:
        risk_reconciliation = {
            "declared_profile_risk": None,
            "derived_prompt_risk": task.risk_level,
            "resolved_risk": task.risk_level,
            "resolution": "MAXIMUM_APPLICABLE_RISK",
            "profile_claims_untrusted": False,
        }
    else:
        claim = TaskProfile.from_mapping(task_profile_claim)
        risk_reconciliation = {
            "declared_profile_risk": claim.risk_level,
            "derived_prompt_risk": task.risk_level,
            "resolved_risk": max(
                (claim.risk_level, task.risk_level),
                key=("LOW", "MEDIUM", "HIGH", "CRITICAL").index,
            ),
            "resolution": "MAXIMUM_APPLICABLE_RISK",
            "profile_claims_untrusted": True,
        }
        task = _reconcile_task_profile_claim(task, claim)
        reasons.append("UNTRUSTED_TASK_PROFILE_CLAIM_RECONCILED_UPWARD")
    return _plan(
        task=task,
        specialist_authority_view=specialist_authority_view,
        specialist_registry=specialist_registry,
        execution_budget=execution_budget,
        source=source,
        matched_signals=(item.to_dict() for item in derivation.matched_signals),
        derivation_reasons=reasons,
        risk_reconciliation=risk_reconciliation,
    )


__all__ = [
    "plan_agentic_workflow",
    "plan_agentic_workflow_from_intake",
]
