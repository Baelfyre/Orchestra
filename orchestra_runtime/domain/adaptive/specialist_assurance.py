"""Pure AQ-3 specialist-assurance and progression contracts.

AQ-3 consumes the qualified AQ-2 profile.  It records routing and evidence
requirements without dispatching specialists, executing Dagger, or changing
authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .assurance import COMPLETION_STATES, DEVELOPMENT_MODES, SOURCE_TRUTH_LABELS
from .risk_profiler import (
    ASSURANCE_ORDER,
    AdaptiveRiskProfile,
    DaggerDecision,
    QUALITY_DIMENSIONS,
    RISK_CHARACTERISTICS,
    SPECIALIST_ORDER,
)


AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION = "orchestra.specialist-assurance-contract.v1"
AQ3_AUTHORITY_RULE = "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION"
DEFAULT_NEXT_TRANSITION_TARGET = "INDEPENDENT_OVERSEER_REVIEW"

FAIL_INDEPENDENT_ASSURANCE_REQUIRED = "FAIL_INDEPENDENT_ASSURANCE_REQUIRED"
FAIL_REQUIRED_DAGGER_OMITTED = "FAIL_REQUIRED_DAGGER_OMITTED"
FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY = (
    "FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY"
)
FAIL_REQUIRED_ASSURANCE_MISSING = "FAIL_REQUIRED_ASSURANCE_MISSING"
FAIL_SOURCE_TRUTH_VIOLATION = "FAIL_SOURCE_TRUTH_VIOLATION"
FAIL_AUTHORITY_SCOPE_VIOLATION = "FAIL_AUTHORITY_SCOPE_VIOLATION"
REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS = "REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS"
FAIL_STALE_EVIDENCE = "FAIL_STALE_EVIDENCE"
FAIL_WRONG_SOURCE_EVIDENCE = "FAIL_WRONG_SOURCE_EVIDENCE"
FAIL_WEAKER_EVIDENCE = "FAIL_WEAKER_EVIDENCE"
FAIL_DUPLICATE_EVIDENCE_IDENTITY = "FAIL_DUPLICATE_EVIDENCE_IDENTITY"
FAIL_PROTECTED_GATE_UNSATISFIED = "FAIL_PROTECTED_GATE_UNSATISFIED"
FAIL_AQ1_COMPLETION_SCOPE = "FAIL_AQ1_COMPLETION_SCOPE"
FAIL_EVIDENCE_BINDING = "FAIL_EVIDENCE_BINDING"
FAIL_EVIDENCE_PROVENANCE = "FAIL_EVIDENCE_PROVENANCE"

FAILURE_CODES = (
    FAIL_INDEPENDENT_ASSURANCE_REQUIRED,
    FAIL_REQUIRED_DAGGER_OMITTED,
    FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY,
    FAIL_REQUIRED_ASSURANCE_MISSING,
    FAIL_SOURCE_TRUTH_VIOLATION,
    FAIL_AUTHORITY_SCOPE_VIOLATION,
    REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS,
    FAIL_STALE_EVIDENCE,
    FAIL_WRONG_SOURCE_EVIDENCE,
    FAIL_WEAKER_EVIDENCE,
    FAIL_DUPLICATE_EVIDENCE_IDENTITY,
    FAIL_PROTECTED_GATE_UNSATISFIED,
    FAIL_AQ1_COMPLETION_SCOPE,
    FAIL_EVIDENCE_BINDING,
    FAIL_EVIDENCE_PROVENANCE,
)

CANONICAL_SPECIALIST_ORDER = SPECIALIST_ORDER + (
    "the-tuner",
    "weaver",
    "ponytail",
    "conductor",
)

REQUIRED_RECEIPT_FIELDS = (
    "source_identities",
    "development_mode",
    "changed_domains",
    "quality_dimensions",
    "risk_characteristics",
    "invariants",
    "selected_specialists",
    "required_assurance",
    "dagger_decision",
    "protected_gates",
    "next_transition_target",
    "authority_boundary",
    "risk_fingerprint",
)

EVIDENCE_STATUSES = ("SATISFIED", "MISSING", "STALE", "WRONG_SOURCE", "WEAKER", "UNVERIFIED")
EVIDENCE_KINDS = (
    "IMPLEMENTATION",
    "TEST",
    "CONTRACT",
    "CI",
    "STATIC",
    "REVIEW",
    "DAGGER_ADVISORY",
    "SOURCE",
)
EVIDENCE_SCOPES = (
    "IMPLEMENTATION",
    "UNIT",
    "CONTRACT",
    "INTEGRATION",
    "RUNTIME",
    "SECURITY",
    "CONCURRENCY",
    "ADVERSARIAL",
    "AGGREGATE",
    "ROW",
    "ROW_VERSION",
    "CI",
    "DOCUMENTATION",
    "SOURCE",
)
PROVENANCE_QUALIFICATIONS = ("AUTHORITATIVE", "SELF_ASSERTED", "UNQUALIFIED")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_:-]{0,127}$")
_SPECIAL_ASSURANCE_SCOPES = {
    "SECURITY_ASSURANCE": {"SECURITY"},
    "CONCURRENCY_ASSURANCE": {"CONCURRENCY"},
    "AGGREGATE_INVARIANT_ASSURANCE": {"AGGREGATE"},
    "ADVERSARIAL_ASSURANCE": {"ADVERSARIAL"},
}
_CLAIM_EVIDENCE_SCOPES = {
    "DOMAIN_IMPLEMENTED": {"IMPLEMENTATION"},
    "APPLICATION_INTEGRATED": {"INTEGRATION"},
    "API_INTEGRATED": {"INTEGRATION"},
    "UI_INTEGRATED": {"INTEGRATION"},
    "UNIT_VERIFIED": {"UNIT"},
    "CONTRACT_VERIFIED": {"CONTRACT"},
    "INTEGRATION_VERIFIED": {"INTEGRATION"},
    "RUNTIME_VERIFIED": {"RUNTIME"},
    "SECURITY_VERIFIED": {"SECURITY"},
    "ADVERSARIALLY_VERIFIED": {"ADVERSARIAL"},
}


class SpecialistAssuranceContractError(ValueError):
    """A deterministic, machine-readable AQ-3 contract failure."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)


def _text(value: object, field_name: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return normalized


def _one_of(value: object, choices: Iterable[str], field_name: str) -> str:
    normalized = _text(value, field_name)
    if normalized not in choices:
        raise ValueError(f"{field_name} is unsupported: {normalized}")
    return normalized


def _values(value: object, field_name: str, *, maximum: int = 64) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if len(raw) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} items")
    normalized = tuple(_text(item, field_name) for item in raw)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return normalized


def _ordered(value: object, field_name: str, order: tuple[str, ...]) -> tuple[str, ...]:
    values = _values(value, field_name, maximum=len(order))
    unknown = sorted(set(values) - set(order))
    if unknown:
        raise ValueError(f"{field_name} contains unsupported values: {', '.join(unknown)}")
    present = set(values)
    return tuple(item for item in order if item in present)


def _evidence_ids(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if len(raw) > 128:
        raise ValueError(f"{field_name} exceeds 128 items")
    return tuple(_text(item, field_name) for item in raw)


def _identifiers(value: object, field_name: str) -> tuple[str, ...]:
    values = tuple(item.upper() for item in _values(value, field_name))
    invalid = [item for item in values if _IDENTIFIER_RE.fullmatch(item) is None]
    if invalid:
        raise ValueError(f"{field_name} contains unsupported identifiers: {', '.join(invalid)}")
    return tuple(sorted(set(values)))


def _sha256(value: object, field_name: str) -> str:
    normalized = _text(value, field_name, maximum=64).casefold()
    if _SHA256_RE.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 fingerprint")
    return normalized


def _append_unique(values: list[str], *codes: str) -> None:
    for code in codes:
        if code not in values:
            values.append(code)


@dataclass(frozen=True, slots=True)
class SpecialistAssuranceReceipt:
    """Structured Conductor output bound to one normalized AQ-2 profile."""

    source_identities: tuple[str, ...]
    development_mode: str
    changed_domains: tuple[str, ...]
    quality_dimensions: tuple[str, ...]
    risk_characteristics: tuple[str, ...]
    invariants: tuple[str, ...]
    selected_specialists: tuple[str, ...]
    required_assurance: tuple[str, ...]
    dagger_decision: DaggerDecision
    protected_gates: tuple[str, ...]
    next_transition_target: str
    authority_boundary: tuple[str, ...]
    risk_fingerprint: str
    coordination_additions: tuple[str, ...] = ()
    assurance_additions: tuple[str, ...] = ()
    selected_by: str = "conductor"
    authority_expansion: bool = False
    provider_activation: bool = False
    production_action: bool = False
    schema_version: str = AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION:
            raise ValueError("unsupported AQ3 specialist assurance schema")
        if self.selected_by != "conductor":
            raise SpecialistAssuranceContractError(
                FAIL_AUTHORITY_SCOPE_VIOLATION,
                "only Conductor may emit an AQ-3 routing receipt",
            )
        if not isinstance(self.dagger_decision, DaggerDecision):
            raise TypeError("dagger_decision must be a DaggerDecision")
        if any(type(getattr(self, field)) is not bool for field in ("authority_expansion", "provider_activation", "production_action")):
            raise TypeError("AQ3 authority flags must be exact booleans")
        if self.authority_expansion or self.provider_activation or self.production_action:
            raise SpecialistAssuranceContractError(
                FAIL_AUTHORITY_SCOPE_VIOLATION,
                "AQ-3 cannot expand authority or activate providers/production",
            )

        sources = tuple(sorted(_values(self.source_identities, "source_identities", maximum=32)))
        if not sources:
            raise ValueError("source_identities must be explicit and non-empty")
        object.__setattr__(self, "source_identities", sources)
        object.__setattr__(self, "development_mode", _one_of(self.development_mode, DEVELOPMENT_MODES, "development_mode"))
        object.__setattr__(self, "changed_domains", tuple(sorted(_values(self.changed_domains, "changed_domains"))))
        object.__setattr__(self, "quality_dimensions", _ordered(self.quality_dimensions, "quality_dimensions", QUALITY_DIMENSIONS))
        object.__setattr__(self, "risk_characteristics", _ordered(self.risk_characteristics, "risk_characteristics", RISK_CHARACTERISTICS))
        object.__setattr__(self, "invariants", _identifiers(self.invariants, "invariants"))
        object.__setattr__(self, "protected_gates", _identifiers(self.protected_gates, "protected_gates"))
        selected = _ordered(self.selected_specialists, "selected_specialists", CANONICAL_SPECIALIST_ORDER)
        if "overseer" not in selected:
            raise SpecialistAssuranceContractError(
                FAIL_REQUIRED_ASSURANCE_MISSING,
                "Overseer is mandatory for independent QA",
            )
        object.__setattr__(self, "selected_specialists", selected)
        required = _ordered(self.required_assurance, "required_assurance", ASSURANCE_ORDER)
        if "INDEPENDENT_QA" not in required:
            raise SpecialistAssuranceContractError(
                FAIL_REQUIRED_ASSURANCE_MISSING,
                "INDEPENDENT_QA is mandatory",
            )
        object.__setattr__(self, "required_assurance", required)
        additions = _ordered(self.coordination_additions, "coordination_additions", CANONICAL_SPECIALIST_ORDER)
        if not set(additions).issubset(set(selected)):
            raise ValueError("coordination additions must be selected explicitly")
        object.__setattr__(self, "coordination_additions", additions)
        assurance_additions = _ordered(self.assurance_additions, "assurance_additions", ASSURANCE_ORDER)
        if not set(assurance_additions).issubset(set(required)):
            raise ValueError("assurance additions must be required explicitly")
        object.__setattr__(self, "assurance_additions", assurance_additions)
        if self.dagger_decision.required and "dagger" not in selected:
            raise SpecialistAssuranceContractError(FAIL_REQUIRED_DAGGER_OMITTED)
        if not self.dagger_decision.required and "dagger" in selected:
            raise SpecialistAssuranceContractError(FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY)
        object.__setattr__(self, "next_transition_target", _text(self.next_transition_target, "next_transition_target"))
        boundary = tuple(sorted(item.upper() for item in _values(self.authority_boundary, "authority_boundary", maximum=32)))
        if not boundary:
            raise ValueError("authority_boundary must be explicit and non-empty")
        object.__setattr__(self, "authority_boundary", boundary)
        object.__setattr__(self, "risk_fingerprint", _sha256(self.risk_fingerprint, "risk_fingerprint"))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SpecialistAssuranceReceipt":
        if not isinstance(data, Mapping):
            raise TypeError("AQ3 receipt must be a mapping")
        allowed_fields = {
            "schema_version",
            "source_identities",
            "development_mode",
            "changed_domains",
            "quality_dimensions",
            "risk_characteristics",
            "invariants",
            "selected_specialists",
            "required_assurance",
            "dagger_decision",
            "protected_gates",
            "next_transition_target",
            "authority_boundary",
            "risk_fingerprint",
            "coordination_additions",
            "assurance_additions",
            "selected_by",
            "authority_expansion",
            "provider_activation",
            "production_action",
        }
        unknown_fields = sorted(set(data) - allowed_fields)
        if unknown_fields:
            raise TypeError(f"unsupported AQ3 receipt fields: {', '.join(unknown_fields)}")
        dagger = data.get("dagger_decision")
        if not isinstance(dagger, Mapping):
            raise TypeError("dagger_decision must be a mapping")
        unknown_dagger_fields = sorted(
            set(dagger) - {"required", "triggered_by", "execution_authorized", "reason"}
        )
        if unknown_dagger_fields:
            raise TypeError(
                "unsupported Dagger decision fields: " + ", ".join(unknown_dagger_fields)
            )
        return cls(
            source_identities=tuple(data.get("source_identities", ())),
            development_mode=data.get("development_mode", ""),
            changed_domains=tuple(data.get("changed_domains", ())),
            quality_dimensions=tuple(data.get("quality_dimensions", ())),
            risk_characteristics=tuple(data.get("risk_characteristics", ())),
            invariants=tuple(data.get("invariants", ())),
            selected_specialists=tuple(data.get("selected_specialists", ())),
            required_assurance=tuple(data.get("required_assurance", ())),
            dagger_decision=DaggerDecision(
                required=dagger.get("required"),
                triggered_by=tuple(dagger.get("triggered_by", ())),
                execution_authorized=dagger.get("execution_authorized", False),
                reason=dagger.get("reason", "No material Dagger trigger."),
            ),
            protected_gates=tuple(data.get("protected_gates", ())),
            next_transition_target=data.get("next_transition_target", ""),
            authority_boundary=tuple(data.get("authority_boundary", ())),
            risk_fingerprint=data.get("risk_fingerprint", ""),
            coordination_additions=tuple(data.get("coordination_additions", ())),
            assurance_additions=tuple(data.get("assurance_additions", ())),
            selected_by=data.get("selected_by", "conductor"),
            authority_expansion=data.get("authority_expansion", False),
            provider_activation=data.get("provider_activation", False),
            production_action=data.get("production_action", False),
            schema_version=data.get("schema_version", AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_identities": list(self.source_identities),
            "development_mode": self.development_mode,
            "changed_domains": list(self.changed_domains),
            "quality_dimensions": list(self.quality_dimensions),
            "risk_characteristics": list(self.risk_characteristics),
            "invariants": list(self.invariants),
            "selected_specialists": list(self.selected_specialists),
            "required_assurance": list(self.required_assurance),
            "dagger_decision": self.dagger_decision.to_dict(),
            "protected_gates": list(self.protected_gates),
            "next_transition_target": self.next_transition_target,
            "authority_boundary": list(self.authority_boundary),
            "risk_fingerprint": self.risk_fingerprint,
            "coordination_additions": list(self.coordination_additions),
            "assurance_additions": list(self.assurance_additions),
            "selected_by": self.selected_by,
            "authority_expansion": self.authority_expansion,
            "provider_activation": self.provider_activation,
            "production_action": self.production_action,
        }

    @property
    def receipt_fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def build_routing_receipt(
    profile: AdaptiveRiskProfile,
    *,
    source_identities: Iterable[str],
    next_transition_target: str = DEFAULT_NEXT_TRANSITION_TARGET,
    coordination_additions: Iterable[str] = (),
    assurance_additions: Iterable[str] = (),
) -> SpecialistAssuranceReceipt:
    """Build one deterministic receipt from a qualified AQ-2 profile."""

    if not isinstance(profile, AdaptiveRiskProfile):
        raise TypeError("profile must be an AdaptiveRiskProfile")
    additions = _ordered(coordination_additions, "coordination_additions", CANONICAL_SPECIALIST_ORDER)
    assurance_extras = _ordered(assurance_additions, "assurance_additions", ASSURANCE_ORDER)
    if set(additions).intersection(profile.recommended_specialists):
        raise SpecialistAssuranceContractError(
            FAIL_AUTHORITY_SCOPE_VIOLATION,
            "coordination additions must not relabel AQ-2 selections",
        )
    if set(assurance_extras).intersection(profile.required_assurance_classes):
        raise SpecialistAssuranceContractError(
            FAIL_AUTHORITY_SCOPE_VIOLATION,
            "assurance additions must not relabel AQ-2 requirements",
        )
    selected = _ordered(
        set(profile.recommended_specialists).union(additions),
        "selected_specialists",
        CANONICAL_SPECIALIST_ORDER,
    )
    required = _ordered(
        set(profile.required_assurance_classes).union(assurance_extras),
        "required_assurance",
        ASSURANCE_ORDER,
    )
    return SpecialistAssuranceReceipt(
        source_identities=source_identities,
        development_mode=profile.development_mode,
        changed_domains=profile.changed_domains,
        quality_dimensions=profile.quality_dimensions,
        risk_characteristics=profile.risk_characteristics,
        invariants=profile.invariants,
        selected_specialists=selected,
        required_assurance=required,
        dagger_decision=profile.dagger_decision,
        protected_gates=profile.protected_gates,
        next_transition_target=next_transition_target,
        authority_boundary=profile.authority_boundary,
        risk_fingerprint=profile.risk_fingerprint,
        coordination_additions=additions,
        assurance_additions=assurance_extras,
    )


build_specialist_assurance_receipt = build_routing_receipt


def validate_routing_receipt(
    receipt: SpecialistAssuranceReceipt,
    profile: AdaptiveRiskProfile | None = None,
) -> SpecialistAssuranceReceipt:
    """Verify AQ-3 receipt binding and monotonicity against AQ-2."""

    if not isinstance(receipt, SpecialistAssuranceReceipt):
        raise TypeError("receipt must be a SpecialistAssuranceReceipt")
    if profile is None:
        return receipt
    if not isinstance(profile, AdaptiveRiskProfile):
        raise TypeError("profile must be an AdaptiveRiskProfile")
    if receipt.risk_fingerprint != profile.risk_fingerprint:
        raise SpecialistAssuranceContractError(FAIL_WRONG_SOURCE_EVIDENCE, "risk fingerprint is not AQ-2 bound")
    for field_name in (
        "development_mode",
        "changed_domains",
        "quality_dimensions",
        "risk_characteristics",
        "invariants",
        "protected_gates",
        "authority_boundary",
    ):
        if getattr(receipt, field_name) != getattr(profile, field_name):
            raise SpecialistAssuranceContractError(
                FAIL_WRONG_SOURCE_EVIDENCE,
                f"receipt field is not bound to AQ-2: {field_name}",
            )
    if profile.dagger_required and (
        not receipt.dagger_decision.required
        or "dagger" not in receipt.selected_specialists
        or receipt.dagger_decision.triggered_by != profile.dagger_decision.triggered_by
    ):
        raise SpecialistAssuranceContractError(FAIL_REQUIRED_DAGGER_OMITTED)
    if not profile.dagger_required and (
        receipt.dagger_decision.required or "dagger" in receipt.selected_specialists
    ):
        raise SpecialistAssuranceContractError(FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY)
    missing_specialists = set(profile.recommended_specialists) - set(receipt.selected_specialists)
    if missing_specialists:
        raise SpecialistAssuranceContractError(
            FAIL_REQUIRED_ASSURANCE_MISSING,
            "AQ-2 specialist selection was weakened",
        )
    extra_specialists = set(receipt.selected_specialists) - set(profile.recommended_specialists)
    if extra_specialists != set(receipt.coordination_additions):
        raise SpecialistAssuranceContractError(
            FAIL_AUTHORITY_SCOPE_VIOLATION,
            "specialist additions must be explicit bounded coordination",
        )
    missing_assurance = set(profile.required_assurance_classes) - set(receipt.required_assurance)
    if missing_assurance:
        raise SpecialistAssuranceContractError(FAIL_REQUIRED_ASSURANCE_MISSING, "AQ-2 assurance was weakened")
    extra_assurance = set(receipt.required_assurance) - set(profile.required_assurance_classes)
    if extra_assurance != set(receipt.assurance_additions):
        raise SpecialistAssuranceContractError(
            FAIL_AUTHORITY_SCOPE_VIOLATION,
            "assurance additions must be explicit",
        )
    return receipt


@dataclass(frozen=True, slots=True)
class SpecialistAssuranceEvidence:
    """One source-bound assurance record used by Overseer and Arbiter."""

    evidence_id: str
    assurance_class: str
    producer: str
    validator: str
    source_identity: str
    candidate_ref: str = "candidate"
    work_item_ref: str = "work-item"
    freshness_ref: str = "fresh"
    version_ref: str = "version"
    scope: str = "CONTRACT"
    kind: str = "TEST"
    status: str = "SATISFIED"
    source_truth: str = "OBSERVED"
    provenance_qualification: str = "AUTHORITATIVE"
    logical_identity: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "assurance_class", _one_of(self.assurance_class, ASSURANCE_ORDER, "assurance_class"))
        object.__setattr__(self, "producer", _text(self.producer, "producer").casefold())
        object.__setattr__(self, "validator", _text(self.validator, "validator").casefold())
        object.__setattr__(self, "source_identity", _text(self.source_identity, "source_identity"))
        for field_name in ("candidate_ref", "work_item_ref", "freshness_ref", "version_ref"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(self, "scope", _one_of(self.scope, EVIDENCE_SCOPES, "scope"))
        object.__setattr__(self, "kind", _one_of(self.kind, EVIDENCE_KINDS, "kind"))
        object.__setattr__(self, "status", _one_of(self.status, EVIDENCE_STATUSES, "status"))
        object.__setattr__(self, "source_truth", _one_of(self.source_truth, SOURCE_TRUTH_LABELS, "source_truth"))
        object.__setattr__(
            self,
            "provenance_qualification",
            _one_of(self.provenance_qualification, PROVENANCE_QUALIFICATIONS, "provenance_qualification"),
        )
        if self.logical_identity is None:
            object.__setattr__(self, "logical_identity", self.evidence_id)
        else:
            object.__setattr__(self, "logical_identity", _text(self.logical_identity, "logical_identity"))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SpecialistAssuranceEvidence":
        if not isinstance(data, Mapping):
            raise TypeError("AQ3 evidence must be a mapping")
        return cls(**dict(data))

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "assurance_class": self.assurance_class,
            "producer": self.producer,
            "validator": self.validator,
            "source_identity": self.source_identity,
            "candidate_ref": self.candidate_ref,
            "work_item_ref": self.work_item_ref,
            "freshness_ref": self.freshness_ref,
            "version_ref": self.version_ref,
            "scope": self.scope,
            "kind": self.kind,
            "status": self.status,
            "source_truth": self.source_truth,
            "provenance_qualification": self.provenance_qualification,
            "logical_identity": self.logical_identity or self.evidence_id,
        }


def _records(evidence: Iterable[SpecialistAssuranceEvidence]) -> tuple[SpecialistAssuranceEvidence, ...]:
    if isinstance(evidence, (str, bytes)):
        raise TypeError("evidence must be an iterable of SpecialistAssuranceEvidence")
    records = tuple(evidence)
    if any(not isinstance(record, SpecialistAssuranceEvidence) for record in records):
        raise TypeError("evidence must contain SpecialistAssuranceEvidence values")
    return records


def _record_failures(records: tuple[SpecialistAssuranceEvidence, ...], receipt: SpecialistAssuranceReceipt) -> list[str]:
    failures: list[str] = []
    ids = tuple(record.evidence_id for record in records)
    logical_ids = tuple(record.logical_identity for record in records)
    if len(ids) != len(set(ids)) or len(logical_ids) != len(set(logical_ids)):
        _append_unique(failures, FAIL_DUPLICATE_EVIDENCE_IDENTITY)
    if any(record.source_identity not in receipt.source_identities for record in records):
        _append_unique(failures, FAIL_WRONG_SOURCE_EVIDENCE)
    if any(record.status == "STALE" for record in records):
        _append_unique(failures, FAIL_STALE_EVIDENCE)
    if any(record.status == "WRONG_SOURCE" for record in records):
        _append_unique(failures, FAIL_WRONG_SOURCE_EVIDENCE)
    if any(record.status == "WEAKER" for record in records):
        _append_unique(failures, FAIL_WEAKER_EVIDENCE)
    if any(record.source_truth in {"INFERRED", "UNVERIFIED"} for record in records):
        _append_unique(failures, FAIL_SOURCE_TRUTH_VIOLATION)
    if any(record.provenance_qualification != "AUTHORITATIVE" for record in records):
        _append_unique(failures, FAIL_EVIDENCE_PROVENANCE)
    for field_name in ("candidate_ref", "work_item_ref", "freshness_ref", "version_ref"):
        values = {getattr(record, field_name) for record in records}
        if len(values) > 1:
            _append_unique(failures, FAIL_EVIDENCE_BINDING)
    return failures


def _usable(record: SpecialistAssuranceEvidence, receipt: SpecialistAssuranceReceipt) -> bool:
    if record.status != "SATISFIED" or record.source_identity not in receipt.source_identities:
        return False
    if record.source_truth not in {"OBSERVED", "DECIDED"} or record.provenance_qualification != "AUTHORITATIVE":
        return False
    if record.kind == "CI" and record.assurance_class in {
        "SECURITY_ASSURANCE",
        "CONCURRENCY_ASSURANCE",
        "ADVERSARIAL_ASSURANCE",
    }:
        return False
    allowed_scopes = _SPECIAL_ASSURANCE_SCOPES.get(record.assurance_class)
    if allowed_scopes is not None and record.scope not in allowed_scopes:
        return False
    return True


def _actual_assurance(
    records: tuple[SpecialistAssuranceEvidence, ...],
    receipt: SpecialistAssuranceReceipt,
) -> tuple[str, ...]:
    present = {record.assurance_class for record in records if _usable(record, receipt)}
    return tuple(item for item in ASSURANCE_ORDER if item in present)


@dataclass(frozen=True, slots=True)
class OverseerAssuranceReview:
    reviewer: str
    implementation_contract_satisfied: bool
    invariant_preservation_sufficient: bool
    evidence_ids: tuple[str, ...]
    failure_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "reviewer", _text(self.reviewer, "reviewer").casefold())
        if any(type(getattr(self, field)) is not bool for field in ("implementation_contract_satisfied", "invariant_preservation_sufficient")):
            raise TypeError("Overseer review decisions must be exact booleans")
        object.__setattr__(self, "evidence_ids", tuple(sorted(_evidence_ids(self.evidence_ids, "evidence_ids"))))
        object.__setattr__(self, "failure_codes", tuple(dict.fromkeys(_values(self.failure_codes, "failure_codes"))))

    @property
    def satisfied(self) -> bool:
        return self.implementation_contract_satisfied and self.invariant_preservation_sufficient and not self.failure_codes

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "implementation_contract_satisfied": self.implementation_contract_satisfied,
            "invariant_preservation_sufficient": self.invariant_preservation_sufficient,
            "evidence_ids": list(self.evidence_ids),
            "failure_codes": list(self.failure_codes),
            "satisfied": self.satisfied,
        }


def assess_overseer_review(
    receipt: SpecialistAssuranceReceipt,
    evidence: Iterable[SpecialistAssuranceEvidence],
    *,
    reviewer: str = "overseer",
) -> OverseerAssuranceReview:
    """Return an independent Overseer decision without claiming transition authority."""

    validate_routing_receipt(receipt)
    records = _records(evidence)
    reviewer_id = _text(reviewer, "reviewer").casefold()
    failures = _record_failures(records, receipt)
    actual = set(_actual_assurance(records, receipt))
    independent = reviewer_id == "overseer" and any(
        _usable(record, receipt) and record.validator == reviewer_id and record.producer != reviewer_id
        for record in records
    )
    if not independent:
        _append_unique(failures, FAIL_INDEPENDENT_ASSURANCE_REQUIRED)
    missing = set(receipt.required_assurance) - actual
    if missing:
        _append_unique(failures, FAIL_REQUIRED_ASSURANCE_MISSING)
    implementation_satisfied = not failures
    invariant_sufficient = implementation_satisfied and (
        not receipt.invariants or "INVARIANT_PRESERVATION_ASSURANCE" in actual
    )
    return OverseerAssuranceReview(
        reviewer=reviewer_id,
        implementation_contract_satisfied=implementation_satisfied,
        invariant_preservation_sufficient=invariant_sufficient,
        evidence_ids=tuple(record.evidence_id for record in records),
        failure_codes=tuple(failures),
    )


evaluate_overseer_review = assess_overseer_review


@dataclass(frozen=True, slots=True)
class ArbiterProgressionDecision:
    claimed_completion_state: str
    required_assurance_set: tuple[str, ...]
    actual_evidence_set: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    disposition: str
    failure_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "claimed_completion_state", _one_of(self.claimed_completion_state, COMPLETION_STATES, "claimed_completion_state"))
        object.__setattr__(self, "required_assurance_set", _ordered(self.required_assurance_set, "required_assurance_set", ASSURANCE_ORDER))
        object.__setattr__(self, "actual_evidence_set", _ordered(self.actual_evidence_set, "actual_evidence_set", ASSURANCE_ORDER))
        object.__setattr__(self, "evidence_ids", tuple(sorted(_evidence_ids(self.evidence_ids, "evidence_ids"))))
        object.__setattr__(self, "disposition", _one_of(self.disposition, ("ADVANCE", "BLOCK"), "disposition"))
        object.__setattr__(self, "failure_codes", tuple(dict.fromkeys(_values(self.failure_codes, "failure_codes"))))

    @property
    def can_advance(self) -> bool:
        return self.disposition == "ADVANCE" and not self.failure_codes

    def to_dict(self) -> dict[str, Any]:
        return {
            "claimed_completion_state": self.claimed_completion_state,
            "required_assurance_set": list(self.required_assurance_set),
            "actual_evidence_set": list(self.actual_evidence_set),
            "evidence_ids": list(self.evidence_ids),
            "disposition": self.disposition,
            "failure_codes": list(self.failure_codes),
            "can_advance": self.can_advance,
        }


def evaluate_arbiter_progression(
    receipt: SpecialistAssuranceReceipt,
    evidence: Iterable[SpecialistAssuranceEvidence],
    *,
    claimed_completion_state: str = "CONTRACT_VERIFIED",
    claimed_source_truth: str = "OBSERVED",
    protected_gates_satisfied: bool = False,
    overseer_review: OverseerAssuranceReview | None = None,
    candidate_ref: str | None = None,
    work_item_ref: str | None = None,
    freshness_ref: str | None = None,
    version_ref: str | None = None,
) -> ArbiterProgressionDecision:
    """Compare required, actual, and claimed state without performing a transition."""

    validate_routing_receipt(receipt)
    records = _records(evidence)
    failures = _record_failures(records, receipt)
    actual = set(_actual_assurance(records, receipt))
    if overseer_review is None or not isinstance(overseer_review, OverseerAssuranceReview) or not overseer_review.satisfied:
        _append_unique(failures, FAIL_INDEPENDENT_ASSURANCE_REQUIRED)
    else:
        actual.add("INDEPENDENT_QA")
    missing = set(receipt.required_assurance) - actual
    if missing:
        _append_unique(failures, FAIL_REQUIRED_ASSURANCE_MISSING)
    if receipt.protected_gates and protected_gates_satisfied is not True:
        _append_unique(failures, FAIL_PROTECTED_GATE_UNSATISFIED)
    try:
        state = _one_of(claimed_completion_state, COMPLETION_STATES, "claimed_completion_state")
        truth = _one_of(claimed_source_truth, SOURCE_TRUTH_LABELS, "claimed_source_truth")
    except (TypeError, ValueError):
        state = "CONTRACT_VERIFIED"
        truth = "UNVERIFIED"
        _append_unique(failures, FAIL_AQ1_COMPLETION_SCOPE)
    if state in {"CANONICAL_VERIFIED", "PRODUCT_COMPLETE"} or truth in {"INFERRED", "UNVERIFIED"}:
        _append_unique(failures, FAIL_AQ1_COMPLETION_SCOPE)
    required_scopes = _CLAIM_EVIDENCE_SCOPES.get(state, set())
    if required_scopes and not any(
        _usable(record, receipt) and record.scope in required_scopes for record in records
    ):
        _append_unique(failures, FAIL_AQ1_COMPLETION_SCOPE)
    if any(
        expected is not None and any(getattr(record, field_name) != expected for record in records)
        for field_name, expected in (
            ("candidate_ref", candidate_ref),
            ("work_item_ref", work_item_ref),
            ("freshness_ref", freshness_ref),
            ("version_ref", version_ref),
        )
    ):
        _append_unique(failures, FAIL_EVIDENCE_BINDING)
    if "AGGREGATE_INVARIANT_ASSURANCE" in receipt.required_assurance and any(
        record.assurance_class == "AGGREGATE_INVARIANT_ASSURANCE" and record.scope in {"ROW", "ROW_VERSION"}
        for record in records
    ):
        _append_unique(failures, REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS)
    ordered_actual = tuple(item for item in ASSURANCE_ORDER if item in actual)
    return ArbiterProgressionDecision(
        claimed_completion_state=state,
        required_assurance_set=receipt.required_assurance,
        actual_evidence_set=ordered_actual,
        evidence_ids=tuple(record.evidence_id for record in records),
        disposition="ADVANCE" if not failures else "BLOCK",
        failure_codes=tuple(failures),
    )


def validate_specialist_claim(
    specialist: str,
    *,
    claim_type: str,
    source_truth: str,
    authoritative_source_ref: str | None = None,
) -> bool:
    """Keep AQ1 source-truth labels authoritative for specialist claims."""

    specialist_id = _text(specialist, "specialist").casefold()
    claim = _text(claim_type, "claim_type").upper().replace(" ", "_")
    truth = _one_of(source_truth, SOURCE_TRUTH_LABELS, "source_truth")
    if specialist_id == "scribe" and claim in {"HISTORICAL_INTENT", "PAST_DECISION", "HISTORICAL_DECISION"} and truth in {
        "INFERRED",
        "UNVERIFIED",
    }:
        raise SpecialistAssuranceContractError(FAIL_SOURCE_TRUTH_VIOLATION)
    if truth == "DECIDED" and authoritative_source_ref is None:
        raise SpecialistAssuranceContractError(FAIL_SOURCE_TRUTH_VIOLATION, "DECIDED claims require an authority reference")
    return True


def validate_authority_scope(
    specialist: str,
    *,
    actor_scope: str,
    mutation_scope: str,
    action: str = "MUTATE",
) -> bool:
    """Prevent tenant-scoped security review from mutating global authority."""

    specialist_id = _text(specialist, "specialist").casefold()
    actor = _text(actor_scope, "actor_scope").upper().replace(" ", "_")
    mutation = _text(mutation_scope, "mutation_scope").upper().replace(" ", "_")
    operation = _text(action, "action").upper()
    if specialist_id == "cipher" and actor in {"TENANT", "TENANT_ADMIN"} and mutation == "GLOBAL" and operation in {
        "MUTATE",
        "GRANT",
        "AUTHORIZE",
    }:
        raise SpecialistAssuranceContractError(FAIL_AUTHORITY_SCOPE_VIOLATION)
    return True


def validate_concurrency_claim(
    specialist: str,
    *,
    invariant: str,
    claim_scope: str,
    evidence_scope: str,
) -> bool:
    """Require aggregate/concurrency evidence for tenant-wide aggregate claims."""

    specialist_id = _text(specialist, "specialist").casefold()
    invariant_id = _text(invariant, "invariant").upper().replace(" ", "_")
    claim = _text(claim_scope, "claim_scope").upper().replace(" ", "_")
    evidence = _text(evidence_scope, "evidence_scope").upper().replace(" ", "_")
    if (
        specialist_id == "chronicler"
        and ("AGGREGATE" in invariant_id or claim in {"AGGREGATE", "TENANT_WIDE_AGGREGATE"})
        and evidence in {"ROW", "ROW_LEVEL", "ROW_VERSION"}
    ):
        raise SpecialistAssuranceContractError(REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS)
    return True


__all__ = [
    "AQ3_AUTHORITY_RULE",
    "AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION",
    "ArbiterProgressionDecision",
    "CANONICAL_SPECIALIST_ORDER",
    "DEFAULT_NEXT_TRANSITION_TARGET",
    "EVIDENCE_KINDS",
    "EVIDENCE_SCOPES",
    "EVIDENCE_STATUSES",
    "FAILURE_CODES",
    "FAIL_AUTHORITY_SCOPE_VIOLATION",
    "FAIL_AQ1_COMPLETION_SCOPE",
    "FAIL_DUPLICATE_EVIDENCE_IDENTITY",
    "FAIL_EVIDENCE_BINDING",
    "FAIL_EVIDENCE_PROVENANCE",
    "FAIL_INDEPENDENT_ASSURANCE_REQUIRED",
    "FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY",
    "FAIL_PROTECTED_GATE_UNSATISFIED",
    "FAIL_REQUIRED_ASSURANCE_MISSING",
    "FAIL_REQUIRED_DAGGER_OMITTED",
    "FAIL_SOURCE_TRUTH_VIOLATION",
    "FAIL_STALE_EVIDENCE",
    "FAIL_WEAKER_EVIDENCE",
    "FAIL_WRONG_SOURCE_EVIDENCE",
    "PROVENANCE_QUALIFICATIONS",
    "REQUIRED_RECEIPT_FIELDS",
    "REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS",
    "SpecialistAssuranceContractError",
    "SpecialistAssuranceEvidence",
    "SpecialistAssuranceReceipt",
    "OverseerAssuranceReview",
    "assess_overseer_review",
    "build_routing_receipt",
    "build_specialist_assurance_receipt",
    "evaluate_arbiter_progression",
    "evaluate_overseer_review",
    "validate_authority_scope",
    "validate_concurrency_claim",
    "validate_routing_receipt",
    "validate_specialist_claim",
]
