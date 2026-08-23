from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.a5_topology_benchmark_executor import digest_json, load_envelope
from scripts.b2_real_calibration_preflight import ROOT, static_preflight


FREEZE = ROOT / "machine" / "benchmarking" / "b2-real-calibration-freeze.v1.json"
ENVELOPE = ROOT / "machine" / "benchmarking" / "b2-real-calibration-eligibility-envelope.v1.json"
SCHEMA = ROOT / "machine" / "schemas" / "adaptive-topology-eligibility-envelope.schema.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_b2_2_static_preflight_passes_with_zero_live_calls():
    result = static_preflight()
    assert result["status"] == "PASS_STATIC_ZERO_LIVE_CALLS"
    assert result["live_model_calls"] == 0
    assert result["planned_runs"] == 20
    assert result["maximum_underlying_model_calls"] == 60
    assert result["canonical_envelope"] is True


def test_b2_2_eligibility_envelope_is_schema_valid_and_canonical():
    raw = load(ENVELOPE)
    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(raw)
    normalized, envelope, envelope_digest = load_envelope(ENVELOPE)
    freeze = load(FREEZE)
    assert raw == normalized == envelope.to_dict()
    assert envelope_digest == freeze["topology"]["eligibility_envelope_digest"]
    assert list(envelope.candidate_ids) == [
        "b2.seq.clockwork-overseer.v1",
        "b2.seq.overseer-clockwork.v1",
    ]


def test_b2_2_changes_only_sequential_specialist_order():
    freeze = load(FREEZE)
    _, envelope, _ = load_envelope(ENVELOPE)
    first, second = envelope.candidates
    assert [stage.specialists[0] for stage in first.stages] == ["clockwork", "overseer"]
    assert [stage.specialists[0] for stage in second.stages] == ["overseer", "clockwork"]
    assert all(stage.mode == "SEQUENTIAL" for candidate in envelope.candidates for stage in candidate.stages)
    assert first.required_specialists == second.required_specialists == ("clockwork", "overseer")
    assert freeze["topology"]["parallel_execution_authorized"] is False
    assert freeze["topology"]["topology_effective"] is False
    assert freeze["topology"]["shadow_influenced_execution"] is False


def test_b2_2_resource_and_authority_boundaries_are_frozen():
    freeze = load(FREEZE)
    resource = freeze["resource_freeze"]
    assert resource == {
        "per_run_total_token_ceiling": 75000,
        "cumulative_accepted_token_ceiling": 1200000,
        "maximum_benchmark_runs": 20,
        "maximum_underlying_model_calls": 60,
        "model_calls_per_run": 3,
        "call_timeout_seconds": 600,
        "automatic_retry": False,
        "stop_on_first_invalid_run": True,
    }
    assert digest_json(resource) == freeze["resource_budget_digest"]
    assert freeze["activation"]["live_execution_authorized"] is False
    assert freeze["activation"]["separate_explicit_human_live_execution_authorization_required"] is True
    assert freeze["authority"]["a5_execution_effective_promotion"] is False
    assert freeze["authority"]["a6_authorized"] is False
    assert freeze["authority"]["b4_authorized"] is False


def test_b2_2_reuses_frozen_five_task_identity_without_semantic_redefinition():
    freeze = load(FREEZE)
    taskset = load(ROOT / freeze["task_set"]["source"])
    assert freeze["task_set"]["aggregate_digest"] == "fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8"
    assert freeze["task_set"]["validator"] == "EXACT_JSON_CONFORMANCE_V1"
    assert len(freeze["task_set"]["tasks"]) == len(taskset["tasks"]) == 5
    source = {task["task_id"]: task for task in taskset["tasks"]}
    for frozen in freeze["task_set"]["tasks"]:
        actual = source[frozen["task_id"]]
        for field in (
            "task_class",
            "starting_state_digest",
            "task_prompt_digest",
            "task_payload_digest",
            "validation_contract_digest",
        ):
            assert frozen[field] == actual[field]


def test_b2_2_host_preflight_is_version_only_and_not_live_execution_authority():
    freeze = load(FREEZE)
    preflight = freeze["zero_call_preflight"]
    assert preflight["model_calls_permitted"] == 0
    assert preflight["host_preflight_may_invoke"] == "CODEX_VERSION_ONLY"
    assert preflight["host_preflight_may_not_invoke"] == "CODEX_EXEC"
    assert freeze["host_binding"]["cli_version"] == "0.148.0"
    assert freeze["host_binding"]["model"] == "gpt-5.6-sol"
    assert freeze["host_binding"]["reasoning_effort"] == "medium"
