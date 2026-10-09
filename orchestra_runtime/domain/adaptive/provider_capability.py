"""Shadow-only provider/model capability advice."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PROVIDER_CAPABILITY_BROKER_POLICY_VERSION = "orchestra.provider-capability-broker.v1"
BROKER_DISPOSITIONS = frozenset({"ELIGIBLE", "ELIGIBLE_WITH_LIMITS", "INELIGIBLE", "UNKNOWN", "POLICY_BLOCKED"})
CAPABILITY_DISPOSITIONS = frozenset(
    {
        "SUPPORTED_VERIFIED",
        "SUPPORTED_WITH_LIMITS",
        "AVAILABLE_NOT_YET_VERIFIED",
        "UNKNOWN",
        "BLOCKED_BY_POLICY",
        "VERIFIED_UNSUPPORTED_LOCALLY",
        "UNSUPPORTED",
    }
)


def _unique_strings(values: Iterable[str], field: str, *, required: bool = True) -> tuple[str, ...]:
    normalized = tuple(str(value).strip() for value in values)
    if (required and not normalized) or any(not value for value in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} must contain unique non-empty strings")
    return normalized


@dataclass(frozen=True, slots=True)
class ProviderCapabilityRequirements:
    required_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_capabilities", _unique_strings(self.required_capabilities, "required_capabilities", required=False))


@dataclass(frozen=True, slots=True)
class HostProviderModelOption:
    host_id: str
    provider_id: str
    model_id: str
    policy_allowed: bool = True

    def __post_init__(self) -> None:
        for field in ("host_id", "provider_id", "model_id"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field} must be a non-empty string")
        if type(self.policy_allowed) is not bool:
            raise ValueError("policy_allowed must be a boolean")


@dataclass(frozen=True, slots=True)
class ProviderCapabilityEvidence:
    host_id: str
    provider_id: str
    model_id: str
    capability_dispositions: tuple[tuple[str, str], ...]
    evidence_refs: tuple[str, ...]
    freshness_status: str = "CURRENT_AT_OBSERVATION"
    policy_allowed: bool = True
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("host_id", "provider_id", "model_id"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field} must be a non-empty string")
        if not self.capability_dispositions:
            raise ValueError("capability_dispositions must not be empty")
        seen: set[str] = set()
        for capability_id, disposition in self.capability_dispositions:
            if not isinstance(capability_id, str) or not capability_id.strip() or capability_id in seen:
                raise ValueError("capability_dispositions must contain unique non-empty capability IDs")
            if disposition not in CAPABILITY_DISPOSITIONS:
                raise ValueError("capability disposition is unsupported")
            seen.add(capability_id)
        object.__setattr__(self, "evidence_refs", _unique_strings(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "limitations", _unique_strings(self.limitations, "limitations", required=False))
        if self.freshness_status not in {"CURRENT_AT_OBSERVATION", "STALE", "UNKNOWN"}:
            raise ValueError("freshness_status is unsupported")
        if type(self.policy_allowed) is not bool:
            raise ValueError("policy_allowed must be a boolean")

    @property
    def capabilities(self) -> dict[str, str]:
        return dict(self.capability_dispositions)


@dataclass(frozen=True, slots=True)
class ProviderCapabilityAdvisory:
    host_id: str
    provider_id: str
    model_id: str
    disposition: str
    matched_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    shadow_only: bool = True
    provider_selection_authority: bool = False
    automatic_provider_switching: bool = False
    automatic_provider_fallback: bool = False
    learned_routing_promotion: bool = False
    specialist_routing_changed: bool = False
    workflow_topology_changed: bool = False

    def __post_init__(self) -> None:
        if self.disposition not in BROKER_DISPOSITIONS:
            raise ValueError("broker disposition is unsupported")
        for field in ("matched_capabilities", "missing_capabilities", "reason_codes", "limitations"):
            object.__setattr__(self, field, _unique_strings(getattr(self, field), field, required=False))
        object.__setattr__(self, "evidence_refs", _unique_strings(self.evidence_refs, "evidence_refs", required=False))
        flags = (
            "shadow_only",
            "provider_selection_authority",
            "automatic_provider_switching",
            "automatic_provider_fallback",
            "learned_routing_promotion",
            "specialist_routing_changed",
            "workflow_topology_changed",
        )
        if self.shadow_only is not True or not all(getattr(self, flag) is False for flag in flags[1:]):
            raise ValueError("provider capability advice cannot create authority")


@dataclass(frozen=True, slots=True)
class ProviderCapabilityBrokerDecision:
    advisories: tuple[ProviderCapabilityAdvisory, ...]
    reason_codes: tuple[str, ...]
    shadow_only: bool = True
    provider_selection_changed: bool = False
    automatic_provider_switching: bool = False
    automatic_provider_fallback: bool = False
    learned_routing_promotion: bool = False
    specialist_routing_changed: bool = False
    workflow_topology_changed: bool = False

    def __post_init__(self) -> None:
        if not self.shadow_only or any(
            getattr(self, field) is not False
            for field in (
                "provider_selection_changed",
                "automatic_provider_switching",
                "automatic_provider_fallback",
                "learned_routing_promotion",
                "specialist_routing_changed",
                "workflow_topology_changed",
            )
        ):
            raise ValueError("provider capability broker cannot create authority")
        if not all(isinstance(advisory, ProviderCapabilityAdvisory) for advisory in self.advisories):
            raise TypeError("advisories must contain ProviderCapabilityAdvisory")
        object.__setattr__(self, "reason_codes", _unique_strings(self.reason_codes, "reason_codes"))


def _advisory(
    option: HostProviderModelOption,
    requirements: ProviderCapabilityRequirements,
    evidence: ProviderCapabilityEvidence | None,
) -> ProviderCapabilityAdvisory:
    identity = (option.host_id, option.provider_id, option.model_id)
    if not option.policy_allowed:
        return ProviderCapabilityAdvisory(*identity, "POLICY_BLOCKED", (), requirements.required_capabilities, (), ("HOST_OPTION_POLICY_BLOCKED",))
    if evidence is None:
        return ProviderCapabilityAdvisory(*identity, "UNKNOWN", (), requirements.required_capabilities, (), ("NO_CURRENT_PROVIDER_MODEL_EVIDENCE",))
    if not evidence.policy_allowed:
        return ProviderCapabilityAdvisory(*identity, "POLICY_BLOCKED", (), requirements.required_capabilities, evidence.evidence_refs, ("PROVIDER_MODEL_POLICY_BLOCKED",), evidence.limitations)
    if evidence.freshness_status != "CURRENT_AT_OBSERVATION":
        return ProviderCapabilityAdvisory(*identity, "UNKNOWN", (), requirements.required_capabilities, evidence.evidence_refs, ("STALE_OR_UNKNOWN_EVIDENCE",), evidence.limitations)

    capabilities = evidence.capabilities
    missing = tuple(capability for capability in requirements.required_capabilities if capability not in capabilities)
    required_dispositions = tuple(capabilities.get(capability) for capability in requirements.required_capabilities if capability in capabilities)
    if any(disposition == "BLOCKED_BY_POLICY" for disposition in required_dispositions):
        disposition = "POLICY_BLOCKED"
        reasons = ("REQUIRED_CAPABILITY_POLICY_BLOCKED",)
    elif missing:
        disposition = "UNKNOWN"
        reasons = ("MISSING_CAPABILITY_EVIDENCE",)
    elif any(disposition in {"UNKNOWN", "AVAILABLE_NOT_YET_VERIFIED"} for disposition in required_dispositions):
        disposition = "UNKNOWN"
        reasons = ("REQUIRED_CAPABILITY_NOT_VERIFIED",)
    elif any(disposition in {"UNSUPPORTED", "VERIFIED_UNSUPPORTED_LOCALLY"} for disposition in required_dispositions):
        disposition = "INELIGIBLE"
        reasons = ("REQUIRED_CAPABILITY_UNSUPPORTED",)
    elif any(disposition == "SUPPORTED_WITH_LIMITS" for disposition in required_dispositions):
        disposition = "ELIGIBLE_WITH_LIMITS"
        reasons = ("REQUIRED_CAPABILITIES_SUPPORTED_WITH_LIMITS",)
    else:
        disposition = "ELIGIBLE"
        reasons = ("REQUIRED_CAPABILITIES_SUPPORTED",)
    matched = tuple(capability for capability in requirements.required_capabilities if capability not in missing and capabilities[capability] in {"SUPPORTED_VERIFIED", "SUPPORTED_WITH_LIMITS"})
    return ProviderCapabilityAdvisory(*identity, disposition, matched, missing, evidence.evidence_refs, reasons, evidence.limitations)


def broker_provider_capabilities(
    requirements: ProviderCapabilityRequirements,
    host_options: Iterable[HostProviderModelOption],
    evidence_profiles: Iterable[ProviderCapabilityEvidence],
) -> ProviderCapabilityBrokerDecision:
    """Classify exposed provider/model options without selecting or switching one."""
    if not isinstance(requirements, ProviderCapabilityRequirements):
        raise TypeError("requirements must be ProviderCapabilityRequirements")
    option_map: dict[tuple[str, str, str], HostProviderModelOption] = {}
    for option in host_options:
        if not isinstance(option, HostProviderModelOption):
            raise TypeError("host_options must contain HostProviderModelOption")
        key = (option.host_id, option.provider_id, option.model_id)
        if key in option_map:
            raise ValueError("host_options must contain unique host/provider/model identities")
        option_map[key] = option
    evidence_map: dict[tuple[str, str, str], ProviderCapabilityEvidence] = {}
    for evidence in evidence_profiles:
        if not isinstance(evidence, ProviderCapabilityEvidence):
            raise TypeError("evidence_profiles must contain ProviderCapabilityEvidence")
        key = (evidence.host_id, evidence.provider_id, evidence.model_id)
        if key in evidence_map:
            raise ValueError("evidence_profiles must contain unique host/provider/model identities")
        evidence_map[key] = evidence
    advisories = tuple(
        _advisory(option, requirements, evidence_map.get(key))
        for key, option in sorted(option_map.items())
    )
    return ProviderCapabilityBrokerDecision(
        advisories=advisories,
        reason_codes=("SHADOW_ADVISORY_ONLY", "PROVIDER_SELECTION_NOT_PERFORMED", "AUTOMATIC_PROVIDER_SWITCHING_PROHIBITED"),
    )


__all__ = [
    "BROKER_DISPOSITIONS",
    "CAPABILITY_DISPOSITIONS",
    "PROVIDER_CAPABILITY_BROKER_POLICY_VERSION",
    "HostProviderModelOption",
    "ProviderCapabilityAdvisory",
    "ProviderCapabilityBrokerDecision",
    "ProviderCapabilityEvidence",
    "ProviderCapabilityRequirements",
    "broker_provider_capabilities",
]
