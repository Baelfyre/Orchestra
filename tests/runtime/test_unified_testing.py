from __future__ import annotations

from copy import deepcopy

import pytest

from orchestra_runtime.unified_testing import (
    SCHEMA_VERSION,
    STAGE_IDS,
    STAGE_NAMES,
    STAGE_OWNERS,
    aggregate_packet,
    validate_packet,
)


SHA = "a" * 40


def _packet(*, required: set[str] | None = None, release_intent: str = "NON_RELEASE") -> dict:
    required = required or {"T0", "T1", "T2", "T3", "T8", "T9"}
    stages = []
    evidence = []
    for stage_id in STAGE_IDS:
        applicable = stage_id in required
        stages.append(
            {
                "stage_id": stage_id,
                "name": STAGE_NAMES[stage_id],
                "applicability": "REQUIRED" if applicable else "NOT_APPLICABLE",
                "owners": list(STAGE_OWNERS[stage_id]),
                "rationale": "Required for this risk surface." if applicable else "No relevant risk surface in this fixture.",
                "evidence_requirements": [f"evidence:{stage_id.lower()}"] if applicable else [],
            }
        )
        if applicable:
            evidence.append(
                {
                    "stage_id": stage_id,
                    "revision_sha": SHA,
                    "result": "PASS",
                    "evidence_refs": [f"artifact:{stage_id.lower()}"],
                    "limitations": [],
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_id": "utm.fixture.complete",
        "subject": {"repository": "Baelfyre/Orchestra", "revision_sha": SHA},
        "release_intent": release_intent,
        "stages": stages,
        "evidence": evidence,
        "human_signoff": {"status": "NOT_REQUESTED", "decision_owner": None, "evidence_refs": []},
    }


def test_complete_packet_is_non_authorizing_readiness_evidence() -> None:
    verdict = aggregate_packet(_packet())
    assert verdict.disposition == "READINESS_EVIDENCE_COMPLETE"
    assert verdict.required_stages == ("T0", "T1", "T2", "T3", "T8", "T9")
    assert verdict.release_authorized is False
    assert verdict.merge_authorized is False
    assert verdict.deployment_authorized is False
    assert verdict.policy_activation_authorized is False


def test_missing_required_stage_waits_for_evidence() -> None:
    packet = _packet()
    packet["evidence"] = [item for item in packet["evidence"] if item["stage_id"] != "T3"]
    verdict = aggregate_packet(packet)
    assert verdict.disposition == "WAIT_FOR_EVIDENCE"
    assert verdict.missing_stages == ("T3",)


def test_pending_required_stage_waits_for_evidence() -> None:
    packet = _packet()
    item = next(item for item in packet["evidence"] if item["stage_id"] == "T2")
    item["result"] = "PENDING"
    item["evidence_refs"] = []
    verdict = aggregate_packet(packet)
    assert verdict.disposition == "WAIT_FOR_EVIDENCE"
    assert verdict.pending_stages == ("T2",)


def test_failed_required_stage_blocks() -> None:
    packet = _packet()
    item = next(item for item in packet["evidence"] if item["stage_id"] == "T1")
    item["result"] = "FAIL"
    verdict = aggregate_packet(packet)
    assert verdict.disposition == "BLOCKED"
    assert verdict.failed_stages == ("T1",)


def test_stale_evidence_fails_closed() -> None:
    packet = _packet()
    packet["evidence"][0]["revision_sha"] = "b" * 40
    with pytest.raises(ValueError, match="stale"):
        validate_packet(packet)


def test_t0_and_t9_cannot_be_not_applicable() -> None:
    for stage_id in ("T0", "T9"):
        packet = _packet()
        stage = next(item for item in packet["stages"] if item["stage_id"] == stage_id)
        stage["applicability"] = "NOT_APPLICABLE"
        stage["evidence_requirements"] = []
        packet["evidence"] = [item for item in packet["evidence"] if item["stage_id"] != stage_id]
        with pytest.raises(ValueError, match="T0 and T9"):
            validate_packet(packet)


def test_not_applicable_stage_requires_reason_and_forbids_evidence() -> None:
    packet = _packet()
    stage = next(item for item in packet["stages"] if item["stage_id"] == "T4")
    stage["rationale"] = ""
    with pytest.raises(ValueError, match="T4 requires"):
        validate_packet(packet)

    packet = _packet()
    packet["evidence"].append(
        {"stage_id": "T4", "revision_sha": SHA, "result": "PASS", "evidence_refs": ["bad"], "limitations": []}
    )
    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        validate_packet(packet)


def test_canonical_owner_mapping_is_enforced() -> None:
    packet = _packet()
    next(item for item in packet["stages"] if item["stage_id"] == "T7")["owners"] = ["overseer"]
    with pytest.raises(ValueError, match="canonical ownership"):
        validate_packet(packet)


def test_release_candidate_does_not_grant_release_authority() -> None:
    packet = _packet(release_intent="RELEASE_CANDIDATE")
    packet["human_signoff"] = {
        "status": "APPROVED",
        "decision_owner": "Human maintainer",
        "evidence_refs": ["approval:fixture"],
    }
    verdict = aggregate_packet(packet)
    assert verdict.disposition == "READINESS_EVIDENCE_COMPLETE"
    assert verdict.human_signoff_status == "APPROVED"
    assert verdict.release_authorized is False


def test_duplicate_stage_and_noncanonical_name_fail_closed() -> None:
    packet = _packet()
    packet["stages"][1] = deepcopy(packet["stages"][0])
    with pytest.raises(ValueError, match="exactly once"):
        validate_packet(packet)

    packet = _packet()
    packet["stages"][0]["name"] = "Other"
    with pytest.raises(ValueError, match="canonical stage name"):
        validate_packet(packet)
