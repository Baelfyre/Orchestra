"""Compatibility facade for shared runtime contract errors.

New code should import from ``orchestra_runtime.shared.errors``.
"""

# ARCHITECTURE_COMPATIBILITY_FACADE
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
    "RuntimeContractError",
    "InvalidAuthorityConfigurationError",
    "AuthorityDeniedError",
    "InvalidCapabilityConfigurationError",
    "CapabilityCollisionError",
    "CapabilityDeniedError",
    "DelegationRejectedError",
    "DelegationDepthViolationError",
    "InvalidLifecycleTransitionError",
    "InvalidLifecycleSignalError",
    "ConflictingTerminalSignalError",
    "RuntimeInitializationError",
    "RuntimeBindingError",
    "RuntimeAuditError",
    "InvalidCoordinationContractError",
    "InvalidCoordinationTransitionError",
    "InvalidCoordinationSignalError",
    "CoordinationReadinessError",
    "ConflictingCoordinationSignalError",
]
