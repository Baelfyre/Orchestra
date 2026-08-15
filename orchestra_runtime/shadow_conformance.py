from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from pathlib import Path
from typing import Any

from .evidence import receipt_digest
from .governance_kernel import ArbiterKernelResult, TransitionDisposition
from .machine_contracts import (
    command_route_record,
    governance_required_specialists,
    valid_specialist_ids,
)


SHADOW_CONFORMANCE_SCHEMA_VERSION = "orchestra.shadow-conformance.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MigrationStage(str, Enum):
    SHADOW = "SHADOW"
    ADVISORY = "ADVISORY"
    VALIDATION_AUTHORITY = "VALIDATION_AUTHORITY"
    CANONICAL_PROMOTION_AUTHORITY = "CANONICAL_PROMOTION_AUTHORITY"
    LEGACY_RETIRED = "LEGACY_RETIRED"


class ShadowDiscrepancy(str, Enum):
    UNKNOWN_LEGACY_SPECIALIST = "UNKNOWN_LEGACY_SPECIALIST"
    SPECIALIST_MISMATCH = "SPECIALIST_MISMATCH"
    GOVERNANCE_REQUIRED_MISMATCH = "GOVERNANCE_REQUIRED_MISMATCH"
    VALIDATION_MISMATCH = "VALIDATION_MISMATCH"
    UNKNOWN_LEGACY_DISPOSITION = "UNKNOWN_LEGACY_DISPOSITION"
    ARBITER_DISPOSITION_MISMATCH = "ARBITER_DISPOSITION_MISMATCH"
    MISSING_EVIDENCE_DIGEST = "MISSING_EVIDENCE_DIGEST"


_DISCREPANCY_ORDER = tuple(item.value for item in ShadowDiscrepancy)


def _nonempty(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _sha256(value: object, field_name: str) -> str:
    text = _nonempty(value, field_name).lower()
    if _SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return text


def _ordered_discrepancies(values: list[ShadowDiscrepancy]) -> tuple[ShadowDiscrepancy, ...]:
    rank = {value: index for index, value in enumerate(_DISCREPANCY_ORDER)}
    unique = {item.value: item for item in values}
    return tuple(unique[key] for key in sorted(unique, key=rank.__getitem__))


@dataclass(frozen=True, slots=True)
class LegacyWorkflowClaim:
    command_name: str
    specialist_id: str
    governance_required: bool
    validation_allowed: bool
    arbiter_disposition: str
    evidence_digests: tuple[str, ...] = ()
    schema_version: str = SHADOW_CONFORMANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_CONFORMANCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow claim schema {self.schema_version!r}")
        object.__setattr__(self, "command_name", _nonempty(self.command_name, "command_name"))
        object.__setattr__(self, "specialist_id", _nonempty(self.specialist_id, "specialist_id"))
        if not isinstance(self.governance_required, bool):
            raise TypeError("governance_required must be bool")
        if not isinstance(self.validation_allowed, bool):
            raise TypeError("validation_allowed must be bool")
        object.__setattr__(self, "arbiter_disposition", _nonempty(self.arbiter_disposition, "arbiter_disposition"))
        if not isinstance(self.evidence_digests, tuple):
            raise TypeError("evidence_digests must be a tuple")
        normalized = tuple(sorted(_sha256(item, "evidence_digest") for item in self.evidence_digests))
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_digests contains duplicates")
        object.__setattr__(self, "evidence_digests", normalized)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command_name": self.command_name,
            "specialist_id": self.specialist_id,
            "governance_required": self.governance_required,
            "validation_allowed": self.validation_allowed,
            "arbiter_disposition": self.arbiter_disposition,
            "evidence_digests": list(self.evidence_digests),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ShadowComparisonRecord:
    legacy_claim: LegacyWorkflowClaim
    machine_route_id: str
    machine_specialist_id: str
    machine_governance_required: bool
    machine_validation_allowed: bool
    machine_arbiter_disposition: str
    discrepancy_codes: tuple[ShadowDiscrepancy, ...]
    schema_version: str = SHADOW_CONFORMANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_CONFORMANCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow comparison schema {self.schema_version!r}")
        if not isinstance(self.legacy_claim, LegacyWorkflowClaim):
            raise TypeError("legacy_claim must be LegacyWorkflowClaim")
        object.__setattr__(self, "machine_route_id", _nonempty(self.machine_route_id, "machine_route_id"))
        object.__setattr__(self, "machine_specialist_id", _nonempty(self.machine_specialist_id, "machine_specialist_id"))
        if not isinstance(self.machine_governance_required, bool):
            raise TypeError("machine_governance_required must be bool")
        if not isinstance(self.machine_validation_allowed, bool):
            raise TypeError("machine_validation_allowed must be bool")
        object.__setattr__(self, "machine_arbiter_disposition", _nonempty(self.machine_arbiter_disposition, "machine_arbiter_disposition"))
        if not isinstance(self.discrepancy_codes, tuple) or not all(
            isinstance(item, ShadowDiscrepancy) for item in self.discrepancy_codes
        ):
            raise TypeError("discrepancy_codes must contain ShadowDiscrepancy values")
        object.__setattr__(self, "discrepancy_codes", _ordered_discrepancies(list(self.discrepancy_codes)))

    @property
    def command_name(self) -> str:
        return self.legacy_claim.command_name

    @property
    def matches(self) -> bool:
        return not self.discrepancy_codes

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "legacy_claim": self.legacy_claim.to_dict(),
            "machine": {
                "route_id": self.machine_route_id,
                "specialist_id": self.machine_specialist_id,
                "governance_required": self.machine_governance_required,
                "validation_allowed": self.machine_validation_allowed,
                "arbiter_disposition": self.machine_arbiter_disposition,
            },
            "matches": self.matches,
            "discrepancy_codes": [item.value for item in self.discrepancy_codes],
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def compare_shadow_claim(
    claim: LegacyWorkflowClaim,
    *,
    machine_validation_allowed: bool,
    machine_arbiter_result: ArbiterKernelResult,
    root: Path | str | None = None,
) -> ShadowComparisonRecord:
    if not isinstance(claim, LegacyWorkflowClaim):
        raise TypeError("claim must be LegacyWorkflowClaim")
    if not isinstance(machine_validation_allowed, bool):
        raise TypeError("machine_validation_allowed must be bool")
    if not isinstance(machine_arbiter_result, ArbiterKernelResult):
        raise TypeError("machine_arbiter_result must be ArbiterKernelResult")

    expected_route = command_route_record(claim.command_name, root)
    machine_specialist = expected_route["specialist"]
    machine_governance_required = machine_specialist in governance_required_specialists(root)
    machine_disposition = machine_arbiter_result.disposition.value
    discrepancies: list[ShadowDiscrepancy] = []

    known_specialists = valid_specialist_ids(root)
    if claim.specialist_id not in known_specialists:
        discrepancies.append(ShadowDiscrepancy.UNKNOWN_LEGACY_SPECIALIST)
    if claim.specialist_id != machine_specialist:
        discrepancies.append(ShadowDiscrepancy.SPECIALIST_MISMATCH)
    if claim.governance_required is not machine_governance_required:
        discrepancies.append(ShadowDiscrepancy.GOVERNANCE_REQUIRED_MISMATCH)
    if claim.validation_allowed is not machine_validation_allowed:
        discrepancies.append(ShadowDiscrepancy.VALIDATION_MISMATCH)

    known_dispositions = {item.value for item in TransitionDisposition}
    if claim.arbiter_disposition not in known_dispositions:
        discrepancies.append(ShadowDiscrepancy.UNKNOWN_LEGACY_DISPOSITION)
    elif claim.arbiter_disposition != machine_disposition:
        discrepancies.append(ShadowDiscrepancy.ARBITER_DISPOSITION_MISMATCH)

    if not claim.evidence_digests:
        discrepancies.append(ShadowDiscrepancy.MISSING_EVIDENCE_DIGEST)

    return ShadowComparisonRecord(
        legacy_claim=claim,
        machine_route_id=expected_route["route_id"],
        machine_specialist_id=machine_specialist,
        machine_governance_required=machine_governance_required,
        machine_validation_allowed=machine_validation_allowed,
        machine_arbiter_disposition=machine_disposition,
        discrepancy_codes=_ordered_discrepancies(discrepancies),
    )


@dataclass(frozen=True, slots=True)
class ShadowConformanceReport:
    records: tuple[ShadowComparisonRecord, ...]
    migration_stage: MigrationStage | str = MigrationStage.SHADOW
    schema_version: str = SHADOW_CONFORMANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_CONFORMANCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow report schema {self.schema_version!r}")
        try:
            stage = self.migration_stage if isinstance(self.migration_stage, MigrationStage) else MigrationStage(_nonempty(self.migration_stage, "migration_stage"))
        except ValueError as exc:
            raise ValueError(f"unsupported migration_stage: {self.migration_stage!r}") from exc
        if stage is not MigrationStage.SHADOW:
            raise ValueError("P9 report construction is restricted to SHADOW stage")
        object.__setattr__(self, "migration_stage", stage)
        if not isinstance(self.records, tuple) or not all(isinstance(item, ShadowComparisonRecord) for item in self.records):
            raise TypeError("records must contain ShadowComparisonRecord values")
        ordered = tuple(sorted(self.records, key=lambda item: (item.command_name, item.digest)))
        object.__setattr__(self, "records", ordered)

    @property
    def discrepancy_count(self) -> int:
        return sum(len(record.discrepancy_codes) for record in self.records)

    @property
    def eligible_for_separately_governed_next_stage(self) -> bool:
        return bool(self.records) and self.discrepancy_count == 0

    @property
    def authorizes_execution(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        codes = sorted({code.value for record in self.records for code in record.discrepancy_codes})
        return {
            "schema_version": self.schema_version,
            "migration_stage": self.migration_stage.value,
            "authorizes_execution": self.authorizes_execution,
            "record_count": len(self.records),
            "record_digests": [record.digest for record in self.records],
            "discrepancy_count": self.discrepancy_count,
            "discrepancy_codes": codes,
            "eligible_for_separately_governed_next_stage": self.eligible_for_separately_governed_next_stage,
            "records": [record.to_dict() for record in self.records],
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())
