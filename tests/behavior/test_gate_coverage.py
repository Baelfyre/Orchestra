#!/usr/bin/env python3
"""Behavior checks for the AQ-6 CLI boundary."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.gate_coverage import (
    AQ6_CONTRACT_SCHEMA_VERSION,
    GateCoverageDeclaration,
    GateCoverageManifest,
    GateExecutionReceipt,
)
from orchestra_runtime.shared.canonicalization import receipt_digest
from scripts.validation.classify_f3_jev_successor_scope import (
    EXACT_F3_JEV_SUCCESSOR,
    NOT_EXACT_F3_JEV_SUCCESSOR,
    classify_f3_jev_successor_scope,
)

spec = importlib.util.spec_from_file_location(
    "validate_gate_coverage",
    ROOT / "scripts" / "validation" / "validate_gate_coverage.py",
)
validation = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validation)

scope_spec = importlib.util.spec_from_file_location(
    "classify_adaptive_assurance_scope",
    ROOT / "scripts" / "validation" / "classify_adaptive_assurance_scope.py",
)
scope = importlib.util.module_from_spec(scope_spec)
assert scope_spec and scope_spec.loader
scope_spec.loader.exec_module(scope)


AQ6_SCOPE_PATHS = (
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
)

F3_JEV_SUCCESSOR_PATHS = (
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
)

ORIGINAL_AQ6_EXACT_WORKFLOW_PATHS = (
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
)


CONTRACT = ROOT / "machine" / "adaptive" / "aq6-gate-coverage.v1.json"
SOURCE = "orchestra:aq6"
CANDIDATE = "a" * 40
TREE = "b" * 40
WHEN = "2026-09-09T01:00:00Z"
WORKFLOW = ".github/workflows/aq6-gate-coverage.yml"
COMMAND = "python -B -m pytest"
CHANGED = "orchestra_runtime/domain/adaptive/gate_coverage.py"
TEST_ID = "tests/runtime/test_adaptive_assurance_aq6.py::test_positive_decision_is_source_bound_and_non_authorizing"


def _sample():
    declaration = GateCoverageDeclaration(
        gate_id="aq6-runtime",
        assurance_classes=("FUNCTIONAL_ASSURANCE", "PROVENANCE_ASSURANCE", "INDEPENDENT_QA"),
        covered_paths=(CHANGED,),
        covered_risks=("PROVENANCE",),
        test_ids=(TEST_ID,),
        workflow_path=WORKFLOW,
        commands=(COMMAND,),
    )
    payload = {
        "schema_version": AQ6_CONTRACT_SCHEMA_VERSION,
        "manifest_id": "manifest-aq6-behavior",
        "repository": "Baelfyre/Orchestra",
        "source_ref": SOURCE,
        "candidate_sha": CANDIDATE,
        "tree_sha": TREE,
        "work_item_ref": "AQ6_GATE_COVERAGE",
        "changed_paths": [CHANGED],
        "required_assurance": ["FUNCTIONAL_ASSURANCE", "PROVENANCE_ASSURANCE", "INDEPENDENT_QA"],
        "required_risks": ["PROVENANCE"],
        "declarations": [declaration.to_dict()],
        "generated_at": WHEN,
    }
    manifest = GateCoverageManifest.from_mapping(
        {**payload, "manifest_digest": receipt_digest(payload)}
    )
    receipt = GateExecutionReceipt(
        execution_id="execution-aq6-behavior",
        gate_id="aq6-runtime",
        result="PASS",
        candidate_sha=CANDIDATE,
        tree_sha=TREE,
        command=COMMAND,
        executed_test_ids=(TEST_ID,),
        observed_at=WHEN,
    )
    return manifest, receipt


def test_cli_passes_source_bound_evidence():
    manifest, receipt = _sample()
    coverage = {TEST_ID: [CHANGED]}
    original_read_json = validation.read_json

    def fake_read_json(path: Path):
        if path.name == "contract.json":
            return json.loads(CONTRACT.read_text(encoding="utf-8"))
        if path.name == "manifest.json":
            return manifest.to_dict()
        if path.name == "executions.json":
            return [receipt.to_dict()]
        if path.name == "coverage.json":
            return coverage
        raise AssertionError(path)

    validation.read_json = fake_read_json
    arguments = [
        "validate_gate_coverage.py",
        "--manifest",
        "manifest.json",
        "--executions",
        "executions.json",
        "--repository",
        "Baelfyre/Orchestra",
        "--source-ref",
        SOURCE,
        "--candidate-sha",
        CANDIDATE,
        "--tree-sha",
        TREE,
        "--work-item-ref",
        "AQ6_GATE_COVERAGE",
        "--available-test",
        TEST_ID,
        "--workflow",
        WORKFLOW,
        "--test-coverage",
        "coverage.json",
        "--contract",
        "contract.json",
    ]
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            sys.argv = arguments
            assert validation.main() == 0
    finally:
        validation.read_json = original_read_json
    assert "AQ6_RESULT=PASS" in output.getvalue()


def test_complete_aq6_scope_is_not_applicable_to_legacy_gates():
    complete = (*AQ6_SCOPE_PATHS, "CHANGELOG.md", "README.json")
    assert scope.classify_paths(complete, "aq5") == "NOT_APPLICABLE"
    assert scope.classify_paths(complete, "prai") == "NOT_APPLICABLE"

    partial = tuple(
        path for path in complete
        if path != "scripts/validation/classify_adaptive_assurance_scope.py"
    )
    assert scope.classify_paths(partial, "aq5") == "APPLICABLE"
    assert scope.classify_paths((*complete, "unexpected.py"), "prai") == "APPLICABLE"
    assert scope.classify_paths(
        (*complete, "orchestra_runtime/domain/adaptive/qa_compliance.py"),
        "aq5",
    ) == "APPLICABLE"


def test_f3_jev_successor_scope_requires_the_exact_approved_inventory():
    assert len(F3_JEV_SUCCESSOR_PATHS) == 18
    assert classify_f3_jev_successor_scope(F3_JEV_SUCCESSOR_PATHS) == EXACT_F3_JEV_SUCCESSOR

    rejected = {
        "partial": F3_JEV_SUCCESSOR_PATHS[:-1],
        "mixed": (*F3_JEV_SUCCESSOR_PATHS, "orchestra_runtime/domain/adaptive/gate_coverage.py"),
        "superset": (*F3_JEV_SUCCESSOR_PATHS, "unexpected-future-change.py"),
        "duplicate": (*F3_JEV_SUCCESSOR_PATHS, F3_JEV_SUCCESSOR_PATHS[0]),
        "unknown": ("unregistered/future-change.py",),
        "unsafe": (*F3_JEV_SUCCESSOR_PATHS[:-1], "../CHANGELOG.md"),
    }
    for case, paths in rejected.items():
        assert classify_f3_jev_successor_scope(paths) == NOT_EXACT_F3_JEV_SUCCESSOR, case


def test_aq6_exact_inventory_and_coverage_floors_remain_unchanged():
    workflow = (ROOT / ".github" / "workflows" / "aq6-gate-coverage.yml").read_text(encoding="utf-8")
    block = workflow.split("cat > expected-paths.txt <<'EOF'\n", 1)[1].split("\n          EOF", 1)[0]
    original_paths = tuple(line.removeprefix("          ") for line in block.splitlines())
    assert frozenset(original_paths) == frozenset(ORIGINAL_AQ6_EXACT_WORKFLOW_PATHS)
    assert "--cov-fail-under=97" in workflow
    assert "coverage report --fail-under=95" in workflow
    assert "AQ6_SCOPE_LANE=F3_JEV_SUCCESSOR_EXACT" in workflow


def main() -> int:
    test_cli_passes_source_bound_evidence()
    test_complete_aq6_scope_is_not_applicable_to_legacy_gates()
    test_f3_jev_successor_scope_requires_the_exact_approved_inventory()
    test_aq6_exact_inventory_and_coverage_floors_remain_unchanged()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
