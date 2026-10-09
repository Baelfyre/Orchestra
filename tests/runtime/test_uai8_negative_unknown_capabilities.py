from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest
from orchestra_runtime.domain.adaptive.integration_strategy import (
    IntegrationStrategy,
    IntegrationStrategyRequirements,
    TransportCapabilityEvidence,
    resolve_integration_strategy,
    resolve_transport_fallback,
)
from orchestra_runtime.domain.adaptive.provider_capability import (
    HostProviderModelOption,
    ProviderCapabilityAdvisory,
    ProviderCapabilityBrokerDecision,
    ProviderCapabilityEvidence,
    ProviderCapabilityRequirements,
    broker_provider_capabilities,
)
from scripts.compile_portable_projections import (
    CONTRACT_PATH,
    CONTRACT_SCHEMA_PATH,
    validate_contract,
)
from scripts.validate_host_capability_contract import validate_payload as validate_host_payload


ROOT = Path(__file__).resolve().parents[2]
HOST_CONTRACT_PATH = ROOT / "machine" / "hosts" / "capability-contract.v1.json"
HOST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "host-capability-contract.v1.schema.json"
PROJECTION_CONTRACT_PATH = ROOT / CONTRACT_PATH


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _provider_evidence(
    host_id: str,
    provider_id: str,
    model_id: str,
    disposition: str = "SUPPORTED_VERIFIED",
    **overrides: object,
) -> ProviderCapabilityEvidence:
    values: dict[str, object] = {
        "host_id": host_id,
        "provider_id": provider_id,
        "model_id": model_id,
        "capability_dispositions": (("TOOL_CALLING", disposition),),
        "evidence_refs": (f"uai8:{host_id}:{provider_id}:{model_id}",),
    }
    values.update(overrides)
    return ProviderCapabilityEvidence(**values)


def _transport(
    strategy: IntegrationStrategy,
    disposition: str = "SUPPORTED_VERIFIED",
    *,
    provided: tuple[str, ...] = ("SPECIALIST_ROUTING_INSTRUCTION",),
    policy_allowed: bool = True,
    installation_complexity: int = 0,
) -> TransportCapabilityEvidence:
    return TransportCapabilityEvidence(
        strategy_id=strategy,
        disposition=disposition,
        provided_capabilities=provided,
        evidence_refs=(f"uai8:transport:{strategy.value}",),
        policy_allowed=policy_allowed,
        installation_complexity=installation_complexity,
    )


def test_known_host_with_admitted_capability_evidence_is_current() -> None:
    contract = _load(HOST_CONTRACT_PATH)
    schema = _load(HOST_SCHEMA_PATH)
    assert validate_host_payload(contract, schema) == []
    profile = contract["profiles"][0]
    capabilities = {item["capability_id"]: item["disposition"] for item in profile["capabilities"]}
    assert capabilities["orchestra_command_recognition_conductor"] == "SUPPORTED_WITH_LIMITS"
    assert capabilities["orchestra_specialist_recognition_ponytail"] == "SUPPORTED_VERIFIED"
    assert all(value is False for value in contract["authority"].values())


def test_known_host_missing_expected_surface_is_unknown() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("github-copilot", "declared-provider", "declared-model"),),
        (_provider_evidence("github-copilot", "declared-provider", "declared-model", capability_dispositions=(("OTHER", "SUPPORTED_VERIFIED"),)),),
    )
    assert decision.advisories[0].disposition == "UNKNOWN"
    assert decision.advisories[0].reason_codes == ("MISSING_CAPABILITY_EVIDENCE",)


def test_unknown_capability_compatible_host_remains_non_authorizing_advice() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("unknown-host", "provider", "model"),),
        (_provider_evidence("unknown-host", "provider", "model"),),
    )
    advisory = decision.advisories[0]
    assert advisory.disposition == "ELIGIBLE"
    assert advisory.shadow_only is True
    assert advisory.provider_selection_authority is False
    assert advisory.specialist_routing_changed is False
    assert decision.provider_selection_changed is False


def test_host_identity_claims_contradict_observed_copilot_capability() -> None:
    contract = deepcopy(_load(HOST_CONTRACT_PATH))
    schema = _load(HOST_SCHEMA_PATH)
    profile = contract["profiles"][0]
    capability = next(item for item in profile["capabilities"] if item["capability_id"] == "orchestra_command_recognition_conductor")
    capability["disposition"] = "UNSUPPORTED"
    errors = validate_host_payload(contract, schema)
    assert "COPILOT_STATUS_DRIFT:orchestra_command_recognition_conductor:UNSUPPORTED:SUPPORTED_WITH_LIMITS" in errors


def test_policy_disabled_transport_fails_closed() -> None:
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("SPECIALIST_ROUTING_INSTRUCTION",)),
        (_transport(IntegrationStrategy.MCP_TRANSPORT, policy_allowed=False),),
    )
    assert decision.selected_strategy is IntegrationStrategy.UNSUPPORTED_FAIL_CLOSED
    assert decision.fail_closed is True


def test_instruction_only_host_has_a_bounded_fallback_surface() -> None:
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("SPECIALIST_ROUTING_INSTRUCTION",)),
        (_transport(IntegrationStrategy.INSTRUCTION_ONLY_FALLBACK),),
    )
    assert decision.selected_strategy is IntegrationStrategy.INSTRUCTION_ONLY_FALLBACK
    assert decision.transport_selection_only is True
    assert decision.specialist_routing_changed is False


def test_supported_host_with_unsupported_provider_model_is_ineligible() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("github-copilot", "unsupported-provider", "unsupported-model"),),
        (_provider_evidence("github-copilot", "unsupported-provider", "unsupported-model", "UNSUPPORTED"),),
    )
    assert decision.advisories[0].disposition == "INELIGIBLE"


def test_unknown_provider_declared_capability_is_not_verified() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("github-copilot", "unknown-provider", "model"),),
        (_provider_evidence("github-copilot", "unknown-provider", "model", "AVAILABLE_NOT_YET_VERIFIED"),),
    )
    assert decision.advisories[0].disposition == "UNKNOWN"


def test_stale_provider_capability_is_unknown() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("github-copilot", "stale-provider", "model"),),
        (_provider_evidence("github-copilot", "stale-provider", "model", freshness_status="STALE"),),
    )
    assert decision.advisories[0].disposition == "UNKNOWN"
    assert decision.advisories[0].reason_codes == ("STALE_OR_UNKNOWN_EVIDENCE",)


def test_tool_access_does_not_create_execution_or_routing_authority() -> None:
    contract = _load(HOST_CONTRACT_PATH)
    authority = contract["authority"]
    assert authority["capability_grants_execution_authority"] is False
    assert authority["capability_grants_routing_authority"] is False
    advisory = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (HostProviderModelOption("github-copilot", "provider", "model"),),
        (_provider_evidence("github-copilot", "provider", "model"),),
    ).advisories[0]
    assert advisory.provider_selection_authority is False
    assert advisory.workflow_topology_changed is False


def test_provider_advice_cannot_change_specialist_routing() -> None:
    with pytest.raises(ValueError, match="cannot create authority"):
        ProviderCapabilityAdvisory(
            "host",
            "provider",
            "model",
            "ELIGIBLE",
            (),
            (),
            (),
            ("reason",),
            specialist_routing_changed=True,
        )


def test_provider_broker_cannot_switch_provider_automatically() -> None:
    with pytest.raises(ValueError, match="cannot create authority"):
        ProviderCapabilityBrokerDecision(
            (),
            ("reason",),
            automatic_provider_switching=True,
        )


def test_partial_installation_uses_instruction_only_transport_fallback() -> None:
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("SPECIALIST_ROUTING_INSTRUCTION",)),
        (
            _transport(IntegrationStrategy.MCP_TRANSPORT, "AVAILABLE_NOT_YET_VERIFIED"),
            _transport(IntegrationStrategy.INSTRUCTION_ONLY_FALLBACK, installation_complexity=2),
        ),
    )
    assert decision.selected_strategy is IntegrationStrategy.INSTRUCTION_ONLY_FALLBACK
    assert any(strategy == "MCP_TRANSPORT" for strategy, _ in decision.rejected_strategies)


def test_stale_generated_projection_fails_closed(tmp_path: Path) -> None:
    contract = _load(PROJECTION_CONTRACT_PATH)
    paths = {CONTRACT_PATH, CONTRACT_SCHEMA_PATH}
    paths.update(source["path"] for source in contract["canonical_sources"])
    paths.update(projection["output_path"] for projection in contract["projections"])
    for relative_path in paths:
        source_path = ROOT / relative_path
        target_path = tmp_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    target = tmp_path / contract["projections"][0]["output_path"]
    content = target.read_text(encoding="utf-8")
    target.write_text(content.replace("CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER", "CONDUCTOR_ROUTER_MARKER_REMOVED", 1), encoding="utf-8")
    errors, _ = validate_contract(tmp_path)
    assert "PARITY_MISSING:github-copilot-repository-instructions-template:conductor-sole-router" in errors


def test_transport_fallback_preserves_governance_and_never_selects_a_provider() -> None:
    decision = resolve_transport_fallback(
        IntegrationStrategyRequirements(("SPECIALIST_ROUTING_INSTRUCTION",)),
        (
            _transport(IntegrationStrategy.MCP_TRANSPORT, installation_complexity=0),
            _transport(IntegrationStrategy.INSTRUCTION_ONLY_FALLBACK, installation_complexity=1),
        ),
    )
    assert decision.fail_closed is False
    assert decision.transport_fallback_only is True
    assert decision.automatic_provider_fallback is False
    assert decision.primary_decision.provider_selection_changed is False
    assert decision.primary_decision.specialist_routing_changed is False
    assert decision.primary_decision.workflow_topology_changed is False
    assert "FALLBACK_NON_AUTOMATIC" in decision.reason_codes
    assert "PROVIDER_FALLBACK_PROHIBITED" in decision.reason_codes
