from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.validate_provider_model_capability_contract import validate_payload


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "providers" / "provider-model-capability-contract.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "provider-model-capability-contract.v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical() -> tuple[dict[str, object], dict[str, object]]:
    return deepcopy(_load(CONTRACT_PATH)), _load(SCHEMA_PATH)


def _profile(contract: dict[str, object]) -> dict[str, object]:
    profiles = contract["provider_model_profiles"]
    assert isinstance(profiles, list)
    profile = {
        "profile_id": "provider-model-capability." + "1" * 24,
        "host_id": "fixture-host",
        "provider_source_id": "fixture-source",
        "provider_id": "fixture-provider",
        "model_id": "fixture-model",
        "evidence": {
            "source_repository": "fixture/repository",
            "source_path": "fixture/evidence.json",
            "source_commit": "1" * 40,
            "source_type": "CURRENT_MAINTAINER_OBSERVATION",
            "observation_id": "fixture-observation",
            "observed_at": "2026-09-06T00:00:00Z",
            "freshness": {
                "status": "CURRENT_AT_OBSERVATION",
                "max_age_hours": 24,
                "invalidation_triggers": ["HOST_POLICY_UPDATE"],
            },
        },
        "authority": deepcopy(contract["authority"]),
        "capabilities": [
            {
                "capability_id": "TOOL_CALLING",
                "disposition": "SUPPORTED_VERIFIED",
                "evidence_refs": ["fixture-observation#tool-calling"],
                "observed_value": True,
            }
        ],
    }
    profiles.append(profile)
    return profile


def test_canonical_contract_is_schema_valid_and_provider_model_neutral() -> None:
    contract, schema = _canonical()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    assert validate_payload(contract, schema) == []
    assert contract["provider_model_profiles"] == []
    authority = contract["authority"]
    assert isinstance(authority, dict)
    assert all(value is False for value in authority.values())


def test_profile_positive_capability_requires_current_evidence() -> None:
    contract, schema = _canonical()
    profile = _profile(contract)
    evidence = profile["evidence"]
    assert isinstance(evidence, dict)
    freshness = evidence["freshness"]
    assert isinstance(freshness, dict)
    freshness["status"] = "STALE"
    errors = validate_payload(contract, schema)
    assert any(error.startswith("CONTRADICTORY_EVIDENCE:") for error in errors)


def test_duplicate_capability_and_authority_expansion_fail_closed() -> None:
    contract, schema = _canonical()
    profile = _profile(contract)
    capabilities = profile["capabilities"]
    assert isinstance(capabilities, list)
    capabilities.append(deepcopy(capabilities[0]))
    authority = profile["authority"]
    assert isinstance(authority, dict)
    authority["capability_grants_provider_selection_authority"] = True
    errors = validate_payload(contract, schema)
    assert any(error.startswith("CONTRADICTORY_CAPABILITY:") for error in errors)
    assert "AUTHORITY_EXPANSION:provider_model_profiles[0].authority.capability_grants_provider_selection_authority" in errors


def test_contract_policy_cannot_authorize_provider_switching_or_learning() -> None:
    contract, schema = _canonical()
    policy = contract["evidence_policy"]
    assert isinstance(policy, dict)
    policy["provider_switching_authorized"] = True
    policy["learned_routing_promotion_authorized"] = True
    errors = validate_payload(contract, schema)
    assert any(error.startswith("SCHEMA_VALIDATION:evidence_policy") for error in errors)
    assert "AUTHORITY_OR_EVIDENCE_POLICY_DRIFT:evidence_policy.provider_switching_authorized" in errors
    assert "AUTHORITY_OR_EVIDENCE_POLICY_DRIFT:evidence_policy.learned_routing_promotion_authorized" in errors
