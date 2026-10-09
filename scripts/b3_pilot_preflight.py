#!/usr/bin/env python3
"""Fail-closed zero-model-call preflight for the frozen B3 pilot."""

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

from scripts.comparative_benchmark_runner import build_plan, digest_json, validate_manifest

FREEZE_PATH = ROOT / "machine" / "benchmarking" / "b3-pilot-freeze.v1.json"


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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_source(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def static_preflight() -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    require(freeze["schema_version"] == "orchestra.b3-pilot-freeze.v1", "unexpected freeze schema")
    require(freeze["activation"]["live_execution_authorized"] is False, "canonical freeze must not self-authorize live execution")
    taskset = load_json(ROOT / freeze["task_set"]["source"])
    manifest = load_json(ROOT / freeze["manifest"]["source"])
    plan = load_json(ROOT / freeze["plan"]["source"])
    require(digest_json(taskset["tasks"]) == taskset["aggregate_digest"], "task-set digest drift")
    validate_manifest(manifest)
    require(digest_json(manifest) == freeze["manifest"]["digest"], "manifest digest drift")
    require(build_plan(manifest) == plan and digest_json(plan) == freeze["plan"]["digest"], "plan drift")
    require(len(taskset["tasks"]) == 20 and len(plan["entries"]) == 180, "B3 pilot size drift")
    require(manifest["repetitions_per_arm"] == 3 and len(manifest["arms"]) == 3, "B3 pilot design drift")
    resources = freeze["resource_freeze"]
    require(resources["maximum_runs"] == 180 and resources["maximum_model_calls"] == 180, "resource ceiling drift")
    require(resources["automatic_retry"] is False and resources["attempts_per_slot"] == 1, "retry policy drift")
    for relative, expected in freeze["implementation"]["sha256"].items():
        require(sha256_source(ROOT / relative) == expected, f"implementation identity drift: {relative}")
    return {
        "status": "PASS_STATIC_ZERO_MODEL_CALLS",
        "agy_exec_invoked": False,
        "live_model_calls": 0,
        "freeze_digest": digest_json(freeze),
        "manifest_digest": digest_json(manifest),
        "plan_digest": digest_json(plan),
        "task_set_digest": taskset["aggregate_digest"],
        "planned_runs": 180,
        "maximum_model_calls": 180,
    }


def host_preflight(static: dict[str, Any]) -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    host = freeze["host_binding"]
    executable = Path(host["executable_path"])
    require(executable.is_file() and sha256_file(executable) == host["executable_sha256"], "Antigravity executable identity drift")
    settings = Path(host["settings_path"])
    require(settings.is_file() and sha256_file(settings) == host["settings_sha256"], "B3 settings identity drift")
    workspace = Path(freeze["workspace_boundary"]["path"])
    require(workspace.is_dir() and not (workspace / "AGENTS.md").exists(), "workspace boundary drift")
    require(not [p for p in workspace.iterdir() if p.name != ".git"], "workspace contamination")
    caveman = Path(freeze["communication_binding"]["caveman_repo_path"])
    git = freeze["repository_binding"]["git_executable"]
    revision = subprocess.run([git, "-C", str(caveman), "rev-parse", "HEAD"], capture_output=True, text=True, check=False, shell=False)
    blob = subprocess.run([git, "-C", str(caveman), "hash-object", "--", "skills/caveman/SKILL.md"], capture_output=True, text=True, check=False, shell=False)
    require(revision.returncode == 0 and revision.stdout.strip() == freeze["communication_binding"]["caveman_revision"], "Caveman revision drift")
    require(blob.returncode == 0 and blob.stdout.strip() == freeze["communication_binding"]["caveman_blob"], "Caveman policy drift")
    version = subprocess.run([str(executable), "--version"], capture_output=True, text=True, check=False, shell=False)
    require(version.returncode == 0 and version.stdout.strip() == host["cli_version"], "Antigravity version drift")
    models = subprocess.run([str(executable), "models"], capture_output=True, text=True, check=False, shell=False)
    require(models.returncode == 0 and any(line.split("\t", 1)[0] == host["model"] for line in models.stdout.splitlines()), "frozen model unavailable")
    return {**static, "status": "PASS_ZERO_MODEL_CALLS", "host_verified": True, "agy_exec_invoked": False, "live_model_calls": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
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
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, PreflightError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "agy_exec_invoked": False, "live_model_calls": 0, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
