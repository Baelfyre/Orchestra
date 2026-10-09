#!/usr/bin/env python3
"""Deterministic validation for Orchestra README.json machine discovery index."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "README.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "readme-machine-index.schema.json"
PLUGIN_PATH = ROOT / "plugin.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_repo_path(relative: str) -> None:
    path = ROOT / relative.rstrip("/")
    assert path.exists(), f"README.json references missing path: {relative}"


def main() -> int:
    index = load(INDEX_PATH)
    schema = load(SCHEMA_PATH)
    plugin = load(PLUGIN_PATH)

    assert index["$schema"] == "./machine/schemas/readme-machine-index.schema.json"
    assert index["schema_version"] == "orchestra.readme-machine-index.v2"
    assert schema["properties"]["schema_version"]["const"] == index["schema_version"]
    assert schema["properties"]["$schema"]["const"] == index["$schema"]

    for key in schema["required"]:
        assert key in index, f"README.json missing schema-required top-level key: {key}"

    assert index["document_role"] == "machine_repository_index"
    assert index["authority"] == "derived_and_parity_validated_projection"
    assert index["human_readme"] == "README.md"
    assert index["human_documentation_map"] == "docs/README.md"

    assert index["repository"]["package_version"] == str(plugin["version"])
    assert index["repository"]["package_version_source"] == "plugin.json#/version"

    scan = index["machine_scan_order"]
    orders = [entry["order"] for entry in scan]
    assert orders == list(range(1, len(scan) + 1)), "machine_scan_order must be sequential"
    scan_paths = [entry["path"] for entry in scan]
    assert len(scan_paths) == len(set(scan_paths)), "machine_scan_order paths must be unique"
    for entry in scan:
        require_repo_path(entry["path"])

    required_contracts = [
        "specialist_registry",
        "routing_contract",
        "governance_policy",
        "host_update_contract",
        "prap_certification_contract",
        "developer_portal_catalog",
        "third_party_provenance",
        "truesheet_specialist_reference",
        "readme_machine_index_schema",
    ]
    for key in required_contracts:
        require_repo_path(index["machine_contracts"][key])

    for key in (
        "documentation_map",
        "architecture_overview",
        "installation",
        "validation",
        "developer_portal",
        "mcp_transport",
        "hybrid_context_formats",
        "changelog",
    ):
        require_repo_path(index["documentation"][key])

    assert index["representation_policy"]["json"].startswith("Canonical structured machine state")
    assert "non-authoritative" in index["representation_policy"]["toon"]
    assert index["ai_review_guidance"]["preferred_entrypoint"] == "README.json"
    assert index["ai_review_guidance"]["do_not_infer_authority_from_prose"] is True

    print(
        "README_MACHINE_INDEX_V2_TEST=PASS "
        f"scan_entries={len(scan)} specialists={index['specialists']['count']} package={plugin['version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
