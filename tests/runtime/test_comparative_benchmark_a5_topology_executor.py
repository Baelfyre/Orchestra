from __future__ import annotations

import json
import subprocess
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
    validate_candidate_for_b2,
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
        return {
            "response": response,
            "usage": {"input_tokens": tokens - 10, "cached_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 2},
            "total_tokens": tokens,
            "elapsed_ms": 5,
            "agent_message_count": 1,
        }

    return fake_call, prompts


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
    with pytest.raises(Exception, match="does not authorize PARALLEL"):
        validate_candidate_for_b2(request, envelope, digest_json(envelope.to_dict()))


def test_execute_forward_topology_uses_three_bounded_calls_and_aggregates_tokens(tmp_path: Path):
    envelope = make_envelope()
    request = make_request(envelope, "clockwork-then-overseer")
    expected = request["task_payload"]["validation_contract"]["expected_response"]
    fake_call, prompts = call_factory(expected, tokens=100)
    result = execute_request(
        request,
        envelope=envelope,
        eligibility_digest=digest_json(envelope.to_dict()),
        expected_cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        command_prefix=("node", "codex.js"),
        workspace=tmp_path,
        call_timeout_seconds=30,
        per_run_total_token_ceiling=1000,
        call_runner=fake_call,
        version_runner=fake_version_ok,
        git_runner=fake_git_ok,
    )
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
    result = execute_request(
        request,
        envelope=envelope,
        eligibility_digest=digest_json(envelope.to_dict()),
        expected_cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        command_prefix=("node", "codex.js"),
        workspace=tmp_path,
        call_timeout_seconds=30,
        per_run_total_token_ceiling=1000,
        call_runner=fake_call,
        version_runner=fake_version_ok,
        git_runner=fake_git_ok,
    )
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
    result = execute_request(
        request,
        envelope=envelope,
        eligibility_digest=digest_json(envelope.to_dict()),
        expected_cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        command_prefix=("node", "codex.js"),
        workspace=tmp_path,
        call_timeout_seconds=30,
        per_run_total_token_ceiling=350,
        call_runner=fake_call,
        version_runner=fake_version_ok,
        git_runner=fake_git_ok,
    )
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
    result = execute_request(
        request,
        envelope=envelope,
        eligibility_digest=digest_json(envelope.to_dict()),
        expected_cli_version="0.148.0",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        command_prefix=("node", "codex.js"),
        workspace=tmp_path,
        call_timeout_seconds=30,
        per_run_total_token_ceiling=1000,
        call_runner=fake_call,
        version_runner=fake_version_ok,
        git_runner=fake_git_ok,
    )
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
