from __future__ import annotations

import pytest

from internal.codex_user_model_selection import (
    MODEL_SELECTION_SOURCE,
    CodexUserModelSelection,
    build_mutation_assessment_config,
    build_read_only_config,
)


def test_model_selection_is_explicit_user_configuration():
    selection = CodexUserModelSelection(model="  gpt-user-choice  ", reasoning_effort=" high ")

    assert MODEL_SELECTION_SOURCE == "USER_CONFIG"
    assert selection.model == "gpt-user-choice"
    assert selection.reasoning_effort == "high"
    assert selection.evidence_identity == "codex-model:gpt-user-choice"


def test_model_selection_rejects_blank_or_control_characters():
    with pytest.raises(ValueError):
        CodexUserModelSelection(model="   ")
    with pytest.raises(ValueError):
        CodexUserModelSelection(model="model\nother")
    with pytest.raises(ValueError):
        CodexUserModelSelection(model="model", reasoning_effort="   ")


def test_read_only_config_uses_selected_model_without_widening_policy():
    config = build_read_only_config(
        CodexUserModelSelection(model="gpt-selected", reasoning_effort="medium")
    )

    assert config.model == "gpt-selected"
    assert config.reasoning_effort == "medium"
    assert config.approval_policy == "never"
    assert config.sandbox_mode == "read-only"
    assert config.network_access is False


def test_mutation_assessment_config_uses_selected_model_without_widening_policy():
    config = build_mutation_assessment_config(
        CodexUserModelSelection(model="gpt-selected", reasoning_effort="low")
    )

    assert config.model == "gpt-selected"
    assert config.reasoning_effort == "low"
    assert config.approval_policy == "never"
    assert config.sandbox_mode == "workspace-write"
    assert config.network_access is False
    assert config.writable_root == "mutation"
    assert config.allowed_relative_paths == ("mutation/target.md",)


def test_selection_cannot_widen_fixed_security_controls():
    selection = CodexUserModelSelection(model="another-model")
    read_only = build_read_only_config(selection)
    mutation = build_mutation_assessment_config(selection)

    assert read_only.approval_policy == mutation.approval_policy == "never"
    assert read_only.network_access is False
    assert mutation.network_access is False
