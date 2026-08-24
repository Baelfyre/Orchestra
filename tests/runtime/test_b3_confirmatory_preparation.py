from __future__ import annotations

import json

from scripts.b3_confirmatory_preflight import ROOT, static_preflight
from scripts.comparative_benchmark_runner import build_plan, digest_json


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_confirmatory_plan_and_held_out_task_set_are_exact() -> None:
    freeze = load("machine/benchmarking/b3-confirmatory-freeze.v1.json")
    taskset = load(freeze["task_set"]["source"])
    manifest = load(freeze["manifest"]["source"])
    plan = load(freeze["plan"]["source"])
    assert len(taskset["tasks"]) == 50
    assert not {task["task_id"] for task in taskset["tasks"]}.intersection(taskset["calibration_and_pilot_task_ids_excluded"])
    assert len(plan["entries"]) == 450
    assert build_plan(manifest) == plan


def test_confirmatory_static_preflight_is_zero_call() -> None:
    result = static_preflight()
    assert result["status"] == "PASS_STATIC_ZERO_MODEL_CALLS"
    assert result["agy_exec_invoked"] is False
    assert result["live_model_calls"] == 0
    assert result["planned_runs"] == result["maximum_model_calls"] == 450
