from orchestra_runtime.authority import (
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityScope,
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
    DelegationRequest,
    DelegationTask,
    DelegationValidator,
    delegation_accepted_event,
    delegation_rejected_event,
)
from orchestra_runtime.lifecycle import (
    LifecycleController,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleState,
    StructuredTerminalResult,
    lifecycle_transition_event,
    terminal_result_event,
)
from orchestra_runtime.models import RunIdentity


class Registry:
    def get_skill(self, slug: str):
        return object() if slug == "clockwork" else None


def test_accepted_delegation_contract_initializes_child_lifecycle_without_execution():
    root = AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, "policy.root", "1", "runtime")
    parent_scope = AuthorityScope(
        "scope.parent",
        (TargetSelector("repository:orchestra"),),
        ("read",),
        (),
        root,
    )
    capability = RuntimeCapability("filesystem.read", "clockwork", ("read",), "Read repository")
    grant = RuntimeCapabilityGrant(capability, ("read",), root)
    parent_manifest = RuntimeCapabilityManifest(
        "manifest.parent",
        RunIdentity("parent-run"),
        "1",
        (grant,),
        root,
    )
    request = DelegationRequest(
        "request-1",
        RunIdentity("parent-run"),
        RunIdentity("child-run", "parent-run"),
        "clockwork",
        DelegationTask("Inspect runtime", ("Return findings",)),
        AuthorityScope("scope.child", parent_scope.targets, parent_scope.operations, (), root),
        (grant,),
        ("project_root",),
        ("secrets",),
        1,
        root,
    )
    resolution = DelegationValidator(
        AuthorityEvaluator(),
        CapabilityResolver(),
        Registry(),
        DelegationPolicy("delegation.policy", "1", 1, ("project_root",), ("secrets",)),
    ).validate(request, parent_scope, parent_manifest)

    assert resolution.decision.allowed is True
    assert resolution.effective_manifest is not None
    controller = LifecycleController()
    initial = controller.initialize(resolution.effective_manifest.run_identity.run_id)
    activate = LifecycleSignal(
        "activate-child",
        "child-run",
        LifecycleSignalType.ACTIVATE,
        LifecycleState.INITIALIZING,
        LifecycleState.ACTIVE,
        "ACTIVATED",
        "runtime",
        resolution.decision.provenance,
    )
    active = controller.apply(initial, activate)
    result = StructuredTerminalResult("child-run", LifecycleState.COMPLETED, "DONE", "validated")
    complete = LifecycleSignal(
        "complete-child",
        "child-run",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
        "DONE",
        "runtime",
        resolution.decision.provenance,
        terminal_result=result,
    )
    completed = controller.apply(active, complete)

    assert delegation_accepted_event(resolution).parent_run_id == "parent-run"
    assert lifecycle_transition_event(initial, activate, active).run_id == "child-run"
    assert terminal_result_event(completed).reason_code == "DONE"


def test_rejected_delegation_produces_no_child_contract_or_lifecycle_start():
    root = AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, "policy.root", "1", "runtime")
    parent_scope = AuthorityScope("scope.parent", (TargetSelector("repository:orchestra"),), ("read",), (), root)
    capability = RuntimeCapability("filesystem.read", "clockwork", ("read",), "Read repository")
    grant = RuntimeCapabilityGrant(capability, ("read",), root)
    manifest = RuntimeCapabilityManifest("manifest.parent", RunIdentity("parent-run"), "1", (grant,), root)
    request = DelegationRequest(
        "request-unknown",
        RunIdentity("parent-run"),
        RunIdentity("child-run", "parent-run"),
        "unknown",
        DelegationTask("Inspect runtime", ("Return findings",)),
        AuthorityScope("scope.child", parent_scope.targets, parent_scope.operations, (), root),
        (grant,),
        (),
        ("secrets",),
        1,
        root,
    )
    resolution = DelegationValidator(
        AuthorityEvaluator(),
        CapabilityResolver(),
        Registry(),
        DelegationPolicy("delegation.policy", "1", 1, (), ("secrets",)),
    ).validate(request, parent_scope, manifest)

    assert resolution.decision.allowed is False
    assert resolution.effective_scope is None
    assert resolution.effective_manifest is None
    assert delegation_rejected_event(resolution).run_id == "parent-run"
