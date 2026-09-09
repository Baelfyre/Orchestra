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
