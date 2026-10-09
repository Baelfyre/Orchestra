from __future__ import annotations

import ast
from pathlib import Path

import pytest

from orchestra_runtime import authority as legacy_authority
from orchestra_runtime.domain.governance import authority as domain_authority
from orchestra_runtime.errors import InvalidAuthorityConfigurationError


def _provenance() -> domain_authority.AuthorityProvenance:
    return domain_authority.AuthorityProvenance(
        domain_authority.ProvenanceSource.TRUSTED_REPOSITORY_POLICY,
        "policy.root",
        "1.0",
        "runtime.composition",
    )


def _scope() -> domain_authority.AuthorityScope:
    return domain_authority.AuthorityScope(
        "scope.root",
        (domain_authority.TargetSelector("repository:orchestra"),),
        ("read", "write"),
        (domain_authority.Constraint.allowed_set("environment", ["dev", "test"]),),
        _provenance(),
    )


def test_legacy_authority_exports_are_canonical_domain_symbols():
    assert legacy_authority.AuthorityProvenance is domain_authority.AuthorityProvenance
    assert legacy_authority.TargetSelector is domain_authority.TargetSelector
    assert legacy_authority.Constraint is domain_authority.Constraint
    assert legacy_authority.AuthorityScope is domain_authority.AuthorityScope
    assert legacy_authority.AuthorityDecision is domain_authority.AuthorityDecision
    assert legacy_authority.AuthorityReasonCode is domain_authority.AuthorityReasonCode
    assert legacy_authority.ProvenanceSource is domain_authority.ProvenanceSource


def test_domain_authority_preserves_normalization_and_intersection_semantics():
    scope = _scope()
    assert scope.scope_id == "scope.root"
    assert scope.operations == ("read", "write")
    assert scope.constraints == (
        domain_authority.Constraint.allowed_set("environment", ["dev", "test"]),
    )
    assert domain_authority._constraints_permit(
        scope.constraints,
        (domain_authority.Constraint.exact("environment", "dev"),),
    )
    assert domain_authority._intersect_constraints(
        scope.constraints,
        (domain_authority.Constraint.allowed_set("environment", ["test", "prod"]),),
    ) == (domain_authority.Constraint.exact("environment", "test"),)


def test_domain_authority_fails_closed_on_untrusted_or_wildcard_scope():
    with pytest.raises(InvalidAuthorityConfigurationError):
        domain_authority.AuthorityProvenance(
            domain_authority.ProvenanceSource.ACCEPTED_DELEGATION,
            "delegation",
            "1",
            "runtime",
        )
    with pytest.raises(InvalidAuthorityConfigurationError, match="exact"):
        domain_authority.TargetSelector("repository:*")


def test_domain_authority_has_no_io_or_legacy_runtime_imports():
    source_path = Path(domain_authority.__file__)
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
        "orchestra_runtime.authority",
        "orchestra_runtime.interfaces",
        "orchestra_runtime.models",
    }
    assert not imports.intersection(forbidden)
