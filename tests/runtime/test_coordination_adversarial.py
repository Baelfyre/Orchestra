from dataclasses import replace
import ast
import json
from pathlib import Path

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
    EvidenceStatus,
    CoordinationSignalType,
    DependencyKind,
    InvalidationEvent,
    InvalidationStatus,
    InvalidationTargetKind,
    coordination_rejection_event,
)
from orchestra_runtime.errors import InvalidCoordinationContractError, CoordinationReadinessError

from coordination_support import (
    build_artifact,
    build_contract,
    build_graph,
    build_session,
    BASELINE_SHA,
    ready_session,
    signal,
)


def test_invalidation_cannot_invent_undeclared_dependency():
    event = InvalidationEvent(
        "invalidation.undeclared",
        "session.phase3",
        1,
        "dep.not-declared",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(event,))
    assert exc.value.reason_code == "UNDECLARED_INVALIDATION_DEPENDENCY"


def test_declared_dependency_cannot_invalidate_unrelated_specialists_or_targets():
    unrelated = InvalidationEvent(
        "invalidation.expanded",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("clockwork", "ponytail"),
        ("clockwork",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(unrelated,))
    assert exc.value.reason_code == "INVALID_INVALIDATION_PROPAGATION"

    nonexistent = InvalidationEvent(
        "invalidation.nonexistent",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.not-real",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(nonexistent,))
    assert exc.value.reason_code in {"INVALID_INVALIDATION_PROPAGATION", "UNKNOWN_INVALIDATION_TARGET"}


def test_required_reentry_must_match_dependency_rule_exactly():
    event = InvalidationEvent(
        "invalidation.overbroad",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("overseer", "ponytail"),
        ("overseer", "ponytail"),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(event,))
    assert exc.value.reason_code == "INVALID_INVALIDATION_PROPAGATION"


def test_open_contradiction_blocks_readiness_and_tuner_cannot_resolve_it():
    contradiction = ContradictionRecord(
        "contradiction.phase3",
        "session.phase3",
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("impact.runtime",),
        ContradictionStatus.OPEN,
        "the-steward",
        ("review.validation",),
    )
    session = build_session(contradictions=(contradiction,))
    with pytest.raises(CoordinationReadinessError):
        CoordinationController().apply(
            session,
            signal(
                "signal.ready-contradicted",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                evidence_refs=(),
            ),
        )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        ContradictionRecord(
            "contradiction.tuner",
            "session.phase3",
            ("section.arch", "section.impl"),
            ("clockwork", "ponytail"),
            ("impact.runtime",),
            ContradictionStatus.OPEN,
            "the-tuner",
        )
    assert exc.value.reason_code == "TUNER_AUTHORITY_EXPANSION"



def test_unknown_contradiction_authority_is_rejected_by_session():
    contradiction = ContradictionRecord(
        "contradiction.unknown-owner",
        "session.phase3",
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("impact.runtime",),
        ContradictionStatus.OPEN,
        "unknown-authority",
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contradictions=(contradiction,))
    assert exc.value.reason_code == "INVALID_CONTRADICTION_AUTHORITY"

def test_review_edges_may_cycle_but_blocking_dependency_edges_may_not():
    graph = build_graph()
    review_cycle = graph.dependencies + (
        CollaborationDependency(
            "dep.arbiter.overseer-review",
            "arbiter",
            "overseer",
            DependencyKind.REVIEWS,
        ),
    )
    reviewed = replace(graph, dependencies=review_cycle)
    assert reviewed.fingerprint

    blocking_cycle = review_cycle + (
        CollaborationDependency(
            "dep.overseer.clockwork",
            "overseer",
            "clockwork",
            DependencyKind.REQUIRES,
        ),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        replace(graph, dependencies=blocking_cycle)
    assert exc.value.reason_code == "COORDINATION_DEPENDENCY_CYCLE"


def test_public_manifest_does_not_expose_direct_tuner_command():
    repo_root = Path(__file__).resolve().parents[2]
    manifest = json.loads((repo_root / "plugin.json").read_text(encoding="utf-8"))
    assert "the-tuner" not in manifest["commands"]
    tuner = next(item for item in manifest["skills"] if item["slug"] == "the-tuner")
    assert tuner["depends_on"] == "conductor"


def test_coordination_module_has_no_persistence_network_or_git_execution_dependencies():
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "orchestra_runtime" / "coordination.py").read_text(encoding="utf-8")
    prohibited_imports = {
        "sqlite3",
        "sqlalchemy",
        "socket",
        "requests",
        "subprocess",
        "dulwich",
        "git",
    }
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(prohibited_imports)


def test_unknown_enum_values_fail_closed():
    with pytest.raises(ValueError):
        signal(
            "signal.unknown",
            "UNKNOWN_SIGNAL",
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
        )


def test_rejection_event_fallback_identity_is_deterministic_without_repr_address():
    session = build_session()
    error = InvalidCoordinationContractError("bad", "BAD_SIGNAL")

    class OpaqueSignal:
        pass

    first = coordination_rejection_event(session, OpaqueSignal(), error)
    second = coordination_rejection_event(session, OpaqueSignal(), error)
    assert first.event_id == second.event_id
    assert "0x" not in dict(first.details)["signal_fingerprint"]


def test_artifact_cleanup_state_requires_explicit_authority():
    cleaned = build_artifact(
        retention=ArtifactRetentionRequirement.CLEANUP_ALLOWED,
        current_state=ArtifactLifecycleState.CLEANED,
        evidence_ref="evidence.artifact",
    )
    assert cleaned.current_state is ArtifactLifecycleState.CLEANED

    with pytest.raises(InvalidCoordinationContractError):
        build_artifact(
            retention=ArtifactRetentionRequirement.NONE_REQUIRED,
            current_state=ArtifactLifecycleState.CLEANED,
        )


def test_open_invalidation_revision_must_equal_current_session_revision():
    event = InvalidationEvent(
        "invalidation.future",
        "session.phase3",
        999,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(event,))
    assert exc.value.reason_code == "INVALID_INVALIDATION_REVISION"


def test_resolved_invalidation_requires_current_revision_and_real_refresh_evidence():
    graph = build_graph(revision=2)
    contract = build_contract(revision=2)
    event = InvalidationEvent(
        "invalidation.resolved",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("overseer", "ponytail"),
        ("overseer",),
        InvalidationStatus.RESOLVED,
        resolved_by_revision=2,
        evidence_refresh_refs=("evidence.refresh",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(
            graph=graph,
            contract=contract,
            current_revision=2,
            invalidations=(event,),
        )
    assert exc.value.reason_code == "UNKNOWN_COORDINATION_EVIDENCE"

    evidence = CoordinationEvidenceRecord(
        "evidence.refresh",
        "session.phase3",
        "overseer",
        contract.fingerprint,
        2,
        BASELINE_SHA,
        "change.phase3",
    )
    resolved = build_session(
        graph=graph,
        contract=contract,
        current_revision=2,
        invalidations=(event,),
        evidence_records=(evidence,),
    )
    assert resolved.open_invalidations == ()


def test_resolved_invalidation_rejects_stale_refresh_evidence():
    graph = build_graph(revision=2)
    contract = build_contract(revision=2)
    evidence = CoordinationEvidenceRecord(
        "evidence.refresh-stale",
        "session.phase3",
        "overseer",
        contract.fingerprint,
        2,
        BASELINE_SHA,
        "change.phase3",
        EvidenceStatus.STALE,
    )
    event = InvalidationEvent(
        "invalidation.resolved-stale",
        "session.phase3",
        1,
        "dep.impl.qa",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("overseer", "ponytail"),
        ("overseer",),
        InvalidationStatus.RESOLVED,
        resolved_by_revision=2,
        evidence_refresh_refs=("evidence.refresh-stale",),
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(
            graph=graph,
            contract=contract,
            current_revision=2,
            invalidations=(event,),
            evidence_records=(evidence,),
        )
    assert exc.value.reason_code == "INVALID_INVALIDATION_REFRESH_EVIDENCE"


def test_artifact_source_and_evidence_references_must_resolve():
    unknown_source = build_artifact(source_ref="section.not-real")
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(artifacts=(unknown_source,))
    assert exc.value.reason_code == "UNKNOWN_ARTIFACT_SOURCE"

    dangling = build_artifact(
        retention=ArtifactRetentionRequirement.RETAIN_REQUIRED,
        current_state=ArtifactLifecycleState.RETAIN,
        evidence_ref="evidence.missing",
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(artifacts=(dangling,))
    assert exc.value.reason_code == "UNKNOWN_ARTIFACT_EVIDENCE"


def test_artifact_evidence_must_be_current_and_contract_bound():
    contract = build_contract()
    artifact = build_artifact(
        retention=ArtifactRetentionRequirement.RETAIN_REQUIRED,
        current_state=ArtifactLifecycleState.RETAIN,
        evidence_ref="evidence.artifact",
    )
    stale = CoordinationEvidenceRecord(
        "evidence.artifact",
        "session.phase3",
        "overseer",
        contract.fingerprint,
        1,
        BASELINE_SHA,
        "change.phase3",
        EvidenceStatus.STALE,
    )
    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(contract=contract, artifacts=(artifact,), evidence_records=(stale,))
    assert exc.value.reason_code == "INVALID_ARTIFACT_EVIDENCE"

    current = replace(stale, status=EvidenceStatus.CURRENT)
    session = build_session(contract=contract, artifacts=(artifact,), evidence_records=(current,))
    assert session.artifact_lifecycle_records[0].evidence_ref == "evidence.artifact"


def test_internal_receipt_type_is_not_exported_as_public_package_api():
    repo_root = Path(__file__).resolve().parents[2]
    public_init = (repo_root / "orchestra_runtime" / "__init__.py").read_text(encoding="utf-8")
    assert '    AcceptedCoordinationSignal,\n' not in public_init
    assert '    "AcceptedCoordinationSignal",\n' not in public_init
