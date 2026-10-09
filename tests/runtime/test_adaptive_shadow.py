from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import (
    append_explicit_preference,
    append_preference_removal,
)
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
)
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"
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
    measurement: dict | None = None,
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


def test_shadow_records_validate_against_machine_schemas():
    first = signal(source_digest=D0, observed_at=T0)
    second = signal(source_digest=D1, observed_at=T1)
    candidate = learn_shadow_candidates((first, second))[0]
    comparison = build_shadow_comparison(
        candidate,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )
    for instance, schema_name in (
        (first.to_dict(), "adaptive-shadow-signal.schema.json"),
        (candidate.to_dict(), "adaptive-shadow-candidate.schema.json"),
        (comparison.to_dict(), "adaptive-shadow-comparison.schema.json"),
    ):
        schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def test_a1_signal_extraction_is_bounded_and_does_not_write_shadow_state(tmp_path: Path):
    a1 = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    append_explicit_preference(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="test:explicit",
    )
    append_preference_removal(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        occurred_at=T1,
        source_ref="test:remove",
    )
    a1.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=project_scope(),
        subject_key="workflow.phase_outcome",
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref="retrospective:test",
        occurred_at=T2,
        payload={"phase_id": "A3", "phase_status": "accepted"},
    )
    signals = extract_a1_shadow_signals(a1.load_observations())
    assert [item.signal_type for item in signals] == [
        "USER_SELECTION",
        "USER_REJECTION",
        "TERMINAL_DISPOSITION",
    ]
    assert signals[0].observed_value == "compact"
    assert signals[1].observed_value == "REMOVED"
    assert signals[2].observed_value == "accepted"
    assert not (a1.layout.root / "shadow").exists()


def test_strategy_signal_requires_explicit_strategy_decision_evidence():
    with pytest.raises(ValueError, match="strategy decision evidence"):
        signal(
            signal_type="SPECIALIST_STRATEGY_ACCEPTED",
            source_kind="GOVERNED_RETROSPECTIVE",
            subject_key="strategy.review_order",
        )
    accepted = signal(
        signal_type="SPECIALIST_STRATEGY_ACCEPTED",
        source_kind="STRATEGY_DECISION_EVIDENCE",
        subject_key="strategy.review_order",
    )
    assert accepted.source_kind == "STRATEGY_DECISION_EVIDENCE"


def test_generic_phase_success_never_becomes_strategy_success(tmp_path: Path):
    a1 = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    a1.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=project_scope(),
        subject_key="workflow.phase_outcome",
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref="retrospective:phase",
        occurred_at=T0,
        payload={"phase_id": "A3", "phase_status": "accepted"},
    )
    extracted = extract_a1_shadow_signals(a1.load_observations())
    assert len(extracted) == 1
    assert extracted[0].signal_type == "TERMINAL_DISPOSITION"
    assert extracted[0].source_kind == "A1_VALIDATED_OBSERVATION"
    assert "STRATEGY" not in extracted[0].signal_type


def test_measured_latency_and_cost_require_trustworthy_measurement():
    with pytest.raises(ValueError, match="trustworthy measurement"):
        signal(
            signal_type="MEASURED_LATENCY",
            source_kind="MEASURED_TELEMETRY",
            subject_key="workflow.latency",
            value=12.5,
        )
    measured = signal(
        signal_type="MEASURED_COST",
        source_kind="MEASURED_TELEMETRY",
        subject_key="workflow.cost",
        value=1.25,
        measurement={
            "measurement_status": "TRUSTWORTHY_MEASURED",
            "metric": "COST",
            "numeric_value": 1.25,
            "unit": "USD",
        },
    )
    assert measured.measurement["metric"] == "COST"


def test_raw_conversation_and_non_learnable_subjects_fail_closed():
    with pytest.raises(ValueError, match="source kind"):
        signal(source_kind="RAW_CONVERSATION")
    with pytest.raises(ValueError, match="non-learnable"):
        signal(subject_key="governance.merge_gate")


def test_one_off_choice_and_duplicate_evidence_do_not_create_candidate():
    first = signal(source_digest=D0, observed_at=T0)
    duplicate = signal(source_digest=D0, observed_at=T1)
    assert learn_shadow_candidates((first,)) == ()
    assert learn_shadow_candidates((first, duplicate)) == ()


def test_two_distinct_signals_create_shadow_candidate_without_promotion():
    candidate = learn_shadow_candidates(
        (
            signal(source_digest=D0, observed_at=T0),
            signal(source_digest=D1, observed_at=T1),
        )
    )[0]
    assert candidate.status == "CANDIDATE"
    assert candidate.distinct_support_count == 2
    assert candidate.shadow_only is True
    assert candidate.promotion_state == "NOT_PROMOTED"
    assert 0.0 <= candidate.confidence <= 1.0


def test_mixed_users_fail_closed_and_scopes_do_not_leak():
    other = AdaptiveScope(scope_type="project", user_key="other-user", project_key=PROJECT)
    with pytest.raises(ValueError, match="mix users"):
        learn_shadow_candidates(
            (
                signal(source_digest=D0, observed_at=T0),
                signal(source_digest=D1, observed_at=T1, scope=other),
            )
        )
    different_project = AdaptiveScope(scope_type="project", user_key=USER, project_key="Baelfyre/Other")
    candidates = learn_shadow_candidates(
        (
            signal(source_digest=D0, observed_at=T0),
            signal(source_digest=D1, observed_at=T1),
            signal(source_digest=D2, observed_at=T2, scope=different_project),
            signal(source_digest=D3, observed_at=T3, scope=different_project),
        )
    )
    assert len(candidates) == 2
    assert len({item.scope.identity for item in candidates}) == 2


def test_explicit_preference_blocks_conflicting_shadow_candidate(tmp_path: Path):
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
    candidate = learn_shadow_candidates(
        (
            signal(value="detailed", source_digest=D0, observed_at=T0),
            signal(value="detailed", source_digest=D1, observed_at=T1),
        ),
        explicit_profile=profile,
    )[0]
    assert candidate.status == "BLOCKED_BY_EXPLICIT_PREFERENCE"
    assert candidate.explicit_conflict_ref == profile.patterns[0].pattern_id


def test_blocked_candidate_does_not_reactivate_without_post_removal_support(tmp_path: Path):
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
    evidence = (
        signal(value="detailed", source_digest=D0, observed_at=T0),
        signal(value="detailed", source_digest=D1, observed_at=T1),
    )
    blocked = learn_shadow_candidates(evidence, explicit_profile=profile)[0]
    append_preference_removal(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        occurred_at=T2,
        source_ref="explicit:remove",
    )
    removed_profile = materialize_profile(USER, a1.load_observations(), generated_at=T2)
    retained = learn_shadow_candidates(
        evidence,
        explicit_profile=removed_profile,
        previous_candidates=(blocked,),
    )[0]
    assert retained == blocked

    reactivated = learn_shadow_candidates(
        evidence + (signal(value="detailed", source_digest=D2, observed_at=T3),),
        explicit_profile=removed_profile,
        previous_candidates=(blocked,),
    )[0]
    assert reactivated.status == "CANDIDATE"
    assert reactivated.last_seen == T3


def test_latest_explicit_negative_evidence_rejects_candidate():
    candidate = learn_shadow_candidates(
        (
            signal(value="compact", source_digest=D0, observed_at=T0),
            signal(value="compact", source_digest=D1, observed_at=T1),
            signal(
                value="compact",
                source_digest=D2,
                observed_at=T2,
                signal_type="USER_REJECTION",
            ),
        )
    )[0]
    assert candidate.status == "REJECTED"
    assert any("negative evidence" in note for note in candidate.notes)


def test_shadow_comparison_records_match_or_mismatch_but_never_controls_execution():
    candidate = learn_shadow_candidates(
        (
            signal(source_digest=D0, observed_at=T0),
            signal(source_digest=D1, observed_at=T1),
        )
    )[0]
    match = build_shadow_comparison(
        candidate,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:route",
        evaluated_at=T2,
    )
    mismatch = build_shadow_comparison(
        candidate,
        actual_deterministic_choice="detailed",
        actual_choice_ref="deterministic:route",
        evaluated_at=T3,
    )
    assert match.disposition == "MATCH"
    assert mismatch.disposition == "MISMATCH"
    for comparison in (match, mismatch):
        assert comparison.execution_controlled_by == "DETERMINISTIC_ORCHESTRA"
        assert comparison.shadow_influenced_execution is False


def test_blocked_candidate_comparison_is_non_authorizing(tmp_path: Path):
    a1 = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    append_explicit_preference(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="explicit",
    )
    profile = materialize_profile(USER, a1.load_observations(), generated_at=T1)
    blocked = learn_shadow_candidates(
        (
            signal(value="detailed", source_digest=D0, observed_at=T0),
            signal(value="detailed", source_digest=D1, observed_at=T1),
        ),
        explicit_profile=profile,
    )[0]
    comparison = build_shadow_comparison(
        blocked,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:explicit-precedence",
        evaluated_at=T2,
    )
    assert comparison.disposition == "CANDIDATE_BLOCKED"
    assert comparison.shadow_influenced_execution is False


def test_shadow_store_persists_separately_from_a1_profile_and_a2_context(tmp_path: Path):
    root = tmp_path / "adaptive"
    a1 = JsonlAdaptiveStore(USER, root=root)
    append_explicit_preference(
        a1,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="explicit",
    )
    profile = materialize_profile(USER, a1.load_observations(), generated_at=T1)
    a1.write_profile(profile)
    profile_before = a1.layout.profile_path.read_bytes()
    observations_before = a1.observations_path.read_bytes()

    shadow = JsonlShadowStore(USER, root=root)
    first = shadow.append_signal(signal(source_digest=D0, observed_at=T0))
    second = shadow.append_signal(signal(source_digest=D1, observed_at=T1))
    candidates = learn_shadow_candidates(shadow.load_signals(), explicit_profile=profile)
    shadow.write_candidates(candidates)
    shadow.append_comparison(
        build_shadow_comparison(
            candidates[0],
            actual_deterministic_choice="compact",
            actual_choice_ref="deterministic:test",
            evaluated_at=T2,
        )
    )

    assert shadow.layout.root == a1.layout.root / "shadow" / "a3"
    assert a1.layout.profile_path.read_bytes() == profile_before
    assert a1.observations_path.read_bytes() == observations_before
    assert shadow.load_signals() == (first, second)
    assert shadow.load_candidates() == candidates
    assert len(shadow.load_comparisons()) == 1


def test_malformed_shadow_state_fails_closed(tmp_path: Path):
    shadow = JsonlShadowStore(USER, root=tmp_path / "adaptive")
    shadow.layout.root.mkdir(parents=True, exist_ok=True)
    shadow.layout.signals_path.write_text("{broken-json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed shadow signal JSONL"):
        shadow.load_signals()
    shadow.layout.candidates_path.write_text(
        json.dumps({"schema_version": "orchestra.adaptive-shadow-candidate-state.v999", "candidates": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported shadow candidate state schema"):
        shadow.load_candidates()


def test_shadow_model_rejects_execution_authority_forgery():
    candidate = learn_shadow_candidates(
        (
            signal(source_digest=D0, observed_at=T0),
            signal(source_digest=D1, observed_at=T1),
        )
    )[0]
    payload = build_shadow_comparison(
        candidate,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    ).to_dict()
    payload["shadow_influenced_execution"] = True
    with pytest.raises(ValueError, match="cannot control execution"):
        ShadowComparison.from_dict(payload)

    candidate_payload = candidate.to_dict()
    candidate_payload["promotion_state"] = "PROMOTED"
    with pytest.raises(ValueError, match="cannot become execution or promotion authority"):
        ShadowCandidate.from_dict(candidate_payload)
