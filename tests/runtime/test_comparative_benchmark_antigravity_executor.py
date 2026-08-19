from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_PATH = ROOT / "scripts" / "antigravity_benchmark_executor.py"
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
SCHEMA_DIR = ROOT / "machine" / "schemas"

SPEC_EXEC = importlib.util.spec_from_file_location("antigravity_benchmark_executor", EXECUTOR_PATH)
assert SPEC_EXEC is not None and SPEC_EXEC.loader is not None
executor = importlib.util.module_from_spec(SPEC_EXEC)
SPEC_EXEC.loader.exec_module(executor)

SPEC_RUNNER = importlib.util.spec_from_file_location("comparative_benchmark_runner", RUNNER_PATH)
assert SPEC_RUNNER is not None and SPEC_RUNNER.loader is not None
runner = importlib.util.module_from_spec(SPEC_RUNNER)
SPEC_RUNNER.loader.exec_module(runner)

DIGEST = "1" * 64


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validate_result_schema(value: dict[str, Any]) -> None:
    schema = _load_schema("comparative-benchmark-executor-result.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)


def _base_request(request_id: str = "req-001", **task_payload_kwargs: Any) -> dict[str, Any]:
    return {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-calibration",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": request_id,
        "task_id": "task-01",
        "task_class": "SINGLE_DOMAIN",
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": "default",
            "topology_candidate_id": "fixed-topology",
            "topology_class": "FIXED_DETERMINISTIC",
            "topology_digest": DIGEST,
            "communication_mode": "DEFAULT",
        },
        "control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "task_payload": dict(task_payload_kwargs),
        "task_payload_digest": DIGEST,
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
    }


def _mock_host_envelope(
    status: str = "SUCCESS",
    input_tokens: int = 1500,
    output_tokens: int = 400,
    thinking_tokens: int = 120,
    cache_read_tokens: int = 300,
    total_tokens: int = 2320,
    model: str = "gemini-3.7-flash-high",
    cli_version: str = "1.1.14",
    task_completed: bool = True,
    validation_passed: bool = True,
    governance_valid: bool = True,
    response: str | None = "Sample structured response payload",
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "status": status,
        "model": model,
        "cli_version": cli_version,
        "useG1Credits": False,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "cache_read_tokens": cache_read_tokens,
            "total_tokens": total_tokens,
        },
        "task_completed": task_completed,
        "validation_passed": validation_passed,
        "governance_valid": governance_valid,
    }
    if response is not None:
        envelope["response"] = response
    return envelope


def _create_mock_settings(tmp_path: Path, use_g1_credits: Any = False) -> Path:
    settings_file = tmp_path / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if use_g1_credits is not None:
        data["useG1Credits"] = use_g1_credits
    settings_file.write_text(json.dumps(data), encoding="utf-8")
    return settings_file


def test_01_valid_antigravity_usage_maps_to_host_reported_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(input_tokens=1000, output_tokens=250))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["source"] == "HOST_REPORTED"
    assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert res["tokens"]["input_tokens"] == 1000
    assert res["tokens"]["output_tokens"] == 250


def test_02_thinking_tokens_maps_to_reasoning_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(thinking_tokens=180))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["reasoning_tokens"] == 180


def test_03_cache_read_tokens_maps_to_cached_input_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(cache_read_tokens=450))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["cached_input_tokens"] == 450


def test_04_total_tokens_remains_raw_evidence_only() -> None:
    envelope = _mock_host_envelope(total_tokens=9999)
    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["raw_evidence"]["total_tokens"] == 9999
    assert res["raw_evidence"]["outer_envelope"]["usage"]["total_tokens"] == 9999
    assert res["tokens"]["fresh_billable_tokens"] is None


def test_05_fresh_billable_tokens_remains_null() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(input_tokens=500, output_tokens=100))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["fresh_billable_tokens"] is None


def test_06_provider_cost_remains_unavailable() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["cost"]["source"] == "UNAVAILABLE"
    assert res["cost"]["amount"] is None
    assert res["cost"]["currency"] is None


def test_07_missing_usage_becomes_invalid_run_measurement_capture_failure() -> None:
    envelope = _mock_host_envelope()
    del envelope["usage"]
    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert res["tokens"]["source"] == "UNAVAILABLE"


def test_08_missing_input_or_output_counters_becomes_invalid_run() -> None:
    # Missing input_tokens
    envelope_no_input = _mock_host_envelope()
    del envelope_no_input["usage"]["input_tokens"]
    req1 = _base_request(raw_host_output=envelope_no_input)
    res1 = executor.execute_request(req1)
    _validate_result_schema(res1)
    assert res1["outcome"]["status"] == "INVALID_RUN"
    assert res1["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Missing output_tokens
    envelope_no_output = _mock_host_envelope()
    del envelope_no_output["usage"]["output_tokens"]
    req2 = _base_request(raw_host_output=envelope_no_output)
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_09_malformed_outer_json_becomes_invalid_run() -> None:
    req = _base_request(raw_host_output="NOT_VALID_JSON_<<<>>>")
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_10_antigravity_success_does_not_automatically_set_task_outcome_pass() -> None:
    # Host is SUCCESS, but validation_passed is False
    envelope_val_fail = _mock_host_envelope(
        status="SUCCESS",
        task_completed=True,
        validation_passed=False,
        governance_valid=True,
    )
    req = _base_request(raw_host_output=envelope_val_fail)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "FAIL"
    assert res["outcome"]["invalid_reason"] is None
    assert res["outcome"]["validation_passed"] is False
    assert res["tokens"]["source"] == "HOST_REPORTED"

    # Host is SUCCESS, but task_completed is False
    envelope_inc = _mock_host_envelope(
        status="SUCCESS",
        task_completed=False,
        validation_passed=True,
        governance_valid=True,
    )
    res2 = executor.execute_request(_base_request(raw_host_output=envelope_inc))
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "FAIL"
    assert res2["outcome"]["task_completed"] is False


def test_11_host_success_without_independent_evidence_cannot_produce_pass() -> None:
    # Regression test for Objective 5: Host envelope has status=SUCCESS and valid tokens,
    # but no task_completed, validation_passed, or governance_valid fields.
    # The executor must NOT default missing fields to True or manufacture benchmark PASS.
    bare_envelope = {
        "status": "SUCCESS",
        "usage": {
            "input_tokens": 1200,
            "output_tokens": 350,
            "thinking_tokens": 50,
            "cache_read_tokens": 100,
            "total_tokens": 1700,
        },
        "response": "Completed the request successfully.",
    }
    req = _base_request(raw_host_output=bare_envelope)
    # Ensure task_payload contains no manufactured outcome flags
    req["task_payload"].pop("task_completed", None)
    req["task_payload"].pop("validation_passed", None)
    req["task_payload"].pop("governance_valid", None)

    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "FAIL"
    assert res["outcome"]["invalid_reason"] is None
    assert res["outcome"]["task_completed"] is False
    assert res["outcome"]["validation_passed"] is False
    assert res["outcome"]["governance_valid"] is False
    assert res["tokens"]["source"] == "HOST_REPORTED"
    assert res["tokens"]["input_tokens"] == 1200
    assert res["tokens"]["output_tokens"] == 350


def test_12_counter_identity_is_deterministic() -> None:
    cid1 = executor.compute_counter_id()
    cid2 = executor.compute_counter_id("1.1.14", "gemini-3.7-flash-high", "json-usage")
    assert cid1 == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert cid1 == cid2 == executor.DEFAULT_COUNTER_ID


def test_13_changed_cli_or_model_identity_changes_counter_identity() -> None:
    base_cid = executor.DEFAULT_COUNTER_ID

    cid_cli_change = executor.compute_counter_id(cli_version="1.2.0")
    assert cid_cli_change != base_cid
    assert cid_cli_change == "antigravity-cli-1.2.0:json-usage:gemini-3.7-flash-high"

    cid_model_change = executor.compute_counter_id(model="gemini-2.5-pro")
    assert cid_model_change != base_cid
    assert cid_model_change == "antigravity-cli-1.1.14:json-usage:gemini-2.5-pro"

    # And executing with mismatched host cli_version fails closed
    envelope_drift = _mock_host_envelope(cli_version="1.2.0")
    res = executor.execute_request(_base_request(raw_host_output=envelope_drift))
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_14_no_live_antigravity_invocation_occurs_during_tests() -> None:
    called = []

    def fake_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        called.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req, runner_fn=fake_runner)
    assert len(called) == 0
    assert res["outcome"]["status"] == "PASS"


def test_15_corrupted_starting_state_fails_closed() -> None:
    req = _base_request(corrupted_starting_state=True, raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"

    # Missing starting state digest in control_identity
    req2 = _base_request(raw_host_output=_mock_host_envelope())
    req2["control_identity"]["starting_state_digest"] = ""
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_16_model_mismatch_fails_closed() -> None:
    # Request control_identity model != pinned model
    req = _base_request(raw_host_output=_mock_host_envelope())
    req["control_identity"]["model"] = "unpinned-model-variant"
    res = executor.execute_request(req)
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Response model != pinned model
    envelope_wrong_model = _mock_host_envelope(model="unpinned-model-variant")
    req2 = _base_request(raw_host_output=envelope_wrong_model)
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_17_live_argv_construction_and_no_stdin_prompt(tmp_path: Path) -> None:
    # Tests Objective 1:
    # Command is: ["agy", "--model", "gemini-3.7-flash-high", "-p", prompt, "--output-format", "json"]
    # Prompt is passed via -p, prompt is not passed on stdin, --no-use-g1-credits is absent.
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    captured_calls: list[dict[str, Any]] = []

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        captured_calls.append({"cmd": cmd, "prompt": prompt})
        envelope = _mock_host_envelope(
            task_completed=True,
            validation_passed=True,
            governance_valid=True,
        )
        return (0, json.dumps(envelope), "")

    test_prompt = "Refactor the authentication middleware."
    req = _base_request(prompt=test_prompt)
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert len(captured_calls) == 1
    call_info = captured_calls[0]
    cmd = call_info["cmd"]

    expected_cmd = [
        "agy",
        "--model",
        "gemini-3.7-flash-high",
        "-p",
        test_prompt,
        "--output-format",
        "json",
    ]
    assert cmd == expected_cmd
    assert "-p" in cmd
    assert cmd[cmd.index("-p") + 1] == test_prompt
    assert "--no-use-g1-credits" not in cmd
    assert res["outcome"]["status"] == "PASS"


def test_18_preflight_accepts_exact_cli_version_1_1_14(tmp_path: Path) -> None:
    # Tests Objective 2: Preflight accepts exact version 1.1.14
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        assert cmd == ["agy", "--version"]
        return (0, "antigravity-cli 1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["cli_version"] == "1.1.14"


def test_19_preflight_fails_closed_on_different_cli_version(tmp_path: Path) -> None:
    # Tests Objective 2: CLI version mismatch fails closed before model invocation
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.2.0\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "1.2.0" in str(res["raw_evidence"]["detail"])


def test_20_preflight_accepts_explicit_use_g1_credits_false(tmp_path: Path) -> None:
    # Tests Objective 2: useG1Credits: false in settings.json passes preflight
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"


def test_21_preflight_fails_closed_on_use_g1_credits_true(tmp_path: Path) -> None:
    # Tests Objective 2: useG1Credits: true fails closed before model invocation
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=True)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "useG1Credits" in str(res["raw_evidence"]["detail"])


def test_22_preflight_fails_closed_on_malformed_or_missing_settings(tmp_path: Path) -> None:
    # Tests Objective 2: Missing settings file, malformed JSON, and missing useG1Credits key
    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.14\n", "")

    # 1. Missing settings file
    missing_settings = tmp_path / "non_existent_settings.json"
    req1 = _base_request(prompt="Sample prompt")
    res1 = executor.execute_request(
        req1,
        settings_path=missing_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res1)
    assert res1["outcome"]["status"] == "INVALID_RUN"
    assert res1["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # 2. Malformed settings file
    malformed_settings = tmp_path / "bad_settings.json"
    malformed_settings.write_text("{not-valid-json", encoding="utf-8")
    req2 = _base_request(prompt="Sample prompt")
    res2 = executor.execute_request(
        req2,
        settings_path=malformed_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # 3. Missing useG1Credits key (e.g. empty object)
    missing_key_settings = _create_mock_settings(tmp_path / "sub", use_g1_credits=None)
    req3 = _base_request(prompt="Sample prompt")
    res3 = executor.execute_request(
        req3,
        settings_path=missing_key_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res3)
    assert res3["outcome"]["status"] == "INVALID_RUN"
    assert res3["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_23_provenance_semantics_explicitly_preserved() -> None:
    # Tests Objective 3: Explicit provenance for CLI version, model, usage, and counter ID
    envelope = _mock_host_envelope()
    # Remove model and cli_version from envelope to ensure they are not claimed to be host-returned
    del envelope["model"]
    del envelope["cli_version"]

    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["cli_version_provenance"]["source"] == "PREFLIGHT_COMMAND"
    assert raw_ev["cli_version_provenance"]["value"] == "1.1.14"
    assert raw_ev["model_provenance"]["source"] == "PINNED_COMMAND_ARGUMENT"
    assert raw_ev["model_provenance"]["value"] == "gemini-3.7-flash-high"
    assert raw_ev["usage_provenance"]["source"] == "HOST_REPORTED_JSON_USAGE"
    assert raw_ev["counter_id_provenance"]["provenance"] == "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE"
    assert raw_ev["counter_id_provenance"]["vendor_assigned_claim"] is False
    assert raw_ev["counter_id_provenance"]["identifier"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"


def test_24_response_bytes_captured_from_response_field() -> None:
    # Tests Objective 6: Observed Antigravity envelope uses 'response' field
    # user_visible_bytes is calculated from 'response' field, not zero
    response_text = "Here is the refactored code and summary."
    envelope = _mock_host_envelope(response=response_text)
    envelope.pop("content", None)

    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    expected_bytes = len(response_text.encode("utf-8"))
    assert res["communication"]["user_visible_bytes"] == expected_bytes
    assert res["communication"]["user_visible_bytes"] > 0


def test_25_runner_integration_with_antigravity_executor(tmp_path: Path) -> None:
    # Test runner execution with scripts/antigravity_benchmark_executor.py
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-1-integration",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 12345,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "arms": [
            {"arm_id": "default", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "DEFAULT"},
            {"arm_id": "caveman", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "CAVEMAN"},
            {"arm_id": "murmurs", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "MURMURS"},
        ],
        "tasks": [
            {
                "task_id": "task-01",
                "task_class": "SINGLE_DOMAIN",
                "starting_state_digest": DIGEST,
                "task_prompt_digest": DIGEST,
                "task_payload": {
                    "raw_host_output": _mock_host_envelope(input_tokens=1200, output_tokens=300),
                },
            }
        ],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    output_dir = tmp_path / "bench-out"

    cmd = [sys.executable, str(EXECUTOR_PATH)]
    rc = runner.run(manifest_path, cmd, output_dir)
    assert rc == 0

    plan = json.loads((output_dir / "plan.json").read_text(encoding="utf-8"))
    assert len(plan["entries"]) == 3

    run_files = sorted((output_dir / "runs").glob("*.json"))
    assert len(run_files) == 3

    for r_file in run_files:
        run_record = json.loads(r_file.read_text(encoding="utf-8"))
        schema = _load_schema("comparative-benchmark-run.schema.json")
        jsonschema.Draft202012Validator(schema).validate(run_record)
        assert run_record["tokens"]["source"] == "HOST_REPORTED"
        assert run_record["tokens"]["counter_id"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
        assert run_record["tokens"]["fresh_billable_tokens"] is None
        assert run_record["outcome"]["status"] == "PASS"

    experiment = json.loads((output_dir / "experiment.json").read_text(encoding="utf-8"))
    exp_schema = _load_schema("comparative-benchmark-experiment.schema.json")
    jsonschema.Draft202012Validator(exp_schema).validate(experiment)
    assert experiment["status"] == "COMPLETE"
    assert experiment["conclusion"] == "MEASUREMENT_CALIBRATED"
