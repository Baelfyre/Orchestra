from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import append_explicit_preference
from orchestra_runtime.adaptive.privacy import build_export_bundle, delete_scope, export_bundle
from orchestra_runtime.adaptive.profile import materialize_profile
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore

USER = "fixture-user"
T0 = "2026-08-17T10:00:00Z"
T1 = "2026-08-17T10:01:00Z"
T2 = "2026-08-17T10:02:00Z"


def scope(user: str = USER) -> AdaptiveScope:
    return AdaptiveScope.from_dict(
        {
            "scope_type": "project",
            "user_key": user,
            "project_key": "Baelfyre/Orchestra",
        }
    )


def test_export_is_structured_and_never_claims_forensic_erase(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    append_explicit_preference(
        store,
        scope=scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="test:explicit",
    )
    profile = materialize_profile(USER, store.load_observations(), generated_at=T1)

    payload = build_export_bundle(store, profile)
    assert payload["schema_version"] == "orchestra.adaptive-export.v1"
    assert payload["forensic_secure_erase_guaranteed"] is False
    assert len(payload["observations"]) == 1
    assert payload["profile"] == profile.to_dict()

    destination = tmp_path / "exports" / "adaptive.json"
    export_bundle(store, profile, destination)
    assert json.loads(destination.read_text(encoding="utf-8")) == payload
    assert build_export_bundle(store, profile, include_observations=False)["observations"] == []


def test_export_and_delete_reject_cross_user_scope(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    other = JsonlAdaptiveStore("other-user", root=tmp_path / "other" / "adaptive")
    append_explicit_preference(
        other,
        scope=scope("other-user"),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="test:other",
    )
    other_profile = materialize_profile(
        "other-user", other.load_observations(), generated_at=T1
    )
    with pytest.raises(ValueError, match="profile user_key does not match"):
        build_export_bundle(store, other_profile)
    with pytest.raises(ValueError, match="scope user_key does not match"):
        delete_scope(store, scope("other-user"), occurred_at=T2)
