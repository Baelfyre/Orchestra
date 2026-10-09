#!/usr/bin/env python3
"""Validate the canonical UAI provider/model capability evidence contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("machine/providers/provider-model-capability-contract.v1.json")
SCHEMA_PATH = Path("machine/schemas/provider-model-capability-contract.v1.schema.json")
CAPABILITY_DEFINITIONS = {
    "TOOL_CALLING": ("INTERACTION", "BOOLEAN"),
    "STRUCTURED_OUTPUT": ("OUTPUT", "BOOLEAN"),
    "CONTEXT_LIMITS": ("CONTEXT", "INTEGER_OR_RANGE"),
    "VISION_MULTIMODAL_INPUT": ("INPUT", "BOOLEAN"),
    "CODE_TERMINAL_EXPOSURE": ("EXECUTION", "ENUM_SET"),
    "SUB_AGENT_SUPPORT": ("ORCHESTRATION", "BOOLEAN"),
    "CONCURRENCY_EXPOSURE": ("ORCHESTRATION", "ENUM_SET"),
    "MCP_TOOL_COMPATIBILITY": ("TRANSPORT", "ENUM_SET"),
    "MODEL_SELECTION_CONTROLS": ("SELECTION", "ENUM_SET"),
    "REASONING_RUNTIME_MODES": ("RUNTIME", "ENUM_SET"),
    "PERMISSION_SEMANTICS": ("PERMISSION", "DESCRIPTIVE"),
    "PROVIDER_POLICY_RESTRICTIONS": ("POLICY", "DESCRIPTIVE"),
}
DISPOSITIONS = {
    "SUPPORTED_VERIFIED",
    "SUPPORTED_WITH_LIMITS",
    "AVAILABLE_NOT_YET_VERIFIED",
    "UNKNOWN",
    "BLOCKED_BY_POLICY",
    "VERIFIED_UNSUPPORTED_LOCALLY",
    "UNSUPPORTED",
}
AUTHORITY_FIELDS = {
    "capability_grants_execution_authority",
    "capability_grants_routing_authority",
    "capability_grants_specialist_selection_authority",
    "capability_grants_workflow_topology_authority",
    "capability_grants_provider_selection_authority",
    "capability_grants_model_selection_authority",
    "automatic_provider_switching",
    "automatic_provider_fallback",
    "learned_routing_promotion",
    "execution_authorized",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PROFILE_ID_PATTERN = re.compile(r"^provider-model-capability\.[0-9a-f]{24}$")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_object(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"MALFORMED:{label}:must_be_object")
        return False
    return True


def _require_non_empty_strings(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"MALFORMED:{label}:must_be_non_empty_string_list")
        return
    if len(value) != len(set(value)):
        errors.append(f"MALFORMED:{label}:duplicates")


def _validate_authority(value: Any, label: str, errors: list[str]) -> None:
    if not _require_object(value, label, errors):
        return
    for field in sorted(AUTHORITY_FIELDS):
        if value.get(field) is not False:
            errors.append(f"AUTHORITY_EXPANSION:{label}.{field}")
    for field in sorted(set(value) - AUTHORITY_FIELDS):
        errors.append(f"AUTHORITY_EXPANSION:{label}.{field}")


def _validate_evidence(value: Any, label: str, errors: list[str]) -> str | None:
    if not _require_object(value, label, errors):
        return None
    for field in ("source_repository", "source_path", "source_type", "observation_id", "observed_at"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"MALFORMED:{label}.{field}")
    for field in ("source_commit",):
        if not isinstance(value.get(field), str) or not SHA_PATTERN.fullmatch(value[field]):
            errors.append(f"MALFORMED:{label}.{field}:sha")
    freshness = value.get("freshness")
    if not _require_object(freshness, f"{label}.freshness", errors):
        return None
    status = freshness.get("status")
    if status not in {"CURRENT_AT_OBSERVATION", "STALE", "UNKNOWN"}:
        errors.append(f"FRESHNESS_INVALID:{label}.freshness.status")
    if not isinstance(freshness.get("max_age_hours"), int) or freshness["max_age_hours"] < 1:
        errors.append(f"MALFORMED:{label}.freshness.max_age_hours")
    _require_non_empty_strings(
        freshness.get("invalidation_triggers"),
        f"{label}.freshness.invalidation_triggers",
        errors,
    )
    return status if isinstance(status, str) else None


def validate_payload(contract: Any, schema: Any | None = None) -> list[str]:
    errors: list[str] = []
    if not _require_object(contract, "contract", errors):
        return errors

    required = {
        "$schema",
        "schema_version",
        "contract_id",
        "contract_revision",
        "contract_role",
        "authority",
        "broker_policy",
        "capability_definitions",
        "provider_model_profiles",
        "evidence_policy",
    }
    for field in sorted(required - set(contract)):
        errors.append(f"MALFORMED:missing:{field}")
    expected = {
        "$schema": "./machine/schemas/provider-model-capability-contract.v1.schema.json",
        "schema_version": "orchestra.provider-model-capability-contract.v1",
        "contract_id": "orchestra-provider-model-capability",
        "contract_revision": 1,
        "contract_role": "canonical_uai_provider_model_capability_contract",
    }
    for field, expected_value in expected.items():
        if field in contract and contract[field] != expected_value:
            errors.append(f"MALFORMED:{field}:unexpected_value")

    if schema is not None and not isinstance(schema, dict):
        errors.append("MALFORMED:schema:must_be_object")
    else:
        try:
            import jsonschema

            validator = jsonschema.Draft202012Validator(schema)
            for item in validator.iter_errors(contract):
                location = ".".join(str(part) for part in item.absolute_path) or "$"
                errors.append(f"SCHEMA_VALIDATION:{location}:{item.message}")
        except ImportError:
            pass
        except Exception as exc:  # pragma: no cover - schema tooling failure is environment-specific
            errors.append(f"SCHEMA_VALIDATION:validator_error:{exc}")

    _validate_authority(contract.get("authority"), "authority", errors)

    broker_policy = contract.get("broker_policy")
    if _require_object(broker_policy, "broker_policy", errors):
        expected_broker_policy = {
            "mode": "SHADOW_ADVISORY_NON_AUTHORIZING",
            "output_dispositions": ["ELIGIBLE", "ELIGIBLE_WITH_LIMITS", "INELIGIBLE", "UNKNOWN", "POLICY_BLOCKED"],
            "provider_selection_changed": False,
            "automatic_provider_switching": False,
            "automatic_provider_fallback": False,
            "learned_routing_promotion": False,
            "specialist_routing_changed": False,
            "workflow_topology_changed": False,
        }
        for field, expected_value in expected_broker_policy.items():
            if broker_policy.get(field) != expected_value:
                errors.append(f"AUTHORITY_OR_BROKER_POLICY_DRIFT:broker_policy.{field}")

    definitions = contract.get("capability_definitions")
    seen_definitions: set[str] = set()
    if not isinstance(definitions, list) or not definitions:
        errors.append("MALFORMED:capability_definitions:must_be_non_empty_list")
    else:
        for index, definition in enumerate(definitions):
            label = f"capability_definitions[{index}]"
            if not _require_object(definition, label, errors):
                continue
            capability_id = definition.get("capability_id")
            if not isinstance(capability_id, str) or not capability_id:
                errors.append(f"MALFORMED:{label}.capability_id")
                continue
            if capability_id in seen_definitions:
                errors.append(f"MALFORMED:DUPLICATE_CAPABILITY_DEFINITION:{capability_id}")
                continue
            seen_definitions.add(capability_id)
            expected_definition = CAPABILITY_DEFINITIONS.get(capability_id)
            if expected_definition is None:
                errors.append(f"MALFORMED:UNKNOWN_CAPABILITY_DEFINITION:{capability_id}")
            elif (definition.get("category"), definition.get("value_kind")) != expected_definition:
                errors.append(f"MALFORMED:CAPABILITY_DEFINITION_DRIFT:{capability_id}")
    if seen_definitions != set(CAPABILITY_DEFINITIONS):
        errors.append("MALFORMED:capability_definitions:taxonomy_set_mismatch")

    profiles = contract.get("provider_model_profiles")
    profile_ids: set[str] = set()
    if not isinstance(profiles, list):
        errors.append("MALFORMED:provider_model_profiles:must_be_list")
    else:
        for index, profile in enumerate(profiles):
            label = f"provider_model_profiles[{index}]"
            if not _require_object(profile, label, errors):
                continue
            profile_id = profile.get("profile_id")
            if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
                errors.append(f"MALFORMED:{label}.profile_id")
            elif profile_id in profile_ids:
                errors.append(f"MALFORMED:DUPLICATE_PROFILE:{profile_id}")
            else:
                profile_ids.add(profile_id)
            for field in ("host_id", "provider_source_id", "provider_id", "model_id"):
                if not isinstance(profile.get(field), str) or not profile[field].strip():
                    errors.append(f"MALFORMED:{label}.{field}")
            freshness_status = _validate_evidence(profile.get("evidence"), f"{label}.evidence", errors)
            _validate_authority(profile.get("authority"), f"{label}.authority", errors)

            capabilities = profile.get("capabilities")
            seen_capabilities: set[str] = set()
            if not isinstance(capabilities, list) or not capabilities:
                errors.append(f"MALFORMED:{label}.capabilities:must_be_non_empty_list")
            else:
                for capability_index, capability in enumerate(capabilities):
                    capability_label = f"{label}.capabilities[{capability_index}]"
                    if not _require_object(capability, capability_label, errors):
                        continue
                    capability_id = capability.get("capability_id")
                    disposition = capability.get("disposition")
                    if not isinstance(capability_id, str) or not capability_id:
                        errors.append(f"MALFORMED:{capability_label}.capability_id")
                    elif capability_id in seen_capabilities:
                        errors.append(f"CONTRADICTORY_CAPABILITY:{profile_id}:{capability_id}")
                    else:
                        seen_capabilities.add(capability_id)
                        if capability_id not in set(CAPABILITY_DEFINITIONS):
                            errors.append(f"UNKNOWN_CAPABILITY:{profile_id}:{capability_id}")
                    if disposition not in DISPOSITIONS:
                        errors.append(f"MALFORMED:{capability_label}.disposition")
                    _require_non_empty_strings(
                        capability.get("evidence_refs"),
                        f"{capability_label}.evidence_refs",
                        errors,
                    )
                    if disposition in {"SUPPORTED_VERIFIED", "SUPPORTED_WITH_LIMITS"} and freshness_status != "CURRENT_AT_OBSERVATION":
                        errors.append(f"CONTRADICTORY_EVIDENCE:{profile_id}:{capability_id}:positive_status_with_stale_evidence")

    policy = contract.get("evidence_policy")
    if _require_object(policy, "evidence_policy", errors):
        expected_policy = {
            "positive_disposition_requires_current_evidence": True,
            "unknown_identity_disposition": "UNKNOWN",
            "static_declaration_disposition": "AVAILABLE_NOT_YET_VERIFIED",
            "provider_switching_authorized": False,
            "learned_routing_promotion_authorized": False,
        }
        for field, expected_value in expected_policy.items():
            if policy.get(field) != expected_value:
                errors.append(f"AUTHORITY_OR_EVIDENCE_POLICY_DRIFT:evidence_policy.{field}")

    return errors


def validate(root: Path) -> list[str]:
    try:
        contract = _load_json(root / CONTRACT_PATH)
    except FileNotFoundError:
        return [f"MALFORMED:missing:{CONTRACT_PATH.as_posix()}"]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"MALFORMED:{CONTRACT_PATH.as_posix()}:{exc}"]
    try:
        schema = _load_json(root / SCHEMA_PATH)
    except FileNotFoundError:
        return [f"MALFORMED:missing:{SCHEMA_PATH.as_posix()}"] + validate_payload(contract)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"MALFORMED:{SCHEMA_PATH.as_posix()}:{exc}"] + validate_payload(contract)
    return validate_payload(contract, schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] UAI provider/model capability contract is schema-valid and authority-bounded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
