from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    ActivationDecision,
    CollaborationDependency,
    CoordinationEvidenceRecord,
    DependencyKind,
    ProgressionMode,
    SpecialistHandoffDelta,
)
from orchestra_runtime.errors import InvalidCoordinationContractError

from coordination_support import BASELINE_SHA, CHANGE_ID, SESSION_ID, build_contract, build_graph, build_session


def test_session_authority_binding_requires_exactly_one_mode_specific_reference():
    session = build_session()
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, manual_authorization_reference=None)
    assert exc.value.reason_code == "INVALID_COORDINATION_AUTHORITY_BINDING"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, delegated_envelope_id="envelope.one")
    assert exc.value.reason_code == "INVALID_COORDINATION_AUTHORITY_BINDING"

    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(
            session,
            progression_mode=ProgressionMode.DELEGATED,
            manual_authorization_reference=session.manual_authorization_reference,
            delegated_envelope_id=None,
        )
    assert exc.value.reason_code == "INVALID_COORDINATION_AUTHORITY_BINDING"

    delegated = replace(
        session,
        progression_mode=ProgressionMode.DELEGATED,
        manual_authorization_reference=None,
        delegated_envelope_id="envelope.one",
    )
    assert delegated.delegated_envelope_id == "envelope.one"


def test_session_rejects_bypass_activation_graph_contract_identity_and_revision_drift():
    session = build_session()
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, activation_decision=ActivationDecision.BYPASS_SINGLE_OWNER)
    assert exc.value.reason_code == "BYPASS_SESSION_PROHIBITED"

    foreign_graph = replace(session.graph, session_id="session.other")
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, graph=foreign_graph)
    assert exc.value.reason_code == "COORDINATION_SESSION_ID_MISMATCH"

    revision_graph = replace(session.graph, revision=2)
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, graph=revision_graph)
    assert exc.value.reason_code == "COORDINATION_REVISION_MISMATCH"

    other_baseline = replace(session.contract, baseline_sha="b" * 40)
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, contract=other_baseline)
    assert exc.value.reason_code == "COORDINATION_BASELINE_MISMATCH"


def test_session_rejects_duplicate_record_identifiers_and_cross_session_records():
    session = build_session()
    delta = SpecialistHandoffDelta(
        "delta.edge",
        SESSION_ID,
        "clockwork",
        "ponytail",
        1,
        confirmed_decision_refs=("decision.one",),
        change_identity_ref=CHANGE_ID,
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, handoff_deltas=(delta, delta))
    assert exc.value.reason_code == "DUPLICATE_COORDINATION_RECORD"

    foreign_delta = replace(delta, delta_id="delta.foreign", session_id="session.other")
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, handoff_deltas=(foreign_delta,))
    assert exc.value.reason_code == "COORDINATION_SESSION_ID_MISMATCH"


def test_session_rejects_graph_contract_layer_mismatch_after_external_corruption():
    session = build_session()
    graph = build_graph()
    object.__setattr__(graph, "affected_layers", (graph.affected_layers[0],))
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(session, graph=graph)
    assert exc.value.reason_code == "COORDINATION_LAYER_MISMATCH"


def test_evidence_record_owner_is_overseer_only_and_roundtrips_projection():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        CoordinationEvidenceRecord(
            "evidence.bad-owner",
            SESSION_ID,
            "clockwork",
            build_contract().fingerprint,
            1,
            BASELINE_SHA,
            CHANGE_ID,
        )
    assert exc.value.reason_code == "INVALID_EVIDENCE_OWNER"

    record = CoordinationEvidenceRecord(
        "evidence.edge",
        SESSION_ID,
        "overseer",
        build_contract().fingerprint,
        1,
        BASELINE_SHA,
        CHANGE_ID,
    )
    assert record.to_dict()["owner_ref"] == "overseer"


def test_graph_rejects_unknown_dependency_participant_and_blocking_cycle():
    graph = build_graph()
    unknown = CollaborationDependency(
        "dep.unknown",
        "clockwork",
        "missing-specialist",
        DependencyKind.REQUIRES,
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, dependencies=graph.dependencies + (unknown,))
    assert exc.value.reason_code == "UNKNOWN_COORDINATION_PARTICIPANT"

    reverse = CollaborationDependency(
        "dep.reverse",
        "ponytail",
        "clockwork",
        DependencyKind.REQUIRES,
        blocking=True,
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, dependencies=graph.dependencies + (reverse,))
    assert exc.value.reason_code == "COORDINATION_DEPENDENCY_CYCLE"