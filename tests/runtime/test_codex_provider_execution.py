from __future__ import annotations

from pathlib import Path

from internal.codex_provider_execution import (
    CODEX_PROVIDER_ID,
    CodexAppServerProviderExecutionEngine,
    CodexAppServerProviderMutationAssessmentEngine,
)
from internal.codex_user_model_selection import (
    CodexUserModelSelection,
    build_mutation_assessment_config,
    build_read_only_config,
)
from orchestra_runtime.provider_execution import ProviderExecutionCapability


ROOT = Path(__file__).resolve().parents[2]


def test_codex_read_only_wrapper_maps_explicit_user_model_to_provider_profile() -> None:
    config = build_read_only_config(
        CodexUserModelSelection(model="gpt-user-choice", reasoning_effort="high")
    )
    engine = CodexAppServerProviderExecutionEngine(ROOT, config=config)

    profile = engine.provider_execution_profile

    assert profile.provider_id == CODEX_PROVIDER_ID == "openai-codex"
    assert profile.model_id == "gpt-user-choice"
    assert ProviderExecutionCapability.STRUCTURED_OUTPUT in profile.capabilities
    assert ProviderExecutionCapability.CANCELLATION in profile.capabilities
    assert ProviderExecutionCapability.NETWORK_RESTRICTION in profile.capabilities
    assert ProviderExecutionCapability.APPROVAL_CONTROL in profile.capabilities
    assert ProviderExecutionCapability.HOST_ACTIVITY_OBSERVATION in profile.capabilities
    assert ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL in profile.capabilities
    assert config.reasoning_effort == "high"
    assert config.approval_policy == "never"
    assert config.sandbox_mode == "read-only"
    assert config.network_access is False


def test_codex_mutation_wrapper_preserves_bounded_controls_without_claiming_read_only() -> None:
    config = build_mutation_assessment_config(
        CodexUserModelSelection(model="gpt-user-choice", reasoning_effort="low")
    )
    engine = CodexAppServerProviderMutationAssessmentEngine(ROOT, config=config)

    profile = engine.provider_execution_profile

    assert profile.provider_id == CODEX_PROVIDER_ID
    assert profile.model_id == "gpt-user-choice"
    assert ProviderExecutionCapability.STRUCTURED_OUTPUT in profile.capabilities
    assert ProviderExecutionCapability.CANCELLATION in profile.capabilities
    assert ProviderExecutionCapability.NETWORK_RESTRICTION in profile.capabilities
    assert ProviderExecutionCapability.APPROVAL_CONTROL in profile.capabilities
    assert ProviderExecutionCapability.HOST_ACTIVITY_OBSERVATION in profile.capabilities
    assert ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL not in profile.capabilities
    assert config.reasoning_effort == "low"
    assert config.approval_policy == "never"
    assert config.sandbox_mode == "workspace-write"
    assert config.network_access is False
    assert config.allowed_relative_paths == ("mutation/target.md",)


def test_codex_provider_profile_identity_changes_with_explicit_model_selection() -> None:
    first = CodexAppServerProviderExecutionEngine(
        ROOT,
        config=build_read_only_config(CodexUserModelSelection(model="model-a")),
    ).provider_execution_profile
    second = CodexAppServerProviderExecutionEngine(
        ROOT,
        config=build_read_only_config(CodexUserModelSelection(model="model-b")),
    ).provider_execution_profile

    assert first.provider_id == second.provider_id
    assert first.model_id != second.model_id
    assert first.profile_id != second.profile_id
    assert first.profile_digest != second.profile_digest
