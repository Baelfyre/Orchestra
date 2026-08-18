from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from orchestra_runtime.adaptive.topology import (
    REQUIRED_TOPOLOGY_INVARIANTS,
    TopologyCandidate,
    TopologyEvidenceItem,
    TopologyEligibilityEnvelope,
    TopologyMeasuredMetric,
    TopologyStage,
    build_topology_evidence_packet,
    build_topology_eligibility_envelope,
    qualify_topology_evidence,
    rank_shadow_topologies,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"
ADAPTIVE_MACHINE = ROOT / "machine" / "adaptive"

USER = "topology-user"
PROJECT = "Baelfyre/Orchestra"
SESSION = "coordination.session.a5"
CONTRACT_REF = "coordination:contract:a5"
REVISION = 7
REQUIRED = ("clockwork", "overseer")
T0 = "2026-08-18T11:20:00Z"
T1 = "2026-08-18T11:21:00Z"
T2 = "2026-08-18T11:22:00Z"
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64


def invariants(**overrides: bool) -> dict[str, bool]:
    result = {key: True for key in REQUIRED_TOPOLOGY_INVARIANTS}
    result.update(overrides)
    return result


def stage(
    stage_id: str,
    specialists: tuple[str, ...],
    *,
    mode: str = "SEQUENTIAL",
    join_required: bool = True,
    review_owner: str | None = None,
) -> TopologyStage:
    return TopologyStage(
        stage_id=stage_id,
        mode=mode,
        specialists=specialists,
        join_required=join_required,
        review_owner=review_owner,
    )


def candidate(
    candidate_id: str,
    *,
    first: str = "clockwork",
    second: str = "overseer",
    revision: int = REVISION,
    required: tuple[str, ...] = REQUIRED,
) -> TopologyCandidate:
    return TopologyCandidate(
        candidate_id=candidate_id,
        coordination_contract_revision=revision,
        required_specialists=required,
        stages=(
            stage(f"{candidate_id}.stage.1", (first,)),
            stage(f"{candidate_id}.stage.2", (second,)),
        ),
        reentry_order=(second,),
        prior_output_disclosure_refs=(f"context:{candidate_id}",),
        eligibility_evidence_refs=(f"coordination:{candidate_id}:eligible",),
    )


def envelope(
    *,
    candidates: tuple[TopologyCandidate, ...] | None = None,
    deterministic: str | None = "deterministic",
    explicit_current_constraint_ref: str | None = None,
    applied: dict[str, bool] | None = None,
    created_at: str = T0,
) -> TopologyEligibilityEnvelope:
    if candidates is None:
        candidates = (
            candidate("deterministic"),
            candidate("adaptive", first="overseer", second="clockwork"),
        )
    return build_topology_eligibility_envelope(
        session_id=SESSION,
        created_at=created_at,
        user_key=USER,
        project_key=PROJECT,
        task_session_key="task.a5",
        coordination_contract_ref=CONTRACT_REF,
        coordination_contract_revision=REVISION,
        required_specialists=REQUIRED,
        invariant_evidence_refs=(
            "coordination:validated",
            "ownership:validated",
            "governance:validated",
        ),
        candidates=candidates,
        deterministic_topology_candidate_id=deterministic,
        explicit_current_constraint_ref=explicit_current_constraint_ref,
        invariants_applied=applied or invariants(),
    )


def evidence(
    env: TopologyEligibilityEnvelope,
    *,
    evidence_id: str,
    digest: str,
    candidate_id: str,
    source_kind: str = "GOVERNED_COORDINATION_OUTCOME",
    direction: str = "POSITIVE",
    session_id: str = SESSION,
    revision: int = REVISION,
    metric: TopologyMeasuredMetric | None = None,
) -> TopologyEvidenceItem:
    item = qualify_topology_evidence(
        env,
        candidate_id=candidate_id,
        source_kind=source_kind,
        source_ref=f"evidence:{evidence_id}",
        source_digest=digest,
        session_id=session_id,
        coordination_contract_revision=revision,
        direction=direction,
        measured_metric=metric,
    )
    return TopologyEvidenceItem(
        evidence_id=evidence_id,
        source_kind=item.source_kind,
        source_ref=item.source_ref,
        source_digest=item.source_digest,
        candidate_id=item.candidate_id,
        session_id=item.session_id,
        coordination_contract_revision=item.coordination_contract_revision,
        qualification_status=item.qualification_status,
        reason_code=item.reason_code,
        direction=item.direction,
        measured_metric=item.measured_metric,
    )


def packet(
    env: TopologyEligibilityEnvelope,
    items: tuple[TopologyEvidenceItem, ...] = (),
    *,
    collected_at: str = T1,
):
    return build_topology_evidence_packet(
        env,
        collected_at=collected_at,
        items=items,
    )


def test_machine_implementation_record_preserves_a5_1_shadow_only_boundary():
    record = json.loads(
        (ADAPTIVE_MACHINE / "a5-shadow-topology-ranker-implementation.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert record["phase"] == "A5.1_SHADOW_TOPOLOGY_RANKER_AND_EVIDENCE_QUALIFICATION"
    assert record["scorer"]["version"] == "orchestra.adaptive-topology-scorer.v1"
    assert record["eligibility"]["adaptive_candidate_creation"] is False
    assert record["eligibility"]["required_specialist_omission"] is False
    assert record["decision_boundary"]["topology_effective"] is False
    assert record["decision_boundary"]["shadow_influenced_execution"] is False
    assert record["decision_boundary"]["conductor_dispatch_attachment"] is False
    assert record["decision_boundary"]["runtime_executor_attachment"] is False
    assert record["future_boundary"]["a5_2_or_execution_effective_selection"] == "NOT_INTRODUCED"


def test_a5_records_validate_against_frozen_machine_schemas():
    env = envelope()
    items = (
        evidence(env, evidence_id="one", digest=D1, candidate_id="adaptive"),
        evidence(env, evidence_id="two", digest=D2, candidate_id="adaptive"),
    )
    evidence_packet = packet(env, items)
    decision = rank_shadow_topologies(
        env,
        evidence_packet,
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "SHADOW_RANKED"
    assert decision.shadow_recommendation_id == "adaptive"

    for instance, schema_name in (
        (env.to_dict(), "adaptive-topology-eligibility-envelope.schema.json"),
        (evidence_packet.to_dict(), "adaptive-topology-evidence.schema.json"),
        (decision.to_dict(), "adaptive-topology-decision.schema.json"),
    ):
        schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).validate(instance)


def test_eligibility_requires_every_frozen_invariant_true():
    with pytest.raises(ValueError, match="invariants"):
        envelope(applied=invariants(governance_complete=False))

    missing = invariants()
    missing.pop("resource_ceilings")
    with pytest.raises(ValueError, match="invariants"):
        envelope(applied=missing)


def test_candidate_must_preserve_every_required_specialist():
    with pytest.raises(ValueError, match="required specialist"):
        TopologyCandidate(
            candidate_id="omits-required",
            coordination_contract_revision=REVISION,
            required_specialists=REQUIRED,
            stages=(stage("only.clockwork", ("clockwork",)),),
            reentry_order=(),
            prior_output_disclosure_refs=(),
            eligibility_evidence_refs=("coordination:eligible",),
        )


def test_candidate_required_set_and_revision_must_match_immutable_envelope():
    wrong_required = candidate(
        "wrong-required",
        required=("clockwork", "forge"),
        first="clockwork",
        second="forge",
    )
    with pytest.raises(ValueError, match="required_specialists"):
        envelope(candidates=(wrong_required,), deterministic="wrong-required")

    wrong_revision = candidate("wrong-revision", revision=REVISION + 1)
    with pytest.raises(ValueError, match="revision"):
        envelope(candidates=(wrong_revision,), deterministic="wrong-revision")


def test_actual_deterministic_topology_must_remain_inside_eligible_set():
    env = envelope()
    decision = rank_shadow_topologies(
        env,
        packet(env),
        actual_deterministic_candidate_id="not-eligible",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.ranked_candidate_ids == env.candidate_ids
    assert decision.shadow_recommendation_id is None
    assert decision.reason_codes == ("ACTUAL_DETERMINISTIC_TOPOLOGY_NOT_ELIGIBLE",)


def test_explicit_current_constraint_retains_precedence_over_adaptive_evidence():
    env = envelope(explicit_current_constraint_ref="user:current:constraint")
    items = (
        evidence(env, evidence_id="one", digest=D1, candidate_id="adaptive"),
        evidence(env, evidence_id="two", digest=D2, candidate_id="adaptive"),
    )
    decision = rank_shadow_topologies(
        env,
        packet(env, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.ranked_candidate_ids == env.candidate_ids
    assert decision.shadow_recommendation_id is None
    assert decision.reason_codes == ("EXPLICIT_CURRENT_CONSTRAINT_PRECEDENCE",)


def test_scoped_preference_can_only_reorder_an_already_eligible_candidate():
    env = envelope()
    preferred = rank_shadow_topologies(
        env,
        packet(env),
        actual_deterministic_candidate_id="deterministic",
        explicit_scoped_preference_candidate_id="adaptive",
        evaluated_at=T2,
    )
    assert preferred.disposition == "SHADOW_RANKED"
    assert preferred.ranked_candidate_ids[0] == "adaptive"
    assert preferred.shadow_recommendation_id == "adaptive"

    rejected = rank_shadow_topologies(
        env,
        packet(env),
        actual_deterministic_candidate_id="deterministic",
        explicit_scoped_preference_candidate_id="not-eligible",
        evaluated_at=T2,
    )
    assert rejected.disposition == "DETERMINISTIC_FALLBACK"
    assert rejected.ranked_candidate_ids == env.candidate_ids
    assert rejected.shadow_recommendation_id is None


def test_exact_evidence_qualification_binds_candidate_session_and_revision():
    env = envelope()
    qualified = evidence(
        env,
        evidence_id="qualified",
        digest=D1,
        candidate_id="adaptive",
    )
    assert qualified.qualification_status == "QUALIFIED"
    assert qualified.reason_code == "EXACT_TOPOLOGY_BOUND_GOVERNED_EVIDENCE"

    wrong_session = evidence(
        env,
        evidence_id="wrong-session",
        digest=D2,
        candidate_id="adaptive",
        session_id="coordination.other",
    )
    assert wrong_session.qualification_status == "REJECTED"
    assert wrong_session.reason_code == "TOPOLOGY_SESSION_MISMATCH"

    wrong_revision = evidence(
        env,
        evidence_id="wrong-revision",
        digest=D3,
        candidate_id="adaptive",
        revision=REVISION + 1,
    )
    assert wrong_revision.qualification_status == "REJECTED"
    assert wrong_revision.reason_code == "TOPOLOGY_CONTRACT_REVISION_MISMATCH"


def test_duplicate_source_digest_counts_only_once_for_support_floor():
    env = envelope()
    items = (
        evidence(env, evidence_id="one", digest=D1, candidate_id="adaptive"),
        evidence(env, evidence_id="duplicate", digest=D1, candidate_id="adaptive"),
    )
    decision = rank_shadow_topologies(
        env,
        packet(env, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("INSUFFICIENT_DISTINCT_POSITIVE_SUPPORT",)
    assert decision.ranked_candidate_ids == env.candidate_ids


def test_stable_tie_break_uses_existing_deterministic_candidate_order():
    env = envelope()
    items = (
        evidence(env, evidence_id="det-one", digest=D0, candidate_id="deterministic"),
        evidence(env, evidence_id="det-two", digest=D1, candidate_id="deterministic"),
        evidence(env, evidence_id="adapt-one", digest=D2, candidate_id="adaptive"),
        evidence(env, evidence_id="adapt-two", digest=D3, candidate_id="adaptive"),
    )
    first = rank_shadow_topologies(
        env,
        packet(env, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    second = rank_shadow_topologies(
        env,
        packet(env, tuple(reversed(items))),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert first.ranked_candidate_ids == env.candidate_ids
    assert second.ranked_candidate_ids == env.candidate_ids
    assert first.shadow_recommendation_id == "deterministic"
    assert second.shadow_recommendation_id == "deterministic"


def test_shadow_decision_is_structurally_non_authorizing():
    env = envelope()
    items = (
        evidence(env, evidence_id="one", digest=D1, candidate_id="adaptive"),
        evidence(env, evidence_id="two", digest=D2, candidate_id="adaptive"),
    )
    decision = rank_shadow_topologies(
        env,
        packet(env, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    payload = decision.to_dict()
    assert payload["execution_controlled_by"] == "DETERMINISTIC_ORCHESTRA"
    assert payload["dispatch_controlled_by"] == "CONDUCTOR"
    assert payload["transition_controlled_by"] == "ARBITER"
    assert payload["topology_effective"] is False
    assert payload["shadow_influenced_execution"] is False
    assert payload["promotion_state"] == "NOT_PROMOTED"


def test_measured_telemetry_requires_explicit_provenance_bound_metric():
    env = envelope()
    metric = TopologyMeasuredMetric(
        metric_name="LATENCY",
        value=12.5,
        unit="ms",
        measurement_ref="telemetry:run:1",
    )
    item = evidence(
        env,
        evidence_id="telemetry",
        digest=D4,
        candidate_id="adaptive",
        source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
        metric=metric,
    )
    assert item.qualification_status == "QUALIFIED"
    assert item.measured_metric == metric

    with pytest.raises(ValueError, match="measured_metric"):
        evidence(
            env,
            evidence_id="missing-measurement",
            digest=D3,
            candidate_id="adaptive",
            source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
        )
