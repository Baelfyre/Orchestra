# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Schema-level historical identity cases. No human decision or clearance is authenticated."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "machine/schemas/protected-governance-escalation.v1.schema.json"
CONTRACT = ROOT / "machine/governance/protected-governance-escalation.v1.json"


def synthetic_packet():
    return {
        "schema_version": "orchestra.protected-governance-escalation.v1",
        "record_type": "GovernanceEscalationPacket",
        "escalation_id": "synthetic-1003",
        "originating_run_id": None,
        "originating_run_identity_status": "UNAVAILABLE_DOCUMENTED",
        "originating_run_identity_evidence_refs": ["synthetic:run-identity-evidence-not-authenticated"],
        "originating_run_missing_identity_decision_ref": "synthetic:missing-identity-decision-not-authenticated",
        "repository": "Baelfyre/Orchestra",
        "base_sha": "a" * 40,
        "candidate_sha": "b" * 40,
        "tree_sha": "c" * 40,
        "work_item_ref": "synthetic:1003",
        "phase_id": "v1.12.0",
        "trigger_code": "POLICY_CHOICE_REQUIRED",
        "protected_rule": "human review of applicable IP",
        "affected_paths": ["docs/governance/RELEASE_GATES.md"],
        "failing_evidence_refs": ["synthetic:governor-blocked"],
        "proposed_governance_change": "review one-time exception",
        "prime_directive_analysis": "preserve evidence and protected decision",
        "alternatives_considered": ["retain block", "seek review"],
        "risk_if_unchanged": "technical release delayed",
        "risk_if_changed": "rights dispute remains unresolved",
        "required_reviewers": ["ARBITER", "CLOCKWORK", "GOVERNOR"],
        "reviewer_findings": [],
        "dissenting_findings": ["identity not authenticated"],
        "ai_recommendation": "REQUEST_MORE_EVIDENCE",
        "human_review_required": True,
        "candidate_frozen": True,
        "same_run_mutation_forbidden": True,
        "next_allowed_action": "HUMAN_GOVERNANCE_REVIEW",
        "generated_at": "2026-11-09T02:02:22Z",
    }


def errors(packet):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(packet))


def test_unavailable_identity_preserves_required_structural_references():
    packet = synthetic_packet()
    assert packet["originating_run_id"] is None
    assert "originating_run_identity_governance_qualification" not in packet
    assert packet["originating_run_identity_evidence_refs"]
    assert packet["originating_run_missing_identity_decision_ref"].endswith("not-authenticated")
    assert errors(packet) == []


def synthetic_verified_packet():
    packet = synthetic_packet()
    packet["originating_run_id"] = "synthetic-run-id-not-authenticated"
    packet["originating_run_identity_status"] = "VERIFIED"
    packet["originating_run_identity_evidence_refs"] = ["synthetic:caller-reference-not-authenticated"]
    packet["originating_run_identity_governance_qualification"] = "UNQUALIFIED"
    packet.pop("originating_run_missing_identity_decision_ref")
    return packet


def test_verified_identity_claim_is_structural_and_unqualified():
    packet = synthetic_verified_packet()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert errors(packet) == []
    assert packet["originating_run_identity_governance_qualification"] == "UNQUALIFIED"
    assert contract["originating_run_identity_provenance"] == {
        "verified_governance_qualification": "UNQUALIFIED",
        "run_id_and_reference_values_are_structural_claims_only": True,
        "trusted_source_authenticator_available": False,
        "authority_effect": "NONE",
    }


def test_verified_run_id_and_refs_cannot_substitute_for_human_decision_record():
    packet = synthetic_verified_packet()
    assert errors(packet) == []
    assert packet["human_review_required"] is True
    assert packet["next_allowed_action"] == "HUMAN_GOVERNANCE_REVIEW"

    attempted_decision = copy.deepcopy(packet)
    attempted_decision["record_type"] = "HumanGovernanceDecisionRecord"
    attempted_decision["decision"] = "APPROVE_BOUNDED_EXCEPTION"
    attempted_decision["human_authority_source"] = "synthetic:not-authenticated"
    assert errors(attempted_decision)


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(originating_run_id="UNVERIFIED_NOT_AN_AUTHENTIC_RUN_ID"),
    lambda p: p.pop("originating_run_identity_status"),
    lambda p: p.pop("originating_run_identity_evidence_refs"),
    lambda p: p.pop("originating_run_missing_identity_decision_ref"),
    lambda p: p.update(originating_run_identity_status="VERIFIED"),
    lambda p: p.update(originating_run_id="synthetic-run-id-not-authenticated"),
    lambda p: p.update(originating_run_id="synthetic-run-id-not-authenticated", originating_run_identity_status="UNAVAILABLE_DOCUMENTED"),
    lambda p: p.update(originating_run_identity_evidence_refs=[]),
    lambda p: p.update(generated_at="not-an-iso-timestamp"),
])
def test_unavailable_identity_fails_closed_on_missing_or_conflicting_fields(mutate):
    packet = copy.deepcopy(synthetic_packet())
    mutate(packet)
    assert errors(packet)


def test_human_governance_record_cannot_claim_approval_from_draft_value():
    packet = synthetic_packet()
    packet["record_type"] = "HumanGovernanceDecisionRecord"
    packet["decision"] = "PENDING_HUMAN_DECISION"
    assert errors(packet)


@pytest.mark.parametrize("mutate", [
    lambda p: p.pop("originating_run_identity_governance_qualification"),
    lambda p: p.update(originating_run_identity_governance_qualification="QUALIFIED"),
    lambda p: p.pop("originating_run_identity_evidence_refs"),
    lambda p: p.update(originating_run_identity_evidence_refs=[]),
    lambda p: p.update(originating_run_identity_status="UNAVAILABLE_DOCUMENTED"),
    lambda p: p.update(originating_run_missing_identity_decision_ref="synthetic:not-applicable"),
])
def test_verified_identity_fails_closed_on_missing_or_conflicting_fields(mutate):
    packet = synthetic_verified_packet()
    mutate(packet)
    assert errors(packet)
