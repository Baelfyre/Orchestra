from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.domain.adaptive import (
    EvidenceReceipt,
    EvidenceSlot,
    build_assurance_manifest,
    build_evidence_receipt,
    build_routing_receipt,
    profile_risk,
)
from orchestra_runtime.domain.adaptive.assurance_manifest import (
    AssuranceManifestContractError,
    FAIL_PASS_NONZERO_EXIT,
)
from orchestra_runtime.domain.adaptive import qa_compliance as aq5
from orchestra_runtime.domain.adaptive.qa_compliance import (
    AQ5_AUTHORITY_MODEL,
    AQ5_CONTRACT_SCHEMA_VERSION,
    AQ5_DECISION_SCHEMA_VERSION,
    FAIL_CHANGED_PATH_OMITTED,
    FAIL_CONCURRENCY_NO_EVIDENCE,
    FAIL_GATE_EVIDENCE_MISSING,
    FAIL_OLD_CANDIDATE_SHA,
    FAIL_PASS_NONZERO_EXIT_CLAIM,
    FAIL_POLICY_SELF_MODIFICATION,
    FAIL_PRODUCT_COMPLETE_WITHOUT_CALLER,
    FAIL_REQUIRED_ASSURANCE_MISSING,
    FAIL_RUNTIME_ONLY_OPENAPI,
    FAIL_SECURITY_NO_EVIDENCE,
    FAIL_SEMANTIC_RISK_UNDECLARED,
    FAIL_SOURCE_BINDING,
    FAIL_TEST_DOES_NOT_REACH_CHANGED_CODE,
    FAIL_TREE_BINDING,
    FAIL_UNEXECUTED_TEST_CLAIM,
    FAIL_AQ4_INVALID,
    FAIL_COMPLETION_SCOPE,
    QaComplianceContractError,
    QaComplianceDecision,
    assert_qa_compliance,
    evaluate_qa_compliance,
    validate_qa_compliance_contract,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq5-qa-compliance.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "qa-compliance.v1.schema.json"
SOURCE = "orchestra:2fb6a0a8b1d4a207742c9daaa1f5cbf0e87305de"
CANDIDATE = "a" * 40
TREE = "b" * 40
OTHER_CANDIDATE = "c" * 40
OTHER_TREE = "d" * 40
GENERATED = "2026-09-08T14:00:00+08:00"
OBSERVED = "2026-09-08T14:01:00+08:00"


def _profile(
    *,
    quality_dimensions: tuple[str, ...] = (),
    risk_characteristics: tuple[str, ...] = (),
    invariants: tuple[str, ...] = (),
    protected_gates: tuple[str, ...] = (),
):
    return profile_risk(
        development_mode="SPEC_FIRST",
        material_behavior="repository QA compliance evidence evaluation",
        authority_boundary=("IMPLEMENTATION",),
        changed_domains=("domain",),
        changed_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        quality_dimensions=quality_dimensions,
        risk_characteristics=risk_characteristics,
        invariants=invariants,
        protected_gates=protected_gates,
    )


def _layer_for(assurance_class: str) -> tuple[str, str]:
    if assurance_class == "SECURITY_ASSURANCE":
        return "SECURITY", "SECURITY"
    if assurance_class == "CONCURRENCY_ASSURANCE":
        return "CONCURRENCY", "CONCURRENCY"
    if assurance_class == "PROVENANCE_ASSURANCE":
        return "PROVENANCE", "CANONICAL"
    if assurance_class == "INDEPENDENT_QA":
        return "CONTRACT", "CONTRACT"
    return "CONTRACT", "CONTRACT"


def _slots(
    required_assurance: tuple[str, ...],
    *,
    risks: tuple[str, ...] = (),
    invariants: tuple[str, ...] = (),
    layer_overrides: dict[str, str] | None = None,
    scope_overrides: dict[str, str] | None = None,
    extra_slots: tuple[EvidenceSlot, ...] = (),
) -> tuple[EvidenceSlot, ...]:
    layer_overrides = layer_overrides or {}
    scope_overrides = scope_overrides or {}
    slots = [
        EvidenceSlot(
            slot_id=f"gate-{index}-{assurance.casefold()}",
            assurance_class=assurance,
            required_layer=layer_overrides.get(assurance, _layer_for(assurance)[0]),
            required_scope=scope_overrides.get(assurance, _layer_for(assurance)[1]),
            required_validator="overseer",
            required_source_truth="OBSERVED",
            required_provenance="AUTHORITATIVE",
            covered_risks=risks,
            covered_invariants=invariants,
            independence_required=assurance == "INDEPENDENT_QA",
        )
        for index, assurance in enumerate(required_assurance)
    ]
    return tuple(slots) + extra_slots


def _manifest(
    profile=None,
    *,
    layer_overrides: dict[str, str] | None = None,
    scope_overrides: dict[str, str] | None = None,
    extra_slots: tuple[EvidenceSlot, ...] = (),
    protected_gates: tuple[str, ...] | None = None,
):
    profile = profile or _profile()
    routing = build_routing_receipt(profile, source_identities=(SOURCE,))
    protected = tuple(profile.protected_gates) if protected_gates is None else protected_gates
    return build_assurance_manifest(
        profile=profile,
        receipt=routing,
        manifest_id="manifest-aq5",
        repository="Baelfyre/Orchestra",
        source_ref=SOURCE,
        candidate_sha=CANDIDATE,
        tree_sha=TREE,
        work_item_ref="AQ5",
        change_class="AQ5_IMPLEMENTATION",
        completion_target="AQ5_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW",
        required_evidence_slots=_slots(
            tuple(routing.required_assurance),
            risks=tuple(profile.risk_characteristics),
            invariants=tuple(profile.invariants),
            layer_overrides=layer_overrides,
            scope_overrides=scope_overrides,
            extra_slots=extra_slots,
        ),
        selected_specialists=tuple(routing.selected_specialists),
        required_assurance=tuple(routing.required_assurance),
        generated_at=GENERATED,
        protected_gates=protected,
    )


def _receipt(manifest, *, gate_id: str, **overrides: object):
    values: dict[str, object] = {
        "receipt_id": f"receipt-{gate_id}",
        "gate_id": gate_id,
        "gate_type": "TEST",
        "command_or_workflow": "python -B -m pytest",
        "result": "PASS",
        "observed_at": OBSERVED,
        "producer": "ponytail",
        "exit_code": 0,
        "logical_identity": f"logical-{gate_id}",
    }
    values.update(overrides)
    return build_evidence_receipt(manifest, **values)


def _receipts(manifest):
    return tuple(
        _receipt(manifest, gate_id=slot.slot_id)
        for slot in manifest.required_evidence_slots
    )


def _decision(manifest, receipts, **kwargs):
    kwargs.setdefault("changed_paths", ())
    kwargs.setdefault("declared_paths", ())
    kwargs.setdefault("evaluated_at", OBSERVED)
    return evaluate_qa_compliance(manifest, receipts, **kwargs)


def test_positive_decision_is_source_bound_and_non_authorizing():
    manifest = _manifest(_profile(invariants=("FAILED_VALIDATION_MUST_NOT_BECOME_PASS",)))
    decision = _decision(manifest, _receipts(manifest))
    assert decision.result == "PASS"
    assert decision.compliant is True
    assert decision.failure_codes == ()
    assert decision.candidate_sha == CANDIDATE
    assert decision.tree_sha == TREE
    assert decision.to_dict()["compliant"] is True


def test_contract_runtime_parity_is_strict():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert validate_qa_compliance_contract(contract) is contract
    assert contract["schema_version"] == AQ5_CONTRACT_SCHEMA_VERSION
    assert contract["authority_model"] == AQ5_AUTHORITY_MODEL
    assert contract["decision_schema_version"] == AQ5_DECISION_SCHEMA_VERSION
    with pytest.raises(QaComplianceContractError):
        validate_qa_compliance_contract({**contract, "authority_model": "AUTHORIZING"})
    with pytest.raises(QaComplianceContractError):
        validate_qa_compliance_contract({**contract, "unexpected": True})


def test_decision_schema_is_strict_and_accepts_runtime_output():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    manifest = _manifest(_profile())
    decision = _decision(manifest, _receipts(manifest))
    jsonschema.Draft202012Validator(schema).validate(decision.to_dict())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate({**decision.to_dict(), "extra": True})


def test_security_sensitive_change_without_security_layer_fails():
    manifest = _manifest(
        _profile(quality_dimensions=("SECURITY",), risk_characteristics=("AUTHORIZATION",)),
        layer_overrides={"SECURITY_ASSURANCE": "CONTRACT"},
    )
    decision = _decision(manifest, _receipts(manifest))
    assert decision.result == "FAIL"
    assert FAIL_SECURITY_NO_EVIDENCE in decision.failure_codes


def test_concurrency_change_without_concurrency_layer_fails():
    manifest = _manifest(
        _profile(risk_characteristics=("CONCURRENCY",)),
        layer_overrides={"CONCURRENCY_ASSURANCE": "CONTRACT"},
    )
    decision = _decision(manifest, _receipts(manifest))
    assert decision.result == "FAIL"
    assert FAIL_CONCURRENCY_NO_EVIDENCE in decision.failure_codes


def test_runtime_claim_needs_http_and_runtime_evidence():
    manifest = _manifest(
        _profile(quality_dimensions=("FUNCTIONAL_SUITABILITY",)),
        layer_overrides={"FUNCTIONAL_ASSURANCE": "HTTP", "INDEPENDENT_QA": "HTTP"},
    )
    decision = _decision(manifest, _receipts(manifest), completion_state="RUNTIME_VERIFIED")
    assert decision.result == "FAIL"
    assert FAIL_RUNTIME_ONLY_OPENAPI in decision.failure_codes


def test_product_complete_needs_caller_and_integration_evidence():
    manifest = _manifest(_profile())
    decision = _decision(manifest, _receipts(manifest), completion_state="PRODUCT_COMPLETE")
    assert decision.result == "FAIL"
    assert FAIL_PRODUCT_COMPLETE_WITHOUT_CALLER in decision.failure_codes


def test_pass_with_nonzero_exit_is_rejected_and_preserved():
    manifest = _manifest(_profile())
    receipts = list(_receipts(manifest))
    tampered = receipts[0].to_dict()
    tampered["exit_code"] = 1
    tampered["evidence_digest"] = ""
    decision = _decision(manifest, [tampered])
    assert decision.result == "FAIL"
    assert FAIL_PASS_NONZERO_EXIT_CLAIM in decision.failure_codes
    assert FAIL_PASS_NONZERO_EXIT in decision.failure_codes


def test_old_candidate_sha_is_rejected():
    manifest = _manifest(_profile())
    decision = _decision(
        manifest,
        _receipts(manifest),
        current_candidate_sha=OTHER_CANDIDATE,
    )
    assert decision.result == "FAIL"
    assert FAIL_OLD_CANDIDATE_SHA in decision.failure_codes


def test_required_test_claim_without_execution_fails():
    manifest = _manifest(_profile())
    decision = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        declared_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        test_claimed=True,
    )
    assert decision.result == "FAIL"
    assert FAIL_UNEXECUTED_TEST_CLAIM in decision.failure_codes


def test_executed_test_that_misses_changed_code_fails():
    manifest = _manifest(_profile())
    decision = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        declared_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        executed_test_ids=("aq5-runtime",),
        test_coverage={"aq5-runtime": ("tests/runtime/test_adaptive_assurance_aq5.py",)},
    )
    assert decision.result == "FAIL"
    assert FAIL_TEST_DOES_NOT_REACH_CHANGED_CODE in decision.failure_codes


def test_changed_path_omitted_from_declaration_fails():
    manifest = _manifest(_profile())
    decision = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        declared_paths=(),
    )
    assert decision.result == "FAIL"
    assert FAIL_CHANGED_PATH_OMITTED in decision.failure_codes


def test_policy_self_modification_fails_closed():
    manifest = _manifest(_profile())
    decision = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=("machine/governance/policy.json",),
        declared_paths=("machine/governance/policy.json",),
        policy_self_modification=True,
    )
    assert decision.result == "FAIL"
    assert FAIL_POLICY_SELF_MODIFICATION in decision.failure_codes


def test_undeclared_semantic_risk_fails():
    manifest = _manifest(_profile())
    decision = _decision(manifest, _receipts(manifest), semantic_risks=("SECURITY",))
    assert decision.result == "FAIL"
    assert FAIL_SEMANTIC_RISK_UNDECLARED in decision.failure_codes


def test_explicit_protected_slot_needs_a_pass_receipt():
    profile = _profile()
    manifest = _manifest(profile)
    protected_slot = manifest.required_evidence_slots[0].slot_id
    manifest = _manifest(profile, protected_gates=(protected_slot,))
    receipts = tuple(
        receipt for receipt in _receipts(manifest) if receipt.gate_id != protected_slot
    )
    decision = _decision(manifest, receipts)
    assert decision.result == "FAIL"
    assert FAIL_GATE_EVIDENCE_MISSING in decision.failure_codes


def test_receipt_order_does_not_change_canonical_decision():
    manifest = _manifest(_profile(quality_dimensions=("PROVENANCE",), risk_characteristics=("PROVENANCE",)))
    receipts = _receipts(manifest)
    first = _decision(manifest, receipts, semantic_risks=("PROVENANCE",))
    second = _decision(manifest, tuple(reversed(receipts)), semantic_risks=("PROVENANCE",))
    assert first.to_dict() == second.to_dict()


def test_decision_mapping_rejects_tampering_and_unknown_fields():
    manifest = _manifest(_profile())
    decision = _decision(manifest, _receipts(manifest))
    from orchestra_runtime.domain.adaptive.qa_compliance import QaComplianceDecision

    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping({**decision.to_dict(), "compliant": False})
    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping({**decision.to_dict(), "extra": True})


def test_stale_receipt_candidate_is_rejected():
    manifest = _manifest(_profile())
    receipt = _receipts(manifest)[0].to_dict()
    receipt["candidate_sha"] = OTHER_CANDIDATE
    receipt["evidence_digest"] = ""
    decision = _decision(manifest, [receipt])
    assert decision.result == "FAIL"
    assert "AQ4-N4_RECEIPT_CANDIDATE_MISMATCH" in decision.failure_codes
    assert FAIL_OLD_CANDIDATE_SHA in decision.failure_codes


def test_mapping_inputs_aliases_and_source_tree_guards():
    manifest = _manifest(_profile())
    receipts = _receipts(manifest)
    mapped = _decision(
        manifest.to_dict(),
        {"receipts": [receipt.to_dict() for receipt in receipts]},
        actual_changed_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        manifest_declared_paths=("orchestra_runtime/domain/adaptive/qa_compliance.py",),
        claimed_risks=(),
    )
    assert mapped.result == "PASS"
    single = _decision(manifest, receipts[0].to_dict())
    assert single.result == "PASS"
    source_mismatch = _decision(manifest, receipts, current_source_ref="orchestra:other")
    tree_mismatch = _decision(manifest, receipts, current_tree_sha=OTHER_TREE)
    assert FAIL_SOURCE_BINDING in source_mismatch.failure_codes
    assert FAIL_TREE_BINDING in tree_mismatch.failure_codes
    invalid_boundary = _decision(manifest, receipts, current_authority_boundary=123)
    assert FAIL_AQ4_INVALID in invalid_boundary.failure_codes


def test_evidence_and_input_exceptions_fail_closed(monkeypatch):
    manifest = _manifest(_profile())
    no_receipts = _decision(manifest, None)
    assert FAIL_AQ4_INVALID in no_receipts.failure_codes

    def raise_aq4(*args, **kwargs):
        raise AssuranceManifestContractError("AQ4_TEST_FAILURE")

    monkeypatch.setattr(aq5, "reconcile_manifest_evidence", raise_aq4)
    decision = _decision(manifest, _receipts(manifest))
    assert "AQ4_TEST_FAILURE" in decision.failure_codes

    def raise_type_error(*args, **kwargs):
        raise TypeError("reconciliation type failure")

    monkeypatch.setattr(aq5, "reconcile_manifest_evidence", raise_type_error)
    type_failure = _decision(manifest, _receipts(manifest))
    assert FAIL_AQ4_INVALID in type_failure.failure_codes

    with pytest.raises(TypeError):
        evaluate_qa_compliance("not-a-manifest", ())


@pytest.mark.parametrize(
    "operation",
    (
        lambda: aq5._text("", "field"),
        lambda: aq5._sha("z" * 40, "sha"),
        lambda: aq5._sha256("bad"),
        lambda: aq5._timestamp("not-a-date", "time"),
        lambda: aq5._timestamp("2026-09-08T14:00:00", "time"),
        lambda: aq5._values("not-iterable", "values"),
        lambda: aq5._values(123, "values"),
        lambda: aq5._values(("duplicate", "duplicate"), "values"),
        lambda: aq5._paths(("/absolute.py",), "paths"),
        lambda: aq5._paths(("C:/absolute.py",), "paths"),
        lambda: aq5._paths(("./relative.py",), "paths"),
        lambda: aq5._paths(("a/../b.py",), "paths"),
        lambda: aq5._paths(("a\\b.py", "a/b.py"), "paths"),
        lambda: aq5._assurance(("UNKNOWN_ASSURANCE",), "assurance"),
    ),
)
def test_normalizers_fail_closed(operation):
    with pytest.raises(QaComplianceContractError):
        operation()


def test_normalizer_and_mapping_success_edges():
    assert aq5._text(" value ", "field") == "value"
    assert aq5._sha(CANDIDATE.upper(), "sha") == CANDIDATE
    assert aq5._timestamp(OBSERVED, "time") == OBSERVED
    assert aq5._values(("b", "a"), "values") == ("a", "b")
    assert aq5._paths(("a\\b.py",), "paths") == ("a/b.py",)
    assert aq5._assurance(("INDEPENDENT_QA",), "assurance") == ("INDEPENDENT_QA",)
    assert aq5._risk_assurance("PROVENANCE") == "PROVENANCE_ASSURANCE"
    assert aq5._risk_assurance("PROVENANCE") == aq5._risk_assurance("PROVENANCE")
    assert aq5._risk_assurance("NOT_A_RISK") is None
    assert aq5._is_policy_path("machine/governance/policy.json") is True
    assert aq5._is_policy_path("docs/notes.md") is False


def test_scope_completion_runtime_and_test_claim_variants():
    manifest = _manifest(_profile())
    ten_paths = tuple(f"path-{index}.py" for index in range(10))
    oversized = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=ten_paths,
        declared_paths=ten_paths,
    )
    assert aq5.FAIL_SCOPE_LIMIT in oversized.failure_codes

    invalid_state = _decision(manifest, _receipts(manifest), completion_state="NOT_A_STATE")
    assert FAIL_COMPLETION_SCOPE in invalid_state.failure_codes

    runtime_manifest = _manifest(
        _profile(quality_dimensions=("FUNCTIONAL_SUITABILITY",)),
        layer_overrides={"FUNCTIONAL_ASSURANCE": "HTTP", "INDEPENDENT_QA": "RUNTIME"},
    )
    runtime_receipts = _receipts(runtime_manifest)
    runtime_pass = _decision(
        runtime_manifest,
        runtime_receipts,
        completion_state="RUNTIME_VERIFIED",
        runtime_claimed=True,
    )
    assert runtime_pass.result == "PASS"

    changed = "orchestra_runtime/domain/adaptive/qa_compliance.py"
    covered = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=(changed,),
        declared_paths=(changed,),
        executed_test_ids=("aq5-runtime",),
        test_coverage={"aq5-runtime": (changed,)},
        test_claimed=True,
    )
    assert covered.result == "PASS"
    missing_id = _decision(
        manifest,
        _receipts(manifest),
        executed_test_ids=("missing",),
        test_coverage={"known": ()},
    )
    invalid_coverage = _decision(
        manifest,
        _receipts(manifest),
        executed_test_ids=("bad",),
        test_coverage={"bad": None},
    )
    assert FAIL_UNEXECUTED_TEST_CLAIM in missing_id.failure_codes
    assert FAIL_UNEXECUTED_TEST_CLAIM in invalid_coverage.failure_codes
    policy_prefix = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=(changed,),
        declared_paths=(changed,),
        policy_paths=("orchestra_runtime",),
    )
    assert FAIL_POLICY_SELF_MODIFICATION in policy_prefix.failure_codes

    runtime_failure = _decision(manifest, _receipts(manifest), runtime_claimed=True)
    assert FAIL_RUNTIME_ONLY_OPENAPI in runtime_failure.failure_codes
    unit_claim = _decision(manifest, _receipts(manifest), completion_state="UNIT_VERIFIED")
    assert FAIL_COMPLETION_SCOPE in unit_claim.failure_codes
    invalid_flags = _decision(
        manifest,
        _receipts(manifest),
        runtime_claimed=1,
        test_claimed=1,
        policy_self_modification=1,
    )
    assert aq5.FAIL_INVALID_INPUT in invalid_flags.failure_codes
    assert aq5.FAIL_POLICY_INPUT_INVALID in invalid_flags.failure_codes


def test_assurance_presence_and_provenance_layer_guards():
    functional = _manifest(_profile(quality_dimensions=("FUNCTIONAL_SUITABILITY",)))
    removed = replace(
        functional,
        required_assurance=("INDEPENDENT_QA",),
        manifest_digest="",
    )
    not_required = _decision(
        removed,
        _receipts(removed),
        semantic_risks=("FUNCTIONAL_SUITABILITY",),
    )
    assert FAIL_REQUIRED_ASSURANCE_MISSING in not_required.failure_codes

    functional_receipt = next(
        receipt
        for receipt in _receipts(functional)
        if receipt.gate_id == "gate-0-functional_assurance"
    )
    missing_receipt = _decision(
        functional,
        tuple(receipt for receipt in _receipts(functional) if receipt != functional_receipt),
        semantic_risks=("FUNCTIONAL_SUITABILITY",),
    )
    assert FAIL_REQUIRED_ASSURANCE_MISSING in missing_receipt.failure_codes

    provenance = _manifest(
        _profile(quality_dimensions=("PROVENANCE",), risk_characteristics=("PROVENANCE",)),
        layer_overrides={"PROVENANCE_ASSURANCE": "CONTRACT"},
    )
    provenance_missing = _decision(
        provenance,
        _receipts(provenance),
        semantic_risks=("PROVENANCE",),
    )
    assert FAIL_REQUIRED_ASSURANCE_MISSING in provenance_missing.failure_codes

    protected = functional.required_evidence_slots[0].slot_id
    assert _decision(functional, _receipts(functional), protected_gate_ids=(protected,)).result == "PASS"


def test_validate_alias_and_decision_integrity_boundaries():
    manifest = _manifest(_profile())
    receipts = _receipts(manifest)
    from orchestra_runtime.domain.adaptive.qa_compliance import validate_qa_compliance

    assert validate_qa_compliance(manifest, receipts, evaluated_at=OBSERVED).result == "PASS"


def test_product_complete_positive_and_protected_unknown_gate():
    profile = _profile(quality_dimensions=("FUNCTIONAL_SUITABILITY",))
    completion_slot = EvidenceSlot(
        slot_id="gate-completion-state",
        assurance_class="INDEPENDENT_QA",
        required_layer="COMPLETION_STATE",
        required_scope="COMPLETION",
        required_validator="overseer",
        required_source_truth="OBSERVED",
        required_provenance="AUTHORITATIVE",
        covered_risks=(),
        covered_invariants=(),
        independence_required=False,
    )
    manifest = _manifest(
        profile,
        layer_overrides={"FUNCTIONAL_ASSURANCE": "INTEGRATION", "INDEPENDENT_QA": "INTEGRATION"},
        extra_slots=(completion_slot,),
    )
    receipts = _receipts(manifest)
    product = _decision(
        manifest,
        receipts,
        completion_state="PRODUCT_COMPLETE",
        caller_authority_ref="human-review-1",
        integration_evidence_ids=(receipts[0].receipt_id,),
        completion_evidence_ids=(receipts[-1].receipt_id,),
    )
    assert product.result == "PASS"
    unknown_gate = _decision(manifest, receipts, protected_gate_ids=("unknown-gate",))
    assert FAIL_GATE_EVIDENCE_MISSING in unknown_gate.failure_codes


def test_invalid_receipt_metadata_and_decision_assertions():
    manifest = _manifest(_profile())
    raw = _receipts(manifest)[0].to_dict()
    raw.pop("exit_code")
    raw["evidence_digest"] = ""
    invalid = _decision(manifest, [raw])
    assert FAIL_UNEXECUTED_TEST_CLAIM in invalid.failure_codes

    good = _decision(manifest, _receipts(manifest))
    assert QaComplianceDecision.from_mapping(good.to_dict()).to_dict() == good.to_dict()
    assert assert_qa_compliance(good) is good
    assert assert_qa_compliance(manifest, _receipts(manifest)).result == "PASS"
    with pytest.raises(QaComplianceContractError):
        assert_qa_compliance(invalid)
    with pytest.raises(QaComplianceContractError):
        assert_qa_compliance(manifest)
    with pytest.raises(TypeError):
        QaComplianceDecision.from_mapping([])


def test_decision_constructor_rejects_each_integrity_boundary():
    manifest = _manifest(_profile())
    good = _decision(manifest, _receipts(manifest)).to_dict()

    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping({**good, "schema_version": "wrong"})
    bad_result = {**good, "result": "UNKNOWN", "compliant": False}
    bad_result["decision_digest"] = aq5._digest(
        {key: value for key, value in bad_result.items() if key != "decision_digest"}
    )
    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping(bad_result)
    bad_state = {**good, "completion_state": "UNKNOWN", "compliant": True}
    bad_state["decision_digest"] = aq5._digest(
        {key: value for key, value in bad_state.items() if key != "decision_digest"}
    )
    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping(bad_state)
    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping({**good, "decision_digest": "0" * 64})

    failed = _decision(
        manifest,
        _receipts(manifest),
        changed_paths=("a.py",),
        declared_paths=(),
    ).to_dict()
    failed["result"] = "PASS"
    failed["compliant"] = True
    failed["decision_digest"] = aq5._digest(
        {key: value for key, value in failed.items() if key != "decision_digest"}
    )
    with pytest.raises(QaComplianceContractError):
        QaComplianceDecision.from_mapping(failed)


def test_contract_validator_type_boundary():
    with pytest.raises(TypeError):
        validate_qa_compliance_contract([])
