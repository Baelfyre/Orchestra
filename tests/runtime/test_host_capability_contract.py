from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.validate_host_capability_contract import validate_payload


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "hosts" / "capability-contract.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "host-capability-contract.v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical() -> tuple[dict[str, object], dict[str, object]]:
    return deepcopy(_load(CONTRACT_PATH)), _load(SCHEMA_PATH)


def _copilot(contract: dict[str, object]) -> dict[str, object]:
    profiles = contract["profiles"]
    assert isinstance(profiles, list)
    profile = profiles[0]
    assert isinstance(profile, dict)
    return profile


def test_canonical_contract_is_schema_valid_and_semantically_bounded() -> None:
    contract, schema = _canonical()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    assert validate_payload(contract, schema) == []

    profile = _copilot(contract)
    capabilities = {item["capability_id"]: item for item in profile["capabilities"]}
    assert capabilities["orchestra_command_recognition_conductor"]["disposition"] == "SUPPORTED_WITH_LIMITS"
    assert capabilities["orchestra_specialist_recognition_ponytail"]["disposition"] == "SUPPORTED_VERIFIED"
    assert all(item["host_neutral"] is True for item in contract["transport_strategies"])


def test_malformed_contract_fails_closed() -> None:
    contract, schema = _canonical()
    del contract["profiles"]
    errors = validate_payload(contract, schema)
    assert any(error.startswith("MALFORMED:missing:profiles") for error in errors)


def test_stale_evidence_fails_closed() -> None:
    contract, schema = _canonical()
    profile = _copilot(contract)
    evidence = profile["evidence"]
    assert isinstance(evidence, dict)
    freshness = evidence["freshness"]
    assert isinstance(freshness, dict)
    freshness["status"] = "STALE"
    errors = validate_payload(contract, schema)
    assert any(error.startswith("FRESHNESS_INVALID:") for error in errors)
    assert any(error.startswith("CONTRADICTORY_EVIDENCE:") for error in errors)


def test_contradictory_capability_and_authority_expansion_fail_closed() -> None:
    contract, schema = _canonical()
    profile = _copilot(contract)
    capabilities = profile["capabilities"]
    assert isinstance(capabilities, list)
    contradictory = deepcopy(capabilities[0])
    contradictory["disposition"] = "UNKNOWN"
    capabilities.append(contradictory)
    authority = contract["authority"]
    assert isinstance(authority, dict)
    authority["capability_grants_routing_authority"] = True
    errors = validate_payload(contract, schema)
    assert any(error.startswith("CONTRADICTORY_CAPABILITY:") for error in errors)
    assert "AUTHORITY_EXPANSION:authority.capability_grants_routing_authority" in errors


def test_unknown_transport_strategy_fails_closed() -> None:
    contract, schema = _canonical()
    profile = _copilot(contract)
    compatibility = profile["transport_compatibility"]
    assert isinstance(compatibility, list)
    compatibility[0]["strategy_id"] = "UNDECLARED_TRANSPORT"
    errors = validate_payload(contract, schema)
    assert "TRANSPORT_STRATEGY_UNKNOWN:github-copilot:UNDECLARED_TRANSPORT" in errors
