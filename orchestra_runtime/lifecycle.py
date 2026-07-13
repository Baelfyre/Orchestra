from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .authority import AuthorityProvenance
from .errors import InvalidLifecycleSignalError
from .models import RunIdentity


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


SIGNAL_DESTINATIONS = {
    LifecycleSignalType.ACTIVATE: LifecycleState.ACTIVE,
    LifecycleSignalType.WAIT: LifecycleState.WAITING,
    LifecycleSignalType.RESUME: LifecycleState.ACTIVE,
    LifecycleSignalType.COMPLETE: LifecycleState.COMPLETED,
    LifecycleSignalType.FAIL: LifecycleState.FAILED,
    LifecycleSignalType.CANCEL: LifecycleState.CANCELLED,
    LifecycleSignalType.TIME_OUT: LifecycleState.TIMED_OUT,
    LifecycleSignalType.BLOCK: LifecycleState.BLOCKED,
}


def _text(value: object, field_name: str) -> str:
    text = str(value).strip()
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

    def __post_init__(self) -> None:
        state = LifecycleState(self.state)
        last_signal_id = self.last_signal_id.strip() if self.last_signal_id else None
        if state.terminal:
            if self.terminal_result is None or self.terminal_result.run_id != self.run_identity.run_id or self.terminal_result.state is not state:
                raise InvalidLifecycleSignalError("terminal snapshot requires matching result", "INVALID_TERMINAL_RESULT")
        elif self.terminal_result is not None:
            raise InvalidLifecycleSignalError("non-terminal snapshot cannot carry terminal result", "INVALID_TERMINAL_RESULT")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "last_signal_id", last_signal_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_identity": self.run_identity.to_dict(),
            "state": self.state.value,
            "last_signal_id": self.last_signal_id,
            "terminal_result": self.terminal_result.to_dict() if self.terminal_result else None,
        }
