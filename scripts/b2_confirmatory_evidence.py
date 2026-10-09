#!/usr/bin/env python3
"""Pure B2.3.1 evidence instrumentation helpers.

These helpers retain and recompute synthetic specialist handoff evidence and
Codex host-counter provenance for the non-production B2 topology benchmark.
They perform no model, network, tool, repository, or policy action.
"""

from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping, Sequence

MAX_RETAINED_ADVISORY_UTF8_BYTES = 16_384
RESPONSE_ENCODING = "UTF-8"
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
COUNTER_STABILITY_CLASSIFICATIONS = frozenset(
    {
        "STABLE_EXACT",
        "CACHE_STATE_VARIANT",
        "INPUT_COUNTER_VARIANT",
        "UNSTABLE_ATTRIBUTION",
    }
)


class B2EvidenceError(ValueError):
    """Raised when measurement evidence cannot be retained or recomputed exactly."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_response_evidence(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise B2EvidenceError("specialist response must be a string")
    raw = text.encode("utf-8")
    if len(raw) > MAX_RETAINED_ADVISORY_UTF8_BYTES:
        raise B2EvidenceError(
            "specialist advisory exceeds the 16384-byte B2.3.1 retention ceiling"
        )
    return {
        "response_text": text,
        "response_encoding": RESPONSE_ENCODING,
        "response_utf8_bytes": len(raw),
        "response_utf8_sha256": sha256(raw).hexdigest(),
        "response_digest": digest_json(text),
    }


def build_advisory_reference(
    *, source_call_index: int, specialist: str, response_evidence: Mapping[str, Any]
) -> dict[str, Any]:
    if source_call_index < 1:
        raise B2EvidenceError("source_call_index must be positive")
    byte_count = response_evidence.get("response_utf8_bytes")
    raw_digest = response_evidence.get("response_utf8_sha256")
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
        raise B2EvidenceError("response_utf8_bytes must be a non-negative integer")
    if not isinstance(raw_digest, str) or len(raw_digest) != 64:
        raise B2EvidenceError("response_utf8_sha256 must be a SHA-256 hex digest")
    return {
        "source_call_index": source_call_index,
        "specialist": specialist,
        "response_utf8_bytes": byte_count,
        "response_utf8_sha256": raw_digest,
    }


def validate_usage_object(raw_usage: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_usage, Mapping):
        raise B2EvidenceError("turn.completed usage must be an object")
    exact = copy.deepcopy(dict(raw_usage))
    for field in USAGE_FIELDS:
        value = exact.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise B2EvidenceError(f"turn.completed usage.{field} must be a non-negative integer")
    if exact["cached_input_tokens"] > exact["input_tokens"]:
        raise B2EvidenceError("cached_input_tokens cannot exceed input_tokens")
    return exact


def build_counter_identity(
    *,
    counter_id: str,
    prompt_digest: str,
    role: str,
    specialist: str | None,
    cli_version: str,
    model: str,
    reasoning_effort: str,
    transport: str,
    workspace_identity: str,
) -> dict[str, Any]:
    identity = {
        "counter_id": counter_id,
        "prompt_digest": prompt_digest,
        "role": role,
        "specialist": specialist,
        "cli_version": cli_version,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "transport": transport,
        "workspace_identity": workspace_identity,
    }
    return {
        "identity": identity,
        "counter_stability_key": digest_json(identity),
    }


def build_usage_evidence(
    *, raw_usage: Mapping[str, Any], counter_identity: Mapping[str, Any]
) -> dict[str, Any]:
    exact = validate_usage_object(raw_usage)
    stability_key = counter_identity.get("counter_stability_key")
    identity = counter_identity.get("identity")
    if not isinstance(stability_key, str) or len(stability_key) != 64:
        raise B2EvidenceError("counter_stability_key is invalid")
    if not isinstance(identity, Mapping):
        raise B2EvidenceError("counter identity is missing")
    return {
        "turn_completed_usage": exact,
        "turn_completed_usage_digest": digest_json(exact),
        "input_tokens": exact["input_tokens"],
        "cached_input_tokens": exact["cached_input_tokens"],
        "output_tokens": exact["output_tokens"],
        "reasoning_output_tokens": exact["reasoning_output_tokens"],
        "non_cached_input_tokens": exact["input_tokens"] - exact["cached_input_tokens"],
        "counter_identity": copy.deepcopy(dict(identity)),
        "counter_stability_key": stability_key,
        "counter_stability_classification": None,
    }


def classify_counter_stability(records: Sequence[Mapping[str, Any]]) -> str:
    """Classify repeated call evidence sharing one frozen measurement identity."""
    if len(records) < 2:
        return "UNSTABLE_ATTRIBUTION"
    keys = {record.get("counter_stability_key") for record in records}
    if len(keys) != 1 or None in keys:
        return "UNSTABLE_ATTRIBUTION"
    try:
        inputs = {int(record["input_tokens"]) for record in records}
        cached = {int(record["cached_input_tokens"]) for record in records}
    except (KeyError, TypeError, ValueError):
        return "UNSTABLE_ATTRIBUTION"
    if any(value < 0 for value in inputs | cached):
        return "UNSTABLE_ATTRIBUTION"
    if len(inputs) == 1 and len(cached) == 1:
        return "STABLE_EXACT"
    if len(inputs) == 1:
        return "CACHE_STATE_VARIANT"
    return "INPUT_COUNTER_VARIANT"


def recompute_context_transfer_ledger(
    *,
    specialist_calls: Sequence[Mapping[str, Any]],
    finalizer_call: Mapping[str, Any],
    reported_context_transfer_bytes: int | None = None,
) -> dict[str, int]:
    downstream = 0
    for call in specialist_calls:
        refs = call.get("prior_advisory_inputs", [])
        if not isinstance(refs, list):
            raise B2EvidenceError("prior_advisory_inputs must be an array")
        for ref in refs:
            if not isinstance(ref, Mapping):
                raise B2EvidenceError("prior advisory reference must be an object")
            value = ref.get("response_utf8_bytes")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise B2EvidenceError("prior advisory response_utf8_bytes is invalid")
            downstream += value

    final_refs = finalizer_call.get("advisory_inputs", [])
    if not isinstance(final_refs, list):
        raise B2EvidenceError("finalizer advisory_inputs must be an array")
    finalizer = 0
    for ref in final_refs:
        if not isinstance(ref, Mapping):
            raise B2EvidenceError("finalizer advisory reference must be an object")
        value = ref.get("response_utf8_bytes")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise B2EvidenceError("finalizer advisory response_utf8_bytes is invalid")
        finalizer += value

    recomputed = downstream + finalizer
    if reported_context_transfer_bytes is not None:
        if (
            not isinstance(reported_context_transfer_bytes, int)
            or isinstance(reported_context_transfer_bytes, bool)
            or reported_context_transfer_bytes < 0
        ):
            raise B2EvidenceError("reported context_transfer_bytes is invalid")
        if reported_context_transfer_bytes != recomputed:
            raise B2EvidenceError(
                "reported context_transfer_bytes does not equal recomputed context-transfer evidence"
            )
    return {
        "downstream_specialist_handoff_bytes": downstream,
        "finalizer_advisory_bytes": finalizer,
        "recomputed_context_transfer_bytes": recomputed,
    }
