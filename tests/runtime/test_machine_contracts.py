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


def test_legacy_specialist_identity_import_remains_machine_derived_compatibility():
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

    fidelity_path = tmp_path / "machine" / "routing"
    fidelity_path.mkdir(parents=True)
    (fidelity_path / "ui-fidelity-routing.v1.json").write_text('{"schema_version":"wrong"}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported UI fidelity routing"):
        contracts.load_ui_fidelity_routing_contract(tmp_path)

    handoff_path = tmp_path / "machine" / "ui"
    handoff_path.mkdir(parents=True)
    (handoff_path / "ui-fidelity-handoff.v1.json").write_text('{"schema_version":"wrong"}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported UI fidelity handoff"):
        contracts.load_ui_fidelity_handoff_contract(tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("selected_by", "ponytail", "UI_FIDELITY_ROUTING_SELECTOR_INVALID"),
        ("profiles", ["MINIMAL_SAFE"], "UI_FIDELITY_ROUTING_PROFILE_SET_INVALID"),
        ("triggers", [{"id": ""}], "UI_FIDELITY_ROUTING_TRIGGER_SET_INVALID"),
        ("authority", {"grants_implementation_authority": True}, "UI_FIDELITY_ROUTING_AUTHORITY_EXPANSION"),
    ],
)
def test_machine_contract_errors_reject_ui_fidelity_contract_drift(monkeypatch, field, value, message):
    fidelity = deepcopy(contracts.load_ui_fidelity_routing_contract(ROOT))
    fidelity[field] = value
    monkeypatch.setattr(contracts, "load_ui_fidelity_routing_contract", lambda root=None: fidelity)
    assert message in contracts.machine_contract_errors(ROOT)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("owned_by", "ponytail", "UI_FIDELITY_HANDOFF_OWNER_INVALID"),
        ("authority", {"implementation_authorized": True}, "UI_FIDELITY_HANDOFF_AUTHORITY_EXPANSION"),
    ],
)
def test_machine_contract_errors_reject_ui_fidelity_handoff_contract_drift(monkeypatch, field, value, message):
    handoff = deepcopy(contracts.load_ui_fidelity_handoff_contract(ROOT))
    handoff[field] = value
    monkeypatch.setattr(contracts, "load_ui_fidelity_handoff_contract", lambda root=None: handoff)
    assert message in contracts.machine_contract_errors(ROOT)


def test_machine_contract_errors_reject_ui_fidelity_handoff_missing_required_field(monkeypatch):
    handoff = deepcopy(contracts.load_ui_fidelity_handoff_contract(ROOT))
    del handoff["preserve"]
    monkeypatch.setattr(contracts, "load_ui_fidelity_handoff_contract", lambda root=None: handoff)
    assert "UI_FIDELITY_HANDOFF_MISSING_FIELD:preserve" in contracts.machine_contract_errors(ROOT)


def test_machine_contract_errors_reject_ui_fidelity_handoff_contract_exception(monkeypatch):
    def _failing_loader(root=None):
        raise ValueError("corrupted handoff")
    monkeypatch.setattr(contracts, "load_ui_fidelity_handoff_contract", _failing_loader)
    assert "UI_FIDELITY_HANDOFF_CONTRACT_INVALID:corrupted handoff" in contracts.machine_contract_errors(ROOT)
