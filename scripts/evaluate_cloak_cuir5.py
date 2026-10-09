from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "machine/evaluation/cloak-ui-reference-cuir5-benchmark.v1.json"
RETRIEVER = ROOT / "scripts/retrieve_cloak_patterns.py"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _retriever_module():
    spec = importlib.util.spec_from_file_location("cuir4_retrieval", RETRIEVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate() -> dict[str, Any]:
    benchmark = _load(BENCHMARK)
    module = _retriever_module()

    expected_total = 0
    expected_hits = 0
    provenance_total = 0
    provenance_complete = 0
    bounded_cases = 0
    authority_safe_cases = 0
    source_copying_violations = 0
    case_results = []

    for case in benchmark["cases"]:
        result = module.retrieve_patterns(case["task"])
        selected = result["patterns"]
        selected_ids = {pattern["pattern_id"] for pattern in selected}
        expected = set(case["expected_patterns"])
        hits = expected & selected_ids
        expected_total += len(expected)
        expected_hits += len(hits)

        for pattern in selected:
            provenance_total += 1
            if (
                pattern.get("source_analysis_ids")
                and pattern.get("source_record_paths")
                and pattern.get("reuse_classifications")
            ):
                provenance_complete += 1
            if not pattern.get("orchestra_native_normalization", False):
                source_copying_violations += 1
            if pattern.get("implementation_authority", True):
                source_copying_violations += 1

        bounded = len(result["problem_classes"]) <= 3 and len(selected) <= 5
        authority_safe = result["implementation_authority"] is False
        bounded_cases += int(bounded)
        authority_safe_cases += int(authority_safe)

        case_results.append(
            {
                "id": case["id"],
                "expected": sorted(expected),
                "retrieved": sorted(selected_ids),
                "hits": sorted(hits),
                "expected_recall": (len(hits) / len(expected)) if expected else 1.0,
                "bounded_context": bounded,
                "authority_boundary": authority_safe,
            }
        )

    case_count = len(benchmark["cases"])
    metrics = {
        "expected_pattern_recall": expected_hits / expected_total if expected_total else 1.0,
        "provenance_completeness": provenance_complete / provenance_total if provenance_total else 1.0,
        "bounded_context_compliance": bounded_cases / case_count if case_count else 1.0,
        "authority_boundary_compliance": authority_safe_cases / case_count if case_count else 1.0,
        "source_copying_violation_count": source_copying_violations,
        "baseline_expected_pattern_recall": 0.0,
    }

    thresholds = benchmark["pass_thresholds"]
    passed = (
        metrics["expected_pattern_recall"] >= thresholds["expected_pattern_recall"]
        and metrics["provenance_completeness"] >= thresholds["provenance_completeness"]
        and metrics["bounded_context_compliance"] >= thresholds["bounded_context_compliance"]
        and metrics["authority_boundary_compliance"] >= thresholds["authority_boundary_compliance"]
        and metrics["source_copying_violation_count"] == thresholds["source_copying_violation_count"]
    )

    return {
        "schema_version": "orchestra.cloak-ui-reference-cuir5-evaluation-result.v1",
        "scope": benchmark["evaluation_scope"],
        "result": "CONTROLLED_EVALUATION_PASS" if passed else "CONTROLLED_EVALUATION_FAIL",
        "recommendation": "ADOPT_OPTIONAL" if passed else "REVISE_AND_RETEST",
        "metrics": metrics,
        "thresholds": thresholds,
        "cases": case_results,
        "unsupported_claims": benchmark["claims_not_supported_by_this_evaluation"],
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["result"] == "CONTROLLED_EVALUATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
