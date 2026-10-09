from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import jsonschema
import pytest

from adapters.codex.validate_codex_export import normalize_body_for_parity


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "portable-specialist-parity.schema.json"
CONTRACT_PATH = ROOT / "machine" / "ui" / "portable-specialist-parity.v1.json"
HOST_CONTRACT_PATH = ROOT / "machine" / "hosts" / "update-contract.v1.json"

EXPECTED_OWNERS = ["conductor", "cloak", "clockwork", "the-governor", "ponytail", "overseer", "arbiter"]
EXPECTED_HOSTS = ["codex", "antigravity", "claude-code", "cursor", "windsurf", "vscode", "jetbrains", "zed", "neovim"]
EXPECTED_SURFACES = {
    owner: {
        "source_path": f"skills/{owner}/SKILL.md",
        "projection_path": f"adapters/codex/skills/{owner}/SKILL.md",
    }
    for owner in EXPECTED_OWNERS
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _contract() -> dict:
    return _load(CONTRACT_PATH)


def test_uix8_contract_revalidates_live_hosts_and_supported_codex_projection() -> None:
    contract = _contract()
    _validator().validate(contract)

    assert contract["schema_version"] == "orchestra.ui-portable-specialist-parity.v1"
    assert contract["source_authority"]["owners"] == EXPECTED_OWNERS
    assert [entry["host_id"] for entry in contract["host_projections"]] == EXPECTED_HOSTS

    hosts = {entry["host_id"]: entry["maturity"] for entry in _load(HOST_CONTRACT_PATH)["hosts"]}
    assert {entry["host_id"]: entry["maturity"] for entry in contract["host_projections"]} == hosts

    surfaces = {entry["owner"]: entry for entry in contract["surfaces"]}
    assert list(surfaces) == EXPECTED_OWNERS
    for owner, expected in EXPECTED_SURFACES.items():
        surface = surfaces[owner]
        assert surface["source_path"] == expected["source_path"]
        assert surface["projection_path"] == expected["projection_path"]
        source = ROOT / surface["source_path"]
        projection = ROOT / surface["projection_path"]
        assert source.is_file()
        assert projection.is_file()
        source_text = source.read_text(encoding="utf-8")
        projection_text = projection.read_text(encoding="utf-8")
        assert normalize_body_for_parity(source_text) == normalize_body_for_parity(projection_text)
        for marker in surface["required_markers"]:
            assert marker in source_text
            assert marker in projection_text

    assert not (ROOT / "adapters" / "antigravity" / "skills").exists()


def test_uix8_positive_codex_projection_is_normalized_portable_parity() -> None:
    contract = _contract()
    codex = next(entry for entry in contract["host_projections"] if entry["host_id"] == "codex")
    assert codex["maturity"] == "SUPPORTED"
    assert codex["disposition"] == "NORMALIZED_PORTABLE_COPY"
    assert codex["copy_required"] is True


def test_uix8_negative_stale_source_copy_is_rejected() -> None:
    contract = _contract()
    surface = contract["surfaces"][0]
    source_text = (ROOT / surface["source_path"]).read_text(encoding="utf-8")
    projection_text = (ROOT / surface["projection_path"]).read_text(encoding="utf-8")
    stale_projection = projection_text.replace(surface["required_markers"][0], "stale UIX-5 ownership flow", 1)

    assert normalize_body_for_parity(source_text) != normalize_body_for_parity(stale_projection)


def test_uix8_negative_authority_expansion_is_rejected() -> None:
    candidate = deepcopy(_contract())
    candidate["authority"]["parity_grants_runtime_authority"] = True

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate)


def test_uix8_negative_scaffold_host_promotion_is_rejected() -> None:
    candidate = deepcopy(_contract())
    candidate["host_projections"][2].update(
        {
            "disposition": "NORMALIZED_PORTABLE_COPY",
            "source_root": "skills",
            "projection_root": "adapters/claude-code/skills",
            "validator": "adapters/codex/validate_codex_export.py",
            "copy_required": True,
        }
    )

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate)


def test_uix8_negative_fabricated_antigravity_copy_is_rejected() -> None:
    candidate = deepcopy(_contract())
    candidate["host_projections"][1].update(
        {
            "disposition": "EXACT_PORTABLE_COPY",
            "projection_root": "adapters/antigravity/skills",
            "validator": "adapters/codex/validate_codex_export.py",
            "copy_required": True,
        }
    )

    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate)
