from __future__ import annotations

from dataclasses import fields
import json
import pytest

from orchestra_runtime import (
    APPROVED_UNIT_PLAN_SCHEMA_VERSION,
    ApprovedUnitPlan,
    EnvelopeMessageType,
    OrchestraRuntimeEnvelope,
    deserialize_approved_unit_plan,
    serialize_approved_unit_plan,
    validate_approved_unit_plan_context,
)


def test_gate_a_exact_15_dataclass_fields() -> None:
    plan_fields = fields(ApprovedUnitPlan)
    assert len(plan_fields) == 15
    field_names = [f.name for f in plan_fields]
    expected_15_fields = [
        "unit_id",
        "unit_revision",
        "unit_name",
        "phase_id",
        "execution_envelope_ref",
        "scope_ref",
        "responsible_specialist",
        "objective",
        "expected_outputs",
        "validation_requirements",
        "schema_version",
        "allowed_paths",
        "prohibited_paths",
        "dependency_unit_ids",
        "governance_decision_ref",
    ]
    assert field_names == expected_15_fields


def test_gate_a_exact_15_field_schema_and_types() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-01-core-models",
        unit_revision="rev-1",
        unit_name="Core Models Infrastructure",
        phase_id="phase-01-architecture",
        execution_envelope_ref="env-20260803-01",
        scope_ref="sec-04-approved-scope",
        responsible_specialist="clockwork",
        objective="Define core typed dataclasses for coordination runtime.",
        expected_outputs=("orchestra_runtime/models.py",),
        validation_requirements=("python scripts/governance_check.py --strict",),
        schema_version=APPROVED_UNIT_PLAN_SCHEMA_VERSION,
        allowed_paths=("orchestra_runtime/models.py",),
        prohibited_paths=("docs/governance/", "tests/"),
        dependency_unit_ids=(),
        governance_decision_ref="gov-dec-20260722-01",
    )

    assert plan.schema_version == "1.0.0"
    assert plan.unit_id == "unit-01-core-models"
    assert plan.unit_revision == "rev-1"
    assert plan.unit_name == "Core Models Infrastructure"
    assert plan.phase_id == "phase-01-architecture"
    assert plan.execution_envelope_ref == "env-20260803-01"
    assert plan.scope_ref == "sec-04-approved-scope"
    assert plan.responsible_specialist == "clockwork"
    assert plan.objective == "Define core typed dataclasses for coordination runtime."
    assert plan.expected_outputs == ("orchestra_runtime/models.py",)
    assert plan.validation_requirements == ("python scripts/governance_check.py --strict",)
    assert plan.allowed_paths == ("orchestra_runtime/models.py",)
    assert plan.prohibited_paths == ("docs/governance/", "tests/")
    assert plan.dependency_unit_ids == ()
    assert plan.governance_decision_ref == "gov-dec-20260722-01"


def test_gate_a_revision_integer_normalization() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-02",
        unit_revision=2,
        unit_name="Test Unit",
        phase_id="phase-01",
        execution_envelope_ref="env-01",
        scope_ref="scope-01",
        responsible_specialist="ponytail",
        objective="Objective test",
        expected_outputs=("out.txt",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.txt",),
    )
    assert plan.unit_revision == "rev-2"

    with pytest.raises(ValueError, match="unit_revision integer must be non-negative"):
        ApprovedUnitPlan(
            unit_id="unit-02",
            unit_revision=-1,
            unit_name="Test Unit",
            phase_id="phase-01",
            execution_envelope_ref="env-01",
            scope_ref="scope-01",
            responsible_specialist="ponytail",
            objective="Objective test",
            expected_outputs=("out.txt",),
            validation_requirements=("val.sh",),
            allowed_paths=("out.txt",),
        )


def test_contextual_validator_file_mutation_allowed_paths() -> None:
    # Plan with allowed_paths=None is valid structurally
    non_file_plan = ApprovedUnitPlan(
        unit_id="unit-nf",
        unit_revision="rev-1",
        unit_name="Non File Unit",
        phase_id="p1",
        execution_envelope_ref="e1",
        scope_ref="s1",
        responsible_specialist="overseer",
        objective="Review docs",
        expected_outputs=("doc.md",),
        validation_requirements=("check.sh",),
        allowed_paths=None,
    )

    # Validated under READ_ONLY operation context -> Allowed
    res1 = validate_approved_unit_plan_context(non_file_plan, operation_context="READ_ONLY")
    assert res1.allowed is True
    assert res1.status == "ACCEPTED"

    # Validated under FILE_MUTATION operation context -> Rejected for missing allowed_paths
    res2 = validate_approved_unit_plan_context(non_file_plan, operation_context="FILE_MUTATION")
    assert res2.allowed is False
    assert res2.status == "REJECTED"
    assert any("MISSING_ALLOWED_PATHS" in r for r in res2.reasons)


def test_gate_a_path_validation_traversal_and_absolute_rejections() -> None:
    kwargs = {
        "unit_id": "unit-path-test",
        "unit_revision": "rev-1",
        "unit_name": "Path Test",
        "phase_id": "p1",
        "execution_envelope_ref": "e1",
        "scope_ref": "s1",
        "responsible_specialist": "ponytail",
        "objective": "Test paths",
        "expected_outputs": ("out.py",),
        "validation_requirements": ("val.sh",),
    }

    # Absolute path rejection
    with pytest.raises(ValueError, match="absolute path rejected"):
        ApprovedUnitPlan(**kwargs, allowed_paths=("/abs/path/file.py",))

    # Drive letter absolute path
    with pytest.raises(ValueError, match="absolute path rejected"):
        ApprovedUnitPlan(**kwargs, allowed_paths=("C:\\path\\file.py",))

    # File URI path rejection
    with pytest.raises(ValueError, match="file-URI path rejected"):
        ApprovedUnitPlan(**kwargs, allowed_paths=("file:///path/file.py",))

    # Path traversal rejection
    with pytest.raises(ValueError, match="path traversal rejected"):
        ApprovedUnitPlan(**kwargs, allowed_paths=("rel/../file.py",))

    # Persistent .agents/ mutation rejection
    with pytest.raises(ValueError, match="persistent .agents/ path mutation rejected"):
        ApprovedUnitPlan(**kwargs, allowed_paths=(".agents/skills/test/SKILL.md",))


def test_gate_a_prohibited_and_allowed_path_overlap_rejection() -> None:
    with pytest.raises(ValueError, match="prohibited path 'orchestra_runtime' overlaps with allowed path 'orchestra_runtime/models.py'"):
        ApprovedUnitPlan(
            unit_id="unit-overlap",
            unit_revision="rev-1",
            unit_name="Overlap Test",
            phase_id="p1",
            execution_envelope_ref="e1",
            scope_ref="s1",
            responsible_specialist="ponytail",
            objective="Test overlap",
            expected_outputs=("orchestra_runtime/models.py",),
            validation_requirements=("test.sh",),
            allowed_paths=("orchestra_runtime/models.py",),
            prohibited_paths=("orchestra_runtime",),
        )


def test_gate_a_self_dependency_rejection() -> None:
    with pytest.raises(ValueError, match="self dependency rejected: unit 'unit-self' cannot depend on itself"):
        ApprovedUnitPlan(
            unit_id="unit-self",
            unit_revision="rev-1",
            unit_name="Self Dep Test",
            phase_id="p1",
            execution_envelope_ref="e1",
            scope_ref="s1",
            responsible_specialist="ponytail",
            objective="Test self dep",
            expected_outputs=("out.py",),
            validation_requirements=("val.sh",),
            allowed_paths=("out.py",),
            dependency_unit_ids=("unit-self",),
        )


def test_gate_a_dataclass_immutability() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-immutable",
        unit_revision="rev-1",
        unit_name="Immutable Test",
        phase_id="p1",
        execution_envelope_ref="e1",
        scope_ref="s1",
        responsible_specialist="ponytail",
        objective="Test immutability",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    with pytest.raises(Exception):
        plan.unit_id = "new-id"  # type: ignore[misc]


def test_contextual_validator_execution_envelope_and_dependency_binding() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-bound",
        unit_revision="rev-1",
        unit_name="Bound Unit",
        phase_id="phase-01",
        execution_envelope_ref="run-100",
        scope_ref="sec-01",
        responsible_specialist="clockwork",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
        dependency_unit_ids=("pred-unit-01",),
    )

    envelope_matching = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T12:00:00Z",
        run_id="run-100",
        specialist="clockwork",
        operation="FILE_MUTATION",
        status="SUCCESS",
        reason_code="EXECUTION_ACCEPTED",
    )

    # Valid dependency evidence mapping
    evidence_ok = {"pred-unit-01": {"status": "ACCEPTED"}}

    res_ok = validate_approved_unit_plan_context(
        plan,
        envelope=envelope_matching,
        predecessor_evidence=evidence_ok,
    )
    assert res_ok.allowed is True
    assert res_ok.status == "ACCEPTED"

    # Mismatched envelope run_id
    envelope_bad_id = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T12:00:00Z",
        run_id="run-999",
        specialist="clockwork",
        operation="FILE_MUTATION",
        status="SUCCESS",
        reason_code="EXECUTION_ACCEPTED",
    )
    res_bad_env = validate_approved_unit_plan_context(plan, envelope=envelope_bad_id)
    assert res_bad_env.allowed is False
    assert any("ENVELOPE_MISMATCH" in r for r in res_bad_env.reasons)

    # Unaccepted dependency evidence
    evidence_unaccepted = {"pred-unit-01": {"status": "FAILED"}}
    res_bad_dep = validate_approved_unit_plan_context(
        plan,
        envelope=envelope_matching,
        predecessor_evidence=evidence_unaccepted,
    )
    assert res_bad_dep.allowed is False
    assert any("UNACCEPTED_DEPENDENCY" in r for r in res_bad_dep.reasons)


def test_gate_d_strict_serialization_and_deserialization_roundtrip() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-serialize",
        unit_revision="rev-1",
        unit_name="Serialization Unit Test",
        phase_id="phase-02",
        execution_envelope_ref="env-2026-02",
        scope_ref="scope-sec-02",
        responsible_specialist="clockwork",
        objective="Verify UTF-8 JSON roundtrip",
        expected_outputs=("orchestra_runtime/serialization.py",),
        validation_requirements=("python -m pytest tests/runtime/test_approved_unit_plan.py",),
        allowed_paths=("orchestra_runtime/serialization.py",),
        prohibited_paths=("tests/",),
        dependency_unit_ids=("unit-01-core-models",),
        governance_decision_ref="gov-decision-001",
    )

    payload_bytes = serialize_approved_unit_plan(plan)
    assert isinstance(payload_bytes, bytes)
    parsed_dict = json.loads(payload_bytes.decode("utf-8"))
    assert parsed_dict["schema_version"] == "1.0.0"
    assert parsed_dict["unit_id"] == "unit-serialize"
    assert parsed_dict["dependency_unit_ids"] == ["unit-01-core-models"]

    restored = deserialize_approved_unit_plan(payload_bytes)
    assert restored == plan

    restored_str = deserialize_approved_unit_plan(payload_bytes.decode("utf-8"))
    assert restored_str == plan

    assert serialize_approved_unit_plan(restored) == payload_bytes


def test_gate_d_deserialization_rejections() -> None:
    valid_dict = {
        "schema_version": "1.0.0",
        "unit_id": "unit-1",
        "unit_revision": "rev-1",
        "unit_name": "Unit 1",
        "phase_id": "p1",
        "execution_envelope_ref": "e1",
        "scope_ref": "s1",
        "responsible_specialist": "ponytail",
        "objective": "Obj",
        "expected_outputs": ["out.py"],
        "validation_requirements": ["val.sh"],
        "allowed_paths": ["out.py"],
    }
    valid_bytes = json.dumps(valid_dict).encode("utf-8")

    with pytest.raises(TypeError, match="payload must be bytes or str"):
        deserialize_approved_unit_plan(valid_dict)  # type: ignore[arg-type]

    bom_payload = b"\xef\xbb\xbf" + valid_bytes
    with pytest.raises(ValueError, match="UTF-8 BOM is rejected"):
        deserialize_approved_unit_plan(bom_payload)

    with pytest.raises(ValueError, match="empty or whitespace-only unit plan payload"):
        deserialize_approved_unit_plan(b"")

    dup_json = '{"unit_id": "u1", "unit_id": "u2"}'
    with pytest.raises(ValueError, match="duplicate key 'unit_id' detected"):
        deserialize_approved_unit_plan(dup_json.encode("utf-8"))

    missing_data = dict(valid_dict)
    del missing_data["scope_ref"]
    with pytest.raises(ValueError, match="missing required field 'scope_ref'"):
        deserialize_approved_unit_plan(json.dumps(missing_data).encode("utf-8"))

    unknown_data = dict(valid_dict, unknown_field="bogus")
    with pytest.raises(ValueError, match="unknown top-level field 'unknown_field'"):
        deserialize_approved_unit_plan(json.dumps(unknown_data).encode("utf-8"))
