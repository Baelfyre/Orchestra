from __future__ import annotations

import json
import math
from typing import Any

from .models import APPROVED_UNIT_PLAN_SCHEMA_VERSION, ApprovedUnitPlan, OrchestraRuntimeEnvelope


def _validate_json_domain(value: Any, seen: set[int] | None = None) -> None:
    """Validate that nested values strictly adhere to the supported JSON domain."""
    if seen is None:
        seen = set()

    if value is None or isinstance(value, (bool, str, int)):
        return
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"non-finite float value '{value}' is not supported in Orchestra-deterministic JSON")
        return
    elif isinstance(value, (list, tuple)):
        obj_id = id(value)
        if obj_id in seen:
            raise ValueError("cyclic structure detected in detail/data payload")
        seen.add(obj_id)
        try:
            for item in value:
                _validate_json_domain(item, seen)
        finally:
            seen.remove(obj_id)
    elif isinstance(value, dict):
        obj_id = id(value)
        if obj_id in seen:
            raise ValueError("cyclic structure detected in detail/data payload")
        seen.add(obj_id)
        try:
            for k, v in value.items():
                if not isinstance(k, str):
                    raise TypeError(f"dictionary keys must be strings, got {type(k).__name__}")
                _validate_json_domain(v, seen)
        finally:
            seen.remove(obj_id)
    else:
        raise TypeError(f"unsupported data type '{type(value).__name__}' in envelope payload")


ALLOWED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "message_type",
    "timestamp",
    "run_id",
    "specialist",
    "operation",
    "status",
    "disposition",
    "reason_code",
    "event_type",
    "details",
    "parent_run_id",
    "collaboration_session_id",
    "phase_id",
    "unit_id",
    "authority_decision_ref",
    "capability_decision_ref",
    "governance_decision_ref",
    "evidence_fingerprint",
    "correlation_id",
    "summary",
    "data",
}

ALLOWED_UNIT_PLAN_FIELDS = {
    "schema_version",
    "unit_id",
    "unit_revision",
    "unit_name",
    "phase_id",
    "execution_envelope_ref",
    "scope_ref",
    "responsible_specialist",
    "objective",
    "expected_outputs",
    "validation_requirements",
    "allowed_paths",
    "prohibited_paths",
    "dependency_unit_ids",
    "governance_decision_ref",
}


def _duplicate_key_detect_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise ValueError(f"duplicate key '{k}' detected in JSON payload")
        res[k] = v
    return res


def serialize_runtime_envelope(envelope: OrchestraRuntimeEnvelope) -> bytes:
    if not isinstance(envelope, OrchestraRuntimeEnvelope):
        raise TypeError(f"expected OrchestraRuntimeEnvelope instance, got {type(envelope).__name__}")

    raw_dict = envelope.to_dict()
    _validate_json_domain(raw_dict)

    serialized_str = json.dumps(
        raw_dict,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )

    return serialized_str.encode("utf-8")


def deserialize_runtime_envelope(payload: bytes | str) -> OrchestraRuntimeEnvelope:
    if isinstance(payload, bytes):
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("UTF-8 BOM is rejected as non-canonical transport")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"invalid UTF-8 byte sequence: {exc}") from exc
    elif isinstance(payload, str):
        if payload.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is rejected as non-canonical transport")
        text = payload
    else:
        raise TypeError(f"payload must be bytes or str, got {type(payload).__name__}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("empty or whitespace-only envelope payload")

    try:
        raw_data = json.loads(text, object_pairs_hook=_duplicate_key_detect_hook)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON payload: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"top-level envelope JSON must be an object, got {type(raw_data).__name__}")

    for key in raw_data:
        if key not in ALLOWED_TOP_LEVEL_FIELDS:
            raise ValueError(f"unknown top-level field '{key}'")

    _validate_json_domain(raw_data)

    required_non_null = {
        "schema_version",
        "message_type",
        "timestamp",
        "run_id",
        "specialist",
    }
    for req in required_non_null:
        if req not in raw_data:
            raise ValueError(f"missing required field '{req}'")
        if raw_data[req] is None:
            raise ValueError(f"field '{req}' cannot be null")
        if not isinstance(raw_data[req], str):
            raise ValueError(f"field '{req}' must be a string")

    schema_ver = raw_data["schema_version"]
    if schema_ver != "1.0.0":
        raise ValueError(f"unsupported schema_version: '{schema_ver}'")

    return OrchestraRuntimeEnvelope(**raw_data)


def serialize_approved_unit_plan(plan: ApprovedUnitPlan) -> bytes:
    if not isinstance(plan, ApprovedUnitPlan):
        raise TypeError(f"expected ApprovedUnitPlan instance, got {type(plan).__name__}")

    raw_dict: dict[str, Any] = {
        "schema_version": plan.schema_version,
        "unit_id": plan.unit_id,
        "unit_revision": plan.unit_revision,
        "unit_name": plan.unit_name,
        "phase_id": plan.phase_id,
        "execution_envelope_ref": plan.execution_envelope_ref,
        "scope_ref": plan.scope_ref,
        "responsible_specialist": plan.responsible_specialist,
        "objective": plan.objective,
        "expected_outputs": list(plan.expected_outputs),
        "validation_requirements": list(plan.validation_requirements),
    }

    if plan.allowed_paths is not None:
        raw_dict["allowed_paths"] = list(plan.allowed_paths)
    if plan.prohibited_paths is not None:
        raw_dict["prohibited_paths"] = list(plan.prohibited_paths)
    if plan.dependency_unit_ids is not None:
        raw_dict["dependency_unit_ids"] = list(plan.dependency_unit_ids)
    if plan.governance_decision_ref is not None:
        raw_dict["governance_decision_ref"] = plan.governance_decision_ref

    _validate_json_domain(raw_dict)

    serialized_str = json.dumps(
        raw_dict,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )
    return serialized_str.encode("utf-8")


def deserialize_approved_unit_plan(payload: bytes | str) -> ApprovedUnitPlan:
    if isinstance(payload, bytes):
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("UTF-8 BOM is rejected as non-canonical transport")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"invalid UTF-8 byte sequence: {exc}") from exc
    elif isinstance(payload, str):
        if payload.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is rejected as non-canonical transport")
        text = payload
    else:
        raise TypeError(f"payload must be bytes or str, got {type(payload).__name__}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("empty or whitespace-only unit plan payload")

    try:
        raw_data = json.loads(text, object_pairs_hook=_duplicate_key_detect_hook)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON payload: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"top-level unit plan JSON must be an object, got {type(raw_data).__name__}")

    for key in raw_data:
        if key not in ALLOWED_UNIT_PLAN_FIELDS:
            raise ValueError(f"unknown top-level field '{key}'")

    _validate_json_domain(raw_data)

    schema_ver = str(raw_data.get("schema_version", "1.0.0")).strip()
    if schema_ver != APPROVED_UNIT_PLAN_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: '{schema_ver}'")

    required_fields = [
        "unit_id",
        "unit_revision",
        "unit_name",
        "phase_id",
        "execution_envelope_ref",
        "scope_ref",
        "responsible_specialist",
        "objective",
        "expected_outputs",
        "validation_requirements",
    ]
    for req in required_fields:
        if req not in raw_data:
            raise ValueError(f"missing required field '{req}'")
        if raw_data[req] is None:
            raise ValueError(f"field '{req}' cannot be null")

    outputs = raw_data["expected_outputs"]
    if not isinstance(outputs, list):
        raise ValueError("expected_outputs must be a list")
    expected_outputs_tuple = tuple(outputs)

    val_reqs = raw_data["validation_requirements"]
    if not isinstance(val_reqs, list):
        raise ValueError("validation_requirements must be a list")
    val_reqs_tuple = tuple(val_reqs)

    allowed_paths = tuple(raw_data["allowed_paths"]) if isinstance(raw_data.get("allowed_paths"), list) else None if "allowed_paths" in raw_data else None
    prohibited_paths = tuple(raw_data["prohibited_paths"]) if isinstance(raw_data.get("prohibited_paths"), list) else None if "prohibited_paths" in raw_data else None
    dependency_unit_ids = tuple(raw_data["dependency_unit_ids"]) if isinstance(raw_data.get("dependency_unit_ids"), list) else None if "dependency_unit_ids" in raw_data else None

    return ApprovedUnitPlan(
        schema_version=schema_ver,
        unit_id=str(raw_data["unit_id"]),
        unit_revision=raw_data["unit_revision"],
        unit_name=str(raw_data["unit_name"]),
        phase_id=str(raw_data["phase_id"]),
        execution_envelope_ref=str(raw_data["execution_envelope_ref"]),
        scope_ref=str(raw_data["scope_ref"]),
        responsible_specialist=str(raw_data["responsible_specialist"]),
        objective=str(raw_data["objective"]),
        expected_outputs=expected_outputs_tuple,
        validation_requirements=val_reqs_tuple,
        allowed_paths=allowed_paths,
        prohibited_paths=prohibited_paths,
        dependency_unit_ids=dependency_unit_ids,
        governance_decision_ref=raw_data.get("governance_decision_ref"),
    )
