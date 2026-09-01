"""Backward-compatible facade for runtime contract errors.

Canonical implementations live under :mod:`orchestra_runtime.shared.errors` during
AR-2+ strangler migration. Keep this facade until all supported public and internal
imports have migrated and compatibility retirement is separately qualified.
"""

from .shared.errors import (
    AuthorityDeniedError,
    CapabilityCollisionError,
    CapabilityDeniedError,
    ConflictingCoordinationSignalError,
    ConflictingTerminalSignalError,
    CoordinationReadinessError,
    DelegationDepthViolationError,
    DelegationRejectedError,
    InvalidAuthorityConfigurationError,
    InvalidCapabilityConfigurationError,
    InvalidCoordinationContractError,
    InvalidCoordinationSignalError,
    InvalidCoordinationTransitionError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
    RuntimeAuditError,
    RuntimeBindingError,
    RuntimeContractError,
    RuntimeInitializationError,
)

__all__ = [
    "AuthorityDeniedError",
    "CapabilityCollisionError",
    "CapabilityDeniedError",
    "ConflictingCoordinationSignalError",
    "ConflictingTerminalSignalError",
    "CoordinationReadinessError",
    "DelegationDepthViolationError",
    "DelegationRejectedError",
    "InvalidAuthorityConfigurationError",
    "InvalidCapabilityConfigurationError",
    "InvalidCoordinationContractError",
    "InvalidCoordinationSignalError",
    "InvalidCoordinationTransitionError",
    "InvalidLifecycleSignalError",
    "InvalidLifecycleTransitionError",
    "RuntimeAuditError",
    "RuntimeBindingError",
    "RuntimeContractError",
    "RuntimeInitializationError",
]
