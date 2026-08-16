from pathlib import Path

import pytest

from orchestra_runtime.communication_budget import (
    CommunicationMeasurement,
    TokenMeasurementSource,
)
from orchestra_runtime.compliance_protocol import ComplianceConsumptionReceipt
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
)
from orchestra_runtime.presentation import PresentationMode, load_presentation_policy
from orchestra_runtime.remediation_circuit import (
    RemediationCircuitState,
    evaluate_circuit_with_arbiter,
    failure_signature,
    request_remediation,
)
from orchestra_runtime.shadow_conformance import LegacyWorkflowClaim
from orchestra_runtime.workflow_contracts import WorkflowSanityReceipt


VALIDATION_DIGEST = "a" * 64
GOVERNANCE_DIGEST = "b" * 64


def _approved_decision() -> GovernanceDecisionRecord:
    return GovernanceDecisionRecord(
        reviewer="release-sanity",
        project_context="post-murmurs-rc",
        decision="APPROVED",
        reason="release candidate trust-edge fixture",
    )


def test_communication_measurement_rejects_empty_scenario_identity():
    with pytest.raises(ValueError, match="scenario_id must be non-empty"):
        CommunicationMeasurement(
            scenario_id=" ",
            mode=PresentationMode.NORMAL,
            implementation_revision="rc",
            progress_messages=0,
            model_progress_calls=0,
            user_visible_bytes=0,
            context_bytes_admitted=0,
            tool_result_bytes_admitted=0,
            repeated_reads=0,
            task_outcome="PASS",
            validation_digest=VALIDATION_DIGEST,
            governance_digest=GOVERNANCE_DIGEST,
            token_source=TokenMeasurementSource.UNAVAILABLE,
        )


def test_compliance_consumption_rejects_duplicate_classification_keys():
    with pytest.raises(ValueError, match="classifications contain duplicate obligation IDs"):
        ComplianceConsumptionReceipt(
            query_digest="c" * 64,
            source_ids=("SOURCE-1",),
            obligation_ids=("OBLIGATION-1", "OBLIGATION-2"),
            classifications=(
                ("OBLIGATION-1", "EVIDENCE_PRESENT"),
                ("OBLIGATION-1", "EVIDENCE_MISSING"),
            ),
            verdict="REVISION_REQUIRED",
        )


def test_governance_record_rejects_unknown_decision_enum():
    with pytest.raises(ValueError, match="unsupported decision"):
        GovernanceDecisionRecord(
            reviewer="release-sanity",
            project_context="post-murmurs-rc",
            decision="PASS_WITH_FINDINGS",
            reason="unsupported decision fixture",
        )


def test_arbiter_input_rejects_zero_identical_failure_limit():
    with pytest.raises(ValueError, match="maximum_identical_failure_repetitions must be > 0"):
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="post-murmurs-rc",
            governance_decisions=(_approved_decision(),),
            maximum_identical_failure_repetitions=0,
        )


def test_circuit_arbiter_evaluation_digest_is_stable_and_complete():
    state = RemediationCircuitState(
        project_id="orchestra",
        unit_id="post-murmurs-rc",
        envelope_id="release-sanity-envelope",
    )
    circuit = request_remediation(
        state,
        failure_digest=failure_signature(
            validator_id="pytest",
            reason_code="RELEASE_SANITY",
            evidence_digest="d" * 64,
        ),
    )
    kernel_input = ArbiterKernelInput(
        project_id="orchestra",
        unit_id="post-murmurs-rc",
        governance_decisions=(
            GovernanceDecisionRecord(
                reviewer="release-sanity",
                project_context="post-murmurs-rc",
                decision="REVISION_REQUIRED",
                reason="bounded release-sanity remediation",
            ),
        ),
        deterministic_defect=True,
        remediation_authorized=True,
        remediation_in_scope=True,
    )
    evaluation = evaluate_circuit_with_arbiter(kernel_input, circuit)
    assert len(evaluation.digest) == 64
    assert evaluation.digest == evaluation.digest


def test_shadow_claim_digest_binds_machine_comparison_input():
    claim = LegacyWorkflowClaim(
        command_name="review-architecture",
        specialist_id="clockwork",
        governance_required=False,
        validation_allowed=True,
        arbiter_disposition="AUTO_CONTINUE",
        evidence_digests=("e" * 64,),
    )
    assert len(claim.digest) == 64
    assert claim.digest == claim.digest


def test_workflow_receipt_rejects_empty_required_identity():
    with pytest.raises(ValueError, match="command_name must be non-empty"):
        WorkflowSanityReceipt(
            command_name="",
            route_id="architecture-structure",
            specialist_id="clockwork",
            governance_required=False,
            validation_status="NOT_REQUIRED",
            validation_rules=(),
            arbiter_disposition="AUTO_CONTINUE",
            arbiter_reason_codes=(),
            evidence_refs=(),
            execution_order=("ROUTING",),
        )


def test_presentation_contract_loader_rejects_invalid_json(tmp_path: Path):
    presentation_dir = tmp_path / "machine" / "presentation"
    presentation_dir.mkdir(parents=True)
    (presentation_dir / "murmurs-policy.v1.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="presentation contract is invalid JSON"):
        load_presentation_policy(tmp_path)
