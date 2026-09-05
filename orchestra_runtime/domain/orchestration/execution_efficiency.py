from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

EXECUTION_BUDGET_SCHEMA = "orchestra.execution-budget.v1"
EXECUTION_BUDGET_INVARIANT = (
    "MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY"
)
EVIDENCE_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5")
EVIDENCE_TIER_NAMES = ("ORIENTATION", "INPUT_INTEGRITY", "TARGETED_ANALYSIS", "IMPLEMENTATION", "QUALIFICATION", "PROMOTION")
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
DEFAULT_FIELDS = (
    "max_parallel_specialists",
    "specialist_retry_limit",
    *REQUIRED_TRUE_DEFAULTS,
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

        if set(self.defaults) != set(DEFAULT_FIELDS):
            raise ValueError("ExecutionBudget defaults field set changed")
        if (
            type(self.defaults.get("max_parallel_specialists")) is not int
            or self.defaults.get("max_parallel_specialists") != 1
        ):
            raise ValueError("ExecutionBudget max_parallel_specialists must default to integer 1")
        if (
            type(self.defaults.get("specialist_retry_limit")) is not int
            or self.defaults.get("specialist_retry_limit") != 1
        ):
            raise ValueError("ExecutionBudget specialist_retry_limit must default to integer 1")
        for field in REQUIRED_TRUE_DEFAULTS:
            if self.defaults.get(field) is not True:
                raise ValueError(f"ExecutionBudget default {field} must be true")

        tier_ids = tuple(str(item.get("tier", "")).strip() for item in self.evidence_tiers)
        tier_names = tuple(str(item.get("name", "")).strip() for item in self.evidence_tiers)
        if tier_ids != EVIDENCE_TIERS or tier_names != EVIDENCE_TIER_NAMES:
            raise ValueError("ExecutionBudget evidence tiers must be exact E0-E5 order and names")
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

        if (
            not self.measurement_fields
            or any(not field.strip() for field in self.measurement_fields)
            or len(set(self.measurement_fields)) != len(self.measurement_fields)
        ):
            raise ValueError("ExecutionBudget measurement_fields must be non-empty and unique")

        if set(self.authority) != set(AUTHORITY_FALSE_FIELDS):
            raise ValueError("ExecutionBudget authority field set changed")
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
    for field in ("defaults", "decisive_stop", "authority"):
        if not isinstance(data.get(field), Mapping):
            raise ValueError(f"ExecutionBudget {field} must be a mapping")
    for field in ("evidence_tiers", "search_escalation", "validation_escalation", "measurement_fields"):
        if not isinstance(data.get(field), (list, tuple)):
            raise ValueError(f"ExecutionBudget {field} must be a list or tuple")
    if any(not isinstance(item, str) for item in data.get("measurement_fields", ())):
        raise ValueError("ExecutionBudget measurement_fields items must be strings")
    if any(not isinstance(item, Mapping) for item in data.get("evidence_tiers", ())):
        raise ValueError("ExecutionBudget evidence_tiers items must be mappings")
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
    for field in ("evidence_sufficient", "stop_required", "downstream_execution_allowed"):
        if type(data.get(field)) is not bool:
            raise ValueError(f"DecisiveStopSignal {field} must be a boolean")
    if not isinstance(data.get("evidence_refs"), (list, tuple)):
        raise ValueError("DecisiveStopSignal evidence_refs must be a list or tuple")
    signal = DecisiveStopSignal(
        owner=str(data.get("owner", "")),
        evidence_sufficient=data["evidence_sufficient"],
        stop_required=data["stop_required"],
        downstream_execution_allowed=data["downstream_execution_allowed"],
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
    if type(current_stage_insufficient) is not bool:
        raise ValueError("current_stage_insufficient must be a boolean")
    stages = tuple(stages)
    if current_stage not in stages or target_stage not in stages:
        raise ValueError("unknown escalation stage")
    current_index = stages.index(current_stage)
    target_index = stages.index(target_stage)
    if target_index < current_index:
        raise ValueError("escalation cannot move backward")
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
    if type(ci_state_changed) is not bool or type(active_model_reasoning) is not bool:
        raise ValueError("CI wait state flags must be booleans")
    if (
        activity == "CI_WAIT"
        and not ci_state_changed
        and active_model_reasoning
    ):
        raise ValueError(
            "active model reasoning is prohibited when the sole activity is waiting on unchanged CI state"
        )


SPECIALIST_INVOCATION_ROLES = ("PRIMARY", "SUPPORTING", "ADVERSARIAL", "REROUTE")
CI_WAIT_DISPOSITIONS = ("PASSIVE_WAIT", "REVIEW_CHANGED_STATE")


def _clean_text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _exact_non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class SpecialistInvocationRequest:
    owner_specialist: str
    requested_specialist: str
    role: str
    active_parallel_specialists: int
    retry_number: int
    justification: str
    cross_domain_required: bool = False
    adversarial_review_required: bool = False
    reroute_required: bool = False
    optional_review: bool = False
    blocking_requested: bool = False

    def validate(self) -> None:
        owner = _clean_text(self.owner_specialist, "owner_specialist").casefold()
        requested = _clean_text(self.requested_specialist, "requested_specialist").casefold()
        role = _clean_text(self.role, "role").upper()
        if role not in SPECIALIST_INVOCATION_ROLES:
            raise ValueError("unknown specialist invocation role")
        _exact_non_negative_int(self.active_parallel_specialists, "active_parallel_specialists")
        _exact_non_negative_int(self.retry_number, "retry_number")
        for field in (
            "cross_domain_required",
            "adversarial_review_required",
            "reroute_required",
            "optional_review",
            "blocking_requested",
        ):
            if type(getattr(self, field)) is not bool:
                raise ValueError(f"{field} must be a boolean")
        if role != "PRIMARY":
            _clean_text(self.justification, "justification")
        if role == "PRIMARY" and requested != owner:
            raise ValueError("primary specialist must be the decision owner")
        if role == "SUPPORTING" and requested == owner:
            raise ValueError("supporting specialist must differ from the decision owner")
        if role == "ADVERSARIAL" and not self.adversarial_review_required:
            raise ValueError("adversarial specialist requires explicit adversarial_review_required")
        if role == "REROUTE" and not self.reroute_required:
            raise ValueError("reroute specialist requires explicit reroute_required")


@dataclass(frozen=True)
class SpecialistInvocationDecision:
    allowed: bool
    reason_code: str
    requested_specialist: str
    role: str
    blocking_allowed: bool

    def __post_init__(self) -> None:
        if type(self.allowed) is not bool or type(self.blocking_allowed) is not bool:
            raise ValueError("specialist invocation decision flags must be booleans")
        _clean_text(self.reason_code, "reason_code")
        _clean_text(self.requested_specialist, "requested_specialist")
        if self.role not in SPECIALIST_INVOCATION_ROLES:
            raise ValueError("unknown specialist invocation decision role")


def evaluate_specialist_invocation(
    request: SpecialistInvocationRequest,
    budget: ExecutionBudget,
) -> SpecialistInvocationDecision:
    if not isinstance(request, SpecialistInvocationRequest):
        raise ValueError("request must be SpecialistInvocationRequest")
    if not isinstance(budget, ExecutionBudget):
        raise ValueError("budget must be ExecutionBudget")
    budget.validate()
    request.validate()
    defaults = budget.defaults
    role = request.role.upper()
    requested = request.requested_specialist.casefold()

    if request.active_parallel_specialists >= defaults["max_parallel_specialists"]:
        return SpecialistInvocationDecision(
            False,
            "PARALLEL_SPECIALIST_BUDGET_EXCEEDED",
            requested,
            role,
            False,
        )
    if request.retry_number > defaults["specialist_retry_limit"]:
        return SpecialistInvocationDecision(
            False,
            "SPECIALIST_RETRY_BUDGET_EXCEEDED",
            requested,
            role,
            False,
        )
    if role == "PRIMARY" and requested != request.owner_specialist.casefold():
        return SpecialistInvocationDecision(False, "OWNER_FIRST_REQUIRED", requested, role, False)

    secondary_reason = (
        request.cross_domain_required
        or request.adversarial_review_required
        or request.reroute_required
    )
    if role != "PRIMARY" and not secondary_reason:
        return SpecialistInvocationDecision(
            False,
            "SECONDARY_SPECIALIST_REASON_REQUIRED",
            requested,
            role,
            False,
        )
    if request.optional_review and request.blocking_requested:
        return SpecialistInvocationDecision(
            False,
            "OPTIONAL_REVIEW_CANNOT_BLOCK",
            requested,
            role,
            False,
        )

    return SpecialistInvocationDecision(
        True,
        "SPECIALIST_INVOCATION_ALLOWED",
        requested,
        role,
        not request.optional_review,
    )


def evaluate_decisive_stop(signal: DecisiveStopSignal) -> str:
    if not isinstance(signal, DecisiveStopSignal):
        raise ValueError("signal must be DecisiveStopSignal")
    signal.validate()
    if (
        signal.evidence_sufficient
        and signal.stop_required
    ) or not signal.downstream_execution_allowed:
        return "STOP"
    return "CONTINUE"


@dataclass(frozen=True)
class EvidenceReuseRecord:
    evidence_id: str
    source_ref: str
    source_identity: str
    content_digest: str
    produced_tier: str
    allowed_consumers: tuple[str, ...]

    def validate(self) -> None:
        _clean_text(self.evidence_id, "evidence_id")
        _clean_text(self.source_ref, "source_ref")
        _clean_text(self.source_identity, "source_identity")
        digest = _clean_text(self.content_digest, "content_digest").casefold()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("content_digest must be a SHA-256 hex digest")
        if self.produced_tier not in EVIDENCE_TIERS:
            raise ValueError("produced_tier must be an OEE evidence tier")
        consumers = tuple(item.casefold() for item in self.allowed_consumers)
        if (
            not consumers
            or any(not item.strip() for item in consumers)
            or len(set(consumers)) != len(consumers)
        ):
            raise ValueError("allowed_consumers must be non-empty and unique")


def require_evidence_reuse(
    record: EvidenceReuseRecord,
    *,
    current_source_identity: str,
    consumer: str,
) -> None:
    if not isinstance(record, EvidenceReuseRecord):
        raise ValueError("record must be EvidenceReuseRecord")
    record.validate()
    identity = _clean_text(current_source_identity, "current_source_identity")
    consumer_id = _clean_text(consumer, "consumer").casefold()
    if identity != record.source_identity:
        raise ValueError("cached evidence source identity is stale")
    if consumer_id not in {item.casefold() for item in record.allowed_consumers}:
        raise ValueError("cached evidence consumer is not authorized")


def authorize_validation_stage(
    target_stage: str,
    completed_stages: Sequence[str],
    *,
    candidate_stable: bool,
) -> None:
    if type(candidate_stable) is not bool:
        raise ValueError("candidate_stable must be a boolean")
    if target_stage not in VALIDATION_ESCALATION:
        raise ValueError("unknown validation stage")
    completed = tuple(completed_stages)
    if any(stage not in VALIDATION_ESCALATION for stage in completed):
        raise ValueError("completed_stages contains unknown validation stage")
    if len(set(completed)) != len(completed):
        raise ValueError("completed_stages must be unique")
    target_index = VALIDATION_ESCALATION.index(target_stage)
    required = VALIDATION_ESCALATION[:target_index]
    missing = [stage for stage in required if stage not in completed]
    if missing:
        raise ValueError(
            "cannot enter validation stage before required prior stages pass: "
            + ", ".join(missing)
        )
    if (
        target_stage in {"REPOSITORY_QUALIFICATION", "PROTECTED_GATES"}
        and not candidate_stable
    ):
        raise ValueError("expensive validation requires a stable candidate")


@dataclass(frozen=True)
class CIWaitRequest:
    previous_state_identity: str
    current_state_identity: str
    active_model_reasoning: bool
    continuous_watch_requested: bool = False

    def evaluate(self) -> str:
        previous = _clean_text(self.previous_state_identity, "previous_state_identity")
        current = _clean_text(self.current_state_identity, "current_state_identity")
        if (
            type(self.active_model_reasoning) is not bool
            or type(self.continuous_watch_requested) is not bool
        ):
            raise ValueError("CI wait request flags must be booleans")
        if self.continuous_watch_requested:
            raise ValueError("continuous CI watch is prohibited by the execution budget")
        changed = previous != current
        enforce_ci_wait_boundary(
            activity="CI_WAIT",
            ci_state_changed=changed,
            active_model_reasoning=self.active_model_reasoning,
        )
        return "REVIEW_CHANGED_STATE" if changed else "PASSIVE_WAIT"


@dataclass(frozen=True)
class ContextReference:
    ref: str
    source_identity: str
    purpose: str

    def validate(self) -> None:
        _clean_text(self.ref, "context ref")
        _clean_text(self.source_identity, "context source_identity")
        _clean_text(self.purpose, "context purpose")


@dataclass(frozen=True)
class PhaseContextPack:
    phase_id: str
    owner_specialist: str
    objective: str
    required_refs: tuple[ContextReference, ...]
    conditional_refs: tuple[ContextReference, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    prohibited_actions: tuple[str, ...] = ()
    historical_context_included: bool = False
    historical_context_reason: str | None = None

    def validate(self) -> None:
        _clean_text(self.phase_id, "phase_id")
        _clean_text(self.owner_specialist, "owner_specialist")
        _clean_text(self.objective, "objective")
        if type(self.historical_context_included) is not bool:
            raise ValueError("historical_context_included must be a boolean")
        if not self.required_refs:
            raise ValueError("phase context pack requires at least one required reference")
        refs = self.required_refs + self.conditional_refs
        for ref in refs:
            if not isinstance(ref, ContextReference):
                raise ValueError("phase context references must be ContextReference values")
            ref.validate()
        ref_ids = tuple(ref.ref for ref in refs)
        if len(set(ref_ids)) != len(ref_ids):
            raise ValueError("phase context references must be unique")
        for field_name, values in (
            ("unresolved_questions", self.unresolved_questions),
            ("allowed_actions", self.allowed_actions),
            ("prohibited_actions", self.prohibited_actions),
        ):
            cleaned = tuple(str(item).strip() for item in values)
            if any(not item for item in cleaned) or len(set(cleaned)) != len(cleaned):
                raise ValueError(f"{field_name} must contain unique non-empty values")
        if set(self.allowed_actions).intersection(self.prohibited_actions):
            raise ValueError("allowed_actions and prohibited_actions must not overlap")
        if self.historical_context_included:
            _clean_text(self.historical_context_reason, "historical_context_reason")
        elif self.historical_context_reason is not None:
            raise ValueError(
                "historical_context_reason requires historical_context_included"
            )


__all__ = [
    "CI_WAIT_DISPOSITIONS",
    "CIWaitRequest",
    "ContextReference",
    "EvidenceReuseRecord",
    "PhaseContextPack",
    "SPECIALIST_INVOCATION_ROLES",
    "SpecialistInvocationDecision",
    "SpecialistInvocationRequest",
    "authorize_validation_stage",
    "evaluate_decisive_stop",
    "evaluate_specialist_invocation",
    "require_evidence_reuse",
    "AUTHORITY_FALSE_FIELDS",
    "DEFAULT_FIELDS",
    "DecisiveStopSignal",
    "EVIDENCE_TIERS",
    "EVIDENCE_TIER_NAMES",
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
