from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    CollaborationSession,
    CollaborationStatus,
    CoordinationController,
    CoordinationSignalType,
    CoordinationValidationResult,
    InvalidationEvent,
    InvalidationTargetKind,
)
from orchestra_runtime.errors import (
    ConflictingCoordinationSignalError,
    CoordinationReadinessError,
    InvalidCoordinationSignalError,
    RuntimeAuditError,
    RuntimeContractError,
)
from orchestra_runtime.interfaces import IAuditSink
from orchestra_runtime.services import AuditLogger, CoordinationRuntimeService, InMemoryAuditSink

from coordination_support import build_session, ready_session, signal, with_evidence
from test_runtime_authority_integration import RecordingLifecycleController, build_active_environment


class RecordingCoordinationController(CoordinationController):
    def __init__(self, sequence: list[str] | None = None, validation_result: object | None = None) -> None:
        self.sequence = sequence if sequence is not None else []
        self.validation_result = validation_result
        self.validation_calls = 0

    def validate(self, session: CollaborationSession):
        self.validation_calls += 1
        self.sequence.append("coordination-validate")
        if self.validation_result is not None:
            return self.validation_result
        return super().validate(session)


class FailingAuditSink(IAuditSink):
    def write(self, entry: dict[str, object]) -> str:
        raise OSError("audit unavailable")


def test_runtime_executor_constructs_one_public_coordination_service() -> None:
    environment = build_active_environment()
    service = environment.executor.coordination

    assert isinstance(service, CoordinationRuntimeService)
    assert environment.executor.coordination is service


def test_direct_execution_bypasses_coordination_validation() -> None:
    sequence: list[str] = []
    controller = RecordingCoordinationController(sequence)
    environment = build_active_environment(
        run_id="direct-bypass-run",
        sequence=sequence,
        coordination_controller=controller,
    )

    result = environment.executor.execute(environment.adapter, "conductor")

    assert result.success is True
    assert controller.validation_calls == 0
    assert "coordination-validate" not in sequence


def test_supplied_session_validates_before_lifecycle_and_adapter_access() -> None:
    sequence: list[str] = []
    controller = RecordingCoordinationController(sequence)
    environment = build_active_environment(
        run_id="coordination-preflight-run",
        sequence=sequence,
        lifecycle_controller=RecordingLifecycleController(sequence),
        coordination_controller=controller,
    )
    session = build_session()
    fingerprint = session.fingerprint

    result = environment.executor.execute(
        environment.adapter,
        "conductor",
        coordination_session=session,
    )

    assert result.success is True
    assert controller.validation_calls == 1
    assert sequence.index("coordination-validate") < sequence.index("lifecycle-initialize")
    assert sequence.index("coordination-validate") < sequence.index("adapter-context")
    assert session.fingerprint == fingerprint


def test_blocked_preflight_fails_before_lifecycle_adapter_and_audit() -> None:
    sequence: list[str] = []
    blocked = CoordinationValidationResult(
        False,
        "BLOCKED",
        ("OPEN_CONTRADICTION",),
        ("open contradiction requires external resolution",),
    )
    controller = RecordingCoordinationController(sequence, blocked)
    environment = build_active_environment(
        run_id="coordination-blocked-run",
        sequence=sequence,
        coordination_controller=controller,
    )
    session = build_session()

    with pytest.raises(CoordinationReadinessError) as error:
        environment.executor.execute(
            environment.adapter,
            "conductor",
            coordination_session=session,
        )

    assert error.value.reason_code == "RUNTIME_COORDINATION_BLOCKED"
    assert dict(error.value.context) == {
        "blocker_codes": "OPEN_CONTRADICTION",
        "collaboration_status": "COLLECTING",
        "session_id": session.session_id,
    }
    assert sequence == ["coordination-validate"]
    assert environment.sink.entries == []


def test_malformed_controller_validation_result_fails_closed() -> None:
    controller = RecordingCoordinationController(validation_result=object())
    environment = build_active_environment(
        run_id="coordination-malformed-run",
        coordination_controller=controller,
    )

    with pytest.raises(RuntimeContractError) as error:
        environment.executor.execute(
            environment.adapter,
            "conductor",
            coordination_session=build_session(),
        )

    assert error.value.reason_code == "INVALID_COORDINATION_VALIDATION_RESULT"
    assert environment.adapter.sequence == []


def test_real_stale_session_is_blocked_before_runtime_initialization() -> None:
    ready = ready_session()
    invalidation = InvalidationEvent(
        "invalidation.phase4-stale",
        ready.session_id,
        ready.current_revision,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        ("evidence.ready",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    invalidatable = replace(ready, invalidation_events=(invalidation,))
    stale = CoordinationController().apply(
        invalidatable,
        signal(
            "signal.phase4-stale",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="overseer",
        ),
    )
    environment = build_active_environment(run_id="coordination-stale-run")

    with pytest.raises(CoordinationReadinessError) as error:
        environment.executor.execute(
            environment.adapter,
            "conductor",
            coordination_session=stale,
        )

    assert error.value.reason_code == "RUNTIME_COORDINATION_BLOCKED"
    assert "OPEN_INVALIDATION" in dict(error.value.context)["blocker_codes"]
    assert environment.adapter.sequence == []
    assert environment.sink.entries == []


def test_coordination_preflight_does_not_expand_authority_or_capability() -> None:
    environment = build_active_environment(run_id="coordination-authority-preservation-run")
    scope = environment.composition.root_authority
    manifest = environment.composition.capability_manifest

    result = environment.executor.execute(
        environment.adapter,
        "conductor",
        coordination_session=build_session(),
    )

    assert result.success is True
    assert environment.composition.root_authority is scope
    assert environment.composition.capability_manifest is manifest
    assert environment.composition.root_authority.operations == ("execute",)
    assert all(grant.allowed_operations == ("execute",) for grant in manifest.grants)


def test_validation_only_service_call_emits_no_audit_event() -> None:
    sink = InMemoryAuditSink()
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(sink))

    result = service.validate(build_session())

    assert result.allowed is True
    assert sink.entries == []


def test_accepted_transition_audits_once_and_exact_replay_does_not_duplicate() -> None:
    sink = InMemoryAuditSink()
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(sink))
    session = with_evidence(build_session(), CollaborationStatus.READY, "evidence.ready")
    mark_ready = signal(
        "signal.phase4-ready",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )

    updated = service.apply(session, mark_ready)
    replayed = service.apply(updated, mark_ready)

    assert updated.status is CollaborationStatus.READY
    assert replayed is updated
    assert [entry["event_type"] for entry in sink.entries] == ["COLLABORATION_STATUS_TRANSITIONED"]


def test_typed_rejection_audits_once_and_reraises_original_error() -> None:
    sink = InMemoryAuditSink()
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(sink))
    session = with_evidence(build_session(), CollaborationStatus.READY, "evidence.ready")
    unauthorized = signal(
        "signal.phase4-unauthorized",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        source_component="the-tuner",
        evidence_refs=("evidence.ready",),
    )

    with pytest.raises(InvalidCoordinationSignalError) as error:
        service.apply(session, unauthorized)

    assert error.value.reason_code == "UNAUTHORIZED_COORDINATION_SIGNAL_SOURCE"
    assert [entry["event_type"] for entry in sink.entries] == ["COORDINATION_INPUT_REJECTED"]


def test_audit_failure_fails_closed_without_mutating_source_session() -> None:
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(FailingAuditSink()))
    session = with_evidence(build_session(), CollaborationStatus.READY, "evidence.ready")
    fingerprint = session.fingerprint
    mark_ready = signal(
        "signal.phase4-audit-failure",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )

    with pytest.raises(RuntimeAuditError) as error:
        service.apply(session, mark_ready)

    assert error.value.reason_code == "AUDIT_SINK_FAILURE"
    assert session.status is CollaborationStatus.COLLECTING
    assert session.fingerprint == fingerprint


def test_conflicting_replay_audits_rejection_once_and_preserves_state() -> None:
    sink = InMemoryAuditSink()
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(sink))
    session = with_evidence(build_session(), CollaborationStatus.READY, "evidence.ready")
    accepted = signal(
        "signal.phase4-conflict",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        reason="phase4-original",
        evidence_refs=("evidence.ready",),
    )
    updated = service.apply(session, accepted)
    fingerprint = updated.fingerprint
    accepted_count = len(updated.accepted_signals)
    conflicting = signal(
        "signal.phase4-conflict",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        reason="phase4-conflicting-replay",
        evidence_refs=("evidence.ready",),
    )

    with pytest.raises(ConflictingCoordinationSignalError) as error:
        service.apply(updated, conflicting)

    assert error.value.reason_code == "CONFLICTING_COORDINATION_SIGNAL"
    assert updated.fingerprint == fingerprint
    assert len(updated.accepted_signals) == accepted_count
    assert [entry["event_type"] for entry in sink.entries] == [
        "COLLABORATION_STATUS_TRANSITIONED",
        "COORDINATION_INPUT_REJECTED",
    ]


def test_coordination_preflight_preserves_dagger_and_external_action_default_deny() -> None:
    environment = build_active_environment(
        run_id="coordination-authority-regression-run"
    )

    result = environment.executor.execute(
        environment.adapter,
        "conductor",
        coordination_session=build_session(),
    )

    assert result.success is True
    assert environment.composition.policy.binding_for("dagger", "dagger") is None
    assert (
        environment.composition.policy.binding_for(
            "external-action",
            "conductor",
        )
        is None
    )
    assert environment.composition.root_authority.operations == ("execute",)
    assert all(
        grant.allowed_operations == ("execute",)
        for grant in environment.composition.capability_manifest.grants
    )
