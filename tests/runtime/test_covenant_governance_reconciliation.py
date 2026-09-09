# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import pytest

from orchestra_runtime.domain.governance.covenant import (
    CovenantBasis,
    GovernanceJudgment,
    ReconciliationProposal,
    evaluate_covenant,
)


BASIS = CovenantBasis(
    project_ref="PROJECT_CONTEXT.md",
    prime_directive_ref="docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
    project_goal_refs=("goal:reliable-governed-orchestration",),
    critical_flows=("governed-change-to-verified-transition",),
    system_invariants=("authority-never-expands-silently",),
    prohibited_outcomes=("unreviewed-protected-transition",),
)


def judgment(
    reviewer: str,
    *,
    decision: str = "APPROVED",
    prime: str = "ALIGNED",
    goal: str = "ALIGNED",
    human: bool = False,
):
    return GovernanceJudgment(
        reviewer=reviewer,
        decision=decision,
        prime_directive_alignment=prime,
        project_goal_alignment=goal,
        constraints=(f"{reviewer.lower()}-constraint",),
        evidence_refs=(f"evidence:{reviewer.lower()}",),
        human_review_required=human,
    )


def test_prime_directive_conflict_cannot_be_reconciled_by_consensus():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD", prime="CONFLICT"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        reconciliation=ReconciliationProposal(
            "both reviewers prefer delivery",
            True,
            True,
            True,
            True,
            ("evidence:delivery",),
        ),
    )
    assert result.disposition == "BLOCKED"
    assert result.human_review_required is True
    assert result.reason_codes == ("PRIME_DIRECTIVE_CONFLICT",)


def test_steward_approval_cannot_override_governor_block():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR", decision="BLOCKED"),
        assurance_result="PASS",
    )
    assert result.disposition == "BLOCKED"


def test_governor_approval_cannot_override_steward_revision():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD", decision="REVISION_REQUIRED"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
    )
    assert result.disposition == "REVISION_REQUIRED"


def test_missing_assurance_fails_closed():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="MISSING",
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"


def test_prai_pass_does_not_override_system_contradiction():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        system_contradictions=("last-admin invariant is raceable",),
    )
    assert result.disposition == "REVISION_REQUIRED"
    assert result.reason_codes == ("SYSTEM_CONTRADICTION",)


def test_audit_atomicity_escape_is_revision_required_even_with_green_assurance():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        system_contradictions=(
            "privilege mutation can commit before mandatory audit recording",
        ),
    )
    assert result.disposition == "REVISION_REQUIRED"


def test_project_goal_misalignment_requires_revision():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD", goal="CONFLICT"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
    )
    assert result.disposition == "REVISION_REQUIRED"


def test_human_governance_boundary_escalates():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR", human=True),
        assurance_result="PASS",
    )
    assert result.disposition == "ESCALATE_HUMAN"
    assert result.human_review_required is True


def test_unresolved_cross_governance_conflict_requires_revision():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
    )
    assert result.disposition == "REVISION_REQUIRED"


def test_verified_narrow_reconciliation_preserving_both_is_accepted():
    proposal = ReconciliationProposal(
        summary="retain minimal durable audit identifiers and exclude response echo",
        preserves_prime_directive=True,
        preserves_project_goals=True,
        steward_accepts=True,
        governor_accepts=True,
        evidence_refs=("evidence:minimized-durable-audit-design",),
    )
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
        reconciliation=proposal,
    )
    assert result.disposition == "RECONCILED_WITH_CONSTRAINTS"


def test_reconciliation_that_sacrifices_project_goal_is_rejected():
    proposal = ReconciliationProposal(
        summary="drop auditability to minimize data",
        preserves_prime_directive=True,
        preserves_project_goals=False,
        steward_accepts=True,
        governor_accepts=True,
        evidence_refs=("evidence:proposal",),
    )
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
        cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
        reconciliation=proposal,
    )
    assert result.disposition == "REVISION_REQUIRED"


def test_fully_coherent_candidate_passes_without_creating_authority():
    result = evaluate_covenant(
        BASIS,
        judgment("STEWARD"),
        judgment("GOVERNOR"),
        assurance_result="PASS",
    )
    assert result.disposition == "PASS"
    assert result.human_review_required is False
    assert "PROJECT_CONTEXT.md" in result.evidence_refs
    assert "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md" in result.evidence_refs
    assert "goal:reliable-governed-orchestration" in result.evidence_refs


def test_material_covenant_basis_requires_flows_and_invariants():
    with pytest.raises(ValueError):
        CovenantBasis(
            project_ref="PROJECT_CONTEXT.md",
            prime_directive_ref="docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
            project_goal_refs=("goal:a",),
            critical_flows=(),
            system_invariants=("invariant:a",),
        )
    with pytest.raises(ValueError):
        CovenantBasis(
            project_ref="PROJECT_CONTEXT.md",
            prime_directive_ref="docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
            project_goal_refs=("goal:a",),
            critical_flows=("flow:a",),
            system_invariants=(),
        )


def test_invalid_reviewer_is_rejected():
    with pytest.raises(ValueError):
        judgment("ARBITER")
