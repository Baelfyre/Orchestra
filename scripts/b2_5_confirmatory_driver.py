#!/usr/bin/env python3
"""Fail-closed B2.5 confirmatory driver. Requires the frozen live authorization."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.a5_topology_benchmark_executor import digest_json
from scripts.b2_confirmatory_evidence import B2EvidenceError, classify_counter_stability
from scripts.b2_instrumentation_pilot_driver import (
    PilotDriverError,
    build_advisory_reference,
    build_response_evidence,
    build_usage_evidence,
    enforce_cross_run_invariants,
    repository_snapshot,
    validate_evidence,
    validate_output_boundary,
)
from scripts.b2_5_confirmatory_preflight import FREEZE_PATH, host_preflight, load_json, static_preflight
from scripts.comparative_benchmark_runner import (
    HarnessError,
    build_experiment_record,
    build_plan,
    build_run_record,
    invoke_executor,
    make_request,
    validate_manifest,
    validate_result,
    write_json,
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotDriverError(message)


def validate_authorization(authorization: dict[str, Any], freeze: dict[str, Any], manifest: dict[str, Any], plan: dict[str, Any], taskset: dict[str, Any]) -> None:
    require(authorization.get("schema_version") == "orchestra.b2-5-confirmatory-live-authorization.v1", "unsupported B2.5 authorization schema")
    require(authorization.get("live_execution_authorized") is True, "B2.5 live execution is not authorized")
    expected = {
        "freeze_digest": digest_json(freeze),
        "manifest_digest": digest_json(manifest),
        "plan_digest": digest_json(plan),
        "task_set_digest": taskset["aggregate_digest"],
        "planned_runs": 40,
        "maximum_underlying_model_calls": 120,
    }
    for key, value in expected.items():
        require(authorization.get(key) == value, f"authorization {key} mismatch")
    for key in ("preparation_sha", "preparation_tree"):
        value = authorization.get(key)
        require(isinstance(value, str) and len(value) == 40, f"authorization {key} must be an exact Git identity")


def exact_executor_command(freeze: dict[str, Any]) -> list[str]:
    host = freeze["host_binding"]
    return [
        sys.executable, str(ROOT / freeze["implementation"]["executor"]),
        "--eligibility-envelope", str(ROOT / freeze["topology"]["eligibility_envelope"]),
        "--expected-cli-version", host["cli_version"], "--model", host["model"],
        "--reasoning-effort", host["reasoning_effort"],
        "--codex-command-prefix-json", json.dumps([host["node_exe_path"], host["codex_js_path"]]),
        "--workspace-dir", freeze["workspace_boundary"]["path"],
        "--call-timeout-seconds", str(freeze["resource_freeze"]["call_timeout_seconds"]),
        "--per-run-total-token-ceiling", str(freeze["resource_freeze"]["per_run_total_token_ceiling"]),
    ]


def run_session(
    authorization: dict[str, Any], output_dir: Path, *,
    invoke: Callable[[list[str], dict[str, Any], int], tuple[dict[str, Any], dict[str, Any] | None]] = invoke_executor,
    snapshot: Callable[[], dict[str, Any]] = repository_snapshot,
    preflight: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    manifest = load_json(ROOT / freeze["manifest"]["source"])
    plan = load_json(ROOT / freeze["plan"]["source"])
    taskset = load_json(ROOT / freeze["task_selection"]["source_task_set"])
    validate_manifest(manifest)
    require(build_plan(manifest) == plan, "frozen B2.5 plan does not match manifest")
    validate_authorization(authorization, freeze, manifest, plan, taskset)
    (preflight or (lambda: host_preflight(static_preflight())))()
    workspace = Path(freeze["workspace_boundary"]["path"])
    validate_output_boundary(output_dir, workspace)
    baseline = snapshot()
    require(baseline["head"] == authorization["preparation_sha"] and baseline["tree"] == authorization["preparation_tree"] and baseline["status"] == "", "repository identity or cleanliness drift")
    output_dir.mkdir(parents=True, exist_ok=False)
    write_json(output_dir / "authorization.json", authorization)
    write_json(output_dir / "plan.json", plan)
    tasks = {task["task_id"]: task for task in manifest["tasks"]}
    command = exact_executor_command(freeze)
    calls_consumed = 0
    accepted_tokens = 0
    runs: list[dict[str, Any]] = []
    run_digests: list[str] = []
    call_records: list[dict[str, Any]] = []
    terminal = "COMPLETE"
    stop_reason = None
    for entry in plan["entries"]:
        require(calls_consumed + 3 <= freeze["resource_freeze"]["maximum_underlying_model_calls"], "model-call ceiling would be exceeded")
        if snapshot() != baseline:
            terminal, stop_reason = "STOPPED", "REPOSITORY_MUTATED_BEFORE_RUN"
            break
        request = make_request(manifest, entry, tasks[entry["task_id"]])
        write_json(output_dir / "requests" / f"{entry['request_id']}.json", request)
        result, partial = invoke(command, request, manifest["executor_timeout_seconds"])
        calls_consumed += 3
        write_json(output_dir / "executor-results" / f"{entry['request_id']}.json", result)
        if partial is not None:
            write_json(output_dir / "partials" / f"{entry['request_id']}.json", partial)
        if snapshot() != baseline:
            terminal, stop_reason = "STOPPED", "REPOSITORY_MUTATED_DURING_RUN"
            break
        try:
            validate_result(result, request)
            if result["outcome"]["status"] != "INVALID_RUN":
                call_records.extend(validate_evidence(result))
        except (HarnessError, B2EvidenceError, PilotDriverError, KeyError, TypeError, ValueError) as exc:
            terminal, stop_reason = "STOPPED", f"EVIDENCE_OR_VALIDATOR_FAILURE:{exc}"
            break
        run_record = build_run_record(manifest, request, result)
        write_json(output_dir / "runs" / f"{entry['request_id']}.json", run_record)
        runs.append(run_record)
        run_digests.append(digest_json(run_record))
        accepted_tokens += int(result.get("raw_evidence", {}).get("observed_total_tokens", 0))
        if accepted_tokens > freeze["resource_freeze"]["cumulative_accepted_token_ceiling"]:
            terminal, stop_reason = "STOPPED", "CUMULATIVE_TOKEN_CEILING_EXCEEDED"
            break
        if result["outcome"]["status"] in {"INVALID_RUN", "FAIL"}:
            terminal, stop_reason = "STOPPED", result["outcome"]["status"]
            break
    try:
        enforce_cross_run_invariants(manifest, runs)
    except HarnessError as exc:
        terminal, stop_reason = "STOPPED", f"CROSS_RUN_VALIDATOR_FAILURE:{exc}"
    index = {"schema_version": "orchestra.b2-5-confirmatory-run-index.v1", "run_digests": run_digests}
    write_json(output_dir / "run-index.json", index)
    experiment = build_experiment_record(manifest, run_digests, [run["run_id"] for run in runs if run["outcome"]["status"] == "INVALID_RUN"], plan)
    experiment["benefit_claim_allowed"] = False
    experiment["a5_promotion_evidence_allowed"] = False
    write_json(output_dir / "experiment.json", experiment)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for call in call_records:
        grouped.setdefault(str(call["counter_stability_key"]), []).append(call)
    summary = {
        "schema_version": "orchestra.b2-5-confirmatory-session-summary.v1",
        "status": terminal,
        "stop_reason": stop_reason,
        "completed_runs": len(runs),
        "live_model_calls_consumed": calls_consumed,
        "maximum_underlying_model_calls": 120,
        "accepted_total_tokens": accepted_tokens,
        "counter_stability": {key: classify_counter_stability(records) for key, records in sorted(grouped.items())},
        "repository_snapshot": baseline,
    }
    write_json(output_dir / "session-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the separately authorized B2.5 confirmatory measurement")
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = run_session(load_json(args.authorization), args.output_dir)
        print(json.dumps(summary, sort_keys=True))
        return 0 if summary["status"] == "COMPLETE" else 2
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, PilotDriverError, HarnessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "live_model_calls_consumed": 0, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
