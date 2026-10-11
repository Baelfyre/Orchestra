#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Classify AQ6 PR applicability without reusing historical AQ7 scope rules.

This is a scope classifier, not evidence of successful runtime assurance or
permission to amend a protected rule without independent human governance.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable


NOT_APPLICABLE = "NOT_APPLICABLE"
AQ6_MAINTENANCE = "AQ6_MAINTENANCE"
AQ6_FUNCTIONAL_CHANGE = "AQ6_FUNCTIONAL_CHANGE"
HISTORICAL_AQ6_EXACT = "HISTORICAL_AQ6_EXACT"
INVALID_AQ6_SCOPE = "INVALID_AQ6_SCOPE"

# Preserved historical closeout inventory; not a blanket requirement for
# ordinary feature PRs or later governance maintenance.
HISTORICAL_AQ6_PATHS = frozenset(
    {
        ".github/workflows/aq6-gate-coverage.yml",
        "CHANGELOG.md",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ6.md",
        "machine/adaptive/aq6-gate-coverage.v1.json",
        "machine/schemas/aq6-gate-coverage.v1.schema.json",
        "orchestra_runtime/domain/adaptive/__init__.py",
        "orchestra_runtime/domain/adaptive/gate_coverage.py",
        "README.json",
        "scripts/validation/classify_adaptive_assurance_scope.py",
        "scripts/validation/validate_gate_coverage.py",
        "tests/behavior/test_gate_coverage.py",
        "tests/runtime/test_adaptive_assurance_aq6.py",
    }
)

_METADATA_PATHS = frozenset({"CHANGELOG.md", "README.json"})
_SHARED_FACADE = "orchestra_runtime/domain/adaptive/__init__.py"
_MAINTENANCE_PATHS = frozenset(
    {
        ".github/workflows/aq6-gate-coverage.yml",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ6.md",
        "scripts/validation/classify_aq6_scope.py",
        "tests/behavior/test_gate_coverage.py",
    }
)
_IMPLEMENTATION_PATHS = frozenset(
    {
        "machine/adaptive/aq6-gate-coverage.v1.json",
        "machine/schemas/aq6-gate-coverage.v1.schema.json",
        "orchestra_runtime/domain/adaptive/gate_coverage.py",
        "scripts/validation/validate_gate_coverage.py",
        "tests/runtime/test_adaptive_assurance_aq6.py",
    }
)
_AQ6_OWNED = _MAINTENANCE_PATHS | _IMPLEMENTATION_PATHS
_ALLOWED_AQ6_CHANGE = _AQ6_OWNED | _METADATA_PATHS | {_SHARED_FACADE}


def _normalized_paths(paths: Iterable[str]) -> frozenset[str]:
    values = tuple(paths)
    if not values:
        raise ValueError("empty changed-path inventory")
    if any(
        not isinstance(path, str)
        or not path
        or path != path.strip()
        or "\\" in path
        or path.startswith("/")
        or any(part in {".", "..", ""} for part in path.split("/"))
        for path in values
    ):
        raise ValueError("unsafe or malformed changed path")
    if len(set(values)) != len(values):
        raise ValueError("duplicate changed path")
    return frozenset(values)


def classify_aq6_scope(paths: Iterable[str]) -> str:
    """Fail closed for mixed AQ6-owned changes while allowing shared facade use."""
    changed = _normalized_paths(paths)
    if changed == HISTORICAL_AQ6_PATHS:
        return HISTORICAL_AQ6_EXACT

    owned = changed & _AQ6_OWNED
    if not owned:
        # A shared package facade is not AQ6-owned implementation. AQ6 runtime,
        # behavior and schema checks still execute on a triggered workflow.
        return NOT_APPLICABLE

    if not changed.issubset(_ALLOWED_AQ6_CHANGE):
        return INVALID_AQ6_SCOPE

    if changed & _IMPLEMENTATION_PATHS:
        if "CHANGELOG.md" not in changed:
            return INVALID_AQ6_SCOPE
        if changed & {
            "machine/adaptive/aq6-gate-coverage.v1.json",
            "machine/schemas/aq6-gate-coverage.v1.schema.json",
            "orchestra_runtime/domain/adaptive/gate_coverage.py",
        } and "tests/runtime/test_adaptive_assurance_aq6.py" not in changed:
            return INVALID_AQ6_SCOPE
        if "scripts/validation/validate_gate_coverage.py" in changed and (
            "tests/behavior/test_gate_coverage.py" not in changed
        ):
            return INVALID_AQ6_SCOPE
        return AQ6_FUNCTIONAL_CHANGE

    if changed & {
        ".github/workflows/aq6-gate-coverage.yml",
        "scripts/validation/classify_aq6_scope.py",
    } and not {
        "CHANGELOG.md",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ6.md",
        "tests/behavior/test_gate_coverage.py",
    }.issubset(changed):
        return INVALID_AQ6_SCOPE

    return AQ6_MAINTENANCE


def main() -> int:
    try:
        result = classify_aq6_scope(sys.stdin.read().splitlines())
    except ValueError as exc:
        print(f"AQ6_SCOPE=INVALID: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0 if result != INVALID_AQ6_SCOPE else 1


if __name__ == "__main__":
    raise SystemExit(main())
