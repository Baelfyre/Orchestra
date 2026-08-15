from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    ArtifactLifecycleRecord,
    ArtifactLifecycleState,
    ArtifactRetentionRequirement,
    CollaborationStatus,
    ContractReadiness,
    ContradictionRecord,
    ContradictionStatus,
    CoordinationEvidenceRecord,
    CrossLayerContractPacket,
    EvidenceStatus,
    InvalidationEvent,
    InvalidationStatus,
    InvalidationTargetKind,
    SpecialistHandoffDelta,
    _current_status_invariant_blockers,
    _evidence_blockers_for_records,
)
from orchestra_runtime.errors import InvalidCoordinationContractError

from coordination_support import BASELINE_SHA, CHANGE_ID, SESSION_ID, build_contract


SHA256 = "a" * 64


def _artifact(**overrides):
    values = dict(
        artifact_id="artifact.edge",
        session_id=SESSION_ID,
        path="docs/artifact.txt",
        producer_ref="ponytail",
        source_ref="section.impl",
        pre_execution_state=ArtifactLifecycleState.ABSENT,
        current_state=ArtifactLifecycleState.RETAIN,
        retention_requirement=ArtifactRetentionRequirement.NONE_REQUIRED,
        cleanup_authority_ref="arbiter",
        contract_revision=1,
        change_identity_ref=CHANGE_ID,
        evidence_ref=None,
    )
    values.update(overrides)
    return ArtifactLifecycleRecord(**values)


def _contradiction(**overrides):
    values = dict(
        contradiction_id="contradiction.edge",
        session_id=SESSION_ID,
        contract_section_refs=("section.arch", "section.impl"),
        specialist_refs=("clockwork", "ponytail"),
        impact_refs=("impact.architecture",),
        status=ContradictionStatus.OPEN,
        required_resolution_owner_ref="arbiter",
    )
    values.update(overrides)
    return ContradictionRecord(**values)


def _invalidation(**overrides):
    values = dict(
        event_id="invalidation.edge",
        session_id=SESSION_ID,
        source_revision=1,
        trigger_ref="dep.arch.impl",
        target_kind=InvalidationTargetKind.CONTRACT_SECTION,
        target_refs=("section.arch",),
        affected_specialist_refs=("clockwork", "ponytail"),
        required_reentry_refs=("clockwork",),
        status=InvalidationStatus.OPEN,
    )
    values.update(overrides)
    return InvalidationEvent(**values)


def test_contract_packet_layer_section_and_version_guards():
    contract = build_contract()
    with pytest.raises(InvalidCoordinationContractError) as no_layers:
        replace(contract, affected_layers=())
    assert no_layers.value.reason_code == "MISSING_AFFECTED_LAYERS"

    with pytest.raises(InvalidCoordinationContractError) as duplicate_section:
        replace(contract, section_records=contract.section_records + (contract.section_records[0],))
    assert duplicate_section.value.reason_code == "DUPLICATE_CONTRACT_SECTION"

    duplicate_layer_section = replace(
        contract.section_records[1],
        section_id="section.impl-duplicate",
        layer=contract.section_records[0].layer,
    )
    with pytest.raises(InvalidCoordinationContractError) as duplicate_layer:
        replace(contract, section_records=contract.section_records + (duplicate_layer_section,))
    assert duplicate_layer.value.reason_code == "DUPLICATE_CONTRACT_LAYER"

    unknown_layer_section = replace(contract.section_records[0], layer="outside")
    with pytest.raises(InvalidCoordinationContractError) as unknown:
        replace(contract, section_records=(unknown_layer_section,) + contract.section_records[1:])
    assert unknown.value.reason_code == "UNKNOWN_CONTRACT_LAYER"

    with pytest.raises(InvalidCoordinationContractError) as bad_version:
        replace(contract, canonicalization_version="coordination-v999")
    assert bad_version.value.reason_code == "UNSUPPORTED_COORDINATION_VERSION"

    frozen = contract.with_status(ContractReadiness.FROZEN)
    assert frozen.status is ContractReadiness.FROZEN
    assert frozen.to_dict()["fingerprint"] == frozen.fingerprint


def test_handoff_self_context_and_full_serialization_edges():
    with pytest.raises(InvalidCoordinationContractError) as self_handoff:
        SpecialistHandoffDelta(
            "delta.self",
            SESSION_ID,
            "clockwork",
            "clockwork",
            1,
            confirmed_decision_refs=("decision.one",),
            change_identity_ref=CHANGE_ID,
        )
    assert self_handoff.value.reason_code == "SELF_SPECIALIST_HANDOFF"

    with pytest.raises(InvalidCoordinationContractError) as empty:
        SpecialistHandoffDelta(
            "delta.empty",
            SESSION_ID,
            "clockwork",
            "ponytail",
            1,
            change_identity_ref=CHANGE_ID,
        )
    assert empty.value.reason_code == "CONTEXT_FREE_HANDOFF"

    delta = SpecialistHandoffDelta(
        "delta.full",
        SESSION_ID,
        "clockwork",
        "ponytail",
        1,
        confirmed_decision_refs=("decision.one",),
        constraint_refs=("constraint.one",),
        updated_section_refs=("section.arch",),
        assumptions=("assumption one",),
        open_question_refs=("question.one",),
        required_reviewer_refs=("overseer",),
        invalidation_trigger_refs=("dep.arch.impl",),
        evidence_refs=("evidence.one",),
        change_identity_ref=CHANGE_ID,
        artifact_lifecycle_refs=("artifact.one",),
    )
    payload = delta.to_dict()
    assert payload["source_specialist"] == "clockwork"
    assert payload["artifact_lifecycle_refs"] == ["artifact.one"]


def test_invalidation_event_resolution_and_subset_guards():
    with pytest.raises(InvalidCoordinationContractError) as incomplete:
        _invalidation(target_refs=())
    assert incomplete.value.reason_code == "INCOMPLETE_INVALIDATION_EVENT"

    with pytest.raises(InvalidCoordinationContractError) as subset:
        _invalidation(required_reentry_refs=("arbiter",))
    assert subset.value.reason_code == "INVALID_REENTRY_SET"

    with pytest.raises(InvalidCoordinationContractError) as resolved_invalid:
        _invalidation(status=InvalidationStatus.RESOLVED, resolved_by_revision=1, evidence_refresh_refs=())
    assert resolved_invalid.value.reason_code == "INVALID_INVALIDATION_RESOLUTION"

    with pytest.raises(InvalidCoordinationContractError) as open_with_resolution:
        _invalidation(resolved_by_revision=2, evidence_refresh_refs=("evidence.new",))
    assert open_with_resolution.value.reason_code == "INVALID_INVALIDATION_RESOLUTION"

    resolved = _invalidation(
        status=InvalidationStatus.RESOLVED,
        resolved_by_revision=2,
        evidence_refresh_refs=("evidence.new",),
    )
    payload = resolved.to_dict()
    assert payload["resolved_by_revision"] == 2
    assert payload["evidence_refresh_refs"] == ["evidence.new"]


def test_artifact_state_retention_and_evidence_matrix():
    with pytest.raises(InvalidCoordinationContractError) as bad_before:
        _artifact(pre_execution_state=ArtifactLifecycleState.GENERATED)
    assert bad_before.value.reason_code == "INVALID_ARTIFACT_PRE_EXECUTION_STATE"

    with pytest.raises(InvalidCoordinationContractError) as preexisting_generated:
        _artifact(
            pre_execution_state=ArtifactLifecycleState.PREEXISTING,
            current_state=ArtifactLifecycleState.GENERATED,
        )
    assert preexisting_generated.value.reason_code == "INVALID_ARTIFACT_STATE_TRANSITION"

    with pytest.raises(InvalidCoordinationContractError) as none_generated:
        _artifact(current_state=ArtifactLifecycleState.GENERATED)
    assert none_generated.value.reason_code == "INVALID_ARTIFACT_RETENTION_STATE"

    with pytest.raises(InvalidCoordinationContractError) as retained_cleanup:
        _artifact(
            current_state=ArtifactLifecycleState.CLEANED,
            retention_requirement=ArtifactRetentionRequirement.RETAIN_REQUIRED,
            evidence_ref="evidence.artifact",
        )
    assert retained_cleanup.value.reason_code == "INVALID_ARTIFACT_RETENTION_STATE"

    with pytest.raises(InvalidCoordinationContractError) as cleanup_without_policy:
        _artifact(
            current_state=ArtifactLifecycleState.CLEANUP_PENDING,
            retention_requirement=ArtifactRetentionRequirement.RETAIN_ALLOWED,
            evidence_ref="evidence.artifact",
        )
    assert cleanup_without_policy.value.reason_code == "INVALID_ARTIFACT_RETENTION_STATE"

    with pytest.raises(InvalidCoordinationContractError) as required_but_retained:
        _artifact(
            current_state=ArtifactLifecycleState.RETAIN,
            retention_requirement=ArtifactRetentionRequirement.CLEANUP_REQUIRED,
            evidence_ref="evidence.artifact",
        )
    assert required_but_retained.value.reason_code == "INVALID_ARTIFACT_RETENTION_STATE"

    with pytest.raises(InvalidCoordinationContractError) as unexpected_evidence:
        _artifact(evidence_ref="evidence.unexpected")
    assert unexpected_evidence.value.reason_code == "UNEXPECTED_ARTIFACT_EVIDENCE"

    with pytest.raises(InvalidCoordinationContractError) as missing_evidence:
        _artifact(retention_requirement=ArtifactRetentionRequirement.RETAIN_ALLOWED)
    assert missing_evidence.value.reason_code == "MISSING_ARTIFACT_EVIDENCE"

    valid = _artifact(
        current_state=ArtifactLifecycleState.CLEANUP_PENDING,
        retention_requirement=ArtifactRetentionRequirement.CLEANUP_ALLOWED,
        evidence_ref="evidence.artifact",
    )
    assert valid.to_dict()["current_state"] == "CLEANUP_PENDING"


def test_contradiction_completeness_resolution_and_serialization_edges():
    with pytest.raises(InvalidCoordinationContractError) as incomplete:
        _contradiction(contract_section_refs=("section.arch",))
    assert incomplete.value.reason_code == "INCOMPLETE_CONTRADICTION"

    with pytest.raises(InvalidCoordinationContractError) as resolved_missing:
        _contradiction(status=ContradictionStatus.RESOLVED)
    assert resolved_missing.value.reason_code == "INVALID_CONTRADICTION_RESOLUTION"

    with pytest.raises(InvalidCoordinationContractError) as open_resolution:
        _contradiction(resolution_ref="resolution.one")
    assert open_resolution.value.reason_code == "INVALID_CONTRADICTION_RESOLUTION"

    resolved = _contradiction(status=ContradictionStatus.RESOLVED, resolution_ref="resolution.one")
    assert resolved.to_dict()["resolution_ref"] == "resolution.one"


def test_current_status_invariant_blockers_cover_both_required_open_records():
    contradicted = _current_status_invariant_blockers(CollaborationStatus.CONTRADICTED, (), ())
    assert contradicted == (("MISSING_OPEN_CONTRADICTION", "contradicted status requires an open contradiction"),)
    assert _current_status_invariant_blockers(
        CollaborationStatus.CONTRADICTED,
        (),
        (_contradiction(),),
    ) == ()

    stale = _current_status_invariant_blockers(CollaborationStatus.STALE, (), ())
    assert stale == (("MISSING_OPEN_INVALIDATION", "stale status requires an open invalidation"),)
    assert _current_status_invariant_blockers(
        CollaborationStatus.STALE,
        (_invalidation(),),
        (),
    ) == ()


def test_evidence_blockers_exercise_missing_unknown_stale_and_identity_mismatches():
    contract = build_contract()
    assert _evidence_blockers_for_records(
        {}, (), contract, 1, BASELINE_SHA, CHANGE_ID
    ) == (("MISSING_COORDINATION_EVIDENCE", "transition requires current Overseer evidence"),)

    unknown = _evidence_blockers_for_records(
        {}, ("evidence.missing",), contract, 1, BASELINE_SHA, CHANGE_ID
    )
    assert unknown[0][0] == "UNKNOWN_COORDINATION_EVIDENCE"

    evidence = CoordinationEvidenceRecord(
        "evidence.edge",
        SESSION_ID,
        "overseer",
        contract.fingerprint,
        1,
        BASELINE_SHA,
        CHANGE_ID,
    )
    assert _evidence_blockers_for_records(
        {evidence.evidence_id: evidence},
        (evidence.evidence_id,),
        contract,
        1,
        BASELINE_SHA,
        CHANGE_ID,
    ) == ()

    corrupted = replace(evidence, status=EvidenceStatus.STALE)
    object.__setattr__(corrupted, "owner_ref", "clockwork")
    object.__setattr__(corrupted, "contract_fingerprint", SHA256)
    object.__setattr__(corrupted, "contract_revision", 2)
    object.__setattr__(corrupted, "baseline_sha", "b" * 40)
    object.__setattr__(corrupted, "change_identity_ref", "change.other")
    blockers = _evidence_blockers_for_records(
        {corrupted.evidence_id: corrupted},
        (corrupted.evidence_id,),
        contract,
        1,
        BASELINE_SHA,
        CHANGE_ID,
    )
    codes = {code for code, _ in blockers}
    assert codes == {
        "STALE_COORDINATION_EVIDENCE",
        "INVALID_EVIDENCE_OWNER",
        "EVIDENCE_CONTRACT_MISMATCH",
        "EVIDENCE_BASELINE_MISMATCH",
        "EVIDENCE_CHANGE_IDENTITY_MISMATCH",
    }
