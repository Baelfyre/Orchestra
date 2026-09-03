"""Deterministic OR-GOV-5 behavior checks for Conductor intake and routing."""

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "skills" / "conductor" / "ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md"
CODEX_GUIDE = ROOT / "adapters" / "codex" / "skills" / "conductor" / "ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md"
ROUTING_GUIDE = ROOT / "skills" / "conductor" / "ROUTING_EVALUATION_GUIDE.md"
CODEX_ROUTING_GUIDE = ROOT / "adapters" / "codex" / "skills" / "conductor" / "ROUTING_EVALUATION_GUIDE.md"
FROZEN_SKILL = ROOT / "skills" / "conductor" / "SKILL.md"
UIX_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
SCHEMA = ROOT / "machine" / "schemas" / "architecture-governance-intake.v1.schema.json"
ROUTES = ROOT / "machine" / "routing" / "routes.v1.json"
FIXTURES = ROOT / "tests" / "behavior" / "router-contract-fixtures.json"

REQUIRED_IDS = {
    "or-gov5-vague-scale",
    "or-gov5-premature-redis",
    "or-gov5-exact-capacity",
    "or-gov5-partial-capacity",
    "or-gov5-prototype-unknown-workload",
    "or-gov5-possible-future-organizations",
    "or-gov5-single-tenant",
    "or-gov5-live-tenant-migration",
    "or-gov5-development-nullable-column",
    "or-gov5-requested-feature",
    "or-gov5-trivial-ui-copy",
    "or-gov5-capacity-changed",
    "or-gov5-unsupported-capacity-claim",
    "or-gov5-existing-architecture-sufficient",
    "or-gov5-unauthorized-dagger",
    "or-gov5-unknown-production-presence",
    "or-gov5-compound-redis-future-growth",
    "or-gov5-compound-live-tenant-model",
    "or-gov5-compound-prove-500-rps",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixtures_by_id() -> dict[str, dict[str, Any]]:
    return {fixture["id"]: fixture for fixture in _read_json(FIXTURES)}


def _validate_intake_schema(intake: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA)
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - repository validation normally installs jsonschema
        assert intake["schema_version"] == "orchestra.architecture-governance-intake.v1"
        assert intake["contract_name"] == "ArchitectureGovernanceIntake"
        assert intake["owner"] == "conductor"
        required = schema["required"]
        assert all(field in intake for field in required)
        return
    jsonschema.Draft202012Validator(schema).validate(intake)


def test_frozen_conductor_guidance_identity_is_preserved() -> None:
    manifest = _read_json(UIX_MANIFEST)
    entry = next(item for item in manifest["materials"] if item["path"] == "skills/conductor/SKILL.md")
    baseline = subprocess.run(
        ["git", "show", "origin/main:skills/conductor/SKILL.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert FROZEN_SKILL.read_bytes().replace(b"\r\n", b"\n") == baseline
    baseline_manifest = json.loads(
        subprocess.run(
            ["git", "show", "origin/main:machine/ui/uix9-live-guidance-manifest.v1.json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
    )
    baseline_entry = next(item for item in baseline_manifest["materials"] if item["path"] == "skills/conductor/SKILL.md")
    assert entry == baseline_entry
    assert "Architecture Governance Intake" not in FROZEN_SKILL.read_text(encoding="utf-8")


def test_intake_schema_remains_canonical_without_migration_tristate_amendment() -> None:
    schema = _read_json(SCHEMA)
    assert schema["$id"].endswith("architecture-governance-intake.v1.schema.json")
    assert schema["properties"]["owner"]["const"] == "conductor"
    assert schema["properties"]["change_materiality"]["enum"] == [
        "TRIVIAL",
        "STANDARD",
        "ARCHITECTURAL",
        "PRODUCTION_CRITICAL",
    ]
    assert "UNKNOWN" not in schema["properties"].get("production_data", {}).get("enum", [])
    assert "production_data" not in schema["properties"]


def test_or_gov5_fixture_matrix_is_schema_valid_and_complete() -> None:
    fixtures = _fixtures_by_id()
    assert REQUIRED_IDS <= fixtures.keys()
    for fixture_id in REQUIRED_IDS:
        fixture = fixtures[fixture_id]
        values = fixture["architecture_governance_intake"]
        intake = {
            "schema_version": "orchestra.architecture-governance-intake.v1",
            "contract_name": "ArchitectureGovernanceIntake",
            "owner": "conductor",
            **values,
        }
        _validate_intake_schema(intake)
        assert fixture["expected_route"]
        assert fixture["expected_route"] == list(dict.fromkeys(fixture["expected_route"]))


def test_route_metadata_preserves_conditional_minimum_sequences() -> None:
    routing = _read_json(ROUTES)
    direct = {route["route_id"]: route for route in routing["direct_routes"]}
    assert direct["architecture-governance-intake"]["target"] == "conductor"
    assert direct["adaptive-capacity-routing"]["target"] == "conductor"
    assert direct["route-composition"]["target"] == "conductor"

    sequences = {route["route_id"]: route["sequence"] for route in routing["ordered_sequences"]}
    assert sequences["product-intent-before-architecture"] == ["the-steward", "clockwork"]
    assert sequences["capacity-measurement-before-architecture"] == ["the-steward", "overseer", "clockwork"]
    assert sequences["persistence-before-implementation"] == ["chronicler", "ponytail"]
    assert sequences["security-before-implementation"] == ["cipher", "ponytail"]


def test_authority_and_deferred_boundaries_are_explicit() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    for marker in (
        "Classification does not grant implementation authority",
        "Classification does not authorize deployment, destructive action, release,",
        "never runs a universal workload questionnaire",
        "PROBLEM != REQUESTED_SOLUTION",
        "FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION",
        "PRODUCTION_PRESENCE_UNRESOLVED",
        "CHRONICLER_PRECONTRACT_SCHEMA_GAP_APPLIES",
        "NOT_PROVEN",
        "OR-GOV-6",
        "keep Dagger unpromoted",
        "Conductor does not\nexecute migrations",
    ):
        assert marker in guide

    assert "do not emit `production_data = false`" in guide


def test_source_and_codex_conductor_guidance_are_identical() -> None:
    assert GUIDE.read_bytes() == CODEX_GUIDE.read_bytes()
    assert ROUTING_GUIDE.read_bytes().replace(b"\r\n", b"\n") == CODEX_ROUTING_GUIDE.read_bytes().replace(b"\r\n", b"\n")


def _run() -> None:
    tests = [
        test_frozen_conductor_guidance_identity_is_preserved,
        test_intake_schema_remains_canonical_without_migration_tristate_amendment,
        test_or_gov5_fixture_matrix_is_schema_valid_and_complete,
        test_route_metadata_preserves_conditional_minimum_sequences,
        test_authority_and_deferred_boundaries_are_explicit,
        test_source_and_codex_conductor_guidance_are_identical,
    ]
    for test in tests:
        test()
    print(f"[PASS] {len(tests)} OR-GOV-5 Conductor intake checks")


if __name__ == "__main__":
    _run()
