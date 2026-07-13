from dataclasses import FrozenInstanceError

import pytest

from orchestra_runtime.authority import AuthorityProvenance, ProvenanceSource
from orchestra_runtime.errors import InvalidLifecycleSignalError
from orchestra_runtime.lifecycle import (
    LifecycleController,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
)
from orchestra_runtime.models import RunIdentity


def provenance() -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, "runtime.policy", "1", "runtime")


def test_lifecycle_states_have_stable_strings_and_terminal_classification():
    assert LifecycleState.INITIALIZING.value == "INITIALIZING"
    assert LifecycleState.WAITING.terminal is False
    assert LifecycleState.COMPLETED.terminal is True


def test_terminal_result_requires_terminal_state_and_is_immutable():
    with pytest.raises(InvalidLifecycleSignalError, match="terminal state"):
        StructuredTerminalResult("run-1", LifecycleState.ACTIVE, "ACTIVE")

    result = StructuredTerminalResult("run-1", LifecycleState.COMPLETED, "DONE", "ok", ["evidence-1"])  # type: ignore[arg-type]
    assert result.to_dict()["state"] == "COMPLETED"
    with pytest.raises(FrozenInstanceError):
        result.state = LifecycleState.FAILED  # type: ignore[misc]


def test_lifecycle_signal_validates_state_and_terminal_payload_placement():
    result = StructuredTerminalResult("run-1", LifecycleState.COMPLETED, "DONE")
    signal = LifecycleSignal(
        "signal-1",
        "run-1",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
        "DONE",
        "runtime",
        provenance(),
        terminal_result=result,
    )

    assert signal.to_dict()["terminal_result"]["state"] == "COMPLETED"  # type: ignore[index]
    with pytest.raises(InvalidLifecycleSignalError, match="does not match"):
        LifecycleSignal(
            "signal-2",
            "run-1",
            LifecycleSignalType.WAIT,
            LifecycleState.ACTIVE,
            LifecycleState.COMPLETED,
            "WAIT",
            "runtime",
            provenance(),
            terminal_result=result,
        )
    with pytest.raises(InvalidLifecycleSignalError, match="non-terminal"):
        LifecycleSignal(
            "signal-3",
            "run-1",
            LifecycleSignalType.WAIT,
            LifecycleState.ACTIVE,
            LifecycleState.WAITING,
            "WAIT",
            "runtime",
            provenance(),
            terminal_result=result,
        )


def test_lifecycle_snapshot_validates_terminal_result_and_exposes_controller():
    active = LifecycleSnapshot(RunIdentity("run-1"), LifecycleState.ACTIVE)
    assert active.to_dict()["terminal_result"] is None
    with pytest.raises(InvalidLifecycleSignalError, match="requires matching"):
        LifecycleSnapshot(RunIdentity("run-1"), LifecycleState.COMPLETED)

    assert LifecycleController is not None


def test_lifecycle_rejects_empty_fields_terminal_mismatch_and_nonterminal_result():
    with pytest.raises(InvalidLifecycleSignalError):
        StructuredTerminalResult("", LifecycleState.COMPLETED, "DONE")
    result = StructuredTerminalResult("run-1", LifecycleState.COMPLETED, "DONE")
    with pytest.raises(InvalidLifecycleSignalError, match="matching terminal"):
        LifecycleSignal(
            "signal",
            "run-2",
            LifecycleSignalType.COMPLETE,
            LifecycleState.ACTIVE,
            LifecycleState.COMPLETED,
            "DONE",
            "runtime",
            provenance(),
            terminal_result=result,
        )
    with pytest.raises(InvalidLifecycleSignalError, match="non-terminal snapshot"):
        LifecycleSnapshot(RunIdentity("run-1"), LifecycleState.ACTIVE, terminal_result=result)
