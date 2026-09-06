from __future__ import annotations

import pytest

from orchestra_runtime.domain.adaptive.provider_capability import (
    HostProviderModelOption,
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
        from orchestra_runtime.domain.adaptive.provider_capability import ProviderCapabilityAdvisory

        ProviderCapabilityAdvisory("host", "provider", "model", "UNKNOWN", (), (), (), ("reason",), provider_selection_authority=True)
