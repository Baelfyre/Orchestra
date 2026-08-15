from __future__ import annotations

from copy import deepcopy

import pytest

from orchestra_runtime import machine_contracts as mc


def _policy() -> dict:
    return deepcopy(mc.load_governance_policy())


def _routing() -> dict:
    return deepcopy(mc.load_routing_contract())


def test_unique_governance_values_fail_closed(monkeypatch):
    policy = _policy()
    for value in (None, [], "APPROVED"):
        candidate = deepcopy(policy)
        candidate["governance_decisions"] = value
        monkeypatch.setattr(mc, "load_governance_policy", lambda root=None, candidate=candidate: candidate)
        with pytest.raises(ValueError, match="non-empty list"):
            mc.governance_decision_values()

    candidate = deepcopy(policy)
    candidate["governance_decisions"] = ["APPROVED", "APPROVED"]
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: candidate)
    with pytest.raises(ValueError, match="empty or duplicate"):
        mc.governance_decision_values()


def test_route_map_rejects_missing_and_malformed_records(monkeypatch):
    for routes in ({}, [], None):
        routing = _routing()
        routing["command_routes"] = routes
        monkeypatch.setattr(mc, "load_routing_contract", lambda root=None, routing=routing: routing)
        with pytest.raises(ValueError, match="contains no command routes"):
            mc.command_route_map()

    routing = _routing()
    routing["command_routes"] = {"bad": []}
    monkeypatch.setattr(mc, "load_routing_contract", lambda root=None: routing)
    with pytest.raises(ValueError, match="must be an object"):
        mc.command_route_map()

    routing = _routing()
    routing["command_routes"] = {"bad": {"specialist": ""}}
    monkeypatch.setattr(mc, "load_routing_contract", lambda root=None: routing)
    with pytest.raises(ValueError, match="has no specialist"):
        mc.command_route_map()


def test_route_record_rejects_missing_fallback_and_malformed_record(monkeypatch):
    routing = _routing()
    routing["command_routes"] = {}
    routing["ambiguity_fallback"] = ""
    monkeypatch.setattr(mc, "load_routing_contract", lambda root=None: routing)
    with pytest.raises(ValueError, match="no ambiguity fallback"):
        mc.command_route_record("unknown")

    routing = _routing()
    routing["command_routes"] = {"bad": []}
    monkeypatch.setattr(mc, "load_routing_contract", lambda root=None: routing)
    with pytest.raises(ValueError, match="must be an object"):
        mc.command_route_record("bad")


def test_governance_required_and_validation_rules_fail_closed(monkeypatch):
    policy = _policy()
    policy["governance_required_specialists"] = ["dagger", "dagger"]
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    with pytest.raises(ValueError, match="invalid governance_required_specialists"):
        mc.governance_required_specialists()

    policy = _policy()
    policy["governance_required_specialists"] = [""]
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    with pytest.raises(ValueError, match="invalid governance_required_specialists"):
        mc.governance_required_specialists()

    for rules in (None, {}, []):
        policy = _policy()
        policy["runtime_validation_rules"] = rules
        monkeypatch.setattr(mc, "load_governance_policy", lambda root=None, policy=policy: policy)
        with pytest.raises(ValueError, match="contains no runtime validation rules"):
            mc.runtime_validation_rule_records()


def test_transition_precedence_requires_exact_disposition_set(monkeypatch):
    policy = _policy()
    policy["transition_precedence"] = policy["transition_precedence"][:-1]
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    with pytest.raises(ValueError, match="every transition disposition"):
        mc.transition_precedence()


def test_remediation_limits_validate_shape_types_and_bounds(monkeypatch):
    policy = _policy()
    policy["default_remediation"] = []
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    with pytest.raises(ValueError, match="must be an object"):
        mc.default_remediation_limits()

    for key, value in (
        ("maximum_remediation_attempts_per_unit", True),
        ("maximum_identical_failure_repetitions", "2"),
        ("maximum_scope_growth", None),
    ):
        policy = _policy()
        policy["default_remediation"][key] = value
        monkeypatch.setattr(mc, "load_governance_policy", lambda root=None, policy=policy: policy)
        with pytest.raises(ValueError, match=f"{key} must be an integer"):
            mc.default_remediation_limits()

    for key, value, message in (
        ("maximum_remediation_attempts_per_unit", 0, "must be > 0"),
        ("maximum_identical_failure_repetitions", 0, "must be > 0"),
        ("maximum_scope_growth", -1, "must be >= 0"),
    ):
        policy = _policy()
        policy["default_remediation"][key] = value
        monkeypatch.setattr(mc, "load_governance_policy", lambda root=None, policy=policy: policy)
        with pytest.raises(ValueError, match=message):
            mc.default_remediation_limits()


def test_machine_contract_error_surfaces_cover_policy_set_and_rule_shape(monkeypatch):
    policy = _policy()
    policy["compatibility_rules"].pop("APPROVED")
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    assert "GOVERNANCE_COMPATIBILITY_DECISION_SET_MISMATCH" in mc.machine_contract_errors()

    policy = _policy()
    policy["compatibility_rules"]["APPROVED"] = []
    monkeypatch.setattr(mc, "load_governance_policy", lambda root=None: policy)
    assert "GOVERNANCE_COMPATIBILITY_INVALID:APPROVED" in mc.machine_contract_errors()


def test_contract_loaders_reject_schema_mismatch(tmp_path):
    (tmp_path / "machine/routing").mkdir(parents=True)
    (tmp_path / "machine/governance").mkdir(parents=True)
    (tmp_path / "machine/routing/routes.v1.json").write_text('{"schema_version":"wrong"}', encoding="utf-8")
    (tmp_path / "machine/governance/policy.v1.json").write_text('{"schema_version":"wrong"}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported routing contract"):
        mc.load_routing_contract(tmp_path)
    with pytest.raises(ValueError, match="unsupported governance policy"):
        mc.load_governance_policy(tmp_path)
