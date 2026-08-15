import json

import pytest

from orchestra_runtime.models import ApprovedUnitPlan, EnvelopeMessageType, OrchestraRuntimeEnvelope
from orchestra_runtime.retrospective import (
    RETROSPECTIVE_SCHEMA_VERSION,
    OrchestraPhaseRetrospective,
    build_phase_retrospective,
    derive_evidence_fingerprint,
    derive_retrospective_id,
    deserialize_phase_retrospective,
    maybe_build_phase_retrospective,
    serialize_phase_retrospective,
    serialize_phase_retrospective_to_str,
    should_generate_phase_retrospective,
)
from orchestra_runtime.serialization import (
    _validate_json_domain,
    deserialize_approved_unit_plan,
    deserialize_runtime_envelope,
    serialize_approved_unit_plan,
    serialize_runtime_envelope,
)


def _retro(**overrides):
    values = dict(
        retrospective_id="retro-P9-run-1",
        phase_id="P9",
        execution_envelope_ref="run-1",
        phase_status="COMPLETED",
        total_units_planned=2,
        units_accepted=2,
        remediation_cycle_count=0,
        capacity_wait_count=0,
        human_escalation_count=0,
        evidence_fingerprint="a" * 64,
        created_at="2026-08-15T12:00:00Z",
    )
    values.update(overrides)
    return OrchestraPhaseRetrospective(**values)


def _plan(**overrides):
    values = dict(
        unit_id="u1",
        unit_revision=1,
        unit_name="Unit",
        phase_id="P9",
        execution_envelope_ref="run-1",
        scope_ref="scope",
        responsible_specialist="conductor",
        objective="fixture",
        expected_outputs=("out",),
        validation_requirements=("pytest",),
    )
    values.update(overrides)
    return ApprovedUnitPlan(**values)


def _envelope(**overrides):
    values = dict(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-15T12:00:00Z",
        run_id="run-1",
        specialist="conductor",
        operation="test",
        status="COMPLETED",
        reason_code="OK",
    )
    values.update(overrides)
    return OrchestraRuntimeEnvelope(**values)


@pytest.mark.parametrize("phase,envelope", [("", "run"), ("P9", "")])
def test_retrospective_identity_rejects_blank_inputs(phase, envelope):
    with pytest.raises(ValueError):
        derive_retrospective_id(phase, envelope)


def test_evidence_fingerprint_accepts_bytes_and_text_equally():
    assert derive_evidence_fingerprint("abc") == derive_evidence_fingerprint(b"abc")
    assert len(derive_evidence_fingerprint("abc")) == 64


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"schema_version": "bad"}, "unsupported schema_version"),
        ({"phase_id": ""}, "phase_id"),
        ({"execution_envelope_ref": ""}, "execution_envelope_ref"),
        ({"created_at": ""}, "created_at"),
        ({"retrospective_id": "wrong"}, "does not match derived identity"),
        ({"phase_status": "RUNNING"}, "invalid phase_status"),
        ({"total_units_planned": True}, "total_units_planned"),
        ({"units_accepted": -1}, "units_accepted"),
        ({"units_accepted": 3}, "cannot exceed"),
        ({"remediation_cycle_count": -1}, "remediation_cycle_count"),
        ({"capacity_wait_count": True}, "capacity_wait_count"),
        ({"human_escalation_count": -1}, "human_escalation_count"),
        ({"evidence_fingerprint": ""}, "evidence_fingerprint"),
    ],
)
def test_retrospective_constructor_fail_closed_edges(overrides, match):
    with pytest.raises(ValueError, match=match):
        _retro(**overrides)


def test_retrospective_optional_fields_normalize_and_serialize():
    retro = _retro(
        outcome_summary=" done ",
        known_limitations=(" ", "limitation"),
        follow_up_candidates=("candidate", ""),
    )
    assert retro.outcome_summary == "done"
    assert retro.known_limitations == ("limitation",)
    assert retro.follow_up_candidates == ("candidate",)
    payload = json.loads(serialize_phase_retrospective_to_str(retro))
    assert payload["outcome_summary"] == "done"
    assert payload["known_limitations"] == ["limitation"]
    assert payload["follow_up_candidates"] == ["candidate"]
    assert serialize_phase_retrospective(retro) == serialize_phase_retrospective_to_str(retro).encode()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"governance_phase_gate": True},
        {"maintainer_decision_ref": "decision:1"},
        {"total_units_planned": 2, "phase_status": "FAILED"},
        {"total_units_planned": 2, "phase_status": "COMPLETED", "remediation_cycle_count": 1},
        {"total_units_planned": 2, "phase_status": "COMPLETED", "capacity_wait_count": 1},
        {"total_units_planned": 2, "phase_status": "COMPLETED", "human_escalation_count": 1},
    ],
)
def test_retrospective_generation_material_signal_edges(kwargs):
    base = dict(total_units_planned=1, phase_status="COMPLETED")
    base.update(kwargs)
    assert should_generate_phase_retrospective(**base) is True


def test_retrospective_not_generated_for_single_clean_completed_phase():
    assert should_generate_phase_retrospective(total_units_planned=1, phase_status="COMPLETED") is False
    assert maybe_build_phase_retrospective(
        phase_id="P9", execution_envelope_ref="run-1", phase_status="COMPLETED",
        total_units_planned=1, units_accepted=1, created_at="now", evidence_fingerprint="a" * 64,
    ) is None


def test_build_and_maybe_build_retrospective_success():
    built = build_phase_retrospective(
        phase_id="P9", execution_envelope_ref="run-1", phase_status="FAILED",
        total_units_planned=2, units_accepted=1, created_at="now", evidence_fingerprint="a" * 64,
        remediation_cycle_count=1,
    )
    assert built.retrospective_id == "retro-P9-run-1"
    maybe = maybe_build_phase_retrospective(
        phase_id="P9", execution_envelope_ref="run-1", phase_status="FAILED",
        total_units_planned=2, units_accepted=1, created_at="now", evidence_fingerprint="a" * 64,
    )
    assert isinstance(maybe, OrchestraPhaseRetrospective)


def test_retrospective_serialization_rejects_wrong_type_and_duplicate_unknown_missing_schema():
    with pytest.raises(TypeError, match="expected OrchestraPhaseRetrospective"):
        serialize_phase_retrospective("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate JSON key"):
        deserialize_phase_retrospective('{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    payload = json.loads(serialize_phase_retrospective_to_str(_retro()))
    payload["unknown"] = 1
    with pytest.raises(ValueError, match="unknown field"):
        deserialize_phase_retrospective(json.dumps(payload))
    del payload["unknown"]
    del payload["phase_id"]
    with pytest.raises(ValueError, match="missing required"):
        deserialize_phase_retrospective(json.dumps(payload))
    payload["phase_id"] = "P9"
    payload["schema_version"] = "bad"
    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_phase_retrospective(json.dumps(payload))


def test_retrospective_deserialize_rejects_invalid_transport_shapes():
    with pytest.raises(ValueError, match="invalid UTF-8"):
        deserialize_phase_retrospective(b"\xff")
    with pytest.raises(ValueError, match="invalid JSON"):
        deserialize_phase_retrospective("{bad")
    with pytest.raises(ValueError, match="non-finite"):
        deserialize_phase_retrospective('{"x":NaN}')
    with pytest.raises(TypeError, match="expected bytes or str"):
        deserialize_phase_retrospective(123)  # type: ignore[arg-type]


def test_retrospective_roundtrip_with_list_optionals():
    original = _retro(known_limitations=("one",), follow_up_candidates=("two",))
    restored = deserialize_phase_retrospective(serialize_phase_retrospective(original))
    assert restored == original


# Deterministic JSON domain / runtime envelope serialization

def test_json_domain_accepts_primitives_and_rejects_nonfinite_unsupported_and_cycles():
    _validate_json_domain({"ok": [None, True, "x", 1, 1.5]})
    with pytest.raises(ValueError, match="non-finite"):
        _validate_json_domain(float("nan"))
    with pytest.raises(TypeError, match="dictionary keys must be strings"):
        _validate_json_domain({1: "bad"})
    with pytest.raises(TypeError, match="unsupported data type"):
        _validate_json_domain(object())
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match="cyclic"):
        _validate_json_domain(cyclic)
    cyclic_dict = {}
    cyclic_dict["self"] = cyclic_dict
    with pytest.raises(ValueError, match="cyclic"):
        _validate_json_domain(cyclic_dict)


def test_runtime_envelope_roundtrip_and_transport_failures():
    original = _envelope(summary="summary", data={"a": [1, 2]})
    encoded = serialize_runtime_envelope(original)
    restored = deserialize_runtime_envelope(encoded)
    assert restored.to_dict() == original.to_dict()
    with pytest.raises(TypeError, match="expected OrchestraRuntimeEnvelope"):
        serialize_runtime_envelope("bad")  # type: ignore[arg-type]
    for bad in (b"\xef\xbb\xbf{}", "\ufeff{}"):
        with pytest.raises(ValueError, match="BOM"):
            deserialize_runtime_envelope(bad)
    with pytest.raises(ValueError, match="invalid UTF-8"):
        deserialize_runtime_envelope(b"\xff")
    with pytest.raises(TypeError, match="payload must be bytes or str"):
        deserialize_runtime_envelope(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="empty"):
        deserialize_runtime_envelope("   ")
    with pytest.raises(ValueError, match="malformed JSON"):
        deserialize_runtime_envelope("{bad")
    with pytest.raises(ValueError, match="top-level envelope JSON must be an object"):
        deserialize_runtime_envelope("[]")


def test_runtime_envelope_deserialize_rejects_duplicate_unknown_missing_null_type_and_schema():
    with pytest.raises(ValueError, match="duplicate key"):
        deserialize_runtime_envelope('{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    base = _envelope().to_dict()
    base["unknown"] = 1
    with pytest.raises(ValueError, match="unknown top-level field"):
        deserialize_runtime_envelope(json.dumps(base))
    del base["unknown"]
    del base["run_id"]
    with pytest.raises(ValueError, match="missing required field"):
        deserialize_runtime_envelope(json.dumps(base))
    base["run_id"] = None
    with pytest.raises(ValueError, match="cannot be null"):
        deserialize_runtime_envelope(json.dumps(base))
    base["run_id"] = 1
    with pytest.raises(ValueError, match="must be a string"):
        deserialize_runtime_envelope(json.dumps(base))
    base["run_id"] = "run-1"
    base["schema_version"] = "9"
    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_runtime_envelope(json.dumps(base))


# ApprovedUnitPlan serialization

def test_unit_plan_full_optional_roundtrip():
    plan = _plan(
        allowed_paths=("src",), prohibited_paths=("docs/private",), dependency_unit_ids=("u0",),
        governance_decision_ref="gov:1",
    )
    encoded = serialize_approved_unit_plan(plan)
    restored = deserialize_approved_unit_plan(encoded)
    assert restored == plan
    payload = json.loads(encoded)
    assert payload["allowed_paths"] == ["src"]
    assert payload["prohibited_paths"] == ["docs/private"]
    assert payload["dependency_unit_ids"] == ["u0"]
    assert payload["governance_decision_ref"] == "gov:1"


def test_unit_plan_serialization_transport_and_shape_failures():
    with pytest.raises(TypeError, match="expected ApprovedUnitPlan"):
        serialize_approved_unit_plan("bad")  # type: ignore[arg-type]
    for bad in (b"\xef\xbb\xbf{}", "\ufeff{}"):
        with pytest.raises(ValueError, match="BOM"):
            deserialize_approved_unit_plan(bad)
    with pytest.raises(ValueError, match="invalid UTF-8"):
        deserialize_approved_unit_plan(b"\xff")
    with pytest.raises(TypeError, match="payload must be bytes or str"):
        deserialize_approved_unit_plan(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="empty"):
        deserialize_approved_unit_plan(" ")
    with pytest.raises(ValueError, match="malformed JSON"):
        deserialize_approved_unit_plan("{bad")
    with pytest.raises(ValueError, match="top-level unit plan JSON must be an object"):
        deserialize_approved_unit_plan("[]")
    with pytest.raises(ValueError, match="duplicate key"):
        deserialize_approved_unit_plan('{"unit_id":"a","unit_id":"b"}')


def test_unit_plan_deserialize_rejects_unknown_schema_missing_null_and_wrong_list_shapes():
    payload = json.loads(serialize_approved_unit_plan(_plan()))
    payload["unknown"] = 1
    with pytest.raises(ValueError, match="unknown top-level field"):
        deserialize_approved_unit_plan(json.dumps(payload))
    del payload["unknown"]
    payload["schema_version"] = "bad"
    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_approved_unit_plan(json.dumps(payload))
    payload["schema_version"] = RETROSPECTIVE_SCHEMA_VERSION
    del payload["unit_id"]
    with pytest.raises(ValueError, match="missing required field"):
        deserialize_approved_unit_plan(json.dumps(payload))
    payload["unit_id"] = None
    with pytest.raises(ValueError, match="cannot be null"):
        deserialize_approved_unit_plan(json.dumps(payload))
    payload["unit_id"] = "u1"
    payload["expected_outputs"] = "bad"
    with pytest.raises(ValueError, match="expected_outputs must be a list"):
        deserialize_approved_unit_plan(json.dumps(payload))
    payload["expected_outputs"] = ["out"]
    payload["validation_requirements"] = "bad"
    with pytest.raises(ValueError, match="validation_requirements must be a list"):
        deserialize_approved_unit_plan(json.dumps(payload))
