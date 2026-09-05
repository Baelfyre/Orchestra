from __future__ import annotations

from typing import Any, Mapping

from ...domain.adaptive import TaskProfile, parse_authority_view, select_agentic_workflow
from ...domain.orchestration.execution_efficiency import validate_execution_budget


def plan_agentic_workflow(
    *,
    task_profile: Mapping[str, Any],
    specialist_authority_view: Mapping[str, Any],
    specialist_registry: Mapping[str, Any],
    execution_budget: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an execution-effective Conductor topology without expanding authority."""

    task = TaskProfile.from_mapping(task_profile)
    authorities = parse_authority_view(specialist_authority_view)
    budget = validate_execution_budget(execution_budget)

    raw_specialists = specialist_registry.get("specialists")
    if not isinstance(raw_specialists, list):
        raise TypeError("specialist registry specialists must be a list")
    registry_slugs = {
        str(item.get("slug", "")).strip().casefold()
        for item in raw_specialists
        if isinstance(item, Mapping)
    }
    if registry_slugs != set(authorities):
        raise ValueError("authority view and canonical specialist registry must have identical specialist sets")

    profile, critic = select_agentic_workflow(task, authorities, budget)
    parallel_peak = max((len(group) for group in profile.parallel_groups), default=1)
    return {
        "task_profile": task.to_dict(),
        "workflow_profile": profile.to_dict(),
        "critic_contract": None if critic is None else critic.to_dict(),
        "telemetry": {
            "specialist_count": len(profile.required_specialists),
            "pattern_count": len(profile.selected_patterns),
            "parallel_specialist_peak": parallel_peak,
            "max_parallel_specialists": profile.max_parallel_specialists,
            "human_gate_required": profile.human_gate_required,
            "topology_effective": profile.topology_effective,
            "reentry_specialist_count": len(task.reentry_specialists),
        },
        "authority_rule": "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION",
    }


__all__ = ["plan_agentic_workflow"]
