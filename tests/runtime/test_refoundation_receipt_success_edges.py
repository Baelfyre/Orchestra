import pytest

from orchestra_runtime.evidence import (
    SourceStateReceipt,
    ValidationExecutionReceipt,
)
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
    evaluate_arbiter,
)
from orchestra_runtime.host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    evaluate_host_capabilities,
    evaluate_host_with_arbiter,
)
from orchestra_runtime.preexecution import (
    ExecutionAction,
    ExecutionIntent,
    PreExecutionConstraint,
    PreExecutionPolicy,
    evaluate_preexecution,
    evaluate_preexecution_with_arbiter,
)


A40 = "a" * 40
B40 = "b" * 40
A64 = "a" * 64
B64 = "b" * 64


def _decision():
    return GovernanceDecisionRecord("receipt-edge", "receipt-edge", "APPROVED", "fixture")


def _kernel(**overrides):
    values = dict(project_id="orchestra", unit_id="receipt-edge", governance_decisions=(_decision(),))
    values.update(overrides)
    return ArbiterKernelInput(**values)


def _host(*capabilities):
    return HostCapabilityDeclaration(
        host_id="receipt-host",
        adapter_id="adapter:receipt",
        capabilities=tuple(capabilities),
        evidence_refs=("receipt:host",),
        observed_at="2026-08-15T11:00:00Z",
    )


def _validation_receipt(**overrides):
    values = dict(
        command_id="optional-heads",
        command=("git", "status"),
        exit_code=0,
        started_at="2026-08-15T11:00:00Z",
        finished_at="2026-08-15T11:00:01Z",
        stdout_sha256=A64,
        stderr_sha256=B64,
    )
    values.update(overrides)
    return ValidationExecutionReceipt(**values)


def test_full_source_receipt_success_surface_and_assertions():
    receipt = SourceStateReceipt(
        repository="Baelfyre/Orchestra",
        canonical_branch="main",
        live_canonical_sha=A40,
        verification_timestamp="2026-08-15T11:00:00+00:00",
        verification_method="GITHUB_API",
        pull_request_number=293,
        exact_pr_head=B40,
        merge_or_squash_sha=A40,
        tree_sha=B40,
    )
    receipt.assert_canonical_sha(A40.upper())
    receipt.assert_pr_head(B40.upper())
    payload = receipt.to_dict()
    assert payload["pull_request_number"] == 293
    assert payload["exact_pr_head"] == B40
    assert payload["merge_or_squash_sha"] == A40
    assert payload["tree_sha"] == B40
    assert len(receipt.digest) == 64


def test_validation_receipt_full_success_and_changed_state_surfaces():
    receipt = ValidationExecutionReceipt(
        command_id="full",
        command=("git", "diff", "--check"),
        exit_code=0,
        started_at="2026-08-15T11:00:00Z",
        finished_at="2026-08-15T11:00:01Z",
        stdout_sha256=A64,
        stderr_sha256=B64,
        head_before=A40,
        head_after=B40,
        evidence_ref="receipt:validation",
    )
    assert receipt.exact_state_preserved is False
    receipt.assert_claimed_verdict("pass")
    payload = receipt.to_dict()
    assert payload["head_before"] == A40
    assert payload["head_after"] == B40
    assert payload["evidence_ref"] == "receipt:validation"
    assert payload["verdict"] == "PASS"
    assert len(receipt.digest) == 64


def test_validation_receipt_serializes_each_optional_head_independently():
    before_only = _validation_receipt(head_before=A40)
    before_payload = before_only.to_dict()
    assert before_payload["head_before"] == A40
    assert "head_after" not in before_payload
    assert before_only.exact_state_preserved is None

    after_only = _validation_receipt(head_after=B40)
    after_payload = after_only.to_dict()
    assert "head_before" not in after_payload
    assert after_payload["head_after"] == B40
    assert after_only.exact_state_preserved is None


def test_arbiter_remediation_candidate_from_validation_failure():
    result = evaluate_arbiter(
        _kernel(
            validation_passed=False,
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            remediation_attempt_count=1,
        )
    )
    assert result.disposition is TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE
    assert len(result.digest) == 64


def test_host_gate_non_alternate_path_and_evaluation_digest():
    declaration = _host(HostCapability.FILESYSTEM_READ)
    gate = evaluate_host_capabilities(
        declaration,
        (HostCapability.SHELL_EXECUTE,),
        alternate_host_allowed=False,
    )
    assert gate.ready is False
    assert gate.to_dict()["missing_capabilities"] == ["SHELL_EXECUTE"]
    evaluation = evaluate_host_with_arbiter(_kernel(), gate)
    assert evaluation.arbiter_result.disposition is TransitionDisposition.ESCALATE_HUMAN
    assert len(evaluation.digest) == 64


def test_preexecution_path_outside_scope_and_remote_authority_edges():
    host = _host(HostCapability.FILESYSTEM_READ, HostCapability.REMOTE_WRITE)
    read_policy = PreExecutionPolicy(
        "read-policy",
        (ExecutionAction.FILE_READ,),
        allowed_paths=("src",),
    )
    outside = evaluate_preexecution(
        ExecutionIntent("outside", ExecutionAction.FILE_READ, requested_paths=("docs/readme.md",)),
        read_policy,
        host,
    )
    assert outside.constraint is PreExecutionConstraint.STOP
    stopped = evaluate_preexecution_with_arbiter(_kernel(), outside)
    assert stopped.arbiter_result.disposition is TransitionDisposition.STOP
    assert len(stopped.digest) == 64

    remote_policy = PreExecutionPolicy(
        "remote-policy",
        (ExecutionAction.REMOTE_WRITE,),
        remote_write_authorized=False,
    )
    remote = evaluate_preexecution(ExecutionIntent("remote", ExecutionAction.REMOTE_WRITE), remote_policy, host)
    assert remote.constraint is PreExecutionConstraint.ESCALATE_HUMAN
    escalated = evaluate_preexecution_with_arbiter(_kernel(), remote)
    assert escalated.arbiter_result.disposition is TransitionDisposition.ESCALATE_HUMAN


def test_preexecution_action_not_allowed_stops_before_capability():
    host = _host(HostCapability.FILESYSTEM_READ)
    policy = PreExecutionPolicy("shell-only", (ExecutionAction.SHELL_EXECUTE,))
    intent = ExecutionIntent("read", ExecutionAction.FILE_READ, requested_paths=("src/x.py",))
    gate = evaluate_preexecution(intent, policy, host)
    assert gate.constraint is PreExecutionConstraint.STOP
    assert gate.host_gate is None