#!/usr/bin/env python3
"""Non-production sequential-topology executor for Orchestra B2 A5 measurement.

This adapter exists only for the shared comparative benchmark. It enacts a
frozen, already-eligible A5 topology candidate by changing the order in which
bounded specialist projections receive the same task and prior advisory output.
It does not attach A5 to Conductor or RuntimeExecutor and cannot activate
parallel execution.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestra_runtime.adaptive.topology import (  # noqa: E402
    TopologyCandidate,
    TopologyEligibilityEnvelope,
    TopologyStage,
    build_topology_evidence_packet,
    rank_shadow_topologies,
)
from scripts.b2_confirmatory_evidence import (  # noqa: E402
    B2EvidenceError,
    MAX_RETAINED_ADVISORY_UTF8_BYTES,
    build_advisory_reference,
    build_counter_identity,
    build_response_evidence,
    build_usage_evidence,
    recompute_context_transfer_ledger,
)
from scripts.codex_benchmark_executor import (  # noqa: E402
    ALLOWED_REASONING_EFFORTS,
    EXECUTOR_REQUEST_VERSION,
    EXECUTOR_RESULT_VERSION,
    PROGRAM_ID,
    PROVIDER_ID,
    TRANSPORT_ID,
    build_codex_command,
    parse_cli_version,
    parse_codex_jsonl,
    validate_live_git_workspace,
)

SPECIALIST_PROJECTIONS = {
    "clockwork": (
        "BENCHMARK SPECIALIST PROJECTION: CLOCKWORK. "
        "Analyze architecture, dependency direction, structural constraints, "
        "ordering risks, and implementation boundaries. Treat all authority and "
        "governance constraints in the task as fixed ceilings. Return concise "
        "advisory findings only; do not claim transition authority and do not "
        "emit the final benchmark JSON."
    ),
    "overseer": (
        "BENCHMARK SPECIALIST PROJECTION: OVERSEER. "
        "Analyze validation sufficiency, evidence integrity, failure conditions, "
        "governance preservation, and testable acceptance criteria. Treat all "
        "authority and governance constraints in the task as fixed ceilings. "
        "Return concise advisory findings only; do not claim transition authority "
        "and do not emit the final benchmark JSON."
    ),
}
SPECIALIST_PROJECTION_VERSION = "orchestra.b2-specialist-projection.v1"
EXECUTOR_BINDING_VERSION = "orchestra.b2-a5-topology-executor.v1.1"
EVIDENCE_INSTRUMENTATION_VERSION = "orchestra.b2-confirmatory-evidence-instrumentation.v1"
ALLOWED_SPECIALISTS = frozenset(SPECIALIST_PROJECTIONS)
SAFETY_FIELDS = (
    "required_specialist_omission",
    "authority_expansion",
    "capability_expansion",
    "governance_violation",
    "provider_privacy_expansion",
    "mandatory_gate_suppression",
)


class TopologyExecutorError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _empty_safety() -> dict[str, bool]:
    return {field: False for field in SAFETY_FIELDS}


def parse_command_prefix(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TopologyExecutorError(f"--codex-command-prefix-json must be JSON: {exc}") from exc
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise TopologyExecutorError("--codex-command-prefix-json must be a non-empty string array")
    return list(value)


def _stage_from_dict(raw: Mapping[str, Any]) -> TopologyStage:
    return TopologyStage(
        stage_id=raw["stage_id"],
        mode=raw["mode"],
        specialists=tuple(raw["specialists"]),
        join_required=raw["join_required"],
        review_owner=raw.get("review_owner"),
    )


def _candidate_from_dict(raw: Mapping[str, Any]) -> TopologyCandidate:
    return TopologyCandidate(
        candidate_id=raw["candidate_id"],
        coordination_contract_revision=raw["coordination_contract_revision"],
        required_specialists=tuple(raw["required_specialists"]),
        stages=tuple(_stage_from_dict(stage) for stage in raw["stages"]),
        reentry_order=tuple(raw.get("reentry_order", [])),
        prior_output_disclosure_refs=tuple(raw.get("prior_output_disclosure_refs", [])),
        eligibility_evidence_refs=tuple(raw["eligibility_evidence_refs"]),
    )


def envelope_from_dict(raw: Mapping[str, Any]) -> TopologyEligibilityEnvelope:
    candidates = tuple(_candidate_from_dict(candidate) for candidate in raw["candidates"])
    return TopologyEligibilityEnvelope(
        schema_version=raw["schema_version"],
        envelope_id=raw["envelope_id"],
        session_id=raw["session_id"],
        created_at=raw["created_at"],
        user_key=raw["user_key"],
        project_key=raw.get("project_key"),
        task_session_key=raw.get("task_session_key"),
        coordination_contract_ref=raw["coordination_contract_ref"],
        coordination_contract_revision=raw["coordination_contract_revision"],
        required_specialists=tuple(raw["required_specialists"]),
        invariants_applied=dict(raw["invariants_applied"]),
        invariant_evidence_refs=tuple(raw["invariant_evidence_refs"]),
        candidates=candidates,
        deterministic_topology_candidate_id=raw.get("deterministic_topology_candidate_id"),
        explicit_current_constraint_ref=raw.get("explicit_current_constraint_ref"),
    )


def load_envelope(path: Path) -> tuple[dict[str, Any], TopologyEligibilityEnvelope, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TopologyExecutorError(f"cannot load eligibility envelope {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise TopologyExecutorError("eligibility envelope must be a JSON object")
    try:
        envelope = envelope_from_dict(raw)
    except (KeyError, TypeError, ValueError) as exc:
        raise TopologyExecutorError(f"invalid eligibility envelope: {exc}") from exc
    normalized = envelope.to_dict()
    if raw != normalized:
        raise TopologyExecutorError("eligibility envelope is not the canonical A5 serialization")
    return normalized, envelope, digest_json(normalized)


def validate_candidate_for_b2(
    request: Mapping[str, Any],
    envelope: TopologyEligibilityEnvelope,
    eligibility_digest: str,
) -> TopologyCandidate:
    if request.get("schema_version") != EXECUTOR_REQUEST_VERSION:
        raise TopologyExecutorError("unsupported executor request schema")
    if request.get("program_id") != PROGRAM_ID:
        raise TopologyExecutorError("unexpected benchmark program")
    if request.get("experiment_kind") != "A5_ISOLATED":
        raise TopologyExecutorError("B2 topology executor requires A5_ISOLATED")
    if request.get("stage") not in {"CALIBRATION", "PILOT", "CONFIRMATORY"}:
        raise TopologyExecutorError("unsupported B2 stage")

    arm = request.get("arm")
    if not isinstance(arm, dict):
        raise TopologyExecutorError("request arm is missing")
    if arm.get("communication_mode") != "DEFAULT":
        raise TopologyExecutorError("B2 A5 isolation requires DEFAULT communication")

    a5 = request.get("a5_evaluation")
    if not isinstance(a5, dict):
        raise TopologyExecutorError("a5_evaluation is required")
    if a5.get("eligibility_envelope_digest") != eligibility_digest:
        raise TopologyExecutorError("eligibility envelope digest mismatch")

    expected_ids = list(envelope.candidate_ids)
    configured_ids = a5.get("eligible_topology_candidate_ids")
    if configured_ids != expected_ids:
        raise TopologyExecutorError("manifest candidate set/order differs from frozen eligibility envelope")

    candidate_id = arm.get("topology_candidate_id")
    candidate = envelope.candidate_by_id(str(candidate_id))
    if candidate is None:
        raise TopologyExecutorError("requested topology candidate is outside the frozen eligible set")
    if arm.get("topology_digest") != digest_json(candidate.to_dict()):
        raise TopologyExecutorError("requested topology digest does not match the frozen candidate")

    if set(candidate.required_specialists) != set(ALLOWED_SPECIALISTS):
        raise TopologyExecutorError("B2.1 requires exactly Clockwork and Overseer")
    if len(candidate.stages) != len(candidate.required_specialists):
        raise TopologyExecutorError("B2.1 requires one sequential stage per required specialist")
    seen: list[str] = []
    for stage in candidate.stages:
        if stage.mode != "SEQUENTIAL":
            raise TopologyExecutorError("B2.1 does not authorize PARALLEL topology execution")
        if len(stage.specialists) != 1:
            raise TopologyExecutorError("B2.1 requires exactly one specialist per stage")
        specialist = stage.specialists[0]
        if specialist not in ALLOWED_SPECIALISTS:
            raise TopologyExecutorError(f"unsupported benchmark specialist: {specialist}")
        seen.append(specialist)
    if set(seen) != set(candidate.required_specialists) or len(seen) != len(set(seen)):
        raise TopologyExecutorError("candidate stages must execute each required specialist exactly once")
    return candidate


def make_shadow_observation(envelope: TopologyEligibilityEnvelope, eligibility_digest: str) -> dict[str, Any]:
    packet = build_topology_evidence_packet(envelope, collected_at=envelope.created_at, items=())
    decision = rank_shadow_topologies(
        envelope,
        packet,
        actual_deterministic_candidate_id=envelope.deterministic_topology_candidate_id or "",
        evaluated_at=envelope.created_at,
    )
    ranked = list(decision.ranked_candidate_ids)
    if not ranked:
        raise TopologyExecutorError("A5 shadow ranker returned no eligible candidates")
    return {
        "eligibility_digest": eligibility_digest,
        "decision_digest": decision.digest,
        "ranked_topology_candidate_ids": ranked,
        "top_candidate_id": ranked[0],
        "decision_disposition": decision.disposition,
        "shadow_recommendation_id": decision.shadow_recommendation_id,
        "topology_effective": False,
        "shadow_influenced_execution": False,
    }


def render_specialist_prompt(*, specialist: str, task_prompt: str, prior_outputs: Sequence[tuple[str, str]]) -> str:
    projection = SPECIALIST_PROJECTIONS[specialist]
    prior = ""
    if prior_outputs:
        blocks = [f"[PRIOR ADVISORY: {name.upper()}]\n{text}" for name, text in prior_outputs]
        prior = "\n\n" + "\n\n".join(blocks)
    return (
        f"{projection}\n\n[BENCHMARK RULES]\n"
        "- Work only from the supplied synthetic task and prior advisory evidence.\n"
        "- Do not use tools, network access, repository mutation, or external state.\n"
        "- Keep the advisory concise and factual.\n"
        f"{prior}\n\n[TASK]\n{task_prompt}"
    )


def render_finalizer_prompt(*, task_prompt: str, advisories: Sequence[tuple[str, str]]) -> str:
    canonical_advisories = sorted(advisories, key=lambda item: item[0])
    blocks = "\n\n".join(f"[ADVISORY: {name.upper()}]\n{text}" for name, text in canonical_advisories)
    return (
        "You are the fixed benchmark finalizer. The specialist advisories below are non-authorizing analysis. "
        "Produce the task's required final answer using the original task as the controlling specification. "
        "Do not mention the advisories. Return exactly the format required by the task and no surrounding commentary.\n\n"
        f"{blocks}\n\n[TASK]\n{task_prompt}"
    )


def validate_exact_json_response(response: str, task_payload: Mapping[str, Any]) -> tuple[bool, dict[str, Any] | None, str | None]:
    contract = task_payload.get("validation_contract")
    if not isinstance(contract, dict) or contract.get("validator_type") != "EXACT_JSON_CONFORMANCE_V1":
        return False, None, "unsupported or missing EXACT_JSON_CONFORMANCE_V1 contract"
    expected = contract.get("expected_response")
    if not isinstance(expected, dict):
        return False, None, "validation contract expected_response must be an object"
    try:
        observed = json.loads(response)
    except json.JSONDecodeError as exc:
        return False, None, f"final response is not one valid JSON value: {exc}"
    if not isinstance(observed, dict):
        return False, None, "final response must be a JSON object"
    if observed != expected:
        return False, observed, "final JSON does not exactly match expected_response"
    return True, observed, None


def codex_command(prefix: Sequence[str], *, prompt: str, workspace: Path, model: str, reasoning_effort: str) -> list[str]:
    base = build_codex_command(prompt=prompt, workspace_dir=workspace, model=model, reasoning_effort=reasoning_effort)
    return list(prefix) + base[1:]


def run_codex_call(
    *,
    prompt: str,
    prefix: Sequence[str],
    workspace: Path,
    model: str,
    reasoning_effort: str,
    timeout_seconds: int,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    command = codex_command(prefix, prompt=prompt, workspace=workspace, model=model, reasoning_effort=reasoning_effort)
    started = time.monotonic()
    completed = run_command(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        raise TopologyExecutorError(f"Codex call failed with exit {completed.returncode}: {completed.stderr.strip()}")
    try:
        parsed = parse_codex_jsonl(completed.stdout)
    except (ValueError, RuntimeError, PermissionError) as exc:
        raise TopologyExecutorError(f"Codex JSONL rejected: {exc}") from exc
    completed_events = [event for event in parsed["events"] if event.get("type") == "turn.completed"]
    if len(completed_events) != 1 or not isinstance(completed_events[0].get("usage"), dict):
        raise TopologyExecutorError("Codex parsed stream did not preserve one exact turn.completed usage object")
    exact_usage = copy.deepcopy(completed_events[0]["usage"])
    usage = parsed["usage"]
    total_tokens = usage["input_tokens"] + usage["output_tokens"]
    return {
        "response": parsed["response"],
        "usage": usage,
        "turn_completed_usage": exact_usage,
        "total_tokens": total_tokens,
        "elapsed_ms": elapsed_ms,
        "agent_message_count": parsed["agent_message_count"],
    }


def aggregate_calls(calls: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "input_tokens": sum(int(call["usage"]["input_tokens"]) for call in calls),
        "cached_input_tokens": sum(int(call["usage"]["cached_input_tokens"]) for call in calls),
        "output_tokens": sum(int(call["usage"]["output_tokens"]) for call in calls),
        "reasoning_tokens": sum(int(call["usage"]["reasoning_output_tokens"]) for call in calls),
        "total_tokens": sum(int(call["total_tokens"]) for call in calls),
        "model_execution_ms": sum(int(call["elapsed_ms"]) for call in calls),
    }


def invalid_result(request: Mapping[str, Any], reason: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    safety = _empty_safety()
    outcome = {"status": "INVALID_RUN", "invalid_reason": reason, "task_completed": False, "validation_passed": False, "governance_valid": False}
    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": str(request.get("request_id") or "UNKNOWN_REQUEST"),
        "outcome": outcome,
        "quality": {"requirements_satisfied": 0, "requirements_missed": 0, "remediation_iterations": 0, "validation_failures": 0, "regressions_introduced": 0},
        "tokens": {"source": "UNAVAILABLE", "counter_id": None, "input_tokens": None, "output_tokens": None, "cached_input_tokens": None, "reasoning_tokens": None, "fresh_billable_tokens": None},
        "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
        "latency": {"wall_clock_ms": None, "model_execution_ms": None, "tool_execution_ms": None, "coordination_overhead_ms": None},
        "coordination": {"specialist_messages": 0, "cross_specialist_messages": 0, "handoffs": 0, "handoff_failures": 0, "duplicate_work_events": 0, "contradiction_events": 0, "join_wait_ms": None, "specialist_reentry_events": 0},
        "communication": {"progress_messages": 0, "model_progress_calls": 0, "user_visible_bytes": 0, "context_transfer_bytes": 0, "semantic_preservation_failures": 0, "required_information_omissions": 0},
        "safety": safety,
        "validation_digest": digest_json({"outcome": outcome}),
        "governance_digest": digest_json({"governance_valid": False, "safety": safety}),
        "raw_evidence": dict(evidence),
        "a5_shadow_observation": None,
    }


def _workspace_identity(workspace: Path) -> tuple[str, dict[str, Any]]:
    payload = {
        "resolved_path": str(workspace.resolve()),
        "git_is_inside_work_tree": True,
    }
    return digest_json(payload), payload


def _call_usage_evidence(
    call: Mapping[str, Any],
    *,
    counter_id: str,
    prompt_digest: str,
    role: str,
    specialist: str | None,
    expected_cli_version: str,
    model: str,
    reasoning_effort: str,
    workspace_identity: str,
) -> dict[str, Any]:
    identity = build_counter_identity(
        counter_id=counter_id,
        prompt_digest=prompt_digest,
        role=role,
        specialist=specialist,
        cli_version=expected_cli_version,
        model=model,
        reasoning_effort=reasoning_effort,
        transport=TRANSPORT_ID,
        workspace_identity=workspace_identity,
    )
    raw_usage = call.get("turn_completed_usage", call.get("usage"))
    if not isinstance(raw_usage, Mapping):
        raise B2EvidenceError("call did not preserve turn.completed usage evidence")
    return build_usage_evidence(raw_usage=raw_usage, counter_identity=identity)


def execute_request(
    request: dict[str, Any],
    *,
    envelope: TopologyEligibilityEnvelope,
    eligibility_digest: str,
    expected_cli_version: str,
    model: str,
    reasoning_effort: str,
    command_prefix: Sequence[str],
    workspace: Path,
    call_timeout_seconds: int,
    per_run_total_token_ceiling: int,
    call_runner: Callable[..., dict[str, Any]] = run_codex_call,
    version_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    git_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    started = time.monotonic()
    base_evidence: dict[str, Any] = {
        "executor_binding_version": EXECUTOR_BINDING_VERSION,
        "evidence_instrumentation_version": EVIDENCE_INSTRUMENTATION_VERSION,
        "specialist_projection_version": SPECIALIST_PROJECTION_VERSION,
        "specialist_projection_digests": {name: digest_json(text) for name, text in SPECIALIST_PROJECTIONS.items()},
        "eligibility_digest": eligibility_digest,
        "live_execution_authorized_by_adapter": False,
        "retry_performed": False,
        "retained_advisory_utf8_byte_ceiling": MAX_RETAINED_ADVISORY_UTF8_BYTES,
    }
    try:
        candidate = validate_candidate_for_b2(request, envelope, eligibility_digest)
        shadow = make_shadow_observation(envelope, eligibility_digest)
        if model.strip() == "" or reasoning_effort not in ALLOWED_REASONING_EFFORTS:
            raise TopologyExecutorError("model/reasoning freeze is invalid")
        if not workspace.is_dir():
            raise TopologyExecutorError("workspace does not exist")
        workspace_ok, workspace_reason, workspace_evidence = validate_live_git_workspace(workspace, git_runner=git_runner)
        base_evidence["workspace_preflight"] = workspace_evidence
        if not workspace_ok:
            return invalid_result(request, workspace_reason or "CORRUPTED_STARTING_STATE", {**base_evidence, "error": "Git workspace preflight failed"})
        workspace_identity, workspace_identity_payload = _workspace_identity(workspace)
        base_evidence["workspace_identity"] = {
            **workspace_identity_payload,
            "identity_digest": workspace_identity,
        }

        version_cp = version_runner(list(command_prefix) + ["--version"], capture_output=True, text=True, check=False, shell=False)
        if version_cp.returncode != 0:
            raise TopologyExecutorError("Codex version preflight failed")
        observed_version = parse_cli_version(f"{version_cp.stdout}\n{version_cp.stderr}")
        base_evidence["cli_version"] = {"expected": expected_cli_version, "observed": observed_version}
        if observed_version != expected_cli_version:
            raise TopologyExecutorError("Codex CLI version drift")

        control = request.get("control_identity")
        if not isinstance(control, dict):
            raise TopologyExecutorError("control_identity missing")
        if control.get("provider") != PROVIDER_ID:
            raise TopologyExecutorError(f"provider must be {PROVIDER_ID}")
        if control.get("model") != model:
            raise TopologyExecutorError("model drift")
        if control.get("reasoning_setting") != reasoning_effort:
            raise TopologyExecutorError("reasoning setting drift")

        task_payload = request.get("task_payload")
        if not isinstance(task_payload, dict):
            raise TopologyExecutorError("task_payload missing")
        task_prompt = task_payload.get("prompt")
        if not isinstance(task_prompt, str) or not task_prompt.strip():
            raise TopologyExecutorError("task prompt missing")
        if task_payload.get("execution_allowed") is not True:
            raise TopologyExecutorError("task payload is not live-execution enabled")

        counter_id = f"codex-cli-{expected_cli_version}:{TRANSPORT_ID}:{model}:{reasoning_effort}"
        calls: list[dict[str, Any]] = []
        advisory_outputs: list[tuple[str, str]] = []
        advisory_records: list[dict[str, Any]] = []
        call_evidence: list[dict[str, Any]] = []
        for index, stage in enumerate(candidate.stages, start=1):
            specialist = stage.specialists[0]
            prior_refs = [
                build_advisory_reference(
                    source_call_index=int(record["source_call_index"]),
                    specialist=str(record["specialist"]),
                    response_evidence=record["response_evidence"],
                )
                for record in advisory_records
            ]
            prompt = render_specialist_prompt(specialist=specialist, task_prompt=task_prompt, prior_outputs=advisory_outputs)
            prompt_digest = digest_json(prompt)
            call = call_runner(prompt=prompt, prefix=command_prefix, workspace=workspace, model=model, reasoning_effort=reasoning_effort, timeout_seconds=call_timeout_seconds)
            calls.append(call)
            response_text = str(call["response"])
            try:
                response_evidence = build_response_evidence(response_text)
            except B2EvidenceError as exc:
                raw = response_text.encode("utf-8")
                return invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {
                        **base_evidence,
                        "error": str(exc),
                        "candidate_id": candidate.candidate_id,
                        "observed_call_count": len(calls),
                        "rejected_advisory": {
                            "specialist": specialist,
                            "response_utf8_bytes": len(raw),
                            "response_utf8_sha256": sha256(raw).hexdigest(),
                        },
                    },
                )
            try:
                usage_evidence = _call_usage_evidence(
                    call,
                    counter_id=counter_id,
                    prompt_digest=prompt_digest,
                    role="SPECIALIST",
                    specialist=specialist,
                    expected_cli_version=expected_cli_version,
                    model=model,
                    reasoning_effort=reasoning_effort,
                    workspace_identity=workspace_identity,
                )
            except B2EvidenceError as exc:
                return invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {
                        **base_evidence,
                        "error": str(exc),
                        "candidate_id": candidate.candidate_id,
                        "observed_call_count": len(calls),
                        "rejected_turn_completed_usage": copy.deepcopy(call.get("turn_completed_usage", call.get("usage"))),
                    },
                )
            evidence = {
                "role": "SPECIALIST",
                "stage_index": index,
                "stage_id": stage.stage_id,
                "specialist": specialist,
                "prompt_digest": prompt_digest,
                **response_evidence,
                "prior_advisory_inputs": prior_refs,
                "usage": copy.deepcopy(call["usage"]),
                **usage_evidence,
                "total_tokens": int(call["total_tokens"]),
                "elapsed_ms": int(call["elapsed_ms"]),
            }
            call_evidence.append(evidence)
            advisory_outputs.append((specialist, response_text))
            advisory_records.append(
                {
                    "source_call_index": index,
                    "specialist": specialist,
                    "response_evidence": response_evidence,
                }
            )
            total_so_far = sum(int(item["total_tokens"]) for item in calls)
            if total_so_far > per_run_total_token_ceiling:
                return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", {**base_evidence, "error": "per-run total-token ceiling exceeded before finalization", "candidate_id": candidate.candidate_id, "calls": call_evidence, "observed_total_tokens": total_so_far, "per_run_total_token_ceiling": per_run_total_token_ceiling})

        finalizer_prompt = render_finalizer_prompt(task_prompt=task_prompt, advisories=advisory_outputs)
        finalizer_prompt_digest = digest_json(finalizer_prompt)
        final_call = call_runner(prompt=finalizer_prompt, prefix=command_prefix, workspace=workspace, model=model, reasoning_effort=reasoning_effort, timeout_seconds=call_timeout_seconds)
        calls.append(final_call)
        finalizer_refs = sorted(
            [
                build_advisory_reference(
                    source_call_index=int(record["source_call_index"]),
                    specialist=str(record["specialist"]),
                    response_evidence=record["response_evidence"],
                )
                for record in advisory_records
            ],
            key=lambda item: str(item["specialist"]),
        )
        try:
            final_usage_evidence = _call_usage_evidence(
                final_call,
                counter_id=counter_id,
                prompt_digest=finalizer_prompt_digest,
                role="FIXED_FINALIZER",
                specialist=None,
                expected_cli_version=expected_cli_version,
                model=model,
                reasoning_effort=reasoning_effort,
                workspace_identity=workspace_identity,
            )
        except B2EvidenceError as exc:
            return invalid_result(
                request,
                "MEASUREMENT_CAPTURE_FAILURE",
                {
                    **base_evidence,
                    "error": str(exc),
                    "candidate_id": candidate.candidate_id,
                    "observed_call_count": len(calls),
                    "calls": call_evidence,
                    "rejected_turn_completed_usage": copy.deepcopy(final_call.get("turn_completed_usage", final_call.get("usage"))),
                },
            )
        finalizer_evidence = {
            "role": "FIXED_FINALIZER",
            "stage_index": None,
            "stage_id": "fixed.finalizer",
            "specialist": None,
            "prompt_digest": finalizer_prompt_digest,
            "response_digest": digest_json(str(final_call["response"])),
            "advisory_inputs": finalizer_refs,
            "usage": copy.deepcopy(final_call["usage"]),
            **final_usage_evidence,
            "total_tokens": int(final_call["total_tokens"]),
            "elapsed_ms": int(final_call["elapsed_ms"]),
        }
        call_evidence.append(finalizer_evidence)
        totals = aggregate_calls(calls)
        if totals["total_tokens"] > per_run_total_token_ceiling:
            return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", {**base_evidence, "error": "per-run total-token ceiling exceeded", "candidate_id": candidate.candidate_id, "calls": call_evidence, "observed_total_tokens": totals["total_tokens"], "per_run_total_token_ceiling": per_run_total_token_ceiling})

        valid, observed, validation_error = validate_exact_json_response(str(final_call["response"]), task_payload)
        outcome = {"status": "PASS" if valid else "FAIL", "invalid_reason": None, "task_completed": True, "validation_passed": valid, "governance_valid": True}
        safety = _empty_safety()
        specialist_evidence = [item for item in call_evidence if item["role"] == "SPECIALIST"]
        context_ledger = recompute_context_transfer_ledger(
            specialist_calls=specialist_evidence,
            finalizer_call=finalizer_evidence,
        )
        context_transfer_bytes = context_ledger["recomputed_context_transfer_bytes"]
        context_ledger = recompute_context_transfer_ledger(
            specialist_calls=specialist_evidence,
            finalizer_call=finalizer_evidence,
            reported_context_transfer_bytes=context_transfer_bytes,
        )
        raw_evidence = {
            **base_evidence,
            "candidate_id": candidate.candidate_id,
            "candidate_digest": digest_json(candidate.to_dict()),
            "candidate_stage_order": [{"stage_id": stage.stage_id, "mode": stage.mode, "specialists": list(stage.specialists)} for stage in candidate.stages],
            "calls": call_evidence,
            "context_transfer_recomputation": context_ledger,
            "final_response": str(final_call["response"]),
            "observed_json": observed,
            "validation_error": validation_error,
            "per_run_total_token_ceiling": per_run_total_token_ceiling,
            "observed_total_tokens": totals["total_tokens"],
            "counter_id": counter_id,
            "counter_stability_evaluation_scope": "CROSS_RUN_RECONCILIATION_REQUIRED",
        }
        wall_ms = int((time.monotonic() - started) * 1000)
        return {
            "schema_version": EXECUTOR_RESULT_VERSION,
            "request_id": request["request_id"],
            "outcome": outcome,
            "quality": {"requirements_satisfied": 1 if valid else 0, "requirements_missed": 0 if valid else 1, "remediation_iterations": 0, "validation_failures": 0 if valid else 1, "regressions_introduced": 0},
            "tokens": {"source": "HOST_REPORTED", "counter_id": raw_evidence["counter_id"], "input_tokens": totals["input_tokens"], "output_tokens": totals["output_tokens"], "cached_input_tokens": totals["cached_input_tokens"], "reasoning_tokens": totals["reasoning_tokens"], "fresh_billable_tokens": None},
            "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
            "latency": {"wall_clock_ms": wall_ms, "model_execution_ms": totals["model_execution_ms"], "tool_execution_ms": 0, "coordination_overhead_ms": max(0, wall_ms - totals["model_execution_ms"])},
            "coordination": {"specialist_messages": len(candidate.stages), "cross_specialist_messages": max(0, len(candidate.stages) - 1), "handoffs": max(0, len(candidate.stages) - 1), "handoff_failures": 0, "duplicate_work_events": 0, "contradiction_events": 0, "join_wait_ms": None, "specialist_reentry_events": 0},
            "communication": {"progress_messages": 0, "model_progress_calls": len(calls), "user_visible_bytes": len(str(final_call["response"]).encode("utf-8")), "context_transfer_bytes": context_transfer_bytes, "semantic_preservation_failures": 0 if valid else 1, "required_information_omissions": 0 if valid else 1},
            "safety": safety,
            "validation_digest": digest_json({"validator": "EXACT_JSON_CONFORMANCE_V1", "valid": valid, "observed": observed}),
            "governance_digest": digest_json({"governance_valid": True, "safety": safety}),
            "raw_evidence": raw_evidence,
            "a5_shadow_observation": shadow,
        }
    except (TopologyExecutorError, B2EvidenceError, OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", {**base_evidence, "error": str(exc)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one bounded B2 topology benchmark request")
    parser.add_argument("--eligibility-envelope", required=True, type=Path)
    parser.add_argument("--expected-cli-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", required=True)
    parser.add_argument("--codex-command-prefix-json", required=True)
    parser.add_argument("--workspace-dir", required=True, type=Path)
    parser.add_argument("--call-timeout-seconds", required=True, type=int)
    parser.add_argument("--per-run-total-token-ceiling", required=True, type=int)
    args = parser.parse_args(argv)

    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise TopologyExecutorError("stdin request must be one JSON object")
        _, envelope, eligibility_digest = load_envelope(args.eligibility_envelope)
        prefix = parse_command_prefix(args.codex_command_prefix_json)
        result = execute_request(
            request,
            envelope=envelope,
            eligibility_digest=eligibility_digest,
            expected_cli_version=args.expected_cli_version,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            command_prefix=prefix,
            workspace=args.workspace_dir,
            call_timeout_seconds=args.call_timeout_seconds,
            per_run_total_token_ceiling=args.per_run_total_token_ceiling,
        )
        json.dump(result, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (TopologyExecutorError, OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        json.dump({"schema_version": EXECUTOR_RESULT_VERSION, "request_id": "UNKNOWN_REQUEST", "fatal_executor_error": str(exc)}, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
