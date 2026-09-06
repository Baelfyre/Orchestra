from __future__ import annotations

import json
from pathlib import Path

from scripts.compile_portable_projections import compile_projections
from scripts.validate_host_capability_contract import validate_payload as validate_host_payload
from scripts.validate_provider_model_capability_contract import validate_payload as validate_provider_payload


ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_uai_maturity_is_layered_and_authority_bounded() -> None:
    host = _load("machine/hosts/capability-contract.v1.json")
    provider = _load("machine/providers/provider-model-capability-contract.v1.json")
    integration = _load("machine/hosts/integration-strategy-policy.v1.json")
    projection = _load("machine/projections/portable-projection-contract.v1.json")

    assert validate_host_payload(host, _load("machine/schemas/host-capability-contract.v1.schema.json")) == []
    assert validate_provider_payload(provider, _load("machine/schemas/provider-model-capability-contract.v1.schema.json")) == []
    assert provider["provider_model_profiles"] == []
    assert integration["authority"] == {
        "transport_selection_only": True,
        "specialist_routing_changed": False,
        "workflow_topology_changed": False,
        "provider_selection_changed": False,
        "automatic_fallback": False,
        "credentials_mutated": False,
    }
    assert projection["authority"]["canonical_source_remains_authoritative"] is True
    assert projection["authority"]["generated_projection_is_derived_only"] is True
    assert all(value is False for key, value in projection["authority"].items() if key != "canonical_source_remains_authoritative" and key != "generated_projection_is_derived_only")


def test_uai_closeout_retains_observed_host_limits_and_retest_boundary() -> None:
    readme = _load("README.json")
    uai = readme["capabilities"]["universal_adaptive_integration_uai"]

    assert uai["status"] == "UAI_10_MATURITY_AND_CLOSEOUT_COMPLETE"
    assert uai["probed_hosts"] == ["github-copilot"]
    assert uai["copilot_conductor_status"] == "SUPPORTED_WITH_LIMITS"
    assert uai["copilot_ponytail_status"] == "SUPPORTED_VERIFIED"
    assert uai["authority_expansion"] is False
    assert uai["automatic_provider_routing"] is False
    assert uai["automatic_provider_fallback"] is False
    assert uai["learned_routing_promotion"] is False


def test_uai_closeout_projection_parity_is_current_without_release_claim() -> None:
    errors, index = compile_projections(ROOT)
    assert errors == []
    assert index is not None
    assert index["parity_status"] == "PASS"
    assert all(item["parity"] == "PASS" for item in index["projections"])
    assert _load("README.json")["release_state"]["current_public_release"] == "v1.9.0"
