from __future__ import annotations

from hashlib import sha256
import json

from .authority import AuthorityProvenance
from .domain.execution.lifecycle import (
    FINGERPRINT_PATTERN,
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
from .errors import (
    ConflictingTerminalSignalError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
    RuntimeContractError,
)
from .interfaces import ILifecycleController
from .models import AuditEventType, RunIdentity, RuntimeAuditEvent


def _stable_id(prefix: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}.{sha256(encoded).hexdigest()[:24]}"


class LifecycleController(ILifecycleController):
    def initialize(self, run_id: str, correlation_id: str | None = None) -> LifecycleSnapshot:
        return initialize_lifecycle_snapshot(run_id, correlation_id)

    def apply(self, snapshot: LifecycleSnapshot, signal: object) -> LifecycleSnapshot:
        return apply_lifecycle_signal(snapshot, signal)

    def terminal_result(self, snapshot: LifecycleSnapshot) -> StructuredTerminalResult | None:
        return snapshot.terminal_result


def lifecycle_transition_event(
    previous: LifecycleSnapshot,
    signal: LifecycleSignal,
    current: LifecycleSnapshot,
) -> RuntimeAuditEvent:
    fingerprint = lifecycle_signal_fingerprint(signal)
    if (
        signal.run_id != previous.run_identity.run_id
        or current.run_identity != previous.run_identity
        or signal.expected_state is not previous.state
        or signal.requested_state is not current.state
        or current.last_signal_id != signal.signal_id
        or current.accepted_signal_fingerprint != fingerprint
    ):
        raise InvalidLifecycleSignalError("transition event requires matching accepted signal", "INVALID_SIGNAL_IDENTITY")
    return RuntimeAuditEvent(
        _stable_id("event", {"type": AuditEventType.LIFECYCLE_TRANSITIONED.value, "signal": signal.to_dict()}),
        AuditEventType.LIFECYCLE_TRANSITIONED,
        signal.run_id,
        signal.signal_id,
        signal.reason_code,
        provenance_ids=(signal.provenance.source_id,),
        details=(
            ("accepted", "true"),
            ("from_state", previous.state.value),
            ("signal_fingerprint", fingerprint),
            ("to_state", current.state.value),
        ),
        parent_run_id=current.run_identity.parent_run_id,
    )


def lifecycle_rejection_event(
    snapshot: LifecycleSnapshot,
    signal: object,
    error: RuntimeContractError,
) -> RuntimeAuditEvent:
    structured = signal if isinstance(signal, LifecycleSignal) else None
    signal_id = structured.signal_id if structured else _stable_id(
        "invalid-signal",
        {"run_id": snapshot.run_identity.run_id, "state": snapshot.state.value, "input_type": type(signal).__name__},
    )
    requested_state = structured.requested_state.value if structured else ""
    return RuntimeAuditEvent(
        _stable_id(
            "event",
            {
                "type": AuditEventType.LIFECYCLE_TRANSITIONED.value,
                "run_id": snapshot.run_identity.run_id,
                "state": snapshot.state.value,
                "signal_id": signal_id,
                "reason_code": error.reason_code,
                "requested_state": requested_state,
            },
        ),
        AuditEventType.LIFECYCLE_TRANSITIONED,
        snapshot.run_identity.run_id,
        signal_id,
        error.reason_code,
        provenance_ids=(
            (structured.provenance.source_id,)
            if structured
            else (snapshot.accepted_signal_fingerprint or signal_id,)
        ),
        details=(
            ("accepted", "false"),
            ("from_state", snapshot.state.value),
            ("to_state", requested_state),
        ),
        parent_run_id=snapshot.run_identity.parent_run_id,
    )


def terminal_result_event(snapshot: LifecycleSnapshot) -> RuntimeAuditEvent:
    if not snapshot.state.terminal or snapshot.terminal_result is None or snapshot.last_signal_id is None:
        raise InvalidLifecycleSignalError("terminal result event requires terminal snapshot", "INVALID_TERMINAL_RESULT")
    return RuntimeAuditEvent(
        _stable_id("event", {"type": AuditEventType.TERMINAL_RESULT_RECORDED.value, "snapshot": snapshot.to_dict()}),
        AuditEventType.TERMINAL_RESULT_RECORDED,
        snapshot.run_identity.run_id,
        snapshot.last_signal_id,
        snapshot.terminal_result.reason_code,
        provenance_ids=(snapshot.accepted_signal_fingerprint or snapshot.last_signal_id,),
        details=(
            ("signal_fingerprint", snapshot.accepted_signal_fingerprint or ""),
            ("state", snapshot.state.value),
        ),
        parent_run_id=snapshot.run_identity.parent_run_id,
    )
