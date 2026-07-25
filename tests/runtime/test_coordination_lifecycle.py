import copy
from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    CollaborationStatus,
    ContradictionRecord,
    ContradictionStatus,
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
    InvalidCoordinationContractError,
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


def test_controller_receipt_preserves_complete_transition_identity():
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    transition = signal(
        "signal.ready-complete",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )
    ready = CoordinationController().apply(collecting, transition)
    receipt = ready.accepted_signals[0]

    assert receipt.signal_type is transition.signal_type
    assert receipt.expected_status is transition.expected_status
    assert receipt.requested_status is transition.requested_status
    assert receipt.source_component == "arbiter"
    assert receipt.source_revision == ready.current_revision
    assert receipt.evidence_refs == ("evidence.ready",)
    assert receipt.prior_contract_fingerprint == collecting.contract.fingerprint


def test_tampered_trusted_receipt_cannot_bypass_source_or_transition_policy():
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    ready = CoordinationController().apply(
        collecting,
        signal(
            "signal.ready-tamper",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
            evidence_refs=("evidence.ready",),
        ),
    )
    forged = copy.copy(ready.accepted_signals[0])
    object.__setattr__(forged, "source_component", "the-tuner")

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(ready, accepted_signals=(forged,))
    assert getattr(exc.value, "reason_code", None) == "UNAUTHORIZED_COORDINATION_SIGNAL_SOURCE"


def test_receipt_chain_cannot_skip_required_intermediate_state():
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    ready = CoordinationController().apply(
        collecting,
        signal(
            "signal.ready-chain",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
            evidence_refs=("evidence.ready",),
        ),
    )
    forged = copy.copy(ready.accepted_signals[0])
    object.__setattr__(forged, "requested_status", CollaborationStatus.FROZEN)
    object.__setattr__(forged, "resulting_status", CollaborationStatus.FROZEN)

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(ready, accepted_signals=(forged,))
    assert getattr(exc.value, "reason_code", None) in {
        "COORDINATION_SIGNAL_STATUS_MISMATCH",
        "INVALID_COORDINATION_TRANSITION",
        "INVALID_ACCEPTED_SIGNAL_LEDGER",
    }

def _open_current_state_contradiction() -> ContradictionRecord:
    return ContradictionRecord(
        "contradiction.current-state",
        "session.phase3",
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("impact.runtime",),
        ContradictionStatus.OPEN,
        "the-steward",
        ("review.validation",),
    )


def _current_state_invalidation(target_ref: str) -> InvalidationEvent:
    return InvalidationEvent(
        "invalidation.current-state",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        (target_ref,),
        ("overseer", "ponytail"),
        ("overseer",),
        InvalidationStatus.OPEN,
    )


def test_status_bound_blocker_records_are_required_during_session_construction():
    controller = CoordinationController()
    contradiction = _open_current_state_contradiction()
    collecting = build_session(contradictions=(contradiction,))
    contradicted = controller.apply(
        collecting,
        signal(
            "signal.contradicted-construction",
            CoordinationSignalType.MARK_CONTRADICTED,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.CONTRADICTED,
            source_component="the-tuner",
        ),
    )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(contradicted, contradictions=())
    assert exc.value.reason_code == "INVALID_COORDINATION_SESSION_STATE"

    ready = ready_session()
    event = _current_state_invalidation("evidence.ready")
    stale = controller.apply(
        replace(ready, invalidation_events=(event,)),
        signal(
            "signal.stale-construction",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="overseer",
        ),
    )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(stale, invalidation_events=())
    assert exc.value.reason_code == "INVALID_COORDINATION_SESSION_STATE"


def test_valid_blocked_sessions_preserve_corrective_transition_paths():
    controller = CoordinationController()
    contradiction = _open_current_state_contradiction()
    collecting = build_session(contradictions=(contradiction,))
    contradicted = controller.apply(
        collecting,
        signal(
            "signal.contradicted-valid",
            CoordinationSignalType.MARK_CONTRADICTED,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.CONTRADICTED,
            source_component="the-tuner",
        ),
    )
    reopened = controller.apply(
        contradicted,
        signal(
            "signal.reopen-contradicted",
            CoordinationSignalType.REOPEN_COLLECTION,
            CollaborationStatus.CONTRADICTED,
            CollaborationStatus.COLLECTING,
            source_component="conductor",
        ),
    )
    assert reopened.status is CollaborationStatus.COLLECTING
    assert reopened.open_contradictions == (contradiction,)

    ready = ready_session()
    ready_with_contradiction = replace(ready, contradictions=(contradiction,))
    contradicted_from_ready = controller.apply(
        ready_with_contradiction,
        signal(
            "signal.ready-to-contradicted",
            CoordinationSignalType.MARK_CONTRADICTED,
            CollaborationStatus.READY,
            CollaborationStatus.CONTRADICTED,
            source_component="the-tuner",
        ),
    )
    assert contradicted_from_ready.status is CollaborationStatus.CONTRADICTED

    frozen = frozen_session()
    event = _current_state_invalidation("evidence.freeze")
    stale = controller.apply(
        replace(frozen, invalidation_events=(event,)),
        signal(
            "signal.frozen-to-stale",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.FROZEN,
            CollaborationStatus.STALE,
            source_component="overseer",
        ),
    )
    reopened_stale = controller.apply(
        stale,
        signal(
            "signal.reopen-stale",
            CoordinationSignalType.REOPEN_COLLECTION,
            CollaborationStatus.STALE,
            CollaborationStatus.COLLECTING,
            source_component="conductor",
        ),
    )
    assert reopened_stale.status is CollaborationStatus.COLLECTING
    assert reopened_stale.open_invalidations == (event,)
