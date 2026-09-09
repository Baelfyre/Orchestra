# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]


def test_covenant_machine_contract_matches_schema_and_boundaries():
    contract = json.loads(
        (ROOT / "machine/governance/covenant.v1.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "machine/schemas/covenant.v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)

    assert contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING"
    assert contract["legacy_assurance_engine"]["name"] == "PRAI"
    assert contract["legacy_assurance_engine"]["prai_pass_sufficient_for_covenant_pass"] is False
    assert contract["constitutional_precedence"][0] == "PRIME_DIRECTIVE"
    assert "PRAI_PASS_DOES_NOT_OVERRIDE_CROSS_JUDGMENT_CONTRADICTION" in contract["reconciliation_invariants"]
    assert "CONCURRENT_AGGREGATE_INVARIANT" in contract["required_scenario_classes"]
    assert "MUTATION_VS_AUDIT_ATOMICITY" in contract["required_scenario_classes"]
