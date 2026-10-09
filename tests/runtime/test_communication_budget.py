import json
from pathlib import Path

import pytest

from orchestra_runtime.communication_budget import (
    COMMUNICATION_MEASUREMENT_SCHEMA_VERSION,
    CommunicationMeasurement,
    TokenMeasurementSource,
    communication_measurement_digest,
    compare_communication_measurements,
)
from orchestra_runtime.presentation import PresentationMode


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "communication-measurement.schema.json"
VALIDATION_DIGEST = "a" * 64
GOVERNANCE_DIGEST = "b" * 64


def measurement(**overrides):
    values = {
        "scenario_id": "scenario-1",
        "mode": PresentationMode.NORMAL,
        "implementation_revision": "baseline",
        "progress_messages": 8,
        "model_progress_calls": 8,
        "user_visible_bytes": 1200,
        "context_bytes_admitted": 4000,
        "tool_result_bytes_admitted": 3000,
        "repeated_reads": 3,
        "task_outcome": "PASS",
        "validation_digest": VALIDATION_DIGEST,
        "governance_digest": GOVERNANCE_DIGEST,
        "token_source": TokenMeasurementSource.UNAVAILABLE,
    }
    values.update(overrides)
    return CommunicationMeasurement(**values)


def test_measurement_schema_version_and_runtime_payload_align():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    sample = measurement()
    assert schema["properties"]["schema_version"]["const"] == COMMUNICATION_MEASUREMENT_SCHEMA_VERSION
    assert sample.to_dict()["schema_version"] == COMMUNICATION_MEASUREMENT_SCHEMA_VERSION
    assert sample.to_dict()["input_tokens"] is None
    assert sample.to_dict()["output_tokens"] is None


def test_unavailable_token_source_never_invents_token_counts():
    baseline = measurement()
    candidate = measurement(
        mode=PresentationMode.MURMURS,
        implementation_revision="candidate",
        progress_messages=4,
        model_progress_calls=0,
        user_visible_bytes=40,
    )
    comparison = compare_communication_measurements(baseline, candidate)
    assert comparison.outcome_parity is True
    assert comparison.model_progress_call_delta == -8
    assert comparison.progress_message_delta == -4
    assert comparison.user_visible_byte_delta == -1160
    assert comparison.token_comparison_available is False
    assert comparison.input_token_delta is None
    assert comparison.output_token_delta is None
    assert comparison.token_counter_id is None


def test_host_reported_same_counter_allows_absolute_token_delta_only():
    baseline = measurement(
        token_source=TokenMeasurementSource.HOST_REPORTED,
        token_counter_id="host:model-x:usage-v1",
        input_tokens=1200,
        output_tokens=500,
    )
    candidate = measurement(
        mode=PresentationMode.MURMURS,
        implementation_revision="candidate",
        token_source=TokenMeasurementSource.HOST_REPORTED,
        token_counter_id="host:model-x:usage-v1",
        input_tokens=900,
        output_tokens=120,
        model_progress_calls=0,
    )
    comparison = compare_communication_measurements(baseline, candidate)
    assert comparison.token_comparison_available is True
    assert comparison.input_token_delta == -300
    assert comparison.output_token_delta == -380
    assert comparison.token_counter_id == "host:model-x:usage-v1"
    assert "percent" not in comparison.to_dict()


def test_different_token_counter_identity_is_not_compared():
    baseline = measurement(
        token_source=TokenMeasurementSource.HOST_REPORTED,
        token_counter_id="host:model-x:usage-v1",
        input_tokens=100,
        output_tokens=100,
    )
    candidate = measurement(
        token_source=TokenMeasurementSource.HOST_REPORTED,
        token_counter_id="host:model-y:usage-v1",
        input_tokens=10,
        output_tokens=10,
    )
    comparison = compare_communication_measurements(baseline, candidate)
    assert comparison.token_comparison_available is False
    assert comparison.input_token_delta is None
    assert comparison.output_token_delta is None


def test_outcome_parity_requires_task_validation_and_governance_identity():
    baseline = measurement()
    changed_outcome = measurement(task_outcome="FAIL")
    changed_validation = measurement(validation_digest="c" * 64)
    changed_governance = measurement(governance_digest="d" * 64)
    assert compare_communication_measurements(baseline, changed_outcome).outcome_parity is False
    assert compare_communication_measurements(baseline, changed_validation).outcome_parity is False
    assert compare_communication_measurements(baseline, changed_governance).outcome_parity is False


def test_elapsed_overhead_is_compared_only_when_both_sides_report_it():
    baseline = measurement(elapsed_communication_ms=80)
    candidate = measurement(elapsed_communication_ms=30)
    assert compare_communication_measurements(baseline, candidate).elapsed_communication_ms_delta == -50
    assert compare_communication_measurements(baseline, measurement()).elapsed_communication_ms_delta is None


def test_measurement_digest_is_deterministic():
    first = measurement()
    second = measurement()
    assert communication_measurement_digest(first) == communication_measurement_digest(second)
    assert len(communication_measurement_digest(first)) == 64


def test_measurement_rejects_invented_or_incomparable_token_payloads():
    with pytest.raises(ValueError, match="cannot carry token counts"):
        measurement(input_tokens=1)
    with pytest.raises(ValueError, match="require counter identity"):
        measurement(token_source=TokenMeasurementSource.HOST_REPORTED, input_tokens=1, output_tokens=1)
    with pytest.raises(ValueError, match="non-negative integer"):
        measurement(progress_messages=-1)
    with pytest.raises(ValueError, match="SHA-256"):
        measurement(validation_digest="not-a-digest")


def test_comparison_requires_same_scenario_identity():
    with pytest.raises(ValueError, match="same scenario_id"):
        compare_communication_measurements(measurement(), measurement(scenario_id="scenario-2"))
