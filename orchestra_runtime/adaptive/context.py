from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Protocol

from ..delegation import DelegationRequest, DelegationResolution
from ..models import RouteDecision, ValidationResult
from ..services import RuntimeExecutor, RuntimeOperationResult
from .models import (
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
    ADAPTIVE_MEMORY_RULE_VERSION,
    safe_json_object,
)
from .store import JsonlAdaptiveStore

ADAPTIVE_CONTEXT_SCHEMA_VERSION = "orchestra.adaptive-context.v1"

_PRECEDENCE = {
    "EXPLICIT_CURRENT_INSTRUCTION": (4, "EXPLICIT_CURRENT_INSTRUCTION"),
    "EXPLICIT_SCOPED_PREFERENCE": (3, "EXPLICIT_SCOPED_PREFERENCE"),
    "CONFIRMED_LEARNED_PATTERN": (2, "CONFIRMED_LEARNED_PATTERN"),
    "INFERRED_CANDIDATE": (1, "INFERRED_CANDIDATE"),
}
_SCOPE_RANK = {
    "global_user": 0,
    "project": 1,
    "specialist": 2,
    "task_session": 3,
}


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _stable_refs(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    refs = tuple(sorted({_text(value, "reference") for value in values}))
    return refs


@dataclass(frozen=True, slots=True)
class AdaptiveInvocationContext:
    user_key: str
    project_key: str | None = None
    task_session_key: str | None = None
    repository_refs: tuple[str, ...] = ()
    current_instruction_refs: tuple[str, ...] = ()
    max_items: int = 16
    max_outcome_evidence: int = 8
    min_candidate_confidence: float | None = None

    def __post_init__(self) -> None:
        user_key = _text(self.user_key, "user_key")
        project_key = None if self.project_key is None else _text(self.project_key, "project_key")
        task_key = None if self.task_session_key is None else _text(self.task_session_key, "task_session_key")
        if isinstance(self.max_items, bool) or not isinstance(self.max_items, int) or self.max_items <= 0:
            raise ValueError("max_items must be a positive integer")
        if (
            isinstance(self.max_outcome_evidence, bool)
            or not isinstance(self.max_outcome_evidence, int)
            or self.max_outcome_evidence < 0
        ):
            raise ValueError("max_outcome_evidence must be a non-negative integer")
        threshold = self.min_candidate_confidence
        if threshold is not None:
            if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
                raise TypeError("min_candidate_confidence must be numeric when provided")
            threshold = float(threshold)
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("min_candidate_confidence must be between 0 and 1")
        repository_refs = _stable_refs(list(self.repository_refs))
        instruction_refs = _stable_refs(list(self.current_instruction_refs))
        safe_json_object(
            {
                "repository_refs": list(repository_refs),
                "current_instruction_refs": list(instruction_refs),
            },
            "adaptive_invocation",
        )
        object.__setattr__(self, "user_key", user_key)
        object.__setattr__(self, "project_key", project_key)
        object.__setattr__(self, "task_session_key", task_key)
        object.__setattr__(self, "repository_refs", repository_refs)
        object.__setattr__(self, "current_instruction_refs", instruction_refs)
        object.__setattr__(self, "min_candidate_confidence", threshold)


@dataclass(frozen=True, slots=True)
class AdaptiveContextItem:
    subject_key: str
    value: Any
    scope: AdaptiveScope
    status: str
    evidence_class: str
    evidence_refs: tuple[str, ...]
    confidence: float
    precedence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_key": self.subject_key,
            "value": self.value,
            "scope": self.scope.to_dict(),
            "status": self.status,
            "evidence_class": self.evidence_class,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "precedence": self.precedence,
        }


@dataclass(frozen=True, slots=True)
class AdaptiveOutcomeEvidence:
    source_ref: str
    scope: AdaptiveScope
    occurred_at: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "scope": self.scope.to_dict(),
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class AdaptiveContextPacket:
    specialist_slug: str
    command_name: str
    status: str
    reason_code: str
    items: tuple[AdaptiveContextItem, ...] = ()
    outcome_evidence: tuple[AdaptiveOutcomeEvidence, ...] = ()
    repository_refs: tuple[str, ...] = ()
    current_instruction_refs: tuple[str, ...] = ()
    schema_version: str = ADAPTIVE_CONTEXT_SCHEMA_VERSION
    advisory_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != ADAPTIVE_CONTEXT_SCHEMA_VERSION:
            raise ValueError(f"unsupported adaptive context schema '{self.schema_version}'")
        specialist = _text(self.specialist_slug, "specialist_slug").casefold()
        command = _text(self.command_name, "command_name").casefold()
        status = _text(self.status, "status").upper()
        if status not in {"ADVISORY", "DETERMINISTIC_FALLBACK"}:
            raise ValueError("adaptive context status must be ADVISORY or DETERMINISTIC_FALLBACK")
        reason = _text(self.reason_code, "reason_code")
        if self.advisory_only is not True:
            raise ValueError("A2 adaptive context must remain advisory_only")
        object.__setattr__(self, "specialist_slug", specialist)
        object.__setattr__(self, "command_name", command)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reason_code", reason)
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "outcome_evidence", tuple(self.outcome_evidence))
        object.__setattr__(self, "repository_refs", _stable_refs(list(self.repository_refs)))
        object.__setattr__(
            self,
            "current_instruction_refs",
            _stable_refs(list(self.current_instruction_refs)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "specialist_slug": self.specialist_slug,
            "command_name": self.command_name,
            "status": self.status,
            "reason_code": self.reason_code,
            "advisory_only": self.advisory_only,
            "repository_refs": list(self.repository_refs),
            "current_instruction_refs": list(self.current_instruction_refs),
            "items": [item.to_dict() for item in self.items],
            "outcome_evidence": [item.to_dict() for item in self.outcome_evidence],
        }


class AdaptiveContextProvider(Protocol):
    def compile(
        self,
        decision: RouteDecision,
        validation: ValidationResult,
        invocation: AdaptiveInvocationContext,
    ) -> AdaptiveContextPacket: ...


def fallback_packet(
    decision: RouteDecision,
    invocation: AdaptiveInvocationContext,
    reason_code: str,
) -> AdaptiveContextPacket:
    return AdaptiveContextPacket(
        specialist_slug=decision.skill_slug,
        command_name=decision.command_name,
        status="DETERMINISTIC_FALLBACK",
        reason_code=reason_code,
        repository_refs=invocation.repository_refs,
        current_instruction_refs=invocation.current_instruction_refs,
    )


class StoreBackedAdaptiveContextProvider:
    """Compile bounded read-only A2 context from the validated A1 local store."""

    def __init__(self, store: JsonlAdaptiveStore):
        if not isinstance(store, JsonlAdaptiveStore):
            raise TypeError("store must be JsonlAdaptiveStore")
        self._store = store

    def compile(
        self,
        decision: RouteDecision,
        validation: ValidationResult,
        invocation: AdaptiveInvocationContext,
    ) -> AdaptiveContextPacket:
        if not validation.allowed:
            return fallback_packet(decision, invocation, "GOVERNANCE_NOT_APPROVED")
        if invocation.user_key != self._store.user_key:
            return fallback_packet(decision, invocation, "USER_SCOPE_MISMATCH")

        observations = self._store.load_observations()
        profile = self._store.load_profile()
        if profile is None:
            return fallback_packet(decision, invocation, "NO_VALID_PROFILE")
        if not self._profile_is_current(profile, observations):
            return fallback_packet(decision, invocation, "STALE_OR_INCOMPATIBLE_PROFILE")

        selected = self._select_patterns(profile, decision.skill_slug, invocation)
        outcomes = self._select_outcomes(observations, decision.skill_slug, invocation)
        return AdaptiveContextPacket(
            specialist_slug=decision.skill_slug,
            command_name=decision.command_name,
            status="ADVISORY",
            reason_code="A2_CONTEXT_COMPILED",
            items=selected[: invocation.max_items],
            outcome_evidence=outcomes[: invocation.max_outcome_evidence],
            repository_refs=invocation.repository_refs,
            current_instruction_refs=invocation.current_instruction_refs,
        )

    @staticmethod
    def _profile_is_current(
        profile: AdaptiveProfile,
        observations: tuple,
    ) -> bool:
        if profile.memory_rule_version != ADAPTIVE_MEMORY_RULE_VERSION:
            return False
        expected_head = None if not observations else observations[-1].digest
        return profile.source_head_digest == expected_head

    def _select_patterns(
        self,
        profile: AdaptiveProfile,
        specialist_slug: str,
        invocation: AdaptiveInvocationContext,
    ) -> tuple[AdaptiveContextItem, ...]:
        winners: dict[str, tuple[tuple[int, int, str, str], AdaptiveContextItem]] = {}
        for pattern in profile.patterns:
            if not self._scope_matches(pattern.scope, specialist_slug, invocation):
                continue
            classification = self._classify_pattern(pattern, invocation)
            if classification is None:
                continue
            precedence_rank, precedence_label = _PRECEDENCE[classification]
            item = AdaptiveContextItem(
                subject_key=pattern.subject_key,
                value=pattern.value,
                scope=pattern.scope,
                status=pattern.status,
                evidence_class=pattern.evidence_class,
                evidence_refs=pattern.evidence_refs,
                confidence=pattern.confidence,
                precedence=precedence_label,
            )
            rank = (
                precedence_rank,
                _SCOPE_RANK[pattern.scope.scope_type],
                pattern.updated_at,
                pattern.pattern_id,
            )
            current = winners.get(pattern.subject_key)
            if current is None or rank > current[0]:
                winners[pattern.subject_key] = (rank, item)
        return tuple(
            item
            for _, item in sorted(
                winners.values(),
                key=lambda pair: (-pair[0][0], -pair[0][1], pair[1].subject_key),
            )
        )

    @staticmethod
    def _classify_pattern(
        pattern: AdaptivePattern,
        invocation: AdaptiveInvocationContext,
    ) -> str | None:
        if pattern.status in {"deprecated", "rejected"}:
            return None
        if pattern.evidence_class == "EXPLICIT_CURRENT_INSTRUCTION":
            return "EXPLICIT_CURRENT_INSTRUCTION"
        if pattern.evidence_class == "EXPLICIT_SCOPED_PREFERENCE":
            return "EXPLICIT_SCOPED_PREFERENCE"
        if pattern.evidence_class == "INFERRED_CANDIDATE":
            if pattern.status == "confirmed":
                return "CONFIRMED_LEARNED_PATTERN"
            if pattern.status != "candidate":
                return None
            threshold = invocation.min_candidate_confidence
            if threshold is None or pattern.confidence < threshold:
                return None
            return "INFERRED_CANDIDATE"
        return None

    def _select_outcomes(
        self,
        observations: tuple,
        specialist_slug: str,
        invocation: AdaptiveInvocationContext,
    ) -> tuple[AdaptiveOutcomeEvidence, ...]:
        outcomes = []
        for observation in observations:
            if observation.event_type != "GOVERNED_OUTCOME_RECORDED":
                continue
            if not self._scope_matches(observation.scope, specialist_slug, invocation):
                continue
            outcomes.append(
                AdaptiveOutcomeEvidence(
                    source_ref=observation.source_ref,
                    scope=observation.scope,
                    occurred_at=observation.occurred_at,
                    payload=dict(observation.payload),
                )
            )
        return tuple(
            sorted(
                outcomes,
                key=lambda item: (item.occurred_at, item.source_ref),
                reverse=True,
            )
        )

    @staticmethod
    def _scope_matches(
        scope: AdaptiveScope,
        specialist_slug: str,
        invocation: AdaptiveInvocationContext,
    ) -> bool:
        if scope.user_key != invocation.user_key:
            return False
        if scope.project_key is not None and scope.project_key != invocation.project_key:
            return False
        if scope.specialist_slug is not None and scope.specialist_slug != specialist_slug.casefold():
            return False
        if scope.scope_type == "task_session" and scope.task_session_key != invocation.task_session_key:
            return False
        return True


class AdaptiveRuntimeExecutor(RuntimeExecutor):
    """Opt-in A2 executor that adds advisory context only at the operation boundary."""

    def __init__(
        self,
        *args,
        adaptive_provider: AdaptiveContextProvider,
        **kwargs,
    ):
        if adaptive_provider is None or not hasattr(adaptive_provider, "compile"):
            raise TypeError("adaptive_provider must implement compile")
        super().__init__(*args, **kwargs)
        self._adaptive_provider = adaptive_provider
        self._base_operation = self._operation
        self._adaptive_invocation: ContextVar[AdaptiveInvocationContext | None] = ContextVar(
            "orchestra_adaptive_invocation",
            default=None,
        )
        self._operation = self._adaptive_operation

    def execute(
        self,
        adapter,
        prompt: str,
        metadata: dict | None = None,
        *,
        coordination_session=None,
        adaptive_context: AdaptiveInvocationContext | None = None,
    ):
        token = self._adaptive_invocation.set(adaptive_context)
        try:
            return super().execute(
                adapter,
                prompt,
                metadata,
                coordination_session=coordination_session,
            )
        finally:
            self._adaptive_invocation.reset(token)

    def execute_delegation_request(
        self,
        adapter,
        prompt: str,
        request: DelegationRequest,
        metadata: dict | None = None,
        *,
        coordination_session=None,
        adaptive_context: AdaptiveInvocationContext | None = None,
    ):
        if adaptive_context is not None:
            raise ValueError("A2 adaptive context is not enabled for delegated execution")
        return super().execute_delegation_request(
            adapter,
            prompt,
            request,
            metadata,
            coordination_session=coordination_session,
        )

    def execute_delegated(
        self,
        adapter,
        prompt: str,
        resolution: DelegationResolution,
        metadata: dict | None = None,
        *,
        coordination_session=None,
        adaptive_context: AdaptiveInvocationContext | None = None,
    ):
        if adaptive_context is not None:
            raise ValueError("A2 adaptive context is not enabled for delegated execution")
        return super().execute_delegated(
            adapter,
            prompt,
            resolution,
            metadata,
            coordination_session=coordination_session,
        )

    def _adaptive_operation(
        self,
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> RuntimeOperationResult:
        invocation = self._adaptive_invocation.get()
        if invocation is None:
            return self._base_operation(adapter_name, decision, validation)
        try:
            packet = self._adaptive_provider.compile(decision, validation, invocation)
        except Exception:
            packet = fallback_packet(decision, invocation, "ADAPTIVE_CONTEXT_UNAVAILABLE")
        metadata = dict(decision.metadata)
        metadata["adaptive_context"] = packet.to_dict()
        advisory_decision = RouteDecision(
            command_name=decision.command_name,
            skill_slug=decision.skill_slug,
            governance_required=decision.governance_required,
            reason=decision.reason,
            metadata=metadata,
        )
        return self._base_operation(adapter_name, advisory_decision, validation)
