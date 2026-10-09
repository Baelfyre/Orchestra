from __future__ import annotations

from pathlib import Path

import pytest

from orchestra_runtime.mcp_specialist_execution import (
    build_mcp_specialist_runtime_factory,
    build_mcp_stdio_transport_with_specialist_execution,
)
from orchestra_runtime.specialist_execution import SpecialistExecutionMode


ROOT = Path(__file__).resolve().parents[2]


def test_specialist_runtime_factory_rejects_empty_adapter() -> None:
    with pytest.raises(ValueError, match="backing_adapter"):
        build_mcp_specialist_runtime_factory(
            ROOT,
            execution_engine_factory=lambda: object(),  # type: ignore[return-value]
            backing_adapter=" ",
        )


def test_specialist_runtime_factory_rejects_non_callable_factory() -> None:
    with pytest.raises(TypeError, match="execution_engine_factory"):
        build_mcp_specialist_runtime_factory(
            ROOT,
            execution_engine_factory=None,  # type: ignore[arg-type]
        )


def test_specialist_runtime_factory_rejects_factory_returning_non_engine() -> None:
    factory = build_mcp_specialist_runtime_factory(
        ROOT,
        execution_engine_factory=lambda: object(),  # type: ignore[return-value]
    )
    with pytest.raises(TypeError, match="ISpecialistExecutionEngine"):
        factory()


def test_stdio_specialist_builder_requires_non_empty_plugin_version(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "plugin.json").write_text('{"version": ""}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty version"):
        build_mcp_stdio_transport_with_specialist_execution(
            root,
            execution_engine_factory=lambda: object(),  # type: ignore[return-value]
        )


def test_execution_mode_is_validated_at_factory_construction() -> None:
    with pytest.raises(ValueError):
        build_mcp_specialist_runtime_factory(
            ROOT,
            execution_engine_factory=lambda: object(),  # type: ignore[return-value]
            execution_mode="NOT_A_MODE",  # type: ignore[arg-type]
        )

    factory = build_mcp_specialist_runtime_factory(
        ROOT,
        execution_engine_factory=lambda: object(),  # type: ignore[return-value]
        execution_mode=SpecialistExecutionMode.HOST_NATIVE,
    )
    with pytest.raises(TypeError):
        factory()
