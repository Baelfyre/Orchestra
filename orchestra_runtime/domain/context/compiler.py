from __future__ import annotations

from typing import Any, Sequence

from ...shared.canonicalization import normalize_sha256
from .state import CONTEXT_STATE_SCHEMA_VERSION, ContinuityEvent, CurrentProjectState


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


__all__ = ["compile_context"]
