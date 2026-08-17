#!/usr/bin/env python3
"""Deterministic validation for Orchestra README.json and machine provenance discovery."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "README.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "readme-machine-index.schema.json"
PLUGIN_PATH = ROOT / "plugin.json"
PROVENANCE_PATH = ROOT / "machine" / "provenance" / "third-party.v1.json"
README_PATH = ROOT / "README.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_repo_path(relative: str) -> None:
    path = ROOT / relative.rstrip("/")
    assert path.exists(), f"README.json references missing path: {relative}"


def validate_provenance() -> None:
    data = load(PROVENANCE_PATH)
    assert data["policy"]["semantic_context_required_for_references"] is True
    assert data["policy"]["unknown_historical_facts_must_remain_unknown"] is True

    allowed = set(data["policy"]["allowed_classifications"])
    assert allowed == {
        "TEST_TOOL_DEPENDENCY",
        "REFERENCE_ONLY",
        "PROTOCOL_STANDARD_REFERENCE",
        "HISTORICAL_RESEARCH_REFERENCE",
        "EVALUATED_OR_PLANNED_REFERENCE",
        "INTEGRATED_RUNTIME_DEPENDENCY",
        "VENDORED_OR_COPIED_CODE",
    }

    ids = [item["id"] for item in data["items"]]
    assert len(ids) == len(set(ids))
    assert data["summary"]["total_items"] == len(ids)
    assert {
        "mutmut",
        "hypothesis",
        "cosmic-ray",
        "strix",
        "openhero",
        "spec-kitty",
        "bryl-minimal-design",
        "ponytail",
        "caveman",
        "truesheet",
        "mcp-specification",
        "phionyx-research",
        "ai-safe2-framework",
        "orchestra-hq-orchestra-skills",
        "sakana-fugu",
    } <= set(ids)

    counts: dict[str, int] = {}
    for item in data["items"]:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1
        assert item["purpose"].strip()
        assert item["incorporated_or_learned_patterns"]
        assert item["orchestra_surfaces"]
        assert item["evidence"]
        assert item["reviewed_revision"]["status"].strip()
        assert item["license"]["status"].strip()

        if item["classification"] in {
            "REFERENCE_ONLY",
            "PROTOCOL_STANDARD_REFERENCE",
            "HISTORICAL_RESEARCH_REFERENCE",
            "EVALUATED_OR_PLANNED_REFERENCE",
        }:
            assert item["runtime_dependency"] is False
            assert item["source_copied_or_vendored"] is False
            assert item["upstream_source_adapted"] is False

    assert data["summary"]["classification_counts"] == counts


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
        "third_party_provenance_schema",
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
        "adapter_sdk_prap",
        "third_party_provenance",
        "third_party_provenance_machine",
        "hybrid_context_formats",
        "changelog",
    ):
        require_repo_path(index["documentation"][key])

    assert index["capabilities"]["mcp_stdio_transport"]["quickstart_command"] == "python scripts/mcp_server.py --adapter codex"
    assert "python scripts/certify_adapter.py --adapter codex --json" in index["capabilities"]["adapter_sdk_and_prap_certification"]["quickstart_commands"]
    assert index["knowledge_provenance"]["third_party_machine_role"] == "CANONICAL_SEMANTIC_PROVENANCE_RECORD"
    assert index["knowledge_provenance"]["third_party_human_role"] == "CURATED_HUMAN_PROJECTION"
    assert index["knowledge_provenance"]["historical_uncertainty_rule"].startswith("Unknown historical facts")

    assert index["representation_policy"]["json"].startswith("Canonical structured machine state")
    assert "non-authoritative" in index["representation_policy"]["toon"]
    assert index["ai_review_guidance"]["preferred_entrypoint"] == "README.json"
    assert index["ai_review_guidance"]["do_not_infer_authority_from_prose"] is True
    assert index["ai_review_guidance"]["third_party_provenance_machine_source_is_semantically_canonical"] is True

    text = README_PATH.read_text(encoding="utf-8")
    assert "python scripts/mcp_server.py --adapter codex" in text
    assert "python scripts/certify_adapter.py --adapter codex --json" in text
    assert "docs/THIRD_PARTY_PROVENANCE.md" in text
    assert "machine/provenance/third-party.v1.json" in text
    assert "MCP is transport, not authority." in text

    validate_provenance()

    print(
        "README_MACHINE_INDEX_V2_TEST=PASS "
        f"scan_entries={len(scan)} specialists={index['specialists']['count']} package={plugin['version']} "
        f"provenance_items={load(PROVENANCE_PATH)['summary']['total_items']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
