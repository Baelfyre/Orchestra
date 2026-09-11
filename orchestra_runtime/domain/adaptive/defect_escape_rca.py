"""Deterministic, evidence-only AQ10 defect-escape root-cause analysis."""

# @codebase_provenance_JEO
# @codebase_rights_JEO
# @codebase_verified_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ10_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
CAUSE_PRECEDENCE = (
    "PROCESS_GOVERNANCE_GAP",
    "SCOPE_CLASSIFICATION_GAP",
    "ASSURANCE_TOOL_COMPATIBILITY",
    "DEPENDENCY_ENVIRONMENT_GAP",
    "ORACLE_GAP",
    "ASSERTION_GAP",
    "COVERAGE_GAP",
    "UNKNOWN",
)
SIGNAL_CAUSE = {
    "MISSING_TEST_SURFACE": "COVERAGE_GAP",
    "UNEXERCISED_BRANCH": "COVERAGE_GAP",
    "WEAK_ASSERTION": "ASSERTION_GAP",
    "MISSING_NEGATIVE_ASSERTION": "ASSERTION_GAP",
    "WRONG_EXPECTED_RESULT": "ORACLE_GAP",
    "SELF_ASSERTED_PASS": "ORACLE_GAP",
    "INCORRECT_SCOPE_CLASSIFICATION": "SCOPE_CLASSIFICATION_GAP",
    "UNREGISTERED_PHASE_COLLISION": "SCOPE_CLASSIFICATION_GAP",
    "MISSING_OPTIONAL_DEPENDENCY": "DEPENDENCY_ENVIRONMENT_GAP",
    "ENVIRONMENT_PARITY_MISMATCH": "DEPENDENCY_ENVIRONMENT_GAP",
    "MUTATION_OPERATOR_CRASH": "ASSURANCE_TOOL_COMPATIBILITY",
    "ASSURANCE_TOOL_INCOMPATIBILITY": "ASSURANCE_TOOL_COMPATIBILITY",
    "MISSING_GOVERNANCE_CONTRACT": "PROCESS_GOVERNANCE_GAP",
    "STALE_TRANSACTION_METADATA": "PROCESS_GOVERNANCE_GAP",
    "STALE_RELAY_PROJECTION": "PROCESS_GOVERNANCE_GAP",
    "CAUSE_UNRESOLVED": "UNKNOWN",
}
PREVENTION_ACTIONS = {
    "COVERAGE_GAP": ("EXPAND_TARGETED_TEST_COVERAGE",),
    "ASSERTION_GAP": ("STRENGTHEN_ASSERTIONS_AND_NEGATIVE_CASES",),
    "ORACLE_GAP": ("INDEPENDENT_ORACLE_CROSS_CHECK",),
    "SCOPE_CLASSIFICATION_GAP": ("EXACT_SCOPE_REGRESSION_AND_FAIL_CLOSED_CLASSIFICATION",),
    "DEPENDENCY_ENVIRONMENT_GAP": ("DEPENDENCY_FREE_BEHAVIOR_VALIDATION_OR_EXPLICIT_RUNTIME_DEPENDENCY",),
    "ASSURANCE_TOOL_COMPATIBILITY": ("TOOL_COMPATIBILITY_REGRESSION_WITH_UNKNOWN_OUTCOME_FAIL_CLOSED",),
    "PROCESS_GOVERNANCE_GAP": ("CONTRACT_PARITY_AND_COMPILER_GENERATED_RECONCILIATION",),
    "UNKNOWN": ("HUMAN_RCA_REVIEW_REQUIRED",),
}


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _identifiers(
    values: Iterable[str],
    field_name: str,
    *,
    uppercase: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(value, f"{field_name} item") for value in values)
    if uppercase:
        result = tuple(value.upper() for value in result)
    if not result:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return result


@dataclass(frozen=True, slots=True)
class DefectEscapeObservation:
    """Evidence-bound observation of a defect that escaped one or more earlier gates."""

    defect_id: str
    phase_detected: str
    escaped_gates: tuple[str, ...]
    detection_gate: str
    signals: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "defect_id", _text(self.defect_id, "defect_id"))
        object.__setattr__(self, "phase_detected", _text(self.phase_detected, "phase_detected").upper())
        object.__setattr__(
            self, "escaped_gates", _identifiers(self.escaped_gates, "escaped_gates", uppercase=True)
        )
        object.__setattr__(self, "detection_gate", _text(self.detection_gate, "detection_gate").upper())
        signals = _identifiers(self.signals, "signals", uppercase=True)
        unknown = tuple(signal for signal in signals if signal not in SIGNAL_CAUSE)
        if unknown:
            raise ValueError(f"signals contain unsupported values: {unknown}")
        object.__setattr__(self, "signals", signals)
        object.__setattr__(self, "evidence_ids", _identifiers(self.evidence_ids, "evidence_ids"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DefectEscapeObservation":
        if not isinstance(value, Mapping):
            raise TypeError("observation must be a mapping")
        required = {
            "defect_id", "phase_detected", "escaped_gates",
            "detection_gate", "signals", "evidence_ids",
        }
        if set(value) != required:
            raise ValueError("observation fields must match the AQ10 observation contract")
        return cls(
            defect_id=value["defect_id"],
            phase_detected=value["phase_detected"],
            escaped_gates=tuple(value["escaped_gates"]),
            detection_gate=value["detection_gate"],
            signals=tuple(value["signals"]),
            evidence_ids=tuple(value["evidence_ids"]),
        )


@dataclass(frozen=True, slots=True)
class DefectEscapeFinding:
    """Deterministic RCA output. It is evidence only and grants no authority."""

    defect_id: str
    root_cause: str
    contributing_causes: tuple[str, ...]
    escaped_gates: tuple[str, ...]
    detection_gate: str
    prevention_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    confidence: str
    human_review_required: bool
    authority_granted: bool = False
    automatic_policy_change: bool = False


@dataclass(frozen=True, slots=True)
class DefectEscapeSummary:
    """Stable aggregate evidence over a bounded set of defect escapes."""

    findings: tuple[DefectEscapeFinding, ...]
    cause_counts: tuple[tuple[str, int], ...]
    human_review_required_count: int
    authority_granted: bool = False
    automatic_policy_change: bool = False


def _ordered_causes(signals: tuple[str, ...]) -> tuple[str, ...]:
    observed = {SIGNAL_CAUSE[signal] for signal in signals}
    return tuple(cause for cause in CAUSE_PRECEDENCE if cause in observed)


def classify_defect_escape(observation: DefectEscapeObservation) -> DefectEscapeFinding:
    """Classify one escape using only explicit evidence signals and fixed precedence."""

    if not isinstance(observation, DefectEscapeObservation):
        raise TypeError("observation must be DefectEscapeObservation")
    causes = _ordered_causes(observation.signals)
    if not causes:
        raise ValueError("at least one classified cause is required")
    root_cause = causes[0]
    contributing = causes[1:]
    actions: list[str] = []
    for cause in causes:
        for action in PREVENTION_ACTIONS[cause]:
            if action not in actions:
                actions.append(action)
    human_review = "UNKNOWN" in causes
    confidence = "LOW" if human_review else ("HIGH" if len(causes) == 1 else "MEDIUM")
    reason_codes = tuple(f"AQ10_{cause}" for cause in causes)
    if len(causes) > 1:
        reason_codes = (*reason_codes, "AQ10_MULTI_CAUSE_ESCAPE")
    if human_review:
        reason_codes = (*reason_codes, "AQ10_HUMAN_RCA_REQUIRED")
    return DefectEscapeFinding(
        defect_id=observation.defect_id,
        root_cause=root_cause,
        contributing_causes=contributing,
        escaped_gates=observation.escaped_gates,
        detection_gate=observation.detection_gate,
        prevention_actions=tuple(actions),
        reason_codes=reason_codes,
        evidence_ids=observation.evidence_ids,
        confidence=confidence,
        human_review_required=human_review,
    )


def analyze_defect_escapes(
    observations: Iterable[DefectEscapeObservation],
) -> DefectEscapeSummary:
    """Analyze a bounded collection deterministically and reject duplicate defect identities."""

    if isinstance(observations, (str, bytes)):
        raise TypeError("observations must be an iterable of DefectEscapeObservation")
    materialized = tuple(observations)
    if not materialized:
        raise ValueError("observations must contain at least one item")
    if any(not isinstance(item, DefectEscapeObservation) for item in materialized):
        raise TypeError("observations must contain only DefectEscapeObservation values")
    ids = tuple(item.defect_id for item in materialized)
    if len(ids) != len(set(ids)):
        raise ValueError("observations must not contain duplicate defect_id values")
    findings = tuple(
        sorted((classify_defect_escape(item) for item in materialized), key=lambda item: item.defect_id)
    )
    cause_counts = tuple(
        (cause, sum(1 for finding in findings if finding.root_cause == cause))
        for cause in CAUSE_PRECEDENCE
        if any(finding.root_cause == cause for finding in findings)
    )
    return DefectEscapeSummary(
        findings=findings,
        cause_counts=cause_counts,
        human_review_required_count=sum(finding.human_review_required for finding in findings),
    )
