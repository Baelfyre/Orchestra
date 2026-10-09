import json
from pathlib import Path

import pytest

from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeExecutor,
    SkillRegistry,
    build_compatibility_composition,
)


def build_executor(repo_root: Path) -> RuntimeExecutor:
    manifest_repository = ManifestRepository(repo_root)
    skill_repository = SkillSourceRepository(repo_root)
    skill_registry = SkillRegistry(manifest_repository, skill_repository)
    router = RouterService(skill_registry)
    governance = GovernanceValidator()
    context_assembler = ContextAssembler(manifest_repository)
    composition = build_compatibility_composition(
        skill_registry,
        InMemoryAuditSink(),
        run_id="runtime-core-compatibility",
    )
    return RuntimeExecutor(skill_registry, router, governance, context_assembler, composition)


class EmptySkillRegistry:
    def load_skills(self) -> tuple:
        return ()

    def get_skill(self, slug: str):
        return None


def test_skill_registry_loads_manifest_skills():
    repo_root = Path(__file__).resolve().parents[2]
    registry = SkillRegistry(ManifestRepository(repo_root), SkillSourceRepository(repo_root))

    skills = registry.load_skills()
    skill_slugs = {skill.slug for skill in skills}

    assert "conductor" in skill_slugs
    assert "clockwork" in skill_slugs
    assert registry.get_skill("scribe").commands == ("scribe", "review-docs")


def test_runtime_executor_routes_codex_entrypoint_to_conductor():
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create("codex", repo_root)

    result = executor.execute(adapter, "@Orchestra rerun the prompt")

    assert result.success is True
    assert result.command_name == "conductor"
    assert result.route.skill_slug == "conductor"
    assert result.validation.status == "NOT_REQUIRED"
    assert result.audit_entry_id
    assert result.authority_mode == "COMPATIBILITY"
    assert result.lifecycle_state == "COMPLETED"
    assert result.authority_decision_id
    assert result.capability_decision_id


def test_manifest_repository_load_aliases_returns_empty_dict_when_missing(tmp_path: Path):
    repository = ManifestRepository(tmp_path)

    assert repository.load_aliases() == {}


def test_manifest_repository_load_aliases_parses_aliases_json(tmp_path: Path):
    aliases = {"legacy": "conductor", "docs": "review-docs"}
    (tmp_path / "aliases.json").write_text(json.dumps(aliases), encoding="utf-8")
    repository = ManifestRepository(tmp_path)

    assert repository.load_aliases() == aliases


def test_router_service_raises_when_command_route_and_conductor_are_unresolved():
    router = RouterService(EmptySkillRegistry(), command_routes={"mystery-command": "missing-skill"})
    command = Command(name="mystery-command", raw_input="mystery-command", adapter_name="codex")
    context = ContextPackage(
        adapter_name="codex",
        prompt="mystery-command",
        project_root=Path(__file__).resolve().parents[2],
        available_commands=("mystery-command",),
        manifest_version="1.0.0",
    )

    with pytest.raises(ValueError, match="Unable to resolve skill for command 'mystery-command'"):
        router.route(command, context)
