from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "ui-design-contract.schema.json"
VALID_FIXTURE = ROOT / "tests" / "fixtures" / "ui" / "uix1-valid-contract.json"
INVALID_FIXTURES = (
    ROOT / "tests" / "fixtures" / "ui" / "uix1-invalid-inferred-without-approval.json",
    ROOT / "tests" / "fixtures" / "ui" / "uix1-invalid-unknown-field.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix1_schema_and_reference_fixture_are_valid() -> None:
    contract = _load(VALID_FIXTURE)
    validator = _validator()

    validator.validate(contract)

    assert contract["schema_version"] == "orchestra.ui-design-contract.v1"
    assert contract["validation"]["status"] == "PRE_IMPLEMENTATION"
    assert contract["validation"]["comparison_result"] == "NOT_RUN"
    assert contract["authority"]["contract_grants_implementation_authority"] is False
    assert contract["authority"]["external_tools_grant_authority"] is False
    assert contract["authority"]["validation_grants_authority"] is False


@pytest.mark.parametrize("fixture_path", INVALID_FIXTURES)
def test_uix1_invalid_fixtures_are_rejected(fixture_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(_load(fixture_path))


def test_uix1_inferred_evidence_requires_and_accepts_explicit_approval_ref() -> None:
    contract = _load(VALID_FIXTURE)
    contract["source"]["evidence_confidence"] = "INFERRED_WITH_EXPLICIT_APPROVAL"

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(contract)

    contract["source"]["approval_ref"] = "human-approval:uix1-fixture"
    _validator().validate(contract)


def test_uix1_intentional_adaptation_requires_reason_and_approval() -> None:
    contract = _load(VALID_FIXTURE)
    item = contract["fidelity"]["items"][0]
    item["disposition"] = "INTENTIONALLY_ADAPTED"

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(contract)

    item["reason"] = "Project-native component preserves semantics with a deliberate visual adaptation."
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(contract)

    item["approval_ref"] = "human-approval:uix1-adaptation"
    _validator().validate(contract)


def test_uix1_figma_and_code_connect_are_optional_capabilities() -> None:
    contract = _load(VALID_FIXTURE)
    contract["source"] = {
        "provider": "PROJECT_NATIVE",
        "artifact_identity": "project-design-system",
        "reference_identity": "project:design-system:v1",
        "node_or_component_identity": None,
        "reference_revision_or_timestamp": "project-revision-123",
        "evidence_confidence": "CONFIRMED",
        "evidence_refs": ["project:design-system:v1"],
        "capabilities": ["COMPONENT_DOCS", "DESIGN_TOKENS"],
    }
    contract["validation"]["reference_identity"] = "project:design-system:v1"

    _validator().validate(contract)


def test_uix1_project_mapping_exact_or_adapted_requires_target() -> None:
    contract = _load(VALID_FIXTURE)
    mapping = contract["components"][0]["project_component_mapping"]
    mapping.pop("target")

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(contract)

    mapping["mapping_kind"] = "UNRESOLVED"
    _validator().validate(contract)


def test_uix1_contract_cannot_turn_evidence_into_authority() -> None:
    for field in (
        "contract_grants_implementation_authority",
        "external_tools_grant_authority",
        "validation_grants_authority",
    ):
        contract = _load(VALID_FIXTURE)
        contract["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            _validator().validate(contract)


def test_uix1_validation_evidence_is_revision_bound_without_claiming_preimplementation_results() -> None:
    contract = copy.deepcopy(_load(VALID_FIXTURE))
    assert contract["validation"]["implementation_revision"] is None
    assert contract["validation"]["rendered_evidence"] == []
    assert contract["validation"]["accessibility_evidence"] == []
    assert contract["validation"]["comparison_result"] == "NOT_RUN"
    _validator().validate(contract)
