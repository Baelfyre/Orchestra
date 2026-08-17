from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import (
    append_explicit_preference,
    append_preference_removal,
)
from orchestra_runtime.adaptive.privacy import delete_scope, prune_expired
from orchestra_runtime.adaptive.profile import materialize_profile
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

USER = "fixture-user"
T0 = "2026-08-17T10:00:00Z"
T1 = "2026-08-17T10:01:00Z"
T2 = "2026-08-17T10:02:00Z"


def scope(project: str = "Baelfyre/Orchestra") -> AdaptiveScope:
    return AdaptiveScope.from_dict(
        {"scope_type": "project", "user_key": USER, "project_key": project}
    )


def append_pref(
    store: JsonlAdaptiveStore,
    record_scope: AdaptiveScope,
    *,
    subject: str = "docs.response_style",
    value="compact",
    occurred_at: str = T0,
    source_ref: str = "test:explicit",
    expires_at: str | None = None,
):
    return append_explicit_preference(
        store,
        scope=record_scope,
        subject_key=subject,
        value=value,
        occurred_at=occurred_at,
        source_ref=source_ref,
        expires_at=expires_at,
    )


def test_preference_removal_prevents_materialization(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    record_scope = scope()
    append_pref(store, record_scope)
    append_preference_removal(
        store,
        scope=record_scope,
        subject_key="docs.response_style",
        occurred_at=T1,
        source_ref="test:remove",
    )
    profile = materialize_profile(USER, store.load_observations(), generated_at=T2)
    assert profile.patterns == ()


def test_delete_compaction_rechains_and_invalidates_profile(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    scope_a = scope("Baelfyre/Orchestra")
    scope_b = scope("Baelfyre/Other")
    append_pref(store, scope_a, source_ref="test:a")
    retained_before = append_pref(
        store,
        scope_b,
        subject="docs.detail_level",
        value="bounded",
        occurred_at=T1,
        source_ref="test:b",
    )
    profile = materialize_profile(USER, store.load_observations(), generated_at=T2)
    store.write_profile(profile)

    assert delete_scope(store, scope_a, occurred_at=T2) == 1
    retained = store.load_observations()
    assert len(retained) == 1
    assert retained[0].scope.identity == scope_b.identity
    assert retained[0].sequence == 1
    assert retained[0].previous_observation_digest is None
    assert retained[0].observation_id != retained_before.observation_id
    assert not store.layout.profile_path.exists()

    metadata = json.loads(store.layout.metadata_path.read_text(encoding="utf-8"))
    assert metadata["generation"] == 1
    assert metadata["removed_count"] == 1
    assert metadata["observation_count"] == 1
    assert metadata["head_digest"] == retained[0].digest


def test_expiry_pruning_uses_normalized_time_and_rechains(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    record_scope = scope()
    append_pref(store, record_scope, expires_at=T1, source_ref="test:expiring")
    append_pref(
        store,
        record_scope,
        subject="docs.detail_level",
        value="bounded",
        occurred_at=T1,
        source_ref="test:persistent",
    )
    assert prune_expired(store, now=T1) == 1
    remaining = store.load_observations()
    assert len(remaining) == 1
    assert remaining[0].subject_key == "docs.detail_level"
    assert remaining[0].sequence == 1
    assert remaining[0].previous_observation_digest is None
    assert prune_expired(store, now=T2) == 0
