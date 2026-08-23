#!/usr/bin/env python3
"""B2.4 static and exact-host preflight. Never invokes Codex exec."""

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

from scripts.a5_topology_benchmark_executor import digest_json, load_envelope  # noqa: E402
from scripts.codex_benchmark_executor import parse_cli_version, validate_live_git_workspace  # noqa: E402
from scripts.comparative_benchmark_runner import build_plan, validate_manifest  # noqa: E402

FREEZE_PATH = ROOT / "machine" / "benchmarking" / "b2-instrumentation-pilot-freeze.v1.json"


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


def static_preflight() -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    require(freeze.get("schema_version") == "orchestra.b2-instrumentation-pilot-freeze.v1", "unexpected freeze schema")
    require(freeze.get("phase") == "B2_4_INSTRUMENTATION_PILOT_PREPARATION", "unexpected phase")
    require(freeze["activation"]["live_execution_authorized"] is False, "live execution must remain disabled")
    require(freeze["authority"]["b2_5_authorized"] is False, "B2.5 must remain disabled")
    resources = freeze["resource_freeze"]
    require(resources == {
        "per_run_total_token_ceiling": 75000, "cumulative_accepted_token_ceiling": 1200000,
        "maximum_benchmark_runs": 8, "maximum_underlying_model_calls": 24,
        "model_calls_per_run": 3, "call_timeout_seconds": 600, "automatic_retry": False,
        "stop_on_first_invalid_run": True, "stop_on_first_validator_failure": True,
        "specialist_advisory_retention_ceiling_bytes": 16384,
    }, "resource freeze drift")
    require(digest_json(resources) == freeze["resource_budget_digest"], "resource digest drift")

    taskset = load_json(ROOT / freeze["task_selection"]["source_task_set"])
    require(digest_json(taskset["tasks"]) == taskset["aggregate_digest"], "source task-set digest drift")
    mandatory = freeze["task_selection"]["mandatory_task_id"]
    eligible = sorted(task["task_id"] for task in taskset["tasks"] if task["task_id"] != mandatory and task["task_class"] == "HIGH_COORDINATION")
    require(eligible, "no eligible HIGH_COORDINATION task")
    require(eligible[0] == freeze["task_selection"]["second_task_id"], "second-task selection rule mismatch")
    require(freeze["task_selection"]["selected_task_ids"] == [mandatory, eligible[0]], "selected task order drift")
    source_tasks = {task["task_id"]: task for task in taskset["tasks"]}

    manifest = load_json(ROOT / freeze["manifest"]["source"])
    validate_manifest(manifest)
    require(digest_json(manifest) == freeze["manifest"]["digest"], "manifest digest drift")
    require([task["task_id"] for task in manifest["tasks"]] == freeze["task_selection"]["selected_task_ids"], "manifest task selection drift")
    for task in manifest["tasks"]:
        source = source_tasks[task["task_id"]]
        require(task["task_class"] == source["task_class"], f"task class drift: {task['task_id']}")
        require(task["starting_state_digest"] == source["starting_state_digest"], f"starting state drift: {task['task_id']}")
        require(task["task_prompt_digest"] == source["task_prompt_digest"], f"prompt drift: {task['task_id']}")
        require(digest_json(task["task_payload"]) == source["task_payload_digest"], f"payload drift: {task['task_id']}")
    require(manifest["common_control_identity"]["resource_budget_digest"] == freeze["resource_budget_digest"], "manifest resource identity drift")
    require(all(arm["communication_mode"] == "DEFAULT" and arm["topology_class"] == "SEQUENTIAL" for arm in manifest["arms"]), "arm policy drift")

    _, envelope, envelope_digest = load_envelope(ROOT / freeze["topology"]["eligibility_envelope"])
    require(envelope_digest == freeze["topology"]["eligibility_envelope_digest"], "eligibility envelope drift")
    require(list(envelope.candidate_ids) == freeze["topology"]["candidate_ids"], "candidate order drift")
    plan = load_json(ROOT / freeze["plan"]["source"])
    require(build_plan(manifest) == plan, "plan is not the deterministic manifest projection")
    require(digest_json(plan) == freeze["plan"]["digest"], "plan digest drift")
    require(len(plan["entries"]) == 8, "pilot must contain exactly eight runs")
    blocks: dict[tuple[str, int], set[str]] = {}
    for entry in plan["entries"]:
        blocks.setdefault((entry["task_id"], entry["repetition_index"]), set()).add(entry["arm"]["arm_id"])
    require(len(blocks) == 4 and all(len(arms) == 2 for arms in blocks.values()), "paired 2x2x2 plan drift")

    for relative, expected in freeze["implementation"]["sha256"].items():
        require(sha256_file(ROOT / relative) == expected, f"implementation identity drift: {relative}")
    return {
        "status": "PASS_STATIC_ZERO_LIVE_CALLS", "codex_exec_invoked": False, "live_model_calls": 0,
        "freeze_digest": digest_json(freeze), "manifest_digest": digest_json(manifest), "plan_digest": digest_json(plan),
        "planned_runs": 8, "maximum_underlying_model_calls": 24,
        "selected_task_ids": freeze["task_selection"]["selected_task_ids"],
    }


def host_preflight(static: dict[str, Any], run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    host = freeze["host_binding"]
    for path_key, digest_key in (("node_exe_path", "node_exe_sha256"), ("codex_js_path", "codex_js_sha256"), ("codex_package_json_path", "codex_package_json_sha256")):
        path = Path(host[path_key])
        require(path.is_file() and sha256_file(path) == host[digest_key], f"host file identity drift: {path_key}")
    command = [host["node_exe_path"], host["codex_js_path"], "--version"]
    version = run(command, capture_output=True, text=True, check=False, shell=False)
    require(command[-1] == "--version" and "exec" not in command, "preflight command boundary crossed")
    require(version.returncode == 0 and parse_cli_version(f"{version.stdout}\n{version.stderr}") == host["cli_version"], "Codex CLI version drift")
    workspace = Path(freeze["workspace_boundary"]["path"])
    ok, reason, evidence = validate_live_git_workspace(workspace)
    require(ok, reason or "workspace Git preflight failed")
    require(not (workspace / "AGENTS.md").exists(), "AGENTS.md is prohibited in pilot workspace")
    require(not [entry.name for entry in workspace.iterdir() if entry.name != ".git"], "pilot workspace is not empty")
    return {**static, "status": "PASS_ZERO_LIVE_CALLS", "host_verified": True, "workspace_preflight": evidence, "codex_exec_invoked": False, "live_model_calls": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate B2.4 preparation without model calls")
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
