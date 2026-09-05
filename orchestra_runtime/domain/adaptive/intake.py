from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from .task_profile import (
    AUTHORITY_DOMAINS,
    AUTHORITY_DOMAIN_OWNERS,
    EXECUTION_MODES,
    RISK_LEVELS,
    TASK_PROFILE_SCHEMA_VERSION,
    TaskProfile,
)

DERIVATION_POLICY_SCHEMA_VERSION = "orchestra.task-profile-derivation.v1"
MODE_ORDER = ("FAST", "STANDARD", "GOVERNED", "AUDIT", "DESTRUCTIVE")
RISK_ORDER = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
TERMINAL_DOMAINS = frozenset({"ROUTING", "COORDINATION", "IMPLEMENTATION", "VALIDATION", "TRANSITION"})
_OPERATION_KEYS = (
    "mutation",
    "implementation",
    "validation",
    "transition",
    "audit",
    "destructive",
    "protected_action",
    "parallel",
)


@dataclass(frozen=True, slots=True)
class IntakeSignal:
    kind: str
    value: str
    signal: str
    position: int

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "value": self.value,
            "signal": self.signal,
            "position": self.position,
        }


@dataclass(frozen=True, slots=True)
class TaskProfileDerivation:
    task_profile: TaskProfile
    matched_signals: tuple[IntakeSignal, ...]
    derivation_reasons: tuple[str, ...]


def _clean_prompt(prompt: object) -> str:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    text = " ".join(prompt.split())
    if not text:
        raise ValueError("prompt must be non-empty")
    if len(text) > 4096:
        raise ValueError("prompt exceeds 4096 characters")
    return text


def _signal_position(text: str, signal: str) -> int | None:
    signal_text = " ".join(str(signal).casefold().split())
    if not signal_text:
        raise ValueError("derivation signals must be non-empty")
    escaped = re.escape(signal_text).replace(r"\ ", r"\s+")
    match = re.search(rf"(?<!\w){escaped}(?!\w)", text.casefold())
    return None if match is None else match.start()


def _exact_bool_or_default(value: object, default: bool, field_name: str) -> bool:
    if value is None:
        return default
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be an exact boolean")
    return value


def _bounded_nonnegative_int(value: object, default: int, field_name: str) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0 or value > 64:
        raise ValueError(f"{field_name} must be between 0 and 64")
    return value


def _string_list(value: object, field_name: str, *, maximum: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    items = tuple(str(item).strip() for item in value)
    if len(items) > maximum or any(not item for item in items) or len(items) != len(set(items)):
        raise ValueError(f"{field_name} must be unique, non-empty, and bounded")
    return items


def validate_derivation_policy(policy: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], Mapping[str, Any], frozenset[str]]:
    if not isinstance(policy, Mapping):
        raise TypeError("TaskProfile derivation policy must be a mapping")
    if policy.get("schema_version") != DERIVATION_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported TaskProfile derivation policy schema")
    if policy.get("owner") != "conductor":
        raise ValueError("TaskProfile derivation policy owner must be conductor")
    if policy.get("default_execution_mode") not in EXECUTION_MODES:
        raise ValueError("TaskProfile derivation default execution mode is invalid")
    if policy.get("default_risk_level") not in RISK_LEVELS:
        raise ValueError("TaskProfile derivation default risk level is invalid")

    raw_rules = policy.get("domain_rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise TypeError("TaskProfile derivation domain_rules must be a non-empty list")
    seen_domains: set[str] = set()
    rules: list[Mapping[str, Any]] = []
    for rule in raw_rules:
        if not isinstance(rule, Mapping):
            raise TypeError("TaskProfile derivation domain rule must be a mapping")
        domain = str(rule.get("domain", "")).strip().upper()
        signals = rule.get("signals")
        if domain not in AUTHORITY_DOMAINS or domain in seen_domains:
            raise ValueError("TaskProfile derivation domain rule set is invalid")
        if not isinstance(signals, list) or not signals or any(not str(item).strip() for item in signals):
            raise ValueError("TaskProfile derivation domain signals must be non-empty")
        seen_domains.add(domain)
        rules.append(rule)

    raw_operations = policy.get("operation_signals")
    if not isinstance(raw_operations, Mapping):
        raise TypeError("TaskProfile derivation operation_signals must be a mapping")
    if set(raw_operations) != set(_OPERATION_KEYS):
        raise ValueError("TaskProfile derivation operation signal set changed")
    for key in _OPERATION_KEYS:
        signals = raw_operations[key]
        if not isinstance(signals, list) or not signals or any(not str(item).strip() for item in signals):
            raise ValueError(f"TaskProfile derivation operation signals are invalid: {key}")

    governed = frozenset(str(item).strip().upper() for item in policy.get("governed_domains", ()))
    if not governed or not governed.issubset(AUTHORITY_DOMAINS):
        raise ValueError("TaskProfile derivation governed_domains are invalid")
    return rules, raw_operations, governed


def _matched_signals(
    prompt: str,
    domain_rules: list[Mapping[str, Any]],
    operation_signals: Mapping[str, Any],
) -> tuple[IntakeSignal, ...]:
    matches: list[IntakeSignal] = []
    for rule in domain_rules:
        domain = str(rule["domain"]).strip().upper()
        for raw_signal in rule["signals"]:
            signal = str(raw_signal).strip()
            position = _signal_position(prompt, signal)
            if position is not None:
                matches.append(IntakeSignal("DOMAIN", domain, signal, position))
    for operation in _OPERATION_KEYS:
        for raw_signal in operation_signals[operation]:
            signal = str(raw_signal).strip()
            position = _signal_position(prompt, signal)
            if position is not None:
                matches.append(IntakeSignal("OPERATION", operation.upper(), signal, position))
    return tuple(sorted(matches, key=lambda item: (item.position, item.kind, item.value, item.signal)))


def _operation_active(matches: tuple[IntakeSignal, ...], operation: str) -> bool:
    target = operation.upper()
    return any(item.kind == "OPERATION" and item.value == target for item in matches)


def _domain_order(matches: tuple[IntakeSignal, ...]) -> list[str]:
    first_position: dict[str, int] = {}
    for item in matches:
        if item.kind == "DOMAIN":
            first_position.setdefault(item.value, item.position)
    return [
        domain
        for domain, _ in sorted(first_position.items(), key=lambda pair: (pair[1], pair[0]))
    ]


def _stronger(current: str, explicit: object, ordered: tuple[str, ...], field_name: str) -> str:
    if explicit is None:
        return current
    candidate = str(explicit).strip().upper()
    if candidate not in ordered:
        raise ValueError(f"{field_name} is invalid")
    return ordered[max(ordered.index(current), ordered.index(candidate))]


def _stable_task_id(prompt: str, source_identity: str) -> str:
    payload = json.dumps(
        {"prompt": prompt, "source_identity": source_identity},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "task." + sha256(payload).hexdigest()[:24]


def derive_task_profile(
    *,
    prompt: str,
    metadata: Mapping[str, Any],
    current_source_identity: str,
    policy: Mapping[str, Any],
) -> TaskProfileDerivation:
    """Derive a minimum authority-safe TaskProfile from deterministic intake signals."""

    text = _clean_prompt(prompt)
    if not isinstance(metadata, Mapping):
        raise TypeError("TaskProfile derivation metadata must be a mapping")
    source_identity = str(current_source_identity).strip()
    if not source_identity:
        raise ValueError("current_source_identity must be non-empty")

    domain_rules, operation_signals, governed_domains = validate_derivation_policy(policy)
    matches = _matched_signals(text, domain_rules, operation_signals)
    domains = _domain_order(matches)

    explicit_domains = tuple(item.upper() for item in _string_list(
        metadata.get("agentic_authority_domains"),
        "agentic_authority_domains",
        maximum=14,
    ))
    if any(item not in AUTHORITY_DOMAINS for item in explicit_domains):
        raise ValueError("agentic_authority_domains contains an unknown authority domain")
    for domain in explicit_domains:
        if domain not in domains:
            domains.append(domain)

    mutation_required = _operation_active(matches, "mutation")
    implementation_required = _operation_active(matches, "implementation")
    validation_required = _operation_active(matches, "validation")
    transition_required = _operation_active(matches, "transition")
    audit_requested = _operation_active(matches, "audit")
    production_transition = transition_required and _signal_position(text, "production") is not None
    destructive_requested = _operation_active(matches, "destructive") or production_transition
    protected_action_required = _operation_active(matches, "protected_action")
    parallelizable = _operation_active(matches, "parallel")

    if implementation_required and "IMPLEMENTATION" not in domains:
        domains.append("IMPLEMENTATION")
    if validation_required and "VALIDATION" not in domains:
        domains.append("VALIDATION")
    if transition_required and "TRANSITION" not in domains:
        domains.append("TRANSITION")
    if not domains:
        domains.append("ROUTING")

    nonterminal_domains = [item for item in domains if item not in TERMINAL_DOMAINS]
    implementation_dependency = 1 if implementation_required and nonterminal_domains else 0
    dependency_default = max(0, len(nonterminal_domains) - 1) + implementation_dependency
    independent_default = len(nonterminal_domains) if len(nonterminal_domains) >= 2 else 0

    if destructive_requested:
        mode = "DESTRUCTIVE"
    elif audit_requested and not mutation_required:
        mode = "AUDIT"
    elif any(domain in governed_domains for domain in domains):
        mode = "GOVERNED"
    elif mutation_required or implementation_required or len(nonterminal_domains) > 1:
        mode = "STANDARD"
    else:
        mode = str(policy["default_execution_mode"]).strip().upper()
    explicit_mode = metadata.get("agentic_execution_mode")
    if explicit_mode is None:
        risk_mode = metadata.get("risk_mode")
        if isinstance(risk_mode, str) and risk_mode.strip().upper() in MODE_ORDER:
            explicit_mode = risk_mode
    mode = _stronger(mode, explicit_mode, MODE_ORDER, "agentic_execution_mode")

    if destructive_requested:
        risk = "CRITICAL"
    elif protected_action_required or any(domain in governed_domains for domain in domains):
        risk = "HIGH"
    elif mutation_required or implementation_required or len(nonterminal_domains) > 1 or audit_requested:
        risk = "MEDIUM"
    else:
        risk = str(policy["default_risk_level"]).strip().upper()
    risk = _stronger(risk, metadata.get("agentic_risk_level"), RISK_ORDER, "agentic_risk_level")

    explicit_owner = metadata.get("agentic_primary_owner")
    if explicit_owner is None:
        owner_domain = nonterminal_domains[0] if nonterminal_domains else domains[0]
        primary_owner = AUTHORITY_DOMAIN_OWNERS[owner_domain]
    else:
        primary_owner = str(explicit_owner).strip().casefold()
        valid_owners = set(AUTHORITY_DOMAIN_OWNERS.values())
        if primary_owner not in valid_owners:
            raise ValueError("agentic_primary_owner is not a canonical specialist owner")

    protected_action_authorized = _exact_bool_or_default(
        metadata.get("protected_action_authorized"),
        False,
        "protected_action_authorized",
    )
    if protected_action_authorized and not protected_action_required:
        raise ValueError("protected_action_authorized requires a protected action signal")

    critic_owner = metadata.get("critic_owner")
    critic_domain = metadata.get("critic_domain")
    if (critic_owner is None) != (critic_domain is None):
        raise ValueError("critic_owner and critic_domain must be supplied together")

    reentry_specialists = _string_list(
        metadata.get("reentry_specialists"),
        "reentry_specialists",
        maximum=14,
    )
    human_gate_requirements = _string_list(
        metadata.get("human_gate_requirements"),
        "human_gate_requirements",
        maximum=32,
    )

    task_id = str(metadata.get("agentic_task_id", "")).strip() or _stable_task_id(text, source_identity)
    goal = str(metadata.get("agentic_goal", "")).strip() or text
    profile = TaskProfile(
        schema_version=TASK_PROFILE_SCHEMA_VERSION,
        task_id=task_id,
        goal=goal,
        execution_mode=mode,
        risk_level=risk,
        authority_domains=tuple(domains),
        primary_owner=primary_owner,
        dependency_depth=_bounded_nonnegative_int(
            metadata.get("dependency_depth"),
            dependency_default,
            "dependency_depth",
        ),
        independent_subtasks=_bounded_nonnegative_int(
            metadata.get("independent_subtasks"),
            independent_default,
            "independent_subtasks",
        ),
        parallelizable=_exact_bool_or_default(
            metadata.get("parallelizable"),
            parallelizable,
            "parallelizable",
        ),
        mutation_required=_exact_bool_or_default(
            metadata.get("mutation_required"),
            mutation_required,
            "mutation_required",
        ),
        implementation_required=_exact_bool_or_default(
            metadata.get("implementation_required"),
            implementation_required,
            "implementation_required",
        ),
        validation_required=_exact_bool_or_default(
            metadata.get("validation_required"),
            validation_required,
            "validation_required",
        ),
        transition_required=_exact_bool_or_default(
            metadata.get("transition_required"),
            transition_required,
            "transition_required",
        ),
        external_state_required=_exact_bool_or_default(
            metadata.get("external_state_required"),
            audit_requested or mutation_required or validation_required or transition_required,
            "external_state_required",
        ),
        protected_action_required=protected_action_required,
        protected_action_authorized=protected_action_authorized,
        objective_verifier_available=_exact_bool_or_default(
            metadata.get("objective_verifier_available"),
            validation_required,
            "objective_verifier_available",
        ),
        critic_owner=critic_owner,
        critic_domain=critic_domain,
        reentry_specialists=reentry_specialists,
        current_source_identity=source_identity,
        human_gate_requirements=human_gate_requirements,
    )

    reasons: list[str] = []
    for domain in domains:
        reasons.append(f"AUTHORITY_DOMAIN:{domain}")
    reasons.extend(
        (
            f"EXECUTION_MODE:{mode}",
            f"RISK_LEVEL:{risk}",
            f"PRIMARY_OWNER:{profile.primary_owner}",
        )
    )
    if protected_action_required and not protected_action_authorized:
        reasons.append("PROTECTED_ACTION_AUTHORITY_NOT_INFERRED")
    if domains == ["ROUTING"]:
        reasons.append("UNKNOWN_DOMAIN_FAILS_TO_CONDUCTOR_ROUTING")
    if explicit_domains:
        reasons.append("EXPLICIT_AUTHORITY_DOMAINS_PRESERVED")
    if explicit_mode is not None:
        reasons.append("EXPLICIT_EXECUTION_MODE_MAY_ESCALATE_ONLY")
    if metadata.get("agentic_risk_level") is not None:
        reasons.append("EXPLICIT_RISK_LEVEL_MAY_ESCALATE_ONLY")
    if production_transition:
        reasons.append("PRODUCTION_TRANSITION_CLASSIFIED_DESTRUCTIVE")

    return TaskProfileDerivation(
        task_profile=profile,
        matched_signals=matches,
        derivation_reasons=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "DERIVATION_POLICY_SCHEMA_VERSION",
    "IntakeSignal",
    "MODE_ORDER",
    "RISK_ORDER",
    "TaskProfileDerivation",
    "derive_task_profile",
    "validate_derivation_policy",
]
