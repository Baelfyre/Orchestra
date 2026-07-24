from dataclasses import replace
import ast
import json
from pathlib import Path

import pytest

from orchestra_runtime.coordination import (
    CollaborationDependency,
    CollaborationStatus,
    ContradictionRecord,
    ContradictionStatus,
    CoordinationController,
    CoordinationSignal,
    CoordinationSignalType,
    DependencyKind,
    InvalidationEvent,
    InvalidationTargetKind,
)
from orchestra_runtime.errors import InvalidCoordinationContractError, CoordinationReadinessError

from coordination_support import build_graph, build_session


def test_invalidation_cannot_invent_undeclared_dependency():
    event = InvalidationEvent(
        "invalidation.undeclared",
        "session.phase3",
        1,
        "dep.not-declared",
        InvalidationTargetKind.CONTRACT_SECTION,
        ("section.impl",),
        ("clockwork", "ponytail"),
        ("clockwork",),
    )

    with pytest.raises(InvalidCoordinationContractError) as exc:
        build_session(invalidations=(event,))

    assert exc.value.reason_code == "UNDECLARED_INVALIDATION_DEPENDENCY"


def test_required_reentry_must_be_minimal_subset_of_affected_specialists():
    with pytest.raises(InvalidCoordinationContractError) as exc:
        InvalidationEvent(
            "invalidation.expanded",
            "session.phase3",
            1,
            "dep.impl.qa",
            InvalidationTargetKind.EVIDENCE,
            ("evidence.phase3",),
            ("ponytail", "overseer"),
            ("clockwork",),
        )

    assert exc.value.reason_code == "INVALID_REENTRY_SET"


def test_open_contradiction_blocks_readiness_and_tuner_does_not_resolve_it():
    contradiction = ContradictionRecord(
        "contradiction.phase3",
        "session.phase3",
        ("section.arch", "section.impl"),
        ("clockwork", "ponytail"),
        ("impact.runtime",),
        ContradictionStatus.OPEN,
        "the-steward",
        ("review.architecture",),
    )
    session = build_session(contradictions=(contradiction,))
    controller = CoordinationController()

    with pytest.raises(CoordinationReadinessError):
        controller.apply(
            session,
            CoordinationSignal(
                "signal.ready-contradicted",
                "session.phase3",
                CoordinationSignalType.MARK_READY,
                CollaborationStatus.COLLECTING,
                CollaborationStatus.READY,
                "ready",
                "the-tuner",
                1,
                ("evidence.phase3",),
            ),
        )

    assert contradiction.required_resolution_owner_ref == "the-steward"
    assert contradiction.resolution_ref is None


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


def test_coordination_module_has_no_persistence_network_or_git_dependencies():
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "orchestra_runtime" / "coordination.py").read_text(
        encoding="utf-8"
    )

    prohibited_imports = {
        "sqlite3",
        "sqlalchemy",
        "socket",
        "requests",
        "subprocess",
        "urllib",
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
        CoordinationSignal(
            "signal.unknown",
            "session.phase3",
            "UNKNOWN_SIGNAL",
            CollaborationStatus.COLLECTING,
            CollaborationStatus.READY,
            "unknown",
            "conductor",
            1,
        )
