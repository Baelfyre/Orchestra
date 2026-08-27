"""Evidence-preserving UIX-9C V3 post-study adjudication.

This module does not execute models, providers, network calls, or mutate captured
campaign evidence. It exists to resolve two defects discovered after the V3 live
capture: counterbalanced Pair 2 was passed to the frozen pair adjudicator in
execution order rather than baseline/governed arm order, and the frozen campaign
adjudicator did not encode the preregistered no-benefit branch.

The live runner and frozen adjudicator remain unchanged for provenance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import uix9b_live_proof_adjudicator_v2 as frozen
except ImportError:
    import uix9b_live_proof_adjudicator_v2 as frozen


EXPECTED_RUNS = ("A1", "B1", "B2", "A2", "A3", "B3")
PAIR_IDS = ("PAIR_1", "PAIR_2", "PAIR_3")
IDENTITY_FAILURE_PREFIXES = (
    "ARM_IDENTITY_MISMATCH",
    "PAIR_IDENTITY_MISMATCH",
    "SHARED_IDENTITY_MISMATCH_",
    "TREATMENT_GUIDANCE_IDENTITY_MISMATCH",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def observation_path(evidence_root: Path, run_id: str) -> Path:
    pair_id = f"PAIR_{run_id[1]}"
    return evidence_root / "pairs" / pair_id / run_id / "observations" / f"{run_id}.json"


def load_observations(evidence_root: Path) -> dict[str, dict[str, Any]]:
    observations: dict[str, dict[str, Any]] = {}
    for run_id in EXPECTED_RUNS:
        path = observation_path(evidence_root, run_id)
        if not path.is_file():
            raise FileNotFoundError(f"MISSING_OBSERVATION:{run_id}:{path}")
        observation = load_json(path)
        if observation.get("run_id") != run_id:
            raise ValueError(f"RUN_ID_MISMATCH:{run_id}")
        frozen.validate_observation(observation)
        observations[run_id] = observation
    return observations


def corrected_pair_adjudications(observations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for repetition in (1, 2, 3):
        baseline = observations[f"A{repetition}"]
        governed = observations[f"B{repetition}"]
        results.append(frozen.pair_adjudication(baseline, governed))
    return results


def _identity_failure(code: str) -> bool:
    return any(code == prefix or code.startswith(prefix) for prefix in IDENTITY_FAILURE_PREFIXES)


def classify_pair_adjudications(pair_results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    if len(pair_results) != 3 or {item.get("pair_id") for item in pair_results} != set(PAIR_IDS):
        return "PROTOCOL_INVALID", ["PAIR_SET_MISMATCH"]

    identity_failures = sorted(
        {
            code
            for pair in pair_results
            for code in pair.get("failure_codes", [])
            if _identity_failure(str(code))
        }
    )
    if identity_failures:
        return "PROTOCOL_INVALID", identity_failures

    comparisons = [
        comparison
        for pair in pair_results
        for comparison in pair.get("metric_comparison", {}).values()
    ]
    if len(comparisons) != 3 * len(frozen.PRIMARY_METRICS):
        return "PROTOCOL_INVALID", ["PRIMARY_METRIC_COMPARISON_SET_MISMATCH"]

    # This is the exact null case observed by V3 and directly maps to the
    # preregistered rule: valid evidence does not establish a repeatable
    # governed advantage. It does not assert harm.
    if all(not item.get("improved", False) and not item.get("regressed", False) for item in comparisons):
        return "NO_BENEFIT_ESTABLISHED", []

    # Any non-null pattern is kept conservative. The frozen machine code did
    # not operationalize a numeric threshold for "multiple structural metrics"
    # beyond the prose plan, so remediation must not invent one after seeing
    # live data.
    return "MIXED_OR_INCONCLUSIVE", ["NON_NULL_PATTERN_REQUIRES_PREDECLARED_THRESHOLD"]


def adjudicate(evidence_root: Path) -> dict[str, Any]:
    observations = load_observations(evidence_root)
    pair_results = corrected_pair_adjudications(observations)
    classification, failure_codes = classify_pair_adjudications(pair_results)
    result = {
        "$schema": "../../../machine/schemas/uix9b-live-proof-result.v2.schema.json",
        "schema_version": "orchestra.uix9b.live-proof-result.v2",
        "role": "UIX_9B_LIVE_PROOF_RESULT",
        "result_classification": classification,
        "observations_count": len(observations),
        "valid_executions_counted": 0 if classification == "PROTOCOL_INVALID" else len(observations),
        "failure_codes": failure_codes,
        "model_behavior_claim": "NONE",
        "benefit_claim": "NONE",
        "harm_claim": "NONE",
    }
    frozen.validate(result, frozen.RESULT_SCHEMA)
    return {
        "result": result,
        "pair_adjudications": pair_results,
        "poststudy_remediation": {
            "model_calls": 0,
            "provider_calls": 0,
            "network_access": 0,
            "captured_evidence_mutations": 0,
            "live_runner_modified": False,
            "frozen_adjudicator_modified": False,
            "pair_order_rule": "A_BASELINE_THEN_B_GOVERNED_BY_REPETITION",
            "null_result_rule": "ALL_39_PAIRWISE_PRIMARY_METRICS_UNCHANGED_IMPLIES_NO_BENEFIT_ESTABLISHED",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True, type=Path)
    args = parser.parse_args()
    output = adjudicate(args.evidence_root.resolve())
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
