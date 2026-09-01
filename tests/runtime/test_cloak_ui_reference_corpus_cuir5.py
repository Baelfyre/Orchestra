from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALUATOR = ROOT / "scripts/evaluate_cloak_cuir5.py"


def _module():
    spec = importlib.util.spec_from_file_location("cuir5_evaluation", EVALUATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cuir5_controlled_retrieval_evaluation_passes_without_overclaiming():
    result = _module().evaluate()
    assert result["result"] == "CONTROLLED_EVALUATION_PASS"
    assert result["recommendation"] == "ADOPT_OPTIONAL"
    assert result["metrics"]["expected_pattern_recall"] >= 0.8
    assert result["metrics"]["expected_pattern_recall"] > result["metrics"]["baseline_expected_pattern_recall"]
    assert result["metrics"]["provenance_completeness"] == 1.0
    assert result["metrics"]["bounded_context_compliance"] == 1.0
    assert result["metrics"]["authority_boundary_compliance"] == 1.0
    assert result["metrics"]["source_copying_violation_count"] == 0
    assert "end-to-end LLM output quality" in result["unsupported_claims"]
    assert "rendered visual correctness" in result["unsupported_claims"]


def test_every_case_preserves_bounded_context_and_authority_boundary():
    result = _module().evaluate()
    for case in result["cases"]:
        assert case["bounded_context"] is True
        assert case["authority_boundary"] is True
