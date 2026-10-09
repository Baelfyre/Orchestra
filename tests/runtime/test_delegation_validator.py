from dataclasses import FrozenInstanceError

import pytest

from orchestra_runtime.authority import (
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityScope,
    Constraint,
    ProvenanceSource,
    TargetSelector,
)
from orchestra_runtime.capabilities import (
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
)
from orchestra_runtime.delegation import (
    DelegationPolicy,
    DelegationReasonCode,
    DelegationRequest,
    DelegationResolution,
    DelegationTask,
    DelegationValidator,
    delegation_accepted_event,
    delegation_rejected_event,
)
from orchestra_runtime.errors import DelegationRejectedError
from orchestra_runtime.models import AuditEventType, RunIdentity


class Registry:
    def __init__(self, slugs: tuple[str, ...] = ("clockwork",)) -> None:
        self.slugs = slugs

    def get_skill(self, slug: str):
        return object() if slug in self.slugs else None


def provenance(source_id: str = "policy.root") -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, source_id, "1", "runtime")


def capability(owner: str = "clockwork") -> RuntimeCapability:
    return RuntimeCapability("filesystem.access", owner, ("read", "write"), "Repository access")


def parent_contracts() -> tuple[AuthorityScope, RuntimeCapabilityManifest]:
    authority_provenance = provenance()
    capability_provenance = provenance("policy.capabilities")
    scope = AuthorityScope(
        "scope.parent",
        (TargetSelector("repository:orchestra"), TargetSelector("repository:orchestra:docs")),
        ("read", "write"),
        (Constraint.allowed_set("path", ("docs", "runtime")),),
        authority_provenance,
    )
    grant = RuntimeCapabilityGrant(
        capability(),
        ("read", "write"),
        capability_provenance,
        (Constraint.allowed_set("path", ("docs", "runtime")),),
    )
    manifest = RuntimeCapabilityManifest(
        "manifest.parent",
        RunIdentity("parent-run"),
        "1",
        (grant,),
        capability_provenance,
    )
    return scope, manifest


def request(parent_scope: AuthorityScope, parent_manifest: RuntimeCapabilityManifest, **changes) -> DelegationRequest:
    parent_grant = parent_manifest.grants[0]
    data = {
        "request_id": "request-1",
        "parent_run": RunIdentity("parent-run"),
        "child_run": RunIdentity("child-run", "parent-run"),
        "specialist_slug": "clockwork",
        "task": DelegationTask("Inspect runtime", ("Report findings",)),
        "requested_scope": AuthorityScope(
            "scope.child",
            (TargetSelector("repository:orchestra"),),
            ("read",),
            (Constraint.exact("path", "runtime"),),
            parent_scope.provenance,
        ),
        "requested_capabilities": (
            RuntimeCapabilityGrant(
                parent_grant.capability,
                ("read",),
                parent_grant.provenance,
                (Constraint.exact("path", "runtime"),),
            ),
        ),
        "context_allowlist": ("project_root",),
        "sensitive_context_exclusions": ("secrets",),
        "depth": 1,
        "provenance": parent_scope.provenance,
    }
    data.update(changes)
    return DelegationRequest(**data)


def validator(registry: Registry | None = None) -> DelegationValidator:
    return DelegationValidator(
        AuthorityEvaluator(),
        CapabilityResolver(),
        registry or Registry(),
        DelegationPolicy(
            "delegation.policy",
            "1",
            2,
            ("project_root",),
            ("secrets", "token"),
        ),
    )


def test_accepts_bounded_delegation_with_deterministic_immutable_child_contracts():
    parent_scope, parent_manifest = parent_contracts()
    value = request(parent_scope, parent_manifest)

    first = validator().validate(value, parent_scope, parent_manifest)
    second = validator().validate(value, parent_scope, parent_manifest)

    assert first == second
    assert first.decision.allowed is True
    assert first.decision.reason_code is DelegationReasonCode.ACCEPTED
    assert first.effective_scope is not None
    assert first.effective_manifest is not None
    assert first.effective_scope.targets == value.requested_scope.targets
    assert first.effective_manifest.run_identity == RunIdentity("child-run", "parent-run")
    assert first.effective_manifest.grants[0].allowed_operations == ("read",)
    assert first.decision.effective_context_keys == ("project_root",)
    assert first.decision.provenance.source_type is ProvenanceSource.ACCEPTED_DELEGATION
    assert first.to_dict()["effective_scope"]["scope_id"] == "scope.child"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        first.effective_scope = None  # type: ignore[misc]

    event = delegation_accepted_event(first)
    assert event == delegation_accepted_event(second)
    assert event.event_type is AuditEventType.DELEGATION_ACCEPTED
    assert event.run_id == "child-run"
    assert event.parent_run_id == "parent-run"


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"specialist_slug": "unknown"}, DelegationReasonCode.UNKNOWN_SPECIALIST),
        ({"depth": 3}, DelegationReasonCode.DEPTH_EXCEEDED),
        ({"context_allowlist": ("other",)}, DelegationReasonCode.CONTEXT_REJECTED),
        ({"context_allowlist": ("secrets",), "sensitive_context_exclusions": ("token",)}, DelegationReasonCode.CONTEXT_REJECTED),
    ],
)
def test_rejects_unknown_over_depth_unauthorized_and_sensitive_requests(change, reason):
    parent_scope, parent_manifest = parent_contracts()
    resolution = validator().validate(request(parent_scope, parent_manifest, **change), parent_scope, parent_manifest)

    assert resolution.decision.allowed is False
    assert resolution.decision.reason_code is reason
    assert resolution.effective_scope is None
    assert resolution.effective_manifest is None
    assert resolution.decision.provenance.source_type is not ProvenanceSource.ACCEPTED_DELEGATION
    assert delegation_rejected_event(resolution).event_type is AuditEventType.DELEGATION_REJECTED


def test_rejects_parent_mismatch_and_broader_authority_without_partial_contracts():
    parent_scope, parent_manifest = parent_contracts()
    other_manifest = RuntimeCapabilityManifest(
        parent_manifest.manifest_id,
        RunIdentity("other-parent"),
        parent_manifest.policy_version,
        parent_manifest.grants,
        parent_manifest.provenance,
    )
    invalid_parent = validator().validate(request(parent_scope, parent_manifest), parent_scope, other_manifest)

    broader_scope = AuthorityScope(
        "scope.child",
        (TargetSelector("repository:orchestra"), TargetSelector("outside")),
        ("read",),
        (Constraint.exact("path", "runtime"),),
        parent_scope.provenance,
    )
    broader = validator().validate(
        request(parent_scope, parent_manifest, requested_scope=broader_scope),
        parent_scope,
        parent_manifest,
    )

    assert invalid_parent.decision.reason_code is DelegationReasonCode.INVALID_PARENT
    assert invalid_parent.decision.specialist_registered is False
    assert broader.decision.reason_code is DelegationReasonCode.AUTHORITY_REJECTED
    assert broader.effective_scope is None


def test_rejects_broader_or_wrong_owner_capabilities():
    parent_scope, parent_manifest = parent_contracts()
    parent_grant = parent_manifest.grants[0]
    broader_grant = RuntimeCapabilityGrant(
        parent_grant.capability,
        ("read", "write"),
        parent_grant.provenance,
        (),
    )
    wrong_owner = RuntimeCapabilityGrant(
        capability("scribe"),
        ("read",),
        parent_grant.provenance,
        (Constraint.exact("path", "runtime"),),
    )

    broader = validator().validate(
        request(parent_scope, parent_manifest, requested_capabilities=(broader_grant,)),
        parent_scope,
        parent_manifest,
    )
    owner = validator().validate(
        request(parent_scope, parent_manifest, requested_capabilities=(wrong_owner,)),
        parent_scope,
        parent_manifest,
    )

    assert broader.decision.reason_code is DelegationReasonCode.CAPABILITY_REJECTED
    assert owner.decision.reason_code is DelegationReasonCode.CAPABILITY_REJECTED


def test_resolution_and_event_factories_reject_contradictory_use():
    parent_scope, parent_manifest = parent_contracts()
    accepted = validator().validate(request(parent_scope, parent_manifest), parent_scope, parent_manifest)
    rejected = validator(Registry(())).validate(request(parent_scope, parent_manifest), parent_scope, parent_manifest)

    with pytest.raises(DelegationRejectedError, match="rejected event"):
        delegation_rejected_event(accepted)
    with pytest.raises(DelegationRejectedError, match="accepted event"):
        delegation_accepted_event(rejected)
    with pytest.raises(DelegationRejectedError, match="cannot contain"):
        DelegationResolution(rejected.decision, accepted.effective_scope, accepted.effective_manifest)
