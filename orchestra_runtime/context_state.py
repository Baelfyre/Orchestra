from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .domain.context import (
    CONTEXT_STATE_SCHEMA_VERSION,
    ContinuityEvent,
    CurrentProjectState,
    compile_context,
)
from .shared.canonicalization import canonical_json_bytes


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


class JsonlContinuityStore:
    """Legacy filesystem-backed continuity store retained until infrastructure extraction."""

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
