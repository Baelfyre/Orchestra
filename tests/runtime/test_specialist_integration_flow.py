from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "specialist-integration-flow.schema.json"
CONTRACT_PATH = ROOT / "machine" / "ui" / "specialist-integration-flow.v1.json"
INVALID_FIXTURES = (
    ROOT / "tests" / "fixtures" / "ui" / "uix5-invalid-authority-expansion.json",
    ROOT / "tests" / "fixtures" / "ui" / "uix5-invalid-ownership-overlap.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix5_flow_and_consumed_ui_contracts_are_valid() -> None:
    contract = _load(CONTRACT_PATH)
    _validator().validate(contract)

    assert contract["schema_version"] == "orchestra.ui-specialist-integration-flow.v1"
    assert [stage["specialist"] for stage in contract["flow"]] == [
        "conductor",
        "cloak",
        "clockwork",
        "the-governor",
        "ponytail",
        "cloak",
        "overseer",
        "arbiter",
    ]
    assert contract["flow"][3]["conditional"] is True
    for relative in contract["consumes"].values():
        assert (ROOT / relative).is_file()


@pytest.mark.parametrize("fixture_path", INVALID_FIXTURES)
def test_uix5_invalid_authority_and_ownership_fixtures_are_rejected(fixture_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(_load(fixture_path))


def test_uix5_ownership_is_explicit_and_non_overlapping() -> None:
    contract = _load(CONTRACT_PATH)
    ownership = contract["ownership"]
    owned = [item for entry in ownership.values() for item in entry["owns"]]

    assert len(owned) == len(set(owned))
    assert set(ownership) == set(contract["validation"]["required_specialists"])
    assert "caveman" not in ownership
    assert "butler" not in ownership
    assert contract["validation"]["conductor_routing_only"] is True
    assert contract["validation"]["overseer_rendered_evidence_owner"] is True
    assert contract["validation"]["arbiter_transition_owner"] is True


def test_uix5_flow_preserves_evidence_boundaries_and_authority_limits() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["validation"]["caveman_role"] == "PRESENTATION_ONLY_NO_AUTHORITY"
    assert contract["validation"]["butler_role"] == "NOT_REGISTERED_OR_ACTIVE_OWNER"
    assert contract["validation"]["ui_evidence_authority"] == "EVIDENCE_NOT_AUTHORITY"
    assert contract["validation"]["runtime_integration"] is False
    assert contract["validation"]["new_specialist_required"] is False
    assert contract["authority"]["transition_disposition_required"] is True
    assert all(value is False for key, value in contract["authority"].items() if key != "transition_disposition_required")
