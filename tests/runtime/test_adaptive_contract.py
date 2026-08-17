from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from orchestra_runtime.adaptive.models import AdaptiveObservation, AdaptiveScope
from orchestra_runtime.adaptive.observations import (
    append_explicit_preference,
    append_inferred_candidate,
)
from orchestra_runtime.adaptive.privacy import build_export_bundle
from orchestra_runtime.adaptive.profile import materialize_profile, profile_from_dict
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "adaptive"
SCHEMAS = ROOT / "machine" / "schemas"
USER = "fixture-user"
T0 = "2026-08-17T10:00:00Z"
T1 = "2026-08-17T10:01:00Z"
T2 = "2026-08-17T10:02:00Z"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def project_scope(user: str = USER, project: str = "Baelfyre/Orchestra") -> AdaptiveScope:
    return AdaptiveScope.from_dict(
        {"scope_type": "project", "user_key": user, "project_key": project}
    )


def make_store(tmp_path: Path, user: str = USER) -> JsonlAdaptiveStore:
    return JsonlAdaptiveStore(user, root=tmp_path / "adaptive")


def test_machine_fixtures_validate_against_draft_2020_12_schemas():
    pairs = (
        ("observation.v1.json", "adaptive-observation.schema.json"),
        ("profile.v1.json", "adaptive-profile.schema.json"),
        ("export.v1.json", "adaptive-export.schema.json"),
    )
    for fixture_name, schema_name in pairs:
        instance = load_json(FIXTURES / fixture_name)
        schema = load_json(SCHEMAS / schema_name)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def test_fixture_materialization_and_export_are_deterministic(tmp_path: Path):
    observation_payload = load_json(FIXTURES / "observation.v1.json")
    expected_profile = load_json(FIXTURES / "profile.v1.json")
    expected_export = load_json(FIXTURES / "export.v1.json")
    observation = AdaptiveObservation.from_dict(observation_payload)
    profile = materialize_profile(USER, (observation,), generated_at=T1)
    assert profile.to_dict() == expected_profile

    store = make_store(tmp_path)
    store.layout.root.mkdir(parents=True, exist_ok=True)
    store.observations_path.write_text(
        json.dumps(observation_payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    assert build_export_bundle(store, profile) == expected_export


def test_non_learnable_sensitive_and_raw_sources_fail_closed(tmp_path: Path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="non-learnable"):
        append_explicit_preference(
            store,
            scope=project_scope(),
            subject_key="governance.merge_gate",
            value="allow",
            occurred_at=T0,
            source_ref="test:governance",
        )
    with pytest.raises(ValueError, match="sensitive key"):
        append_explicit_preference(
            store,
            scope=project_scope(),
            subject_key="tool.preference",
            value={"api_token": "should-not-be-stored"},
            occurred_at=T0,
            source_ref="test:sensitive",
        )
    with pytest.raises(ValueError, match="credential-like"):
        append_explicit_preference(
            store,
            scope=project_scope(),
            subject_key="tool.preference",
            value="Bearer abcdefghijklmnopqrstuvwxyz0123456789",
            occurred_at=T0,
            source_ref="test:credential",
        )
    with pytest.raises(ValueError, match="source_type is not allowed"):
        store.append(
            event_type="EXPLICIT_PREFERENCE_SET",
            scope=project_scope(),
            subject_key="docs.response_style",
            evidence_class="EXPLICIT_SCOPED_PREFERENCE",
            source_type="raw_conversation",
            source_ref="conversation:raw",
            occurred_at=T0,
            payload={"value": "compact"},
        )


def test_current_instruction_requires_task_session_scope(tmp_path: Path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="task_session"):
        append_explicit_preference(
            store,
            scope=project_scope(),
            subject_key="docs.response_style",
            value="compact",
            occurred_at=T0,
            source_ref="test:current",
            current_instruction=True,
        )
    task_scope = AdaptiveScope.from_dict(
        {
            "scope_type": "task_session",
            "user_key": USER,
            "project_key": "Baelfyre/Orchestra",
            "specialist_slug": "beatrice",
            "task_session_key": "task-1",
        }
    )
    observation = append_explicit_preference(
        store,
        scope=task_scope,
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="test:current-task",
        current_instruction=True,
    )
    assert observation.evidence_class == "EXPLICIT_CURRENT_INSTRUCTION"


def test_explicit_inferred_and_governed_outcomes_remain_distinct(tmp_path: Path):
    store = make_store(tmp_path)
    append_explicit_preference(
        store,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="test:explicit",
    )
    append_inferred_candidate(
        store,
        scope=project_scope(),
        subject_key="docs.example_density",
        value="low",
        confidence=0.75,
        evidence_refs=("test:evidence-a", "test:evidence-b"),
        occurred_at=T1,
        source_ref="test:inferred",
    )
    store.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=project_scope(),
        subject_key="workflow.phase_outcome",
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref="retrospective:test",
        occurred_at=T2,
        payload={"phase_id": "A1", "phase_status": "accepted"},
    )
    profile = materialize_profile(USER, store.load_observations(), generated_at=T2)
    patterns = {pattern.subject_key: pattern for pattern in profile.patterns}
    assert set(patterns) == {"docs.response_style", "docs.example_density"}
    assert patterns["docs.response_style"].status == "confirmed"
    assert patterns["docs.response_style"].confidence == 1.0
    assert patterns["docs.example_density"].status == "candidate"
    assert patterns["docs.example_density"].confidence == 0.75


def test_invalid_confidence_and_unknown_schema_versions_fail_closed(tmp_path: Path):
    store = make_store(tmp_path)
    append_inferred_candidate(
        store,
        scope=project_scope(),
        subject_key="docs.example_density",
        value="low",
        confidence=1.5,
        evidence_refs=("test:evidence",),
        occurred_at=T0,
        source_ref="test:bad-confidence",
    )
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        materialize_profile(USER, store.load_observations(), generated_at=T1)

    observation_payload = load_json(FIXTURES / "observation.v1.json")
    observation_payload["schema_version"] = "orchestra.adaptive-observation.v999"
    with pytest.raises(ValueError, match="unsupported adaptive observation schema"):
        AdaptiveObservation.from_dict(observation_payload)

    profile_payload = load_json(FIXTURES / "profile.v1.json")
    profile_payload["schema_version"] = "orchestra.adaptive-profile.v999"
    with pytest.raises(ValueError, match="unsupported adaptive profile schema"):
        profile_from_dict(profile_payload)
