# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Regression coverage for the human-authorized AQ8 assurance-scope policy."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation.classify_adaptive_assurance_scope import (  # noqa: E402
    APPLICABLE,
    AQ5_IMPLEMENTATION_PATHS,
    AQ6_IMPLEMENTATION_PATHS,
    AQ7_IMPLEMENTATION_PATHS,
    AQ8_IMPLEMENTATION_PATHS,
    AQ8_SCOPE_ANCHOR_PATHS,
    NOT_APPLICABLE,
    PRAI_IMPLEMENTATION_PATHS,
    classify_paths,
)


HISTORICAL_GATES = ("prai", "aq5", "aq7")
AQ8_COMPLETE_PATHS = tuple(
    sorted((*AQ8_IMPLEMENTATION_PATHS, "CHANGELOG.md", "README.json"))
)

AQ8_POLICY_AMENDMENT_PATHS = (
    ".github/workflows/governance-check.yml",
    "CHANGELOG.md",
    "README.json",
    "docs/governance/AQ8_ASSURANCE_SCOPE_POLICY.md",
    "scripts/validation/classify_adaptive_assurance_scope.py",
    "tests/behavior/test_protected_aq8_assurance_scope_policy.py",
)


def _assert_equal(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def test_complete_aq8_scope_is_not_applicable_to_historical_gates() -> None:
    for assurance in HISTORICAL_GATES:
        _assert_equal(
            f"{assurance} complete AQ8 scope",
            classify_paths(AQ8_COMPLETE_PATHS, assurance),
            NOT_APPLICABLE,
        )


def test_partial_aq8_scope_remains_fail_closed_applicable() -> None:
    anchor = "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md"
    _assert_equal("AQ8 anchor registered", anchor in AQ8_SCOPE_ANCHOR_PATHS, True)
    partial = ("CHANGELOG.md", anchor)
    for assurance in HISTORICAL_GATES:
        _assert_equal(
            f"{assurance} partial AQ8 scope",
            classify_paths(partial, assurance),
            APPLICABLE,
        )


def test_mixed_aq8_scope_remains_fail_closed_applicable() -> None:
    mixed = (*AQ8_COMPLETE_PATHS, "unexpected-aq8-scope-path.txt")
    for assurance in HISTORICAL_GATES:
        _assert_equal(
            f"{assurance} mixed AQ8 scope",
            classify_paths(mixed, assurance),
            APPLICABLE,
        )


def test_unknown_unanchored_scope_remains_fail_closed_applicable() -> None:
    unknown = ("CHANGELOG.md", "machine/adaptive/aq8-unrecognized-future-surface.v1.json")
    for assurance in HISTORICAL_GATES:
        _assert_equal(
            f"{assurance} unknown AQ8 scope",
            classify_paths(unknown, assurance),
            APPLICABLE,
        )


def test_duplicate_paths_fail_closed() -> None:
    duplicate = (
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
    )
    for assurance in HISTORICAL_GATES:
        try:
            classify_paths(duplicate, assurance)
        except ValueError:
            continue
        raise AssertionError(f"{assurance} duplicate AQ8 paths did not fail closed")


def test_policy_amendment_uses_preexisting_governance_classification() -> None:
    for assurance in HISTORICAL_GATES:
        _assert_equal(
            f"{assurance} AQ8 policy amendment",
            classify_paths(AQ8_POLICY_AMENDMENT_PATHS, assurance),
            NOT_APPLICABLE,
        )


def test_historical_implementation_inventories_remain_separate() -> None:
    unique_aq8_anchors = AQ8_SCOPE_ANCHOR_PATHS
    for name, historical in (
        ("PRAI", PRAI_IMPLEMENTATION_PATHS),
        ("AQ5", AQ5_IMPLEMENTATION_PATHS),
        ("AQ6", AQ6_IMPLEMENTATION_PATHS),
        ("AQ7", AQ7_IMPLEMENTATION_PATHS),
    ):
        overlap = unique_aq8_anchors.intersection(historical)
        _assert_equal(f"{name} unique AQ8 anchor overlap", overlap, frozenset())


def main() -> None:
    test_complete_aq8_scope_is_not_applicable_to_historical_gates()
    test_partial_aq8_scope_remains_fail_closed_applicable()
    test_mixed_aq8_scope_remains_fail_closed_applicable()
    test_unknown_unanchored_scope_remains_fail_closed_applicable()
    test_duplicate_paths_fail_closed()
    test_policy_amendment_uses_preexisting_governance_classification()
    test_historical_implementation_inventories_remain_separate()
    print("AQ8 assurance scope policy tests passed.")


if __name__ == "__main__":
    main()
