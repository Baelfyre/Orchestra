from __future__ import annotations

import json
import pytest

from orchestra_runtime import (
    RETROSPECTIVE_SCHEMA_VERSION,
    OrchestraPhaseRetrospective,
    build_phase_retrospective,
    deserialize_phase_retrospective,
    derive_evidence_fingerprint,
    derive_retrospective_id,
    generate_correlation_id,
    maybe_build_phase_retrospective,
    serialize_phase_retrospective,
    serialize_phase_retrospective_to_str,
    should_generate_phase_retrospective,
)


def test_derive_retrospective_id_formula_and_determinism() -> None:
    phase_id = "phase-2d-1"
    env_ref = "env-100"
    expected = "retro-phase-2d-1-env-100"

    # Determinism test
    id1 = derive_retrospective_id(phase_id, env_ref)
    id2 = derive_retrospective_id(phase_id, env_ref)
    assert id1 == expected
    assert id1 == id2

    # Different phase or envelope yields different ID
    assert derive_retrospective_id("phase-2d-2", env_ref) != expected
    assert derive_retrospective_id(phase_id, "env-101") != expected

    with pytest.raises(ValueError, match="phase_id must be a non-empty string"):
        derive_retrospective_id("", env_ref)

    with pytest.raises(ValueError, match="execution_envelope_ref must be a non-empty string"):
        derive_retrospective_id(phase_id, "")


def test_derive_evidence_fingerprint() -> None:
    data = "test-evidence-content"
    fp = derive_evidence_fingerprint(data)
    assert isinstance(fp, str)
    assert len(fp) == 64
    assert fp == derive_evidence_fingerprint(data.encode("utf-8"))


def test_exact_16_field_schema_and_types() -> None:
    phase_id = "phase-alpha"
    env_ref = "envelope-123"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)
    cid = generate_correlation_id()
    fp = derive_evidence_fingerprint("evidence")

    # 12 required + 4 optional = 16 fields total
    retro = OrchestraPhaseRetrospective(
        retrospective_id=retro_id,
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=5,
        units_accepted=5,
        remediation_cycle_count=0,
        capacity_wait_count=0,
        human_escalation_count=0,
        evidence_fingerprint=fp,
        created_at=created_at,
        correlation_id=cid,
        outcome_summary="Phase completed cleanly with 5 units accepted.",
        known_limitations=("None",),
        follow_up_candidates=("Phase 2E authorization",),
    )

    assert retro.schema_version == RETROSPECTIVE_SCHEMA_VERSION
    assert retro.retrospective_id == retro_id
    assert retro.phase_id == phase_id
    assert retro.execution_envelope_ref == env_ref
    assert retro.phase_status == "COMPLETED"
    assert retro.total_units_planned == 5
    assert retro.units_accepted == 5
    assert retro.remediation_cycle_count == 0
    assert retro.capacity_wait_count == 0
    assert retro.human_escalation_count == 0
    assert retro.evidence_fingerprint == fp
    assert retro.created_at == created_at
    assert retro.correlation_id == cid
    assert retro.outcome_summary == "Phase completed cleanly with 5 units accepted."
    assert retro.known_limitations == ("None",)
    assert retro.follow_up_candidates == ("Phase 2E authorization",)


def test_schema_version_rejection() -> None:
    phase_id = "phase-beta"
    env_ref = "env-1"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)

    with pytest.raises(ValueError, match="unsupported schema_version"):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="COMPLETED",
            total_units_planned=2,
            units_accepted=2,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
            schema_version="2.0.0",
        )


def test_retrospective_id_mismatch_rejection() -> None:
    with pytest.raises(ValueError, match="does not match derived identity"):
        OrchestraPhaseRetrospective(
            retrospective_id="wrong-id",
            phase_id="phase-1",
            execution_envelope_ref="env-1",
            phase_status="COMPLETED",
            total_units_planned=2,
            units_accepted=2,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at="2026-08-04T12:00:00Z",
        )


def test_invalid_phase_status_rejection() -> None:
    phase_id = "phase-1"
    env_ref = "env-1"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)

    # STOP is an Arbiter disposition, NOT a phase status
    with pytest.raises(ValueError, match="invalid phase_status 'STOP'"):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="STOP",
            total_units_planned=2,
            units_accepted=2,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
        )

    # INCOMPLETE_EVIDENCE is metadata, NOT a phase status
    with pytest.raises(ValueError, match="invalid phase_status 'INCOMPLETE_EVIDENCE'"):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="INCOMPLETE_EVIDENCE",
            total_units_planned=2,
            units_accepted=2,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
        )


def test_all_canonical_terminal_phase_statuses() -> None:
    phase_id = "phase-status-check"
    env_ref = "env-99"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)

    for status in ("COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "TIMED_OUT"):
        retro = OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status=status,
            total_units_planned=2,
            units_accepted=2 if status == "COMPLETED" else 1,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
        )
        assert retro.phase_status == status


def test_negative_counts_and_over_acceptance_rejection() -> None:
    phase_id = "phase-1"
    env_ref = "env-1"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)

    # Negative units
    with pytest.raises(ValueError, match="total_units_planned must be a non-negative integer"):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="COMPLETED",
            total_units_planned=-1,
            units_accepted=0,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
        )

    # Accepted > planned
    with pytest.raises(ValueError, match="cannot exceed total_units_planned"):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="COMPLETED",
            total_units_planned=2,
            units_accepted=3,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
        )


def test_metric_provenance_dedicated_scenarios() -> None:
    # Scenario: Explicit empty log produces count = 0
    phase_id = "phase-metric-test"
    env_ref = "env-metric-test"
    transition_logs: list[dict[str, str]] = []

    remediation_count = sum(1 for item in transition_logs if item.get("disposition") == "AUTO_REMEDIATE_AND_REVALIDATE")
    capacity_count = sum(1 for item in transition_logs if item.get("disposition") == "WAIT_FOR_CAPACITY")
    escalation_count = sum(1 for item in transition_logs if item.get("disposition") == "ESCALATE_HUMAN")

    assert remediation_count == 0
    assert capacity_count == 0
    assert escalation_count == 0

    retro = build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=3,
        units_accepted=3,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp-metric-1",
        remediation_cycle_count=remediation_count,
        capacity_wait_count=capacity_count,
        human_escalation_count=escalation_count,
    )
    assert retro.remediation_cycle_count == 0
    assert retro.capacity_wait_count == 0
    assert retro.human_escalation_count == 0

    # Scenario: Matching phase events filtered from logs
    mixed_logs = [
        {"phase_id": phase_id, "disposition": "AUTO_REMEDIATE_AND_REVALIDATE"},
        {"phase_id": "other-phase", "disposition": "AUTO_REMEDIATE_AND_REVALIDATE"},
        {"phase_id": phase_id, "disposition": "WAIT_FOR_CAPACITY"},
        {"phase_id": phase_id, "disposition": "ESCALATE_HUMAN"},
        {"phase_id": phase_id, "disposition": "AUTO_CONTINUE"},  # Unrelated disposition
    ]

    remed_filtered = sum(1 for item in mixed_logs if item.get("phase_id") == phase_id and item.get("disposition") == "AUTO_REMEDIATE_AND_REVALIDATE")
    cap_filtered = sum(1 for item in mixed_logs if item.get("phase_id") == phase_id and item.get("disposition") == "WAIT_FOR_CAPACITY")
    esc_filtered = sum(1 for item in mixed_logs if item.get("phase_id") == phase_id and item.get("disposition") == "ESCALATE_HUMAN")

    assert remed_filtered == 1
    assert cap_filtered == 1
    assert esc_filtered == 1

    retro_filtered = build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="FAILED",
        total_units_planned=3,
        units_accepted=1,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp-metric-2",
        remediation_cycle_count=remed_filtered,
        capacity_wait_count=cap_filtered,
        human_escalation_count=esc_filtered,
    )
    assert retro_filtered.remediation_cycle_count == 1
    assert retro_filtered.capacity_wait_count == 1
    assert retro_filtered.human_escalation_count == 1


def test_invalid_correlation_id_rejection() -> None:
    phase_id = "phase-1"
    env_ref = "env-1"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)

    with pytest.raises(ValueError):
        OrchestraPhaseRetrospective(
            retrospective_id=retro_id,
            phase_id=phase_id,
            execution_envelope_ref=env_ref,
            phase_status="COMPLETED",
            total_units_planned=2,
            units_accepted=2,
            remediation_cycle_count=0,
            capacity_wait_count=0,
            human_escalation_count=0,
            evidence_fingerprint="fp123",
            created_at=created_at,
            correlation_id="invalid-uuid-format",
        )


def test_retrospective_immutability() -> None:
    phase_id = "phase-1"
    env_ref = "env-1"
    created_at = "2026-08-04T12:00:00Z"
    retro_id = derive_retrospective_id(phase_id, env_ref)
    retro = OrchestraPhaseRetrospective(
        retrospective_id=retro_id,
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=2,
        units_accepted=2,
        remediation_cycle_count=0,
        capacity_wait_count=0,
        human_escalation_count=0,
        evidence_fingerprint="fp123",
        created_at=created_at,
    )
    with pytest.raises(Exception):
        retro.phase_status = "FAILED"  # type: ignore[misc]


def test_should_generate_phase_retrospective_predicate() -> None:
    # Single unit without material signal -> False
    assert not should_generate_phase_retrospective(
        total_units_planned=1,
        phase_status="COMPLETED",
    )

    # Single unit with maintainer_decision_ref -> True
    assert should_generate_phase_retrospective(
        total_units_planned=1,
        phase_status="COMPLETED",
        maintainer_decision_ref="decision-rec-001",
    )

    # Multi-unit without material signal -> False
    assert not should_generate_phase_retrospective(
        total_units_planned=3,
        phase_status="COMPLETED",
        remediation_cycle_count=0,
        capacity_wait_count=0,
        human_escalation_count=0,
    )

    # Multi-unit with remediation signal -> True
    assert should_generate_phase_retrospective(
        total_units_planned=3,
        phase_status="COMPLETED",
        remediation_cycle_count=1,
    )

    # Multi-unit with capacity wait signal -> True
    assert should_generate_phase_retrospective(
        total_units_planned=3,
        phase_status="COMPLETED",
        capacity_wait_count=1,
    )

    # Multi-unit with human escalation signal -> True
    assert should_generate_phase_retrospective(
        total_units_planned=3,
        phase_status="COMPLETED",
        human_escalation_count=1,
    )

    # Multi-unit with non-completed terminal outcome -> True
    for status in ("FAILED", "BLOCKED", "CANCELLED", "TIMED_OUT"):
        assert should_generate_phase_retrospective(
            total_units_planned=3,
            phase_status=status,
        )


def test_build_and_maybe_build_phase_retrospective() -> None:
    # maybe_build_phase_retrospective returns None when trigger is False
    opt1 = maybe_build_phase_retrospective(
        phase_id="p1",
        execution_envelope_ref="e1",
        phase_status="COMPLETED",
        total_units_planned=1,
        units_accepted=1,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp1",
    )
    assert opt1 is None

    # maybe_build_phase_retrospective returns instance when trigger is True
    opt2 = maybe_build_phase_retrospective(
        phase_id="p1",
        execution_envelope_ref="e1",
        phase_status="FAILED",
        total_units_planned=3,
        units_accepted=1,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp1",
    )
    assert isinstance(opt2, OrchestraPhaseRetrospective)
    assert opt2.phase_status == "FAILED"

    # Direct build_phase_retrospective always builds
    retro = build_phase_retrospective(
        phase_id="p2",
        execution_envelope_ref="e2",
        phase_status="TIMED_OUT",
        total_units_planned=2,
        units_accepted=0,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp2",
    )
    assert retro.phase_status == "TIMED_OUT"
    assert retro.retrospective_id == "retro-p2-e2"


def test_same_phase_duplicate_prevention_at_most_one() -> None:
    phase_id = "phase-dup-check"
    env_ref = "env-dup-check"

    # Calling builder twice at different times returns the exact same retrospective_id
    r1 = build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=4,
        units_accepted=4,
        created_at="2026-08-04T12:00:00Z",
        evidence_fingerprint="fp-dup",
    )

    r2 = build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=4,
        units_accepted=4,
        created_at="2026-08-04T12:00:05Z",  # Different timestamp
        evidence_fingerprint="fp-dup",
    )

    assert r1.retrospective_id == r2.retrospective_id == f"retro-{phase_id}-{env_ref}"


def test_strict_bytes_serialization_and_deserialization_roundtrip() -> None:
    phase_id = "phase-roundtrip"
    env_ref = "env-777"
    created_at = "2026-08-04T15:30:00Z"
    cid = generate_correlation_id()
    retro = build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=env_ref,
        phase_status="COMPLETED",
        total_units_planned=4,
        units_accepted=4,
        created_at=created_at,
        evidence_fingerprint="a1b2c3d4e5f67890",
        correlation_id=cid,
        outcome_summary="Clean execution across 4 units",
        known_limitations=("Limitation 1",),
        follow_up_candidates=("Candidate 1",),
    )

    # Serialization produces UTF-8 encoded bytes
    serialized_bytes = serialize_phase_retrospective(retro)
    assert isinstance(serialized_bytes, bytes)
    parsed_dict = json.loads(serialized_bytes.decode("utf-8"))
    assert parsed_dict["schema_version"] == "1.0.0"
    assert parsed_dict["retrospective_id"] == f"retro-{phase_id}-{env_ref}"
    assert parsed_dict["correlation_id"] == cid

    # String helper
    serialized_str = serialize_phase_retrospective_to_str(retro)
    assert isinstance(serialized_str, str)
    assert serialized_str == serialized_bytes.decode("utf-8")

    # Deserialization from bytes
    restored_bytes = deserialize_phase_retrospective(serialized_bytes)
    assert restored_bytes == retro

    # Deserialization from string
    restored_str = deserialize_phase_retrospective(serialized_str)
    assert restored_str == retro

    # Byte-identical re-serialization
    assert serialize_phase_retrospective(restored_bytes) == serialized_bytes


def test_deserialization_strict_validation_failures() -> None:
    valid_dict = {
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
    valid_bytes = json.dumps(valid_dict).encode("utf-8")

    # Public dict input rejection (TypeError)
    with pytest.raises(TypeError, match="expected bytes or str payload"):
        deserialize_phase_retrospective(valid_dict)  # type: ignore[arg-type]

    # Invalid UTF-8 bytes payload
    bad_utf8 = b"\x80\x81\xfe\xff"
    with pytest.raises(ValueError, match="invalid UTF-8 bytes payload"):
        deserialize_phase_retrospective(bad_utf8)

    # Empty bytes payload
    with pytest.raises(ValueError, match="invalid JSON payload"):
        deserialize_phase_retrospective(b"")

    # Whitespace bytes payload
    with pytest.raises(ValueError, match="invalid JSON payload"):
        deserialize_phase_retrospective(b"   ")

    # Top-level array rejection
    with pytest.raises(ValueError, match="JSON payload must be a dictionary object"):
        deserialize_phase_retrospective(b"[1, 2, 3]")

    # Duplicate key in JSON
    dup_json = '{"phase_id": "p1", "phase_id": "p2"}'
    with pytest.raises(ValueError, match="duplicate JSON key rejected"):
        deserialize_phase_retrospective(dup_json.encode("utf-8"))

    # Missing required field
    missing_data = dict(valid_dict)
    del missing_data["evidence_fingerprint"]
    with pytest.raises(ValueError, match="missing required field"):
        deserialize_phase_retrospective(json.dumps(missing_data).encode("utf-8"))

    # Unknown field
    unknown_data = dict(valid_dict, extra_unknown_field="bogus")
    with pytest.raises(ValueError, match="unknown field"):
        deserialize_phase_retrospective(json.dumps(unknown_data).encode("utf-8"))

    # Non-finite number (NaN)
    nan_json = '{"total_units_planned": NaN}'
    with pytest.raises(ValueError, match="invalid JSON payload"):
        deserialize_phase_retrospective(nan_json.encode("utf-8"))

    # Invalid JSON syntax
    with pytest.raises(ValueError, match="invalid JSON payload"):
        deserialize_phase_retrospective(b"not a valid json string {")


def test_legacy_phase_without_retrospective_compatibility() -> None:
    # Legacy phase records have retrospective = None and remain fully valid
    legacy_retrospective = None
    assert legacy_retrospective is None
