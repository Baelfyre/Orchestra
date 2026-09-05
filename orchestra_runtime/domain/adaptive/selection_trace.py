from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from .task_profile import TaskProfile
from .topology_validator import AgenticWorkflowProfile

SELECTION_TRACE_SCHEMA_VERSION = "orchestra.agentic-selection-trace.v1"
AUTHORITY_RULE = "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION"

_REJECTED_PATTERN_REASONS = {
    "PLANNING": "NO_DEPENDENCY_DECOMPOSITION_OR_MULTI_SPECIALIST_SEQUENCE",
    "TOOL_REACT": "NO_EXTERNAL_STATE_MUTATION_IMPLEMENTATION_OR_VALIDATION_REQUIRED",
    "REFLECTION_CRITIC": "NO_DISTINCT_CRITIC_CONTRACT",
    "MULTI_AGENT": "INSUFFICIENT_DISTINCT_AUTHORITY_REENTRY_OR_SUBTASK_VALUE",
}


def _trace_id(task_id: str, profile_id: str, source: str) -> str:
    payload = json.dumps(
        {"task_id": task_id, "profile_id": profile_id, "source": source},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "agentic-selection." + sha256(payload).hexdigest()[:24]


def build_selection_trace(
    *,
    task: TaskProfile,
    profile: AgenticWorkflowProfile,
    source: str,
    matched_signals: Iterable[dict[str, object]] = (),
    derivation_reasons: Iterable[str] = (),
) -> dict[str, object]:
    if source not in {"DERIVED_INTAKE", "STRUCTURED_TASK_PROFILE"}:
        raise ValueError("selection trace source is invalid")

    selected = set(profile.selected_patterns)
    rejected = {
        pattern: reason
        for pattern, reason in _REJECTED_PATTERN_REASONS.items()
        if pattern not in selected
    }

    selection_reasons: list[str] = [
        f"PRIMARY_OWNER:{profile.primary_owner}",
        *(f"SPECIALIST_SELECTED:{item}" for item in profile.required_specialists),
        *(f"PATTERN_SELECTED:{item}" for item in profile.selected_patterns),
    ]
    if profile.human_gate_required:
        selection_reasons.append("HUMAN_GATE_FROM_UNDERLYING_BOUNDARY")
    else:
        selection_reasons.append("NO_TOPOLOGY_ONLY_HUMAN_GATE")
    if profile.concurrency_mode != "SINGLE_OWNER":
        selection_reasons.append(f"CONCURRENCY_MODE:{profile.concurrency_mode}")

    return {
        "schema_version": SELECTION_TRACE_SCHEMA_VERSION,
        "trace_id": _trace_id(task.task_id, profile.profile_id, source),
        "source": source,
        "task_id": task.task_id,
        "matched_signals": list(matched_signals),
        "derivation_reasons": list(dict.fromkeys(str(item) for item in derivation_reasons)),
        "selected_specialists": list(profile.required_specialists),
        "selected_patterns": list(profile.selected_patterns),
        "rejected_patterns": rejected,
        "selection_reasons": list(dict.fromkeys(selection_reasons)),
        "human_gate_required": profile.human_gate_required,
        "escalation_reasons": list(profile.escalation_reasons),
        "authority_rule": AUTHORITY_RULE,
    }


__all__ = [
    "AUTHORITY_RULE",
    "SELECTION_TRACE_SCHEMA_VERSION",
    "build_selection_trace",
]
