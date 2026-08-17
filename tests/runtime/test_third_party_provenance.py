from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "machine" / "provenance" / "third-party.v1.json"
README = ROOT / "README.md"


def _load() -> dict:
    return json.loads(PROVENANCE.read_text(encoding="utf-8"))


def test_provenance_references_are_semantically_complete() -> None:
    data = _load()
    assert data["policy"]["semantic_context_required_for_references"] is True
    assert data["policy"]["unknown_historical_facts_must_remain_unknown"] is True

    allowed = set(data["policy"]["allowed_classifications"])
    assert {
        "TEST_TOOL_DEPENDENCY",
        "REFERENCE_ONLY",
        "PROTOCOL_STANDARD_REFERENCE",
        "HISTORICAL_RESEARCH_REFERENCE",
        "EVALUATED_OR_PLANNED_REFERENCE",
        "INTEGRATED_RUNTIME_DEPENDENCY",
        "VENDORED_OR_COPIED_CODE",
    } == allowed

    ids = [item["id"] for item in data["items"]]
    assert len(ids) == len(set(ids))
    assert data["summary"]["total_items"] == len(ids)

    expected = {
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
    }
    assert expected <= set(ids)

    for item in data["items"]:
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


def test_provenance_summary_matches_items() -> None:
    data = _load()
    counts: dict[str, int] = {}
    for item in data["items"]:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1
    assert data["summary"]["classification_counts"] == counts


def test_readme_exposes_mcp_sdk_and_provenance_entrypoints() -> None:
    text = README.read_text(encoding="utf-8")
    assert "python scripts/mcp_server.py --adapter codex" in text
    assert "python scripts/certify_adapter.py --adapter codex --json" in text
    assert "docs/THIRD_PARTY_PROVENANCE.md" in text
    assert "machine/provenance/third-party.v1.json" in text
    assert "MCP is transport, not authority." in text
