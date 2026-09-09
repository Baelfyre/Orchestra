#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Classify whether a change set requires legacy AQ5 or PRAI exact-scope validation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable


APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"

COMMON_TRIGGER_PATHS = frozenset({"CHANGELOG.md", "README.json"})

WORKFLOW_INTEGRATION_PATHS = frozenset(
    {
        ".github/workflows/prai.yml",
        ".github/workflows/qa-compliance.yml",
    }
)

PRAI_IMPLEMENTATION_PATHS = frozenset(
    {
        *WORKFLOW_INTEGRATION_PATHS,
        "machine/adaptive/prai-post-run-assurance.v1.json",
        "machine/schemas/prai-post-run-assurance.v1.schema.json",
        "orchestra_runtime/domain/adaptive/prai.py",
        "scripts/validation/validate_prai.py",
        "tests/behavior/test_prai.py",
        "tests/runtime/test_prai.py",
    }
)

AQ5_IMPLEMENTATION_PATHS = frozenset(
    {
        *WORKFLOW_INTEGRATION_PATHS,
        "machine/adaptive/aq5-qa-compliance.v1.json",
        "machine/schemas/qa-compliance.v1.schema.json",
        "orchestra_runtime/domain/adaptive/qa_compliance.py",
        "scripts/validation/validate_qa_compliance.py",
        "tests/behavior/test_qa_compliance.py",
        "tests/runtime/test_adaptive_assurance_aq5.py",
    }
)

AQ6_IMPLEMENTATION_PATHS = frozenset(
    {
        ".github/workflows/aq6-gate-coverage.yml",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ6.md",
        "machine/adaptive/aq6-gate-coverage.v1.json",
        "machine/schemas/aq6-gate-coverage.v1.schema.json",
        "orchestra_runtime/domain/adaptive/__init__.py",
        "orchestra_runtime/domain/adaptive/gate_coverage.py",
        "scripts/validation/classify_adaptive_assurance_scope.py",
        "scripts/validation/validate_gate_coverage.py",
        "tests/behavior/test_gate_coverage.py",
        "tests/runtime/test_adaptive_assurance_aq6.py",
    }
)


AQ7_IMPLEMENTATION_PATHS = frozenset(
    {
        ".github/workflows/aq6-gate-coverage.yml",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ7.md",
        "orchestra_runtime/application/dto/tenant_administration.py",
        "orchestra_runtime/application/ports/repositories/__init__.py",
        "orchestra_runtime/application/ports/repositories/tenant_members.py",
        "orchestra_runtime/application/services/tenant_administration.py",
        "orchestra_runtime/domain/governance/tenant_administration.py",
        "orchestra_runtime/entrypoints/__init__.py",
        "orchestra_runtime/entrypoints/api/__init__.py",
        "orchestra_runtime/entrypoints/api/tenant_administration.py",
        "orchestra_runtime/infrastructure/persistence/repositories/__init__.py",
        "orchestra_runtime/infrastructure/persistence/repositories/tenant_members.py",
        "scripts/validation/classify_adaptive_assurance_scope.py",
        "tests/runtime/test_adaptive_assurance_scope.py",
        "tests/runtime/test_aq7_http_adapter_parity.py",
    }
)


COVENANT_IMPLEMENTATION_PATHS = frozenset(
    {
        "AGENTS.md",
        "docs/architecture/ADAPTIVE_ASSURANCE_PRAI.md",
        "docs/governance/README.md",
        "docs/governance/THE_COVENANT.md",
        "docs/validation/COVENANT_CONFLICT_SCENARIO_MATRIX_20260910.md",
        "machine/governance/covenant.v1.json",
        "machine/schemas/covenant.v1.schema.json",
        "orchestra_runtime/domain/governance/__init__.py",
        "orchestra_runtime/domain/governance/covenant.py",
        "skills/the-governor/COVENANT_PROTECTED_OBLIGATION_JUDGMENT_GUIDE.md",
        "skills/the-governor/SKILL.md",
        "skills/the-steward/COVENANT_SYSTEM_INTENT_JUDGMENT_GUIDE.md",
        "skills/the-steward/SKILL.md",
        "tests/runtime/test_covenant_contract.py",
        "tests/runtime/test_covenant_governance_reconciliation.py",
    }
)

COVENANT_SCOPE_ANCHOR_PATHS = frozenset(
    {
        "docs/governance/THE_COVENANT.md",
        "docs/validation/COVENANT_CONFLICT_SCENARIO_MATRIX_20260910.md",
        "machine/governance/covenant.v1.json",
        "machine/schemas/covenant.v1.schema.json",
        "orchestra_runtime/domain/governance/covenant.py",
        "skills/the-governor/COVENANT_PROTECTED_OBLIGATION_JUDGMENT_GUIDE.md",
        "skills/the-steward/COVENANT_SYSTEM_INTENT_JUDGMENT_GUIDE.md",
        "tests/runtime/test_covenant_contract.py",
        "tests/runtime/test_covenant_governance_reconciliation.py",
    }
)

ADAPTIVE_ASSURANCE_REFERENCE_PATHS = frozenset(
    {
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ5.md",
        "docs/architecture/ADAPTIVE_ASSURANCE_PRAI.md",
    }
)

PROTECTED_GOVERNANCE_ANCHORS = frozenset(
    {
        "docs/governance/PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md",
        "machine/governance/protected-governance-escalation.v1.json",
        "machine/schemas/protected-governance-escalation.v1.schema.json",
        "scripts/validate_protected_governance_escalation.py",
        "tests/behavior/test_protected_governance_escalation.py",
    }
)

GOVERNANCE_EXACT_PATHS = frozenset(
    {
        "AGENTS.md",
        ".github/workflows/governance-check.yml",
        ".github/workflows/required-analysis-compat.yml",
        "docs/CONTRIBUTING.md",
        "machine/projections/portable-projection-index.v1.json",
        "machine/schemas/governance-policy.schema.json",
        "scripts/governance_check.py",
        "scripts/test_governance_check.py",
        "scripts/validation/classify_adaptive_assurance_scope.py",
    }
).union(PROTECTED_GOVERNANCE_ANCHORS)

GOVERNANCE_PREFIXES = (
    "docs/governance/",
    "machine/governance/",
    "scripts/validate_governance_",
    "scripts/validate_protected_",
    "tests/behavior/test_governance_",
    "tests/behavior/test_protected_",
)

IMPLEMENTATION_PATHS_BY_GATE = {
    "aq5": AQ5_IMPLEMENTATION_PATHS,
    "aq7": AQ7_IMPLEMENTATION_PATHS,
    "prai": PRAI_IMPLEMENTATION_PATHS,
}


def normalize_paths(paths: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_path in paths:
        path = str(raw_path).strip().replace("\\", "/")
        if not path:
            continue
        parts = path.split("/")
        if path.startswith("/") or any(part in {".", ".."} for part in parts):
            raise ValueError(f"unsafe changed path: {path}")
        if path in seen:
            raise ValueError(f"duplicate changed path: {path}")
        seen.add(path)
        normalized.append(path)
    if not normalized:
        raise ValueError("at least one changed path is required")
    return tuple(sorted(normalized))


def is_governance_path(path: str) -> bool:
    return path in GOVERNANCE_EXACT_PATHS or any(
        path.startswith(prefix) for prefix in GOVERNANCE_PREFIXES
    )


def classify_paths(paths: Iterable[str], assurance: str) -> str:
    gate = assurance.casefold()
    try:
        implementation_paths = IMPLEMENTATION_PATHS_BY_GATE[gate]
    except KeyError as exc:
        raise ValueError(f"unsupported assurance gate: {assurance}") from exc

    normalized = normalize_paths(paths)
    strict_implementation_paths = implementation_paths - WORKFLOW_INTEGRATION_PATHS
    if gate != "aq7" and set(normalized).intersection(strict_implementation_paths):
        return APPLICABLE

    non_neutral = set(normalized) - COMMON_TRIGGER_PATHS
    if not non_neutral:
        return NOT_APPLICABLE

    # The Covenant is a separate, human-authorized governance-assurance scope.
    # Only its complete declared slice is outside the historical AQ5/AQ6/PRAI
    # exact inventories. Any anchored partial or mixed Covenant change remains
    # APPLICABLE so those legacy gates fail closed rather than silently exempt it.
    if non_neutral == COVENANT_IMPLEMENTATION_PATHS:
        return NOT_APPLICABLE
    if non_neutral.intersection(COVENANT_SCOPE_ANCHOR_PATHS):
        return APPLICABLE

    # AQ6 and AQ7 have their own exact-scope gates. Partial or mixed changes
    # remain APPLICABLE so the legacy gates continue to fail closed.
    if non_neutral in {AQ6_IMPLEMENTATION_PATHS, AQ7_IMPLEMENTATION_PATHS}:
        return NOT_APPLICABLE

    governance_paths = {path for path in non_neutral if is_governance_path(path)}
    reference_paths = non_neutral.intersection(ADAPTIVE_ASSURANCE_REFERENCE_PATHS)
    workflow_paths = non_neutral.intersection(WORKFLOW_INTEGRATION_PATHS)
    unknown_paths = non_neutral - governance_paths - reference_paths - workflow_paths

    # Governance/metadata compatibility is exempt only as a wholly recognized
    # change set. Unknown or partial assurance paths remain fail-closed.
    if unknown_paths or not governance_paths:
        return APPLICABLE
    if workflow_paths and not PROTECTED_GOVERNANCE_ANCHORS.intersection(normalized):
        return APPLICABLE
    return NOT_APPLICABLE


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assurance", choices=tuple(IMPLEMENTATION_PATHS_BY_GATE), required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = classify_paths(sys.stdin, args.assurance)
    except ValueError as exc:
        print(f"scope classification failed: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
