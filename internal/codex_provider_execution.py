from __future__ import annotations

from internal.codex_app_server_bridge import CodexAppServerExecutionEngine
from internal.codex_app_server_mutation_assessment import CodexAppServerMutationAssessmentEngine
from orchestra_runtime.provider_execution import (
    IProviderExecutionEngine,
    ProviderExecutionCapability,
    ProviderExecutionProfile,
)


CODEX_PROVIDER_ID = "openai-codex"
_CODEX_COMMON_CAPABILITIES = (
    ProviderExecutionCapability.APPROVAL_CONTROL,
    ProviderExecutionCapability.CANCELLATION,
    ProviderExecutionCapability.HOST_ACTIVITY_OBSERVATION,
    ProviderExecutionCapability.NETWORK_RESTRICTION,
    ProviderExecutionCapability.STRUCTURED_OUTPUT,
)


class CodexAppServerProviderExecutionEngine(
    CodexAppServerExecutionEngine,
    IProviderExecutionEngine,
):
    """Provider-aware wrapper over the existing bounded Codex read-only bridge."""

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        return ProviderExecutionProfile.create(
            provider_id=CODEX_PROVIDER_ID,
            model_id=self._config.model,
            capabilities=(
                *_CODEX_COMMON_CAPABILITIES,
                ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,
            ),
        )


class CodexAppServerProviderMutationAssessmentEngine(
    CodexAppServerMutationAssessmentEngine,
    IProviderExecutionEngine,
):
    """Provider-aware wrapper over the existing bounded Codex mutation assessment."""

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        return ProviderExecutionProfile.create(
            provider_id=CODEX_PROVIDER_ID,
            model_id=self._config.model,
            capabilities=_CODEX_COMMON_CAPABILITIES,
        )
