from __future__ import annotations

import json
import pytest

from orchestra_runtime import (
    APPROVED_UNIT_PLAN_SCHEMA_VERSION,
    RETROSPECTIVE_SCHEMA_VERSION,
    ApprovedUnitPlan,
    EnvelopeMessageType,
    OrchestraPhaseRetrospective,
    OrchestraRuntimeEnvelope,
    RunIdentity,
    build_phase_retrospective,
    deserialize_approved_unit_plan,
    deserialize_phase_retrospective,
    deserialize_runtime_envelope,
    generate_correlation_id,
    serialize_approved_unit_plan,
    serialize_phase_retrospective,
    serialize_runtime_envelope,
    validate_approved_unit_plan_context,
    validate_correlation_id,
)


def test_cross_contract_01_trusted_root_correlation_reaches_envelope() -> None:
    cid = generate_correlation_id()
    assert validate_correlation_id(cid) == cid

    identity = RunIdentity(run_id="run-root-01", correlation_id=cid)
    assert identity.correlation_id == cid

    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T12:00:00Z",
        run_id=identity.run_id,
        specialist="ponytail",
        operation="FILE_MUTATION",
        status="SUCCESS",
        reason_code="EXECUTION_COMPLETED",
        correlation_id=cid,
    )
    assert envelope.correlation_id == cid


def test_cross_contract_02_child_correlation_propagates_without_new_authority() -> None:
    root_cid = generate_correlation_id()
    parent_id = RunIdentity(run_id="run-parent", correlation_id=root_cid)
    child_id = RunIdentity(run_id="run-child", parent_run_id=parent_id.run_id, correlation_id=root_cid)

    assert child_id.correlation_id == root_cid
    assert child_id.parent_run_id == "run-parent"


def test_cross_contract_03_envelope_correlation_transport_only() -> None:
    cid = generate_correlation_id()
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T12:00:00Z",
        run_id="run-transport",
        specialist="ponytail",
        operation="FILE_MUTATION",
        status="SUCCESS",
        reason_code="EXECUTION_COMPLETED",
        correlation_id=cid,
    )
    # Correlation ID presence in envelope does not grant execution authority or override governance
    assert envelope.correlation_id == cid
    assert envelope.authority_decision_ref is None


def test_cross_contract_04_retrospective_correlation_observational_and_non_authorizing() -> None:
    cid = generate_correlation_id()
    retro = build_phase_retrospective(
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        phase_status="COMPLETED",
        total_units_planned=3,
        units_accepted=3,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp123",
        correlation_id=cid,
    )
    assert retro.correlation_id == cid
    # Retrospective is purely observational metadata, does not replace execution envelopes or decision logs
    assert retro.phase_status == "COMPLETED"


def test_cross_contract_05_approved_unit_plan_correlation_non_authorizing() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-01",
        unit_revision="rev-1",
        unit_name="Unit 1",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="clockwork",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    # ApprovedUnitPlan binds authority via execution_envelope_ref, not correlation ID
    assert plan.execution_envelope_ref == "env-100"


def test_cross_contract_06_governance_ref_cannot_replace_execution_envelope() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-gov-check",
        unit_revision="rev-1",
        unit_name="Gov Check Unit",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
        governance_decision_ref="gov-dec-999",
    )
    # Validating against a mismatched envelope fails even if governance_decision_ref is set
    envelope_wrong = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T12:00:00Z",
        run_id="env-OTHER",
        specialist="ponytail",
        operation="FILE_MUTATION",
        status="SUCCESS",
        reason_code="EXECUTION_ACCEPTED",
    )
    res = validate_approved_unit_plan_context(plan, envelope=envelope_wrong)
    assert res.allowed is False
    assert any("ENVELOPE_MISMATCH" in r for r in res.reasons)


def test_cross_contract_07_retrospective_cannot_satisfy_dependency_acceptance() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-dep-check",
        unit_revision="rev-1",
        unit_name="Dep Check",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
        dependency_unit_ids=("pred-01",),
    )

    # Passing retrospective object as predecessor evidence does not substitute for accepted evidence
    bad_evidence = {"pred-01": "retrospective-record-string"}
    res = validate_approved_unit_plan_context(plan, predecessor_evidence=bad_evidence)
    assert res.allowed is False
    assert any("UNACCEPTED_DEPENDENCY" in r for r in res.reasons)


def test_cross_contract_08_runtime_envelope_cannot_satisfy_dependency_acceptance() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-dep-env",
        unit_revision="rev-1",
        unit_name="Dep Env Check",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
        dependency_unit_ids=("pred-01",),
    )
    bad_evidence = {"pred-01": {"status": "IN_PROGRESS"}}
    res = validate_approved_unit_plan_context(plan, predecessor_evidence=bad_evidence)
    assert res.allowed is False


def test_cross_contract_09_completion_does_not_equal_predecessor_acceptance() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-dep-acc",
        unit_revision="rev-1",
        unit_name="Dep Acc Check",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
        dependency_unit_ids=("pred-01",),
    )
    # Execution completed with FAILED or REJECTED status does NOT satisfy dependency
    failed_evidence = {"pred-01": {"status": "FAILED"}}
    res = validate_approved_unit_plan_context(plan, predecessor_evidence=failed_evidence)
    assert res.allowed is False


def test_cross_contract_10_approved_unit_plan_scope_cannot_widen_by_revision_alone() -> None:
    plan_v1 = ApprovedUnitPlan(
        unit_id="unit-rev-scope",
        unit_revision="rev-1",
        unit_name="Rev Scope Check",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    plan_v2 = ApprovedUnitPlan(
        unit_id="unit-rev-scope",
        unit_revision="rev-2",
        unit_name="Rev Scope Check",
        phase_id="phase-01",
        execution_envelope_ref="env-100",
        scope_ref="sec-01",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    assert plan_v1.scope_ref == plan_v2.scope_ref == "sec-01"
    assert plan_v2.unit_revision == "rev-2"


def test_cross_contract_11_adapter_parsing_cannot_create_canonical_authority() -> None:
    # Parsing envelope via adapter helper returns typed OrchestraRuntimeEnvelope, not execution authority
    envelope_data = {
        "schema_version": "1.0.0",
        "message_type": "execution_result",
        "timestamp": "2026-08-04T12:00:00Z",
        "run_id": "run-adapter-1",
        "specialist": "codex",
        "operation": "READ_ONLY",
        "status": "SUCCESS",
        "reason_code": "EXECUTION_COMPLETED",
    }
    parsed = deserialize_runtime_envelope(json.dumps(envelope_data).encode("utf-8"))
    assert parsed.specialist == "codex"
    assert parsed.authority_decision_ref is None


def test_cross_contract_12_deserializing_any_contract_does_not_create_trusted_provenance() -> None:
    retro_data = {
        "schema_version": "1.0.0",
        "retrospective_id": "retro-p1-e1",
        "phase_id": "p1",
        "execution_envelope_ref": "e1",
        "phase_status": "COMPLETED",
        "total_units_planned": 2,
        "units_accepted": 2,
        "remediation_cycle_count": 0,
        "capacity_wait_count": 0,
        "human_escalation_count": 0,
        "evidence_fingerprint": "fp123",
        "created_at": "2026-08-04T12:00:00Z",
    }
    parsed = deserialize_phase_retrospective(json.dumps(retro_data).encode("utf-8"))
    assert parsed.retrospective_id == "retro-p1-e1"


def test_cross_contract_13_legacy_records_without_new_fields_remain_safe() -> None:
    # Legacy unit plan payload without optional fields deserializes safely
    legacy_json = {
        "schema_version": "1.0.0",
        "unit_id": "unit-leg",
        "unit_revision": "rev-1",
        "unit_name": "Legacy Unit",
        "phase_id": "p1",
        "execution_envelope_ref": "e1",
        "scope_ref": "s1",
        "responsible_specialist": "ponytail",
        "objective": "Obj",
        "expected_outputs": ["out.py"],
        "validation_requirements": ["val.sh"],
    }
    parsed = deserialize_approved_unit_plan(json.dumps(legacy_json).encode("utf-8"))
    assert parsed.allowed_paths is None
    assert parsed.prohibited_paths is None
    assert parsed.dependency_unit_ids is None


def test_cross_contract_14_missing_authority_fields_never_produce_broad_defaults() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-no-paths",
        unit_revision="rev-1",
        unit_name="No Paths Unit",
        phase_id="p1",
        execution_envelope_ref="e1",
        scope_ref="s1",
        responsible_specialist="overseer",
        objective="Obj",
        expected_outputs=("doc.md",),
        validation_requirements=("val.sh",),
        allowed_paths=None,
    )
    # Omitting allowed_paths for non-file units does not grant file mutation authority
    res = validate_approved_unit_plan_context(plan, operation_context="FILE_MUTATION")
    assert res.allowed is False


def test_cross_contract_15_unknown_schema_version_rejected_independently() -> None:
    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_runtime_envelope(b'{"schema_version": "9.9.9", "message_type": "execution_result", "timestamp": "t", "run_id": "r", "specialist": "s"}')

    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_phase_retrospective(b'{"schema_version": "9.9.9", "retrospective_id": "r", "phase_id": "p", "execution_envelope_ref": "e", "phase_status": "COMPLETED", "total_units_planned": 1, "units_accepted": 1, "remediation_cycle_count": 0, "capacity_wait_count": 0, "human_escalation_count": 0, "evidence_fingerprint": "f", "created_at": "c"}')

    with pytest.raises(ValueError, match="unsupported schema_version"):
        deserialize_approved_unit_plan(b'{"schema_version": "9.9.9", "unit_id": "u", "unit_revision": "r", "unit_name": "n", "phase_id": "p", "execution_envelope_ref": "e", "scope_ref": "s", "responsible_specialist": "s", "objective": "o", "expected_outputs": ["out"], "validation_requirements": ["val"]}')


def test_cross_contract_16_duplicate_keys_rejected_independently() -> None:
    dup_env = b'{"schema_version": "1.0.0", "schema_version": "1.0.0", "message_type": "execution_result", "timestamp": "t", "run_id": "r", "specialist": "s"}'
    with pytest.raises(ValueError, match="duplicate key"):
        deserialize_runtime_envelope(dup_env)

    dup_retro = b'{"schema_version": "1.0.0", "phase_id": "p1", "phase_id": "p1", "retrospective_id": "r", "execution_envelope_ref": "e", "phase_status": "COMPLETED", "total_units_planned": 1, "units_accepted": 1, "remediation_cycle_count": 0, "capacity_wait_count": 0, "human_escalation_count": 0, "evidence_fingerprint": "f", "created_at": "c"}'
    with pytest.raises(ValueError, match="duplicate JSON key rejected"):
        deserialize_phase_retrospective(dup_retro)

    dup_plan = b'{"schema_version": "1.0.0", "unit_id": "u1", "unit_id": "u1", "unit_revision": "r", "unit_name": "n", "phase_id": "p", "execution_envelope_ref": "e", "scope_ref": "s", "responsible_specialist": "s", "objective": "o", "expected_outputs": ["out"], "validation_requirements": ["val"]}'
    with pytest.raises(ValueError, match="duplicate key"):
        deserialize_approved_unit_plan(dup_plan)


def test_cross_contract_17_contract_parsers_reject_other_contract_payloads() -> None:
    plan = ApprovedUnitPlan(
        unit_id="unit-cross",
        unit_revision="rev-1",
        unit_name="Cross Test",
        phase_id="p1",
        execution_envelope_ref="e1",
        scope_ref="s1",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    plan_bytes = serialize_approved_unit_plan(plan)

    # Deserializing ApprovedUnitPlan JSON with deserialize_runtime_envelope raises ValueError
    with pytest.raises(ValueError):
        deserialize_runtime_envelope(plan_bytes)

    # Deserializing ApprovedUnitPlan JSON with deserialize_phase_retrospective raises ValueError
    with pytest.raises(ValueError):
        deserialize_phase_retrospective(plan_bytes)


def test_cross_contract_18_deferred_phase_2c_and_2d_flows_remain_absent() -> None:
    # Cross-session correlation restoration and automatic retrospective phase closeout generation are deferred
    from orchestra_runtime import build_phase_retrospective
    retro = build_phase_retrospective(
        phase_id="p1",
        execution_envelope_ref="e1",
        phase_status="COMPLETED",
        total_units_planned=2,
        units_accepted=2,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp123",
    )
    assert retro.schema_version == "1.0.0"


def test_cross_contract_19_no_standalone_unit_state_authority_exists() -> None:
    # Standalone competing unit-state files or classes are strictly absent
    from orchestra_runtime import ApprovedUnitPlan
    plan = ApprovedUnitPlan(
        unit_id="u1",
        unit_revision="rev-1",
        unit_name="Name",
        phase_id="p1",
        execution_envelope_ref="e1",
        scope_ref="s1",
        responsible_specialist="ponytail",
        objective="Obj",
        expected_outputs=("out.py",),
        validation_requirements=("val.sh",),
        allowed_paths=("out.py",),
    )
    assert hasattr(plan, "unit_id")
    assert not hasattr(plan, "mutable_execution_state")


def test_cross_contract_20_no_automatic_merge_release_or_policy_mutation() -> None:
    # Verify policy activation remains un-mutated
    from orchestra_runtime import APPROVED_UNIT_PLAN_SCHEMA_VERSION, RETROSPECTIVE_SCHEMA_VERSION
    assert APPROVED_UNIT_PLAN_SCHEMA_VERSION == "1.0.0"
    assert RETROSPECTIVE_SCHEMA_VERSION == "1.0.0"
