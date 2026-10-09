"""Deterministic OR-GOV-6 governance dependency and re-entry checks."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts" / "validate_tuner_evidence_continuity.py"
FIXTURES_PATH = ROOT / "tests" / "behavior" / "tuner-governance-contract-fixtures.json"

spec = importlib.util.spec_from_file_location("tuner_evidence_continuity", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def _fixtures() -> dict[str, dict]:
    return {item["id"]: item for item in json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))}


def _result(fixture_id: str) -> dict:
    fixture = _fixtures()[fixture_id]
    return validator.evaluate_governance_invalidation(
        fixture["previous_contracts"],
        fixture["current_contracts"],
        fixture["dependency_edges"],
        fixture["contract_owners"],
        fixture["trigger_contracts"],
        self_invalidated_contracts=fixture.get("self_invalidated_contracts", []),
        trigger_category=fixture.get("trigger_category", "CONTRACT_CHANGE"),
    )


def test_fixture_matrix_is_complete_and_deterministic() -> None:
    fixtures = list(_fixtures().values())
    assert validator.validate_governance_fixtures(fixtures) == []


def test_semantic_change_traverses_declared_edges_only() -> None:
    result = _result("capacity-chain-stops-without-migration-edge")
    assert result["minimal_reentry"] == ["clockwork"]
    assert "chronicler" not in result["minimal_reentry"]


def test_identity_only_change_refreshes_reference_without_domain_reentry() -> None:
    result = _result("identity-only-contract-revision")
    assert result["coordination_status"] == "CROSS_LAYER_CONTRACT_STALE"
    assert result["identity_only"] is True
    assert result["minimal_reentry"] == []


def test_transitive_cycles_and_duplicate_paths_are_finite_and_deduplicated() -> None:
    cycle = _result("cyclic-governance-invalidation")
    duplicate = _result("duplicate-governance-paths")
    assert cycle["minimal_reentry"] == ["chronicler", "clockwork"]
    assert duplicate["minimal_reentry"] == ["clockwork", "overseer"]


def test_trigger_owner_reentry_requires_explicit_self_invalidation() -> None:
    result = _result("implementation-invalidates-trigger-owner")
    assert result["minimal_reentry"] == ["chronicler", "overseer"]
    assert _result("migration-rollback-change-invalidates-validation")["minimal_reentry"] == ["overseer"]


def test_output_preserves_boundaries_and_special_target_owners() -> None:
    documentation = _result("documentation-only-dependency")
    diagram = _result("diagram-only-dependency")
    authority = _result("authority-scope-change")
    gap = _result("migration-risk-unknown-production-gap")
    assert documentation["minimal_reentry"] == ["scribe"]
    assert diagram["minimal_reentry"] == ["weaver"]
    assert authority["authority_change"] is True
    assert authority["authority_expansion"] is False
    assert gap["migration_risk_unknown_production_gap"] == "MIGRATION_RISK_SCHEMA_GAP"
    assert gap["production_data_preserved"] is True
    for result in (documentation, diagram, authority, gap):
        assert result["recommended_next_route"] == "conductor"
        assert result["tuner_dispatches"] is False


def test_malformed_or_unknown_dependencies_fail_closed() -> None:
    fixtures = _fixtures()
    for fixture_id in ("unknown-trigger-contract", "missing-governance-owner", "malformed-governance-edge"):
        fixture = fixtures[fixture_id]
        try:
            validator.evaluate_governance_invalidation(
                fixture["previous_contracts"],
                fixture["current_contracts"],
                fixture["dependency_edges"],
                fixture["contract_owners"],
                fixture["trigger_contracts"],
            )
        except validator.ContinuityContractError:
            continue
        raise AssertionError(f"{fixture_id} did not fail closed")


def _run() -> None:
    tests = [
        test_fixture_matrix_is_complete_and_deterministic,
        test_semantic_change_traverses_declared_edges_only,
        test_identity_only_change_refreshes_reference_without_domain_reentry,
        test_transitive_cycles_and_duplicate_paths_are_finite_and_deduplicated,
        test_trigger_owner_reentry_requires_explicit_self_invalidation,
        test_output_preserves_boundaries_and_special_target_owners,
        test_malformed_or_unknown_dependencies_fail_closed,
    ]
    for test in tests:
        test()
    print(f"[PASS] {len(tests)} OR-GOV-6 Tuner governance dependency checks")


if __name__ == "__main__":
    _run()
