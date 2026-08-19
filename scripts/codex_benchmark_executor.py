#!/usr/bin/env python3
"""Codex measurement executor binding for Orchestra comparative benchmarks.

Readiness-only until a separate human gate freezes exact Codex CLI version,
model, reasoning effort, counter identity, authentication surface, workspace,
and resource/stop ceilings. Frozen B3 tasks and accepted Antigravity evidence
are not changed by this adapter.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.antigravity_benchmark_executor import (  # noqa: E402
    SAFETY_FIELDS,
    bind_communication_treatment,
    digest_json,
    evaluate_task_outcome,
)

EXECUTOR_RESULT_VERSION = "orchestra.comparative-benchmark-executor-result.v1"
EXECUTOR_REQUEST_VERSION = "orchestra.comparative-benchmark-executor-request.v1"
PROGRAM_ID = "orchestra.shared-comparative-benchmark.v1"
PROVIDER_ID = "openai-codex"
TRANSPORT_ID = "jsonl-usage"
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+(?:[-.][0-9A-Za-z]+)*")
ALLOWED_REASONING_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
DISALLOWED_ITEM_TYPES = {"command_execution", "file_change", "mcp_tool_call", "web_search"}

BENCHMARK_SUBJECT_SHA = "d95f677dbf23ab79c4698c26645ea30cea9b3019"
BENCHMARK_SUBJECT_TREE = "ceab55bd512ea6fde4e8e76877cbb7006d18500e"
COMMON_MEASUREMENT_CORE_SHA = "e182e478988c77125127811375aa1b69278cca63"
COMMON_MEASUREMENT_CORE_TREE = "9e1d9c0dcf5e615c4b16dfd95bb72f63eaacc33e"
TASKSET_DIGEST = "fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8"


def compute_counter_id(cli_version: str, model: str, reasoning_effort: str) -> str:
    return f"codex-cli-{cli_version}:{TRANSPORT_ID}:{model}:{reasoning_effort}"


def _empty_safety() -> dict[str, bool]:
    return {field: False for field in SAFETY_FIELDS}


def _invalid_result(request: dict[str, Any], invalid_reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    outcome = {
        "status": "INVALID_RUN",
        "invalid_reason": invalid_reason,
        "task_completed": False,
        "validation_passed": False,
        "governance_valid": False,
    }
    quality = {
        "requirements_satisfied": 0,
        "requirements_missed": 0,
        "remediation_iterations": 0,
        "validation_failures": 0,
        "regressions_introduced": 0,
    }
    safety = _empty_safety()
    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": str(request.get("request_id") or "UNKNOWN_REQUEST"),
        "outcome": outcome,
        "quality": quality,
        "tokens": {
            "source": "UNAVAILABLE",
            "counter_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cached_input_tokens": None,
            "reasoning_tokens": None,
            "fresh_billable_tokens": None,
        },
        "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
        "latency": {
            "wall_clock_ms": None,
            "model_execution_ms": None,
            "tool_execution_ms": None,
            "coordination_overhead_ms": None,
        },
        "coordination": {
            "specialist_messages": 0,
            "cross_specialist_messages": 0,
            "handoffs": 0,
            "handoff_failures": 0,
            "duplicate_work_events": 0,
            "contradiction_events": 0,
            "join_wait_ms": None,
            "specialist_reentry_events": 0,
        },
        "communication": {
            "progress_messages": 0,
            "model_progress_calls": 0,
            "user_visible_bytes": 0,
            "context_transfer_bytes": 0,
            "semantic_preservation_failures": 0,
            "required_information_omissions": 0,
        },
        "safety": safety,
        "validation_digest": digest_json({"outcome": outcome}),
        "governance_digest": digest_json({"governance_valid": False, "safety": safety}),
        "raw_evidence": evidence,
        "a5_shadow_observation": None,
    }


def parse_cli_version(raw: str) -> str:
    matches = VERSION_PATTERN.findall(raw or "")
    unique = sorted(set(matches))
    if len(unique) != 1:
        raise ValueError(f"cannot resolve one exact Codex CLI version from: {raw!r}")
    return unique[0]


def build_codex_command(*, prompt: str, workspace_dir: Path, model: str, reasoning_effort: str) -> list[str]:
    """Build one bounded Codex non-interactive benchmark invocation."""
    return [
        "codex",
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        "read-only",
        "--ignore-user-config",
        "--ignore-rules",
        "--model",
        model,
        "--cd",
        str(workspace_dir),
        "-c",
        'approval_policy="never"',
        "-c",
        "agents.enabled=false",
        "-c",
        'web_search="disabled"',
        "-c",
        "features.shell_tool=false",
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        prompt,
    ]


def parse_codex_jsonl(raw_output: str) -> dict[str, Any]:
    """Parse one Codex JSONL turn and fail closed on unsafe/missing evidence."""
    events: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate((raw_output or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed Codex JSONL at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"Codex JSONL event at line {line_number} is not an object")
        events.append(event)

    if not events:
        raise ValueError("Codex JSONL stream is empty")
    if not any(event.get("type") == "thread.started" for event in events):
        raise ValueError("Codex JSONL is missing thread.started")
    if any(event.get("type") in {"turn.failed", "error"} for event in events):
        raise RuntimeError("Codex reported turn.failed or error")

    completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(completed) != 1:
        raise ValueError(f"Codex JSONL requires exactly one turn.completed event; observed {len(completed)}")
    usage = completed[0].get("usage")
    if not isinstance(usage, dict):
        raise ValueError("Codex turn.completed is missing usage")
    usage_fields = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    for field in usage_fields:
        value = usage.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Codex usage.{field} must be a non-negative integer")

    agent_messages: list[str] = []
    unexpected_tools: list[str] = []
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type in DISALLOWED_ITEM_TYPES:
            unexpected_tools.append(item_type)
        if item_type == "agent_message":
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                agent_messages.append(text)

    if unexpected_tools:
        raise PermissionError(f"Codex emitted disallowed tool events: {sorted(set(unexpected_tools))}")
    if not agent_messages:
        raise ValueError("Codex JSONL is missing a completed agent message")
    return {
        "events": events,
        "usage": {field: usage[field] for field in usage_fields},
        "response": agent_messages[-1],
        "agent_message_count": len(agent_messages),
    }


def _validate_request_identity(
    request: dict[str, Any], *, expected_model: str, expected_reasoning_effort: str
) -> str | None:
    if request.get("schema_version") != EXECUTOR_REQUEST_VERSION:
        return "unsupported executor request schema"
    if request.get("program_id") != PROGRAM_ID:
        return "unexpected benchmark program_id"
    control = request.get("control_identity")
    if not isinstance(control, dict):
        return "control_identity is missing"
    if control.get("orchestra_revision") != BENCHMARK_SUBJECT_SHA:
        return "benchmark subject orchestra_revision drifted from frozen d95f identity"
    if control.get("provider") != PROVIDER_ID:
        return f"provider must be {PROVIDER_ID}"
    if control.get("model") != expected_model:
        return "request model does not match frozen Codex model"
    if control.get("reasoning_setting") != expected_reasoning_effort:
        return "request reasoning_setting does not match frozen Codex reasoning effort"
    return None


def execute_request(
    request: dict[str, Any],
    *,
    expected_cli_version: str | None,
    expected_model: str | None,
    expected_reasoning_effort: str | None,
    workspace_dir: Path | str | None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    version_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    raw_jsonl: str | None = None,
    observed_cli_version: str | None = None,
    caveman_policy_content: str | bytes | None = None,
    caveman_policy_path: Path | str | None = None,
    caveman_repo_path: Path | str | None = None,
    presentation_root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute or deterministically parse one bounded Codex benchmark request."""
    evidence: dict[str, Any] = {
        "benchmark_subject": {"sha": BENCHMARK_SUBJECT_SHA, "tree": BENCHMARK_SUBJECT_TREE},
        "common_measurement_core_baseline": {
            "sha": COMMON_MEASUREMENT_CORE_SHA,
            "tree": COMMON_MEASUREMENT_CORE_TREE,
        },
        "taskset_digest": TASKSET_DIGEST,
        "host": "codex-cli",
        "transport": TRANSPORT_ID,
        "live_execution_authorized_by_adapter": False,
    }

    freeze_values = (expected_cli_version, expected_model, expected_reasoning_effort)
    if not all(isinstance(value, str) and value.strip() for value in freeze_values):
        return _invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {**evidence, "error": "exact Codex CLI version, model, and reasoning effort must be frozen before execution"},
        )
    assert expected_cli_version is not None
    assert expected_model is not None
    assert expected_reasoning_effort is not None
    if expected_reasoning_effort not in ALLOWED_REASONING_EFFORTS:
        return _invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {**evidence, "error": f"unsupported reasoning effort: {expected_reasoning_effort}"},
        )

    workspace = Path(workspace_dir) if workspace_dir is not None else None
    if workspace is None or not workspace.is_dir():
        return _invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {**evidence, "error": "workspace_dir must resolve to an existing directory"},
        )

    identity_error = _validate_request_identity(
        request,
        expected_model=expected_model,
        expected_reasoning_effort=expected_reasoning_effort,
    )
    if identity_error:
        return _invalid_result(request, "CORRUPTED_STARTING_STATE", {**evidence, "error": identity_error})

    treatment_ok, treatment_reason, treatment_detail, binding = bind_communication_treatment(
        request,
        caveman_policy_content=caveman_policy_content,
        caveman_policy_path=caveman_policy_path,
        caveman_repo_path=caveman_repo_path,
        presentation_root=presentation_root,
    )
    if not treatment_ok or not isinstance(binding, dict):
        return _invalid_result(
            request,
            treatment_reason or "MEASUREMENT_CAPTURE_FAILURE",
            {**evidence, "communication_treatment_error": treatment_detail},
        )
    prompt = str(binding.get("effective_prompt") or "")
    evidence["communication_binding"] = binding

    if observed_cli_version is None:
        try:
            version_cp = version_runner(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
        except OSError as exc:
            return _invalid_result(
                request,
                "INFRASTRUCTURE_OUTAGE",
                {**evidence, "error": f"cannot execute codex --version: {exc}"},
            )
        if version_cp.returncode != 0:
            return _invalid_result(
                request,
                "INFRASTRUCTURE_OUTAGE",
                {**evidence, "error": "codex --version failed", "stderr": version_cp.stderr},
            )
        try:
            observed_cli_version = parse_cli_version(version_cp.stdout or version_cp.stderr)
        except ValueError as exc:
            return _invalid_result(request, "MEASUREMENT_CAPTURE_FAILURE", {**evidence, "error": str(exc)})

    evidence.update(
        {
            "expected_cli_version": expected_cli_version,
            "observed_cli_version": observed_cli_version,
            "model": expected_model,
            "reasoning_effort": expected_reasoning_effort,
            "workspace": str(workspace.resolve()),
        }
    )
    if observed_cli_version != expected_cli_version:
        return _invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {**evidence, "error": "Codex CLI version mismatch"},
        )

    command = build_codex_command(
        prompt=prompt,
        workspace_dir=workspace.resolve(),
        model=expected_model,
        reasoning_effort=expected_reasoning_effort,
    )
    evidence["command"] = command
    started = time.perf_counter()

    if raw_jsonl is None:
        try:
            cp = run_command(
                command,
                cwd=str(workspace.resolve()),
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
        except OSError as exc:
            return _invalid_result(
                request,
                "INFRASTRUCTURE_OUTAGE",
                {**evidence, "error": f"Codex execution failed to start: {exc}"},
            )
        if cp.returncode != 0:
            return _invalid_result(
                request,
                "PROVIDER_OUTAGE",
                {
                    **evidence,
                    "error": "codex exec returned non-zero",
                    "returncode": cp.returncode,
                    "stderr": cp.stderr,
                },
            )
        raw_jsonl = cp.stdout
        evidence["stderr"] = cp.stderr
    wall_clock_ms = max(0, int((time.perf_counter() - started) * 1000))

    try:
        parsed = parse_codex_jsonl(raw_jsonl)
    except PermissionError as exc:
        return _invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {**evidence, "error": str(exc), "raw_jsonl": raw_jsonl},
        )
    except RuntimeError as exc:
        return _invalid_result(
            request,
            "PROVIDER_OUTAGE",
            {**evidence, "error": str(exc), "raw_jsonl": raw_jsonl},
        )
    except ValueError as exc:
        return _invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {**evidence, "error": str(exc), "raw_jsonl": raw_jsonl},
        )

    task_payload = request.get("task_payload")
    if not isinstance(task_payload, dict):
        task_payload = {}
    outcome, quality, safety = evaluate_task_outcome(
        {"response": parsed["response"]},
        task_payload,
    )
    usage = parsed["usage"]
    counter_id = compute_counter_id(observed_cli_version, expected_model, expected_reasoning_effort)
    evidence.update(
        {
            "jsonl_events": parsed["events"],
            "final_agent_message": parsed["response"],
            "counter_identity_provenance": "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE",
            "codex_adapter_revision": "TO_BE_FROZEN_AFTER_READINESS_CANONICALIZATION",
        }
    )
    validator_type = None
    validation_contract = task_payload.get("validation_contract")
    if isinstance(validation_contract, dict):
        validator_type = validation_contract.get("validator_type")
    validation_digest = digest_json(
        {"validator": validator_type, "outcome": outcome, "taskset_digest": TASKSET_DIGEST}
    )
    governance_digest = digest_json(
        {"governance_valid": outcome["governance_valid"], "safety": safety}
    )

    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": request["request_id"],
        "outcome": outcome,
        "quality": quality,
        "tokens": {
            "source": "HOST_REPORTED",
            "counter_id": counter_id,
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cached_input_tokens": usage["cached_input_tokens"],
            "reasoning_tokens": usage["reasoning_output_tokens"],
            "fresh_billable_tokens": None,
        },
        "cost": {"source": "UNAVAILABLE", "amount": None, "currency": None},
        "latency": {
            "wall_clock_ms": wall_clock_ms,
            "model_execution_ms": None,
            "tool_execution_ms": 0,
            "coordination_overhead_ms": None,
        },
        "coordination": {
            "specialist_messages": 0,
            "cross_specialist_messages": 0,
            "handoffs": 0,
            "handoff_failures": 0,
            "duplicate_work_events": 0,
            "contradiction_events": 0,
            "join_wait_ms": None,
            "specialist_reentry_events": 0,
        },
        "communication": {
            "progress_messages": 0,
            "model_progress_calls": 1,
            "user_visible_bytes": len(parsed["response"].encode("utf-8")),
            "context_transfer_bytes": len(prompt.encode("utf-8")),
            "semantic_preservation_failures": 0,
            "required_information_omissions": 0,
        },
        "safety": safety,
        "validation_digest": validation_digest,
        "governance_digest": governance_digest,
        "raw_evidence": evidence,
        "a5_shadow_observation": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Codex measurement executor readiness binding for Orchestra benchmark."
    )
    parser.add_argument("--expected-cli-version", required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument(
        "--expected-reasoning-effort",
        required=True,
        choices=sorted(ALLOWED_REASONING_EFFORTS),
    )
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--caveman-policy-path", type=Path)
    parser.add_argument("--caveman-repo-path", type=Path)
    parser.add_argument("--presentation-root", type=Path)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)

    try:
        request = (
            json.loads(args.request_file.read_text(encoding="utf-8"))
            if args.request_file
            else json.load(sys.stdin)
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": f"cannot load benchmark request: {exc}"}), file=sys.stderr)
        return 2
    if not isinstance(request, dict):
        print(json.dumps({"error": "benchmark request must be a JSON object"}), file=sys.stderr)
        return 2

    result = execute_request(
        request,
        expected_cli_version=args.expected_cli_version,
        expected_model=args.expected_model,
        expected_reasoning_effort=args.expected_reasoning_effort,
        workspace_dir=args.workspace_dir,
        caveman_policy_path=args.caveman_policy_path,
        caveman_repo_path=args.caveman_repo_path,
        presentation_root=args.presentation_root,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_file:
        args.output_file.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
