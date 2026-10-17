"""Ports for advisory JEV transport and trusted candidate freshness lookup."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Protocol, runtime_checkable

from ...domain.adaptive.jev_adjudication import (
    JevCandidateBinding,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
)


@runtime_checkable
class JevAdjudicationProvider(Protocol):
    def adjudicate(
        self,
        state: OrchestraJevAdjudicationState,
        questions: Mapping[str, Mapping[str, object]],
    ) -> JevProviderResponse: ...


class JevProviderRequestProjectionContext(ABC):
    """Local capability for validating and restoring one sanitized provider request."""

    __slots__ = ()

    @abstractmethod
    def validate_request(
        self,
        state: OrchestraJevAdjudicationState,
        request_bytes: bytes,
    ) -> Mapping[str, object]:
        raise NotImplementedError

    @abstractmethod
    def restore_response(
        self,
        state: OrchestraJevAdjudicationState,
        request_bytes: bytes,
        response: JevProviderResponse,
    ) -> JevProviderResponse:
        raise NotImplementedError


@runtime_checkable
class CurrentJevCandidateBindingProvider(Protocol):
    """Trusted host lookup used before and after one advisory provider request."""

    def current_binding(self) -> JevCandidateBinding | None: ...


__all__ = [
    "CurrentJevCandidateBindingProvider",
    "JevAdjudicationProvider",
    "JevProviderRequestProjectionContext",
]
