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
    positions = _signal_positions(text, signal)
    return None if not positions else positions[0]


def _signal_positions(text: str, signal: str) -> tuple[int, ...]:
    signal_text = " ".join(str(signal).casefold().split())
    if not signal_text:
        raise ValueError("derivation signals must be non-empty")
    escaped = re.escape(signal_text).replace(r"\ ", r"\s+")
    return tuple(
        match.start()
        for match in re.finditer(rf"(?<!\w){escaped}(?!\w)", text.casefold())
    )


def _quoted_ranges(text: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    for pattern in (r"`[^`]*`", r'"[^"]*"', r"'[^']*'"):
        for match in re.finditer(pattern, text):
            ranges.append((match.start(), match.end()))
    return tuple(sorted(ranges))


def _position_in_ranges(position: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _phrase_present(text: str, phrase: str) -> bool:
    normalized = " ".join(str(phrase).casefold().split())
    if not normalized:
        return False
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    return re.search(rf"(?<!\w){escaped}(?!\w)", text.casefold()) is not None


def _semantic_clause_ranges(text: str) -> tuple[tuple[int, int], ...]:
    separators = re.compile(
        r"[.!?;]+|,\s*(?:but|then|however|instead)\s+|\s+(?:but|however)\s+",
        re.IGNORECASE,
    )
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for match in separators.finditer(text):
        if cursor < match.start():
            ranges.append((cursor, match.start()))
        cursor = match.end()
    if cursor < len(text):
        ranges.append((cursor, len(text)))
    return tuple((start, end) for start, end in ranges if text[start:end].strip())


def _clause_for_position(text: str, position: int) -> tuple[int, int]:
    for start, end in _semantic_clause_ranges(text):
        if start <= position < end:
            return start, end
    return 0, len(text)


def _is_negated(
    text: str,
    position: int,
    negation_phrases: tuple[str, ...],
) -> bool:
    start, _ = _clause_for_position(text, position)
    prefix = text[start:position].casefold()

    # A coordinated independent action resets negation scope. Keep transition
    # verbs out of this reset set so "do not deploy and merge" remains jointly
    # negated while "hold off on merge and review the changelog" does not
    # suppress the later review object.
    reset_verbs = (
        "review",
        "audit",
        "assess",
        "analyze",
        "update",
        "write",
        "summarize",
        "explain",
        "describe",
        "document",
        "rename",
        "fix",
        "remove",
        "change",
        "add",
        "implement",
        "build",
        "run",
        "refactor",
        "modify",
        "edit",
    )
    conjunctions = tuple(re.finditer(r"\band\b", prefix))
    if conjunctions:
        suffix = prefix[conjunctions[-1].end():]
        if any(re.search(rf"(?<!\w){re.escape(verb)}(?!\w)", suffix) for verb in reset_verbs):
            prefix = suffix

    for phrase in negation_phrases:
        normalized = " ".join(str(phrase).casefold().split())
        escaped = re.escape(normalized).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){escaped}(?!\w)", prefix):
            return True
    return False


def _is_hypothetical(
    text: str,
    position: int,
    hypothetical_prefixes: tuple[str, ...],
) -> bool:
    start, _ = _clause_for_position(text, position)
    normalized = text[start:position].casefold().lstrip()
    for prefix in hypothetical_prefixes:
        candidate = " ".join(str(prefix).casefold().split())
        if normalized.startswith(candidate):
            return True
    return False


def _active_execution_signal_in_clause(
    text: str,
    start: int,
    end: int,
    operation_signals: Mapping[str, Any],
    quoted: tuple[tuple[int, int], ...],
    negations: tuple[str, ...],
    hypotheticals: tuple[str, ...],
) -> bool:
    execution_operations = (
        "implementation",
        "validation",
        "transition",
        "destructive",
        "protected_action",
    )
    for operation in execution_operations:
        for raw_signal in operation_signals[operation]:
            signal = str(raw_signal).strip()
            for position in _signal_positions(text, signal):
                if not (start <= position < end):
                    continue
                if _position_in_ranges(position, quoted):
                    continue
                if _is_negated(text, position, negations):
                    continue
                if _is_hypothetical(text, position, hypotheticals):
                    continue
                return True
    return False


def _representation_ranges(
    text: str,
    suppression_rules: Mapping[str, Any],
    operation_signals: Mapping[str, Any],
    quoted: tuple[tuple[int, int], ...],
) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
    artifacts = tuple(str(item).casefold() for item in suppression_rules["representation_artifacts"])
    verbs = tuple(str(item).casefold() for item in suppression_rules["representation_verbs"])
    edit_verbs = tuple(str(item).casefold() for item in suppression_rules["representation_edit_verbs"])
    scope_phrases = tuple(str(item).casefold() for item in suppression_rules["representation_scope_phrases"])
    negations = tuple(str(item).casefold() for item in suppression_rules["negation_phrases"])
    hypotheticals = tuple(str(item).casefold() for item in suppression_rules["hypothetical_prefixes"])

    representation: list[tuple[int, int]] = []
    edit_positions: list[int] = []
    for start, end in _semantic_clause_ranges(text):
        clause = text[start:end]
        lower = clause.casefold()
        artifact_present = any(_phrase_present(lower, item) for item in artifacts)
        active_representation_verb = False
        for verb in verbs:
            for position in _signal_positions(text, verb):
                if not (start <= position < end):
                    continue
                if _position_in_ranges(position, quoted):
                    continue
                if _is_negated(text, position, negations):
                    continue
                active_representation_verb = True
                break
            if active_representation_verb:
                break
        scope_present = any(_phrase_present(lower, item) for item in scope_phrases)
        representation_candidate = (
            (artifact_present and active_representation_verb)
            or scope_present
            or lower.lstrip().startswith("document ")
            or lower.lstrip().startswith("summarize ")
        )
        if not representation_candidate:
            continue
        if not scope_present and _active_execution_signal_in_clause(
            text,
            start,
            end,
            operation_signals,
            quoted,
            negations,
            hypotheticals,
        ):
            continue
        representation.append((start, end))
        for verb in edit_verbs:
            for position in _signal_positions(text, verb):
                if not (start <= position < end):
                    continue
                if _position_in_ranges(position, quoted):
                    continue
                if _is_negated(text, position, negations):
                    continue
                edit_positions.append(position)
    return tuple(representation), tuple(sorted(set(edit_positions)))


def _first_active_signal_position(
    text: str,
    signal: str,
    *,
    quoted: tuple[tuple[int, int], ...],
    negation_phrases: tuple[str, ...],
    hypothetical_prefixes: tuple[str, ...],
    suppress_hypothetical: bool,
) -> int | None:
    directives: list[tuple[int, bool]] = []
    for position in _signal_positions(text, signal):
        if _position_in_ranges(position, quoted):
            continue
        if suppress_hypothetical and _is_hypothetical(text, position, hypothetical_prefixes):
            continue
        directives.append((position, _is_negated(text, position, negation_phrases)))
    if not directives:
        return None
    position, negated = directives[-1]
    return None if negated else position

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


def validate_derivation_policy(policy: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], Mapping[str, Any], frozenset[str], Mapping[str, Any]]:
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

    raw_suppression = policy.get("suppression_rules")
    required_suppression = {
        "negation_phrases",
        "hypothetical_prefixes",
        "representation_artifacts",
        "representation_verbs",
        "representation_edit_verbs",
        "representation_scope_phrases",
    }
    if not isinstance(raw_suppression, Mapping):
        raise TypeError("TaskProfile derivation suppression_rules must be a mapping")
    if set(raw_suppression) != required_suppression:
        raise ValueError("TaskProfile derivation suppression rule set changed")
    for key in sorted(required_suppression):
        values = raw_suppression[key]
        if not isinstance(values, list) or not values or any(not str(item).strip() for item in values):
            raise ValueError(f"TaskProfile derivation suppression rules are invalid: {key}")
    return rules, raw_operations, governed, raw_suppression


def _matched_signals(
    prompt: str,
    domain_rules: list[Mapping[str, Any]],
    operation_signals: Mapping[str, Any],
    suppression_rules: Mapping[str, Any],
) -> tuple[tuple[IntakeSignal, ...], int, bool]:
    matches: list[IntakeSignal] = []
    suppressed = 0
    quoted = _quoted_ranges(prompt)
    negations = tuple(str(item).casefold() for item in suppression_rules["negation_phrases"])
    hypotheticals = tuple(str(item).casefold() for item in suppression_rules["hypothetical_prefixes"])
    representation_ranges, representation_edit_positions = _representation_ranges(
        prompt,
        suppression_rules,
        operation_signals,
        quoted,
    )

    for rule in domain_rules:
        domain = str(rule["domain"]).strip().upper()
        for raw_signal in rule["signals"]:
            signal = str(raw_signal).strip()
            directives: list[tuple[int, bool]] = []
            for position in _signal_positions(prompt, signal):
                if _position_in_ranges(position, quoted):
                    suppressed += 1
                    continue
                if _position_in_ranges(position, representation_ranges) and domain != "DOCUMENTATION":
                    suppressed += 1
                    continue
                directives.append((position, _is_negated(prompt, position, negations)))
            if not directives:
                continue
            active_position, negated = directives[-1]
            if negated:
                suppressed += 1
                continue
            matches.append(IntakeSignal("DOMAIN", domain, signal, active_position))

    for operation in _OPERATION_KEYS:
        for raw_signal in operation_signals[operation]:
            signal = str(raw_signal).strip()
            directives: list[tuple[int, bool]] = []
            for position in _signal_positions(prompt, signal):
                if _position_in_ranges(position, quoted):
                    suppressed += 1
                    continue
                if _is_hypothetical(prompt, position, hypotheticals):
                    suppressed += 1
                    continue
                if _position_in_ranges(position, representation_ranges) and operation != "audit":
                    suppressed += 1
                    continue
                directives.append((position, _is_negated(prompt, position, negations)))
            if not directives:
                continue
            active_position, negated = directives[-1]
            if negated:
                suppressed += 1
                continue
            matches.append(
                IntakeSignal("OPERATION", operation.upper(), signal, active_position)
            )

    for start, _ in representation_ranges:
        if not any(
            item.kind == "DOMAIN"
            and item.value == "DOCUMENTATION"
            and start <= item.position
            for item in matches
        ):
            matches.append(IntakeSignal("DOMAIN", "DOCUMENTATION", "representation_context", start))

    for position in representation_edit_positions:
        matches.append(
            IntakeSignal("OPERATION", "MUTATION", "representation_edit", position)
        )

    return (
        tuple(sorted(matches, key=lambda item: (item.position, item.kind, item.value, item.signal))),
        suppressed,
        bool(representation_ranges),
    )

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

    domain_rules, operation_signals, governed_domains, suppression_rules = validate_derivation_policy(policy)
    matches, suppressed_signal_count, representation_only = _matched_signals(
        text,
        domain_rules,
        operation_signals,
        suppression_rules,
    )
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
    quoted_ranges = _quoted_ranges(text)
    production_position = _first_active_signal_position(
        text,
        "production",
        quoted=quoted_ranges,
        negation_phrases=tuple(str(item).casefold() for item in suppression_rules["negation_phrases"]),
        hypothetical_prefixes=tuple(str(item).casefold() for item in suppression_rules["hypothetical_prefixes"]),
        suppress_hypothetical=True,
    )
    if representation_only and production_position is not None and _position_in_ranges(production_position, _representation_ranges(text, suppression_rules, operation_signals, quoted_ranges)[0]):
        production_position = None
    production_transition = transition_required and production_position is not None
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
    if suppressed_signal_count:
        reasons.append(f"NEGATIVE_ROUTING_SIGNALS_SUPPRESSED:{suppressed_signal_count}")
    if representation_only:
        reasons.append("REPRESENTATION_ONLY_CONTEXT_SUPPRESSED_DOMAIN_EXECUTION")

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
