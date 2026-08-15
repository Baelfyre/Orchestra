import json
import subprocess

import pytest

from orchestra_runtime import compliance_protocol as cp
from orchestra_runtime import evidence as ev
from orchestra_runtime import governance_kernel as gk
from orchestra_runtime import host_protocol as hp
from orchestra_runtime import preexecution as pe
from orchestra_runtime import shadow_conformance as sc
from orchestra_runtime.compliance_protocol import (
    ComplianceArbiterEvaluation,
    ComplianceConsumptionReceipt,
    ComplianceQueryReceipt,
    ComplianceSetEqualityGateResult,
    StewardTraceabilityReceipt,
    evaluate_compliance_set_equality,
    evaluate_compliance_with_arbiter,
)
from orchestra_runtime.governance_kernel import ArbiterKernelInput, GovernanceDecisionRecord, evaluate_arbiter
from orchestra_runtime.host_protocol import HostCapability, HostCapabilityDeclaration, HostCapabilityGateResult
from orchestra_runtime.preexecution import ExecutionAction, ExecutionIntent, PreExecutionConstraint, PreExecutionPolicy, evaluate_preexecution, evaluate_preexecution_with_arbiter
from orchestra_runtime.shadow_conformance import LegacyWorkflowClaim, ShadowComparisonRecord, ShadowConformanceReport, ShadowDiscrepancy
from orchestra_runtime.test_evidence import _actual_tested_sha, parse_coverage, parse_junit


A40 = "a" * 40
A64 = "a" * 64
B64 = "b" * 64


def _decision():
    return GovernanceDecisionRecord("critical-edge", "critical-edge", "APPROVED", "fixture")


def _kernel(**overrides):
    values = dict(project_id="orchestra", unit_id="critical-edge", governance_decisions=(_decision(),))
    values.update(overrides)
    return ArbiterKernelInput(**values)


def _query():
    return ComplianceQueryReceipt("x/y", "1", 1, "v1", A64, (), ("SRC",), ("A",))


def _consumption(query):
    return ComplianceConsumptionReceipt(query.digest, ("SRC",), ("A",), (("A", "OK"),), "APPROVED")


def _trace(query):
    return StewardTraceabilityReceipt(query.digest, ("SRC",), ("A",), ("receipt:trace",))


def _host(*capabilities):
    return HostCapabilityDeclaration("host", "adapter", tuple(capabilities), ("receipt:host",), "now")


# Evidence branch completion

def test_evidence_private_text_schema_and_success_assertion_edges():
    with pytest.raises(ValueError, match="control characters"):
        ev._clean_nonempty("bad\nvalue", "field")
    with pytest.raises(ValueError, match="unsupported source-state"):
        ev.SourceStateReceipt("x/y", "main", A40, "2026-08-15T11:00:00Z", "api", schema_version="bad")
    receipt = ev.SourceStateReceipt("x/y", "main", A40, "2026-08-15T11:00:00Z", "api")
    receipt.assert_canonical_sha(A40)
    with pytest.raises(ValueError, match="unsupported validation receipt"):
        ev.ValidationExecutionReceipt("x", ("x",), 0, "2026-08-15T11:00:00Z", "2026-08-15T11:00:00Z", A64, B64, schema_version="bad")


# Governance branch completion

def test_governance_private_and_schema_edges():
    with pytest.raises(TypeError, match="must be a string"):
        gk._nonempty(1, "field")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty"):
        gk._nonempty(" ", "field")
    with pytest.raises(ValueError, match="unsupported decision"):
        gk._enum("MAGIC", gk.GovernanceDecision, "decision")
    with pytest.raises(ValueError, match="unsupported Arbiter"):
        ArbiterKernelInput("p", "u", (_decision(),), schema_version="bad")
    with pytest.raises(ValueError, match="> 0"):
        _kernel(maximum_identical_failure_repetitions=0)
    valid = _kernel()
    assert gk.safe_evaluate_arbiter(valid).to_dict() == evaluate_arbiter(valid).to_dict()


# Compliance branch completion

def test_compliance_private_filters_types_and_full_arbiter_surface():
    with pytest.raises(ValueError, match="non-empty"):
        cp._text("", "field")
    with pytest.raises(ValueError, match="SHA-256"):
        cp._sha256("abc", "digest")
    assert cp._filters({"jurisdiction": "PH", "domain": None, "blank": " "}) == (("jurisdiction", "PH"),)
    with pytest.raises(ValueError, match="unsupported compliance query schema"):
        ComplianceQueryReceipt("x/y", "1", 1, "v1", A64, (), (), (), schema_version="bad")
    with pytest.raises(TypeError, match="filters"):
        ComplianceQueryReceipt("x/y", "1", 1, "v1", A64, [], (), ())  # type: ignore[arg-type]
    query = _query()
    consumption = _consumption(query)
    trace = _trace(query)
    with pytest.raises(TypeError, match="consumption"):
        evaluate_compliance_set_equality(query, "bad", trace)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="traceability"):
        evaluate_compliance_set_equality(query, consumption, "bad")  # type: ignore[arg-type]
    gate = evaluate_compliance_set_equality(query, consumption, trace)
    evaluation = evaluate_compliance_with_arbiter(_kernel(), gate)
    assert isinstance(evaluation, ComplianceArbiterEvaluation)
    assert evaluation.to_dict()["arbiter_result"]["disposition"] == "AUTO_CONTINUE"
    assert len(evaluation.digest) == 64
    with pytest.raises(TypeError, match="compliance_gate"):
        evaluate_compliance_with_arbiter(_kernel(), "bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate IDs"):
        ComplianceSetEqualityGateResult(True, (), A64, A64, A64, ("A", "A"))


# Host branch completion

def test_host_private_text_and_gate_boolean_edges():
    with pytest.raises(ValueError, match="non-empty"):
        hp._text("", "host_id")
    declaration = _host(HostCapability.GIT_READ)
    with pytest.raises(TypeError, match="must be bool"):
        HostCapabilityGateResult("h", declaration.digest, (), (), 1, True)  # type: ignore[arg-type]
    gate = hp.evaluate_host_capabilities(declaration, (), alternate_host_allowed=True)
    assert gate.ready is True
    assert gate.missing_capabilities == ()


# Pre-execution branch completion

def test_preexecution_private_action_path_and_authority_edges():
    with pytest.raises(ValueError, match="non-empty"):
        pe._text("", "field")
    with pytest.raises(ValueError, match="unsupported execution action"):
        pe._action("MAGIC")
    for bad in ("\\absolute", "./relative", "src/./x", "src/../secret"):
        with pytest.raises(ValueError):
            pe._path(bad, "path")
    with pytest.raises(ValueError, match="unsupported pre-execution policy"):
        PreExecutionPolicy("p", (ExecutionAction.SHELL_EXECUTE,), schema_version="bad")

    host = _host(HostCapability.SANDBOX_EXECUTE, HostCapability.REMOTE_WRITE)
    destructive = evaluate_preexecution(
        ExecutionIntent("d", ExecutionAction.DESTRUCTIVE_SIMULATION),
        PreExecutionPolicy("p", (ExecutionAction.DESTRUCTIVE_SIMULATION,)),
        host,
    )
    assert destructive.constraint is PreExecutionConstraint.ESCALATE_HUMAN
    production = evaluate_preexecution(
        ExecutionIntent("prod", ExecutionAction.PRODUCTION_MUTATION),
        PreExecutionPolicy("p2", (ExecutionAction.PRODUCTION_MUTATION,)),
        host,
    )
    assert production.constraint is PreExecutionConstraint.ESCALATE_HUMAN
    wait = evaluate_preexecution(
        ExecutionIntent("shell", ExecutionAction.SHELL_EXECUTE),
        PreExecutionPolicy("p3", (ExecutionAction.SHELL_EXECUTE,), alternate_host_allowed=True),
        host,
    )
    assert wait.constraint is PreExecutionConstraint.WAIT_FOR_CAPACITY
    assert evaluate_preexecution_with_arbiter(_kernel(), wait).arbiter_result.disposition.value == "WAIT_FOR_CAPACITY"


# Shadow branch completion

def test_shadow_private_constructor_and_report_edges():
    with pytest.raises(ValueError, match="non-empty"):
        sc._nonempty("", "field")
    with pytest.raises(ValueError, match="SHA-256"):
        sc._sha256("abc", "digest")
    with pytest.raises(TypeError, match="validation_allowed"):
        LegacyWorkflowClaim("x", "conductor", False, 1, "AUTO_CONTINUE")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="evidence_digests"):
        LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE", [A64])  # type: ignore[arg-type]
    claim = LegacyWorkflowClaim("x", "conductor", False, True, "AUTO_CONTINUE", (A64,))
    with pytest.raises(ValueError, match="unsupported shadow comparison"):
        ShadowComparisonRecord(claim, "r", "conductor", False, True, "AUTO_CONTINUE", (), schema_version="bad")
    with pytest.raises(TypeError, match="machine_governance_required"):
        ShadowComparisonRecord(claim, "r", "conductor", 1, True, "AUTO_CONTINUE", ())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="machine_validation_allowed"):
        ShadowComparisonRecord(claim, "r", "conductor", False, 1, "AUTO_CONTINUE", ())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="discrepancy_codes"):
        ShadowComparisonRecord(claim, "r", "conductor", False, True, "AUTO_CONTINUE", ("BAD",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported shadow report"):
        ShadowConformanceReport((), schema_version="bad")


# Test-evidence branch completion

def test_test_evidence_nested_junit_zero_branch_and_real_git_sha(tmp_path):
    junit = tmp_path / "nested.xml"
    junit.write_text(
        '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="1"/><testsuite tests="3" failures="1" errors="0" skipped="0"/></testsuites>',
        encoding="utf-8",
    )
    counts = parse_junit(junit)
    assert counts == {"total": 5, "passed": 3, "failures": 1, "errors": 0, "skipped": 1}
    coverage = tmp_path / "coverage.json"
    coverage.write_text(json.dumps({"totals": {"num_statements": 2, "covered_lines": 2, "missing_lines": 0, "num_branches": 0, "covered_branches": 0, "missing_branches": 0}}), encoding="utf-8")
    assert parse_coverage(coverage)["branch_percent"] == 100.0
    assert len(_actual_tested_sha()) == 40
