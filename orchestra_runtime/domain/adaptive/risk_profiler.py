"""Pure, deterministic AQ-2 adaptive risk profiling rules."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .assurance import validate_development_mode


AQ2_RISK_PROFILER_SCHEMA_VERSION = "orchestra.adaptive-risk-profiler.v1"

BASE_QUALITY_DIMENSIONS = (
    "FUNCTIONAL_SUITABILITY",
    "PERFORMANCE_EFFICIENCY",
    "COMPATIBILITY",
    "INTERACTION_CAPABILITY",
    "RELIABILITY",
    "SECURITY",
    "MAINTAINABILITY",
    "FLEXIBILITY",
    "SAFETY",
)

ORCHESTRA_OVERLAYS = (
    "PROVENANCE",
    "AUTHORITY_TRUST",
    "PRIVACY",
    "TENANT_WORKSPACE_ISOLATION",
    "DATA_OWNERSHIP",
    "CONCURRENCY",
    "STATE_TRANSITIONS",
    "RETRY_IDEMPOTENCY",
    "RECOVERY_ROLLBACK",
    "EXTERNAL_INPUT",
    "EXTERNAL_DEPENDENCY",
    "MIGRATION",
    "DESTRUCTIVE_LIFECYCLE",
    "HUMAN_AUTHORITY",
    "OBSERVABILITY",
)

QUALITY_DIMENSIONS = BASE_QUALITY_DIMENSIONS + ORCHESTRA_OVERLAYS

RISK_CHARACTERISTICS = (
    "AUTHENTICATION",
    "AUTHORIZATION",
    "PRIVILEGE_MUTATION",
    "MULTI_TENANT",
    "MULTI_ACTOR",
    "CONCURRENCY",
    "AGGREGATE_INVARIANT",
    "STATE_MACHINE",
    "TRANSACTION",
    "RETRY_IDEMPOTENCY",
    "RECOVERY_ROLLBACK",
    "DELETION",
    "EXTERNAL_INPUT",
    "EXTERNAL_PROVIDER",
    "PROVENANCE",
    "MIGRATION",
    "RESOURCE_PRESSURE",
    "UI_ACCESSIBILITY",
    "PUBLICATION",
    "HUMAN_DECISION_AUTHORITY",
)

INVARIANT_EXAMPLES = (
    "TENANT_MUST_RETAIN_ACTIVE_ADMIN",
    "CLIENT_MUST_NOT_AUTHOR_AUTHORITATIVE_PROVENANCE",
    "TENANT_ADMIN_MUST_NOT_GAIN_GLOBAL_AUTHORITY",
    "FAILED_VALIDATION_MUST_NOT_BECOME_PASS",
    "CROSS_TENANT_GUESS_MUST_NOT_DISCLOSE_RESOURCE",
)

SPECIALIST_ORDER = (
    "the-steward",
    "the-governor",
    "clockwork",
    "cloak",
    "cipher",
    "chronicler",
    "scribe",
    "overseer",
    "arbiter",
    "dagger",
)

ASSURANCE_ORDER = (
    "DOCUMENTATION_RECONCILIATION",
    "ARCHITECTURE_BOUNDARY",
    "FUNCTIONAL_ASSURANCE",
    "PERFORMANCE_ASSURANCE",
    "COMPATIBILITY_ASSURANCE",
    "INTERACTION_ASSURANCE",
    "RELIABILITY_ASSURANCE",
    "SECURITY_ASSURANCE",
    "MAINTAINABILITY_ASSURANCE",
    "FLEXIBILITY_ASSURANCE",
    "SAFETY_ASSURANCE",
    "PROVENANCE_ASSURANCE",
    "AUTHORITY_TRUST_ASSURANCE",
    "PRIVACY_ASSURANCE",
    "TENANT_ISOLATION_ASSURANCE",
    "DATA_OWNERSHIP_ASSURANCE",
    "CONCURRENCY_ASSURANCE",
    "STATE_TRANSITION_ASSURANCE",
    "RETRY_IDEMPOTENCY_ASSURANCE",
    "RECOVERY_ROLLBACK_ASSURANCE",
    "EXTERNAL_INPUT_ASSURANCE",
    "EXTERNAL_PROVIDER_ASSURANCE",
    "MIGRATION_ASSURANCE",
    "DESTRUCTIVE_LIFECYCLE_ASSURANCE",
    "HUMAN_AUTHORITY_ASSURANCE",
    "OBSERVABILITY_ASSURANCE",
    "AUTHENTICATION_ASSURANCE",
    "AUTHORIZATION_ASSURANCE",
    "PRIVILEGE_BOUNDARY_ASSURANCE",
    "MULTI_ACTOR_ASSURANCE",
    "AGGREGATE_INVARIANT_ASSURANCE",
    "TRANSACTION_ASSURANCE",
    "DELETION_ASSURANCE",
    "PUBLICATION_ASSURANCE",
    "INVARIANT_PRESERVATION_ASSURANCE",
    "ADVERSARIAL_ASSURANCE",
    "INDEPENDENT_QA",
)

_QUALITY_ASSURANCE = {
    "FUNCTIONAL_SUITABILITY": "FUNCTIONAL_ASSURANCE",
    "PERFORMANCE_EFFICIENCY": "PERFORMANCE_ASSURANCE",
    "COMPATIBILITY": "COMPATIBILITY_ASSURANCE",
    "INTERACTION_CAPABILITY": "INTERACTION_ASSURANCE",
    "RELIABILITY": "RELIABILITY_ASSURANCE",
    "SECURITY": "SECURITY_ASSURANCE",
    "MAINTAINABILITY": "MAINTAINABILITY_ASSURANCE",
    "FLEXIBILITY": "FLEXIBILITY_ASSURANCE",
    "SAFETY": "SAFETY_ASSURANCE",
    "PROVENANCE": "PROVENANCE_ASSURANCE",
    "AUTHORITY_TRUST": "AUTHORITY_TRUST_ASSURANCE",
    "PRIVACY": "PRIVACY_ASSURANCE",
    "TENANT_WORKSPACE_ISOLATION": "TENANT_ISOLATION_ASSURANCE",
    "DATA_OWNERSHIP": "DATA_OWNERSHIP_ASSURANCE",
    "CONCURRENCY": "CONCURRENCY_ASSURANCE",
    "STATE_TRANSITIONS": "STATE_TRANSITION_ASSURANCE",
    "RETRY_IDEMPOTENCY": "RETRY_IDEMPOTENCY_ASSURANCE",
    "RECOVERY_ROLLBACK": "RECOVERY_ROLLBACK_ASSURANCE",
    "EXTERNAL_INPUT": "EXTERNAL_INPUT_ASSURANCE",
    "EXTERNAL_DEPENDENCY": "EXTERNAL_PROVIDER_ASSURANCE",
    "MIGRATION": "MIGRATION_ASSURANCE",
    "DESTRUCTIVE_LIFECYCLE": "DESTRUCTIVE_LIFECYCLE_ASSURANCE",
    "HUMAN_AUTHORITY": "HUMAN_AUTHORITY_ASSURANCE",
    "OBSERVABILITY": "OBSERVABILITY_ASSURANCE",
}

# The tuple values are (assurance classes, specialist slugs, Dagger trigger).
RISK_RULES = {
    "AUTHENTICATION": (("AUTHENTICATION_ASSURANCE",), ("cipher",), False),
    "AUTHORIZATION": (("AUTHORIZATION_ASSURANCE",), ("cipher",), False),
    "PRIVILEGE_MUTATION": (("PRIVILEGE_BOUNDARY_ASSURANCE",), ("cipher",), True),
    "MULTI_TENANT": (("TENANT_ISOLATION_ASSURANCE",), ("cipher",), True),
    "MULTI_ACTOR": (("MULTI_ACTOR_ASSURANCE",), ("clockwork",), True),
    "CONCURRENCY": (("CONCURRENCY_ASSURANCE",), ("chronicler",), True),
    "AGGREGATE_INVARIANT": (("AGGREGATE_INVARIANT_ASSURANCE",), ("chronicler",), True),
    "STATE_MACHINE": (("STATE_TRANSITION_ASSURANCE",), ("clockwork",), False),
    "TRANSACTION": (("TRANSACTION_ASSURANCE",), ("chronicler",), False),
    "RETRY_IDEMPOTENCY": (("RETRY_IDEMPOTENCY_ASSURANCE",), ("chronicler",), True),
    "RECOVERY_ROLLBACK": (("RECOVERY_ROLLBACK_ASSURANCE",), ("chronicler",), True),
    "DELETION": (("DELETION_ASSURANCE",), ("chronicler",), True),
    "EXTERNAL_INPUT": (("EXTERNAL_INPUT_ASSURANCE",), ("cipher",), False),
    "EXTERNAL_PROVIDER": (("EXTERNAL_PROVIDER_ASSURANCE",), ("clockwork",), False),
    "PROVENANCE": (("PROVENANCE_ASSURANCE",), ("cipher",), True),
    "MIGRATION": (("MIGRATION_ASSURANCE",), ("chronicler",), False),
    "RESOURCE_PRESSURE": (("RELIABILITY_ASSURANCE",), ("clockwork",), True),
    "UI_ACCESSIBILITY": (("INTERACTION_ASSURANCE",), ("cloak",), False),
    "PUBLICATION": (("PUBLICATION_ASSURANCE",), ("scribe",), False),
    "HUMAN_DECISION_AUTHORITY": (("HUMAN_AUTHORITY_ASSURANCE",), ("arbiter",), False),
}

INVARIANT_RULES = {
    "TENANT_MUST_RETAIN_ACTIVE_ADMIN": (("TENANT_ISOLATION_ASSURANCE",), ("cipher", "chronicler"), True),
    "CLIENT_MUST_NOT_AUTHOR_AUTHORITATIVE_PROVENANCE": (("PROVENANCE_ASSURANCE",), ("cipher",), True),
    "TENANT_ADMIN_MUST_NOT_GAIN_GLOBAL_AUTHORITY": (("AUTHORITY_TRUST_ASSURANCE",), ("cipher",), True),
    "FAILED_VALIDATION_MUST_NOT_BECOME_PASS": (("RELIABILITY_ASSURANCE",), ("overseer",), False),
    "CROSS_TENANT_GUESS_MUST_NOT_DISCLOSE_RESOURCE": (("TENANT_ISOLATION_ASSURANCE",), ("cipher",), True),
}

_SECURITY_WORDS = (
    "authentication",
    "authorization",
    "privilege",
    "tenant",
    "security",
    "secret",
    "credential",
    "rbac",
    "permission",
    "access control",
    "role assignment",
    "token",
    "session validation",
)
_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_:-]{0,127}$")


def _text(value: object, field_name: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return normalized


def _values(value: object, field_name: str, *, maximum: int = 64) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        raw_values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if len(raw_values) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} items")
    normalized = tuple(sorted({str(item).strip().upper() for item in raw_values}))
    if any(not item for item in normalized):
        raise ValueError(f"{field_name} must not contain empty values")
    return normalized


def _identifiers(value: object, field_name: str) -> tuple[str, ...]:
    normalized = _values(value, field_name)
    invalid = [item for item in normalized if _IDENTIFIER_RE.fullmatch(item) is None]
    if invalid:
        raise ValueError(f"{field_name} contains unsupported identifiers: {', '.join(invalid)}")
    return normalized


def _paths(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise TypeError("changed_paths must be an iterable of strings")
    try:
        raw_paths = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError("changed_paths must be an iterable of strings") from exc
    if len(raw_paths) > 128:
        raise ValueError("changed_paths exceeds 128 items")
    normalized = {
        "/".join(part for part in str(item).strip().replace("\\", "/").split("/") if part).casefold()
        for item in raw_paths
    }
    if any(not item for item in normalized):
        raise ValueError("changed_paths must not contain empty values")
    return tuple(sorted(normalized))


def _authority_boundary(value: object) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        flattened: list[str] = []
        for key in sorted(value, key=lambda item: str(item).casefold()):
            entries = value[key]
            if isinstance(entries, str):
                entries = (entries,)
            for entry in _values(entries, "authority_boundary"):
                flattened.append(f"{str(key).strip().upper()}:{entry}")
        value = flattened
    normalized = _values(value, "authority_boundary")
    if not normalized:
        raise ValueError("authority_boundary must be explicit and non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class RiskProfileInput:
    """The observations and explicit boundaries supplied to the profiler."""

    development_mode: str
    material_behavior: str
    authority_boundary: tuple[str, ...] | Iterable[str]
    changed_domains: tuple[str, ...] | Iterable[str] = ()
    changed_paths: tuple[str, ...] | Iterable[str] = ()
    quality_dimensions: tuple[str, ...] | Iterable[str] = ()
    risk_characteristics: tuple[str, ...] | Iterable[str] = ()
    invariants: tuple[str, ...] | Iterable[str] = ()
    protected_gates: tuple[str, ...] | Iterable[str] = ()

    def __post_init__(self) -> None:
        mode = validate_development_mode(str(self.development_mode).strip().upper())
        quality = _values(self.quality_dimensions, "quality_dimensions")
        unknown_quality = sorted(set(quality) - set(QUALITY_DIMENSIONS))
        if unknown_quality:
            raise ValueError("unsupported quality dimensions: " + ", ".join(unknown_quality))
        risks = _values(self.risk_characteristics, "risk_characteristics")
        unknown_risks = sorted(set(risks) - set(RISK_CHARACTERISTICS))
        if unknown_risks:
            raise ValueError("unsupported risk characteristics: " + ", ".join(unknown_risks))
        object.__setattr__(self, "development_mode", mode)
        object.__setattr__(self, "material_behavior", _text(self.material_behavior, "material_behavior", maximum=4096))
        object.__setattr__(self, "authority_boundary", _authority_boundary(self.authority_boundary))
        object.__setattr__(self, "changed_domains", _values(self.changed_domains, "changed_domains"))
        object.__setattr__(self, "changed_paths", _paths(self.changed_paths))
        object.__setattr__(self, "quality_dimensions", quality)
        object.__setattr__(self, "risk_characteristics", risks)
        object.__setattr__(self, "invariants", _identifiers(self.invariants, "invariants"))
        object.__setattr__(self, "protected_gates", _identifiers(self.protected_gates, "protected_gates"))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RiskProfileInput":
        if not isinstance(data, Mapping):
            raise TypeError("risk profile input must be a mapping")
        behavior = data.get("material_behavior", data.get("material_behavioral_description"))
        boundary = data.get("authority_boundary", data.get("explicit_authority_boundary"))
        return cls(
            development_mode=data.get("development_mode", ""),
            material_behavior=behavior,
            authority_boundary=boundary,
            changed_domains=data.get("changed_domains", ()),
            changed_paths=data.get("changed_paths", ()),
            quality_dimensions=data.get("quality_dimensions", ()),
            risk_characteristics=data.get("risk_characteristics", data.get("risks", ())),
            invariants=data.get("invariants", ()),
            protected_gates=data.get("protected_gates", ()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "development_mode": self.development_mode,
            "changed_domains": list(self.changed_domains),
            "changed_paths": list(self.changed_paths),
            "material_behavior": self.material_behavior,
            "quality_dimensions": list(self.quality_dimensions),
            "risk_characteristics": list(self.risk_characteristics),
            "invariants": list(self.invariants),
            "protected_gates": list(self.protected_gates),
            "authority_boundary": list(self.authority_boundary),
        }


@dataclass(frozen=True, slots=True)
class DaggerDecision:
    required: bool
    triggered_by: tuple[str, ...]
    execution_authorized: bool = False
    reason: str = "No material Dagger trigger."

    def __post_init__(self) -> None:
        if type(self.required) is not bool or type(self.execution_authorized) is not bool:
            raise TypeError("Dagger decision flags must be exact booleans")
        if self.execution_authorized:
            raise ValueError("AQ2 profiling cannot authorize Dagger execution")
        object.__setattr__(self, "triggered_by", tuple(sorted(set(self.triggered_by))))
        if self.required != bool(self.triggered_by):
            raise ValueError("Dagger requirement must match its trigger set")
        object.__setattr__(
            self,
            "reason",
            _text(self.reason, "Dagger decision reason", maximum=512),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "triggered_by": list(self.triggered_by),
            "execution_authorized": self.execution_authorized,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class AdaptiveRiskProfile:
    """Deterministic AQ-2 output suitable for a later routing receipt."""

    normalized_risk_fingerprint: str
    development_mode: str
    changed_domains: tuple[str, ...]
    changed_paths: tuple[str, ...]
    material_behavior: str
    quality_dimensions: tuple[str, ...]
    risk_characteristics: tuple[str, ...]
    invariants: tuple[str, ...]
    required_assurance_classes: tuple[str, ...]
    recommended_specialists: tuple[str, ...]
    dagger_decision: DaggerDecision
    protected_gates: tuple[str, ...]
    authority_boundary: tuple[str, ...]
    decision_reasons: tuple[str, ...]
    authority_expansion: bool = False
    provider_activation: bool = False
    production_action: bool = False
    schema_version: str = AQ2_RISK_PROFILER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AQ2_RISK_PROFILER_SCHEMA_VERSION:
            raise ValueError("unsupported AQ2 risk profiler schema")
        for field_name in ("authority_expansion", "provider_activation", "production_action"):
            if getattr(self, field_name) is not False:
                raise ValueError(f"AQ2 profiler cannot set {field_name}")
        if not isinstance(self.dagger_decision, DaggerDecision):
            raise TypeError("dagger_decision must be a DaggerDecision")
        object.__setattr__(self, "required_assurance_classes", tuple(self.required_assurance_classes))
        object.__setattr__(self, "recommended_specialists", tuple(self.recommended_specialists))
        object.__setattr__(self, "protected_gates", tuple(self.protected_gates))
        object.__setattr__(self, "decision_reasons", tuple(self.decision_reasons))

    @property
    def risk_fingerprint(self) -> str:
        return self.normalized_risk_fingerprint

    @property
    def specialist_topology(self) -> tuple[str, ...]:
        return self.recommended_specialists

    @property
    def recommended_specialist_topology(self) -> tuple[str, ...]:
        return self.recommended_specialists

    @property
    def dagger_required(self) -> bool:
        return self.dagger_decision.required

    @property
    def explanation(self) -> tuple[str, ...]:
        return self.decision_reasons

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "normalized_risk_fingerprint": self.normalized_risk_fingerprint,
            "development_mode": self.development_mode,
            "changed_domains": list(self.changed_domains),
            "changed_paths": list(self.changed_paths),
            "material_behavior": self.material_behavior,
            "quality_dimensions": list(self.quality_dimensions),
            "risk_characteristics": list(self.risk_characteristics),
            "invariants": list(self.invariants),
            "required_assurance_classes": list(self.required_assurance_classes),
            "recommended_specialists": list(self.recommended_specialists),
            "dagger_decision": self.dagger_decision.to_dict(),
            "protected_gates": list(self.protected_gates),
            "authority_boundary": list(self.authority_boundary),
            "decision_reasons": list(self.decision_reasons),
            "authority_expansion": self.authority_expansion,
            "provider_activation": self.provider_activation,
            "production_action": self.production_action,
        }


def _ordered(values: Iterable[str], order: tuple[str, ...]) -> tuple[str, ...]:
    present = set(values)
    return tuple(item for item in order if item in present)


def _is_documentation_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.startswith("docs/") or name.endswith((".md", ".mdx", ".rst")) or name in {
        "readme",
        "readme.json",
        "changelog.md",
    }


def _is_documentation_observation(request: RiskProfileInput) -> bool:
    domains = set(request.changed_domains)
    return "DOCUMENTATION" in domains or "DOCS" in domains or any(
        _is_documentation_path(path) for path in request.changed_paths
    )


def _is_architecture_observation(request: RiskProfileInput) -> bool:
    description = request.material_behavior.casefold()
    return "architecture" in description and len(request.changed_domains) > 1 or "cross-domain" in description


def _security_critical_without_risk(request: RiskProfileInput) -> bool:
    if request.risk_characteristics or request.invariants:
        return False
    description = request.material_behavior.casefold()
    return "SECURITY" in request.quality_dimensions or any(word in description for word in _SECURITY_WORDS)


def _fingerprint(request: RiskProfileInput) -> str:
    payload = json.dumps(request.to_dict(), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def profile_risk(
    request: RiskProfileInput | Mapping[str, Any] | None = None,
    *,
    development_mode: str | None = None,
    material_behavior: str | None = None,
    material_behavioral_description: str | None = None,
    authority_boundary: Iterable[str] | Mapping[str, Any] | None = None,
    changed_domains: Iterable[str] = (),
    changed_paths: Iterable[str] = (),
    quality_dimensions: Iterable[str] = (),
    risk_characteristics: Iterable[str] = (),
    invariants: Iterable[str] = (),
    protected_gates: Iterable[str] = (),
) -> AdaptiveRiskProfile:
    """Profile assurance needs without executing routing or external actions."""

    if request is None:
        behavior = material_behavior if material_behavior is not None else material_behavioral_description
        request = RiskProfileInput(
            development_mode=development_mode,
            material_behavior=behavior,
            authority_boundary=authority_boundary,
            changed_domains=changed_domains,
            changed_paths=changed_paths,
            quality_dimensions=quality_dimensions,
            risk_characteristics=risk_characteristics,
            invariants=invariants,
            protected_gates=protected_gates,
        )
    elif isinstance(request, Mapping):
        request = RiskProfileInput.from_mapping(request)
    elif not isinstance(request, RiskProfileInput):
        raise TypeError("request must be RiskProfileInput or a mapping")

    if _security_critical_without_risk(request):
        raise ValueError("security-critical behavior requires explicit material risk characteristics")

    assurances: set[str] = {"INDEPENDENT_QA"}
    specialists: set[str] = {"overseer"}
    reasons = [
        "RISK_CHARACTERISTICS_AND_INVARIANTS_PRIMARY",
        "CHANGED_PATHS_AND_DOMAINS_OBSERVATIONAL_ONLY",
        "DEVELOPMENT_MODE_CONTEXT_ONLY",
        "OVERSEER_REQUIRED_FOR_INDEPENDENT_QA",
        "AUTHORITY_BOUNDARY_PRESERVED",
    ]
    dagger_triggers: set[str] = set()

    for dimension in request.quality_dimensions:
        assurances.add(_QUALITY_ASSURANCE[dimension])

    for risk in request.risk_characteristics:
        risk_assurances, risk_specialists, dagger = RISK_RULES[risk]
        assurances.update(risk_assurances)
        specialists.update(risk_specialists)
        reasons.append(f"RISK_{risk}_MAPPED_EXPLICITLY")
        if dagger:
            dagger_triggers.add(risk)

    if request.invariants:
        assurances.add("INVARIANT_PRESERVATION_ASSURANCE")
        reasons.append("INVARIANTS_ARE_MATERIAL_ACCEPTANCE_CONDITIONS")
    for invariant in request.invariants:
        rule = INVARIANT_RULES.get(invariant)
        if rule is None:
            continue
        invariant_assurances, invariant_specialists, dagger = rule
        assurances.update(invariant_assurances)
        specialists.update(invariant_specialists)
        if dagger:
            dagger_triggers.add("INVARIANT:" + invariant)

    if _is_documentation_observation(request):
        assurances.add("DOCUMENTATION_RECONCILIATION")
        specialists.add("scribe")
        reasons.append("DOCUMENTATION_OBSERVATION_REQUIRES_RECONCILIATION_ASSURANCE")

    if _is_architecture_observation(request):
        assurances.add("ARCHITECTURE_BOUNDARY")
        specialists.add("clockwork")
        reasons.append("CROSS_DOMAIN_ARCHITECTURE_REQUIRES_BOUNDARY_ASSURANCE")

    if "HUMAN_DECISION_AUTHORITY" in request.risk_characteristics:
        reasons.append("HUMAN_DECISION_AUTHORITY_GATE_IS_NONWAIVABLE")
    protected_gates = set(request.protected_gates)
    if "HUMAN_DECISION_AUTHORITY" in request.risk_characteristics:
        protected_gates.add("HUMAN_DECISION_AUTHORITY")
    if protected_gates:
        reasons.append("PROTECTED_GATES_ARE_NONWAIVABLE")

    if "EXTERNAL_PROVIDER" in request.risk_characteristics:
        reasons.append("EXTERNAL_PROVIDER_CLASSIFIED_WITHOUT_PROVIDER_ACTIVATION")
    if dagger_triggers:
        assurances.add("ADVERSARIAL_ASSURANCE")
        specialists.add("dagger")
        reasons.append("DAGGER_REQUIRED_FOR_MATERIAL_RISK_TRIGGERS")
    else:
        reasons.append("NO_DAGGER_TRIGGERING_MATERIAL_RISK")

    dagger = DaggerDecision(
        required=bool(dagger_triggers),
        triggered_by=tuple(sorted(dagger_triggers)),
        reason=(
            "Dagger recommendation is risk-triggered and execution remains unauthorized."
            if dagger_triggers
            else "No material Dagger-triggering risk remains in the normalized profile."
        ),
    )
    return AdaptiveRiskProfile(
        normalized_risk_fingerprint=_fingerprint(request),
        development_mode=request.development_mode,
        changed_domains=request.changed_domains,
        changed_paths=request.changed_paths,
        material_behavior=request.material_behavior,
        quality_dimensions=request.quality_dimensions,
        risk_characteristics=request.risk_characteristics,
        invariants=request.invariants,
        required_assurance_classes=_ordered(assurances, ASSURANCE_ORDER),
        recommended_specialists=_ordered(specialists, SPECIALIST_ORDER),
        dagger_decision=dagger,
        protected_gates=tuple(sorted(protected_gates)),
        authority_boundary=request.authority_boundary,
        decision_reasons=tuple(reasons),
    )


def profile_adaptive_risk(
    request: RiskProfileInput | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> AdaptiveRiskProfile:
    """Named alias for callers using the full AQ-2 terminology."""

    return profile_risk(request, **kwargs)


RiskProfilerInput = RiskProfileInput
AdaptiveRiskProfilerInput = RiskProfileInput


__all__ = [
    "ASSURANCE_ORDER",
    "AQ2_RISK_PROFILER_SCHEMA_VERSION",
    "AdaptiveRiskProfile",
    "AdaptiveRiskProfilerInput",
    "BASE_QUALITY_DIMENSIONS",
    "DaggerDecision",
    "INVARIANT_EXAMPLES",
    "INVARIANT_RULES",
    "ORCHESTRA_OVERLAYS",
    "QUALITY_DIMENSIONS",
    "RISK_CHARACTERISTICS",
    "RISK_RULES",
    "RiskProfileInput",
    "RiskProfilerInput",
    "SPECIALIST_ORDER",
    "profile_adaptive_risk",
    "profile_risk",
]
