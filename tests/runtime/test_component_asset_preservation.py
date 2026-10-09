from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "component-asset-preservation.schema.json"
CONTRACT_PATH = ROOT / "machine" / "ui" / "component-asset-preservation-contract.v1.json"
INVALID_FIXTURES = (
    ROOT / "tests" / "fixtures" / "ui" / "uix4-invalid-unapproved-substitution.json",
    ROOT / "tests" / "fixtures" / "ui" / "uix4-invalid-incomplete-state-coverage.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix4_schema_and_contract_are_valid() -> None:
    contract = _load(CONTRACT_PATH)
    _validator().validate(contract)

    assert contract["schema_version"] == "orchestra.component-asset-preservation.v1"
    assert len(contract["components"]) == 1
    assert {asset["asset_type"] for asset in contract["assets"]} == {
        "FONT",
        "ICON",
        "IMAGE",
        "ILLUSTRATION",
        "LOGO",
    }


@pytest.mark.parametrize("fixture_path", INVALID_FIXTURES)
def test_uix4_invalid_fixtures_are_rejected(fixture_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(_load(fixture_path))


def test_uix4_precedence_and_component_coverage_are_fail_closed() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["precedence"] == [
        "EXACT_SUPPLIED_PROJECT_ASSET_OR_COMPONENT",
        "VERIFIED_EXISTING_PROJECT_NATIVE_EQUIVALENT",
        "APPROVED_SEMANTIC_MAPPING",
        "EXPLICITLY_APPROVED_ADAPTATION",
        "REVIEWED_NEW_IMPLEMENTATION",
        "UNRESOLVED_NO_FABRICATED_REPLACEMENT",
    ]

    component = contract["components"][0]
    assert component["variants"]
    assert {"focus_visible", "disabled", "error"} <= set(component["states"])
    assert component["semantic_tokens"]
    assert component["coverage_status"] == "COMPLETE"
    assert component["implementation_disposition"] == "READY_FOR_IMPLEMENTATION"

    incomplete = copy.deepcopy(contract)
    incomplete["components"][0]["coverage_status"] = "INCOMPLETE"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(incomplete)


def test_uix4_adaptations_and_substitutions_require_traceable_approval() -> None:
    contract = _load(CONTRACT_PATH)
    component = copy.deepcopy(contract["components"][0])
    component["mapping_kind"] = "APPROVED_ADAPTATION"
    component.pop("approval_ref", None)
    component.pop("reason", None)
    candidate = copy.deepcopy(contract)
    candidate["components"] = [component]

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate)

    component["reason"] = "Approved semantic adaptation preserves the project component boundary."
    component["approval_ref"] = "human-approval:uix4-component-adaptation"
    _validator().validate(candidate)

    asset = copy.deepcopy(contract["assets"][-1])
    asset["substitution_policy"] = "APPROVAL_REQUIRED"
    asset["reason"] = "A replacement is required because the supplied asset is unavailable."
    candidate["assets"] = [asset]
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate)

    asset["approval_ref"] = "human-approval:uix4-asset-substitution"
    _validator().validate(candidate)


def test_uix4_known_assets_preserve_provenance_and_never_grant_authority() -> None:
    contract = _load(CONTRACT_PATH)
    for asset in contract["assets"]:
        assert asset["source_identity"]
        assert asset["evidence_ref"]
        assert asset["provenance_status"] in {"CONFIRMED", "REVIEW_REQUIRED", "UNRESOLVED"}

    assert contract["asset_contract"]["known_asset_without_evidence"] == "REJECT"
    assert contract["deviation_rules"]["invented_svg_or_logo_allowed"] is False
    assert contract["deviation_rules"]["silent_known_asset_substitution_allowed"] is False
    assert all(value is False for value in contract["authority"].values())

    invalid = copy.deepcopy(contract)
    invalid["assets"][0]["arbitrary_css_value"] = "#fff"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)
