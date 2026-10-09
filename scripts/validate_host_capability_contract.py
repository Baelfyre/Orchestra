#!/usr/bin/env python3
"""Validate the canonical UAI host capability contract without granting authority."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("machine/hosts/capability-contract.v1.json")
SCHEMA_PATH = Path("machine/schemas/host-capability-contract.v1.schema.json")
DISPOSITIONS = {
    "SUPPORTED_VERIFIED",
    "SUPPORTED_WITH_LIMITS",
    "AVAILABLE_NOT_YET_VERIFIED",
    "UNKNOWN",
    "BLOCKED_BY_POLICY",
    "VERIFIED_UNSUPPORTED_LOCALLY",
    "UNSUPPORTED",
}
REQUIRED_DIMENSIONS = {
    "instruction_surface",
    "agent_skills",
    "custom_agents",
    "tool_transport",
    "execution_environment",
    "control_surface",
    "model_selection",
    "policy_enforcement",
}
AUTHORITY_FIELDS = {
    "capability_grants_execution_authority",
    "capability_grants_routing_authority",
    "capability_grants_specialist_selection_authority",
    "capability_grants_workflow_topology_authority",
    "capability_grants_provider_selection_authority",
    "automatic_provider_routing",
    "automatic_provider_fallback",
    "execution_authorized",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


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
    extra = set(value) - AUTHORITY_FIELDS
    for field in sorted(extra):
        errors.append(f"AUTHORITY_EXPANSION:{label}.{field}")


def _validate_evidence(value: Any, label: str, errors: list[str]) -> None:
    if not _require_object(value, label, errors):
        return
    for field in (
        "source_repository",
        "source_path",
        "source_type",
        "observation_id",
        "observed_at",
        "environment",
        "probe",
        "subject_repository",
    ):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"MALFORMED:{label}.{field}")
    for field in ("source_commit", "subject_commit"):
        if not isinstance(value.get(field), str) or not SHA_PATTERN.fullmatch(value[field]):
            errors.append(f"MALFORMED:{label}.{field}:sha")
    freshness = value.get("freshness")
    if not _require_object(freshness, f"{label}.freshness", errors):
        return
    if freshness.get("status") != "CURRENT_AT_OBSERVATION":
        errors.append(f"FRESHNESS_INVALID:{label}.freshness.status")
    if not isinstance(freshness.get("max_age_hours"), int) or freshness["max_age_hours"] < 1:
        errors.append(f"MALFORMED:{label}.freshness.max_age_hours")
    _require_non_empty_strings(freshness.get("invalidation_triggers"), f"{label}.freshness.invalidation_triggers", errors)


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
        "dispositions",
        "capability_dimensions",
        "transport_strategies",
        "profiles",
    }
    for field in sorted(required - set(contract)):
        errors.append(f"MALFORMED:missing:{field}")
    expected_values = {
        "$schema": "./machine/schemas/host-capability-contract.v1.schema.json",
        "schema_version": "orchestra.host-capability-contract.v1",
        "contract_id": "orchestra-host-capability",
        "contract_revision": 1,
        "contract_role": "canonical_uai_host_capability_contract",
    }
    for field, expected in expected_values.items():
        if field in contract and contract[field] != expected:
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

    dispositions = contract.get("dispositions")
    if (
        not isinstance(dispositions, list)
        or any(not isinstance(item, str) for item in dispositions)
        or set(dispositions) != DISPOSITIONS
        or len(dispositions) != len(DISPOSITIONS)
    ):
        errors.append("MALFORMED:dispositions:must_list_all_supported_dispositions_once")

    dimensions = contract.get("capability_dimensions")
    if _require_object(dimensions, "capability_dimensions", errors):
        if set(dimensions) != REQUIRED_DIMENSIONS:
            errors.append("MALFORMED:capability_dimensions:taxonomy_set_mismatch")
        for dimension in sorted(REQUIRED_DIMENSIONS):
            _require_non_empty_strings(dimensions.get(dimension), f"capability_dimensions.{dimension}", errors)

    strategies = contract.get("transport_strategies")
    strategy_ids: set[str] = set()
    if not isinstance(strategies, list) or not strategies:
        errors.append("MALFORMED:transport_strategies:must_be_non_empty_list")
    else:
        for index, strategy in enumerate(strategies):
            label = f"transport_strategies[{index}]"
            if not _require_object(strategy, label, errors):
                continue
            strategy_id = strategy.get("strategy_id")
            if not isinstance(strategy_id, str) or not strategy_id:
                errors.append(f"MALFORMED:{label}.strategy_id")
            elif strategy_id in strategy_ids:
                errors.append(f"MALFORMED:DUPLICATE_TRANSPORT_STRATEGY:{strategy_id}")
            else:
                strategy_ids.add(strategy_id)
            if strategy.get("host_neutral") is not True:
                errors.append(f"AUTHORITY_EXPANSION:{label}.host_neutral")

    profiles = contract.get("profiles")
    profile_ids: set[str] = set()
    if not isinstance(profiles, list) or not profiles:
        errors.append("MALFORMED:profiles:must_be_non_empty_list")
    else:
        for index, profile in enumerate(profiles):
            label = f"profiles[{index}]"
            if not _require_object(profile, label, errors):
                continue
            host_id = profile.get("host_id")
            if not isinstance(host_id, str) or not host_id:
                errors.append(f"MALFORMED:{label}.host_id")
            elif host_id in profile_ids:
                errors.append(f"MALFORMED:DUPLICATE_PROFILE:{host_id}")
            else:
                profile_ids.add(host_id)
            _validate_evidence(profile.get("evidence"), f"{label}.evidence", errors)
            _validate_authority(profile.get("authority"), f"{label}.authority", errors)

            capabilities = profile.get("capabilities")
            seen_capabilities: dict[str, str] = {}
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
                        errors.append(
                            f"CONTRADICTORY_CAPABILITY:{host_id}:{capability_id}:"
                            f"{seen_capabilities[capability_id]}:{disposition}"
                        )
                    else:
                        seen_capabilities[capability_id] = str(disposition)
                    if disposition not in DISPOSITIONS:
                        errors.append(f"MALFORMED:{capability_label}.disposition")
                    _require_non_empty_strings(capability.get("evidence_refs"), f"{capability_label}.evidence_refs", errors)

            compatibility = profile.get("transport_compatibility")
            seen_strategies: set[str] = set()
            if not isinstance(compatibility, list) or not compatibility:
                errors.append(f"MALFORMED:{label}.transport_compatibility:must_be_non_empty_list")
            else:
                for compatibility_index, item in enumerate(compatibility):
                    item_label = f"{label}.transport_compatibility[{compatibility_index}]"
                    if not _require_object(item, item_label, errors):
                        continue
                    strategy_id = item.get("strategy_id")
                    if not isinstance(strategy_id, str) or not strategy_id:
                        errors.append(f"MALFORMED:{item_label}.strategy_id")
                    else:
                        if strategy_id in seen_strategies:
                            errors.append(f"CONTRADICTORY_TRANSPORT:{host_id}:{strategy_id}")
                        seen_strategies.add(strategy_id)
                        if strategy_id not in strategy_ids:
                            errors.append(f"TRANSPORT_STRATEGY_UNKNOWN:{host_id}:{strategy_id}")
                    if item.get("disposition") not in DISPOSITIONS:
                        errors.append(f"MALFORMED:{item_label}.disposition")
                    _require_non_empty_strings(item.get("evidence_refs"), f"{item_label}.evidence_refs", errors)

            evidence = profile.get("evidence")
            freshness_status = evidence.get("freshness", {}).get("status") if isinstance(evidence, dict) else None
            if freshness_status != "CURRENT_AT_OBSERVATION":
                for capability_id, disposition in seen_capabilities.items():
                    if disposition in {"SUPPORTED_VERIFIED", "SUPPORTED_WITH_LIMITS"}:
                        errors.append(f"CONTRADICTORY_EVIDENCE:{host_id}:{capability_id}:positive_status_with_stale_evidence")

            if host_id == "github-copilot":
                expected = {
                    "orchestra_command_recognition_conductor": "SUPPORTED_WITH_LIMITS",
                    "orchestra_specialist_recognition_ponytail": "SUPPORTED_VERIFIED",
                }
                for capability_id, expected_disposition in expected.items():
                    actual = seen_capabilities.get(capability_id)
                    if actual != expected_disposition:
                        errors.append(f"COPILOT_STATUS_DRIFT:{capability_id}:{actual}:{expected_disposition}")

    return errors


def validate(root: Path) -> list[str]:
    contract_path = root / CONTRACT_PATH
    schema_path = root / SCHEMA_PATH
    errors: list[str] = []
    try:
        contract = _load_json(contract_path)
    except FileNotFoundError:
        return [f"MALFORMED:missing:{CONTRACT_PATH.as_posix()}"]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"MALFORMED:{CONTRACT_PATH.as_posix()}:{exc}"]
    try:
        schema = _load_json(schema_path)
    except FileNotFoundError:
        errors.append(f"MALFORMED:missing:{SCHEMA_PATH.as_posix()}")
        schema = None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"MALFORMED:{SCHEMA_PATH.as_posix()}:{exc}")
        schema = None
    errors.extend(validate_payload(contract, schema))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] UAI host capability contract is schema-valid, fresh, and authority-bounded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
