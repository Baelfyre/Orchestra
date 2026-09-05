from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

TASK_PROFILE_SCHEMA_VERSION = "orchestra.task-profile.v1"

EXECUTION_MODES = frozenset({"FAST", "STANDARD", "GOVERNED", "AUDIT", "DESTRUCTIVE"})
RISK_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
AUTHORITY_DOMAIN_OWNERS: dict[str, str] = {
    "BUSINESS_SCOPE": "the-steward",
    "LEGAL_COMPLIANCE": "the-governor",
    "TRANSITION": "arbiter",
    "VALIDATION": "overseer",
    "ROUTING": "conductor",
    "COORDINATION": "the-tuner",
    "SECURITY": "cipher",
    "UI_UX": "cloak",
    "ADVERSARIAL": "dagger",
    "PERSISTENCE": "chronicler",
    "DIAGRAM": "weaver",
    "DOCUMENTATION": "scribe",
    "ARCHITECTURE": "clockwork",
    "IMPLEMENTATION": "ponytail",
}
AUTHORITY_DOMAINS = frozenset(AUTHORITY_DOMAIN_OWNERS)

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")


def _text(value: object, field_name: str, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    if len(text) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{field_name} must not contain control characters")
    return text


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name, max_length=128).casefold()
    if not _IDENTIFIER_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return text


def _optional_identifier(value: object | None, field_name: str) -> str | None:
    return None if value is None else _identifier(value, field_name)


def _exact_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be an exact boolean")
    return value


def _bounded_int(value: object, field_name: str, *, maximum: int = 64) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0 or value > maximum:
        raise ValueError(f"{field_name} must be between 0 and {maximum}")
    return value


def _unique_strings(values: object, field_name: str, *, max_items: int) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    normalized = tuple(_text(value, field_name, max_length=256) for value in values)
    if len(normalized) > max_items:
        raise ValueError(f"{field_name} exceeds {max_items} items")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return normalized


@dataclass(frozen=True, slots=True)
class TaskProfile:
    task_id: str
    goal: str
    execution_mode: str
    risk_level: str
    authority_domains: tuple[str, ...]
    primary_owner: str | None
    dependency_depth: int
    independent_subtasks: int
    parallelizable: bool
    mutation_required: bool
    implementation_required: bool
    validation_required: bool
    transition_required: bool
    external_state_required: bool
    protected_action_required: bool
    protected_action_authorized: bool
    objective_verifier_available: bool
    critic_owner: str | None
    critic_domain: str | None
    current_source_identity: str
    human_gate_requirements: tuple[str, ...] = ()
    schema_version: str = TASK_PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TASK_PROFILE_SCHEMA_VERSION:
            raise ValueError(f"unsupported task profile schema: {self.schema_version}")
        mode = _text(self.execution_mode, "execution_mode", max_length=32).upper()
        if mode not in EXECUTION_MODES:
            raise ValueError(f"unsupported execution_mode: {mode}")
        risk = _text(self.risk_level, "risk_level", max_length=32).upper()
        if risk not in RISK_LEVELS:
            raise ValueError(f"unsupported risk_level: {risk}")
        domains = tuple(_text(item, "authority_domain", max_length=64).upper() for item in self.authority_domains)
        if not domains or len(domains) > 14 or len(domains) != len(set(domains)):
            raise ValueError("authority_domains must be non-empty, unique, and bounded")
        unknown = [item for item in domains if item not in AUTHORITY_DOMAINS]
        if unknown:
            raise ValueError("unknown authority_domains: " + ", ".join(unknown))
        critic_owner = _optional_identifier(self.critic_owner, "critic_owner")
        critic_domain = None if self.critic_domain is None else _text(self.critic_domain, "critic_domain", max_length=128).upper()
        if (critic_owner is None) != (critic_domain is None):
            raise ValueError("critic_owner and critic_domain must be supplied together")
        protected_required = _exact_bool(self.protected_action_required, "protected_action_required")
        protected_authorized = _exact_bool(self.protected_action_authorized, "protected_action_authorized")
        if protected_authorized and not protected_required:
            raise ValueError("protected_action_authorized requires protected_action_required")
        object.__setattr__(self, "task_id", _text(self.task_id, "task_id", max_length=256))
        object.__setattr__(self, "goal", _text(self.goal, "goal", max_length=4096))
        object.__setattr__(self, "execution_mode", mode)
        object.__setattr__(self, "risk_level", risk)
        object.__setattr__(self, "authority_domains", domains)
        object.__setattr__(self, "primary_owner", _optional_identifier(self.primary_owner, "primary_owner"))
        object.__setattr__(self, "dependency_depth", _bounded_int(self.dependency_depth, "dependency_depth"))
        object.__setattr__(self, "independent_subtasks", _bounded_int(self.independent_subtasks, "independent_subtasks"))
        for field_name in (
            "parallelizable",
            "mutation_required",
            "implementation_required",
            "validation_required",
            "transition_required",
            "external_state_required",
            "objective_verifier_available",
        ):
            object.__setattr__(self, field_name, _exact_bool(getattr(self, field_name), field_name))
        object.__setattr__(self, "protected_action_required", protected_required)
        object.__setattr__(self, "protected_action_authorized", protected_authorized)
        object.__setattr__(self, "critic_owner", critic_owner)
        object.__setattr__(self, "critic_domain", critic_domain)
        object.__setattr__(
            self,
            "current_source_identity",
            _text(self.current_source_identity, "current_source_identity", max_length=512),
        )
        object.__setattr__(
            self,
            "human_gate_requirements",
            _unique_strings(self.human_gate_requirements, "human_gate_requirement", max_items=32),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TaskProfile":
        if not isinstance(data, Mapping):
            raise TypeError("task profile must be a mapping")
        return cls(
            schema_version=str(data.get("schema_version", "")),
            task_id=data.get("task_id", ""),
            goal=data.get("goal", ""),
            execution_mode=data.get("execution_mode", ""),
            risk_level=data.get("risk_level", ""),
            authority_domains=tuple(data.get("authority_domains", ())),
            primary_owner=data.get("primary_owner"),
            dependency_depth=data.get("dependency_depth", -1),
            independent_subtasks=data.get("independent_subtasks", -1),
            parallelizable=data.get("parallelizable"),
            mutation_required=data.get("mutation_required"),
            implementation_required=data.get("implementation_required"),
            validation_required=data.get("validation_required"),
            transition_required=data.get("transition_required"),
            external_state_required=data.get("external_state_required"),
            protected_action_required=data.get("protected_action_required"),
            protected_action_authorized=data.get("protected_action_authorized"),
            objective_verifier_available=data.get("objective_verifier_available"),
            critic_owner=data.get("critic_owner"),
            critic_domain=data.get("critic_domain"),
            current_source_identity=data.get("current_source_identity", ""),
            human_gate_requirements=tuple(data.get("human_gate_requirements", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "goal": self.goal,
            "execution_mode": self.execution_mode,
            "risk_level": self.risk_level,
            "authority_domains": list(self.authority_domains),
            "primary_owner": self.primary_owner,
            "dependency_depth": self.dependency_depth,
            "independent_subtasks": self.independent_subtasks,
            "parallelizable": self.parallelizable,
            "mutation_required": self.mutation_required,
            "implementation_required": self.implementation_required,
            "validation_required": self.validation_required,
            "transition_required": self.transition_required,
            "external_state_required": self.external_state_required,
            "protected_action_required": self.protected_action_required,
            "protected_action_authorized": self.protected_action_authorized,
            "objective_verifier_available": self.objective_verifier_available,
            "critic_owner": self.critic_owner,
            "critic_domain": self.critic_domain,
            "current_source_identity": self.current_source_identity,
            "human_gate_requirements": list(self.human_gate_requirements),
        }


__all__ = [
    "AUTHORITY_DOMAINS",
    "AUTHORITY_DOMAIN_OWNERS",
    "EXECUTION_MODES",
    "RISK_LEVELS",
    "TASK_PROFILE_SCHEMA_VERSION",
    "TaskProfile",
]
