"""Pure domain rules for the AQ-1 adaptive assurance doctrine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

AQ1_DOCTRINE_SCHEMA_VERSION = "orchestra.adaptive-assurance-doctrine.v1"

DEVELOPMENT_MODES = (
    "SPEC_FIRST",
    "DISCOVERY_FIRST",
    "AS_BUILT",
    "RECONCILIATION",
    "DEFECT_DRIVEN",
    "MAINTENANCE",
)

SOURCE_TRUTH_LABELS = ("OBSERVED", "INFERRED", "DECIDED", "UNVERIFIED")

COMPLETION_STATES = (
    "IDEATED",
    "PROTOTYPED",
    "DOMAIN_IMPLEMENTED",
    "APPLICATION_INTEGRATED",
    "API_INTEGRATED",
    "UI_INTEGRATED",
    "UNIT_VERIFIED",
    "CONTRACT_VERIFIED",
    "INTEGRATION_VERIFIED",
    "RUNTIME_VERIFIED",
    "SECURITY_VERIFIED",
    "ADVERSARIALLY_VERIFIED",
    "CANONICAL_VERIFIED",
    "PRODUCT_COMPLETE",
)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _one_of(value: object, choices: tuple[str, ...], field_name: str) -> str:
    normalized = _text(value, field_name)
    if normalized not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return normalized


def _states(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("states must be an iterable of state strings")
    normalized = tuple(_one_of(value, COMPLETION_STATES, "completion state") for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError("completion states must not contain duplicates")
    return normalized


@dataclass(frozen=True, slots=True)
class AssuranceEvidence:
    evidence_id: str
    claimed_state: str
    source_truth: str
    authority_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(
            self,
            "claimed_state",
            _one_of(self.claimed_state, COMPLETION_STATES, "claimed_state"),
        )
        object.__setattr__(
            self,
            "source_truth",
            _one_of(self.source_truth, SOURCE_TRUTH_LABELS, "source_truth"),
        )
        if self.authority_ref is not None:
            object.__setattr__(self, "authority_ref", _text(self.authority_ref, "authority_ref"))


@dataclass(frozen=True, slots=True)
class CompletionAssessment:
    explicit_states: tuple[str, ...]
    target_state: str
    canonical_proves_empirical_effectiveness: bool = False
    product_complete: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "explicit_states", _states(self.explicit_states))
        object.__setattr__(
            self,
            "target_state",
            _one_of(self.target_state, COMPLETION_STATES, "target_state"),
        )
        if self.canonical_proves_empirical_effectiveness:
            raise ValueError("CANONICAL_VERIFIED cannot prove empirical effectiveness")


def validate_development_mode(mode: str) -> str:
    """Return a declared mode or fail closed on an unknown mode."""

    return _one_of(mode, DEVELOPMENT_MODES, "development mode")


def transition_mode(current_mode: str, target_mode: str) -> str:
    """Support explicit transitions among all declared AQ-1 modes."""

    validate_development_mode(current_mode)
    return validate_development_mode(target_mode)


def select_mode_for_evidence(current_mode: str, *, conflicting_sources: bool = False) -> str:
    """Select reconciliation when authoritative sources conflict."""

    current = validate_development_mode(current_mode)
    if not isinstance(conflicting_sources, bool):
        raise TypeError("conflicting_sources must be a bool")
    return "RECONCILIATION" if conflicting_sources else current


def validate_completion_escalation(
    current_states: Iterable[str],
    target_state: str,
    evidence: Iterable[AssuranceEvidence],
    *,
    claim_source_truth: str = "OBSERVED",
    authority_ref: str | None = None,
) -> CompletionAssessment:
    """Validate one explicit state claim without inferring higher states."""

    current = _states(current_states)
    target = _one_of(target_state, COMPLETION_STATES, "target_state")
    claim_truth = _one_of(claim_source_truth, SOURCE_TRUTH_LABELS, "claim_source_truth")
    records = tuple(evidence)
    if any(not isinstance(record, AssuranceEvidence) for record in records):
        raise TypeError("evidence must contain AssuranceEvidence values")
    if target not in current and not records:
        raise ValueError("completion-state escalation requires evidence")
    if target == "PRODUCT_COMPLETE" and not records:
        raise ValueError("PRODUCT_COMPLETE requires explicit evidence")
    if claim_truth == "UNVERIFIED" or any(record.source_truth == "UNVERIFIED" for record in records):
        raise ValueError("UNVERIFIED evidence cannot qualify a completion claim")
    if any(record.claimed_state != target for record in records):
        raise ValueError("completion evidence must claim the target state")
    authority = None if authority_ref is None else _text(authority_ref, "authority_ref")
    has_inferred_support = any(record.source_truth == "INFERRED" for record in records)
    if claim_truth == "DECIDED" and has_inferred_support and authority is None:
        raise ValueError("INFERRED evidence cannot become DECIDED without authority")
    if claim_truth == "INFERRED" and target not in {"IDEATED", "PROTOTYPED"} and authority is None:
        raise ValueError("inferred completion claims require authority beyond prototype states")

    explicit = tuple(dict.fromkeys((*current, target)))
    return CompletionAssessment(
        explicit_states=explicit,
        target_state=target,
        product_complete=target == "PRODUCT_COMPLETE",
    )


def validate_product_complete(
    mode: str,
    current_states: Iterable[str],
    evidence: Iterable[AssuranceEvidence],
    *,
    claim_source_truth: str = "OBSERVED",
    authority_ref: str | None = None,
    reconciled: bool = False,
) -> CompletionAssessment:
    """Apply the product-complete gates that AQ-1 makes explicit."""

    selected_mode = validate_development_mode(mode)
    if not isinstance(reconciled, bool):
        raise TypeError("reconciled must be a bool")
    assessment = validate_completion_escalation(
        current_states,
        "PRODUCT_COMPLETE",
        evidence,
        claim_source_truth=claim_source_truth,
        authority_ref=authority_ref,
    )
    state_set = set(assessment.explicit_states)
    if selected_mode == "DISCOVERY_FIRST" and not reconciled:
        raise ValueError("DISCOVERY_FIRST requires RECONCILIATION before PRODUCT_COMPLETE")
    if "DOMAIN_IMPLEMENTED" in state_set and "APPLICATION_INTEGRATED" not in state_set:
        raise ValueError("domain-only implementation cannot be represented as product integration")
    return assessment


__all__ = [
    "AQ1_DOCTRINE_SCHEMA_VERSION",
    "AssuranceEvidence",
    "COMPLETION_STATES",
    "CompletionAssessment",
    "DEVELOPMENT_MODES",
    "SOURCE_TRUTH_LABELS",
    "select_mode_for_evidence",
    "transition_mode",
    "validate_completion_escalation",
    "validate_development_mode",
    "validate_product_complete",
]
