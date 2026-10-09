from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.domain.adaptive.gate_coverage import (
    AQ6_CONTRACT_SCHEMA_VERSION,
    AQ6_DECISION_SCHEMA_VERSION,
    GateCoverageContractError,
    GateCoverageDeclaration,
    GateCoverageDecision,
    GateCoverageManifest,
    GateExecutionReceipt,
    evaluate_gate_coverage,
    validate_gate_coverage_contract,
)
from orchestra_runtime.domain.adaptive import gate_coverage
from orchestra_runtime.shared.canonicalization import receipt_digest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq6-gate-coverage.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "aq6-gate-coverage.v1.schema.json"
SOURCE = "orchestra:aq6"
CANDIDATE = "a" * 40
TREE = "b" * 40
STALE = "c" * 40
WHEN = "2026-09-09T01:00:00Z"
WORKFLOW = ".github/workflows/aq6-gate-coverage.yml"
COMMAND = "python -B -m pytest"
CHANGED = "orchestra_runtime/domain/adaptive/gate_coverage.py"
TEST_ID = "tests/runtime/test_adaptive_assurance_aq6.py::test_positive"


def _declaration(
    *,
    gate_id="aq6-runtime",
    assurance=("FUNCTIONAL_ASSURANCE", "PROVENANCE_ASSURANCE", "INDEPENDENT_QA"),
    risks=("PROVENANCE",),
    paths=(CHANGED,),
    tests=(TEST_ID,),
    commands=(COMMAND,),
):
    return GateCoverageDeclaration(
        gate_id=gate_id,
        assurance_classes=assurance,
        covered_paths=paths,
        covered_risks=risks,
        test_ids=tests,
        workflow_path=WORKFLOW,
        commands=commands,
    )


def _manifest(
    *,
    assurance=("FUNCTIONAL_ASSURANCE", "PROVENANCE_ASSURANCE", "INDEPENDENT_QA"),
    risks=("PROVENANCE",),
    declaration=None,
):
    declaration = declaration or _declaration(assurance=assurance, risks=risks)
    payload = {
        "schema_version": AQ6_CONTRACT_SCHEMA_VERSION,
        "manifest_id": "manifest-aq6",
        "repository": "Baelfyre/Orchestra",
        "source_ref": SOURCE,
        "candidate_sha": CANDIDATE,
        "tree_sha": TREE,
        "work_item_ref": "AQ6_GATE_COVERAGE",
        "changed_paths": [CHANGED],
        "required_assurance": list(assurance),
        "required_risks": list(risks),
        "declarations": [declaration.to_dict()],
        "generated_at": WHEN,
    }
    digest = receipt_digest(payload)
    payload["declarations"] = (declaration,)
    return GateCoverageManifest(**payload, manifest_digest=digest)


def _receipt(manifest, *, candidate=CANDIDATE, tree=TREE, **overrides):
    values = {
        "execution_id": "execution-aq6-runtime",
        "gate_id": manifest.declarations[0].gate_id,
        "result": "PASS",
        "candidate_sha": candidate,
        "tree_sha": tree,
        "command": COMMAND,
        "executed_test_ids": (TEST_ID,),
        "observed_at": WHEN,
    }
    values.update(overrides)
    return GateExecutionReceipt(**values)


def _decision(manifest, receipts, **overrides):
    values = {
        "current_repository": "Baelfyre/Orchestra",
        "current_source_ref": SOURCE,
        "current_candidate_sha": CANDIDATE,
        "current_tree_sha": TREE,
        "current_work_item_ref": "AQ6_GATE_COVERAGE",
        "available_test_ids": (TEST_ID,),
        "workflow_texts": {WORKFLOW: COMMAND},
        "test_coverage": {TEST_ID: (CHANGED,)},
        "evaluated_at": WHEN,
    }
    values.update(overrides)
    return evaluate_gate_coverage(manifest, receipts, **values)


def test_positive_decision_is_source_bound_and_non_authorizing():
    manifest = _manifest()
    decision = _decision(manifest, (_receipt(manifest),))
    assert decision.result == "PASS"
    assert decision.compliant
    assert decision.failure_codes == ()
    assert decision.candidate_sha == CANDIDATE
    assert GateCoverageDecision.from_mapping(decision.to_dict()) == decision


def test_contract_and_schema_are_strictly_bound_to_runtime():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert validate_gate_coverage_contract(contract) is contract
    assert contract["decision_schema_version"] == AQ6_DECISION_SCHEMA_VERSION
    jsonschema.Draft202012Validator.check_schema(schema)
    decision = _decision(_manifest(), (_receipt(_manifest()),))
    jsonschema.Draft202012Validator(schema).validate(decision.to_dict())
    with pytest.raises(GateCoverageContractError):
        validate_gate_coverage_contract({**contract, "unexpected": True})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate({**decision.to_dict(), "extra": True})


def test_current_identity_is_mandatory():
    manifest = _manifest()
    decision = evaluate_gate_coverage(manifest, (_receipt(manifest),), evaluated_at=WHEN)
    assert decision.result == "FAIL"
    assert "AQ6_CURRENT_IDENTITY_REQUIRED" in decision.failure_codes


def test_declared_gate_that_did_not_execute_fails_closed():
    manifest = _manifest()
    decision = _decision(manifest, ())
    assert decision.result == "FAIL"
    assert "AQ6_GATE_NOT_EXECUTED" in decision.failure_codes


def test_missing_workflow_command_fails_closed():
    manifest = _manifest()
    decision = _decision(manifest, (_receipt(manifest),), workflow_texts={WORKFLOW: "run: another command"})
    assert decision.result == "FAIL"
    assert "AQ6_WORKFLOW_COMMAND_MISSING" in decision.failure_codes
    decision = _decision(manifest, (_receipt(manifest, command="another command"),))
    assert decision.result == "FAIL"
    assert "AQ6_WORKFLOW_COMMAND_MISSING" in decision.failure_codes


def test_unknown_test_reference_fails_closed():
    manifest = _manifest()
    decision = _decision(manifest, (_receipt(manifest),), available_test_ids=())
    assert decision.result == "FAIL"
    assert "AQ6_UNKNOWN_TEST_REFERENCE" in decision.failure_codes


def test_executed_test_that_does_not_reach_changed_code_fails_closed():
    manifest = _manifest()
    decision = _decision(manifest, (_receipt(manifest),), test_coverage={TEST_ID: ()})
    assert decision.result == "FAIL"
    assert "AQ6_TEST_DOES_NOT_REACH_CHANGED_CODE" in decision.failure_codes


def test_stale_gate_evidence_fails_closed():
    manifest = _manifest()
    decision = _decision(manifest, (_receipt(manifest, candidate=STALE),))
    assert decision.result == "FAIL"
    assert "AQ6_STALE_GATE_EVIDENCE" in decision.failure_codes


def test_legacy_gate_without_adversarial_coverage_is_insufficient():
    assurance = ("FUNCTIONAL_ASSURANCE", "ADVERSARIAL_ASSURANCE", "INDEPENDENT_QA")
    manifest = _manifest(
        assurance=assurance,
        declaration=_declaration(assurance=("FUNCTIONAL_ASSURANCE",), risks=("PROVENANCE",)),
    )
    decision = _decision(manifest, (_receipt(manifest),))
    assert decision.result == "FAIL"
    assert "AQ6_LEGACY_GATE_COVERAGE_INSUFFICIENT" in decision.failure_codes


def test_generic_security_gate_without_tenant_coverage_is_insufficient():
    assurance = ("SECURITY_ASSURANCE", "TENANT_ISOLATION_ASSURANCE", "INDEPENDENT_QA")
    manifest = _manifest(
        assurance=assurance,
        risks=("MULTI_TENANT",),
        declaration=_declaration(assurance=("SECURITY_ASSURANCE",), risks=("MULTI_TENANT",)),
    )
    decision = _decision(manifest, (_receipt(manifest),))
    assert decision.result == "FAIL"
    assert "AQ6_TENANT_SECURITY_COVERAGE_INSUFFICIENT" in decision.failure_codes


def test_execution_result_and_scope_are_checked():
    manifest = _manifest()
    failed = _decision(manifest, (_receipt(manifest, result="FAIL"),))
    assert "AQ6_GATE_EXECUTION_FAILED" in failed.failure_codes
    extra = _receipt(manifest, executed_test_ids=("unlisted-test",))
    scoped = _decision(manifest, (extra,))
    assert "AQ6_EXECUTION_SCOPE_EXCEEDED" in scoped.failure_codes


def test_changed_path_and_required_assurance_are_checked_independently():
    manifest = _manifest(
        assurance=("FUNCTIONAL_ASSURANCE", "PROVENANCE_ASSURANCE", "INDEPENDENT_QA"),
        declaration=_declaration(paths=("other.py",)),
    )
    decision = _decision(manifest, (_receipt(manifest),), test_coverage={TEST_ID: ("other.py",)})
    assert "AQ6_CHANGED_PATH_UNCOVERED" in decision.failure_codes
    assert "AQ6_INCOMPLETE_INTEGRATION_WITH_GREEN_TESTS" in decision.failure_codes


def test_contract_normalizers_and_roundtrips_fail_closed():
    with pytest.raises(GateCoverageContractError):
        _declaration(gate_id=1)
    with pytest.raises(GateCoverageContractError):
        _declaration(gate_id=" ")
    with pytest.raises(GateCoverageContractError):
        _declaration(gate_id="bad id")
    with pytest.raises(GateCoverageContractError):
        _declaration(assurance="FUNCTIONAL_ASSURANCE")
    with pytest.raises(GateCoverageContractError):
        _declaration(paths=tuple(f"path-{index}.py" for index in range(257)))
    with pytest.raises(GateCoverageContractError):
        _declaration(tests=("bad test",))
    with pytest.raises(GateCoverageContractError):
        _declaration(paths=("../bad",))
    with pytest.raises(GateCoverageContractError):
        _declaration(assurance=("UNKNOWN",))
    with pytest.raises(GateCoverageContractError):
        _declaration(risks=("UNKNOWN",))
    with pytest.raises(GateCoverageContractError):
        _declaration(commands=())

    declaration = _declaration()
    assert GateCoverageDeclaration.from_mapping(declaration.to_dict()) == declaration
    with pytest.raises(TypeError):
        GateCoverageDeclaration.from_mapping(None)
    with pytest.raises(GateCoverageContractError):
        GateCoverageDeclaration.from_mapping({**declaration.to_dict(), "extra": True})

    manifest = _manifest()
    assert GateCoverageManifest.from_mapping(manifest.to_dict()) == manifest
    with pytest.raises(TypeError):
        GateCoverageManifest.from_mapping(None)
    with pytest.raises(GateCoverageContractError):
        GateCoverageManifest.from_mapping({**manifest.to_dict(), "extra": True})
    with pytest.raises(GateCoverageContractError):
        replace(manifest, schema_version="bad")
    with pytest.raises(GateCoverageContractError):
        replace(manifest, declarations=())
    with pytest.raises(GateCoverageContractError):
        replace(manifest, declarations=(manifest.declarations[0], manifest.declarations[0]))
    with pytest.raises(GateCoverageContractError):
        replace(manifest, manifest_digest=("0" * 63) + "z")
    with pytest.raises(GateCoverageContractError):
        replace(manifest, manifest_digest="0" * 64)


def test_receipt_and_decision_contract_edges_fail_closed():
    manifest = _manifest()
    receipt = _receipt(manifest)
    assert GateExecutionReceipt.from_mapping(receipt.to_dict()) == receipt
    with pytest.raises(GateCoverageContractError):
        replace(receipt, result="INVALID")
    with pytest.raises(TypeError):
        GateExecutionReceipt.from_mapping(None)
    with pytest.raises(GateCoverageContractError):
        GateExecutionReceipt.from_mapping({**receipt.to_dict(), "extra": True})

    decision = _decision(manifest, (receipt,))
    with pytest.raises(GateCoverageContractError):
        replace(decision, result="INVALID")
    with pytest.raises(GateCoverageContractError):
        replace(decision, result="PASS", failure_codes=("AQ6_INVALID_INPUT",))
    with pytest.raises(GateCoverageContractError):
        replace(decision, decision_digest=("0" * 63) + "z")
    with pytest.raises(GateCoverageContractError):
        replace(decision, decision_digest="0" * 64)
    with pytest.raises(TypeError):
        GateCoverageDecision.from_mapping(None)
    with pytest.raises(GateCoverageContractError):
        GateCoverageDecision.from_mapping({**decision.to_dict(), "extra": True})
    invalid_compliant = decision.to_dict()
    invalid_compliant["compliant"] = False
    with pytest.raises(GateCoverageContractError):
        GateCoverageDecision.from_mapping(invalid_compliant)


def test_identity_scope_and_receipt_container_edges_fail_closed():
    manifest = _manifest()
    receipt = _receipt(manifest)
    for field, value, code in (
        ("current_repository", "Other/Repository", "AQ6_SOURCE_BINDING_MISMATCH"),
        ("current_source_ref", "other-source", "AQ6_SOURCE_BINDING_MISMATCH"),
        ("current_candidate_sha", STALE, "AQ6_CANDIDATE_BINDING_MISMATCH"),
        ("current_tree_sha", STALE, "AQ6_TREE_BINDING_MISMATCH"),
        ("current_work_item_ref", "OTHER_WORK_ITEM", "AQ6_INVALID_INPUT"),
    ):
        decision = _decision(manifest, (receipt,), **{field: value})
        assert code in decision.failure_codes

    mapped = _decision(manifest, {"receipts": [receipt.to_dict()]})
    assert mapped.result == "PASS"
    with pytest.raises(TypeError):
        evaluate_gate_coverage(manifest, "not-executions")

    duplicate = _decision(
        manifest,
        (receipt, replace(receipt, execution_id="execution-aq6-duplicate")),
    )
    assert "AQ6_DUPLICATE_GATE_EXECUTION" in duplicate.failure_codes

    unknown_gate = _decision(
        manifest,
        (replace(receipt, gate_id="unknown-gate"),),
    )
    assert "AQ6_EXECUTION_SCOPE_EXCEEDED" in unknown_gate.failure_codes

    missing_risk = _decision(
        _manifest(
            risks=("MULTI_TENANT",),
            declaration=_declaration(risks=("PROVENANCE",)),
        ),
        (receipt,),
    )
    assert "AQ6_REQUIRED_RISK_UNCOVERED" in missing_risk.failure_codes

    unknown_test = _decision(manifest, (receipt,), available_test_ids=("other-test",))
    assert "AQ6_UNKNOWN_TEST_REFERENCE" in unknown_test.failure_codes

    values = []
    gate_coverage._add(values, "DUPLICATE", "DUPLICATE")
    assert values == ["DUPLICATE"]


def test_machine_contract_rejects_non_mapping():
    with pytest.raises(TypeError):
        validate_gate_coverage_contract(None)
