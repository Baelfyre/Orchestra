from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..evidence import receipt_digest
from .models import (
    AdaptiveObservation,
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
    ADAPTIVE_MEMORY_RULE_VERSION,
)


def materialize_profile(
    user_key: str,
    observations: Sequence[AdaptiveObservation],
    *,
    generated_at: str,
    memory_rule_version: str = ADAPTIVE_MEMORY_RULE_VERSION,
) -> AdaptiveProfile:
    """Deterministically materialize local memory without promoting governed outcomes."""
    current: dict[tuple[str, str], AdaptivePattern] = {}
    source_head: str | None = None
    for observation in observations:
        if observation.scope.user_key != user_key:
            raise ValueError("cannot materialize profile from another user's observation")
        if observation.memory_rule_version != memory_rule_version:
            raise ValueError("adaptive observation memory rule version does not match materializer")
        source_head = observation.digest
        key = (observation.scope.identity, observation.subject_key)
        prior = current.get(key)
        event = observation.event_type
        payload = dict(observation.payload)

        if event == "GOVERNED_OUTCOME_RECORDED":
            continue
        if event == "EXPLICIT_PREFERENCE_REMOVED":
            current.pop(key, None)
            continue

        if event in {"EXPLICIT_PREFERENCE_SET", "EXPLICIT_PREFERENCE_CORRECTED"}:
            if "value" not in payload:
                raise ValueError(f"{event} requires payload.value")
            current[key] = _pattern(
                observation,
                value=payload["value"],
                status="confirmed",
                confidence=1.0,
                prior=prior,
                evidence_class=observation.evidence_class,
            )
            continue

        if event in {"INFERRED_PATTERN_CANDIDATE", "INFERRED_PATTERN_CONFIRMED"}:
            if "value" not in payload:
                raise ValueError(f"{event} requires payload.value")
            confidence = payload.get("confidence")
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise ValueError(f"{event} requires numeric payload.confidence")
            current[key] = _pattern(
                observation,
                value=payload["value"],
                status="candidate" if event.endswith("CANDIDATE") else "confirmed",
                confidence=float(confidence),
                prior=prior,
                evidence_class="INFERRED_CANDIDATE",
                extra_refs=tuple(payload.get("evidence_refs", ())),
            )
            continue

        if event in {"INFERRED_PATTERN_DEPRECATED", "INFERRED_PATTERN_REJECTED"}:
            if prior is None:
                raise ValueError(f"{event} requires an existing pattern")
            current[key] = _pattern(
                observation,
                value=prior.value,
                status="deprecated" if event.endswith("DEPRECATED") else "rejected",
                confidence=prior.confidence,
                prior=prior,
                evidence_class="INFERRED_CANDIDATE",
            )
            continue

        raise ValueError(f"unhandled adaptive event '{event}'")

    patterns = tuple(current.values())
    profile_seed = {
        "user_key": user_key,
        "source_head_digest": source_head,
        "pattern_ids": sorted(pattern.pattern_id for pattern in patterns),
        "memory_rule_version": memory_rule_version,
    }
    return AdaptiveProfile(
        profile_id=f"profile-{receipt_digest(profile_seed)[:24]}",
        user_key=user_key,
        generated_at=generated_at,
        patterns=patterns,
        source_head_digest=source_head,
        memory_rule_version=memory_rule_version,
    )


def _pattern(
    observation: AdaptiveObservation,
    *,
    value: Any,
    status: str,
    confidence: float,
    prior: AdaptivePattern | None,
    evidence_class: str,
    extra_refs: tuple[str, ...] = (),
) -> AdaptivePattern:
    refs = set(() if prior is None else prior.evidence_refs)
    refs.add(observation.source_ref)
    refs.update(str(ref).strip() for ref in extra_refs if str(ref).strip())
    created_at = observation.occurred_at if prior is None else prior.created_at
    count = 1 if prior is None else prior.observation_count + 1
    pattern_seed = {
        "scope": observation.scope.to_dict(),
        "subject_key": observation.subject_key,
        "created_at": created_at,
        "memory_rule_version": observation.memory_rule_version,
    }
    return AdaptivePattern(
        pattern_id=f"pattern-{receipt_digest(pattern_seed)[:24]}",
        scope=observation.scope,
        subject_key=observation.subject_key,
        value=value,
        status=status,
        evidence_class=evidence_class,
        evidence_refs=tuple(refs),
        observation_count=count,
        confidence=confidence,
        created_at=created_at,
        updated_at=observation.occurred_at,
        expires_at=observation.expires_at,
        memory_rule_version=observation.memory_rule_version,
    )


def profile_from_dict(payload: Mapping[str, Any]) -> AdaptiveProfile:
    if not isinstance(payload, Mapping):
        raise TypeError("adaptive profile payload must be an object")
    patterns = []
    for raw in payload.get("patterns", ()):
        if not isinstance(raw, Mapping):
            raise TypeError("adaptive profile patterns must be objects")
        patterns.append(
            AdaptivePattern(
                pattern_id=raw.get("pattern_id", ""),
                scope=AdaptiveScope.from_dict(raw.get("scope", {})),
                subject_key=raw.get("subject_key", ""),
                value=raw.get("value"),
                status=raw.get("status", ""),
                evidence_class=raw.get("evidence_class", ""),
                evidence_refs=tuple(raw.get("evidence_refs", ())),
                observation_count=raw.get("observation_count", 0),
                confidence=raw.get("confidence", -1),
                created_at=raw.get("created_at", ""),
                updated_at=raw.get("updated_at", ""),
                expires_at=raw.get("expires_at"),
                memory_rule_version=raw.get("memory_rule_version", ""),
            )
        )
    return AdaptiveProfile(
        schema_version=payload.get("schema_version", ""),
        memory_rule_version=payload.get("memory_rule_version", ""),
        profile_id=payload.get("profile_id", ""),
        user_key=payload.get("user_key", ""),
        generated_at=payload.get("generated_at", ""),
        source_head_digest=payload.get("source_head_digest"),
        patterns=tuple(patterns),
    )
