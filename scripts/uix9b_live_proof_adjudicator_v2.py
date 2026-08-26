"""Deterministic, treatment-blind UIX-9B V2 observation adjudication."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-observation.v2.schema.json"
RESULT_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-result.v2.schema.json"
PAIR_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-pair-adjudication.v2.schema.json"

ARM_A = "BASELINE_NO_ORCHESTRA_UIX_GUIDANCE"
ARM_B = "GOVERNED_CANONICAL_UIX_1_8_GUIDANCE"
TRUE_IS_BETTER = {"COMPONENT_REUSE", "STATE_COVERAGE", "ASSET_PROVENANCE", "RESPONSIVE_CONTAINMENT", "ACCESSIBILITY_INVARIANTS", "DETERMINISTIC_ACCEPTANCE"}
FALSE_IS_BETTER = {"ASSET_SUBSTITUTION", "REVISION_MISMATCH", "VISUAL_BASELINE_REPLACEMENT"}
LOWER_IS_BETTER = {"DUPLICATE_COMPONENT_COUNT", "TOKEN_VIOLATIONS", "ARBITRARY_STYLE_DRIFT", "UNRESOLVED_MAPPINGS"}
PRIMARY_METRICS = TRUE_IS_BETTER | FALSE_IS_BETTER | LOWER_IS_BETTER
HARD_GUARDRAILS = {"ACCESSIBILITY_INVARIANTS", "RESPONSIVE_CONTAINMENT", "ASSET_PROVENANCE", "ASSET_SUBSTITUTION", "REVISION_MISMATCH", "VISUAL_BASELINE_REPLACEMENT", "DETERMINISTIC_ACCEPTANCE"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(value: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def validate_observation(observation: dict[str, Any]) -> None:
    validate(observation, OBSERVATION_SCHEMA)
    if observation["run_classification"] not in {"ZERO_CALL_CANARY_PASS", "VALID_UNFAVORABLE_OUTPUT"}:
        raise ValueError("observation is not a countable deterministic output")
    if observation["model_call_count"] != 0 or observation["provider_call_count"] != 0:
        raise ValueError("zero-call adjudicator received a call-bearing observation")


def pair_adjudication(baseline: dict[str, Any], governed: dict[str, Any]) -> dict[str, Any]:
    validate_observation(baseline)
    validate_observation(governed)
    failures: list[str] = []
    if baseline["arm_id"] != ARM_A or governed["arm_id"] != ARM_B:
        failures.append("ARM_IDENTITY_MISMATCH")
    if (baseline["pair_id"], baseline["repetition"]) != (governed["pair_id"], governed["repetition"]):
        failures.append("PAIR_IDENTITY_MISMATCH")
    for field in ("starting_fixture_digest", "requirements_digest", "task_digest", "validator_digest", "evaluator_digest", "evaluator_version"):
        if baseline[field] != governed[field]:
            failures.append(f"SHARED_IDENTITY_MISMATCH_{field.upper()}")
    if baseline["guidance_digest_or_NONE"] != "NONE" or governed["guidance_digest_or_NONE"] == "NONE":
        failures.append("TREATMENT_GUIDANCE_IDENTITY_MISMATCH")
    metric_comparison: dict[str, dict[str, Any]] = {}
    for metric in sorted(PRIMARY_METRICS):
        a = baseline["primary_metrics"][metric]
        b = governed["primary_metrics"][metric]
        if metric in LOWER_IS_BETTER:
            improvement = b < a
        elif metric in FALSE_IS_BETTER:
            improvement = (not b) and a
        else:
            improvement = (not a) and b if isinstance(a, bool) else b > a
        regression = (a and not b) if metric in TRUE_IS_BETTER and isinstance(a, bool) else ((not a) and b if metric in FALSE_IS_BETTER else (b < a if metric in TRUE_IS_BETTER else (b > a if metric in FALSE_IS_BETTER else (b > a))))
        metric_comparison[metric] = {"baseline": a, "governed": b, "improved": improvement, "regressed": regression}
        if metric in HARD_GUARDRAILS and regression:
            failures.append(f"HARD_GUARDRAIL_REGRESSION_{metric}")
    result = {
        "$schema": "../../../machine/schemas/uix9b-live-pair-adjudication.v2.schema.json",
        "schema_version": "orchestra.uix9b.live-pair-adjudication.v2",
        "role": "UIX_9B_PAIR_ADJUDICATION",
        "pair_id": baseline["pair_id"],
        "repetition": baseline["repetition"],
        "valid": not failures,
        "failure_codes": sorted(set(failures)),
        "metric_comparison": metric_comparison,
        "model_behavior_claim": "NONE",
    }
    validate(result, PAIR_SCHEMA)
    return result


def campaign_adjudication(observations: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    expected_order = ["A1", "B1", "B2", "A2", "A3", "B3"]
    by_run = {item.get("run_id"): item for item in observations}
    if len(observations) != 6 or sorted(by_run) != sorted(expected_order):
        failures.append("RUN_SET_MISMATCH")
    for observation in observations:
        try:
            validate_observation(observation)
        except (ValueError, jsonschema.exceptions.ValidationError) as exc:
            failures.append(f"INVALID_OBSERVATION:{observation.get('run_id', 'UNKNOWN')}:{type(exc).__name__}")
    if failures:
        result_classification = "PROTOCOL_INVALID"
    else:
        result_classification = "MIXED_OR_INCONCLUSIVE"
    result = {
        "$schema": "../../../machine/schemas/uix9b-live-proof-result.v2.schema.json",
        "schema_version": "orchestra.uix9b.live-proof-result.v2",
        "role": "UIX_9B_LIVE_PROOF_RESULT",
        "result_classification": result_classification,
        "observations_count": len(observations),
        "valid_executions_counted": 0 if failures else 6,
        "failure_codes": sorted(set(failures)),
        "model_behavior_claim": "NONE",
        "benefit_claim": "NONE",
        "harm_claim": "NONE",
    }
    validate(result, RESULT_SCHEMA)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--governed", type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    if args.baseline and args.governed:
        output = pair_adjudication(load_json(args.baseline), load_json(args.governed))
    elif args.observations:
        data = json.loads(args.observations.read_text(encoding="utf-8"))
        output = campaign_adjudication(data)
    else:
        parser.error("provide --baseline and --governed, or --observations")
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
