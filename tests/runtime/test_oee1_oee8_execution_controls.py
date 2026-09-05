from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.domain.orchestration.execution_efficiency import DecisiveStopSignal
from orchestra_runtime.domain.orchestration.execution_efficiency_runtime import (
    CI_IDLE_NO_REASONING,
    CI_READ_ONCE,
    ContextEvidence,
    EfficiencyPhaseResult,
    EvidenceCacheEntry,
    PhaseContextPack,
    SpecialistInvocationPlan,
    build_owner_first_plan,
    evaluate_decisive_progression,
    evaluate_evidence_reuse,
    evaluate_program_resume_gate,
    next_search_stage,
    plan_ci_activity,
    require_active_phase,
    validate_validation_request,
)


def test_oee1_owner_first_plan_keeps_one_active_specialist() -> None:
    plan = build_owner_first_plan("cloak")
    assert plan.active_specialists == ("cloak",)
    assert plan.planned_specialists == ("cloak",)


def test_oee1_supporting_specialist_requires_explicit_reason_and_evidence() -> None:
    with pytest.raises(ValueError, match="explicit cross-domain or adversarial"):
        build_owner_first_plan("cloak", ("clockwork",))

    with pytest.raises(ValueError, match="expansion evidence"):
        build_owner_first_plan(
            "cloak",
            ("clockwork",),
            expansion_reason="CROSS_DOMAIN_AUTHORITY",
        )

    plan = build_owner_first_plan(
        "cloak",
        ("clockwork", "overseer"),
        expansion_reason="CROSS_DOMAIN_AUTHORITY",
        expansion_evidence_refs=("handoff.boundary",),
    )
    assert plan.active_specialists == ("cloak",)
    assert plan.planned_specialists == ("cloak", "clockwork", "overseer")


def test_oee1_retry_budget_is_exactly_zero_or_one() -> None:
    build_owner_first_plan("cloak", retry_counts={"cloak": 1})

    with pytest.raises(ValueError, match="integer 0 or 1"):
        build_owner_first_plan("cloak", retry_counts={"cloak": 2})

    with pytest.raises(ValueError, match="integer 0 or 1"):
        build_owner_first_plan("cloak", retry_counts={"cloak": True})

    with pytest.raises(ValueError, match="only planned specialists"):
        build_owner_first_plan("cloak", retry_counts={"clockwork": 1})


def test_oee1_rejects_duplicate_or_unused_expansion_metadata() -> None:
    with pytest.raises(ValueError, match="must not be duplicated"):
        build_owner_first_plan(
            "cloak",
            ("cloak",),
            expansion_reason="CROSS_DOMAIN_AUTHORITY",
            expansion_evidence_refs=("boundary",),
        )

    with pytest.raises(ValueError, match="unused expansion metadata"):
        build_owner_first_plan(
            "cloak",
            expansion_reason="ADVERSARIAL_REVIEW_REQUIRED",
        )

    plan = SpecialistInvocationPlan(
        owner_specialist="cloak",
        supporting_specialists=("clockwork",),
        retry_counts=(("cloak", 0), ("cloak", 1)),
        expansion_reason="CROSS_DOMAIN_AUTHORITY",
        expansion_evidence_refs=("boundary",),
    )
    with pytest.raises(ValueError, match="keys must be unique"):
        plan.validate()


def test_oee2_decisive_stop_blocks_all_downstream_execution() -> None:
    signal = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=True,
        stop_required=True,
        downstream_execution_allowed=False,
        reason="responsive intent contradicts itself below 1024px",
        evidence_refs=("machine/ui/ui-fidelity-handoff.v1.json",),
    )
    decision = evaluate_decisive_progression(signal)
    assert decision.allowed is False
    assert decision.downstream_execution_allowed is False
    assert decision.reason_code == "DECISIVE_EVIDENCE_STOP"


def test_oee2_non_decisive_evidence_allows_progression() -> None:
    signal = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=False,
        stop_required=False,
        downstream_execution_allowed=True,
        reason="review still collecting evidence",
        evidence_refs=("evidence.partial",),
    )
    decision = evaluate_decisive_progression(signal)
    assert decision.allowed is True
    assert decision.reason_code == "NO_DECISIVE_STOP"


def test_oee3_evidence_reuse_requires_exact_source_revision_and_identity() -> None:
    entry = EvidenceCacheEntry(
        evidence_id="uief4.handoff",
        owner_ref="cloak",
        source_revision="1927d3f0672198ddc67cc32624d38c2b14c434e8",
        source_identity="sha256:abc",
        content_identity="sha256:def",
    )
    assert evaluate_evidence_reuse(
        entry,
        source_revision=entry.source_revision,
        source_identity=entry.source_identity,
    ).reusable is True
    assert evaluate_evidence_reuse(
        entry,
        source_revision="changed",
        source_identity=entry.source_identity,
    ).reason_code == "SOURCE_REVISION_CHANGED"
    assert evaluate_evidence_reuse(
        entry,
        source_revision=entry.source_revision,
        source_identity="sha256:changed",
    ).reason_code == "SOURCE_IDENTITY_CHANGED"


def test_oee3_search_escalates_one_level_only_when_needed() -> None:
    assert next_search_stage("EXACT_PATH", current_stage_insufficient=False) == "EXACT_PATH"
    assert next_search_stage("EXACT_PATH", current_stage_insufficient=True) == "EXACT_SYMBOL"
    assert next_search_stage("EXACT_SYMBOL", current_stage_insufficient=True) == "BOUNDED_DIRECTORY"
    assert next_search_stage("EXTERNAL", current_stage_insufficient=True) == "EXTERNAL"

    with pytest.raises(ValueError, match="unknown search stage"):
        next_search_stage("EVERYWHERE", current_stage_insufficient=True)
    with pytest.raises(ValueError, match="must be a boolean"):
        next_search_stage("EXACT_PATH", current_stage_insufficient=1)


def test_oee4_expensive_validation_requires_stable_candidate_and_prerequisites() -> None:
    validate_validation_request("SYNTAX_SCHEMA", (), candidate_stable=False)
    validate_validation_request(
        "SUBSYSTEM",
        ("SYNTAX_SCHEMA", "DIRECT_TESTS"),
        candidate_stable=False,
    )
    validate_validation_request(
        "REPOSITORY_QUALIFICATION",
        ("SYNTAX_SCHEMA", "DIRECT_TESTS", "SUBSYSTEM"),
        candidate_stable=True,
    )

    with pytest.raises(ValueError, match="stable candidate"):
        validate_validation_request(
            "REPOSITORY_QUALIFICATION",
            ("SYNTAX_SCHEMA", "DIRECT_TESTS", "SUBSYSTEM"),
            candidate_stable=False,
        )

    with pytest.raises(ValueError, match="skip prerequisites"):
        validate_validation_request(
            "PROTECTED_GATES",
            ("SYNTAX_SCHEMA",),
            candidate_stable=True,
        )


def test_oee4_validation_request_rejects_unknown_or_malformed_state() -> None:
    with pytest.raises(ValueError, match="unknown validation stage"):
        validate_validation_request("ALL_THE_TESTS", (), candidate_stable=True)
    with pytest.raises(ValueError, match="unknown validation stage"):
        validate_validation_request(
            "DIRECT_TESTS",
            ("UNKNOWN",),
            candidate_stable=True,
        )
    with pytest.raises(ValueError, match="must be a boolean"):
        validate_validation_request("SYNTAX_SCHEMA", (), candidate_stable=1)


def test_oee5_ci_wait_is_idle_until_state_change_or_decision_point() -> None:
    idle = plan_ci_activity(ci_state_changed=False, decision_point=False)
    assert idle.action == CI_IDLE_NO_REASONING
    assert idle.active_model_reasoning_allowed is False
    assert idle.poll_required is False

    changed = plan_ci_activity(ci_state_changed=True, decision_point=False)
    assert changed.action == CI_READ_ONCE
    assert changed.active_model_reasoning_allowed is True
    assert changed.poll_required is True

    decision = plan_ci_activity(ci_state_changed=False, decision_point=True)
    assert decision.action == CI_READ_ONCE

    with pytest.raises(ValueError, match="must be booleans"):
        plan_ci_activity(ci_state_changed="yes", decision_point=False)


def _context_pack() -> PhaseContextPack:
    return PhaseContextPack(
        phase_id="OEE-6",
        owner_specialist="conductor",
        source_revision="1927d3f0672198ddc67cc32624d38c2b14c434e8",
        evidence=(
            ContextEvidence(
                ref="machine/governance/execution-budget.v1.json",
                source_identity="blob:budget",
                required_for=("conductor", "all"),
            ),
            ContextEvidence(
                ref="docs/governance/OEE_EXECUTION_EFFICIENCY_V1.md",
                source_identity="blob:guide",
                required_for=("conductor",),
            ),
            ContextEvidence(
                ref="tests/runtime/test_oee1_oee8_execution_controls.py",
                source_identity="blob:tests",
                required_for=("overseer",),
            ),
        ),
        excluded_refs=("docs/unrelated/history.md",),
    )


def test_oee6_phase_context_pack_is_specialist_scoped_and_exact_source_bound() -> None:
    pack = _context_pack()
    pack.validate()
    assert pack.refs_for("conductor") == (
        "machine/governance/execution-budget.v1.json",
        "docs/governance/OEE_EXECUTION_EFFICIENCY_V1.md",
    )
    assert pack.refs_for("overseer") == (
        "machine/governance/execution-budget.v1.json",
        "tests/runtime/test_oee1_oee8_execution_controls.py",
    )


def test_oee6_context_pack_rejects_duplicates_exclusions_and_empty_sources() -> None:
    pack = _context_pack()
    with pytest.raises(ValueError, match="evidence refs must be unique"):
        replace(pack, evidence=pack.evidence + (pack.evidence[0],)).validate()
    with pytest.raises(ValueError, match="cannot also be excluded"):
        replace(
            pack,
            excluded_refs=("machine/governance/execution-budget.v1.json",),
        ).validate()
    with pytest.raises(ValueError, match="source_identity must be non-empty"):
        replace(
            pack,
            evidence=(replace(pack.evidence[0], source_identity=""),),
        ).validate()


def test_oee6_autonomous_campaign_loads_one_phase_at_a_time() -> None:
    require_active_phase("OEE-6", "OEE-6")
    with pytest.raises(ValueError, match="only the active phase"):
        require_active_phase("OEE-6", "OEE-7")


def test_oee7_replay_reaches_same_blocker_with_less_specialist_fanout_and_no_ci_watch() -> None:
    historical_unique_specialists = {"clockwork", "overseer", "cloak", "arbiter"}
    historical_disposition = "BLOCKED_PRE_IMPLEMENTATION_REVIEW"

    plan = build_owner_first_plan("cloak")
    stop = evaluate_decisive_progression(
        DecisiveStopSignal(
            owner="cloak",
            evidence_sufficient=True,
            stop_required=True,
            downstream_execution_allowed=False,
            reason="responsive intent contradiction is authoritative upstream blocker",
            evidence_refs=("machine/ui/ui-fidelity-handoff.v1.json",),
        )
    )
    ci = plan_ci_activity(ci_state_changed=False, decision_point=False)
    replay_disposition = "BLOCKED_PRE_IMPLEMENTATION_REVIEW" if not stop.allowed else "CONTINUE"

    assert replay_disposition == historical_disposition
    assert len(set(plan.active_specialists)) < len(historical_unique_specialists)
    assert stop.downstream_execution_allowed is False
    assert ci.action == CI_IDLE_NO_REASONING
    assert ci.poll_required is False


def _phase_result(index: int, passed: bool = True) -> EfficiencyPhaseResult:
    return EfficiencyPhaseResult(
        phase_id=f"OEE-{index}",
        passed=passed,
        evidence_refs=(f"evidence.oee{index}",) if passed else (),
    )


def test_oee8_resume_gate_requires_exact_ordered_oee0_through_oee7_evidence() -> None:
    results = tuple(_phase_result(index) for index in range(8))
    assert evaluate_program_resume_gate(results) is True

    failed = list(results)
    failed[3] = _phase_result(3, passed=False)
    assert evaluate_program_resume_gate(failed) is False

    with pytest.raises(ValueError, match="exact ordered"):
        evaluate_program_resume_gate(results[:-1])


def test_oee8_passed_phase_cannot_claim_success_without_evidence() -> None:
    result = EfficiencyPhaseResult("OEE-7", True, ())
    with pytest.raises(ValueError, match="requires evidence"):
        result.validate()
