"""Governance-domain semantics for Orchestra runtime architecture."""

from .authority import (
    AuthorityDecision,
    AuthorityProvenance,
    AuthorityReasonCode,
    AuthorityScope,
    Constraint,
    ConstraintKind,
    ProvenanceSource,
    TargetSelector,
    TargetSelectorType,
)
from .kernel import (
    GOVERNANCE_KERNEL_SCHEMA_VERSION,
    ArbiterKernelResult,
    ArbiterReasonCode,
    GovernanceDecision,
    GovernanceDecisionRecord,
    TransitionDisposition,
)
from .preexecution import (
    PREEXECUTION_SCHEMA_VERSION,
    ExecutionAction,
    ExecutionIntent,
    PreExecutionConstraint,
    PreExecutionPolicy,
    PreExecutionReason,
)

__all__ = [
    "GOVERNANCE_KERNEL_SCHEMA_VERSION",
    "PREEXECUTION_SCHEMA_VERSION",
    "ArbiterKernelResult",
    "ArbiterReasonCode",
    "AuthorityDecision",
    "AuthorityProvenance",
    "AuthorityReasonCode",
    "AuthorityScope",
    "Constraint",
    "ConstraintKind",
    "ExecutionAction",
    "ExecutionIntent",
    "GovernanceDecision",
    "GovernanceDecisionRecord",
    "PreExecutionConstraint",
    "PreExecutionPolicy",
    "PreExecutionReason",
    "ProvenanceSource",
    "TargetSelector",
    "TargetSelectorType",
    "TransitionDisposition",
]
