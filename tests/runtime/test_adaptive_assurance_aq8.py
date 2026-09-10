# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive import high_risk_assurance as aq8
from orchestra_runtime.domain.governance.covenant import (
    ReconciliationProposal,
    SpecialistEvidence,
)


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
TREE = "b" * 40
RUN_ID = "aq8-test-run-20260910"

ALL_CASES = tuple(
    (pack, case_id)
    for pack in aq8.PACKS
    for case_id in aq8.REQUIRED_CASES[pack]
)


def _context(**changes: object) -> aq8.AssuranceContext:
    values: dict[str, object] = {
        "repository": "Baelfyre/Orchestra",
        "source_ref": "orchestra:aq8",
        "candidate_sha": SHA,
        "tree_sha": TREE,
        "work_item_ref": "AQ8-HIGH-RISK-ASSURANCE-PACKS",
        "basis_revision": "orchestra-aq8-basis-v1",
        "project_context_ref": "PROJECT_CONTEXT.md",
        "prime_directive_ref": "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
        "project_goal_refs": ("goal:governed-high-risk-assurance",),
        "critical_flows": ("assurance-to-arbiter-transition",),
        "system_invariants": ("evidence-bound", "authority-never-expands"),
        "prohibited_outcomes": ("unverified-high-risk-transition",),
        "authority_boundaries": ("ARBITER_ONLY",),
        "observed_at": "2026-09-10T10:00:00Z",
        "workflow_run_id": RUN_ID,
    }
    values.update(changes)
    return aq8.AssuranceContext(**values)


def _evidence(
    context: aq8.AssuranceContext,
    evidence_id: str,
    **changes: object,
) -> aq8.EvidenceRecord:
    values: dict[str, object] = {
        "evidence_id": evidence_id,
        "evidence_type": "CONTROLLED_FIXTURE",
        "repository": context.repository,
        "source_ref": context.source_ref,
        "candidate_sha": context.candidate_sha,
        "tree_sha": context.tree_sha,
        "validator_identity": "OVERSEER_AQ8",
        "observed_at": context.observed_at,
        "result": "PASS",
        "exit_code": 0,
        "workflow_run_id": context.workflow_run_id,
        "freshness_ref": context.workflow_run_id,
        "durable": True,
        "retrievable": True,
        "independent": True,
        "producer_role": "OVERSEER",
    }
    values.update(changes)
    return aq8.EvidenceRecord(**values)


def _safe_facts(pack: str, case_id: str) -> dict[str, Any]:
    facts = dict(aq8._CASE_REQUIREMENTS[case_id])
    if pack == "CONCURRENCY":
        facts["interleaving_trace"] = ("SYNC:before", "worker-a", "BARRIER:commit")
    return facts


def _observation(
    context: aq8.AssuranceContext,
    pack: str,
    case_id: str,
    *,
    facts: dict[str, Any] | None = None,
    replace_facts: bool = False,
    evidence: tuple[aq8.EvidenceRecord, ...] | None = None,
    controlled_fixture: bool = True,
) -> aq8.HighRiskCaseObservation:
    selected = {} if replace_facts else _safe_facts(pack, case_id)
    if facts:
        selected.update(facts)
    return aq8.HighRiskCaseObservation(
        facts=selected,
        evidence=evidence
        if evidence is not None
        else (_evidence(context, f"evidence:{case_id}"),),
        controlled_fixture=controlled_fixture,
    )


def _observations(
    context: aq8.AssuranceContext,
) -> dict[str, dict[str, aq8.HighRiskCaseObservation]]:
    return {
        pack: {
            case_id: _observation(context, pack, case_id)
            for case_id in aq8.REQUIRED_CASES[pack]
        }
        for pack in aq8.PACKS
    }


def _pack_decision(context: aq8.AssuranceContext) -> aq8.HighRiskAssuranceDecision:
    return aq8.run_all_high_risk_packs(context, _observations(context))


def _steward(
    context: aq8.AssuranceContext,
    **changes: object,
) -> aq8.StewardSystemIntentJudgment:
    values: dict[str, object] = {
        "candidate_sha": context.candidate_sha,
        "tree_sha": context.tree_sha,
        "decision": "APPROVED",
        "prime_directive_alignment": "ALIGNED",
        "project_goal_alignment": "ALIGNED",
        "critical_flow_alignment": "ALIGNED",
        "system_invariant_alignment": "ALIGNED",
        "scope_complete": True,
        "evidence_refs": ("evidence:steward",),
    }
    values.update(changes)
    return aq8.StewardSystemIntentJudgment(**values)


def _governor(
    context: aq8.AssuranceContext,
    **changes: object,
) -> aq8.GovernorProtectedObligationJudgment:
    values: dict[str, object] = {
        "candidate_sha": context.candidate_sha,
        "tree_sha": context.tree_sha,
        "decision": "APPROVED",
        "prime_directive_alignment": "ALIGNED",
        "project_goal_alignment": "ALIGNED",
        "critical_flow_alignment": "ALIGNED",
        "system_invariant_alignment": "ALIGNED",
        "obligation_satisfaction": "SATISFIED",
        "protected_obligations": ("PRAI_AND_COVENANT_REQUIRED",),
        "evidence_refs": ("evidence:governor",),
    }
    values.update(changes)
    return aq8.GovernorProtectedObligationJudgment(**values)


def _specialist(
    context: aq8.AssuranceContext,
    reviewer: str,
) -> SpecialistEvidence:
    return SpecialistEvidence(
        reviewer=reviewer,
        result="PASS",
        claim_scope="candidate-system",
        evidence_refs=(f"evidence:{reviewer.lower()}",),
        candidate_sha=context.candidate_sha,
        tree_sha=context.tree_sha,
    )


def _covenant(
    context: aq8.AssuranceContext,
    *,
    steward: aq8.StewardSystemIntentJudgment | None = None,
    governor: aq8.GovernorProtectedObligationJudgment | None = None,
    **changes: object,
):
    values: dict[str, object] = {
        "assurance_result": "PASS",
        "assurance_evidence_refs": ("evidence:prai",),
        "assurance_evidence_durable": True,
        "assurance_evidence_retrievable": True,
        "pack_decision": _pack_decision(context),
    }
    values.update(changes)
    return aq8.evaluate_state_bound_covenant(
        context,
        steward if steward is not None else _steward(context),
        governor if governor is not None else _governor(context),
        **values,
    )


def test_machine_contract_matches_schema_and_runtime() -> None:
    contract = json.loads(
        (ROOT / "machine/adaptive/aq8-high-risk-assurance-packs.v1.json").read_text(
            encoding="utf-8"
        )
    )
    schema = json.loads(
        (ROOT / "machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    assert aq8.validate_aq8_contract(contract) == contract
    assert contract["packs"] == list(aq8.PACKS)
    assert contract["required_cases"] == {
        pack: list(aq8.REQUIRED_CASES[pack]) for pack in aq8.PACKS
    }
    assert contract["required_covenant_scenarios"] == list(
        aq8.AQ8_REQUIRED_COVENANT_SCENARIOS
    )
    assert contract["required_aq7_regression_anchors"] == list(
        aq8.AQ8_AQ7_REGRESSION_ANCHORS
    )
    assert contract["authority"]["decision_grants_authority"] is False


def test_context_evidence_and_observation_serialization_is_strict() -> None:
    context = _context()
    assert aq8.AssuranceContext.from_mapping(context.to_dict()) == context

    evidence = _evidence(context, "evidence:roundtrip")
    assert aq8.EvidenceRecord.from_mapping(evidence.to_dict()) == evidence

    observation = _observation(
        context, "SECURITY", "SECURITY_UNKNOWN_CREDENTIAL"
    )
    assert aq8.HighRiskCaseObservation.from_mapping(observation.to_dict()) == observation

    with pytest.raises(TypeError):
        aq8.AssuranceContext.from_mapping([])
    with pytest.raises(ValueError):
        aq8.AssuranceContext.from_mapping({**context.to_dict(), "unexpected": True})
    missing_context = context.to_dict()
    missing_context.pop("work_item_ref")
    with pytest.raises(ValueError):
        aq8.AssuranceContext.from_mapping(missing_context)

    with pytest.raises(TypeError):
        aq8.EvidenceRecord.from_mapping([])
    with pytest.raises(ValueError):
        aq8.EvidenceRecord.from_mapping({**evidence.to_dict(), "unexpected": True})
    missing_evidence = evidence.to_dict()
    missing_evidence.pop("evidence_id")
    with pytest.raises(ValueError):
        aq8.EvidenceRecord.from_mapping(missing_evidence)

    with pytest.raises(TypeError):
        aq8.HighRiskCaseObservation.from_mapping([])
    with pytest.raises(ValueError):
        aq8.HighRiskCaseObservation.from_mapping({"facts": {}, "unexpected": True})
    with pytest.raises(ValueError):
        aq8.HighRiskCaseObservation.from_mapping({"evidence": []})


def test_constructor_validation_branches_fail_closed() -> None:
    context = _context()
    evidence = _evidence(context, "evidence:validation")
    observation = _observation(
        context, "SECURITY", "SECURITY_UNKNOWN_CREDENTIAL"
    )

    with pytest.raises(TypeError):
        replace(evidence, exit_code=True)
    with pytest.raises(TypeError):
        replace(evidence, durable="yes")
    with pytest.raises(TypeError):
        replace(evidence, retrievable=1)
    with pytest.raises(TypeError):
        replace(evidence, independent=None)
    with pytest.raises(ValueError):
        replace(evidence, evidence_digest="0" * 64)
    with pytest.raises(ValueError):
        replace(evidence, evidence_id="")
    with pytest.raises(ValueError):
        replace(evidence, producer_role="bad\nrole")

    with pytest.raises(TypeError):
        aq8.HighRiskCaseObservation(facts=[], evidence=())
    with pytest.raises(TypeError):
        aq8.HighRiskCaseObservation(facts={}, evidence="bad")
    with pytest.raises(TypeError):
        replace(observation, controlled_fixture="yes")

    with pytest.raises(ValueError):
        _context(project_goal_refs=())
    with pytest.raises(TypeError):
        _context(critical_flows="not-a-list")
    with pytest.raises(ValueError):
        _context(system_invariants=("same", "same"))


def test_every_declared_case_is_executable_and_non_authorizing() -> None:
    context = _context()
    for pack, case_id in ALL_CASES:
        result = aq8.evaluate_case(
            context,
            pack,
            case_id,
            _observation(context, pack, case_id),
        )
        assert result.disposition == "PASS"
        assert result.compliant is True
        assert result.authority_granted is False

    decision = _pack_decision(context)
    assert decision.result == "PASS"
    assert decision.compliant is True
    assert decision.transition_owner == "ARBITER"
    assert decision.authority_granted is False
    assert tuple(pack.pack for pack in decision.packs) == aq8.PACKS
    assert decision.decision_digest
    assert decision.to_dict()["authority_granted"] is False
    for pack in decision.packs:
        assert pack.result == "PASS"
        assert pack.controlled_case_count == len(aq8.REQUIRED_CASES[pack.pack])
        assert pack.organic_case_count == 0


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    (
        ({"repository": "other/repo"}, "AQ8_EVIDENCE_REPOSITORY_MISMATCH"),
        ({"source_ref": "other:source"}, "AQ8_EVIDENCE_SOURCE_MISMATCH"),
        ({"candidate_sha": "c" * 40}, "AQ8_EVIDENCE_CANDIDATE_MISMATCH"),
        ({"tree_sha": "d" * 40}, "AQ8_EVIDENCE_TREE_MISMATCH"),
        ({"validator_identity": None}, "AQ8_EVIDENCE_VALIDATOR_MISSING"),
        ({"evidence_type": "UNSUPPORTED"}, "AQ8_EVIDENCE_TYPE_UNSUPPORTED"),
        ({"result": "FAIL", "exit_code": 1}, "AQ8_EVIDENCE_RESULT_NOT_PASS"),
        (
            {"workflow_run_id": "old-run", "freshness_ref": "old-run"},
            "AQ8_EVIDENCE_STALE_WORKFLOW_RUN",
        ),
        ({"durable": False}, "AQ8_EVIDENCE_NOT_DURABLE"),
        ({"retrievable": False}, "AQ8_EVIDENCE_NOT_RETRIEVABLE"),
        ({"exit_code": 1}, "AQ8_EVIDENCE_PASS_NONZERO_EXIT"),
        ({"producer_role": "CALLER"}, "AQ8_EVIDENCE_CALLER_ASSERTED"),
        ({"independent": False}, "AQ8_EVIDENCE_NOT_INDEPENDENT"),
    ),
)
def test_evidence_binding_fails_closed(
    changes: dict[str, object], expected_code: str
) -> None:
    context = _context()
    record = _evidence(context, "evidence:bad", **changes)
    result = aq8.evaluate_security_case(
        context,
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(record,),
        ),
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert expected_code in result.reason_codes


def test_invalid_digest_duplicate_missing_and_invalid_evidence_fail_closed() -> None:
    context = _context()
    record = _evidence(context, "evidence:invalid-digest")
    object.__setattr__(record, "evidence_digest", "0" * 64)
    result = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(record,),
        ),
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_INVALID_DIGEST" in result.reason_codes

    duplicate = _evidence(context, "evidence:duplicate")
    duplicate_result = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(duplicate, duplicate),
        ),
    )
    assert "AQ8_EVIDENCE_DUPLICATE_ID" in duplicate_result.reason_codes

    missing = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(),
        ),
    )
    assert "AQ8_EVIDENCE_MISSING" in missing.reason_codes
    assert aq8.validate_evidence_record(object(), object()) == (
        "AQ8_INVALID_OBSERVATION",
    )


def test_fact_and_concurrency_fail_closed_paths() -> None:
    context = _context()

    unknown = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            facts={"state": "UNKNOWN"},
        ),
    )
    assert unknown.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_STATE" in unknown.reason_codes

    missing = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            replace_facts=True,
        ),
    )
    assert missing.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_REQUIRED_FACT_MISSING" in missing.reason_codes

    violation = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            facts={"credential_accepted": True},
        ),
    )
    assert violation.disposition == "REVISION_REQUIRED"
    assert "AQ8_CONTROL_VIOLATION" in violation.reason_codes

    uncontrolled = aq8.evaluate_concurrency_case(
        context,
        "CONCURRENCY_SAME_ROW_RACE",
        _observation(
            context,
            "CONCURRENCY",
            "CONCURRENCY_SAME_ROW_RACE",
            controlled_fixture=False,
        ),
    )
    assert uncontrolled.disposition == "WAIT_FOR_EVIDENCE"

    sequential = aq8.evaluate_concurrency_case(
        context,
        "CONCURRENCY_SAME_ROW_RACE",
        _observation(
            context,
            "CONCURRENCY",
            "CONCURRENCY_SAME_ROW_RACE",
            facts={
                "interleaving_trace": ("worker-a", "worker-b"),
                "sequential_approximation": True,
            },
        ),
    )
    assert sequential.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_CONTROLLED_INTERLEAVING_REQUIRED" in sequential.reason_codes

    aggregate = aq8.evaluate_concurrency_case(
        context,
        "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
        _observation(
            context,
            "CONCURRENCY",
            "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
            facts={"aggregate_concurrency_proof": False},
        ),
    )
    assert aggregate.disposition == "REVISION_REQUIRED"
    assert "AQ8_AGGREGATE_PROOF_REQUIRED" in aggregate.reason_codes


def test_result_models_reject_shape_and_authority_drift() -> None:
    context = _context()
    decision = _pack_decision(context)
    pack = decision.packs[0]
    case = pack.cases[0]

    with pytest.raises(ValueError):
        replace(case, pack="PROVENANCE")
    with pytest.raises(ValueError):
        replace(case, compliant=False)
    with pytest.raises(TypeError):
        replace(case, controlled_fixture="yes")
    with pytest.raises(ValueError):
        replace(case, authority_granted=True)

    with pytest.raises(ValueError):
        replace(pack, compliant=False)
    with pytest.raises(ValueError):
        replace(pack, cases=(decision.packs[1].cases[0],))
    with pytest.raises(ValueError):
        replace(pack, authority_granted=True)

    with pytest.raises(TypeError):
        replace(decision, context=object())
    with pytest.raises(ValueError):
        replace(decision, compliant=False)
    with pytest.raises(ValueError):
        replace(decision, packs=tuple(reversed(decision.packs)))
    with pytest.raises(ValueError):
        replace(decision, authority_granted=True)


def test_owner_judgment_validation_and_scope_downgrade() -> None:
    context = _context()
    incomplete = _steward(context, scope_complete=False)
    assert incomplete.to_governance_judgment().decision == "REVISION_REQUIRED"

    with pytest.raises(TypeError):
        _steward(context, scope_complete="yes")
    with pytest.raises(TypeError):
        _governor(context, human_review_required="yes")

    governor = _governor(context, human_review_required=True)
    assert governor.to_governance_judgment().human_review_required is True


def test_pack_runners_reject_missing_malformed_and_unknown_inputs() -> None:
    context = _context()

    with pytest.raises(TypeError):
        aq8.run_high_risk_pack(context, "SECURITY", [])

    missing = aq8.run_high_risk_pack(context, "SECURITY", {})
    assert missing.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_CASE_OBSERVATION_MISSING" in missing.failure_codes

    malformed = aq8.run_high_risk_pack(
        context,
        "SECURITY",
        {"SECURITY_UNKNOWN_CREDENTIAL": {"facts": []}},
    )
    assert malformed.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_INVALID_OBSERVATION" in malformed.failure_codes

    unknown_cases = _observations(context)["SECURITY"]
    unknown_cases["NOT_A_CASE"] = _observation(
        context, "SECURITY", "SECURITY_UNKNOWN_CREDENTIAL"
    )
    result = aq8.run_high_risk_pack(context, "SECURITY", unknown_cases)
    assert result.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_CASE" in result.failure_codes

    with pytest.raises(TypeError):
        aq8.run_all_high_risk_packs(object(), {})
    with pytest.raises(TypeError):
        aq8.run_all_high_risk_packs(context, [])

    unknown_packs = _observations(context)
    unknown_packs["NOT_A_PACK"] = {}
    decision = aq8.run_all_high_risk_packs(context, unknown_packs)
    assert decision.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_PACK" in decision.failure_codes

    invalid_pack = _observations(context)
    invalid_pack["SECURITY"] = []
    decision = aq8.run_all_high_risk_packs(context, invalid_pack)
    assert decision.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_INVALID_OBSERVATION" in decision.failure_codes


def test_public_case_routers_reject_wrong_case_and_pack() -> None:
    context = _context()
    observation = _observation(
        context, "SECURITY", "SECURITY_UNKNOWN_CREDENTIAL"
    )
    with pytest.raises(ValueError, match="AQ8_UNKNOWN_CASE"):
        aq8.evaluate_security_case(context, "STATE_MACHINE_LEGAL_TRANSITION", observation)
    with pytest.raises(ValueError):
        aq8.evaluate_case(context, "UNKNOWN", "SECURITY_UNKNOWN_CREDENTIAL", observation)

    assert aq8.evaluate_provenance_case(
        context,
        "PROVENANCE_FORGED_SOURCE_SHA",
        _observation(context, "PROVENANCE", "PROVENANCE_FORGED_SOURCE_SHA"),
    ).disposition == "PASS"
    assert aq8.evaluate_state_machine_case(
        context,
        "STATE_MACHINE_LEGAL_TRANSITION",
        _observation(context, "STATE_MACHINE", "STATE_MACHINE_LEGAL_TRANSITION"),
    ).disposition == "PASS"
    assert aq8.evaluate_evidence_integrity_case(
        context,
        "EVIDENCE_SELF_ASSERTED_PASS",
        _observation(context, "EVIDENCE_INTEGRITY", "EVIDENCE_SELF_ASSERTED_PASS"),
    ).disposition == "PASS"


def test_state_bound_covenant_pack_preconditions_fail_closed() -> None:
    context = _context()
    assert _covenant(context).disposition == "PASS"

    with pytest.raises(TypeError):
        aq8.evaluate_state_bound_covenant(
            object(),
            _steward(context),
            _governor(context),
            assurance_result="PASS",
            assurance_evidence_refs=("evidence:prai",),
            assurance_evidence_durable=True,
            assurance_evidence_retrievable=True,
        )
    with pytest.raises(TypeError):
        aq8.evaluate_state_bound_covenant(
            context,
            object(),
            _governor(context),
            assurance_result="PASS",
            assurance_evidence_refs=("evidence:prai",),
            assurance_evidence_durable=True,
            assurance_evidence_retrievable=True,
        )

    assert _covenant(context, pack_decision=None).disposition == "REVISION_REQUIRED"
    assert _covenant(context, pack_decision=object()).disposition == "REVISION_REQUIRED"

    nonpass = aq8.run_all_high_risk_packs(context, {})
    assert nonpass.result == "WAIT_FOR_EVIDENCE"
    assert _covenant(context, pack_decision=nonpass).disposition == "REVISION_REQUIRED"

    stale_context = _context(candidate_sha="c" * 40)
    stale_pack = _pack_decision(stale_context)
    assert _covenant(context, pack_decision=stale_pack).disposition == "REVISION_REQUIRED"
    assert _covenant(
        context, governor=_governor(context, candidate_sha="c" * 40)
    ).disposition == "REVISION_REQUIRED"


def test_covenant_required_scenarios_execute_with_expected_precedence() -> None:
    context = _context()
    scenarios = {
        "COV-01": _covenant(
            context,
            steward=_steward(context, prime_directive_alignment="CONFLICT"),
        ),
        "COV-02": _covenant(context, governor=_governor(context, decision="BLOCKED")),
        "COV-03": _covenant(
            context, steward=_steward(context, decision="REVISION_REQUIRED")
        ),
        "COV-04A": _covenant(
            context,
            cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
            reconciliation=ReconciliationProposal(
                "unsafe broad audit retention",
                True,
                False,
                True,
                True,
                ("evidence:unsafe-reconciliation",),
            ),
        ),
        "COV-04B": _covenant(
            context,
            cross_judgment_conflicts=("privacy-minimization-vs-auditability",),
            reconciliation=ReconciliationProposal(
                "minimum necessary durable audit identifiers",
                True,
                True,
                True,
                True,
                ("evidence:narrow-reconciliation",),
                ("minimum-identifiers", "controlled-retention"),
            ),
        ),
        "COV-05": _covenant(
            context,
            governor=_governor(context, decision="REVISION_REQUIRED"),
            cross_judgment_conflicts=("scope-vs-compliance-requirement",),
        ),
        "COV-06": _covenant(
            context,
            governor=_governor(context, decision="BLOCKED"),
            cross_judgment_conflicts=("convenience-vs-authorization",),
        ),
        "COV-07": _covenant(context, assurance_result="MISSING"),
        "COV-08": _covenant(
            context,
            system_contradictions=("concurrent last-admin aggregate invariant can fail",),
        ),
        "COV-09": _covenant(
            context,
            system_contradictions=("privilege mutation can precede durable audit",),
        ),
        "COV-10": _covenant(
            context,
            specialist_evidence=tuple(
                _specialist(context, reviewer)
                for reviewer in ("CLOCKWORK", "CIPHER", "CHRONICLER", "OVERSEER")
            ),
            system_contradictions=("PRAI pass conflicts with system behavior",),
        ),
        "COV-11": _covenant(
            context,
            assurance_evidence_refs=("sha256:missing-durable-evidence",),
            assurance_evidence_durable=False,
            assurance_evidence_retrievable=False,
        ),
        "COV-12": _covenant(
            context,
            cross_judgment_conflicts=("owner-boundary-conflict",),
            reconciliation=ReconciliationProposal(
                "bounded reconciliation",
                True,
                True,
                True,
                True,
                ("evidence:bounded-reconciliation",),
                ("preserve-owner-boundaries",),
            ),
        ),
        "COV-13": _covenant(
            context,
            steward=_steward(context, critical_flow_alignment="CONTRADICTIONS"),
        ),
        "COV-14": _covenant(
            context, governor=_governor(context, decision="REVISION_REQUIRED")
        ),
        "COV-15": _covenant(
            context, steward=_steward(context, project_goal_alignment="CONFLICT")
        ),
        "COV-16": _covenant(
            context,
            governor=_governor(
                context,
                human_review_required=True,
                obligation_satisfaction="UNKNOWN",
            ),
        ),
        "COV-17": _covenant(
            context,
            governor=_governor(
                context,
                decision="NOT_APPLICABLE",
                obligation_satisfaction="NOT_APPLICABLE",
            ),
        ),
        "COV-18": _covenant(
            context,
            steward=_steward(context, prime_directive_alignment="UNKNOWN"),
        ),
    }
    expected = {
        "COV-01": "BLOCKED",
        "COV-02": "BLOCKED",
        "COV-03": "REVISION_REQUIRED",
        "COV-04A": "REVISION_REQUIRED",
        "COV-04B": "RECONCILED_WITH_CONSTRAINTS",
        "COV-05": "REVISION_REQUIRED",
        "COV-06": "BLOCKED",
        "COV-07": "WAIT_FOR_EVIDENCE",
        "COV-08": "REVISION_REQUIRED",
        "COV-09": "REVISION_REQUIRED",
        "COV-10": "REVISION_REQUIRED",
        "COV-11": "WAIT_FOR_EVIDENCE",
        "COV-12": "RECONCILED_WITH_CONSTRAINTS",
        "COV-13": "REVISION_REQUIRED",
        "COV-14": "REVISION_REQUIRED",
        "COV-15": "REVISION_REQUIRED",
        "COV-16": "ESCALATE_HUMAN",
        "COV-17": "PASS",
        "COV-18": "WAIT_FOR_EVIDENCE",
    }
    assert tuple(aq8.AQ8_REQUIRED_COVENANT_SCENARIOS) == tuple(
        f"COV-{number:02d}" for number in range(1, 19)
    )
    for scenario, disposition in expected.items():
        assert scenarios[scenario].disposition == disposition


def test_aq7_regression_anchors_execute_fail_closed() -> None:
    context = _context()

    aggregate = aq8.evaluate_case(
        context,
        "CONCURRENCY",
        "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
        _observation(
            context,
            "CONCURRENCY",
            "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
            facts={"aggregate_concurrency_proof": False},
        ),
    )
    assert aggregate.disposition == "REVISION_REQUIRED"
    assert "AQ8_AGGREGATE_PROOF_REQUIRED" in aggregate.reason_codes

    privilege = aq8.evaluate_case(
        context,
        "CONCURRENCY",
        "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION",
        _observation(
            context,
            "CONCURRENCY",
            "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION",
            facts={
                "authorization_rechecked_at_commit": False,
                "commit_after_revocation": True,
            },
        ),
    )
    assert privilege.disposition == "REVISION_REQUIRED"

    missing_durable = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY",
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(
                _evidence(context, "evidence:missing-durable", durable=False),
            ),
        ),
    )
    assert missing_durable.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_NOT_DURABLE" in missing_durable.reason_codes

    assert len(aq8.AQ8_AQ7_REGRESSION_ANCHORS) == 3


def test_contract_runtime_parity_rejects_shape_and_value_drift() -> None:
    contract = json.loads(
        (ROOT / "machine/adaptive/aq8-high-risk-assurance-packs.v1.json").read_text(
            encoding="utf-8"
        )
    )
    with pytest.raises(TypeError):
        aq8.validate_aq8_contract([])
    with pytest.raises(ValueError, match="AQ8_SCHEMA_RUNTIME_DRIFT"):
        aq8.validate_aq8_contract({**contract, "unexpected": True})

    drift = dict(contract)
    drift["transition_owner"] = "CONDUCTOR"
    with pytest.raises(ValueError, match="AQ8_SCHEMA_RUNTIME_DRIFT"):
        aq8.validate_aq8_contract(drift)


def test_adversarial_inventory_and_authority_boundary_remain_fixed() -> None:
    context = _context()
    assert len(aq8.AQ8_ADVERSARIAL_PERMUTATIONS) == 14
    assert _covenant(
        context, system_contradictions=("PRAI contradiction",)
    ).disposition == "REVISION_REQUIRED"
    assert _covenant(context, reconciliation=object()).disposition == "WAIT_FOR_EVIDENCE"

    decision = _pack_decision(context)
    assert decision.transition_owner == "ARBITER"
    assert decision.authority_granted is False
    assert all(pack.authority_granted is False for pack in decision.packs)
    assert all(
        case.authority_granted is False
        for pack in decision.packs
        for case in pack.cases
    )
