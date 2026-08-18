from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "benchmarking" / "b2-a5-isolated-calibration-plan-only.json"
PLAN_RECORD_PATH = ROOT / "machine" / "benchmarking" / "a5-isolated-calibration-plan.v1.json"
MANIFEST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "comparative-benchmark-manifest.schema.json"

SPEC = importlib.util.spec_from_file_location("comparative_benchmark_runner_b2", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_b2_plan_record_preserves_no_execution_and_no_promotion_boundaries() -> None:
    record = _load(PLAN_RECORD_PATH)

    assert record["status"] == "CALIBRATION_PLAN_FROZEN_NO_EXECUTION"
    assert record["canonical_entry_head"] == "eed2e870dbfbc2782f941015761886e55c849185"
    assert record["calibration_design"]["minimum_task_count"] == 5
    assert record["calibration_design"]["repetitions_per_arm"] == 2
    assert record["calibration_design"]["communication_mode"] == "DEFAULT"
    assert record["calibration_design"]["benefit_claim_allowed"] is False
    assert record["calibration_design"]["measurement_maturity_after_plan_only"] == "MEASUREMENT_NOT_STARTED"

    assert record["plan_only_fixture"]["synthetic"] is True
    assert record["plan_only_fixture"]["real_a5_evidence"] is False
    assert record["plan_only_fixture"]["benefit_evidence"] is False
    assert record["plan_only_fixture"]["provider_execution"] is False

    resource = record["resource_boundary"]
    assert resource["current_mode"] == "NO_SPEND_PLAN_ONLY"
    assert resource["paid_provider_calls_authorized"] is False
    assert resource["external_compute_spend_authorized"] is False

    authority = record["authority_boundary"]
    assert authority["a5_topology_effective"] is False
    assert authority["a5_shadow_influenced_execution"] is False
    assert authority["a5_runtime_topology_control"] is False
    assert authority["conductor_dispatch_attachment"] is False
    assert authority["runtime_executor_attachment"] is False
    assert authority["a6_authorized"] is False


def test_b2_plan_only_fixture_is_schema_valid_and_meets_calibration_floor() -> None:
    manifest = _load(MANIFEST_PATH)
    schema = _load(MANIFEST_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    runner.validate_manifest(manifest)

    assert manifest["experiment_kind"] == "A5_ISOLATED"
    assert manifest["stage"] == "CALIBRATION"
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
