from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.selection import (
    SelectionCandidate,
    SelectionEvidenceItem,
    build_evidence_packet,
    build_eligibility_envelope,
)
from orchestra_runtime.adaptive.selection_runtime import (
    AdaptiveSelectionExecutionResult,
    AdaptiveSelectionInvocation,
    AdaptiveSelectionRuntimeExecutor,
    BoundedAdaptiveSelectionProvider,
    SelectionExecutionAttachment,
)
from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.lifecycle import LifecycleState
from orchestra_runtime.models import ValidationResult
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeOperationResult,
    SkillRegistry,
    build_compatibility_composition,
)

ROOT = Path(__file__).resolve().parents[2]
USER = "fixture-user"
PROJECT = "Baelfyre/Orchestra"
CREATED_AT = "2026-08-18T07:00:00Z"
COLLECTED_AT = "2026-08-18T07:01:00Z"
EVALUATED_AT = "2026-08-18T07:02:00Z"


def build_invocation() -> AdaptiveSelectionInvocation:
    deterministic = SelectionCandidate(
        candidate_id="strategy:deterministic",
        option_kind="SPECIALIST_STRATEGY",
        option_key="architecture-first",
        eligibility_evidence_refs=("eligibility:deterministic",),
        owner_specialist_slug="conductor",
    )
    shadow = SelectionCandidate(
        candidate_id="strategy:shadow",
        option_kind="SPECIALIST_STRATEGY",
        option_key="prototype-first",
        eligibility_evidence_refs=("eligibility:shadow",),
        owner_specialist_slug="conductor",
    )
    envelope = build_eligibility_envelope(
        selection_type="SPECIALIST_STRATEGY",
        created_at=CREATED_AT,
        user_key=USER,
        project_key=PROJECT,
        command_name="conductor",
        routed_specialist_slug="conductor",
        deterministic_route_ref="runtime-route:conductor",
        filter_evidence_refs=(
            "filter:ownership",
            "filter:route-binding",
            "filter:authority",
            "filter:capability",
            "filter:governance",
            "filter:provider-privacy",
            "filter:lifecycle",
            "filter:resource-ceilings",
        ),
        candidates=(deterministic, shadow),
    )
    evidence = (
        SelectionEvidenceItem(
            evidence_id="selection-evidence:shadow:1",
            source_kind="GOVERNED_SELECTION_OUTCOME",
            source_ref="selection-outcome:shadow:1",
            source_digest="a" * 64,
            option_id=shadow.candidate_id,
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="EXACT_OPTION_GOVERNED_OUTCOME",
            direction="POSITIVE",
        ),
        SelectionEvidenceItem(
            evidence_id="selection-evidence:shadow:2",
            source_kind="VALIDATION_EVIDENCE",
            source_ref="validation:shadow:2",
            source_digest="b" * 64,
            option_id=shadow.candidate_id,
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="EXACT_OPTION_VALIDATION",
            direction="POSITIVE",
        ),
    )
    packet = build_evidence_packet(
        envelope,
        collected_at=COLLECTED_AT,
        items=evidence,
    )
    return AdaptiveSelectionInvocation(
        eligibility_envelope=envelope,
        evidence_packet=packet,
        actual_deterministic_choice_id=deterministic.candidate_id,
        evaluated_at=EVALUATED_AT,
    )


def build_executor(*, operation=None, governance=None, provider=None, run_id="a4-attachment"):
    manifests = ManifestRepository(ROOT)
    skills = SkillRegistry(manifests, SkillSourceRepository(ROOT))
    return AdaptiveSelectionRuntimeExecutor(
        skills,
        RouterService(skills),
        governance or GovernanceValidator(),
        ContextAssembler(manifests),
        build_compatibility_composition(skills, InMemoryAuditSink(), run_id=run_id),
        operation=operation,
        adaptive_selection_provider=provider,
    )


def test_a4_attachment_runs_only_after_operation_and_preserves_execution_choice():
    order: list[str] = []
    captured = {}

    def operation(adapter_name, decision, validation):
        order.append("operation")
        captured["operation_route"] = decision
        assert "adaptive_selection" not in decision.metadata
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            "deterministic-output",
            "TEST_COMPLETED",
        )

    class SpyProvider(BoundedAdaptiveSelectionProvider):
        def compile(self, result, invocation):
            order.append("provider")
            assert result.output == "deterministic-output"
            return super().compile(result, invocation)

    result = build_executor(
        operation=operation,
        provider=SpyProvider(),
        run_id="a4-attachment-order",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=build_invocation(),
    )

    assert order == ["operation", "provider"]
    assert isinstance(result, AdaptiveSelectionExecutionResult)
    assert result.success is True
    assert result.output == "deterministic-output"
    assert result.route == captured["operation_route"]
    assert result.route.command_name == "conductor"
    assert result.route.skill_slug == "conductor"
    assert "adaptive_selection" not in result.route.metadata

    attachment = result.adaptive_selection_attachment
    assert attachment is not None
    assert attachment.status == "ATTACHED"
    assert attachment.run_id == result.run_identity.run_id
    assert attachment.authority_decision_ref == result.authority_decision_id
    assert attachment.capability_decision_ref == result.capability_decision_id
    assert attachment.decision is not None
    assert attachment.decision.disposition == "SHADOW_RANKED"
    assert attachment.decision.shadow_recommendation_id == "strategy:shadow"
    assert attachment.decision.actual_deterministic_choice_id == "strategy:deterministic"

    payload = attachment.to_dict()
    assert payload["attached_after_operation"] is True
    assert payload["operation_inputs_received_shadow_data"] is False
    assert payload["execution_controlled_by"] == "DETERMINISTIC_ORCHESTRA"
    assert payload["selection_effective"] is False
    assert payload["shadow_influenced_execution"] is False
    assert payload["runtime_outcome_used_as_selection_evidence"] is False
    assert payload["performance_attribution"] == "NONE"
    assert payload["audit_persisted"] is False


def test_a4_attachment_does_not_run_when_deterministic_governance_blocks():
    class BlockingGovernance:
        def validate(self, decision, context):
            return ValidationResult(
                False,
                "BLOCKED_PENDING_VALIDATION",
                ("blocked",),
                ("test",),
            )

    class SpyProvider:
        calls = 0

        def compile(self, result, invocation):
            self.calls += 1
            raise AssertionError("provider must not run when deterministic gates block")

    provider = SpyProvider()
    result = build_executor(
        governance=BlockingGovernance(),
        provider=provider,
        run_id="a4-attachment-blocked",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=build_invocation(),
    )

    assert result.success is False
    assert provider.calls == 0
    assert isinstance(result, AdaptiveSelectionExecutionResult)
    attachment = result.adaptive_selection_attachment
    assert attachment is not None
    assert attachment.status == "NOT_EVALUATED"
    assert attachment.reason_code == "DETERMINISTIC_RUNTIME_GATES_NOT_COMPLETE"
    assert attachment.decision is None
    assert attachment.to_dict()["attached_after_operation"] is False


def test_a4_attachment_failure_cannot_change_completed_deterministic_result():
    class FailingProvider:
        def compile(self, result, invocation):
            raise RuntimeError("private-secret-diagnostic")

    def operation(adapter_name, decision, validation):
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            "deterministic-output",
            "TEST_COMPLETED",
        )

    result = build_executor(
        operation=operation,
        provider=FailingProvider(),
        run_id="a4-attachment-fallback",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=build_invocation(),
    )

    assert result.success is True
    assert result.output == "deterministic-output"
    attachment = result.adaptive_selection_attachment
    assert attachment is not None
    assert attachment.status == "UNAVAILABLE"
    assert attachment.reason_code == "ADAPTIVE_SELECTION_UNAVAILABLE"
    assert attachment.decision is None
    assert "private-secret-diagnostic" not in json.dumps(attachment.to_dict())


def test_a4_attachment_rejects_route_mismatch_without_affecting_execution():
    mismatched = build_eligibility_envelope(
        selection_type="SPECIALIST_STRATEGY",
        created_at=CREATED_AT,
        user_key=USER,
        project_key=PROJECT,
        command_name="scribe",
        routed_specialist_slug="scribe",
        deterministic_route_ref="runtime-route:scribe",
        filter_evidence_refs=("filter:complete",),
        candidates=(
            SelectionCandidate(
                candidate_id="strategy:scribe",
                option_kind="SPECIALIST_STRATEGY",
                option_key="documentation-first",
                eligibility_evidence_refs=("eligibility:scribe",),
                owner_specialist_slug="scribe",
            ),
        ),
    )
    mismatched_packet = build_evidence_packet(
        mismatched,
        collected_at=COLLECTED_AT,
        items=(),
    )
    invocation = AdaptiveSelectionInvocation(
        eligibility_envelope=mismatched,
        evidence_packet=mismatched_packet,
        actual_deterministic_choice_id="strategy:scribe",
        evaluated_at=EVALUATED_AT,
    )

    def operation(adapter_name, decision, validation):
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            "deterministic-output",
            "TEST_COMPLETED",
        )

    result = build_executor(
        operation=operation,
        run_id="a4-attachment-route-mismatch",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=invocation,
    )

    assert result.success is True
    assert result.output == "deterministic-output"
    attachment = result.adaptive_selection_attachment
    assert attachment is not None
    assert attachment.status == "UNAVAILABLE"
    assert attachment.decision is None


def test_a4_attachment_is_not_enabled_for_delegated_execution():
    executor = build_executor(run_id="a4-attachment-delegation")
    with pytest.raises(ValueError, match="not enabled for delegated execution"):
        executor.execute_delegated(
            AdapterFactory.create("codex", ROOT),
            "@Orchestra rerun the prompt",
            None,  # type: ignore[arg-type]
            adaptive_selection=build_invocation(),
        )


def test_a4_invocation_validation_covers_fail_closed_inputs():
    valid = build_invocation()

    with pytest.raises(TypeError, match="eligibility_envelope"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=object(),  # type: ignore[arg-type]
            evidence_packet=valid.evidence_packet,
            actual_deterministic_choice_id=None,
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(TypeError, match="evidence_packet"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=valid.eligibility_envelope,
            evidence_packet=object(),  # type: ignore[arg-type]
            actual_deterministic_choice_id=None,
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(ValueError, match="evaluated_at"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=valid.eligibility_envelope,
            evidence_packet=valid.evidence_packet,
            actual_deterministic_choice_id=None,
            evaluated_at=" ",
        )
    with pytest.raises(ValueError, match="evaluated_at"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=valid.eligibility_envelope,
            evidence_packet=valid.evidence_packet,
            actual_deterministic_choice_id=None,
            evaluated_at=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="actual_deterministic_choice_id"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=valid.eligibility_envelope,
            evidence_packet=valid.evidence_packet,
            actual_deterministic_choice_id=" ",
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(ValueError, match="explicit_scoped_preference_candidate_id"):
        AdaptiveSelectionInvocation(
            eligibility_envelope=valid.eligibility_envelope,
            evidence_packet=valid.evidence_packet,
            actual_deterministic_choice_id=None,
            evaluated_at=EVALUATED_AT,
            explicit_scoped_preference_candidate_id=" ",
        )

    normalized = AdaptiveSelectionInvocation(
        eligibility_envelope=valid.eligibility_envelope,
        evidence_packet=valid.evidence_packet,
        actual_deterministic_choice_id=" strategy:deterministic ",
        evaluated_at=f" {EVALUATED_AT} ",
        explicit_scoped_preference_candidate_id=" strategy:shadow ",
    )
    assert normalized.actual_deterministic_choice_id == "strategy:deterministic"
    assert normalized.explicit_scoped_preference_candidate_id == "strategy:shadow"
    assert normalized.evaluated_at == EVALUATED_AT


def test_a4_attachment_record_validation_covers_invalid_states():
    kwargs = {
        "run_id": None,
        "authority_decision_ref": None,
        "capability_decision_ref": None,
        "lifecycle_state": None,
    }

    with pytest.raises(ValueError, match="unsupported attachment schema"):
        SelectionExecutionAttachment(
            status="UNAVAILABLE",
            reason_code="TEST",
            schema_version="unsupported",
            **kwargs,
        )
    with pytest.raises(ValueError, match="unsupported attachment status"):
        SelectionExecutionAttachment(
            status="unknown",
            reason_code="TEST",
            **kwargs,
        )
    with pytest.raises(ValueError, match="reason_code"):
        SelectionExecutionAttachment(
            status="UNAVAILABLE",
            reason_code=" ",
            **kwargs,
        )
    with pytest.raises(ValueError, match="ATTACHED status requires"):
        SelectionExecutionAttachment(
            status="ATTACHED",
            reason_code="TEST",
            **kwargs,
        )
    with pytest.raises(ValueError, match="non-attached status"):
        SelectionExecutionAttachment(
            status="UNAVAILABLE",
            reason_code="TEST",
            decision=object(),  # type: ignore[arg-type]
            **kwargs,
        )

    normalized = SelectionExecutionAttachment(
        status=" unavailable ",
        reason_code=" test_reason ",
        run_id=" ",
        authority_decision_ref=" authority ",
        capability_decision_ref=" ",
        lifecycle_state=" completed ",
    )
    assert normalized.status == "UNAVAILABLE"
    assert normalized.reason_code == "TEST_REASON"
    assert normalized.run_id is None
    assert normalized.authority_decision_ref == "authority"
    assert normalized.capability_decision_ref is None
    assert normalized.lifecycle_state == "completed"


def test_a4_provider_and_executor_fail_closed_validation_paths():
    provider = BoundedAdaptiveSelectionProvider()
    invocation = build_invocation()

    with pytest.raises(TypeError, match="result must be ExecutionResult"):
        provider.compile(object(), invocation)  # type: ignore[arg-type]

    executor = build_executor(run_id="a4-no-invocation")
    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
    )
    assert not isinstance(result, AdaptiveSelectionExecutionResult)

    with pytest.raises(TypeError, match="invocation must be AdaptiveSelectionInvocation"):
        provider.compile(result, object())  # type: ignore[arg-type]

    class BlockingGovernance:
        def validate(self, decision, context):
            return ValidationResult(
                False,
                "BLOCKED_PENDING_VALIDATION",
                ("blocked",),
                ("test",),
            )

    blocked = build_executor(
        governance=BlockingGovernance(),
        run_id="a4-provider-blocked",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
    )
    with pytest.raises(ValueError, match="requires an allowed deterministic validation"):
        provider.compile(blocked, invocation)

    with pytest.raises(TypeError, match="adaptive_selection_provider"):
        build_executor(provider=object(), run_id="a4-provider-invalid")


def test_a4_invalid_invocation_and_provider_result_degrade_attachment_only():
    def operation(adapter_name, decision, validation):
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            "deterministic-output",
            "TEST_COMPLETED",
        )

    invalid_invocation_result = build_executor(
        operation=operation,
        run_id="a4-invalid-invocation",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=object(),  # type: ignore[arg-type]
    )
    assert invalid_invocation_result.success is True
    assert invalid_invocation_result.output == "deterministic-output"
    invalid_attachment = invalid_invocation_result.adaptive_selection_attachment
    assert invalid_attachment is not None
    assert invalid_attachment.status == "UNAVAILABLE"
    assert invalid_attachment.reason_code == "ADAPTIVE_SELECTION_INVOCATION_INVALID"

    class InvalidDecisionProvider:
        def compile(self, result, invocation):
            return object()

    invalid_provider_result = build_executor(
        operation=operation,
        provider=InvalidDecisionProvider(),
        run_id="a4-invalid-provider-result",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_selection=build_invocation(),
    )
    assert invalid_provider_result.success is True
    assert invalid_provider_result.output == "deterministic-output"
    invalid_provider_attachment = invalid_provider_result.adaptive_selection_attachment
    assert invalid_provider_attachment is not None
    assert invalid_provider_attachment.status == "UNAVAILABLE"
    assert invalid_provider_attachment.reason_code == "ADAPTIVE_SELECTION_UNAVAILABLE"


def test_a4_delegation_request_attachment_remains_disabled():
    executor = build_executor(run_id="a4-attachment-delegation-request")
    with pytest.raises(ValueError, match="not enabled for delegated execution"):
        executor.execute_delegation_request(
            AdapterFactory.create("codex", ROOT),
            "@Orchestra rerun the prompt",
            None,  # type: ignore[arg-type]
            adaptive_selection=build_invocation(),
        )
