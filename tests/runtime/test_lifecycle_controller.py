from dataclasses import FrozenInstanceError

import pytest

from orchestra_runtime.authority import AuthorityProvenance, ProvenanceSource
from orchestra_runtime.errors import (
    ConflictingTerminalSignalError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
)
from orchestra_runtime.lifecycle import (
    LIFECYCLE_TRANSITIONS,
    LifecycleController,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
    lifecycle_rejection_event,
    lifecycle_signal_fingerprint,
    lifecycle_transition_event,
    terminal_result_event,
)
from orchestra_runtime.models import AuditEventType


def provenance() -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, "runtime.policy", "1", "runtime")


def signal(
    signal_id: str,
    signal_type: LifecycleSignalType,
    expected: LifecycleState,
    requested: LifecycleState,
    *,
    run_id: str = "run-1",
    output: str = "",
) -> LifecycleSignal:
    result = (
        StructuredTerminalResult(run_id, requested, requested.value, output)
        if requested.terminal
        else None
    )
    return LifecycleSignal(
        signal_id,
        run_id,
        signal_type,
        expected,
        requested,
        requested.value,
        "runtime",
        provenance(),
        terminal_result=result,
    )


def active(controller: LifecycleController) -> LifecycleSnapshot:
    initial = controller.initialize("run-1")
    return controller.apply(
        initial,
        signal("activate-1", LifecycleSignalType.ACTIVATE, LifecycleState.INITIALIZING, LifecycleState.ACTIVE),
    )


def test_exact_transition_table_initialization_waiting_and_resume():
    controller = LifecycleController()
    initial = controller.initialize("run-1")
    activate = signal("activate-1", LifecycleSignalType.ACTIVATE, LifecycleState.INITIALIZING, LifecycleState.ACTIVE)
    current = controller.apply(initial, activate)
    waiting = controller.apply(
        current,
        signal("wait-1", LifecycleSignalType.WAIT, LifecycleState.ACTIVE, LifecycleState.WAITING),
    )
    resumed = controller.apply(
        waiting,
        signal("resume-1", LifecycleSignalType.RESUME, LifecycleState.WAITING, LifecycleState.ACTIVE),
    )

    assert initial.state is LifecycleState.INITIALIZING
    assert current.accepted_signal_fingerprint == lifecycle_signal_fingerprint(activate)
    assert waiting.state is LifecycleState.WAITING
    assert waiting.state.terminal is False
    assert resumed.state is LifecycleState.ACTIVE
    assert controller.terminal_result(resumed) is None
    assert LIFECYCLE_TRANSITIONS[LifecycleState.COMPLETED] == frozenset()
    with pytest.raises(TypeError):
        LIFECYCLE_TRANSITIONS[LifecycleState.ACTIVE] = frozenset()  # type: ignore[index]


@pytest.mark.parametrize(
    ("signal_type", "state"),
    [
        (LifecycleSignalType.COMPLETE, LifecycleState.COMPLETED),
        (LifecycleSignalType.FAIL, LifecycleState.FAILED),
        (LifecycleSignalType.CANCEL, LifecycleState.CANCELLED),
        (LifecycleSignalType.TIME_OUT, LifecycleState.TIMED_OUT),
        (LifecycleSignalType.BLOCK, LifecycleState.BLOCKED),
    ],
)
def test_terminal_states_remain_distinct(signal_type, state):
    controller = LifecycleController()
    snapshot = controller.apply(active(controller), signal(f"terminal-{state.value}", signal_type, LifecycleState.ACTIVE, state))

    assert snapshot.state is state
    assert snapshot.terminal_result is not None
    assert snapshot.terminal_result.state is state
    assert controller.terminal_result(snapshot) is snapshot.terminal_result
    with pytest.raises(FrozenInstanceError):
        snapshot.state = LifecycleState.ACTIVE  # type: ignore[misc]


def test_identical_terminal_replay_is_idempotent_and_conflicts_preserve_first_result():
    controller = LifecycleController()
    terminal_signal = signal(
        "complete-1",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
        output="first",
    )
    terminal = controller.apply(active(controller), terminal_signal)

    assert controller.apply(terminal, terminal_signal) is terminal

    altered = signal(
        "complete-1",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
        output="altered",
    )
    different = signal(
        "fail-2",
        LifecycleSignalType.FAIL,
        LifecycleState.ACTIVE,
        LifecycleState.FAILED,
    )
    with pytest.raises(ConflictingTerminalSignalError):
        controller.apply(terminal, altered)
    with pytest.raises(ConflictingTerminalSignalError):
        controller.apply(terminal, different)
    assert terminal.terminal_result is not None
    assert terminal.terminal_result.output == "first"


def test_invalid_inputs_transitions_and_state_mismatches_leave_snapshot_unchanged():
    controller = LifecycleController()
    initial = controller.initialize("run-1")

    with pytest.raises(InvalidLifecycleSignalError):
        controller.initialize(None)  # type: ignore[arg-type]
    with pytest.raises(InvalidLifecycleSignalError, match="structured") as ordinary:
        controller.apply(initial, "COMPLETED")
    with pytest.raises(InvalidLifecycleSignalError, match="run_id"):
        controller.apply(
            initial,
            signal(
                "activate-other",
                LifecycleSignalType.ACTIVATE,
                LifecycleState.INITIALIZING,
                LifecycleState.ACTIVE,
                run_id="other-run",
            ),
        )
    with pytest.raises(InvalidLifecycleSignalError, match="expected state"):
        controller.apply(
            initial,
            signal("complete-early", LifecycleSignalType.COMPLETE, LifecycleState.ACTIVE, LifecycleState.COMPLETED),
        )
    invalid = signal("wait-early", LifecycleSignalType.WAIT, LifecycleState.INITIALIZING, LifecycleState.WAITING)
    with pytest.raises(InvalidLifecycleTransitionError) as transition:
        controller.apply(initial, invalid)

    assert initial == controller.initialize("run-1")
    ordinary_event = lifecycle_rejection_event(initial, "COMPLETED", ordinary.value)
    assert ordinary_event.to_dict()["details"]["accepted"] == "false"
    assert ordinary_event.provenance_ids
    assert lifecycle_rejection_event(initial, invalid, transition.value).reason_code == "INVALID_TRANSITION"


def test_terminal_state_rejects_nonterminal_transition():
    controller = LifecycleController()
    terminal = controller.apply(
        active(controller),
        signal("complete-1", LifecycleSignalType.COMPLETE, LifecycleState.ACTIVE, LifecycleState.COMPLETED),
    )
    with pytest.raises(InvalidLifecycleTransitionError, match="terminal"):
        controller.apply(
            terminal,
            signal("wait-after", LifecycleSignalType.WAIT, LifecycleState.COMPLETED, LifecycleState.WAITING),
        )


def test_transition_rejection_and_terminal_event_factories_are_deterministic():
    controller = LifecycleController()
    previous = active(controller)
    terminal_signal = signal(
        "complete-1",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
    )
    current = controller.apply(previous, terminal_signal)

    transition = lifecycle_transition_event(previous, terminal_signal, current)
    terminal = terminal_result_event(current)

    assert transition == lifecycle_transition_event(previous, terminal_signal, current)
    assert transition.event_type is AuditEventType.LIFECYCLE_TRANSITIONED
    assert terminal.event_type is AuditEventType.TERMINAL_RESULT_RECORDED
    assert terminal.provenance_ids == (current.accepted_signal_fingerprint,)
    assert terminal == terminal_result_event(current)
    with pytest.raises(InvalidLifecycleSignalError, match="matching accepted"):
        lifecycle_transition_event(previous, terminal_signal, previous)
    with pytest.raises(InvalidLifecycleSignalError, match="terminal snapshot"):
        terminal_result_event(previous)


def test_snapshot_rejects_incomplete_or_invalid_signal_fingerprint():
    controller = LifecycleController()
    current = active(controller)
    with pytest.raises(InvalidLifecycleSignalError, match="fingerprint"):
        LifecycleSnapshot(current.run_identity, current.state, "signal-only")
    with pytest.raises(InvalidLifecycleSignalError, match="fingerprint"):
        LifecycleSnapshot(current.run_identity, current.state, "signal", accepted_signal_fingerprint="bad")
