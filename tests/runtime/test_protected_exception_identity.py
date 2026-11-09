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


def synthetic_packet():
    return {
        "schema_version": "orchestra.protected-governance-escalation.v1",
        "record_type": "GovernanceEscalationPacket",
        "escalation_id": "synthetic-1003",
        "originating_run_id": None,
        "originating_run_identity_status": "UNAVAILABLE_DOCUMENTED",
        "originating_run_identity_evidence_refs": [
            "https://github.com/Baelfyre/Orchestra/issues/991"
        ],
        "originating_run_missing_identity_decision_ref": "synthetic:human-review-not-authenticated",
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


def test_documented_missing_identity_has_explicit_human_review_reference():
    assert errors(synthetic_packet()) == []


def test_valid_existing_run_id_remains_supported():
    packet = synthetic_packet()
    packet["originating_run_id"] = "run-12345"
    packet["originating_run_identity_status"] = "VERIFIED"
    assert errors(packet) == []


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(originating_run_id="UNVERIFIED_NOT_AN_AUTHENTIC_RUN_ID"),
    lambda p: p.pop("originating_run_identity_status"),
    lambda p: p.pop("originating_run_identity_evidence_refs"),
    lambda p: p.pop("originating_run_missing_identity_decision_ref"),
    lambda p: p.update(originating_run_identity_status="VERIFIED"),
    lambda p: p.update(originating_run_identity_evidence_refs=[]),
    lambda p: p.update(generated_at="not-an-iso-timestamp"),
])
def test_missing_identity_never_passes_without_schema_evidence(mutate):
    packet = copy.deepcopy(synthetic_packet())
    mutate(packet)
    assert errors(packet)


def test_human_governance_record_cannot_claim_approval_from_draft_value():
    packet = synthetic_packet()
    packet["record_type"] = "HumanGovernanceDecisionRecord"
    packet["decision"] = "PENDING_HUMAN_DECISION"
    assert errors(packet)
