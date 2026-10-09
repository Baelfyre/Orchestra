from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
)
from orchestra_runtime.remediation_circuit import (
    CircuitConstraint,
    CircuitReason,
    RemediationCircuitState,
    evaluate_circuit_with_arbiter,
    failure_signature,
    record_evidence_wait,
    record_success,
    request_remediation,
)


def _state(**overrides):
    values = {
        "project_id": "orchestra",
        "unit_id": "p7",
        "envelope_id": "env-p7",
    }
    values.update(overrides)
    return RemediationCircuitState(**values)


def _sig(reason="TEST_FAIL", evidence="a" * 64):
    return failure_signature(validator_id="pytest", reason_code=reason, evidence_digest=evidence)


def _kernel(**overrides):
    values = {
        "project_id": "orchestra",
        "unit_id": "p7",
        "governance_decisions": (
            GovernanceDecisionRecord(
                reviewer="overseer",
                project_context="p7",
                decision="REVISION_REQUIRED",
                reason="deterministic test failure",
            ),
        ),
    }
    values.update(overrides)
    return ArbiterKernelInput(**values)


def test_first_deterministic_failure_allows_bounded_remediation():
    decision = request_remediation(_state(), failure_digest=_sig())
    assert decision.constraint is CircuitConstraint.ALLOW_REMEDIATION
    assert decision.reason is CircuitReason.REMEDIATION_AVAILABLE
    assert decision.state.total_remediation_attempts == 1
    result = evaluate_circuit_with_arbiter(_kernel(), decision)
    assert result.arbiter_result.disposition is TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE


def test_identical_failure_two_attempts_allowed_third_request_escalates():
    first = request_remediation(_state(), failure_digest=_sig())
    second = request_remediation(first.state, failure_digest=_sig())
    third = request_remediation(second.state, failure_digest=_sig())
    assert first.constraint is CircuitConstraint.ALLOW_REMEDIATION
    assert second.constraint is CircuitConstraint.ALLOW_REMEDIATION
    assert third.constraint is CircuitConstraint.ESCALATE_HUMAN
    assert third.reason is CircuitReason.IDENTICAL_FAILURE_LIMIT_EXCEEDED


def test_total_budget_three_exhausted_even_across_different_failures():
    state = _state()
    for index in range(3):
        decision = request_remediation(state, failure_digest=_sig(f"FAIL_{index}"))
        assert decision.constraint is CircuitConstraint.ALLOW_REMEDIATION
        state = decision.state
    exhausted = request_remediation(state, failure_digest=_sig("FAIL_4"))
    assert exhausted.constraint is CircuitConstraint.ESCALATE_HUMAN
    assert exhausted.reason is CircuitReason.TOTAL_BUDGET_EXHAUSTED


def test_changed_failure_signature_resets_identical_count_not_total_budget():
    first = request_remediation(_state(), failure_digest=_sig("A"))
    second = request_remediation(first.state, failure_digest=_sig("A"))
    changed = request_remediation(second.state, failure_digest=_sig("B"))
    assert changed.state.identical_failure_repetitions == 1
    assert changed.state.total_remediation_attempts == 3


def test_no_progress_across_changed_failures_escalates_when_limit_exceeded():
    state = _state(maximum_remediation_attempts=10, maximum_identical_failure_repetitions=10, maximum_no_progress_cycles=2)
    progress = "c" * 64
    first = request_remediation(state, failure_digest=_sig("A"), progress_digest=progress)
    second = request_remediation(first.state, failure_digest=_sig("B"), progress_digest=progress)
    third = request_remediation(second.state, failure_digest=_sig("C"), progress_digest=progress)
    fourth = request_remediation(third.state, failure_digest=_sig("D"), progress_digest=progress)
    assert fourth.constraint is CircuitConstraint.ESCALATE_HUMAN
    assert fourth.reason is CircuitReason.NO_PROGRESS_LIMIT_EXCEEDED


def test_wait_remediation_oscillation_escalates_beyond_bound():
    state = _state(
        maximum_remediation_attempts=10,
        maximum_identical_failure_repetitions=10,
        maximum_wait_remediation_transitions=4,
    )
    first = request_remediation(state, failure_digest=_sig("A"))
    wait1 = record_evidence_wait(first.state)
    second = request_remediation(wait1.state, failure_digest=_sig("B"))
    wait2 = record_evidence_wait(second.state)
    third = request_remediation(wait2.state, failure_digest=_sig("C"))
    assert third.constraint is CircuitConstraint.ALLOW_REMEDIATION
    assert third.state.wait_remediation_transitions == 4
    wait3 = record_evidence_wait(third.state)
    assert wait3.constraint is CircuitConstraint.ESCALATE_HUMAN
    assert wait3.reason is CircuitReason.WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED


def test_success_resets_local_loop_counters_but_preserves_total_attempt_audit():
    first = request_remediation(_state(), failure_digest=_sig())
    wait = record_evidence_wait(first.state)
    success = record_success(wait.state, progress_digest="d" * 64)
    assert success.constraint is CircuitConstraint.CONTINUE
    assert success.state.total_remediation_attempts == 1
    assert success.state.identical_failure_repetitions == 0
    assert success.state.wait_remediation_transitions == 0
    assert success.state.no_progress_cycles == 0
    assert success.state.successful_recoveries == 1


def test_serialized_state_round_trip_preserves_budget_and_digest():
    first = request_remediation(_state(), failure_digest=_sig())
    reloaded = RemediationCircuitState.from_dict(first.state.to_dict())
    assert reloaded == first.state
    assert reloaded.digest == first.state.digest
    second = request_remediation(reloaded, failure_digest=_sig("NEW"))
    assert second.state.total_remediation_attempts == 2


def test_circuit_escalation_cannot_override_higher_priority_authority_stop():
    state = _state(total_remediation_attempts=3)
    circuit = request_remediation(state, failure_digest=_sig("NEW"))
    result = evaluate_circuit_with_arbiter(_kernel(authority_valid=False), circuit)
    assert circuit.constraint is CircuitConstraint.ESCALATE_HUMAN
    assert result.arbiter_result.disposition is TransitionDisposition.STOP


def test_evidence_wait_constraint_maps_to_arbiter_wait_for_evidence():
    wait = record_evidence_wait(_state())
    result = evaluate_circuit_with_arbiter(
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="p7",
            governance_decisions=(
                GovernanceDecisionRecord(
                    reviewer="overseer",
                    project_context="p7",
                    decision="APPROVED",
                    reason="waiting for fresh evidence",
                ),
            ),
        ),
        wait,
    )
    assert result.arbiter_result.disposition is TransitionDisposition.WAIT_FOR_EVIDENCE
