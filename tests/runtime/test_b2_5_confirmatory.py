from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.a5_topology_benchmark_executor import digest_json, execute_request, load_envelope
from scripts.b2_5_confirmatory_driver import (
    PilotDriverError,
    exact_executor_command,
    run_session,
    validate_authorization,
)
from scripts.b2_5_confirmatory_preflight import FREEZE_PATH, host_preflight, static_preflight
from scripts.comparative_benchmark_runner import build_plan

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frozen_records() -> tuple[dict, dict, dict, dict]:
    freeze = load(FREEZE_PATH)
    manifest = load(ROOT / freeze["manifest"]["source"])
    plan = load(ROOT / freeze["plan"]["source"])
    taskset = load(ROOT / freeze["task_selection"]["source_task_set"])
    return freeze, manifest, plan, taskset


def authorization(freeze: dict, manifest: dict, plan: dict, taskset: dict) -> dict:
    return {
        "schema_version": "orchestra.b2-5-confirmatory-live-authorization.v1",
        "live_execution_authorized": True,
        "freeze_digest": digest_json(freeze),
        "manifest_digest": digest_json(manifest),
        "plan_digest": digest_json(plan),
        "task_set_digest": taskset["aggregate_digest"],
        "preparation_sha": "a" * 40,
        "preparation_tree": "b" * 40,
        "planned_runs": 40,
        "maximum_underlying_model_calls": 120,
    }


def snapshot() -> dict:
    return {"head": "a" * 40, "tree": "b" * 40, "status": ""}


def fixture_invoke(tmp_path: Path, status: str = "PASS", tamper: bool = False):
    freeze, _, _, _ = frozen_records()
    _, envelope, envelope_digest = load_envelope(ROOT / freeze["topology"]["eligibility_envelope"])
    workspace = tmp_path / "fixture-workspace"
    workspace.mkdir(exist_ok=True)

    def fake_git(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="true\n", stderr="")

    def fake_version(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="codex-cli 0.148.0\n", stderr="")

    def invoke(command, request, timeout):
        expected = request["task_payload"]["validation_contract"]["expected_response"]
        prompts: list[str] = []

        def fake_call(**kwargs):
            prompts.append(kwargs["prompt"])
            response = json.dumps(expected, separators=(",", ":")) if "fixed benchmark finalizer" in kwargs["prompt"] else f"advisory-{len(prompts)}"
            usage = {"input_tokens": 90, "cached_input_tokens": 10, "output_tokens": 10, "reasoning_output_tokens": 2}
            return {"response": response, "usage": usage, "turn_completed_usage": dict(usage), "total_tokens": 100, "elapsed_ms": 1, "agent_message_count": 1}

        result = execute_request(
            request,
            envelope=envelope,
            eligibility_digest=envelope_digest,
            expected_cli_version="0.148.0",
            model="gpt-5.6-sol",
            reasoning_effort="medium",
            command_prefix=("node", "codex.js"),
            workspace=workspace,
            call_timeout_seconds=timeout,
            per_run_total_token_ceiling=75000,
            call_runner=fake_call,
            version_runner=fake_version,
            git_runner=fake_git,
        )
        if status == "INVALID_RUN":
            result["outcome"] = {"status": "INVALID_RUN", "invalid_reason": "MEASUREMENT_CAPTURE_FAILURE", "task_completed": False, "validation_passed": False, "governance_valid": False}
        elif status == "FAIL":
            result["outcome"] = {"status": "FAIL", "invalid_reason": None, "task_completed": True, "validation_passed": False, "governance_valid": True}
        if tamper:
            result["raw_evidence"]["calls"][0]["response_utf8_bytes"] += 1
        return result, None

    return invoke


def test_static_preflight_freezes_exact_held_out_plan_without_calls():
    freeze, manifest, plan, taskset = frozen_records()
    result = static_preflight()
    assert build_plan(manifest) == plan
    assert len(taskset["tasks"]) == 10
    assert len(plan["entries"]) == 10 * 2 * 2 == 40
    assert freeze["resource_freeze"]["maximum_underlying_model_calls"] == 120
    assert freeze["resource_freeze"]["automatic_retry"] is False
    assert result["codex_exec_invoked"] is False
    assert result["live_model_calls"] == 0


def test_host_preflight_invokes_version_only():
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="codex-cli 0.148.0\n", stderr="")

    result = host_preflight(static_preflight(), fake_run, lambda freeze: {"fixture": "ZERO_CALL"})
    assert commands and all(command[-1] == "--version" and "exec" not in command for command in commands)
    assert result["codex_exec_invoked"] is False
    assert result["live_model_calls"] == 0


def test_executor_command_uses_corrected_contract():
    freeze, _, _, _ = frozen_records()
    command = exact_executor_command(freeze)
    assert "--codex-command-prefix-json" in command
    assert "--workspace-dir" in command
    assert "--codex-prefix-json" not in command
    assert "--workspace" not in command


def test_authorization_is_required_before_executor_invocation(tmp_path: Path):
    freeze, manifest, plan, taskset = frozen_records()
    calls = 0

    def forbidden(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("executor must not run")

    authorization_record = authorization(freeze, manifest, plan, taskset)
    authorization_record["live_execution_authorized"] = False
    with pytest.raises(PilotDriverError, match="not authorized"):
        run_session(authorization_record, tmp_path / "blocked", invoke=forbidden, snapshot=snapshot, preflight=lambda: {})
    assert calls == 0


def test_fixture_driver_completes_all_forty_slots(tmp_path: Path):
    freeze, manifest, plan, taskset = frozen_records()
    output = tmp_path / "complete"
    summary = run_session(authorization(freeze, manifest, plan, taskset), output, invoke=fixture_invoke(tmp_path), snapshot=snapshot, preflight=lambda: {})
    assert summary["status"] == "COMPLETE"
    assert summary["completed_runs"] == 40
    assert summary["live_model_calls_consumed"] == 120
    assert len(list((output / "requests").glob("*.json"))) == 40
    assert len(list((output / "executor-results").glob("*.json"))) == 40
    assert len(list((output / "runs").glob("*.json"))) == 40
    assert (output / "run-index.json").is_file()
    assert (output / "experiment.json").is_file()
    assert (output / "session-summary.json").is_file()


@pytest.mark.parametrize(("status", "expected"), [("INVALID_RUN", "INVALID_RUN"), ("FAIL", "FAIL")])
def test_driver_stops_after_first_failed_slot(tmp_path: Path, status: str, expected: str):
    freeze, manifest, plan, taskset = frozen_records()
    summary = run_session(authorization(freeze, manifest, plan, taskset), tmp_path / status, invoke=fixture_invoke(tmp_path, status=status), snapshot=snapshot, preflight=lambda: {})
    assert summary["status"] == "STOPPED"
    assert summary["stop_reason"] == expected
    assert summary["completed_runs"] == 1
    assert summary["live_model_calls_consumed"] == 3


def test_driver_rejects_evidence_mismatch(tmp_path: Path):
    freeze, manifest, plan, taskset = frozen_records()
    summary = run_session(authorization(freeze, manifest, plan, taskset), tmp_path / "tampered", invoke=fixture_invoke(tmp_path, tamper=True), snapshot=snapshot, preflight=lambda: {})
    assert summary["status"] == "STOPPED"
    assert summary["stop_reason"].startswith("EVIDENCE_OR_VALIDATOR_FAILURE:")
    assert summary["completed_runs"] == 0


def test_authorization_digest_mismatch_fails_closed():
    freeze, manifest, plan, taskset = frozen_records()
    record = authorization(freeze, manifest, plan, taskset)
    record["task_set_digest"] = "0" * 64
    with pytest.raises(PilotDriverError, match="task_set_digest"):
        validate_authorization(record, freeze, manifest, plan, taskset)
