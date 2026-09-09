# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_protected_governance_escalation_contract_is_fail_closed() -> None:
    contract = json.loads(
        (ROOT / "machine/governance/protected-governance-escalation.v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["same_run_policy_change_forbidden"] is True
    assert contract["human_review_required"] is True
    assert contract["new_execution_context_required"] is True
    assert contract["candidate_freeze_required"] is True
    assert contract["ordinary_auto_remediation_allowed"] is False
    assert contract["originating_run_may_resume_after_human_decision"] is False
    assert "FAIL_POLICY_SELF_MODIFICATION" in contract["prai_failure_triggers"]
    assert contract["required_default_reviewers"] == ["ARBITER", "OVERSEER", "CLOCKWORK"]
    assert contract["exception_properties"]["same_run_creation_and_consumption_forbidden"] is True
    assert contract["exception_properties"]["non_transitive"] is True


def test_protected_governance_escalation_requires_human_decision_vocabulary() -> None:
    contract = json.loads(
        (ROOT / "machine/governance/protected-governance-escalation.v1.json").read_text(
            encoding="utf-8"
        )
    )

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
