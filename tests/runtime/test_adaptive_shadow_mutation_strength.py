from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

import orchestra_runtime.adaptive.shadow as shadow_module
from orchestra_runtime.adaptive.models import (
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
)
from orchestra_runtime.adaptive.shadow import (
    JsonlShadowStore,
    ShadowCandidate,
    ShadowComparison,
    ShadowSignal,
    ShadowStoreLayout,
    build_shadow_comparison,
    build_shadow_signal,
    learn_shadow_candidates,
)

USER = "shadow-user"
PROJECT = "Baelfyre/Orchestra"
T0 = "2026-08-18T00:00:00Z"
T1 = "2026-08-18T00:01:00Z"
T2 = "2026-08-18T00:02:00Z"
T3 = "2026-08-18T00:03:00Z"
T4 = "2026-08-18T00:04:00Z"
T5 = "2026-08-18T00:05:00Z"
T6 = "2026-08-18T00:06:00Z"


def digest(index: int) -> str:
    return f"{index:064x}"


def project_scope(user: str = USER, project: str = PROJECT) -> AdaptiveScope:
    return AdaptiveScope(scope_type="project", user_key=user, project_key=project)


def signal(
    *,
    value: object = "compact",
    observed_at: str = T0,
    source_digest: str = digest(1),
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
        source_ref=f"evidence:{source_digest[-8:]}:{observed_at}",
        source_digest=source_digest,
        observed_at=observed_at,
        measurement=measurement,
    )


def candidate(*, value: object = "compact", subject_key: str = "docs.response_style") -> ShadowCandidate:
    return learn_shadow_candidates(
        (
            signal(value=value, subject_key=subject_key, source_digest=digest(1), observed_at=T0),
            signal(value=value, subject_key=subject_key, source_digest=digest(2), observed_at=T1),
        )
    )[0]


def comparison(*, value: object = "compact") -> ShadowComparison:
    item = candidate(value=value)
    return build_shadow_comparison(
        item,
        actual_deterministic_choice=value,
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )


def candidate_payload(**changes: object) -> dict:
    payload = candidate().to_dict()
    payload.update(changes)
    return payload


def comparison_payload(**changes: object) -> dict:
    payload = comparison().to_dict()
    payload.update(changes)
    return payload


def test_text_exact_limits_control_boundary_and_keyword_only_contract():
    assert shadow_module._text("x" * 512, "field") == "x" * 512
    with pytest.raises(ValueError, match="exceeds maximum length"):
        shadow_module._text("x" * 513, "field")
    with pytest.raises(ValueError, match="control characters"):
        shadow_module._text("a" + chr(31) + "b", "field")
    assert shadow_module._text("a b", "field") == "a b"
    with pytest.raises(TypeError):
        shadow_module._text("x", "field", 10)


def test_measurement_exact_schema_equality_zero_boundary_and_unit_limit():
    extra = {
        "measurement_status": "TRUSTWORTHY_MEASURED",
        "metric": "COST",
        "numeric_value": 1,
        "unit": "USD",
        "extra": "forbidden",
    }
    with pytest.raises(ValueError, match="contain exactly"):
        shadow_module._measurement(extra, "MEASURED_COST")

    bad_status = {
        "measurement_status": "ZZZ_NOT_TRUSTWORTHY",
        "metric": "COST",
        "numeric_value": 1,
        "unit": "USD",
    }
    with pytest.raises(ValueError, match="trustworthy and measured"):
        shadow_module._measurement(bad_status, "MEASURED_COST")

    bad_metric = {
        "measurement_status": "TRUSTWORTHY_MEASURED",
        "metric": "A",
        "numeric_value": 1,
        "unit": "USD",
    }
    with pytest.raises(ValueError, match="metric must be COST"):
        shadow_module._measurement(bad_metric, "MEASURED_COST")

    zero = {
        "measurement_status": "TRUSTWORTHY_MEASURED",
        "metric": "COST",
        "numeric_value": 0,
        "unit": "U" * 64,
    }
    measured = shadow_module._measurement(zero, "MEASURED_COST")
    assert measured is not None
    assert measured["numeric_value"] == 0
    assert measured["unit"] == "U" * 64

    too_long = dict(zero, unit="U" * 65)
    with pytest.raises(ValueError, match="exceeds maximum length"):
        shadow_module._measurement(too_long, "MEASURED_COST")


def test_signal_fail_closed_versions_source_provenance_and_id_limit():
    base = signal()
    payload = base.to_dict()

    for field in ("schema_version", "learner_rule_version"):
        modified = dict(payload)
        modified[field] = "aaa"
        with pytest.raises(ValueError):
            ShadowSignal.from_dict(modified)

    for wrong_source in ("VALIDATION_EVIDENCE", "REMEDIATION_EVIDENCE"):
        with pytest.raises(ValueError, match="strategy decision evidence"):
            signal(
                signal_type="SPECIALIST_STRATEGY_ACCEPTED",
                source_kind=wrong_source,
                subject_key="strategy.review_order",
            )

    with pytest.raises(ValueError, match="requires measured telemetry"):
        signal(
            signal_type="MEASURED_COST",
            source_kind="VALIDATION_EVIDENCE",
            subject_key="workflow.cost",
            value=0,
            measurement={
                "measurement_status": "TRUSTWORTHY_MEASURED",
                "metric": "COST",
                "numeric_value": 0,
                "unit": "USD",
            },
        )

    allowed = dict(payload, signal_id="s" * 256)
    assert ShadowSignal.from_dict(allowed).signal_id == "s" * 256
    rejected = dict(payload, signal_id="s" * 257)
    with pytest.raises(ValueError, match="exceeds maximum length"):
        ShadowSignal.from_dict(rejected)

    assert len(base.signal_id) == len("signal-") + 24


def test_signal_build_remains_keyword_only():
    scope = project_scope()
    with pytest.raises(TypeError):
        ShadowSignal.build(
            scope,
            signal_type="USER_SELECTION",
            subject_key="docs.response_style",
            observed_value="compact",
            source_kind="A1_VALIDATED_OBSERVATION",
            source_ref="evidence:test",
            source_digest=digest(1),
            observed_at=T0,
        )


def test_shadow_records_are_frozen_and_slotted():
    records = (
        (signal(), "signal_id"),
        (candidate(), "candidate_id"),
        (comparison(), "comparison_id"),
        (ShadowStoreLayout.build(USER, root=Path("/tmp/a3-shadow-layout-strength")), "root"),
    )
    for record, field in records:
        assert not hasattr(record, "__dict__")
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, getattr(record, field))


def test_candidate_fail_closed_versions_authority_identity_and_boundaries():
    base = candidate()
    payload = base.to_dict()

    for field in ("schema_version", "learner_rule_version", "confidence_method"):
        modified = dict(payload)
        modified[field] = "aaa"
        with pytest.raises(ValueError):
            ShadowCandidate.from_dict(modified)

    integer_true = dict(payload, shadow_only=1)
    with pytest.raises(ValueError, match="cannot become execution or promotion authority"):
        ShadowCandidate.from_dict(integer_true)

    lower_promotion = dict(payload, promotion_state="A")
    with pytest.raises(ValueError, match="cannot become execution or promotion authority"):
        ShadowCandidate.from_dict(lower_promotion)

    for confidence in (0.0, 1.0):
        boundary = dict(payload, confidence=confidence)
        assert ShadowCandidate.from_dict(boundary).confidence == confidence

    allowed = dict(payload, candidate_id="c" * 256)
    assert ShadowCandidate.from_dict(allowed).candidate_id == "c" * 256
    rejected = dict(payload, candidate_id="c" * 257)
    with pytest.raises(ValueError, match="exceeds maximum length"):
        ShadowCandidate.from_dict(rejected)

    refs_256 = dict(payload)
    refs_256["supporting_signal_refs"] = ["r" * 256, "short-ref"]
    assert len(ShadowCandidate.from_dict(refs_256).supporting_signal_refs) == 2
    refs_257 = dict(refs_256)
    refs_257["supporting_signal_refs"] = ["r" * 257, "short-ref"]
    with pytest.raises(ValueError, match="exceeds maximum length"):
        ShadowCandidate.from_dict(refs_257)


def test_candidate_support_count_requires_exact_ref_and_digest_cardinality():
    base = candidate_payload()
    cases = []

    more_refs = dict(base)
    more_refs["supporting_signal_refs"] = ["a", "b", "c"]
    cases.append(more_refs)

    more_digests = dict(base)
    more_digests["supporting_signal_digests"] = [digest(10), digest(11), digest(12)]
    cases.append(more_digests)

    fewer_refs = dict(base, distinct_support_count=3)
    fewer_refs["supporting_signal_refs"] = ["a", "b"]
    fewer_refs["supporting_signal_digests"] = [digest(10), digest(11), digest(12)]
    cases.append(fewer_refs)

    fewer_digests = dict(base, distinct_support_count=3)
    fewer_digests["supporting_signal_refs"] = ["a", "b", "c"]
    fewer_digests["supporting_signal_digests"] = [digest(10), digest(11)]
    cases.append(fewer_digests)

    for payload in cases:
        with pytest.raises(ValueError, match="distinct support count must equal"):
            ShadowCandidate.from_dict(payload)


def test_candidate_from_dict_missing_authority_and_confidence_fields_fail_closed():
    base = candidate_payload()
    for field in ("confidence", "shadow_only"):
        modified = dict(base)
        modified.pop(field)
        with pytest.raises((TypeError, ValueError)):
            ShadowCandidate.from_dict(modified)


def test_candidate_notes_are_serialized_when_present():
    rejected = learn_shadow_candidates(
        (
            signal(source_digest=digest(1), observed_at=T0),
            signal(source_digest=digest(2), observed_at=T2),
            signal(
                source_digest=digest(3),
                observed_at=T1,
                signal_type="USER_REJECTION",
            ),
        )
    )[0]
    assert rejected.notes
    assert rejected.to_dict()["notes"] == list(rejected.notes)


def test_comparison_fail_closed_versions_authority_cardinality_and_id_limits():
    base = comparison()
    payload = base.to_dict()

    for field in ("schema_version", "learner_rule_version"):
        modified = dict(payload)
        modified[field] = "aaa"
        with pytest.raises(ValueError):
            ShadowComparison.from_dict(modified)

    lower_controller = dict(payload, execution_controlled_by="A")
    with pytest.raises(ValueError, match="cannot control execution"):
        ShadowComparison.from_dict(lower_controller)

    integer_false = dict(payload, shadow_influenced_execution=0)
    with pytest.raises(ValueError, match="cannot control execution"):
        ShadowComparison.from_dict(integer_false)

    missing_shadow_flag = dict(payload)
    missing_shadow_flag.pop("shadow_influenced_execution")
    with pytest.raises(ValueError, match="cannot control execution"):
        ShadowComparison.from_dict(missing_shadow_flag)

    refs_more = dict(payload, outcome_evidence_refs=["one", "two"], outcome_evidence_digests=[digest(1)])
    digests_more = dict(payload, outcome_evidence_refs=["one"], outcome_evidence_digests=[digest(1), digest(2)])
    for modified in (refs_more, digests_more):
        with pytest.raises(ValueError, match="equal unique counts"):
            ShadowComparison.from_dict(modified)

    for field in ("comparison_id", "candidate_ref"):
        allowed = dict(payload, **{field: "x" * 256})
        assert getattr(ShadowComparison.from_dict(allowed), field) == "x" * 256
        rejected = dict(payload, **{field: "x" * 257})
        with pytest.raises(ValueError, match="exceeds maximum length"):
            ShadowComparison.from_dict(rejected)

    assert isinstance(base.digest, str)
    assert not callable(base.digest)
    assert len(base.comparison_id) == len("comparison-") + 24


def test_keyword_only_store_layout_store_learning_and_comparison_contracts(tmp_path: Path):
    with pytest.raises(TypeError):
        ShadowStoreLayout.build(USER, tmp_path)
    with pytest.raises(TypeError):
        JsonlShadowStore(USER, tmp_path)
    with pytest.raises(TypeError):
        learn_shadow_candidates((signal(),), None)
    with pytest.raises(TypeError):
        build_shadow_comparison(candidate(), "compact", "deterministic:test", T2)


def test_store_accepts_equal_distinct_user_key_and_rejects_greater_user_key(tmp_path: Path):
    same_user = ("x" + USER)[1:]
    assert same_user == USER
    assert same_user is not USER

    store = JsonlShadowStore(USER, root=tmp_path / "same-user")
    accepted = signal(scope=project_scope(user=same_user))
    assert store.append_signal(accepted) == accepted

    greater_user = "zzzz-shadow-user"
    with pytest.raises(ValueError, match="shadow signal user mismatch"):
        JsonlShadowStore(USER, root=tmp_path / "greater-signal").append_signal(
            signal(scope=project_scope(user=greater_user))
        )

    greater_candidate = learn_shadow_candidates(
        (
            signal(scope=project_scope(user=greater_user), source_digest=digest(20), observed_at=T0),
            signal(scope=project_scope(user=greater_user), source_digest=digest(21), observed_at=T1),
        )
    )[0]
    with pytest.raises(ValueError, match="shadow candidate user mismatch"):
        JsonlShadowStore(USER, root=tmp_path / "greater-candidate").write_candidates((greater_candidate,))

    greater_comparison = build_shadow_comparison(
        greater_candidate,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )
    with pytest.raises(ValueError, match="shadow comparison user mismatch"):
        JsonlShadowStore(USER, root=tmp_path / "greater-comparison").append_comparison(greater_comparison)


def test_store_load_rejects_greater_user_records(tmp_path: Path):
    greater_user = "zzzz-shadow-user"
    greater_scope = project_scope(user=greater_user)
    greater_signal = signal(scope=greater_scope)
    greater_candidate = learn_shadow_candidates(
        (
            signal(scope=greater_scope, source_digest=digest(30), observed_at=T0),
            signal(scope=greater_scope, source_digest=digest(31), observed_at=T1),
        )
    )[0]
    greater_comparison = build_shadow_comparison(
        greater_candidate,
        actual_deterministic_choice="compact",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )

    signal_store = JsonlShadowStore(USER, root=tmp_path / "signals")
    signal_store.layout.root.mkdir(parents=True, exist_ok=True)
    signal_store.layout.signals_path.write_text(json.dumps(greater_signal.to_dict()) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="shadow signal store user mismatch"):
        signal_store.load_signals()

    candidate_store = JsonlShadowStore(USER, root=tmp_path / "candidates")
    candidate_store.layout.root.mkdir(parents=True, exist_ok=True)
    candidate_store.layout.candidates_path.write_text(
        json.dumps(
            {
                "schema_version": shadow_module.SHADOW_CANDIDATE_STATE_SCHEMA_VERSION,
                "learner_rule_version": shadow_module.SHADOW_RULE_VERSION,
                "candidates": [greater_candidate.to_dict()],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="shadow candidate state user mismatch"):
        candidate_store.load_candidates()

    comparison_store = JsonlShadowStore(USER, root=tmp_path / "comparisons")
    comparison_store.layout.root.mkdir(parents=True, exist_ok=True)
    comparison_store.layout.comparisons_path.write_text(
        json.dumps(greater_comparison.to_dict()) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="shadow comparison store user mismatch"):
        comparison_store.load_comparisons()


def test_store_write_operations_create_full_parent_chain_when_called_first(tmp_path: Path):
    candidates_store = JsonlShadowStore(USER, root=tmp_path / "fresh-candidates" / "nested")
    candidates_store.write_candidates((candidate(),))
    assert candidates_store.layout.candidates_path.is_file()

    comparisons_store = JsonlShadowStore(USER, root=tmp_path / "fresh-comparisons" / "nested")
    comparisons_store.append_comparison(comparison())
    assert comparisons_store.layout.comparisons_path.is_file()


def test_candidate_state_lower_versions_fail_closed(tmp_path: Path):
    for field in ("schema_version", "learner_rule_version"):
        store = JsonlShadowStore(USER, root=tmp_path / field)
        store.layout.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": shadow_module.SHADOW_CANDIDATE_STATE_SCHEMA_VERSION,
            "learner_rule_version": shadow_module.SHADOW_RULE_VERSION,
            "candidates": [],
        }
        payload[field] = "aaa"
        store.layout.candidates_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError):
            store.load_candidates()


def test_jsonl_error_reports_exact_first_line_number(tmp_path: Path):
    path = tmp_path / "records.jsonl"
    path.write_text("\n{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"blank line at 1$"):
        JsonlShadowStore._load_jsonl(path, lambda payload: payload, "record")

    path.write_text("{broken}\n{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"at line 1:"):
        JsonlShadowStore._load_jsonl(path, lambda payload: payload, "record")


def test_candidate_type_exact_precedence_for_strategy_user_and_workflow():
    strategy = signal(
        signal_type="SPECIALIST_STRATEGY_ACCEPTED",
        source_kind="STRATEGY_DECISION_EVIDENCE",
        subject_key="strategy.review_order",
    )
    user = signal(signal_type="USER_SELECTION")
    workflow = signal(
        signal_type="VALIDATION_OUTCOME",
        source_kind="VALIDATION_EVIDENCE",
        subject_key="workflow.validation_result",
    )
    assert shadow_module._candidate_type((strategy,)) == "SPECIALIST_STRATEGY_TENDENCY"
    assert shadow_module._candidate_type((user,)) == "USER_PREFERENCE_TENDENCY"
    assert shadow_module._candidate_type((workflow,)) == "WORKFLOW_TENDENCY"
    assert shadow_module._candidate_type((workflow, user, strategy)) == "SPECIALIST_STRATEGY_TENDENCY"


def test_candidate_identity_uses_exact_24_digest_characters():
    identifier = shadow_module._candidate_identity(
        project_scope(), "docs.response_style", "USER_PREFERENCE_TENDENCY", "compact"
    )
    assert identifier.startswith("candidate-")
    assert len(identifier) == len("candidate-") + 24


def test_non_explicit_confirmed_pattern_is_not_treated_as_explicit():
    scope = project_scope()
    inferred = AdaptivePattern(
        pattern_id="pattern-inferred",
        scope=scope,
        subject_key="docs.response_style",
        value="compact",
        status="confirmed",
        evidence_class="INFERRED_CANDIDATE",
        evidence_refs=("observation:1",),
        observation_count=2,
        confidence=0.8,
        created_at=T0,
        updated_at=T1,
    )
    profile = AdaptiveProfile(
        profile_id="profile-test",
        user_key=USER,
        generated_at=T2,
        patterns=(inferred,),
        source_head_digest=None,
    )
    assert shadow_module._explicit_patterns(profile) == {}


def test_learning_continues_past_one_off_group_to_later_durable_group():
    results = learn_shadow_candidates(
        (
            signal(value="one-off", source_digest=digest(40), observed_at=T0),
            signal(value="durable", source_digest=digest(41), observed_at=T1),
            signal(value="durable", source_digest=digest(42), observed_at=T2),
        )
    )
    assert len(results) == 1
    assert results[0].candidate_value == "durable"


def test_explicit_preference_dominates_when_explicit_value_sorts_after_candidate_value():
    scope = project_scope()
    explicit = AdaptivePattern(
        pattern_id="pattern-explicit-zulu",
        scope=scope,
        subject_key="docs.response_style",
        value="zulu",
        status="confirmed",
        evidence_class="EXPLICIT_SCOPED_PREFERENCE",
        evidence_refs=("explicit:1",),
        observation_count=1,
        confidence=1.0,
        created_at=T0,
        updated_at=T0,
    )
    profile = AdaptiveProfile(
        profile_id="profile-explicit-zulu",
        user_key=USER,
        generated_at=T1,
        patterns=(explicit,),
        source_head_digest=None,
    )
    learned = learn_shadow_candidates(
        (
            signal(value="alpha", source_digest=digest(43), observed_at=T1),
            signal(value="alpha", source_digest=digest(44), observed_at=T2),
        ),
        explicit_profile=profile,
    )[0]
    assert learned.status == "BLOCKED_BY_EXPLICIT_PREFERENCE"
    assert learned.explicit_conflict_ref == explicit.pattern_id


def test_nonblocked_previous_candidate_is_recomputed_with_new_support():
    previous = candidate()
    learned = learn_shadow_candidates(
        (
            signal(source_digest=digest(1), observed_at=T0),
            signal(source_digest=digest(2), observed_at=T1),
            signal(source_digest=digest(45), observed_at=T3),
        ),
        previous_candidates=(previous,),
    )[0]
    assert learned.status == "CANDIDATE"
    assert learned.distinct_support_count == 3
    assert learned.last_seen == T3
    assert "post-block evidence observed; candidate remains shadow-only" not in learned.notes


def test_blocked_previous_candidate_retains_when_new_evidence_is_older_not_only_equal():
    blocked = ShadowCandidate.from_dict(
        candidate_payload(
            status="BLOCKED_BY_EXPLICIT_PREFERENCE",
            explicit_conflict_ref="explicit:future",
            last_seen=T4,
        )
    )
    retained = learn_shadow_candidates(
        (
            signal(source_digest=digest(1), observed_at=T0),
            signal(source_digest=digest(2), observed_at=T1),
        ),
        previous_candidates=(blocked,),
    )[0]
    assert retained == blocked


def test_retaining_blocked_group_does_not_stop_later_groups():
    blocked = ShadowCandidate.from_dict(
        candidate_payload(
            status="BLOCKED_BY_EXPLICIT_PREFERENCE",
            explicit_conflict_ref="explicit:future",
            last_seen=T4,
        )
    )
    results = learn_shadow_candidates(
        (
            signal(value="compact", source_digest=digest(1), observed_at=T0),
            signal(value="compact", source_digest=digest(2), observed_at=T1),
            signal(value="detailed", source_digest=digest(46), observed_at=T2),
            signal(value="detailed", source_digest=digest(47), observed_at=T3),
        ),
        previous_candidates=(blocked,),
    )
    assert {item.candidate_value for item in results} == {"compact", "detailed"}
    assert next(item for item in results if item.candidate_value == "compact") == blocked


def test_latest_negative_at_same_time_as_last_positive_rejects_and_latest_negative_wins():
    learned = learn_shadow_candidates(
        (
            signal(source_digest=digest(50), observed_at=T1),
            signal(source_digest=digest(51), observed_at=T3),
            signal(source_digest=digest(52), observed_at=T0, signal_type="USER_REJECTION"),
            signal(source_digest=digest(53), observed_at=T3, signal_type="USER_REJECTION"),
        )
    )[0]
    assert learned.status == "REJECTED"
    assert learned.explicit_conflict_ref is None
    assert "latest explicit negative evidence rejects this shadow candidate" in learned.notes


def test_confidence_progression_is_exact_and_caps_support_contribution_at_five():
    expected = {
        2: 0.66,
        3: 0.74,
        4: 0.82,
        5: 0.90,
        6: 0.90,
    }
    for count, confidence in expected.items():
        signals = tuple(
            signal(
                source_digest=digest(100 + index),
                observed_at=f"2026-08-18T00:{index:02d}:00Z",
            )
            for index in range(count)
        )
        learned = learn_shadow_candidates(signals)[0]
        assert learned.distinct_support_count == count
        assert learned.confidence == confidence


def test_confidence_negative_penalty_is_exact_and_caps_at_three_negatives():
    expected = {
        0: 0.66,
        1: 0.58,
        2: 0.50,
        3: 0.42,
        4: 0.42,
    }
    for negative_count, confidence in expected.items():
        positives = (
            signal(source_digest=digest(200), observed_at=T5),
            signal(source_digest=digest(201), observed_at=T6),
        )
        negatives = tuple(
            signal(
                source_digest=digest(210 + index),
                observed_at=f"2026-08-18T00:0{index}:30Z",
                signal_type="USER_REJECTION",
            )
            for index in range(negative_count)
        )
        learned = learn_shadow_candidates(negatives + positives)[0]
        assert learned.status == "CANDIDATE"
        assert learned.confidence == confidence


def test_comparison_blocks_noncandidate_status_even_when_status_sorts_after_candidate():
    rejected = ShadowCandidate.from_dict(candidate_payload(status="REJECTED"))
    result = build_shadow_comparison(
        rejected,
        actual_deterministic_choice=rejected.candidate_value,
        actual_choice_ref="deterministic:rejected",
        evaluated_at=T3,
    )
    assert result.disposition == "CANDIDATE_BLOCKED"
    assert result.execution_controlled_by == "DETERMINISTIC_ORCHESTRA"
    assert result.shadow_influenced_execution is False


def test_comparison_does_not_treat_greater_shadow_value_as_equal():
    greater = candidate(value="zulu")
    result = build_shadow_comparison(
        greater,
        actual_deterministic_choice="alpha",
        actual_choice_ref="deterministic:ordering",
        evaluated_at=T3,
    )
    assert result.disposition == "MISMATCH"


def test_comparison_uses_value_equality_not_object_identity():
    shadow_value = int("1000")
    actual_value = int("1000")
    assert shadow_value == actual_value
    assert shadow_value is not actual_value
    numeric = candidate(value=shadow_value, subject_key="workflow.batch_size")
    result = build_shadow_comparison(
        numeric,
        actual_deterministic_choice=actual_value,
        actual_choice_ref="deterministic:numeric",
        evaluated_at=T3,
    )
    assert result.disposition == "MATCH"
