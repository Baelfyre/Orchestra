from pathlib import Path

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
    router = RouterService(skill_registry)
    governance = GovernanceValidator()
    context_assembler = ContextAssembler(manifest_repository)
    audit_logger = AuditLogger(InMemoryAuditSink())
    return RuntimeExecutor(skill_registry, router, governance, context_assembler, audit_logger)


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
