from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from .lifecycle import LifecycleSignal, LifecycleSignalType


PRESENTATION_POLICY_SCHEMA_VERSION = "orchestra.presentation-policy.v1"
MURMURS_VOCABULARY_SCHEMA_VERSION = "orchestra.murmurs-vocabulary.v1"

_MACHINE_ROOT = Path("machine")
_PRESENTATION_POLICY = _MACHINE_ROOT / "presentation" / "murmurs-policy.v1.json"
_MURMURS_VOCABULARY = _MACHINE_ROOT / "presentation" / "murmurs-vocabulary.v1.json"


class PresentationDisposition(str, Enum):
    SILENT = "SILENT"
    MURMUR = "MURMUR"
    EXPLAIN = "EXPLAIN"


class PresentationEventKind(str, Enum):
    EXECUTION_HEARTBEAT = "EXECUTION_HEARTBEAT"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    ROUTINE_VALIDATION_PASSED = "ROUTINE_VALIDATION_PASSED"
    HUMAN_ACTION_REQUIRED = "HUMAN_ACTION_REQUIRED"
    AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNRECOVERABLE_BLOCKER = "UNRECOVERABLE_BLOCKER"
    GOVERNANCE_STOP = "GOVERNANCE_STOP"
    HANDOFF_REQUIRED = "HANDOFF_REQUIRED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"


FORCED_EXPLAIN_EVENTS = (
    PresentationEventKind.HUMAN_ACTION_REQUIRED,
    PresentationEventKind.AUTHORITY_REQUIRED,
    PresentationEventKind.VALIDATION_FAILED,
    PresentationEventKind.UNRECOVERABLE_BLOCKER,
    PresentationEventKind.GOVERNANCE_STOP,
    PresentationEventKind.HANDOFF_REQUIRED,
    PresentationEventKind.TASK_COMPLETED,
    PresentationEventKind.TASK_FAILED,
)

_LIFECYCLE_EVENT_MAP = {
    LifecycleSignalType.ACTIVATE: PresentationEventKind.EXECUTION_HEARTBEAT,
    LifecycleSignalType.WAIT: PresentationEventKind.EXECUTION_HEARTBEAT,
    LifecycleSignalType.RESUME: PresentationEventKind.EXECUTION_HEARTBEAT,
    LifecycleSignalType.COMPLETE: PresentationEventKind.TASK_COMPLETED,
    LifecycleSignalType.FAIL: PresentationEventKind.TASK_FAILED,
    LifecycleSignalType.CANCEL: PresentationEventKind.TASK_FAILED,
    LifecycleSignalType.TIME_OUT: PresentationEventKind.TASK_FAILED,
    LifecycleSignalType.BLOCK: PresentationEventKind.UNRECOVERABLE_BLOCKER,
}

_FORBIDDEN_STATUS_TERMS = frozenset(
    {
        "almost",
        "blocked",
        "complete",
        "completed",
        "done",
        "error",
        "fail",
        "failed",
        "fixed",
        "pass",
        "passed",
        "success",
        "working",
    }
)


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _root(root: Path | str | None) -> Path:
    return repository_root() if root is None else Path(root)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"presentation contract missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"presentation contract is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"presentation contract must be a JSON object: {path}")
    return value


def _text(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema_version") != PRESENTATION_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported presentation policy schema_version")
    if policy.get("default_disposition") != PresentationDisposition.EXPLAIN.value:
        raise ValueError("presentation default disposition must fail closed to EXPLAIN")

    events = policy.get("events")
    if not isinstance(events, dict):
        raise ValueError("presentation policy events must be an object")
    expected_events = {item.value for item in PresentationEventKind}
    if set(events) != expected_events:
        raise ValueError("presentation policy event set does not match the runtime vocabulary")
    for event_name, raw_disposition in events.items():
        try:
            disposition = PresentationDisposition(raw_disposition)
        except ValueError as exc:
            raise ValueError(f"presentation event {event_name!r} has an invalid disposition") from exc
        if PresentationEventKind(event_name) in FORCED_EXPLAIN_EVENTS and disposition is not PresentationDisposition.EXPLAIN:
            raise ValueError(f"presentation event {event_name!r} must require EXPLAIN")

    explain_required = policy.get("explain_required")
    if not isinstance(explain_required, list):
        raise ValueError("presentation explain_required must be a list")
    expected_explain = [item.value for item in FORCED_EXPLAIN_EVENTS]
    if explain_required != expected_explain:
        raise ValueError("presentation explain_required does not match fail-closed runtime requirements")

    authority_effect = policy.get("authority_effect")
    expected_authority_effect = {
        "presentation_may_change_machine_state": False,
        "presentation_may_override_governance": False,
        "presentation_may_suppress_required_explanation": False,
    }
    if authority_effect != expected_authority_effect:
        raise ValueError("presentation policy cannot create authority or suppress required explanation")
    return policy


def _validate_vocabulary(vocabulary: dict[str, Any]) -> dict[str, Any]:
    if vocabulary.get("schema_version") != MURMURS_VOCABULARY_SCHEMA_VERSION:
        raise ValueError("unsupported Murmurs vocabulary schema_version")
    if vocabulary.get("selection") != "SHA256_MODULO":
        raise ValueError("unsupported Murmurs vocabulary selection strategy")
    constraints = vocabulary.get("constraints")
    if constraints != {
        "maximum_characters": 12,
        "allow_newlines": False,
        "allow_status_claims": False,
    }:
        raise ValueError("Murmurs vocabulary constraints must preserve the non-semantic presentation boundary")

    entries = vocabulary.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Murmurs vocabulary entries must be a non-empty list")
    cleaned = tuple(str(item) for item in entries)
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Murmurs vocabulary entries must be unique")
    for entry in cleaned:
        if not entry or entry != entry.strip():
            raise ValueError("Murmurs vocabulary entries must be non-empty and trimmed")
        if len(entry) > 12 or "\n" in entry or "\r" in entry:
            raise ValueError("Murmurs vocabulary entry violates length/newline constraints")
        words = set(re.findall(r"[a-z]+", entry.lower()))
        if words & _FORBIDDEN_STATUS_TERMS:
            raise ValueError("Murmurs vocabulary entries cannot contain status or completion claims")
    return vocabulary


def load_presentation_policy(root: Path | str | None = None) -> dict[str, Any]:
    return _validate_policy(_load_json(_root(root) / _PRESENTATION_POLICY))


def load_murmurs_vocabulary(root: Path | str | None = None) -> dict[str, Any]:
    return _validate_vocabulary(_load_json(_root(root) / _MURMURS_VOCABULARY))


@dataclass(frozen=True, slots=True)
class PresentationEvent:
    run_id: str
    event_kind: PresentationEventKind
    sequence: int
    source_component: str = "runtime"
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        run_id = _text(self.run_id, "run_id")
        event_kind = PresentationEventKind(self.event_kind)
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise ValueError("presentation sequence must be a non-negative integer")
        source_component = _text(self.source_component, "source_component")
        evidence_refs = tuple(sorted({_text(item, "evidence_ref") for item in self.evidence_refs}))
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "event_kind", event_kind)
        object.__setattr__(self, "source_component", source_component)
        object.__setattr__(self, "evidence_refs", evidence_refs)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "event_kind": self.event_kind.value,
            "sequence": self.sequence,
            "source_component": self.source_component,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class PresentationDecision:
    event: PresentationEvent
    disposition: PresentationDisposition
    reason_code: str
    murmur_text: str | None = None

    def __post_init__(self) -> None:
        disposition = PresentationDisposition(self.disposition)
        reason_code = _text(self.reason_code, "reason_code")
        murmur_text = self.murmur_text
        if disposition is PresentationDisposition.MURMUR:
            if murmur_text is None or not str(murmur_text).strip():
                raise ValueError("MURMUR presentation requires local murmur_text")
            murmur_text = str(murmur_text)
        elif murmur_text is not None:
            raise ValueError("only MURMUR presentation may carry murmur_text")
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "murmur_text", murmur_text)

    @property
    def requires_explanation(self) -> bool:
        return self.disposition is PresentationDisposition.EXPLAIN

    def to_dict(self) -> dict[str, object]:
        return {
            "event": self.event.to_dict(),
            "disposition": self.disposition.value,
            "reason_code": self.reason_code,
            "murmur_text": self.murmur_text,
        }


def presentation_decision_digest(decision: PresentationDecision) -> str:
    payload = json.dumps(decision.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def _select_murmur(event: PresentationEvent, entries: tuple[str, ...]) -> str:
    seed = f"{event.run_id}\0{event.sequence}\0{event.event_kind.value}".encode("utf-8")
    index = int.from_bytes(sha256(seed).digest()[:8], "big") % len(entries)
    return entries[index]


def decide_presentation(event: PresentationEvent, root: Path | str | None = None) -> PresentationDecision:
    try:
        policy = load_presentation_policy(root)
        disposition = PresentationDisposition(policy["events"][event.event_kind.value])
        if disposition is PresentationDisposition.MURMUR:
            vocabulary = load_murmurs_vocabulary(root)
            entries = tuple(str(item) for item in vocabulary["entries"])
            return PresentationDecision(
                event,
                disposition,
                "POLICY_MURMUR",
                _select_murmur(event, entries),
            )
        if disposition is PresentationDisposition.SILENT:
            return PresentationDecision(event, disposition, "POLICY_SILENT")
        return PresentationDecision(event, disposition, "POLICY_EXPLAIN")
    except (KeyError, OSError, TypeError, ValueError):
        return PresentationDecision(event, PresentationDisposition.EXPLAIN, "PRESENTATION_CONTRACT_INVALID")


def render_presentation(decision: PresentationDecision) -> str | None:
    if decision.disposition is PresentationDisposition.SILENT:
        return ""
    if decision.disposition is PresentationDisposition.MURMUR:
        return decision.murmur_text
    return None


def lifecycle_presentation_event(signal: LifecycleSignal, sequence: int) -> PresentationEvent:
    if not isinstance(signal, LifecycleSignal):
        raise ValueError("lifecycle presentation input must be a LifecycleSignal")
    return PresentationEvent(
        run_id=signal.run_id,
        event_kind=_LIFECYCLE_EVENT_MAP[signal.signal_type],
        sequence=sequence,
        source_component=signal.source_component,
        evidence_refs=signal.evidence_refs,
    )


def decide_lifecycle_presentation(
    signal: LifecycleSignal,
    sequence: int,
    root: Path | str | None = None,
) -> PresentationDecision:
    return decide_presentation(lifecycle_presentation_event(signal, sequence), root)
