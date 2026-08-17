from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..evidence import canonical_json_bytes, normalize_timestamp
from .models import AdaptiveProfile, AdaptiveScope, validate_subject_key
from .store import JsonlAdaptiveStore

ADAPTIVE_EXPORT_SCHEMA_VERSION = "orchestra.adaptive-export.v1"


def build_export_bundle(
    store: JsonlAdaptiveStore,
    profile: AdaptiveProfile | None,
    *,
    include_observations: bool = True,
) -> dict[str, Any]:
    if profile is not None and profile.user_key != store.user_key:
        raise ValueError("profile user_key does not match adaptive store")
    observations = store.load_observations() if include_observations else ()
    return {
        "schema_version": ADAPTIVE_EXPORT_SCHEMA_VERSION,
        "user_key": store.user_key,
        "profile": None if profile is None else profile.to_dict(),
        "observations": [item.to_dict() for item in observations],
        "forensic_secure_erase_guaranteed": False,
    }


def export_bundle(
    store: JsonlAdaptiveStore,
    profile: AdaptiveProfile | None,
    destination: Path,
    *,
    include_observations: bool = True,
) -> None:
    payload = build_export_bundle(store, profile, include_observations=include_observations)
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


def delete_scope(
    store: JsonlAdaptiveStore,
    scope: AdaptiveScope,
    *,
    occurred_at: str | None = None,
    subject_key: str | None = None,
) -> int:
    if scope.user_key != store.user_key:
        raise ValueError("scope user_key does not match adaptive store")
    normalized_subject = None if subject_key is None else validate_subject_key(subject_key)
    timestamp = occurred_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return store.compact(
        lambda observation: not (
            observation.scope.identity == scope.identity
            and (normalized_subject is None or observation.subject_key == normalized_subject)
        ),
        occurred_at=timestamp,
        reason="explicit-user-delete",
    )


def prune_expired(store: JsonlAdaptiveStore, *, now: str) -> int:
    normalized_now = normalize_timestamp(now, "now")
    return store.compact(
        lambda observation: observation.expires_at is None or observation.expires_at > normalized_now,
        occurred_at=normalized_now,
        reason="retention-expiry",
    )
