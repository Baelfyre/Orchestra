from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re
from types import MappingProxyType

from .authority import AuthorityProvenance
from .errors import (
    ConflictingTerminalSignalError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
    RuntimeContractError,
)
from .interfaces import ILifecycleController
from .models import AuditEventType, RunIdentity, RuntimeAuditEvent


class LifecycleState(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED = "BLOCKED"

    @property
    def terminal(self) -> bool:
        return self in {
            LifecycleState.COMPLETED,
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
            LifecycleState.TIMED_OUT,
            LifecycleState.BLOCKED,
        }


class LifecycleSignalType(str, Enum):
    ACTIVATE = "ACTIVATE"
    WAIT = "WAIT"
    RESUME = "RESUME"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    CANCEL = "CANCEL"
    TIME_OUT = "TIME_OUT"
    BLOCK = "BLOCK"


SIGNAL_DESTINATIONS = MappingProxyType({
    LifecycleSignalType.ACTIVATE: LifecycleState.ACTIVE,
    LifecycleSignalType.WAIT: LifecycleState.WAITING,
    LifecycleSignalType.RESUME: LifecycleState.ACTIVE,
    LifecycleSignalType.COMPLETE: LifecycleState.COMPLETED,
    LifecycleSignalType.FAIL: LifecycleState.FAILED,
    LifecycleSignalType.CANCEL: LifecycleState.CANCELLED,
    LifecycleSignalType.TIME_OUT: LifecycleState.TIMED_OUT,
    LifecycleSignalType.BLOCK: LifecycleState.BLOCKED,
})

SIGNAL_SOURCE_STATES = MappingProxyType({
    LifecycleSignalType.ACTIVATE: LifecycleState.INITIALIZING,
    LifecycleSignalType.WAIT: LifecycleState.ACTIVE,
    LifecycleSignalType.RESUME: LifecycleState.WAITING,
})

LIFECYCLE_TRANSITIONS = MappingProxyType(
    {
        LifecycleState.INITIALIZING: frozenset(
            {
                LifecycleState.ACTIVE,
                LifecycleState.FAILED,
                LifecycleState.CANCELLED,
                LifecycleState.TIMED_OUT,
                LifecycleState.BLOCKED,
            }
        ),
        LifecycleState.ACTIVE: frozenset(
            {
                LifecycleState.WAITING,
                LifecycleState.COMPLETED,
                LifecycleState.FAILED,
                LifecycleState.CANCELLED,
                LifecycleState.TIMED_OUT,
                LifecycleState.BLOCKED,
            }
        ),
        LifecycleState.WAITING: frozenset(
            {
                LifecycleState.ACTIVE,
                LifecycleState.FAILED,
                LifecycleState.CANCELLED,
                LifecycleState.TIMED_OUT,
                LifecycleState.BLOCKED,
            }
        ),
        LifecycleState.COMPLETED: frozenset(),
        LifecycleState.FAILED: frozenset(),
        LifecycleState.CANCELLED: frozenset(),
        LifecycleState.TIMED_OUT: frozenset(),
        LifecycleState.BLOCKED: frozenset(),
    }
)

FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _stable_id(prefix: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}.{sha256(encoded).hexdigest()[:24]}"


def _text(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise InvalidLifecycleSignalError(
            f"{field_name} must be non-empty",
            "INVALID_SIGNAL",
            {"field": field_name},
        )
    return text


@dataclass(frozen=True, slots=True)
class StructuredTerminalResult:
    run_id: str
    state: LifecycleState
    reason_code: str
    output: str = ""
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        state = LifecycleState(self.state)
        if not state.terminal:
            raise InvalidLifecycleSignalError("terminal result requires terminal state", "INVALID_TERMINAL_RESULT")
        object.__setattr__(self, "run_id", _text(self.run_id, "run_id"))
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "reason_code", _text(self.reason_code, "reason_code"))
        object.__setattr__(self, "output", str(self.output))
        object.__setattr__(self, "evidence_refs", tuple(sorted({_text(item, "evidence_ref") for item in self.evidence_refs})))

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "state": self.state.value,
            "reason_code": self.reason_code,
            "output": self.output,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class LifecycleSignal:
    signal_id: str
    run_id: str
    signal_type: LifecycleSignalType
    expected_state: LifecycleState
    requested_state: LifecycleState
    reason_code: str
    source_component: str
    provenance: AuthorityProvenance
    evidence_refs: tuple[str, ...] = ()
    terminal_result: StructuredTerminalResult | None = None

    def __post_init__(self) -> None:
        signal_type = LifecycleSignalType(self.signal_type)
        expected_state = LifecycleState(self.expected_state)
        requested_state = LifecycleState(self.requested_state)
        run_id = _text(self.run_id, "run_id")
        if SIGNAL_DESTINATIONS[signal_type] is not requested_state:
            raise InvalidLifecycleSignalError(
                "signal type does not match requested state",
                "STATE_SIGNAL_MISMATCH",
                {"signal_type": signal_type.value, "requested_state": requested_state.value},
            )
        if requested_state.terminal:
            if self.terminal_result is None or self.terminal_result.run_id != run_id or self.terminal_result.state is not requested_state:
                raise InvalidLifecycleSignalError("terminal signal requires matching terminal result", "INVALID_TERMINAL_RESULT")
        elif self.terminal_result is not None:
            raise InvalidLifecycleSignalError("non-terminal signal cannot carry terminal result", "INVALID_TERMINAL_RESULT")
        object.__setattr__(self, "signal_id", _text(self.signal_id, "signal_id"))
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "signal_type", signal_type)
        object.__setattr__(self, "expected_state", expected_state)
        object.__setattr__(self, "requested_state", requested_state)
        object.__setattr__(self, "reason_code", _text(self.reason_code, "reason_code"))
        object.__setattr__(self, "source_component", _text(self.source_component, "source_component"))
        object.__setattr__(self, "evidence_refs", tuple(sorted({_text(item, "evidence_ref") for item in self.evidence_refs})))

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "run_id": self.run_id,
            "signal_type": self.signal_type.value,
            "expected_state": self.expected_state.value,
            "requested_state": self.requested_state.value,
            "reason_code": self.reason_code,
            "source_component": self.source_component,
            "provenance": self.provenance.to_dict(),
            "evidence_refs": list(self.evidence_refs),
            "terminal_result": self.terminal_result.to_dict() if self.terminal_result else None,
        }


@dataclass(frozen=True, slots=True)
class LifecycleSnapshot:
    run_identity: RunIdentity
    state: LifecycleState
    last_signal_id: str | None = None
    terminal_result: StructuredTerminalResult | None = None
    accepted_signal_fingerprint: str | None = None

    def __post_init__(self) -> None:
        state = LifecycleState(self.state)
        last_signal_id = self.last_signal_id.strip() if self.last_signal_id else None
        fingerprint = self.accepted_signal_fingerprint.strip() if self.accepted_signal_fingerprint else None
        if bool(last_signal_id) != bool(fingerprint) or (fingerprint and not FINGERPRINT_PATTERN.fullmatch(fingerprint)):
            raise InvalidLifecycleSignalError(
                "accepted signal identity requires a deterministic fingerprint",
                "INVALID_SIGNAL_IDENTITY",
            )
        if state.terminal:
            if self.terminal_result is None or self.terminal_result.run_id != self.run_identity.run_id or self.terminal_result.state is not state:
                raise InvalidLifecycleSignalError("terminal snapshot requires matching result", "INVALID_TERMINAL_RESULT")
            if last_signal_id is None:
                raise InvalidLifecycleSignalError("terminal snapshot requires accepted signal identity", "INVALID_SIGNAL_IDENTITY")
        elif self.terminal_result is not None:
            raise InvalidLifecycleSignalError("non-terminal snapshot cannot carry terminal result", "INVALID_TERMINAL_RESULT")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "last_signal_id", last_signal_id)
        object.__setattr__(self, "accepted_signal_fingerprint", fingerprint)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_identity": self.run_identity.to_dict(),
            "state": self.state.value,
            "last_signal_id": self.last_signal_id,
            "terminal_result": self.terminal_result.to_dict() if self.terminal_result else None,
            "accepted_signal_fingerprint": self.accepted_signal_fingerprint,
        }


def lifecycle_signal_fingerprint(signal: LifecycleSignal) -> str:
    return sha256(
        json.dumps(signal.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


class LifecycleController(ILifecycleController):
    def initialize(self, run_id: str) -> LifecycleSnapshot:
        return LifecycleSnapshot(RunIdentity(_text(run_id, "run_id")), LifecycleState.INITIALIZING)

    def apply(self, snapshot: LifecycleSnapshot, signal: object) -> LifecycleSnapshot:
        if not isinstance(signal, LifecycleSignal):
            raise InvalidLifecycleSignalError("lifecycle input must be a structured signal", "INVALID_SIGNAL")
        if signal.run_id != snapshot.run_identity.run_id:
            raise InvalidLifecycleSignalError(
                "signal run_id does not match lifecycle snapshot",
                "RUN_ID_MISMATCH",
                {"run_id": signal.run_id},
            )
        fingerprint = lifecycle_signal_fingerprint(signal)
        if snapshot.state.terminal:
            if signal.requested_state.terminal:
                if signal.signal_id == snapshot.last_signal_id and fingerprint == snapshot.accepted_signal_fingerprint:
                    return snapshot
                raise ConflictingTerminalSignalError(
                    "terminal signal conflicts with accepted terminal result",
                    "CONFLICTING_TERMINAL_SIGNAL",
                    {"signal_id": signal.signal_id},
                )
            raise InvalidLifecycleTransitionError(
                "terminal lifecycle state cannot transition",
                "TERMINAL_STATE",
                {"state": snapshot.state.value},
            )
        if signal.expected_state is not snapshot.state:
            raise InvalidLifecycleSignalError(
                "signal expected state does not match lifecycle snapshot",
                "EXPECTED_STATE_MISMATCH",
                {"expected_state": signal.expected_state.value, "state": snapshot.state.value},
            )
        if signal.requested_state not in LIFECYCLE_TRANSITIONS[snapshot.state]:
            raise InvalidLifecycleTransitionError(
                "lifecycle transition is not allowed",
                "INVALID_TRANSITION",
                {"from_state": snapshot.state.value, "to_state": signal.requested_state.value},
            )
        required_state = SIGNAL_SOURCE_STATES.get(signal.signal_type)
        if required_state is not None and snapshot.state is not required_state:
            raise InvalidLifecycleSignalError(
                "lifecycle signal is invalid for the current source state",
                "INVALID_SIGNAL_SOURCE_STATE",
                {
                    "signal_type": signal.signal_type.value,
                    "current_state": snapshot.state.value,
                    "required_state": required_state.value,
                },
            )
        return LifecycleSnapshot(
            snapshot.run_identity,
            signal.requested_state,
            signal.signal_id,
            signal.terminal_result,
            fingerprint,
        )

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
