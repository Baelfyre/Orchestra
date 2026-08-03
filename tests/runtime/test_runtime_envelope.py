import json
import math
import pytest

from orchestra_runtime.models import (
    EnvelopeMessageType,
    OrchestraRuntimeEnvelope,
)
from orchestra_runtime.serialization import (
    deserialize_runtime_envelope,
    serialize_runtime_envelope,
)


# --- Positive Tests ---

def test_execution_result_envelope_construction():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="ponytail",
        operation="targeted_code_edit",
        status="COMPLETED",
        reason_code="IMPLEMENTATION_SUCCESS",
        evidence_fingerprint="abc123sha256",
        summary="Refactoring done.",
        data={"files_changed": ["orchestra_runtime/models.py"]},
    )

    assert envelope.schema_version == "1.0.0"
    assert envelope.message_type == EnvelopeMessageType.EXECUTION_RESULT
    assert envelope.timestamp == "2026-08-03T08:00:00Z"
    assert envelope.run_id == "run-001"
    assert envelope.specialist == "ponytail"
    assert envelope.operation == "targeted_code_edit"
    assert envelope.status == "COMPLETED"
    assert envelope.reason_code == "IMPLEMENTATION_SUCCESS"
    assert envelope.evidence_fingerprint == "abc123sha256"
    assert envelope.summary == "Refactoring done."
    assert envelope.data == {"files_changed": ["orchestra_runtime/models.py"]}
    assert envelope.correlation_id is None


def test_transition_decision_envelope_construction():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-03T08:05:00Z",
        run_id="run-002",
        specialist="arbiter",
        operation="delegated_phase_transition_check",
        disposition="AUTO_CONTINUE",
        reason_code="PHASE_GATE_CLEARANCE",
        phase_id="delegated-phase-b",
        unit_id="unit-1",
        governance_decision_ref="gov-dec-123",
        summary="Arbiter phase gate clearance.",
    )

    assert envelope.message_type == EnvelopeMessageType.TRANSITION_DECISION
    assert envelope.operation == "delegated_phase_transition_check"
    assert envelope.disposition == "AUTO_CONTINUE"
    assert envelope.reason_code == "PHASE_GATE_CLEARANCE"
    assert envelope.phase_id == "delegated-phase-b"
    assert envelope.unit_id == "unit-1"
    assert envelope.governance_decision_ref == "gov-dec-123"


def test_audit_event_envelope_construction():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:10:00Z",
        run_id="run-003",
        specialist="chronicler",
        event_type="COORDINATION_SIGNAL_RECORDED",
        collaboration_session_id="session-001",
        details={"signal_name": "unit_completion_verified"},
    )

    assert envelope.message_type == EnvelopeMessageType.AUDIT_EVENT
    assert envelope.event_type == "COORDINATION_SIGNAL_RECORDED"
    assert envelope.collaboration_session_id == "session-001"
    assert envelope.details == {"signal_name": "unit_completion_verified"}


def test_serialization_returns_utf8_bytes():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="clockwork",
        operation="schema_design",
        status="COMPLETED",
        reason_code="DESIGN_CLEARANCE",
    )

    output = serialize_runtime_envelope(envelope)
    assert isinstance(output, bytes)
    parsed = json.loads(output.decode("utf-8"))
    assert parsed["schema_version"] == "1.0.0"
    assert parsed["message_type"] == "execution_result"


def test_repeated_serialization_produces_identical_bytes():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="arbiter",
        operation="phase_check",
        disposition="AUTO_CONTINUE",
        reason_code="CLEARANCE",
        summary="Test summary",
        data={"b": 2, "a": 1},
    )

    bytes1 = serialize_runtime_envelope(envelope)
    bytes2 = serialize_runtime_envelope(envelope)
    assert bytes1 == bytes2


def test_equivalent_mapping_input_produces_stable_key_ordering():
    env1 = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="chronicler",
        event_type="AUDIT",
        details={"z": 26, "a": 1, "m": 13},
    )
    env2 = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="chronicler",
        event_type="AUDIT",
        details={"a": 1, "m": 13, "z": 26},
    )

    assert serialize_runtime_envelope(env1) == serialize_runtime_envelope(env2)


def test_unicode_data_roundtrips_through_json_decoding():
    summary_text = "Refactoring finished — 🚀 test passed safely."
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-unicode",
        specialist="ponytail",
        operation="edit",
        status="COMPLETED",
        reason_code="SUCCESS",
        summary=summary_text,
    )

    raw_bytes = serialize_runtime_envelope(envelope)
    decoded = json.loads(raw_bytes.decode("utf-8"))
    assert decoded["summary"] == summary_text


def test_optional_correlation_id_omitted_when_absent():
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="ponytail",
        operation="edit",
        status="COMPLETED",
        reason_code="SUCCESS",
    )

    raw_bytes = serialize_runtime_envelope(envelope)
    decoded = json.loads(raw_bytes.decode("utf-8"))
    assert "correlation_id" not in decoded


def test_optional_correlation_id_emitted_when_present():
    cid = "018c3b7a-9f4a-7111-8201-000000000001"
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="ponytail",
        operation="edit",
        status="COMPLETED",
        reason_code="SUCCESS",
        correlation_id=cid,
    )

    raw_bytes = serialize_runtime_envelope(envelope)
    decoded = json.loads(raw_bytes.decode("utf-8"))
    assert decoded["correlation_id"] == cid


def test_variant_discriminator_is_correct():
    for msg_enum, str_val in (
        (EnvelopeMessageType.EXECUTION_RESULT, "execution_result"),
        (EnvelopeMessageType.TRANSITION_DECISION, "transition_decision"),
        (EnvelopeMessageType.AUDIT_EVENT, "audit_event"),
    ):
        if msg_enum == EnvelopeMessageType.EXECUTION_RESULT:
            env = OrchestraRuntimeEnvelope(
                schema_version="1.0.0",
                message_type=msg_enum,
                timestamp="2026-08-03T08:00:00Z",
                run_id="r1",
                specialist="s1",
                operation="op",
                status="COMPLETED",
                reason_code="RC",
            )
        elif msg_enum == EnvelopeMessageType.TRANSITION_DECISION:
            env = OrchestraRuntimeEnvelope(
                schema_version="1.0.0",
                message_type=msg_enum,
                timestamp="2026-08-03T08:00:00Z",
                run_id="r1",
                specialist="s1",
                operation="op",
                disposition="AUTO_CONTINUE",
                reason_code="RC",
            )
        else:
            env = OrchestraRuntimeEnvelope(
                schema_version="1.0.0",
                message_type=msg_enum,
                timestamp="2026-08-03T08:00:00Z",
                run_id="r1",
                specialist="s1",
                event_type="EVT",
                details={"k": "v"},
            )

        decoded = json.loads(serialize_runtime_envelope(env).decode("utf-8"))
        assert decoded["message_type"] == str_val


def test_canonical_status_disposition_reason_code_transcribed_unchanged():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="arbiter",
        operation="phase_gate",
        disposition="AUTO_REMEDIATE_AND_REVALIDATE",
        reason_code="VALIDATION_REMEDIATION_REQUIRED",
    )

    decoded = json.loads(serialize_runtime_envelope(env).decode("utf-8"))
    assert decoded["disposition"] == "AUTO_REMEDIATE_AND_REVALIDATE"
    assert decoded["reason_code"] == "VALIDATION_REMEDIATION_REQUIRED"


def test_serialization_does_not_mutate_source_model_or_details():
    orig_details = {"key1": "val1", "key2": "val2"}
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-001",
        specialist="chronicler",
        event_type="TEST_EVENT",
        details=orig_details,
    )

    _ = serialize_runtime_envelope(env)

    assert env.details == {"key1": "val1", "key2": "val2"}
    assert orig_details == {"key1": "val1", "key2": "val2"}


# --- Negative Tests ---

def test_missing_shared_required_field():
    with pytest.raises(ValueError, match="schema_version must be non-empty"):
        OrchestraRuntimeEnvelope(
            schema_version="",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            operation="op",
            status="COMPLETED",
            reason_code="RC",
        )

    with pytest.raises(ValueError, match="timestamp must be non-empty"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="   ",
            run_id="r1",
            specialist="s1",
            operation="op",
            status="COMPLETED",
            reason_code="RC",
        )


def test_missing_variant_specific_field():
    with pytest.raises(ValueError, match="execution_result variant requires non-empty operation, status, and reason_code"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            operation="op",
            status="COMPLETED",
            reason_code="",
        )

    with pytest.raises(ValueError, match="transition_decision variant requires non-empty operation, disposition, and reason_code"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.TRANSITION_DECISION,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            operation="op",
            disposition="",
            reason_code="RC",
        )

    with pytest.raises(ValueError, match="audit_event variant requires details mapping"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.AUDIT_EVENT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            event_type="EVT",
            details=None,
        )


def test_unsupported_message_type():
    with pytest.raises(ValueError, match="unsupported message_type: invalid_type"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type="invalid_type",
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
        )


def test_cross_variant_field_misuse():
    with pytest.raises(ValueError, match="execution_result variant prohibits field 'disposition'"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            operation="op",
            status="COMPLETED",
            reason_code="RC",
            disposition="AUTO_CONTINUE",
        )

    with pytest.raises(ValueError, match="transition_decision variant prohibits field 'status'"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.TRANSITION_DECISION,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            operation="op",
            disposition="AUTO_CONTINUE",
            reason_code="RC",
            status="COMPLETED",
        )

    with pytest.raises(ValueError, match="audit_event variant prohibits field 'operation'"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.AUDIT_EVENT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="r1",
            specialist="s1",
            event_type="EVT",
            details={"a": 1},
            operation="op",
        )


def test_empty_required_identifier_or_discriminator():
    with pytest.raises(ValueError, match="run_id must be non-empty"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="2026-08-03T08:00:00Z",
            run_id="   ",
            specialist="s1",
            operation="op",
            status="COMPLETED",
            reason_code="RC",
        )


def test_non_string_audit_detail_key():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={123: "val"},  # Integer key
    )

    with pytest.raises(TypeError, match="dictionary keys must be strings"):
        serialize_runtime_envelope(env)


def test_unsupported_custom_object():
    class CustomObj:
        pass

    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={"key": CustomObj()},
    )

    with pytest.raises(TypeError, match="unsupported data type 'CustomObj'"):
        serialize_runtime_envelope(env)


def test_nan_rejection():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={"bad_float": float("nan")},
    )

    with pytest.raises(ValueError, match="non-finite float value"):
        serialize_runtime_envelope(env)


def test_positive_infinity_rejection():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={"bad_float": float("inf")},
    )

    with pytest.raises(ValueError, match="non-finite float value"):
        serialize_runtime_envelope(env)


def test_negative_infinity_rejection():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={"bad_float": float("-inf")},
    )

    with pytest.raises(ValueError, match="non-finite float value"):
        serialize_runtime_envelope(env)


def test_cyclic_detail_structure():
    cyclic_dict = {}
    cyclic_dict["self"] = cyclic_dict

    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details=cyclic_dict,
    )

    with pytest.raises(ValueError, match="cyclic structure detected"):
        serialize_runtime_envelope(env)


def test_cyclic_list_structure():
    cyclic_list = []
    cyclic_list.append(cyclic_list)

    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        event_type="EVT",
        details={"nested_list": cyclic_list},
    )

    with pytest.raises(ValueError, match="cyclic structure detected"):
        serialize_runtime_envelope(env)


def test_nested_list_and_tuple_types_supported():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="r1",
        specialist="s1",
        operation="op",
        status="COMPLETED",
        reason_code="RC",
        data={"items": [1, True, 3.14, (4, "text")]},
    )

    raw_bytes = serialize_runtime_envelope(env)
    decoded = json.loads(raw_bytes.decode("utf-8"))
    assert decoded["data"]["items"] == [1, True, 3.14, [4, "text"]]


def test_unsupported_envelope_object_passed_to_serializer():
    with pytest.raises(TypeError, match="expected OrchestraRuntimeEnvelope instance"):
        serialize_runtime_envelope({"not": "an_envelope"})


# --- Deserialization Positive and Negative Tests ---

def test_deserialize_positive_all_variants_round_trip():
    from orchestra_runtime import generate_correlation_id
    valid_cid = generate_correlation_id()
    res_env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-01",
        specialist="ponytail",
        operation="edit",
        status="COMPLETED",
        reason_code="SUCCESS",
        correlation_id=valid_cid,
        summary="Done",
        data={"ok": True},
    )
    bytes_payload = serialize_runtime_envelope(res_env)
    parsed_res = deserialize_runtime_envelope(bytes_payload)
    assert parsed_res == res_env
    assert serialize_runtime_envelope(parsed_res) == bytes_payload

    dec_env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-02",
        specialist="arbiter",
        operation="transition",
        disposition="AUTO_CONTINUE",
        reason_code="GOVERNANCE_PASS",
        phase_id="2B.2",
    )
    parsed_dec = deserialize_runtime_envelope(serialize_runtime_envelope(dec_env))
    assert parsed_dec == dec_env

    aud_env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.AUDIT_EVENT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-03",
        specialist="cipher",
        event_type="SECURITY_AUDIT",
        details={"finding": "NONE", "unicode": "こんにちは"},
    )
    parsed_aud = deserialize_runtime_envelope(serialize_runtime_envelope(aud_env))
    assert parsed_aud == aud_env
    assert parsed_aud.details["unicode"] == "こんにちは"


def test_deserialize_accepts_str_payload():
    env = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-str",
        specialist="ponytail",
        operation="op",
        status="COMPLETED",
        reason_code="RC",
    )
    json_str = serialize_runtime_envelope(env).decode("utf-8")
    parsed = deserialize_runtime_envelope(json_str)
    assert parsed == env


def test_deserialize_invalid_payload_type():
    with pytest.raises(TypeError, match="payload must be bytes or str"):
        deserialize_runtime_envelope(12345)


def test_deserialize_invalid_utf8_bytes():
    with pytest.raises(ValueError, match="invalid UTF-8 byte sequence"):
        deserialize_runtime_envelope(b"\x80\x81\x82")


def test_deserialize_utf8_bom_rejected():
    bom_bytes = b"\xef\xbb\xbf" + json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": "r1",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    }).encode("utf-8")

    with pytest.raises(ValueError, match="UTF-8 BOM is rejected"):
        deserialize_runtime_envelope(bom_bytes)

    bom_str = "\ufeff" + json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": "r1",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    })

    with pytest.raises(ValueError, match="UTF-8 BOM is rejected"):
        deserialize_runtime_envelope(bom_str)


def test_deserialize_empty_or_whitespace_payload():
    with pytest.raises(ValueError, match="empty or whitespace-only envelope payload"):
        deserialize_runtime_envelope(b"")

    with pytest.raises(ValueError, match="empty or whitespace-only envelope payload"):
        deserialize_runtime_envelope("   \n\t  ")


def test_deserialize_malformed_json():
    with pytest.raises(ValueError, match="malformed JSON payload"):
        deserialize_runtime_envelope("{not_valid_json")


def test_deserialize_top_level_non_object():
    with pytest.raises(ValueError, match="top-level envelope JSON must be an object"):
        deserialize_runtime_envelope("[1, 2, 3]")

    with pytest.raises(ValueError, match="top-level envelope JSON must be an object"):
        deserialize_runtime_envelope('"just a string"')


def test_deserialize_duplicate_key_rejected():
    raw_json = """{
        "schema_version": "1.0.0",
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": "r1",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC"
    }"""
    with pytest.raises(ValueError, match="duplicate key 'schema_version' detected"):
        deserialize_runtime_envelope(raw_json)


def test_deserialize_unknown_top_level_field():
    raw_json = json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": "r1",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
        "unauthorized_extra_field": "test",
    })
    with pytest.raises(ValueError, match="unknown top-level field 'unauthorized_extra_field'"):
        deserialize_runtime_envelope(raw_json)


def test_deserialize_unsupported_schema_version():
    raw_json = json.dumps({
        "schema_version": "2.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": "r1",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    })
    with pytest.raises(ValueError, match="unsupported schema_version: '2.0.0'"):
        deserialize_runtime_envelope(raw_json)


def test_deserialize_null_in_required_field():
    raw_json = json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": None,
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    })
    with pytest.raises(ValueError, match="field 'run_id' cannot be null"):
        deserialize_runtime_envelope(raw_json)


def test_deserialize_missing_required_shared_field():
    raw_json = json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    })
    with pytest.raises(ValueError, match="missing required field 'run_id'"):
        deserialize_runtime_envelope(raw_json)


def test_deserialize_non_string_required_field():
    raw_json = json.dumps({
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-03T08:00:00Z",
        "run_id": 12345,
        "specialist": "s1",
        "operation": "op",
        "status": "COMPLETED",
        "reason_code": "RC",
    })
    with pytest.raises(ValueError, match="field 'run_id' must be a string"):
        deserialize_runtime_envelope(raw_json)



