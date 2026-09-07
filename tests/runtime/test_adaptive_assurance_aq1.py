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
    REQUIRED_EVIDENCE_METADATA,
    REQUIRED_EVIDENCE_LAYERS,
    REQUIRED_VERIFIER_CONTEXT,
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
    authority_ref: str | None = "authority-1",
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


_VERIFIER_CONTEXT = {
    "source_ref": "source-1",
    "candidate_ref": "candidate-1",
    "work_item_ref": "work-item-1",
    "freshness_ref": "fresh-1",
    "version_ref": "version-1",
    "verified_authority_ref": "authority-1",
}


def _validate(
    current_states: tuple[str, ...],
    target_state: str,
    evidence: list[AssuranceEvidence],
    **overrides: str,
):
    return validate_completion_escalation(
        current_states,
        target_state,
        evidence,
        **{**_VERIFIER_CONTEXT, **overrides},
    )


def _complete(
    mode: str,
    current_states: tuple[str, ...],
    evidence: list[AssuranceEvidence],
    **overrides: object,
):
    return validate_product_complete(
        mode,
        current_states,
        evidence,
        **{**_VERIFIER_CONTEXT, **overrides},
    )


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
    assert contract["evidence_policy"]["required_metadata"] == list(REQUIRED_EVIDENCE_METADATA)
    assert contract["evidence_policy"]["required_verifier_context"] == list(REQUIRED_VERIFIER_CONTEXT)
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
    prototype = _validate(
        (), "PROTOTYPED", [_evidence("PROTOTYPED")]
    )
    assert prototype.product_complete is False
    with pytest.raises(ValueError, match="RECONCILIATION"):
        _complete(
            "DISCOVERY_FIRST",
            ("PROTOTYPED",),
            [_evidence("PRODUCT_COMPLETE")],
        )
    complete = _complete(
        "DISCOVERY_FIRST",
        ("PROTOTYPED", "APPLICATION_INTEGRATED"),
        [_evidence("PRODUCT_COMPLETE")],
        reconciled=True,
    )
    assert complete.product_complete is True


def test_as_built_and_inferred_claims_require_authority() -> None:
    with pytest.raises(ValueError, match="authority"):
        _validate(
            ("DOMAIN_IMPLEMENTED",),
            "CANONICAL_VERIFIED",
            [_evidence("CANONICAL_VERIFIED", "INFERRED")],
            claim_source_truth="INFERRED",
        )
    with pytest.raises(ValueError, match="DECIDED"):
        _validate(
            ("IDEATED",),
            "PROTOTYPED",
            [_evidence("PROTOTYPED", "INFERRED")],
            claim_source_truth="DECIDED",
        )
    assessment = _validate(
        ("DOMAIN_IMPLEMENTED",),
        "CANONICAL_VERIFIED",
        [_evidence("CANONICAL_VERIFIED", "INFERRED", "decision-1")],
        claim_source_truth="INFERRED",
        authority_ref="decision-1",
        verified_authority_ref="decision-1",
    )
    assert assessment.canonical_proves_empirical_effectiveness is False


def test_domain_only_implementation_is_not_product_integration() -> None:
    with pytest.raises(ValueError, match="domain-only"):
        _complete(
            "SPEC_FIRST",
            ("DOMAIN_IMPLEMENTED",),
            [_evidence("PRODUCT_COMPLETE")],
        )


def test_completion_escalation_without_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires evidence"):
        validate_completion_escalation(("IDEATED",), "PROTOTYPED", [])


def test_wrong_evidence_layer_fails_closed() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        _validate(
            ("INTEGRATION_VERIFIED",),
            "RUNTIME_VERIFIED",
            [_evidence("RUNTIME_VERIFIED", evidence_layer="STATIC", evidence_scope="SOURCE")],
        )


def test_narrower_evidence_scope_cannot_qualify_broader_claim() -> None:
    with pytest.raises(ValueError, match="evidence scope"):
        _validate(
            ("DOMAIN_IMPLEMENTED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED", evidence_scope="DOMAIN")],
        )


def test_self_asserted_provenance_cannot_qualify_completion() -> None:
    with pytest.raises(ValueError, match="authoritative provenance"):
        _complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", provenance_qualification="SELF_ASSERTED")],
        )


def test_verifier_context_is_required_for_bound_evidence() -> None:
    with pytest.raises(ValueError, match="verifier context"):
        validate_completion_escalation(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED")],
            verified_authority_ref="authority-1",
        )


def test_self_labeled_authority_requires_verifier_owned_qualification() -> None:
    with pytest.raises(ValueError, match="verifier-owned authority"):
        validate_completion_escalation(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED")],
            source_ref="source-1",
            candidate_ref="candidate-1",
            work_item_ref="work-item-1",
            freshness_ref="fresh-1",
            version_ref="version-1",
        )


def test_authority_binding_must_match_verifier_owned_context() -> None:
    with pytest.raises(ValueError, match="verifier-owned authority"):
        _validate(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED", authority_ref="forged-authority")],
        )


def test_authoritative_source_reference_must_match_bound_source() -> None:
    with pytest.raises(ValueError, match="authoritative source reference"):
        _validate(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence(
                "APPLICATION_INTEGRATED",
                authoritative_source_ref="source-2",
            )],
        )


def test_evidence_records_must_share_one_subject_binding() -> None:
    with pytest.raises(ValueError, match="not consistently bound"):
        _validate(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [
                _evidence("APPLICATION_INTEGRATED"),
                _evidence(
                    "APPLICATION_INTEGRATED",
                    evidence_id="evidence-2",
                    source_ref="source-2",
                    authoritative_source_ref="source-2",
                ),
            ],
        )


def test_inferred_evidence_cannot_be_decided_under_different_authority() -> None:
    with pytest.raises(ValueError, match="cannot become DECIDED"):
        _validate(
            ("IDEATED",),
            "PROTOTYPED",
            [_evidence("PROTOTYPED", "INFERRED")],
            claim_source_truth="DECIDED",
            authority_ref="authority-2",
        )


def test_decided_evidence_requires_matching_claim_authority() -> None:
    with pytest.raises(ValueError, match="DECIDED evidence"):
        _validate(
            ("IDEATED",),
            "PROTOTYPED",
            [_evidence("PROTOTYPED", "DECIDED")],
            authority_ref="authority-2",
        )


def test_evidence_type_supplies_missing_evidence_layer() -> None:
    evidence = _evidence("UNIT_VERIFIED", evidence_layer=None, evidence_type="UNIT")
    assert evidence.evidence_layer == "UNIT"
    assert _validate(("IDEATED",), "UNIT_VERIFIED", [evidence]).target_state == "UNIT_VERIFIED"


def test_empty_evidence_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="evidence_id"):
        _evidence("UNIT_VERIFIED", evidence_id=" ")


@pytest.mark.parametrize("field_name", ["source_ref", "candidate_ref", "work_item_ref", "version_ref"])
def test_evidence_bound_to_the_wrong_subject_fails_closed(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _validate(
            ("APPLICATION_INTEGRATED",),
            "APPLICATION_INTEGRATED",
            [_evidence("APPLICATION_INTEGRATED")],
            **{field_name: "expected-" + field_name},
        )


def test_http_only_evidence_cannot_qualify_runtime_verification() -> None:
    with pytest.raises(ValueError, match="layers are incomplete"):
        _validate(
            ("INTEGRATION_VERIFIED",),
            "RUNTIME_VERIFIED",
            [_evidence("RUNTIME_VERIFIED", evidence_layer="HTTP", evidence_scope="RUNTIME")],
        )


@pytest.mark.parametrize("layer", ["ADVERSARIAL", "MUTATION"])
def test_adversarial_verification_requires_all_layers(layer: str) -> None:
    with pytest.raises(ValueError, match="layers are incomplete"):
        _validate(
            ("SECURITY_VERIFIED",),
            "ADVERSARIALLY_VERIFIED",
            [_evidence(
                "ADVERSARIALLY_VERIFIED",
                evidence_layer=layer,
                evidence_scope="ADVERSARIAL",
            )],
        )


def test_multi_layer_requirements_accept_complete_evidence() -> None:
    runtime = _validate(
        ("INTEGRATION_VERIFIED",),
        "RUNTIME_VERIFIED",
        [
            _evidence(
                "RUNTIME_VERIFIED",
                evidence_id="http-evidence",
                evidence_layer="HTTP",
                evidence_scope="RUNTIME",
            ),
            _evidence(
                "RUNTIME_VERIFIED",
                evidence_id="runtime-evidence",
                evidence_layer="RUNTIME",
                evidence_scope="RUNTIME",
            ),
        ],
    )
    assert runtime.target_state == "RUNTIME_VERIFIED"

    adversarial = _validate(
        ("SECURITY_VERIFIED",),
        "ADVERSARIALLY_VERIFIED",
        [
            _evidence(
                "ADVERSARIALLY_VERIFIED",
                evidence_id="adversarial-evidence",
                evidence_layer="ADVERSARIAL",
                evidence_scope="ADVERSARIAL",
            ),
            _evidence(
                "ADVERSARIALLY_VERIFIED",
                evidence_id="mutation-evidence",
                evidence_layer="MUTATION",
                evidence_scope="ADVERSARIAL",
            ),
        ],
    )
    assert adversarial.target_state == "ADVERSARIALLY_VERIFIED"


def test_stale_evidence_fails_closed_when_freshness_is_required() -> None:
    with pytest.raises(ValueError, match="freshness_ref"):
        _complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", freshness_ref="stale-1")],
            freshness_ref="fresh-1",
        )


def test_domain_evidence_cannot_qualify_application_integration() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        _validate(
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
        _validate(
            ("INTEGRATION_VERIFIED",),
            "RUNTIME_VERIFIED",
            [_evidence("RUNTIME_VERIFIED", evidence_layer="STATIC", evidence_scope="SOURCE")],
        )


def test_generic_unit_pass_cannot_qualify_security_verification() -> None:
    with pytest.raises(ValueError, match="evidence layer"):
        _validate(
            ("UNIT_VERIFIED",),
            "SECURITY_VERIFIED",
            [_evidence("SECURITY_VERIFIED", evidence_layer="UNIT", evidence_scope="UNIT")],
        )


def test_schema_valid_but_semantically_unqualified_evidence_fails_closed() -> None:
    evidence = _evidence("PRODUCT_COMPLETE", provenance_qualification="UNQUALIFIED")
    assert evidence.claimed_state == "PRODUCT_COMPLETE"
    with pytest.raises(ValueError, match="authoritative provenance"):
        _complete("SPEC_FIRST", ("APPLICATION_INTEGRATED",), [evidence])


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
        _complete("SPEC_FIRST", ("APPLICATION_INTEGRATED",), [evidence])


def test_unverified_evidence_cannot_qualify_completion() -> None:
    with pytest.raises(ValueError, match="UNVERIFIED"):
        _complete(
            "SPEC_FIRST",
            ("APPLICATION_INTEGRATED",),
            [_evidence("PRODUCT_COMPLETE", truth="UNVERIFIED")],
        )


def test_canonical_source_identity_cannot_qualify_empirical_effectiveness() -> None:
    with pytest.raises(ValueError, match="claim scope"):
        _validate(
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
