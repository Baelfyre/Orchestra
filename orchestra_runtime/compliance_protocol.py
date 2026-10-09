from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any, Iterable, Mapping

from .evidence import receipt_digest
from .governance_kernel import (
    ArbiterKernelInput,
    ArbiterKernelResult,
    GovernanceDecision,
    evaluate_arbiter,
)

COMPLIANCE_PROTOCOL_SCHEMA_VERSION = "orchestra.compliance-protocol.v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name).lower()
    if SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return text


def _ids(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    raw = tuple(_text(value, field_name) for value in values)
    if len(raw) != len(set(raw)):
        raise ValueError(f"{field_name} contains duplicate IDs")
    return tuple(sorted(raw))


def _filters(values: Mapping[str, object | None]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values.items():
        if value is None or str(value).strip() == "":
            continue
        normalized.append((_text(key, "filter key"), _text(value, f"filter {key}")))
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ComplianceQueryReceipt:
    canonical_repository: str
    registry_version: str
    release_sequence: int
    release_tag: str
    manifest_sha256: str
    filters: tuple[tuple[str, str], ...]
    source_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    schema_version: str = COMPLIANCE_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != COMPLIANCE_PROTOCOL_SCHEMA_VERSION:
            raise ValueError(f"unsupported compliance query schema {self.schema_version!r}")
        object.__setattr__(self, "canonical_repository", _text(self.canonical_repository, "canonical_repository"))
        object.__setattr__(self, "registry_version", _text(self.registry_version, "registry_version"))
        if isinstance(self.release_sequence, bool) or not isinstance(self.release_sequence, int) or self.release_sequence <= 0:
            raise ValueError("release_sequence must be a positive integer")
        object.__setattr__(self, "release_tag", _text(self.release_tag, "release_tag"))
        object.__setattr__(self, "manifest_sha256", _sha256(self.manifest_sha256, "manifest_sha256"))
        if not isinstance(self.filters, tuple):
            raise TypeError("filters must be a tuple")
        normalized_filters = tuple(sorted((_text(k, "filter key"), _text(v, f"filter {k}")) for k, v in self.filters))
        if len(normalized_filters) != len({key for key, _ in normalized_filters}):
            raise ValueError("filters contain duplicate keys")
        object.__setattr__(self, "filters", normalized_filters)
        object.__setattr__(self, "source_ids", _ids(self.source_ids, "source_ids"))
        object.__setattr__(self, "obligation_ids", _ids(self.obligation_ids, "obligation_ids"))

    @classmethod
    def from_registry_result(
        cls,
        registry_status: Mapping[str, Any],
        query_result: Mapping[str, Any],
        *,
        filters: Mapping[str, object | None],
    ) -> "ComplianceQueryReceipt":
        if registry_status.get("registry_status") != "VERIFIED":
            raise ValueError("registry status must be VERIFIED before producing a query receipt")
        if registry_status.get("registry_version") != query_result.get("registry_version"):
            raise ValueError("registry version differs between status and query result")
        if registry_status.get("release_sequence") != query_result.get("release_sequence"):
            raise ValueError("release sequence differs between status and query result")
        sources = query_result.get("sources")
        obligations = query_result.get("obligations")
        if not isinstance(sources, list) or not isinstance(obligations, list):
            raise ValueError("query result must contain source and obligation lists")
        source_ids = []
        for record in sources:
            if not isinstance(record, Mapping):
                raise ValueError("query source record must be an object")
            source_ids.append(_text(record.get("source_id"), "source_id"))
        obligation_ids = []
        for record in obligations:
            if not isinstance(record, Mapping):
                raise ValueError("query obligation record must be an object")
            obligation_ids.append(_text(record.get("obligation_id"), "obligation_id"))
        return cls(
            canonical_repository=_text(registry_status.get("canonical_repository"), "canonical_repository"),
            registry_version=_text(registry_status.get("registry_version"), "registry_version"),
            release_sequence=registry_status.get("release_sequence"),
            release_tag=_text(registry_status.get("release_tag"), "release_tag"),
            manifest_sha256=_sha256(registry_status.get("manifest_sha256"), "manifest_sha256"),
            filters=_filters(filters),
            source_ids=tuple(source_ids),
            obligation_ids=tuple(obligation_ids),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "canonical_repository": self.canonical_repository,
            "registry_version": self.registry_version,
            "release_sequence": self.release_sequence,
            "release_tag": self.release_tag,
            "manifest_sha256": self.manifest_sha256,
            "filters": {key: value for key, value in self.filters},
            "source_ids": list(self.source_ids),
            "obligation_ids": list(self.obligation_ids),
            "source_count": len(self.source_ids),
            "obligation_count": len(self.obligation_ids),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ComplianceExclusion:
    obligation_id: str
    reason_code: str
    evidence_ref: str
    authorized_by: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "obligation_id", _text(self.obligation_id, "obligation_id"))
        object.__setattr__(self, "reason_code", _text(self.reason_code, "reason_code"))
        object.__setattr__(self, "evidence_ref", _text(self.evidence_ref, "evidence_ref"))
        object.__setattr__(self, "authorized_by", _text(self.authorized_by, "authorized_by"))

    def to_dict(self) -> dict[str, str]:
        return {
            "obligation_id": self.obligation_id,
            "reason_code": self.reason_code,
            "evidence_ref": self.evidence_ref,
            "authorized_by": self.authorized_by,
        }


@dataclass(frozen=True, slots=True)
class ComplianceConsumptionReceipt:
    query_digest: str
    source_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    classifications: tuple[tuple[str, str], ...]
    verdict: GovernanceDecision | str
    exclusions: tuple[ComplianceExclusion, ...] = ()
    schema_version: str = COMPLIANCE_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != COMPLIANCE_PROTOCOL_SCHEMA_VERSION:
            raise ValueError(f"unsupported compliance consumption schema {self.schema_version!r}")
        object.__setattr__(self, "query_digest", _sha256(self.query_digest, "query_digest"))
        source_ids = _ids(self.source_ids, "source_ids")
        obligation_ids = _ids(self.obligation_ids, "obligation_ids")
        object.__setattr__(self, "source_ids", source_ids)
        object.__setattr__(self, "obligation_ids", obligation_ids)
        if not isinstance(self.classifications, tuple):
            raise TypeError("classifications must be a tuple")
        normalized = tuple(sorted((_text(key, "classification obligation_id"), _text(value, "classification")) for key, value in self.classifications))
        keys = tuple(key for key, _ in normalized)
        if len(keys) != len(set(keys)):
            raise ValueError("classifications contain duplicate obligation IDs")
        if set(keys) != set(obligation_ids):
            raise ValueError("classifications must cover exactly the consumed obligation IDs")
        object.__setattr__(self, "classifications", normalized)
        try:
            verdict = self.verdict if isinstance(self.verdict, GovernanceDecision) else GovernanceDecision(_text(self.verdict, "verdict"))
        except ValueError as exc:
            raise ValueError(f"unsupported compliance verdict: {self.verdict!r}") from exc
        object.__setattr__(self, "verdict", verdict)
        if not isinstance(self.exclusions, tuple) or not all(isinstance(item, ComplianceExclusion) for item in self.exclusions):
            raise TypeError("exclusions must contain ComplianceExclusion values")
        exclusion_ids = tuple(item.obligation_id for item in self.exclusions)
        if len(exclusion_ids) != len(set(exclusion_ids)):
            raise ValueError("exclusions contain duplicate obligation IDs")
        if set(exclusion_ids) & set(obligation_ids):
            raise ValueError("an obligation cannot be both consumed and excluded")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query_digest": self.query_digest,
            "source_ids": list(self.source_ids),
            "obligation_ids": list(self.obligation_ids),
            "classifications": {key: value for key, value in self.classifications},
            "verdict": self.verdict.value,
            "exclusions": [item.to_dict() for item in self.exclusions],
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class StewardTraceabilityReceipt:
    query_digest: str
    source_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    schema_version: str = COMPLIANCE_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != COMPLIANCE_PROTOCOL_SCHEMA_VERSION:
            raise ValueError(f"unsupported Steward traceability schema {self.schema_version!r}")
        object.__setattr__(self, "query_digest", _sha256(self.query_digest, "query_digest"))
        object.__setattr__(self, "source_ids", _ids(self.source_ids, "source_ids"))
        object.__setattr__(self, "obligation_ids", _ids(self.obligation_ids, "obligation_ids"))
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("evidence_refs must be a tuple")
        refs = tuple(_text(item, "evidence_ref") for item in self.evidence_refs)
        if len(refs) != len(set(refs)):
            raise ValueError("evidence_refs contain duplicates")
        object.__setattr__(self, "evidence_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query_digest": self.query_digest,
            "source_ids": list(self.source_ids),
            "obligation_ids": list(self.obligation_ids),
            "evidence_refs": list(self.evidence_refs),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ComplianceSetEqualityGateResult:
    ready: bool
    error_codes: tuple[str, ...]
    query_digest: str
    consumption_digest: str
    traceability_digest: str
    excluded_obligation_ids: tuple[str, ...]
    schema_version: str = COMPLIANCE_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.ready, bool):
            raise TypeError("ready must be bool")
        object.__setattr__(self, "query_digest", _sha256(self.query_digest, "query_digest"))
        object.__setattr__(self, "consumption_digest", _sha256(self.consumption_digest, "consumption_digest"))
        object.__setattr__(self, "traceability_digest", _sha256(self.traceability_digest, "traceability_digest"))
        object.__setattr__(self, "error_codes", tuple(_text(item, "error_code") for item in self.error_codes))
        object.__setattr__(self, "excluded_obligation_ids", _ids(self.excluded_obligation_ids, "excluded_obligation_ids"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ready": self.ready,
            "error_codes": list(self.error_codes),
            "query_digest": self.query_digest,
            "consumption_digest": self.consumption_digest,
            "traceability_digest": self.traceability_digest,
            "excluded_obligation_ids": list(self.excluded_obligation_ids),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def evaluate_compliance_set_equality(
    query: ComplianceQueryReceipt,
    consumption: ComplianceConsumptionReceipt,
    traceability: StewardTraceabilityReceipt,
) -> ComplianceSetEqualityGateResult:
    if not isinstance(query, ComplianceQueryReceipt):
        raise TypeError("query must be ComplianceQueryReceipt")
    if not isinstance(consumption, ComplianceConsumptionReceipt):
        raise TypeError("consumption must be ComplianceConsumptionReceipt")
    if not isinstance(traceability, StewardTraceabilityReceipt):
        raise TypeError("traceability must be StewardTraceabilityReceipt")

    errors: list[str] = []
    if consumption.query_digest != query.digest:
        errors.append("CONSUMPTION_QUERY_DIGEST_MISMATCH")
    if traceability.query_digest != query.digest:
        errors.append("TRACEABILITY_QUERY_DIGEST_MISMATCH")

    query_sources = set(query.source_ids)
    if set(consumption.source_ids) != query_sources:
        errors.append("CONSUMED_SOURCE_SET_MISMATCH")
    if set(traceability.source_ids) != query_sources:
        errors.append("TRACEABILITY_SOURCE_SET_MISMATCH")

    query_obligations = set(query.obligation_ids)
    excluded = {item.obligation_id for item in consumption.exclusions}
    if not excluded <= query_obligations:
        errors.append("EXCLUSION_UNKNOWN_OBLIGATION_ID")
    accounted = set(consumption.obligation_ids) | excluded
    if accounted != query_obligations:
        errors.append("CONSUMED_OBLIGATION_SET_MISMATCH")
    if set(traceability.obligation_ids) != query_obligations:
        errors.append("TRACEABILITY_OBLIGATION_SET_MISMATCH")

    return ComplianceSetEqualityGateResult(
        ready=not errors,
        error_codes=tuple(errors),
        query_digest=query.digest,
        consumption_digest=consumption.digest,
        traceability_digest=traceability.digest,
        excluded_obligation_ids=tuple(sorted(excluded)),
    )


@dataclass(frozen=True, slots=True)
class ComplianceArbiterEvaluation:
    compliance_gate: ComplianceSetEqualityGateResult
    arbiter_result: ArbiterKernelResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliance_gate": self.compliance_gate.to_dict(),
            "arbiter_result": self.arbiter_result.to_dict(),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def evaluate_compliance_with_arbiter(
    kernel_input: ArbiterKernelInput,
    compliance_gate: ComplianceSetEqualityGateResult,
) -> ComplianceArbiterEvaluation:
    if not isinstance(kernel_input, ArbiterKernelInput):
        raise TypeError("kernel_input must be ArbiterKernelInput")
    if not isinstance(compliance_gate, ComplianceSetEqualityGateResult):
        raise TypeError("compliance_gate must be ComplianceSetEqualityGateResult")
    effective = kernel_input
    if not compliance_gate.ready:
        effective = replace(kernel_input, governance_evidence_complete=False)
    return ComplianceArbiterEvaluation(
        compliance_gate=compliance_gate,
        arbiter_result=evaluate_arbiter(effective),
    )
