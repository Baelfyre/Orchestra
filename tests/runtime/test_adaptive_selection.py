from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.selection import (
    REQUIRED_ELIGIBILITY_FILTERS,
    SelectionCandidate,
    SelectionEligibilityEnvelope,
    SelectionEvidenceItem,
    SelectionEvidencePacket,
    SelectionMeasurement,
    build_evidence_packet,
    build_eligibility_envelope,
    qualify_a3_candidate,
    qualify_a3_comparison,
    rank_shadow_selection,
)
from orchestra_runtime.adaptive.shadow import (
    build_shadow_comparison,
    build_shadow_signal,
    learn_shadow_candidates,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"
ADAPTIVE_MACHINE = ROOT / "machine" / "adaptive"
USER = "selection-user"
PROJECT = "Baelfyre/Orchestra"
SPECIALIST = "clockwork"
T0 = "2026-08-18T00:00:00Z"
T1 = "2026-08-18T00:01:00Z"
T2 = "2026-08-18T00:02:00Z"
T3 = "2026-08-18T00:03:00Z"
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64


def candidate(
    candidate_id: str,
    option_key: str,
    *,
    selection_type: str = "SPECIALIST_STRATEGY",
    owner: str | None = SPECIALIST,
    provider_id: str | None = None,
) -> SelectionCandidate:
    return SelectionCandidate(
        candidate_id=candidate_id,
        option_kind=selection_type,
        option_key=option_key,
        owner_specialist_slug=owner,
        provider_id=provider_id,
        eligibility_evidence_refs=(f"eligibility:{candidate_id}",),
    )


def envelope(
    *,
    selection_type: str = "SPECIALIST_STRATEGY",
    candidates: tuple[SelectionCandidate, ...] | None = None,
    explicit_current_constraint_ref: str | None = None,
    user_key: str = USER,
    project_key: str = PROJECT,
    specialist: str = SPECIALIST,
    created_at: str = T0,
) -> SelectionEligibilityEnvelope:
    if candidates is None:
        candidates = (
            candidate("default", "architecture-first", selection_type=selection_type),
            candidate("adaptive", "threat-first", selection_type=selection_type),
        )
    return build_eligibility_envelope(
        selection_type=selection_type,
        created_at=created_at,
        user_key=user_key,
        project_key=project_key,
        command_name="architecture",
        routed_specialist_slug=specialist,
        deterministic_route_ref="machine:routing:architecture",
        filter_evidence_refs=("authority:ok", "capability:ok", "governance:ok"),
        candidates=candidates,
        explicit_current_constraint_ref=explicit_current_constraint_ref,
    )


def direct_item(
    *,
    evidence_id: str,
    digest: str,
    option_id: str,
    selection_type: str = "SPECIALIST_STRATEGY",
    source_kind: str = "GOVERNED_SELECTION_OUTCOME",
    direction: str = "POSITIVE",
    measurement: SelectionMeasurement | None = None,
) -> SelectionEvidenceItem:
    return SelectionEvidenceItem(
        evidence_id=evidence_id,
        source_kind=source_kind,
        source_ref=f"governed:{evidence_id}",
        source_digest=digest,
        option_id=option_id,
        selection_type=selection_type,
        qualification_status="QUALIFIED",
        reason_code="EXACT_OPTION_BOUND_GOVERNED_EVIDENCE",
        direction=direction,
        measurement=measurement,
    )


def packet(
    env: SelectionEligibilityEnvelope,
    items: tuple[SelectionEvidenceItem, ...] = (),
    *,
    collected_at: str = T1,
) -> SelectionEvidencePacket:
    return build_evidence_packet(env, collected_at=collected_at, items=items)


def strategy_scope(
    *,
    user_key: str = USER,
    project_key: str = PROJECT,
    specialist: str | None = None,
) -> AdaptiveScope:
    return AdaptiveScope(
        scope_type="project" if specialist is None else "specialist",
        user_key=user_key,
        project_key=project_key,
        specialist_slug=specialist,
    )


def strategy_candidate(
    *,
    value: str = "threat-first",
    scope: AdaptiveScope | None = None,
):
    scope = scope or strategy_scope()
    first = build_shadow_signal(
        scope=scope,
        signal_type="SPECIALIST_STRATEGY_ACCEPTED",
        subject_key="strategy.review_order",
        observed_value=value,
        source_kind="STRATEGY_DECISION_EVIDENCE",
        source_ref="strategy:one",
        source_digest=D0,
        observed_at=T0,
    )
    second = build_shadow_signal(
        scope=scope,
        signal_type="SPECIALIST_STRATEGY_ACCEPTED",
        subject_key="strategy.review_order",
        observed_value=value,
        source_kind="STRATEGY_DECISION_EVIDENCE",
        source_ref="strategy:two",
        source_digest=D1,
        observed_at=T1,
    )
    return learn_shadow_candidates((first, second))[0]



def test_machine_implementation_record_preserves_shadow_only_boundary():
    record = json.loads((ADAPTIVE_MACHINE / "a4-shadow-ranker-implementation.v1.json").read_text(encoding="utf-8"))
    assert record["phase"] == "A4.1_SHADOW_RANKER_AND_EVIDENCE_QUALIFICATION"
    assert record["scorer"]["version"] == "orchestra.adaptive-selection-scorer.v1"
    assert record["eligibility"]["adaptive_candidate_creation"] is False
    assert record["eligibility"]["adaptive_candidate_restoration"] is False
    assert record["decision_boundary"]["execution_controlled_by"] == "DETERMINISTIC_ORCHESTRA"
    assert record["decision_boundary"]["selection_effective"] is False
    assert record["decision_boundary"]["shadow_influenced_execution"] is False
    assert record["decision_boundary"]["provider_or_worker_eligibility_expanded"] is False
    assert record["future_boundary"]["a5_behavior"] == "NOT_INTRODUCED"

def test_a4_records_validate_against_frozen_machine_schemas():
    env = envelope()
    items = (
        direct_item(evidence_id="one", digest=D2, option_id="adaptive"),
        direct_item(evidence_id="two", digest=D3, option_id="adaptive"),
    )
    evidence = packet(env, items)
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "SHADOW_RANKED"

    for instance, schema_name in (
        (env.to_dict(), "adaptive-selection-eligibility-envelope.schema.json"),
        (evidence.to_dict(), "adaptive-selection-evidence.schema.json"),
        (decision.to_dict(), "adaptive-selection-decision.schema.json"),
    ):
        schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def test_eligibility_requires_every_deterministic_filter_and_exact_owner():
    filters = {key: True for key in REQUIRED_ELIGIBILITY_FILTERS}
    filters["authority"] = False
    with pytest.raises(ValueError, match="filters"):
        envelope().__class__(
            envelope_id="invalid",
            selection_type="SPECIALIST_STRATEGY",
            created_at=T0,
            user_key=USER,
            project_key=PROJECT,
            command_name="architecture",
            routed_specialist_slug=SPECIALIST,
            deterministic_route_ref="machine:routing:architecture",
            filter_evidence_refs=("filters:checked",),
            candidates=(candidate("one", "threat-first"),),
            filters_applied=filters,
        )

    with pytest.raises(ValueError, match="ownership"):
        envelope(
            candidates=(
                candidate("wrong-owner", "threat-first", owner="the-governor"),
            )
        )


def test_candidate_kind_must_match_selection_type():
    with pytest.raises(ValueError, match="option_kind"):
        envelope(
            selection_type="MODEL",
            candidates=(candidate("strategy", "threat-first", selection_type="SPECIALIST_STRATEGY"),),
        )


def test_actual_deterministic_choice_must_be_in_immutable_eligible_set():
    env = envelope()
    decision = rank_shadow_selection(
        env,
        packet(env),
        actual_deterministic_choice_id="filtered-out",
        evaluated_at=T2,
    )
    assert decision.disposition == "INVALID_ELIGIBILITY"
    assert decision.shadow_recommendation_id is None
    assert decision.ranked_candidate_ids == env.candidate_ids


def test_explicit_current_constraint_dominates_adaptive_score():
    env = envelope(explicit_current_constraint_ref="user:current:constraint")
    evidence = packet(
        env,
        (
            direct_item(evidence_id="one", digest=D2, option_id="adaptive"),
            direct_item(evidence_id="two", digest=D3, option_id="adaptive"),
        ),
    )
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "EXPLICIT_CONSTRAINT"
    assert decision.ranked_candidate_ids == env.candidate_ids
    assert decision.shadow_recommendation_id is None


def test_explicit_scoped_preference_precedes_adaptive_evidence_but_cannot_restore_filtered_option():
    env = envelope()
    evidence = packet(
        env,
        (
            direct_item(evidence_id="one", digest=D2, option_id="default"),
            direct_item(evidence_id="two", digest=D3, option_id="default"),
        ),
    )
    preferred = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        explicit_scoped_preference_candidate_id="adaptive",
        evaluated_at=T2,
    )
    assert preferred.disposition == "SHADOW_RANKED"
    assert preferred.shadow_recommendation_id == "adaptive"
    assert preferred.ranked_candidate_ids[0] == "adaptive"

    filtered = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        explicit_scoped_preference_candidate_id="not-eligible",
        evaluated_at=T2,
    )
    assert filtered.disposition == "DETERMINISTIC_FALLBACK"
    assert filtered.shadow_recommendation_id is None
    assert filtered.ranked_candidate_ids == env.candidate_ids


def test_a3_strategy_evidence_requires_exact_scope_and_option_binding():
    env = envelope()
    learned = strategy_candidate()
    qualified = qualify_a3_candidate(learned, env, option_id="adaptive")
    assert qualified.qualification_status == "QUALIFIED"
    assert qualified.a3_candidate_type == "SPECIALIST_STRATEGY_TENDENCY"

    wrong_project = strategy_candidate(
        scope=strategy_scope(project_key="Baelfyre/Other"),
    )
    rejected = qualify_a3_candidate(wrong_project, env, option_id="adaptive")
    assert rejected.qualification_status == "REJECTED"


def test_a3_comparison_is_exact_bound_and_never_execution_authority():
    env = envelope()
    learned = strategy_candidate()
    comparison = build_shadow_comparison(
        learned,
        actual_deterministic_choice="threat-first",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )
    qualified = qualify_a3_comparison(comparison, learned, env, option_id="adaptive")
    assert qualified.qualification_status == "QUALIFIED"
    assert qualified.direction == "POSITIVE"
    assert comparison.execution_controlled_by == "DETERMINISTIC_ORCHESTRA"
    assert comparison.shadow_influenced_execution is False


def test_non_strategy_a3_tendency_cannot_be_repurposed_as_strategy_evidence():
    env = envelope()
    unsupported = SelectionEvidenceItem(
        evidence_id="workflow",
        source_kind="A3_SHADOW_CANDIDATE",
        source_ref="a3:workflow",
        source_digest=D2,
        option_id="adaptive",
        selection_type="SPECIALIST_STRATEGY",
        a3_candidate_type="WORKFLOW_TENDENCY",
        direction="POSITIVE",
        qualification_status="QUALIFIED",
        reason_code="WORKFLOW_TENDENCY_NOT_STRATEGY_PERFORMANCE",
    )
    decision = rank_shadow_selection(
        env,
        packet(env, (unsupported,)),
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE"
    assert decision.shadow_recommendation_id is None


@pytest.mark.parametrize("selection_type", ["MODEL", "WORKER"])
def test_model_worker_without_direct_qualified_evidence_falls_back(selection_type: str):
    env = envelope(
        selection_type=selection_type,
        candidates=(
            candidate("default", "deterministic-default", selection_type=selection_type, owner=None),
            candidate("other", "eligible-other", selection_type=selection_type, owner=None),
        ),
    )
    decision = rank_shadow_selection(
        env,
        packet(env),
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.ranked_candidate_ids == env.candidate_ids
    assert decision.shadow_recommendation_id is None


@pytest.mark.parametrize("selection_type", ["MODEL", "WORKER"])
def test_a3_evidence_is_explicitly_unsupported_for_model_worker(selection_type: str):
    env = envelope(
        selection_type=selection_type,
        candidates=(
            candidate("default", "deterministic-default", selection_type=selection_type, owner=None),
            candidate("other", "eligible-other", selection_type=selection_type, owner=None),
        ),
    )
    a3 = SelectionEvidenceItem(
        evidence_id="a3",
        source_kind="A3_SHADOW_CANDIDATE",
        source_ref="a3:strategy",
        source_digest=D2,
        option_id="other",
        selection_type=selection_type,
        a3_candidate_type="SPECIALIST_STRATEGY_TENDENCY",
        direction="POSITIVE",
        qualification_status="QUALIFIED",
        reason_code="A3_CANNOT_PROVE_MODEL_OR_WORKER",
    )
    decision = rank_shadow_selection(
        env,
        packet(env, (a3,)),
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE"
    assert decision.shadow_recommendation_id is None


@pytest.mark.parametrize("selection_type", ["MODEL", "WORKER"])
def test_direct_exact_bound_model_worker_evidence_can_only_shadow_rank(selection_type: str):
    env = envelope(
        selection_type=selection_type,
        candidates=(
            candidate("default", "deterministic-default", selection_type=selection_type, owner=None),
            candidate("other", "eligible-other", selection_type=selection_type, owner=None),
        ),
    )
    evidence = packet(
        env,
        (
            direct_item(
                evidence_id="direct-one",
                digest=D2,
                option_id="other",
                selection_type=selection_type,
            ),
            direct_item(
                evidence_id="direct-two",
                digest=D3,
                option_id="other",
                selection_type=selection_type,
            ),
        ),
    )
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "SHADOW_RANKED"
    assert decision.shadow_recommendation_id == "other"
    payload = decision.to_dict()
    assert payload["selection_effective"] is False
    assert payload["shadow_influenced_execution"] is False
    assert payload["execution_controlled_by"] == "DETERMINISTIC_ORCHESTRA"
    assert decision.actual_deterministic_choice_id == "default"


def test_duplicate_source_digest_never_inflates_support_floor():
    env = envelope()
    evidence = packet(
        env,
        (
            direct_item(evidence_id="dup-one", digest=D2, option_id="adaptive"),
            direct_item(evidence_id="dup-two", digest=D2, option_id="adaptive"),
        ),
    )
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.shadow_recommendation_id is None


def test_one_digest_cannot_support_multiple_options():
    env = envelope()
    evidence = packet(
        env,
        (
            direct_item(evidence_id="one", digest=D2, option_id="default"),
            direct_item(evidence_id="two", digest=D2, option_id="adaptive"),
        ),
    )
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "INVALID_EVIDENCE"


def test_qualified_evidence_cannot_add_or_restore_ineligible_option():
    env = envelope()
    outside = direct_item(evidence_id="outside", digest=D2, option_id="provider-filtered")
    decision = rank_shadow_selection(
        env,
        packet(env, (outside,)),
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert decision.disposition == "INVALID_EVIDENCE"
    assert "provider-filtered" not in decision.ranked_candidate_ids


def test_trustworthy_measured_telemetry_requires_measured_value():
    with pytest.raises(ValueError, match="validated measurement"):
        direct_item(
            evidence_id="latency",
            digest=D2,
            option_id="adaptive",
            source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
        )

    item = direct_item(
        evidence_id="latency",
        digest=D2,
        option_id="adaptive",
        source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
        measurement=SelectionMeasurement(
            metric="LATENCY",
            value=12.5,
            unit="ms",
        ),
    )
    assert item.measurement is not None
    assert item.measurement.measurement_status == "TRUSTWORTHY_MEASURED"


def test_packet_mismatch_and_stale_time_fail_closed():
    env = envelope(created_at=T1)
    valid = packet(env, collected_at=T2)
    mismatched = SelectionEvidencePacket(
        packet_id="mismatch",
        eligibility_envelope_ref=env.envelope_id,
        eligibility_envelope_digest=D4,
        selection_type=env.selection_type,
        collected_at=T2,
        items=(),
    )
    wrong_binding = rank_shadow_selection(
        env,
        mismatched,
        actual_deterministic_choice_id="default",
        evaluated_at=T3,
    )
    assert wrong_binding.disposition == "INVALID_EVIDENCE"

    stale = SelectionEvidencePacket(
        packet_id="stale",
        eligibility_envelope_ref=env.envelope_id,
        eligibility_envelope_digest=env.digest,
        selection_type=env.selection_type,
        collected_at=T0,
        items=(),
    )
    stale_decision = rank_shadow_selection(
        env,
        stale,
        actual_deterministic_choice_id="default",
        evaluated_at=T3,
    )
    assert stale_decision.disposition == "INVALID_EVIDENCE"

    time_inverted = rank_shadow_selection(
        env,
        valid,
        actual_deterministic_choice_id="default",
        evaluated_at=T1,
    )
    assert time_inverted.disposition == "INVALID_EVIDENCE"


def test_same_validated_inputs_produce_same_rank_and_stable_ties_preserve_default_order():
    env = envelope()
    tie_evidence = packet(
        env,
        (
            direct_item(evidence_id="d-one", digest=D0, option_id="default"),
            direct_item(evidence_id="d-two", digest=D1, option_id="default"),
            direct_item(evidence_id="a-one", digest=D2, option_id="adaptive"),
            direct_item(evidence_id="a-two", digest=D3, option_id="adaptive"),
        ),
    )
    first = rank_shadow_selection(
        env,
        tie_evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    second = rank_shadow_selection(
        env,
        tie_evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    assert first == second
    assert first.decision_id == second.decision_id
    assert first.ranked_candidate_ids == ("default", "adaptive")
    assert first.shadow_recommendation_id == "default"


def test_shadow_decision_is_structurally_non_authorizing():
    env = envelope()
    evidence = packet(
        env,
        (
            direct_item(evidence_id="one", digest=D2, option_id="adaptive"),
            direct_item(evidence_id="two", digest=D3, option_id="adaptive"),
        ),
    )
    decision = rank_shadow_selection(
        env,
        evidence,
        actual_deterministic_choice_id="default",
        evaluated_at=T2,
    )
    payload = decision.to_dict()
    assert payload["execution_controlled_by"] == "DETERMINISTIC_ORCHESTRA"
    assert payload["selection_effective"] is False
    assert payload["shadow_influenced_execution"] is False
    assert payload["promotion_state"] == "NOT_PROMOTED"
    assert env.candidate_ids == ("default", "adaptive")
