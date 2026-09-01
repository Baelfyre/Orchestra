"""Canonical domain context state and continuity semantics."""

from .state import CONTEXT_STATE_SCHEMA_VERSION, ContinuityEvent, CurrentProjectState

__all__ = [
    "CONTEXT_STATE_SCHEMA_VERSION",
    "ContinuityEvent",
    "CurrentProjectState",
]
