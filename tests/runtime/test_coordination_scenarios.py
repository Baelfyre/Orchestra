from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    ArtifactLifecycleState,
    ArtifactRetentionRequirement,
    CollaborationDependency,
    CollaborationStatus,
    ContradictionRecord,
    ContradictionStatus,
    CoordinationController,
    CoordinationEvidenceRecord,
    CoordinationSignalType,
    ContractReadiness,
    DependencyKind,
    EvidenceStatus,
    InvalidationEvent,
    InvalidationRule,
    InvalidationTargetKind,
)
from orchestra_runtime.errors import CoordinationReadinessError
from orchestra_runtime.services import (
    AuditLogger,
    CoordinationRuntimeService,
    InMemoryAuditSink,
)

from coordination_scenarios import (
    BusinessOperationLedger,
    DuplicateBusinessOperationError,
    SCENARIO_BY_ID,
    SCENARIOS,
    ScenarioContractViolation,
)
from coordination_support import (
    BASELINE_SHA,
    build_artifact,
    build_contract,
    build_graph,
    build_session,
    evidence_for,
    frozen_session,
    ready_session,
    signal,
    with_evidence,
)
from test_runtime_authority_integration import build_active_environment


CANONICAL_IDS = tuple(f"SCN-{index:02d}" for index in range(1, 7))
PROHIBITED_CONSUMER_IDENTIFIERS = tuple(
    "".join(parts)
    for parts in (
        ("path", "way"),
        ("hive", "mind"),
        ("motor", "ph"),
    )
)
COORDINATION_EVENT_TYPES = {
    "COLLABORATION_STATUS_TRANSITIONED",
    "CONTRACT_FROZEN",
    "CONTRACT_INVALIDATED",
    "COLLABORATION_SESSION_CLOSED",
    "COORDINATION_INPUT_REJECTED",
}


class CountingCoordinationController(CoordinationController):
    def __init__(self) -> None:
        self.validation_calls = 0

    def validate(self, session):
        self.validation_calls += 1
        return super().validate(session)


def test_canonical_scenario_set_is_exact_complete_and_consumer_neutral() -> None:
    assert tuple(scenario.scenario_id for scenario in SCENARIOS) == CANONICAL_IDS
    assert tuple(SCENARIO_BY_ID) == CANONICAL_IDS
    serialized = repr(SCENARIOS).casefold()
    assert all(identifier not in serialized for identifier in PROHIBITED_CONSUMER_IDENTIFIERS)


def test_scn_01_security_delta_invalidates_review_and_evidence_then_blocks_runtime() -> None:
    scenario = SCENARIO_BY_ID["SCN-01"]
    dependency_id = "dep.scn01-security-review"
    review_ref = scenario.required_review_refs[0]
    artifact_id = scenario.generated_artifact_refs[0]
    generated_evidence_ref, validation_evidence_ref = scenario.evidence_refs

    base = build_session()
    dependency = CollaborationDependency(
        dependency_id,
        "clockwork",
        "overseer",
        DependencyKind.INVALIDATES,
        blocking=False,
        invalidation_rules=(
            InvalidationRule(
                InvalidationTargetKind.REVIEW,
                (review_ref,),
                ("clockwork", "overseer"),
                ("clockwork", "overseer"),
            ),
            InvalidationRule(
                InvalidationTargetKind.EVIDENCE,
                (generated_evidence_ref, validation_evidence_ref),
                ("clockwork", "overseer"),
                ("clockwork", "overseer"),
            ),
        ),
    )
    graph = replace(
        base.graph,
        dependencies=base.graph.dependencies + (dependency,),
    )
    contract = replace(
        build_contract(
            artifact_refs=(artifact_id,),
            owner_refs=("clockwork", "overseer", "ponytail"),
        ),
        invalidation_dependency_refs=tuple(
            sorted(base.contract.invalidation_dependency_refs + (dependency_id,))
        ),
        declared_reference_refs=tuple(
            sorted(base.contract.declared_reference_refs + (review_ref,))
        ),
    )
    ready_contract = contract.with_status(ContractReadiness.READY_FOR_FREEZE)
    generated_artifact = build_artifact(
        artifact_id=artifact_id,
        retention=ArtifactRetentionRequirement.RETAIN_REQUIRED,
        current_state=ArtifactLifecycleState.GENERATED,
        evidence_ref=generated_evidence_ref,
    )
    generated_evidence = CoordinationEvidenceRecord(
        generated_evidence_ref,
        base.session_id,
        "overseer",
        ready_contract.fingerprint,
        base.current_revision,
        BASELINE_SHA,
        contract.change_identity_ref,
    )
    validation_evidence = CoordinationEvidenceRecord(
        validation_evidence_ref,
        base.session_id,
        "overseer",
        ready_contract.fingerprint,
        base.current_revision,
        BASELINE_SHA,
        contract.change_identity_ref,
    )
    collecting = replace(
        base,
        graph=graph,
        contract=contract,
        artifact_lifecycle_records=(generated_artifact,),
        evidence_records=(generated_evidence, validation_evidence),
    )
    ready = CoordinationController().apply(
        collecting,
        signal(
            "signal.scn01-ready",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
            evidence_refs=(generated_evidence_ref, validation_evidence_ref),
        ),
    )

    invalidations = (
        InvalidationEvent(
            "invalidation.scn01-initialization-review",
            ready.session_id,
            ready.current_revision,
            dependency_id,
            InvalidationTargetKind.REVIEW,
            (review_ref,),
            ("clockwork", "overseer"),
            ("clockwork", "overseer"),
            opened_reason_code="SECURITY_DELTA_INVALIDATED_INITIALIZATION_REVIEW",
        ),
        InvalidationEvent(
            "invalidation.scn01-generated-and-validation-evidence",
            ready.session_id,
            ready.current_revision,
            dependency_id,
            InvalidationTargetKind.EVIDENCE,
            (generated_evidence_ref, validation_evidence_ref),
            ("clockwork", "overseer"),
            ("clockwork", "overseer"),
            opened_reason_code="SECURITY_DELTA_INVALIDATED_EVIDENCE",
        ),
    )
    stale = CoordinationController().apply(
        replace(ready, invalidation_events=invalidations),
        signal(
            "signal.scn01-stale",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="overseer",
        ),
    )

    exact_reentry = tuple(
        sorted(
            {
                specialist
                for event in stale.open_invalidations
                for specialist in event.required_reentry_refs
            }
        )
    )
    review_events = tuple(
        event
        for event in stale.open_invalidations
        if event.target_kind is InvalidationTargetKind.REVIEW
    )
    evidence_events = tuple(
        event
        for event in stale.open_invalidations
        if event.target_kind is InvalidationTargetKind.EVIDENCE
    )

    assert ready.accepted_signals[-1].signal_id == "signal.scn01-ready"
    assert generated_artifact.current_state is ArtifactLifecycleState.GENERATED
    assert generated_artifact.evidence_ref == generated_evidence_ref
    assert review_events[0].target_refs == (review_ref,)
    assert set(evidence_events[0].target_refs) == {
        generated_evidence_ref,
        validation_evidence_ref,
    }
    assert scenario.required_reentry == ("clockwork", "overseer")
    assert exact_reentry == scenario.required_reentry
    assert stale.status is CollaborationStatus.STALE
    assert "OPEN_INVALIDATION" in CoordinationController().validate(stale).blocker_codes

    environment = build_active_environment(run_id="scn01-stale-preflight")
    with pytest.raises(CoordinationReadinessError) as error:
        environment.executor.execute(
            environment.adapter,
            "conductor",
            coordination_session=stale,
        )

    assert error.value.reason_code == "RUNTIME_COORDINATION_BLOCKED"
    assert environment.adapter.sequence == []
    assert environment.sink.entries == []


@pytest.mark.parametrize("specialist", SCENARIO_BY_ID["SCN-02"].variants)
def test_scn_02_direct_variants_bypass_coordination_and_emit_no_coordination_audit(
    specialist: str,
) -> None:
    controller = CountingCoordinationController()
    environment = build_active_environment(
        run_id=f"scn02-{specialist}",
        command_name=specialist,
        skill_slug=specialist,
        coordination_controller=controller,
    )

    result = environment.executor.execute(
        environment.adapter,
        specialist,
        coordination_session=None,
    )

    assert result.success is True
    assert controller.validation_calls == 0
    assert not any(
        entry.get("event_type") in COORDINATION_EVENT_TYPES
        for entry in environment.sink.entries
    )


def test_scn_03_business_duplicate_is_distinct_from_signal_replay() -> None:
    scenario = SCENARIO_BY_ID["SCN-03"]
    assert scenario.owner_for("service") == "ponytail"
    assert scenario.owner_for("persistence") == "chronicler"
    assert scenario.owner_for("validation") == "overseer"
    assert scenario.idempotency_contract is not None
    scenario.idempotency_contract.validate()

    ledger = BusinessOperationLedger()
    assert ledger.accept("operation.retry-42") == "operation.retry-42"
    with pytest.raises(DuplicateBusinessOperationError):
        ledger.accept("operation.retry-42")

    sink = InMemoryAuditSink()
    service = CoordinationRuntimeService(CoordinationController(), AuditLogger(sink))
    session = with_evidence(
        build_session(),
        CollaborationStatus.READY,
        "evidence.ready",
    )
    mark_ready = signal(
        "signal.scn03-ready",
        CoordinationSignalType.MARK_READY,
        CollaborationStatus.COLLECTING,
        CollaborationStatus.READY,
        evidence_refs=("evidence.ready",),
    )

    updated = service.apply(session, mark_ready)
    replayed = service.apply(updated, mark_ready)

    assert replayed is updated
    assert [entry["event_type"] for entry in sink.entries] == [
        "COLLABORATION_STATUS_TRANSITIONED"
    ]


def test_scn_03_missing_owner_blocks_readiness() -> None:
    scenario = SCENARIO_BY_ID["SCN-03"]
    with pytest.raises(ScenarioContractViolation):
        scenario.ownership.without_layer("persistence").require_layers(
            scenario.affected_layers
        )

    session = build_session(graph=build_graph(include_validation_owner=False))
    with pytest.raises(CoordinationReadinessError) as error:
        CoordinationController().apply(
            session,
            signal(
                "signal.scn03-owner-required",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
            ),
        )

    assert error.value.reason_code == "COORDINATION_NOT_READY"
    assert "MISSING_COORDINATION_OWNER" in dict(error.value.context)["blocker_codes"]


def test_scn_04_dependent_write_failure_enforces_partial_success_and_invalidates_persistence_evidence() -> None:
    scenario = SCENARIO_BY_ID["SCN-04"]
    assert scenario.transaction_boundary is not None
    failure_evidence_ref, persistence_evidence_ref = scenario.evidence_refs

    outcome = scenario.transaction_boundary.execute(
        ("write.primary", "write.dependent"),
        fail_after=1,
        failure_evidence_ref=failure_evidence_ref,
    )

    assert outcome.committed_writes == ()
    assert outcome.rolled_back_writes == ("write.primary",)
    assert outcome.failed_write == "write.dependent"
    assert outcome.partial_success is False
    assert outcome.failure_evidence_ref == failure_evidence_ref

    prohibited_partial = replace(
        scenario.transaction_boundary,
        rollback_required=False,
        partial_success_allowed=False,
    )
    with pytest.raises(ScenarioContractViolation):
        prohibited_partial.execute(
            ("write.primary", "write.dependent"),
            fail_after=1,
            failure_evidence_ref=failure_evidence_ref,
        )

    allowed_partial = replace(
        scenario.transaction_boundary,
        rollback_required=False,
        partial_success_allowed=True,
    )
    partial = allowed_partial.execute(
        ("write.primary", "write.dependent"),
        fail_after=1,
        failure_evidence_ref=failure_evidence_ref,
    )
    assert partial.committed_writes == ("write.primary",)
    assert partial.partial_success is True
    assert partial.failure_evidence_ref == failure_evidence_ref

    ready = ready_session()
    ready = with_evidence(
        ready,
        CollaborationStatus.READY,
        persistence_evidence_ref,
    )
    ready = with_evidence(
        ready,
        CollaborationStatus.READY,
        failure_evidence_ref,
    )
    persistence_invalidation = InvalidationEvent(
        "invalidation.scn04-persistence-evidence",
        ready.session_id,
        ready.current_revision,
        "dep.impl.qa",
        InvalidationTargetKind.EVIDENCE,
        (persistence_evidence_ref,),
        ("overseer", "ponytail"),
        ("overseer",),
        opened_reason_code="DEPENDENT_WRITE_FAILED",
    )
    stale = CoordinationController().apply(
        replace(ready, invalidation_events=(persistence_invalidation,)),
        signal(
            "signal.scn04-stale",
            CoordinationSignalType.INVALIDATE,
            CollaborationStatus.READY,
            CollaborationStatus.STALE,
            source_component="overseer",
        ),
    )

    assert any(
        evidence.evidence_id == outcome.failure_evidence_ref
        for evidence in ready.evidence_records
    )
    assert persistence_invalidation.target_refs == (persistence_evidence_ref,)
    assert persistence_invalidation.opened_reason_code == "DEPENDENT_WRITE_FAILED"
    assert persistence_invalidation.required_reentry_refs == ("overseer",)
    assert stale.status is CollaborationStatus.STALE
    assert "OPEN_INVALIDATION" in CoordinationController().validate(stale).blocker_codes


def test_scn_05_route_plan_and_ui_api_authorization_require_independent_owners() -> None:
    scenario = SCENARIO_BY_ID["SCN-05"]
    assert scenario.route_plan is not None
    assert scenario.authorization_contract is not None

    assert scenario.route_plan.validate(("cipher", "cloak")) == ("cipher", "cloak")
    with pytest.raises(ScenarioContractViolation):
        scenario.route_plan.validate(("cloak",))
    with pytest.raises(ScenarioContractViolation):
        scenario.route_plan.validate(("cipher",))

    scenario.authorization_contract.validate(
        ui_behavior_applied=True,
        api_authorized=True,
    )
    with pytest.raises(ScenarioContractViolation):
        scenario.authorization_contract.validate(
            ui_behavior_applied=True,
            api_authorized=False,
        )
    with pytest.raises(ScenarioContractViolation):
        scenario.authorization_contract.validate(
            ui_behavior_applied=False,
            api_authorized=True,
        )
    with pytest.raises(ScenarioContractViolation):
        scenario.ownership.without_layer("security").require_layers(
            scenario.affected_layers
        )


def test_scn_05_open_authorization_contradiction_blocks_freeze() -> None:
    ready = ready_session()
    contradiction = ContradictionRecord(
        "contradiction.scn05-ui-api",
        ready.session_id,
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("authorization.mismatch",),
        ContradictionStatus.OPEN,
        "the-steward",
        ("review.validation",),
    )
    blocked = replace(ready, contradictions=(contradiction,))
    blocked = with_evidence(
        blocked,
        CollaborationStatus.FROZEN,
        "evidence.freeze",
    )

    with pytest.raises(CoordinationReadinessError) as error:
        CoordinationController().apply(
            blocked,
            signal(
                "signal.scn05-freeze",
                CoordinationSignalType.FREEZE,
                CollaborationStatus.READY,
                CollaborationStatus.FROZEN,
                evidence_refs=("evidence.freeze",),
            ),
        )

    assert error.value.reason_code == "COORDINATION_NOT_READY"
    assert "OPEN_CONTRADICTION" in dict(error.value.context)["blocker_codes"]


def test_scn_06_compatibility_windows_assumptions_and_stale_evidence_block_readiness() -> None:
    scenario = SCENARIO_BY_ID["SCN-06"]
    assert scenario.mixed_version_contract is not None
    contract = scenario.mixed_version_contract

    assert contract.assumptions == (
        "old clients require the version-one response contract",
        "new clients require the version-two response contract",
    )
    assert contract.application_window.label == "application-window"

    contract.validate_versions(
        client_version=1,
        application_version=1,
        schema_version=1,
    )
    contract.validate_versions(
        client_version=2,
        application_version=2,
        schema_version=2,
    )
    with pytest.raises(ScenarioContractViolation):
        contract.validate_versions(
            client_version=2,
            application_version=3,
            schema_version=2,
        )
    with pytest.raises(ScenarioContractViolation):
        contract.validate_versions(
            client_version=1,
            application_version=2,
            schema_version=2,
        )

    collecting = build_session()
    stale_migration = evidence_for(
        collecting,
        CollaborationStatus.READY,
        evidence_id="evidence.migration",
        evidence_status=EvidenceStatus.STALE,
    )
    stale_api = evidence_for(
        collecting,
        CollaborationStatus.READY,
        evidence_id="evidence.api",
        evidence_status=EvidenceStatus.STALE,
    )
    stale_evidence_session = replace(
        collecting,
        evidence_records=(stale_migration, stale_api),
    )

    with pytest.raises(CoordinationReadinessError) as error:
        CoordinationController().apply(
            stale_evidence_session,
            signal(
                "signal.scn06-ready",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                evidence_refs=("evidence.api", "evidence.migration"),
            ),
        )

    assert error.value.reason_code == "COORDINATION_EVIDENCE_REQUIRED"
    assert "STALE_COORDINATION_EVIDENCE" in dict(error.value.context)["blocker_codes"]


def test_scn_06_mixed_version_contradiction_blocks_closeout() -> None:
    frozen = frozen_session()
    contradiction = ContradictionRecord(
        "contradiction.scn06-mixed-version",
        frozen.session_id,
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("compatibility.window",),
        ContradictionStatus.OPEN,
        "the-steward",
        ("review.validation",),
    )
    blocked = replace(frozen, contradictions=(contradiction,))
    blocked = with_evidence(
        blocked,
        CollaborationStatus.CLOSED,
        "evidence.close",
    )

    with pytest.raises(CoordinationReadinessError) as error:
        CoordinationController().apply(
            blocked,
            signal(
                "signal.scn06-close",
                CoordinationSignalType.CLOSE,
                CollaborationStatus.FROZEN,
                CollaborationStatus.CLOSED,
                evidence_refs=("evidence.close",),
            ),
        )

    assert error.value.reason_code == "COORDINATION_CLOSEOUT_BLOCKED"
