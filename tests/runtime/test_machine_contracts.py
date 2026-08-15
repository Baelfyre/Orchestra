from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from orchestra_runtime import machine_contracts as contracts
from orchestra_runtime.governance_kernel import (
    DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS,
    DEFAULT_MAX_REMEDIATION_ATTEMPTS,
    GovernanceDecision,
    TransitionDisposition,
)
from orchestra_runtime.models import VALID_SPECIALISTS


ROOT = Path(__file__).resolve().parents[2]


def test_checked_registry_is_exact_frontmatter_compilation():
    assert contracts.load_specialist_registry(ROOT) == contracts.compile_specialist_registry(ROOT)


def test_specialist_identity_set_matches_existing_runtime_constant_during_migration():
    assert contracts.valid_specialist_ids(ROOT) == VALID_SPECIALISTS


def test_machine_contracts_are_internally_consistent():
    assert contracts.machine_contract_errors(ROOT) == ()
    contracts.assert_machine_contracts(ROOT)


def test_governance_policy_is_arbiter_kernel_validation_authority():
    assert contracts.governance_decision_values(ROOT) == tuple(item.value for item in GovernanceDecision)
    assert set(contracts.transition_disposition_values(ROOT)) == {
        item.value for item in TransitionDisposition
    }
    assert contracts.transition_precedence(ROOT) == (
        "STOP",
        "ESCALATE_HUMAN",
        "WAIT_FOR_CAPACITY",
        "WAIT_FOR_EVIDENCE",
        "AUTO_REMEDIATE_AND_REVALIDATE",
        "AUTO_CONTINUE",
    )
    remediation = contracts.default_remediation_limits(ROOT)
    assert remediation["maximum_remediation_attempts_per_unit"] == DEFAULT_MAX_REMEDIATION_ATTEMPTS
    assert remediation["maximum_identical_failure_repetitions"] == DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS


def test_routing_contract_resolves_only_known_specialists():
    ids = contracts.valid_specialist_ids(ROOT)
    routing = contracts.load_routing_contract(ROOT)
    assert routing["ambiguity_fallback"] in ids
    for route in routing["direct_routes"]:
        assert route["target"] in ids
        if "via" in route:
            assert route["via"] in ids
    for alias_target in routing["legacy_aliases"].values():
        assert alias_target in ids


def test_guarded_dagger_route_requires_explicit_authority():
    routing = contracts.load_routing_contract(ROOT)
    dagger = next(route for route in routing["direct_routes"] if route["target"] == "dagger")
    assert dagger["explicit_authority_required"] is True


def test_unknown_route_specialist_fails_validation(monkeypatch):
    routing = deepcopy(contracts.load_routing_contract(ROOT))
    routing["direct_routes"][0]["target"] = "ghost-specialist"
    monkeypatch.setattr(contracts, "load_routing_contract", lambda root=None: routing)
    assert any(error.startswith("ROUTE_UNKNOWN_SPECIALIST:") for error in contracts.machine_contract_errors(ROOT))


def test_dagger_without_explicit_authority_fails_validation(monkeypatch):
    routing = deepcopy(contracts.load_routing_contract(ROOT))
    dagger = next(route for route in routing["direct_routes"] if route["target"] == "dagger")
    dagger.pop("explicit_authority_required")
    monkeypatch.setattr(contracts, "load_routing_contract", lambda root=None: routing)
    assert any(error.startswith("DAGGER_ROUTE_MISSING_EXPLICIT_AUTHORITY:") for error in contracts.machine_contract_errors(ROOT))


def test_unknown_alias_target_fails_validation(monkeypatch):
    routing = deepcopy(contracts.load_routing_contract(ROOT))
    routing["legacy_aliases"]["old-ghost"] = "ghost-specialist"
    monkeypatch.setattr(contracts, "load_routing_contract", lambda root=None: routing)
    assert "ALIAS_UNKNOWN_SPECIALIST:old-ghost:ghost-specialist" in contracts.machine_contract_errors(ROOT)


def test_governance_precedence_must_be_exact_disposition_permutation(monkeypatch):
    policy = deepcopy(contracts.load_governance_policy(ROOT))
    policy["transition_precedence"][-1] = policy["transition_precedence"][0]
    monkeypatch.setattr(contracts, "load_governance_policy", lambda root=None: policy)
    errors = contracts.machine_contract_errors(ROOT)
    assert any(error.startswith("GOVERNANCE_POLICY_INVALID:") for error in errors)


def test_governance_compatibility_rejects_unknown_disposition(monkeypatch):
    policy = deepcopy(contracts.load_governance_policy(ROOT))
    policy["compatibility_rules"]["APPROVED"].append("UNKNOWN_DISPOSITION")
    monkeypatch.setattr(contracts, "load_governance_policy", lambda root=None: policy)
    assert "GOVERNANCE_COMPATIBILITY_INVALID:APPROVED" in contracts.machine_contract_errors(ROOT)


def test_registry_duplicate_slug_is_rejected(monkeypatch):
    registry = deepcopy(contracts.load_specialist_registry(ROOT))
    registry["specialists"].append(deepcopy(registry["specialists"][0]))
    monkeypatch.setattr(contracts, "load_specialist_registry", lambda root=None: registry)
    with pytest.raises(ValueError, match="duplicate slugs"):
        contracts.valid_specialist_ids(ROOT)


def test_assert_machine_contracts_fails_closed(monkeypatch):
    monkeypatch.setattr(contracts, "machine_contract_errors", lambda root=None: ("SYNTHETIC_FAILURE",))
    with pytest.raises(ValueError, match="SYNTHETIC_FAILURE"):
        contracts.assert_machine_contracts(ROOT)


def test_load_contract_rejects_wrong_schema(tmp_path):
    path = tmp_path / "machine" / "specialists"
    path.mkdir(parents=True)
    (path / "registry.v1.json").write_text('{"schema_version":"wrong","specialists":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported specialist registry"):
        contracts.load_specialist_registry(tmp_path)
