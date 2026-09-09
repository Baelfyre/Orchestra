# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.governance.covenant import (
    ALIGNMENT_STATES,
    ASSURANCE_RESULTS,
    COVENANT_DISPOSITIONS,
    COVENANT_SCHEMA_VERSION,
    FLOW_ALIGNMENT_STATES,
    GOVERNANCE_DECISIONS,
    OBLIGATION_STATES,
    SPECIALIST_RESULTS,
    CovenantBasis,
    CovenantDecision,
    GovernanceJudgment,
    ReconciliationProposal,
    SpecialistEvidence,
    evaluate_covenant,
)


ROOT = Path(__file__).resolve().parents[2]
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


def _judgment(reviewer: str, **changes: object) -> GovernanceJudgment:
    values: dict[str, object] = {
        "reviewer": reviewer,
        "evidence_refs": (f"evidence:{reviewer.lower()}",),
    }
    values.update(changes)
    return GovernanceJudgment(**values)


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
        _basis(),
        steward if steward is not None else _judgment("STEWARD"),
        governor if governor is not None else _judgment("GOVERNOR"),
        **kwargs,
    )


BASIS = _basis()


def test_machine_contract_matches_schema_and_authority_boundaries() -> None:
    contract = json.loads(
        (ROOT / "machine/governance/covenant.v1.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "machine/schemas/covenant.v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)

    assert contract["schema_version"] == COVENANT_SCHEMA_VERSION
    assert contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING"
    assert contract["transition_owner"] == "ARBITER"
    assert contract["legacy_assurance_engine"]["name"] == "PRAI"
    assert contract["legacy_assurance_engine"]["prai_pass_sufficient_for_covenant_pass"] is False
    assert contract["constitutional_precedence"][:2] == [
        "PRIME_DIRECTIVE",
        "EXPLICIT_HUMAN_AUTHORITY",
    ]
    assert contract["basis_required_fields"] == [
        "repository",
        "candidate_sha",
        "tree_sha",
        "basis_revision",
        "project_context_ref",
        "prime_directive_ref",
        "project_goal_refs",
        "critical_flows",
        "system_invariants",
        "prohibited_outcomes",
        "authority_boundaries",
    ]
    assert "SYSTEM_CONTRADICTION" in contract["reconciliation_invariants"]
    assert (
        "PRIME_DIRECTIVE_ALIGNMENT_CANNOT_BE_NOT_APPLICABLE"
        in contract["reconciliation_invariants"]
    )
    assert "CONCURRENT_AGGREGATE_INVARIANT" in contract["required_scenario_classes"]
    assert "MUTATION_VS_AUDIT_ATOMICITY" in contract["required_scenario_classes"]
    assert set(contract["dispositions"]) == set(COVENANT_DISPOSITIONS)


def test_runtime_vocabularies_and_serialization_are_strict() -> None:
    assert "UNKNOWN" in ALIGNMENT_STATES
    assert "CONTRADICTIONS" in FLOW_ALIGNMENT_STATES
    assert "NOT_APPLICABLE" in OBLIGATION_STATES
    assert "PASS" in ASSURANCE_RESULTS
    assert "PASS" in SPECIALIST_RESULTS
    assert "BLOCKED" in GOVERNANCE_DECISIONS

    basis = _basis()
    result = evaluate_covenant(
        basis,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        current_candidate_sha=SHA,
        current_tree_sha=TREE,
    )
    payload = result.to_dict()
    assert payload["authority_granted"] is False
    assert payload["basis"]["project_context_ref"] == "PROJECT_CONTEXT.md"
    assert "project_ref" not in payload["basis"]
    assert result.basis_digest
    assert result.decision_digest
    assert result.evidence_refs


@pytest.mark.parametrize(
    "field_name",
    ["project_goal_refs", "critical_flows", "system_invariants"],
)
def test_material_basis_collections_cannot_be_empty(field_name: str) -> None:
    with pytest.raises(ValueError):
        _basis(**{field_name: ()})


def test_project_context_legacy_alias_is_not_emitted() -> None:
    basis = _basis(project_context_ref=None, project_ref="PROJECT_CONTEXT.md")
    assert basis.project_context_ref == "PROJECT_CONTEXT.md"
    assert basis.project_ref == "PROJECT_CONTEXT.md"
    assert "project_ref" not in basis.to_dict()


def test_conflicting_context_aliases_are_rejected() -> None:
    with pytest.raises(ValueError):
        _basis(project_ref="other-context.md")


def test_decision_requires_evidence_and_valid_disposition() -> None:
    basis = _basis()
    with pytest.raises(ValueError):
        CovenantDecision(
            basis=basis,
            disposition="PASS",
            reason_codes=(),
            constraints=(),
            evidence_refs=(),
            human_review_required=False,
        )
    with pytest.raises(ValueError):
        CovenantDecision(
            basis=basis,
            disposition="INVALID",
            reason_codes=(),
            constraints=(),
            evidence_refs=("evidence",),
            human_review_required=False,
        )
    with pytest.raises(ValueError):
        CovenantDecision(
            basis=basis,
            disposition="PASS",
            reason_codes=(),
            constraints=(),
            evidence_refs=("evidence",),
            human_review_required=False,
        )


def test_reconciliation_requires_nonempty_evidence() -> None:
    with pytest.raises(ValueError):
        ReconciliationProposal(
            "narrow design",
            True,
            True,
            True,
            True,
            (),
        )


def test_domain_serializers_and_strict_text_validation() -> None:
    with pytest.raises(TypeError):
        _basis(repository=object())
    with pytest.raises(ValueError):
        _basis(repository="\x01")
    with pytest.raises(TypeError):
        _basis(project_goal_refs="goal")
    with pytest.raises(TypeError):
        _basis(project_goal_refs=None)
    with pytest.raises(ValueError):
        _basis(project_context_ref=None, project_ref=None)
    with pytest.raises(TypeError):
        _basis(assurance_required=1)

    steward = _judgment("STEWARD")
    specialist = SpecialistEvidence(
        reviewer="CLOCKWORK",
        result="PASS",
        claim_scope="candidate-system",
        evidence_refs=("evidence:clockwork",),
        candidate_sha=SHA,
        tree_sha=TREE,
        limitations=("static-only",),
    )
    proposal = ReconciliationProposal(
        "narrow design",
        True,
        True,
        True,
        True,
        ("evidence:proposal",),
    )
    assert steward.to_dict()["reviewer"] == "STEWARD"
    assert specialist.to_dict()["limitations"] == ["static-only"]
    assert proposal.to_dict()["evidence_refs"] == ["evidence:proposal"]

    with pytest.raises(TypeError):
        GovernanceJudgment(reviewer="STEWARD", human_review_required=1)
    with pytest.raises(TypeError):
        CovenantDecision(
            basis=object(),
            disposition="PASS",
            reason_codes=("reason",),
            constraints=(),
            evidence_refs=("evidence",),
            human_review_required=False,
        )
    with pytest.raises(TypeError):
        CovenantDecision(
            basis=_basis(),
            disposition="PASS",
            reason_codes=("reason",),
            constraints=(),
            evidence_refs=("evidence",),
            human_review_required=1,
        )


def test_evaluator_rejects_malformed_and_ambiguous_inputs() -> None:
    with pytest.raises(TypeError):
        evaluate_covenant(object(), _judgment("STEWARD"), _judgment("GOVERNOR"))

    invalid_governance = evaluate_covenant(BASIS, object(), object())
    invalid_state = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        current_candidate_sha="not-a-sha",
        current_tree_sha=TREE,
    )
    swapped_reviewers = evaluate_covenant(
        BASIS,
        _judgment("GOVERNOR"),
        _judgment("STEWARD"),
    )
    missing_governance_evidence = evaluate_covenant(
        BASIS,
        _judgment("STEWARD", evidence_refs=()),
        _judgment("GOVERNOR"),
    )
    malformed_durable = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        assurance_evidence_durable=1,
    )
    malformed_retrievable = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        assurance_evidence_retrievable=1,
    )
    unknown_scope = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        claim_to_evidence_scope="UNSPECIFIED",
    )
    invalid_reconciliation = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        reconciliation=object(),
    )
    invalid_specialist = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        specialist_evidence=(object(),),
    )
    missing_specialist_refs = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR"),
        specialist_evidence=(
            SpecialistEvidence(
                reviewer="CLOCKWORK",
                result="PASS",
                claim_scope="candidate-system",
                evidence_refs=(),
                candidate_sha=SHA,
                tree_sha=TREE,
            ),
        ),
    )

    assert invalid_governance.reason_codes == ("INVALID_GOVERNANCE_JUDGMENT",)
    assert invalid_state.reason_codes == ("INVALID_STATE_IDENTITY",)
    assert swapped_reviewers.reason_codes == ("WRONG_GOVERNANCE_REVIEWER",)
    assert missing_governance_evidence.reason_codes == ("GOVERNANCE_EVIDENCE_MISSING",)
    assert malformed_durable.reason_codes == ("MALFORMED_COVENANT_INPUT",)
    assert malformed_retrievable.reason_codes == ("MALFORMED_COVENANT_INPUT",)
    assert unknown_scope.reason_codes == ("MALFORMED_COVENANT_INPUT",)
    assert invalid_reconciliation.reason_codes == ("INVALID_RECONCILIATION",)
    assert invalid_specialist.reason_codes == ("INVALID_SPECIALIST_EVIDENCE",)
    assert missing_specialist_refs.reason_codes == ("SPECIALIST_EVIDENCE_MISSING",)


def test_evaluator_closes_each_non_final_or_prohibited_state() -> None:
    duplicate_basis_evidence = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR", evidence_refs=("PROJECT_CONTEXT.md",)),
        assurance_result="PASS",
        assurance_evidence_refs=("evidence:prai",),
        assurance_evidence_durable=True,
        assurance_evidence_retrievable=True,
    )
    blocked_obligation = evaluate_covenant(
        BASIS,
        _judgment("STEWARD"),
        _judgment("GOVERNOR", obligation_satisfaction="GAPS"),
        assurance_result="PASS",
    )
    blocked_assurance = _evaluate(assurance_result="BLOCKED")
    prohibited_present = _evaluate(prohibited_outcome_avoidance="PRESENT")
    prohibited_unknown = _evaluate(prohibited_outcome_avoidance="UNKNOWN")
    advisory_steward = _evaluate(steward=_judgment("STEWARD", decision="ADVISORY_ONLY"))
    governor_not_applicable = _evaluate(
        governor=_judgment("GOVERNOR", decision="NOT_APPLICABLE")
    )
    coverage_not_applicable = _evaluate(
        steward=_judgment("STEWARD", critical_flow_alignment="NOT_APPLICABLE")
    )
    blocked_specialist = _evaluate(
        specialist_evidence=(
            SpecialistEvidence(
                reviewer="CLOCKWORK",
                result="BLOCKED",
                claim_scope="candidate-system",
                evidence_refs=("evidence:clockwork",),
                candidate_sha=SHA,
                tree_sha=TREE,
            ),
        )
    )
    unexpected_reconciliation = _evaluate(
        reconciliation=ReconciliationProposal(
            "unrequested reconciliation",
            True,
            True,
            True,
            True,
            ("evidence:unexpected",),
        )
    )
    explicit_claim_scope = _evaluate(claim_to_evidence_scope="PASS")

    assert duplicate_basis_evidence.disposition == "PASS"
    assert blocked_obligation.disposition == "BLOCKED"
    assert blocked_assurance.disposition == "BLOCKED"
    assert prohibited_present.disposition == "BLOCKED"
    assert prohibited_unknown.disposition == "WAIT_FOR_EVIDENCE"
    assert advisory_steward.disposition == "WAIT_FOR_EVIDENCE"
    assert governor_not_applicable.disposition == "WAIT_FOR_EVIDENCE"
    assert coverage_not_applicable.disposition == "WAIT_FOR_EVIDENCE"
    assert blocked_specialist.disposition == "REVISION_REQUIRED"
    assert unexpected_reconciliation.disposition == "REVISION_REQUIRED"
    assert explicit_claim_scope.disposition == "PASS"
