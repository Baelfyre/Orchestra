import pytest

from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
)
from orchestra_runtime.host_protocol import HostCapability, HostCapabilityDeclaration
from orchestra_runtime.preexecution import (
    ExecutionAction,
    ExecutionIntent,
    PreExecutionConstraint,
    PreExecutionPolicy,
    PreExecutionReason,
    evaluate_preexecution,
    evaluate_preexecution_with_arbiter,
)


def _host(*capabilities):
    return HostCapabilityDeclaration(
        host_id="fixture-host",
        adapter_id="fixture-adapter",
        capabilities=tuple(capabilities),
        evidence_refs=("receipt:host",),
        observed_at="2026-08-15T08:55:00Z",
    )


def _policy(**overrides):
    values = {
        "policy_id": "p8-test",
        "allowed_actions": (ExecutionAction.FILE_READ, ExecutionAction.FILE_WRITE),
        "allowed_paths": ("src", "docs"),
        "prohibited_paths": ("src/secrets",),
    }
    values.update(overrides)
    return PreExecutionPolicy(**values)


def _kernel(**overrides):
    values = {
        "project_id": "orchestra",
        "unit_id": "p8",
        "governance_decisions": (
            GovernanceDecisionRecord(
                reviewer="arbiter",
                project_context="p8",
                decision="APPROVED",
                reason="fixture",
            ),
        ),
    }
    values.update(overrides)
    return ArbiterKernelInput(**values)


def test_allowed_read_inside_scope_with_host_capability_is_ready():
    intent = ExecutionIntent("read-1", ExecutionAction.FILE_READ, ("src/runtime.py",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_READ))
    assert gate.constraint is PreExecutionConstraint.ALLOW
    assert gate.reason is PreExecutionReason.READY


def test_allowed_write_inside_scope_with_host_capability_is_ready():
    intent = ExecutionIntent("write-1", ExecutionAction.FILE_WRITE, ("docs/guide.md",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_WRITE))
    assert gate.constraint is PreExecutionConstraint.ALLOW


def test_absolute_and_traversal_paths_are_rejected_before_gate():
    for path in ("/etc/passwd", "\\server\\share", "file://tmp/data", "C:/Windows/system.ini"):
        with pytest.raises(ValueError, match="repository-relative"):
            ExecutionIntent("bad", ExecutionAction.FILE_READ, (path,))
    with pytest.raises(ValueError, match="unsafe path traversal"):
        ExecutionIntent("bad2", ExecutionAction.FILE_READ, ("src/../secret",))


def test_repository_relative_path_boundary_accepts_one_character_and_non_drive_colon_position():
    single = ExecutionIntent("one-char", ExecutionAction.FILE_READ, ("x",))
    ordinary = ExecutionIntent("ordinary", ExecutionAction.FILE_READ, ("ab/c",))
    assert single.requested_paths == ("x",)
    assert ordinary.requested_paths == ("ab/c",)
    with pytest.raises(ValueError, match="repository-relative"):
        ExecutionIntent("drive-like", ExecutionAction.FILE_READ, ("a:b",))


def test_path_outside_allowed_scope_stops():
    intent = ExecutionIntent("outside", ExecutionAction.FILE_WRITE, ("infra/prod.yml",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_WRITE))
    assert gate.constraint is PreExecutionConstraint.STOP
    assert gate.reason is PreExecutionReason.PATH_OUTSIDE_SCOPE


def test_prohibited_path_stops_even_with_host_capability():
    intent = ExecutionIntent("secret", ExecutionAction.FILE_READ, ("src/secrets/key.txt",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_READ))
    assert gate.constraint is PreExecutionConstraint.STOP
    assert gate.reason is PreExecutionReason.PROHIBITED_PATH


def test_unlisted_action_is_default_deny():
    intent = ExecutionIntent("shell", ExecutionAction.SHELL_EXECUTE, operation_ref="pytest")
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.SHELL_EXECUTE))
    assert gate.constraint is PreExecutionConstraint.STOP
    assert gate.reason is PreExecutionReason.ACTION_NOT_ALLOWED


def test_production_mutation_without_explicit_authority_escalates():
    policy = _policy(allowed_actions=(ExecutionAction.PRODUCTION_MUTATION,))
    intent = ExecutionIntent("prod", ExecutionAction.PRODUCTION_MUTATION, operation_ref="deploy")
    gate = evaluate_preexecution(intent, policy, _host(HostCapability.REMOTE_WRITE))
    assert gate.constraint is PreExecutionConstraint.ESCALATE_HUMAN
    assert gate.reason is PreExecutionReason.PRODUCTION_AUTHORITY_REQUIRED


def test_destructive_simulation_without_explicit_authority_escalates():
    policy = _policy(allowed_actions=(ExecutionAction.DESTRUCTIVE_SIMULATION,))
    intent = ExecutionIntent("dagger", ExecutionAction.DESTRUCTIVE_SIMULATION, operation_ref="resilience-check")
    gate = evaluate_preexecution(intent, policy, _host(HostCapability.SANDBOX_EXECUTE))
    assert gate.constraint is PreExecutionConstraint.ESCALATE_HUMAN
    assert gate.reason is PreExecutionReason.DESTRUCTIVE_AUTHORITY_REQUIRED


def test_missing_host_capability_waits_when_alternate_host_is_allowed():
    intent = ExecutionIntent("read", ExecutionAction.FILE_READ, ("src/a.py",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.GIT_READ))
    assert gate.constraint is PreExecutionConstraint.WAIT_FOR_CAPACITY
    assert gate.reason is PreExecutionReason.HOST_CAPABILITY_MISSING


def test_explicit_authority_cannot_override_prohibited_path():
    policy = _policy(
        allowed_actions=(ExecutionAction.FILE_WRITE,),
        production_mutation_authorized=True,
        destructive_simulation_authorized=True,
        remote_write_authorized=True,
    )
    intent = ExecutionIntent("secret-write", ExecutionAction.FILE_WRITE, ("src/secrets/key.txt",))
    gate = evaluate_preexecution(intent, policy, _host(HostCapability.FILESYSTEM_WRITE))
    assert gate.constraint is PreExecutionConstraint.STOP


def test_safe_gate_does_not_override_stale_arbiter_evidence():
    intent = ExecutionIntent("read", ExecutionAction.FILE_READ, ("src/a.py",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_READ))
    evaluation = evaluate_preexecution_with_arbiter(_kernel(evidence_fresh=False), gate)
    assert gate.constraint is PreExecutionConstraint.ALLOW
    assert evaluation.arbiter_result.disposition is TransitionDisposition.WAIT_FOR_EVIDENCE


def test_gate_stop_maps_to_higher_priority_arbiter_stop():
    intent = ExecutionIntent("outside", ExecutionAction.FILE_WRITE, ("infra/prod.yml",))
    gate = evaluate_preexecution(intent, _policy(), _host(HostCapability.FILESYSTEM_WRITE))
    evaluation = evaluate_preexecution_with_arbiter(_kernel(), gate)
    assert evaluation.arbiter_result.disposition is TransitionDisposition.STOP


def test_missing_protected_authority_maps_to_arbiter_escalation():
    policy = _policy(allowed_actions=(ExecutionAction.REMOTE_WRITE,), remote_write_authorized=False)
    intent = ExecutionIntent("remote", ExecutionAction.REMOTE_WRITE, operation_ref="push")
    gate = evaluate_preexecution(intent, policy, _host(HostCapability.REMOTE_WRITE))
    evaluation = evaluate_preexecution_with_arbiter(_kernel(), gate)
    assert evaluation.arbiter_result.disposition is TransitionDisposition.ESCALATE_HUMAN


def test_host_capability_pass_cannot_override_policy_prohibition():
    policy = _policy(allowed_actions=(ExecutionAction.SHELL_EXECUTE,))
    intent = ExecutionIntent("shell", ExecutionAction.SHELL_EXECUTE, operation_ref="safe-command")
    allowed = evaluate_preexecution(intent, policy, _host(HostCapability.SHELL_EXECUTE))
    assert allowed.constraint is PreExecutionConstraint.ALLOW

    denied = evaluate_preexecution(
        ExecutionIntent("file", ExecutionAction.FILE_READ, ("src/a.py",)),
        policy,
        _host(HostCapability.FILESYSTEM_READ, HostCapability.SHELL_EXECUTE),
    )
    assert denied.constraint is PreExecutionConstraint.STOP
    assert denied.reason is PreExecutionReason.ACTION_NOT_ALLOWED
