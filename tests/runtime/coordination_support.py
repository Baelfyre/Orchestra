from __future__ import annotations

from dataclasses import replace

from orchestra_runtime.coordination import (
    ActivationDecision,
    ArtifactLifecycleRecord,
    ArtifactLifecycleState,
    ArtifactRetentionRequirement,
    CollaborationDependency,
    CollaborationGraph,
    CollaborationParticipant,
    CollaborationSession,
    CollaborationStatus,
    ContractReadiness,
    ContractSectionRecord,
    CoordinationController,
    CoordinationEvidenceRecord,
    CoordinationSignal,
    CoordinationSignalType,
    CrossLayerContractPacket,
    DependencyKind,
    EvidenceStatus,
    ExecutionMode,
    InvalidationRule,
    InvalidationTargetKind,
    ProgressionMode,
    SpecialistParticipationRole,
)


BASELINE_SHA = "a" * 40
SHA256_BASELINE = "b" * 64
CHANGE_ID = "change.phase3"
SESSION_ID = "session.phase3"


def build_graph(
    *,
    session_id: str = SESSION_ID,
    revision: int = 1,
    include_implementation_owner: bool = True,
    include_validation_owner: bool = True,
    include_continuity_owner: bool = True,
) -> CollaborationGraph:
    participants = (
        CollaborationParticipant(
            "clockwork",
            (
                SpecialistParticipationRole.ACCOUNTABLE_OWNER,
                SpecialistParticipationRole.COLLABORATOR,
            ),
            ("architecture",),
            ("implementation",),
        ),
        CollaborationParticipant(
            "ponytail",
            (
                SpecialistParticipationRole.ACCOUNTABLE_OWNER,
                SpecialistParticipationRole.IMPLEMENTATION_OWNER,
            ),
            ("implementation",),
            ("architecture",),
        ),
        CollaborationParticipant(
            "overseer",
            (
                SpecialistParticipationRole.ACCOUNTABLE_OWNER,
                SpecialistParticipationRole.VALIDATION_OWNER,
            ),
            ("validation",),
            (),
        ),
        CollaborationParticipant(
            "arbiter",
            (SpecialistParticipationRole.CONTINUITY_OWNER,),
            (),
            ("validation",),
        ),
        CollaborationParticipant(
            "the-tuner",
            (SpecialistParticipationRole.COLLABORATOR,),
            (),
            ("architecture", "implementation", "validation"),
        ),
    )
    dependencies = (
        CollaborationDependency(
            "dep.arch.impl",
            "clockwork",
            "ponytail",
            DependencyKind.REQUIRES,
            ("section.arch",),
            ("architecture-changed",),
            True,
            (
                InvalidationRule(
                    InvalidationTargetKind.CONTRACT_SECTION,
                    ("section.arch",),
                    ("clockwork", "ponytail"),
                    ("clockwork",),
                ),
            ),
        ),
        CollaborationDependency(
            "dep.impl.qa",
            "ponytail",
            "overseer",
            DependencyKind.REQUIRES,
            ("section.impl",),
            ("implementation-changed",),
            True,
            (
                InvalidationRule(
                    InvalidationTargetKind.CONTRACT_SECTION,
                    ("section.impl",),
                    ("overseer", "ponytail"),
                    ("overseer",),
                ),
                InvalidationRule(
                    InvalidationTargetKind.EVIDENCE,
                    ("evidence.phase3", "evidence.ready", "evidence.freeze", "evidence.close"),
                    ("overseer", "ponytail"),
                    ("overseer",),
                ),
            ),
        ),
        CollaborationDependency(
            "dep.qa.arbiter",
            "overseer",
            "arbiter",
            DependencyKind.REVIEWS,
            ("section.validation",),
            ("evidence-changed",),
            True,
            (
                InvalidationRule(
                    InvalidationTargetKind.REVIEW,
                    ("review.validation",),
                    ("arbiter", "overseer"),
                    ("arbiter",),
                ),
            ),
        ),
    )
    return CollaborationGraph(
        graph_id="graph.phase3",
        session_id=session_id,
        participants=participants,
        dependencies=dependencies,
        affected_layers=("architecture", "implementation", "validation"),
        implementation_owner="ponytail" if include_implementation_owner else None,
        validation_owner="overseer" if include_validation_owner else None,
        continuity_owner="arbiter" if include_continuity_owner else None,
        visual_model_owner=None,
        revision=revision,
    )


def build_contract(
    *,
    session_id: str = SESSION_ID,
    revision: int = 1,
    status: ContractReadiness = ContractReadiness.COLLECTING,
    open_decisions: tuple[str, ...] = (),
    artifact_refs: tuple[str, ...] = ("artifact.none",),
    baseline_sha: str = BASELINE_SHA,
    change_identity_ref: str = CHANGE_ID,
    sections: tuple[ContractSectionRecord, ...] | None = None,
    owner_refs: tuple[str, ...] = ("clockwork", "overseer", "ponytail"),
) -> CrossLayerContractPacket:
    sections = sections or (
        ContractSectionRecord(
            "section.arch",
            "architecture",
            "clockwork",
            revision,
            "1" * 64,
            ("dep.arch.impl",),
            ("criterion.arch",),
            (),
        ),
        ContractSectionRecord(
            "section.impl",
            "implementation",
            "ponytail",
            revision,
            "2" * 64,
            ("dep.impl.qa",),
            ("criterion.impl",),
            (),
        ),
        ContractSectionRecord(
            "section.validation",
            "validation",
            "overseer",
            revision,
            "3" * 64,
            ("dep.qa.arbiter",),
            ("criterion.validation",),
            ("arbiter",),
        ),
    )
    return CrossLayerContractPacket(
        contract_id="contract.phase3",
        session_id=session_id,
        revision=revision,
        objective="Typed cross-specialist coordination runtime",
        acceptance_criteria=("criterion.arch", "criterion.impl", "criterion.validation"),
        baseline_sha=baseline_sha,
        affected_layers=("architecture", "implementation", "validation"),
        section_records=sections,
        assumptions=(),
        open_decisions=open_decisions,
        prohibited_scope=("no persistence", "no rpc", "no external action authority"),
        validation_requirements=("focused runtime tests", "full repository validation"),
        artifact_lifecycle_refs=artifact_refs,
        invalidation_dependency_refs=("dep.arch.impl", "dep.impl.qa"),
        owner_refs=owner_refs,
        reviewer_refs=("arbiter",),
        status=status,
        change_identity_ref=change_identity_ref,
        declared_reference_refs=("review.validation", "diagram.architecture", "documentation.protocol"),
    )


def build_artifact(
    *,
    session_id: str = SESSION_ID,
    revision: int = 1,
    cleanup_authority_ref: str = "arbiter",
    retention: ArtifactRetentionRequirement = ArtifactRetentionRequirement.NONE_REQUIRED,
    current_state: ArtifactLifecycleState = ArtifactLifecycleState.RETAIN,
    change_identity_ref: str = CHANGE_ID,
) -> ArtifactLifecycleRecord:
    return ArtifactLifecycleRecord(
        artifact_id="artifact.none",
        session_id=session_id,
        path="docs/.orchestra-none-required",
        producer_ref="ponytail",
        source_ref="section.impl",
        pre_execution_state=ArtifactLifecycleState.ABSENT,
        current_state=current_state,
        retention_requirement=retention,
        cleanup_authority_ref=cleanup_authority_ref,
        contract_revision=revision,
        change_identity_ref=change_identity_ref,
        evidence_ref="evidence.phase3",
    )


def build_session(
    *,
    graph: CollaborationGraph | None = None,
    contract: CrossLayerContractPacket | None = None,
    invalidations=(),
    contradictions=(),
    handoffs=(),
    artifacts=None,
    evidence_records=(),
    repository_identity: str = "https://github.com/Baelfyre/Orchestra",
    baseline_sha: str = BASELINE_SHA,
    execution_mode: ExecutionMode = ExecutionMode.IMPLEMENTATION,
    progression_mode: ProgressionMode = ProgressionMode.MANUAL,
    manual_authorization_reference: str | None = "approval.phase3",
    delegated_envelope_id: str | None = None,
) -> CollaborationSession:
    graph = graph or build_graph()
    contract = contract or build_contract(baseline_sha=baseline_sha)
    artifact_records = (build_artifact(),) if artifacts is None else tuple(artifacts)
    return CollaborationSession(
        session_id=SESSION_ID,
        task_id="issue.195",
        repository_identity=repository_identity,
        branch="feat/issue-195-tuner-phase3-typed-runtime-foundation",
        baseline_sha=baseline_sha,
        execution_mode=execution_mode,
        progression_mode=progression_mode,
        activation_decision=ActivationDecision.ACTIVATE_MULTI_DOMAIN,
        activation_reason="The phase crosses architecture, implementation, validation, and continuity.",
        graph=graph,
        contract=contract,
        handoff_deltas=tuple(handoffs),
        invalidation_events=tuple(invalidations),
        artifact_lifecycle_records=artifact_records,
        contradictions=tuple(contradictions),
        status=CollaborationStatus.COLLECTING,
        current_revision=1,
        manual_authorization_reference=manual_authorization_reference,
        delegated_envelope_id=delegated_envelope_id,
        evidence_records=tuple(evidence_records),
    )


def target_contract(session: CollaborationSession, status: CollaborationStatus) -> CrossLayerContractPacket:
    readiness = {
        CollaborationStatus.COLLECTING: ContractReadiness.COLLECTING,
        CollaborationStatus.INCOMPLETE: ContractReadiness.INCOMPLETE,
        CollaborationStatus.CONTRADICTED: ContractReadiness.CONTRADICTED,
        CollaborationStatus.READY: ContractReadiness.READY_FOR_FREEZE,
        CollaborationStatus.FROZEN: ContractReadiness.FROZEN,
        CollaborationStatus.STALE: ContractReadiness.STALE,
        CollaborationStatus.SUPERSEDED: ContractReadiness.SUPERSEDED,
        CollaborationStatus.CLOSED: ContractReadiness.CLOSED,
    }[status]
    return session.contract.with_status(readiness)


def evidence_for(
    session: CollaborationSession,
    status: CollaborationStatus,
    *,
    evidence_id: str,
    owner: str = "overseer",
    evidence_status: EvidenceStatus = EvidenceStatus.CURRENT,
    revision: int | None = None,
    baseline_sha: str | None = None,
    change_identity_ref: str | None = None,
) -> CoordinationEvidenceRecord:
    contract = target_contract(session, status)
    return CoordinationEvidenceRecord(
        evidence_id=evidence_id,
        session_id=session.session_id,
        owner_ref=owner,
        contract_fingerprint=contract.fingerprint,
        contract_revision=revision or session.current_revision,
        baseline_sha=baseline_sha or session.baseline_sha,
        change_identity_ref=change_identity_ref or contract.change_identity_ref,
        status=evidence_status,
    )


def with_evidence(
    session: CollaborationSession,
    status: CollaborationStatus,
    evidence_id: str,
    **kwargs,
) -> CollaborationSession:
    record = evidence_for(session, status, evidence_id=evidence_id, **kwargs)
    return replace(session, evidence_records=session.evidence_records + (record,))


def signal(
    signal_id: str,
    signal_type: CoordinationSignalType,
    expected: CollaborationStatus,
    requested: CollaborationStatus,
    *,
    source_component: str = "arbiter",
    reason: str = "phase3-transition",
    revision: int = 1,
    evidence_refs: tuple[str, ...] = (),
) -> CoordinationSignal:
    return CoordinationSignal(
        signal_id=signal_id,
        session_id=SESSION_ID,
        signal_type=signal_type,
        expected_status=expected,
        requested_status=requested,
        reason_code=reason,
        source_component=source_component,
        source_revision=revision,
        evidence_refs=evidence_refs,
    )


def ready_session() -> CollaborationSession:
    controller = CoordinationController()
    collecting = build_session()
    collecting = with_evidence(collecting, CollaborationStatus.READY, "evidence.ready")
    return controller.apply(
        collecting,
        signal(
            "signal.ready",
            CoordinationSignalType.MARK_READY,
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
            evidence_refs=("evidence.ready",),
        ),
    )


def frozen_session() -> CollaborationSession:
    controller = CoordinationController()
    ready = ready_session()
    ready = with_evidence(ready, CollaborationStatus.FROZEN, "evidence.freeze")
    return controller.apply(
        ready,
        signal(
            "signal.freeze",
            CoordinationSignalType.FREEZE,
            CollaborationStatus.READY,
            CollaborationStatus.FROZEN,
            evidence_refs=("evidence.freeze",),
        ),
    )
