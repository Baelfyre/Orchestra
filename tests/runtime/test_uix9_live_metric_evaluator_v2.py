from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import uix9_live_metric_evaluator_v2 as evaluator
import uix9b_live_proof_adjudicator_v2 as adjudicator


CALIBRATION = ROOT / "tests" / "fixtures" / "ui" / "uix9b-live-calibration"
FIXTURE = ROOT / "tests" / "fixtures" / "ui" / "uix9-live-project"
IDENTITY = ROOT / "machine" / "ui" / "uix9b-live-proof-v2-identity.json"
RESULT_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-metric-result.v2.schema.json"
OBSERVATION_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-observation.v2.schema.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(value, schema_path: Path):
    schema = read_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def evaluate_case(name: str):
    case = CALIBRATION / name
    return evaluator.evaluate(FIXTURE, case / "candidate", case / "validator-result.json", IDENTITY)


def test_calibration_outputs_are_frozen_and_schema_valid():
    expected_names = ("positive", "negative", "boundary")
    for name in expected_names:
        result = evaluate_case(name)
        expected = read_json(CALIBRATION / name / "expected-metric-result.json")
        validate(result, RESULT_SCHEMA)
        assert result["status"] == expected["status"]
        assert result["candidate_tree_digest"] == expected["candidate_tree_digest"]
        assert result["metric_result_digest"] == expected["metric_result_digest"]
        assert result["metrics"] == expected["metrics"]


def test_malformed_and_missing_required_inputs_fail_closed():
    for name in ("malformed", "missing-artifact"):
        case = CALIBRATION / name
        validator_result = case / "validator-result.json"
        result = evaluator.evaluate(FIXTURE, case / "candidate", validator_result, IDENTITY)
        expected = read_json(case / "expected-metric-result.json")
        validate(result, RESULT_SCHEMA)
        assert result["status"] == "FAIL_CLOSED"
        assert result["failure_codes"] == expected["failure_codes"]
        assert result["metric_result_digest"] == expected["metric_result_digest"]


def test_identical_candidate_trees_produce_identical_results():
    first = evaluate_case("positive")
    second = evaluate_case("positive")
    assert first == second


def test_frozen_contract_and_calibration_manifest():
    manifest = read_json(ROOT / "machine" / "ui" / "uix9b-live-calibration-manifest.v2.json")
    validate(manifest, ROOT / "machine" / "schemas" / "uix9b-live-calibration-manifest.v2.schema.json")
    identity = read_json(IDENTITY)
    assert manifest["evaluator_digest"] == identity["evaluator_digest"]
    assert manifest["historical_evidence_used"] is False
    assert {case["case_id"] for case in manifest["cases"]} == {
        "EXPECTED_POSITIVE", "EXPECTED_NEGATIVE", "BOUNDARY_STRUCTURAL_LITERAL", "MALFORMED_CANDIDATE", "MISSING_REQUIRED_ARTIFACT"
    }


def check(status: str, details: str):
    return {"status": status, "deterministic": True, "details": details}


def observation(result: dict, run_id: str, arm_id: str, guidance: str):
    final_files = [path for path, _ in evaluator.tree_records(CALIBRATION / "positive" / "candidate")]
    starting_files = [path for path, _ in evaluator.tree_records(FIXTURE)]
    identity = read_json(IDENTITY)
    requirements_digest = evaluator.digest_file(FIXTURE / "requirements.json")
    task_digest = evaluator.digest_file(FIXTURE / "task.md")
    return {
        "$schema": "../../../machine/schemas/uix9b-live-proof-observation.v2.schema.json",
        "schema_version": "orchestra.uix9b-live-proof-observation.v2",
        "role": "UIX_9B_LIVE_PROOF_OBSERVATION",
        "run_id": run_id,
        "arm_id": arm_id,
        "pair_id": "PAIR_1",
        "repetition": 1,
        "execution_order": 1 if run_id == "A1" else 2,
        "provider": "openai-codex",
        "model": "gpt-5.6-luna",
        "model_revision": "UNRESOLVED_PENDING_LIVE_AUTHORIZATION",
        "reasoning_effort": "xhigh",
        "codex_cli_version": "ZERO_CALL_CANARY",
        "host_os": "TEST_HOST",
        "starting_fixture_digest": identity["fixture_digest"],
        "requirements_digest": requirements_digest,
        "task_digest": task_digest,
        "prompt_digest": "0" * 64,
        "guidance_digest_or_NONE": guidance,
        "validator_digest": identity["validator_digest"],
        "evaluator_version": result["evaluator_version"],
        "evaluator_digest": result["evaluator_digest"],
        "metric_result_digest": result["metric_result_digest"],
        "starting_tree": {"digest": identity["fixture_digest"], "files": starting_files},
        "final_tree": {"digest": result["candidate_tree_digest"], "files": final_files},
        "changed_file_manifest": ["project/src/screens/work-queue.js"],
        "git_diff_digest": "0" * 64,
        "build_result": check("PASS", "zero-call calibration build"),
        "test_result": check("PASS", "zero-call calibration tests"),
        "validator_result": check("PASS", "zero-call calibration validator"),
        "primary_metrics": result["metrics"],
        "secondary_metrics": {
            "IMPLEMENTATION_DIFF_SIZE": None, "NEW_COMPONENT_COUNT": None, "NEW_ARBITRARY_TOKEN_VALUE_COUNT": None,
            "VALIDATION_REMEDIATION_COUNT": None, "WALL_CLOCK_EXECUTION_TIME": None, "INPUT_TOKENS": None,
            "OUTPUT_TOKENS": None, "TOTAL_TOKENS": None,
            "metric_status": {"WALL_CLOCK_EXECUTION_TIME": "UNAVAILABLE", "INPUT_TOKENS": "UNAVAILABLE", "OUTPUT_TOKENS": "UNAVAILABLE", "TOTAL_TOKENS": "UNAVAILABLE"}
        },
        "failure_codes": [],
        "model_call_count": 0,
        "provider_call_count": 0,
        "token_counts_if_trustworthy": {"status": "UNAVAILABLE", "input": None, "output": None, "total": None},
        "start_timestamp": None,
        "end_timestamp": None,
        "run_classification": "ZERO_CALL_CANARY_PASS",
        "outage_or_invalid_reason": None,
        "external_side_effects": {"model_calls": 0, "provider_calls": 0, "external_repo_mutations": 0, "orderly_mutations": 0, "padayon_mutations": 0, "registry_mutations": 0, "production_mutations": 0, "installed_integration_mutations": 0, "release_tag_mutations": 0, "deployments": 0, "secrets_or_customer_data_used": False}
    }


def test_zero_call_candidate_to_observation_to_pair_adjudication():
    result = evaluate_case("positive")
    baseline = observation(result, "A1", adjudicator.ARM_A, "NONE")
    governed = observation(result, "B1", adjudicator.ARM_B, read_json(IDENTITY)["uix_guidance_digest"])
    validate(baseline, OBSERVATION_SCHEMA)
    validate(governed, OBSERVATION_SCHEMA)
    pair = adjudicator.pair_adjudication(baseline, governed)
    assert pair["valid"] is True
    assert pair["failure_codes"] == []
    assert pair["model_behavior_claim"] == "NONE"


def test_campaign_result_classification_is_closed():
    result = adjudicator.campaign_adjudication([])
    validate(result, ROOT / "machine" / "schemas" / "uix9b-live-proof-result.v2.schema.json")
    assert result["result_classification"] == "PROTOCOL_INVALID"
    assert result["model_behavior_claim"] == "NONE"
