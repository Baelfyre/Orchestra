from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from orchestra_runtime.authority import AuthorityEvaluator, AuthorityProvenance, AuthorityScope, ProvenanceSource, TargetSelector
from orchestra_runtime.capabilities import CapabilityResolver, RuntimeCapability, RuntimeCapabilityGrant
from orchestra_runtime.delegation import (
    DelegationPolicy,
    DelegationRequest,
    DelegationResolution,
    DelegationTask,
    DelegationValidator,
)
from orchestra_runtime.errors import DelegationRejectedError, RuntimeInitializationError
from orchestra_runtime.interfaces import IIDEAdapter
from orchestra_runtime.lifecycle import LifecycleController, LifecycleState
from orchestra_runtime.models import Command, ContextPackage, RouteDecision, RunIdentity, ValidationResult
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    AuthorityMode,
    AuditLogger,
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeComposition,
    RuntimeExecutionPolicy,
    RuntimeExecutor,
    RuntimeOperationResult,
    RuntimePolicyBinding,
    SkillRegistry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class ChildAdapter(IIDEAdapter):
    def __init__(self) -> None:
        self.context_calls = 0
        self.parse_calls = 0
        self.context_metadata: dict[str, object] | None = None
        self.command_metadata: dict[str, object] | None = None

    @property
    def adapter_name(self) -> str:
        return "child"

    def provide_context(self, prompt: str, metadata: dict | None = None) -> ContextPackage:
        self.context_calls += 1
        self.context_metadata = dict(metadata or {})
        return ContextPackage(
            self.adapter_name,
            prompt,
            REPO_ROOT,
            ("ponytail",),
            "1",
            dict(metadata or {}),
        )

    def expose_commands(self) -> tuple[str, ...]:
        return ("ponytail",)

    def parse_command(self, prompt: str, metadata: dict | None = None) -> Command:
        self.parse_calls += 1
        self.command_metadata = dict(metadata or {})
        return Command("ponytail", prompt, self.adapter_name, metadata=dict(metadata or {}))


@dataclass
class DelegationEnvironment:
    executor: RuntimeExecutor
    adapter: ChildAdapter
    sink: InMemoryAuditSink
    composition: RuntimeComposition
    validator: DelegationValidator
    capability: RuntimeCapability
    grant: RuntimeCapabilityGrant
    operation_calls: list[tuple[str, str]]


def build_delegation_environment(run_id: str = "parent-run") -> DelegationEnvironment:
    repository = ManifestRepository(REPO_ROOT)
    registry = SkillRegistry(repository, SkillSourceRepository(REPO_ROOT))
    evaluator = AuthorityEvaluator()
    resolver = CapabilityResolver()
    lifecycle = LifecycleController()
    provenance = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.delegation.test",
        "1",
        "runtime-composition",
    )
    target = TargetSelector("specialist:ponytail")
    scope = AuthorityScope("runtime.delegation.parent", (target,), ("execute",), (), provenance)
    capability = RuntimeCapability(
        "runtime.execute.ponytail",
        "ponytail",
        ("execute",),
        "Execute a bounded Ponytail child route.",
    )
    grant = RuntimeCapabilityGrant(capability, ("execute",), provenance)
    manifest = resolver.build_manifest(
        run_id,
        (grant,),
        provenance,
        manifest_id="runtime.delegation.parent.manifest",
        policy_version="1",
    )
    policy = RuntimeExecutionPolicy(
        "runtime.delegation.test",
        "1",
        (
            RuntimePolicyBinding(
                "ponytail",
                "ponytail",
                target,
                "execute",
                capability.capability_id,
                "execute",
            ),
        ),
    )
    validator = DelegationValidator(
        evaluator,
        resolver,
        registry,
        DelegationPolicy(
            "runtime.delegation.test",
            "1",
            2,
            allowed_context_keys=("governance_validated",),
            sensitive_context_keys=("secret", "token"),
        ),
    )
    sink = InMemoryAuditSink()
    composition = RuntimeComposition(
        AuthorityMode.ACTIVE,
        manifest.run_identity,
        scope,
        manifest,
        evaluator,
        resolver,
        lifecycle,
        validator,
        AuditLogger(sink),
        policy,
    )
    operation_calls: list[tuple[str, str]] = []

    def operation(adapter_name: str, route: RouteDecision, validation: ValidationResult) -> RuntimeOperationResult:
        operation_calls.append((adapter_name, route.skill_slug))
        return RuntimeOperationResult(LifecycleState.COMPLETED, "child complete", "CHILD_COMPLETED")

    executor = RuntimeExecutor(
        registry,
        RouterService(registry),
        GovernanceValidator(),
        ContextAssembler(repository),
        composition,
        operation,
    )
    return DelegationEnvironment(executor, ChildAdapter(), sink, composition, validator, capability, grant, operation_calls)


def delegation_request(
    environment: DelegationEnvironment,
    *,
    request_id: str = "request-1",
    child_run_id: str = "child-run",
    specialist_slug: str = "ponytail",
    requested_scope: AuthorityScope | None = None,
    requested_capabilities: tuple[RuntimeCapabilityGrant, ...] | None = None,
    context_allowlist: tuple[str, ...] = ("governance_validated",),
    depth: int = 1,
) -> DelegationRequest:
    parent = environment.composition.run_identity
    return DelegationRequest(
        request_id,
        parent,
        RunIdentity(child_run_id, parent.run_id),
        specialist_slug,
        DelegationTask("Perform bounded child work", ("Return a structured result",)),
        requested_scope
        or AuthorityScope(
            "runtime.delegation.child.request",
            environment.composition.root_authority.targets,
            environment.composition.root_authority.operations,
            (),
            environment.composition.root_authority.provenance,
        ),
        requested_capabilities or (environment.grant,),
        context_allowlist,
        ("secret", "token"),
        depth,
        environment.composition.root_authority.provenance,
    )


def test_accepted_resolution_executes_child_in_process_with_bounded_contracts() -> None:
    environment = build_delegation_environment()
    request = delegation_request(environment)

    result = environment.executor.execute_delegation_request(
        environment.adapter,
        "ponytail child work",
        request,
        metadata={
            "governance_validated": True,
            "dry_run": True,
            "secret": "must-not-inherit",
            "authority_mode": "COMPATIBILITY",
        },
    )

    assert result.success is True
    assert result.lifecycle_state == "COMPLETED"
    assert result.authority_mode == "ACTIVE"
    assert result.run_identity and result.run_identity.run_id == "child-run"
    assert result.run_identity.parent_run_id == "parent-run"
    assert result.terminal_result and result.terminal_result.reason_code == "CHILD_COMPLETED"
    assert environment.operation_calls == [("child", "ponytail")]
    assert environment.adapter.context_metadata == {"governance_validated": True}
    assert environment.adapter.command_metadata == {"governance_validated": True}
    assert environment.executor.last_lifecycle_snapshot
    assert environment.executor.last_lifecycle_snapshot.run_identity.parent_run_id == "parent-run"
    event_types = [entry.get("event_type") for entry in environment.sink.entries]
    assert event_types[0] == "DELEGATION_ACCEPTED"
    assert "ROOT_AUTHORITY_CREATED" not in event_types
    assert "CAPABILITY_MANIFEST_CREATED" in event_types
    assert "AUTHORITY_DECIDED" in event_types
    assert "CAPABILITY_DECIDED" in event_types
    assert "TERMINAL_RESULT_RECORDED" in event_types


def test_child_run_identity_cannot_execute_twice_but_distinct_child_can() -> None:
    environment = build_delegation_environment()
    resolution = environment.validator.validate(
        delegation_request(environment),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )

    first = environment.executor.execute_delegated(environment.adapter, "first child", resolution)
    first_snapshot = environment.executor.last_lifecycle_snapshot
    assert first_snapshot is not None
    first_terminal = first_snapshot.terminal_result

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute_delegated(environment.adapter, "same child", resolution)

    assert error.value.reason_code == "RUN_ALREADY_INITIALIZED"
    assert error.value.context == (("current_state", "COMPLETED"), ("run_id", "child-run"))
    assert environment.adapter.context_calls == 1
    assert environment.adapter.parse_calls == 1
    assert environment.operation_calls == [("child", "ponytail")]
    assert environment.executor.last_lifecycle_snapshot is first_snapshot
    assert first.terminal_result is first_terminal

    second_resolution = environment.validator.validate(
        delegation_request(environment, request_id="request-2", child_run_id="child-run-2"),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )
    second = environment.executor.execute_delegated(environment.adapter, "second child", second_resolution)

    assert second.run_identity and second.run_identity.run_id == "child-run-2"
    assert environment.adapter.context_calls == 2
    assert environment.adapter.parse_calls == 2
    assert environment.operation_calls == [("child", "ponytail"), ("child", "ponytail")]

    legacy_entries = [entry for entry in environment.sink.entries if "event_id" not in entry]
    assert [(entry["run_id"], entry["id"]) for entry in legacy_entries] == [
        ("child-run", first.audit_entry_id),
        ("child-run-2", second.audit_entry_id),
    ]
    assert all(entry["authority_mode"] == "ACTIVE" for entry in legacy_entries)
    assert all(entry["lifecycle_state"] == "COMPLETED" for entry in legacy_entries)
    assert len({entry["id"] for entry in legacy_entries}) == 2
    assert first.audit_entry_id != second.audit_entry_id

    structured_entries = {
        str(entry["event_id"]): entry
        for entry in environment.sink.entries
        if "event_id" in entry
    }
    for result in (first, second):
        assert result.runtime_audit_event_ids
        assert result.audit_entry_id not in result.runtime_audit_event_ids
        assert all(event_id.startswith("event.") for event_id in result.runtime_audit_event_ids)
        assert all(structured_entries[event_id]["id"] == event_id for event_id in result.runtime_audit_event_ids)


def test_accepted_resolution_contains_strict_immutable_child_contracts() -> None:
    environment = build_delegation_environment()
    request = delegation_request(environment)

    resolution = environment.validator.validate(
        request,
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )

    assert resolution.decision.allowed is True
    assert resolution.effective_scope is not None
    assert resolution.effective_manifest is not None
    assert set(resolution.effective_scope.targets).issubset(environment.composition.root_authority.targets)
    assert set(resolution.effective_scope.operations).issubset(environment.composition.root_authority.operations)
    assert resolution.effective_scope.parent_scope_id == environment.composition.root_authority.scope_id
    assert resolution.effective_manifest.run_identity.parent_run_id == environment.composition.run_identity.run_id
    assert resolution.effective_manifest.grants[0].capability == environment.capability
    assert resolution.decision.effective_context_keys == ("governance_validated",)
    with pytest.raises(AttributeError):
        resolution.effective_scope.scope_id = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    (
        ("provenance", "CAPABILITY_GRANT_PROVENANCE_MISMATCH"),
        ("owner", "CAPABILITY_OWNER_MISMATCH"),
    ),
)
def test_delegated_composition_rejects_invalid_effective_grant_contract(
    mutation: str,
    reason_code: str,
) -> None:
    environment = build_delegation_environment()
    resolution = environment.validator.validate(
        delegation_request(environment),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )
    assert resolution.effective_manifest is not None
    grant = resolution.effective_manifest.grants[0]
    if mutation == "provenance":
        foreign = AuthorityProvenance(
            ProvenanceSource.TRUSTED_COMPOSITION,
            "runtime.foreign",
            "1",
            "runtime-composition",
        )
        invalid_grant = replace(grant, provenance=foreign)
    else:
        invalid_grant = replace(grant, capability=replace(grant.capability, owner="conductor"))
        assert invalid_grant.capability.capability_id == environment.composition.policy.bindings[0].capability_id
        assert "execute" in invalid_grant.allowed_operations
    invalid_manifest = replace(resolution.effective_manifest, grants=(invalid_grant,))
    invalid_resolution = replace(resolution, effective_manifest=invalid_manifest)

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute_delegated(environment.adapter, "invalid child", invalid_resolution)

    assert error.value.reason_code == reason_code
    assert environment.adapter.context_calls == 0
    assert environment.adapter.parse_calls == 0
    assert environment.operation_calls == []


def test_rejected_resolution_never_initializes_adapter_or_child_operation() -> None:
    environment = build_delegation_environment()
    request = delegation_request(environment, specialist_slug="unknown-specialist")
    resolution = environment.validator.validate(
        request,
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )

    with pytest.raises(DelegationRejectedError) as error:
        environment.executor.execute_delegated(environment.adapter, "child work", resolution)

    assert error.value.reason_code == "UNKNOWN_SPECIALIST"
    assert environment.adapter.context_calls == 0
    assert environment.adapter.parse_calls == 0
    assert environment.operation_calls == []
    assert environment.executor.last_lifecycle_snapshot is None
    assert environment.sink.entries[-1]["event_type"] == "DELEGATION_REJECTED"


def test_rejected_resolution_object_is_required_for_child_execution() -> None:
    environment = build_delegation_environment()

    with pytest.raises(DelegationRejectedError) as error:
        environment.executor.execute_delegated(environment.adapter, "child work", object())  # type: ignore[arg-type]

    assert error.value.reason_code == "INVALID_REQUEST"
    assert environment.adapter.context_calls == 0
    assert environment.operation_calls == []


def test_accepted_resolution_cannot_execute_under_another_parent() -> None:
    first = build_delegation_environment("first-parent")
    second = build_delegation_environment("second-parent")
    resolution = first.validator.validate(
        delegation_request(first),
        first.composition.root_authority,
        first.composition.capability_manifest,
    )

    with pytest.raises(DelegationRejectedError) as error:
        second.executor.execute_delegated(second.adapter, "child work", resolution)

    assert error.value.reason_code == "INVALID_PARENT"
    assert second.adapter.context_calls == 0
    assert second.operation_calls == []
    assert [entry.get("event_type") for entry in second.sink.entries] == [
        "DELEGATION_ACCEPTED",
        "INITIALIZATION_FAILED",
    ]


def test_broader_child_authority_is_rejected_before_child_execution() -> None:
    environment = build_delegation_environment()
    broader = AuthorityScope(
        "runtime.delegation.child.broader",
        (TargetSelector("specialist:clockwork"),),
        ("execute",),
        (),
        environment.composition.root_authority.provenance,
    )

    with pytest.raises(DelegationRejectedError) as error:
        environment.executor.execute_delegation_request(
            environment.adapter,
            "child work",
            delegation_request(environment, requested_scope=broader),
        )

    assert error.value.reason_code == "AUTHORITY_REJECTED"
    assert environment.adapter.context_calls == 0
    assert environment.operation_calls == []


def test_broader_child_capability_is_rejected_before_child_execution() -> None:
    environment = build_delegation_environment()
    broader_capability = RuntimeCapability(
        "runtime.execute.clockwork",
        "ponytail",
        ("execute",),
        "Not granted to the parent.",
    )
    broader_grant = RuntimeCapabilityGrant(
        broader_capability,
        ("execute",),
        environment.composition.root_authority.provenance,
    )

    with pytest.raises(DelegationRejectedError) as error:
        environment.executor.execute_delegation_request(
            environment.adapter,
            "child work",
            delegation_request(environment, requested_capabilities=(broader_grant,)),
        )

    assert error.value.reason_code == "CAPABILITY_REJECTED"
    assert environment.adapter.context_calls == 0
    assert environment.operation_calls == []


def test_delegated_composition_requires_matching_accepted_identity() -> None:
    environment = build_delegation_environment()
    resolution = environment.validator.validate(
        delegation_request(environment),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )
    assert resolution.effective_scope and resolution.effective_manifest

    with pytest.raises(RuntimeInitializationError) as error:
        RuntimeComposition(
            AuthorityMode.ACTIVE,
            resolution.effective_manifest.run_identity,
            resolution.effective_scope,
            resolution.effective_manifest,
            environment.composition.authority_evaluator,
            environment.composition.capability_resolver,
            environment.composition.lifecycle_controller,
            environment.composition.delegation_validator,
            environment.composition.audit_logger,
            environment.composition.policy,
            "wrong-decision",
        )

    assert error.value.reason_code == "INVALID_DELEGATED_COMPOSITION"


def test_delegation_resolution_serialization_has_no_context_values() -> None:
    environment = build_delegation_environment()
    resolution: DelegationResolution = environment.validator.validate(
        delegation_request(environment),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )

    serialized = resolution.to_dict()

    assert serialized["decision"]["effective_context_keys"] == ["governance_validated"]
    assert "context_values" not in serialized
    assert "secret" not in str(serialized)
