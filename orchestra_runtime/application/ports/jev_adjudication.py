"""Ports for advisory JEV transport and trusted candidate freshness lookup."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

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


@runtime_checkable
class CurrentJevCandidateBindingProvider(Protocol):
    """Trusted host lookup used before and after one advisory provider request."""

    def current_binding(self) -> JevCandidateBinding | None: ...


__all__ = ["CurrentJevCandidateBindingProvider", "JevAdjudicationProvider"]
