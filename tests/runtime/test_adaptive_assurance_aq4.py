from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.domain.adaptive import (
    ALLOWED_RECEIPT_RESULTS,
    ASSURANCE_MANIFEST_FIELDS,
    ASSURANCE_ORDER,
    AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION,
    AQ4_AUTHORITY_MODEL,
    AQ4_CONTRACT_SCHEMA_VERSION,
    AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION,
    AQ4_REQUIRED_NEGATIVE_TESTS,
    AQ4_REQUIRED_PROPERTY_TESTS,
    CANONICAL_SPECIALIST_ORDER,
    COMPLETION_STATES,
    DEVELOPMENT_MODES,
    EVIDENCE_LAYERS,
    EVIDENCE_RECEIPT_FIELDS,
    EVIDENCE_SCOPES,
    EVIDENCE_SLOT_FIELDS,
    MAX_FINAL_PR_PATHS,
    OPTIONAL_RECEIPT_IDENTITY_FIELDS,
    PROVENANCE_QUALIFICATIONS,
    SOURCE_TRUTH_LABELS,
    AssuranceManifest,
    AssuranceManifestContractError,
    EvidenceReceipt,
    EvidenceSlot,
    build_assurance_manifest,
    build_evidence_receipt,
    build_routing_receipt,
    evaluate_manifest_sufficiency,
    profile_risk,
    reconcile_manifest_evidence,
    validate_assurance_contract,
    validate_assurance_manifest,
    validate_evidence_receipt,
)
from orchestra_runtime.domain.adaptive import assurance_manifest as aq4
from orchestra_runtime.domain.adaptive.assurance_manifest import (
    FAIL_AUTHORITY_EXPANSION,
    FAIL_BROAD_COVERAGE,
    FAIL_CALLER_AUTHORED_PROVENANCE,
    FAIL_CONTRADICTORY_EVIDENCE,
    FAIL_DUPLICATE_NOT_ADDITIVE,
    FAIL_INDEPENDENT_EVIDENCE_REUSE,
    FAIL_INVALID_EXECUTION_METADATA,
    FAIL_LOWER_EVIDENCE_LAYER,
    FAIL_PASS_NONZERO_EXIT,
    FAIL_RECEIPT_CANDIDATE_BINDING,
    FAIL_RECEIPT_TREE_BINDING,
    FAIL_REQUIRED_MANIFEST_FIELD,
    FAIL_REQUIRED_RECEIPT_FIELD,
    FAIL_REQUIRED_SLOT_UNSATISFIED,
    FAIL_SEMANTIC_DRIFT,
    FAIL_STALE_EVIDENCE,
    FAIL_WEAKENED_PREDECESSOR_ASSURANCE,
    FAIL_WRONG_SOURCE,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq4-assurance-manifests-receipts.v1.json"
MANIFEST_SCHEMA_PATH = ROOT / "machine" / "schemas" / "assurance-manifest.v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "machine" / "schemas" / "evidence-receipt.v1.schema.json"
SOURCE = "orchestra:2fb6a0a8b1d4a207742c9daaa1f5cbf0e87305de"
CANDIDATE = "a" * 40
TREE = "b" * 40
OTHER_CANDIDATE = "c" * 40
OTHER_TREE = "d" * 40
GENERATED = "2026-09-08T14:00:00+08:00"
OBSERVED = "2026-09-08T14:01:00+08:00"


def _profile(**overrides: object):
    values: dict[str, object] = {
        "development_mode": "SPEC_FIRST",
        "material_behavior": "AQ4 assurance manifest and evidence receipt implementation",
        "authority_boundary": ("IMPLEMENTATION",),
        "changed_domains": (),
        "changed_paths": (),
        "quality_dimensions": (),
        "risk_characteristics": (),
        "invariants": (),
        "protected_gates": (),
    }
    values.update(overrides)
    return profile_risk(**values)


def _material_profile():
    return _profile(
        material_behavior="AQ4 source provenance and authority binding",
        changed_domains=("domain",),
        changed_paths=("orchestra_runtime/domain/adaptive/assurance_manifest.py",),
        quality_dimensions=("PROVENANCE",),
        risk_characteristics=("PROVENANCE",),
        invariants=("CLIENT_MUST_NOT_AUTHOR_AUTHORITATIVE_PROVENANCE",),
        protected_gates=("HUMAN_REVIEW",),
    )


def _routing(profile):
    return build_routing_receipt(profile, source_identities=(SOURCE,))


def _layer_for(assurance_class: str) -> tuple[str, str]:
    if assurance_class == "ADVERSARIAL_ASSURANCE":
        return "ADVERSARIAL", "ADVERSARIAL"
    if assurance_class == "PROVENANCE_ASSURANCE":
        return "PROVENANCE", "CANONICAL"
    if assurance_class == "SECURITY_ASSURANCE":
        return "SECURITY", "SECURITY"
    return "CONTRACT", "CONTRACT"


def _slots(
    required_assurance: tuple[str, ...],
    *,
    risks: tuple[str, ...] = (),
    invariants: tuple[str, ...] = (),
    layer_overrides: dict[str, str] | None = None,
    scope_overrides: dict[str, str] | None = None,
) -> tuple[EvidenceSlot, ...]:
    layer_overrides = layer_overrides or {}
    scope_overrides = scope_overrides or {}
    return tuple(
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
    )


def _manifest(
    profile=None,
    *,
    required_assurance: tuple[str, ...] | None = None,
    layer_overrides: dict[str, str] | None = None,
    scope_overrides: dict[str, str] | None = None,
):
    profile = profile or _profile()
    routing = _routing(profile)
    required = required_assurance or tuple(routing.required_assurance)
    return build_assurance_manifest(
        profile=profile,
        receipt=routing,
        manifest_id="manifest-aq4",
        repository="Baelfyre/Orchestra",
        source_ref=SOURCE,
        candidate_sha=CANDIDATE,
        tree_sha=TREE,
        work_item_ref="AQ4",
        change_class="AQ4_IMPLEMENTATION",
        completion_target="AQ4_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW",
        required_evidence_slots=_slots(
            required,
            risks=tuple(profile.risk_characteristics),
            invariants=tuple(profile.invariants),
            layer_overrides=layer_overrides,
            scope_overrides=scope_overrides,
        ),
        selected_specialists=tuple(routing.selected_specialists),
        required_assurance=required,
        generated_at=GENERATED,
    )


def _receipt(manifest, *, gate_id: str | None = None, **overrides: object):
    gate_id = gate_id or manifest.required_evidence_slots[0].slot_id
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


def _with_mapping_value(value, field: str, replacement):
    data = value.to_dict()
    data[field] = replacement
    if isinstance(value, AssuranceManifest):
        data["manifest_digest"] = ""
        return AssuranceManifest.from_mapping(data)
    data["evidence_digest"] = ""
    return EvidenceReceipt.from_mapping(data)


def _error_code(error: pytest.ExceptionInfo[Exception]) -> str:
    assert isinstance(error.value, AssuranceManifestContractError)
    return error.value.code


def test_contract_runtime_parity_and_schema_fixtures():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    validate_assurance_contract(contract)
    assert contract["schema_version"] == AQ4_CONTRACT_SCHEMA_VERSION
    assert contract["authority_model"] == AQ4_AUTHORITY_MODEL
    assert contract["manifest_fields"] == list(ASSURANCE_MANIFEST_FIELDS)
    assert contract["evidence_slot_fields"] == list(EVIDENCE_SLOT_FIELDS)
    assert contract["receipt_fields"] == list(EVIDENCE_RECEIPT_FIELDS)
    assert contract["optional_receipt_identity_fields"] == list(OPTIONAL_RECEIPT_IDENTITY_FIELDS)
    assert contract["allowed_results"] == list(ALLOWED_RECEIPT_RESULTS)
    assert contract["development_modes"] == list(DEVELOPMENT_MODES)
    assert contract["evidence_layers"] == list(EVIDENCE_LAYERS)
    assert contract["evidence_scopes"] == list(EVIDENCE_SCOPES)
    assert contract["source_truth_labels"] == list(SOURCE_TRUTH_LABELS)
    assert contract["provenance_qualifications"] == list(PROVENANCE_QUALIFICATIONS)
    assert contract["completion_states"] == list(COMPLETION_STATES)
    assert contract["assurance_order"] == list(ASSURANCE_ORDER)
    assert contract["canonical_specialist_order"] == list(CANONICAL_SPECIALIST_ORDER)
    assert contract["required_negative_tests"] == list(AQ4_REQUIRED_NEGATIVE_TESTS)
    assert contract["required_property_tests"] == list(AQ4_REQUIRED_PROPERTY_TESTS)
    assert contract["max_final_pr_paths"] == MAX_FINAL_PR_PATHS
    manifest = _manifest()
    receipt = _receipt(manifest)
    jsonschema.Draft202012Validator(
        json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")),
        format_checker=jsonschema.FormatChecker(),
    ).validate(manifest.to_dict())
    jsonschema.Draft202012Validator(
        json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8")),
        format_checker=jsonschema.FormatChecker(),
    ).validate(receipt.to_dict())
    assert manifest.schema_version == AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION
    assert receipt.schema_version == AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION


def test_contract_semantic_drift_is_rejected():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    drifted = deepcopy(contract)
    drifted["assurance_order"][0] = "DRIFTED_ASSURANCE"
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_contract(drifted)
    assert _error_code(error) == FAIL_SEMANTIC_DRIFT


def test_manifest_and_receipt_digests_are_canonical():
    manifest = _manifest()
    reordered = manifest.to_dict()
    reordered["required_evidence_slots"] = list(reversed(reordered["required_evidence_slots"]))
    reordered["manifest_digest"] = ""
    assert AssuranceManifest.from_mapping(reordered).manifest_digest == manifest.manifest_digest
    receipt = _receipt(manifest)
    changed_order = replace(
        receipt,
        covered_risks=tuple(reversed(receipt.covered_risks)),
        covered_invariants=tuple(reversed(receipt.covered_invariants)),
        evidence_digest="",
    )
    assert changed_order.evidence_digest == receipt.evidence_digest


def test_required_negative_and_property_registries_are_complete():
    assert AQ4_REQUIRED_NEGATIVE_TESTS == tuple(f"AQ4-N{i}" for i in range(1, 19))
    assert AQ4_REQUIRED_PROPERTY_TESTS == (
        "DETERMINISM",
        "ORDER_INVARIANCE",
        "ASSURANCE_MONOTONICITY",
        "AUTHORITY_NON_EXPANSION",
        "IDENTITY_MONOTONICITY",
        "CONTRADICTION_MONOTONICITY",
        "DUPLICATE_NORMALIZATION",
    )


def test_aq4_n1_unknown_assurance_type_rejects():
    values = _manifest().required_evidence_slots[0].to_dict()
    values["assurance_class"] = "UNKNOWN_ASSURANCE"
    with pytest.raises(AssuranceManifestContractError) as error:
        EvidenceSlot.from_mapping(values)
    assert _error_code(error) == "AQ4-N1_UNKNOWN_ASSURANCE_TYPE"
    values = _manifest().to_dict()
    values["required_assurance"] = ["UNKNOWN_ASSURANCE"]
    values["manifest_digest"] = ""
    with pytest.raises(AssuranceManifestContractError) as error:
        AssuranceManifest.from_mapping(values)
    assert _error_code(error) == "AQ4-N1_UNKNOWN_ASSURANCE_TYPE"


def test_aq4_n2_missing_manifest_field_rejects():
    values = _manifest().to_dict()
    values.pop("manifest_id")
    with pytest.raises(AssuranceManifestContractError) as error:
        AssuranceManifest.from_mapping(values)
    assert _error_code(error) == FAIL_REQUIRED_MANIFEST_FIELD


def test_aq4_n3_missing_receipt_field_rejects():
    values = _receipt(_manifest()).to_dict()
    values.pop("validator")
    with pytest.raises(AssuranceManifestContractError) as error:
        EvidenceReceipt.from_mapping(values)
    assert _error_code(error) == FAIL_REQUIRED_RECEIPT_FIELD


def test_aq4_n4_receipt_candidate_mismatch_rejects():
    manifest = _manifest()
    receipt = _with_mapping_value(_receipt(manifest), "candidate_sha", OTHER_CANDIDATE)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_RECEIPT_CANDIDATE_BINDING


def test_aq4_n5_receipt_tree_mismatch_rejects():
    manifest = _manifest()
    receipt = _with_mapping_value(_receipt(manifest), "tree_sha", OTHER_TREE)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_RECEIPT_TREE_BINDING


def test_aq4_n6_pass_with_nonzero_exit_rejects():
    manifest = _manifest()
    with pytest.raises(AssuranceManifestContractError) as error:
        replace(_receipt(manifest), exit_code=1, evidence_digest="")
    assert _error_code(error) == FAIL_PASS_NONZERO_EXIT


def test_aq4_n7_wrong_repository_or_source_rejects():
    manifest = _manifest()
    receipt = _with_mapping_value(_receipt(manifest), "source_ref", "orchestra:other-source")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_WRONG_SOURCE


def test_aq4_n8_stale_freshness_binding_rejects():
    manifest = _manifest()
    receipt = _with_mapping_value(_receipt(manifest), "observed_at", "2026-09-08T13:59:00+08:00")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_STALE_EVIDENCE


def test_aq4_n9_contradictory_logical_evidence_rejects():
    manifest = _manifest()
    slot = manifest.required_evidence_slots[0]
    first = _receipt(manifest, gate_id=slot.slot_id, logical_identity="same-logical")
    second = _receipt(
        manifest,
        gate_id=slot.slot_id,
        receipt_id="receipt-fail",
        logical_identity="same-logical",
        result="FAIL",
        exit_code=None,
    )
    evaluation = reconcile_manifest_evidence(manifest, [first, second])
    assert FAIL_CONTRADICTORY_EVIDENCE in evaluation.failure_codes
    assert not evaluation.sufficient


def test_aq4_n10_logical_evidence_cannot_satisfy_two_independent_slots():
    manifest = _manifest()
    extra_slot = EvidenceSlot(
        slot_id="gate-extra-independent",
        assurance_class="INDEPENDENT_QA",
        required_layer="UNIT",
        required_scope="UNIT",
        required_validator="overseer",
        required_source_truth="OBSERVED",
        required_provenance="AUTHORITATIVE",
        independence_required=True,
    )
    values = manifest.to_dict()
    values["required_evidence_slots"].append(extra_slot.to_dict())
    values["manifest_digest"] = ""
    expanded = AssuranceManifest.from_mapping(values)
    first = _receipt(expanded, gate_id=expanded.required_evidence_slots[0].slot_id, logical_identity="reused")
    second = _receipt(expanded, gate_id="gate-extra-independent", receipt_id="receipt-extra", logical_identity="reused")
    evaluation = reconcile_manifest_evidence(expanded, [first, second])
    assert FAIL_INDEPENDENT_EVIDENCE_REUSE in evaluation.failure_codes
    assert not evaluation.sufficient


def test_aq4_n11_receipt_cannot_claim_broader_coverage():
    manifest = _manifest(_material_profile())
    receipt = _with_mapping_value(_receipt(manifest), "covered_risks", ["PROVENANCE", "AUTHORIZATION"])
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_BROAD_COVERAGE


def test_aq4_n12_lower_layer_cannot_satisfy_higher_slot():
    manifest = _manifest(
        required_assurance=("INDEPENDENT_QA",),
        layer_overrides={"INDEPENDENT_QA": "RUNTIME"},
        scope_overrides={"INDEPENDENT_QA": "RUNTIME"},
    )
    receipt = _with_mapping_value(_receipt(manifest), "evidence_layer", "UNIT")
    receipt = _with_mapping_value(receipt, "evidence_scope", "UNIT")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_LOWER_EVIDENCE_LAYER


def test_aq4_n13_implementer_self_certification_rejects():
    manifest = _manifest()
    receipt = _with_mapping_value(_receipt(manifest), "producer", "overseer")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == "AQ4-N13_IMPLEMENTER_SELF_CERTIFIED"


def test_aq4_n14_caller_authored_authoritative_provenance_rejects():
    manifest = _manifest(required_assurance=("FUNCTIONAL_ASSURANCE", "INDEPENDENT_QA"))
    functional = next(slot for slot in manifest.required_evidence_slots if slot.assurance_class == "FUNCTIONAL_ASSURANCE")
    receipt = _with_mapping_value(_receipt(manifest, gate_id=functional.slot_id), "producer", "caller")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, manifest)
    assert _error_code(error) == FAIL_CALLER_AUTHORED_PROVENANCE


def test_aq4_n15_manifest_cannot_weaken_aq2_or_aq3():
    profile = _material_profile()
    manifest = _manifest(profile)
    values = manifest.to_dict()
    values["required_assurance"] = ["INDEPENDENT_QA"]
    values["manifest_digest"] = ""
    weakened = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(weakened, aq2_profile=profile, aq3_receipt=_routing(profile))
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE


def test_aq4_n16_manifest_authority_boundary_cannot_expand():
    values = _manifest().to_dict()
    values["authority_boundary"] = ["IMPLEMENTATION", "RELEASE"]
    values["manifest_digest"] = ""
    with pytest.raises(AssuranceManifestContractError) as error:
        AssuranceManifest.from_mapping(values)
    assert _error_code(error) == FAIL_AUTHORITY_EXPANSION


def test_aq4_n17_schema_valid_mapping_with_runtime_semantic_drift_rejects():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    drifted = deepcopy(contract)
    drifted["required_property_tests"] = list(drifted["required_property_tests"]) + ["DRIFT"]
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_contract(drifted)
    assert _error_code(error) == FAIL_SEMANTIC_DRIFT


def test_aq4_n18_exact_duplicate_receipt_is_normalized_without_assurance_inflation():
    manifest = _manifest()
    receipt = _receipt(manifest)
    evaluation = reconcile_manifest_evidence(manifest, [receipt, receipt])
    assert evaluation.sufficient
    assert evaluation.assurance_count == 1
    assert evaluation.evidence_count == 1
    assert evaluation.duplicate_receipt_ids == (receipt.receipt_id,)


def test_property_order_invariance_and_determinism():
    manifest = _manifest(required_assurance=("FUNCTIONAL_ASSURANCE", "INDEPENDENT_QA"))
    receipts = [_receipt(manifest, gate_id=slot.slot_id) for slot in manifest.required_evidence_slots]
    forward = reconcile_manifest_evidence(manifest, receipts)
    reverse = reconcile_manifest_evidence(manifest, list(reversed(receipts)))
    assert forward.to_dict() == reverse.to_dict()


def test_property_assurance_monotonicity():
    manifest = _manifest(required_assurance=("FUNCTIONAL_ASSURANCE", "INDEPENDENT_QA"))
    independent = next(slot for slot in manifest.required_evidence_slots if slot.assurance_class == "INDEPENDENT_QA")
    functional = next(slot for slot in manifest.required_evidence_slots if slot.assurance_class == "FUNCTIONAL_ASSURANCE")
    partial = evaluate_manifest_sufficiency(manifest, [_receipt(manifest, gate_id=independent.slot_id)])
    complete = evaluate_manifest_sufficiency(manifest, [_receipt(manifest, gate_id=independent.slot_id), _receipt(manifest, gate_id=functional.slot_id)])
    assert partial.assurance_count == 1
    assert complete.assurance_count == 2
    assert set(partial.satisfied_assurance).issubset(set(complete.satisfied_assurance))


def test_property_authority_non_expansion_and_identity_monotonicity():
    manifest = _manifest()
    receipt = _receipt(manifest)
    baseline = reconcile_manifest_evidence(manifest, [])
    with_receipt = reconcile_manifest_evidence(manifest, [receipt])
    assert manifest.authority_boundary == ("IMPLEMENTATION",)
    assert baseline.manifest_id == with_receipt.manifest_id
    changed = _with_mapping_value(manifest, "candidate_sha", OTHER_CANDIDATE)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, changed)
    assert _error_code(error) == FAIL_RECEIPT_CANDIDATE_BINDING


def test_property_contradiction_monotonicity():
    manifest = _manifest()
    good = _receipt(manifest, logical_identity="logical-stable")
    bad = _receipt(manifest, receipt_id="receipt-conflict", logical_identity="logical-stable", result="FAIL", exit_code=None)
    base = reconcile_manifest_evidence(manifest, [good])
    contradictory = reconcile_manifest_evidence(manifest, [good, bad])
    assert base.sufficient
    assert not contradictory.sufficient
    assert FAIL_CONTRADICTORY_EVIDENCE in contradictory.failure_codes




def test_scalar_normalizers_reject_malformed_values():
    with pytest.raises(TypeError):
        aq4._text(None, "value")
    with pytest.raises(ValueError):
        aq4._text("   ", "value")
    with pytest.raises(ValueError):
        aq4._text("x" * 257, "value")
    with pytest.raises(TypeError):
        aq4._values("value", "values")
    with pytest.raises(TypeError):
        aq4._values(1, "values")
    with pytest.raises(ValueError):
        aq4._values(["x"] * 129, "values")
    with pytest.raises(ValueError):
        aq4._values(["x", "x"], "values")
    with pytest.raises(ValueError):
        aq4._identifiers(("not valid",), "identifiers")
    with pytest.raises(ValueError):
        aq4._one_of("NOPE", ("YES",), "choice")
    with pytest.raises(ValueError):
        aq4._git_sha("bad", "sha")
    with pytest.raises(ValueError):
        aq4._sha256("bad", "digest")
    with pytest.raises(ValueError):
        aq4._timestamp("not-a-date", "timestamp")
    with pytest.raises(ValueError):
        aq4._timestamp("2026-09-08T14:00:00", "timestamp")
    with pytest.raises(ValueError):
        aq4._optional_identity(-1, "identity")
    assert aq4._optional_identity(7, "identity") == 7
    assert aq4._optional_identity("run", "identity") == "run"
    with pytest.raises(TypeError):
        aq4._exact_bool(1, "flag")


def test_slot_and_manifest_shape_guards_are_strict():
    with pytest.raises(TypeError):
        EvidenceSlot.from_mapping([])
    slot_values = _manifest().required_evidence_slots[0].to_dict()
    slot_values.pop("slot_id")
    with pytest.raises(AssuranceManifestContractError) as error:
        EvidenceSlot.from_mapping(slot_values)
    assert _error_code(error) == FAIL_REQUIRED_MANIFEST_FIELD
    slot_values = _manifest().required_evidence_slots[0].to_dict()
    slot_values["unexpected"] = True
    with pytest.raises(AssuranceManifestContractError):
        EvidenceSlot.from_mapping(slot_values)

    with pytest.raises(TypeError):
        AssuranceManifest.from_mapping([])
    with pytest.raises(AssuranceManifestContractError):
        AssuranceManifest.from_mapping({"schema_version": "wrong"})


def test_manifest_integrity_and_slot_guards_are_strict():
    manifest = _manifest()
    assert AssuranceManifest.from_mapping(manifest.to_dict()) == manifest
    with pytest.raises(AssuranceManifestContractError) as error:
        replace(manifest, schema_version="wrong")
    assert _error_code(error) == FAIL_SEMANTIC_DRIFT

    values = manifest.to_dict()
    values["authority_boundary"] = []
    values["manifest_digest"] = ""
    with pytest.raises(ValueError):
        AssuranceManifest.from_mapping(values)

    with pytest.raises(TypeError):
        replace(manifest, required_evidence_slots="bad")
    with pytest.raises(AssuranceManifestContractError) as error:
        replace(manifest, required_evidence_slots=())
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED

    values = manifest.to_dict()
    values["required_evidence_slots"] = [
        values["required_evidence_slots"][0],
        values["required_evidence_slots"][0],
    ]
    values["manifest_digest"] = ""
    with pytest.raises(ValueError):
        AssuranceManifest.from_mapping(values)

    values = manifest.to_dict()
    values["manifest_digest"] = "0" * 64
    with pytest.raises(AssuranceManifestContractError) as error:
        AssuranceManifest.from_mapping(values)
    assert _error_code(error) == aq4.FAIL_INVALID_DIGEST


def test_receipt_integrity_and_metadata_guards_are_strict():
    manifest = _manifest()
    receipt = _receipt(manifest)
    assert EvidenceReceipt.from_mapping(receipt.to_dict()) == receipt
    with pytest.raises(AssuranceManifestContractError) as error:
        replace(receipt, schema_version="wrong")
    assert _error_code(error) == FAIL_STALE_EVIDENCE

    with pytest.raises(AssuranceManifestContractError):
        _receipt(manifest, gate_type="TEST", exit_code=None)
    with pytest.raises(ValueError):
        replace(receipt, exit_code=-1, evidence_digest="")
    with pytest.raises(ValueError):
        replace(receipt, exit_code=True, evidence_digest="")

    values = receipt.to_dict()
    values["evidence_digest"] = "0" * 64
    with pytest.raises(AssuranceManifestContractError) as error:
        EvidenceReceipt.from_mapping(values)
    assert _error_code(error) == aq4.FAIL_INVALID_DIGEST

    with pytest.raises(TypeError):
        EvidenceReceipt.from_mapping([])
    with pytest.raises(AssuranceManifestContractError):
        EvidenceReceipt.from_mapping({"schema_version": "wrong"})

    with_job = _receipt(
        manifest,
        logical_identity=None,
        job_or_check_id="job-1",
    )
    with_command = _receipt(manifest, logical_identity=None)
    assert with_job.logical_identity == f"{with_job.gate_id}:job-1"
    assert with_command.logical_identity == f"{with_command.gate_id}:python -B -m pytest"


def test_manifest_coercion_and_current_identity_guards():
    manifest = _manifest()
    receipt = _receipt(manifest)
    assert validate_assurance_manifest(manifest.to_dict()) == manifest
    assert validate_evidence_receipt(receipt.to_dict(), manifest) == receipt
    with pytest.raises(TypeError):
        validate_assurance_manifest(object())
    with pytest.raises(TypeError):
        validate_evidence_receipt(object())
    with pytest.raises(TypeError):
        validate_evidence_receipt(receipt, manifest, slot="bad")

    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, current_repository="Other/Repository")
    assert _error_code(error) == FAIL_WRONG_SOURCE
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, current_candidate_sha=OTHER_CANDIDATE)
    assert _error_code(error) == FAIL_RECEIPT_CANDIDATE_BINDING
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, current_tree_sha=OTHER_TREE)
    assert _error_code(error) == FAIL_RECEIPT_TREE_BINDING
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, current_authority_boundary=("OTHER",))
    assert _error_code(error) == FAIL_AUTHORITY_EXPANSION

    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, current_candidate_sha=OTHER_CANDIDATE)
    assert _error_code(error) == FAIL_RECEIPT_CANDIDATE_BINDING
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, current_tree_sha=OTHER_TREE)
    assert _error_code(error) == FAIL_RECEIPT_TREE_BINDING


def test_aq2_profile_qualification_and_inheritance_guards():
    profile = _material_profile()
    manifest = _manifest(profile)
    with pytest.raises(TypeError):
        validate_assurance_manifest(manifest, aq2_profile="bad")

    malformed = replace(profile, material_behavior="")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, aq2_profile=malformed)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    altered = replace(profile, decision_reasons=profile.decision_reasons + ("drift",))
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, aq2_profile=altered)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    fields = {
        "development_mode": "MAINTENANCE",
        "quality_dimensions": (),
        "risk_characteristics": (),
        "invariants": (),
        "risk_fingerprint": "0" * 64,
        "authority_boundary": ("OTHER",),
    }
    for field, value in fields.items():
        values = manifest.to_dict()
        values[field] = list(value) if isinstance(value, tuple) else value
        values["manifest_digest"] = ""
        altered_manifest = AssuranceManifest.from_mapping(values)
        with pytest.raises(AssuranceManifestContractError) as error:
            validate_assurance_manifest(altered_manifest, aq2_profile=profile)
        assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE


def test_predecessor_and_slot_monotonicity_guards():
    profile = _material_profile()
    routing = _routing(profile)
    manifest = _manifest(profile)

    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(manifest, aq3_receipt=routing)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = manifest.to_dict()
    values["source_ref"] = "orchestra:other-source"
    values["manifest_digest"] = ""
    wrong_source = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(wrong_source, aq2_profile=profile, aq3_receipt=routing)
    assert _error_code(error) == FAIL_WRONG_SOURCE

    values = manifest.to_dict()
    values["selected_specialists"] = ["overseer"]
    values["manifest_digest"] = ""
    weak_specialists = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(weak_specialists, aq2_profile=profile, aq3_receipt=routing)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = manifest.to_dict()
    values["required_assurance"] = ["INDEPENDENT_QA"]
    values["manifest_digest"] = ""
    weak_assurance = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(weak_assurance, aq2_profile=profile)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = manifest.to_dict()
    values["selected_specialists"] = ["overseer"]
    values["manifest_digest"] = ""
    weak_selected = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(weak_selected, aq2_profile=profile)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = manifest.to_dict()
    values["protected_gates"] = []
    values["manifest_digest"] = ""
    weak_protected = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(weak_protected, aq2_profile=profile)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = _manifest().to_dict()
    values["required_assurance"] = ["FUNCTIONAL_ASSURANCE"]
    values["manifest_digest"] = ""
    without_independent = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(without_independent)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    values = _manifest().to_dict()
    values["required_assurance"] = ["FUNCTIONAL_ASSURANCE", "INDEPENDENT_QA"]
    values["manifest_digest"] = ""
    missing_slot = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(missing_slot)
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED

    values = _manifest().to_dict()
    values["required_evidence_slots"][0]["required_validator"] = "ponytail"
    values["manifest_digest"] = ""
    bad_validator = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(bad_validator)
    assert _error_code(error) == FAIL_INVALID_EXECUTION_METADATA

    values = _manifest().to_dict()
    values["required_evidence_slots"][0]["covered_risks"] = ["PROVENANCE"]
    values["manifest_digest"] = ""
    broad_risk_slot = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(broad_risk_slot)
    assert _error_code(error) == FAIL_BROAD_COVERAGE

    values = _manifest().to_dict()
    values["required_evidence_slots"][0]["covered_invariants"] = [
        "CLIENT_MUST_NOT_AUTHOR_AUTHORITATIVE_PROVENANCE"
    ]
    values["manifest_digest"] = ""
    broad_invariant_slot = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(broad_invariant_slot)
    assert _error_code(error) == FAIL_BROAD_COVERAGE

    values = _manifest().to_dict()
    values["required_evidence_slots"][0]["independence_required"] = False
    values["manifest_digest"] = ""
    no_independent_slot = AssuranceManifest.from_mapping(values)
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_manifest(no_independent_slot)
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED


def test_builder_argument_and_predecessor_conflicts_fail_closed():
    profile = _profile()
    alternate = _profile(development_mode="MAINTENANCE")
    manifest = _manifest()
    kwargs = {
        "manifest_id": "builder-boundary",
        "repository": manifest.repository,
        "source_ref": manifest.source_ref,
        "candidate_sha": manifest.candidate_sha,
        "tree_sha": manifest.tree_sha,
        "work_item_ref": manifest.work_item_ref,
        "change_class": manifest.change_class,
        "completion_target": manifest.completion_target,
        "required_evidence_slots": manifest.required_evidence_slots,
        "generated_at": manifest.generated_at,
    }
    with pytest.raises(AssuranceManifestContractError) as error:
        build_assurance_manifest(
            profile=profile,
            aq2_profile=alternate,
            **kwargs,
        )
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    routing = _routing(profile)
    alternate_routing = build_routing_receipt(profile, source_identities=("other-source",))
    with pytest.raises(AssuranceManifestContractError) as error:
        build_assurance_manifest(
            profile=profile,
            receipt=routing,
            aq3_receipt=alternate_routing,
            **kwargs,
        )
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    with pytest.raises(AssuranceManifestContractError) as error:
        build_assurance_manifest(receipt=routing, **kwargs)
    assert _error_code(error) == FAIL_WEAKENED_PREDECESSOR_ASSURANCE

    with pytest.raises(TypeError):
        build_assurance_manifest(
            manifest_id="no-predecessor",
            repository=manifest.repository,
            source_ref=manifest.source_ref,
            candidate_sha=manifest.candidate_sha,
            tree_sha=manifest.tree_sha,
            work_item_ref=manifest.work_item_ref,
            change_class=manifest.change_class,
            completion_target=manifest.completion_target,
            required_evidence_slots=manifest.required_evidence_slots,
            generated_at=manifest.generated_at,
        )


def test_receipt_slot_and_metadata_relationship_guards():
    manifest = _manifest()
    receipt = _receipt(manifest)
    slot = manifest.required_evidence_slots[0]
    unknown_gate = replace(receipt, gate_id="unknown-gate", evidence_digest="")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(unknown_gate, manifest)
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED

    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(
            receipt,
            manifest,
            slot=replace(slot, slot_id="different-slot"),
        )
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED

    for field, replacement in (
        ("validator", "ponytail"),
        ("source_truth", "DECIDED"),
        ("provenance_qualification", "SELF_ASSERTED"),
    ):
        altered = _with_mapping_value(receipt, field, replacement)
        with pytest.raises(AssuranceManifestContractError) as error:
            validate_evidence_receipt(altered, manifest)
        assert _error_code(error) == FAIL_INVALID_EXECUTION_METADATA

    altered = _with_mapping_value(receipt, "evidence_scope", "UNIT")
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(altered, manifest)
    assert _error_code(error) == FAIL_LOWER_EVIDENCE_LAYER

    material = _manifest(_material_profile())
    altered = _with_mapping_value(
        _receipt(material),
        "covered_invariants",
        ["CLIENT_MUST_NOT_AUTHOR_AUTHORITATIVE_PROVENANCE", "OTHER_INVARIANT"],
    )
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(altered, material)
    assert _error_code(error) == FAIL_BROAD_COVERAGE

    values = manifest.to_dict()
    values["required_evidence_slots"][0]["required_provenance"] = "SELF_ASSERTED"
    values["manifest_digest"] = ""
    non_authoritative = AssuranceManifest.from_mapping(values)
    non_authoritative_receipt = replace(
        _receipt(manifest),
        provenance_qualification="SELF_ASSERTED",
        evidence_digest="",
    )
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(non_authoritative_receipt, non_authoritative)
    assert _error_code(error) == "AQ4-N13_IMPLEMENTER_SELF_CERTIFIED"

    lexically_earlier = replace(
        _receipt(manifest),
        observed_at="2026-09-08T06:30:00Z",
        evidence_digest="",
    )
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(lexically_earlier, manifest)
    assert _error_code(error) == FAIL_STALE_EVIDENCE


def test_reconciliation_handles_invalid_receipts_and_execution_identities():
    manifest = _manifest()
    with pytest.raises(TypeError):
        reconcile_manifest_evidence(manifest, "receipts")

    class BrokenReceipts:
        def __iter__(self):
            raise TypeError("broken iterator")

    with pytest.raises(TypeError):
        reconcile_manifest_evidence(manifest, BrokenReceipts())

    invalid_mapping = {"schema_version": AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION}
    invalid = reconcile_manifest_evidence(manifest, [invalid_mapping, object()])
    assert FAIL_REQUIRED_RECEIPT_FIELD in invalid.failure_codes
    assert aq4.FAIL_INVALID_FIELD in invalid.failure_codes

    workflow = _receipt(
        manifest,
        gate_type="CI",
        workflow_run_id=100,
        logical_identity="workflow-pass",
    )
    workflow_duplicate = _receipt(
        manifest,
        receipt_id="receipt-workflow-duplicate",
        gate_type="CI",
        workflow_run_id=100,
        logical_identity="workflow-second",
    )
    job = _receipt(
        manifest,
        receipt_id="receipt-job",
        gate_type="REVIEW",
        job_or_check_id="job-1",
        logical_identity="job-evidence",
    )
    evaluation = reconcile_manifest_evidence(manifest, [job, workflow_duplicate, workflow])
    assert evaluation.sufficient
    assert evaluation.evidence_count == 3

    conflicting_workflow = _receipt(
        manifest,
        receipt_id="receipt-workflow-fail",
        gate_type="CI",
        workflow_run_id=100,
        logical_identity="workflow-conflict",
        result="FAIL",
        exit_code=None,
    )
    evaluation = reconcile_manifest_evidence(manifest, [workflow, conflicting_workflow])
    assert FAIL_CONTRADICTORY_EVIDENCE in evaluation.failure_codes
    assert not evaluation.sufficient


def test_reconciliation_detects_receipt_id_and_non_independent_duplicates():
    manifest = _manifest(required_assurance=("FUNCTIONAL_ASSURANCE", "INDEPENDENT_QA"))
    functional = next(
        slot for slot in manifest.required_evidence_slots
        if slot.assurance_class == "FUNCTIONAL_ASSURANCE"
    )
    first = _receipt(
        manifest,
        gate_id=functional.slot_id,
        receipt_id="same-receipt-id",
        logical_identity="logical-one",
    )
    same_id_different_payload = _receipt(
        manifest,
        gate_id=functional.slot_id,
        receipt_id="same-receipt-id",
        logical_identity="logical-two",
        command_or_workflow="different-command",
    )
    evaluation = reconcile_manifest_evidence(
        manifest,
        [first, same_id_different_payload],
    )
    assert FAIL_CONTRADICTORY_EVIDENCE in evaluation.failure_codes

    second = _receipt(
        manifest,
        gate_id=functional.slot_id,
        receipt_id="second-receipt",
        logical_identity="logical-one",
    )
    evaluation = reconcile_manifest_evidence(manifest, [first, second])
    assert FAIL_DUPLICATE_NOT_ADDITIVE in evaluation.failure_codes
    assert not evaluation.sufficient


def test_remaining_strict_shape_and_contract_guards():
    manifest = _manifest()
    manifest_values = manifest.to_dict()
    manifest_values["unexpected"] = True
    with pytest.raises(AssuranceManifestContractError):
        AssuranceManifest.from_mapping(manifest_values)

    receipt_values = _receipt(manifest).to_dict()
    receipt_values["unexpected"] = True
    with pytest.raises(AssuranceManifestContractError):
        EvidenceReceipt.from_mapping(receipt_values)

    evaluation = reconcile_manifest_evidence(manifest, [_receipt(manifest)])
    assert evaluation.is_sufficient
    assert evaluation.can_advance

    assert validate_assurance_manifest(
        manifest,
        current_authority_boundary=("IMPLEMENTATION",),
    ) == manifest

    receipt = _receipt(manifest)
    slot = manifest.required_evidence_slots[0]
    assert validate_evidence_receipt(receipt, manifest, slot=slot.to_dict()) == receipt
    assert validate_evidence_receipt(receipt) == receipt

    with pytest.raises(AssuranceManifestContractError) as error:
        validate_evidence_receipt(receipt, current_repository="Other/Repository")
    assert _error_code(error) == FAIL_WRONG_SOURCE

    with pytest.raises(AssuranceManifestContractError) as error:
        build_evidence_receipt(
            manifest,
            receipt_id="unknown-gate",
            gate_id="missing-gate",
            gate_type="REVIEW",
            command_or_workflow="review",
            result="NOT_APPLICABLE",
            observed_at=OBSERVED,
            producer="overseer",
        )
    assert _error_code(error) == FAIL_REQUIRED_SLOT_UNSATISFIED

    with pytest.raises(TypeError):
        validate_assurance_contract(object())
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    drifted = deepcopy(contract)
    drifted["max_final_pr_paths"] = 10
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_contract(drifted)
    assert _error_code(error) == FAIL_SEMANTIC_DRIFT
    drifted = deepcopy(contract)
    drifted["authority"]["provider_activation"] = True
    with pytest.raises(AssuranceManifestContractError) as error:
        validate_assurance_contract(drifted)
    assert _error_code(error) == FAIL_SEMANTIC_DRIFT


def test_reconciliation_normalizes_duplicate_execution_records():
    manifest = _manifest()
    workflow = _receipt(
        manifest,
        gate_type="CI",
        workflow_run_id=101,
        logical_identity="workflow-one",
    )
    job = _receipt(
        manifest,
        receipt_id="receipt-job-two",
        gate_type="REVIEW",
        job_or_check_id="job-two",
        logical_identity="job-two",
    )
    evaluation = reconcile_manifest_evidence(manifest, [workflow, job])
    assert evaluation.sufficient
    assert evaluation.evidence_count == 2


def test_pass_workflow_requires_run_or_check_identity():
    manifest = _manifest()
    with pytest.raises(AssuranceManifestContractError) as error:
        EvidenceReceipt(
            schema_version=AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION,
            receipt_id='receipt-missing-workflow-identity',
            manifest_id=manifest.manifest_id,
            repository=manifest.repository,
            source_ref=manifest.source_ref,
            candidate_sha=manifest.candidate_sha,
            tree_sha=manifest.tree_sha,
            work_item_ref=manifest.work_item_ref,
            gate_id=manifest.required_evidence_slots[0].slot_id,
            gate_type='WORKFLOW',
            command_or_workflow='ci.yml',
            workflow_run_id=None,
            job_or_check_id=None,
            exit_code=None,
            result='PASS',
            observed_at=OBSERVED,
            producer='overseer',
            validator='overseer',
            source_truth='REPOSITORY',
            provenance_qualification='AUTHORITATIVE',
            evidence_layer='RUNTIME',
            evidence_scope='REPOSITORY',
            covered_risks=manifest.risk_characteristics,
            covered_invariants=manifest.invariants,
            limitations=(),
            evidence_digest='',
        )
    assert _error_code(error) == FAIL_INVALID_EXECUTION_METADATA
