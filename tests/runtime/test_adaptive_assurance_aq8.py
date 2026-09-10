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


SAFE_FACTS: dict[str, dict[str, Any]] = {
    "SECURITY_UNKNOWN_CREDENTIAL": {
        "control_verified": True, "credential_accepted": False,
        "decision": "DENY", "enumeration_safe": True,
    },
    "SECURITY_INACTIVE_PRINCIPAL": {
        "control_verified": True, "principal_accepted": False, "decision": "DENY",
    },
    "SECURITY_MISSING_GRANT": {
        "control_verified": True, "grant_accepted": False, "decision": "DENY",
    },
    "SECURITY_GUESSED_OBJECT_ID": {
        "control_verified": True, "object_enumerated": False, "decision": "DENY",
    },
    "SECURITY_CROSS_TENANT_ID": {
        "control_verified": True, "tenant_scope_match": False,
        "object_enumerated": False, "decision": "DENY",
    },
    "SECURITY_CROSS_WORKSPACE_ID": {
        "control_verified": True, "workspace_scope_match": False,
        "object_enumerated": False, "decision": "DENY",
    },
    "SECURITY_PRIVILEGE_ESCALATION": {
        "control_verified": True, "escalation_accepted": False, "decision": "DENY",
    },
    "SECURITY_TENANT_ADMIN_GLOBAL_AUTHORITY_SEPARATION": {
        "control_verified": True, "global_authority_mutated": False,
        "tenant_authority_isolated": True,
    },
    "SECURITY_REVOCATION_BEFORE_REQUEST": {
        "control_verified": True, "revocation_observed": True, "decision": "DENY",
    },
    "SECURITY_REVOCATION_DURING_REQUEST": {
        "control_verified": True, "revocation_rechecked": True,
        "commit_after_revocation": False, "decision": "DENY",
    },
    "SECURITY_STALE_AUTHORIZATION_STATE": {
        "control_verified": True, "authorization_refreshed": True,
        "stale_state_accepted": False, "decision": "DENY",
    },
    "PROVENANCE_CALLER_SUPPLIED_AUTHORITATIVE_VERSION": {
        "defect_detected": True, "authoritative_version_source": "REPOSITORY",
        "decision": "REJECT",
    },
    "PROVENANCE_FORGED_SOURCE_SHA": {
        "defect_detected": True, "source_sha_verified": False, "decision": "REJECT",
    },
    "PROVENANCE_REPORT_HASH_MISMATCH": {
        "defect_detected": True, "report_hash_matches": False, "decision": "REJECT",
    },
    "PROVENANCE_STALE_EVIDENCE": {
        "defect_detected": True, "evidence_fresh": False, "decision": "REJECT",
    },
    "PROVENANCE_WRONG_TENANT_WORKSPACE_EVIDENCE": {
        "defect_detected": True, "tenant_workspace_match": False,
        "decision": "REJECT",
    },
    "PROVENANCE_WRONG_CANDIDATE_EVIDENCE": {
        "defect_detected": True, "candidate_binding_match": False,
        "decision": "REJECT",
    },
    "PROVENANCE_DUPLICATE_PROVENANCE_ID": {
        "defect_detected": True, "duplicate_provenance_rejected": True,
        "decision": "REJECT",
    },
    "CONCURRENCY_SAME_ROW_RACE": {
        "controlled_interleaving_proof": True, "row_version_checked": True,
        "lost_update": False, "decision": "REJECT",
    },
    "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE": {
        "controlled_interleaving_proof": True, "aggregate_concurrency_proof": True,
        "aggregate_invariant_preserved": True, "row_versions_only": False,
    },
    "CONCURRENCY_LOST_UPDATE": {
        "controlled_interleaving_proof": True, "lost_update_prevented": True,
        "decision": "REJECT",
    },
    "CONCURRENCY_DUPLICATE_SUBMIT": {
        "controlled_interleaving_proof": True, "idempotency_enforced": True,
        "logical_effect_count": 1,
    },
    "CONCURRENCY_RETRY_AFTER_TIMEOUT": {
        "controlled_interleaving_proof": True, "retry_reconciled": True,
        "logical_effect_count": 1,
    },
    "CONCURRENCY_IDEMPOTENCY_COLLISION": {
        "controlled_interleaving_proof": True, "collision_rejected": True,
        "logical_effect_count": 1,
    },
    "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION": {
        "controlled_interleaving_proof": True,
        "authorization_rechecked_at_commit": True,
        "commit_after_revocation": False, "decision": "REJECT",
    },
    "CONCURRENCY_PARTIAL_WRITE_ROLLBACK": {
        "controlled_interleaving_proof": True, "rollback_complete": True,
        "partial_write_visible": False,
    },
    "CONCURRENCY_MULTI_PROCESS_SERVICE_INSTANCE": {
        "controlled_interleaving_proof": True, "process_count": 2,
        "service_instance_count": 2, "shared_invariant_guard": True,
    },
    "STATE_MACHINE_LEGAL_TRANSITION": {
        "transition_allowed": True, "validation_before_transition": True,
        "transition_applied": True, "decision": "APPLY",
    },
    "STATE_MACHINE_ILLEGAL_TRANSITION": {
        "transition_allowed": False, "transition_applied": False, "decision": "REJECT",
    },
    "STATE_MACHINE_TERMINAL_MUTATION": {
        "terminal_mutation_attempt": True, "transition_applied": False,
        "decision": "REJECT",
    },
    "STATE_MACHINE_STALE_TRANSITION": {
        "stale_transition": True, "transition_applied": False, "decision": "REJECT",
    },
    "STATE_MACHINE_DUPLICATE_TRANSITION": {
        "duplicate_transition": True, "duplicate_effect": False,
        "decision": "REJECT",
    },
    "STATE_MACHINE_FAILED_VALIDATION_BEFORE_TRANSITION": {
        "validation_before_transition": False, "transition_applied": False,
        "decision": "REJECT",
    },
    "STATE_MACHINE_ROLLBACK_SEMANTICS": {
        "rollback_complete": True, "partial_state_visible": False,
    },
    "EVIDENCE_SELF_ASSERTED_PASS": {
        "defect_detected": True, "self_asserted_rejected": True, "decision": "REJECT",
    },
    "EVIDENCE_NONZERO_EXIT_LABELED_PASS": {
        "defect_detected": True, "nonzero_exit_rejected": True, "decision": "REJECT",
    },
    "EVIDENCE_MISMATCHED_CANDIDATE_HASH": {
        "defect_detected": True, "candidate_mismatch_rejected": True, "decision": "REJECT",
    },
    "EVIDENCE_MISSING_VALIDATOR_IDENTITY": {
        "defect_detected": True, "missing_validator_rejected": True,
        "decision": "REJECT",
    },
    "EVIDENCE_UNSUPPORTED_EVIDENCE_TYPE": {
        "defect_detected": True, "unsupported_type_rejected": True, "decision": "REJECT",
    },
    "EVIDENCE_STALE_WORKFLOW_RUN": {
        "defect_detected": True, "stale_workflow_rejected": True, "decision": "REJECT",
    },
}

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


def _evidence(context: aq8.AssuranceContext, evidence_id: str, **changes: object) -> aq8.EvidenceRecord:
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


def _observation(
    context: aq8.AssuranceContext,
    case_id: str,
    *,
    facts: dict[str, Any] | None = None,
    evidence: tuple[aq8.EvidenceRecord, ...] | None = None,
    controlled_fixture: bool = True,
) -> aq8.HighRiskCaseObservation:
    selected_facts = dict(SAFE_FACTS[case_id])
    if facts:
        selected_facts.update(facts)
    return aq8.HighRiskCaseObservation(
        facts=selected_facts,
        evidence=evidence if evidence is not None else (
            _evidence(context, f"evidence:{case_id}"),
        ),
        controlled_fixture=controlled_fixture,
    )


def _observations(context: aq8.AssuranceContext) -> dict[str, dict[str, aq8.HighRiskCaseObservation]]:
    result: dict[str, dict[str, aq8.HighRiskCaseObservation]] = {}
    for pack in aq8.PACKS:
        result[pack] = {}
        for case_id in aq8.REQUIRED_CASES[pack]:
            facts = {"interleaving_trace": ("SYNC:before", "worker-a", "BARRIER:commit")} if pack == "CONCURRENCY" else {}
            result[pack][case_id] = _observation(context, case_id, facts=facts)
    return result


def _pack_decision(context: aq8.AssuranceContext) -> aq8.HighRiskAssuranceDecision:
    return aq8.run_all_high_risk_packs(context, _observations(context))


def _steward(context: aq8.AssuranceContext, **changes: object) -> aq8.StewardSystemIntentJudgment:
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


def _governor(context: aq8.AssuranceContext, **changes: object) -> aq8.GovernorProtectedObligationJudgment:
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


def _specialist(context: aq8.AssuranceContext, reviewer: str, **changes: object) -> SpecialistEvidence:
    values: dict[str, object] = {
        "reviewer": reviewer,
        "result": "PASS",
        "claim_scope": "candidate-system",
        "evidence_refs": (f"evidence:{reviewer.lower()}",),
        "candidate_sha": context.candidate_sha,
        "tree_sha": context.tree_sha,
    }
    values.update(changes)
    return SpecialistEvidence(**values)


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
    aq8.validate_aq8_contract(contract)
    assert contract["packs"] == list(aq8.PACKS)
    assert contract["required_covenant_scenarios"] == list(aq8.AQ8_REQUIRED_COVENANT_SCENARIOS)
    assert contract["required_aq7_regression_anchors"] == list(aq8.AQ8_AQ7_REGRESSION_ANCHORS)
    assert contract["authority"]["decision_grants_authority"] is False


def test_context_and_observation_serialization_is_strict() -> None:
    context = _context()
    restored = aq8.AssuranceContext.from_mapping(context.to_dict())
    assert restored == context
    observation = _observation(context, "SECURITY_UNKNOWN_CREDENTIAL")
    restored_observation = aq8.HighRiskCaseObservation.from_mapping(observation.to_dict())
    assert restored_observation == observation
    with pytest.raises(ValueError):
        aq8.AssuranceContext.from_mapping({**context.to_dict(), "unexpected": True})
    with pytest.raises(ValueError):
        aq8.HighRiskCaseObservation.from_mapping({"facts": {}, "unexpected": True})


def test_all_five_packs_and_every_required_case_pass() -> None:
    context = _context()
    decision = _pack_decision(context)
    assert decision.result == "PASS"
    assert decision.compliant is True
    assert decision.transition_owner == "ARBITER"
    assert decision.authority_granted is False
    assert tuple(pack.pack for pack in decision.packs) == aq8.PACKS
    for pack in decision.packs:
        assert pack.result == "PASS"
        assert pack.compliant is True
        assert pack.controlled_case_count == len(aq8.REQUIRED_CASES[pack.pack])
        assert pack.organic_case_count == 0
        assert tuple(case.case_id for case in pack.cases) == aq8.REQUIRED_CASES[pack.pack]
        assert all(case.disposition == "PASS" for case in pack.cases)
        assert all(case.authority_granted is False for case in pack.cases)
    assert decision.decision_digest
    assert decision.to_dict()["authority_granted"] is False


@pytest.mark.parametrize(("pack", "case_id"), ALL_CASES)
def test_each_required_case_is_executable(pack: str, case_id: str) -> None:
    context = _context()
    facts = {"interleaving_trace": ("SYNC:start", "worker-a", "BARRIER:end")} if pack == "CONCURRENCY" else {}
    result = aq8.evaluate_case(context, pack, case_id, _observation(context, case_id, facts=facts))
    assert result.disposition == "PASS"
    assert result.compliant is True
    assert result.controlled_fixture is True


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    (
        ({"candidate_sha": "c" * 40}, "AQ8_EVIDENCE_CANDIDATE_MISMATCH"),
        ({"tree_sha": "d" * 40}, "AQ8_EVIDENCE_TREE_MISMATCH"),
        ({"validator_identity": None}, "AQ8_EVIDENCE_VALIDATOR_MISSING"),
        ({"evidence_type": "UNSUPPORTED"}, "AQ8_EVIDENCE_TYPE_UNSUPPORTED"),
        ({"result": "FAIL", "exit_code": 1}, "AQ8_EVIDENCE_RESULT_NOT_PASS"),
        ({"workflow_run_id": "old-run", "freshness_ref": "old-run"}, "AQ8_EVIDENCE_STALE_WORKFLOW_RUN"),
        ({"durable": False}, "AQ8_EVIDENCE_NOT_DURABLE"),
        ({"retrievable": False}, "AQ8_EVIDENCE_NOT_RETRIEVABLE"),
        ({"independent": False}, "AQ8_EVIDENCE_NOT_INDEPENDENT"),
        ({"exit_code": 1}, "AQ8_EVIDENCE_PASS_NONZERO_EXIT"),
        ({"producer_role": "CALLER"}, "AQ8_EVIDENCE_CALLER_ASSERTED"),
    ),
)
def test_evidence_binding_fails_closed(changes: dict[str, object], expected_code: str) -> None:
    context = _context()
    record = _evidence(context, "evidence:bad", **changes)
    result = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(context, "SECURITY_UNKNOWN_CREDENTIAL", evidence=(record,)),
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert expected_code in result.reason_codes


def test_invalid_digest_and_duplicate_evidence_fail_closed() -> None:
    context = _context()
    invalid = _evidence(context, "evidence:invalid")
    object.__setattr__(invalid, "evidence_digest", "0" * 64)
    result = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(context, "SECURITY_UNKNOWN_CREDENTIAL", evidence=(invalid,)),
    )
    assert result.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_INVALID_DIGEST" in result.reason_codes

    duplicate = _evidence(context, "evidence:duplicate")
    duplicate_result = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(context, "SECURITY_UNKNOWN_CREDENTIAL", evidence=(duplicate, duplicate)),
    )
    assert duplicate_result.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_DUPLICATE_ID" in duplicate_result.reason_codes


def test_missing_evidence_and_missing_facts_wait() -> None:
    context = _context()
    no_evidence = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        aq8.HighRiskCaseObservation(facts=SAFE_FACTS["SECURITY_UNKNOWN_CREDENTIAL"], evidence=()),
    )
    assert no_evidence.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_MISSING" in no_evidence.reason_codes

    no_facts = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        aq8.HighRiskCaseObservation(
            facts={}, evidence=(_evidence(context, "evidence:missing-facts"),)
        ),
    )
    assert no_facts.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_REQUIRED_FACT_MISSING" in no_facts.reason_codes


def test_concurrency_requires_controlled_interleaving_and_aggregate_proof() -> None:
    context = _context()
    case_id = "CONCURRENCY_SAME_ROW_RACE"
    base = _observation(context, case_id, facts={"interleaving_trace": ("SYNC:start", "worker")})

    sequential = aq8.evaluate_case(
        context, "CONCURRENCY", case_id,
        _observation(context, case_id, facts={
            "interleaving_trace": ("worker-a", "worker-b"),
            "sequential_approximation": True,
        }),
    )
    uncontrolled = aq8.evaluate_case(
        context, "CONCURRENCY", case_id, replace(base, controlled_fixture=False)
    )
    missing_trace = aq8.evaluate_case(
        context, "CONCURRENCY", case_id,
        _observation(context, case_id, facts={}),
    )
    for result in (sequential, uncontrolled, missing_trace):
        assert result.disposition == "WAIT_FOR_EVIDENCE"
        assert "AQ8_CONTROLLED_INTERLEAVING_REQUIRED" in result.reason_codes

    aggregate = aq8.evaluate_case(
        context,
        "CONCURRENCY",
        "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
        _observation(context, "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE", facts={
            "interleaving_trace": ("SYNC:start", "worker-a", "BARRIER:end"),
            "aggregate_concurrency_proof": False,
        }),
    )
    assert aggregate.disposition == "REVISION_REQUIRED"
    assert "AQ8_AGGREGATE_PROOF_REQUIRED" in aggregate.reason_codes


def test_unknown_state_case_pack_and_pack_keys_fail_closed() -> None:
    context = _context()
    unknown_state = aq8.evaluate_case(
        context, "SECURITY", "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(context, "SECURITY_UNKNOWN_CREDENTIAL", facts={"state": "UNKNOWN"}),
    )
    assert unknown_state.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_STATE" in unknown_state.reason_codes

    raw_security = _observations(context)["SECURITY"]
    raw_security["NOT_A_CASE"] = _observation(context, "SECURITY_UNKNOWN_CREDENTIAL")
    pack_result = aq8.run_high_risk_pack(context, "SECURITY", raw_security)
    assert pack_result.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_CASE" in pack_result.failure_codes

    raw_all = _observations(context)
    raw_all["NOT_A_PACK"] = {}
    decision = aq8.run_all_high_risk_packs(context, raw_all)
    assert decision.result == "WAIT_FOR_EVIDENCE"
    assert "AQ8_UNKNOWN_PACK" in decision.failure_codes


def test_state_bound_covenant_is_current_and_non_authorizing() -> None:
    context = _context()
    result = _covenant(context)
    assert result.disposition == "PASS"
    assert result.basis.candidate_sha == context.candidate_sha
    assert result.basis.tree_sha == context.tree_sha
    assert result.to_dict()["authority_granted"] is False

    stale_owner = _steward(context, candidate_sha="c" * 40)
    stale = _covenant(context, steward=stale_owner)
    assert stale.disposition == "REVISION_REQUIRED"
    assert stale.reason_codes == ("SYSTEM_CONTRADICTION",)

    bad_pack = _pack_decision(_context(candidate_sha="c" * 40))
    not_current = _covenant(context, pack_decision=bad_pack)
    assert not_current.disposition == "REVISION_REQUIRED"
    assert not_current.reason_codes == ("SYSTEM_CONTRADICTION",)

    with pytest.raises(ValueError):
        replace(_pack_decision(context).packs[0].cases[0], authority_granted=True)


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
)
def test_covenant_conflict_scenarios(scenario: str, expected: str) -> None:
    context = _context()
    results = {
        "COV-01": _covenant(
            context,
            steward=_steward(context, prime_directive_alignment="CONFLICT"),
        ),
        "COV-02": _covenant(
            context,
            governor=_governor(context, decision="BLOCKED"),
        ),
        "COV-03": _covenant(
            context,
            steward=_steward(context, decision="REVISION_REQUIRED"),
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
            context,
            governor=_governor(context, decision="REVISION_REQUIRED"),
        ),
        "COV-15": _covenant(
            context,
            steward=_steward(context, project_goal_alignment="CONFLICT"),
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
    assert scenario.removesuffix("A") in aq8.AQ8_REQUIRED_COVENANT_SCENARIOS or scenario.removesuffix("B") in aq8.AQ8_REQUIRED_COVENANT_SCENARIOS
    assert results[scenario].disposition == expected


def test_adversarial_permutations_are_declared_and_executable() -> None:
    assert len(aq8.AQ8_ADVERSARIAL_PERMUTATIONS) == 14
    context = _context()

    assert _covenant(context, system_contradictions=("PRAI contradiction",)).disposition == "REVISION_REQUIRED"
    assert _covenant(context, reconciliation=object()).disposition == "WAIT_FOR_EVIDENCE"

    sequential = aq8.evaluate_case(
        context, "CONCURRENCY", "CONCURRENCY_SAME_ROW_RACE",
        _observation(
            context,
            "CONCURRENCY_SAME_ROW_RACE",
            facts={"interleaving_trace": ("worker-a", "worker-b"), "sequential_approximation": True},
        ),
    )
    assert sequential.disposition == "WAIT_FOR_EVIDENCE"

    with pytest.raises(ValueError, match="AQ8_UNKNOWN_CASE"):
        aq8.evaluate_case(
            context, "SECURITY", "UNKNOWN_CASE",
            _observation(context, "SECURITY_UNKNOWN_CREDENTIAL"),
        )
    with pytest.raises(ValueError):
        aq8.AssuranceContext.from_mapping({})

    decision = _pack_decision(context)
    with pytest.raises(ValueError):
        replace(decision, authority_granted=True)


def test_aq7_regression_anchors_execute_fail_closed() -> None:
    context = _context()

    aggregate = aq8.evaluate_case(
        context,
        "CONCURRENCY",
        "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
        _observation(context, "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE", facts={
            "interleaving_trace": ("SYNC:start", "worker-a", "BARRIER:commit"),
            "aggregate_concurrency_proof": False,
        }),
    )
    assert aggregate.disposition == "REVISION_REQUIRED"
    assert "AQ8_AGGREGATE_PROOF_REQUIRED" in aggregate.reason_codes

    privilege_mutation = aq8.evaluate_case(
        context,
        "CONCURRENCY",
        "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION",
        _observation(context, "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION", facts={
            "interleaving_trace": ("SYNC:request", "BARRIER:revocation", "worker-commit"),
            "authorization_rechecked_at_commit": False,
            "commit_after_revocation": True,
        }),
    )
    assert privilege_mutation.disposition == "REVISION_REQUIRED"

    missing_durable = aq8.evaluate_case(
        context,
        "SECURITY",
        "SECURITY_UNKNOWN_CREDENTIAL",
        _observation(
            context,
            "SECURITY_UNKNOWN_CREDENTIAL",
            evidence=(_evidence(context, "evidence:missing-durable", durable=False),),
        ),
    )
    assert missing_durable.disposition == "WAIT_FOR_EVIDENCE"
    assert "AQ8_EVIDENCE_NOT_DURABLE" in missing_durable.reason_codes


def test_authority_expansion_is_rejected_and_arbiter_owns_transition() -> None:
    context = _context()
    decision = _pack_decision(context)
    assert decision.transition_owner == "ARBITER"
    assert decision.authority_granted is False
    with pytest.raises(ValueError):
        replace(decision.packs[0], authority_granted=True)
    with pytest.raises(ValueError):
        replace(decision, authority_granted=True)