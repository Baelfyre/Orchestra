from __future__ import annotations

import json
from dataclasses import replace
from itertools import product
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive import (
    AQ1_DOCTRINE_SCHEMA_VERSION,
    CLAIM_SCOPE_BY_STATE,
    COMPLETION_STATES,
    DEVELOPMENT_MODES,
    EVIDENCE_LAYERS,
    EVIDENCE_SCOPES,
    SOURCE_TRUTH_LABELS,
    AssuranceEvidence,
    PROVENANCE_QUALIFICATIONS,
    REQUIRED_EVIDENCE_LAYERS,
    select_mode_for_evidence,
    transition_mode,
    validate_completion_escalation,
    validate_product_complete,
)

ROOT = Path(__file__).parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq1-normative-doctrine.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "adaptive-assurance-doctrine.v1.schema.json"


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence(
    state: str,
    truth: str = "OBSERVED",
    authority_ref: str | None = None,
    **overrides: object,
) -> AssuranceEvidence:
    fields: dict[str, object] = {
        "evidence_id": "evidence-1",
        "claimed_state": state,
        "source_truth": truth,
        "authority_ref": authority_ref,
        "originating_source": "test-runner",
        "authoritative_source_ref": "source-1",
        "producer": "test-producer",
        "validator": "test-validator",
        "source_ref": "source-1",
        "candidate_ref": "candidate-1",
        "work_item_ref": "work-item-1",
        "freshness_ref": "fresh-1",
        "version_ref": "version-1",
        "provenance_qualification": "AUTHORITATIVE",
        "evidence_layer": REQUIRED_EVIDENCE_LAYERS[state][0],
        "evidence_scope": CLAIM_SCOPE_BY_STATE[state],
        "claim_scope": CLAIM_SCOPE_BY_STATE[state],
    }
    fields.update(overrides)
    return AssuranceEvidence(**fields)


def test_aq1_contract_matches_schema_and_domain_constants() -> None:
    contract = _json(CONTRACT_PATH)
    schema = _json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=str)
    assert errors == []
    assert contract["schema_version"] == AQ1_DOCTRINE_SCHEMA_VERSION
    assert contract["development_modes"] == list(DEVELOPMENT_MODES)
    assert contract["source_truth_labels"] == list(SOURCE_TRUTH_LABELS)
    assert contract["completion_states"] == list(COMPLETION_STATES)
    assert contract["evidence_policy"]["layers"] == list(EVIDENCE_LAYERS)
    assert contract["evidence_policy"]["scopes"] == list(EVIDENCE_SCOPES)
    assert contract["evidence_policy"]["provenance_qualifications"] == list(PROVENANCE_QUALIFICATIONS)
    assert contract["evidence_policy"]["claim_scope_by_state"] == CLAIM_SCOPE_BY_STATE
    assert contract["evidence_policy"]["required_layers_by_state"] == {
        state: list(layers) for state, layers in REQUIRED_EVIDENCE_LAYERS.items()
    }
    assert contract["authority"]["aq2_or_later_authorized"] is False
    assert contract["authority"]["cud10_authorized"] is False


@pytest.mark.parametrize("current_mode,target_mode", list(product(DEVELOPMENT_MODES, repeat=2)))
def test_all_declared_mode_transitions_are_supported(current_mode: str, target_mode: str) -> None:
    assert transition_mode(current_mode, target_mode) == target_mode


def test_conflicting_sources_select_reconciliation() -> None:
    assert select_mode_for_evidence("AS_BUILT", conflicting_sources=True) == "RECONCILIATION"
    assert select_mode_for_evidence("AS_BUILT", conflicting_sources=False) == "AS_BUILT"


def test_discovery_first_allows_prototype_but_requires_reconciliation_for_product_complete() -> None:
    prototype = validate_completion_escalation(
        (), "PROTOTYPED", [_evidence("PROTOTYPED")]
    )
    assert prototype.product_complete is False
    with pytest.raises(ValueError, match="RECONCILIATION"):
        validate_product_complete(
            "DISCOVERY_FIRST",
            ("PROTOTYPED",),
            [_evidence("PRODUCT_COMPLETE")],
        )
    complete = validate_product_complete(
        "DISCOVERY_FIRST",
        ("PROTOTYPED", "APPLICATION_INTEGRATED"),
        [_evidence("PRODUCT_COMPLETE")],
        reconciled=True,
    )
    assert complete.product_complete is True


def test_as_built_and_inferred_claims_require_authority() -> None:
    with pytest.raises(ValueError, match="authority"):
        validate_completion_escalation(
            ("DOMAIN_IMPLEMENTED",),
            "CANONICAL_VERIFIED",
            [_evidence("CANONICAL_VERIFIED", "INFERRED")],
            claim_source_truth="INFERRED",
        )
    with pytest.raises(ValueError, match="DECIDED"):
        validate_completion_escalation(
            ("IDEATED",),
            "PROTOTYPED",
            [_evidence("PROTOTYPED", "INFERRED")],
            claim_source_truth="DECIDED",
        )
    assessment = validate_completion_escalation(
        ("DOMAIN_IMPLEMENTED",),
        "CANONICAL_VERIFIED",
        [_evidence("CANONICAL_VERIFIED", "INFERRED", "decision-1")],
        claim_source_truth="INFERRED",
        authority_ref="decision-1",
    )
    assert assessment.canonical_proves_empirical_effectiveness is False


def test_domain_only_implementation_is_not_product_integration() -> None:
    with pytest.raises(ValueError, match="domain-only"):
        validate_product_complete(
            "SPEC_FIRST",
            ("DOMAIN_IMPLEMENTED",),
            [_evidence("PRODUCT_COMPLETE")],
        )


def test_completion_escalation_without_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires evidence"):
        validate_completion_escalation(("IDEATED",), "PROTOTYPED", [])


def test_wrong_evidence_layer_fails_closed() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        validate_completion_escalation(
            ("INTEGRATION_VERIFIED",),
            "RUNTIME_VERIFIED",
            [_evidence("RUNTIME_VERIFIED", evidence_layer="STATIC", evidence_scope="SOURCE")],
        )


def test_narrower_evidence_scope_cannot_qualify_broader_claim() -> None:
    with pytest.raises(ValueError, match="evidence scope"):
        validate_completion_escalation(
            ("DOMAIN_IMPLEMENTED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED", evidence_scope="DOMAIN")],
        )


def test_self_asserted_provenance_cannot_qualify_completion() -> None:
    with pytest.raises(ValueError, match="authoritative provenance"):
        validate_product_complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", provenance_qualification="SELF_ASSERTED")],
        )


@pytest.mark.parametrize("field_name", ["source_ref", "candidate_ref", "work_item_ref"])
def test_evidence_bound_to_the_wrong_subject_fails_closed(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        validate_completion_escalation(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED")],
            **{field_name: "expected-" + field_name},
        )


def test_stale_evidence_fails_closed_when_freshness_is_required() -> None:
    with pytest.raises(ValueError, match="freshness_ref"):
        validate_product_complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", freshness_ref="stale-1")],
            freshness_ref="fresh-1",
        )


def test_domain_evidence_cannot_qualify_application_integration() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        validate_completion_escalation(
            ("DOMAIN_IMPLEMENTED",),
            "APPLICATION_INTEGRATED",
            [_evidence(
                "APPLICATION_INTEGRATED",
                evidence_layer="DOMAIN",
                evidence_scope="DOMAIN",
            )],
        )


def test_static_evidence_cannot_qualify_runtime_verification() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        validate_completion_escalation(
            ("INTEGRATION_VERIFIED",),
            "RUNTIME_VERIFIED",
            [_evidence("RUNTIME_VERIFIED", evidence_layer="STATIC", evidence_scope="SOURCE")],
        )


def test_generic_unit_pass_cannot_qualify_security_verification() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        validate_completion_escalation(
            ("UNIT_VERIFIED",),
            "SECURITY_VERIFIED",
            [_evidence("SECURITY_VERIFIED", evidence_layer="UNIT", evidence_scope="UNIT")],
        )


def test_schema_valid_but_semantically_unqualified_evidence_fails_closed() -> None:
    evidence = _evidence("PRODUCT_COMPLETE", provenance_qualification="UNQUALIFIED")
    assert evidence.claimed_state == "PRODUCT_COMPLETE"
    with pytest.raises(ValueError, match="authoritative provenance"):
        validate_product_complete("SPEC_FIRST", ("APPLICATION_INTEGRATED",), [evidence])


def test_authoritative_marker_without_required_provenance_metadata_fails_closed() -> None:
    evidence = AssuranceEvidence(
        "evidence-1",
        "PRODUCT_COMPLETE",
        "OBSERVED",
        provenance_qualification="AUTHORITATIVE",
        evidence_layer="COMPLETION_STATE",
        evidence_scope="PRODUCT",
        claim_scope="PRODUCT",
    )
    with pytest.raises(ValueError, match="metadata"):
        validate_product_complete("SPEC_FIRST", ("APPLICATION_INTEGRATED",), [evidence])


def test_unverified_evidence_cannot_qualify_completion() -> None:
    with pytest.raises(ValueError, match="UNVERIFIED"):
        validate_product_complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", truth="UNVERIFIED")],
        )


def test_canonical_source_identity_cannot_qualify_empirical_effectiveness() -> None:
    with pytest.raises(ValueError, match="claim scope"):
        validate_completion_escalation(
            ("INTEGRATION_VERIFIED",),
            "CANONICAL_VERIFIED",
            [_evidence(
                "CANONICAL_VERIFIED",
                evidence_scope="SOURCE",
                claim_scope="EMPIRICAL_EFFECTIVENESS",
            )],
        )


def test_evidence_type_and_layer_must_not_disagree() -> None:
    with pytest.raises(ValueError, match="must match"):
        replace(
            _evidence("UNIT_VERIFIED"),
            evidence_type="STATIC",
            evidence_layer="UNIT",
        )
