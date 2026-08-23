#!/usr/bin/env python3
"""Zero-live-call B2.2 freeze and host preflight.

This script validates the frozen B2 A5-isolated calibration identities. With
--verify-host it may run only the pinned Codex `--version` command; it never
invokes `codex exec` and therefore performs zero model calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.a5_topology_benchmark_executor import digest_json, load_envelope  # noqa: E402
from scripts.codex_benchmark_executor import parse_cli_version, validate_live_git_workspace  # noqa: E402

FREEZE_PATH = ROOT / "machine" / "benchmarking" / "b2-real-calibration-freeze.v1.json"
TASKSET_PATH = ROOT / "machine" / "benchmarking" / "b3-calibration-task-set.v1.json"


class PreflightError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError(f"{path} must contain one JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def static_preflight() -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    require(freeze.get("schema_version") == "orchestra.b2-real-calibration-freeze.v1", "unexpected freeze schema")
    require(freeze.get("program_id") == "orchestra.shared-comparative-benchmark.v1", "unexpected program")
    require(freeze.get("phase") == "B2_2_REAL_CALIBRATION_FREEZE_AND_ZERO_CALL_PREFLIGHT", "unexpected phase")
    require(freeze["activation"]["live_execution_authorized"] is False, "B2 live execution must remain disabled")
    require(freeze["experimental_constraints"]["automatic_retry"] is False, "automatic retry must remain off")
    require(freeze["experiment"]["communication_mode"] == "DEFAULT", "B2 must isolate topology under DEFAULT communication")
    require(freeze["experiment"]["planned_runs"] == 20, "B2 calibration must freeze exactly 20 runs")
    require(freeze["resource_freeze"]["maximum_underlying_model_calls"] == 60, "B2 calibration must freeze exactly 60 maximum model calls")
    require(freeze["resource_freeze"]["maximum_benchmark_runs"] == 20, "run ceiling must equal frozen plan size")
    require(freeze["resource_freeze"]["model_calls_per_run"] == 3, "B2 topology run must remain three calls")
    require(digest_json(freeze["resource_freeze"]) == freeze["resource_budget_digest"], "resource budget digest drift")

    envelope_path = ROOT / freeze["topology"]["eligibility_envelope"]
    raw_envelope, envelope, envelope_digest = load_envelope(envelope_path)
    require(envelope_digest == freeze["topology"]["eligibility_envelope_digest"], "eligibility envelope digest drift")
    require(list(envelope.candidate_ids) == freeze["topology"]["candidate_ids"], "candidate set/order drift")
    require(list(envelope.required_specialists) == freeze["topology"]["required_specialists"], "required specialist drift")
    require(envelope.deterministic_topology_candidate_id == freeze["topology"]["deterministic_baseline_candidate_id"], "deterministic baseline drift")
    for candidate in envelope.candidates:
        require(digest_json(candidate.to_dict()) == freeze["topology"]["candidate_digests"][candidate.candidate_id], f"candidate digest drift: {candidate.candidate_id}")
        require(all(stage.mode == "SEQUENTIAL" for stage in candidate.stages), "parallel candidate is not permitted")

    taskset = load_json(TASKSET_PATH)
    require(taskset.get("status") == "PADAYON_GROUNDED_V1_FROZEN", "task set is not frozen")
    require(taskset.get("design_rules", {}).get("validator_type") == "EXACT_JSON_CONFORMANCE_V1", "validator drift")
    require(freeze["task_set"]["aggregate_digest"] == "fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8", "task-set digest drift")
    source_tasks = {task["task_id"]: task for task in taskset["tasks"]}
    require(len(source_tasks) == freeze["task_set"]["task_count"] == 5, "task count drift")
    for frozen in freeze["task_set"]["tasks"]:
        source = source_tasks.get(frozen["task_id"])
        require(source is not None, f"missing frozen task: {frozen['task_id']}")
        for field in ("task_class", "starting_state_digest", "task_prompt_digest", "task_payload_digest", "validation_contract_digest"):
            require(source.get(field) == frozen[field], f"task identity drift: {frozen['task_id']}:{field}")

    return {
        "status": "PASS_STATIC_ZERO_LIVE_CALLS",
        "live_model_calls": 0,
        "freeze_digest": digest_json(freeze),
        "eligibility_envelope_digest": envelope_digest,
        "task_set_digest": freeze["task_set"]["aggregate_digest"],
        "planned_runs": freeze["experiment"]["planned_runs"],
        "maximum_underlying_model_calls": freeze["resource_freeze"]["maximum_underlying_model_calls"],
        "candidate_ids": list(envelope.candidate_ids),
        "canonical_envelope": raw_envelope == envelope.to_dict(),
    }


def host_preflight(static: dict[str, Any]) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    host = freeze["host_binding"]
    for path_key, digest_key in (
        ("node_exe_path", "node_exe_sha256"),
        ("codex_js_path", "codex_js_sha256"),
        ("codex_package_json_path", "codex_package_json_sha256"),
    ):
        path = Path(host[path_key])
        require(path.is_file(), f"missing frozen host file: {path}")
        require(sha256_file(path) == host[digest_key], f"host file digest drift: {path_key}")

    prefix = [host["node_exe_path"], host["codex_js_path"]]
    version = subprocess.run(prefix + ["--version"], capture_output=True, text=True, check=False, shell=False)
    require(version.returncode == 0, "Codex version preflight failed")
    observed = parse_cli_version(f"{version.stdout}\n{version.stderr}")
    require(observed == host["cli_version"], "Codex CLI version drift")

    workspace = Path(freeze["workspace_boundary"]["path"])
    require(workspace.is_dir(), "frozen workspace does not exist")
    workspace_ok, workspace_reason, workspace_evidence = validate_live_git_workspace(workspace)
    require(workspace_ok, workspace_reason or "workspace Git preflight failed")
    require(not (workspace / "AGENTS.md").exists(), "AGENTS.md is prohibited in the frozen workspace")
    visible = [entry.name for entry in workspace.iterdir() if entry.name != ".git"]
    require(not visible, f"workspace is not empty outside Git metadata: {visible}")

    result = dict(static)
    result.update({
        "status": "PASS_ZERO_LIVE_CALLS",
        "host_verified": True,
        "observed_cli_version": observed,
        "workspace_preflight": workspace_evidence,
        "codex_exec_invoked": False,
        "live_model_calls": 0,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate B2.2 calibration freeze without model calls")
    parser.add_argument("--verify-host", action="store_true", help="Verify exact local Codex files/version/workspace; still performs zero model calls")
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
    except (PreflightError, OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        result = {"status": "FAIL_CLOSED", "live_model_calls": 0, "error": str(exc)}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
