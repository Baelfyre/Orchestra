from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive.integration_strategy import (
    IntegrationStrategy,
    IntegrationStrategyRequirements,
    TransportCapabilityEvidence,
    resolve_integration_strategy,
    resolve_transport_fallback,
)


ROOT = Path(__file__).resolve().parents[2]


def option(strategy: str, **overrides: object) -> TransportCapabilityEvidence:
    values: dict[str, object] = {
        "strategy_id": strategy,
        "disposition": "SUPPORTED_VERIFIED",
        "provided_capabilities": ("instructions", "tools"),
        "evidence_refs": (f"fixture:{strategy}",),
        "portability_score": 5,
        "context_cost": 5,
        "installation_complexity": 5,
        "evidence_quality": 5,
    }
    values.update(overrides)
    return TransportCapabilityEvidence(**values)


def test_policy_schema_and_minimality_are_deterministic() -> None:
    policy_path = ROOT / "machine" / "hosts" / "integration-strategy-policy.v1.json"
    schema_path = ROOT / "machine" / "schemas" / "integration-strategy-policy.v1.schema.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(policy)
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("instructions",)),
        (
            option("PLUGIN_OR_EXTENSION", installation_complexity=1),
            option("REPOSITORY_INSTRUCTIONS", installation_complexity=0, context_cost=1),
        ),
    )
    assert decision.selected_strategy is IntegrationStrategy.REPOSITORY_INSTRUCTIONS
    assert decision.fail_closed is False
    assert decision.transport_selection_only is True
    assert decision.specialist_routing_changed is False
    assert decision.workflow_topology_changed is False
    assert decision.provider_selection_changed is False


def test_unverified_or_policy_blocked_options_fail_closed() -> None:
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("tools",)),
        (
            option("MCP_TRANSPORT", disposition="AVAILABLE_NOT_YET_VERIFIED"),
            option("CUSTOM_AGENT", policy_allowed=False),
        ),
    )
    assert decision.selected_strategy is IntegrationStrategy.UNSUPPORTED_FAIL_CLOSED
    assert decision.fail_closed is True
    assert {item[0] for item in decision.rejected_strategies} == {"MCP_TRANSPORT", "CUSTOM_AGENT"}


def test_authority_and_capability_gaps_are_rejected() -> None:
    decision = resolve_integration_strategy(
        IntegrationStrategyRequirements(("terminal",)),
        (
            option("AGENT_SKILLS", provided_capabilities=("instructions",)),
            option("CLI_ADAPTER", authority_preserved=False, provided_capabilities=("terminal",)),
        ),
    )
    assert decision.fail_closed is True
    rejected = dict(decision.rejected_strategies)
    assert "MISSING_CAPABILITIES:terminal" in rejected["AGENT_SKILLS"]
    assert "AUTHORITY_NOT_PRESERVED" in rejected["CLI_ADAPTER"]


def test_limits_are_explicit_and_duplicate_options_fail() -> None:
    limited = option("WORKSPACE_INSTRUCTIONS", disposition="SUPPORTED_WITH_LIMITS", limitations=("host policy",))
    decision = resolve_integration_strategy(IntegrationStrategyRequirements(), (limited,))
    assert decision.selected_strategy is IntegrationStrategy.WORKSPACE_INSTRUCTIONS
    assert decision.reason_codes == ("MINIMAL_ELIGIBLE_TRANSPORT", "SELECTED_WITH_LIMITS")
    try:
        resolve_integration_strategy(IntegrationStrategyRequirements(), (limited, limited))
    except ValueError as exc:
        assert "one record per strategy" in str(exc)
    else:
        raise AssertionError("duplicate strategy options must fail closed")


def test_transport_fallback_is_deterministic_and_non_authorizing() -> None:
    decision = resolve_transport_fallback(
        IntegrationStrategyRequirements(("instructions",)),
        (
            option("REPOSITORY_INSTRUCTIONS", installation_complexity=0),
            option("WORKSPACE_INSTRUCTIONS", installation_complexity=1),
            option("MCP_TRANSPORT", installation_complexity=2),
        ),
    )
    assert decision.primary_decision.selected_strategy is IntegrationStrategy.REPOSITORY_INSTRUCTIONS
    assert decision.fallback_strategies == (
        IntegrationStrategy.WORKSPACE_INSTRUCTIONS,
        IntegrationStrategy.MCP_TRANSPORT,
    )
    assert decision.reason_codes == (
        "DETERMINISTIC_TRANSPORT_FALLBACK_CHAIN",
        "FALLBACK_NON_AUTOMATIC",
        "PROVIDER_FALLBACK_PROHIBITED",
    )
    assert decision.transport_fallback_only is True
    assert decision.automatic_provider_fallback is False
    assert decision.primary_decision.specialist_routing_changed is False
    assert decision.primary_decision.workflow_topology_changed is False
    assert decision.primary_decision.provider_selection_changed is False


def test_transport_fallback_fails_closed_without_supported_evidence() -> None:
    decision = resolve_transport_fallback(
        IntegrationStrategyRequirements(("tools",)),
        (option("MCP_TRANSPORT", disposition="UNKNOWN"),),
    )
    assert decision.fail_closed is True
    assert decision.fallback_strategies == ()
    assert decision.reason_codes == (
        "NO_EVIDENCE_SUPPORTED_TRANSPORT",
        "TRANSPORT_FALLBACK_FAIL_CLOSED",
    )
