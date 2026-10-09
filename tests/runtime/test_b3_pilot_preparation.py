from __future__ import annotations

import json
from pathlib import Path

from scripts.b3_pilot_preflight import ROOT, static_preflight
from scripts.comparative_benchmark_runner import build_plan, digest_json


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_b3_pilot_is_exactly_twenty_by_three_by_three() -> None:
    freeze = load("machine/benchmarking/b3-pilot-freeze.v1.json")
    manifest = load(freeze["manifest"]["source"])
    plan = load(freeze["plan"]["source"])
    assert len(manifest["tasks"]) == 20
    assert manifest["repetitions_per_arm"] == 3
    assert len(manifest["arms"]) == 3
    assert len(plan["entries"]) == 180
    assert build_plan(manifest) == plan


def test_b3_pilot_zero_call_static_preflight_and_boundaries() -> None:
    result = static_preflight()
    assert result["status"] == "PASS_STATIC_ZERO_MODEL_CALLS"
    assert result["agy_exec_invoked"] is False
    assert result["live_model_calls"] == 0
    freeze = load("machine/benchmarking/b3-pilot-freeze.v1.json")
    assert freeze["activation"]["live_execution_authorized"] is False
    assert freeze["resource_freeze"]["automatic_retry"] is False
    assert freeze["resource_freeze"]["maximum_model_calls"] == 180


def test_b3_pilot_tasks_are_held_out_and_digest_stable() -> None:
    taskset = load("machine/benchmarking/b3-pilot-task-set.v1.json")
    ids = [task["task_id"] for task in taskset["tasks"]]
    assert len(ids) == len(set(ids)) == 20
    assert not set(ids).intersection(taskset["calibration_task_ids_excluded"])
    assert digest_json(taskset["tasks"]) == taskset["aggregate_digest"]
