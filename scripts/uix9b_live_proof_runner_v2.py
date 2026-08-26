"""V2 preparation runner and fail-closed live execution gate.

This revision verifies every frozen identity before a future run.  It has no
provider adapter and therefore cannot execute a live model task in V2
preparation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema

import uix9_live_metric_evaluator_v2 as evaluator


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "machine" / "ui" / "uix9b-live-proof-plan.v2.json"
PLAN_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-plan.v2.schema.json"
IDENTITY_PATH = ROOT / "machine" / "ui" / "uix9b-live-proof-v2-identity.json"
CALIBRATION_MANIFEST = ROOT / "machine" / "ui" / "uix9b-live-calibration-manifest.v2.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(value: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def git_value(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def verify_frozen_identities() -> dict[str, Any]:
    plan = load_json(PLAN_PATH)
    validate(plan, PLAN_SCHEMA)
    identity = load_json(IDENTITY_PATH)
    evaluator.verify_identity(IDENTITY_PATH, evaluator.DEFAULT_FIXTURE_ROOT)
    calibration = load_json(CALIBRATION_MANIFEST)
    validate(calibration, ROOT / "machine" / "schemas" / "uix9b-live-calibration-manifest.v2.schema.json")
    if plan["canonical_sha"] != git_value("rev-parse", "HEAD") or plan["canonical_sha"] != git_value("rev-parse", "origin/main"):
        raise RuntimeError("CANONICAL_SHA_MISMATCH")
    if plan["fixture_digest"] != identity["fixture_digest"] or plan["task_digest"] != identity["task_digest"] or plan["validator_digest"] != identity["validator_digest"] or plan["uix_guidance_digest"] != identity["uix_guidance_digest"]:
        raise RuntimeError("PLAN_IDENTITY_MISMATCH")
    if plan["evaluator_digest"] != identity["evaluator_digest"] or calibration["evaluator_digest"] != identity["evaluator_digest"]:
        raise RuntimeError("EVALUATOR_IDENTITY_MISMATCH")
    expected_cases = {item["case_id"] for item in calibration["cases"]}
    if expected_cases != {"EXPECTED_POSITIVE", "EXPECTED_NEGATIVE", "BOUNDARY_STRUCTURAL_LITERAL", "MALFORMED_CANDIDATE", "MISSING_REQUIRED_ARTIFACT"}:
        raise RuntimeError("CALIBRATION_CASE_SET_MISMATCH")
    return {"canonical_sha": plan["canonical_sha"], "fixture_digest": plan["fixture_digest"], "task_digest": plan["task_digest"], "validator_digest": plan["validator_digest"], "uix_guidance_digest": plan["uix_guidance_digest"], "evaluator_digest": plan["evaluator_digest"], "calibration_cases": sorted(expected_cases), "live_calls_executed": 0, "provider_calls_executed": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify-frozen-identities", "execute"])
    args = parser.parse_args()
    try:
        report = verify_frozen_identities()
        if args.command == "execute":
            print("UIX_9C_EXECUTION_REFUSED_PREPARATION_ONLY")
            print(json.dumps(report, indent=2, sort_keys=True))
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        print("V2_FROZEN_IDENTITIES=PASS")
        return 0
    except (RuntimeError, OSError, json.JSONDecodeError, jsonschema.exceptions.ValidationError) as exc:
        print(f"V2_FROZEN_IDENTITIES=FAIL_CLOSED:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
