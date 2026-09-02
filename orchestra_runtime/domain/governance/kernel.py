from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...shared.canonicalization import receipt_digest


GOVERNANCE_KERNEL_SCHEMA_VERSION = "1.0.0"


class GovernanceDecision(str, Enum):
    APPROVED = "APPROVED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TransitionDisposition(str, Enum):
    AUTO_CONTINUE = "AUTO_CONTINUE"
    AUTO_REMEDIATE_AND_REVALIDATE = "AUTO_REMEDIATE_AND_REVALIDATE"
    WAIT_FOR_EVIDENCE = "WAIT_FOR_EVIDENCE"
    WAIT_FOR_CAPACITY = "WAIT_FOR_CAPACITY"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"
    STOP = "STOP"


class ArbiterReasonCode(str, Enum):
    AUTHORITY_INVALID = "AUTHORITY_INVALID"
    PROTECTED_BOUNDARY_VIOLATION = "PROTECTED_BOUNDARY_VIOLATION"
    GOVERNANCE_BLOCKED = "GOVERNANCE_BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    SCOPE_OR_POLICY_DECISION_REQUIRED = "SCOPE_OR_POLICY_DECISION_REQUIRED"
    EXTERNAL_AUTHORITY_REQUIRED = "EXTERNAL_AUTHORITY_REQUIRED"
    CONTRADICTION_UNRESOLVED = "CONTRADICTION_UNRESOLVED"
    REVISION_NOT_AUTOREMEDIABLE = "REVISION_NOT_AUTOREMEDIABLE"
    REMEDIATION_BUDGET_EXHAUSTED = "REMEDIATION_BUDGET_EXHAUSTED"
    IDENTICAL_FAILURE_LIMIT_EXCEEDED = "IDENTICAL_FAILURE_LIMIT_EXCEEDED"
    HOST_CAPACITY_UNAVAILABLE = "HOST_CAPACITY_UNAVAILABLE"
    GOVERNANCE_EVIDENCE_INCOMPLETE = "GOVERNANCE_EVIDENCE_INCOMPLETE"
    REQUIRED_RECEIPT_MISSING = "REQUIRED_RECEIPT_MISSING"
    EXACT_STATE_MISMATCH = "EXACT_STATE_MISMATCH"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    BOUNDED_REMEDIATION_AVAILABLE = "BOUNDED_REMEDIATION_AVAILABLE"
    CONTINUATION_READY = "CONTINUATION_READY"
    MALFORMED_INPUT = "MALFORMED_INPUT"


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    return cleaned


def _enum(value: str | Enum, enum_type: type[Enum], field_name: str):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(_nonempty(value, field_name))
    except ValueError as exc:
        raise ValueError(f"unsupported {field_name}: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class GovernanceDecisionRecord:
    reviewer: str
    project_context: str
    decision: GovernanceDecision | str
    reason: str
    risks: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    human_review_required: bool = False
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = GOVERNANCE_KERNEL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != GOVERNANCE_KERNEL_SCHEMA_VERSION:
            raise ValueError(f"unsupported governance decision schema {self.schema_version!r}")
        object.__setattr__(self, "reviewer", _nonempty(self.reviewer, "reviewer"))
        object.__setattr__(self, "project_context", _nonempty(self.project_context, "project_context"))
        object.__setattr__(self, "decision", _enum(self.decision, GovernanceDecision, "decision"))
        object.__setattr__(self, "reason", _nonempty(self.reason, "reason"))
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be bool")
        for name in ("risks", "required_actions", "evidence_refs"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            object.__setattr__(self, name, tuple(_nonempty(item, name) for item in values))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "reviewer": self.reviewer,
            "project_context": self.project_context,
            "decision": self.decision.value,
            "reason": self.reason,
            "risks": list(self.risks),
            "required_actions": list(self.required_actions),
            "human_review_required": self.human_review_required,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class ArbiterKernelResult:
    disposition: TransitionDisposition
    reason_codes: tuple[ArbiterReasonCode, ...]
    input_digest: str
    schema_version: str = GOVERNANCE_KERNEL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "disposition": self.disposition.value,
            "reason_codes": [item.value for item in self.reason_codes],
            "input_digest": self.input_digest,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())

    def assert_claimed_disposition(self, claimed: str) -> None:
        candidate = _enum(claimed, TransitionDisposition, "claimed_disposition")
        if candidate is not self.disposition:
            raise ValueError(
                f"claimed disposition {candidate.value!r} conflicts with "
                f"kernel disposition {self.disposition.value!r}"
            )


__all__ = [
    "GOVERNANCE_KERNEL_SCHEMA_VERSION",
    "ArbiterKernelResult",
    "ArbiterReasonCode",
    "GovernanceDecision",
    "GovernanceDecisionRecord",
    "TransitionDisposition",
]
