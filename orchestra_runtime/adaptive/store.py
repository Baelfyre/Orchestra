from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..evidence import canonical_json_bytes, normalize_timestamp, receipt_digest
from .models import AdaptiveObservation, AdaptiveProfile, AdaptiveScope, ADAPTIVE_MEMORY_RULE_VERSION

ADAPTIVE_STORE_META_SCHEMA_VERSION = "orchestra.adaptive-store-meta.v1"
ADAPTIVE_STORE_LAYOUT_VERSION = 1
_ALLOWED_SOURCE_BY_EVENT = {
    "EXPLICIT_PREFERENCE_SET": frozenset({"explicit_user_instruction"}),
    "EXPLICIT_PREFERENCE_CORRECTED": frozenset({"explicit_user_instruction"}),
    "EXPLICIT_PREFERENCE_REMOVED": frozenset({"explicit_user_correction"}),
    "INFERRED_PATTERN_CANDIDATE": frozenset({"governed_pattern_materializer"}),
    "INFERRED_PATTERN_CONFIRMED": frozenset({"governed_pattern_materializer"}),
    "INFERRED_PATTERN_DEPRECATED": frozenset({"governed_pattern_materializer"}),
    "INFERRED_PATTERN_REJECTED": frozenset({"governed_pattern_materializer"}),
    "GOVERNED_OUTCOME_RECORDED": frozenset({"orchestra_phase_retrospective"}),
}


def default_adaptive_home() -> Path:
    configured = os.environ.get("ORCHESTRA_ADAPTIVE_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".orchestra" / "adaptive"


def _resolved(path: Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def assert_store_outside_repository(store_root: Path, repository_root: Path) -> None:
    store = _resolved(store_root)
    repo = _resolved(repository_root)
    if store == repo or repo in store.parents:
        raise ValueError("adaptive store must remain outside the repository working tree")


def _user_storage_key(user_key: str) -> str:
    text = str(user_key or "").strip()
    if not text:
        raise ValueError("user_key must be non-empty")
    return sha256(text.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True, slots=True)
class AdaptiveStoreLayout:
    root: Path
    user_key: str
    layout_version: int = ADAPTIVE_STORE_LAYOUT_VERSION

    @classmethod
    def build(
        cls,
        user_key: str,
        *,
        root: Path | None = None,
        repository_root: Path | None = None,
    ) -> "AdaptiveStoreLayout":
        base = _resolved(default_adaptive_home() if root is None else root)
        if repository_root is not None:
            assert_store_outside_repository(base, repository_root)
        normalized_user = str(user_key or "").strip()
        if not normalized_user:
            raise ValueError("user_key must be non-empty")
        return cls(
            root=base / f"v{ADAPTIVE_STORE_LAYOUT_VERSION}" / _user_storage_key(normalized_user),
            user_key=normalized_user,
        )

    @property
    def observations_path(self) -> Path:
        return self.root / "observations.jsonl"

    @property
    def profile_path(self) -> Path:
        return self.root / "profile.json"

    @property
    def metadata_path(self) -> Path:
        return self.root / "store-meta.json"


class JsonlAdaptiveStore:
    """Machine-local A1 store. It has no runtime routing or policy authority."""

    def __init__(
        self,
        user_key: str,
        *,
        root: Path | None = None,
        repository_root: Path | None = None,
    ):
        self.layout = AdaptiveStoreLayout.build(user_key, root=root, repository_root=repository_root)
        self.user_key = self.layout.user_key

    @property
    def observations_path(self) -> Path:
        return self.layout.observations_path

    def load_observations(self) -> tuple[AdaptiveObservation, ...]:
        path = self.observations_path
        if not path.exists():
            return ()
        observations: list[AdaptiveObservation] = []
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                raise ValueError(f"adaptive JSONL contains blank line at {lineno}")
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed adaptive JSONL at line {lineno}: {exc.msg}") from exc
            observation = AdaptiveObservation.from_dict(raw)
            if observation.scope.user_key != self.user_key:
                raise ValueError(f"adaptive observation user mismatch at line {lineno}")
            expected_sequence = len(observations) + 1
            if observation.sequence != expected_sequence:
                raise ValueError(
                    f"adaptive observation sequence gap at line {lineno}: expected {expected_sequence}, got {observation.sequence}"
                )
            expected_previous = None if not observations else observations[-1].digest
            if observation.previous_observation_digest != expected_previous:
                raise ValueError(f"adaptive observation hash-chain mismatch at line {lineno}")
            observations.append(observation)
        return tuple(observations)

    def append(
        self,
        *,
        event_type: str,
        scope: AdaptiveScope,
        subject_key: str,
        evidence_class: str,
        source_type: str,
        source_ref: str,
        occurred_at: str,
        payload: Mapping[str, Any],
        expires_at: str | None = None,
        memory_rule_version: str = ADAPTIVE_MEMORY_RULE_VERSION,
    ) -> AdaptiveObservation:
        if scope.user_key != self.user_key:
            raise ValueError("scope user_key does not match adaptive store")
        normalized_event = str(event_type or "").strip().upper()
        normalized_source = str(source_type or "").strip()
        if normalized_source not in _ALLOWED_SOURCE_BY_EVENT.get(normalized_event, frozenset()):
            raise ValueError("adaptive observation source_type is not allowed for this event type")
        observations = self.load_observations()
        sequence = len(observations) + 1
        previous = None if not observations else observations[-1].digest
        occurred = normalize_timestamp(occurred_at, "occurred_at")
        return self._append_validated(
            sequence=sequence,
            previous=previous,
            event_type=normalized_event,
            scope=scope,
            subject_key=subject_key,
            evidence_class=evidence_class,
            source_type=normalized_source,
            source_ref=source_ref,
            occurred_at=occurred,
            payload=payload,
            expires_at=expires_at,
            memory_rule_version=memory_rule_version,
        )

    def _append_validated(
        self,
        *,
        sequence: int,
        previous: str | None,
        event_type: str,
        scope: AdaptiveScope,
        subject_key: str,
        evidence_class: str,
        source_type: str,
        source_ref: str,
        occurred_at: str,
        payload: Mapping[str, Any],
        expires_at: str | None,
        memory_rule_version: str,
    ) -> AdaptiveObservation:
        identity_payload = {
            "sequence": sequence,
            "event_type": event_type,
            "scope": scope.to_dict(),
            "subject_key": subject_key,
            "evidence_class": evidence_class,
            "source_type": source_type,
            "source_ref": source_ref,
            "occurred_at": occurred_at,
            "payload": dict(payload),
            "previous_observation_digest": previous,
            "expires_at": expires_at,
            "memory_rule_version": memory_rule_version,
        }
        observation = AdaptiveObservation(
            observation_id=f"obs-{receipt_digest(identity_payload)[:24]}",
            sequence=sequence,
            event_type=event_type,
            scope=scope,
            subject_key=subject_key,
            evidence_class=evidence_class,
            source_type=source_type,
            source_ref=source_ref,
            occurred_at=occurred_at,
            payload=payload,
            previous_observation_digest=previous,
            expires_at=expires_at,
            memory_rule_version=memory_rule_version,
        )
        self.layout.root.mkdir(parents=True, exist_ok=True)
        with self.observations_path.open("ab") as handle:
            handle.write(canonical_json_bytes(observation.to_dict()) + b"\n")
        return observation

    def load_profile(self) -> AdaptiveProfile | None:
        path = self.layout.profile_path
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed adaptive profile JSON: {exc.msg}") from exc
        from .profile import profile_from_dict

        profile = profile_from_dict(raw)
        if profile.user_key != self.user_key:
            raise ValueError("adaptive profile user mismatch")
        return profile

    def write_profile(self, profile: AdaptiveProfile) -> None:
        if profile.user_key != self.user_key:
            raise ValueError("adaptive profile user mismatch")
        observations = self.load_observations()
        expected_head = None if not observations else observations[-1].digest
        if profile.source_head_digest != expected_head:
            raise ValueError("adaptive profile source head is stale or does not match the observation log")
        self.layout.root.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.layout.profile_path, canonical_json_bytes(profile.to_dict()) + b"\n")

    def recover_profile(self, *, generated_at: str) -> AdaptiveProfile:
        """Rebuild the derived profile from the validated JSONL source of truth."""
        from .profile import materialize_profile

        profile = materialize_profile(self.user_key, self.load_observations(), generated_at=generated_at)
        self.write_profile(profile)
        return profile

    def compact(
        self,
        retain: Callable[[AdaptiveObservation], bool],
        *,
        occurred_at: str,
        reason: str,
    ) -> int:
        observations = self.load_observations()
        retained = tuple(observation for observation in observations if retain(observation))
        removed_count = len(observations) - len(retained)
        if removed_count == 0:
            return 0
        rebuilt = _rechain(retained)
        data = b"".join(canonical_json_bytes(item.to_dict()) + b"\n" for item in rebuilt)
        self.layout.root.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.observations_path, data)
        if self.layout.profile_path.exists():
            self.layout.profile_path.unlink()
        metadata = self._next_metadata(
            occurred_at=occurred_at,
            reason=reason,
            removed_count=removed_count,
            observations=rebuilt,
        )
        _atomic_write(self.layout.metadata_path, canonical_json_bytes(metadata) + b"\n")
        return removed_count

    def _next_metadata(
        self,
        *,
        occurred_at: str,
        reason: str,
        removed_count: int,
        observations: Sequence[AdaptiveObservation],
    ) -> dict[str, Any]:
        generation = 1
        if self.layout.metadata_path.exists():
            try:
                raw = json.loads(self.layout.metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed adaptive store metadata: {exc.msg}") from exc
            if raw.get("schema_version") != ADAPTIVE_STORE_META_SCHEMA_VERSION:
                raise ValueError("unsupported adaptive store metadata schema")
            generation = int(raw.get("generation", 0)) + 1
        return {
            "schema_version": ADAPTIVE_STORE_META_SCHEMA_VERSION,
            "layout_version": ADAPTIVE_STORE_LAYOUT_VERSION,
            "generation": generation,
            "compacted_at": normalize_timestamp(occurred_at, "occurred_at"),
            "reason": str(reason or "").strip() or "privacy-compaction",
            "removed_count": removed_count,
            "observation_count": len(observations),
            "head_digest": None if not observations else observations[-1].digest,
        }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)


def _rechain(observations: Sequence[AdaptiveObservation]) -> tuple[AdaptiveObservation, ...]:
    rebuilt: list[AdaptiveObservation] = []
    for sequence, source in enumerate(observations, start=1):
        previous = None if not rebuilt else rebuilt[-1].digest
        identity_payload = {
            "sequence": sequence,
            "event_type": source.event_type,
            "scope": source.scope.to_dict(),
            "subject_key": source.subject_key,
            "evidence_class": source.evidence_class,
            "source_type": source.source_type,
            "source_ref": source.source_ref,
            "occurred_at": source.occurred_at,
            "payload": dict(source.payload),
            "previous_observation_digest": previous,
            "expires_at": source.expires_at,
            "memory_rule_version": source.memory_rule_version,
        }
        rebuilt.append(
            AdaptiveObservation(
                observation_id=f"obs-{receipt_digest(identity_payload)[:24]}",
                sequence=sequence,
                event_type=source.event_type,
                scope=source.scope,
                subject_key=source.subject_key,
                evidence_class=source.evidence_class,
                source_type=source.source_type,
                source_ref=source.source_ref,
                occurred_at=source.occurred_at,
                payload=source.payload,
                previous_observation_digest=previous,
                memory_rule_version=source.memory_rule_version,
                expires_at=source.expires_at,
            )
        )
    return tuple(rebuilt)
