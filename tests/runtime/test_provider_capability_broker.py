from __future__ import annotations

import pytest

from orchestra_runtime.domain.adaptive.provider_capability import (
    HostProviderModelOption,
    ProviderCapabilityAdvisory,
    ProviderCapabilityBrokerDecision,
    ProviderCapabilityEvidence,
    ProviderCapabilityRequirements,
    broker_provider_capabilities,
)


def evidence(provider: str, model: str, **overrides: object) -> ProviderCapabilityEvidence:
    values: dict[str, object] = {
        "host_id": "fixture-host",
        "provider_id": provider,
        "model_id": model,
        "capability_dispositions": (("TOOL_CALLING", "SUPPORTED_VERIFIED"), ("VISION_MULTIMODAL_INPUT", "SUPPORTED_WITH_LIMITS")),
        "evidence_refs": (f"fixture:{provider}:{model}",),
    }
    values.update(overrides)
    return ProviderCapabilityEvidence(**values)


def option(provider: str, model: str, **overrides: object) -> HostProviderModelOption:
    values: dict[str, object] = {"host_id": "fixture-host", "provider_id": provider, "model_id": model}
    values.update(overrides)
    return HostProviderModelOption(**values)


def test_broker_returns_all_classifications_without_selection() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING", "VISION_MULTIMODAL_INPUT")),
        (option("alpha", "full"), option("beta", "missing"), option("gamma", "unknown"), option("delta", "blocked", policy_allowed=False)),
        (
            evidence("alpha", "full"),
            evidence("beta", "missing", capability_dispositions=(("TOOL_CALLING", "UNSUPPORTED"), ("VISION_MULTIMODAL_INPUT", "SUPPORTED_VERIFIED"))),
            evidence("gamma", "unknown", freshness_status="UNKNOWN"),
        ),
    )
    assert [(item.provider_id, item.disposition) for item in decision.advisories] == [
        ("alpha", "ELIGIBLE_WITH_LIMITS"),
        ("beta", "INELIGIBLE"),
        ("delta", "POLICY_BLOCKED"),
        ("gamma", "UNKNOWN"),
    ]
    assert decision.shadow_only is True
    assert decision.provider_selection_changed is False
    assert decision.automatic_provider_switching is False
    assert decision.automatic_provider_fallback is False
    assert decision.learned_routing_promotion is False
    assert decision.specialist_routing_changed is False
    assert decision.workflow_topology_changed is False


def test_missing_profile_is_unknown_and_stale_evidence_cannot_be_eligible() -> None:
    decision = broker_provider_capabilities(
        ProviderCapabilityRequirements(("TOOL_CALLING",)),
        (option("missing", "model"), option("stale", "model")),
        (evidence("stale", "model", freshness_status="STALE"),),
    )
    assert [item.disposition for item in decision.advisories] == ["UNKNOWN", "UNKNOWN"]
    assert all(item.evidence_refs == () for item in decision.advisories if item.provider_id == "missing")


def test_duplicate_identities_and_authority_expansion_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique host/provider/model"):
        broker_provider_capabilities(ProviderCapabilityRequirements(), (option("alpha", "model"), option("alpha", "model")), ())
    with pytest.raises(ValueError, match="cannot create authority"):
        ProviderCapabilityAdvisory("host", "provider", "model", "UNKNOWN", (), (), (), ("reason",), provider_selection_authority=True)


def test_broker_classifies_current_evidence_and_policy_states() -> None:
    requirements = ProviderCapabilityRequirements(("TOOL_CALLING",))
    decision = broker_provider_capabilities(
        requirements,
        (
            option("eligible", "model"),
            option("limited", "model"),
            option("blocked", "model"),
            option("missing", "model"),
            option("unknown", "model"),
            option("unsupported", "model"),
            option("profile-blocked", "model"),
        ),
        (
            evidence("eligible", "model", capability_dispositions=(("TOOL_CALLING", "SUPPORTED_VERIFIED"),)),
            evidence("limited", "model", capability_dispositions=(("TOOL_CALLING", "SUPPORTED_WITH_LIMITS"),)),
            evidence("blocked", "model", capability_dispositions=(("TOOL_CALLING", "BLOCKED_BY_POLICY"),)),
            evidence("missing", "model", capability_dispositions=(("OTHER", "SUPPORTED_VERIFIED"),)),
            evidence("unknown", "model", capability_dispositions=(("TOOL_CALLING", "UNKNOWN"),)),
            evidence("unsupported", "model", capability_dispositions=(("TOOL_CALLING", "VERIFIED_UNSUPPORTED_LOCALLY"),)),
            evidence("profile-blocked", "model", policy_allowed=False),
        ),
    )
    assert [(item.provider_id, item.disposition) for item in decision.advisories] == [
        ("blocked", "POLICY_BLOCKED"),
        ("eligible", "ELIGIBLE"),
        ("limited", "ELIGIBLE_WITH_LIMITS"),
        ("missing", "UNKNOWN"),
        ("profile-blocked", "POLICY_BLOCKED"),
        ("unknown", "UNKNOWN"),
        ("unsupported", "INELIGIBLE"),
    ]


def test_contract_objects_reject_invalid_inputs_and_authority() -> None:
    with pytest.raises(ValueError, match="unique non-empty"):
        ProviderCapabilityRequirements(("TOOL_CALLING", "TOOL_CALLING"))
    with pytest.raises(ValueError, match="unique non-empty"):
        ProviderCapabilityRequirements(("",))
    with pytest.raises(ValueError, match="host_id"):
        HostProviderModelOption("", "provider", "model")
    with pytest.raises(ValueError, match="boolean"):
        HostProviderModelOption("host", "provider", "model", policy_allowed=1)
    with pytest.raises(ValueError, match="host_id"):
        evidence("provider", "model", host_id="")
    with pytest.raises(ValueError, match="must not be empty"):
        evidence("provider", "model", capability_dispositions=())
    with pytest.raises(ValueError, match="unique non-empty capability IDs"):
        evidence("provider", "model", capability_dispositions=(("", "SUPPORTED_VERIFIED"),))
    with pytest.raises(ValueError, match="unsupported"):
        evidence("provider", "model", capability_dispositions=(("TOOL_CALLING", "NOT_A_DISPOSITION"),))
    with pytest.raises(ValueError, match="freshness"):
        evidence("provider", "model", freshness_status="NOT_CURRENT")
    with pytest.raises(ValueError, match="boolean"):
        evidence("provider", "model", policy_allowed=1)
    with pytest.raises(ValueError, match="unsupported"):
        ProviderCapabilityAdvisory("host", "provider", "model", "NOT_A_DISPOSITION", (), (), (), ("reason",))
    with pytest.raises(ValueError, match="cannot create authority"):
        ProviderCapabilityBrokerDecision((), ("reason",), provider_selection_changed=True)
    with pytest.raises(TypeError, match="ProviderCapabilityAdvisory"):
        ProviderCapabilityBrokerDecision((object(),), ("reason",))
    with pytest.raises(TypeError, match="requirements"):
        broker_provider_capabilities(object(), (), ())
    with pytest.raises(TypeError, match="host_options"):
        broker_provider_capabilities(ProviderCapabilityRequirements(), (object(),), ())
    with pytest.raises(TypeError, match="evidence_profiles"):
        broker_provider_capabilities(ProviderCapabilityRequirements(), (), (object(),))
    with pytest.raises(ValueError, match="unique host/provider/model"):
        broker_provider_capabilities(
            ProviderCapabilityRequirements(), (), (evidence("provider", "model"), evidence("provider", "model"))
        )
