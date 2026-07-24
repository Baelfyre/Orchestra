from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    ActivationDecision,
    ArtifactLifecycleRecord,
    ArtifactLifecycleState,
    ArtifactRetentionRequirement,
    CollaborationDependency,
    CollaborationParticipant,
    CollaborationSession,
    CollaborationStatus,
    ContractReadiness,
    ContractSectionRecord,
    CoordinationController,
    CoordinationEvidenceRecord,
    DependencyKind,
    ExecutionMode,
    ProgressionMode,
    SpecialistHandoffDelta,
    SpecialistParticipationRole,
)
from orchestra_runtime.errors import InvalidCoordinationContractError

from coordination_support import (
    BASELINE_SHA,
    SHA256_BASELINE,
    build_artifact,
    build_contract,
    build_graph,
    build_session,
)


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


def test_duplicate_semantic_identifiers_fail_closed():
    graph = build_graph()
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, affected_layers=graph.affected_layers + ("architecture",))
    assert exc.value.reason_code == "DUPLICATE_COORDINATION_VALUE"


def test_manual_and_delegated_authority_binding_is_exact():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(manual_authorization_reference=None)
    assert exc.value.reason_code == "INVALID_COORDINATION_AUTHORITY_BINDING"

    delegated = build_session(
        progression_mode=ProgressionMode.DELEGATED,
        manual_authorization_reference=None,
        delegated_envelope_id="envelope.phase3",
    )
    assert delegated.delegated_envelope_id == "envelope.phase3"

    with pytest.raises(InvalidCoordinationContractError):
        build_session(
            progression_mode=ProgressionMode.DELEGATED,
            manual_authorization_reference="approval.phase3",
            delegated_envelope_id="envelope.phase3",
        )


def test_unknown_execution_and_progression_modes_fail_closed():
    with pytest.raises(ValueError):
        build_session(execution_mode="UNKNOWN")
    with pytest.raises(ValueError):
        build_session(progression_mode="UNKNOWN")


def test_repository_identity_strips_credentials_and_supports_sha256_git_ids():
    session = build_session(
        repository_identity="https://user:secret@github.com/Baelfyre/Orchestra?token=secret#fragment"
    )
    assert session.repository_identity == "https://github.com/Baelfyre/Orchestra"
    assert "secret" not in session.to_dict()["repository_identity"]

    sha256_session = build_session(
        baseline_sha=SHA256_BASELINE,
        contract=build_contract(baseline_sha=SHA256_BASELINE),
    )
    assert sha256_session.baseline_sha == SHA256_BASELINE


def test_local_repository_identity_is_non_reversible():
    local_path = "\\".join(("C:", "Users", "Example", "secret-repo"))
    session = build_session(repository_identity=local_path)
    assert session.repository_identity.startswith("local-repository-sha256:")
    assert "Example" not in session.repository_identity



def test_evidence_owner_and_identity_are_strict():
    contract = build_contract(status=ContractReadiness.READY_FOR_FREEZE)
    with pytest.raises(InvalidCoordinationContractError) as exc:
        CoordinationEvidenceRecord(
            "evidence.bad-owner",
            "session.phase3",
            "the-tuner",
            contract.fingerprint,
            1,
            BASELINE_SHA,
            "change.phase3",
        )
    assert exc.value.reason_code == "INVALID_EVIDENCE_OWNER"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        CoordinationEvidenceRecord(
            "evidence.bad-hash",
            "session.phase3",
            "overseer",
            "not-a-hash",
            1,
            BASELINE_SHA,
            "change.phase3",
        )
    assert exc.value.reason_code == "INVALID_COORDINATION_SHA256"

def test_missing_and_duplicate_accountable_owners_fail_closed():
    graph = build_graph()
    participants = tuple(
        replace(item, accountable_layers=())
        if item.specialist_slug == "clockwork"
        else item
        for item in graph.participants
    )
    incomplete = replace(graph, participants=participants)
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(graph=incomplete)
    assert exc.value.reason_code == "CONTRACT_SECTION_OWNER_MISMATCH"

    participants = tuple(
        replace(
            item,
            participation_roles=item.participation_roles
            + (SpecialistParticipationRole.ACCOUNTABLE_OWNER,),
            accountable_layers=("architecture",),
        )
        if item.specialist_slug == "the-tuner"
        else item
        for item in graph.participants
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, participants=participants)
    assert exc.value.reason_code == "DUPLICATE_LAYER_OWNER"


def test_contract_section_owner_must_match_graph_accountability():
    contract = build_contract()
    sections = tuple(
        replace(item, owner_specialist="the-tuner") if item.layer == "architecture" else item
        for item in contract.section_records
    )
    malformed = replace(
        contract,
        section_records=sections,
        owner_refs=("the-tuner", "overseer", "ponytail"),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contract=malformed)
    assert exc.value.reason_code == "CONTRACT_SECTION_OWNER_MISMATCH"


def test_contract_section_revision_dependency_and_acceptance_refs_are_current():
    contract = build_contract()
    stale_sections = tuple(
        replace(item, revision=2) if item.layer == "architecture" else item
        for item in contract.section_records
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contract=replace(contract, section_records=stale_sections))
    assert exc.value.reason_code == "STALE_CONTRACT_SECTION_REVISION"

    unknown_dependency = tuple(
        replace(item, dependency_refs=("dep.unknown",)) if item.layer == "architecture" else item
        for item in contract.section_records
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contract=replace(contract, section_records=unknown_dependency))
    assert exc.value.reason_code == "UNKNOWN_COORDINATION_DEPENDENCY"

    unknown_acceptance = tuple(
        replace(item, acceptance_criteria_refs=("criterion.unknown",))
        if item.layer == "architecture"
        else item
        for item in contract.section_records
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contract=replace(contract, section_records=unknown_acceptance))
    assert exc.value.reason_code == "UNKNOWN_ACCEPTANCE_CRITERION"


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
        ContractSectionRecord("section.bad", "architecture", "clockwork", 1, "not-a-sha")
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
            ArtifactRetentionRequirement.NONE_REQUIRED,
            "arbiter",
            1,
            "change.phase3",
            "evidence.phase3",
        )
    assert exc.value.reason_code == "UNSAFE_COORDINATION_PATH"


def test_artifact_cleanup_authority_and_retention_are_enforced():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_artifact(cleanup_authority_ref="the-tuner")
    assert exc.value.reason_code == "TUNER_AUTHORITY_EXPANSION"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_artifact(
            retention=ArtifactRetentionRequirement.RETAIN_REQUIRED,
            current_state=ArtifactLifecycleState.CLEANED,
        )
    assert exc.value.reason_code == "INVALID_ARTIFACT_RETENTION_STATE"

    unknown = build_artifact(cleanup_authority_ref="unknown-authority")
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(artifacts=(unknown,))
    assert exc.value.reason_code == "INVALID_CLEANUP_AUTHORITY"


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


@pytest.mark.parametrize(
    ("status", "contract_status"),
    (
        (CollaborationStatus.READY, ContractReadiness.READY_FOR_FREEZE),
        (CollaborationStatus.FROZEN, ContractReadiness.FROZEN),
        (CollaborationStatus.CLOSED, ContractReadiness.CLOSED),
    ),
)
def test_direct_non_initial_snapshot_requires_transition_provenance(status, contract_status):
    session = build_session()
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, status=status, contract=replace(session.contract, status=contract_status))
    assert exc.value.reason_code == "MISSING_COORDINATION_TRANSITION_PROVENANCE"
