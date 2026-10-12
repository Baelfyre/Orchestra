"""Run optional JEV advice after upstream evidence and mitigation are complete."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from ...domain.adaptive.jev_adjudication import (
    JevAdjudicationEligibilityError,
    JevAdvisoryResult,
    JevCandidateBinding,
    JevProviderFailure,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
    OrchestraJevInterpreter,
    OrchestraJevQuestionBuilder,
    validate_jev_adjudication_eligibility,
)
from ...shared.canonicalization import canonical_json_bytes
from ..ports.jev_adjudication import (
    CurrentJevCandidateBindingProvider,
    JevAdjudicationProvider,
)


class OrchestraJevAdjudicationUseCase:
    """Call JEV once for an eligible, currently bound adjudication state."""

    def __init__(
        self,
        provider: JevAdjudicationProvider,
        candidate_binding_provider: CurrentJevCandidateBindingProvider,
    ) -> None:
        if not isinstance(provider, JevAdjudicationProvider):
            raise TypeError("provider must implement JevAdjudicationProvider")
        if not isinstance(candidate_binding_provider, CurrentJevCandidateBindingProvider):
            raise TypeError("candidate_binding_provider must implement CurrentJevCandidateBindingProvider")
        self._provider = provider
        self._candidate_binding_provider = candidate_binding_provider
        self._question_builder = OrchestraJevQuestionBuilder()
        self._interpreter = OrchestraJevInterpreter()

    def execute(self, state: OrchestraJevAdjudicationState) -> JevAdvisoryResult:
        if not isinstance(state, OrchestraJevAdjudicationState):
            raise TypeError("state must be OrchestraJevAdjudicationState")
        current = self._current_binding()
        if current is None:
            return self._interpreter.unbound(state)
        if current != state.candidate_binding:
            return self._interpreter.stale(state, current)

        validate_jev_adjudication_eligibility(state)
        if not _has_competing_material_alternatives(state):
            return self._interpreter.not_required(state)

        questions = self._question_builder.build(state)
        try:
            response = self._provider.adjudicate(state, questions)
            if not isinstance(response, JevProviderResponse):
                raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE")
        except JevProviderFailure as failure:
            return self._interpreter.unavailable(state, failure.code)
        except Exception:
            return self._interpreter.unavailable(state, "PROVIDER_FAILURE")

        try:
            return self._interpreter.interpret(state, response, self._current_binding())
        except (TypeError, ValueError):
            return self._interpreter.unavailable(state, "RESPONSE_CONTRACT_INCOMPATIBLE")

    def _current_binding(self):
        try:
            binding = self._candidate_binding_provider.current_binding()
        except Exception:
            return None
        return binding if isinstance(binding, JevCandidateBinding) else None


def _has_competing_material_alternatives(state: OrchestraJevAdjudicationState) -> bool:
    alternatives = state.to_payload()["mitigation_options"]
    distinct = {
        canonical_json_bytes({key: value for key, value in option.items() if key != "id"})
        for option in alternatives
    }
    return len(distinct) >= 2


__all__ = [
    "JevAdjudicationEligibilityError",
    "OrchestraJevAdjudicationUseCase",
]
