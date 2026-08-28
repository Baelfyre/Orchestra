from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TextIO
from uuid import uuid4

from .factories import AdapterFactory
from .interfaces import IIDEAdapter, ISpecialistExecutionEngine
from .mcp_transport import McpToolTransport, RuntimeFactory
from .repositories import ManifestRepository, SkillSourceRepository
from .services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    SkillRegistry,
    build_compatibility_composition,
)
from .specialist_execution import SpecialistExecutionMode, SpecialistRuntimeExecutor


SpecialistExecutionEngineFactory = Callable[[], ISpecialistExecutionEngine]


def build_mcp_specialist_runtime_factory(
    repo_root: Path | str,
    *,
    execution_engine_factory: SpecialistExecutionEngineFactory,
    execution_mode: SpecialistExecutionMode = SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    backing_adapter: str = "codex",
) -> RuntimeFactory:
    """Build an MCP runtime that explicitly opts into a specialist execution engine.

    The existing build_mcp_runtime_factory remains route-only. Engine selection is
    constructor-owned and cannot be supplied through MCP client metadata or tool input.
    """

    root = Path(repo_root).resolve()
    adapter_name = str(backing_adapter).strip().casefold()
    if not adapter_name:
        raise ValueError("backing_adapter must be non-empty")
    if not callable(execution_engine_factory):
        raise TypeError("execution_engine_factory must be callable")
    mode = SpecialistExecutionMode(execution_mode)

    def factory() -> tuple[SpecialistRuntimeExecutor, IIDEAdapter]:
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
        if not isinstance(engine, ISpecialistExecutionEngine):
            raise TypeError("execution_engine_factory must return ISpecialistExecutionEngine")
        executor = SpecialistRuntimeExecutor(
            skill_registry,
            RouterService(skill_registry),
            GovernanceValidator(),
            ContextAssembler(manifest_repository),
            composition,
            execution_engine=engine,
            execution_mode=mode,
        )
        adapter = AdapterFactory.create(adapter_name, root)
        return executor, adapter

    return factory


def build_mcp_stdio_transport_with_specialist_execution(
    repo_root: Path | str,
    *,
    execution_engine_factory: SpecialistExecutionEngineFactory,
    execution_mode: SpecialistExecutionMode = SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    backing_adapter: str = "codex",
    error_stream: TextIO | None = None,
) -> McpToolTransport:
    """Explicit opt-in MCP transport builder for typed specialist execution."""

    root = Path(repo_root).resolve()
    manifest = ManifestRepository(root).load_manifest()
    server_version = str(manifest.get("version", "")).strip()
    if not server_version:
        raise ValueError("plugin.json must declare a non-empty version")
    return McpToolTransport(
        build_mcp_specialist_runtime_factory(
            root,
            execution_engine_factory=execution_engine_factory,
            execution_mode=execution_mode,
            backing_adapter=backing_adapter,
        ),
        server_name="orchestra",
        server_version=server_version,
        error_stream=error_stream,
    )
