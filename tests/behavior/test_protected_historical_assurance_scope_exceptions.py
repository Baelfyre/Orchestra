# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Regression coverage for human-approved historical assurance exact-scope exceptions."""

from __future__ import annotations

from scripts.validation.classify_adaptive_assurance_scope import (
    APPLICABLE,
    NOT_APPLICABLE,
    classify_paths,
    load_registered_exception_scopes,
)

HISTORICAL_GATES = ("prai", "aq5", "aq7")
SCOPE_ID = "ISSUE_937_F1_F2_INTEGRATION"
F3_PATH = "orchestra_runtime/infrastructure/providers/typesafe_jev.py"


def _registered_scope() -> tuple[frozenset[str], frozenset[str]]:
    registry = load_registered_exception_scopes()
    assert tuple(sorted(registry)) == (SCOPE_ID,)
    return registry[SCOPE_ID]


def test_issue_937_f1_f2_exact_scope_is_separated_from_historical_gates() -> None:
    exact_paths, anchors = _registered_scope()
    assert len(exact_paths) == 47
    assert anchors
    assert anchors.issubset(exact_paths)
    for assurance in HISTORICAL_GATES:
        assert classify_paths(sorted(exact_paths), assurance) == NOT_APPLICABLE


def test_issue_937_f1_f2_partial_scope_remains_fail_closed() -> None:
    exact_paths, _ = _registered_scope()
    partial = sorted(exact_paths - {"README.json"})
    for assurance in HISTORICAL_GATES:
        assert classify_paths(partial, assurance) == APPLICABLE


def test_issue_937_f1_f2_superset_remains_fail_closed() -> None:
    exact_paths, _ = _registered_scope()
    superset = [*sorted(exact_paths), "unexpected-issue-937-scope.txt"]
    for assurance in HISTORICAL_GATES:
        assert classify_paths(superset, assurance) == APPLICABLE


def test_issue_937_f1_f2_plus_f3_remains_fail_closed() -> None:
    exact_paths, _ = _registered_scope()
    mixed = [*sorted(exact_paths), F3_PATH]
    for assurance in HISTORICAL_GATES:
        assert classify_paths(mixed, assurance) == APPLICABLE


def test_issue_937_f1_f2_duplicate_path_fails_closed() -> None:
    exact_paths, _ = _registered_scope()
    duplicated = [*sorted(exact_paths), sorted(exact_paths)[0]]
    for assurance in HISTORICAL_GATES:
        try:
            classify_paths(duplicated, assurance)
        except ValueError:
            continue
        raise AssertionError(f"{assurance} duplicate scope path did not fail closed")
