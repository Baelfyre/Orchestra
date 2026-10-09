#!/usr/bin/env python3
"""Fail-closed B2.5 static and exact-host preflight. Never invokes codex exec."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.a5_topology_benchmark_executor import load_envelope
from scripts.codex_benchmark_executor import parse_cli_version, validate_live_git_workspace
from scripts.comparative_benchmark_runner import build_plan, digest_json, validate_manifest

FREEZE_PATH = ROOT / "machine" / "benchmarking" / "b2-5-confirmatory-freeze.v1.json"
TASKSET_PATH = ROOT / "machine" / "benchmarking" / "b2-5-held-out-task-set.v1.json"


class PreflightError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain one JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_source_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def expected_payload(task: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "task_id": task["task_id"],
        "decision": task["required_decision"],
        "validation_gates": task["required_validation_gates"],
        "authority_expansion": False,
    }
    return {
        "prompt": task["prompt"],
        "execution_allowed": True,
        "validation_contract": {
            "validator_type": "EXACT_JSON_CONFORMANCE_V1",
            "expected_response": expected,
            "required_keys": ["task_id", "decision", "validation_gates", "authority_expansion"],
            "prohibited_dispositions": ["AUTHORITY_EXPANSION", "GOVERNANCE_BYPASS"],
        },
    }


def validate_taskset(taskset: dict[str, Any], freeze: dict[str, Any]) -> None:
    require(taskset.get("status") == "B2_5_HELD_OUT_V1_FROZEN_EXECUTABLE_NOT_LIVE_AUTHORIZED", "held-out task set is not frozen")
    require(taskset.get("selection_rule", {}).get("rule_id") == "B2_5_ONE_HELD_OUT_TASK_PER_B0_STRATUM_V1", "task selection rule drift")
    tasks = taskset.get("tasks")
    require(isinstance(tasks, list) and len(tasks) == 10, "B2.5 requires exactly ten held-out tasks")
    frozen = freeze["task_selection"]
    require([task["task_id"] for task in tasks] == frozen["task_ids"], "held-out task order drift")
    require([task["task_class"] for task in tasks] == frozen["task_classes"], "B0 stratum coverage drift")
    calibration_ids = {"b2-cal-api-boundary", "b2-cal-schema-migration", "b2-cal-cache-freshness", "b2-cal-retry-amplification", "b2-cal-cross-layer-release"}
    require(not calibration_ids.intersection(frozen["task_ids"]), "held-out task collides with B2 calibration")
    for task in tasks:
        require(task.get("authority_expansion") is False, f"authority expansion in task {task['task_id']}")
        require(digest_json(task["starting_state"]) == task["starting_state_digest"], f"starting-state digest drift: {task['task_id']}")
        require(digest_json(task["prompt"]) == task["task_prompt_digest"], f"prompt digest drift: {task['task_id']}")
        expected = {"task_id": task["task_id"], "decision": task["required_decision"], "validation_gates": task["required_validation_gates"], "authority_expansion": False}
        require(digest_json(expected) == task["expected_response_digest"], f"expected-response digest drift: {task['task_id']}")
        require(digest_json(expected_payload(task)) == task["task_payload_digest"], f"payload digest drift: {task['task_id']}")
    require(digest_json(tasks) == taskset["aggregate_digest"], "held-out task-set aggregate digest drift")


def static_preflight() -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    require(freeze.get("schema_version") == "orchestra.b2-5-confirmatory-freeze.v1", "unexpected B2.5 freeze schema")
    require(freeze.get("phase") == "B2_5_CONFIRMATORY_PREPARATION", "unexpected B2.5 phase")
    require(freeze["activation"]["live_execution_authorized"] is False, "live execution must remain disabled in freeze")
    require(freeze["authority"]["a5_execution_effective_promotion"] is False, "A5 promotion must remain disabled")
    taskset = load_json(TASKSET_PATH)
    validate_taskset(taskset, freeze)
    manifest = load_json(ROOT / freeze["manifest"]["source"])
    validate_manifest(manifest)
    require(digest_json(manifest) == freeze["manifest"]["digest"], "manifest digest drift")
    require(manifest["task_set_digest"] == taskset["aggregate_digest"], "manifest task-set identity drift")
    require(manifest["common_control_identity"]["resource_budget_digest"] == freeze["resource_budget_digest"], "manifest resource identity drift")
    require([task["task_id"] for task in manifest["tasks"]] == freeze["task_selection"]["task_ids"], "manifest task selection drift")
    for task in manifest["tasks"]:
        source = next(item for item in taskset["tasks"] if item["task_id"] == task["task_id"])
        require(task["task_class"] == source["task_class"], f"task class drift: {task['task_id']}")
        require(task["starting_state_digest"] == source["starting_state_digest"], f"starting state drift: {task['task_id']}")
        require(task["task_prompt_digest"] == source["task_prompt_digest"], f"prompt drift: {task['task_id']}")
        require(task["task_payload_digest"] == source["task_payload_digest"], f"payload identity drift: {task['task_id']}")
        require(digest_json(task["task_payload"]) == task["task_payload_digest"], f"manifest payload drift: {task['task_id']}")
    resources = freeze["resource_freeze"]
    require(resources["maximum_benchmark_runs"] == 40 and resources["maximum_underlying_model_calls"] == 120, "B2.5 run ceiling drift")
    require(resources["model_calls_per_run"] == 3 and resources["automatic_retry"] is False, "B2.5 retry/call policy drift")
    require(resources["stop_on_first_invalid_run"] is True and resources["stop_on_first_validator_failure"] is True, "B2.5 stop policy drift")
    require(resources["cumulative_accepted_token_ceiling"] == 3000000, "B2.5 cumulative ceiling drift")
    require(digest_json(resources) == freeze["resource_budget_digest"], "resource budget digest drift")
    plan = load_json(ROOT / freeze["plan"]["source"])
    require(build_plan(manifest) == plan, "B2.5 plan is not deterministic manifest projection")
    require(digest_json(plan) == freeze["plan"]["digest"], "plan digest drift")
    require(len(plan["entries"]) == 40, "B2.5 must contain exactly forty runs")
    blocks: dict[tuple[str, int], set[str]] = {}
    for entry in plan["entries"]:
        blocks.setdefault((entry["task_id"], entry["repetition_index"]), set()).add(entry["arm"]["arm_id"])
    require(len(blocks) == 20 and all(len(arms) == 2 for arms in blocks.values()), "B2.5 paired plan drift")
    _, envelope, envelope_digest = load_envelope(ROOT / freeze["topology"]["eligibility_envelope"])
    require(envelope_digest == freeze["topology"]["eligibility_envelope_digest"], "eligibility envelope drift")
    require(list(envelope.candidate_ids) == freeze["topology"]["candidate_ids"], "topology candidate order drift")
    for relative, expected in freeze["implementation"]["sha256"].items():
        require(sha256_source_file(ROOT / relative) == expected, f"implementation identity drift: {relative}")
    return {"status": "PASS_STATIC_ZERO_LIVE_CALLS", "codex_exec_invoked": False, "live_model_calls": 0, "freeze_digest": digest_json(freeze), "manifest_digest": digest_json(manifest), "plan_digest": digest_json(plan), "task_set_digest": taskset["aggregate_digest"], "planned_runs": 40, "maximum_underlying_model_calls": 120, "task_ids": freeze["task_selection"]["task_ids"]}


def verify_exact_boundaries(freeze: dict[str, Any]) -> dict[str, Any]:
    host = freeze["host_binding"]
    for path_key, digest_key in (("node_exe_path", "node_exe_sha256"), ("codex_js_path", "codex_js_sha256"), ("codex_package_json_path", "codex_package_json_sha256")):
        path = Path(host[path_key])
        require(path.is_file() and sha256_file(path) == host[digest_key], f"host file identity drift: {path_key}")
    workspace = Path(freeze["workspace_boundary"]["path"])
    ok, reason, evidence = validate_live_git_workspace(workspace)
    require(ok, reason or "workspace Git preflight failed")
    require(not (workspace / "AGENTS.md").exists(), "AGENTS.md is prohibited in pilot workspace")
    require(not [entry.name for entry in workspace.iterdir() if entry.name != ".git"], "pilot workspace is not empty")
    return evidence


def host_preflight(static: dict[str, Any], run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run, verify_boundaries: Callable[[dict[str, Any]], dict[str, Any]] = verify_exact_boundaries) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    evidence = verify_boundaries(freeze)
    host = freeze["host_binding"]
    command = [host["node_exe_path"], host["codex_js_path"], "--version"]
    version = run(command, capture_output=True, text=True, check=False, shell=False)
    require(command[-1] == "--version" and "exec" not in command, "preflight command boundary crossed")
    require(version.returncode == 0 and parse_cli_version(f"{version.stdout}\n{version.stderr}") == host["cli_version"], "Codex CLI version drift")
    return {**static, "status": "PASS_ZERO_LIVE_CALLS", "host_verified": True, "workspace_preflight": evidence, "codex_exec_invoked": False, "live_model_calls": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate B2.5 preparation without model calls")
    parser.add_argument("--verify-host", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = static_preflight()
        if args.verify_host:
            result = host_preflight(result)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, PreflightError, subprocess.SubprocessError) as exc:
        result = {"status": "FAIL_CLOSED", "codex_exec_invoked": False, "live_model_calls": 0, "error": str(exc)}
        print(json.dumps(result, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
