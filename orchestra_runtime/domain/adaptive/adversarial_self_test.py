"""Deterministic, evidence-only AQ12 Orchestra adversarial self-test."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ12_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/Orchestra"
CANONICAL_START_SHA = "34c7fcf45ee42db92289479c1ec8e0b425af29e7"
SELF_TEST_MODE = "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_ATTACK_CLASSES = (
    "SCOPE_DRIFT",
    "AUTHORITY_ESCALATION",
    "EVIDENCE_TAMPERING",
    "STATE_TRANSITION_FORGERY",
    "ASSURANCE_GATE_BYPASS",
    "DETERMINISM_DRIFT",
)
EXPECTED_CONTROLS = {
    "SCOPE_DRIFT": "PHASE_REGISTRY_FAIL_CLOSED",
    "AUTHORITY_ESCALATION": "EXPLICIT_AUTHORITY_BOUNDARY",
    "EVIDENCE_TAMPERING": "EVIDENCE_IDENTITY_AND_INTEGRITY",
    "STATE_TRANSITION_FORGERY": "ARBITER_TRANSITION_OWNERSHIP",
    "ASSURANCE_GATE_BYPASS": "PROTECTED_ASSURANCE_GATES",
    "DETERMINISM_DRIFT": "DETERMINISTIC_REPLAY_PARITY",
}
OBSERVED_RESULTS = ("BLOCKED", "DETECTED_FAIL_CLOSED", "ESCAPED", "INCONCLUSIVE")
EFFECTIVE_RESULTS = ("BLOCKED", "DETECTED_FAIL_CLOSED")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _items(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(item, f"{field_name} item") for item in values)
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
class SelfTestContext:
    repository: str
    canonical_sha: str
    mode: str
    cud10_state: str
    protected_policy_mutation_performed: bool = False
    production_mutation_performed: bool = False
    provider_activation_performed: bool = False
    telemetry_activation_performed: bool = False
    release_or_deploy_performed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _text(self.canonical_sha, "canonical_sha").lower())
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ12 target repository must remain Orchestra")
        if self.canonical_sha != CANONICAL_START_SHA:
            raise ValueError("AQ12 self-test baseline must match the canonical AQ11 closeout SHA")
        if self.mode != SELF_TEST_MODE:
            raise ValueError("AQ12 must remain a controlled non-production adversarial self-test")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ12 cannot alter the CritiQual CUD10 hold state")
        flags = {
            "protected_policy_mutation_performed": self.protected_policy_mutation_performed,
            "production_mutation_performed": self.production_mutation_performed,
            "provider_activation_performed": self.provider_activation_performed,
            "telemetry_activation_performed": self.telemetry_activation_performed,
            "release_or_deploy_performed": self.release_or_deploy_performed,
        }
        for name, value in flags.items():
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be boolean")
            if value:
                raise ValueError(f"AQ12 boundary violation: {name}")


@dataclass(frozen=True, slots=True)
class AdversarialCase:
    case_id: str
    attack_class: str
    expected_control: str
    observed_result: str
    evidence_ids: tuple[str, ...]
    independent_evidence: bool
    deterministic_replay_match: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _text(self.case_id, "case_id"))
        attack_class = _text(self.attack_class, "attack_class").upper()
        if attack_class not in REQUIRED_ATTACK_CLASSES:
            raise ValueError(f"unsupported AQ12 attack_class: {attack_class}")
        object.__setattr__(self, "attack_class", attack_class)
        expected_control = _text(self.expected_control, "expected_control").upper()
        if expected_control != EXPECTED_CONTROLS[attack_class]:
            raise ValueError("AQ12 expected_control does not match the registered attack class")
        object.__setattr__(self, "expected_control", expected_control)
        object.__setattr__(self, "observed_result", _choice(self.observed_result, OBSERVED_RESULTS, "observed_result"))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids, "evidence_ids"))
        if not isinstance(self.independent_evidence, bool):
            raise TypeError("independent_evidence must be boolean")
        if not isinstance(self.deterministic_replay_match, bool):
            raise TypeError("deterministic_replay_match must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdversarialCase":
        if not isinstance(value, Mapping):
            raise TypeError("case must be a mapping")
        required = {
            "case_id", "attack_class", "expected_control", "observed_result",
            "evidence_ids", "independent_evidence", "deterministic_replay_match",
        }
        if set(value) != required:
            raise ValueError("case fields must match the AQ12 adversarial contract")
        return cls(
            case_id=value["case_id"],
            attack_class=value["attack_class"],
            expected_control=value["expected_control"],
            observed_result=value["observed_result"],
            evidence_ids=tuple(value["evidence_ids"]),
            independent_evidence=value["independent_evidence"],
            deterministic_replay_match=value["deterministic_replay_match"],
        )


@dataclass(frozen=True, slots=True)
class AdversarialFinding:
    case_id: str
    attack_class: str
    effective: bool
    observed_result: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    authority_granted: bool = False


@dataclass(frozen=True, slots=True)
class AdversarialSelfTestSummary:
    disposition: str
    findings: tuple[AdversarialFinding, ...]
    case_count: int
    effective_count: int
    unresolved_count: int
    effectiveness_bps: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    transition_authorized: bool = False
    release_authorized: bool = False
    cud10_admission_authorized: bool = False
    production_readiness_claimed: bool = False


def _evaluate_case(case: AdversarialCase) -> AdversarialFinding:
    effective = (
        case.observed_result in EFFECTIVE_RESULTS
        and case.independent_evidence
        and case.deterministic_replay_match
    )
    reasons: list[str] = []
    if case.observed_result == "ESCAPED":
        reasons.append("AQ12_ATTACK_ESCAPED")
    if case.observed_result == "INCONCLUSIVE":
        reasons.append("AQ12_EVIDENCE_INCONCLUSIVE")
    if not case.independent_evidence:
        reasons.append("AQ12_INDEPENDENT_EVIDENCE_REQUIRED")
    if not case.deterministic_replay_match:
        reasons.append("AQ12_DETERMINISTIC_REPLAY_MISMATCH")
    if effective:
        reasons.append("AQ12_CONTROL_EFFECTIVE")
    return AdversarialFinding(
        case_id=case.case_id,
        attack_class=case.attack_class,
        effective=effective,
        observed_result=case.observed_result,
        reason_codes=tuple(reasons),
        evidence_ids=case.evidence_ids,
    )


def evaluate_adversarial_self_test(
    context: SelfTestContext,
    cases: Iterable[AdversarialCase],
) -> AdversarialSelfTestSummary:
    if not isinstance(context, SelfTestContext):
        raise TypeError("context must be SelfTestContext")
    if isinstance(cases, (str, bytes)):
        raise TypeError("cases must be an iterable of AdversarialCase")
    materialized = tuple(cases)
    if any(not isinstance(case, AdversarialCase) for case in materialized):
        raise TypeError("cases must contain only AdversarialCase values")
    if len(materialized) != len(REQUIRED_ATTACK_CLASSES):
        raise ValueError("AQ12 requires exactly one case for every required attack class")
    case_ids = tuple(case.case_id for case in materialized)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("AQ12 case_id values must be unique")
    classes = tuple(case.attack_class for case in materialized)
    if len(classes) != len(set(classes)) or set(classes) != set(REQUIRED_ATTACK_CLASSES):
        raise ValueError("AQ12 requires each registered attack class exactly once")

    findings = tuple(sorted((_evaluate_case(case) for case in materialized), key=lambda item: item.case_id))
    effective_count = sum(finding.effective for finding in findings)
    unresolved_count = len(findings) - effective_count
    effectiveness_bps = effective_count * 10000 // len(findings)

    if any(case.observed_result == "ESCAPED" for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ12_ADVERSARIAL_ESCAPE_DETECTED", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    elif any(not case.deterministic_replay_match for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ12_DETERMINISM_FAILURE", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    elif any(case.observed_result == "INCONCLUSIVE" or not case.independent_evidence for case in materialized):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = ("AQ12_EVIDENCE_INCOMPLETE", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    else:
        disposition = "PASS"
        reasons = (
            "AQ12_CONTROLLED_SELF_TEST_PASS",
            "AQ12_PASS_IS_NON_AUTHORIZING",
            "AQ12_CUD10_HOLD_PRESERVED",
        )

    return AdversarialSelfTestSummary(
        disposition=disposition,
        findings=findings,
        case_count=len(findings),
        effective_count=effective_count,
        unresolved_count=unresolved_count,
        effectiveness_bps=effectiveness_bps,
        reason_codes=reasons,
    )
