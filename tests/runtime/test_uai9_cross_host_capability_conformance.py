from __future__ import annotations

import json
from pathlib import Path

from scripts.compile_portable_projections import compile_projections
from scripts.validate_host_capability_contract import validate_payload as validate_host_payload
from scripts.validate_provider_model_capability_contract import validate_payload as validate_provider_payload


ROOT = Path(__file__).resolve().parents[2]
HOST_CONTRACT_PATH = ROOT / "machine" / "hosts" / "capability-contract.v1.json"
HOST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "host-capability-contract.v1.schema.json"
PROVIDER_CONTRACT_PATH = ROOT / "machine" / "providers" / "provider-model-capability-contract.v1.json"
PROVIDER_SCHEMA_PATH = ROOT / "machine" / "schemas" / "provider-model-capability-contract.v1.schema.json"
DECLARED_HOSTS = ("antigravity", "codex", "github-copilot")


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cross_host_matrix_does_not_fabricate_unobserved_host_evidence() -> None:
    contract = _load(HOST_CONTRACT_PATH)
    schema = _load(HOST_SCHEMA_PATH)
    assert validate_host_payload(contract, schema) == []
    profiles = {profile["host_id"]: profile for profile in contract["profiles"]}

    assert set(profiles) == {"github-copilot"}
    assert "antigravity" not in profiles
    assert "codex" not in profiles

    for host_id in DECLARED_HOSTS:
        if host_id in profiles:
            assert profiles[host_id]["evidence"]["freshness"]["status"] == "CURRENT_AT_OBSERVATION"
        else:
            assert host_id in {"antigravity", "codex"}


def test_copilot_conformance_covers_discovery_capability_ownership_and_permissions() -> None:
    contract = _load(HOST_CONTRACT_PATH)
    profile = contract["profiles"][0]
    capabilities = {item["capability_id"]: item for item in profile["capabilities"]}
    dimensions = {item["category"] for item in profile["capabilities"]}

    assert dimensions == set(contract["capability_dimensions"])
    assert capabilities["orchestra_command_recognition_conductor"]["disposition"] == "SUPPORTED_WITH_LIMITS"
    assert capabilities["orchestra_specialist_recognition_ponytail"]["disposition"] == "SUPPORTED_VERIFIED"
    assert capabilities["approval_and_permission_controls"]["disposition"] == "AVAILABLE_NOT_YET_VERIFIED"
    assert capabilities["organization_or_account_policy_restrictions"]["disposition"] == "AVAILABLE_NOT_YET_VERIFIED"
    assert all(value is False for value in profile["authority"].values())

    transports = {item["strategy_id"]: item for item in profile["transport_compatibility"]}
    assert transports["INSTRUCTION_ONLY_FALLBACK"]["disposition"] == "AVAILABLE_NOT_YET_VERIFIED"
    assert transports["UNSUPPORTED_FAIL_CLOSED"]["disposition"] == "SUPPORTED_VERIFIED"
    assert all(item["host_neutral"] is True for item in contract["transport_strategies"])


def test_cross_host_validation_provider_boundary_and_projection_parity_remain_canonical() -> None:
    provider_contract = _load(PROVIDER_CONTRACT_PATH)
    assert validate_provider_payload(provider_contract, _load(PROVIDER_SCHEMA_PATH)) == []
    assert provider_contract["provider_model_profiles"] == []
    assert provider_contract["broker_policy"]["provider_selection_changed"] is False
    assert provider_contract["broker_policy"]["automatic_provider_switching"] is False
    assert provider_contract["broker_policy"]["automatic_provider_fallback"] is False

    errors, index = compile_projections(ROOT)
    assert errors == []
    assert index is not None
    assert index["parity_status"] == "PASS"
    assert all(projection["parity"] == "PASS" for projection in index["projections"])
