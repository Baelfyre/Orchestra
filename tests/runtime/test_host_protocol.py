import pytest

from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
)
from orchestra_runtime.host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    evaluate_host_capabilities,
    evaluate_host_with_arbiter,
)


def _declaration(host_id, capabilities):
    return HostCapabilityDeclaration(
        host_id=host_id,
        adapter_id=f"adapter:{host_id}",
        capabilities=tuple(capabilities),
        evidence_refs=(f"receipt:host:{host_id}",),
        observed_at="2026-08-15T08:00:00Z",
    )


def _kernel(**overrides):
    values = {
        "project_id": "orchestra",
        "unit_id": "host-conformance",
        "governance_decisions": (
            GovernanceDecisionRecord(
                reviewer="workflow-sanity",
                project_context="host-conformance",
                decision="APPROVED",
                reason="fixture",
            ),
        ),
    }
    values.update(overrides)
    return ArbiterKernelInput(**values)


def test_equivalent_host_capabilities_produce_same_kernel_verdict():
    required = (HostCapability.FILESYSTEM_READ, HostCapability.SHELL_EXECUTE, HostCapability.GIT_READ)
    verdicts = []
    for host_id in ("agy-fixture", "codex-fixture", "claude-fixture"):
        declaration = _declaration(host_id, reversed(required))
        gate = evaluate_host_capabilities(declaration, required, alternate_host_allowed=True)
        result = evaluate_host_with_arbiter(_kernel(), gate)
        assert gate.ready is True
        verdicts.append(result.arbiter_result.disposition)
    assert verdicts == [TransitionDisposition.AUTO_CONTINUE] * 3


def test_missing_shell_capability_waits_for_alternate_host_capacity():
    declaration = _declaration("limited-host", (HostCapability.FILESYSTEM_READ,))
    gate = evaluate_host_capabilities(
        declaration,
        (HostCapability.FILESYSTEM_READ, HostCapability.SHELL_EXECUTE),
        alternate_host_allowed=True,
    )
    result = evaluate_host_with_arbiter(_kernel(), gate)
    assert gate.ready is False
    assert gate.missing_capabilities == (HostCapability.SHELL_EXECUTE,)
    assert result.arbiter_result.disposition is TransitionDisposition.WAIT_FOR_CAPACITY


def test_missing_non_resumable_capability_escalates_human():
    declaration = _declaration("limited-host", (HostCapability.FILESYSTEM_READ,))
    gate = evaluate_host_capabilities(
        declaration,
        (HostCapability.REMOTE_WRITE,),
        alternate_host_allowed=False,
    )
    result = evaluate_host_with_arbiter(_kernel(), gate)
    assert result.arbiter_result.disposition is TransitionDisposition.ESCALATE_HUMAN


def test_unknown_capability_is_rejected():
    with pytest.raises(ValueError, match="unsupported host capability"):
        _declaration("bad-host", ("ROOT_EVERYTHING",))


def test_duplicate_capability_is_rejected():
    with pytest.raises(ValueError, match="duplicate capabilities"):
        _declaration("bad-host", (HostCapability.GIT_READ, HostCapability.GIT_READ))


def test_empty_evidence_is_rejected():
    with pytest.raises(ValueError, match="evidence_refs"):
        HostCapabilityDeclaration(
            host_id="unattested-host",
            adapter_id="adapter:unattested",
            capabilities=(HostCapability.GIT_READ,),
            evidence_refs=(),
            observed_at="2026-08-15T08:00:00Z",
        )


def test_capability_pass_does_not_override_stale_evidence():
    declaration = _declaration("capable-host", (HostCapability.GIT_READ,))
    gate = evaluate_host_capabilities(declaration, (HostCapability.GIT_READ,), alternate_host_allowed=True)
    result = evaluate_host_with_arbiter(_kernel(evidence_fresh=False), gate)
    assert gate.ready is True
    assert result.arbiter_result.disposition is TransitionDisposition.WAIT_FOR_EVIDENCE


def test_capability_pass_does_not_override_governance_block():
    declaration = _declaration("capable-host", (HostCapability.GIT_READ,))
    gate = evaluate_host_capabilities(declaration, (HostCapability.GIT_READ,), alternate_host_allowed=True)
    blocked = _kernel(
        governance_decisions=(
            GovernanceDecisionRecord(
                reviewer="the-governor",
                project_context="host-conformance",
                decision="BLOCKED",
                reason="fixture block",
            ),
        )
    )
    result = evaluate_host_with_arbiter(blocked, gate)
    assert result.arbiter_result.disposition is TransitionDisposition.STOP


def test_missing_capability_does_not_override_authority_stop():
    declaration = _declaration("limited-host", (HostCapability.FILESYSTEM_READ,))
    gate = evaluate_host_capabilities(declaration, (HostCapability.SHELL_EXECUTE,), alternate_host_allowed=True)
    result = evaluate_host_with_arbiter(_kernel(authority_valid=False), gate)
    assert result.arbiter_result.disposition is TransitionDisposition.STOP


def test_required_capability_order_does_not_change_gate_digest_or_verdict():
    declaration = _declaration(
        "stable-host",
        (HostCapability.GIT_READ, HostCapability.SHELL_EXECUTE, HostCapability.FILESYSTEM_READ),
    )
    first = evaluate_host_capabilities(
        declaration,
        (HostCapability.FILESYSTEM_READ, HostCapability.SHELL_EXECUTE, HostCapability.GIT_READ),
        alternate_host_allowed=True,
    )
    second = evaluate_host_capabilities(
        declaration,
        (HostCapability.GIT_READ, HostCapability.FILESYSTEM_READ, HostCapability.SHELL_EXECUTE),
        alternate_host_allowed=True,
    )
    assert first.digest == second.digest
    assert first.ready is second.ready is True
