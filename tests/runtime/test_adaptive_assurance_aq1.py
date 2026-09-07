from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive import (
    AQ1_DOCTRINE_SCHEMA_VERSION,
    COMPLETION_STATES,
    DEVELOPMENT_MODES,
    SOURCE_TRUTH_LABELS,
    AssuranceEvidence,
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


def _evidence(state: str, truth: str = "OBSERVED", authority_ref: str | None = None) -> AssuranceEvidence:
    return AssuranceEvidence("evidence-1", state, truth, authority_ref)


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
