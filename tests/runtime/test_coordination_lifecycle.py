from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    CollaborationStatus,
    ContractReadiness,
    CoordinationController,
    CoordinationSignal,
    CoordinationSignalType,
    InvalidationEvent,
    InvalidationStatus,
    InvalidationTargetKind,
    coordination_transition_event,
)
from orchestra_runtime.errors import (
    ConflictingCoordinationSignalError,
    CoordinationReadinessError,
    InvalidCoordinationSignalError,
    InvalidCoordinationTransitionError,
)

from coordination_support import build_session


def signal(
    signal_id: str,
    signal_type: CoordinationSignalType,
    expected: CollaborationStatus,
    requested: CollaborationStatus,
    *,
    reason: str = "phase3-transition",
    revision: int = 1,
) -> CoordinationSignal:
    return CoordinationSignal(
        signal_id,
        "session.phase3",
        signal_type,
        expected,
        requested,
        reason,
        "conductor",
        revision,
        ("evidence.phase3",),
    )


def test_ready_and_freeze_transitions_are_deterministic_and_idempotent():
    controller = CoordinationController()
    collecting = build_session()

    mark_ready = signal(
        "signal.ready",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
    )
    ready = controller.apply(collecting, mark_ready)
    assert ready.status is CollaborationStatus.READY
    assert ready.contract.status is ContractReadiness.READY_FOR_FREEZE
    assert controller.validate(ready).allowed is True

    freeze = signal(
        "signal.freeze",
        CoordinationSignalType.FREEZE,
        CollaborationStatus.READY,
        CollaborationStatus.FROZEN,
    )
    frozen = controller.apply(ready, freeze)
    assert frozen.status is CollaborationStatus.FROZEN
    assert frozen.contract.status is ContractReadiness.FROZEN
    assert controller.apply(frozen, freeze) is frozen

    event = coordination_transition_event(ready, freeze, frozen)
    assert event.event_type.value == "CONTRACT_FROZEN"
    assert dict(event.details)["from_status"] == "READY"
    assert dict(event.details)["to_status"] == "FROZEN"


def test_duplicate_signal_id_with_changed_payload_is_rejected():
    controller = CoordinationController()
    collecting = build_session()
    accepted = controller.apply(
        collecting,
        signal(
            "signal.ready",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
        ),
    )
    conflict = signal(
        "signal.ready",
        CoordinationSignalType.FREEZE,
        CollaborationStatus.READY,
        CollaborationStatus.FROZEN,
    )

    with pytest.raises(ConflictingCoordinationSignalError):
        controller.apply(accepted, conflict)


def test_expected_status_and_revision_mismatches_fail_closed():
    controller = CoordinationController()
    collecting = build_session()

    wrong_status = signal(
        "signal.wrong-status",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.INCOMPLETE,
        CollaborationStatus.READY,
    )
    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(collecting, wrong_status)
    assert exc.value.reason_code == "EXPECTED_COORDINATION_STATUS_MISMATCH"

    stale = signal(
        "signal.stale",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        revision=2,
    )
    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(collecting, stale)
    assert exc.value.reason_code == "STALE_COORDINATION_SIGNAL"


def test_signal_type_must_match_requested_status():
    controller = CoordinationController()
    collecting = build_session()
    malformed = signal(
        "signal.malformed",
        CoordinationSignalType.MARK_INCOMPLETE,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
    )

    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(collecting, malformed)

    assert exc.value.reason_code == "COORDINATION_SIGNAL_STATUS_MISMATCH"


def test_invalid_transition_and_closed_terminal_state_are_rejected():
    controller = CoordinationController()
    collecting = build_session()
    invalid = signal(
        "signal.freeze-too-early",
        CoordinationSignalType.FREEZE,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.FROZEN,
    )
    with pytest.raises(InvalidCoordinationTransitionError):
        controller.apply(collecting, invalid)

    closed = controller.apply(
        collecting,
        signal(
            "signal.close",
            CoordinationSignalType.CLOSE,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.CLOSED,
        ),
    )
    assert closed.status is CollaborationStatus.CLOSED
    with pytest.raises(InvalidCoordinationTransitionError):
        controller.apply(
            closed,
            signal(
                "signal.reopen",
                CoordinationSignalType.REOPEN_COLLECTION,
                CollaborationStatus.CLOSED,
                CollaborationStatus.COLLECTING,
            ),
        )


def test_open_invalidation_blocks_ready_and_drives_stale_transition():
    event = InvalidationEvent(
        "invalidation.phase3",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        ("evidence.phase3",),
        ("ponytail", "overseer"),
        ("overseer",),
        InvalidationStatus.OPEN,
    )
    collecting = build_session(invalidations=(event,))
    controller = CoordinationController()

    with pytest.raises(CoordinationReadinessError) as exc:
        controller.apply(
            collecting,
            signal(
                "signal.ready",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
            ),
        )
    assert exc.value.reason_code == "COORDINATION_NOT_READY"

    ready_without_event = controller.apply(
        build_session(),
        signal(
            "signal.ready-clean",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
        ),
    )
    ready_with_event = replace(
        ready_without_event,
        invalidation_events=(event,),
    )
    stale = controller.apply(
        ready_with_event,
        signal(
            "signal.invalidate",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
        ),
    )
    assert stale.status is CollaborationStatus.STALE
    assert stale.contract.status is ContractReadiness.STALE


def test_stale_session_cannot_close_successfully():
    event = InvalidationEvent(
        "invalidation.phase3",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        ("evidence.phase3",),
        ("ponytail", "overseer"),
        ("overseer",),
    )
    stale = build_session(
        status=CollaborationStatus.STALE,
        contract_status=ContractReadiness.STALE,
        invalidations=(event,),
    )

    with pytest.raises(CoordinationReadinessError) as exc:
        CoordinationController().apply(
            stale,
            signal(
                "signal.close-stale",
                CoordinationSignalType.CLOSE,
                CollaborationStatus.STALE,
                CollaborationStatus.CLOSED,
            ),
        )

    assert exc.value.reason_code == "COORDINATION_CLOSEOUT_BLOCKED"
