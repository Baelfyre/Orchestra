from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..delegation import DelegationRequest, DelegationResolution
from ..models import ExecutionResult
from ..services import RuntimeExecutor
from .selection import (
    SelectionDecision,
    SelectionEligibilityEnvelope,
    SelectionEvidencePacket,
    rank_shadow_selection,
)

ATTACHMENT_SCHEMA_VERSION = "orchestra.adaptive-selection-execution-attachment.v1"
ATTACHMENT_STATUSES = frozenset({"ATTACHED", "NOT_EVALUATED", "UNAVAILABLE"})


@dataclass(frozen=True, slots=True)
class AdaptiveSelectionInvocation:
    """Caller-supplied A4 inputs for a post-execution shadow comparison."""

    eligibility_envelope: SelectionEligibilityEnvelope
    evidence_packet: SelectionEvidencePacket
    actual_deterministic_choice_id: str | None
    evaluated_at: str
    explicit_scoped_preference_candidate_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.eligibility_envelope, SelectionEligibilityEnvelope):
            raise TypeError("eligibility_envelope must be SelectionEligibilityEnvelope")
        if not isinstance(self.evidence_packet, SelectionEvidencePacket):
            raise TypeError("evidence_packet must be SelectionEvidencePacket")
        if not isinstance(self.evaluated_at, str) or not self.evaluated_at.strip():
            raise ValueError("evaluated_at must be a non-empty timestamp string")
        if self.actual_deterministic_choice_id is not None:
            choice = str(self.actual_deterministic_choice_id).strip()
            if not choice:
                raise ValueError("actual_deterministic_choice_id must be non-empty when provided")
            object.__setattr__(self, "actual_deterministic_choice_id", choice)
        if self.explicit_scoped_preference_candidate_id is not None:
            preference = str(self.explicit_scoped_preference_candidate_id).strip()
            if not preference:
                raise ValueError(
                    "explicit_scoped_preference_candidate_id must be non-empty when provided"
                )
            object.__setattr__(self, "explicit_scoped_preference_candidate_id", preference)
        object.__setattr__(self, "evaluated_at", self.evaluated_at.strip())


@dataclass(frozen=True, slots=True)
class SelectionExecutionAttachment:
    """Non-authorizing A4 decision attached only after deterministic execution returns."""

    status: str
    reason_code: str
    run_id: str | None
    authority_decision_ref: str | None
    capability_decision_ref: str | None
    lifecycle_state: str | None
    decision: SelectionDecision | None = None
    schema_version: str = ATTACHMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ATTACHMENT_SCHEMA_VERSION:
            raise ValueError(f"unsupported attachment schema '{self.schema_version}'")
        status = str(self.status).strip().upper()
        if status not in ATTACHMENT_STATUSES:
            raise ValueError(f"unsupported attachment status '{status}'")
        reason = str(self.reason_code).strip().upper()
        if not reason:
            raise ValueError("reason_code must be non-empty")
        if status == "ATTACHED" and not isinstance(self.decision, SelectionDecision):
            raise ValueError("ATTACHED status requires a SelectionDecision")
        if status != "ATTACHED" and self.decision is not None:
            raise ValueError("non-attached status cannot carry a SelectionDecision")

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reason_code", reason)
        object.__setattr__(self, "run_id", _optional_text(self.run_id))
        object.__setattr__(
            self, "authority_decision_ref", _optional_text(self.authority_decision_ref)
        )
        object.__setattr__(
            self, "capability_decision_ref", _optional_text(self.capability_decision_ref)
        )
        object.__setattr__(self, "lifecycle_state", _optional_text(self.lifecycle_state))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "status": self.status,
            "reason_code": self.reason_code,
            "run_id": self.run_id,
            "authority_decision_ref": self.authority_decision_ref,
            "capability_decision_ref": self.capability_decision_ref,
            "lifecycle_state": self.lifecycle_state,
            "attached_after_deterministic_result": True,
            "attached_after_operation": self.status in {"ATTACHED", "UNAVAILABLE"},
            "operation_inputs_received_shadow_data": False,
            "audit_persisted": False,
            "execution_controlled_by": "DETERMINISTIC_ORCHESTRA",
            "selection_effective": False,
            "shadow_influenced_execution": False,
            "runtime_outcome_used_as_selection_evidence": False,
            "performance_attribution": "NONE",
        }
        if self.decision is not None:
            payload["selection_decision"] = self.decision.to_dict()
            payload["selection_decision_digest"] = self.decision.digest
        return payload


@dataclass(frozen=True)
class AdaptiveSelectionExecutionResult(ExecutionResult):
    adaptive_selection_attachment: SelectionExecutionAttachment | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.adaptive_selection_attachment is not None and not isinstance(
            self.adaptive_selection_attachment, SelectionExecutionAttachment
        ):
            raise TypeError(
                "adaptive_selection_attachment must be SelectionExecutionAttachment"
            )


class AdaptiveSelectionProvider(Protocol):
    def compile(
        self,
        result: ExecutionResult,
        invocation: AdaptiveSelectionInvocation,
    ) -> SelectionDecision: ...


class BoundedAdaptiveSelectionProvider:
    """Bind A4.1 shadow ranking to an already-completed deterministic runtime result."""

    def compile(
        self,
        result: ExecutionResult,
        invocation: AdaptiveSelectionInvocation,
    ) -> SelectionDecision:
        if not isinstance(result, ExecutionResult):
            raise TypeError("result must be ExecutionResult")
        if not isinstance(invocation, AdaptiveSelectionInvocation):
            raise TypeError("invocation must be AdaptiveSelectionInvocation")
        if not result.validation.allowed:
            raise ValueError("A4 attachment requires an allowed deterministic validation")

        envelope = invocation.eligibility_envelope
        if envelope.command_name != result.route.command_name.casefold():
            raise ValueError("eligibility envelope command does not match deterministic route")
        if envelope.routed_specialist_slug != result.route.skill_slug.casefold():
            raise ValueError(
                "eligibility envelope specialist does not match deterministic route"
            )

        return rank_shadow_selection(
            envelope,
            invocation.evidence_packet,
            actual_deterministic_choice_id=invocation.actual_deterministic_choice_id,
            evaluated_at=invocation.evaluated_at,
            explicit_scoped_preference_candidate_id=(
                invocation.explicit_scoped_preference_candidate_id
            ),
        )


class AdaptiveSelectionRuntimeExecutor(RuntimeExecutor):
    """Opt-in A4 executor that attaches shadow evidence only after execution completes."""

    def __init__(
        self,
        *args,
        adaptive_selection_provider: AdaptiveSelectionProvider | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        provider = adaptive_selection_provider or BoundedAdaptiveSelectionProvider()
        if not hasattr(provider, "compile"):
            raise TypeError("adaptive_selection_provider must implement compile")
        self._adaptive_selection_provider = provider

    def execute(
        self,
        adapter,
        prompt: str,
        metadata: dict | None = None,
        *,
        coordination_session=None,
        adaptive_selection: AdaptiveSelectionInvocation | None = None,
    ) -> ExecutionResult:
        result = super().execute(
            adapter,
            prompt,
            metadata,
            coordination_session=coordination_session,
        )
        return self._attach_after_execution(result, adaptive_selection)

    def execute_delegation_request(
        self,
        adapter,
        prompt: str,
        request: DelegationRequest,
        metadata: dict | None = None,
        *,
        coordination_session=None,
        adaptive_selection: AdaptiveSelectionInvocation | None = None,
    ) -> ExecutionResult:
        if adaptive_selection is not None:
            raise ValueError("A4 adaptive selection attachment is not enabled for delegated execution")
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
        adaptive_selection: AdaptiveSelectionInvocation | None = None,
    ) -> ExecutionResult:
        if adaptive_selection is not None:
            raise ValueError("A4 adaptive selection attachment is not enabled for delegated execution")
        return super().execute_delegated(
            adapter,
            prompt,
            resolution,
            metadata,
            coordination_session=coordination_session,
        )

    def _attach_after_execution(
        self,
        result: ExecutionResult,
        invocation: AdaptiveSelectionInvocation | None,
    ) -> ExecutionResult:
        if invocation is None:
            return result
        if not isinstance(invocation, AdaptiveSelectionInvocation):
            attachment = self._attachment(
                result,
                status="UNAVAILABLE",
                reason_code="ADAPTIVE_SELECTION_INVOCATION_INVALID",
            )
            return _with_attachment(result, attachment)

        if (
            not result.validation.allowed
            or result.run_identity is None
            or result.authority_decision_id is None
            or result.capability_decision_id is None
        ):
            attachment = self._attachment(
                result,
                status="NOT_EVALUATED",
                reason_code="DETERMINISTIC_RUNTIME_GATES_NOT_COMPLETE",
            )
            return _with_attachment(result, attachment)

        try:
            decision = self._adaptive_selection_provider.compile(result, invocation)
            if not isinstance(decision, SelectionDecision):
                raise TypeError("adaptive selection provider returned an invalid decision")
        except Exception:
            attachment = self._attachment(
                result,
                status="UNAVAILABLE",
                reason_code="ADAPTIVE_SELECTION_UNAVAILABLE",
            )
            return _with_attachment(result, attachment)

        attachment = self._attachment(
            result,
            status="ATTACHED",
            reason_code="A4_SHADOW_DECISION_ATTACHED_POST_EXECUTION",
            decision=decision,
        )
        return _with_attachment(result, attachment)

    @staticmethod
    def _attachment(
        result: ExecutionResult,
        *,
        status: str,
        reason_code: str,
        decision: SelectionDecision | None = None,
    ) -> SelectionExecutionAttachment:
        return SelectionExecutionAttachment(
            status=status,
            reason_code=reason_code,
            run_id=result.run_identity.run_id if result.run_identity else None,
            authority_decision_ref=result.authority_decision_id,
            capability_decision_ref=result.capability_decision_id,
            lifecycle_state=result.lifecycle_state,
            decision=decision,
        )


def _with_attachment(
    result: ExecutionResult,
    attachment: SelectionExecutionAttachment,
) -> AdaptiveSelectionExecutionResult:
    return AdaptiveSelectionExecutionResult(
        success=result.success,
        adapter_name=result.adapter_name,
        command_name=result.command_name,
        route=result.route,
        validation=result.validation,
        output=result.output,
        audit_entry_id=result.audit_entry_id,
        run_identity=result.run_identity,
        authority_decision_id=result.authority_decision_id,
        capability_decision_id=result.capability_decision_id,
        authority_mode=result.authority_mode,
        lifecycle_state=result.lifecycle_state,
        terminal_result=result.terminal_result,
        runtime_audit_event_ids=result.runtime_audit_event_ids,
        adaptive_selection_attachment=attachment,
    )


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
