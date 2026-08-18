#!/usr/bin/env python3
"""Non-production comparative benchmark harness for Orchestra B1.

The harness executes every configured experimental arm for every task and
repetition, randomizes arm order within paired blocks, invokes an explicit
executor adapter without a shell, and emits provenance-bound JSON evidence.
It does not choose production routing, change Orchestra runtime behavior, or
interpret raw evidence as promotion authority.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

PROGRAM_ID = "orchestra.shared-comparative-benchmark.v1"
MANIFEST_VERSION = "orchestra.comparative-benchmark-manifest.v1"
EXECUTOR_RESULT_VERSION = "orchestra.comparative-benchmark-executor-result.v1"
RUN_VERSION = "orchestra.comparative-benchmark-run.v1"
EXPERIMENT_VERSION = "orchestra.comparative-benchmark-experiment.v1"
REQUEST_VERSION = "orchestra.comparative-benchmark-executor-request.v1"

EXPERIMENT_KINDS = {"A5_ISOLATED", "MURMURS_ISOLATED", "A5_MURMURS_INTERACTION"}
STAGES = {"CALIBRATION", "PILOT", "CONFIRMATORY"}
COMMUNICATION_MODES = {"DEFAULT", "CAVEMAN", "MURMURS"}
TOPOLOGY_CLASSES = {
    "FIXED_DETERMINISTIC",
    "SEQUENTIAL",
    "CENTRALIZED_STAR",
    "HIERARCHICAL_DECOMPOSITION",
    "PARALLEL_JOIN",
    "OTHER_PERMITTED",
}
INVALID_REASONS = {
    "PROVIDER_OUTAGE",
    "INFRASTRUCTURE_OUTAGE",
    "HARNESS_FAILURE",
    "CORRUPTED_STARTING_STATE",
    "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
    "MEASUREMENT_CAPTURE_FAILURE",
}
SAFETY_FIELDS = (
    "required_specialist_omission",
    "authority_expansion",
    "capability_expansion",
    "governance_violation",
    "provider_privacy_expansion",
    "mandatory_gate_suppression",
)
DIGEST_FIELDS = (
    "system_instruction_digest",
    "tool_access_digest",
    "specialist_set_digest",
    "required_specialist_set_digest",
    "authority_digest",
    "governance_digest",
    "validation_contract_digest",
    "environment_digest",
    "retry_policy_digest",
    "resource_budget_digest",
)


class HarnessError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HarnessError(message)


def is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"cannot load JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_arm(arm: dict[str, Any]) -> None:
    for field in ("arm_id", "topology_candidate_id", "topology_class", "topology_digest", "communication_mode"):
        require(field in arm, f"arm missing {field}")
    require(isinstance(arm["arm_id"], str) and arm["arm_id"].strip(), "arm_id must be non-empty")
    require(isinstance(arm["topology_candidate_id"], str) and arm["topology_candidate_id"].strip(), "topology_candidate_id must be non-empty")
    require(arm["topology_class"] in TOPOLOGY_CLASSES, f"unsupported topology_class: {arm['topology_class']}")
    require(is_digest(arm["topology_digest"]), "topology_digest must be lowercase SHA-256")
    require(arm["communication_mode"] in COMMUNICATION_MODES, f"unsupported communication_mode: {arm['communication_mode']}")


def validate_manifest(manifest: dict[str, Any]) -> None:
    require(manifest.get("schema_version") == MANIFEST_VERSION, "unsupported manifest schema_version")
    require(manifest.get("program_id") == PROGRAM_ID, "unexpected program_id")
    kind = manifest.get("experiment_kind")
    stage = manifest.get("stage")
    require(kind in EXPERIMENT_KINDS, "unsupported experiment_kind")
    require(stage in STAGES, "unsupported stage")
    require(isinstance(manifest.get("experiment_id"), str) and manifest["experiment_id"].strip(), "experiment_id must be non-empty")
    require(isinstance(manifest.get("randomization_seed"), int) and not isinstance(manifest["randomization_seed"], bool) and manifest["randomization_seed"] >= 0, "randomization_seed must be a non-negative integer")
    require(isinstance(manifest.get("repetitions_per_arm"), int) and manifest["repetitions_per_arm"] >= 1, "repetitions_per_arm must be >= 1")

    control = manifest.get("common_control_identity")
    require(isinstance(control, dict), "common_control_identity must be an object")
    for field in ("orchestra_revision", "repository_revision", "provider", "model"):
        require(isinstance(control.get(field), str) and control[field].strip(), f"common_control_identity.{field} must be non-empty")
    for field in DIGEST_FIELDS:
        require(is_digest(control.get(field)), f"common_control_identity.{field} must be lowercase SHA-256")

    arms = manifest.get("arms")
    require(isinstance(arms, list) and len(arms) >= 2, "at least two arms are required")
    require(all(isinstance(arm, dict) for arm in arms), "every arm must be an object")
    for arm in arms:
        validate_arm(arm)
    arm_ids = [arm["arm_id"] for arm in arms]
    require(len(set(arm_ids)) == len(arm_ids), "arm_id values must be unique")

    tasks = manifest.get("tasks")
    require(isinstance(tasks, list) and tasks, "at least one task is required")
    task_ids: list[str] = []
    for task in tasks:
        require(isinstance(task, dict), "every task must be an object")
        require(isinstance(task.get("task_id"), str) and task["task_id"].strip(), "task_id must be non-empty")
        require(is_digest(task.get("starting_state_digest")), f"task {task.get('task_id')} starting_state_digest must be lowercase SHA-256")
        require(is_digest(task.get("task_prompt_digest")), f"task {task.get('task_id')} task_prompt_digest must be lowercase SHA-256")
        require(isinstance(task.get("task_payload"), dict), f"task {task.get('task_id')} task_payload must be an object")
        task_ids.append(task["task_id"])
    require(len(set(task_ids)) == len(task_ids), "task_id values must be unique")

    if kind == "A5_ISOLATED":
        require(isinstance(manifest.get("a5_evaluation"), dict), "A5_ISOLATED requires a5_evaluation")
        require(is_digest(manifest["a5_evaluation"].get("eligibility_envelope_digest")), "A5 eligibility_envelope_digest is required")
        require(all(arm["communication_mode"] == "DEFAULT" for arm in arms), "A5_ISOLATED requires DEFAULT communication for every arm")
        require(manifest.get("murmurs_evaluation") in (None, {}), "A5_ISOLATED cannot include Murmurs evaluation settings")
    elif kind == "MURMURS_ISOLATED":
        require(isinstance(manifest.get("murmurs_evaluation"), dict), "MURMURS_ISOLATED requires murmurs_evaluation")
        require(manifest["murmurs_evaluation"].get("same_counter_identity_for_token_delta") is True, "Murmurs token comparison requires same counter identity")
        require(all(arm["topology_class"] == "FIXED_DETERMINISTIC" for arm in arms), "MURMURS_ISOLATED requires FIXED_DETERMINISTIC topology")
        topology_identity = {(arm["topology_candidate_id"], arm["topology_digest"]) for arm in arms}
        require(len(topology_identity) == 1, "MURMURS_ISOLATED requires one identical fixed topology identity")
        modes = {arm["communication_mode"] for arm in arms}
        require(modes == {"DEFAULT", "CAVEMAN", "MURMURS"}, "MURMURS_ISOLATED requires exactly DEFAULT, CAVEMAN, and MURMURS arms")
        require(len(arms) == 3, "MURMURS_ISOLATED requires exactly three communication arms")
        require(manifest.get("a5_evaluation") in (None, {}), "MURMURS_ISOLATED cannot include A5 evaluation settings")
    else:
        require(isinstance(manifest.get("a5_evaluation"), dict), "interaction experiment requires a5_evaluation")
        require(isinstance(manifest.get("murmurs_evaluation"), dict), "interaction experiment requires murmurs_evaluation")
        interaction = manifest.get("interaction_evaluation")
        require(isinstance(interaction, dict), "interaction experiment requires interaction_evaluation")
        require(is_digest(interaction.get("isolated_a5_evidence_digest")), "interaction requires isolated A5 evidence digest")
        require(is_digest(interaction.get("isolated_murmurs_evidence_digest")), "interaction requires isolated Murmurs evidence digest")

    if stage == "CONFIRMATORY":
        require(is_digest(manifest.get("preregistration_digest")), "CONFIRMATORY requires preregistration_digest")
        require(isinstance(manifest.get("benefit_thresholds"), dict), "CONFIRMATORY requires benefit_thresholds")


def make_control_identity(common: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(common)
    result["starting_state_digest"] = task["starting_state_digest"]
    result["task_prompt_digest"] = task["task_prompt_digest"]
    return result


def build_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    execution_index = 1
    for task in manifest["tasks"]:
        for repetition_index in range(1, manifest["repetitions_per_arm"] + 1):
            arms = [copy.deepcopy(arm) for arm in manifest["arms"]]
            block_seed = f"{manifest['randomization_seed']}:{manifest['experiment_id']}:{task['task_id']}:{repetition_index}"
            random.Random(block_seed).shuffle(arms)
            for arm in arms:
                request_id = sha256(
                    f"{manifest['experiment_id']}:{task['task_id']}:{repetition_index}:{arm['arm_id']}".encode("utf-8")
                ).hexdigest()[:24]
                entries.append(
                    {
                        "request_id": request_id,
                        "task_id": task["task_id"],
                        "task_class": task["task_class"],
                        "repetition_index": repetition_index,
                        "execution_order_index": execution_index,
                        "arm": arm,
                    }
                )
                execution_index += 1
    return {
        "schema_version": "orchestra.comparative-benchmark-plan.v1",
        "program_id": PROGRAM_ID,
        "experiment_id": manifest["experiment_id"],
        "experiment_kind": manifest["experiment_kind"],
        "stage": manifest["stage"],
        "randomization_seed_digest": sha256(str(manifest["randomization_seed"]).encode("utf-8")).hexdigest(),
        "manifest_digest": digest_json(manifest),
        "entries": entries,
    }


def make_request(manifest: dict[str, Any], plan_entry: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": REQUEST_VERSION,
        "program_id": PROGRAM_ID,
        "experiment_id": manifest["experiment_id"],
        "experiment_kind": manifest["experiment_kind"],
        "stage": manifest["stage"],
        "request_id": plan_entry["request_id"],
        "task_id": task["task_id"],
        "task_class": task["task_class"],
        "repetition_index": plan_entry["repetition_index"],
        "execution_order_index": plan_entry["execution_order_index"],
        "arm": copy.deepcopy(plan_entry["arm"]),
        "control_identity": make_control_identity(manifest["common_control_identity"], task),
        "task_payload": copy.deepcopy(task["task_payload"]),
        "task_payload_digest": digest_json(task["task_payload"]),
        "a5_evaluation": copy.deepcopy(manifest.get("a5_evaluation")),
        "murmurs_evaluation": copy.deepcopy(manifest.get("murmurs_evaluation")),
        "interaction_evaluation": copy.deepcopy(manifest.get("interaction_evaluation")),
    }


def validate_result(result: dict[str, Any], request: dict[str, Any]) -> None:
    require(result.get("schema_version") == EXECUTOR_RESULT_VERSION, "executor returned unsupported schema_version")
    require(result.get("request_id") == request["request_id"], "executor result request_id does not match request")

    outcome = result.get("outcome")
    require(isinstance(outcome, dict), "executor result outcome must be an object")
    status = outcome.get("status")
    require(status in {"PASS", "FAIL", "INVALID_RUN"}, "executor result has invalid outcome status")
    invalid_reason = outcome.get("invalid_reason")
    if status == "INVALID_RUN":
        require(invalid_reason in INVALID_REASONS, "INVALID_RUN requires an allowed invalid_reason")
    else:
        require(invalid_reason is None, "non-invalid run must use invalid_reason=null")
    for field in ("task_completed", "validation_passed", "governance_valid"):
        require(isinstance(outcome.get(field), bool), f"outcome.{field} must be boolean")

    for section in ("quality", "tokens", "cost", "latency", "coordination", "communication", "safety"):
        require(isinstance(result.get(section), dict), f"executor result {section} must be an object")

    for field in SAFETY_FIELDS:
        require(result["safety"].get(field) is False, f"safety boundary crossed: {field}")

    tokens = result["tokens"]
    require(tokens.get("source") in {"HOST_REPORTED", "UNAVAILABLE"}, "tokens.source must be HOST_REPORTED or UNAVAILABLE")
    token_fields = ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_tokens", "fresh_billable_tokens")
    if tokens["source"] == "UNAVAILABLE":
        require(tokens.get("counter_id") is None, "UNAVAILABLE tokens cannot carry counter_id")
        require(all(tokens.get(field) is None for field in token_fields), "UNAVAILABLE tokens cannot carry counts")
    else:
        require(isinstance(tokens.get("counter_id"), str) and tokens["counter_id"].strip(), "HOST_REPORTED tokens require counter_id")
        require(isinstance(tokens.get("input_tokens"), int) and tokens["input_tokens"] >= 0, "HOST_REPORTED tokens require input_tokens")
        require(isinstance(tokens.get("output_tokens"), int) and tokens["output_tokens"] >= 0, "HOST_REPORTED tokens require output_tokens")

    cost = result["cost"]
    require(cost.get("source") in {"PROVIDER_REPORTED", "UNAVAILABLE"}, "cost.source must be PROVIDER_REPORTED or UNAVAILABLE")
    if cost["source"] == "UNAVAILABLE":
        require(cost.get("amount") is None and cost.get("currency") is None, "UNAVAILABLE cost cannot carry amount or currency")

    require(is_digest(result.get("validation_digest")), "executor result validation_digest must be lowercase SHA-256")
    require(is_digest(result.get("governance_digest")), "executor result governance_digest must be lowercase SHA-256")
    require(isinstance(result.get("raw_evidence"), dict), "executor result raw_evidence must be an object")

    a5 = result.get("a5_shadow_observation")
    if request["experiment_kind"] in {"A5_ISOLATED", "A5_MURMURS_INTERACTION"}:
        require(isinstance(a5, dict), "A5 experiment requires a5_shadow_observation")
        require(is_digest(a5.get("eligibility_digest")), "A5 observation requires eligibility_digest")
        require(is_digest(a5.get("decision_digest")), "A5 observation requires decision_digest")
        ranked = a5.get("ranked_topology_candidate_ids")
        require(isinstance(ranked, list) and ranked and len(set(ranked)) == len(ranked), "A5 ranked candidates must be a non-empty unique list")
        require(a5.get("top_candidate_id") == ranked[0], "A5 top_candidate_id must equal first ranked candidate")
    else:
        require(a5 in (None, {}), "MURMURS_ISOLATED cannot return an A5 shadow observation")


def invalid_result(request: dict[str, Any], reason: str, detail: dict[str, Any], elapsed_ms: int | None) -> dict[str, Any]:
    unavailable_evidence = {
        "request_id": request["request_id"],
        "invalid_reason": reason,
        "detail": detail,
        "validation_executed": False,
        "governance_evaluated": False,
    }
    unavailable_digest = digest_json(unavailable_evidence)
    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": request["request_id"],
        "outcome": {"status": "INVALID_RUN", "invalid_reason": reason, "task_completed": False, "validation_passed": False, "governance_valid": False},
        "quality": {"requirements_satisfied": 0, "requirements_missed": 0, "remediation_iterations": 0, "validation_failures": 0, "regressions_introduced": 0},
        "tokens": {"source": "UNAVAILABLE", "counter_id": None, "input_tokens": None, "output_tokens": None, "cached_input_tokens": None, "reasoning_tokens": None, "fresh_billable_tokens": None},
        "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
        "latency": {"wall_clock_ms": elapsed_ms, "model_execution_ms": None, "tool_execution_ms": None, "coordination_overhead_ms": None},
        "coordination": {"specialist_messages": 0, "cross_specialist_messages": 0, "handoffs": 0, "handoff_failures": 0, "duplicate_work_events": 0, "contradiction_events": 0, "join_wait_ms": None, "specialist_reentry_events": 0},
        "communication": {"progress_messages": 0, "model_progress_calls": 0, "user_visible_bytes": 0, "context_transfer_bytes": 0, "semantic_preservation_failures": 0, "required_information_omissions": 0},
        "safety": {field: False for field in SAFETY_FIELDS},
        "validation_digest": unavailable_digest,
        "governance_digest": unavailable_digest,
        "raw_evidence": unavailable_evidence,
        "a5_shadow_observation": None,
    }


def invoke_executor(command: list[str], request: dict[str, Any], timeout_seconds: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        detail = {"kind": "EXECUTOR_TIMEOUT", "timeout_seconds": timeout_seconds, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
        return invalid_result(request, "HARNESS_FAILURE", detail, elapsed), detail
    except OSError as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        detail = {"kind": "EXECUTOR_LAUNCH_FAILURE", "error": str(exc)}
        return invalid_result(request, "HARNESS_FAILURE", detail, elapsed), detail

    elapsed = int((time.monotonic() - started) * 1000)
    partial = {"returncode": completed.returncode, "stderr": completed.stderr}
    if completed.returncode != 0:
        partial["kind"] = "EXECUTOR_NONZERO_EXIT"
        partial["stdout"] = completed.stdout
        return invalid_result(request, "HARNESS_FAILURE", partial, elapsed), partial

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        partial.update({"kind": "EXECUTOR_RESULT_NOT_JSON", "stdout": completed.stdout, "error": str(exc)})
        return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", partial, elapsed), partial
    if not isinstance(result, dict):
        partial.update({"kind": "EXECUTOR_RESULT_NOT_OBJECT", "stdout": completed.stdout})
        return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", partial, elapsed), partial

    try:
        validate_result(result, request)
    except HarnessError as exc:
        partial.update({"kind": "EXECUTOR_RESULT_INVALID", "error": str(exc), "stdout": completed.stdout})
        return invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", partial, elapsed), partial
    return result, (partial if completed.stderr else None)


def build_run_record(manifest: dict[str, Any], request: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    raw_evidence_digest = digest_json(result["raw_evidence"])
    a5_observation = copy.deepcopy(result.get("a5_shadow_observation"))
    if a5_observation == {}:
        a5_observation = None
    return {
        "schema_version": RUN_VERSION,
        "program_id": PROGRAM_ID,
        "run_id": request["request_id"],
        "experiment_id": manifest["experiment_id"],
        "experiment_kind": manifest["experiment_kind"],
        "stage": manifest["stage"],
        "task_id": request["task_id"],
        "task_class": request["task_class"],
        "repetition_index": request["repetition_index"],
        "execution_order_index": request["execution_order_index"],
        "started_at": None,
        "completed_at": None,
        "arm": copy.deepcopy(request["arm"]),
        "control_identity": copy.deepcopy(request["control_identity"]),
        "outcome": copy.deepcopy(result["outcome"]),
        "quality": copy.deepcopy(result["quality"]),
        "tokens": copy.deepcopy(result["tokens"]),
        "cost": copy.deepcopy(result["cost"]),
        "latency": copy.deepcopy(result["latency"]),
        "coordination": copy.deepcopy(result["coordination"]),
        "communication": copy.deepcopy(result["communication"]),
        "safety": copy.deepcopy(result["safety"]),
        "a5_shadow_observation": a5_observation,
        "evidence": {
            "validation_digest": result["validation_digest"],
            "governance_digest": result["governance_digest"],
            "raw_evidence_digest": raw_evidence_digest,
        },
    }


def enforce_cross_run_invariants(manifest: dict[str, Any], runs: list[dict[str, Any]]) -> None:
    kind = manifest["experiment_kind"]
    if kind in {"A5_ISOLATED", "A5_MURMURS_INTERACTION"}:
        expected_candidates = {arm["topology_candidate_id"] for arm in manifest["arms"]}
        expected_eligibility = manifest["a5_evaluation"]["eligibility_envelope_digest"]
        observations: dict[tuple[str, int], str] = {}
        for run in runs:
            if run["outcome"]["status"] == "INVALID_RUN":
                continue
            observation = run["a5_shadow_observation"]
            require(observation is not None, "valid A5 run is missing shadow observation")
            require(observation["eligibility_digest"] == expected_eligibility, "A5 eligibility digest differs from manifest")
            require(set(observation["ranked_topology_candidate_ids"]) == expected_candidates, "A5 ranked candidates must exactly equal configured topology candidates")
            require(observation["top_candidate_id"] in expected_candidates, "A5 top candidate is not configured")
            key = (run["task_id"], run["repetition_index"])
            fingerprint = digest_json(observation)
            prior = observations.setdefault(key, fingerprint)
            require(prior == fingerprint, "A5 shadow observation changed across arms in the same paired block")

    if kind == "MURMURS_ISOLATED":
        for run in runs:
            require(run["a5_shadow_observation"] is None, "MURMURS_ISOLATED run unexpectedly contains A5 observation")


def build_experiment_record(manifest: dict[str, Any], run_digests: list[str], invalid_run_ids: list[str], plan: dict[str, Any]) -> dict[str, Any]:
    stage = manifest["stage"]
    if invalid_run_ids:
        status = "INVALIDATED"
        conclusion = "INVALIDATED"
    elif stage == "CALIBRATION":
        status = "COMPLETE"
        conclusion = "MEASUREMENT_CALIBRATED"
    else:
        status = "RUNNING"
        conclusion = "MEASUREMENT_NOT_STARTED"

    thresholds = manifest.get("benefit_thresholds")
    if thresholds is None and stage in {"CALIBRATION", "PILOT"}:
        thresholds = {
            "task_success_absolute_improvement": 0.05,
            "remediation_relative_reduction": 0.15,
            "fresh_token_relative_reduction": 0.10,
            "latency_relative_reduction": 0.10,
            "threshold_role": "PILOT_SIGNAL_ONLY",
        }
    elif thresholds is not None:
        thresholds = dict(thresholds)
        thresholds["threshold_role"] = "CONFIRMATORY_PREREGISTERED" if stage == "CONFIRMATORY" else "PILOT_SIGNAL_ONLY"

    a5_eval = None
    murmurs_eval = None
    interaction_eval = None
    if manifest["experiment_kind"] in {"A5_ISOLATED", "A5_MURMURS_INTERACTION"}:
        a5_eval = {
            "shadow_only": True,
            "eligibility_envelope_digest": manifest["a5_evaluation"]["eligibility_envelope_digest"],
            "run_all_eligible_candidates": True,
            "a5_may_select_execution_arm": False,
            "record_ranked_order": True,
            "record_empirical_best": True,
            "record_top1_match": True,
            "record_topk_match": True,
            "record_regret": True,
        }
    if manifest["experiment_kind"] in {"MURMURS_ISOLATED", "A5_MURMURS_INTERACTION"}:
        murmurs_eval = {
            "fixed_topology": manifest["experiment_kind"] == "MURMURS_ISOLATED",
            "required_communication_arms": ["DEFAULT", "CAVEMAN", "MURMURS"],
            "same_counter_identity_for_token_delta": True,
            "caveman_published_percentage_import_allowed": False,
            "semantic_preservation_required": True,
        }
    if manifest["experiment_kind"] == "A5_MURMURS_INTERACTION":
        interaction_eval = {
            "factorial_design": True,
            "isolated_a5_evidence_digest": manifest["interaction_evaluation"]["isolated_a5_evidence_digest"],
            "isolated_murmurs_evidence_digest": manifest["interaction_evaluation"]["isolated_murmurs_evidence_digest"],
            "interaction_state": "NOT_YET_EVALUATED",
        }

    return {
        "schema_version": EXPERIMENT_VERSION,
        "program_id": PROGRAM_ID,
        "experiment_id": manifest["experiment_id"],
        "experiment_kind": manifest["experiment_kind"],
        "stage": stage,
        "status": status,
        "contract_revision": manifest["common_control_identity"]["orchestra_revision"],
        "preregistration_digest": manifest.get("preregistration_digest"),
        "task_manifest_digest": plan["manifest_digest"],
        "task_count": len(manifest["tasks"]),
        "repetitions_per_arm": manifest["repetitions_per_arm"],
        "paired_task_design": True,
        "randomized_arm_order": True,
        "randomization_seed_digest": plan["randomization_seed_digest"],
        "arms": copy.deepcopy(manifest["arms"]),
        "control_policy": {
            "same_model": True,
            "same_provider": True,
            "same_reasoning_setting_when_configurable": True,
            "same_temperature_when_configurable": True,
            "same_tool_access": True,
            "same_starting_state": True,
            "same_task_prompt": True,
            "same_specialist_set": True,
            "same_required_specialist_set": True,
            "same_authority_envelope": True,
            "same_governance_state": True,
            "same_validation_contract": True,
            "same_retry_policy": True,
            "same_resource_budget_when_configurable": True,
            "experimental_mechanic_is_only_intentional_difference": True,
        },
        "analysis_policy": {
            "paired_analysis": True,
            "report_absolute_difference": True,
            "report_relative_difference": True,
            "report_uncertainty": True,
            "report_task_class_strata": True,
            "report_tail_metrics": True,
            "quality_precedes_efficiency": True,
        },
        "benefit_thresholds": thresholds,
        "regression_guards": {
            "required_specialist_omission_allowed": False,
            "authority_expansion_allowed": False,
            "capability_expansion_allowed": False,
            "governance_violation_allowed": False,
            "provider_privacy_expansion_allowed": False,
            "mandatory_gate_suppression_allowed": False,
            "tail_regression_review_required": True,
            "information_preservation_review_required": True,
        },
        "a5_evaluation": a5_eval,
        "murmurs_evaluation": murmurs_eval,
        "interaction_evaluation": interaction_eval,
        "run_evidence_digests": run_digests,
        "excluded_run_ids": [],
        "conclusion": conclusion,
    }


def parse_executor_command(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"--executor-command-json must be a JSON array: {exc}") from exc
    require(isinstance(value, list) and value, "--executor-command-json must contain at least one argument")
    require(all(isinstance(item, str) and item for item in value), "executor command arguments must be non-empty strings")
    return value


def run(manifest_path: Path, executor_command: list[str], output_dir: Path, plan_only: bool = False) -> int:
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    plan = build_plan(manifest)
    write_json(output_dir / "plan.json", plan)
    if plan_only:
        return 0

    tasks = {task["task_id"]: task for task in manifest["tasks"]}
    timeout_seconds = int(manifest.get("executor_timeout_seconds", 600))
    runs: list[dict[str, Any]] = []
    run_digests: list[str] = []
    invalid_ids: list[str] = []
    index_entries: list[dict[str, Any]] = []

    for entry in plan["entries"]:
        task = tasks[entry["task_id"]]
        request = make_request(manifest, entry, task)
        result, partial = invoke_executor(executor_command, request, timeout_seconds)
        if result["outcome"]["status"] == "INVALID_RUN" and manifest["experiment_kind"] in {"A5_ISOLATED", "A5_MURMURS_INTERACTION"}:
            result["a5_shadow_observation"] = None
        run_record = build_run_record(manifest, request, result)
        run_digest = digest_json(run_record)
        run_path = output_dir / "runs" / f"{entry['execution_order_index']:05d}-{entry['request_id']}.json"
        write_json(run_path, run_record)
        if partial is not None:
            write_json(output_dir / "partial-evidence" / f"{entry['request_id']}.json", partial)
        runs.append(run_record)
        run_digests.append(run_digest)
        if run_record["outcome"]["status"] == "INVALID_RUN":
            invalid_ids.append(run_record["run_id"])
        index_entries.append({"run_id": run_record["run_id"], "path": run_path.relative_to(output_dir).as_posix(), "digest": run_digest, "status": run_record["outcome"]["status"]})

    enforce_cross_run_invariants(manifest, runs)
    run_index = {
        "schema_version": "orchestra.comparative-benchmark-run-index.v1",
        "program_id": PROGRAM_ID,
        "experiment_id": manifest["experiment_id"],
        "manifest_digest": plan["manifest_digest"],
        "planned_run_count": len(plan["entries"]),
        "recorded_run_count": len(runs),
        "invalid_run_count": len(invalid_ids),
        "entries": index_entries,
    }
    write_json(output_dir / "run-index.json", run_index)
    experiment = build_experiment_record(manifest, run_digests, invalid_ids, plan)
    write_json(output_dir / "experiment.json", experiment)
    return 2 if invalid_ids else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a controlled Orchestra comparative benchmark manifest.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--executor-command-json", required=True, help='JSON array, for example ["python","adapter.py"]')
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        command = parse_executor_command(args.executor_command_json)
        return run(args.manifest, command, args.output_dir, plan_only=args.plan_only)
    except HarnessError as exc:
        print(f"comparative benchmark harness error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
