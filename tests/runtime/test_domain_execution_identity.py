from __future__ import annotations

import ast
from pathlib import Path

import pytest

import orchestra_runtime.models as legacy_models
from orchestra_runtime import RunIdentity as public_run_identity
from orchestra_runtime.correlation import generate_correlation_id
from orchestra_runtime.domain.execution import RunIdentity as domain_run_identity
from orchestra_runtime.domain.execution import identity as domain_identity


def test_domain_run_identity_exports_are_legacy_identity_compatible() -> None:
    assert legacy_models.RunIdentity is domain_run_identity
    assert public_run_identity is domain_run_identity


def test_domain_run_identity_preserves_normalization_and_serialization() -> None:
    cid = generate_correlation_id()
    run = domain_run_identity("  run-1  ", "  parent-1  ", correlation_id=cid.upper())

    assert run.run_id == "run-1"
    assert run.parent_run_id == "parent-1"
    assert run.correlation_id == cid
    assert run.to_dict() == {
        "run_id": "run-1",
        "parent_run_id": "parent-1",
        "correlation_id": cid,
    }

    root = domain_run_identity(" root ")
    assert root.to_dict() == {"run_id": "root", "parent_run_id": None}


def test_domain_run_identity_preserves_fail_closed_invariants() -> None:
    with pytest.raises(ValueError, match="run_id must be non-empty"):
        domain_run_identity("   ")

    with pytest.raises(ValueError, match="parent_run_id must differ from run_id"):
        domain_run_identity(" run-1 ", "run-1")

    with pytest.raises(ValueError, match="malformed correlation_id"):
        domain_run_identity("run-1", correlation_id="not-a-uuid")


def test_domain_run_identity_is_pure_and_legacy_free() -> None:
    source_path = Path(domain_identity.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    forbidden = {
        "secrets",
        "time",
        "pathlib",
        "os",
        "subprocess",
        "socket",
        "orchestra_runtime.correlation",
        "orchestra_runtime.models",
        "orchestra_runtime.interfaces",
    }
    assert not imports.intersection(forbidden)
    assert not any(isinstance(node, ast.Name) and node.id == "open" for node in ast.walk(tree))
