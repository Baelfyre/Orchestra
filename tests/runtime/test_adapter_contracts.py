from pathlib import Path

import pytest

from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    AuditLogger,
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeExecutor,
    SkillRegistry,
)


def build_executor(repo_root: Path) -> RuntimeExecutor:
    manifest_repository = ManifestRepository(repo_root)
    skill_repository = SkillSourceRepository(repo_root)
    skill_registry = SkillRegistry(manifest_repository, skill_repository)
    return RuntimeExecutor(
        skill_registry,
        RouterService(skill_registry),
        GovernanceValidator(),
        ContextAssembler(manifest_repository),
        AuditLogger(InMemoryAuditSink()),
    )


@pytest.mark.parametrize(
    ("adapter_name", "prompt"),
    (
        ("codex", "@Orchestra review-docs"),
        ("antigravity", "/ponytail /conductor review docs"),
        ("claude-code", "Use Conductor for this task"),
        ("cursor", "@Orchestra review docs"),
        ("windsurf", "/conductor review docs"),
        ("vscode", "orchestra: review docs"),
        ("jetbrains", "Use Conductor to review docs"),
        ("zed", "@Orchestra review docs"),
        ("neovim", ":Orchestra review docs"),
    ),
)
def test_adapter_contracts(adapter_name: str, prompt: str):
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create(adapter_name, repo_root)

    context = adapter.provide_context(prompt)
    result = executor.execute(adapter, prompt)

    assert context.adapter_name == adapter_name
    assert context.available_commands
    assert "conductor" in context.available_commands
    assert result.adapter_name == adapter_name
    assert result.audit_entry_id
    assert result.output


@pytest.mark.parametrize(
    ("adapter_name", "prompt", "expected_command", "expected_adapter_name"),
    (
        ("cursor", "@Orchestra review docs", "conductor", "cursor"),
        ("windsurf", "/conductor review docs", "conductor", "windsurf"),
        ("vscode", "orchestra: review docs", "conductor", "vscode"),
        ("vscodium", "orchestra: review docs", "conductor", "vscode"),
        ("jetbrains", "Use Conductor to review docs", "conductor", "jetbrains"),
        ("zed", "@Orchestra review docs", "conductor", "zed"),
        ("neovim", ":Orchestra review docs", "conductor", "neovim"),
    ),
)
def test_new_adapter_command_translation(
    adapter_name: str,
    prompt: str,
    expected_command: str,
    expected_adapter_name: str,
):
    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create(adapter_name, repo_root)

    command = adapter.parse_command(prompt)

    assert command.adapter_name == expected_adapter_name
    assert command.name == expected_command


def test_parse_command_falls_back_to_default_command_for_unmatched_prompt():
    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create("codex", repo_root)

    command = adapter.parse_command("plain freeform request", metadata={"source": "test"})

    assert command.adapter_name == "codex"
    assert command.name == adapter.default_command
    assert command.metadata == {"source": "test"}
