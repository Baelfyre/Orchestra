from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "machine/developer-portal/catalog.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/developer-portal-catalog.schema.json"
DOC_PATH = ROOT / "docs/developer/README.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_developer_portal_catalog_schema_and_referenced_paths():
    catalog = load(CATALOG_PATH)
    schema = load(SCHEMA_PATH)
    Draft202012Validator(schema).validate(catalog)
    ids = [item["id"] for item in catalog["surfaces"]]
    assert len(ids) == len(set(ids))
    for surface in catalog["surfaces"]:
        assert (ROOT / surface["path"]).is_file(), surface


def test_journeys_reference_declared_surfaces_only():
    catalog = load(CATALOG_PATH)
    surface_ids = {item["id"] for item in catalog["surfaces"]}
    journey_ids = [item["id"] for item in catalog["journeys"]]
    assert len(journey_ids) == len(set(journey_ids))
    for journey in catalog["journeys"]:
        assert set(journey["surface_ids"]) <= surface_ids


def test_portal_cannot_expand_authority_or_future_phase_scope():
    catalog = load(CATALOG_PATH)
    authority = catalog["authority"]
    assert authority["documentation_and_discovery_only"] is True
    for key, value in authority.items():
        if key != "documentation_and_discovery_only":
  assert value is False, key
    assert catalog["future_phase_boundaries"] == {
        "third_party_specialist_marketplace": "NOT_IMPLEMENTED",
        "mcp_server": "NOT_IMPLEMENTED_FINAL_PHASE",
    }
    assert catalog["public_release_boundary"] == {
        "release": "v1.5.0",
        "target_commit": "b0a56cc7af8ad78234754bcb29ed07f6ab54d920",
        "moved_by_portal": False,
    }


def test_catalog_keeps_canonical_domain_owners_explicit():
    catalog = load(CATALOG_PATH)
    by_id = {item["id"]: item for item in catalog["surfaces"]}
    assert by_id["prap-certification-contract"]["path"] == "machine/protocol/prap-certification-contract.v1.json"
    assert by_id["host-update-contract"]["path"] == "machine/hosts/update-contract.v1.json"
    assert by_id["specialist-registry"]["path"] == "machine/specialists/registry.v1.json"
    assert by_id["governance-policy"]["path"] == "machine/governance/policy.v1.json"
    assert by_id["host-update-contract"]["authority_role"] == "HOST_MATURITY_AUTHORITY"
    assert by_id["specialist-registry"]["authority_role"] == "SPECIALIST_IDENTITY_AUTHORITY"
    assert by_id["governance-policy"]["authority_role"] == "GOVERNANCE_POLICY_AUTHORITY"


def test_human_portal_and_readme_surface_the_machine_index_and_boundaries():
    portal = DOC_PATH.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "machine/developer-portal/catalog.v1.json" in portal
    assert "Third-Party Specialist Marketplace" in portal
    assert "MCP remains the final integration phase" in portal
    assert "docs/developer/README.md" in readme
