# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from typing import Iterable, TypeVar, cast

from orchestra_runtime.shared import normalize_timestamp


_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_EnumT = TypeVar("_EnumT", bound=Enum)
_RecordT = TypeVar("_RecordT")


class CapabilitySourceKind(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class CapabilityClaim(str, Enum):
    SUPPORTS = "SUPPORTS"
    DOES_NOT_SUPPORT = "DOES_NOT_SUPPORT"
    UNKNOWN = "UNKNOWN"


class CapabilityCoverageStatus(str, Enum):
    VERIFIED = "VERIFIED"
    DECLARED = "DECLARED"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    STALE = "STALE"
    CONFLICT = "CONFLICT"


class CapabilityEvidenceLevel(str, Enum):
    DECLARED = "DECLARED"
    TRUSTED_PRODUCER = "TRUSTED_PRODUCER"


class CapabilityEvidenceFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


def _identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip().casefold()
    if not _IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return normalized


def _text(value: object, field_name: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        raise ValueError(f"{field_name} must be non-empty and at most {max_length} characters")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


def _enum_value(value: object, enum_type: type[_EnumT], field_name: str) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or {enum_type.__name__}")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is unsupported") from exc


def _unique_identifiers(values: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    normalized = tuple(_identifier(value, field_name) for value in values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique identifiers")
    return tuple(sorted(normalized))


def _evidence_refs(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("evidence_refs must be a list or tuple")
    normalized = tuple(_text(value, "evidence_ref") for value in values)
    if not normalized:
        raise ValueError("evidence_refs must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError("evidence_refs must be unique")
    return tuple(sorted(normalized))


def _optional_timestamp(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    return normalize_timestamp(value, field_name)


@dataclass(frozen=True, slots=True)
class TaskCapabilityFacet:
    facet_id: str
    required_capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "facet_id", _identifier(self.facet_id, "facet_id"))
        object.__setattr__(
            self,
            "required_capabilities",
            _unique_identifiers(self.required_capabilities, "required_capabilities"),
        )


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    """A source claim. Its claim value cannot assert independent verification."""

    facet_id: str
    capability_id: str
    source_kind: CapabilitySourceKind | str
    source_id: str
    claim: CapabilityClaim | str
    evidence_refs: tuple[str, ...]
    valid_until: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "facet_id", _identifier(self.facet_id, "facet_id"))
        object.__setattr__(self, "capability_id", _identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "source_kind", _enum_value(self.source_kind, CapabilitySourceKind, "source_kind"))
        object.__setattr__(self, "source_id", _identifier(self.source_id, "source_id"))
        object.__setattr__(self, "claim", _enum_value(self.claim, CapabilityClaim, "claim"))
        object.__setattr__(self, "evidence_refs", _evidence_refs(self.evidence_refs))
        object.__setattr__(self, "valid_until", _optional_timestamp(self.valid_until, "valid_until"))


@dataclass(frozen=True, slots=True)
class TrustedCapabilityEvidence:
    """Typed output expected from a future trusted producer; this record does not authenticate one."""

    facet_id: str
    capability_id: str
    source_kind: CapabilitySourceKind | str
    source_id: str
    producer_id: str
    claim: CapabilityClaim | str
    evidence_refs: tuple[str, ...]
    valid_until: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "facet_id", _identifier(self.facet_id, "facet_id"))
        object.__setattr__(self, "capability_id", _identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "source_kind", _enum_value(self.source_kind, CapabilitySourceKind, "source_kind"))
        object.__setattr__(self, "source_id", _identifier(self.source_id, "source_id"))
        object.__setattr__(self, "producer_id", _identifier(self.producer_id, "producer_id"))
        object.__setattr__(self, "claim", _enum_value(self.claim, CapabilityClaim, "claim"))
        object.__setattr__(self, "evidence_refs", _evidence_refs(self.evidence_refs))
        object.__setattr__(self, "valid_until", _optional_timestamp(self.valid_until, "valid_until"))


@dataclass(frozen=True, slots=True)
class CapabilityEvidenceReference:
    source_kind: CapabilitySourceKind
    source_id: str
    evidence_ref: str
    claim: CapabilityClaim
    evidence_level: CapabilityEvidenceLevel
    freshness: CapabilityEvidenceFreshness
    producer_id: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilityCoverageItem:
    facet_id: str
    capability_id: str
    status: CapabilityCoverageStatus
    evidence: tuple[CapabilityEvidenceReference, ...]


@dataclass(frozen=True, slots=True)
class CapabilityCoverageResult:
    evaluated_at: str
    items: tuple[CapabilityCoverageItem, ...]


def _records(values: Iterable[object], expected_type: type[_RecordT], field_name: str) -> tuple[_RecordT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must contain {expected_type.__name__} records")
    try:
        materialized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be iterable") from exc
    if any(not isinstance(value, expected_type) for value in materialized):
        raise TypeError(f"{field_name} must contain {expected_type.__name__} records")
    return tuple(cast(_RecordT, value) for value in materialized)


def _freshness(valid_until: str | None, evaluated_at: datetime) -> CapabilityEvidenceFreshness:
    if valid_until is None:
        return CapabilityEvidenceFreshness.UNKNOWN
    expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
    if expiry <= evaluated_at:
        return CapabilityEvidenceFreshness.STALE
    return CapabilityEvidenceFreshness.CURRENT


def _evidence_sort_key(item: CapabilityEvidenceReference) -> tuple[str, ...]:
    return (
        item.source_kind.value,
        item.source_id,
        item.evidence_ref,
        item.evidence_level.value,
        item.claim.value,
        item.freshness.value,
        item.producer_id or "",
    )


def _coverage_status(evidence: tuple[CapabilityEvidenceReference, ...]) -> CapabilityCoverageStatus:
    non_stale = tuple(item for item in evidence if item.freshness is not CapabilityEvidenceFreshness.STALE)
    claims = {item.claim for item in non_stale if item.claim is not CapabilityClaim.UNKNOWN}
    if CapabilityClaim.SUPPORTS in claims and CapabilityClaim.DOES_NOT_SUPPORT in claims:
        return CapabilityCoverageStatus.CONFLICT
    if CapabilityClaim.SUPPORTS in claims:
        if any(
            item.claim is CapabilityClaim.SUPPORTS
            and item.evidence_level is CapabilityEvidenceLevel.TRUSTED_PRODUCER
            and item.freshness is CapabilityEvidenceFreshness.CURRENT
            for item in non_stale
        ):
            return CapabilityCoverageStatus.VERIFIED
        if any(
            item.claim is CapabilityClaim.SUPPORTS
            and item.evidence_level is CapabilityEvidenceLevel.DECLARED
            for item in non_stale
        ):
            return CapabilityCoverageStatus.DECLARED
        return CapabilityCoverageStatus.UNKNOWN
    if CapabilityClaim.DOES_NOT_SUPPORT in claims:
        if any(
            item.claim is CapabilityClaim.DOES_NOT_SUPPORT
            and (
                item.evidence_level is CapabilityEvidenceLevel.DECLARED
                or item.freshness is CapabilityEvidenceFreshness.CURRENT
            )
            for item in non_stale
        ):
            return CapabilityCoverageStatus.MISSING
        return CapabilityCoverageStatus.UNKNOWN
    if non_stale:
        return CapabilityCoverageStatus.UNKNOWN
    if evidence:
        return CapabilityCoverageStatus.STALE
    return CapabilityCoverageStatus.MISSING


def evaluate_capability_coverage(
    task_facets: Iterable[TaskCapabilityFacet],
    declarations: Iterable[CapabilityDeclaration],
    trusted_evidence: Iterable[TrustedCapabilityEvidence] = (),
    *,
    evaluated_at: str,
) -> CapabilityCoverageResult:
    """Match explicit facets to evidence without selecting a source or route.

    Trusted evidence must already come from a trusted producer. This function
    checks its shape and expiry, but cannot authenticate that producer.
    """
    facets = _records(task_facets, TaskCapabilityFacet, "task_facets")
    declared = _records(declarations, CapabilityDeclaration, "declarations")
    trusted = _records(trusted_evidence, TrustedCapabilityEvidence, "trusted_evidence")
    if not facets:
        raise ValueError("task_facets must not be empty")
    if len({facet.facet_id for facet in facets}) != len(facets):
        raise ValueError("task_facets must have unique facet_id values")
    if len(set(declared)) != len(declared):
        raise ValueError("declarations must not contain duplicates")
    if len(set(trusted)) != len(trusted):
        raise ValueError("trusted_evidence must not contain duplicates")

    normalized_evaluated_at = normalize_timestamp(evaluated_at, "evaluated_at")
    evaluation_time = datetime.fromisoformat(normalized_evaluated_at.replace("Z", "+00:00"))
    grouped: dict[tuple[str, str], list[CapabilityEvidenceReference]] = {}
    for declaration in declared:
        freshness = _freshness(declaration.valid_until, evaluation_time)
        key = (declaration.facet_id, declaration.capability_id)
        for evidence_ref in declaration.evidence_refs:
            grouped.setdefault(key, []).append(
                CapabilityEvidenceReference(
                    declaration.source_kind,
                    declaration.source_id,
                    evidence_ref,
                    declaration.claim,
                    CapabilityEvidenceLevel.DECLARED,
                    freshness,
                )
            )
    for evidence in trusted:
        freshness = _freshness(evidence.valid_until, evaluation_time)
        key = (evidence.facet_id, evidence.capability_id)
        for evidence_ref in evidence.evidence_refs:
            grouped.setdefault(key, []).append(
                CapabilityEvidenceReference(
                    evidence.source_kind,
                    evidence.source_id,
                    evidence_ref,
                    evidence.claim,
                    CapabilityEvidenceLevel.TRUSTED_PRODUCER,
                    freshness,
                    evidence.producer_id,
                )
            )

    items: list[CapabilityCoverageItem] = []
    for facet in sorted(facets, key=lambda item: item.facet_id):
        for capability_id in facet.required_capabilities:
            evidence = tuple(sorted(grouped.get((facet.facet_id, capability_id), ()), key=_evidence_sort_key))
            items.append(
                CapabilityCoverageItem(
                    facet.facet_id,
                    capability_id,
                    _coverage_status(evidence),
                    evidence,
                )
            )
    return CapabilityCoverageResult(normalized_evaluated_at, tuple(items))


__all__ = [
    "CapabilityClaim",
    "CapabilityCoverageItem",
    "CapabilityCoverageResult",
    "CapabilityCoverageStatus",
    "CapabilityDeclaration",
    "CapabilityEvidenceFreshness",
    "CapabilityEvidenceLevel",
    "CapabilityEvidenceReference",
    "CapabilitySourceKind",
    "TaskCapabilityFacet",
    "TrustedCapabilityEvidence",
    "evaluate_capability_coverage",
]
