from __future__ import annotations

import copy
import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
SPEC = importlib.util.spec_from_file_location("comparative_benchmark_runner", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

SCHEMA_DIR = ROOT / "machine" / "schemas"
DIGEST = "1" * 64
ELIGIBILITY_DIGEST = "2" * 64
A5_EVIDENCE_DIGEST = "3" * 64
MURMURS_EVIDENCE_DIGEST = "4" * 64


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validate(schema_name: str, value: dict) -> None:
    schema = _load_schema(schema_name)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)


def _control() -> dict:
    return {
        "orchestra_revision": "3037b6207c844b75a6246fc5c1074cf849e7df82",
        "repository_revision": "fixture-repository-revision",
        "system_instruction_digest": DIGEST,
        "provider": "fixture-provider",
        "model": "fixture-model",
        "model_revision": "fixture-model-revision",
        "reasoning_setting": "fixture-reasoning",
        "temperature": 0,
        "tool_access_digest": DIGEST,
        "specialist_set_digest": DIGEST,
        "required_specialist_set_digest": DIGEST,
        "authority_digest": DIGEST,
        "governance_digest": DIGEST,
        "validation_contract_digest": DIGEST,
        "environment_digest": DIGEST,
        "retry_policy_digest": DIGEST,
        "resource_budget_digest": DIGEST,
    }


def _arm(arm_id: str, topology_id: str, topology_class: str, communication_mode: str, marker: str) -> dict:
    return {
        "arm_id": arm_id,
        "topology_candidate_id": topology_id,
        "topology_class": topology_class,
        "topology_digest": marker * 64,
        "communication_mode": communication_mode,
    }


def _task(task_id: str, task_class: str = "SINGLE_DOMAIN", **payload: object) -> dict:
    return {
        "task_id": task_id,
        "task_class": task_class,
        "starting_state_digest": _digest([task_id, "start"]),
        "task_prompt_digest": _digest([task_id, "prompt"]),
        "task_payload": payload,
    }


def _a5_manifest() -> dict:
    arms = [
        _arm("sequential", "topology-sequential", "SEQUENTIAL", "DEFAULT", "a"),
        _arm("parallel", "topology-parallel", "PARALLEL_JOIN", "DEFAULT", "b"),
    ]
    return {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-a5-calibration",
        "experiment_kind": "A5_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 19082026,
        "repetitions_per_arm": 2,
        "executor_timeout_seconds": 30,
        "common_control_identity": _control(),
        "arms": arms,
        "tasks": [_task("task-a"), _task("task-b", "PARALLEL_FRIENDLY")],
        "a5_evaluation": {
            "eligibility_envelope_digest": ELIGIBILITY_DIGEST,
            "eligible_topology_candidate_ids": [arm["topology_candidate_id"] for arm in arms],
        },
        "murmurs_evaluation": None,
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }


def _murmurs_manifest() -> dict:
    topology_id = "fixed-topology"
    topology_digest = "c" * 64
    return {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-murmurs-calibration",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 19082027,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": _control(),
        "arms": [
            {"arm_id": "default", "topology_candidate_id": topology_id, "topology_class": "FIXED_DETERMINISTIC", "topology_digest": topology_digest, "communication_mode": "DEFAULT"},
            {"arm_id": "caveman", "topology_candidate_id": topology_id, "topology_class": "FIXED_DETERMINISTIC", "topology_digest": topology_digest, "communication_mode": "CAVEMAN"},
            {"arm_id": "murmurs", "topology_candidate_id": topology_id, "topology_class": "FIXED_DETERMINISTIC", "topology_digest": topology_digest, "communication_mode": "MURMURS"},
        ],
        "tasks": [_task("task-m", host_tokens=True)],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }


def _interaction_manifest() -> dict:
    arms = [
        _arm("seq-default", "topology-sequential", "SEQUENTIAL", "DEFAULT", "d"),
        _arm("seq-murmurs", "topology-sequential", "SEQUENTIAL", "MURMURS", "d"),
        _arm("par-default", "topology-parallel", "PARALLEL_JOIN", "DEFAULT", "e"),
        _arm("par-murmurs", "topology-parallel", "PARALLEL_JOIN", "MURMURS", "e"),
    ]
    return {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-interaction-calibration",
        "experiment_kind": "A5_MURMURS_INTERACTION",
        "stage": "CALIBRATION",
        "randomization_seed": 19082028,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": _control(),
        "arms": arms,
        "tasks": [_task("task-i")],
        "a5_evaluation": {
            "eligibility_envelope_digest": ELIGIBILITY_DIGEST,
            "eligible_topology_candidate_ids": ["topology-sequential", "topology-parallel"],
        },
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": {
            "isolated_a5_evidence_digest": A5_EVIDENCE_DIGEST,
            "isolated_murmurs_evidence_digest": MURMURS_EVIDENCE_DIGEST,
        },
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }


def _write_fake_executor(tmp_path: Path) -> Path:
    path = tmp_path / "fixture_executor.py"
    path.write_text(
        r'''import hashlib
import json
import sys

request = json.load(sys.stdin)
if request["task_payload"].get("force_nonzero"):
    print("fixture failure", file=sys.stderr)
    raise SystemExit(7)

raw = {
    "fixture": True,
    "task_id": request["task_id"],
    "repetition_index": request["repetition_index"],
    "arm_id": request["arm"]["arm_id"],
}
digest = hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
mode = request["arm"]["communication_mode"]
host_tokens = bool(request["task_payload"].get("host_tokens"))
if host_tokens:
    output_by_mode = {"DEFAULT": 120, "CAVEMAN": 90, "MURMURS": 72}
    tokens = {
        "source": "HOST_REPORTED",
        "counter_id": "fixture-provider-counter-v1",
        "input_tokens": 200,
        "output_tokens": output_by_mode[mode],
        "cached_input_tokens": 0,
        "reasoning_tokens": 20,
        "fresh_billable_tokens": 200 + output_by_mode[mode] + 20,
    }
else:
    tokens = {
        "source": "UNAVAILABLE",
        "counter_id": None,
        "input_tokens": None,
        "output_tokens": None,
        "cached_input_tokens": None,
        "reasoning_tokens": None,
        "fresh_billable_tokens": None,
    }

a5 = None
if request["experiment_kind"] in {"A5_ISOLATED", "A5_MURMURS_INTERACTION"}:
    ranked = request["a5_evaluation"]["eligible_topology_candidate_ids"]
    decision_basis = {
        "task_id": request["task_id"],
        "repetition_index": request["repetition_index"],
        "ranked": ranked,
    }
    decision_digest = hashlib.sha256(json.dumps(decision_basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    a5 = {
        "eligibility_digest": request["a5_evaluation"]["eligibility_envelope_digest"],
        "ranked_topology_candidate_ids": ranked,
        "top_candidate_id": ranked[0],
        "decision_digest": decision_digest,
    }

result = {
    "schema_version": "orchestra.comparative-benchmark-executor-result.v1",
    "request_id": request["request_id"],
    "outcome": {"status": "PASS", "invalid_reason": None, "task_completed": True, "validation_passed": True, "governance_valid": True},
    "quality": {"requirements_satisfied": 1, "requirements_missed": 0, "remediation_iterations": 0, "validation_failures": 0, "regressions_introduced": 0},
    "tokens": tokens,
    "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
    "latency": {"wall_clock_ms": 10, "model_execution_ms": 5, "tool_execution_ms": 2, "coordination_overhead_ms": 3},
    "coordination": {"specialist_messages": 2, "cross_specialist_messages": 1, "handoffs": 1, "handoff_failures": 0, "duplicate_work_events": 0, "contradiction_events": 0, "join_wait_ms": 0, "specialist_reentry_events": 0},
    "communication": {"progress_messages": 1, "model_progress_calls": 1, "user_visible_bytes": 32, "context_transfer_bytes": 64, "semantic_preservation_failures": 0, "required_information_omissions": 0},
    "safety": {"required_specialist_omission": False, "authority_expansion": False, "capability_expansion": False, "governance_violation": False, "provider_privacy_expansion": False, "mandatory_gate_suppression": False},
    "validation_digest": digest,
    "governance_digest": digest,
    "raw_evidence": raw,
    "a5_shadow_observation": a5,
}
print(json.dumps(result))
''',
        encoding="utf-8",
    )
    return path


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def _load_runs(output_dir: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted((output_dir / "runs").glob("*.json"))]


def test_b1_machine_schemas_are_valid_json_schema() -> None:
    for name in (
        "comparative-benchmark-manifest.schema.json",
        "comparative-benchmark-executor-request.schema.json",
        "comparative-benchmark-executor-result.schema.json",
        "comparative-benchmark-run.schema.json",
        "comparative-benchmark-experiment.schema.json",
    ):
        jsonschema.Draft202012Validator.check_schema(_load_schema(name))


def test_a5_calibration_executes_every_arm_and_emits_schema_valid_evidence(tmp_path: Path) -> None:
    manifest = _a5_manifest()
    _validate("comparative-benchmark-manifest.schema.json", manifest)
    fake = _write_fake_executor(tmp_path)
    output = tmp_path / "out"
    rc = runner.run(_write_manifest(tmp_path, manifest), [sys.executable, str(fake)], output)
    assert rc == 0

    plan = json.loads((output / "plan.json").read_text(encoding="utf-8"))
    assert len(plan["entries"]) == 8
    runs = _load_runs(output)
    assert len(runs) == 8
    grouped: dict[tuple[str, int], set[str]] = {}
    for record in runs:
        _validate("comparative-benchmark-run.schema.json", record)
        grouped.setdefault((record["task_id"], record["repetition_index"]), set()).add(record["arm"]["arm_id"])
        assert record["a5_shadow_observation"]["ranked_topology_candidate_ids"] == ["topology-sequential", "topology-parallel"]
    assert all(arms == {"sequential", "parallel"} for arms in grouped.values())

    experiment = json.loads((output / "experiment.json").read_text(encoding="utf-8"))
    _validate("comparative-benchmark-experiment.schema.json", experiment)
    assert experiment["conclusion"] == "MEASUREMENT_CALIBRATED"
    assert experiment["a5_evaluation"]["a5_may_select_execution_arm"] is False


def test_plan_is_reproducible_for_same_seed_and_manifest() -> None:
    manifest = _a5_manifest()
    assert runner.build_plan(manifest) == runner.build_plan(copy.deepcopy(manifest))


def test_executor_request_exposes_frozen_a5_candidate_set() -> None:
    manifest = _a5_manifest()
    plan = runner.build_plan(manifest)
    task = manifest["tasks"][0]
    request = runner.make_request(manifest, plan["entries"][0], task)
    _validate("comparative-benchmark-executor-request.schema.json", request)
    assert request["a5_evaluation"]["eligible_topology_candidate_ids"] == ["topology-sequential", "topology-parallel"]


def test_a5_manifest_rejects_non_default_communication() -> None:
    manifest = _a5_manifest()
    manifest["arms"][0]["communication_mode"] = "MURMURS"
    with pytest.raises(runner.HarnessError, match="DEFAULT communication"):
        runner.validate_manifest(manifest)


def test_murmurs_manifest_requires_exact_three_communication_arms_and_fixed_topology() -> None:
    manifest = _murmurs_manifest()
    runner.validate_manifest(manifest)
    malformed = copy.deepcopy(manifest)
    malformed["arms"][2]["topology_candidate_id"] = "different-topology"
    with pytest.raises(runner.HarnessError, match="identical fixed topology"):
        runner.validate_manifest(malformed)
    malformed = copy.deepcopy(manifest)
    malformed["arms"] = malformed["arms"][:2]
    with pytest.raises(runner.HarnessError, match="exactly DEFAULT, CAVEMAN, and MURMURS"):
        runner.validate_manifest(malformed)


def test_murmurs_calibration_preserves_same_host_counter_identity(tmp_path: Path) -> None:
    manifest = _murmurs_manifest()
    _validate("comparative-benchmark-manifest.schema.json", manifest)
    fake = _write_fake_executor(tmp_path)
    output = tmp_path / "murmurs-out"
    rc = runner.run(_write_manifest(tmp_path, manifest), [sys.executable, str(fake)], output)
    assert rc == 0
    runs = _load_runs(output)
    assert {record["arm"]["communication_mode"] for record in runs} == {"DEFAULT", "CAVEMAN", "MURMURS"}
    assert {record["tokens"]["counter_id"] for record in runs} == {"fixture-provider-counter-v1"}
    assert all(record["tokens"]["source"] == "HOST_REPORTED" for record in runs)
    for record in runs:
        _validate("comparative-benchmark-run.schema.json", record)
        assert record["a5_shadow_observation"] is None
    _validate("comparative-benchmark-experiment.schema.json", json.loads((output / "experiment.json").read_text(encoding="utf-8")))


def test_interaction_calibration_records_variable_topology_without_reclassifying_isolated_results(tmp_path: Path) -> None:
    manifest = _interaction_manifest()
    _validate("comparative-benchmark-manifest.schema.json", manifest)
    fake = _write_fake_executor(tmp_path)
    output = tmp_path / "interaction-out"
    rc = runner.run(_write_manifest(tmp_path, manifest), [sys.executable, str(fake)], output)
    assert rc == 0
    experiment = json.loads((output / "experiment.json").read_text(encoding="utf-8"))
    _validate("comparative-benchmark-experiment.schema.json", experiment)
    assert experiment["murmurs_evaluation"]["fixed_topology"] is False
    assert experiment["interaction_evaluation"]["isolated_a5_evidence_digest"] == A5_EVIDENCE_DIGEST
    assert experiment["interaction_evaluation"]["isolated_murmurs_evidence_digest"] == MURMURS_EVIDENCE_DIGEST
    assert experiment["interaction_evaluation"]["interaction_state"] == "NOT_YET_EVALUATED"


def test_invalid_a5_executor_run_is_retained_and_schema_valid(tmp_path: Path) -> None:
    manifest = _a5_manifest()
    manifest["tasks"] = [_task("task-invalid", force_nonzero=True)]
    manifest["repetitions_per_arm"] = 1
    fake = _write_fake_executor(tmp_path)
    output = tmp_path / "invalid-out"
    rc = runner.run(_write_manifest(tmp_path, manifest), [sys.executable, str(fake)], output)
    assert rc == 2
    runs = _load_runs(output)
    assert len(runs) == 2
    assert all(record["outcome"]["status"] == "INVALID_RUN" for record in runs)
    assert all(record["a5_shadow_observation"] is None for record in runs)
    for record in runs:
        _validate("comparative-benchmark-run.schema.json", record)
    experiment = json.loads((output / "experiment.json").read_text(encoding="utf-8"))
    _validate("comparative-benchmark-experiment.schema.json", experiment)
    assert experiment["status"] == "INVALIDATED"
    assert experiment["conclusion"] == "INVALIDATED"
    assert json.loads((output / "run-index.json").read_text(encoding="utf-8"))["invalid_run_count"] == 2
    assert len(list((output / "partial-evidence").glob("*.json"))) == 2


def test_synthetic_fixture_is_not_live_benefit_evidence() -> None:
    record = json.loads((ROOT / "machine" / "benchmarking" / "shared-benchmark-harness-implementation.v1.json").read_text(encoding="utf-8"))
    assert record["claim_boundary"]["synthetic_fixture_execution_is_benefit_evidence"] is False
    assert record["authority_boundary"]["a5_topology_effective"] is False
    assert record["resource_boundary"]["paid_provider_calls_authorized_by_b1_implementation"] is False
