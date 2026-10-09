# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_contract() -> dict:
    return json.loads(
        (ROOT / "machine/governance/protected-governance-escalation.v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_protected_governance_escalation_contract_is_fail_closed() -> None:
    contract = _load_contract()

    assert contract["same_run_policy_change_forbidden"] is True
    assert contract["human_review_required"] is True
    assert contract["new_execution_context_required"] is True
    assert contract["candidate_freeze_required"] is True
    assert contract["ordinary_auto_remediation_allowed"] is False
    assert contract["originating_run_may_resume_after_human_decision"] is False
    assert "FAIL_POLICY_SELF_MODIFICATION" in contract["prai_failure_triggers"]
    assert "WHITELIST_MUTATION_REQUIRED" in contract["additional_triggers"]
    assert contract["required_default_reviewers"] == ["ARBITER", "OVERSEER", "CLOCKWORK"]
    assert contract["exception_properties"]["same_run_creation_and_consumption_forbidden"] is True
    assert contract["exception_properties"]["non_transitive"] is True


def test_protected_governance_escalation_requires_human_decision_vocabulary() -> None:
    contract = _load_contract()

    assert contract["ai_recommendations"] == [
        "DENY",
        "REQUEST_MORE_EVIDENCE",
        "RECOMMEND_BOUNDED_EXCEPTION",
        "RECOMMEND_POLICY_AMENDMENT",
    ]
    assert contract["human_decisions"] == [
        "DENY",
        "REQUEST_MORE_EVIDENCE",
        "APPROVE_BOUNDED_EXCEPTION",
        "APPROVE_POLICY_AMENDMENT",
    ]


def test_whitelist_authority_is_human_only_and_non_delegable() -> None:
    contract = _load_contract()
    authority = contract["whitelist_authority"]

    assert authority["authority_class"] == "HUMAN_POLICY"
    assert authority["authority_origin_record"] == (
        "Padayon:c8798f848df0830d04d5f25b4f0680d288768839"
    )
    assert authority["human_approval_required"] is True
    assert authority["human_decision_record_required"] is True
    assert authority["ai_recommendation_allowed"] is True
    assert authority["ai_approval_allowed"] is False
    assert authority["ai_mutation_without_human_decision_allowed"] is False
    assert authority["full_autonomous_override_allowed"] is False
    assert authority["fresh_execution_context_required"] is True
    assert authority["same_run_creation_and_consumption_forbidden"] is True
    assert authority["precedent_is_authority"] is False
    assert authority["protected_mutations"] == [
        "CREATE_WHITELIST",
        "ADD_WHITELIST_ENTRY",
        "REMOVE_WHITELIST_ENTRY",
        "EXPAND_WHITELIST_MATCH",
        "NARROW_WHITELIST_MATCH",
        "REINTERPRET_WHITELIST_SCOPE",
        "CHANGE_WHITELIST_PRECEDENCE",
        "CHANGE_WHITELIST_TRANSITIVITY",
        "CHANGE_WHITELIST_EXPIRATION",
        "CHANGE_WHITELIST_CONSUMPTION",
        "CHANGE_WHITELIST_REASON_CODE",
        "DELETE_OR_DISABLE_WHITELIST",
    ]
