from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import append_explicit_preference
from orchestra_runtime.adaptive.profile import materialize_profile
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

USER = "fixture-user"
T0 = "2026-08-17T10:00:00Z"
T1 = "2026-08-17T10:01:00Z"
T2 = "2026-08-17T10:02:00Z"


def scope(user: str = USER, project: str = "Baelfyre/Orchestra") -> AdaptiveScope:
    return AdaptiveScope.from_dict(
        {"scope_type": "project", "user_key": user, "project_key": project}
    )


def store_at(tmp_path: Path, user: str = USER) -> JsonlAdaptiveStore:
    return JsonlAdaptiveStore(user, root=tmp_path / "adaptive")


def append_pref(
    store: JsonlAdaptiveStore,
    *,
    subject: str = "docs.response_style",
    value="compact",
    occurred_at: str = T0,
    source_ref: str = "test:explicit",
):
    return append_explicit_preference(
        store,
        scope=scope(store.user_key),
        subject_key=subject,
        value=value,
        occurred_at=occurred_at,
        source_ref=source_ref,
    )


def test_store_round_trip_and_hash_chain_tamper_detection(tmp_path: Path):
    store = store_at(tmp_path)
    first = append_pref(store)
    second = append_pref(
        store,
        subject="docs.detail_level",
        value="bounded",
        occurred_at=T1,
        source_ref="test:second",
    )
    assert store.load_observations() == (first, second)
    assert second.sequence == 2
    assert second.previous_observation_digest == first.digest

    lines = store.observations_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[1])
    payload["previous_observation_digest"] = "0" * 64
    lines[1] = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    store.observations_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash-chain mismatch"):
        store.load_observations()


def test_store_fails_closed_on_blank_malformed_sequence_and_user(tmp_path: Path):
    store = store_at(tmp_path)
    store.layout.root.mkdir(parents=True, exist_ok=True)
    store.observations_path.write_text("\n", encoding="utf-8")
    with pytest.raises(ValueError, match="blank line"):
        store.load_observations()

    store.observations_path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed adaptive JSONL"):
        store.load_observations()

    fixture = {
        "schema_version": "orchestra.adaptive-observation.v1",
        "memory_rule_version": "orchestra.adaptive-memory-rules.v1",
        "observation_id": "obs-test",
        "sequence": 2,
        "event_type": "EXPLICIT_PREFERENCE_SET",
        "scope": scope().to_dict(),
        "subject_key": "docs.response_style",
        "evidence_class": "EXPLICIT_SCOPED_PREFERENCE",
        "source_type": "explicit_user_instruction",
        "source_ref": "test:fixture",
        "occurred_at": T0,
        "payload": {"value": "compact"},
        "previous_observation_digest": "0" * 64,
    }
    store.observations_path.write_text(json.dumps(fixture) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sequence gap"):
        store.load_observations()

    fixture["sequence"] = 1
    fixture["previous_observation_digest"] = None
    fixture["scope"]["user_key"] = "other-user"
    store.observations_path.write_text(json.dumps(fixture) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="user mismatch"):
        store.load_observations()


def test_repository_local_store_and_cross_user_scope_are_rejected(tmp_path: Path):
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    with pytest.raises(ValueError, match="outside the repository"):
        JsonlAdaptiveStore(
            USER,
            root=repository_root / ".orchestra" / "adaptive",
            repository_root=repository_root,
        )

    store = store_at(tmp_path / "external")
    with pytest.raises(ValueError, match="scope user_key does not match"):
        append_explicit_preference(
            store,
            scope=scope("other-user"),
            subject_key="docs.response_style",
            value="compact",
            occurred_at=T0,
            source_ref="test:cross-user",
        )


def test_profile_write_rejects_stale_head_and_corrupt_profile_recovers(tmp_path: Path):
    store = store_at(tmp_path)
    append_pref(store)
    profile = materialize_profile(USER, store.load_observations(), generated_at=T1)
    store.write_profile(profile)
    assert store.load_profile() == profile

    store.layout.profile_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed adaptive profile JSON"):
        store.load_profile()
    recovered = store.recover_profile(generated_at=T2)
    assert recovered.source_head_digest == profile.source_head_digest
    assert store.load_profile() == recovered

    append_pref(
        store,
        subject="docs.detail_level",
        value="bounded",
        occurred_at=T2,
        source_ref="test:later",
    )
    with pytest.raises(ValueError, match="source head is stale"):
        store.write_profile(recovered)


@pytest.mark.parametrize(
    "payload",
    (
        {"scope_type": "global_user", "user_key": USER, "project_key": "forbidden"},
        {"scope_type": "project", "user_key": USER},
        {"scope_type": "specialist", "user_key": USER},
        {"scope_type": "task_session", "user_key": USER},
        {"scope_type": "unknown", "user_key": USER},
    ),
)
def test_invalid_scope_shapes_fail_closed(payload):
    with pytest.raises(ValueError):
        AdaptiveScope.from_dict(payload)
