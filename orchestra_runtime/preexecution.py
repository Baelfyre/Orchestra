"""Compatibility facade for the AR-3 pre-execution application use case."""

from .application.use_cases.preexecution import (
    PREEXECUTION_SCHEMA_VERSION,
    ExecutionAction,
    ExecutionIntent,
    PreExecutionArbiterEvaluation,
    PreExecutionConstraint,
    PreExecutionGateResult,
    PreExecutionPolicy,
    PreExecutionReason,
    evaluate_preexecution,
    evaluate_preexecution_with_arbiter,
)

__all__ = [
    "PREEXECUTION_SCHEMA_VERSION",
    "ExecutionAction",
    "ExecutionIntent",
    "PreExecutionArbiterEvaluation",
    "PreExecutionConstraint",
    "PreExecutionGateResult",
    "PreExecutionPolicy",
    "PreExecutionReason",
    "evaluate_preexecution",
    "evaluate_preexecution_with_arbiter",
]
