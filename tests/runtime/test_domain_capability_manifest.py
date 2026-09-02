from __future__ import annotations

import ast
import inspect

import pytest

import orchestra_runtime
from orchestra_runtime.authority import AuthorityProvenance, ProvenanceSource
from orchestra_runtime.capabilities import RuntimeCapabilityManifest as LegacyRuntimeCapabilityManifest
from orchestra_runtime.domain.capabilities import (
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
)
from orchestra_runtime.domain.capabilities import manifest
from orchestra_runtime.domain.execution import RunIdentity
from orchestra_runtime.errors import CapabilityCollisionError, InvalidCapabilityConfigurationError


def _provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.policy",
        "1",
        "conductor",
    )


def _grant(capability_id: str = "runtime.read") -> RuntimeCapabilityGrant:
    capability = RuntimeCapability(capability_id, "conductor", ("read",), "Read runtime state.")
    return RuntimeCapabilityGrant(capability, ("read",), _provenance())


def test_domain_manifest_exports_are_legacy_and_public_identity_compatible() -> None:
    assert LegacyRuntimeCapabilityManifest is RuntimeCapabilityManifest
    assert orchestra_runtime.RuntimeCapabilityManifest is RuntimeCapabilityManifest


def test_domain_manifest_preserves_normalization_order_and_serialization() -> None:
    manifest_value = RuntimeCapabilityManifest(
        " MANIFEST.RUNTIME ",
        RunIdentity(" run-1 "),
        " 1 ",
        (_grant("runtime.write"), _grant("runtime.read")),
        _provenance(),
    )

    assert manifest_value.manifest_id == "manifest.runtime"
    assert manifest_value.run_identity.run_id == "run-1"
    assert manifest_value.policy_version == "1"
    assert tuple(item.capability.capability_id for item in manifest_value.grants) == (
        "runtime.read",
        "runtime.write",
    )
    assert manifest_value.to_dict()["run_identity"] == {
        "run_id": "run-1",
        "parent_run_id": None,
    }


def test_domain_manifest_preserves_fail_closed_invariants() -> None:
    with pytest.raises(InvalidCapabilityConfigurationError, match="at least one grant"):
        RuntimeCapabilityManifest("manifest.empty", RunIdentity("run-1"), "1", (), _provenance())

    duplicate = _grant("runtime.read")
    with pytest.raises(CapabilityCollisionError, match="collide"):
        RuntimeCapabilityManifest(
            "manifest.duplicate",
            RunIdentity("run-1"),
            "1",
            (duplicate, duplicate),
            _provenance(),
        )


def test_domain_manifest_has_only_inward_runtime_dependencies() -> None:
    tree = ast.parse(inspect.getsource(manifest))
    forbidden = {
        "os",
        "pathlib",
        "socket",
        "sqlite3",
        "subprocess",
        "orchestra_runtime.capabilities",
        "orchestra_runtime.interfaces",
        "orchestra_runtime.models",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert not imports.intersection(forbidden)
    assert not any(isinstance(node, ast.Name) and node.id == "open" for node in ast.walk(tree))
