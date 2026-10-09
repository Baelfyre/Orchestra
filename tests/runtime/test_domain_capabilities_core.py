from __future__ import annotations

import ast
import inspect

import pytest

from orchestra_runtime.authority import AuthorityProvenance, Constraint, ProvenanceSource
from orchestra_runtime.capabilities import (
    CapabilityDecision as LegacyCapabilityDecision,
    CapabilityReasonCode as LegacyCapabilityReasonCode,
    RuntimeCapability as LegacyRuntimeCapability,
    RuntimeCapabilityGrant as LegacyRuntimeCapabilityGrant,
)
from orchestra_runtime.domain.capabilities import (
    CapabilityDecision,
    CapabilityReasonCode,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    evaluate_capability_grants,
    intersect_capability_grants,
)
from orchestra_runtime.domain.capabilities import core
from orchestra_runtime.errors import InvalidCapabilityConfigurationError


def _root_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.policy",
        "1",
        "conductor",
    )


def _delegated_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "runtime.delegation",
        "1",
        "conductor",
        parent_run_id="run-parent",
        parent_decision_id="decision-parent",
    )


def _capability() -> RuntimeCapability:
    return RuntimeCapability(
        "runtime.read",
        "conductor",
        ("read", "write"),
        "Read runtime state.",
    )


def test_legacy_capability_symbols_are_canonical_domain_symbols() -> None:
    assert LegacyRuntimeCapability is RuntimeCapability
    assert LegacyRuntimeCapabilityGrant is RuntimeCapabilityGrant
    assert LegacyCapabilityDecision is CapabilityDecision
    assert LegacyCapabilityReasonCode is CapabilityReasonCode


def test_domain_capability_evaluation_preserves_fail_closed_semantics() -> None:
    grant = RuntimeCapabilityGrant(
        _capability(),
        ("read",),
        _root_provenance(),
        (Constraint.allowed_set("region", ("ph", "us")),),
    )

    allowed = evaluate_capability_grants(
        (grant,),
        run_id="run-1",
        manifest_id="manifest-1",
        capability_id="RUNTIME.READ",
        operation="READ",
        constraints=(Constraint.exact("region", "ph"),),
        decision_id="decision-1",
    )
    assert allowed.allowed is True
    assert allowed.reason_code is CapabilityReasonCode.ALLOWED
    assert allowed.capability_id == "runtime.read"
    assert allowed.operation == "read"

    denied_operation = evaluate_capability_grants(
        (grant,),
        run_id="run-1",
        manifest_id="manifest-1",
        capability_id="runtime.read",
        operation="write",
        constraints=(Constraint.exact("region", "ph"),),
        decision_id="decision-2",
    )
    assert denied_operation.allowed is False
    assert denied_operation.reason_code is CapabilityReasonCode.OPERATION_NOT_ALLOWED

    denied_constraint = evaluate_capability_grants(
        (grant,),
        run_id="run-1",
        manifest_id="manifest-1",
        capability_id="runtime.read",
        operation="read",
        constraints=(Constraint.exact("region", "eu"),),
        decision_id="decision-3",
    )
    assert denied_constraint.allowed is False
    assert denied_constraint.reason_code is CapabilityReasonCode.CONSTRAINT_DENIED


def test_domain_capability_intersection_is_restrictive() -> None:
    parent = RuntimeCapabilityGrant(
        _capability(),
        ("read", "write"),
        _root_provenance(),
        (Constraint.allowed_set("region", ("ph", "us")),),
    )
    requested = RuntimeCapabilityGrant(
        _capability(),
        ("read",),
        _root_provenance(),
        (Constraint.exact("region", "ph"),),
    )

    effective = intersect_capability_grants((parent,), (requested,), _delegated_provenance())
    assert len(effective) == 1
    assert effective[0].allowed_operations == ("read",)
    assert effective[0].constraints == (Constraint.exact("region", "ph"),)
    assert effective[0].provenance.source_type is ProvenanceSource.ACCEPTED_DELEGATION

    with pytest.raises(InvalidCapabilityConfigurationError, match="accepted delegation provenance"):
        intersect_capability_grants((parent,), (requested,), _root_provenance())


def test_capability_domain_core_has_only_inward_runtime_dependencies() -> None:
    tree = ast.parse(inspect.getsource(core))
    forbidden_stdlib = {"os", "pathlib", "socket", "sqlite3", "subprocess"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".", 1)[0] not in forbidden_stdlib for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                assert node.module.split(".", 1)[0] not in forbidden_stdlib
            elif node.level:
                assert node.module is not None
                assert node.module.startswith(("governance.", "shared."))
