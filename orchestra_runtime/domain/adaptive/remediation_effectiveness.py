"""Deterministic, evidence-only AQ11 remediation effectiveness pilot."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ11_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/CritiQual"
TARGET_CANONICAL_SHA = "166bbac50a4f02e222aa15ff914c60cec658b7c0"
TARGET_INCIDENT = "Baelfyre/Padayon#441"
PILOT_MODE = "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_ESCAPE_CLASSES = (
    "PROVENANCE_OWNERSHIP",
    "AGGREGATE_CONCURRENCY",
    "CALIBRATION_EVIDENCE_INTEGRITY",
    "AUTHORITY_BOUNDARY",
    "RUNTIME_INTEGRATION",
    "GATE_COVERAGE_TRUTHFULNESS",
)
BEFORE_RESULTS = ("REPRODUCED_DEFECT", "STATIC_RISK_CONFIRMED")
AFTER_RESULTS = ("PREVENTED", "DETECTED_BEFORE_TRANSITION", "STILL_ESCAPES", "INCONCLUSIVE")
EFFECTIVE_AFTER_RESULTS = ("PREVENTED", "DETECTED_BEFORE_TRANSITION")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _items(values: Iterable[str], field_name: str, *, uppercase: bool = False) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(item, f"{field_name} item") for item in values)
    if uppercase:
        result = tuple(item.upper() for item in result)
    if not result:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return result


def _choice(value: Any, choices: tuple[str, ...], field_name: str) -> str:
    normalized = _text(value, field_name).upper()
    if normalized not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return normalized


@dataclass(frozen=True, slots=True)
class PilotContext:
    repository: str
    canonical_sha: str
    incident_reference: str
    mode: str
    cud10_state: str
    source_mutation_performed: bool = False
    production_evidence: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _text(self.canonical_sha, "canonical_sha").lower())
        object.__setattr__(self, "incident_reference", _text(self.incident_reference, "incident_reference"))
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ11 pilot repository must remain CritiQual")
        if self.canonical_sha != TARGET_CANONICAL_SHA:
            raise ValueError("AQ11 pilot baseline must match the observed held CritiQual canonical SHA")
        if self.incident_reference != TARGET_INCIDENT:
            raise ValueError("AQ11 pilot incident reference drift")
        if self.mode != PILOT_MODE:
            raise ValueError("AQ11 pilot must remain controlled non-production evidence only")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ11 pilot cannot alter the CUD10 hold state")
        if self.source_mutation_performed:
            raise ValueError("AQ11 pilot cannot mutate CritiQual source")
        if self.production_evidence:
            raise ValueError("AQ11 pilot cannot consume or claim production evidence")


@dataclass(frozen=True, slots=True)
class RemediationCase:
    case_id: str
    escape_class: str
    before_result: str
    after_result: str
    remediation_actions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    independent_evidence: bool
    recurrence_observed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _text(self.case_id, "case_id"))
        escape_class = _text(self.escape_class, "escape_class").upper()
        if escape_class not in REQUIRED_ESCAPE_CLASSES:
            raise ValueError(f"unsupported AQ11 escape_class: {escape_class}")
        object.__setattr__(self, "escape_class", escape_class)
        object.__setattr__(self, "before_result", _choice(self.before_result, BEFORE_RESULTS, "before_result"))
        object.__setattr__(self, "after_result", _choice(self.after_result, AFTER_RESULTS, "after_result"))
        object.__setattr__(self, "remediation_actions", _items(self.remediation_actions, "remediation_actions", uppercase=True))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids, "evidence_ids"))
        if not isinstance(self.independent_evidence, bool):
            raise TypeError("independent_evidence must be boolean")
        if not isinstance(self.recurrence_observed, bool):
            raise TypeError("recurrence_observed must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RemediationCase":
        if not isinstance(value, Mapping):
            raise TypeError("case must be a mapping")
        required = {"case_id", "escape_class", "before_result", "after_result", "remediation_actions", "evidence_ids", "independent_evidence", "recurrence_observed"}
        if set(value) != required:
            raise ValueError("case fields must match the AQ11 remediation contract")
        return cls(
            case_id=value["case_id"], escape_class=value["escape_class"],
            before_result=value["before_result"], after_result=value["after_result"],
            remediation_actions=tuple(value["remediation_actions"]), evidence_ids=tuple(value["evidence_ids"]),
            independent_evidence=value["independent_evidence"], recurrence_observed=value["recurrence_observed"],
        )


@dataclass(frozen=True, slots=True)
class RemediationCaseFinding:
    case_id: str
    escape_class: str
    effective: bool
    after_result: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    authority_granted: bool = False
    cud10_admission_authorized: bool = False


@dataclass(frozen=True, slots=True)
class RemediationPilotSummary:
    disposition: str
    findings: tuple[RemediationCaseFinding, ...]
    case_count: int
    effective_count: int
    unresolved_count: int
    effectiveness_bps: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    cud10_admission_authorized: bool = False
    production_readiness_claimed: bool = False
    organic_effectiveness_claimed: bool = False


def _evaluate_case(case: RemediationCase) -> RemediationCaseFinding:
    effective = (
        case.after_result in EFFECTIVE_AFTER_RESULTS
        and case.independent_evidence
        and not case.recurrence_observed
    )
    reasons: list[str] = []
    if case.after_result == "STILL_ESCAPES":
        reasons.append("AQ11_ESCAPE_REMAINS")
    if case.after_result == "INCONCLUSIVE":
        reasons.append("AQ11_AFTER_EVIDENCE_INCONCLUSIVE")
    if not case.independent_evidence:
        reasons.append("AQ11_INDEPENDENT_EVIDENCE_REQUIRED")
    if case.recurrence_observed:
        reasons.append("AQ11_RECURRENCE_OBSERVED")
    if effective:
        reasons.append("AQ11_CONTROLLED_REMEDIATION_EFFECTIVE")
    return RemediationCaseFinding(
        case_id=case.case_id,
        escape_class=case.escape_class,
        effective=effective,
        after_result=case.after_result,
        reason_codes=tuple(reasons),
        evidence_ids=case.evidence_ids,
    )


def evaluate_remediation_pilot(context: PilotContext, cases: Iterable[RemediationCase]) -> RemediationPilotSummary:
    if not isinstance(context, PilotContext):
        raise TypeError("context must be PilotContext")
    if isinstance(cases, (str, bytes)):
        raise TypeError("cases must be an iterable of RemediationCase")
    materialized = tuple(cases)
    if any(not isinstance(case, RemediationCase) for case in materialized):
        raise TypeError("cases must contain only RemediationCase values")
    if len(materialized) != len(REQUIRED_ESCAPE_CLASSES):
        raise ValueError("AQ11 pilot requires exactly one case for every required escape class")
    case_ids = tuple(case.case_id for case in materialized)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("AQ11 pilot case_id values must be unique")
    classes = tuple(case.escape_class for case in materialized)
    if len(classes) != len(set(classes)) or set(classes) != set(REQUIRED_ESCAPE_CLASSES):
        raise ValueError("AQ11 pilot requires each registered escape class exactly once")
    findings = tuple(sorted((_evaluate_case(case) for case in materialized), key=lambda item: item.case_id))
    effective_count = sum(finding.effective for finding in findings)
    unresolved_count = len(findings) - effective_count
    effectiveness_bps = effective_count * 10000 // len(findings)
    if any(case.after_result == "STILL_ESCAPES" or case.recurrence_observed for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ11_REMEDIATION_NOT_EFFECTIVE", "AQ11_CUD10_HOLD_PRESERVED")
    elif any(case.after_result == "INCONCLUSIVE" or not case.independent_evidence for case in materialized):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = ("AQ11_EFFECTIVENESS_EVIDENCE_INCOMPLETE", "AQ11_CUD10_HOLD_PRESERVED")
    elif effectiveness_bps == 10000:
        disposition = "PASS"
        reasons = ("AQ11_CONTROLLED_PILOT_PASS", "AQ11_PASS_IS_NON_ADMITTING", "AQ11_CUD10_HOLD_PRESERVED")
    else:
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ11_EFFECTIVENESS_THRESHOLD_NOT_MET", "AQ11_CUD10_HOLD_PRESERVED")
    return RemediationPilotSummary(
        disposition=disposition,
        findings=findings,
        case_count=len(findings),
        effective_count=effective_count,
        unresolved_count=unresolved_count,
        effectiveness_bps=effectiveness_bps,
        reason_codes=reasons,
    )
