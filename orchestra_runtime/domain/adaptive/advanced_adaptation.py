from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_VERSION = "orchestra.advanced-adaptation-admission.v1"
OVERALL_NO_PROMOTION = "COMPLETE_NO_PROMOTION_EVIDENCE_INSUFFICIENT"
OVERALL_PROMOTION_CANDIDATE = "COMPLETE_PROMOTION_CANDIDATE_REQUIRES_SEPARATE_GOVERNED_TRANSITION"

CANDIDATE_A5 = "A5_EXECUTION_EFFECTIVE_TOPOLOGY_SELECTION"
CANDIDATE_LEARNED = "LEARNED_ROUTING_RECOMMENDATIONS"
CANDIDATE_CONCURRENCY = "OEE_CONCURRENCY_WIDENING"


@dataclass(frozen=True, slots=True)
class PromotionCandidateDecision:
    candidate_id: str
    eligible: bool
    disposition: str
    blockers: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "eligible": self.eligible,
            "disposition": self.disposition,
            "blockers": list(self.blockers),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class AdvancedAdaptationAdmission:
    overall_disposition: str
    candidates: tuple[PromotionCandidateDecision, ...]
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "overall_disposition": self.overall_disposition,
            "promotion_effective": False,
            "requires_separate_governed_transition": any(
                candidate.eligible for candidate in self.candidates
            ),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "invariants": {
                "runtime_executor_attachment": False,
                "conductor_dispatch_mutation": False,
                "specialist_authority_expansion": False,
                "learned_routing_controls_execution": False,
                "a5_ranking_controls_execution": False,
                "oee_concurrency_widened": False,
            },
        }


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def _exact(value: object, expected: object, field_name: str) -> None:
    if value != expected:
        raise ValueError(f"{field_name} does not match the canonical N6 evidence contract")


def evaluate_advanced_adaptation_admission(
    *,
    awf_record: Mapping[str, Any],
    a3_contract: Mapping[str, Any],
    a5_record: Mapping[str, Any],
    b2_reconciliation: Mapping[str, Any],
    b5_synthesis: Mapping[str, Any],
    execution_budget: Mapping[str, Any],
) -> AdvancedAdaptationAdmission:
    """Evaluate promotion admission without attaching any candidate to execution."""

    awf = _mapping(awf_record, "awf_record")
    a3 = _mapping(a3_contract, "a3_contract")
    a5 = _mapping(a5_record, "a5_record")
    b2 = _mapping(b2_reconciliation, "b2_reconciliation")
    b5 = _mapping(b5_synthesis, "b5_synthesis")
    budget = _mapping(execution_budget, "execution_budget")

    _exact(awf.get("program"), "AWF_ADAPTIVE_AGENTIC_WORKFLOW", "awf_record.program")
    _exact(
        a3.get("schema_version"),
        "orchestra.adaptive-shadow-learning-contract.v1",
        "a3_contract.schema_version",
    )
    _exact(
        b2.get("schema_version"),
        "orchestra.b2-5-confirmatory-reconciliation.v1",
        "b2_reconciliation.schema_version",
    )
    _exact(
        b5.get("schema_version"),
        "orchestra.b5-final-evidence-synthesis.v1",
        "b5_synthesis.schema_version",
    )
    _exact(
        budget.get("schema_version"),
        "orchestra.execution-budget.v1",
        "execution_budget.schema_version",
    )

    a5_blockers: list[str] = []
    primary = _mapping(b2.get("primary_analysis"), "b2_reconciliation.primary_analysis")
    terminal = _mapping(b2.get("b2_terminal_conclusion"), "b2_reconciliation.b2_terminal_conclusion")
    b5_conclusions = _mapping(b5.get("separate_conclusions"), "b5_synthesis.separate_conclusions")
    b5_promotion = _mapping(b5.get("promotion_decision"), "b5_synthesis.promotion_decision")

    if primary.get("all_preregistered_benefit_criteria_pass") is not True:
        a5_blockers.append("CONFIRMATORY_BENEFIT_CRITERIA_NOT_ALL_PASSED")
    if terminal.get("topology_benefit") != "CONFIRMATORY_BENEFIT_ESTABLISHED":
        a5_blockers.append("A5_TOPOLOGY_BENEFIT_NOT_ESTABLISHED")
    if b5_conclusions.get("a5_topology_benefit") != "CONFIRMATORY_BENEFIT_ESTABLISHED":
        a5_blockers.append("B5_FINAL_SYNTHESIS_DOES_NOT_ESTABLISH_A5_BENEFIT")
    if terminal.get("quality_regression_detected") is not False:
        a5_blockers.append("QUALITY_GUARDRAIL_NOT_CLEAN")
    if primary.get("all_context_values_recomputed") is not True:
        a5_blockers.append("CONTEXT_TRANSFER_EVIDENCE_NOT_RECOMPUTABLE")
    if b5_promotion.get("a5_execution_effective_promotion") != "AUTHORIZED_CANDIDATE":
        a5_blockers.append("EXISTING_PROMOTION_DECISION_IS_NOT_AUTHORIZED_CANDIDATE")

    a5_exit = _mapping(a5.get("a5_exit_evaluation"), "a5_record.a5_exit_evaluation")
    a5_boundary = _mapping(a5.get("decision_boundary"), "a5_record.decision_boundary")
    if a5_exit.get("execution_effective_promotion") != "DEFERRED_NOT_PROMOTED":
        a5_blockers.append("A5_SHADOW_PROMOTION_STATE_UNEXPECTED")
    if a5_boundary.get("topology_effective") is not False:
        a5_blockers.append("A5_SHADOW_TOPOLOGY_EFFECTIVE_STATE_UNEXPECTED")
    if a5_boundary.get("runtime_executor_attachment") is not False:
        a5_blockers.append("A5_RUNTIME_EXECUTOR_ATTACHMENT_UNEXPECTED")

    a5_decision = PromotionCandidateDecision(
        candidate_id=CANDIDATE_A5,
        eligible=not a5_blockers,
        disposition=(
            "PROMOTION_CANDIDATE_REQUIRES_SEPARATE_GOVERNED_TRANSITION"
            if not a5_blockers
            else "BLOCKED_CONFIRMATORY_BENEFIT_NOT_ESTABLISHED"
        ),
        blockers=tuple(a5_blockers),
        evidence_refs=(
            "machine/adaptive/a5-shadow-topology-ranker-implementation.v1.json",
            "machine/benchmarking/b2-5-confirmatory-reconciliation.v1.json",
            "machine/benchmarking/b5-final-evidence-synthesis.v1.json",
        ),
    )

    learned_blockers: list[str] = []
    a3_isolation = _mapping(a3.get("isolation"), "a3_contract.isolation")
    a3_promotion = _mapping(a3.get("promotion_boundary"), "a3_contract.promotion_boundary")
    a3_future = _mapping(a3.get("future_boundary"), "a3_contract.future_boundary")
    if a3_isolation.get("shadow_recommendation_influences_execution") is not False:
        learned_blockers.append("A3_SHADOW_EXECUTION_ISOLATION_NOT_PRESERVED")
    if a3_promotion.get("promotion_bridge") not in {
        "NONE",
        "NOT_IMPLEMENTED_OR_AUTHORIZED_IN_A3",
    }:
        learned_blockers.append("A3_PROMOTION_BRIDGE_STATE_UNEXPECTED")
    if a3_promotion.get("automatic_promotion") is not False:
        learned_blockers.append("A3_AUTOMATIC_PROMOTION_NOT_DISABLED")
    if a3_future.get("a7_route_ranking_policy_promotion") != "NOT_AUTHORIZED":
        learned_blockers.append("A7_ROUTE_RANKING_BOUNDARY_NOT_CLOSED")
    learned_blockers.extend(
        (
            "NO_EXACT_TASKPROFILE_TOPOLOGY_BOUND_PREDICTIVE_BENEFIT_EVIDENCE",
            "NO_MEASURED_LEARNED_ROUTING_BENEFIT_OVER_DETERMINISTIC_AWF",
        )
    )
    learned_decision = PromotionCandidateDecision(
        candidate_id=CANDIDATE_LEARNED,
        eligible=False,
        disposition="BLOCKED_NO_EXACT_PREDICTIVE_BENEFIT_EVIDENCE",
        blockers=tuple(dict.fromkeys(learned_blockers)),
        evidence_refs=(
            "machine/adaptive/a3-shadow-learning-contract.v1.json",
            "machine/adaptive/awf-agentic-workflow-implementation.v1.json",
        ),
    )

    concurrency_blockers: list[str] = []
    defaults = _mapping(budget.get("defaults"), "execution_budget.defaults")
    if defaults.get("max_parallel_specialists") != 1:
        concurrency_blockers.append("CURRENT_OEE_PARALLEL_CEILING_IS_NOT_CANONICAL_ONE")
    concurrency_blockers.extend(
        (
            "NO_CONFIRMATORY_PARALLEL_TOPOLOGY_BENEFIT_EVIDENCE",
            "NO_SEPARATE_OEE_POLICY_AUTHORIZATION_FOR_CONCURRENCY_WIDENING",
        )
    )
    concurrency_decision = PromotionCandidateDecision(
        candidate_id=CANDIDATE_CONCURRENCY,
        eligible=False,
        disposition="BLOCKED_NO_PARALLEL_BENEFIT_OR_POLICY_AUTHORIZATION",
        blockers=tuple(dict.fromkeys(concurrency_blockers)),
        evidence_refs=(
            "machine/governance/execution-budget.v1.json",
            "machine/benchmarking/b5-final-evidence-synthesis.v1.json",
        ),
    )

    candidates = (a5_decision, learned_decision, concurrency_decision)
    overall = (
        OVERALL_PROMOTION_CANDIDATE
        if any(candidate.eligible for candidate in candidates)
        else OVERALL_NO_PROMOTION
    )
    return AdvancedAdaptationAdmission(overall_disposition=overall, candidates=candidates)


__all__ = [
    "AdvancedAdaptationAdmission",
    "CANDIDATE_A5",
    "CANDIDATE_CONCURRENCY",
    "CANDIDATE_LEARNED",
    "OVERALL_NO_PROMOTION",
    "OVERALL_PROMOTION_CANDIDATE",
    "PromotionCandidateDecision",
    "SCHEMA_VERSION",
    "evaluate_advanced_adaptation_admission",
]
