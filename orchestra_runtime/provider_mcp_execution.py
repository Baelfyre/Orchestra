from __future__ import annotations

# @codebase_provenance_JEO
# @codebase_rights_JEO

from collections.abc import Callable
from pathlib import Path
from typing import TextIO
from uuid import uuid4

from .application.ports.specialist_execution import ReadOnlyWorkspaceProvider
from .factories import AdapterFactory
from .interfaces import IIDEAdapter
from .mcp_transport import McpToolTransport, RuntimeFactory
from .provider_execution import (
    IProviderExecutionEngine,
    ProviderExecutionRequirement,
    ProviderSpecialistRuntimeExecutor,
)
from .repositories import ManifestRepository, SkillSourceRepository
from .services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    SkillRegistry,
    build_compatibility_composition,
)


ProviderExecutionEngineFactory = Callable[[], IProviderExecutionEngine]


def build_mcp_provider_runtime_factory(
    repo_root: Path | str,
    *,
    execution_engine_factory: ProviderExecutionEngineFactory,
    provider_requirement: ProviderExecutionRequirement | None = None,
    backing_adapter: str = "codex",
    read_only_workspace_provider: ReadOnlyWorkspaceProvider | None = None,
) -> RuntimeFactory:
    """Build an explicit provider-aware MCP specialist runtime.

    Provider/engine selection remains constructor-owned trusted configuration. MCP
    client metadata, prompt content, and tool arguments cannot select a provider,
    model, capability profile, or fallback route.
    """

    root = Path(repo_root).resolve()
    adapter_name = str(backing_adapter).strip().casefold()
    if not adapter_name:
        raise ValueError("backing_adapter must be non-empty")
    if not callable(execution_engine_factory):
        raise TypeError("execution_engine_factory must be callable")
    if provider_requirement is not None and not isinstance(
        provider_requirement, ProviderExecutionRequirement
    ):
        raise TypeError("provider_requirement must be ProviderExecutionRequirement")

    def factory() -> tuple[ProviderSpecialistRuntimeExecutor, IIDEAdapter]:
        manifest_repository = ManifestRepository(root)
        skill_repository = SkillSourceRepository(root)
        skill_registry = SkillRegistry(manifest_repository, skill_repository)
        audit_sink = InMemoryAuditSink()
        composition = build_compatibility_composition(
            skill_registry,
            audit_sink,
            run_id=f"mcp-{uuid4().hex}",
        )
        engine = execution_engine_factory()
        if not isinstance(engine, IProviderExecutionEngine):
            raise TypeError("execution_engine_factory must return IProviderExecutionEngine")
        executor = ProviderSpecialistRuntimeExecutor(
            skill_registry,
            RouterService(skill_registry),
            GovernanceValidator(),
            ContextAssembler(manifest_repository),
            composition,
            execution_engine=engine,
            provider_requirement=provider_requirement,
            read_only_workspace_provider=read_only_workspace_provider,
        )
        adapter = AdapterFactory.create(adapter_name, root)
        return executor, adapter

    return factory


def build_mcp_stdio_transport_with_provider_execution(
    repo_root: Path | str,
    *,
    execution_engine_factory: ProviderExecutionEngineFactory,
    provider_requirement: ProviderExecutionRequirement | None = None,
    backing_adapter: str = "codex",
    read_only_workspace_provider: ReadOnlyWorkspaceProvider | None = None,
    error_stream: TextIO | None = None,
) -> McpToolTransport:
    """Explicit opt-in MCP transport for provider-aware host execution."""

    root = Path(repo_root).resolve()
    manifest = ManifestRepository(root).load_manifest()
    server_version = str(manifest.get("version", "")).strip()
    if not server_version:
        raise ValueError("plugin.json must declare a non-empty version")
    return McpToolTransport(
        build_mcp_provider_runtime_factory(
            root,
            execution_engine_factory=execution_engine_factory,
            provider_requirement=provider_requirement,
            read_only_workspace_provider=read_only_workspace_provider,
            backing_adapter=backing_adapter,
        ),
        server_name="orchestra",
        server_version=server_version,
        error_stream=error_stream,
    )
