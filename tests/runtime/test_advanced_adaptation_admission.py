from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive.advanced_adaptation import (
    CANDIDATE_A5,
    CANDIDATE_CONCURRENCY,
    CANDIDATE_LEARNED,
    OVERALL_NO_PROMOTION,
    OVERALL_PROMOTION_CANDIDATE,
    evaluate_advanced_adaptation_admission,
)

ROOT = Path(__file__).resolve().parents[2]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _canonical_inputs():
    return {
        "awf_record": _load("machine/adaptive/awf-agentic-workflow-implementation.v1.json"),
        "a3_contract": _load("machine/adaptive/a3-shadow-learning-contract.v1.json"),
        "a5_record": _load("machine/adaptive/a5-shadow-topology-ranker-implementation.v1.json"),
        "b2_reconciliation": _load("machine/benchmarking/b2-5-confirmatory-reconciliation.v1.json"),
        "b5_synthesis": _load("machine/benchmarking/b5-final-evidence-synthesis.v1.json"),
        "execution_budget": _load("machine/governance/execution-budget.v1.json"),
    }


def _candidate(result, candidate_id):
    return next(item for item in result.candidates if item.candidate_id == candidate_id)


def test_n6_canonical_evidence_recomputes_static_no_promotion_record():
    result = evaluate_advanced_adaptation_admission(**_canonical_inputs())
    recorded = _load("machine/adaptive/advanced-adaptation-admission.v1.json")

    assert result.to_dict() == recorded
    assert result.overall_disposition == OVERALL_NO_PROMOTION
    assert all(not item.eligible for item in result.candidates)
    assert result.to_dict()["promotion_effective"] is False
    assert result.to_dict()["requires_separate_governed_transition"] is False


def test_n6_static_record_validates_against_schema():
    schema = _load("machine/schemas/advanced-adaptation-admission.v1.schema.json")
    recorded = _load("machine/adaptive/advanced-adaptation-admission.v1.json")
    Draft202012Validator(schema).validate(recorded)


def test_n6_a5_stays_blocked_by_confirmatory_negative_evidence():
    result = evaluate_advanced_adaptation_admission(**_canonical_inputs())
    a5 = _candidate(result, CANDIDATE_A5)

    assert a5.eligible is False
    assert a5.disposition == "BLOCKED_CONFIRMATORY_BENEFIT_NOT_ESTABLISHED"
    assert "CONFIRMATORY_BENEFIT_CRITERIA_NOT_ALL_PASSED" in a5.blockers
    assert "A5_TOPOLOGY_BENEFIT_NOT_ESTABLISHED" in a5.blockers
    assert "B5_FINAL_SYNTHESIS_DOES_NOT_ESTABLISH_A5_BENEFIT" in a5.blockers
    assert "EXISTING_PROMOTION_DECISION_IS_NOT_AUTHORIZED_CANDIDATE" in a5.blockers


def test_n6_learned_routing_stays_shadow_without_exact_predictive_benefit():
    result = evaluate_advanced_adaptation_admission(**_canonical_inputs())
    learned = _candidate(result, CANDIDATE_LEARNED)

    assert learned.eligible is False
    assert "NO_EXACT_TASKPROFILE_TOPOLOGY_BOUND_PREDICTIVE_BENEFIT_EVIDENCE" in learned.blockers
    assert "NO_MEASURED_LEARNED_ROUTING_BENEFIT_OVER_DETERMINISTIC_AWF" in learned.blockers


def test_n6_concurrency_ceiling_remains_one_and_not_promoted():
    inputs = _canonical_inputs()
    result = evaluate_advanced_adaptation_admission(**inputs)
    concurrency = _candidate(result, CANDIDATE_CONCURRENCY)

    assert inputs["execution_budget"]["defaults"]["max_parallel_specialists"] == 1
    assert concurrency.eligible is False
    assert "NO_CONFIRMATORY_PARALLEL_TOPOLOGY_BENEFIT_EVIDENCE" in concurrency.blockers
    assert "NO_SEPARATE_OEE_POLICY_AUTHORIZATION_FOR_CONCURRENCY_WIDENING" in concurrency.blockers
    assert result.to_dict()["invariants"]["oee_concurrency_widened"] is False


def test_n6_future_a5_evidence_can_only_create_non_effective_promotion_candidate():
    inputs = _canonical_inputs()
    b2 = deepcopy(inputs["b2_reconciliation"])
    b5 = deepcopy(inputs["b5_synthesis"])

    b2["primary_analysis"]["all_preregistered_benefit_criteria_pass"] = True
    b2["b2_terminal_conclusion"]["topology_benefit"] = "CONFIRMATORY_BENEFIT_ESTABLISHED"
    b5["separate_conclusions"]["a5_topology_benefit"] = "CONFIRMATORY_BENEFIT_ESTABLISHED"
    b5["promotion_decision"]["a5_execution_effective_promotion"] = "AUTHORIZED_CANDIDATE"

    inputs["b2_reconciliation"] = b2
    inputs["b5_synthesis"] = b5
    result = evaluate_advanced_adaptation_admission(**inputs)
    a5 = _candidate(result, CANDIDATE_A5)

    assert a5.eligible is True
    assert result.overall_disposition == OVERALL_PROMOTION_CANDIDATE
    payload = result.to_dict()
    assert payload["promotion_effective"] is False
    assert payload["requires_separate_governed_transition"] is True
    assert payload["invariants"]["a5_ranking_controls_execution"] is False
    assert payload["invariants"]["runtime_executor_attachment"] is False
    assert payload["invariants"]["conductor_dispatch_mutation"] is False


def test_n6_partial_evidence_cannot_rescue_a5_promotion():
    inputs = _canonical_inputs()
    b2 = deepcopy(inputs["b2_reconciliation"])
    b2["primary_analysis"]["all_preregistered_benefit_criteria_pass"] = True
    b2["b2_terminal_conclusion"]["topology_benefit"] = "CONFIRMATORY_BENEFIT_ESTABLISHED"
    inputs["b2_reconciliation"] = b2

    result = evaluate_advanced_adaptation_admission(**inputs)
    a5 = _candidate(result, CANDIDATE_A5)

    assert a5.eligible is False
    assert "B5_FINAL_SYNTHESIS_DOES_NOT_ESTABLISH_A5_BENEFIT" in a5.blockers
    assert "EXISTING_PROMOTION_DECISION_IS_NOT_AUTHORIZED_CANDIDATE" in a5.blockers


def test_n6_fails_closed_on_wrong_canonical_contract_identity():
    inputs = _canonical_inputs()
    inputs["b2_reconciliation"] = {
        **inputs["b2_reconciliation"],
        "schema_version": "wrong",
    }

    with pytest.raises(ValueError, match="canonical N6 evidence contract"):
        evaluate_advanced_adaptation_admission(**inputs)


def test_n6_detects_unexpected_a3_or_a5_execution_state():
    inputs = _canonical_inputs()
    a3 = deepcopy(inputs["a3_contract"])
    a5 = deepcopy(inputs["a5_record"])
    a3["isolation"]["shadow_recommendation_influences_execution"] = True
    a5["decision_boundary"]["runtime_executor_attachment"] = True
    inputs["a3_contract"] = a3
    inputs["a5_record"] = a5

    result = evaluate_advanced_adaptation_admission(**inputs)
    learned = _candidate(result, CANDIDATE_LEARNED)
    a5_decision = _candidate(result, CANDIDATE_A5)

    assert "A3_SHADOW_EXECUTION_ISOLATION_NOT_PRESERVED" in learned.blockers
    assert "A5_RUNTIME_EXECUTOR_ATTACHMENT_UNEXPECTED" in a5_decision.blockers
    assert result.to_dict()["promotion_effective"] is False
