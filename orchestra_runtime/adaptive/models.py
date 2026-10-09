from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Iterable, Mapping

from ..evidence import canonical_json_bytes, normalize_sha256, normalize_timestamp, receipt_digest

ADAPTIVE_OBSERVATION_SCHEMA_VERSION = "orchestra.adaptive-observation.v1"
ADAPTIVE_PROFILE_SCHEMA_VERSION = "orchestra.adaptive-profile.v1"
ADAPTIVE_MEMORY_RULE_VERSION = "orchestra.adaptive-memory-rules.v1"

SCOPE_TYPES = frozenset({"global_user", "project", "specialist", "task_session"})
EVIDENCE_CLASSES = frozenset(
    {
        "EXPLICIT_CURRENT_INSTRUCTION",
        "EXPLICIT_SCOPED_PREFERENCE",
        "GOVERNED_OUTCOME",
        "USER_FEEDBACK",
        "INFERRED_CANDIDATE",
    }
)
EVENT_TYPES = frozenset(
    {
        "EXPLICIT_PREFERENCE_SET",
        "EXPLICIT_PREFERENCE_CORRECTED",
        "EXPLICIT_PREFERENCE_REMOVED",
        "INFERRED_PATTERN_CANDIDATE",
        "INFERRED_PATTERN_CONFIRMED",
        "INFERRED_PATTERN_DEPRECATED",
        "INFERRED_PATTERN_REJECTED",
        "GOVERNED_OUTCOME_RECORDED",
    }
)
PATTERN_STATUSES = frozenset({"candidate", "confirmed", "deprecated", "rejected"})

NON_LEARNABLE_SUBJECT_ROOTS = frozenset(
    {
        "authority",
        "capability",
        "required_specialist",
        "governance",
        "human_gate",
        "security_prohibition",
        "mandatory_validation",
        "evidence_integrity",
        "audit_requirement",
        "fail_closed",
        "exact_head",
        "release_gate",
        "merge_gate",
        "privacy_restriction",
        "provider_restriction",
        "resource_ceiling",
    }
)

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_SENSITIVE_KEY_FRAGMENTS = (
    "credential",
    "secret",
    "password",
    "private_key",
    "api_key",
    "authorization",
    "access_token",
    "refresh_token",
    "bearer",
    "cookie",
    "ssn",
    "national_id",
    "personal_data",
    "pii",
    "birth_date",
    "phone_number",
    "email_address",
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{field_name} must not contain control characters")
    return text


def _optional_text(value: object | None, field_name: str) -> str | None:
    return None if value is None else _text(value, field_name)


def _stable_strings(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_text(value, field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(normalized))


def validate_subject_key(value: str) -> str:
    key = _text(value, "subject_key").casefold()
    if not _IDENTIFIER_RE.fullmatch(key):
        raise ValueError("subject_key must be a canonical lower-case identifier")
    root = re.split(r"[.:]", key, maxsplit=1)[0]
    if root in NON_LEARNABLE_SUBJECT_ROOTS:
        raise ValueError(f"subject_key root '{root}' is a non-learnable governance boundary")
    return key


def _assert_safe_json(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _text(str(key), f"{path} key").casefold()
            if any(fragment in key_text for fragment in _SENSITIVE_KEY_FRAGMENTS):
                raise ValueError(f"{path} contains sensitive key '{key_text}'")
            _assert_safe_json(child, f"{path}.{key_text}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_safe_json(child, f"{path}[{index}]")
        return
    if isinstance(value, str) and any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS):
        raise ValueError(f"{path} contains credential-like material")


def safe_json_object(value: Mapping[str, Any], field_name: str = "payload") -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    payload = dict(value)
    _assert_safe_json(payload, field_name)
    canonical_json_bytes(payload)
    return payload


def _normalize_expiry(value: str | None, reference_at: str) -> str | None:
    if value is None:
        return None
    expires = normalize_timestamp(value, "expires_at")
    if datetime.fromisoformat(expires.replace("Z", "+00:00")) <= datetime.fromisoformat(
        reference_at.replace("Z", "+00:00")
    ):
        raise ValueError("expires_at must be later than the record timestamp")
    return expires


@dataclass(frozen=True, slots=True)
class AdaptiveScope:
    scope_type: str
    user_key: str
    project_key: str | None = None
    specialist_slug: str | None = None
    task_session_key: str | None = None

    def __post_init__(self) -> None:
        scope_type = _text(self.scope_type, "scope_type").casefold()
        if scope_type not in SCOPE_TYPES:
            raise ValueError(f"unsupported adaptive scope '{scope_type}'")
        user_key = _text(self.user_key, "user_key")
        project_key = _optional_text(self.project_key, "project_key")
        specialist_slug = _optional_text(self.specialist_slug, "specialist_slug")
        task_session_key = _optional_text(self.task_session_key, "task_session_key")
        if specialist_slug is not None:
            specialist_slug = specialist_slug.casefold()
            if not _IDENTIFIER_RE.fullmatch(specialist_slug):
                raise ValueError("specialist_slug must be a canonical identifier")

        if scope_type == "global_user" and any((project_key, specialist_slug, task_session_key)):
            raise ValueError("global_user scope cannot declare project, specialist, or task identifiers")
        if scope_type == "project" and (
            project_key is None or specialist_slug is not None or task_session_key is not None
        ):
            raise ValueError("project scope requires only project_key")
        if scope_type == "specialist" and (specialist_slug is None or task_session_key is not None):
            raise ValueError("specialist scope requires specialist_slug and cannot declare task_session_key")
        if scope_type == "task_session" and task_session_key is None:
            raise ValueError("task_session scope requires task_session_key")

        object.__setattr__(self, "scope_type", scope_type)
        object.__setattr__(self, "user_key", user_key)
        object.__setattr__(self, "project_key", project_key)
        object.__setattr__(self, "specialist_slug", specialist_slug)
        object.__setattr__(self, "task_session_key", task_session_key)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"scope_type": self.scope_type, "user_key": self.user_key}
        if self.project_key is not None:
            payload["project_key"] = self.project_key
        if self.specialist_slug is not None:
            payload["specialist_slug"] = self.specialist_slug

        if self.task_session_key is not None:
            payload["task_session_key"] = self.task_session_key
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AdaptiveScope":
        if not isinstance(payload, Mapping):
            raise TypeError("adaptive scope payload must be an object")
        return cls(
            scope_type=payload.get("scope_type", ""),
            user_key=payload.get("user_key", ""),
            project_key=payload.get("project_key"),
            specialist_slug=payload.get("specialist_slug"),
            task_session_key=payload.get("task_session_key"),
        )

    @property
    def identity(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class AdaptiveObservation:
    observation_id: str
    sequence: int
    event_type: str
    scope: AdaptiveScope
    subject_key: str
    evidence_class: str
    source_type: str
    source_ref: str
    occurred_at: str
    payload: Mapping[str, Any]
    previous_observation_digest: str | None
    memory_rule_version: str = ADAPTIVE_MEMORY_RULE_VERSION
    expires_at: str | None = None
    schema_version: str = ADAPTIVE_OBSERVATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ADAPTIVE_OBSERVATION_SCHEMA_VERSION:
            raise ValueError(f"unsupported adaptive observation schema '{self.schema_version}'")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:
            raise ValueError("sequence must be a positive integer")
        if not isinstance(self.scope, AdaptiveScope):
            raise TypeError("scope must be AdaptiveScope")
        event_type = _text(self.event_type, "event_type").upper()
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported adaptive event '{event_type}'")
        evidence_class = _text(self.evidence_class, "evidence_class").upper()
        if evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(f"unsupported evidence class '{evidence_class}'")
        if event_type == "GOVERNED_OUTCOME_RECORDED" and evidence_class != "GOVERNED_OUTCOME":
            raise ValueError("governed outcome events require GOVERNED_OUTCOME evidence")
        if event_type.startswith("INFERRED_PATTERN_") and evidence_class != "INFERRED_CANDIDATE":
            raise ValueError("inferred pattern events require INFERRED_CANDIDATE evidence")
        if event_type in {"EXPLICIT_PREFERENCE_SET", "EXPLICIT_PREFERENCE_CORRECTED"} and evidence_class not in {
            "EXPLICIT_CURRENT_INSTRUCTION",
            "EXPLICIT_SCOPED_PREFERENCE",
        }:
            raise ValueError("explicit preference events require explicit instruction evidence")
        if event_type == "EXPLICIT_PREFERENCE_REMOVED" and evidence_class != "USER_FEEDBACK":
            raise ValueError("explicit removal events require USER_FEEDBACK evidence")
        if evidence_class == "EXPLICIT_CURRENT_INSTRUCTION" and self.scope.scope_type != "task_session":
            raise ValueError("explicit current instructions must remain task/session scoped")
        occurred_at = normalize_timestamp(self.occurred_at, "occurred_at")
        previous = self.previous_observation_digest
        if previous is None:
            if self.sequence != 1:
                raise ValueError("only the first observation may omit previous_observation_digest")
        else:
            previous = normalize_sha256(previous, "previous_observation_digest")
            if self.sequence == 1:
                raise ValueError("the first observation must not declare previous_observation_digest")

        object.__setattr__(self, "observation_id", _text(self.observation_id, "observation_id"))
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "subject_key", validate_subject_key(self.subject_key))
        object.__setattr__(self, "evidence_class", evidence_class)
        object.__setattr__(self, "source_type", _text(self.source_type, "source_type"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "payload", safe_json_object(self.payload))
        object.__setattr__(self, "previous_observation_digest", previous)
        object.__setattr__(self, "memory_rule_version", _text(self.memory_rule_version, "memory_rule_version"))
        object.__setattr__(self, "expires_at", _normalize_expiry(self.expires_at, occurred_at))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "memory_rule_version": self.memory_rule_version,
            "observation_id": self.observation_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "scope": self.scope.to_dict(),
            "subject_key": self.subject_key,
            "evidence_class": self.evidence_class,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "previous_observation_digest": self.previous_observation_digest,
        }
        if self.expires_at is not None:
            payload["expires_at"] = self.expires_at
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AdaptiveObservation":
        if not isinstance(payload, Mapping):
            raise TypeError("adaptive observation payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            memory_rule_version=payload.get("memory_rule_version", ""),
            observation_id=payload.get("observation_id", ""),
            sequence=payload.get("sequence", 0),
            event_type=payload.get("event_type", ""),
            scope=AdaptiveScope.from_dict(payload.get("scope", {})),
            subject_key=payload.get("subject_key", ""),
            evidence_class=payload.get("evidence_class", ""),
            source_type=payload.get("source_type", ""),
            source_ref=payload.get("source_ref", ""),
            occurred_at=payload.get("occurred_at", ""),
            payload=payload.get("payload", {}),
            previous_observation_digest=payload.get("previous_observation_digest"),
            expires_at=payload.get("expires_at"),
       )

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class AdaptivePattern:
    pattern_id: str
    scope: AdaptiveScope
    subject_key: str
    value: Any
    status: str
    evidence_class: str
    evidence_refs: tuple[str, ...]
    observation_count: int
    confidence: float
    created_at: str
    updated_at: str
    memory_rule_version: str = ADAPTIVE_MEMORY_RULE_VERSION
    expires_at: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scope, AdaptiveScope):
            raise TypeError("scope must be AdaptiveScope")
        status = _text(self.status, "status").casefold()
        if status not in PATTERN_STATUSES:
            raise ValueError(f"unsupported pattern status '{status}'")
        evidence_class = _text(self.evidence_class, "evidence_class").upper()
        if evidence_class not in EVIDENCE_CLASSES - {"GOVERNED_OUTCOME"}:
            raise ValueError("pattern evidence_class must describe preference or inferred evidence")
        if isinstance(self.observation_count, bool) or not isinstance(self.observation_count, int) or self.observation_count <= 0:
            raise ValueError("observation_count must be a positive integer")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)) or not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        created_at = normalize_timestamp(self.created_at, "created_at")
        updated_at = normalize_timestamp(self.updated_at, "updated_at")
        if datetime.fromisoformat(updated_at.replace("Z", "+00:00")) < datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        ):
            raise ValueError("updated_at must not precede created_at")
        if evidence_class.startswith("EXPLICIT_"):
            if status != "confirmed" or float(self.confidence) != 1.0:
                raise ValueError("explicit preferences must be confirmed with confidence 1.0")
        _assert_safe_json(self.value, "value")
        canonical_json_bytes(self.value)

        object.__setattr__(self, "pattern_id", _text(self.pattern_id, "pattern_id"))
        object.__setattr__(self, "subject_key", validate_subject_key(self.subject_key))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_class", evidence_class)
        object.__setattr__(self, "evidence_refs", _stable_strings(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "memory_rule_version", _text(self.memory_rule_version, "memory_rule_version"))
        object.__setattr__(self, "expires_at", _normalize_expiry(self.expires_at, updated_at))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "pattern_id": self.pattern_id,
            "scope": self.scope.to_dict(),
            "subject_key": self.subject_key,
            "value": self.value,
            "status": self.status,
            "evidence_class": self.evidence_class,
            "evidence_refs": list(self.evidence_refs),
            "observation_count": self.observation_count,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memory_rule_version": self.memory_rule_version,
        }
        if self.expires_at is not None:
            payload["expires_at"] = self.expires_at
        return payload


@dataclass(frozen=True, slots=True)
class AdaptiveProfile:
    profile_id: str
    user_key: str
    generated_at: str
    patterns: tuple[AdaptivePattern, ...]
    source_head_digest: str | None
    memory_rule_version: str = ADAPTIVE_MEMORY_RULE_VERSION
    schema_version: str = ADAPTIVE_PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ADAPTIVE_PROFILE_SCHEMA_VERSION:
            raise ValueError(f"unsupported adaptive profile schema '{self.schema_version}'")
        user_key = _text(self.user_key, "user_key")
        patterns = tuple(self.patterns)
        if any(not isinstance(pattern, AdaptivePattern) for pattern in patterns):
            raise TypeError("patterns must contain AdaptivePattern records")
        if any(pattern.scope.user_key != user_key for pattern in patterns):
            raise ValueError("profile contains pattern for another user scope")
        identities = tuple((pattern.scope.identity, pattern.subject_key) for pattern in patterns)
        if len(identities) != len(set(identities)):
            raise ValueError("profile contains duplicate scope/subject patterns")
        source_head = self.source_head_digest
        if source_head is not None:
            source_head = normalize_sha256(source_head, "source_head_digest")
        object.__setattr__(self, "profile_id", _text(self.profile_id, "profile_id"))
        object.__setattr__(self, "user_key", user_key)
        object.__setattr__(self, "generated_at", normalize_timestamp(self.generated_at, "generated_at"))
        object.__setattr__(
            self,
            "patterns",
            tuple(sorted(patterns, key=lambda p: (p.scope.scope_type, p.scope.identity, p.subject_key))),
        )
        object.__setattr__(self, "source_head_digest", source_head)
        object.__setattr__(self, "memory_rule_version", _text(self.memory_rule_version, "memory_rule_version"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "memory_rule_version": self.memory_rule_version,
            "profile_id": self.profile_id,
            "user_key": self.user_key,
            "generated_at": self.generated_at,
            "source_head_digest": self.source_head_digest,
            "patterns": [pattern.to_dict() for pattern in self.patterns],
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())
