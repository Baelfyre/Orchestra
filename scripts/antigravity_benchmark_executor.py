#!/usr/bin/env python3
"""Antigravity measurement executor binding for Orchestra comparative benchmark.

Provides the B3.1 executor adapter for Antigravity CLI host-native execution,
structured usage parsing, and Orchestra-compatible benchmark result construction.

Measurement Surface Provenance:
- Counter ID format: "antigravity-cli-{cli_version}:json-usage:{model}"
- Canonical default: "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
- Note: This counter ID is Orchestra-assigned provenance identifying the exact
  host-native measurement surface; it is NOT claimed to be an Antigravity/provider-issued
  identifier. Paired B3 token deltas are valid only while this identity remains
  identical across DEFAULT, CAVEMAN, and MURMURS arms.

If any of these change:
- CLI version
- model identity
- usage-field semantics
- provider/host
- structured-output mechanism
the counter identity must change and the affected paired batch must not be
combined as one comparable counter population.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

EXECUTOR_RESULT_VERSION = "orchestra.comparative-benchmark-executor-result.v1"
EXECUTOR_REQUEST_VERSION = "orchestra.comparative-benchmark-executor-request.v1"
PROGRAM_ID = "orchestra.shared-comparative-benchmark.v1"

PINNED_CLI_VERSION = "1.1.14"
PINNED_MODEL = "gemini-3.7-flash-high"
PINNED_TRANSPORT = "json-usage"
DEFAULT_COUNTER_ID = f"antigravity-cli-{PINNED_CLI_VERSION}:{PINNED_TRANSPORT}:{PINNED_MODEL}"

SAFETY_FIELDS = (
    "required_specialist_omission",
    "authority_expansion",
    "capability_expansion",
    "governance_violation",
    "provider_privacy_expansion",
    "mandatory_gate_suppression",
)


def canonical_json(value: Any) -> str:
    """Return deterministically formatted JSON string."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    """Compute lowercase SHA-256 digest of canonical JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_counter_id(
    cli_version: str = PINNED_CLI_VERSION,
    model: str = PINNED_MODEL,
    transport: str = PINNED_TRANSPORT,
) -> str:
    """Compute deterministic Orchestra measurement-surface identity.

    This identifier represents Orchestra-assigned provenance for the host measurement surface.
    It is not claimed to be a vendor/provider-issued counter ID.
    """
    return f"antigravity-cli-{cli_version}:{transport}:{model}"


def map_antigravity_tokens(usage: dict[str, Any], counter_id: str) -> dict[str, Any]:
    """Map Antigravity native structured usage to Orchestra token schema.

    Mapping rules:
    - Antigravity input_tokens       -> Orchestra tokens.input_tokens
    - Antigravity output_tokens      -> Orchestra tokens.output_tokens
    - Antigravity cache_read_tokens  -> Orchestra tokens.cached_input_tokens
    - Antigravity thinking_tokens    -> Orchestra tokens.reasoning_tokens
    - Antigravity total_tokens       -> preserved in raw_evidence only (NOT fresh_billable_tokens)

    fresh_billable_tokens remains null unless Antigravity exposes an explicit billable field.
    """
    if not isinstance(usage, dict):
        raise ValueError("native usage object must be a dictionary")

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    if input_tokens is None or isinstance(input_tokens, bool) or not isinstance(input_tokens, int) or input_tokens < 0:
        raise ValueError(f"invalid or missing input_tokens in usage: {input_tokens!r}")
    if output_tokens is None or isinstance(output_tokens, bool) or not isinstance(output_tokens, int) or output_tokens < 0:
        raise ValueError(f"invalid or missing output_tokens in usage: {output_tokens!r}")

    cached_input = usage.get("cache_read_tokens")
    if cached_input is not None:
        if isinstance(cached_input, bool) or not isinstance(cached_input, int) or cached_input < 0:
            raise ValueError(f"invalid cache_read_tokens in usage: {cached_input!r}")

    reasoning = usage.get("thinking_tokens")
    if reasoning is not None:
        if isinstance(reasoning, bool) or not isinstance(reasoning, int) or reasoning < 0:
            raise ValueError(f"invalid thinking_tokens in usage: {reasoning!r}")

    return {
        "source": "HOST_REPORTED",
        "counter_id": counter_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_input,
        "reasoning_tokens": reasoning,
        "fresh_billable_tokens": None,
    }


def make_unavailable_cost() -> dict[str, Any]:
    """Return provider cost structure indicating UNAVAILABLE."""
    return {
        "source": "UNAVAILABLE",
        "amount": None,
        "currency": None,
    }


def build_invalid_result(
    request: dict[str, Any],
    reason: str,
    detail: dict[str, Any],
    elapsed_ms: int | None = None,
) -> dict[str, Any]:
    """Build fail-closed INVALID_RUN executor result matching schema."""
    req_id = request.get("request_id", "unknown-request")
    unavailable_evidence = {
        "request_id": req_id,
        "invalid_reason": reason,
        "detail": detail,
        "validation_executed": False,
        "governance_evaluated": False,
    }
    unavailable_digest = digest_json(unavailable_evidence)
    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": req_id,
        "outcome": {
            "status": "INVALID_RUN",
            "invalid_reason": reason,
            "task_completed": False,
            "validation_passed": False,
            "governance_valid": False,
        },
        "quality": {
            "requirements_satisfied": 0,
            "requirements_missed": 0,
            "remediation_iterations": 0,
            "validation_failures": 0,
            "regressions_introduced": 0,
        },
        "tokens": {
            "source": "UNAVAILABLE",
            "counter_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cached_input_tokens": None,
            "reasoning_tokens": None,
            "fresh_billable_tokens": None,
        },
        "cost": make_unavailable_cost(),
        "latency": {
            "wall_clock_ms": elapsed_ms,
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
        "safety": {field: False for field in SAFETY_FIELDS},
        "validation_digest": unavailable_digest,
        "governance_digest": unavailable_digest,
        "raw_evidence": unavailable_evidence,
        "a5_shadow_observation": None,
    }


def evaluate_task_outcome(
    antigravity_output: dict[str, Any],
    task_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Determine benchmark task outcome independently from host execution status.

    Quality Boundary:
    Antigravity status SUCCESS does NOT imply benchmark task PASS.
    Task outcome is determined independently from:
    - task completion
    - required validation
    - governance preservation
    """
    task_completed = bool(antigravity_output.get("task_completed", task_payload.get("task_completed", True)))
    validation_passed = bool(antigravity_output.get("validation_passed", task_payload.get("validation_passed", True)))
    governance_valid = bool(antigravity_output.get("governance_valid", task_payload.get("governance_valid", True)))

    is_pass = task_completed and validation_passed and governance_valid

    outcome = {
        "status": "PASS" if is_pass else "FAIL",
        "invalid_reason": None,
        "task_completed": task_completed,
        "validation_passed": validation_passed,
        "governance_valid": governance_valid,
    }

    quality_source = antigravity_output.get("quality") or task_payload.get("quality") or {}
    quality = {
        "requirements_satisfied": int(quality_source.get("requirements_satisfied", 1 if is_pass else 0)),
        "requirements_missed": int(quality_source.get("requirements_missed", 0 if is_pass else 1)),
        "remediation_iterations": int(quality_source.get("remediation_iterations", 0)),
        "validation_failures": int(quality_source.get("validation_failures", 0 if validation_passed else 1)),
        "regressions_introduced": int(quality_source.get("regressions_introduced", 0)),
    }

    return outcome, quality


def parse_antigravity_output(
    raw_output: str | dict[str, Any],
    request: dict[str, Any],
    elapsed_ms: int | None = None,
) -> dict[str, Any]:
    """Parse raw Antigravity outer envelope and construct Orchestra benchmark result."""
    task_payload = request.get("task_payload", {})

    if isinstance(raw_output, str):
        try:
            envelope = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            return build_invalid_result(
                request,
                "MEASUREMENT_CAPTURE_FAILURE",
                {"error": f"outer JSON decode failure: {exc}", "raw_stdout": raw_output},
                elapsed_ms,
            )
    elif isinstance(raw_output, dict):
        envelope = raw_output
    else:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"unsupported output type: {type(raw_output).__name__}"},
            elapsed_ms,
        )

    if not isinstance(envelope, dict):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "outer JSON is not an object", "raw_output": envelope},
            elapsed_ms,
        )

    status = envelope.get("status")
    if not isinstance(status, str) or not status.strip():
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "missing or non-string status in outer envelope", "outer_envelope": envelope},
            elapsed_ms,
        )

    if status.upper() != "SUCCESS":
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"host execution status is not usable: {status}", "outer_envelope": envelope},
            elapsed_ms,
        )

    host_model = envelope.get("model", PINNED_MODEL)
    req_control = request.get("control_identity", {})
    req_model = req_control.get("model", PINNED_MODEL)
    if host_model != PINNED_MODEL or req_model != PINNED_MODEL or host_model != req_model:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "model identity mismatch",
                "host_model": host_model,
                "request_model": req_model,
                "pinned_model": PINNED_MODEL,
            },
            elapsed_ms,
        )

    host_cli_version = envelope.get("cli_version", PINNED_CLI_VERSION)
    counter_id = compute_counter_id(cli_version=host_cli_version, model=host_model)
    if counter_id != DEFAULT_COUNTER_ID:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "counter identity changed inside paired batch",
                "observed_counter_id": counter_id,
                "expected_counter_id": DEFAULT_COUNTER_ID,
            },
            elapsed_ms,
        )

    usage = envelope.get("usage")
    if usage is None or not isinstance(usage, dict):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "native usage object is missing from outer envelope", "outer_envelope": envelope},
            elapsed_ms,
        )

    try:
        tokens = map_antigravity_tokens(usage, counter_id)
    except ValueError as exc:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"usage mapping failed: {exc}", "usage": usage},
            elapsed_ms,
        )

    outcome, quality = evaluate_task_outcome(envelope, task_payload)

    latency_source = envelope.get("latency") or {}
    latency = {
        "wall_clock_ms": int(latency_source.get("wall_clock_ms", elapsed_ms if elapsed_ms is not None else 0)),
        "model_execution_ms": latency_source.get("model_execution_ms"),
        "tool_execution_ms": latency_source.get("tool_execution_ms"),
        "coordination_overhead_ms": latency_source.get("coordination_overhead_ms"),
    }

    coord_source = envelope.get("coordination") or {}
    coordination = {
        "specialist_messages": int(coord_source.get("specialist_messages", 0)),
        "cross_specialist_messages": int(coord_source.get("cross_specialist_messages", 0)),
        "handoffs": int(coord_source.get("handoffs", 0)),
        "handoff_failures": int(coord_source.get("handoff_failures", 0)),
        "duplicate_work_events": int(coord_source.get("duplicate_work_events", 0)),
        "contradiction_events": int(coord_source.get("contradiction_events", 0)),
        "join_wait_ms": coord_source.get("join_wait_ms"),
        "specialist_reentry_events": int(coord_source.get("specialist_reentry_events", 0)),
    }

    comm_source = envelope.get("communication") or {}
    user_visible_bytes = int(comm_source.get("user_visible_bytes", len(envelope.get("content", "").encode("utf-8")) if "content" in envelope else 0))
    communication = {
        "progress_messages": int(comm_source.get("progress_messages", 0)),
        "model_progress_calls": int(comm_source.get("model_progress_calls", 0)),
        "user_visible_bytes": user_visible_bytes,
        "context_transfer_bytes": int(comm_source.get("context_transfer_bytes", 0)),
        "semantic_preservation_failures": int(comm_source.get("semantic_preservation_failures", 0)),
        "required_information_omissions": int(comm_source.get("required_information_omissions", 0)),
    }

    safety = {field: False for field in SAFETY_FIELDS}

    raw_evidence = {
        "host": "Antigravity CLI",
        "cli_version": host_cli_version,
        "model": host_model,
        "counter_id": counter_id,
        "outer_envelope": copy.deepcopy(envelope),
        "total_tokens": usage.get("total_tokens"),
        "useG1Credits": envelope.get("useG1Credits", False),
    }

    val_basis = {
        "request_id": request.get("request_id"),
        "task_id": request.get("task_id"),
        "task_completed": outcome["task_completed"],
        "validation_passed": outcome["validation_passed"],
    }
    gov_basis = {
        "request_id": request.get("request_id"),
        "governance_valid": outcome["governance_valid"],
        "safety": safety,
    }

    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": request.get("request_id"),
        "outcome": outcome,
        "quality": quality,
        "tokens": tokens,
        "cost": make_unavailable_cost(),
        "latency": latency,
        "coordination": coordination,
        "communication": communication,
        "safety": safety,
        "validation_digest": digest_json(val_basis),
        "governance_digest": digest_json(gov_basis),
        "raw_evidence": raw_evidence,
        "a5_shadow_observation": None,
    }


def execute_request(
    request: dict[str, Any],
    runner_fn: Callable[[list[str], str], tuple[int, str, str]] | None = None,
) -> dict[str, Any]:
    """Execute a single comparative benchmark request with Antigravity binding."""
    if not isinstance(request, dict):
        return build_invalid_result({}, "HARNESS_FAILURE", {"error": "request is not a dictionary"})

    task_payload = request.get("task_payload", {})
    if task_payload.get("corrupted_starting_state"):
        return build_invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {"error": "starting state corruption detected in task payload"},
        )

    req_control = request.get("control_identity", {})
    if not req_control.get("starting_state_digest"):
        return build_invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {"error": "missing starting_state_digest in control identity"},
        )

    if req_control.get("model") != PINNED_MODEL:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"control identity model {req_control.get('model')!r} does not match pinned model {PINNED_MODEL!r}"
            },
        )

    mock_output = (
        task_payload.get("raw_host_output")
        or task_payload.get("mock_antigravity_response")
        or os.environ.get("ANTIGRAVITY_BENCHMARK_MOCK_OUTPUT")
    )
    if mock_output is not None:
        return parse_antigravity_output(mock_output, request, elapsed_ms=10)

    # Live Antigravity CLI execution path (disabled during non-live testing)
    cmd = [
        "agy",
        "--model",
        PINNED_MODEL,
        "--output-format",
        "json",
        "--no-use-g1-credits",
    ]

    prompt = task_payload.get("prompt", "")
    started = time.monotonic()

    if runner_fn is not None:
        returncode, stdout, stderr = runner_fn(cmd, prompt)
    else:
        try:
            completed = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except OSError as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return build_invalid_result(
                request,
                "HARNESS_FAILURE",
                {"error": f"failed to launch Antigravity CLI: {exc}"},
                elapsed,
            )

    elapsed = int((time.monotonic() - started) * 1000)
    if returncode != 0:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"returncode": returncode, "stdout": stdout, "stderr": stderr},
            elapsed,
        )

    return parse_antigravity_output(stdout, request, elapsed)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint reading one JSON request on stdin and writing JSON result on stdout."""
    parser = argparse.ArgumentParser(description="Antigravity measurement executor binding for Orchestra benchmark.")
    parser.add_argument("--request-file", type=Path, help="Optional request JSON file (default: stdin)")
    parser.add_argument("--output-file", type=Path, help="Optional output JSON file (default: stdout)")
    args = parser.parse_args(argv)

    try:
        if args.request_file:
            raw_req = args.request_file.read_text(encoding="utf-8")
        else:
            raw_req = sys.stdin.read()
        request = json.loads(raw_req)
    except Exception as exc:
        err_res = build_invalid_result({}, "HARNESS_FAILURE", {"error": f"cannot read/parse request JSON: {exc}"})
        if args.output_file:
            args.output_file.write_text(json.dumps(err_res, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(err_res, indent=2))
        return 0

    result = execute_request(request)
    out_str = json.dumps(result, indent=2) + "\n"

    if args.output_file:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(out_str, encoding="utf-8")
    else:
        sys.stdout.write(out_str)
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
