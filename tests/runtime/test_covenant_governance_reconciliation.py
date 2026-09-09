# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import pytest

from orchestra_runtime.domain.governance.covenant import (
    CovenantBasis,
    GovernanceJudgment,
    ReconciliationProposal,
    SpecialistEvidence,
    evaluate_covenant,
)


SHA = "a" * 40
TREE = "b" * 40


def _basis(**changes: object) -> CovenantBasis:
    values: dict[str, object] = {
        "repository": "Baelfyre/Orchestra",
        "candidate_sha": SHA,
        "tree_sha": TREE,
        "basis_revision": "orchestra-covenant-basis-v1",
        "project_context_ref": "PROJECT_CONTEXT.md",
        "prime_directive_ref": "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
        "project_goal_refs": ("goal:reliable-governed-orchestration",),
        "critical_flows": ("governed-change-to-verified-transition",),
        "system_invariants": ("authority-never-expands-silently",),
        "prohibited_outcomes": ("unreviewed-protected-transition",),
        "authority_boundaries": ("arbiter-owns-transition",),
    }
    values.update(changes)
    return CovenantBasis(**values)


BASIS = _basis()


def _judgment(reviewer: str, **changes: object) -> GovernanceJudgment:
    values: dict[str, object] = {
        "reviewer": reviewer,
        "evidence_refs": (f"evidence:{reviewer.lower()}",),
    }
    values.update(changes)
    return GovernanceJudgment(**values)


def _specialist(reviewer: str, **changes: object) -> SpecialistEvidence:
    values: dict[str, object] = {
        "reviewer": reviewer,
        "result": "PASS",
        "claim_scope": "candidate-system",
        "evidence_refs": (f"evidence:{reviewer.lower()}",),
        "candidate_sha": SHA,
        "tree_sha": TREE,
    }
    values.update(changes)
    return SpecialistEvidence(**values)


def _proposal(**changes: object) -> ReconciliationProposal:
    values: dict[str, object] = {
        "summary": "retain minimum necessary durable identifiers with restricted exposure",
        "preserves_prime_directive": True,
        "preserves_project_goals": True,
        "steward_accepts": True,
        "governor_accepts": True,
        "evidence_refs": ("evidence:narrow-reconciliation",),
        "constraints": ("minimum-identifiers", "controlled-retention"),
    }
    values.update(changes)
    return ReconciliationProposal(**values)


def _evaluate(
    steward: GovernanceJudgment | None = None,
    governor: GovernanceJudgment | None = None,
    **kwargs: object,
):
    kwargs.setdefault("assurance_result", "PASS")
    kwargs.setdefault("assurance_evidence_refs", ("evidence:prai",))
    kwargs.setdefault("assurance_evidence_durable", True)
    kwargs.setdefault("assurance_evidence_retrievable", True)
    return evaluate_covenant(
        BASIS,
        steward if steward is not None else _judgment("STEWARD"),
        governor if governor is not None else _judgment("GOVERNOR"),
        **kwargs,
    )


def _scenario_results():
    return {
        "COV-01": evaluate_covenant(
            BASIS,
            _judgment("STEWARD", prime_directive_alignment="CONFLICT"),
            _judgment("GOVERNOR"),
            assurance_result="PASS",
        ),
        "COV-02": _evaluate(
            governor=_judgment("GOVERNOR", decision="BLOCKED"),
            assurance_result="PASS",
        ),
        "COV-03": _evaluate(
            steward=_judgment("STEWARD", decision="REVISION_REQUIRED"),
            assurance_result="PASS",
        ),
        "COV-04A": _evaluate(
            cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
            reconciliation=_proposal(preserves_project_goals=False),
        ),
        "COV-04B": _evaluate(
            cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
            reconciliation=_proposal(),
        ),
        "COV-05": _evaluate(
            governor=_judgment("GOVERNOR", decision="REVISION_REQUIRED"),
            cross_judgment_conflicts=("scope-vs-compliance-remediation",),
        ),
        "COV-06": _evaluate(
            governor=_judgment("GOVERNOR", decision="BLOCKED"),
            cross_judgment_conflicts=("convenience-vs-authorization",),
        ),
        "COV-07": _evaluate(assurance_result="MISSING"),
        "COV-08": _evaluate(
            assurance_result="PASS",
            system_contradictions=("concurrent demotions can leave zero administrators",),
        ),
        "COV-09": _evaluate(
            assurance_result="PASS",
            system_contradictions=("database commit can precede mandatory audit failure",),
        ),
        "COV-10": _evaluate(
            assurance_result="PASS",
            specialist_evidence=(
                _specialist("CLOCKWORK"),
                _specialist("CIPHER"),
                _specialist("CHRONICLER"),
                _specialist("OVERSEER"),
            ),
            system_contradictions=("local passes form an unsafe combined system",),
        ),
        "COV-11": _evaluate(
            assurance_result="PASS",
            assurance_evidence_refs=("sha256:unavailable-artifact",),
            assurance_evidence_durable=False,
        ),
        "COV-12": _evaluate(
            cross_judgment_conflicts=("steward-governor-initial-disagreement",),
            reconciliation=_proposal(),
        ),
        "COV-13": _evaluate(
            steward=_judgment("STEWARD", critical_flow_alignment="CONTRADICTIONS"),
        ),
        "COV-14": _evaluate(
            governor=_judgment("GOVERNOR", decision="REVISION_REQUIRED"),
        ),
        "COV-15": _evaluate(
            steward=_judgment("STEWARD", project_goal_alignment="CONFLICT"),
        ),
        "COV-16": _evaluate(
            governor=_judgment(
                "GOVERNOR",
                human_review_required=True,
                obligation_satisfaction="UNKNOWN",
            ),
        ),
        "COV-17": _evaluate(
            governor=_judgment(
                "GOVERNOR",
                decision="NOT_APPLICABLE",
                obligation_satisfaction="NOT_APPLICABLE",
            ),
        ),
        "COV-18": _evaluate(
            steward=_judgment("STEWARD", prime_directive_alignment="UNKNOWN"),
        ),
    }


@pytest.mark.parametrize(
    ("scenario", "expected"),
    (
        ("COV-01", "BLOCKED"),
        ("COV-02", "BLOCKED"),
        ("COV-03", "REVISION_REQUIRED"),
        ("COV-04A", "REVISION_REQUIRED"),
        ("COV-04B", "RECONCILED_WITH_CONSTRAINTS"),
        ("COV-05", "REVISION_REQUIRED"),
        ("COV-06", "BLOCKED"),
        ("COV-07", "WAIT_FOR_EVIDENCE"),
        ("COV-08", "REVISION_REQUIRED"),
        ("COV-09", "REVISION_REQUIRED"),
        ("COV-10", "REVISION_REQUIRED"),
        ("COV-11", "WAIT_FOR_EVIDENCE"),
        ("COV-12", "RECONCILED_WITH_CONSTRAINTS"),
        ("COV-13", "REVISION_REQUIRED"),
        ("COV-14", "REVISION_REQUIRED"),
        ("COV-15", "REVISION_REQUIRED"),
        ("COV-16", "ESCALATE_HUMAN"),
        ("COV-17", "PASS"),
        ("COV-18", "WAIT_FOR_EVIDENCE"),
    ),
    ids=lambda value: value if value.startswith("COV-") else value,
)
def test_required_covenant_scenarios(scenario: str, expected: str) -> None:
    result = _scenario_results()[scenario]
    assert result.disposition == expected


def test_prime_directive_conflict_is_blocked_and_requires_human_review() -> None:
    result = _scenario_results()["COV-01"]
    assert result.reason_codes == ("PRIME_DIRECTIVE_CONFLICT",)
    assert result.human_review_required is True


def test_system_contradiction_is_stronger_than_prai_pass() -> None:
    for scenario in ("COV-08", "COV-09", "COV-10"):
        result = _scenario_results()[scenario]
        assert result.disposition == "REVISION_REQUIRED"
        assert result.reason_codes == ("SYSTEM_CONTRADICTION",)


def test_cross_specialist_contradiction_is_revision_required() -> None:
    result = _evaluate(
        assurance_result="PASS",
        cross_specialist_contradictions=("specialist claims cannot compose",),
    )
    assert result.disposition == "REVISION_REQUIRED"
    assert result.reason_codes == ("SYSTEM_CONTRADICTION",)


def test_safe_reconciliation_carries_constraints_and_evidence() -> None:
    result = _scenario_results()["COV-04B"]
    assert result.constraints == ("minimum-identifiers", "controlled-retention")
    assert "evidence:narrow-reconciliation" in result.evidence_refs


def test_covenant_result_is_bound_to_current_candidate_and_tree() -> None:
    stale_candidate = _evaluate(
        current_candidate_sha="c" * 40,
        current_tree_sha=TREE,
    )
    stale_tree = _evaluate(
        current_candidate_sha=SHA,
        current_tree_sha="d" * 40,
    )
    assert stale_candidate.disposition == "WAIT_FOR_EVIDENCE"
    assert stale_candidate.reason_codes == ("STALE_CANDIDATE_SHA",)
    assert stale_tree.disposition == "WAIT_FOR_EVIDENCE"
    assert stale_tree.reason_codes == ("STALE_TREE_SHA",)


@pytest.mark.parametrize(
    ("steward", "governor", "reason"),
    (
        (None, _judgment("GOVERNOR"), "STEWARD_JUDGMENT_MISSING"),
        (_judgment("STEWARD"), None, "GOVERNOR_JUDGMENT_MISSING"),
    ),
)
def test_missing_governance_owner_fails_closed(
    steward: GovernanceJudgment | None,
    governor: GovernanceJudgment | None,
    reason: str,
) -> None:
    result = evaluate_covenant(BASIS, steward, governor)
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert reason in result.reason_codes


@pytest.mark.parametrize(
    "field_name",
    ["project_goal_refs", "critical_flows", "system_invariants"],
)
def test_empty_required_basis_identity_is_rejected(field_name: str) -> None:
    with pytest.raises(ValueError):
        _basis(**{field_name: ()})


def test_missing_or_malformed_candidate_identity_is_rejected() -> None:
    with pytest.raises(ValueError):
        _basis(candidate_sha="")
    with pytest.raises(ValueError):
        _basis(candidate_sha="not-a-sha")


def test_invalid_reviewer_disposition_and_alignment_are_rejected() -> None:
    with pytest.raises(ValueError):
        _judgment("ARBITER")
    with pytest.raises(ValueError):
        _judgment("STEWARD", decision="INVALID")
    with pytest.raises(ValueError):
        _judgment("STEWARD", prime_directive_alignment="MAYBE")
    with pytest.raises(ValueError):
        _judgment("STEWARD", prime_directive_alignment="NOT_APPLICABLE")


def test_duplicate_evidence_references_are_rejected() -> None:
    with pytest.raises(ValueError):
        _judgment("STEWARD", evidence_refs=("same", "same"))


def test_required_assurance_cannot_be_implicitly_passed() -> None:
    missing = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
    )
    pass_without_refs = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        assurance_result="PASS",
        assurance_evidence_durable=True,
        assurance_evidence_retrievable=True,
    )
    pass_without_retrievability = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        assurance_result="PASS",
        assurance_evidence_refs=("evidence:prai",),
        assurance_evidence_durable=True,
    )
    explicit_pass = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        assurance_result="PASS",
        assurance_evidence_refs=("evidence:prai",),
        assurance_evidence_durable=True,
        assurance_evidence_retrievable=True,
    )

    assert missing.disposition == "WAIT_FOR_EVIDENCE"
    assert missing.reason_codes == ("ASSURANCE_EVIDENCE_MISSING",)
    assert pass_without_refs.disposition == "WAIT_FOR_EVIDENCE"
    assert pass_without_refs.reason_codes == ("ASSURANCE_EVIDENCE_MISSING",)
    assert pass_without_retrievability.disposition == "WAIT_FOR_EVIDENCE"
    assert pass_without_retrievability.reason_codes == ("ASSURANCE_EVIDENCE_NOT_DURABLE",)
    assert explicit_pass.disposition == "PASS"


def test_prime_directive_not_applicable_fails_closed_defensively() -> None:
    steward = _judgment("STEWARD")
    object.__setattr__(steward, "prime_directive_alignment", "NOT_APPLICABLE")

    result = _evaluate(steward=steward)

    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert result.reason_codes == ("PRIME_DIRECTIVE_ALIGNMENT_NOT_APPLICABLE",)


def test_partial_state_readback_and_malformed_evaluation_input_fail_closed() -> None:
    partial = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        current_candidate_sha=SHA,
    )
    malformed = _evaluate(assurance_result="INVALID")
    unknown_claim_scope = _evaluate(claim_to_evidence_scope="UNKNOWN")
    assert partial.disposition == "WAIT_FOR_EVIDENCE"
    assert partial.reason_codes == ("STATE_IDENTITY_INCOMPLETE",)
    assert malformed.disposition == "WAIT_FOR_EVIDENCE"
    assert unknown_claim_scope.disposition == "WAIT_FOR_EVIDENCE"


@pytest.mark.parametrize(
    ("steward_accepts", "governor_accepts"),
    ((True, False), (False, True)),
)
def test_reconciliation_requires_both_owner_acceptances(
    steward_accepts: bool,
    governor_accepts: bool,
) -> None:
    result = _evaluate(
        cross_judgment_conflicts=("owner-boundary-conflict",),
        reconciliation=_proposal(
            steward_accepts=steward_accepts,
            governor_accepts=governor_accepts,
        ),
    )
    assert result.disposition == "REVISION_REQUIRED"
    assert result.reason_codes == ("RECONCILIATION_INVALID",)


def test_prime_directive_conflict_cannot_be_reconciled() -> None:
    result = _evaluate(
        steward=_judgment("STEWARD", prime_directive_alignment="CONFLICT"),
        cross_judgment_conflicts=("constitutional-boundary",),
        reconciliation=_proposal(),
    )
    assert result.disposition == "BLOCKED"
    assert result.reason_codes == ("PRIME_DIRECTIVE_CONFLICT",)


def test_human_review_requirement_is_preserved_with_technical_pass() -> None:
    result = _evaluate(
        governor=_judgment("GOVERNOR", human_review_required=True),
        specialist_evidence=(_specialist("CIPHER"),),
    )
    assert result.disposition == "ESCALATE_HUMAN"
    assert result.human_review_required is True


def test_unknown_owner_claim_scope_fails_closed() -> None:
    result = _evaluate(
        steward=_judgment("STEWARD", claim_scope="UNKNOWN"),
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert result.reason_codes == ("CLAIM_TO_EVIDENCE_SCOPE_UNVERIFIED",)


def test_missing_durable_evidence_cannot_be_repaired_by_a_hash() -> None:
    result = _evaluate(
        assurance_result="PASS",
        assurance_evidence_refs=("sha256:only-a-hash",),
        assurance_evidence_durable=False,
        assurance_evidence_retrievable=False,
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert result.reason_codes == ("ASSURANCE_EVIDENCE_NOT_DURABLE",)


def test_stale_or_missing_specialist_evidence_fails_closed() -> None:
    stale = _specialist("CLOCKWORK", candidate_sha="c" * 40)
    missing = _specialist("CLOCKWORK", result="MISSING")
    stale_result = _evaluate(specialist_evidence=(stale,))
    missing_result = _evaluate(specialist_evidence=(missing,))
    assert stale_result.disposition == "WAIT_FOR_EVIDENCE"
    assert missing_result.disposition == "WAIT_FOR_EVIDENCE"
