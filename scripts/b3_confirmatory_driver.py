#!/usr/bin/env python3
"""One-attempt-per-slot fail-closed B3 confirmatory driver."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.b3_confirmatory_preflight import FREEZE_PATH, host_preflight, load_json, static_preflight
from scripts.comparative_benchmark_runner import (
    HarnessError,
    build_experiment_record,
    build_plan,
    build_run_record,
    digest_json,
    invoke_executor,
    make_request,
    validate_manifest,
    validate_result,
    write_json,
)


class DriverError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DriverError(message)


def snapshot(freeze: dict[str, Any]) -> dict[str, str]:
    git = freeze["repository_binding"]["git_executable"]
    def run(*args: str) -> str:
        result = subprocess.run([git, *args], cwd=ROOT, capture_output=True, text=True, check=False, shell=False)
        require(result.returncode == 0, f"Git identity command failed: {' '.join(args)}")
        return result.stdout.strip()
    return {"head": run("rev-parse", "HEAD"), "tree": run("rev-parse", "HEAD^{tree}"), "status": run("status", "--porcelain")}


def validate_authorization(auth: dict[str, Any], freeze: dict[str, Any], manifest: dict[str, Any], plan: dict[str, Any]) -> None:
    require(auth.get("schema_version") == "orchestra.b3-confirmatory-live-authorization.v1", "unsupported authorization schema")
    require(auth.get("live_execution_authorized") is True, "B3 confirmatory live execution is not authorized")
    expected = {
        "freeze_digest": digest_json(freeze),
        "manifest_digest": digest_json(manifest),
        "plan_digest": digest_json(plan),
        "planned_runs": 450,
        "maximum_model_calls": 450,
    }
    for key, value in expected.items():
        require(auth.get(key) == value, f"authorization {key} mismatch")
    require(auth.get("preparation_sha") == snapshot(freeze)["head"], "authorization preparation SHA mismatch")
    require(auth.get("preparation_tree") == snapshot(freeze)["tree"], "authorization preparation tree mismatch")


def run_session(auth: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    manifest = load_json(ROOT / freeze["manifest"]["source"])
    plan = load_json(ROOT / freeze["plan"]["source"])
    validate_manifest(manifest)
    require(build_plan(manifest) == plan, "frozen plan mismatch")
    validate_authorization(auth, freeze, manifest, plan)
    host_preflight(static_preflight())
    baseline = snapshot(freeze)
    require(baseline["status"] == "", "repository must be clean")
    require(not output_dir.exists(), "output directory must be new")
    output_dir.mkdir(parents=True)
    write_json(output_dir / "authorization.json", auth)
    write_json(output_dir / "plan.json", plan)
    tasks = {task["task_id"]: task for task in manifest["tasks"]}
    host = freeze["host_binding"]
    command = [
        sys.executable,
        str(ROOT / freeze["implementation"]["executor_adapter"]),
        "--expected-cli-version", host["cli_version"],
        "--expected-model", host["model"],
        "--agy-executable", host["executable_path"],
        "--settings-path", host["settings_path"],
        "--workspace-dir", freeze["workspace_boundary"]["path"],
        "--caveman-repo-path", freeze["communication_binding"]["caveman_repo_path"],
    ]
    runs: list[dict[str, Any]] = []
    digests: list[str] = []
    calls = 0
    accepted_tokens = 0
    status = "COMPLETE"
    stop_reason = None
    for entry in plan["entries"]:
        if snapshot(freeze) != baseline:
            status, stop_reason = "STOPPED_FAIL_CLOSED", "REPOSITORY_MUTATION"
            break
        require(calls < freeze["resource_freeze"]["maximum_model_calls"], "model-call ceiling reached")
        request = make_request(manifest, entry, tasks[entry["task_id"]])
        write_json(output_dir / "requests" / f"{entry['request_id']}.json", request)
        result, partial = invoke_executor(command, request, manifest["executor_timeout_seconds"])
        calls += 1
        write_json(output_dir / "executor-results" / f"{entry['request_id']}.json", result)
        if partial is not None:
            write_json(output_dir / "partials" / f"{entry['request_id']}.json", partial)
        try:
            validate_result(result, request)
        except (HarnessError, KeyError, TypeError, ValueError) as exc:
            status, stop_reason = "STOPPED_FAIL_CLOSED", f"VALIDATOR_FAILURE:{exc}"
            break
        record = build_run_record(manifest, request, result)
        write_json(output_dir / "runs" / f"{entry['request_id']}.json", record)
        runs.append(record)
        digests.append(digest_json(record))
        total = result.get("raw_evidence", {}).get("total_tokens")
        if isinstance(total, int):
            accepted_tokens += total
            if total > freeze["resource_freeze"]["per_run_total_token_ceiling"]:
                status, stop_reason = "STOPPED_FAIL_CLOSED", "PER_RUN_TOKEN_CEILING_EXCEEDED"
                break
        else:
            status, stop_reason = "STOPPED_FAIL_CLOSED", "TOTAL_TOKEN_COUNTER_MISSING"
            break
        if accepted_tokens > freeze["resource_freeze"]["cumulative_token_ceiling"]:
            status, stop_reason = "STOPPED_FAIL_CLOSED", "CUMULATIVE_TOKEN_CEILING_EXCEEDED"
            break
        if result["outcome"]["status"] != "PASS":
            status, stop_reason = "STOPPED_FAIL_CLOSED", result["outcome"]["status"]
            break
    index = {
        "schema_version": "orchestra.b3-confirmatory-run-index.v1",
        "planned_runs": 450,
        "recorded_runs": len(runs),
        "entries": [{"run_id": run["run_id"], "digest": digest} for run, digest in zip(runs, digests)],
    }
    write_json(output_dir / "run-index.json", index)
    experiment = build_experiment_record(manifest, digests, [run["run_id"] for run in runs if run["outcome"]["status"] == "INVALID_RUN"], plan)
    write_json(output_dir / "experiment.json", experiment)
    summary = {
        "schema_version": "orchestra.b3-confirmatory-session-summary.v1",
        "status": status,
        "stop_reason": stop_reason,
        "completed_runs": len(runs),
        "live_model_calls_consumed": calls,
        "maximum_model_calls": 450,
        "accepted_total_tokens": accepted_tokens,
        "repository_snapshot": baseline,
    }
    write_json(output_dir / "session-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_session(load_json(args.authorization), args.output_dir)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "COMPLETE" else 2
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, DriverError, HarnessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "live_model_calls_consumed": 0, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
