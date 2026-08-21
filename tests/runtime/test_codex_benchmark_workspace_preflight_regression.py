from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex_benchmark_executor.py"
TASKSET_PATH = ROOT / "machine" / "benchmarking" / "b3-calibration-task-set.v1.json"

spec = importlib.util.spec_from_file_location("codex_benchmark_executor_preflight", MODULE_PATH)
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


def _request() -> dict:
    task = _task()
    return {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "codex-preflight-regression",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": "codex-preflight-regression-default",
        "task_id": task["task_id"],
        "task_class": task["task_class"],
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": "DEFAULT",
            "topology_candidate_id": "fixed-deterministic",
            "topology_class": "FIXED_DETERMINISTIC",
            "topology_digest": ZERO,
            "communication_mode": "DEFAULT",
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


def _never_codex(*args, **kwargs):
    raise AssertionError("Codex process must not run when workspace preflight fails")


def _git_not_worktree(*args, **kwargs):
    return subprocess.CompletedProcess(
        args=args[0],
        returncode=128,
        stdout="",
        stderr="fatal: not a git repository (or any of the parent directories): .git\n",
    )


def _git_worktree(*args, **kwargs):
    return subprocess.CompletedProcess(
        args=args[0],
        returncode=0,
        stdout="true\n",
        stderr="",
    )


def test_live_non_git_workspace_fails_before_codex_process(tmp_path: Path) -> None:
    result = codex.execute_request(
        _request(),
        expected_cli_version=CLI_VERSION,
        expected_model=MODEL,
        expected_reasoning_effort=EFFORT,
        workspace_dir=tmp_path,
        run_command=_never_codex,
        version_runner=_never_codex,
        git_runner=_git_not_worktree,
        raw_jsonl=None,
        observed_cli_version=CLI_VERSION,
    )

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"
    preflight = result["raw_evidence"]["workspace_git_preflight"]
    assert preflight["returncode"] == 128
    assert preflight["is_inside_work_tree"] is False


def test_observed_trusted_directory_rejection_is_not_provider_outage() -> None:
    reason = codex.classify_nonzero_codex_exit(
        "",
        "Not inside a trusted directory and --skip-git-repo-check was not specified.\n",
    )
    assert reason == "CORRUPTED_STARTING_STATE"


def test_unstructured_nonzero_exit_defaults_to_infrastructure_outage() -> None:
    assert codex.classify_nonzero_codex_exit("", "unexpected local process failure") == "INFRASTRUCTURE_OUTAGE"


def test_configuration_rejection_is_measurement_capture_failure() -> None:
    assert codex.classify_nonzero_codex_exit("", "error: unexpected argument '--bad-flag'") == "MEASUREMENT_CAPTURE_FAILURE"


def test_structured_host_error_remains_provider_outage() -> None:
    stdout = json.dumps({"type": "turn.failed", "message": "synthetic provider failure"})
    assert codex.classify_nonzero_codex_exit(stdout, "") == "PROVIDER_OUTAGE"


def test_live_nonzero_trusted_directory_exit_is_reclassified(tmp_path: Path) -> None:
    def rejected_codex(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr="Not inside a trusted directory and --skip-git-repo-check was not specified.\n",
        )

    result = codex.execute_request(
        _request(),
        expected_cli_version=CLI_VERSION,
        expected_model=MODEL,
        expected_reasoning_effort=EFFORT,
        workspace_dir=tmp_path,
        run_command=rejected_codex,
        version_runner=_never_codex,
        git_runner=_git_worktree,
        raw_jsonl=None,
        observed_cli_version=CLI_VERSION,
    )

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"
    assert result["raw_evidence"]["nonzero_exit_classification"] == "CORRUPTED_STARTING_STATE"
