from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .evidence import canonical_json_bytes, normalize_git_sha, normalize_sha256, normalize_timestamp, receipt_digest

CONTEXT_STATE_SCHEMA_VERSION = "orchestra.context-state.v1"


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _stable_strings(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    raw = tuple(_text(value, field_name) for value in values)
    if len(raw) != len(set(raw)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(raw))


def _json_payload(value: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    payload = dict(value)
    canonical_json_bytes(payload)
    return payload


@dataclass(frozen=True, slots=True)
class CurrentProjectState:
    project_id: str
    repository: str
    canonical_sha: str
    phase: str
    authority_mode: str
    current_task: str
    blockers: tuple[str, ...]
    critical_receipt_refs: tuple[str, ...]
    evidence_index_refs: tuple[str, ...]
    revision: int
    updated_at: str
    schema_version: str = CONTEXT_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CONTEXT_STATE_SCHEMA_VERSION:
            raise ValueError(f"unsupported current-state schema {self.schema_version!r}")
        object.__setattr__(self, "project_id", _text(self.project_id, "project_id"))
        repository = _text(self.repository, "repository")
        if "/" not in repository or repository.startswith("/") or repository.endswith("/"):
            raise ValueError("repository must be an owner/name identity")
        object.__setattr__(self, "repository", repository)
        object.__setattr__(self, "canonical_sha", normalize_git_sha(self.canonical_sha, "canonical_sha"))
        object.__setattr__(self, "phase", _text(self.phase, "phase"))
        object.__setattr__(self, "authority_mode", _text(self.authority_mode, "authority_mode"))
        object.__setattr__(self, "current_task", _text(self.current_task, "current_task"))
        object.__setattr__(self, "blockers", _stable_strings(self.blockers, "blockers"))
        object.__setattr__(self, "critical_receipt_refs", _stable_strings(self.critical_receipt_refs, "critical_receipt_refs"))
        object.__setattr__(self, "evidence_index_refs", _stable_strings(self.evidence_index_refs, "evidence_index_refs"))
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")
        object.__setattr__(self, "updated_at", normalize_timestamp(self.updated_at, "updated_at"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "repository": self.repository,
            "canonical_sha": self.canonical_sha,
            "phase": self.phase,
            "authority_mode": self.authority_mode,
            "current_task": self.current_task,
            "blockers": list(self.blockers),
            "critical_receipt_refs": list(self.critical_receipt_refs),
            "evidence_index_refs": list(self.evidence_index_refs),
            "revision": self.revision,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CurrentProjectState":
        if not isinstance(payload, Mapping):
            raise TypeError("current state payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            project_id=payload.get("project_id", ""),
            repository=payload.get("repository", ""),
            canonical_sha=payload.get("canonical_sha", ""),
            phase=payload.get("phase", ""),
            authority_mode=payload.get("authority_mode", ""),
            current_task=payload.get("current_task", ""),
            blockers=tuple(payload.get("blockers", ())),
            critical_receipt_refs=tuple(payload.get("critical_receipt_refs", ())),
            evidence_index_refs=tuple(payload.get("evidence_index_refs", ())),
            revision=payload.get("revision", -1),
            updated_at=payload.get("updated_at", ""),
        )

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ContinuityEvent:
    sequence: int
    project_id: str
    event_type: str
    occurred_at: str
    payload: Mapping[str, Any]
    previous_event_digest: str | None
    schema_version: str = CONTEXT_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CONTEXT_STATE_SCHEMA_VERSION:
            raise ValueError(f"unsupported continuity event schema {self.schema_version!r}")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:
            raise ValueError("sequence must be a positive integer")
        object.__setattr__(self, "project_id", _text(self.project_id, "project_id"))
        object.__setattr__(self, "event_type", _text(self.event_type, "event_type"))
        object.__setattr__(self, "occurred_at", normalize_timestamp(self.occurred_at, "occurred_at"))
        object.__setattr__(self, "payload", _json_payload(self.payload, "payload"))
        if self.previous_event_digest is None:
            if self.sequence != 1:
                raise ValueError("only the first event may omit previous_event_digest")
        else:
            object.__setattr__(self, "previous_event_digest", normalize_sha256(self.previous_event_digest, "previous_event_digest"))
            if self.sequence == 1:
                raise ValueError("the first event must not declare previous_event_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "project_id": self.project_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "previous_event_digest": self.previous_event_digest,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContinuityEvent":
        if not isinstance(payload, Mapping):
            raise TypeError("continuity event payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            sequence=payload.get("sequence", 0),
            project_id=payload.get("project_id", ""),
            event_type=payload.get("event_type", ""),
            occurred_at=payload.get("occurred_at", ""),
            payload=payload.get("payload", {}),
            previous_event_digest=payload.get("previous_event_digest"),
        )

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


class JsonlContinuityStore:
    def __init__(self, path: Path, project_id: str):
        self.path = Path(path)
        self.project_id = _text(project_id, "project_id")

    def load(self) -> tuple[ContinuityEvent, ...]:
        if not self.path.exists():
            return ()
        events: list[ContinuityEvent] = []
        for lineno, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                raise ValueError(f"continuity JSONL contains blank line at {lineno}")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed continuity JSONL at line {lineno}: {exc.msg}") from exc
            event = ContinuityEvent.from_dict(payload)
            if event.project_id != self.project_id:
                raise ValueError(f"continuity event project mismatch at line {lineno}")
            expected_sequence = len(events) + 1
            if event.sequence != expected_sequence:
                raise ValueError(f"continuity event sequence gap at line {lineno}: expected {expected_sequence}, got {event.sequence}")
            expected_previous = None if not events else events[-1].digest
            if event.previous_event_digest != expected_previous:
                raise ValueError(f"continuity event hash-chain mismatch at line {lineno}")
            events.append(event)
        return tuple(events)

    def append(self, *, event_type: str, occurred_at: str, payload: Mapping[str, Any]) -> ContinuityEvent:
        events = self.load()
        event = ContinuityEvent(
            sequence=len(events) + 1,
            project_id=self.project_id,
            event_type=event_type,
            occurred_at=occurred_at,
            payload=payload,
            previous_event_digest=None if not events else events[-1].digest,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as handle:
            handle.write(canonical_json_bytes(event.to_dict()) + b"\n")
        return event


_CONTEXT_LEVELS = ("L0", "L1", "L2", "L3")


def compile_context(
    state: CurrentProjectState,
    level: str = "L0",
    *,
    event_head_digest: str | None = None,
    history: Sequence[ContinuityEvent] | None = None,
) -> dict[str, Any]:
    if not isinstance(state, CurrentProjectState):
        raise TypeError("state must be CurrentProjectState")
    if level not in _CONTEXT_LEVELS:
        raise ValueError(f"unsupported context level {level!r}")
    context: dict[str, Any] = {
        "schema_version": CONTEXT_STATE_SCHEMA_VERSION,
        "level": level,
        "project_id": state.project_id,
        "repository": state.repository,
        "canonical_sha": state.canonical_sha,
        "phase": state.phase,
        "authority_mode": state.authority_mode,
        "revision": state.revision,
        "state_digest": state.digest,
    }
    if level in {"L1", "L2", "L3"}:
        context.update(
            {
                "current_task": state.current_task,
                "blockers": list(state.blockers),
                "critical_receipt_refs": list(state.critical_receipt_refs),
            }
        )
    if level in {"L2", "L3"}:
        context["evidence_index_refs"] = list(state.evidence_index_refs)
        context["event_head_digest"] = None if event_head_digest is None else normalize_sha256(event_head_digest, "event_head_digest")
    if level == "L3":
        if history is None:
            raise ValueError("L3 history must be explicitly supplied; history inference is forbidden")
        if not all(isinstance(event, ContinuityEvent) for event in history):
            raise TypeError("L3 history must contain ContinuityEvent records")
        if any(event.project_id != state.project_id for event in history):
            raise ValueError("L3 history contains another project")
        context["history"] = [event.to_dict() for event in history]
    return context


def render_state_markdown(state: CurrentProjectState, *, source_path: str = "machine/state/current.json") -> str:
    if not isinstance(state, CurrentProjectState):
        raise TypeError("state must be CurrentProjectState")
    source_path = _text(source_path, "source_path")
    blockers = "\n".join(f"- {item}" for item in state.blockers) or "- None"
    receipts = "\n".join(f"- `{item}`" for item in state.critical_receipt_refs) or "- None"
    evidence = "\n".join(f"- `{item}`" for item in state.evidence_index_refs) or "- None"
    return (
        f"# {state.project_id} Current State\n\n"
        f"> Generated view. Machine authority: `{source_path}`. State digest: `{state.digest}`.\n\n"
        f"- **Repository:** `{state.repository}`\n"
        f"- **Canonical SHA:** `{state.canonical_sha}`\n"
        f"- **Phase:** `{state.phase}`\n"
        f"- **Authority mode:** `{state.authority_mode}`\n"
        f"- **Revision:** `{state.revision}`\n"
        f"- **Updated:** `{state.updated_at}`\n"
        f"- **Current task:** {state.current_task}\n\n"
        f"## Blockers\n\n{blockers}\n\n"
        f"## Critical receipts\n\n{receipts}\n\n"
        f"## Evidence index\n\n{evidence}\n"
    )


def assert_markdown_parity(state: CurrentProjectState, markdown: str, *, source_path: str = "machine/state/current.json") -> None:
    expected = render_state_markdown(state, source_path=source_path)
    if markdown != expected:
        raise ValueError("generated Markdown state is stale or hand-edited")
