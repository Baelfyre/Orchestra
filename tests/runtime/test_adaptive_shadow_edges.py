from __future__ import annotations

import json
from pathlib import Path

import pytest

import orchestra_runtime.adaptive.shadow as shadow_module
from orchestra_runtime.adaptive.models import AdaptiveObservation, AdaptiveScope
from orchestra_runtime.adaptive.observations import append_explicit_preference
from orchestra_runtime.adaptive.profile import materialize_profile
from orchestra_runtime.adaptive.shadow import (
    JsonlShadowStore,
    ShadowCandidate,
    ShadowComparison,
    ShadowSignal,
    build_shadow_comparison,
    build_shadow_signal,
    extract_a1_shadow_signals,
    learn_shadow_candidates,
    shadow_signal_from_a1_observation,
)
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

USER = "shadow-user"
PROJECT = "Baelfyre/Orchestra"
T0 = "2026-08-18T00:00:00Z"
T1 = "2026-08-18T00:01:00Z"
T2 = "2026-08-18T00:02:00Z"
T3 = "2026-08-18T00:03:00Z"
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64


def project_scope(user: str = USER, project: str = PROJECT) -> AdaptiveScope:
    return AdaptiveScope(scope_type="project", user_key=user, project_key=project)


def signal(
    *,
    value: object = "compact",
    observed_at: str = T0,
    source_digest: str = D0,
    signal_type: str = "USER_SELECTION",
    source_kind: str = "A1_VALIDATED_OBSERVATION",
    subject_key: str = "docs.response_style",
    scope: AdaptiveScope | None = None,
    measurement: object | None = None,
) -> ShadowSignal:
    return build_shadow_signal(
        scope=scope or project_scope(),
        signal_type=signal_type,
        subject_key=subject_key,
        observed_value=value,
        source_kind=source_kind,
        source_ref=f"evidence:{source_digest[:8]}:{observed_at}",
        source_digest=source_digest,
        observed_at=observed_at,
        measurement=measurement,
    )


def candidate(*, scope: AdaptiveScope | None = None, value: object = "compact") -> ShadowCandidate:
    selected_scope = scope or project_scope()
    return learn_shadow_candidates(
        (
            signal(scope=selected_scope, value=value, source_digest=D0, observed_at=T0),
            signal(scope=selected_scope, value=value, source_digest=D1, observed_at=T1),
        )
    )[0]


def comparison(*, scope: AdaptiveScope | None = None) -> ShadowComparison:
    item = candidate(scope=scope)
    return build_shadow_comparison(
        item,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )


@pytest.mark.parametrize(
    ("value", "message"),
    (
        (None, "must be a string"),
        ("", "non-empty"),
        ("x" * 513, "exceeds maximum length"),
        ("bad\x01value", "control characters"),
    ),
)
def test_shadow_text_validation_edges(value: object, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        shadow_module._text(value, "field")


def test_shadow_scalar_validation_edges():
    assert shadow_module._scalar(True, "value") is True
    assert shadow_module._scalar(1, "value") == 1
    assert shadow_module._scalar(1.5, "value") == 1.5
    assert shadow_module._scalar("value", "value") == "value"
    with pytest.raises(TypeError, match="string, number, or boolean"):
        shadow_module._scalar({"not": "scalar"}, "value")


def test_shadow_measurement_validation_edges():
    with pytest.raises(ValueError, match="allowed only"):
        shadow_module._measurement({"unexpected": True}, "USER_SELECTION")
    with pytest.raises(ValueError, match="require trustworthy measurement"):
        shadow_module._measurement([], "MEASURED_COST")
    with pytest.raises(ValueError, match="contain exactly"):
        shadow_module._measurement({"measurement_status": "TRUSTWORTHY_MEASURED"}, "MEASURED_COST")
    with pytest.raises(ValueError, match="trustworthy and measured"):
        shadow_module._measurement(
            {
                "measurement_status": "ESTIMATED",
                "metric": "COST",
                "numeric_value": 1,
                "unit": "USD",
            },
            "MEASURED_COST",
        )
    with pytest.raises(ValueError, match="metric must be COST"):
        shadow_module._measurement(
            {
                "measurement_status": "TRUSTWORTHY_MEASURED",
                "metric": "LATENCY",
                "numeric_value": 1,
                "unit": "USD",
            },
            "MEASURED_COST",
        )
    for numeric in (True, -1):
        with pytest.raises(ValueError, match="non-negative number"):
            shadow_module._measurement(
                {
                    "measurement_status": "TRUSTWORTHY_MEASURED",
                    "metric": "COST",
                    "numeric_value": numeric,
                    "unit": "USD",
                },
                "MEASURED_COST",
            )
    with pytest.raises(TypeError, match="measurement.unit must be a string"):
        shadow_module._measurement(
            {
                "measurement_status": "TRUSTWORTHY_MEASURED",
                "metric": "COST",
                "numeric_value": 1,
                "unit": 1,
            },
            "MEASURED_COST",
        )
    measured = shadow_module._measurement(
        {
            "measurement_status": "TRUSTWORTHY_MEASURED",
            "metric": "LATENCY",
            "numeric_value": 12.5,
            "unit": "ms",
        },
        "MEASURED_LATENCY",
    )
    assert measured == {
        "measurement_status": "TRUSTWORTHY_MEASURED",
        "metric": "LATENCY",
        "numeric_value": 12.5,
        "unit": "ms",
    }


def test_shadow_signal_validation_envelope_edges():
    base = signal()
    payload = base.to_dict()

    with pytest.raises(TypeError, match="payload must be an object"):
        ShadowSignal.from_dict([])

    mutations = (
        ("schema_version", "orchestra.adaptive-shadow-signal.v999", "unsupported shadow signal schema"),
        ("learner_rule_version", "orchestra.adaptive-shadow-rules.v999", "unsupported shadow learner rule"),
        ("signal_type", "UNKNOWN", "unsupported shadow signal type"),
        ("source_kind", "UNKNOWN", "unsupported shadow source kind"),
    )
    for field, value, message in mutations:
        modified = dict(payload)
        modified[field] = value
        with pytest.raises(ValueError, match=message):
            ShadowSignal.from_dict(modified)

    with pytest.raises(TypeError, match="scope must be AdaptiveScope"):
        ShadowSignal(
            signal_id=base.signal_id,
            scope={},
            signal_type=base.signal_type,
            subject_key=base.subject_key,
            observed_value=base.observed_value,
            source_kind=base.source_kind,
            source_ref=base.source_ref,
            source_digest=base.source_digest,
            observed_at=base.observed_at,
        )

    with pytest.raises(ValueError, match="requires measured telemetry"):
        signal(
            signal_type="MEASURED_LATENCY",
            source_kind="A1_VALIDATED_OBSERVATION",
            subject_key="workflow.latency",
            value=12.5,
            measurement={
                "measurement_status": "TRUSTWORTHY_MEASURED",
                "metric": "LATENCY",
                "numeric_value": 12.5,
                "unit": "ms",
            },
        )


def test_shadow_candidate_validation_envelope_edges():
    base = candidate()
    payload = base.to_dict()

    with pytest.raises(TypeError, match="payload must be an object"):
        ShadowCandidate.from_dict([])

    mutations = (
        ("schema_version", "orchestra.adaptive-shadow-candidate.v999", "unsupported shadow candidate schema"),
        ("learner_rule_version", "orchestra.adaptive-shadow-rules.v999", "unsupported shadow learner rule"),
        ("confidence_method", "UNKNOWN", "unsupported confidence method"),
        ("shadow_only", False, "cannot become execution or promotion authority"),
        ("promotion_state", "PROMOTED", "cannot become execution or promotion authority"),
        ("candidate_type", "UNKNOWN", "unsupported candidate type"),
        ("status", "UNKNOWN", "unsupported candidate status"),
        ("distinct_support_count", True, "must be an integer"),
        ("distinct_support_count", 1, "at least two distinct supporting signals"),
        ("confidence", True, "confidence must be numeric"),
        ("confidence", -0.1, "between 0 and 1"),
        ("confidence", 1.1, "between 0 and 1"),
    )
    for field, value, message in mutations:
        modified = dict(payload)
        modified[field] = value
        with pytest.raises((TypeError, ValueError), match=message):
            ShadowCandidate.from_dict(modified)

    mismatch = dict(payload)
    mismatch["supporting_signal_refs"] = mismatch["supporting_signal_refs"][:1]
    with pytest.raises(ValueError, match="distinct support count must equal"):
        ShadowCandidate.from_dict(mismatch)

    blocked_without_ref = dict(payload)
    blocked_without_ref["status"] = "BLOCKED_BY_EXPLICIT_PREFERENCE"
    with pytest.raises(ValueError, match="blocked candidates require explicit_conflict_ref"):
        ShadowCandidate.from_dict(blocked_without_ref)

    with pytest.raises(TypeError, match="scope must be AdaptiveScope"):
        ShadowCandidate(
            candidate_id=base.candidate_id,
            scope={},
            subject_key=base.subject_key,
            candidate_type=base.candidate_type,
            candidate_value=base.candidate_value,
            confidence=base.confidence,
            distinct_support_count=base.distinct_support_count,
            supporting_signal_refs=base.supporting_signal_refs,
            supporting_signal_digests=base.supporting_signal_digests,
            first_seen=base.first_seen,
            last_seen=base.last_seen,
        )


def test_shadow_comparison_validation_envelope_edges():
    item = candidate()
    base = build_shadow_comparison(
        item,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
        outcome_evidence_refs=("outcome:test",),
        outcome_evidence_digests=(D2,),
        notes=("bounded comparison evidence",),
    )
    payload = base.to_dict()
    assert payload["outcome_evidence_refs"] == ["outcome:test"]
    assert payload["notes"] == ["bounded comparison evidence"]

    with pytest.raises(TypeError, match="payload must be an object"):
        ShadowComparison.from_dict([])

    mutations = (
        ("schema_version", "orchestra.adaptive-shadow-comparison.v999", "unsupported shadow comparison schema"),
        ("learner_rule_version", "orchestra.adaptive-shadow-rules.v999", "unsupported shadow learner rule"),
        ("execution_controlled_by", "SHADOW", "cannot control execution"),
        ("shadow_influenced_execution", True, "cannot control execution"),
        ("disposition", "UNKNOWN", "unsupported comparison disposition"),
    )
    for field, value, message in mutations:
        modified = dict(payload)
        modified[field] = value
        with pytest.raises(ValueError, match=message):
            ShadowComparison.from_dict(modified)

    mismatch = dict(payload)
    mismatch["outcome_evidence_digests"] = []
    with pytest.raises(ValueError, match="equal unique counts"):
        ShadowComparison.from_dict(mismatch)

    with pytest.raises(TypeError, match="scope must be AdaptiveScope"):
        ShadowComparison(
            comparison_id=base.comparison_id,
            candidate_ref=base.candidate_ref,
            candidate_digest=base.candidate_digest,
            scope={},
            subject_key=base.subject_key,
            evaluated_at=base.evaluated_at,
            shadow_recommendation=base.shadow_recommendation,
            actual_deterministic_choice=base.actual_deterministic_choice,
            actual_choice_ref=base.actual_choice_ref,
            disposition=base.disposition,
        )

    incomparable = build_shadow_comparison(
        item,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T3,
        comparable=False,
    )
    assert incomparable.disposition == "NO_COMPARABLE_DETERMINISTIC_CHOICE"

    with pytest.raises(TypeError, match="candidate must be ShadowCandidate"):
        build_shadow_comparison(
            object(),
            actual_deterministic_choice="compact",
            actual_choice_ref="deterministic:test",
            evaluated_at=T3,
        )


def test_shadow_store_empty_and_user_isolation_edges(tmp_path: Path):
    empty = JsonlShadowStore(USER, root=tmp_path / "empty")
    assert empty.load_signals() == ()
    assert empty.load_candidates() == ()
    assert empty.load_comparisons() == ()

    other_scope = project_scope(user="other-user")
    other_signal = signal(scope=other_scope)
    other_candidate = candidate(scope=other_scope)
    other_comparison = comparison(scope=other_scope)

    with pytest.raises(ValueError, match="shadow signal user mismatch"):
        empty.append_signal(other_signal)
    with pytest.raises(ValueError, match="shadow candidate user mismatch"):
        empty.write_candidates((other_candidate,))
    with pytest.raises(ValueError, match="shadow comparison user mismatch"):
        empty.append_comparison(other_comparison)


def test_shadow_store_load_validation_edges(tmp_path: Path):
    malformed = JsonlShadowStore(USER, root=tmp_path / "malformed")
    malformed.layout.root.mkdir(parents=True, exist_ok=True)
    malformed.layout.candidates_path.write_text("{broken-json}", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed shadow candidate state JSON"):
        malformed.load_candidates()

    non_object = JsonlShadowStore(USER, root=tmp_path / "non-object")
    non_object.layout.root.mkdir(parents=True, exist_ok=True)
    non_object.layout.candidates_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="shadow candidate state must be an object"):
        non_object.load_candidates()

    bad_rule = JsonlShadowStore(USER, root=tmp_path / "bad-rule")
    bad_rule.layout.root.mkdir(parents=True, exist_ok=True)
    bad_rule.layout.candidates_path.write_text(
        json.dumps(
            {
                "schema_version": shadow_module.SHADOW_CANDIDATE_STATE_SCHEMA_VERSION,
                "learner_rule_version": "orchestra.adaptive-shadow-rules.v999",
                "candidates": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported shadow candidate state learner rule"):
        bad_rule.load_candidates()

    blank = JsonlShadowStore(USER, root=tmp_path / "blank")
    blank.layout.root.mkdir(parents=True, exist_ok=True)
    blank.layout.signals_path.write_text("\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contains blank line"):
        blank.load_signals()


def test_shadow_store_loaded_records_cannot_cross_users(tmp_path: Path):
    other_scope = project_scope(user="other-user")
    other_signal = signal(scope=other_scope)
    other_candidate = candidate(scope=other_scope)
    other_comparison = comparison(scope=other_scope)

    signal_store = JsonlShadowStore(USER, root=tmp_path / "signals")
    signal_store.layout.root.mkdir(parents=True, exist_ok=True)
    signal_store.layout.signals_path.write_text(json.dumps(other_signal.to_dict()) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="shadow signal store user mismatch"):
        signal_store.load_signals()

    candidate_store = JsonlShadowStore(USER, root=tmp_path / "candidates")
    candidate_store.layout.root.mkdir(parents=True, exist_ok=True)
    candidate_store.layout.candidates_path.write_text(
        json.dumps(
            {
                "schema_version": shadow_module.SHADOW_CANDIDATE_STATE_SCHEMA_VERSION,
                "learner_rule_version": shadow_module.SHADOW_RULE_VERSION,
                "candidates": [other_candidate.to_dict()],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="shadow candidate state user mismatch"):
        candidate_store.load_candidates()

    comparison_store = JsonlShadowStore(USER, root=tmp_path / "comparisons")
    comparison_store.layout.root.mkdir(parents=True, exist_ok=True)
    comparison_store.layout.comparisons_path.write_text(
        json.dumps(other_comparison.to_dict()) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="shadow comparison store user mismatch"):
        comparison_store.load_comparisons()


def observation(
    *,
    event_type: str,
    evidence_class: str,
    payload: dict,
    subject_key: str = "docs.response_style",
) -> AdaptiveObservation:
    return AdaptiveObservation(
        observation_id=f"obs-{event_type.casefold()}",
        sequence=1,
        event_type=event_type,
        scope=project_scope(),
        subject_key=subject_key,
        evidence_class=evidence_class,
        source_type="test",
        source_ref="test:observation",
        occurred_at=T0,
        payload=payload,
        previous_observation_digest=None,
    )


def test_a1_shadow_translation_fail_closed_and_skip_edges():
    with pytest.raises(TypeError, match="observation must be AdaptiveObservation"):
        shadow_signal_from_a1_observation(object())

    ignored = observation(
        event_type="INFERRED_PATTERN_CANDIDATE",
        evidence_class="INFERRED_CANDIDATE",
        payload={"value": "compact"},
    )
    assert shadow_signal_from_a1_observation(ignored) is None

    missing_value = observation(
        event_type="EXPLICIT_PREFERENCE_SET",
        evidence_class="EXPLICIT_SCOPED_PREFERENCE",
        payload={},
    )
    with pytest.raises(ValueError, match="lacks value"):
        shadow_signal_from_a1_observation(missing_value)

    bad_outcome = observation(
        event_type="GOVERNED_OUTCOME_RECORDED",
        evidence_class="GOVERNED_OUTCOME",
        payload={"phase_status": {"not": "scalar"}},
        subject_key="workflow.phase_outcome",
    )
    with pytest.raises(ValueError, match="lacks a scalar terminal disposition"):
        shadow_signal_from_a1_observation(bad_outcome)

    selected = observation(
        event_type="EXPLICIT_PREFERENCE_SET",
        evidence_class="EXPLICIT_SCOPED_PREFERENCE",
        payload={"value": "compact"},
    )
    extracted = extract_a1_shadow_signals((ignored, selected))
    assert len(extracted) == 1
    assert extracted[0].signal_type == "USER_SELECTION"


def test_shadow_candidate_additional_evidence_edges(tmp_path: Path):
    assert learn_shadow_candidates(()) == ()

    earlier_negative = learn_shadow_candidates(
        (
            signal(value="compact", source_digest=D0, observed_at=T0),
            signal(
                value="compact",
                source_digest=D2,
                observed_at=T1,
                signal_type="USER_REJECTION",
            ),
            signal(value="compact", source_digest=D1, observed_at=T2),
        )
    )[0]
    assert earlier_negative.status == "CANDIDATE"
    assert any("conflicting negative evidence" in note for note in earlier_negative.notes)

    a1 = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    append_explicit_preference(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="explicit:compact",
    )
    profile = materialize_profile(USER, a1.load_observations(), generated_at=T1)
    matching = learn_shadow_candidates(
        (
            signal(value="compact", source_digest=D0, observed_at=T0),
            signal(value="compact", source_digest=D1, observed_at=T1),
        ),
        explicit_profile=profile,
    )[0]
    assert matching.status == "CANDIDATE"
    assert matching.explicit_conflict_ref is None
