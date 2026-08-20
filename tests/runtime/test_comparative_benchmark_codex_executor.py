from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex_benchmark_executor.py"
TASKSET_PATH = ROOT / "machine" / "benchmarking" / "b3-calibration-task-set.v1.json"
RESULT_SCHEMA_PATH = ROOT / "machine" / "schemas" / "comparative-benchmark-executor-result.schema.json"

spec = importlib.util.spec_from_file_location("codex_benchmark_executor", MODULE_PATH)
assert spec and spec.loader
codex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codex)

MODEL = "codex-test-model"
EFFORT = "medium"
CLI_VERSION = "9.8.7"
ZERO = "0" * 64


def _task() -> dict:
    payload = json.loads(TASKSET_PATH.read_text(encoding="utf-8"))
    return copy.deepcopy(payload["tasks"][0])


def _request(*, communication_mode: str = "DEFAULT") -> dict:
    task = _task()
    return {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "codex-readiness-test",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": f"codex-readiness-{communication_mode.lower()}",
        "task_id": task["task_id"],
        "task_class": task["task_class"],
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": communication_mode,
            "topology_candidate_id": "fixed-deterministic",
            "topology_class": "FIXED_DETERMINISTIC",
            "topology_digest": ZERO,
            "communication_mode": communication_mode,
        },
        "control_identity": {
            "orchestra_revision": codex.BENCHMARK_SUBJECT_SHA,
            "repository_revision": "SYNTHETIC_PLAN_ONLY_NO_WORKLOAD_REPOSITORY",
            "starting_state_digest": task["starting_state_digest"],
            "task_prompt_digest": task["task_prompt_digest"],
            "system_instruction_digest": ZERO,
            "provider": codex.PROVIDER_ID,
            "model": MODEL,
            "model_revision": None,
            "reasoning_setting": EFFORT,
            "temperature": None,
            "tool_access_digest": ZERO,
            "specialist_set_digest": ZERO,
            "required_specialist_set_digest": ZERO,
            "authority_digest": ZERO,
            "governance_digest": ZERO,
            "validation_contract_digest": task["validation_contract_digest"],
            "environment_digest": ZERO,
            "retry_policy_digest": ZERO,
            "resource_budget_digest": ZERO,
        },
        "task_payload": task,
        "task_payload_digest": task["task_payload_digest"],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
    }


def _jsonl(response: str | None = None, *, usage: dict | None = None) -> str:
    if response is None:
        response = json.dumps(_task()["expected_response"], sort_keys=True, separators=(",", ":"))
    if usage is None:
        usage = {
            "input_tokens": 123,
            "cached_input_tokens": 23,
            "output_tokens": 45,
            "reasoning_output_tokens": 17,
        }
    events = [
        {"type": "thread.started", "thread_id": "test-thread"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "item-1", "type": "agent_message", "text": response}},
        {"type": "turn.completed", "usage": usage},
    ]
    return "\n".join(json.dumps(event, sort_keys=True) for event in events)


def _never_run(*args, **kwargs):
    raise AssertionError("live Codex process must not run in deterministic readiness tests")


def _execute(tmp_path: Path, request: dict | None = None, raw_jsonl: str | None = None, **kwargs):
    request = request or _request()
    return codex.execute_request(
        request,
        expected_cli_version=kwargs.pop("expected_cli_version", CLI_VERSION),
        expected_model=kwargs.pop("expected_model", MODEL),
        expected_reasoning_effort=kwargs.pop("expected_reasoning_effort", EFFORT),
        workspace_dir=kwargs.pop("workspace_dir", tmp_path),
        run_command=_never_run,
        version_runner=_never_run,
        raw_jsonl=_jsonl() if raw_jsonl is None else raw_jsonl,
        observed_cli_version=kwargs.pop("observed_cli_version", CLI_VERSION),
        **kwargs,
    )


def test_valid_exact_response_passes_and_maps_host_usage(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    assert result["outcome"] == {
        "status": "PASS",
        "invalid_reason": None,
        "task_completed": True,
        "validation_passed": True,
        "governance_valid": True,
    }
    assert result["tokens"]["source"] == "HOST_REPORTED"
    assert result["tokens"]["input_tokens"] == 123
    assert result["tokens"]["cached_input_tokens"] == 23
    assert result["tokens"]["output_tokens"] == 45
    assert result["tokens"]["reasoning_tokens"] == 17
    assert result["tokens"]["fresh_billable_tokens"] is None
    assert result["tokens"]["counter_id"] == "codex-cli-9.8.7:jsonl-usage:codex-test-model:medium"
    assert result["cost"] == {"source": "UNAVAILABLE", "amount": None, "currency": None}
    assert result["raw_evidence"]["benchmark_subject"]["sha"] == codex.BENCHMARK_SUBJECT_SHA
    assert result["raw_evidence"]["common_measurement_core_baseline"]["sha"] == codex.COMMON_MEASUREMENT_CORE_SHA


def test_valid_result_matches_existing_executor_result_schema(tmp_path: Path) -> None:
    schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_execute(tmp_path))


def test_wrong_semantic_answer_is_task_fail_not_invalid_run(tmp_path: Path) -> None:
    wrong = copy.deepcopy(_task()["expected_response"])
    wrong["disposition"] = "WRONG"
    result = _execute(tmp_path, raw_jsonl=_jsonl(json.dumps(wrong, sort_keys=True, separators=(",", ":"))))
    assert result["outcome"]["status"] == "FAIL"
    assert result["outcome"]["task_completed"] is True
    assert result["outcome"]["validation_passed"] is False
    assert result["outcome"]["invalid_reason"] is None


def test_model_self_reported_pass_flags_cannot_bypass_validator(tmp_path: Path) -> None:
    forged = copy.deepcopy(_task()["expected_response"])
    forged["disposition"] = "WRONG"
    forged["task_completed"] = True
    forged["validation_passed"] = True
    forged["governance_valid"] = True
    result = _execute(tmp_path, raw_jsonl=_jsonl(json.dumps(forged, sort_keys=True, separators=(",", ":"))))
    assert result["outcome"]["status"] == "FAIL"
    assert result["outcome"]["validation_passed"] is False


@pytest.mark.parametrize(
    "raw",
    [
        "not-json",
        json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}}),
        "\n".join([json.dumps({"type": "thread.started", "thread_id": "t"}), json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}})]),
        "\n".join([json.dumps({"type": "thread.started", "thread_id": "t"}), json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}})]),
    ],
)
def test_malformed_or_incomplete_jsonl_is_invalid_measurement(tmp_path: Path, raw: str) -> None:
    result = _execute(tmp_path, raw_jsonl=raw)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


@pytest.mark.parametrize("terminal_type", ["turn.failed", "error"])
def test_host_error_events_are_invalid_provider_runs(tmp_path: Path, terminal_type: str) -> None:
    raw = "\n".join([
        json.dumps({"type": "thread.started", "thread_id": "t"}),
        json.dumps({"type": terminal_type, "message": "synthetic failure"}),
    ])
    result = _execute(tmp_path, raw_jsonl=raw)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "PROVIDER_OUTAGE"


@pytest.mark.parametrize(
    "usage",
    [
        {},
        {"input_tokens": -1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0},
        {"input_tokens": 1, "cached_input_tokens": "0", "output_tokens": 1, "reasoning_output_tokens": 0},
        {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": True, "reasoning_output_tokens": 0},
    ],
)
def test_missing_or_malformed_usage_is_invalid_measurement(tmp_path: Path, usage: dict) -> None:
    result = _execute(tmp_path, raw_jsonl=_jsonl(usage=usage))
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_missing_final_agent_message_is_invalid_measurement(tmp_path: Path) -> None:
    raw = "\n".join([
        json.dumps({"type": "thread.started", "thread_id": "t"}),
        json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}}),
    ])
    result = _execute(tmp_path, raw_jsonl=raw)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


@pytest.mark.parametrize("item_type", ["command_execution", "file_change", "mcp_tool_call", "web_search"])
def test_any_tool_event_is_invalid_under_no_tool_baseline(tmp_path: Path, item_type: str) -> None:
    raw = "\n".join([
        json.dumps({"type": "thread.started", "thread_id": "t"}),
        json.dumps({"type": "item.completed", "item": {"type": item_type, "status": "completed"}}),
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(_task()["expected_response"])}}),
        json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}}),
    ])
    result = _execute(tmp_path, raw_jsonl=raw)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_command_is_ephemeral_read_only_and_disables_host_specific_tools(tmp_path: Path) -> None:
    command = codex.build_codex_command(prompt="PROMPT", workspace_dir=tmp_path, model=MODEL, reasoning_effort=EFFORT)
    joined = " ".join(command)
    assert command[:2] == ["codex", "exec"]
    assert "--ephemeral" in command
    assert "--json" in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" in command
    assert "--ignore-rules" in command
    assert command[command.index("--model") + 1] == MODEL
    assert command[command.index("--cd") + 1] == str(tmp_path)
    assert "agents.enabled=false" in command
    assert 'web_search="disabled"' in command
    assert "features.shell_tool=false" in command
    assert f'model_reasoning_effort="{EFFORT}"' in command
    assert "approval_policy=\"never\"" in command
    assert "--output-schema" not in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "--yolo" not in command
    assert "danger-full-access" not in command
    assert "workspace-write" not in command
    assert "full-auto" not in joined


def test_exact_cli_version_mismatch_fails_before_live_invocation(tmp_path: Path) -> None:
    result = _execute(tmp_path, observed_cli_version="9.8.6")
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_model_and_reasoning_mismatch_fail_before_live_invocation(tmp_path: Path) -> None:
    request = _request()
    request["control_identity"]["model"] = "different-model"
    result = _execute(tmp_path, request=request)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"

    request = _request()
    request["control_identity"]["reasoning_setting"] = "high"
    result = _execute(tmp_path, request=request)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_benchmark_subject_identity_cannot_drift(tmp_path: Path) -> None:
    request = _request()
    request["control_identity"]["orchestra_revision"] = "different"
    result = _execute(tmp_path, request=request)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_missing_live_freeze_values_fail_before_host_invocation(tmp_path: Path) -> None:
    result = codex.execute_request(
        _request(),
        expected_cli_version=None,
        expected_model=None,
        expected_reasoning_effort=None,
        workspace_dir=tmp_path,
        run_command=_never_run,
        version_runner=_never_run,
        raw_jsonl=_jsonl(),
        observed_cli_version=CLI_VERSION,
    )
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_invalid_workspace_fails_before_host_invocation(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = codex.execute_request(
        _request(),
        expected_cli_version=CLI_VERSION,
        expected_model=MODEL,
        expected_reasoning_effort=EFFORT,
        workspace_dir=missing,
        run_command=_never_run,
        version_runner=_never_run,
        raw_jsonl=_jsonl(),
        observed_cli_version=CLI_VERSION,
    )
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_parse_cli_version_is_exact_and_fail_closed() -> None:
    assert codex.parse_cli_version("codex-cli 1.2.3") == "1.2.3"
    with pytest.raises(ValueError):
        codex.parse_cli_version("codex unknown")
    with pytest.raises(ValueError):
        codex.parse_cli_version("1.2.3 and 2.0.0")


def test_counter_identity_changes_when_host_surface_changes() -> None:
    base = codex.compute_counter_id("1.2.3", MODEL, "medium")
    assert codex.compute_counter_id("1.2.4", MODEL, "medium") != base
    assert codex.compute_counter_id("1.2.3", "other-model", "medium") != base
    assert codex.compute_counter_id("1.2.3", MODEL, "high") != base
