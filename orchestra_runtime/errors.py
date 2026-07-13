from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum


class RuntimeContractError(ValueError):
    """Base error carrying a stable reason code and immutable safe context."""

    def __init__(
        self,
        message: str,
        reason_code: str | Enum,
        context: Mapping[str, str] | Iterable[tuple[str, str]] | None = None,
    ) -> None:
        code = reason_code.value if isinstance(reason_code, Enum) else str(reason_code).strip()
        if not code:
            raise ValueError("reason_code must be non-empty")
        items = tuple(sorted((str(key), str(value)) for key, value in (context or {}).items())) if isinstance(
            context, Mapping
        ) else tuple(sorted((str(key), str(value)) for key, value in (context or ())))
        if len({key for key, _ in items}) != len(items):
            raise ValueError("error context keys must be unique")
        self.reason_code = code
        self.context = items
        super().__init__(message)


class InvalidAuthorityConfigurationError(RuntimeContractError):
    pass


class AuthorityDeniedError(RuntimeContractError):
    pass


class InvalidCapabilityConfigurationError(RuntimeContractError):
    pass


class CapabilityCollisionError(RuntimeContractError):
    pass


class CapabilityDeniedError(RuntimeContractError):
    pass


class DelegationRejectedError(RuntimeContractError):
    pass


class DelegationDepthViolationError(RuntimeContractError):
    pass


class InvalidLifecycleTransitionError(RuntimeContractError):
    pass


class InvalidLifecycleSignalError(RuntimeContractError):
    pass


class ConflictingTerminalSignalError(RuntimeContractError):
    pass
