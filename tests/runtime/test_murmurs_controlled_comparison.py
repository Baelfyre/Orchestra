from orchestra_runtime.communication_budget import (
    CommunicationMeasurement,
    TokenMeasurementSource,
    compare_communication_measurements,
)
from orchestra_runtime.presentation import (
    PresentationDisposition,
    PresentationEvent,
    PresentationEventKind,
    PresentationMode,
    decide_presentation,
    render_presentation,
)


VALIDATION_DIGEST = "a" * 64
GOVERNANCE_DIGEST = "b" * 64
ROUTINE_SEQUENCE = (
    PresentationEventKind.EXECUTION_HEARTBEAT,
    PresentationEventKind.TOOL_STARTED,
    PresentationEventKind.TOOL_COMPLETED,
    PresentationEventKind.ROUTINE_VALIDATION_PASSED,
)


def measure_mode(mode: PresentationMode) -> CommunicationMeasurement:
    decisions = [
        decide_presentation(
            PresentationEvent("controlled-scenario", event_kind, index),
            mode=mode,
        )
        for index, event_kind in enumerate(ROUTINE_SEQUENCE)
    ]
    rendered = [render_presentation(item) for item in decisions]
    model_progress_calls = sum(item.disposition is PresentationDisposition.EXPLAIN for item in decisions)
    progress_messages = sum(value not in (None, "") for value in rendered)
    visible_bytes = sum(len(value.encode("utf-8")) for value in rendered if value)
    return CommunicationMeasurement(
        scenario_id="controlled-routine-presentation",
        mode=mode,
        implementation_revision="repository-simulation",
        progress_messages=progress_messages,
        model_progress_calls=model_progress_calls,
        user_visible_bytes=visible_bytes,
        context_bytes_admitted=0,
        tool_result_bytes_admitted=0,
        repeated_reads=0,
        task_outcome="PASS",
        validation_digest=VALIDATION_DIGEST,
        governance_digest=GOVERNANCE_DIGEST,
        token_source=TokenMeasurementSource.UNAVAILABLE,
    )


def test_controlled_policy_comparison_proves_structural_reduction_without_token_claims():
    baseline = measure_mode(PresentationMode.NORMAL)
    candidate = measure_mode(PresentationMode.MURMURS)
    comparison = compare_communication_measurements(baseline, candidate)

    assert baseline.model_progress_calls == len(ROUTINE_SEQUENCE)
    assert candidate.model_progress_calls == 0
    assert comparison.model_progress_call_delta == -len(ROUTINE_SEQUENCE)
    assert comparison.outcome_parity is True

    # One routine event is intentionally SILENT; the others use bounded local fillers.
    assert candidate.progress_messages == 3
    assert candidate.user_visible_bytes > 0

    # Repository simulation does not have host/model token counters. No token delta is inferred.
    assert comparison.token_comparison_available is False
    assert comparison.input_token_delta is None
    assert comparison.output_token_delta is None
