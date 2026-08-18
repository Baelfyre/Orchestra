from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.adaptive.topology import (
    REQUIRED_TOPOLOGY_INVARIANTS,
    TopologyCandidate,
    TopologyEvidenceItem,
    TopologyEvidencePacket,
    TopologyMeasuredMetric,
    TopologyStage,
    build_topology_evidence_packet,
    build_topology_eligibility_envelope,
    qualify_topology_evidence,
    rank_shadow_topologies,
)


SESSION = "coordination.session.a5"
REVISION = 7
REQUIRED = ("clockwork", "overseer")
T0 = "2026-08-18T11:20:00Z"
T1 = "2026-08-18T11:21:00Z"
T2 = "2026-08-18T11:22:00Z"
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64


def candidate(candidate_id: str, *, stages: tuple[TopologyStage, ...] | None = None):
    return TopologyCandidate(
        candidate_id=candidate_id,
        coordination_contract_revision=REVISION,
        required_specialists=REQUIRED,
        stages=stages
        or (
            TopologyStage(
                stage_id=f"{candidate_id}.clockwork",
                mode="SEQUENTIAL",
                specialists=("clockwork",),
                join_required=True,
            ),
            TopologyStage(
                stage_id=f"{candidate_id}.overseer",
                mode="SEQUENTIAL",
                specialists=("overseer",),
                join_required=True,
                review_owner="overseer",
            ),
        ),
        reentry_order=("overseer",),
        prior_output_disclosure_refs=(),
        eligibility_evidence_refs=(f"coordination:{candidate_id}:eligible",),
    )


def env(*, candidates=None, deterministic="deterministic", created_at=T0):
    if candidates is None:
        candidates = (
            candidate("deterministic"),
            candidate(
                "adaptive",
                stages=(
                    TopologyStage(
                        stage_id="adaptive.overseer",
                        mode="SEQUENTIAL",
                        specialists=("overseer",),
                        join_required=True,
                    ),
                    TopologyStage(
                        stage_id="adaptive.clockwork",
                        mode="SEQUENTIAL",
                        specialists=("clockwork",),
                        join_required=True,
                    ),
                ),
            ),
        )
    return build_topology_eligibility_envelope(
        session_id=SESSION,
        created_at=created_at,
        user_key="user",
        project_key="Baelfyre/Orchestra",
        coordination_contract_ref="coordination:contract:a5",
        coordination_contract_revision=REVISION,
        required_specialists=REQUIRED,
        invariant_evidence_refs=("coordination:validated",),
        candidates=candidates,
        deterministic_topology_candidate_id=deterministic,
        invariants_applied={key: True for key in REQUIRED_TOPOLOGY_INVARIANTS},
    )


def item(
    envelope,
    *,
    evidence_id,
    digest,
    candidate_id,
    direction="POSITIVE",
    session_id=SESSION,
    revision=REVISION,
):
    qualified = qualify_topology_evidence(
        envelope,
        candidate_id=candidate_id,
        source_kind="GOVERNED_COORDINATION_OUTCOME",
        source_ref=f"outcome:{evidence_id}",
        source_digest=digest,
        session_id=session_id,
        coordination_contract_revision=revision,
        direction=direction,
    )
    return replace(qualified, evidence_id=evidence_id)


def packet(envelope, items=(), *, collected_at=T1):
    return build_topology_evidence_packet(
        envelope,
        collected_at=collected_at,
        items=items,
    )


def test_topology_stage_rejects_duplicate_or_invalid_specialist_shapes():
    with pytest.raises(ValueError, match="duplicate"):
        TopologyStage(
            stage_id="duplicate",
            mode="PARALLEL",
            specialists=("clockwork", "clockwork"),
            join_required=True,
        )
    with pytest.raises(ValueError, match="mode"):
        TopologyStage(
            stage_id="invalid-mode",
            mode="UNBOUNDED",
            specialists=("clockwork",),
            join_required=True,
        )
    with pytest.raises(TypeError, match="boolean"):
        TopologyStage(
            stage_id="invalid-join",
            mode="SEQUENTIAL",
            specialists=("clockwork",),
            join_required=1,
        )


def test_ranker_never_creates_or_restores_candidate_outside_immutable_envelope():
    envelope = env()
    forged = TopologyEvidenceItem(
        evidence_id="forged",
        source_kind="GOVERNED_COORDINATION_OUTCOME",
        source_ref="outcome:forged",
        source_digest=D0,
        candidate_id="not-eligible",
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        qualification_status="QUALIFIED",
        reason_code="FORGED_OUTSIDE_ENVELOPE",
        direction="POSITIVE",
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, (forged,)),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("QUALIFIED_EVIDENCE_EXACT_BINDING_FAILURE",)
    assert set(decision.ranked_candidate_ids) == set(envelope.candidate_ids)
    assert "not-eligible" not in decision.ranked_candidate_ids


def test_one_source_digest_cannot_support_multiple_topology_candidates():
    envelope = env()
    items = (
        item(envelope, evidence_id="one", digest=D1, candidate_id="deterministic"),
        item(envelope, evidence_id="two", digest=D1, candidate_id="adaptive"),
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("EVIDENCE_DIGEST_MULTI_CANDIDATE_BINDING",)


def test_manually_marked_cross_session_qualified_evidence_fails_closed():
    envelope = env()
    cross_session = TopologyEvidenceItem(
        evidence_id="cross-session",
        source_kind="VALIDATION_EVIDENCE",
        source_ref="validation:other-session",
        source_digest=D1,
        candidate_id="adaptive",
        session_id="coordination.other",
        coordination_contract_revision=REVISION,
        qualification_status="QUALIFIED",
        reason_code="MANUAL_QUALIFICATION_MUST_BE_REVALIDATED",
        direction="POSITIVE",
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, (cross_session,)),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("QUALIFIED_EVIDENCE_EXACT_BINDING_FAILURE",)


def test_manually_marked_stale_revision_qualified_evidence_fails_closed():
    envelope = env()
    stale = TopologyEvidenceItem(
        evidence_id="stale",
        source_kind="REMEDIATION_EVIDENCE",
        source_ref="remediation:old-revision",
        source_digest=D1,
        candidate_id="adaptive",
        session_id=SESSION,
        coordination_contract_revision=REVISION + 1,
        qualification_status="QUALIFIED",
        reason_code="MANUAL_QUALIFICATION_MUST_BE_REVALIDATED",
        direction="POSITIVE",
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, (stale,)),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("QUALIFIED_EVIDENCE_EXACT_BINDING_FAILURE",)


def test_evidence_packet_must_bind_exact_eligibility_identity():
    envelope = env()
    exact = packet(envelope)
    mismatched = TopologyEvidencePacket(
        packet_id=exact.packet_id,
        eligibility_envelope_id="other-envelope",
        eligibility_digest=exact.eligibility_digest,
        session_id=exact.session_id,
        coordination_contract_revision=exact.coordination_contract_revision,
        collected_at=exact.collected_at,
        items=exact.items,
    )
    decision = rank_shadow_topologies(
        envelope,
        mismatched,
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("EVIDENCE_PACKET_BINDING_MISMATCH",)


def test_stale_evidence_packet_time_falls_back():
    envelope = env(created_at=T1)
    stale_packet = packet(envelope, collected_at=T0)
    decision = rank_shadow_topologies(
        envelope,
        stale_packet,
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("EVIDENCE_PACKET_PREDATES_ELIGIBILITY",)


def test_evaluation_cannot_predate_bound_evidence_packet():
    envelope = env()
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, collected_at=T2),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T1,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("EVALUATION_PREDATES_EVIDENCE_PACKET",)


def test_adaptive_unavailable_uses_deterministic_fallback_order_without_recommendation():
    envelope = env()
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
        adaptive_available=False,
    )
    assert decision.disposition == "ADAPTIVE_UNAVAILABLE"
    assert decision.ranked_candidate_ids == envelope.candidate_ids
    assert decision.shadow_recommendation_id is None
    assert decision.to_dict()["topology_effective"] is False


def test_empty_eligible_set_fails_closed_without_creating_candidate():
    envelope = env(candidates=(), deterministic=None)
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope),
        actual_deterministic_candidate_id="deterministic-current",
        evaluated_at=T2,
    )
    assert decision.disposition == "NO_ELIGIBLE_TOPOLOGIES"
    assert decision.ranked_candidate_ids == ()
    assert decision.shadow_recommendation_id is None
    assert decision.reason_codes == ("NO_ELIGIBLE_TOPOLOGIES_FAIL_CLOSED",)


def test_a3_workflow_tendency_is_not_a_supported_topology_evidence_class():
    envelope = env()
    with pytest.raises(ValueError, match="unsupported topology evidence source kind"):
        qualify_topology_evidence(
            envelope,
            candidate_id="adaptive",
            source_kind="A3_WORKFLOW_TENDENCY",
            source_ref="a3:workflow:tendency",
            source_digest=D1,
            session_id=SESSION,
            coordination_contract_revision=REVISION,
            direction="POSITIVE",
        )


def test_generic_phase_success_cannot_be_invented_as_topology_performance_evidence():
    envelope = env()
    with pytest.raises(ValueError, match="unsupported topology evidence source kind"):
        qualify_topology_evidence(
            envelope,
            candidate_id="adaptive",
            source_kind="GENERIC_PHASE_SUCCESS",
            source_ref="phase:a5:success",
            source_digest=D1,
            session_id=SESSION,
            coordination_contract_revision=REVISION,
            direction="POSITIVE",
        )


def test_measured_telemetry_is_rejected_when_metric_is_missing_or_invented():
    with pytest.raises(ValueError, match="measured_metric"):
        TopologyEvidenceItem(
            evidence_id="telemetry",
            source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
            source_ref="telemetry:run",
            source_digest=D1,
            candidate_id="adaptive",
            session_id=SESSION,
            coordination_contract_revision=REVISION,
            qualification_status="QUALIFIED",
            reason_code="EXACT_TOPOLOGY_BOUND_MEASURED_TELEMETRY",
            direction="POSITIVE",
        )

    with pytest.raises(ValueError, match="unsupported topology metric"):
        TopologyMeasuredMetric(
            metric_name="INFERRED_COST",
            value=1,
            unit="unknown",
            measurement_ref="inference:not-measured",
        )


def test_parallel_stage_is_descriptive_only_and_does_not_activate_parallel_execution():
    parallel = candidate(
        "parallel-eligible",
        stages=(
            TopologyStage(
                stage_id="parallel.group",
                mode="PARALLEL",
                specialists=REQUIRED,
                join_required=True,
                review_owner="overseer",
            ),
        ),
    )
    deterministic = candidate("deterministic")
    envelope = env(candidates=(deterministic, parallel), deterministic="deterministic")
    items = (
        item(envelope, evidence_id="one", digest=D1, candidate_id="parallel-eligible"),
        item(envelope, evidence_id="two", digest=D2, candidate_id="parallel-eligible"),
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.shadow_recommendation_id == "parallel-eligible"
    payload = decision.to_dict()
    assert payload["topology_effective"] is False
    assert payload["shadow_influenced_execution"] is False
    assert payload["dispatch_controlled_by"] == "CONDUCTOR"


def test_same_semantic_inputs_produce_same_rank_and_decision_digest():
    envelope = env()
    items = (
        item(envelope, evidence_id="one", digest=D1, candidate_id="adaptive"),
        item(envelope, evidence_id="two", digest=D2, candidate_id="adaptive"),
        item(envelope, evidence_id="neutral", digest=D3, candidate_id="deterministic", direction="NEUTRAL"),
    )
    evidence_packet = packet(envelope, items)
    first = rank_shadow_topologies(
        envelope,
        evidence_packet,
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    second = rank_shadow_topologies(
        envelope,
        evidence_packet,
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert first.ranked_candidate_ids == second.ranked_candidate_ids
    assert first.digest == second.digest


def test_required_specialist_set_cannot_change_across_candidates():
    deterministic = candidate("deterministic")
    different = TopologyCandidate(
        candidate_id="different",
        coordination_contract_revision=REVISION,
        required_specialists=("clockwork", "forge"),
        stages=(
            TopologyStage(stage_id="different.clockwork", mode="SEQUENTIAL", specialists=("clockwork",), join_required=True),
            TopologyStage(stage_id="different.forge", mode="SEQUENTIAL", specialists=("forge",), join_required=True),
        ),
        reentry_order=(),
        prior_output_disclosure_refs=(),
        eligibility_evidence_refs=("coordination:different:eligible",),
    )
    with pytest.raises(ValueError, match="required_specialists"):
        env(candidates=(deterministic, different), deterministic="deterministic")
