"""Pure execution-domain identity and lifecycle semantics."""

from .correlation import is_valid_correlation_id, validate_correlation_id
from .identity import RunIdentity
from .lifecycle import (
    LIFECYCLE_TRANSITIONS,
    SIGNAL_DESTINATIONS,
    SIGNAL_SOURCE_STATES,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
    apply_lifecycle_signal,
    initialize_lifecycle_snapshot,
    lifecycle_signal_fingerprint,
)

__all__ = (
    "LIFECYCLE_TRANSITIONS",
    "SIGNAL_DESTINATIONS",
    "SIGNAL_SOURCE_STATES",
    "LifecycleSignal",
    "LifecycleSignalType",
    "LifecycleSnapshot",
    "LifecycleState",
    "RunIdentity",
    "StructuredTerminalResult",
    "apply_lifecycle_signal",
    "initialize_lifecycle_snapshot",
    "is_valid_correlation_id",
    "lifecycle_signal_fingerprint",
    "validate_correlation_id",
)
