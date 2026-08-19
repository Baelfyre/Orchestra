from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "benchmarking" / "b3-murmurs-isolated-calibration-plan-only.json"
MANIFEST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "comparative-benchmark-manifest.schema.json"

SPEC = importlib.util.spec_from_file_location("comparative_benchmark_runner_b3", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_b3_plan_only_fixture_is_schema_valid_and_isolates_communication_mode() -> None:
    manifest = _load(MANIFEST_PATH)
    schema = _load(MANIFEST_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    runner.validate_manifest(manifest)

    assert manifest["experiment_kind"] == "MURMURS_ISOLATED"
    assert manifest["stage"] == "CALIBRATION"
    assert manifest["common_control_identity"]["orchestra_revision"] == "d95f677dbf23ab79c4698c26645ea30cea9b3019"
    assert manifest["common_control_identity"]["provider"] == "NO_PROVIDER_PLAN_ONLY"
    assert manifest["common_control_identity"]["model"] == "NO_MODEL_PLAN_ONLY"
    assert len(manifest["tasks"]) >= 5
    assert manifest["repetitions_per_arm"] == 2
    assert len(manifest["arms"]) == 3
    assert {arm["communication_mode"] for arm in manifest["arms"]} == {"DEFAULT", "CAVEMAN", "MURMURS"}
    assert all(arm["topology_class"] == "FIXED_DETERMINISTIC" for arm in manifest["arms"])

    topology_identity = {(arm["topology_candidate_id"], arm["topology_digest"]) for arm in manifest["arms"]}
    assert len(topology_identity) == 1
    assert manifest["murmurs_evaluation"]["same_counter_identity_for_token_delta"] is True
    assert manifest["a5_evaluation"] is None
    assert manifest["interaction_evaluation"] is None
    assert all(task["task_payload"]["synthetic"] is True for task in manifest["tasks"])
    assert all(task["task_payload"]["execution_allowed"] is False for task in manifest["tasks"])


def test_b3_plan_only_schedules_three_communication_arms_without_invoking_executor(tmp_path: Path) -> None:
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

    expected_modes = {"DEFAULT", "CAVEMAN", "MURMURS"}
    fixed_topology_identity = {
        (arm["topology_candidate_id"], arm["topology_digest"], arm["topology_class"])
        for arm in manifest["arms"]
    }
    assert len(fixed_topology_identity) == 1

    blocks: dict[tuple[str, int], set[str]] = {}
    for entry in first_plan["entries"]:
        key = (entry["task_id"], entry["repetition_index"])
        blocks.setdefault(key, set()).add(entry["arm"]["communication_mode"])
        assert entry["arm"]["topology_class"] == "FIXED_DETERMINISTIC"
        assert (entry["arm"]["topology_candidate_id"], entry["arm"]["topology_digest"], entry["arm"]["topology_class"]) in fixed_topology_identity

    assert len(blocks) == len(manifest["tasks"]) * manifest["repetitions_per_arm"] == 10
    assert all(block_modes == expected_modes for block_modes in blocks.values())


def test_b3_plan_only_cannot_create_token_savings_or_benefit_evidence(tmp_path: Path) -> None:
    output = tmp_path / "plan-only"

    assert runner.run(MANIFEST_PATH, ["never-executed"], output, plan_only=True) == 0
    plan = _load(output / "plan.json")

    assert plan["stage"] == "CALIBRATION"
    assert plan["experiment_kind"] == "MURMURS_ISOLATED"
    assert "conclusion" not in plan
    assert "run_evidence_digests" not in plan
    assert not (output / "experiment.json").exists()
    assert not (output / "run-index.json").exists()
