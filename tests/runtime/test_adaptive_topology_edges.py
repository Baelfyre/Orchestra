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


def test_scalar_and_identifier_guards_fail_closed_on_malformed_stage_inputs():
    invalid_cases = (
        ({"stage_id": 7, "mode": "SEQUENTIAL", "specialists": ("clockwork",), "join_required": True}, TypeError),
        ({"stage_id": "", "mode": "SEQUENTIAL", "specialists": ("clockwork",), "join_required": True}, ValueError),
        ({"stage_id": "x" * 129, "mode": "SEQUENTIAL", "specialists": ("clockwork",), "join_required": True}, ValueError),
        ({"stage_id": "bad stage", "mode": "SEQUENTIAL", "specialists": ("clockwork",), "join_required": True}, ValueError),
        ({"stage_id": "empty-specialists", "mode": "SEQUENTIAL", "specialists": (), "join_required": True}, ValueError),
        ({"stage_id": "control", "mode": "SEQUENTIAL", "specialists": ("clockwork\n",), "join_required": True}, ValueError),
    )
    for kwargs, error in invalid_cases:
        with pytest.raises(error):
            TopologyStage(**kwargs)

    with pytest.raises(ValueError, match="exceeds 64 items"):
        TopologyStage(
            stage_id="too-many-specialists",
            mode="PARALLEL",
            specialists=tuple(f"s{i}" for i in range(65)),
            join_required=True,
        )


def test_candidate_collection_guards_cover_empty_invalid_duplicate_and_bounded_shapes():
    valid_stage = TopologyStage(
        stage_id="candidate.valid",
        mode="PARALLEL",
        specialists=REQUIRED,
        join_required=True,
    )
    base = dict(
        candidate_id="candidate",
        coordination_contract_revision=REVISION,
        required_specialists=REQUIRED,
        reentry_order=(),
        prior_output_disclosure_refs=(),
        eligibility_evidence_refs=("coordination:eligible",),
    )

    with pytest.raises(ValueError, match="between 1 and 64"):
        TopologyCandidate(stages=(), **base)
    with pytest.raises(TypeError, match="TopologyStage"):
        TopologyCandidate(stages=(object(),), **base)
    with pytest.raises(ValueError, match="stage ids must be unique"):
        TopologyCandidate(stages=(valid_stage, valid_stage), **base)
    with pytest.raises(ValueError, match="duplicate"):
        TopologyCandidate(stages=(valid_stage,), reentry_order=("clockwork", "clockwork"), **{k: v for k, v in base.items() if k != "reentry_order"})
    with pytest.raises(ValueError, match="eligibility_evidence_ref must not be empty"):
        TopologyCandidate(stages=(valid_stage,), eligibility_evidence_refs=(), **{k: v for k, v in base.items() if k != "eligibility_evidence_refs"})
    with pytest.raises(ValueError, match="duplicate"):
        TopologyCandidate(stages=(valid_stage,), prior_output_disclosure_refs=("same", "same"), **{k: v for k, v in base.items() if k != "prior_output_disclosure_refs"})
    with pytest.raises(ValueError, match="exceeds 128 items"):
        TopologyCandidate(stages=(valid_stage,), prior_output_disclosure_refs=tuple(f"ref:{i}" for i in range(129)), **{k: v for k, v in base.items() if k != "prior_output_disclosure_refs"})


def test_revision_and_envelope_identity_guards_reject_invalid_shapes():
    for invalid_revision in (True, "7", 0):
        with pytest.raises(ValueError, match="positive integer"):
            candidate("bad-revision") if invalid_revision == REVISION else TopologyCandidate(
                candidate_id=f"bad-revision-{str(invalid_revision).lower()}",
                coordination_contract_revision=invalid_revision,
                required_specialists=REQUIRED,
                stages=(TopologyStage(stage_id="revision.parallel", mode="PARALLEL", specialists=REQUIRED, join_required=True),),
                reentry_order=(),
                prior_output_disclosure_refs=(),
                eligibility_evidence_refs=("coordination:eligible",),
            )

    envelope = env()
    with pytest.raises(ValueError, match="unsupported topology eligibility schema"):
        replace(envelope, schema_version="orchestra.adaptive-topology-eligibility-envelope.v0")
    with pytest.raises(ValueError, match="candidate ids must be unique"):
        env(candidates=(candidate("same"), candidate("same")), deterministic="same")
    with pytest.raises(TypeError, match="TopologyCandidate"):
        build_topology_eligibility_envelope(
            session_id=SESSION,
            created_at=T0,
            user_key="user",
            coordination_contract_ref="coordination:contract:a5",
            coordination_contract_revision=REVISION,
            required_specialists=REQUIRED,
            invariant_evidence_refs=("coordination:validated",),
            candidates=(object(),),
            deterministic_topology_candidate_id="deterministic",
            invariants_applied={key: True for key in REQUIRED_TOPOLOGY_INVARIANTS},
        )
    with pytest.raises(ValueError, match="requires deterministic_topology_candidate_id"):
        env(candidates=(candidate("only"),), deterministic=None)
    with pytest.raises(ValueError, match="immutable eligible set"):
        env(candidates=(candidate("only"),), deterministic="missing")


def test_metric_and_evidence_item_scalar_guards_reject_untrusted_shapes():
    for value in (True, "12"):
        with pytest.raises(TypeError, match="numeric"):
            TopologyMeasuredMetric(
                metric_name="LATENCY",
                value=value,
                unit="ms",
                measurement_ref="telemetry:bad",
            )
    with pytest.raises(ValueError, match="non-negative"):
        TopologyMeasuredMetric(
            metric_name="LATENCY",
            value=-1,
            unit="ms",
            measurement_ref="telemetry:negative",
        )

    metric = TopologyMeasuredMetric(
        metric_name="LATENCY",
        value=1,
        unit="ms",
        measurement_ref="telemetry:measured",
    )
    base = dict(
        evidence_id="guard",
        source_kind="GOVERNED_COORDINATION_OUTCOME",
        source_ref="outcome:guard",
        source_digest=D0,
        candidate_id="adaptive",
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        qualification_status="QUALIFIED",
        reason_code="EXACT_TOPOLOGY_BOUND_GOVERNED_EVIDENCE",
        direction="POSITIVE",
    )
    with pytest.raises(ValueError, match="qualification status"):
        TopologyEvidenceItem(**{**base, "qualification_status": "UNKNOWN"})
    with pytest.raises(ValueError, match="evidence direction"):
        TopologyEvidenceItem(**{**base, "direction": "UP"})
    with pytest.raises(ValueError, match="measured_metric is valid only"):
        TopologyEvidenceItem(**base, measured_metric=metric)
    with pytest.raises(ValueError, match="reason_code"):
        TopologyEvidenceItem(**{**base, "reason_code": "bad reason"})


def test_packet_collection_guards_reject_schema_type_and_duplicate_identity_errors():
    envelope = env()
    first = item(envelope, evidence_id="same", digest=D1, candidate_id="adaptive")
    second = item(envelope, evidence_id="same", digest=D2, candidate_id="adaptive")
    exact = packet(envelope)
    with pytest.raises(ValueError, match="unsupported topology evidence schema"):
        replace(exact, schema_version="orchestra.adaptive-topology-evidence.v0")
    with pytest.raises(TypeError, match="TopologyEvidenceItem"):
        build_topology_evidence_packet(envelope, collected_at=T1, items=(object(),))
    with pytest.raises(ValueError, match="ids must be unique"):
        build_topology_evidence_packet(envelope, collected_at=T1, items=(first, second))
    with pytest.raises(TypeError, match="TopologyEligibilityEnvelope"):
        build_topology_evidence_packet(object(), collected_at=T1, items=())


def test_qualifier_reports_absent_candidate_and_each_supported_evidence_class():
    envelope = env()
    absent = qualify_topology_evidence(
        envelope,
        candidate_id="absent",
        source_kind="GOVERNED_COORDINATION_OUTCOME",
        source_ref="outcome:absent",
        source_digest=D0,
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        direction="NEGATIVE",
    )
    assert absent.qualification_status == "REJECTED"
    assert absent.reason_code == "TOPOLOGY_CANDIDATE_NOT_ELIGIBLE"

    validation = qualify_topology_evidence(
        envelope,
        candidate_id="adaptive",
        source_kind="VALIDATION_EVIDENCE",
        source_ref="validation:exact",
        source_digest=D1,
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        direction="NEUTRAL",
    )
    remediation = qualify_topology_evidence(
        envelope,
        candidate_id="adaptive",
        source_kind="REMEDIATION_EVIDENCE",
        source_ref="remediation:exact",
        source_digest=D2,
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        direction="POSITIVE",
    )
    telemetry = qualify_topology_evidence(
        envelope,
        candidate_id="adaptive",
        source_kind="TRUSTWORTHY_MEASURED_TELEMETRY",
        source_ref="telemetry:exact",
        source_digest=D3,
        session_id=SESSION,
        coordination_contract_revision=REVISION,
        direction="POSITIVE",
        measured_metric=TopologyMeasuredMetric(
            metric_name="TOKENS",
            value=10,
            unit="tokens",
            measurement_ref="telemetry:exact:measurement",
        ),
    )
    assert validation.reason_code == "EXACT_TOPOLOGY_BOUND_VALIDATION_EVIDENCE"
    assert remediation.reason_code == "EXACT_TOPOLOGY_BOUND_REMEDIATION_EVIDENCE"
    assert telemetry.reason_code == "EXACT_TOPOLOGY_BOUND_MEASURED_TELEMETRY"


def test_ranker_type_and_identity_guards_fail_closed_without_adaptive_authority():
    envelope = env()
    evidence_packet = packet(envelope)
    with pytest.raises(TypeError, match="TopologyEligibilityEnvelope"):
        rank_shadow_topologies(object(), evidence_packet, actual_deterministic_candidate_id="deterministic", evaluated_at=T2)
    with pytest.raises(TypeError, match="TopologyEvidencePacket"):
        rank_shadow_topologies(envelope, object(), actual_deterministic_candidate_id="deterministic", evaluated_at=T2)
    with pytest.raises(TypeError, match="adaptive_available"):
        rank_shadow_topologies(envelope, evidence_packet, actual_deterministic_candidate_id="deterministic", evaluated_at=T2, adaptive_available=1)

    alternate_identity = env(deterministic="adaptive")
    decision = rank_shadow_topologies(
        alternate_identity,
        packet(alternate_identity),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.reason_codes == ("DETERMINISTIC_TOPOLOGY_IDENTITY_MISMATCH",)


def test_supported_candidate_cannot_authorize_an_unsupported_higher_scoring_candidate():
    envelope = env()
    items = (
        item(envelope, evidence_id="det-pos-1", digest=D0, candidate_id="deterministic", direction="POSITIVE"),
        item(envelope, evidence_id="det-pos-2", digest=D1, candidate_id="deterministic", direction="POSITIVE"),
        item(envelope, evidence_id="det-neg-1", digest=D2, candidate_id="deterministic", direction="NEGATIVE"),
        item(envelope, evidence_id="adaptive-only", digest=D3, candidate_id="adaptive", direction="POSITIVE"),
    )
    decision = rank_shadow_topologies(
        envelope,
        packet(envelope, items),
        actual_deterministic_candidate_id="deterministic",
        evaluated_at=T2,
    )
    assert decision.disposition == "DETERMINISTIC_FALLBACK"
    assert decision.shadow_recommendation_id is None
    assert decision.reason_codes == ("NO_QUALIFIED_SHADOW_RECOMMENDATION",)
