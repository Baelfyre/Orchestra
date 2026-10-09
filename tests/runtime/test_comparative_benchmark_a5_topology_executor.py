from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.topology import (
    REQUIRED_TOPOLOGY_INVARIANTS,
    TopologyCandidate,
    TopologyEligibilityEnvelope,
    TopologyStage,
)
from scripts.a5_topology_benchmark_executor import (
    SPECIALIST_PROJECTIONS,
    digest_json,
    execute_request,
    make_shadow_observation,
    run_codex_call,
    validate_candidate_for_b2,
)
from scripts.b2_confirmatory_evidence import (
    B2EvidenceError,
    MAX_RETAINED_ADVISORY_UTF8_BYTES,
    build_counter_identity,
    build_response_evidence,
    build_usage_evidence,
    classify_counter_stability,
    recompute_context_transfer_ledger,
)


def make_candidate(candidate_id: str, order: tuple[str, str]) -> TopologyCandidate:
    return TopologyCandidate(
        candidate_id=candidate_id,
        coordination_contract_revision=1,
        required_specialists=("clockwork", "overseer"),
        stages=tuple(
            TopologyStage(
                stage_id=f"{candidate_id}.{index}",
                mode="SEQUENTIAL",
                specialists=(specialist,),
                join_required=True,
                review_owner="overseer" if specialist == "overseer" else None,
            )
            for index, specialist in enumerate(order, start=1)
        ),
        reentry_order=(),
        prior_output_disclosure_refs=("benchmark:prior-advisory",),
        eligibility_evidence_refs=(f"benchmark:{candidate_id}:eligible",),
    )


def make_envelope() -> TopologyEligibilityEnvelope:
    forward = make_candidate("clockwork-then-overseer", ("clockwork", "overseer"))
    reverse = make_candidate("overseer-then-clockwork", ("overseer", "clockwork"))
    return TopologyEligibilityEnvelope(
        envelope_id="b2.calibration.eligibility.v1",
        session_id="b2.calibration.session.v1",
        created_at="2026-08-22T23:00:00Z",
        user_key="benchmark-user",
        project_key="Baelfyre/Orchestra",
        task_session_key="b2-calibration",
        coordination_contract_ref="machine/adaptive/a5-tuner-topology-contract.v1.json",
        coordination_contract_revision=1,
        required_specialists=("clockwork", "overseer"),
        invariants_applied={key: True for key in REQUIRED_TOPOLOGY_INVARIANTS},
        invariant_evidence_refs=("benchmark:coordination-validated", "benchmark:governance-validated"),
        candidates=(forward, reverse),
        deterministic_topology_candidate_id="clockwork-then-overseer",
    )


def make_request(envelope: TopologyEligibilityEnvelope, candidate_id: str) -> dict:
    candidate = envelope.candidate_by_id(candidate_id)
    assert candidate is not None
    eligibility_digest = digest_json(envelope.to_dict())
    expected = {"task_id": "b2-test", "disposition": "PASS", "authority_expansion": False}
    return {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "b2-a5-isolated-calibration-v1",
        "experiment_kind": "A5_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": f"req-{candidate_id}",
        "task_id": "b2-test",
        "task_class": "VALIDATION_HEAVY",
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": candidate_id,
            "topology_candidate_id": candidate_id,
            "topology_class": "SEQUENTIAL",
            "topology_digest": digest_json(candidate.to_dict()),
            "communication_mode": "DEFAULT",
        },
        "control_identity": {"provider": "openai-codex", "model": "gpt-5.6-sol", "reasoning_setting": "medium"},
        "task_payload": {
            "execution_allowed": True,
            "prompt": "Return exactly one JSON object with task_id=b2-test, disposition=PASS, authority_expansion=false.",
            "validation_contract": {"validator_type": "EXACT_JSON_CONFORMANCE_V1", "expected_response": expected},
        },
        "a5_evaluation": {
            "eligibility_envelope_digest": eligibility_digest,
            "eligible_topology_candidate_ids": list(envelope.candidate_ids),
        },
        "murmurs_evaluation": None,
        "interaction_evaluation": None,
    }


def fake_git_ok(*args, **kwargs):
    return subprocess.CompletedProcess(args=args[0] if args else [], returncode=0, stdout="true\n", stderr="")


def fake_version_ok(*args, **kwargs):
    return subprocess.CompletedProcess(args=args[0] if args else [], returncode=0, stdout="codex-cli 0.148.0\n", stderr="")


def call_factory(final_json: dict, *, tokens: int = 100):
    prompts: list[str] = []

    def fake_call(**kwargs):
        prompt = kwargs["prompt"]
        prompts.append(prompt)
        index = len(prompts)
        response = json.dumps(final_json, separators=(",", ":")) if "fixed benchmark finalizer" in prompt else f"advisory-{index}"
        usage = {"input_tokens": tokens - 10, "cached_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 2}
        return {
            "response": response,
            "usage": usage,
            "turn_completed_usage": dict(usage),
            "total_tokens": tokens,
            "elapsed_ms": 5,
            "agent_message_count": 1,
        }

    return fake_call, prompts


def execute_with_fixtures(request: dict, envelope: TopologyEligibilityEnvelope, tmp_path: Path, call_runner, *, ceiling: int = 1000):
    return execute_request(
        request,
        envelope=envelope,
        eligibility_digest=digest_json(envelope.to_dict()),
        expected_cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        command_prefix=("node", "codex.js"),
        workspace=tmp_path,
        call_timeout_seconds=30,
        per_run_total_token_ceiling=ceiling,
        call_runner=call_runner,
        version_runner=fake_version_ok,
        git_runner=fake_git_ok,
    )


def test_b2_binding_requires_exact_frozen_candidate_digest():
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    eligibility_digest = digest_json(envelope.to_dict())
    candidate = validate_candidate_for_b2(request, envelope, eligibility_digest)
    assert candidate.candidate_id == "clockwork-then-overseer"
    request["arm"]["topology_digest"] = "0" * 64
    with pytest.raises(Exception, match="topology digest"):
        validate_candidate_for_b2(request, envelope, eligibility_digest)


def test_b2_binding_rejects_parallel_stage_even_when_structurally_eligible():
    envelope = make_envelope()
    forward = envelope.candidates[0]
    parallel = TopologyCandidate(
        candidate_id="parallel",
        coordination_contract_revision=1,
        required_specialists=forward.required_specialists,
        stages=(TopologyStage(stage_id="parallel.1", mode="PARALLEL", specialists=("clockwork", "overseer"), join_required=True, review_owner="overseer"),),
        reentry_order=(),
        prior_output_disclosure_refs=(),
        eligibility_evidence_refs=("benchmark:parallel:eligible",),
    )
    envelope = TopologyEligibilityEnvelope(
        envelope_id="parallel-env",
        session_id=envelope.session_id,
        created_at=envelope.created_at,
        user_key=envelope.user_key,
        project_key=envelope.project_key,
        task_session_key=envelope.task_session_key,
        coordination_contract_ref=envelope.coordination_contract_ref,
        coordination_contract_revision=1,
        required_specialists=envelope.required_specialists,
        invariants_applied=envelope.invariants_applied,
        invariant_evidence_refs=envelope.invariant_evidence_refs,
        candidates=(forward, parallel),
        deterministic_topology_candidate_id=forward.candidate_id,
    )
    request = make_request(envelope, "parallel")
    with pytest.raises(Exception, match="B2.1"):
        validate_candidate_for_b2(request, envelope, digest_json(envelope.to_dict()))


def test_execute_forward_topology_uses_three_bounded_calls_and_aggregates_tokens(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected, tokens=100)
    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "PASS"
    assert result["tokens"]["input_tokens"] == 270
    assert result["tokens"]["output_tokens"] == 30
    assert result["raw_evidence"]["observed_total_tokens"] == 300
    assert result["coordination"]["specialist_messages"] == 2
    assert result["coordination"]["handoffs"] == 1
    assert len(prompts) == 3
    assert SPECIALIST_PROJECTIONS["clockwork"] in prompts[0]
    assert SPECIALIST_PROJECTIONS["overseer"] in prompts[1]
    assert "PRIOR ADVISORY: CLOCKWORK" in prompts[1]
    assert "fixed benchmark finalizer" in prompts[2]
    assert result["a5_shadow_observation"]["topology_effective"] is False
    assert result["a5_shadow_observation"]["shadow_influenced_execution"] is False


def test_reverse_candidate_changes_only_specialist_stage_order(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "overseer-then-clockwork")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected)
    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "PASS"
    assert SPECIALIST_PROJECTIONS["overseer"] in prompts[0]
    assert SPECIALIST_PROJECTIONS["clockwork"] in prompts[1]
    assert "PRIOR ADVISORY: OVERSEER" in prompts[1]
    assert result["raw_evidence"]["candidate_stage_order"][0]["specialists"] == ["overseer"]


def test_ceiling_breach_stops_before_fixed_finalizer(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected, tokens=200)
    result = execute_with_fixtures(request, envelope, tmp_path, fake_call, ceiling=350)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert len(prompts) == 2
    assert result["a5_shadow_observation"] is None


def test_execution_allowed_false_fails_before_any_model_call(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    request["task_payload"]["execution_allowed"] = False
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected)
    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert prompts == []


def test_shadow_observation_uses_same_frozen_eligible_set():
    envelope = make_envelope()
    observation = make_shadow_observation(envelope, digest_json(envelope.to_dict()))
    assert observation["ranked_topology_candidate_ids"] == list(envelope.candidate_ids)
    assert observation["top_candidate_id"] in envelope.candidate_ids
    assert observation["topology_effective"] is False
    assert observation["shadow_influenced_execution"] is False
    assert len(observation["decision_digest"]) == 64


def test_b2_3_1_retains_utf8_advisories_and_recomputes_context_transfer(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    responses = ["architecture café ✅", "validation Δ", json.dumps(expected, separators=(",", ":"))]
    prompts: list[str] = []

    def fake_call(**kwargs):
        prompts.append(kwargs["prompt"])
        response = responses[len(prompts) - 1]
        usage = {"input_tokens": 90, "cached_input_tokens": 10, "output_tokens": 10, "reasoning_output_tokens": 2}
        return {"response": response, "usage": usage, "turn_completed_usage": dict(usage), "total_tokens": 100, "elapsed_ms": 5, "agent_message_count": 1}

    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "PASS"
    calls = result["raw_evidence"]["calls"]
    first, second, finalizer = calls
    first_raw = responses[0].encode("utf-8")
    second_raw = responses[1].encode("utf-8")
    assert first["response_text"] == responses[0]
    assert first["response_encoding"] == "UTF-8"
    assert first["response_utf8_bytes"] == len(first_raw)
    assert first["response_utf8_sha256"] == sha256(first_raw).hexdigest()
    assert first["prior_advisory_inputs"] == []
    assert second["prior_advisory_inputs"][0]["response_utf8_sha256"] == first["response_utf8_sha256"]
    assert [ref["specialist"] for ref in finalizer["advisory_inputs"]] == ["clockwork", "overseer"]
    expected_context = len(first_raw) + len(first_raw) + len(second_raw)
    ledger = result["raw_evidence"]["context_transfer_recomputation"]
    assert ledger["downstream_specialist_handoff_bytes"] == len(first_raw)
    assert ledger["finalizer_advisory_bytes"] == len(first_raw) + len(second_raw)
    assert ledger["recomputed_context_transfer_bytes"] == expected_context
    assert result["communication"]["context_transfer_bytes"] == expected_context


def test_context_transfer_mismatch_is_rejected():
    specialist_calls = [
        {"prior_advisory_inputs": []},
        {"prior_advisory_inputs": [{"response_utf8_bytes": 5}]},
    ]
    finalizer = {"advisory_inputs": [{"response_utf8_bytes": 5}, {"response_utf8_bytes": 7}]}
    assert recompute_context_transfer_ledger(specialist_calls=specialist_calls, finalizer_call=finalizer)["recomputed_context_transfer_bytes"] == 17
    with pytest.raises(B2EvidenceError, match="does not equal recomputed"):
        recompute_context_transfer_ledger(
            specialist_calls=specialist_calls,
            finalizer_call=finalizer,
            reported_context_transfer_bytes=16,
        )


def test_advisory_retention_ceiling_fails_closed_before_next_call(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    prompts: list[str] = []

    def fake_call(**kwargs):
        prompts.append(kwargs["prompt"])
        usage = {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 0}
        return {"response": "x" * (MAX_RETAINED_ADVISORY_UTF8_BYTES + 1), "usage": usage, "turn_completed_usage": dict(usage), "total_tokens": 20, "elapsed_ms": 1, "agent_message_count": 1}

    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert len(prompts) == 1
    assert result["raw_evidence"]["rejected_advisory"]["response_utf8_bytes"] == MAX_RETAINED_ADVISORY_UTF8_BYTES + 1
    assert "response_text" not in result["raw_evidence"]["rejected_advisory"]


def test_usage_object_is_preserved_exactly_and_digest_bound():
    identity = build_counter_identity(
        counter_id="counter",
        prompt_digest="a" * 64,
        role="SPECIALIST",
        specialist="clockwork",
        cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        transport="jsonl-usage",
        workspace_identity="b" * 64,
    )
    usage = {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 20, "reasoning_output_tokens": 5, "provider_extension": 7}
    evidence = build_usage_evidence(raw_usage=usage, counter_identity=identity)
    assert evidence["turn_completed_usage"] == usage
    assert evidence["turn_completed_usage_digest"] == digest_json(usage)
    assert evidence["non_cached_input_tokens"] == 60
    assert evidence["counter_stability_key"] == identity["counter_stability_key"]
    assert evidence["counter_stability_classification"] is None


def _counter_record(key: str, input_tokens: int, cached_input_tokens: int) -> dict:
    return {
        "counter_stability_key": key,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
    }


def test_counter_stability_classification_fixtures():
    key = "c" * 64
    assert classify_counter_stability([_counter_record(key, 100, 20), _counter_record(key, 100, 20)]) == "STABLE_EXACT"
    assert classify_counter_stability([_counter_record(key, 100, 20), _counter_record(key, 100, 30)]) == "CACHE_STATE_VARIANT"
    assert classify_counter_stability([_counter_record(key, 100, 20), _counter_record(key, 101, 20)]) == "INPUT_COUNTER_VARIANT"
    assert classify_counter_stability([_counter_record(key, 100, 20), _counter_record("d" * 64, 100, 20)]) == "UNSTABLE_ATTRIBUTION"
    assert classify_counter_stability([_counter_record(key, 100, 20)]) == "UNSTABLE_ATTRIBUTION"


def test_cached_input_greater_than_input_is_rejected():
    identity = build_counter_identity(
        counter_id="counter",
        prompt_digest="a" * 64,
        role="SPECIALIST",
        specialist="clockwork",
        cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        transport="jsonl-usage",
        workspace_identity="b" * 64,
    )
    with pytest.raises(B2EvidenceError, match="cannot exceed"):
        build_usage_evidence(
            raw_usage={"input_tokens": 10, "cached_input_tokens": 11, "output_tokens": 2, "reasoning_output_tokens": 1},
            counter_identity=identity,
        )


def test_executor_rejects_invalid_cached_counter_before_next_call(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    prompts: list[str] = []

    def fake_call(**kwargs):
        prompts.append(kwargs["prompt"])
        usage = {"input_tokens": 10, "cached_input_tokens": 11, "output_tokens": 2, "reasoning_output_tokens": 1}
        return {"response": "advisory", "usage": usage, "turn_completed_usage": dict(usage), "total_tokens": 12, "elapsed_ms": 1, "agent_message_count": 1}

    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert len(prompts) == 1
    assert result["raw_evidence"]["rejected_turn_completed_usage"]["cached_input_tokens"] == 11


@pytest.mark.parametrize("response", ["advisory", "advisory-雪"])
def test_run_codex_call_preserves_exact_turn_completed_usage_with_zero_live_call(tmp_path: Path, response: str):
    usage = {"input_tokens": 21, "cached_input_tokens": 3, "output_tokens": 4, "reasoning_output_tokens": 2, "provider_extension": 9}
    raw = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "t"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": response}}, ensure_ascii=False),
            json.dumps({"type": "turn.completed", "usage": usage}),
        ]
    )
    observed_commands: list[list[str]] = []
    observed_kwargs: list[dict] = []

    def fake_process(command, **kwargs):
        observed_commands.append(command)
        observed_kwargs.append(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=raw, stderr="")

    call = run_codex_call(
        prompt="synthetic",
        prefix=("node", "codex.js"),
        workspace=tmp_path,
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        timeout_seconds=30,
        run_command=fake_process,
    )
    assert len(observed_commands) == 1
    assert observed_kwargs == [{"capture_output": True, "text": True, "encoding": "utf-8", "errors": "strict", "check": False, "shell": False, "timeout": 30}]
    assert call["turn_completed_usage"] == usage
    assert call["usage"] == {key: usage[key] for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}
    assert call["response"] == response
    assert build_response_evidence(call["response"])["response_utf8_sha256"] == sha256(response.encode("utf-8")).hexdigest()


def test_run_codex_call_fails_closed_on_invalid_utf8_without_live_call(tmp_path: Path):
    def fake_process(_command, **kwargs):
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["errors"] == "strict"
        raise UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte")

    def fake_call(**kwargs):
        return run_codex_call(**kwargs, run_command=fake_process)

    envelope = make_envelope()
    result = execute_with_fixtures(make_request(envelope, "clockwork-then-overseer"), envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "invalid start byte" in result["raw_evidence"]["error"]


def test_fixture_integration_uses_only_injected_fake_runners(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected)
    result = execute_with_fixtures(request, envelope, tmp_path, fake_call)
    assert result["outcome"]["status"] == "PASS"
    assert len(prompts) == 3
    assert result["raw_evidence"]["counter_stability_evaluation_scope"] == "CROSS_RUN_RECONCILIATION_REQUIRED"
    for call in result["raw_evidence"]["calls"]:
        assert len(call["turn_completed_usage_digest"]) == 64
        assert len(call["counter_stability_key"]) == 64
        assert call["counter_stability_classification"] is None
