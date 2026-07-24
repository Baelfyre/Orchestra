from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    CollaborationStatus,
    ContractReadiness,
    CoordinationController,
    CoordinationSignalType,
    EvidenceStatus,
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

from coordination_support import (
    build_session,
    evidence_for,
    frozen_session,
    ready_session,
    signal,
    with_evidence,
)


def test_ready_and_freeze_transitions_are_evidence_bound_and_idempotent():
    controller = CoordinationController()
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    mark_ready = signal(
        "signal.ready",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )
    ready = controller.apply(collecting, mark_ready)
    assert ready.status is CollaborationStatus.READY
    assert ready.contract.status is ContractReadiness.READY_FOR_FREEZE
    assert controller.validate(ready).allowed is True

    ready = with_evidence(ready, CollaborationStatus.FROZEN, "evidence.freeze")
    freeze = signal(
        "signal.freeze",
        CoordinationSignalType.FREEZE,
        CollaborationStatus.READY,
        CollaborationStatus.FROZEN,
        evidence_refs=("evidence.freeze",),
    )
    frozen = controller.apply(ready, freeze)
    assert frozen.status is CollaborationStatus.FROZEN
    assert frozen.contract.status is ContractReadiness.FROZEN
    assert controller.apply(frozen, freeze) is frozen

    event = coordination_transition_event(ready, freeze, frozen)
    assert event.event_type.value == "CONTRACT_FROZEN"
    assert dict(event.details)["from_status"] == "READY"
    assert dict(event.details)["to_status"] == "FROZEN"


def test_non_adjacent_signal_id_replay_is_session_wide():
    controller = CoordinationController()
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    first = signal(
        "signal.shared",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )
    ready = controller.apply(collecting, first)
    ready = with_evidence(ready, CollaborationStatus.FROZEN, "evidence.freeze")
    frozen = controller.apply(
        ready,
        signal(
            "signal.freeze",
            CoordinationSignalType.FREEZE,
            CollaborationStatus.READY,
            CollaborationStatus.FROZEN,
            evidence_refs=("evidence.freeze",),
        ),
    )

    assert controller.apply(frozen, first) is frozen
    changed = signal(
        "signal.shared",
        CoordinationSignalType.INVALIDATE,
        CollaborationStatus.FROZEN,
        CollaborationStatus.STALE,
        source_component="the-tuner",
    )
    with pytest.raises(ConflictingCoordinationSignalError):
        controller.apply(frozen, changed)


def test_unauthorized_signal_sources_fail_closed():
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    with pytest.raises(InvalidCoordinationSignalError) as exc:
        CoordinationController().apply(
            collecting,
            signal(
                "signal.tuner-ready",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                source_component="the-tuner",
                evidence_refs=("evidence.ready",),
            ),
        )
    assert exc.value.reason_code == "UNAUTHORIZED_COORDINATION_SIGNAL_SOURCE"

    ready = ready_session()
    ready = with_evidence(ready, CollaborationStatus.FROZEN, "evidence.freeze")
    with pytest.raises(InvalidCoordinationSignalError):
        CoordinationController().apply(
            ready,
            signal(
                "signal.tuner-freeze",
                CoordinationSignalType.FREEZE,
                CollaborationStatus.READY,
                CollaborationStatus.FROZEN,
                source_component="the-tuner",
                evidence_refs=("evidence.freeze",),
            ),
        )


def test_ready_freeze_and_close_require_current_overseer_evidence():
    controller = CoordinationController()
    collecting = build_session()
    with pytest.raises(CoordinationReadinessError) as exc:
        controller.apply(
            collecting,
            signal(
                "signal.ready-no-evidence",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
            ),
        )
    assert exc.value.reason_code == "COORDINATION_EVIDENCE_REQUIRED"

    stale_evidence_session = with_evidence(
        collecting,
        CollaborationStatus.READY,
        "evidence.ready",
        evidence_status=EvidenceStatus.STALE,
    )
    with pytest.raises(CoordinationReadinessError):
        controller.apply(
            stale_evidence_session,
            signal(
                "signal.ready-stale",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                evidence_refs=("evidence.ready",),
            ),
        )

    frozen = frozen_session()
    with pytest.raises(CoordinationReadinessError):
        controller.apply(
            frozen,
            signal(
                "signal.close-no-evidence",
                CoordinationSignalType.CLOSE,
                CollaborationStatus.FROZEN,
                CollaborationStatus.CLOSED,
            ),
        )


def test_wrong_contract_evidence_is_rejected():
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.FROZEN, "evidence.freeze")
    with pytest.raises(CoordinationReadinessError) as exc:
        CoordinationController().apply(
            collecting,
            signal(
                "signal.ready-wrong-contract",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                evidence_refs=("evidence.freeze",),
            ),
        )
    assert exc.value.reason_code == "COORDINATION_EVIDENCE_REQUIRED"


def test_expected_status_revision_signal_type_and_invalid_transition_fail_closed():
    controller = CoordinationController()
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")

    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(
            collecting,
            signal(
                "signal.wrong-status",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.INCOMPLETE,
                CollaborationStatus.READY,
                evidence_refs=("evidence.ready",),
            ),
        )
    assert exc.value.reason_code == "EXPECTED_COORDINATION_STATUS_MISMATCH"

    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(
            collecting,
            signal(
                "signal.stale",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                revision=2,
                evidence_refs=("evidence.ready",),
            ),
        )
    assert exc.value.reason_code == "STALE_COORDINATION_SIGNAL"

    with pytest.raises(InvalidCoordinationSignalError) as exc:
        controller.apply(
            collecting,
            signal(
                "signal.malformed",
                CoordinationSignalType.MARK_INCOMPLETE,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                source_component="conductor",
            ),
        )
    assert exc.value.reason_code == "COORDINATION_SIGNAL_STATUS_MISMATCH"

    with pytest.raises(InvalidCoordinationTransitionError):
        controller.apply(
            collecting,
            signal(
                "signal.freeze-too-early",
                CoordinationSignalType.FREEZE,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.FROZEN,
                evidence_refs=("evidence.ready",),
            ),
        )


def test_open_invalidation_blocks_ready_and_drives_stale_transition():
    event = InvalidationEvent(
        "invalidation.phase3",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        ("evidence.ready",),
        ("overseer", "ponytail"),
        ("overseer",),
        InvalidationStatus.OPEN,
    )
    base = build_session()
    ready_evidence = evidence_for(base, CollaborationStatus.READY, evidence_id="evidence.ready")
    collecting = build_session(invalidations=(event,), evidence_records=(ready_evidence,))
    controller = CoordinationController()

    with pytest.raises(CoordinationReadinessError):
        controller.apply(
            collecting,
            signal(
                "signal.ready",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                evidence_refs=("evidence.ready",),
            ),
        )

    ready = ready_session()
    event = replace(event, target_refs=("evidence.ready",))
    ready_with_event = replace(ready, invalidation_events=(event,))
    stale = controller.apply(
        ready_with_event,
        signal(
            "signal.invalidate",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="the-tuner",
        ),
    )
    assert stale.status is CollaborationStatus.STALE
    assert stale.contract.status is ContractReadiness.STALE


def test_stale_session_cannot_close_successfully():
    ready = ready_session()
    event = InvalidationEvent(
        "invalidation.phase3",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        ("evidence.ready",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    stale = CoordinationController().apply(
        replace(ready, invalidation_events=(event,)),
        signal(
            "signal.invalidate",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="the-tuner",
        ),
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
