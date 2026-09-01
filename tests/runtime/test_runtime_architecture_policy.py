from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.validation.validate_architecture_boundaries import POLICY_PATH, validate_repository


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_architecture_policy_matches_schema():
    policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "machine/schemas/runtime-architecture-boundaries.v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(policy, schema)


def test_runtime_architecture_policy_validator_passes_repository():
    assert validate_repository(ROOT) == []


def test_runtime_architecture_policy_is_fail_closed_and_authority_bounded():
    policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    assert policy["migration"]["new_flat_runtime_modules_prohibited"] is True
    assert policy["enforcement"]["fail_closed_on_unknown_runtime_package_root"] is True
    assert policy["enforcement"]["fail_closed_on_unplaced_runtime_file"] is True
    assert policy["authority"]["validation_does_not_grant_authority"] is True
    assert policy["authority"]["release_authorized"] is False
    assert policy["authority"]["architecture_owner"] == "clockwork"
    assert policy["authority"]["implementation_owner"] == "ponytail"


def test_runtime_architecture_policy_uses_entrypoints_not_legacy_interfaces_package():
    policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    assert "entrypoints" in policy["canonical_package_roots"]
    assert "interfaces" not in policy["canonical_package_roots"]
    assert "interfaces.py" in policy["migration"]["legacy_flat_modules"]
