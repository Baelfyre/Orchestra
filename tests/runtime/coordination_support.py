from __future__ import annotations

from dataclasses import replace

from orchestra_runtime.coordination import (
    ActivationDecision,
    ArtifactLifecycleRecord,
    ArtifactLifecycleState,
    CollaborationDependency,
    CollaborationGraph,
    CollaborationParticipant,
    CollaborationSession,
    CollaborationStatus,
    ContractReadiness,
    ContractSectionRecord,
    DependencyKind,
    SpecialistParticipationRole,
)


BASELINE_SHA = "a" * 40


def build_graph(
    *,
    session_id: str = "session.phase3",
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
        ),
        CollaborationDependency(
            "dep.impl.qa",
            "ponytail",
            "overseer",
            DependencyKind.REQUIRES,
            ("section.impl",),
            ("implementation-changed",),
            True,
        ),
        CollaborationDependency(
            "dep.qa.arbiter",
            "overseer",
            "arbiter",
            DependencyKind.REVIEWS,
            ("section.validation",),
            ("evidence-changed",),
            True,
        ),
    )
    return CollaborationGraph(
        "graph.phase3",
        session_id,
        participants,
        dependencies,
        ("architecture", "implementation", "validation"),
        "ponytail" if include_implementation_owner else None,
        "overseer" if include_validation_owner else None,
        "arbiter" if include_continuity_owner else None,
        None,
        revision,
    )


def build_contract(
    *,
    session_id: str = "session.phase3",
    revision: int = 1,
    status: ContractReadiness = ContractReadiness.COLLECTING,
    open_decisions: tuple[str, ...] = (),
    artifact_refs: tuple[str, ...] = ("artifact.none",),
) -> object:
    sections = (
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
    from orchestra_runtime.coordination import CrossLayerContractPacket

    return CrossLayerContractPacket(
        "contract.phase3",
        session_id,
        revision,
        "Typed cross-specialist coordination runtime",
        ("criterion.arch", "criterion.impl", "criterion.validation"),
        BASELINE_SHA,
        ("architecture", "implementation", "validation"),
        sections,
        (),
        open_decisions,
        ("no persistence", "no rpc", "no external action authority"),
        ("focused runtime tests", "full repository validation"),
        artifact_refs,
        ("dep.arch.impl", "dep.impl.qa"),
        ("clockwork", "ponytail", "overseer"),
        ("arbiter",),
        status,
    )


def build_artifact(
    *,
    session_id: str = "session.phase3",
    revision: int = 1,
) -> ArtifactLifecycleRecord:
    return ArtifactLifecycleRecord(
        "artifact.none",
        session_id,
        "docs/.orchestra-none-required",
        "ponytail",
        "section.impl",
        ArtifactLifecycleState.ABSENT,
        ArtifactLifecycleState.RETAIN,
        "NONE_REQUIRED",
        "arbiter",
        revision,
        "change.phase3",
        "evidence.phase3",
    )


def build_session(
    *,
    status: CollaborationStatus = CollaborationStatus.COLLECTING,
    contract_status: ContractReadiness = ContractReadiness.COLLECTING,
    graph: CollaborationGraph | None = None,
    contract=None,
    invalidations=(),
    contradictions=(),
    handoffs=(),
    artifacts=None,
) -> CollaborationSession:
    graph = graph or build_graph()
    contract = contract or build_contract(status=contract_status)
    artifact_records = (build_artifact(),) if artifacts is None else artifacts
    return CollaborationSession(
        "session.phase3",
        "issue.195",
        "https://github.com/Baelfyre/Orchestra",
        "feat/issue-195-tuner-phase3-typed-runtime",
        BASELINE_SHA,
        "Implementation",
        "MANUAL",
        ActivationDecision.ACTIVATE_MULTI_DOMAIN,
        "The phase crosses architecture, implementation, validation, and continuity.",
        graph,
        contract,
        tuple(handoffs),
        tuple(invalidations),
        tuple(artifact_records),
        tuple(contradictions),
        status,
        1,
    )


def ready_session() -> CollaborationSession:
    return build_session(
        status=CollaborationStatus.READY,
        contract_status=ContractReadiness.READY_FOR_FREEZE,
    )


def with_contract_status(session: CollaborationSession, status: ContractReadiness) -> CollaborationSession:
    return replace(session, contract=replace(session.contract, status=status))
