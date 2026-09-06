from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


INTEGRATION_STRATEGY_POLICY_VERSION = "orchestra.integration-strategy-policy.v1"
ELIGIBLE_DISPOSITIONS = frozenset({"SUPPORTED_VERIFIED", "SUPPORTED_WITH_LIMITS"})


class IntegrationStrategy(str, Enum):
    AGENT_SKILLS = "AGENT_SKILLS"
    CUSTOM_AGENT = "CUSTOM_AGENT"
    MCP_TRANSPORT = "MCP_TRANSPORT"
    PLUGIN_OR_EXTENSION = "PLUGIN_OR_EXTENSION"
    CLI_ADAPTER = "CLI_ADAPTER"
    REPOSITORY_INSTRUCTIONS = "REPOSITORY_INSTRUCTIONS"
    WORKSPACE_INSTRUCTIONS = "WORKSPACE_INSTRUCTIONS"
    INSTRUCTION_ONLY_FALLBACK = "INSTRUCTION_ONLY_FALLBACK"
    UNSUPPORTED_FAIL_CLOSED = "UNSUPPORTED_FAIL_CLOSED"


_DECLARED_ORDER = {strategy: index for index, strategy in enumerate(IntegrationStrategy)}


def _unique_strings(values: Iterable[str], field: str) -> tuple[str, ...]:
    normalized = tuple(str(value).strip() for value in values)
    if any(not value for value in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} must contain unique non-empty strings")
    return normalized


@dataclass(frozen=True, slots=True)
class IntegrationStrategyRequirements:
    required_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_capabilities", _unique_strings(self.required_capabilities, "required_capabilities"))


@dataclass(frozen=True, slots=True)
class TransportCapabilityEvidence:
    strategy_id: IntegrationStrategy | str
    disposition: str
    provided_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    portability_score: int = 0
    context_cost: int = 0
    installation_complexity: int = 0
    evidence_quality: int = 0
    authority_preserved: bool = True
    policy_allowed: bool = True
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        try:
            strategy = IntegrationStrategy(self.strategy_id)
        except ValueError as exc:
            raise ValueError("strategy_id is unsupported") from exc
        if strategy is IntegrationStrategy.UNSUPPORTED_FAIL_CLOSED:
            raise ValueError("fail-closed strategy is an output, not a capability option")
        object.__setattr__(self, "strategy_id", strategy)
        if self.disposition not in ELIGIBLE_DISPOSITIONS | {"AVAILABLE_NOT_YET_VERIFIED", "UNKNOWN", "BLOCKED_BY_POLICY", "VERIFIED_UNSUPPORTED_LOCALLY", "UNSUPPORTED"}:
            raise ValueError("disposition is unsupported")
        object.__setattr__(self, "provided_capabilities", _unique_strings(self.provided_capabilities, "provided_capabilities"))
        object.__setattr__(self, "evidence_refs", _unique_strings(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "limitations", _unique_strings(self.limitations, "limitations"))
        for field in ("portability_score", "context_cost", "installation_complexity", "evidence_quality"):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        if type(self.authority_preserved) is not bool or type(self.policy_allowed) is not bool:
            raise ValueError("authority_preserved and policy_allowed must be booleans")


@dataclass(frozen=True, slots=True)
class IntegrationStrategyDecision:
    selected_strategy: IntegrationStrategy
    fail_closed: bool
    selected_evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rejected_strategies: tuple[tuple[str, tuple[str, ...]], ...]
    policy_version: str = INTEGRATION_STRATEGY_POLICY_VERSION
    transport_selection_only: bool = True
    specialist_routing_changed: bool = False
    workflow_topology_changed: bool = False
    provider_selection_changed: bool = False

    def __post_init__(self) -> None:
        if self.policy_version != INTEGRATION_STRATEGY_POLICY_VERSION:
            raise ValueError("unsupported integration strategy policy")
        if self.fail_closed != (self.selected_strategy is IntegrationStrategy.UNSUPPORTED_FAIL_CLOSED):
            raise ValueError("fail_closed does not match selected strategy")
        if not self.transport_selection_only or self.specialist_routing_changed or self.workflow_topology_changed or self.provider_selection_changed:
            raise ValueError("integration strategy decisions cannot expand routing or authority")


def _rejection(option: TransportCapabilityEvidence, requirements: IntegrationStrategyRequirements) -> tuple[str, ...]:
    reasons: list[str] = []
    if option.disposition not in ELIGIBLE_DISPOSITIONS:
        reasons.append(f"DISPOSITION:{option.disposition}")
    if not option.authority_preserved:
        reasons.append("AUTHORITY_NOT_PRESERVED")
    if not option.policy_allowed:
        reasons.append("BLOCKED_BY_HOST_OR_PROVIDER_POLICY")
    missing = tuple(sorted(set(requirements.required_capabilities) - set(option.provided_capabilities)))
    if missing:
        reasons.append("MISSING_CAPABILITIES:" + ",".join(missing))
    return tuple(reasons)


def resolve_integration_strategy(
    requirements: IntegrationStrategyRequirements,
    options: Iterable[TransportCapabilityEvidence],
) -> IntegrationStrategyDecision:
    if not isinstance(requirements, IntegrationStrategyRequirements):
        raise TypeError("requirements must be IntegrationStrategyRequirements")
    unique_options: dict[IntegrationStrategy, TransportCapabilityEvidence] = {}
    rejected: list[tuple[str, tuple[str, ...]]] = []
    eligible: list[TransportCapabilityEvidence] = []
    for option in options:
        if not isinstance(option, TransportCapabilityEvidence):
            raise TypeError("options must contain TransportCapabilityEvidence")
        if option.strategy_id in unique_options:
            raise ValueError("options must contain one record per strategy")
        unique_options[option.strategy_id] = option
        reasons = _rejection(option, requirements)
        if reasons:
            rejected.append((option.strategy_id.value, reasons))
        else:
            eligible.append(option)

    if not eligible:
        return IntegrationStrategyDecision(
            selected_strategy=IntegrationStrategy.UNSUPPORTED_FAIL_CLOSED,
            fail_closed=True,
            selected_evidence_refs=(),
            reason_codes=("NO_EVIDENCE_SUPPORTED_TRANSPORT",),
            rejected_strategies=tuple(rejected),
        )

    selected = min(
        eligible,
        key=lambda option: (
            option.installation_complexity,
            option.context_cost,
            -option.portability_score,
            -option.evidence_quality,
            _DECLARED_ORDER[option.strategy_id],
        ),
    )
    reasons = ["MINIMAL_ELIGIBLE_TRANSPORT"]
    if selected.disposition == "SUPPORTED_WITH_LIMITS":
        reasons.append("SELECTED_WITH_LIMITS")
    return IntegrationStrategyDecision(
        selected_strategy=selected.strategy_id,
        fail_closed=False,
        selected_evidence_refs=selected.evidence_refs,
        reason_codes=tuple(reasons),
        rejected_strategies=tuple(rejected),
    )


__all__ = [
    "ELIGIBLE_DISPOSITIONS",
    "INTEGRATION_STRATEGY_POLICY_VERSION",
    "IntegrationStrategy",
    "IntegrationStrategyDecision",
    "IntegrationStrategyRequirements",
    "TransportCapabilityEvidence",
    "resolve_integration_strategy",
]
