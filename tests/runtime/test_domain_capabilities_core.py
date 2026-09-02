from __future__ import annotations

import ast
from pathlib import Path

from orchestra_runtime import capabilities as legacy_capabilities
from orchestra_runtime.domain.capabilities import core as domain_capabilities
from orchestra_runtime.domain.governance import authority as domain_authority


def _provenance() -> domain_authority.AuthorityProvenance:
    return domain_authority.AuthorityProvenance(
        domain_authority.ProvenanceSource.TRUSTED_REPOSITORY_POLICY,
        "policy.root",
        "1.0",
        "runtime.composition",
    )


def test_legacy_capability_exports_are_canonical_domain_symbols():
    assert legacy_capabilities.CapabilityReasonCode is domain_capabilities.CapabilityReasonCode
    assert legacy_capabilities.RuntimeCapability is domain_capabilities.RuntimeCapability
    assert legacy_capabilities.RuntimeCapabilityGrant is domain_capabilities.RuntimeCapabilityGrant
    assert legacy_capabilities.CapabilityDecision is domain_capabilities.CapabilityDecision


def test_domain_capability_value_objects_preserve_normalization_semantics():
    capability = domain_capabilities.RuntimeCapability(
        "Capability.Read",
        "Runtime.Owner",
        ("WRITE", "read"),
        "  Read and write runtime state  ",
    )
    assert capability.capability_id == "capability.read"
    assert capability.owner == "runtime.owner"
    assert capability.operations == ("read", "write")
    assert capability.description == "Read and write runtime state"

    grant = domain_capabilities.RuntimeCapabilityGrant(
        capability,
        ("WRITE",),
        _provenance(),
        (domain_authority.Constraint.exact("environment", "test"),),
    )
    assert grant.allowed_operations == ("write",)
    assert grant.constraints == (domain_authority.Constraint.exact("environment", "test"),)

    decision = domain_capabilities.CapabilityDecision(
        " decision.1 ",
        " run.1 ",
        "Manifest.Root",
        "Capability.Read",
        "WRITE",
        grant.constraints,
        True,
        domain_capabilities.CapabilityReasonCode.ALLOWED,
        " capability.read ",
        ("environment", "environment"),
    )
    assert decision.decision_id == "decision.1"
    assert decision.run_id == "run.1"
    assert decision.manifest_id == "manifest.root"
    assert decision.capability_id == "capability.read"
    assert decision.operation == "write"
    assert decision.evaluated_grant_id == "capability.read"
    assert decision.evaluated_constraints == ("environment",)


def test_domain_capability_core_has_no_io_or_legacy_runtime_imports():
    source_path = Path(domain_capabilities.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    forbidden = {
        "pathlib",
        "os",
        "subprocess",
        "socket",
        "authority",
        "capabilities",
        "interfaces",
        "models",
        "orchestra_runtime.authority",
        "orchestra_runtime.capabilities",
        "orchestra_runtime.interfaces",
        "orchestra_runtime.models",
    }
    assert not imports.intersection(forbidden)
    assert not any(isinstance(node, ast.Name) and node.id == "open" for node in ast.walk(tree))
