from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

EXECUTION_BUDGET_SCHEMA = "orchestra.execution-budget.v1"
EXECUTION_BUDGET_INVARIANT = (
    "MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY"
)
EVIDENCE_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5")
SEARCH_ESCALATION = (
    "EXACT_PATH",
    "EXACT_SYMBOL",
    "BOUNDED_DIRECTORY",
    "REPOSITORY_WIDE",
    "EXTERNAL",
)
VALIDATION_ESCALATION = (
    "SYNTAX_SCHEMA",
    "DIRECT_TESTS",
    "SUBSYSTEM",
    "REPOSITORY_QUALIFICATION",
    "PROTECTED_GATES",
)
REQUIRED_TRUE_DEFAULTS = (
    "owner_first_routing",
    "broad_search_requires_narrow_search_exhaustion",
    "evidence_cache_requires_exact_source_identity",
    "full_validation_requires_stable_candidate",
    "ci_wait_must_not_consume_reasoning_budget",
    "autonomous_campaigns_load_one_phase_at_a_time",
    "optional_review_cannot_block_without_explicit_authority",
)
AUTHORITY_FALSE_FIELDS = (
    "creates_or_expands_authority",
    "weakens_existing_governance",
    "weakens_security",
    "weakens_validation",
    "weakens_human_gates",
    "new_specialist_required",
)


@dataclass(frozen=True)
class ExecutionBudget:
    schema_version: str
    contract_name: str
    owner: str
    core_invariant: str
    defaults: dict[str, Any]
    evidence_tiers: tuple[dict[str, Any], ...]
    search_escalation: tuple[str, ...]
    validation_escalation: tuple[str, ...]
    decisive_stop: dict[str, Any]
    measurement_fields: tuple[str, ...]
    authority: dict[str, Any]

    def validate(self) -> None:
        if self.schema_version != EXECUTION_BUDGET_SCHEMA:
            raise ValueError(f"unsupported ExecutionBudget schema_version: {self.schema_version}")
        if self.contract_name != "ExecutionBudget":
            raise ValueError("ExecutionBudget contract_name must be ExecutionBudget")
        if self.owner != "conductor":
            raise ValueError("ExecutionBudget owner must be conductor")
        if self.core_invariant != EXECUTION_BUDGET_INVARIANT:
            raise ValueError("ExecutionBudget core invariant changed")

        if self.defaults.get("max_parallel_specialists") != 1:
            raise ValueError("ExecutionBudget max_parallel_specialists must default to 1")
        if self.defaults.get("specialist_retry_limit") != 1:
            raise ValueError("ExecutionBudget specialist_retry_limit must default to 1")
        for field in REQUIRED_TRUE_DEFAULTS:
            if self.defaults.get(field) is not True:
                raise ValueError(f"ExecutionBudget default {field} must be true")

        tier_ids = tuple(str(item.get("tier", "")).strip() for item in self.evidence_tiers)
        if tier_ids != EVIDENCE_TIERS:
            raise ValueError("ExecutionBudget evidence tiers must be exact E0-E5 order")
        if self.search_escalation != SEARCH_ESCALATION:
            raise ValueError("ExecutionBudget search escalation order changed")
        if self.validation_escalation != VALIDATION_ESCALATION:
            raise ValueError("ExecutionBudget validation escalation order changed")

        if self.decisive_stop.get("rule") != "EARLIEST_DECISIVE_EVIDENCE_WINS":
            raise ValueError("ExecutionBudget decisive stop rule changed")
        required_fields = self.decisive_stop.get("required_fields")
        if required_fields != [
            "owner",
            "evidence_sufficient",
            "stop_required",
            "downstream_execution_allowed",
            "reason",
            "evidence_refs",
        ]:
            raise ValueError("ExecutionBudget decisive stop required fields changed")

        if not self.measurement_fields or len(set(self.measurement_fields)) != len(self.measurement_fields):
            raise ValueError("ExecutionBudget measurement_fields must be non-empty and unique")

        for field in AUTHORITY_FALSE_FIELDS:
            if self.authority.get(field) is not False:
                raise ValueError(f"ExecutionBudget authority field {field} must be false")


@dataclass(frozen=True)
class DecisiveStopSignal:
    owner: str
    evidence_sufficient: bool
    stop_required: bool
    downstream_execution_allowed: bool
    reason: str
    evidence_refs: tuple[str, ...]

    def validate(self) -> None:
        if not self.owner.strip():
            raise ValueError("DecisiveStopSignal owner is required")
        if not self.reason.strip():
            raise ValueError("DecisiveStopSignal reason is required")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("DecisiveStopSignal requires evidence_refs")
        if self.evidence_sufficient and self.stop_required and self.downstream_execution_allowed:
            raise ValueError(
                "downstream execution must be false when decisive evidence is sufficient and stop is required"
            )


def validate_execution_budget(data: Mapping[str, Any]) -> ExecutionBudget:
    if not isinstance(data, Mapping):
        raise ValueError("ExecutionBudget data must be a mapping")
    budget = ExecutionBudget(
        schema_version=str(data.get("schema_version", "")),
        contract_name=str(data.get("contract_name", "")),
        owner=str(data.get("owner", "")),
        core_invariant=str(data.get("core_invariant", "")),
        defaults=dict(data.get("defaults", {})),
        evidence_tiers=tuple(dict(item) for item in data.get("evidence_tiers", ())),
        search_escalation=tuple(str(item) for item in data.get("search_escalation", ())),
        validation_escalation=tuple(str(item) for item in data.get("validation_escalation", ())),
        decisive_stop=dict(data.get("decisive_stop", {})),
        measurement_fields=tuple(str(item) for item in data.get("measurement_fields", ())),
        authority=dict(data.get("authority", {})),
    )
    budget.validate()
    return budget


def validate_decisive_stop_signal(data: Mapping[str, Any]) -> DecisiveStopSignal:
    if not isinstance(data, Mapping):
        raise ValueError("DecisiveStopSignal data must be a mapping")
    signal = DecisiveStopSignal(
        owner=str(data.get("owner", "")),
        evidence_sufficient=data.get("evidence_sufficient") is True,
        stop_required=data.get("stop_required") is True,
        downstream_execution_allowed=data.get("downstream_execution_allowed") is True,
        reason=str(data.get("reason", "")),
        evidence_refs=tuple(str(item) for item in data.get("evidence_refs", ())),
    )
    signal.validate()
    return signal


def require_evidence_tier(target_tier: str, completed_tiers: Sequence[str]) -> None:
    if target_tier not in EVIDENCE_TIERS:
        raise ValueError(f"unknown evidence tier: {target_tier}")
    completed = tuple(completed_tiers)
    if any(item not in EVIDENCE_TIERS for item in completed):
        raise ValueError("completed_tiers contains unknown evidence tier")
    target_index = EVIDENCE_TIERS.index(target_tier)
    required = EVIDENCE_TIERS[:target_index]
    missing = [item for item in required if item not in completed]
    if missing:
        raise ValueError(
            "cannot enter evidence tier before required prior tiers pass: " + ", ".join(missing)
        )


def require_ordered_escalation(
    stages: Sequence[str],
    current_stage: str,
    target_stage: str,
    *,
    current_stage_insufficient: bool,
) -> None:
    stages = tuple(stages)
    if current_stage not in stages or target_stage not in stages:
        raise ValueError("unknown escalation stage")
    current_index = stages.index(current_stage)
    target_index = stages.index(target_stage)
    if target_index > current_index + 1:
        raise ValueError("escalation cannot skip stages")
    if target_index > current_index and not current_stage_insufficient:
        raise ValueError("cannot escalate before current stage is insufficient")


def require_search_escalation(
    current_stage: str, target_stage: str, *, current_stage_insufficient: bool
) -> None:
    require_ordered_escalation(
        SEARCH_ESCALATION,
        current_stage,
        target_stage,
        current_stage_insufficient=current_stage_insufficient,
    )


def require_validation_escalation(
    current_stage: str, target_stage: str, *, current_stage_insufficient: bool
) -> None:
    require_ordered_escalation(
        VALIDATION_ESCALATION,
        current_stage,
        target_stage,
        current_stage_insufficient=current_stage_insufficient,
    )


def enforce_ci_wait_boundary(
    *,
    activity: str,
    ci_state_changed: bool,
    active_model_reasoning: bool,
) -> None:
    if (
        activity == "CI_WAIT"
        and not ci_state_changed
        and active_model_reasoning
    ):
        raise ValueError(
            "active model reasoning is prohibited when the sole activity is waiting on unchanged CI state"
        )


__all__ = [
    "AUTHORITY_FALSE_FIELDS",
    "DecisiveStopSignal",
    "EVIDENCE_TIERS",
    "EXECUTION_BUDGET_INVARIANT",
    "EXECUTION_BUDGET_SCHEMA",
    "ExecutionBudget",
    "SEARCH_ESCALATION",
    "VALIDATION_ESCALATION",
    "enforce_ci_wait_boundary",
    "require_evidence_tier",
    "require_search_escalation",
    "require_validation_escalation",
    "validate_decisive_stop_signal",
    "validate_execution_budget",
]
