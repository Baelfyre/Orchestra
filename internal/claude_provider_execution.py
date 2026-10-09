from __future__ import annotations

from internal.claude_code_bridge import ClaudeCodeExecutionEngine
from orchestra_runtime.provider_execution import (
    IProviderExecutionEngine,
    ProviderExecutionCapability,
    ProviderExecutionProfile,
)


CLAUDE_CODE_PROVIDER_ID = "anthropic-claude-code"
_CLAUDE_CODE_CAPABILITIES = (
    ProviderExecutionCapability.APPROVAL_CONTROL,
    ProviderExecutionCapability.CANCELLATION,
    ProviderExecutionCapability.NETWORK_RESTRICTION,
    ProviderExecutionCapability.STRUCTURED_OUTPUT,
)


class ClaudeCodeProviderExecutionEngine(
    ClaudeCodeExecutionEngine,
    IProviderExecutionEngine,
):
    """Provider-aware wrapper over the bounded read-only Claude Code bridge."""

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        return ProviderExecutionProfile.create(
            provider_id=CLAUDE_CODE_PROVIDER_ID,
            model_id=self._config.model,
            capabilities=_CLAUDE_CODE_CAPABILITIES,
        )
