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

spec = importlib.util.spec_from_file_location(
    "validate_gate_coverage",
    ROOT / "scripts" / "validation" / "validate_gate_coverage.py",
)
validation = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validation)


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


def main() -> int:
    test_cli_passes_source_bound_evidence()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
