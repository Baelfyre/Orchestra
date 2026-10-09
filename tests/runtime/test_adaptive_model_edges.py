from __future__ import annotations

import pytest

from orchestra_runtime.adaptive.models import (
    AdaptiveObservation,
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
)

T0 = "2026-08-17T10:00:00Z"
T1 = "2026-08-17T10:01:00Z"
USER = "fixture-user"


def project_scope(user: str = USER) -> AdaptiveScope:
    return AdaptiveScope("project", user, project_key="Baelfyre/Orchestra")


def valid_observation(**overrides) -> AdaptiveObservation:
    values = {
        "observation_id": "obs-test",
        "sequence": 1,
        "event_type": "EXPLICIT_PREFERENCE_SET",
        "scope": project_scope(),
        "subject_key": "docs.response_style",
        "evidence_class": "EXPLICIT_SCOPED_PREFERENCE",
        "source_type": "explicit_user_instruction",
        "source_ref": "test:source",
        "occurred_at": T0,
        "payload": {"value": "compact"},
        "previous_observation_digest": None,
    }
    values.update(overrides)
    return AdaptiveObservation(**values)


def valid_pattern(**overrides) -> AdaptivePattern:
    values = {
        "pattern_id": "pattern-test",
        "scope": project_scope(),
        "subject_key": "docs.response_style",
        "value": "compact",
        "status": "confirmed",
        "evidence_class": "EXPLICIT_SCOPED_PREFERENCE",
        "evidence_refs": ("test:source",),
        "observation_count": 1,
        "confidence": 1.0,
        "created_at": T0,
        "updated_at": T0,
    }
    values.update(overrides)
    return AdaptivePattern(**values)


def test_scope_variants_and_invalid_text_edges():
    assert AdaptiveScope("global_user", USER).to_dict() == {
        "scope_type": "global_user",
        "user_key": USER,
    }
    specialist = AdaptiveScope("specialist", USER, specialist_slug="Beatrice")
    assert specialist.specialist_slug == "beatrice"
    task = AdaptiveScope(
        "task_session",
        USER,
        project_key="Baelfyre/Orchestra",
        specialist_slug="Beatrice",
        task_session_key="task-1",
    )
    assert task.to_dict()["task_session_key"] == "task-1"

    with pytest.raises(TypeError, match="user_key must be a string"):
        AdaptiveScope("global_user", 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="user_key must be non-empty"):
        AdaptiveScope("global_user", " ")
    with pytest.raises(ValueError, match="control characters"):
        AdaptiveScope("project", USER, project_key="bad\nproject")
    with pytest.raises(ValueError, match="canonical identifier"):
        AdaptiveScope("specialist", USER, specialist_slug="bad slug")
    with pytest.raises(TypeError, match="payload must be an object"):
        AdaptiveScope.from_dict([])  # type: ignore[arg-type]


def test_observation_rejects_invalid_shape_and_event_evidence_combinations():
    with pytest.raises(ValueError, match="positive integer"):
        valid_observation(sequence=True)
    with pytest.raises(TypeError, match="scope must be AdaptiveScope"):
        valid_observation(scope={})
    with pytest.raises(ValueError, match="unsupported adaptive event"):
        valid_observation(event_type="UNKNOWN")
    with pytest.raises(ValueError, match="unsupported evidence class"):
        valid_observation(evidence_class="UNKNOWN")
    with pytest.raises(ValueError, match="GOVERNED_OUTCOME evidence"):
        valid_observation(event_type="GOVERNED_OUTCOME_RECORDED")
    with pytest.raises(ValueError, match="INFERRED_CANDIDATE evidence"):
        valid_observation(event_type="INFERRED_PATTERN_CANDIDATE")
    with pytest.raises(ValueError, match="explicit instruction evidence"):
        valid_observation(evidence_class="USER_FEEDBACK")
    with pytest.raises(ValueError, match="USER_FEEDBACK evidence"):
        valid_observation(event_type="EXPLICIT_PREFERENCE_REMOVED")
    with pytest.raises(ValueError, match="first observation must not declare"):
        valid_observation(previous_observation_digest="0" * 64)
    with pytest.raises(ValueError, match="only the first observation"):
        valid_observation(sequence=2)
    with pytest.raises(ValueError, match="expires_at must be later"):
        valid_observation(expires_at=T0)

    expiring = valid_observation(expires_at=T1)
    assert expiring.to_dict()["expires_at"] == T1
    assert expiring.digest
    with pytest.raises(TypeError, match="payload must be an object"):
        AdaptiveObservation.from_dict([])  # type: ignore[arg-type]


def test_pattern_validation_edges_and_optional_expiry():
    with pytest.raises(TypeError, match="scope must be AdaptiveScope"):
        valid_pattern(scope={})
    with pytest.raises(ValueError, match="unsupported pattern status"):
        valid_pattern(status="unknown")
    with pytest.raises(ValueError, match="preference or inferred evidence"):
        valid_pattern(evidence_class="GOVERNED_OUTCOME")
    with pytest.raises(ValueError, match="positive integer"):
        valid_pattern(observation_count=False)
    with pytest.raises(ValueError, match="between 0 and 1"):
        valid_pattern(confidence=True)
    with pytest.raises(ValueError, match="must not precede"):
        valid_pattern(created_at=T1, updated_at=T0)
    with pytest.raises(ValueError, match="confirmed with confidence 1.0"):
        valid_pattern(status="candidate")
    with pytest.raises(ValueError, match="sensitive key"):
        valid_pattern(value={"access_token": "blocked"})
    with pytest.raises(ValueError, match="duplicate values"):
        valid_pattern(evidence_refs=("same", "same"))
    with pytest.raises(ValueError, match="expires_at must be later"):
        valid_pattern(expires_at=T0)

    candidate = valid_pattern(
        status="candidate",
        evidence_class="INFERRED_CANDIDATE",
        confidence=0.5,
        expires_at=T1,
    )
    assert candidate.to_dict()["expires_at"] == T1


def test_profile_validation_edges():
    pattern = valid_pattern()
    with pytest.raises(TypeError, match="AdaptivePattern"):
        AdaptiveProfile("profile", USER, T0, ({},), None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="another user"):
        AdaptiveProfile("profile", USER, T0, (valid_pattern(scope=project_scope("other")),), None)
    with pytest.raises(ValueError, match="duplicate scope/subject"):
        AdaptiveProfile("profile", USER, T0, (pattern, pattern), None)

    profile = AdaptiveProfile("profile", USER, T0, (pattern,), "0" * 64)
    assert profile.source_head_digest == "0" * 64
    assert profile.digest
