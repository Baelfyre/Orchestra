from dataclasses import FrozenInstanceError

import pytest

from orchestra_runtime.authority import AuthorityProvenance, AuthorityScope, ProvenanceSource, TargetSelector
from orchestra_runtime.capabilities import RuntimeCapability, RuntimeCapabilityGrant
from orchestra_runtime.delegation import (
    DelegationDecision,
    DelegationReasonCode,
    DelegationRequest,
    DelegationTask,
)
from orchestra_runtime.errors import DelegationDepthViolationError, DelegationRejectedError
from orchestra_runtime.models import RunIdentity


def root_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_REPOSITORY_POLICY, "policy.root", "1", "runtime")


def delegated_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation.accepted",
        "1",
        "runtime",
        "parent-run",
        "parent-decision",
    )


def scope() -> AuthorityScope:
    return AuthorityScope(
        "scope.child",
        (TargetSelector("repository:orchestra"),),
        ("read",),
        (),
        delegated_provenance(),
        "scope.parent",
    )


def capability_grant() -> RuntimeCapabilityGrant:
    capability = RuntimeCapability("filesystem.read", "clockwork", ("read",), "Read files")
    return RuntimeCapabilityGrant(capability, ("read",), delegated_provenance())


def request(**changes) -> DelegationRequest:
    data = {
        "request_id": "request-1",
        "parent_run": RunIdentity("parent-run"),
        "child_run": RunIdentity("child-run", "parent-run"),
        "specialist_slug": "clockwork",
        "task": DelegationTask("Inspect authority", ("Report findings",)),
        "requested_scope": scope(),
        "requested_capabilities": (capability_grant(),),
        "context_allowlist": ("project_root",),
        "sensitive_context_exclusions": ("secrets",),
        "depth": 1,
        "provenance": delegated_provenance(),
    }
    data.update(changes)
    return DelegationRequest(**data)


def test_delegation_request_is_model_only_immutable_and_serializable():
    context = ["project_root"]
    value = request(context_allowlist=context)
    context.append("secrets")

    assert value.context_allowlist == ("project_root",)
    assert value.to_dict()["specialist_slug"] == "clockwork"
    with pytest.raises(FrozenInstanceError):
        value.depth = 2  # type: ignore[misc]


def test_delegation_request_rejects_invalid_parent_depth_and_sensitive_context():
    with pytest.raises(DelegationRejectedError, match="parent"):
        request(child_run=RunIdentity("child-run", "different-parent"))
    with pytest.raises(DelegationDepthViolationError):
        request(depth=0)
    with pytest.raises(DelegationRejectedError, match="sensitive"):
        request(context_allowlist=("secrets",), sensitive_context_exclusions=("secrets",))


def test_delegation_decision_requires_effective_references_when_accepted():
    with pytest.raises(DelegationRejectedError, match="effective"):
        DelegationDecision(
            "decision-1",
            "request-1",
            "parent-run",
            True,
            True,
            DelegationReasonCode.ACCEPTED,
            delegated_provenance(),
        )

    decision = DelegationDecision(
        "decision-1",
        "request-1",
        "parent-run",
        True,
        True,
        DelegationReasonCode.ACCEPTED,
        delegated_provenance(),
        child_run_id="child-run",
        authority_decision_id="authority-1",
        capability_decision_ids=("capability-1",),
        effective_scope_id="scope.child",
        effective_manifest_id="manifest.child",
        effective_context_keys=("project_root",),
    )

    assert decision.to_dict()["reason_code"] == "ACCEPTED"


def test_delegation_module_exposes_no_validator_implementation():
    import orchestra_runtime.delegation as delegation

    assert not hasattr(delegation, "DelegationValidator")


def test_delegation_contracts_reject_empty_and_duplicate_values():
    with pytest.raises(DelegationRejectedError):
        DelegationTask("task", ())
    with pytest.raises(DelegationRejectedError):
        DelegationTask("task", ("same", "same"))
    with pytest.raises(DelegationRejectedError):
        request(requested_capabilities=(capability_grant(), capability_grant()))
