"""Pure execution-domain identity, operation, and lifecycle semantics."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from .operation_contracts import (
    DEFENSIVE_SECURITY_REVIEW,
    REGISTERED_OPERATION_CONTRACTS,
    SECURITY_SENSITIVE_EXECUTION,
    OperationAuthority,
    OperationContract,
    OperationKind,
    ReadOnlySpecialistExecutionRequest,
    RoutingDisposition,
    SpecialistReviewResult,
    SpecialistReviewStatus,
    SpecialistSideEffectClass,
    operation_contract_for_route,
)

from .correlation import is_valid_correlation_id, validate_correlation_id
from .identity import RunIdentity
from .lifecycle import (
    LIFECYCLE_TRANSITIONS,
    SIGNAL_DESTINATIONS,
    SIGNAL_SOURCE_STATES,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
    apply_lifecycle_signal,
    initialize_lifecycle_snapshot,
    lifecycle_signal_fingerprint,
)

__all__ = (
    "DEFENSIVE_SECURITY_REVIEW",
    "REGISTERED_OPERATION_CONTRACTS",
    "SECURITY_SENSITIVE_EXECUTION",
    "OperationAuthority",
    "OperationContract",
    "OperationKind",
    "ReadOnlySpecialistExecutionRequest",
    "RoutingDisposition",
    "SpecialistReviewResult",
    "SpecialistReviewStatus",
    "SpecialistSideEffectClass",
    "operation_contract_for_route",
    "LIFECYCLE_TRANSITIONS",
    "SIGNAL_DESTINATIONS",
    "SIGNAL_SOURCE_STATES",
    "LifecycleSignal",
    "LifecycleSignalType",
    "LifecycleSnapshot",
    "LifecycleState",
    "RunIdentity",
    "StructuredTerminalResult",
    "apply_lifecycle_signal",
    "initialize_lifecycle_snapshot",
    "is_valid_correlation_id",
    "lifecycle_signal_fingerprint",
    "validate_correlation_id",
)
