from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "benchmarking" / "b2-a5-isolated-calibration-plan-only.json"
MANIFEST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "comparative-benchmark-manifest.schema.json"

SPEC = importlib.util.spec_from_file_location("comparative_benchmark_runner_b2", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_b2_plan_only_fixture_is_schema_valid_and_meets_calibration_floor() -> None:
    manifest = _load(MANIFEST_PATH)
    schema = _load(MANIFEST_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    runner.validate_manifest(manifest)

    assert manifest["experiment_kind"] == "A5_ISOLATED"
    assert manifest["stage"] == "CALIBRATION"
    assert manifest["common_control_identity"]["orchestra_revision"] == "eed2e870dbfbc2782f941015761886e55c849185"
    assert manifest["common_control_identity"]["provider"] == "NO_PROVIDER_PLAN_ONLY"
    assert manifest["common_control_identity"]["model"] == "NO_MODEL_PLAN_ONLY"
    assert len(manifest["tasks"]) >= 5
    assert manifest["repetitions_per_arm"] == 2
    assert len(manifest["arms"]) >= 2
    assert all(arm["communication_mode"] == "DEFAULT" for arm in manifest["arms"])
    assert all(task["task_payload"]["synthetic"] is True for task in manifest["tasks"])
    assert all(task["task_payload"]["execution_allowed"] is False for task in manifest["tasks"])

    arm_candidate_ids = {arm["topology_candidate_id"] for arm in manifest["arms"]}
    assert set(manifest["a5_evaluation"]["eligible_topology_candidate_ids"]) == arm_candidate_ids


def test_b2_plan_only_schedules_every_arm_without_invoking_executor(tmp_path: Path) -> None:
    manifest = _load(MANIFEST_PATH)
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    impossible_executor = ["python", "THIS_FILE_MUST_NEVER_BE_EXECUTED_IN_PLAN_ONLY_MODE.py"]

    assert runner.run(MANIFEST_PATH, impossible_executor, first_output, plan_only=True) == 0
    assert runner.run(MANIFEST_PATH, impossible_executor, second_output, plan_only=True) == 0

    first_plan = _load(first_output / "plan.json")
    second_plan = _load(second_output / "plan.json")
    assert first_plan == second_plan

    assert not (first_output / "runs").exists()
    assert not (first_output / "run-index.json").exists()
    assert not (first_output / "experiment.json").exists()
    assert not (first_output / "partial-evidence").exists()

    expected_count = len(manifest["tasks"]) * manifest["repetitions_per_arm"] * len(manifest["arms"])
    assert len(first_plan["entries"]) == expected_count == 30

    expected_arm_ids = {arm["arm_id"] for arm in manifest["arms"]}
    blocks: dict[tuple[str, int], set[str]] = {}
    for entry in first_plan["entries"]:
        key = (entry["task_id"], entry["repetition_index"])
        blocks.setdefault(key, set()).add(entry["arm"]["arm_id"])
        assert entry["arm"]["communication_mode"] == "DEFAULT"

    assert len(blocks) == len(manifest["tasks"]) * manifest["repetitions_per_arm"] == 10
    assert all(block_arm_ids == expected_arm_ids for block_arm_ids in blocks.values())


def test_b2_plan_only_fixture_cannot_be_misread_as_measured_evidence(tmp_path: Path) -> None:
    manifest = _load(MANIFEST_PATH)
    output = tmp_path / "plan-only"

    assert runner.run(MANIFEST_PATH, ["never-executed"], output, plan_only=True) == 0
    plan = _load(output / "plan.json")

    assert plan["stage"] == "CALIBRATION"
    assert plan["experiment_kind"] == "A5_ISOLATED"
    assert "conclusion" not in plan
    assert "run_evidence_digests" not in plan
    assert not (output / "experiment.json").exists()
    assert not (output / "run-index.json").exists()
