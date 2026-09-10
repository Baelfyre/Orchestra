#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Classify whether changes require historical adaptive-assurance exact-scope validation."""

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

AQ8_IMPLEMENTATION_PATHS = frozenset(
    {
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
        "machine/adaptive/aq8-high-risk-assurance-packs.v1.json",
        "machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json",
        "orchestra_runtime/domain/adaptive/__init__.py",
        "orchestra_runtime/domain/adaptive/high_risk_assurance.py",
        "scripts/validation/validate_aq8.py",
        "tests/behavior/run_tests.py",
        "tests/runtime/test_adaptive_assurance_aq8.py",
    }
)

AQ8_SCOPE_ANCHOR_PATHS = frozenset(
    {
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
        "machine/adaptive/aq8-high-risk-assurance-packs.v1.json",
        "machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json",
        "orchestra_runtime/domain/adaptive/high_risk_assurance.py",
        "scripts/validation/validate_aq8.py",
        "tests/runtime/test_adaptive_assurance_aq8.py",
    }
)

AQ8_CANONICAL_CLOSEOUT_PATHS = frozenset(
    {
        "CHANGELOG.md",
        "README.json",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
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

# These files govern repository assurance transport itself. Classifying them as
# governance control surfaces is durable taxonomy, not a lifecycle whitelist.
PROMOTION_ASSURANCE_GOVERNANCE_PATHS = frozenset(
    {
        ".github/workflows/validate.yml",
        ".github/workflows/cross-platform-validation.yml",
        ".github/workflows/required-analysis-compat.yml",
        ".github/workflows/governance-check.yml",
        ".github/workflows/signed-materialization.yml",
        "docs/validation/SIGNED_MATERIALIZATION_OPTIMIZATION_2026_08_16.md",
        "scripts/validate_signed_materialization.py",
        "scripts/validate_governance_promotion_attestation.py",
        "tests/behavior/test_signed_materialization.py",
        "tests/behavior/test_governance_promotion_attestation.py",
    }
)

# Specialized assurance workflows are governance transport controls only when
# they are changed together with the promotion-assurance contract and its
# fail-closed classifier/attestation regressions. In isolation they remain
# historical assurance implementation surfaces and therefore APPLICABLE.
SPECIALIZED_PROMOTION_ASSURANCE_WORKFLOW_PATHS = frozenset(
    {
        ".github/workflows/prai.yml",
        ".github/workflows/qa-compliance.yml",
        ".github/workflows/aq6-gate-coverage.yml",
        ".github/workflows/cosmic-ray-confidence.yml",
    }
)

PROMOTION_ASSURANCE_REQUIRED_ANCHORS = frozenset(
    {
        "docs/governance/TREE_ATTESTED_PROMOTION_ASSURANCE.md",
        "scripts/validation/classify_adaptive_assurance_scope.py",
        "tests/behavior/test_governance_promotion_attestation.py",
        "tests/behavior/test_protected_aq8_assurance_scope_policy.py",
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
        *PROMOTION_ASSURANCE_GOVERNANCE_PATHS,
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
    normalized_set = set(normalized)
    strict_implementation_paths = implementation_paths - WORKFLOW_INTEGRATION_PATHS

    # Human-authorized AQ8 lifecycle closeout whitelist. This exemption is
    # exact-set only and does not apply to AQ8 runtime, machine-contract,
    # workflow, test, mixed, superset, or anchor-bearing subset changes.
    if normalized_set == AQ8_CANONICAL_CLOSEOUT_PATHS:
        return NOT_APPLICABLE
    if gate != "aq7" and normalized_set.intersection(strict_implementation_paths):
        return APPLICABLE

    non_neutral = normalized_set - COMMON_TRIGGER_PATHS
    if not non_neutral:
        return NOT_APPLICABLE

    if non_neutral == AQ8_IMPLEMENTATION_PATHS:
        return NOT_APPLICABLE
    if non_neutral.intersection(AQ8_SCOPE_ANCHOR_PATHS):
        return APPLICABLE

    if non_neutral == COVENANT_IMPLEMENTATION_PATHS:
        return NOT_APPLICABLE
    if non_neutral.intersection(COVENANT_SCOPE_ANCHOR_PATHS):
        return APPLICABLE

    if non_neutral in {AQ6_IMPLEMENTATION_PATHS, AQ7_IMPLEMENTATION_PATHS}:
        return NOT_APPLICABLE

    specialized_workflow_paths = non_neutral.intersection(
        SPECIALIZED_PROMOTION_ASSURANCE_WORKFLOW_PATHS
    )
    specialized_workflows_are_anchored = bool(specialized_workflow_paths) and (
        PROMOTION_ASSURANCE_REQUIRED_ANCHORS.issubset(non_neutral)
    )
    if specialized_workflow_paths and not specialized_workflows_are_anchored:
        return APPLICABLE

    governance_paths = {path for path in non_neutral if is_governance_path(path)}
    if specialized_workflows_are_anchored:
        governance_paths.update(specialized_workflow_paths)

    reference_paths = non_neutral.intersection(ADAPTIVE_ASSURANCE_REFERENCE_PATHS)
    workflow_paths = non_neutral.intersection(WORKFLOW_INTEGRATION_PATHS) - governance_paths
    unknown_paths = non_neutral - governance_paths - reference_paths - workflow_paths

    if unknown_paths or not governance_paths:
        return APPLICABLE
    if workflow_paths and not PROTECTED_GOVERNANCE_ANCHORS.intersection(normalized_set):
        return APPLICABLE
    return NOT_APPLICABLE


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assurance", choices=tuple(IMPLEMENTATION_PATHS_BY_GATE), required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    raw_paths = tuple(sys.stdin)
    try:
        result = classify_paths(raw_paths, args.assurance)
        normalized = normalize_paths(raw_paths)
    except ValueError as exc:
        print(f"scope classification failed: {exc}", file=sys.stderr)
        return 2
    if (
        args.assurance == "prai"
        and result == NOT_APPLICABLE
        and set(normalized) == AQ8_CANONICAL_CLOSEOUT_PATHS
    ):
        print(
            "::notice title=PRAI scope whitelist::"
            "AQ8 canonical closeout exact-path whitelist applied; "
            "lifecycle-only projection with no runtime or authority bypass.",
            file=sys.stderr,
        )
        print(
            "PRAI_WHITELIST_NOTICE=AQ8_CANONICAL_CLOSEOUT_EXACT_PATHS",
            file=sys.stderr,
        )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
