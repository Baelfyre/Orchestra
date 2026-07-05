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
    return RuntimeExecutor(
        skill_registry,
        RouterService(skill_registry),
        GovernanceValidator(),
        ContextAssembler(manifest_repository),
        AuditLogger(InMemoryAuditSink()),
    )


def test_destructive_skill_blocked_without_validation():
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create("antigravity", repo_root)

    result = executor.execute(adapter, "/resilience-check run now")

    assert result.success is False
    assert result.route.skill_slug == "dagger"
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"


def test_destructive_skill_allowed_with_validation():
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create("antigravity", repo_root)

    result = executor.execute(
        adapter,
        "/resilience-check dry run",
        metadata={"destructive_validated": True, "dry_run": True},
    )

    assert result.success is True
    assert result.validation.status == "APPROVED"


def test_high_risk_skill_blocked_without_validation():
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create("codex", repo_root)

    result = executor.execute(adapter, "security-check auth boundaries")

    assert result.success is False
    assert result.route.skill_slug == "cipher"
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
