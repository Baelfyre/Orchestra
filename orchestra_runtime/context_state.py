"""Legacy context-state compatibility surface during architecture migration.

AR-2 moves pure context state/event semantics into :mod:`orchestra_runtime.domain.context`.
This module intentionally retains application compilation, filesystem persistence, and Markdown
presentation until their owning AR phases extract them. Existing imports of the domain types are
identity-preserved through re-export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .domain.context.state import (
    CONTEXT_STATE_SCHEMA_VERSION,
    ContinuityEvent,
    CurrentProjectState,
    _text,
)
from .shared.canonicalization import canonical_json_bytes, normalize_sha256


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


__all__ = [
    "CONTEXT_STATE_SCHEMA_VERSION",
    "ContinuityEvent",
    "CurrentProjectState",
    "JsonlContinuityStore",
    "assert_markdown_parity",
    "compile_context",
    "render_state_markdown",
]
