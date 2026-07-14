from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from orchestra_runtime.authority import (
    AuthorityDecision,
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityReasonCode,
    AuthorityScope,
    Constraint,
    ProvenanceSource,
    TargetSelector,
)
from orchestra_runtime.capabilities import (
    CapabilityDecision,
    CapabilityReasonCode,
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
)
from orchestra_runtime.delegation import DelegationPolicy, DelegationValidator
from orchestra_runtime.errors import (
    InvalidLifecycleSignalError,
    RuntimeAuditError,
    RuntimeContractError,
    RuntimeInitializationError,
)
from orchestra_runtime.interfaces import (
    IAuditSink,
    IAuthorityEvaluator,
    ICapabilityResolver,
    IDelegationValidator,
    IGovernanceValidator,
    IIDEAdapter,
    ILifecycleController,
    IRouterService,
    IRuntimeExecutor,
    ISkillRegistry,
)
from orchestra_runtime.lifecycle import (
    LifecycleController,
    LifecycleSignal,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
)
from orchestra_runtime.models import (
    Command,
    ContextPackage,
    ExecutionResult,
    RouteDecision,
    RunIdentity,
    RuntimeAuditEvent,
    ValidationResult,
)
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
    build_compatibility_composition,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class RecordingAdapter(IIDEAdapter):
    def __init__(self, sequence: list[str] | None = None, command_name: str = "conductor") -> None:
        self.sequence = sequence if sequence is not None else []
        self.command_name = command_name
        self.context_metadata: dict[str, object] | None = None
        self.command_metadata: dict[str, object] | None = None

    @property
    def adapter_name(self) -> str:
        return "recording"

    def provide_context(self, prompt: str, metadata: dict | None = None) -> ContextPackage:
        self.sequence.append("adapter-context")
        self.context_metadata = dict(metadata or {})
        return ContextPackage(
            self.adapter_name,
            prompt,
            REPO_ROOT,
            (self.command_name,),
            "1",
            dict(metadata or {}),
        )

    def expose_commands(self) -> tuple[str, ...]:
        return (self.command_name,)

    def parse_command(self, prompt: str, metadata: dict | None = None) -> Command:
        self.sequence.append("command-parse")
        self.command_metadata = dict(metadata or {})
        return Command(self.command_name, prompt, self.adapter_name, metadata=dict(metadata or {}))


class RecordingAuditSink(InMemoryAuditSink):
    def __init__(self, sequence: list[str] | None = None) -> None:
        super().__init__()
        self.sequence = sequence if sequence is not None else []

    def write(self, entry: dict[str, object]) -> str:
        self.sequence.append(f"audit:{entry.get('event_type', 'legacy')}")
        return super().write(entry)


class RecordingAuthorityEvaluator(AuthorityEvaluator):
    def __init__(self, sequence: list[str]) -> None:
        self.sequence = sequence

    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        self.sequence.append("root-validation")
        return super().validate_root(scope)

    def evaluate(self, *args, **kwargs) -> AuthorityDecision:
        self.sequence.append("authority-evaluation")
        return super().evaluate(*args, **kwargs)


class RecordingCapabilityResolver(CapabilityResolver):
    def __init__(self, sequence: list[str]) -> None:
        self.sequence = sequence

    def build_manifest(self, *args, **kwargs) -> RuntimeCapabilityManifest:
        self.sequence.append("manifest-validation")
        return super().build_manifest(*args, **kwargs)

    def evaluate(self, *args, **kwargs) -> CapabilityDecision:
        self.sequence.append("capability-evaluation")
        return super().evaluate(*args, **kwargs)


class RecordingLifecycleController(LifecycleController):
    def __init__(self, sequence: list[str]) -> None:
        self.sequence = sequence

    def initialize(self, run_id: str) -> LifecycleSnapshot:
        self.sequence.append("lifecycle-initialize")
        return super().initialize(run_id)

    def apply(self, snapshot: LifecycleSnapshot, signal: LifecycleSignal) -> LifecycleSnapshot:
        self.sequence.append(f"lifecycle-{signal.requested_state.value}")
        return super().apply(snapshot, signal)


class RecordingGovernance(GovernanceValidator):
    def __init__(self, sequence: list[str], allowed: bool = True) -> None:
        super().__init__(())
        self.sequence = sequence
        self.allowed = allowed

    def validate(self, decision: RouteDecision, context: ContextPackage) -> ValidationResult:
        self.sequence.append("governance")
        if self.allowed:
            return ValidationResult(True, "NOT_REQUIRED")
        return ValidationResult(False, "BLOCKED_PENDING_VALIDATION", ("blocked",), ("test",))


@dataclass
class RuntimeEnvironment:
    executor: RuntimeExecutor
    adapter: RecordingAdapter
    sink: RecordingAuditSink
    registry: SkillRegistry
    repository: ManifestRepository
    composition: RuntimeComposition


def build_active_environment(
    *,
    run_id: str = "active-run",
    command_name: str = "conductor",
    skill_slug: str = "conductor",
    scope_targets: tuple[TargetSelector, ...] | None = None,
    binding_target: TargetSelector | None = None,
    grants: tuple[RuntimeCapabilityGrant, ...] | None = None,
    binding_capability_id: str = "runtime.execute.conductor",
    authority_evaluator: IAuthorityEvaluator | None = None,
    capability_resolver: ICapabilityResolver | None = None,
    lifecycle_controller: ILifecycleController | None = None,
    governance: IGovernanceValidator | None = None,
    audit_sink: RecordingAuditSink | None = None,
    operation=None,
    sequence: list[str] | None = None,
) -> RuntimeEnvironment:
    sequence = sequence if sequence is not None else []
    repository = ManifestRepository(REPO_ROOT)
    registry = SkillRegistry(repository, SkillSourceRepository(REPO_ROOT))
    provenance = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.active.test",
        "1",
        "runtime-composition",
    )
    target = binding_target or TargetSelector(f"specialist:{skill_slug}")
    scope = AuthorityScope(
        "runtime.active.root",
        scope_targets or (target,),
        ("execute",),
        (),
        provenance,
    )
    if grants is None:
        grants = (
            RuntimeCapabilityGrant(
                RuntimeCapability(
                    "runtime.execute.conductor",
                    skill_slug,
                    ("execute",),
                    "Execute the conductor route.",
                ),
                ("execute",),
                provenance,
            ),
        )
    manifest = CapabilityResolver().build_manifest(
        run_id,
        grants,
        provenance,
        manifest_id="runtime.active.manifest",
        policy_version="1",
    )
    binding = RuntimePolicyBinding(
        command_name,
        skill_slug,
        target,
        "execute",
        binding_capability_id,
        "execute",
    )
    policy = RuntimeExecutionPolicy("runtime.active.test", "1", (binding,))
    authority_evaluator = authority_evaluator or AuthorityEvaluator()
    capability_resolver = capability_resolver or CapabilityResolver()
    lifecycle_controller = lifecycle_controller or LifecycleController()
    validator = DelegationValidator(
        authority_evaluator,
        capability_resolver,
        registry,
        DelegationPolicy(
            "runtime.active.delegation",
            "1",
            2,
            allowed_context_keys=("governance_validated",),
            sensitive_context_keys=("secret", "token"),
        ),
    )
    sink = audit_sink or RecordingAuditSink(sequence)
    composition = RuntimeComposition(
        AuthorityMode.ACTIVE,
        manifest.run_identity,
        scope,
        manifest,
        authority_evaluator,
        capability_resolver,
        lifecycle_controller,
        validator,
        AuditLogger(sink),
        policy,
    )
    executor = RuntimeExecutor(
        registry,
        RouterService(registry),
        governance or GovernanceValidator(),
        ContextAssembler(repository),
        composition,
        operation,
    )
    return RuntimeEnvironment(executor, RecordingAdapter(sequence, command_name), sink, registry, repository, composition)


def test_active_runtime_orders_trusted_services_before_operation() -> None:
    sequence: list[str] = []
    evaluator = RecordingAuthorityEvaluator(sequence)
    resolver = RecordingCapabilityResolver(sequence)
    lifecycle = RecordingLifecycleController(sequence)
    governance = RecordingGovernance(sequence)

    def operation(adapter_name: str, route: RouteDecision, validation: ValidationResult) -> RuntimeOperationResult:
        sequence.append("operation")
        return RuntimeOperationResult(LifecycleState.COMPLETED, "done", "EXECUTION_COMPLETED")

    environment = build_active_environment(
        sequence=sequence,
        authority_evaluator=evaluator,
        capability_resolver=resolver,
        lifecycle_controller=lifecycle,
        governance=governance,
        operation=operation,
    )

    result = environment.executor.execute(environment.adapter, "conductor")

    expected = (
        "root-validation",
        "manifest-validation",
        "lifecycle-initialize",
        "audit:ROOT_AUTHORITY_CREATED",
        "audit:CAPABILITY_MANIFEST_CREATED",
        "adapter-context",
        "command-parse",
        "authority-evaluation",
        "audit:AUTHORITY_DECIDED",
        "capability-evaluation",
        "audit:CAPABILITY_DECIDED",
        "governance",
        "lifecycle-ACTIVE",
        "operation",
        "lifecycle-COMPLETED",
        "audit:TERMINAL_RESULT_RECORDED",
        "audit:legacy",
    )
    assert all(sequence.index(item) < sequence.index(expected[index + 1]) for index, item in enumerate(expected[:-1]))
    assert result.success is True
    assert result.authority_mode == "ACTIVE"
    assert result.lifecycle_state == "COMPLETED"
    assert result.run_identity == environment.composition.run_identity
    assert result.authority_decision_id
    assert result.capability_decision_id
    assert result.terminal_result and result.terminal_result.output == "done"
    assert len(result.runtime_audit_event_ids) == 7


def test_active_mode_requires_explicit_composition_before_adapter_access() -> None:
    environment = build_active_environment()
    adapter = RecordingAdapter()

    with pytest.raises(RuntimeInitializationError) as error:
        RuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            None,  # type: ignore[arg-type]
        )

    assert error.value.reason_code == "MISSING_ACTIVE_CONFIGURATION"
    assert adapter.sequence == []


def test_compatibility_mode_is_explicit_and_finite() -> None:
    repository = ManifestRepository(REPO_ROOT)
    registry = SkillRegistry(repository, SkillSourceRepository(REPO_ROOT))
    composition = build_compatibility_composition(registry, InMemoryAuditSink(), run_id="compatibility-run")

    assert composition.mode is AuthorityMode.COMPATIBILITY
    assert composition.policy.bindings
    assert composition.policy.binding_for("conductor", "conductor") is not None
    assert composition.policy.binding_for("unknown", "conductor") is None
    assert all(binding.authority_operation == "execute" for binding in composition.policy.bindings)
    assert all(binding.capability_operation == "execute" for binding in composition.policy.bindings)
    grants = {grant.capability.capability_id: grant for grant in composition.capability_manifest.grants}
    assert all(grant.provenance == composition.capability_manifest.provenance for grant in grants.values())
    assert all(grants[binding.capability_id].capability.owner == binding.skill_slug for binding in composition.policy.bindings)
    with pytest.raises(RuntimeInitializationError, match="explicit compatibility mode"):
        replace(composition, mode=AuthorityMode.ACTIVE)


def test_runtime_composition_rejects_foreign_capability_grant_provenance() -> None:
    foreign = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.foreign",
        "1",
        "runtime-composition",
    )
    grant = RuntimeCapabilityGrant(
        RuntimeCapability("runtime.execute.conductor", "conductor", ("execute",), "Foreign grant."),
        ("execute",),
        foreign,
    )
    sequence: list[str] = []

    with pytest.raises(RuntimeInitializationError) as error:
        build_active_environment(grants=(grant,), sequence=sequence)

    assert error.value.reason_code == "CAPABILITY_GRANT_PROVENANCE_MISMATCH"
    assert error.value.context == (
        ("capability_id", "runtime.execute.conductor"),
        ("manifest_id", "runtime.active.manifest"),
    )
    assert sequence == []


def test_runtime_composition_rejects_binding_capability_owner_mismatch() -> None:
    trusted = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.active.test",
        "1",
        "runtime-composition",
    )
    grant = RuntimeCapabilityGrant(
        RuntimeCapability("runtime.execute.conductor", "ponytail", ("execute",), "Wrong owner."),
        ("execute",),
        trusted,
    )
    sequence: list[str] = []

    assert grant.capability.capability_id == "runtime.execute.conductor"
    assert "execute" in grant.allowed_operations
    with pytest.raises(RuntimeInitializationError) as error:
        build_active_environment(grants=(grant,), sequence=sequence)

    assert error.value.reason_code == "CAPABILITY_OWNER_MISMATCH"
    assert error.value.context == (
        ("capability_id", "runtime.execute.conductor"),
        ("capability_owner", "ponytail"),
        ("skill_slug", "conductor"),
    )
    assert sequence == []


def test_missing_binding_blocks_without_authority_governance_or_operation() -> None:
    sequence: list[str] = []
    governance = RecordingGovernance(sequence)

    def operation(*args) -> RuntimeOperationResult:
        sequence.append("operation")
        return RuntimeOperationResult(LifecycleState.COMPLETED, "unexpected", "UNEXPECTED")

    environment = build_active_environment(sequence=sequence, governance=governance, operation=operation)
    adapter = RecordingAdapter(sequence, "unbound-command")

    result = environment.executor.execute(adapter, "unbound-command")

    assert result.validation.status == "RUNTIME_BINDING_DENIED"
    assert result.lifecycle_state == "BLOCKED"
    assert result.authority_decision_id is None
    assert result.capability_decision_id is None
    assert "governance" not in sequence
    assert "operation" not in sequence


def test_authority_denial_precedes_capability_governance_and_operation() -> None:
    sequence: list[str] = []
    evaluator = RecordingAuthorityEvaluator(sequence)
    resolver = RecordingCapabilityResolver(sequence)
    governance = RecordingGovernance(sequence)
    environment = build_active_environment(
        sequence=sequence,
        scope_targets=(TargetSelector("specialist:clockwork"),),
        binding_target=TargetSelector("specialist:conductor"),
        authority_evaluator=evaluator,
        capability_resolver=resolver,
        governance=governance,
        operation=lambda *args: sequence.append("operation"),
    )

    result = environment.executor.execute(environment.adapter, "conductor", {"governance_validated": True})

    assert result.validation.status == "AUTHORITY_DENIED"
    assert result.lifecycle_state == "BLOCKED"
    assert result.capability_decision_id is None
    assert "capability-evaluation" not in sequence
    assert "governance" not in sequence
    assert "operation" not in sequence


def test_capability_denial_precedes_governance_and_operation() -> None:
    sequence: list[str] = []
    resolver = RecordingCapabilityResolver(sequence)
    governance = RecordingGovernance(sequence)
    environment = build_active_environment(
        sequence=sequence,
        binding_capability_id="runtime.execute.missing",
        capability_resolver=resolver,
        governance=governance,
        operation=lambda *args: sequence.append("operation"),
    )

    result = environment.executor.execute(environment.adapter, "conductor", {"governance_validated": True})

    assert result.validation.status == "CAPABILITY_DENIED"
    assert result.validation.reasons == ("CAPABILITY_NOT_FOUND",)
    assert result.lifecycle_state == "BLOCKED"
    assert result.authority_decision_id
    assert result.capability_decision_id
    assert "governance" not in sequence
    assert "operation" not in sequence
    assert all(
        grant.capability.capability_id != "runtime.execute.missing"
        for grant in environment.composition.capability_manifest.grants
    )


def test_governance_can_block_authorized_work_but_grants_nothing() -> None:
    sequence: list[str] = []
    governance = RecordingGovernance(sequence, allowed=False)
    environment = build_active_environment(
        sequence=sequence,
        governance=governance,
        operation=lambda *args: sequence.append("operation"),
    )

    result = environment.executor.execute(environment.adapter, "conductor")

    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
    assert result.lifecycle_state == "BLOCKED"
    assert result.authority_decision_id
    assert result.capability_decision_id
    assert "operation" not in sequence


@pytest.mark.parametrize(
    ("state", "expected_success", "terminal"),
    (
        (LifecycleState.COMPLETED, True, True),
        (LifecycleState.WAITING, False, False),
        (LifecycleState.FAILED, False, True),
        (LifecycleState.CANCELLED, False, True),
        (LifecycleState.TIMED_OUT, False, True),
    ),
)
def test_structured_operation_results_preserve_lifecycle_states(
    state: LifecycleState,
    expected_success: bool,
    terminal: bool,
) -> None:
    environment = build_active_environment(
        run_id=f"outcome-{state.value.casefold()}",
        operation=lambda *args: RuntimeOperationResult(state, "COMPLETED WAITING CANCELLED", f"TEST_{state.value}"),
    )

    result = environment.executor.execute(environment.adapter, "conductor")

    assert result.success is expected_success
    assert result.lifecycle_state == state.value
    assert (result.terminal_result is not None) is terminal
    assert result.output == "COMPLETED WAITING CANCELLED"


@pytest.mark.parametrize("operation", (lambda *args: (_ for _ in ()).throw(OSError("private")), lambda *args: "text"))
def test_runtime_exception_or_unstructured_result_maps_to_failed(operation) -> None:
    environment = build_active_environment(operation=operation)

    result = environment.executor.execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.lifecycle_state == "FAILED"
    assert result.output == "runtime operation failed"
    assert result.terminal_result and result.terminal_result.reason_code == "RUNTIME_EXCEPTION"
    assert "private" not in result.output


class FailingAuditSink(IAuditSink):
    def __init__(self, fail_event_type: str | None = None, runtime_error: bool = False) -> None:
        self.fail_event_type = fail_event_type
        self.runtime_error = runtime_error
        self.entries: list[dict[str, object]] = []

    def write(self, entry: dict[str, object]) -> str:
        self.entries.append(dict(entry))
        if self.fail_event_type is None or entry.get("event_type") == self.fail_event_type:
            if self.runtime_error:
                raise RuntimeAuditError("already typed", "AUDIT_SINK_FAILURE")
            raise OSError("private sink failure")
        return str(entry.get("event_id", "legacy"))


def test_initial_audit_failure_is_typed_and_precedes_adapter() -> None:
    sink = FailingAuditSink()
    environment = build_active_environment(audit_sink=sink)  # type: ignore[arg-type]

    with pytest.raises(RuntimeAuditError) as error:
        environment.executor.execute(environment.adapter, "conductor")

    assert error.value.reason_code == "AUDIT_SINK_FAILURE"
    assert environment.adapter.sequence == []


def test_terminal_audit_failure_preserves_accepted_terminal_snapshot() -> None:
    sink = FailingAuditSink("TERMINAL_RESULT_RECORDED")
    environment = build_active_environment(audit_sink=sink)  # type: ignore[arg-type]

    with pytest.raises(RuntimeAuditError):
        environment.executor.execute(environment.adapter, "conductor")

    snapshot = environment.executor.last_lifecycle_snapshot
    assert snapshot is not None
    assert snapshot.state is LifecycleState.COMPLETED
    assert snapshot.terminal_result and snapshot.terminal_result.reason_code == "EXECUTION_COMPLETED"


def test_typed_audit_failure_is_not_rewrapped() -> None:
    sink = FailingAuditSink(runtime_error=True)
    environment = build_active_environment(audit_sink=sink)  # type: ignore[arg-type]

    with pytest.raises(RuntimeAuditError, match="already typed"):
        environment.executor.execute(environment.adapter, "conductor")


class RejectingRootEvaluator(AuthorityEvaluator):
    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        raise RuntimeInitializationError("rejected root", "ROOT_REJECTED")


def test_initialization_failure_is_audited_before_adapter() -> None:
    sink = RecordingAuditSink()
    environment = build_active_environment(authority_evaluator=RejectingRootEvaluator(), audit_sink=sink)

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute(environment.adapter, "conductor")

    assert error.value.reason_code == "ROOT_REJECTED"
    assert environment.adapter.sequence == []
    assert [entry.get("event_type") for entry in sink.entries] == ["INITIALIZATION_FAILED"]


class ChangedRootEvaluator(AuthorityEvaluator):
    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        return replace(scope, scope_id="runtime.active.changed")


class ChangedManifestResolver(CapabilityResolver):
    def build_manifest(self, *args, **kwargs) -> RuntimeCapabilityManifest:
        return replace(super().build_manifest(*args, **kwargs), manifest_id="runtime.active.changed")


class InvalidLifecycleController(LifecycleController):
    def initialize(self, run_id: str) -> LifecycleSnapshot:
        return LifecycleSnapshot(RunIdentity(run_id), LifecycleState.ACTIVE)


@pytest.mark.parametrize(
    ("override", "reason_code"),
    (
        ({"authority_evaluator": ChangedRootEvaluator()}, "ROOT_AUTHORITY_MISMATCH"),
        ({"capability_resolver": ChangedManifestResolver()}, "CAPABILITY_MANIFEST_MISMATCH"),
        ({"lifecycle_controller": InvalidLifecycleController()}, "LIFECYCLE_INITIALIZATION_MISMATCH"),
    ),
)
def test_trusted_initialization_rejects_changed_contracts_before_adapter(override, reason_code: str) -> None:
    environment = build_active_environment(**override)

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute(environment.adapter, "conductor")

    assert error.value.reason_code == reason_code
    assert "adapter-context" not in environment.adapter.sequence
    assert "command-parse" not in environment.adapter.sequence


class WrongRunAuthorityEvaluator(AuthorityEvaluator):
    def evaluate(self, *args, **kwargs) -> AuthorityDecision:
        decision = super().evaluate(*args, **kwargs)
        return replace(decision, run_id="wrong-run")


class WrongRunCapabilityResolver(CapabilityResolver):
    def evaluate(self, *args, **kwargs) -> CapabilityDecision:
        decision = super().evaluate(*args, **kwargs)
        return replace(decision, run_id="wrong-run")


@pytest.mark.parametrize(
    ("override", "reason_code"),
    (
        ({"authority_evaluator": WrongRunAuthorityEvaluator()}, "AUTHORITY_DECISION_MISMATCH"),
        ({"capability_resolver": WrongRunCapabilityResolver()}, "CAPABILITY_DECISION_MISMATCH"),
    ),
)
def test_runtime_rejects_decisions_for_another_run(override, reason_code: str) -> None:
    environment = build_active_environment(**override)

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute(environment.adapter, "conductor")

    assert error.value.reason_code == reason_code


class RejectingTransitionController(LifecycleController):
    def apply(self, snapshot: LifecycleSnapshot, signal: LifecycleSignal) -> LifecycleSnapshot:
        raise InvalidLifecycleSignalError("rejected", "TEST_REJECTION")


def test_lifecycle_rejection_is_audited_and_preserves_state() -> None:
    sink = RecordingAuditSink()
    environment = build_active_environment(lifecycle_controller=RejectingTransitionController(), audit_sink=sink)

    with pytest.raises(InvalidLifecycleSignalError):
        environment.executor.execute(environment.adapter, "conductor")

    assert environment.executor.last_lifecycle_snapshot
    assert environment.executor.last_lifecycle_snapshot.state is LifecycleState.INITIALIZING
    rejection = next(entry for entry in sink.entries if entry.get("reason_code") == "TEST_REJECTION")
    assert rejection["details"]["accepted"] == "false"


def test_runtime_contract_values_fail_closed_on_malformed_construction() -> None:
    constraint = Constraint.exact("workspace", "repo")
    valid_binding = RuntimePolicyBinding(
        "conductor",
        "conductor",
        TargetSelector("specialist:conductor"),
        "execute",
        "runtime.execute.conductor",
        "execute",
    )

    with pytest.raises(RuntimeInitializationError):
        replace(valid_binding, command_name="bad command")
    with pytest.raises(RuntimeInitializationError):
        replace(valid_binding, authority_target=object())  # type: ignore[arg-type]
    with pytest.raises(RuntimeInitializationError):
        replace(valid_binding, authority_constraints=(constraint, constraint))
    with pytest.raises(RuntimeInitializationError):
        replace(valid_binding, capability_constraints=(constraint, constraint))
    with pytest.raises(RuntimeInitializationError):
        RuntimeExecutionPolicy("runtime.empty", "1", ())
    with pytest.raises(RuntimeInitializationError):
        RuntimeExecutionPolicy("runtime.duplicate", "1", (valid_binding, valid_binding))
    with pytest.raises(RuntimeInitializationError):
        RuntimeOperationResult(LifecycleState.ACTIVE, "", "INVALID")
    with pytest.raises(RuntimeInitializationError):
        RuntimeOperationResult(LifecycleState.COMPLETED, "", " ")
    assert RuntimeExecutionPolicy("runtime.valid", "1", (valid_binding,)).to_dict()["bindings"]


def test_runtime_composition_rejects_invalid_modes_and_contract_mismatches() -> None:
    environment = build_active_environment()
    composition = environment.composition

    with pytest.raises(RuntimeInitializationError):
        replace(composition, mode="UNLIMITED")  # type: ignore[arg-type]
    with pytest.raises(RuntimeInitializationError):
        replace(composition, authority_evaluator=None)  # type: ignore[arg-type]
    with pytest.raises(RuntimeInitializationError):
        replace(composition, run_identity=RunIdentity("different-run"))
    with pytest.raises(RuntimeInitializationError):
        replace(composition, policy=replace(composition.policy, policy_version="2"))
    with pytest.raises(RuntimeInitializationError):
        replace(composition, root_authority=replace(composition.root_authority, parent_scope_id="parent.scope"))
    with pytest.raises(RuntimeInitializationError):
        RuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            composition,
            operation="not-callable",  # type: ignore[arg-type]
        )
    with pytest.raises(RuntimeInitializationError):
        build_compatibility_composition(object(), object(), run_id="bad")  # type: ignore[arg-type]


def test_runtime_error_context_and_execution_evidence_are_immutable_and_validated() -> None:
    error = RuntimeContractError("denied", AuthorityReasonCode.TARGET_NOT_ALLOWED, {"b": "2", "a": "1"})
    assert error.reason_code == "TARGET_NOT_ALLOWED"
    assert error.context == (("a", "1"), ("b", "2"))
    with pytest.raises(ValueError, match="reason_code"):
        RuntimeContractError("bad", "")
    with pytest.raises(ValueError, match="unique"):
        RuntimeContractError("bad", "BAD", (("key", "1"), ("key", "2")))

    route = RouteDecision("conductor", "conductor", False, "test")
    validation = ValidationResult(True, "NOT_REQUIRED")
    with pytest.raises(ValueError, match="run identity"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", authority_mode="ACTIVE")
    with pytest.raises(ValueError, match="identifiers"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", runtime_audit_event_ids=("same", "same"))
    with pytest.raises(ValueError, match="authority mode"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", RunIdentity("run"), authority_mode="BAD", lifecycle_state="ACTIVE")
    with pytest.raises(ValueError, match="lifecycle state"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", RunIdentity("run"), authority_mode="ACTIVE", lifecycle_state="BAD")
    terminal = StructuredTerminalResult("run", LifecycleState.COMPLETED, "DONE")
    with pytest.raises(ValueError, match="match lifecycle"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", RunIdentity("run"), authority_mode="ACTIVE", lifecycle_state="FAILED", terminal_result=terminal)
    with pytest.raises(ValueError, match="non-terminal"):
        ExecutionResult(True, "test", "conductor", route, validation, "", "", RunIdentity("run"), authority_mode="ACTIVE", lifecycle_state="ACTIVE", terminal_result=terminal)


def test_shared_runtime_models_validate_identity_and_audit_shape() -> None:
    assert RunIdentity(" run ", " parent ").to_dict() == {"run_id": "run", "parent_run_id": "parent"}
    with pytest.raises(ValueError, match="non-empty"):
        RunIdentity(" ")
    with pytest.raises(ValueError, match="differ"):
        RunIdentity("same", "same")
    event = RuntimeAuditEvent("event", "AUTHORITY_DECIDED", "run", "decision", "ALLOWED", ("b", "a"), (("z", "1"), ("a", "2")))
    assert event.to_dict()["provenance_ids"] == ["a", "b"]
    with pytest.raises(ValueError, match="non-empty"):
        RuntimeAuditEvent("", "AUTHORITY_DECIDED", "run", "decision", "ALLOWED")
    with pytest.raises(ValueError, match="unique"):
        RuntimeAuditEvent("event", "AUTHORITY_DECIDED", "run", "decision", "ALLOWED", details=(("key", "1"), ("key", "2")))


def test_abstract_runtime_boundaries_default_to_not_implemented() -> None:
    calls = (
        lambda: IIDEAdapter.adapter_name.fget(object()),
        lambda: IIDEAdapter.provide_context(object(), "prompt"),
        lambda: IIDEAdapter.expose_commands(object()),
        lambda: IIDEAdapter.parse_command(object(), "prompt"),
        lambda: ISkillRegistry.load_skills(object()),
        lambda: ISkillRegistry.get_skill(object(), "slug"),
        lambda: IRouterService.route(object(), None, None),
        lambda: IGovernanceValidator.validate(object(), None, None),
        lambda: IRuntimeExecutor.execute(object(), None, "prompt"),
        lambda: IRuntimeExecutor.execute_delegated(object(), None, "prompt", None),
        lambda: IAuditSink.write(object(), {}),
        lambda: IAuthorityEvaluator.validate_root(object(), None),
        lambda: IAuthorityEvaluator.evaluate(object(), None, None, "execute", (), run_id="run", decision_id="decision"),
        lambda: IAuthorityEvaluator.intersect(object(), None, None, None),
        lambda: ICapabilityResolver.build_manifest(object(), "run", (), None, manifest_id="manifest", policy_version="1"),
        lambda: ICapabilityResolver.evaluate(object(), None, "capability", "execute", (), decision_id="decision"),
        lambda: ICapabilityResolver.intersect(object(), None, (), "child", None, manifest_id="manifest"),
        lambda: IDelegationValidator.validate(object(), None, None, None),
        lambda: ILifecycleController.initialize(object(), "run"),
        lambda: ILifecycleController.apply(object(), None, None),
        lambda: ILifecycleController.terminal_result(object(), None),
    )

    for call in calls:
        with pytest.raises(NotImplementedError):
            call()
