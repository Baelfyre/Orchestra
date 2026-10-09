from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "optional-adapter-boundaries.schema.json"
CONTRACT_PATH = ROOT / "machine" / "ui" / "optional-adapter-boundaries.v1.json"
HOST_CONTRACT_PATH = ROOT / "machine" / "hosts" / "update-contract.v1.json"
INVALID_FIXTURES = (
    ROOT / "tests" / "fixtures" / "ui" / "uix6-invalid-dependency-adoption.json",
    ROOT / "tests" / "fixtures" / "ui" / "uix6-invalid-authority-source.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix6_contract_is_valid_and_matches_host_maturity() -> None:
    contract = _load(CONTRACT_PATH)
    _validator().validate(contract)

    assert contract["schema_version"] == "orchestra.ui-optional-adapter-boundaries.v1"
    hosts = {entry["host_id"]: entry["maturity"] for entry in _load(HOST_CONTRACT_PATH)["hosts"]}
    assert [host for host, maturity in hosts.items() if maturity == "SUPPORTED"] == contract["host_maturity"]["supported_hosts"]
    assert [host for host, maturity in hosts.items() if maturity == "SCAFFOLD_ONLY"] == contract["host_maturity"]["scaffold_only_hosts"]


@pytest.mark.parametrize("fixture_path", INVALID_FIXTURES)
def test_uix6_invalid_adoption_and_authority_fixtures_are_rejected(fixture_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(_load(fixture_path))


def test_uix6_capability_audit_is_explicit_and_project_native_first() -> None:
    contract = _load(CONTRACT_PATH)
    capabilities = contract["capabilities"]
    assert [entry["id"] for entry in capabilities] == [
        "FIGMA_STRUCTURED_CONTEXT",
        "FIGMA_CODE_CONNECT_TEMPLATE_EVIDENCE",
        "STORYBOOK_COMPONENT_STATE_EVIDENCE",
        "PLAYWRIGHT_RENDERED_BROWSER_EVIDENCE",
        "AXE_ACCESSIBILITY_EVIDENCE",
        "PROJECT_NATIVE_DESIGN_TOKEN_EVIDENCE",
    ]
    assert capabilities[-1]["status"] == "AVAILABLE_CONTRACT_ONLY"
    assert all(entry["adoption_disposition"] == "NO_ADOPTION" for entry in capabilities)
    assert all((ROOT / ref).is_file() for entry in capabilities for ref in entry["evidence_refs"])
    assert contract["adapter_policy"]["project_native_first"] is True
    assert contract["adapter_policy"]["missing_capability_behavior"] == "EXPLICIT_EVIDENCE_LIMITATION"


def test_uix6_no_adoption_is_fail_closed_and_non_authorizing() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["terminal_disposition"]["status"] == "NO_ADOPTION"
    assert contract["terminal_disposition"]["new_dependencies"] == []
    assert contract["terminal_disposition"]["new_runtime_adapters"] == []
    assert contract["audit"]["external_calls_performed"] is False
    assert contract["audit"]["dependency_changes"] is False
    assert contract["audit"]["installed_integration_refresh"] is False
    assert contract["audit"]["figma_mutations"] is False
    assert all(value is False for value in contract["authority"].values())
