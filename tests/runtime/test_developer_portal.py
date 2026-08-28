from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "machine/developer-portal/catalog.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/developer-portal-catalog.schema.json"
DOC_PATH = ROOT / "docs/developer/README.md"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_developer_portal_catalog_schema_contract_and_referenced_paths():
    catalog = load(CATALOG_PATH)
    schema = load(SCHEMA_PATH)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) <= set(catalog)
    assert schema["properties"]["schema_version"]["const"] == catalog["schema_version"]
    assert schema["properties"]["portal_mode"]["const"] == catalog["portal_mode"]

    authority_schema = schema["properties"]["authority"]
    assert set(authority_schema["required"]) == set(catalog["authority"])
    for key, value in catalog["authority"].items():
        assert authority_schema["properties"][key]["const"] is value

    release_schema = schema["properties"]["public_release_boundary"]["properties"]
    for key, value in catalog["public_release_boundary"].items():
        assert release_schema[key]["const"] == value

    future_schema = schema["properties"]["future_phase_boundaries"]["properties"]
    for key, value in catalog["future_phase_boundaries"].items():
        assert future_schema[key]["const"] == value

    ids = [item["id"] for item in catalog["surfaces"]]
    assert len(ids) == len(set(ids))
    for surface in catalog["surfaces"]:
        assert ID_PATTERN.fullmatch(surface["id"])
        assert surface["kind"] in {"human_guide", "machine_contract", "machine_schema"}
        assert surface["path"].startswith(("docs/", "machine/"))
        assert (ROOT / surface["path"]).is_file(), surface


def test_journeys_reference_declared_surfaces_only():
    catalog = load(CATALOG_PATH)
    surface_ids = {item["id"] for item in catalog["surfaces"]}
    journey_ids = [item["id"] for item in catalog["journeys"]]
    assert len(journey_ids) == len(set(journey_ids))
    for journey in catalog["journeys"]:
        assert ID_PATTERN.fullmatch(journey["id"])
        assert set(journey["surface_ids"]) <= surface_ids


def test_portal_preserves_authority_boundaries_and_current_mcp_release_projection():
    catalog = load(CATALOG_PATH)
    authority = catalog["authority"]
    assert authority["documentation_and_discovery_only"] is True
    assert authority["implements_mcp"] is True
    for key, value in authority.items():
        if key not in {"documentation_and_discovery_only", "implements_mcp"}:
            assert value is False, key
    assert catalog["future_phase_boundaries"] == {
        "third_party_specialist_marketplace": "NOT_IMPLEMENTED",
        "mcp_server": "PUBLISHED_V1_6_STABLE_RETAINED_V1_7",
    }
    assert catalog["public_release_boundary"] == {
        "release": "v1.7.0",
        "target_commit": "e5305ef3e160209a0345bd2c7843c923940e62c5",
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
    assert "MCP was the final integration phase" in portal
    assert "introduced in v1.6.0 and retained in v1.7.0" in portal
    assert "docs/developer/README.md" in readme
