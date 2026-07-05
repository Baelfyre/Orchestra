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
