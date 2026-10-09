from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from orchestra_runtime.authority import (
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityReasonCode,
    AuthorityScope,
    Constraint,
    ProvenanceSource,
    TargetSelector,
    load_trusted_authority,
)
from orchestra_runtime.capabilities import (
    CapabilityReasonCode,
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
    load_trusted_capability_manifest,
)
from orchestra_runtime.delegation import DelegationRequest
from orchestra_runtime.errors import (
    CapabilityCollisionError,
    ConflictingTerminalSignalError,
    DelegationRejectedError,
    InvalidAuthorityConfigurationError,
    InvalidCapabilityConfigurationError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
    RuntimeAuditError,
    RuntimeInitializationError,
)
from orchestra_runtime.interfaces import IAuditSink
from orchestra_runtime.lifecycle import (
    LifecycleController,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
)
from orchestra_runtime.models import RunIdentity
from orchestra_runtime.services import (
    AuthorityMode,
    ContextAssembler,
    GovernanceValidator,
    RouterService,
    RuntimeComposition,
    RuntimeExecutor,
    RuntimeOperationResult,
    build_compatibility_composition,
)
from tests.runtime.test_runtime_authority_integration import (
    FailingAuditSink,
    RecordingAuthorityEvaluator,
    RecordingCapabilityResolver,
    RecordingGovernance,
    RecordingLifecycleController,
    build_active_environment,
)
from tests.runtime.test_runtime_delegated_execution import (
    build_delegation_environment,
    delegation_request,
)


def provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.adversarial",
        "1",
        "runtime",
    )


def signal(
    signal_id: str,
    signal_type: LifecycleSignalType,
    expected: LifecycleState,
    requested: LifecycleState,
    *,
    output: str = "",
) -> LifecycleSignal:
    terminal_result = (
        StructuredTerminalResult("adversarial-run", requested, requested.value, output)
        if requested.terminal
        else None
    )
    return LifecycleSignal(
        signal_id,
        "adversarial-run",
        signal_type,
        expected,
        requested,
        requested.value,
        "runtime-adversarial-test",
        provenance(),
        terminal_result=terminal_result,
    )


def waiting(controller: LifecycleController) -> LifecycleSnapshot:
    initial = controller.initialize("adversarial-run")
    active = controller.apply(
        initial,
        signal(
            "activate",
            LifecycleSignalType.ACTIVATE,
            LifecycleState.INITIALIZING,
            LifecycleState.ACTIVE,
        ),
    )
    return controller.apply(
        active,
        signal("wait", LifecycleSignalType.WAIT, LifecycleState.ACTIVE, LifecycleState.WAITING),
    )


def test_resume_from_initializing_is_rejected_without_state_change() -> None:
    controller = LifecycleController()
    original = controller.initialize("adversarial-run")
    resume = signal(
        "resume-early",
        LifecycleSignalType.RESUME,
        LifecycleState.INITIALIZING,
        LifecycleState.ACTIVE,
    )

    with pytest.raises(InvalidLifecycleSignalError) as captured:
        controller.apply(original, resume)

    assert captured.value.reason_code == "INVALID_SIGNAL_SOURCE_STATE"
    assert captured.value.context == (
        ("current_state", "INITIALIZING"),
        ("required_state", "WAITING"),
        ("signal_type", "RESUME"),
    )
    assert original.state is LifecycleState.INITIALIZING
    assert controller.terminal_result(original) is None


def test_activate_from_waiting_is_rejected_without_state_change() -> None:
    controller = LifecycleController()
    original = waiting(controller)
    activate = signal(
        "activate-again",
        LifecycleSignalType.ACTIVATE,
        LifecycleState.WAITING,
        LifecycleState.ACTIVE,
    )

    with pytest.raises(InvalidLifecycleSignalError) as captured:
        controller.apply(original, activate)

    assert captured.value.reason_code == "INVALID_SIGNAL_SOURCE_STATE"
    assert captured.value.context == (
        ("current_state", "WAITING"),
        ("required_state", "INITIALIZING"),
        ("signal_type", "ACTIVATE"),
    )
    assert original.state is LifecycleState.WAITING
    assert controller.terminal_result(original) is None


def test_wait_outside_active_remains_a_typed_deterministic_rejection() -> None:
    controller = LifecycleController()
    original = controller.initialize("adversarial-run")
    wait_early = signal(
        "wait-early",
        LifecycleSignalType.WAIT,
        LifecycleState.INITIALIZING,
        LifecycleState.WAITING,
    )

    with pytest.raises(InvalidLifecycleTransitionError) as captured:
        controller.apply(original, wait_early)

    assert captured.value.reason_code == "INVALID_TRANSITION"
    assert original.state is LifecycleState.INITIALIZING
    assert controller.terminal_result(original) is None


def test_valid_activate_wait_and_resume_sequence_is_unchanged() -> None:
    controller = LifecycleController()
    initial = controller.initialize("adversarial-run")
    active = controller.apply(
        initial,
        signal(
            "activate",
            LifecycleSignalType.ACTIVATE,
            LifecycleState.INITIALIZING,
            LifecycleState.ACTIVE,
        ),
    )
    parked = controller.apply(
        active,
        signal("wait", LifecycleSignalType.WAIT, LifecycleState.ACTIVE, LifecycleState.WAITING),
    )
    resumed = controller.apply(
        parked,
        signal("resume", LifecycleSignalType.RESUME, LifecycleState.WAITING, LifecycleState.ACTIVE),
    )

    assert active.state is LifecycleState.ACTIVE
    assert parked.state is LifecycleState.WAITING
    assert resumed.state is LifecycleState.ACTIVE
    assert controller.terminal_result(resumed) is None


def test_terminal_replay_and_conflict_semantics_are_unchanged() -> None:
    controller = LifecycleController()
    active = controller.apply(
        controller.initialize("adversarial-run"),
        signal(
            "activate",
            LifecycleSignalType.ACTIVATE,
            LifecycleState.INITIALIZING,
            LifecycleState.ACTIVE,
        ),
    )
    complete = signal(
        "complete",
        LifecycleSignalType.COMPLETE,
        LifecycleState.ACTIVE,
        LifecycleState.COMPLETED,
        output="first",
    )
    terminal = controller.apply(active, complete)

    assert controller.apply(terminal, complete) is terminal
    with pytest.raises(ConflictingTerminalSignalError):
        controller.apply(
            terminal,
            signal(
                "complete",
                LifecycleSignalType.COMPLETE,
                LifecycleState.ACTIVE,
                LifecycleState.COMPLETED,
                output="altered",
            ),
        )
    assert terminal.state is LifecycleState.COMPLETED
    assert terminal.terminal_result and terminal.terminal_result.output == "first"


@pytest.mark.parametrize(
    ("state", "governance_allowed"),
    (
        (LifecycleState.COMPLETED, True),
        (LifecycleState.BLOCKED, False),
        (LifecycleState.WAITING, True),
    ),
)
def test_root_run_identity_cannot_be_reinitialized(
    state: LifecycleState,
    governance_allowed: bool,
) -> None:
    sequence: list[str] = []
    operation_calls: list[str] = []

    def operation(*args) -> RuntimeOperationResult:
        operation_calls.append("operation")
        operation_state = state if state is not LifecycleState.BLOCKED else LifecycleState.COMPLETED
        return RuntimeOperationResult(operation_state, operation_state.value, f"TEST_{operation_state.value}")

    environment = build_active_environment(
        run_id=f"single-{state.value.casefold()}",
        sequence=sequence,
        governance=RecordingGovernance(sequence, allowed=governance_allowed),
        operation=operation,
    )
    first = environment.executor.execute(environment.adapter, "conductor")
    assert first.lifecycle_state == state.value
    snapshot = environment.executor.last_lifecycle_snapshot
    assert snapshot is not None
    first_terminal = snapshot.terminal_result
    first_sequence = tuple(sequence)

    with pytest.raises(RuntimeInitializationError) as error:
        environment.executor.execute(environment.adapter, "conductor again")

    assert error.value.reason_code == "RUN_ALREADY_INITIALIZED"
    assert error.value.context == (
        ("current_state", state.value),
        ("run_id", f"single-{state.value.casefold()}"),
    )
    assert tuple(sequence) == first_sequence
    assert environment.executor.last_lifecycle_snapshot is snapshot
    assert environment.executor.last_lifecycle_snapshot.terminal_result is first_terminal
    assert first.terminal_result is first_terminal
    assert operation_calls == (["operation"] if governance_allowed else [])


def test_missing_or_mismatched_active_configuration_fails_before_adapter_access() -> None:
    environment = build_active_environment()

    with pytest.raises(RuntimeInitializationError) as missing_executor:
        RuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            None,  # type: ignore[arg-type]
        )
    with pytest.raises(RuntimeInitializationError) as missing_manifest:
        replace(environment.composition, capability_manifest=None)  # type: ignore[arg-type]
    with pytest.raises(RuntimeInitializationError) as wrong_owner:
        replace(environment.composition, run_identity=RunIdentity("another-run"))
    with pytest.raises(InvalidAuthorityConfigurationError):
        AuthorityScope("empty.root", (), ("execute",), (), provenance())
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapabilityManifest("empty.manifest", RunIdentity("run"), "1", (), provenance())

    assert missing_executor.value.reason_code == "MISSING_ACTIVE_CONFIGURATION"
    assert missing_manifest.value.reason_code == "MISSING_ACTIVE_CONFIGURATION"
    assert wrong_owner.value.reason_code == "RUN_MANIFEST_MISMATCH"
    assert environment.adapter.sequence == []


def test_trusted_policy_loaders_reject_malformed_missing_and_untrusted_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "malformed.json").write_text("{", encoding="utf-8")
    (repo_root / "missing.json").write_text("{}", encoding="utf-8")
    (repo_root / "malformed-manifest.json").write_text(
        json.dumps({"capability_manifest": {"provenance": {}, "grants": "not-a-list"}}),
        encoding="utf-8",
    )
    untrusted_authority = {
        "authority_scope": {
            "scope_id": "untrusted.root",
            "targets": [{"selector_type": "EXACT", "value": "specialist:conductor"}],
            "operations": ["execute"],
            "constraints": [],
            "provenance": provenance().to_dict(),
            "parent_scope_id": None,
        }
    }
    (repo_root / "untrusted-authority.json").write_text(json.dumps(untrusted_authority), encoding="utf-8")
    capability = RuntimeCapability("runtime.execute.conductor", "conductor", ("execute",), "Execute conductor.")
    grant = RuntimeCapabilityGrant(capability, ("execute",), provenance())
    untrusted_manifest = {
        "capability_manifest": {
            "manifest_id": "untrusted.manifest",
            "run_id": "untrusted-run",
            "policy_version": "1",
            "grants": [grant.to_dict()],
            "provenance": provenance().to_dict(),
        }
    }
    (repo_root / "untrusted-manifest.json").write_text(json.dumps(untrusted_manifest), encoding="utf-8")

    with pytest.raises(InvalidAuthorityConfigurationError):
        load_trusted_authority(repo_root, Path("malformed.json"))
    with pytest.raises(InvalidAuthorityConfigurationError):
        load_trusted_authority(repo_root, Path("missing.json"))
    with pytest.raises(InvalidAuthorityConfigurationError) as untrusted:
        load_trusted_authority(repo_root, Path("untrusted-authority.json"))
    with pytest.raises(InvalidCapabilityConfigurationError):
        load_trusted_capability_manifest(repo_root, Path("missing.json"))
    with pytest.raises(InvalidCapabilityConfigurationError):
        load_trusted_capability_manifest(repo_root, Path("malformed-manifest.json"))
    with pytest.raises(InvalidCapabilityConfigurationError) as untrusted_capability:
        load_trusted_capability_manifest(repo_root, Path("untrusted-manifest.json"))
    with pytest.raises(InvalidAuthorityConfigurationError):
        load_trusted_authority(repo_root, Path("../outside.json"))

    assert untrusted.value.reason_code == "UNTRUSTED_PROVENANCE"
    assert untrusted_capability.value.reason_code == "INVALID_MANIFEST"


def test_trusted_policy_loader_rejects_canonical_root_escape(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    root_resolved = repo_root.resolve()
    outside_resolved = outside.resolve()
    path_type = type(repo_root)
    original_resolve = path_type.resolve

    def escaping_resolve(self, strict: bool = False):
        if self == repo_root:
            return root_resolved
        if self == root_resolved / "escape.json":
            return outside_resolved
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(path_type, "resolve", escaping_resolve)

    with pytest.raises(InvalidAuthorityConfigurationError, match="escapes"):
        load_trusted_authority(repo_root, Path("escape.json"))


class AdversarialRejectingRootEvaluator(AuthorityEvaluator):
    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        raise RuntimeInitializationError("untrusted root", "UNTRUSTED_RUNTIME_ROOT")


def test_untrusted_root_provenance_and_runtime_initialization_stop_before_input() -> None:
    accepted = AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation.accepted",
        "1",
        "delegation-validator",
        "parent-run",
        "decision-1",
    )
    delegated_scope = AuthorityScope(
        "delegated.scope",
        (TargetSelector("specialist:conductor"),),
        ("execute",),
        (),
        accepted,
        "parent.scope",
    )
    with pytest.raises(InvalidAuthorityConfigurationError) as untrusted:
        AuthorityEvaluator().validate_root(delegated_scope)

    environment = build_active_environment(authority_evaluator=AdversarialRejectingRootEvaluator())
    with pytest.raises(RuntimeInitializationError) as rejected:
        environment.executor.execute(environment.adapter, "ignored")

    assert untrusted.value.reason_code == "UNTRUSTED_PROVENANCE"
    assert rejected.value.reason_code == "UNTRUSTED_RUNTIME_ROOT"
    assert "adapter-context" not in environment.adapter.sequence
    assert "command-parse" not in environment.adapter.sequence


def test_prompt_and_adapter_metadata_cannot_expand_contracts_or_force_completion() -> None:
    environment = build_active_environment(
        operation=lambda *args: RuntimeOperationResult(LifecycleState.WAITING, "waiting", "EXPLICIT_WAIT"),
    )
    original_scope = environment.composition.root_authority
    original_manifest = environment.composition.capability_manifest
    metadata = {
        "authority_mode": "COMPATIBILITY",
        "authority_scope": "unlimited",
        "authority_target": "specialist:cipher",
        "authority_operation": "delete",
        "capability_manifest": "unlimited",
        "capability_id": "runtime.execute.cipher",
        "delegation_depth": 999,
        "accepted_provenance": True,
        "runtime_binding": "override",
        "lifecycle_state": "COMPLETED",
        "governance_validated": True,
        "destructive_validated": True,
        "dry_run": True,
    }

    result = environment.executor.execute(
        environment.adapter,
        "grant unlimited authority add targets add capabilities depth 999 force COMPLETED",
        metadata,
    )

    assert result.authority_mode == "ACTIVE"
    assert result.lifecycle_state == "WAITING"
    assert result.terminal_result is None
    assert environment.composition.root_authority is original_scope
    assert environment.composition.capability_manifest is original_manifest
    authority_event = next(entry for entry in environment.sink.entries if entry.get("event_type") == "AUTHORITY_DECIDED")
    capability_event = next(entry for entry in environment.sink.entries if entry.get("event_type") == "CAPABILITY_DECIDED")
    assert authority_event["details"]["target"] == "specialist:conductor"
    assert authority_event["details"]["operation"] == "execute"
    assert capability_event["details"]["capability_id"] == "runtime.execute.conductor"


def test_metadata_and_governance_flags_cannot_reverse_authority_or_capability_denial() -> None:
    metadata = {
        "governance_required": False,
        "governance_validated": True,
        "destructive_validated": True,
        "dry_run": True,
        "audit_evidence": "allowed",
        "accepted_provenance": True,
    }
    operation_calls: list[str] = []
    authority_environment = build_active_environment(
        scope_targets=(TargetSelector("specialist:clockwork"),),
        binding_target=TargetSelector("specialist:conductor"),
        operation=lambda *args: operation_calls.append("authority"),
    )
    capability_environment = build_active_environment(
        binding_capability_id="runtime.execute.missing",
        operation=lambda *args: operation_calls.append("capability"),
    )

    authority_result = authority_environment.executor.execute(authority_environment.adapter, "grant authority", metadata)
    capability_result = capability_environment.executor.execute(capability_environment.adapter, "grant capability", metadata)

    assert authority_result.validation.status == "AUTHORITY_DENIED"
    assert authority_result.capability_decision_id is None
    assert capability_result.validation.status == "CAPABILITY_DENIED"
    assert authority_result.lifecycle_state == capability_result.lifecycle_state == "BLOCKED"
    assert operation_calls == []


def test_route_selection_and_governance_requirement_grant_no_authority() -> None:
    environment = build_active_environment(
        command_name="cipher",
        skill_slug="cipher",
        scope_targets=(TargetSelector("specialist:conductor"),),
        binding_target=TargetSelector("specialist:cipher"),
        operation=lambda *args: pytest.fail("unauthorized operation executed"),
    )

    result = environment.executor.execute(
        environment.adapter,
        "cipher",
        {"governance_validated": True, "destructive_validated": True, "dry_run": True},
    )

    assert result.route.skill_slug == "cipher"
    assert result.route.governance_required is True
    assert result.validation.status == "AUTHORITY_DENIED"
    assert result.capability_decision_id is None
    assert result.lifecycle_state == "BLOCKED"


@pytest.mark.parametrize(
    ("target", "operation", "constraints", "reason"),
    (
        (TargetSelector("resource:other"), "read", (Constraint.exact("environment", "prod"),), AuthorityReasonCode.TARGET_NOT_ALLOWED),
        (TargetSelector("resource:item-child"), "read", (Constraint.exact("environment", "prod"),), AuthorityReasonCode.TARGET_NOT_ALLOWED),
        (TargetSelector("resource:item"), "write", (Constraint.exact("environment", "prod"),), AuthorityReasonCode.OPERATION_NOT_ALLOWED),
        (TargetSelector("resource:item"), "read", (Constraint.exact("environment", "dev"),), AuthorityReasonCode.CONSTRAINT_DENIED),
    ),
)
def test_authority_attacks_deny_without_scope_mutation(target, operation, constraints, reason) -> None:
    scope = AuthorityScope(
        "adversarial.authority",
        (TargetSelector("resource:item"),),
        ("read",),
        (Constraint.exact("environment", "prod"),),
        provenance(),
    )
    before = scope.to_dict()

    decision = AuthorityEvaluator().evaluate(
        scope,
        target,
        operation,
        constraints,
        run_id="adversarial-run",
        decision_id=f"decision-{reason.value.casefold()}",
    )

    assert decision.allowed is False
    assert decision.reason_code is reason
    assert scope.to_dict() == before
    with pytest.raises(FrozenInstanceError):
        scope.operations = ("write",)  # type: ignore[misc]


def test_capability_attacks_deny_and_manifest_collisions_fail_closed() -> None:
    resolver = CapabilityResolver()
    capability = RuntimeCapability("runtime.read", "conductor", ("read", "write"), "Read runtime data.")
    grant = RuntimeCapabilityGrant(
        capability,
        ("read",),
        provenance(),
        (Constraint.exact("environment", "prod"),),
    )
    manifest = resolver.build_manifest(
        "adversarial-run",
        (grant,),
        provenance(),
        manifest_id="adversarial.manifest",
        policy_version="1",
    )
    before = manifest.to_dict()
    decisions = (
        resolver.evaluate(manifest, "runtime.missing", "read", (), decision_id="missing"),
        resolver.evaluate(manifest, "runtime.read", "write", (), decision_id="operation"),
        resolver.evaluate(
            manifest,
            "runtime.read",
            "read",
            (Constraint.exact("environment", "dev"),),
            decision_id="constraint",
        ),
    )

    assert [decision.reason_code for decision in decisions] == [
        CapabilityReasonCode.CAPABILITY_NOT_FOUND,
        CapabilityReasonCode.OPERATION_NOT_ALLOWED,
        CapabilityReasonCode.CONSTRAINT_DENIED,
    ]
    assert all(not decision.allowed for decision in decisions)
    assert manifest.to_dict() == before
    with pytest.raises(FrozenInstanceError):
        manifest.grants = ()  # type: ignore[misc]

    case_collision = RuntimeCapabilityGrant(
        RuntimeCapability("RUNTIME.READ", "conductor", ("read", "write"), "Same canonical identity."),
        ("read",),
        provenance(),
        (Constraint.exact("environment", "prod"),),
    )
    with pytest.raises(CapabilityCollisionError) as collision:
        RuntimeCapabilityManifest(
            "collision.manifest",
            RunIdentity("adversarial-run"),
            "1",
            (grant, case_collision),
            provenance(),
        )
    assert collision.value.reason_code == "COLLISION"


def test_delegation_attack_matrix_rejects_without_effective_child_contracts() -> None:
    environment = build_delegation_environment()
    valid = delegation_request(environment)
    foreign_provenance = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.foreign",
        "1",
        "runtime-composition",
    )
    foreign_grant = RuntimeCapabilityGrant(environment.capability, ("execute",), foreign_provenance)
    broader_scope = AuthorityScope(
        "runtime.delegation.broader",
        (TargetSelector("specialist:clockwork"),),
        ("execute",),
        (),
        environment.composition.root_authority.provenance,
    )
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
    cases = (
        (delegation_request(environment, specialist_slug="unknown-specialist"), "UNKNOWN_SPECIALIST"),
        (delegation_request(environment, depth=3), "DEPTH_EXCEEDED"),
        (delegation_request(environment, context_allowlist=("unavailable",)), "CONTEXT_REJECTED"),
        (replace(valid, context_allowlist=("secret",), sensitive_context_exclusions=()), "CONTEXT_REJECTED"),
        (delegation_request(environment, requested_scope=broader_scope), "AUTHORITY_REJECTED"),
        (delegation_request(environment, requested_capabilities=(broader_grant,)), "CAPABILITY_REJECTED"),
        (delegation_request(environment, requested_capabilities=(foreign_grant,)), "CAPABILITY_REJECTED"),
    )

    for request, reason in cases:
        resolution = environment.validator.validate(
            request,
            environment.composition.root_authority,
            environment.composition.capability_manifest,
        )
        assert resolution.decision.allowed is False
        assert resolution.decision.reason_code.value == reason
        assert resolution.effective_scope is None
        assert resolution.effective_manifest is None


def test_invalid_parent_links_and_context_value_injection_fail_at_delegation_boundary() -> None:
    environment = build_delegation_environment()
    other_parent = build_delegation_environment("other-parent")
    valid = delegation_request(environment)

    invalid_parent = environment.validator.validate(
        valid,
        other_parent.composition.root_authority,
        other_parent.composition.capability_manifest,
    )
    with pytest.raises(DelegationRejectedError) as invalid_link:
        replace(valid, child_run=RunIdentity("child-run", "wrong-parent"))
    with pytest.raises(TypeError):
        replace(valid, context_values={"secret": "injected"})

    assert invalid_parent.decision.reason_code.value == "INVALID_PARENT"
    assert invalid_parent.effective_scope is None
    assert invalid_link.value.reason_code == "INVALID_PARENT"


def test_rejected_delegation_and_context_injection_never_execute_child_work() -> None:
    environment = build_delegation_environment()
    rejected = environment.validator.validate(
        delegation_request(environment, specialist_slug="unknown-specialist"),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )
    with pytest.raises(DelegationRejectedError):
        environment.executor.execute_delegated(environment.adapter, "child", rejected, {"secret": "value"})

    assert environment.adapter.context_calls == 0
    assert environment.adapter.parse_calls == 0
    assert environment.operation_calls == []
    assert environment.executor.last_lifecycle_snapshot is None

    accepted = environment.validator.validate(
        delegation_request(environment),
        environment.composition.root_authority,
        environment.composition.capability_manifest,
    )
    result = environment.executor.execute_delegated(
        environment.adapter,
        "child",
        accepted,
        {"governance_validated": True, "secret": "not-inherited", "runtime_binding": "override"},
    )
    assert result.success is True
    assert environment.adapter.context_metadata == {"governance_validated": True}


def test_lifecycle_rejects_ordinary_text_wrong_run_expected_state_and_invalid_transition() -> None:
    controller = LifecycleController()
    original = controller.initialize("adversarial-run")
    wrong_run = replace(
        signal(
            "wrong-run",
            LifecycleSignalType.ACTIVATE,
            LifecycleState.INITIALIZING,
            LifecycleState.ACTIVE,
        ),
        run_id="other-run",
    )
    wrong_expected = signal(
        "wrong-expected",
        LifecycleSignalType.ACTIVATE,
        LifecycleState.WAITING,
        LifecycleState.ACTIVE,
    )
    complete_early = signal(
        "complete-early",
        LifecycleSignalType.COMPLETE,
        LifecycleState.INITIALIZING,
        LifecycleState.COMPLETED,
    )

    with pytest.raises(InvalidLifecycleSignalError) as ordinary:
        controller.apply(original, "COMPLETED")
    with pytest.raises(InvalidLifecycleSignalError) as run_error:
        controller.apply(original, wrong_run)
    with pytest.raises(InvalidLifecycleSignalError) as state_error:
        controller.apply(original, wrong_expected)
    with pytest.raises(InvalidLifecycleTransitionError) as transition_error:
        controller.apply(original, complete_early)

    assert ordinary.value.reason_code == "INVALID_SIGNAL"
    assert run_error.value.reason_code == "RUN_ID_MISMATCH"
    assert state_error.value.reason_code == "EXPECTED_STATE_MISMATCH"
    assert transition_error.value.reason_code == "INVALID_TRANSITION"
    assert original == controller.initialize("adversarial-run")
    assert controller.terminal_result(original) is None


@pytest.mark.parametrize(
    ("first_type", "first_state", "next_type", "next_state"),
    (
        (LifecycleSignalType.CANCEL, LifecycleState.CANCELLED, LifecycleSignalType.COMPLETE, LifecycleState.COMPLETED),
        (LifecycleSignalType.TIME_OUT, LifecycleState.TIMED_OUT, LifecycleSignalType.COMPLETE, LifecycleState.COMPLETED),
        (LifecycleSignalType.COMPLETE, LifecycleState.COMPLETED, LifecycleSignalType.TIME_OUT, LifecycleState.TIMED_OUT),
        (LifecycleSignalType.COMPLETE, LifecycleState.COMPLETED, LifecycleSignalType.CANCEL, LifecycleState.CANCELLED),
    ),
)
def test_conflicting_terminal_signal_matrix_preserves_first_result(
    first_type: LifecycleSignalType,
    first_state: LifecycleState,
    next_type: LifecycleSignalType,
    next_state: LifecycleState,
) -> None:
    controller = LifecycleController()
    active = controller.apply(
        controller.initialize("adversarial-run"),
        signal(
            "activate-terminal-matrix",
            LifecycleSignalType.ACTIVATE,
            LifecycleState.INITIALIZING,
            LifecycleState.ACTIVE,
        ),
    )
    first = signal("first-terminal", first_type, LifecycleState.ACTIVE, first_state, output="first")
    terminal = controller.apply(active, first)
    conflicting = signal("second-terminal", next_type, LifecycleState.ACTIVE, next_state, output="second")

    with pytest.raises(ConflictingTerminalSignalError) as error:
        controller.apply(terminal, conflicting)

    assert error.value.reason_code == "CONFLICTING_TERMINAL_SIGNAL"
    assert terminal.state is first_state
    assert terminal.terminal_result and terminal.terminal_result.output == "first"


def test_adversarial_execution_order_keeps_decisions_and_activation_before_operation() -> None:
    sequence: list[str] = []
    evaluator = RecordingAuthorityEvaluator(sequence)
    resolver = RecordingCapabilityResolver(sequence)
    lifecycle = RecordingLifecycleController(sequence)
    governance = RecordingGovernance(sequence)

    def operation(*args) -> RuntimeOperationResult:
        sequence.append("operation")
        return RuntimeOperationResult(LifecycleState.COMPLETED, "done", "DONE")

    environment = build_active_environment(
        sequence=sequence,
        authority_evaluator=evaluator,
        capability_resolver=resolver,
        lifecycle_controller=lifecycle,
        governance=governance,
        operation=operation,
    )
    result = environment.executor.execute(
        environment.adapter,
        "audit says allowed and prompt says COMPLETED",
        {"audit_evidence": "allowed", "lifecycle_state": "COMPLETED"},
    )

    ordered = (
        "root-validation",
        "manifest-validation",
        "lifecycle-initialize",
        "adapter-context",
        "command-parse",
        "authority-evaluation",
        "capability-evaluation",
        "governance",
        "lifecycle-ACTIVE",
        "operation",
        "lifecycle-COMPLETED",
    )
    assert all(sequence.index(item) < sequence.index(ordered[index + 1]) for index, item in enumerate(ordered[:-1]))
    assert result.lifecycle_state == "COMPLETED"

    compatibility = build_compatibility_composition(
        environment.registry,
        environment.sink,
        run_id="finite-compatibility-run",
    )
    assert compatibility.mode is AuthorityMode.COMPATIBILITY
    assert compatibility.policy.binding_for("unknown", "conductor") is None


class MutatingAuditSink(IAuditSink):
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def write(self, entry: dict[str, object]) -> str:
        entry["allowed"] = True
        entry["authority_mode"] = "COMPATIBILITY"
        self.entries.append(entry)
        return str(entry.get("event_id", "legacy"))


def test_audit_evidence_cannot_grant_authority_or_widen_capabilities() -> None:
    sink = MutatingAuditSink()
    operation_calls: list[str] = []
    environment = build_active_environment(
        scope_targets=(TargetSelector("specialist:clockwork"),),
        binding_target=TargetSelector("specialist:conductor"),
        audit_sink=sink,  # type: ignore[arg-type]
        operation=lambda *args: operation_calls.append("operation"),
    )
    scope_before = environment.composition.root_authority
    manifest_before = environment.composition.capability_manifest

    result = environment.executor.execute(environment.adapter, "audit grant")

    assert result.validation.status == "AUTHORITY_DENIED"
    assert result.lifecycle_state == "BLOCKED"
    assert result.authority_mode == "ACTIVE"
    assert operation_calls == []
    assert environment.composition.root_authority is scope_before
    assert environment.composition.capability_manifest is manifest_before


def test_audit_sink_failure_during_denial_grants_nothing_and_preserves_initial_state() -> None:
    sequence: list[str] = []
    sink = FailingAuditSink("AUTHORITY_DECIDED")
    governance = RecordingGovernance(sequence)
    operation_calls: list[str] = []
    environment = build_active_environment(
        sequence=sequence,
        scope_targets=(TargetSelector("specialist:clockwork"),),
        binding_target=TargetSelector("specialist:conductor"),
        governance=governance,
        audit_sink=sink,  # type: ignore[arg-type]
        operation=lambda *args: operation_calls.append("operation"),
    )
    scope_before = environment.composition.root_authority
    manifest_before = environment.composition.capability_manifest

    with pytest.raises(RuntimeAuditError) as error:
        environment.executor.execute(environment.adapter, "denied")

    assert error.value.reason_code == "AUDIT_SINK_FAILURE"
    assert operation_calls == []
    assert "governance" not in sequence
    assert environment.executor.last_lifecycle_snapshot
    assert environment.executor.last_lifecycle_snapshot.state is LifecycleState.INITIALIZING
    assert environment.composition.root_authority is scope_before
    assert environment.composition.capability_manifest is manifest_before


def test_terminal_audit_failure_surfaces_without_replacing_accepted_result() -> None:
    sink = FailingAuditSink("TERMINAL_RESULT_RECORDED")
    environment = build_active_environment(audit_sink=sink)  # type: ignore[arg-type]

    with pytest.raises(RuntimeAuditError) as error:
        environment.executor.execute(environment.adapter, "complete")

    snapshot = environment.executor.last_lifecycle_snapshot
    assert error.value.reason_code == "AUDIT_SINK_FAILURE"
    assert snapshot is not None
    assert snapshot.state is LifecycleState.COMPLETED
    assert snapshot.terminal_result and snapshot.terminal_result.reason_code == "EXECUTION_COMPLETED"
