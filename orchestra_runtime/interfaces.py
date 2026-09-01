"""Compatibility facade for application runtime ports.

New code should import from ``orchestra_runtime.application.ports``.
"""

# ARCHITECTURE_COMPATIBILITY_FACADE
from .application.ports.runtime import (
    IAuditSink,
    IAuthorityEvaluator,
    ICapabilityResolver,
    ICoordinationController,
    IDelegationValidator,
    IGovernanceValidator,
    IIDEAdapter,
    ILifecycleController,
    IRouterService,
    IRuntimeExecutor,
    ISkillRegistry,
    ISpecialistExecutionEngine,
)

__all__ = [
    "IIDEAdapter",
    "ISkillRegistry",
    "IRouterService",
    "IGovernanceValidator",
    "IRuntimeExecutor",
    "IAuditSink",
    "IAuthorityEvaluator",
    "ICapabilityResolver",
    "IDelegationValidator",
    "ILifecycleController",
    "ICoordinationController",
    "ISpecialistExecutionEngine",
]
