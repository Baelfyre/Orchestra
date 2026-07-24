from dataclasses import replace

import pytest

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
    CoordinationController,
    DependencyKind,
    SpecialistHandoffDelta,
    SpecialistParticipationRole,
)
from orchestra_runtime.errors import InvalidCoordinationContractError

from coordination_support import BASELINE_SHA, build_contract, build_graph, build_session


def test_graph_and_contract_fingerprints_are_order_stable():
    first = build_graph()
    second = replace(
        first,
        participants=tuple(reversed(first.participants)),
        dependencies=tuple(reversed(first.dependencies)),
        affected_layers=tuple(reversed(first.affected_layers)),
    )
    assert first.fingerprint == second.fingerprint
    assert first.to_dict() == second.to_dict()

    contract = build_contract()
    reordered = replace(
        contract,
        section_records=tuple(reversed(contract.section_records)),
        prohibited_scope=tuple(reversed(contract.prohibited_scope)),
        owner_refs=tuple(reversed(contract.owner_refs)),
    )
    assert contract.fingerprint == reordered.fingerprint


def test_missing_accountable_owner_blocks_readiness():
    graph = build_graph()
    participants = tuple(
        replace(item, accountable_layers=())
        if item.specialist_slug == "clockwork"
        else item
        for item in graph.participants
    )
    incomplete = replace(graph, participants=participants)
    session = build_session(graph=incomplete)

    result = CoordinationController().validate(replace(
        session,
        status=CollaborationStatus.READY,
        contract=replace(session.contract, status=ContractReadiness.READY_FOR_FREEZE),
    ))

    assert result.allowed is False
    assert "MISSING_ACCOUNTABLE_OWNER" in result.blocker_codes


def test_duplicate_accountable_owner_is_rejected():
    graph = build_graph()
    participants = tuple(
        replace(
            item,
            participation_roles=tuple(
                sorted(
                    set(item.participation_roles)
                    | {SpecialistParticipationRole.ACCOUNTABLE_OWNER},
                    key=lambda value: value.value,
                )
            ),
            accountable_layers=("architecture",),
        )
        if item.specialist_slug == "the-tuner"
        else item
        for item in graph.participants
    )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, participants=participants)

    assert exc.value.reason_code == "DUPLICATE_LAYER_OWNER"


def test_unknown_dependency_participant_and_blocking_cycle_fail_closed():
    graph = build_graph()
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(
            graph,
            dependencies=graph.dependencies
            + (
                CollaborationDependency(
                    "dep.unknown",
                    "ponytail",
                    "missing-specialist",
                    DependencyKind.REQUIRES,
                ),
            ),
        )
    assert exc.value.reason_code == "UNKNOWN_COORDINATION_PARTICIPANT"

    cyclic = graph.dependencies + (
        CollaborationDependency(
            "dep.overseer.clockwork",
            "overseer",
            "clockwork",
            DependencyKind.REQUIRES,
        ),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, dependencies=cyclic)
    assert exc.value.reason_code == "COORDINATION_DEPENDENCY_CYCLE"


def test_tuner_cannot_own_implementation_validation_or_continuity():
    graph = build_graph()
    participants = tuple(
        replace(
            item,
            participation_roles=item.participation_roles
            + (SpecialistParticipationRole.IMPLEMENTATION_OWNER,),
        )
        if item.specialist_slug == "the-tuner"
        else item
        for item in graph.participants
    )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, participants=participants, implementation_owner="the-tuner")

    assert exc.value.reason_code == "TUNER_AUTHORITY_EXPANSION"


def test_contract_section_and_artifact_identity_are_strict():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        ContractSectionRecord(
            "section.bad",
            "architecture",
            "clockwork",
            1,
            "not-a-sha",
        )
    assert exc.value.reason_code == "INVALID_SECTION_CONTENT_IDENTITY"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        ArtifactLifecycleRecord(
            "artifact.bad",
            "session.phase3",
            "../outside.txt",
            "ponytail",
            "section.impl",
            ArtifactLifecycleState.ABSENT,
            ArtifactLifecycleState.RETAIN,
            "NONE_REQUIRED",
            "arbiter",
            1,
            "change.phase3",
            "evidence.phase3",
        )
    assert exc.value.reason_code == "UNSAFE_COORDINATION_PATH"


def test_context_free_handoff_is_rejected():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        SpecialistHandoffDelta(
            "delta.empty",
            "session.phase3",
            "clockwork",
            "ponytail",
            1,
            change_identity_ref="change.phase3",
        )

    assert exc.value.reason_code == "CONTEXT_FREE_HANDOFF"


def test_single_owner_bypass_does_not_create_session():
    session = build_session()

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, activation_decision=ActivationDecision.BYPASS_SINGLE_OWNER)

    assert exc.value.reason_code == "BYPASS_SESSION_PROHIBITED"


def test_session_contract_and_graph_must_share_baseline_revision_and_layers():
    session = build_session()

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, baseline_sha="b" * 40)
    assert exc.value.reason_code == "COORDINATION_BASELINE_MISMATCH"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, current_revision=2)
    assert exc.value.reason_code == "COORDINATION_REVISION_MISMATCH"

    contract = replace(
        session.contract,
        affected_layers=("architecture", "implementation"),
        section_records=session.contract.section_records[:2],
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, contract=contract)
    assert exc.value.reason_code == "COORDINATION_LAYER_MISMATCH"
