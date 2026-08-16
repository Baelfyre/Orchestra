from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.machine_contracts import command_route_record

ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_public_command_surface_has_files_and_canonical_machine_routes() -> None:
    manifest = _load_json("plugin.json")
    routing = _load_json("machine/routing/routes.v1.json")
    public_commands = tuple(manifest["commands"])
    route_names = set(routing["command_routes"])

    assert len(public_commands) == len(set(public_commands))
    assert set(public_commands) <= route_names
    for command in public_commands:
        assert (ROOT / "commands" / f"{command}.md").is_file()


def test_compliance_commands_are_explicit_public_routes() -> None:
    manifest = _load_json("plugin.json")
    assert "compliance-registry" in manifest["commands"]
    assert "compliance-review" in manifest["commands"]

    assert command_route_record("compliance-registry", ROOT) == {
        "specialist": "conductor",
        "route_id": "compliance-registry-lifecycle",
    }
    assert command_route_record("compliance-review", ROOT) == {
        "specialist": "conductor",
        "route_id": "compliance-review-governed",
    }


def test_compliance_review_route_preserves_governance_ownership_order() -> None:
    routing = _load_json("machine/routing/routes.v1.json")
    sequences = {
        record["route_id"]: record["sequence"]
        for record in routing["ordered_sequences"]
    }
    assert sequences["compliance-review-governed"] == [
        "conductor",
        "the-governor",
        "the-steward",
        "arbiter",
    ]
