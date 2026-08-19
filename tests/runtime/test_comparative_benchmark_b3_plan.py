from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
EXECUTOR_PATH = ROOT / "scripts" / "antigravity_benchmark_executor.py"
VALIDATOR_PATH = ROOT / "scripts" / "benchmarking" / "calibration_task_validator.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "benchmarking" / "b3-murmurs-isolated-calibration-plan-only.json"
MANIFEST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "comparative-benchmark-manifest.schema.json"
TASKSET_RECORD_PATH = ROOT / "machine" / "benchmarking" / "b3-calibration-task-set.v1.json"

SPEC_RUNNER = importlib.util.spec_from_file_location("comparative_benchmark_runner_b3", RUNNER_PATH)
assert SPEC_RUNNER is not None and SPEC_RUNNER.loader is not None
runner = importlib.util.module_from_spec(SPEC_RUNNER)
SPEC_RUNNER.loader.exec_module(runner)

SPEC_VAL = importlib.util.spec_from_file_location("calibration_task_validator", VALIDATOR_PATH)
assert SPEC_VAL is not None and SPEC_VAL.loader is not None
validator = importlib.util.module_from_spec(SPEC_VAL)
SPEC_VAL.loader.exec_module(validator)

SPEC_EXEC = importlib.util.spec_from_file_location("antigravity_benchmark_executor", EXECUTOR_PATH)
assert SPEC_EXEC is not None and SPEC_EXEC.loader is not None
executor = importlib.util.module_from_spec(SPEC_EXEC)
SPEC_EXEC.loader.exec_module(executor)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


EXPECTED_TASK_DEFINITIONS = [
    ("b3-cal-padayon-r5-capability-manifest", "SINGLE_DOMAIN"),
    ("b3-cal-padayon-o1-o2-compatibility", "DEPENDENCY_HEAVY"),
    ("b3-cal-padayon-o3-o4-freshness", "VALIDATION_HEAVY"),
    ("b3-cal-padayon-assurance-drift", "DEBUGGING"),
    ("b3-cal-padayon-o5-o6-routing", "HIGH_COORDINATION"),
]


def test_01_b3_plan_only_fixture_is_schema_valid_and_isolates_communication_mode() -> None:
    manifest = _load(MANIFEST_PATH)
    schema = _load(MANIFEST_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    runner.validate_manifest(manifest)

    assert manifest["experiment_kind"] == "MURMURS_ISOLATED"
    assert manifest["stage"] == "CALIBRATION"
    assert manifest["common_control_identity"]["orchestra_revision"] == "d95f677dbf23ab79c4698c26645ea30cea9b3019"
    assert manifest["common_control_identity"]["provider"] == "NO_PROVIDER_PLAN_ONLY"
    assert manifest["common_control_identity"]["model"] == "NO_MODEL_PLAN_ONLY"
    assert len(manifest["tasks"]) == 5
    assert manifest["repetitions_per_arm"] == 2
    assert len(manifest["arms"]) == 3
    assert {arm["communication_mode"] for arm in manifest["arms"]} == {"DEFAULT", "CAVEMAN", "MURMURS"}
    assert all(arm["topology_class"] == "FIXED_DETERMINISTIC" for arm in manifest["arms"])

    topology_identity = {(arm["topology_candidate_id"], arm["topology_digest"]) for arm in manifest["arms"]}
    assert len(topology_identity) == 1
    assert manifest["murmurs_evaluation"]["same_counter_identity_for_token_delta"] is True
    assert manifest["a5_evaluation"] is None
    assert manifest["interaction_evaluation"] is None
    assert all(task["task_payload"]["synthetic"] is True for task in manifest["tasks"])
    assert all(task["task_payload"]["execution_allowed"] is False for task in manifest["tasks"])


def test_02_exact_task_ids_classes_and_count() -> None:
    manifest = _load(MANIFEST_PATH)
    taskset = _load(TASKSET_RECORD_PATH)

    assert len(manifest["tasks"]) == 5
    assert len(taskset["tasks"]) == 5

    observed_manifest = [(t["task_id"], t["task_class"]) for t in manifest["tasks"]]
    observed_taskset = [(t["task_id"], t["task_class"]) for t in taskset["tasks"]]

    assert observed_manifest == EXPECTED_TASK_DEFINITIONS
    assert observed_taskset == EXPECTED_TASK_DEFINITIONS


def test_03_padayon_source_snapshot_is_frozen_in_taskset_record() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    snap = taskset["padayon_source_snapshot"]

    assert snap["repository"] == "Baelfyre/Padayon"
    assert snap["sha"] == "03d1ffd4d1dea512230da5628741ae919d70e7ef"
    assert snap["tree"] == "733cb7ebb50d726b33896e8dd7e6a70030d68b79"
    assert "implementation-phase-prompts/orchestra/CURRENT_PROGRESS.json" in snap["primary_sources"]
    assert "implementation-phase-prompts/orchestra/CURRENT_PROGRESS.md" in snap["primary_sources"]
    assert any("115" in src for src in snap["supplemental_sources"])

    subject = taskset["benchmark_subject"]
    assert subject["repository"] == "Baelfyre/Orchestra"
    assert subject["sha"] == "d95f677dbf23ab79c4698c26645ea30cea9b3019"
    assert subject["tree"] == "ceab55bd512ea6fde4e8e76877cbb7006d18500e"


def test_04_b3_plan_only_schedules_30_entries_in_10_paired_blocks(tmp_path: Path) -> None:
    manifest = _load(MANIFEST_PATH)
    output_dir = tmp_path / "plan-test"
    impossible_executor = ["python", "THIS_FILE_MUST_NEVER_BE_EXECUTED_IN_PLAN_ONLY_MODE.py"]

    assert runner.run(MANIFEST_PATH, impossible_executor, output_dir, plan_only=True) == 0
    plan = _load(output_dir / "plan.json")

    assert len(plan["entries"]) == 30

    expected_modes = {"DEFAULT", "CAVEMAN", "MURMURS"}
    blocks: dict[tuple[str, int], set[str]] = {}
    for entry in plan["entries"]:
        key = (entry["task_id"], entry["repetition_index"])
        blocks.setdefault(key, set()).add(entry["arm"]["communication_mode"])
        assert entry["arm"]["topology_class"] == "FIXED_DETERMINISTIC"

    assert len(blocks) == 10
    assert all(block_modes == expected_modes for block_modes in blocks.values())


def test_05_task_prompt_digest_is_identical_across_arms_for_same_task() -> None:
    manifest = _load(MANIFEST_PATH)
    taskset = _load(TASKSET_RECORD_PATH)

    for task_m, task_t in zip(manifest["tasks"], taskset["tasks"]):
        assert task_m["task_id"] == task_t["task_id"]
        assert task_m["task_prompt_digest"] == task_t["task_prompt_digest"]

        prompt_str = task_m["task_payload"]["prompt"]
        computed_prompt_digest = runner.digest_json(prompt_str)
        assert computed_prompt_digest == task_m["task_prompt_digest"]


def test_06_preseeded_pass_flags_prohibited_in_task_payloads() -> None:
    manifest = _load(MANIFEST_PATH)
    taskset = _load(TASKSET_RECORD_PATH)

    for task in manifest["tasks"]:
        payload = task["task_payload"]
        assert "task_completed" not in payload
        assert "validation_passed" not in payload
        assert "governance_valid" not in payload

    for task in taskset["tasks"]:
        payload = task.get("payload", {})
        assert payload.get("task_completed") is not True
        assert payload.get("validation_passed") is not True
        assert payload.get("governance_valid") is not True


def test_07_task_validator_deterministic_positive_conformance() -> None:
    taskset = _load(TASKSET_RECORD_PATH)

    for task in taskset["tasks"]:
        val_contract = task["validation_contract"]
        expected_resp = task["expected_response"]

        # Formatted string response
        resp_str = json.dumps(expected_resp)
        outcome, quality, safety = validator.validate_calibration_task_response(resp_str, val_contract)

        assert outcome["status"] == "PASS"
        assert outcome["task_completed"] is True
        assert outcome["validation_passed"] is True
        assert outcome["governance_valid"] is True
        assert quality["requirements_satisfied"] == 1
        assert quality["requirements_missed"] == 0
        assert quality["validation_failures"] == 0
        assert all(v is False for v in safety.values())

        # Dict response
        outcome_d, quality_d, safety_d = validator.validate_calibration_task_response(expected_resp, val_contract)
        assert outcome_d["status"] == "PASS"


def test_08_validator_negative_malformed_json_fails_closed() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    val_contract = taskset["tasks"][0]["validation_contract"]

    # Not valid JSON
    outcome, quality, _ = validator.validate_calibration_task_response("NOT_JSON_<<<>>>", val_contract)
    assert outcome["status"] == "FAIL"
    assert outcome["task_completed"] is False
    assert outcome["validation_passed"] is False

    # Markdown fenced JSON (strictly rejected by specification)
    fenced = "```json\n" + json.dumps(taskset["tasks"][0]["expected_response"]) + "\n```"
    outcome_f, quality_f, _ = validator.validate_calibration_task_response(fenced, val_contract)
    assert outcome_f["status"] == "FAIL"
    assert outcome_f["task_completed"] is False

    # None response
    outcome_n, _, _ = validator.validate_calibration_task_response(None, val_contract)
    assert outcome_n["status"] == "FAIL"
    assert outcome_n["task_completed"] is False


def test_09_validator_negative_missing_required_key_fails() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    val_contract = taskset["tasks"][0]["validation_contract"]
    expected_resp = copy.deepcopy(taskset["tasks"][0]["expected_response"])

    del expected_resp["disposition"]
    outcome, quality, _ = validator.validate_calibration_task_response(expected_resp, val_contract)

    assert outcome["status"] == "FAIL"
    assert outcome["task_completed"] is False
    assert outcome["validation_passed"] is False


def test_10_validator_negative_wrong_value_fails() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    val_contract = taskset["tasks"][0]["validation_contract"]
    expected_resp = copy.deepcopy(taskset["tasks"][0]["expected_response"])

    expected_resp["negotiated_schema_version"] = "9.9.9"
    outcome, quality, _ = validator.validate_calibration_task_response(expected_resp, val_contract)

    assert outcome["status"] == "FAIL"
    assert outcome["task_completed"] is True
    assert outcome["validation_passed"] is False
    assert outcome["governance_valid"] is True


def test_11_validator_negative_authority_expansion_fails_governance() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    val_contract = taskset["tasks"][0]["validation_contract"]
    expected_resp = copy.deepcopy(taskset["tasks"][0]["expected_response"])

    expected_resp["authority_expansion"] = True
    outcome, quality, safety = validator.validate_calibration_task_response(expected_resp, val_contract)

    assert outcome["status"] == "FAIL"
    assert outcome["task_completed"] is True
    assert outcome["governance_valid"] is False
    assert safety["authority_expansion"] is True


def test_12_model_self_reporting_pass_cannot_bypass_validator() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    task = taskset["tasks"][0]
    val_contract = task["validation_contract"]

    # Model returns self-reported pass flags but wrong answer
    fake_model_resp = {
        "task_id": "b3-cal-padayon-r5-capability-manifest",
        "task_completed": True,
        "validation_passed": True,
        "governance_valid": True,
        "disposition": "COMPATIBLE",
        "negotiated_schema_version": "WRONG_VERSION_0.0.1",
        "matched_required_capabilities": [],
        "missing_required_capabilities": [],
        "missing_optional_capabilities": [],
        "authority_expansion": False
    }

    outcome, quality, _ = validator.validate_calibration_task_response(fake_model_resp, val_contract)
    assert outcome["status"] == "FAIL"
    assert outcome["validation_passed"] is False


def test_13_executor_evaluates_task_outcome_via_response_validator() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    task = taskset["tasks"][0]

    req = {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "b3-cal-test",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": "req-val-001",
        "task_id": task["task_id"],
        "task_class": task["task_class"],
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": "default",
            "topology_candidate_id": "fixed",
            "topology_class": "FIXED_DETERMINISTIC",
            "topology_digest": "1" * 64,
            "communication_mode": "DEFAULT",
        },
        "control_identity": {
            "orchestra_revision": "d95f677dbf23ab79c4698c26645ea30cea9b3019",
            "repository_revision": "test",
            "starting_state_digest": task["starting_state_digest"],
            "task_prompt_digest": task["task_prompt_digest"],
            "system_instruction_digest": "1" * 64,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": None,
            "temperature": 0.0,
            "tool_access_digest": "1" * 64,
            "specialist_set_digest": "1" * 64,
            "required_specialist_set_digest": "1" * 64,
            "authority_digest": "1" * 64,
            "governance_digest": "1" * 64,
            "validation_contract_digest": task["validation_contract_digest"],
            "environment_digest": "1" * 64,
            "retry_policy_digest": "1" * 64,
            "resource_budget_digest": "1" * 64,
        },
        "task_payload": {
            "synthetic": True,
            "execution_allowed": False,
            "prompt": task["prompt"],
            "validation_contract": task["validation_contract"],
            "raw_host_output": {
                "status": "SUCCESS",
                "model": "gemini-3.7-flash-high",
                "cli_version": "1.1.15",
                "useG1Credits": False,
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "thinking_tokens": 50,
                    "cache_read_tokens": 0,
                    "total_tokens": 1250,
                },
                "response": json.dumps(task["expected_response"]),
            },
        },
        "task_payload_digest": task["task_payload_digest"],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
    }

    res = executor.execute_request(req)
    assert res["outcome"]["status"] == "PASS"
    assert res["outcome"]["task_completed"] is True
    assert res["outcome"]["validation_passed"] is True
    assert res["outcome"]["governance_valid"] is True


def test_14_taskset_aggregate_digest_is_stable() -> None:
    taskset = _load(TASKSET_RECORD_PATH)
    assert taskset["taskset_aggregate_digest"] == "fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8"

    recomputed = runner.digest_json(taskset["tasks"])
    assert recomputed == taskset["taskset_aggregate_digest"]


def test_15_b3_plan_only_cannot_create_token_savings_or_benefit_evidence(tmp_path: Path) -> None:
    output = tmp_path / "plan-only"

    assert runner.run(MANIFEST_PATH, ["never-executed"], output, plan_only=True) == 0
    plan = _load(output / "plan.json")

    assert plan["stage"] == "CALIBRATION"
    assert plan["experiment_kind"] == "MURMURS_ISOLATED"
    assert "conclusion" not in plan
    assert "run_evidence_digests" not in plan
    assert not (output / "experiment.json").exists()
    assert not (output / "run-index.json").exists()
