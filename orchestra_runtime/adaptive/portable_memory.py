from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

import json
import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCHEMA = ROOT / "machine" / "schemas" / "adaptive-shadow-candidate.schema.json"
PORTABLE_SCHEMA = ROOT / "machine" / "schemas" / "portable-memory-candidate.schema.json"

TYPE_MAP = {
    "USER_PREFERENCE_TENDENCY": "USER_PREFERENCE",
    "WORKFLOW_TENDENCY": "WORKFLOW_PATTERN",
    "SPECIALIST_STRATEGY_TENDENCY": "SPECIALIST_STRATEGY",
}

CATEGORIES = (
    "ARCHITECTURE",
    "CODE_REVIEW",
    "CONTEXT_RETRIEVAL",
    "DESIGN_UI_UX",
    "DOCUMENTATION",
    "REMEDIATION",
    "RESEARCH",
    "TESTING",
    "TOOLING",
    "VALIDATION",
    "WORKFLOW",
)
ADAPTER_KINDS = ("LOCAL_JSON", "GIT_JSON", "HTTP_API", "CUSTOM")
RECORD_FORMATS = ("JSON", "JSONL")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load_json(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class MemoryBackendDescriptor:
    backend_id: str
    adapter_kind: str
    record_format: str = "JSON"
    config_ref: str | None = None

    def to_dict(self, *, created_at: str | None = None) -> dict[str, Any]:
        if self.adapter_kind not in ADAPTER_KINDS:
            raise ValueError(f"unsupported adapter_kind: {self.adapter_kind}")
        if self.record_format not in RECORD_FORMATS:
            raise ValueError(f"unsupported record_format: {self.record_format}")
        value: dict[str, Any] = {
            "backend_id": self.backend_id,
            "adapter_kind": self.adapter_kind,
            "record_format": self.record_format,
            "state": "PENDING_BACKEND_VALIDATION",
            "canonical_write_authorized": False,
            "created_at": created_at or _utc_now(),
        }
        if self.config_ref:
            value["config_ref"] = self.config_ref
        return value


class PortableMemoryBackend(Protocol):
    """Storage adapter boundary for portable learned-memory candidates.

    Backends may validate or stage candidates. Candidate creation never grants
    execution authority, policy authority, or permission to write canonical
    memory. Backend-specific commit/publish semantics remain outside this core.
    """

    descriptor: MemoryBackendDescriptor

    def validate_candidate(self, candidate: Mapping[str, Any]) -> list[str]: ...

    def stage_candidate(self, candidate: Mapping[str, Any], destination: Path) -> None: ...


def build_portable_memory_candidate(
    candidate: dict[str, Any],
    *,
    backend: MemoryBackendDescriptor,
    category: str,
    repositories: list[str] | None = None,
    projects: list[str] | None = None,
    use_cases: list[str] | None = None,
    specialists: list[str] | None = None,
    tags: list[str] | None = None,
    created_at: str | None = None,
    privacy_reviewed: bool = False,
) -> dict[str, Any]:
    _validator(SOURCE_SCHEMA).validate(candidate)
    if candidate["status"] != "CANDIDATE":
        raise ValueError("only active A3 CANDIDATE records may enter portable-memory promotion")
    if not privacy_reviewed:
        raise ValueError("portable promotion requires an explicit privacy review")
    if category not in CATEGORIES:
        raise ValueError(f"unsupported category: {category}")

    source_scope = candidate["scope"]
    mapped_projects = list(projects or [])
    mapped_specialists = list(specialists or [])
    if source_scope.get("project_key"):
        mapped_projects.append(source_scope["project_key"])
    if source_scope.get("specialist_slug"):
        mapped_specialists.append(source_scope["specialist_slug"])

    refs = list(candidate["supporting_signal_refs"])
    digests = list(candidate["supporting_signal_digests"])
    if len(refs) != len(digests):
        raise ValueError("supporting signal refs and digests must have one-to-one parity")

    portable = {
        "schema_version": "orchestra.portable-memory-candidate.v1",
        "source": {
            "system": "ORCHESTRA_ADAPTIVE_A3",
            "candidate_id": candidate["candidate_id"],
            "source_schema_version": candidate["schema_version"],
            "learner_rule_version": candidate["learner_rule_version"],
            "status": candidate["status"],
            "shadow_only": candidate["shadow_only"],
            "promotion_state": candidate["promotion_state"],
        },
        "pattern": {
            "key": candidate["subject_key"],
            "type": TYPE_MAP[candidate["candidate_type"]],
            "category": category,
            "value": candidate["candidate_value"],
            "scope": {
                "repositories": _unique(list(repositories or [])),
                "projects": _unique(mapped_projects),
                "use_cases": _unique(list(use_cases or [])),
                "specialists": _unique(mapped_specialists),
            },
            "tags": _unique(list(tags or [])),
        },
        "evidence": {
            "refs": refs,
            "digests": digests,
            "distinct_support_count": candidate["distinct_support_count"],
            "confidence": candidate["confidence"],
            "confidence_method": candidate["confidence_method"],
            "first_seen": candidate["first_seen"],
            "last_seen": candidate["last_seen"],
        },
        "privacy": {
            "contains_raw_conversation": False,
            "contains_sensitive_data": False,
            "contains_credentials": False,
            "local_identity_transferred": False,
            "review_state": "EXPLICITLY_REVIEWED_FOR_PORTABLE_PROMOTION",
        },
        "authority": {
            "execution_authority": False,
            "policy_authority": False,
            "may_override_explicit_instruction": False,
            "may_relax_governance": False,
            "automatic_promotion": False,
        },
        "destination": backend.to_dict(created_at=created_at),
    }
    _validator(PORTABLE_SCHEMA).validate(portable)
    return portable
