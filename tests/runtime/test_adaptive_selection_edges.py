from __future__ import annotations

import pytest

import orchestra_runtime.adaptive.selection as selection
from orchestra_runtime.adaptive.selection import (
    REQUIRED_ELIGIBILITY_FILTERS,
    SelectionCandidate,
    SelectionDecision,
    SelectionEligibilityEnvelope,
    SelectionEvidenceItem,
    SelectionEvidencePacket,
    SelectionMeasurement,
    build_evidence_packet,
    qualify_a3_candidate,
    qualify_a3_comparison,
    rank_shadow_selection,
)

T0 = "2026-08-18T00:00:00Z"
T1 = "2026-08-18T00:01:00Z"
D0 = "0" * 64
D1 = "1" * 64


def candidate(candidate_id: str = "one") -> SelectionCandidate:
    return SelectionCandidate(
        candidate_id=candidate_id,
        option_kind="SPECIALIST_STRATEGY",
        option_key="threat-first",
        owner_specialist_slug="clockwork",
        provider_id="provider-a",
        eligibility_evidence_refs=(f"eligibility:{candidate_id}",),
    )


def envelope(
    *,
    candidates: tuple[SelectionCandidate, ...] | None = None,
) -> SelectionEligibilityEnvelope:
    return SelectionEligibilityEnvelope(
        envelope_id="env",
        selection_type="SPECIALIST_STRATEGY",
        created_at=T0,
        user_key="user",
        project_key="Baelfyre/Orchestra",
        task_session_key="task",
        command_name="architecture",
        routed_specialist_slug="clockwork",
        deterministic_route_ref="machine:routing:architecture",
        filter_evidence_refs=("filters:validated",),
        candidates=(candidate(),) if candidates is None else candidates,
        filters_applied={key: True for key in REQUIRED_ELIGIBILITY_FILTERS},
    )


def evidence_item(
    *,
    evidence_id: str = "evidence",
    option_id: str = "one",
    selection_type: str = "SPECIALIST_STRATEGY",
) -> SelectionEvidenceItem:
    return SelectionEvidenceItem(
        evidence_id=evidence_id,
        source_kind="GOVERNED_SELECTION_OUTCOME",
        source_ref=f"governed:{evidence_id}",
        source_digest=D0,
        option_id=option_id,
        selection_type=selection_type,
        qualification_status="QUALIFIED",
        reason_code="EXACT_OPTION_BOUND_EVIDENCE",
        direction="POSITIVE",
    )


def decision_kwargs() -> dict[str, object]:
    return {
        "decision_id": "decision",
        "selection_type": "SPECIALIST_STRATEGY",
        "eligibility_envelope_ref": "env",
        "eligibility_envelope_digest": D0,
        "evidence_packet_ref": "packet",
        "evidence_packet_digest": D1,
        "evaluated_at": T1,
        "disposition": "DETERMINISTIC_FALLBACK",
        "ranked_candidate_ids": ("one",),
        "shadow_recommendation_id": None,
        "actual_deterministic_choice_id": "one",
    }


def test_text_identifier_collection_and_note_guards_fail_closed():
    with pytest.raises(TypeError, match="must be a string"):
        selection._text(1, "field")
    with pytest.raises(ValueError, match="non-empty"):
        selection._text("   ", "field")
    with pytest.raises(ValueError, match="exceeds"):
        selection._text("abc", "field", max_length=2)
    with pytest.raises(ValueError, match="control characters"):
        selection._text("bad\nvalue", "field")
    with pytest.raises(ValueError, match="canonical identifier"):
        selection._identifier("Bad Value!", "identifier")
    with pytest.raises(ValueError, match="unsupported selection_type"):
        selection._selection_type("ROUTE")
    with pytest.raises(ValueError, match="exceeds 2 items"):
        selection._stable_strings(("a", "b", "c"), "items", max_items=2)
    with pytest.raises(ValueError, match="duplicate"):
        selection._stable_strings(("a", "a"), "items", max_items=2)
    with pytest.raises(ValueError, match="notes exceeds"):
        selection._notes(tuple(f"note-{index}" for index in range(17)))


def test_candidate_serialization_and_evidence_reference_guards():
    payload = candidate().to_dict()
    assert payload["owner_specialist_slug"] == "clockwork"
    assert payload["provider_id"] == "provider-a"

    without_optional = SelectionCandidate(
        candidate_id="two",
        option_kind="SPECIALIST_STRATEGY",
        option_key="architecture-first",
        eligibility_evidence_refs=("eligible:two",),
    ).to_dict()
    assert "owner_specialist_slug" not in without_optional
    assert "provider_id" not in without_optional

    with pytest.raises(ValueError, match="must not be empty"):
        SelectionCandidate(
            candidate_id="empty",
            option_kind="SPECIALIST_STRATEGY",
            option_key="architecture-first",
            eligibility_evidence_refs=(),
        )


def test_envelope_schema_size_type_duplicate_and_filter_reference_guards():
    base = envelope()
    with pytest.raises(ValueError, match="unsupported eligibility schema"):
        SelectionEligibilityEnvelope(
            **{**base.__dict__, "schema_version": "wrong"}
        )

    with pytest.raises(ValueError, match="exceeds 128"):
        envelope(candidates=tuple(candidate(f"c{index}") for index in range(129)))

    with pytest.raises(TypeError, match="SelectionCandidate"):
        SelectionEligibilityEnvelope(
            envelope_id="env",
            selection_type="SPECIALIST_STRATEGY",
            created_at=T0,
            user_key="user",
            project_key="Baelfyre/Orchestra",
            command_name="architecture",
            routed_specialist_slug="clockwork",
            deterministic_route_ref="route",
            filter_evidence_refs=("filters",),
            candidates=("not-a-candidate",),
        )

    duplicate = candidate("duplicate")
    with pytest.raises(ValueError, match="candidate ids"):
        envelope(candidates=(duplicate, duplicate))

    with pytest.raises(ValueError, match="filter_evidence_refs"):
        SelectionEligibilityEnvelope(
            envelope_id="env",
            selection_type="SPECIALIST_STRATEGY",
            created_at=T0,
            user_key="user",
            project_key="Baelfyre/Orchestra",
            command_name="architecture",
            routed_specialist_slug="clockwork",
            deterministic_route_ref="route",
            filter_evidence_refs=(),
            candidates=(candidate(),),
        )


def test_envelope_optional_serialization_and_empty_disposition():
    payload = envelope().to_dict()
    assert payload["project_key"] == "Baelfyre/Orchestra"
    assert payload["task_session_key"] == "task"

    empty = envelope(candidates=())
    assert empty.disposition == "NO_ELIGIBLE_CANDIDATES"
    assert empty.candidate_ids == ()
    assert empty.candidate_by_id("missing") is None


def test_measurement_guards_and_serialization():
    with pytest.raises(ValueError, match="unsupported measurement metric"):
        SelectionMeasurement(metric="QUALITY", value=1, unit="score")
    with pytest.raises(ValueError, match="non-negative number"):
        SelectionMeasurement(metric="LATENCY", value=True, unit="ms")
    with pytest.raises(ValueError, match="non-negative number"):
        SelectionMeasurement(metric="LATENCY", value="bad", unit="ms")
    with pytest.raises(ValueError, match="non-negative number"):
        SelectionMeasurement(metric="LATENCY", value=-1, unit="ms")
    with pytest.raises(ValueError, match="TRUSTWORTHY_MEASURED"):
        SelectionMeasurement(
            metric="LATENCY",
            value=1,
            unit="ms",
            measurement_status="ESTIMATED",
        )

    measured = SelectionMeasurement(metric="TOKEN_COUNT", value=10, unit="tokens")
    assert measured.to_dict()["value"] == 10.0


def test_evidence_item_vocabulary_and_binding_guards():
    common = {
        "evidence_id": "item",
        "source_ref": "source:item",
        "source_digest": D0,
        "option_id": "one",
        "selection_type": "SPECIALIST_STRATEGY",
        "qualification_status": "QUALIFIED",
        "reason_code": "VALID_REASON",
        "direction": "POSITIVE",
    }
    with pytest.raises(ValueError, match="unsupported evidence source kind"):
        SelectionEvidenceItem(source_kind="RAW_CHAT", **common)
    with pytest.raises(ValueError, match="unsupported qualification status"):
        SelectionEvidenceItem(
            source_kind="GOVERNED_SELECTION_OUTCOME",
            **{**common, "qualification_status": "MAYBE"},
        )
    with pytest.raises(ValueError, match="reason_code"):
        SelectionEvidenceItem(
            source_kind="GOVERNED_SELECTION_OUTCOME",
            **{**common, "reason_code": "bad-reason"},
        )
    with pytest.raises(ValueError, match="unsupported A3 candidate type"):
        SelectionEvidenceItem(
            source_kind="A3_SHADOW_CANDIDATE",
            a3_candidate_type="MODEL_TENDENCY",
            **common,
        )
    with pytest.raises(ValueError, match="unsupported evidence direction"):
        SelectionEvidenceItem(
            source_kind="GOVERNED_SELECTION_OUTCOME",
            **{**common, "direction": "LIKELY"},
        )


def test_evidence_item_a3_and_measurement_shape_guards():
    with pytest.raises(ValueError, match="must declare a3_candidate_type"):
        SelectionEvidenceItem(
            evidence_id="a3",
            source_kind="A3_SHADOW_CANDIDATE",
            source_ref="a3:item",
            source_digest=D0,
            option_id="one",
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="VALID_REASON",
            direction="POSITIVE",
        )

    with pytest.raises(ValueError, match="cannot declare a3_candidate_type"):
        SelectionEvidenceItem(
            evidence_id="direct",
            source_kind="GOVERNED_SELECTION_OUTCOME",
            source_ref="direct:item",
            source_digest=D0,
            option_id="one",
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="VALID_REASON",
            a3_candidate_type="SPECIALIST_STRATEGY_TENDENCY",
            direction="POSITIVE",
        )

    measurement = SelectionMeasurement(metric="COST", value=1, unit="usd")
    with pytest.raises(ValueError, match="only valid for trustworthy measured telemetry"):
        SelectionEvidenceItem(
            evidence_id="direct",
            source_kind="GOVERNED_SELECTION_OUTCOME",
            source_ref="direct:item",
            source_digest=D0,
            option_id="one",
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="VALID_REASON",
            direction="POSITIVE",
            measurement=measurement,
        )

    with pytest.raises(ValueError, match="explicit direction"):
        SelectionEvidenceItem(
            evidence_id="direct",
            source_kind="GOVERNED_SELECTION_OUTCOME",
            source_ref="direct:item",
            source_digest=D0,
            option_id="one",
            selection_type="SPECIALIST_STRATEGY",
            qualification_status="QUALIFIED",
            reason_code="VALID_REASON",
        )


def test_evidence_packet_schema_size_type_kind_duplicate_and_notes_guards():
    env = envelope()
    item = evidence_item()
    valid_kwargs = {
        "packet_id": "packet",
        "eligibility_envelope_ref": env.envelope_id,
        "eligibility_envelope_digest": env.digest,
        "selection_type": "SPECIALIST_STRATEGY",
        "collected_at": T1,
        "items": (item,),
    }
    with pytest.raises(ValueError, match="unsupported selection evidence schema"):
        SelectionEvidencePacket(**valid_kwargs, schema_version="wrong")
    with pytest.raises(ValueError, match="exceeds 256"):
        SelectionEvidencePacket(**{**valid_kwargs, "items": (item,) * 257})
    with pytest.raises(TypeError, match="SelectionEvidenceItem"):
        SelectionEvidencePacket(**{**valid_kwargs, "items": ("bad",)})

    model_item = evidence_item(selection_type="MODEL")
    with pytest.raises(ValueError, match="selection_type must match"):
        SelectionEvidencePacket(**{**valid_kwargs, "items": (model_item,)})
    with pytest.raises(ValueError, match="ids must be unique"):
        SelectionEvidencePacket(**{**valid_kwargs, "items": (item, item)})
    with pytest.raises(ValueError, match="notes exceeds"):
        SelectionEvidencePacket(
            **valid_kwargs,
            notes=tuple(f"note-{index}" for index in range(17)),
        )


def test_decision_schema_disposition_rank_scorer_and_notes_guards():
    kwargs = decision_kwargs()
    with pytest.raises(ValueError, match="unsupported selection decision schema"):
        SelectionDecision(**kwargs, schema_version="wrong")
    with pytest.raises(ValueError, match="unsupported decision disposition"):
        SelectionDecision(**{**kwargs, "disposition": "EXECUTE"})
    with pytest.raises(ValueError, match="ranked_candidate_ids"):
        SelectionDecision(**{**kwargs, "ranked_candidate_ids": ("one", "one")})
    with pytest.raises(ValueError, match="ranked_candidate_ids"):
        SelectionDecision(
            **{**kwargs, "ranked_candidate_ids": tuple(f"c{index}" for index in range(129))}
        )
    with pytest.raises(ValueError, match="canonical identifier"):
        SelectionDecision(**kwargs, scorer_version="Bad Scorer!")
    with pytest.raises(ValueError, match="notes exceeds"):
        SelectionDecision(
            **kwargs,
            notes=tuple(f"note-{index}" for index in range(17)),
        )


def test_qualifier_public_type_and_missing_option_guards():
    env = envelope()
    with pytest.raises(TypeError, match="ShadowCandidate"):
        qualify_a3_candidate("bad", env, option_id="one")
    with pytest.raises(TypeError, match="SelectionEligibilityEnvelope"):
        qualify_a3_candidate("bad", "bad", option_id="one")

    with pytest.raises(TypeError, match="ShadowComparison"):
        qualify_a3_comparison("bad", "bad", env, option_id="one")


def test_packet_builder_and_ranker_type_guards():
    env = envelope()
    with pytest.raises(TypeError, match="SelectionEligibilityEnvelope"):
        build_evidence_packet("bad", collected_at=T1, items=())
    with pytest.raises(TypeError, match="SelectionEligibilityEnvelope"):
        rank_shadow_selection(
            "bad",
            "bad",
            actual_deterministic_choice_id="one",
            evaluated_at=T1,
        )

    packet = build_evidence_packet(env, collected_at=T1, items=())
    with pytest.raises(TypeError, match="SelectionEvidencePacket"):
        rank_shadow_selection(
            env,
            "bad",
            actual_deterministic_choice_id="one",
            evaluated_at=T1,
        )

    empty = envelope(candidates=())
    empty_packet = build_evidence_packet(empty, collected_at=T1, items=())
    decision = rank_shadow_selection(
        empty,
        empty_packet,
        actual_deterministic_choice_id=None,
        evaluated_at=T1,
    )
    assert decision.disposition == "NO_ELIGIBLE_CANDIDATES"
    assert decision.ranked_candidate_ids == ()
