from __future__ import annotations

import hashlib
import json
from typing import Mapping

from ..orchestration.execution_efficiency import ExecutionBudget
from .task_profile import AUTHORITY_DOMAIN_OWNERS, TaskProfile
from .topology_validator import (
    AgenticWorkflowProfile,
    CriticContract,
    PATTERN_ORDER,
    SpecialistAuthority,
)

STOP_CONDITIONS = (
    "DECISIVE_BLOCKER",
    "OBJECTIVE_PASS",
    "BUDGET_EXHAUSTED",
    "PROTECTED_BOUNDARY",
)


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _stable_profile_id(task: TaskProfile, sequence: list[str], patterns: list[str]) -> str:
    payload = json.dumps(
        {
            "task_id": task.task_id,
            "source_identity": task.current_source_identity,
            "sequence": sequence,
            "patterns": patterns,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "agentic-workflow." + hashlib.sha256(payload).hexdigest()[:24]


def _domain_owners(task: TaskProfile) -> list[str]:
    owners: list[str] = []
    for domain in task.authority_domains:
        owner = AUTHORITY_DOMAIN_OWNERS[domain]
        if owner != "conductor":
            _append_unique(owners, owner)
    return owners


def select_agentic_workflow(
    task: TaskProfile,
    authorities: Mapping[str, SpecialistAuthority],
    budget: ExecutionBudget,
) -> tuple[AgenticWorkflowProfile, CriticContract | None]:
    if not isinstance(task, TaskProfile):
        raise TypeError("task must be TaskProfile")
    if not isinstance(budget, ExecutionBudget):
        raise TypeError("budget must be ExecutionBudget")
    budget.validate()

    owners = _domain_owners(task)
    primary_owner = task.primary_owner or (owners[0] if owners else "conductor")
    if primary_owner not in authorities:
        raise ValueError(f"primary owner is not in canonical authority view: {primary_owner}")

    required: list[str] = []
    domain_owner_count = len(set(owners))
    tuner_needed = bool(task.reentry_specialists) or (
        domain_owner_count > 1 and (task.dependency_depth > 0 or task.implementation_required)
    )
    if tuner_needed or "the-tuner" in owners:
        _append_unique(required, "the-tuner")

    terminal_owners = {"ponytail", "overseer", "arbiter", "the-tuner"}
    for owner in owners:
        if owner not in terminal_owners:
            _append_unique(required, owner)

    for specialist in task.reentry_specialists:
        if specialist not in authorities:
            raise ValueError(f"re-entry specialist is not in canonical authority view: {specialist}")
        if specialist not in terminal_owners:
            _append_unique(required, specialist)

    if task.implementation_required or "ponytail" in owners or "ponytail" in task.reentry_specialists:
        _append_unique(required, "ponytail")
    if task.validation_required or "overseer" in owners or "overseer" in task.reentry_specialists:
        _append_unique(required, "overseer")
    if task.critic_owner is not None:
        if task.critic_owner not in authorities:
            raise ValueError("critic owner is not in canonical authority view")
        _append_unique(required, task.critic_owner)
    if task.transition_required or "arbiter" in owners or "arbiter" in task.reentry_specialists:
        _append_unique(required, "arbiter")
    if not required:
        _append_unique(required, primary_owner)

    patterns = ["ROUTING"]
    if task.dependency_depth > 0 or len(required) > 1:
        patterns.append("PLANNING")
    if task.external_state_required or task.mutation_required or task.implementation_required or task.validation_required:
        patterns.append("TOOL_REACT")
    if task.critic_owner is not None:
        patterns.append("REFLECTION_CRITIC")

    multi_agent_value = len(required) > 1 and (
        task.independent_subtasks >= 2 or domain_owner_count >= 2 or bool(task.reentry_specialists)
    )
    if multi_agent_value:
        patterns.append("MULTI_AGENT")
    patterns = sorted(dict.fromkeys(patterns), key=PATTERN_ORDER.index)

    max_parallel = int(budget.defaults["max_parallel_specialists"])
    parallel_groups: list[tuple[str, ...]] = []
    if (
        "MULTI_AGENT" in patterns
        and task.parallelizable
        and task.independent_subtasks >= 2
        and max_parallel > 1
    ):
        candidates = [
            specialist
            for specialist in required
            if specialist not in {"the-tuner", "ponytail", "overseer", "arbiter"}
        ][:max_parallel]
        if len(candidates) >= 2:
            parallel_groups.append(tuple(candidates))

    if len(required) == 1:
        concurrency_mode = "SINGLE_OWNER"
    elif parallel_groups:
        concurrency_mode = "PARALLEL_MULTI_AGENT"
    else:
        concurrency_mode = "SEQUENTIAL_MULTI_AGENT"

    escalation_reasons = list(task.human_gate_requirements)
    if task.protected_action_required and not task.protected_action_authorized:
        _append_unique(escalation_reasons, "PROTECTED_ACTION_REQUIRES_INDEPENDENT_AUTHORITY")
    human_gate_required = bool(escalation_reasons)

    critic = None
    if task.critic_owner is not None and task.critic_domain is not None:
        critic = CriticContract(
            contract_id=f"critic.{task.task_id}.{task.critic_owner}",
            critic_owner=task.critic_owner,
            evaluation_domain=task.critic_domain,
            evidence_owner="overseer" if task.validation_required else task.critic_owner,
            can_block=task.critic_owner in {
                "the-steward",
                "the-governor",
                "overseer",
                "arbiter",
                "cipher",
                "cloak",
                "clockwork",
                "chronicler",
            },
            can_request_revision=True,
            can_transition=task.critic_owner == "arbiter",
            max_iterations=1,
        )

    profile = AgenticWorkflowProfile(
        profile_id=_stable_profile_id(task, required, patterns),
        source_task_id=task.task_id,
        primary_owner=primary_owner,
        required_specialists=tuple(required),
        selected_patterns=tuple(patterns),
        sequence=tuple(required),
        parallel_groups=tuple(parallel_groups),
        concurrency_mode=concurrency_mode,
        max_parallel_specialists=max_parallel,
        human_gate_required=human_gate_required,
        escalation_reasons=tuple(escalation_reasons),
        stop_conditions=STOP_CONDITIONS,
        critic_contract_id=None if critic is None else critic.contract_id,
    )
    return profile, critic


__all__ = ["STOP_CONDITIONS", "select_agentic_workflow"]
