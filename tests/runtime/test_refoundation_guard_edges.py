import json
from pathlib import Path

import pytest

from orchestra_runtime import machine_contracts as mc
from orchestra_runtime.compliance_protocol import (
    ComplianceConsumptionReceipt,
    ComplianceExclusion,
    ComplianceQueryReceipt,
    ComplianceSetEqualityGateResult,
    StewardTraceabilityReceipt,
    evaluate_compliance_set_equality,
    evaluate_compliance_with_arbiter,
)
from orchestra_runtime.context_state import (
    ContinuityEvent,
    CurrentProjectState,
    JsonlContinuityStore,
    compile_context,
    render_state_markdown,
)
from orchestra_runtime.evidence import (
    EvidenceMismatchError,
    SourceStateReceipt,
    ValidationExecutionReceipt,
    build_validation_execution_receipt,
    canonical_json_bytes,
    normalize_git_sha,
    normalize_sha256,
    normalize_timestamp,
)
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
    evaluate_arbiter,
    safe_evaluate_arbiter,
)
from orchestra_runtime.host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    HostCapabilityGateResult,
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
from orchestra_runtime.remediation_circuit import (
    CircuitConstraint,
    CircuitDecision,
    CircuitReason,
    RemediationCircuitState,
    evaluate_circuit_with_arbiter,
    failure_signature,
    record_evidence_wait,
    record_success,
    request_remediation,
)
from orchestra_runtime.shadow_conformance import (
    LegacyWorkflowClaim,
    MigrationStage,
    ShadowComparisonRecord,
    ShadowConformanceReport,
    ShadowDiscrepancy,
    compare_shadow_claim,
)
from orchestra_runtime.test_evidence import build_test_evidence, parse_coverage, parse_junit
from orchestra_runtime.workflow_contracts import build_workflow_sanity_receipt


ROOT = Path(__file__).resolve().parents[2]
SHA40_A = "a" * 40
SHA40_B = "b" * 40
SHA64_A = "a" * 64
SHA64_B = "b" * 64


def _decision(value="APPROVED", **overrides):
    values = dict(
        reviewer="edge-suite",
        project_context="edge-suite",
        decision=value,
        reason="fixture",
        evidence_refs=("receipt:edge",),
    )
    values.update(overrides)
    return GovernanceDecisionRecord(**values)


def _kernel(**overrides):
    values = dict(project_id="orchestra", unit_id="edge-suite", governance_decisions=(_decision(),))
    values.update(overrides)
    return ArbiterKernelInput(**values)


def _host(*capabilities, alternate_evidence=True):
    return HostCapabilityDeclaration(
        host_id="edge-host",
        adapter_id="adapter:edge",
        capabilities=tuple(capabilities),
        evidence_refs=("receipt:host",) if alternate_evidence else (),
        observed_at="2026-08-15T11:00:00Z",
    )


def _state(**overrides):
    values = dict(
        project_id="orchestra",
        repository="Baelfyre/Orchestra",
        canonical_sha=SHA40_A,
        phase="P9",
        authority_mode="FULL_AUTONOMOUS_BOUNDED",
        current_task="hardening",
        blockers=(),
        critical_receipt_refs=("receipt:test",),
        evidence_index_refs=("evidence:test",),
        revision=1,
        updated_at="2026-08-15T11:00:00Z",
    )
    values.update(overrides)
    return CurrentProjectState(**values)


def _query_receipt():
    return ComplianceQueryReceipt(
        canonical_repository="Baelfyre/Orchestra-Compliance-Registry",
        registry_version="0.1.0",
        release_sequence=1,
        release_tag="registry-v0.1.0",
        manifest_sha256=SHA64_A,
        filters=(("jurisdiction", "PH"),),
        source_ids=("SRC",),
        obligation_ids=("OBL-A", "OBL-B"),
    )


# Evidence kernel guards
@pytest.mark.parametrize("value", [None, 1, "", "   ", "abc", "g" * 40])
def test_exact_git_sha_guards(value):
    with pytest.raises((TypeError, ValueError)):
        normalize_git_sha(value)  # type: ignore[arg-type]


def test_sha256_timestamp_and_json_guards():
    with pytest.raises(ValueError):
        normalize_sha256("abc")
    with pytest.raises(ValueError):
        normalize_timestamp("2026-08-15T11:00:00")
    with pytest.raises(ValueError):
        normalize_timestamp("not-a-time")
    with pytest.raises(ValueError):
        canonical_json_bytes({"bad": float("nan")})
    with pytest.raises(ValueError):
        canonical_json_bytes({"bad": object()})


def test_source_receipt_relationship_and_optional_field_guards():
    base = dict(
        repository="Baelfyre/Orchestra",
        canonical_branch="main",
        live_canonical_sha=SHA40_A,
        verification_timestamp="2026-08-15T11:00:00Z",
        verification_method="GITHUB_API",
    )
    with pytest.raises(ValueError, match="owner/name"):
        SourceStateReceipt(**{**base, "repository": "Orchestra"})
    with pytest.raises(TypeError):
        SourceStateReceipt(**{**base, "pull_request_number": True})
    with pytest.raises(ValueError):
        SourceStateReceipt(**{**base, "pull_request_number": 0})
    with pytest.raises(ValueError, match="exact_pr_head is required"):
        SourceStateReceipt(**{**base, "pull_request_number": 1})
    with pytest.raises(ValueError, match="pull_request_number is required"):
        SourceStateReceipt(**{**base, "exact_pr_head": SHA40_B})
    with pytest.raises(ValueError, match="pull_request_number is required"):
        SourceStateReceipt(**{**base, "merge_or_squash_sha": SHA40_A})

    receipt = SourceStateReceipt(**base)
    with pytest.raises(EvidenceMismatchError, match="does not contain an exact PR head"):
        receipt.assert_pr_head(SHA40_B)
    assert set(receipt.to_dict()) == {
        "schema_version", "repository", "canonical_branch", "live_canonical_sha",
        "verification_timestamp", "verification_method"
    }


def test_validation_receipt_constructor_guards_and_optional_state():
    base = dict(
        command_id="edge",
        command=("git", "status"),
        exit_code=0,
        started_at="2026-08-15T11:00:00Z",
        finished_at="2026-08-15T11:00:01Z",
        stdout_sha256=SHA64_A,
        stderr_sha256=SHA64_B,
    )
    with pytest.raises(ValueError, match="non-empty tuple"):
        ValidationExecutionReceipt(**{**base, "command": ()})
    with pytest.raises(TypeError, match="exit_code"):
        ValidationExecutionReceipt(**{**base, "exit_code": True})
    with pytest.raises(ValueError, match="must not precede"):
        ValidationExecutionReceipt(**{**base, "started_at": "2026-08-15T11:00:02Z"})
    receipt = ValidationExecutionReceipt(**base)
    assert receipt.exact_state_preserved is None
    with pytest.raises(ValueError, match="PASS or FAIL"):
        receipt.assert_claimed_verdict("MAYBE")
    with pytest.raises(TypeError, match="stdout"):
        build_validation_execution_receipt(
            command_id="edge", command=("x",), exit_code=0,
            started_at="2026-08-15T11:00:00Z", finished_at="2026-08-15T11:00:01Z",
            stdout=object(),  # type: ignore[arg-type]
        )


# Governance kernel guards and precedence

def test_governance_record_and_kernel_input_guards():
    with pytest.raises(ValueError, match="unsupported governance decision schema"):
        _decision(schema_version="bad")
    with pytest.raises(ValueError, match="unsupported decision"):
        _decision(value="MAGIC")
    with pytest.raises(TypeError, match="human_review_required"):
        _decision(human_review_required="yes")
    with pytest.raises(TypeError, match="risks"):
        _decision(risks=["x"])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="governance_decisions must be a tuple"):
        ArbiterKernelInput(project_id="x", unit_id="y", governance_decisions=[])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="GovernanceDecisionRecord"):
        ArbiterKernelInput(project_id="x", unit_id="y", governance_decisions=("bad",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="authority_valid"):
        _kernel(authority_valid=1)
    with pytest.raises(ValueError, match=">= 0"):
        _kernel(remediation_attempt_count=-1)
    with pytest.raises(ValueError, match="> 0"):
        _kernel(maximum_remediation_attempts=0)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"protected_boundary_clear": False}, TransitionDisposition.STOP),
        ({"governance_decisions": (_decision("BLOCKED"),)}, TransitionDisposition.STOP),
        ({"scope_or_policy_decision_required": True}, TransitionDisposition.ESCALATE_HUMAN),
        ({"external_authority_missing": True}, TransitionDisposition.ESCALATE_HUMAN),
        ({"contradiction_unresolved": True}, TransitionDisposition.ESCALATE_HUMAN),
        ({"host_capacity_available": False}, TransitionDisposition.WAIT_FOR_CAPACITY),
        ({"governance_evidence_complete": False}, TransitionDisposition.WAIT_FOR_EVIDENCE),
        ({"required_receipts_present": False}, TransitionDisposition.WAIT_FOR_EVIDENCE),
        ({"exact_state_valid": False}, TransitionDisposition.WAIT_FOR_EVIDENCE),
        ({"validation_passed": False}, TransitionDisposition.WAIT_FOR_EVIDENCE),
    ],
)
def test_governance_precedence_edges(overrides, expected):
    assert evaluate_arbiter(_kernel(**overrides)).disposition is expected


def test_revision_and_identical_failure_edges_and_safe_boundary():
    revision = evaluate_arbiter(_kernel(governance_decisions=(_decision("REVISION_REQUIRED"),)))
    assert revision.disposition is TransitionDisposition.ESCALATE_HUMAN
    identical = evaluate_arbiter(_kernel(identical_failure_repetitions=3))
    assert identical.disposition is TransitionDisposition.ESCALATE_HUMAN
    malformed = safe_evaluate_arbiter({"not": "kernel"})
    assert malformed.disposition is TransitionDisposition.ESCALATE_HUMAN
    good = evaluate_arbiter(_kernel())
    good.assert_claimed_disposition("AUTO_CONTINUE")
    with pytest.raises(ValueError, match="conflicts"):
        good.assert_claimed_disposition("STOP")


# Machine-contract loader/parity guards

def _write_json(root: Path, relative: str, payload):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_machine_contract_loaders_fail_closed(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        mc.load_specialist_registry(tmp_path)
    path = tmp_path / "machine/specialists/registry.v1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        mc.load_specialist_registry(tmp_path)
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        mc.load_specialist_registry(tmp_path)
    _write_json(tmp_path, "machine/specialists/registry.v1.json", {"schema_version": "bad", "specialists": []})
    with pytest.raises(ValueError, match="unsupported specialist registry"):
        mc.load_specialist_registry(tmp_path)


def test_machine_specialist_and_routing_guards(tmp_path):
    _write_json(tmp_path, "machine/specialists/registry.v1.json", {
        "schema_version": mc.SPECIALIST_REGISTRY_SCHEMA_VERSION,
        "specialists": [{"slug": "a"}, {"slug": "a"}],
    })
    with pytest.raises(ValueError, match="duplicate"):
        mc.valid_specialist_ids(tmp_path)
    _write_json(tmp_path, "machine/specialists/registry.v1.json", {
        "schema_version": mc.SPECIALIST_REGISTRY_SCHEMA_VERSION,
        "specialists": [{"slug": ""}],
    })
    with pytest.raises(ValueError, match="empty"):
        mc.valid_specialist_ids(tmp_path)

    _write_json(tmp_path, "machine/routing/routes.v1.json", {
        "schema_version": mc.ROUTING_CONTRACT_SCHEMA_VERSION,
        "command_routes": {},
        "ambiguity_fallback": "conductor",
    })
    with pytest.raises(ValueError, match="no command routes"):
        mc.command_route_map(tmp_path)
    assert mc.command_route_record("unknown", tmp_path) == {
        "specialist": "conductor", "route_id": "ambiguous-overlapping"
    }
    _write_json(tmp_path, "machine/routing/routes.v1.json", {
        "schema_version": mc.ROUTING_CONTRACT_SCHEMA_VERSION,
        "command_routes": {"x": []},
        "ambiguity_fallback": "conductor",
    })
    with pytest.raises(ValueError, match="must be an object"):
        mc.command_route_map(tmp_path)
    with pytest.raises(ValueError, match="must be an object"):
        mc.command_route_record("x", tmp_path)
    _write_json(tmp_path, "machine/routing/routes.v1.json", {
        "schema_version": mc.ROUTING_CONTRACT_SCHEMA_VERSION,
        "command_routes": {"x": {}},
        "ambiguity_fallback": "",
    })
    with pytest.raises(ValueError, match="has no specialist"):
        mc.command_route_map(tmp_path)
    with pytest.raises(ValueError, match="no ambiguity fallback"):
        mc.command_route_record("unknown", tmp_path)


def test_machine_governance_contract_guards(tmp_path):
    _write_json(tmp_path, "machine/governance/policy.v1.json", {
        "schema_version": mc.GOVERNANCE_POLICY_SCHEMA_VERSION,
        "governance_required_specialists": ["a", "a"],
        "runtime_validation_rules": [],
    })
    with pytest.raises(ValueError, match="invalid governance_required"):
        mc.governance_required_specialists(tmp_path)
    with pytest.raises(ValueError, match="no runtime validation rules"):
        mc.runtime_validation_rule_records(tmp_path)


# Compliance protocol guards

def test_compliance_query_constructor_and_registry_input_guards():
    with pytest.raises(ValueError, match="positive integer"):
        ComplianceQueryReceipt(
            canonical_repository="x/y", registry_version="1", release_sequence=0,
            release_tag="v1", manifest_sha256=SHA64_A, filters=(), source_ids=(), obligation_ids=()
        )
    status = {
        "registry_status": "BROKEN", "canonical_repository": "x/y", "registry_version": "1",
        "release_sequence": 1, "release_tag": "v1", "manifest_sha256": SHA64_A,
    }
    with pytest.raises(ValueError, match="VERIFIED"):
        ComplianceQueryReceipt.from_registry_result(status, {}, filters={})
    status["registry_status"] = "VERIFIED"
    with pytest.raises(ValueError, match="version differs"):
        ComplianceQueryReceipt.from_registry_result(status, {"registry_version": "2", "release_sequence": 1}, filters={})
    with pytest.raises(ValueError, match="release sequence differs"):
        ComplianceQueryReceipt.from_registry_result(status, {"registry_version": "1", "release_sequence": 2}, filters={})
    with pytest.raises(ValueError, match="source and obligation lists"):
        ComplianceQueryReceipt.from_registry_result(status, {"registry_version": "1", "release_sequence": 1, "sources": {}, "obligations": []}, filters={})
    with pytest.raises(ValueError, match="source record"):
        ComplianceQueryReceipt.from_registry_result(status, {"registry_version": "1", "release_sequence": 1, "sources": ["bad"], "obligations": []}, filters={})
    with pytest.raises(ValueError, match="obligation record"):
        ComplianceQueryReceipt.from_registry_result(status, {"registry_version": "1", "release_sequence": 1, "sources": [], "obligations": ["bad"]}, filters={})


def test_compliance_consumption_traceability_and_gate_guards():
    query = _query_receipt()
    with pytest.raises(TypeError, match="classifications"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("OBL-A",), [("OBL-A", "OK")], "APPROVED")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cover exactly"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("OBL-A",), (), "APPROVED")
    exclusion = ComplianceExclusion("OBL-A", "reason", "receipt:x", "governor")
    with pytest.raises(ValueError, match="both consumed and excluded"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("OBL-A",), (("OBL-A", "OK"),), "APPROVED", (exclusion,))
    with pytest.raises(TypeError, match="evidence_refs"):
        StewardTraceabilityReceipt(query.digest, ("SRC",), ("OBL-A", "OBL-B"), ["r"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicates"):
        StewardTraceabilityReceipt(query.digest, ("SRC",), ("OBL-A", "OBL-B"), ("r", "r"))
    with pytest.raises(TypeError, match="ready"):
        ComplianceSetEqualityGateResult("yes", (), query.digest, query.digest, query.digest, ())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="query must"):
        evaluate_compliance_set_equality("bad", None, None)  # type: ignore[arg-type]
    gate = ComplianceSetEqualityGateResult(True, (), query.digest, query.digest, query.digest, ())
    with pytest.raises(TypeError, match="kernel_input"):
        evaluate_compliance_with_arbiter("bad", gate)  # type: ignore[arg-type]


# Context state guards

def test_context_state_constructor_and_roundtrip_guards():
    with pytest.raises(ValueError, match="owner/name"):
        _state(repository="Orchestra")
    with pytest.raises(ValueError, match="duplicate values"):
        _state(blockers=("x", "x"))
    with pytest.raises(ValueError, match="non-negative"):
        _state(revision=True)
    with pytest.raises(TypeError, match="object"):
        CurrentProjectState.from_dict([])  # type: ignore[arg-type]
    state = _state()
    assert CurrentProjectState.from_dict(state.to_dict()) == state
    with pytest.raises(ValueError, match="unsupported context level"):
        compile_context(state, "L9")
    with pytest.raises(TypeError, match="state must"):
        compile_context("bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ContinuityEvent"):
        compile_context(state, "L3", history=("bad",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="state must"):
        render_state_markdown("bad")  # type: ignore[arg-type]


def test_continuity_event_and_store_edge_guards(tmp_path):
    with pytest.raises(ValueError, match="positive integer"):
        ContinuityEvent(0, "p", "e", "2026-08-15T11:00:00Z", {}, None)
    with pytest.raises(ValueError, match="only the first"):
        ContinuityEvent(2, "p", "e", "2026-08-15T11:00:00Z", {}, None)
    with pytest.raises(ValueError, match="first event must not"):
        ContinuityEvent(1, "p", "e", "2026-08-15T11:00:00Z", {}, SHA64_A)
    with pytest.raises(TypeError, match="mapping"):
        ContinuityEvent(1, "p", "e", "2026-08-15T11:00:00Z", [], None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="object"):
        ContinuityEvent.from_dict([])  # type: ignore[arg-type]
    store = JsonlContinuityStore(tmp_path / "missing.jsonl", "p")
    assert store.load() == ()
    blank = tmp_path / "blank.jsonl"
    blank.write_text("\n", encoding="utf-8")
    with pytest.raises(ValueError, match="blank line"):
        JsonlContinuityStore(blank, "p").load()


# Host-protocol guards

def test_host_declaration_and_gate_guards():
    with pytest.raises(ValueError, match="unsupported host declaration"):
        HostCapabilityDeclaration("h", "a", (), ("r",), "now", schema_version="bad")
    with pytest.raises(ValueError, match="duplicates"):
        HostCapabilityDeclaration("h", "a", (), ("r", "r"), "now")
    declaration = _host(HostCapability.GIT_READ)
    with pytest.raises(TypeError, match="declaration must"):
        evaluate_host_capabilities("bad", (), alternate_host_allowed=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready must equal"):
        HostCapabilityGateResult("h", declaration.digest, (HostCapability.GIT_READ,), (), True, False)
    gate = evaluate_host_capabilities(declaration, (HostCapability.GIT_READ,), alternate_host_allowed=True)
    assert gate.digest
    with pytest.raises(TypeError, match="kernel_input"):
        evaluate_host_with_arbiter("bad", gate)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="host_gate"):
        evaluate_host_with_arbiter(_kernel(), "bad")  # type: ignore[arg-type]


# Pre-execution guards

def test_execution_intent_policy_and_path_guards():
    with pytest.raises(ValueError, match="unsupported execution intent"):
        ExecutionIntent("x", ExecutionAction.SHELL_EXECUTE, schema_version="bad")
    with pytest.raises(ValueError, match="at least one requested path"):
        ExecutionIntent("x", ExecutionAction.FILE_READ)
    for bad in ("/etc/passwd", "../secret", "file://secret", "C:/secret"):
        with pytest.raises(ValueError):
            ExecutionIntent("x", ExecutionAction.FILE_READ, requested_paths=(bad,))
    with pytest.raises(ValueError, match="duplicate paths"):
        ExecutionIntent("x", ExecutionAction.FILE_READ, requested_paths=("src", "src"))
    with pytest.raises(ValueError, match="duplicates"):
        ExecutionIntent("x", ExecutionAction.SHELL_EXECUTE, evidence_refs=("r", "r"))
    with pytest.raises(ValueError, match="non-empty and unique"):
        PreExecutionPolicy("p", ())
    with pytest.raises(ValueError, match="non-empty and unique"):
        PreExecutionPolicy("p", (ExecutionAction.FILE_READ, ExecutionAction.FILE_READ))
    with pytest.raises(TypeError, match="remote_write_authorized"):
        PreExecutionPolicy("p", (ExecutionAction.SHELL_EXECUTE,), remote_write_authorized=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="inside prohibited"):
        PreExecutionPolicy("p", (ExecutionAction.FILE_READ,), allowed_paths=("src/secrets",), prohibited_paths=("src",))


def test_preexecution_type_and_arbiter_guards():
    policy = PreExecutionPolicy("p", (ExecutionAction.SHELL_EXECUTE,))
    intent = ExecutionIntent("i", ExecutionAction.SHELL_EXECUTE)
    host = _host(HostCapability.SHELL_EXECUTE)
    with pytest.raises(TypeError, match="intent/policy"):
        evaluate_preexecution("bad", policy, host)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="host"):
        evaluate_preexecution(intent, policy, "bad")  # type: ignore[arg-type]
    gate = evaluate_preexecution(intent, policy, host)
    assert gate.constraint is PreExecutionConstraint.ALLOW
    assert gate.digest
    with pytest.raises(TypeError, match="kernel_input/gate"):
        evaluate_preexecution_with_arbiter("bad", gate)  # type: ignore[arg-type]


# Remediation-circuit guards

def _circuit(**overrides):
    values = dict(project_id="orchestra", unit_id="u", envelope_id="e")
    values.update(overrides)
    return RemediationCircuitState(**values)


def test_circuit_state_and_signature_guards():
    with pytest.raises(ValueError, match="unsupported remediation"):
        _circuit(schema_version="bad")
    with pytest.raises(ValueError, match="non-negative"):
        _circuit(total_remediation_attempts=-1)
    with pytest.raises(ValueError, match="> 0"):
        _circuit(maximum_no_progress_cycles=0)
    assert RemediationCircuitState.from_dict(_circuit().to_dict()) == _circuit()
    with pytest.raises(ValueError):
        failure_signature(validator_id="", reason_code="x", evidence_digest=SHA64_A)
    with pytest.raises(TypeError, match="state"):
        request_remediation("bad", failure_digest=SHA64_A)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="state"):
        record_evidence_wait("bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="state"):
        record_success("bad", progress_digest=SHA64_A)  # type: ignore[arg-type]


def test_circuit_exhaustion_and_progress_edges():
    exhausted = request_remediation(_circuit(total_remediation_attempts=3), failure_digest=SHA64_A)
    assert exhausted.reason is CircuitReason.TOTAL_BUDGET_EXHAUSTED
    identical = request_remediation(
        _circuit(current_failure_signature=SHA64_A, identical_failure_repetitions=2),
        failure_digest=SHA64_A,
    )
    assert identical.reason is CircuitReason.IDENTICAL_FAILURE_LIMIT_EXCEEDED
    no_progress = request_remediation(
        _circuit(last_action="REMEDIATION", no_progress_cycles=2),
        failure_digest=SHA64_A,
    )
    assert no_progress.reason is CircuitReason.NO_PROGRESS_LIMIT_EXCEEDED
    wait_loop = request_remediation(
        _circuit(last_action="WAIT_FOR_EVIDENCE", wait_remediation_transitions=4),
        failure_digest=SHA64_A,
    )
    assert wait_loop.reason is CircuitReason.WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED
    wait = record_evidence_wait(_circuit(last_action="REMEDIATION", wait_remediation_transitions=4))
    assert wait.constraint is CircuitConstraint.ESCALATE_HUMAN
    success = record_success(_circuit(current_failure_signature=SHA64_A), progress_digest=SHA64_B)
    assert success.constraint is CircuitConstraint.CONTINUE
    assert success.state.current_failure_signature is None
    assert success.digest


def test_circuit_arbiter_type_guards_and_stop_precedence():
    circuit = CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.TOTAL_BUDGET_EXHAUSTED, _circuit())
    with pytest.raises(TypeError, match="kernel_input"):
        evaluate_circuit_with_arbiter("bad", circuit)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="circuit"):
        evaluate_circuit_with_arbiter(_kernel(), "bad")  # type: ignore[arg-type]
    result = evaluate_circuit_with_arbiter(_kernel(authority_valid=False), circuit)
    assert result.arbiter_result.disposition is TransitionDisposition.STOP


# Shadow/report guards

def test_shadow_constructor_and_type_guards():
    with pytest.raises(ValueError, match="unsupported shadow claim"):
        LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE", schema_version="bad")
    with pytest.raises(TypeError, match="governance_required"):
        LegacyWorkflowClaim("x", "conductor", 1, True, "AUTO_CONTINUE")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicates"):
        LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE", (SHA64_A, SHA64_A))
    arbiter = evaluate_arbiter(_kernel())
    with pytest.raises(TypeError, match="claim"):
        compare_shadow_claim("bad", machine_validation_allowed=True, machine_arbiter_result=arbiter, root=ROOT)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="machine_validation_allowed"):
        compare_shadow_claim(LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE"), machine_validation_allowed=1, machine_arbiter_result=arbiter, root=ROOT)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="machine_arbiter_result"):
        compare_shadow_claim(LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE"), machine_validation_allowed=True, machine_arbiter_result="bad", root=ROOT)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported migration_stage"):
        ShadowConformanceReport(records=(), migration_stage="MAGIC")
    with pytest.raises(TypeError, match="records"):
        ShadowConformanceReport(records=("bad",))  # type: ignore[arg-type]


def test_shadow_record_schema_and_discrepancy_dedup():
    claim = LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE", (SHA64_A,))
    with pytest.raises(TypeError, match="legacy_claim"):
        ShadowComparisonRecord("bad", "r", "conductor", False, True, "AUTO_CONTINUE", ())  # type: ignore[arg-type]
    record = ShadowComparisonRecord(
        claim, "r", "conductor", False, True, "AUTO_CONTINUE",
        (ShadowDiscrepancy.SPECIALIST_MISMATCH, ShadowDiscrepancy.SPECIALIST_MISMATCH),
    )
    assert record.discrepancy_codes == (ShadowDiscrepancy.SPECIALIST_MISMATCH,)


# Test-evidence parser guards

def test_test_evidence_parser_additional_guards(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text("<bad />", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported JUnit"):
        parse_junit(junit)
    junit.write_text('<testsuites tests="x" failures="0" errors="0" skipped="0"/>', encoding="utf-8")
    with pytest.raises(ValueError, match="must be an integer"):
        parse_junit(junit)
    coverage = tmp_path / "coverage.json"
    coverage.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="does not contain totals"):
        parse_coverage(coverage)
    coverage.write_text(json.dumps({"totals": {"num_statements": 0}}), encoding="utf-8")
    with pytest.raises(ValueError, match="statement totals are invalid"):
        parse_coverage(coverage)
    coverage.write_text(json.dumps({"totals": {"num_statements": 1, "covered_lines": 1, "missing_lines": 0, "num_branches": 1, "covered_branches": 2, "missing_branches": -1}}), encoding="utf-8")
    with pytest.raises(ValueError, match="branch totals are invalid"):
        parse_coverage(coverage)


def test_test_evidence_rejects_bad_outcome_and_threshold(tmp_path):
    coverage = tmp_path / "coverage.json"
    coverage.write_text(json.dumps({"totals": {"num_statements": 1, "covered_lines": 1, "missing_lines": 0, "num_branches": 0, "covered_branches": 0, "missing_branches": 0}}), encoding="utf-8")
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites tests="1" failures="0" errors="0" skipped="0"/>', encoding="utf-8")
    kwargs = dict(
        coverage_path=coverage, junit_path=junit, tested_sha=SHA40_A, source_head_sha=SHA40_A,
        minimum_statement_coverage=90, repository="Baelfyre/Orchestra", workflow_run_id="1",
        workflow_run_attempt="1", event_name="push", ref_name="main",
    )
    with pytest.raises(ValueError, match="unsupported runtime_test_outcome"):
        build_test_evidence(runtime_test_outcome="mystery", **kwargs)
    with pytest.raises(ValueError, match="between 0 and 100"):
        build_test_evidence(runtime_test_outcome="success", **{**kwargs, "minimum_statement_coverage": 101})
