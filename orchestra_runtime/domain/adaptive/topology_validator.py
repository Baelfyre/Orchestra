from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

AUTHORITY_VIEW_SCHEMA_VERSION = "orchestra.specialist-authority-view.v1"
CRITIC_CONTRACT_SCHEMA_VERSION = "orchestra.critic-contract.v1"
WORKFLOW_PROFILE_SCHEMA_VERSION = "orchestra.agentic-workflow-profile.v1"

PATTERN_ORDER = ("ROUTING", "PLANNING", "TOOL_REACT", "REFLECTION_CRITIC", "MULTI_AGENT")
PATTERNS = frozenset(PATTERN_ORDER)
EXPECTED_SPECIALISTS = frozenset(
    {
        "the-steward",
        "the-governor",
        "arbiter",
        "overseer",
        "conductor",
        "the-tuner",
        "cipher",
        "cloak",
        "dagger",
        "chronicler",
        "weaver",
        "scribe",
        "clockwork",
        "ponytail",
    }
)
REQUIRED_COMPOSITION_INVARIANT_IDS = tuple(f"AWF-I{index:02d}" for index in range(1, 27))


def _clean(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _strings(values: Iterable[object], field_name: str, *, max_items: int, nonempty: bool = False) -> tuple[str, ...]:
    normalized = tuple(_clean(value, field_name) for value in values)
    if len(normalized) > max_items:
        raise ValueError(f"{field_name} exceeds {max_items} items")
    if nonempty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return normalized


@dataclass(frozen=True, slots=True)
class SpecialistAuthority:
    slug: str
    authority_class: str
    source_path: str
    source_blob_sha: str
    observe_classes: tuple[str, ...]
    decide_classes: tuple[str, ...]
    mutate_classes: tuple[str, ...]
    can_dispatch: bool
    can_transition: bool
    can_validate: bool
    can_coordinate: bool
    can_implement: bool
    can_execute_protected_action_without_external_authority: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SpecialistAuthority":
        if not isinstance(data, Mapping):
            raise TypeError("specialist authority must be a mapping")
        flags = {}
        for field_name in (
            "can_dispatch",
            "can_transition",
            "can_validate",
            "can_coordinate",
            "can_implement",
            "can_execute_protected_action_without_external_authority",
        ):
            value = data.get(field_name)
            if type(value) is not bool:
                raise TypeError(f"{field_name} must be an exact boolean")
            flags[field_name] = value
        sha = _clean(data.get("source_blob_sha"), "source_blob_sha").casefold()
        if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
            raise ValueError("source_blob_sha must be a 40-character Git blob SHA")
        return cls(
            slug=_clean(data.get("slug"), "slug").casefold(),
            authority_class=_clean(data.get("authority_class"), "authority_class"),
            source_path=_clean(data.get("source_path"), "source_path"),
            source_blob_sha=sha,
            observe_classes=_strings(data.get("observe_classes", ()), "observe_class", max_items=32, nonempty=True),
            decide_classes=_strings(data.get("decide_classes", ()), "decide_class", max_items=32, nonempty=True),
            mutate_classes=_strings(data.get("mutate_classes", ()), "mutate_class", max_items=32),
            **flags,
        )


@dataclass(frozen=True, slots=True)
class CriticContract:
    contract_id: str
    critic_owner: str
    evaluation_domain: str
    evidence_owner: str
    can_block: bool
    can_request_revision: bool
    can_transition: bool
    max_iterations: int
    schema_version: str = CRITIC_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CRITIC_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported critic contract schema")
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int):
            raise TypeError("max_iterations must be an integer")
        if self.max_iterations < 0 or self.max_iterations > 3:
            raise ValueError("max_iterations must be between 0 and 3")
        for field_name in ("can_block", "can_request_revision", "can_transition"):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be an exact boolean")
        object.__setattr__(self, "contract_id", _clean(self.contract_id, "contract_id"))
        object.__setattr__(self, "critic_owner", _clean(self.critic_owner, "critic_owner").casefold())
        object.__setattr__(self, "evaluation_domain", _clean(self.evaluation_domain, "evaluation_domain").upper())
        object.__setattr__(self, "evidence_owner", _clean(self.evidence_owner, "evidence_owner").casefold())
        if self.can_transition and self.critic_owner != "arbiter":
            raise ValueError("only Arbiter may hold critic transition authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "critic_owner": self.critic_owner,
            "evaluation_domain": self.evaluation_domain,
            "evidence_owner": self.evidence_owner,
            "can_block": self.can_block,
            "can_request_revision": self.can_request_revision,
            "can_transition": self.can_transition,
            "max_iterations": self.max_iterations,
        }


@dataclass(frozen=True, slots=True)
class AgenticWorkflowProfile:
    profile_id: str
    source_task_id: str
    primary_owner: str
    required_specialists: tuple[str, ...]
    selected_patterns: tuple[str, ...]
    sequence: tuple[str, ...]
    parallel_groups: tuple[tuple[str, ...], ...]
    concurrency_mode: str
    max_parallel_specialists: int
    human_gate_required: bool
    escalation_reasons: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    critic_contract_id: str | None
    selected_by: str = "conductor"
    topology_effective: bool = True
    topology_change_requires_human_approval: bool = False
    authority_expansion: bool = False
    schema_version: str = WORKFLOW_PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != WORKFLOW_PROFILE_SCHEMA_VERSION:
            raise ValueError("unsupported workflow profile schema")
        if self.selected_by != "conductor":
            raise ValueError("agentic workflow profile must be selected by conductor")
        if self.topology_effective is not True:
            raise ValueError("agentic workflow profile must be execution-effective")
        if self.topology_change_requires_human_approval is not False:
            raise ValueError("topology changes inside granted authority must not require human approval")
        if self.authority_expansion is not False:
            raise ValueError("workflow profile cannot expand authority")
        if type(self.human_gate_required) is not bool:
            raise TypeError("human_gate_required must be an exact boolean")
        if isinstance(self.max_parallel_specialists, bool) or not isinstance(self.max_parallel_specialists, int):
            raise TypeError("max_parallel_specialists must be an integer")
        if self.max_parallel_specialists < 1:
            raise ValueError("max_parallel_specialists must be positive")
        required = _strings(self.required_specialists, "required_specialist", max_items=14, nonempty=True)
        sequence = _strings(self.sequence, "sequence_specialist", max_items=20, nonempty=True)
        if set(required) != set(sequence):
            raise ValueError("sequence must contain exactly the required specialist set")
        patterns = _strings(self.selected_patterns, "selected_pattern", max_items=5, nonempty=True)
        if any(pattern not in PATTERNS for pattern in patterns):
            raise ValueError("workflow contains unknown agentic pattern")
        if tuple(sorted(patterns, key=PATTERN_ORDER.index)) != patterns:
            raise ValueError("selected_patterns must use canonical pattern order")
        if "ROUTING" not in patterns:
            raise ValueError("all adaptive workflow profiles require Conductor routing")
        groups = tuple(tuple(group) for group in self.parallel_groups)
        for group in groups:
            members = _strings(group, "parallel_specialist", max_items=14, nonempty=True)
            if len(members) < 2:
                raise ValueError("parallel group must contain at least two specialists")
            if not set(members).issubset(set(required)):
                raise ValueError("parallel group contains specialist outside required set")
            if len(members) > self.max_parallel_specialists:
                raise ValueError("parallel group exceeds OEE max_parallel_specialists")
        mode = _clean(self.concurrency_mode, "concurrency_mode").upper()
        if mode not in {"SINGLE_OWNER", "SEQUENTIAL_MULTI_AGENT", "PARALLEL_MULTI_AGENT"}:
            raise ValueError("unsupported concurrency_mode")
        if mode == "SINGLE_OWNER" and len(required) != 1:
            raise ValueError("SINGLE_OWNER requires exactly one specialist")
        if mode == "PARALLEL_MULTI_AGENT" and not groups:
            raise ValueError("PARALLEL_MULTI_AGENT requires a parallel group")
        if groups and "MULTI_AGENT" not in patterns:
            raise ValueError("parallel groups require MULTI_AGENT pattern")
        if self.human_gate_required and not self.escalation_reasons:
            raise ValueError("human_gate_required requires an underlying escalation reason")
        object.__setattr__(self, "profile_id", _clean(self.profile_id, "profile_id"))
        object.__setattr__(self, "source_task_id", _clean(self.source_task_id, "source_task_id"))
        object.__setattr__(self, "primary_owner", _clean(self.primary_owner, "primary_owner").casefold())
        object.__setattr__(self, "required_specialists", required)
        object.__setattr__(self, "selected_patterns", patterns)
        object.__setattr__(self, "sequence", sequence)
        object.__setattr__(self, "parallel_groups", groups)
        object.__setattr__(self, "concurrency_mode", mode)
        object.__setattr__(self, "escalation_reasons", _strings(self.escalation_reasons, "escalation_reason", max_items=32))
        object.__setattr__(self, "stop_conditions", _strings(self.stop_conditions, "stop_condition", max_items=16, nonempty=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "source_task_id": self.source_task_id,
            "selected_by": self.selected_by,
            "primary_owner": self.primary_owner,
            "required_specialists": list(self.required_specialists),
            "selected_patterns": list(self.selected_patterns),
            "sequence": list(self.sequence),
            "parallel_groups": [list(group) for group in self.parallel_groups],
            "concurrency_mode": self.concurrency_mode,
            "max_parallel_specialists": self.max_parallel_specialists,
            "human_gate_required": self.human_gate_required,
            "escalation_reasons": list(self.escalation_reasons),
            "stop_conditions": list(self.stop_conditions),
            "critic_contract_id": self.critic_contract_id,
            "topology_effective": self.topology_effective,
            "topology_change_requires_human_approval": self.topology_change_requires_human_approval,
            "authority_expansion": self.authority_expansion,
        }


def parse_authority_view(data: Mapping[str, Any]) -> dict[str, SpecialistAuthority]:
    if not isinstance(data, Mapping):
        raise TypeError("authority view must be a mapping")
    if data.get("schema_version") != AUTHORITY_VIEW_SCHEMA_VERSION:
        raise ValueError("unsupported authority view schema")
    if data.get("source_of_truth") != "skills_and_governance_contracts":
        raise ValueError("authority view source_of_truth changed")
    if data.get("generation_policy") != "source_bound_compiled_view":
        raise ValueError("authority view generation_policy changed")
    raw = data.get("specialists")
    if not isinstance(raw, list):
        raise TypeError("authority view specialists must be a list")
    specialists = [SpecialistAuthority.from_mapping(item) for item in raw]
    slugs = [item.slug for item in specialists]
    if len(slugs) != len(set(slugs)):
        raise ValueError("authority view contains duplicate specialist slugs")
    if set(slugs) != EXPECTED_SPECIALISTS:
        raise ValueError("authority view specialist set must equal the canonical 14 specialists")
    by_slug = {item.slug: item for item in specialists}
    if {slug for slug, item in by_slug.items() if item.can_dispatch} != {"conductor"}:
        raise ValueError("Conductor must be the only dispatch authority")
    if {slug for slug, item in by_slug.items() if item.can_transition} != {"arbiter"}:
        raise ValueError("Arbiter must be the only transition authority")
    if {slug for slug, item in by_slug.items() if item.can_validate} != {"overseer"}:
        raise ValueError("Overseer must be the only primary validation authority")
    if {slug for slug, item in by_slug.items() if item.can_coordinate} != {"the-tuner"}:
        raise ValueError("The Tuner must be the only cross-specialist coordination authority")
    if {slug for slug, item in by_slug.items() if item.can_implement} != {"ponytail"}:
        raise ValueError("Ponytail must be the only general implementation authority")
    if any(item.can_execute_protected_action_without_external_authority for item in specialists):
        raise ValueError("no specialist may self-authorize protected actions")
    return by_slug


__all__ = [
    "AUTHORITY_VIEW_SCHEMA_VERSION",
    "CRITIC_CONTRACT_SCHEMA_VERSION",
    "WORKFLOW_PROFILE_SCHEMA_VERSION",
    "EXPECTED_SPECIALISTS",
    "PATTERNS",
    "PATTERN_ORDER",
    "REQUIRED_COMPOSITION_INVARIANT_IDS",
    "AgenticWorkflowProfile",
    "CriticContract",
    "SpecialistAuthority",
    "parse_authority_view",
]
