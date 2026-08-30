from __future__ import annotations

from pathlib import Path

from internal.claude_code_bridge import ClaudeCodeConfig
from internal.claude_provider_execution import (
    CLAUDE_CODE_PROVIDER_ID,
    ClaudeCodeProviderExecutionEngine,
)
from orchestra_runtime.provider_execution import ProviderExecutionCapability


ROOT = Path(__file__).resolve().parents[2]


def test_claude_wrapper_maps_explicit_model_to_provider_profile() -> None:
    engine = ClaudeCodeProviderExecutionEngine(
        ROOT,
        config=ClaudeCodeConfig(model="claude-user-choice"),
    )

    profile = engine.provider_execution_profile

    assert profile.provider_id == CLAUDE_CODE_PROVIDER_ID == "anthropic-claude-code"
    assert profile.model_id == "claude-user-choice"
    assert ProviderExecutionCapability.STRUCTURED_OUTPUT in profile.capabilities
    assert ProviderExecutionCapability.CANCELLATION in profile.capabilities
    assert ProviderExecutionCapability.NETWORK_RESTRICTION in profile.capabilities
    assert ProviderExecutionCapability.APPROVAL_CONTROL in profile.capabilities
    assert ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL not in profile.capabilities
    assert ProviderExecutionCapability.HOST_ACTIVITY_OBSERVATION not in profile.capabilities


def test_claude_provider_profile_does_not_overclaim_host_observation_or_os_sandbox() -> None:
    profile = ClaudeCodeProviderExecutionEngine(
        ROOT,
        config=ClaudeCodeConfig(model="claude-user-choice"),
    ).provider_execution_profile

    assert set(profile.capabilities) == {
        ProviderExecutionCapability.APPROVAL_CONTROL,
        ProviderExecutionCapability.CANCELLATION,
        ProviderExecutionCapability.NETWORK_RESTRICTION,
        ProviderExecutionCapability.STRUCTURED_OUTPUT,
    }


def test_claude_provider_profile_identity_changes_with_explicit_model_selection() -> None:
    first = ClaudeCodeProviderExecutionEngine(
        ROOT,
        config=ClaudeCodeConfig(model="model-a"),
    ).provider_execution_profile
    second = ClaudeCodeProviderExecutionEngine(
        ROOT,
        config=ClaudeCodeConfig(model="model-b"),
    ).provider_execution_profile

    assert first.provider_id == second.provider_id
    assert first.model_id != second.model_id
    assert first.profile_id != second.profile_id
    assert first.profile_digest != second.profile_digest
