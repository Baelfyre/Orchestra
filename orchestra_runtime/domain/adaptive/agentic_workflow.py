from __future__ import annotations

import hashlib
import json
import re
from typing import Mapping

from ..orchestration.execution_efficiency import ExecutionBudget
from ...shared.canonicalization import normalize_git_sha
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

_RISK_AUDIT_DEPTH = {
    "LOW": "LIGHT",
    "MEDIUM": "STANDARD",
    "HIGH": "DEEP",
    "CRITICAL": "DEEP",
}
_LOW_RISK_LIGHT_DOMAINS = frozenset({"BUSINESS_SCOPE", "DOCUMENTATION", "ROUTING"})
_AUDIT_DEPTH_ORDER = ("LIGHT", "STANDARD", "DEEP")
_ASSURANCE_REQUIREMENT_SOURCES = tuple(f"AQ{number}" for number in range(1, 15)) + ("PRAI",)
_REQUIRED_ASSURANCE_REQUIREMENT_SOURCES = ("AQ2", "AQ3", "AQ4", "PRAI")
_REPOSITORY_IDENTITY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _explicitly_harmless(task: TaskProfile) -> bool:
    return (
        task.risk_level == "LOW"
        and len(task.authority_domains) == 1
        and task.authority_domains[0] in _LOW_RISK_LIGHT_DOMAINS
        and task.primary_owner in (None, AUTHORITY_DOMAIN_OWNERS[task.authority_domains[0]])
        and task.dependency_depth == 0
        and task.independent_subtasks == 0
        and not task.parallelizable
        and task.execution_mode not in {"AUDIT", "DESTRUCTIVE"}
        and not task.mutation_required
        and not task.implementation_required
        and not task.validation_required
        and not task.transition_required
        and not task.external_state_required
        and not task.protected_action_required
        and not task.human_gate_requirements
        and task.critic_owner is None
        and not task.reentry_specialists
    )


def minimum_task_audit_depth(task: TaskProfile) -> str:
    """Return the task-risk floor; AQ2 and PRAI may raise it, never lower it."""

    if not isinstance(task, TaskProfile):
        raise TypeError("task must be TaskProfile")
    if task.risk_level == "LOW" and not _explicitly_harmless(task):
        return "STANDARD"
    return _RISK_AUDIT_DEPTH[task.risk_level]


def _resolve_assurance_requirement_union(
    task_risk_floor: Mapping[str, object],
    source_requirements: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Combine available requirement evidence without treating missing sources as false."""

    if not isinstance(task_risk_floor, Mapping):
        raise TypeError("task_risk_floor must be a mapping")
    floor_depth = task_risk_floor.get("audit_depth")
    floor_targeted = task_risk_floor.get("targeted_verification_required")
    if floor_depth not in _AUDIT_DEPTH_ORDER or type(floor_targeted) is not bool:
        raise ValueError("task risk floor is malformed")
    if source_requirements is None:
        source_requirements = {}
    if not isinstance(source_requirements, Mapping):
        raise TypeError("source_requirements must be a mapping")
    if any(not isinstance(source, str) for source in source_requirements):
        raise ValueError("assurance requirement source names must be strings")

    unknown = set(source_requirements) - set(_ASSURANCE_REQUIREMENT_SOURCES)
    if unknown:
        raise ValueError("unknown assurance requirement sources: " + ", ".join(sorted(unknown)))

    available: dict[str, dict[str, object]] = {}
    for source in _ASSURANCE_REQUIREMENT_SOURCES:
        if source not in source_requirements:
            continue
        requirement = source_requirements[source]
        if not isinstance(requirement, Mapping) or set(requirement) != {
            "audit_depth",
            "targeted_verification_required",
        }:
            raise ValueError(f"{source} assurance requirement is malformed")
        depth = requirement["audit_depth"]
        targeted = requirement["targeted_verification_required"]
        if depth not in _AUDIT_DEPTH_ORDER or type(targeted) is not bool:
            raise ValueError(f"{source} assurance requirement is malformed")
        available[source] = {
            "audit_depth": depth,
            "targeted_verification_required": targeted,
        }

    unresolved = [
        source
        for source in _REQUIRED_ASSURANCE_REQUIREMENT_SOURCES
        if source not in available
    ]
    state = (
        "FLOOR_ONLY"
        if not available
        else "RESOLVED"
        if not unresolved
        else "PARTIAL"
    )
    depths = [str(floor_depth), *(str(item["audit_depth"]) for item in available.values())]
    highest_depth = max(depths, key=_AUDIT_DEPTH_ORDER.index)
    any_targeted = floor_targeted or any(
        item["targeted_verification_required"] is True for item in available.values()
    )
    targeted_result = True if any_targeted else False if not unresolved else None
    resolved = (
        {
            "audit_depth": highest_depth,
            "targeted_verification_required": targeted_result,
        }
        if not unresolved
        else None
    )
    return {
        "resolution_state": state,
        "resolved_assurance_requirements": resolved,
        "known_requirement_union": {
            "audit_depth_lower_bound": highest_depth,
            "targeted_verification_required": (
                True if any_targeted else False if not unresolved else None
            ),
        },
        "targeted_verification_required": targeted_result,
        "required_sources": list(_REQUIRED_ASSURANCE_REQUIREMENT_SOURCES),
        "available_sources": list(available),
        "unresolved_sources": unresolved,
    }


def _build_candidate_freshness_binding(
    candidate_identity: Mapping[str, object] | None,
) -> dict[str, object]:
    if candidate_identity is None:
        return {
            "binding_version": "orchestra.candidate-freshness-binding.v1",
            "state": "UNBOUND",
            "repository": None,
            "candidate_sha": None,
            "tree_sha": None,
            "source_state_identity": None,
            "may_authorize": False,
        }
    if not isinstance(candidate_identity, Mapping) or set(candidate_identity) != {
        "repository",
        "candidate_sha",
        "tree_sha",
    }:
        raise ValueError("candidate identity must contain repository, candidate_sha, and tree_sha")
    repository = candidate_identity["repository"]
    if (
        not isinstance(repository, str)
        or len(repository) > 255
        or not _REPOSITORY_IDENTITY_RE.fullmatch(repository)
    ):
        raise ValueError("candidate repository identity is invalid")
    candidate_sha = normalize_git_sha(candidate_identity["candidate_sha"], "candidate_sha")
    tree_sha = normalize_git_sha(candidate_identity["tree_sha"], "tree_sha")
    identity = {
        "repository": repository,
        "candidate_sha": candidate_sha,
        "tree_sha": tree_sha,
    }
    identity_bytes = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return {
        "binding_version": "orchestra.candidate-freshness-binding.v1",
        "state": "BOUND",
        **identity,
        "source_state_identity": "sha256:" + hashlib.sha256(identity_bytes).hexdigest(),
        "may_authorize": False,
    }


def _candidate_binding_matches(
    binding: Mapping[str, object],
    current_candidate_identity: Mapping[str, object] | None,
) -> bool:
    if (
        not isinstance(binding, Mapping)
        or set(binding)
        != {
            "binding_version",
            "state",
            "repository",
            "candidate_sha",
            "tree_sha",
            "source_state_identity",
            "may_authorize",
        }
        or binding.get("state") != "BOUND"
        or binding.get("may_authorize") is not False
    ):
        return False
    try:
        current = _build_candidate_freshness_binding(current_candidate_identity)
    except (TypeError, ValueError):
        return False
    return all(
        binding.get(key) == current.get(key)
        for key in (
            "binding_version",
            "repository",
            "candidate_sha",
            "tree_sha",
            "source_state_identity",
        )
    ) and current["state"] == "BOUND"


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
    terminal_owners = {"ponytail", "overseer", "arbiter", "the-tuner"}
    decision_owners = [owner for owner in owners if owner not in terminal_owners]
    decision_owner_count = len(set(decision_owners))
    tuner_needed = bool(task.reentry_specialists) or (
        decision_owner_count > 1 and (task.dependency_depth > 0 or task.implementation_required)
    )
    if tuner_needed or "the-tuner" in owners:
        _append_unique(required, "the-tuner")

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
        task.independent_subtasks >= 2 or decision_owner_count >= 2 or bool(task.reentry_specialists)
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


__all__ = ["STOP_CONDITIONS", "minimum_task_audit_depth", "select_agentic_workflow"]
