from __future__ import annotations

from typing import Any, Iterable, Mapping

from ...domain.adaptive import (
    TaskProfile,
    build_selection_trace,
    derive_task_profile,
    parse_authority_view,
    select_agentic_workflow,
)
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
) -> dict[str, Any]:
    authorities = parse_authority_view(specialist_authority_view)
    budget = validate_execution_budget(execution_budget)
    _validate_registry(specialist_registry, set(authorities))

    profile, critic = select_agentic_workflow(task, authorities, budget)
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
) -> dict[str, Any]:
    """Derive a TaskProfile from ordinary intake and build the authority-safe topology."""

    derivation = derive_task_profile(
        prompt=prompt,
        metadata=metadata,
        current_source_identity=current_source_identity,
        policy=derivation_policy,
    )
    return _plan(
        task=derivation.task_profile,
        specialist_authority_view=specialist_authority_view,
        specialist_registry=specialist_registry,
        execution_budget=execution_budget,
        source="DERIVED_INTAKE",
        matched_signals=(item.to_dict() for item in derivation.matched_signals),
        derivation_reasons=derivation.derivation_reasons,
    )


__all__ = [
    "plan_agentic_workflow",
    "plan_agentic_workflow_from_intake",
]
