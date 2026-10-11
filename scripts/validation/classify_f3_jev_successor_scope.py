#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Recognize only the reviewed exact Issue #937 F3 JEV successor path set."""

from __future__ import annotations

import sys
from collections.abc import Iterable


EXACT_F3_JEV_SUCCESSOR = "EXACT_F3_JEV_SUCCESSOR"
NOT_EXACT_F3_JEV_SUCCESSOR = "NOT_EXACT_F3_JEV_SUCCESSOR"

F3_JEV_SUCCESSOR_PATHS = frozenset(
    {
        "CHANGELOG.md",
        "README.json",
        "docs/architecture/EVIDENCE_GATED_DECISION_HIERARCHY.md",
        "machine/adaptive/evidence-gated-decision-hierarchy.v1.json",
        "machine/schemas/evidence-gated-decision-hierarchy.v1.schema.json",
        "orchestra_runtime/application/ports/__init__.py",
        "orchestra_runtime/application/ports/jev_adjudication.py",
        "orchestra_runtime/application/use_cases/__init__.py",
        "orchestra_runtime/application/use_cases/jev_adjudication.py",
        "orchestra_runtime/domain/adaptive/__init__.py",
        "orchestra_runtime/domain/adaptive/jev_adjudication.py",
        "orchestra_runtime/infrastructure/providers/__init__.py",
        "orchestra_runtime/infrastructure/providers/typesafe_jev.py",
        "scripts/check_stale_references.py",
        "tests/behavior/run_tests.py",
        "tests/behavior/test_stale_reference_scanner.py",
        "tests/runtime/test_evidence_gated_decision_hierarchy.py",
        "tests/runtime/test_jev_adjudication.py",
    }
)


def classify_f3_jev_successor_scope(paths: Iterable[str]) -> str:
    changed_paths = tuple(paths)
    if any(
        not path
        or path != path.strip()
        or "\\" in path
        or path.startswith("/")
        or any(part in {".", ".."} for part in path.split("/"))
        for path in changed_paths
    ):
        return NOT_EXACT_F3_JEV_SUCCESSOR
    if len(changed_paths) != len(set(changed_paths)):
        return NOT_EXACT_F3_JEV_SUCCESSOR
    if frozenset(changed_paths) != F3_JEV_SUCCESSOR_PATHS:
        return NOT_EXACT_F3_JEV_SUCCESSOR
    return EXACT_F3_JEV_SUCCESSOR


def main() -> int:
    result = classify_f3_jev_successor_scope(sys.stdin.read().splitlines())
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
