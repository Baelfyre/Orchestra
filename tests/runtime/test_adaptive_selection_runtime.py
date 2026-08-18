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
