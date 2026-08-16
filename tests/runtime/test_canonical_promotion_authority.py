from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from orchestra_runtime import machine_contracts as contracts
from orchestra_runtime.models import (
    ContextPackage,
    RouteDecision,
    VALID_SPECIALISTS,
)
from orchestra_runtime import services
from orchestra_runtime.errors import RuntimeInitializationError
from orchestra_runtime.services import GovernanceValidator


ROOT = Path(__file__).resolve().parents[2]


def _context(**metadata: bool) -> ContextPackage:
    return ContextPackage(
        adapter_name="test",
        prompt="test",
        project_root=ROOT,
        available_commands=(),
        manifest_version="test",
        metadata=metadata,
    )


def _decision(command: str, specialist: str) -> RouteDecision:
    return RouteDecision(
        command_name=command,
        skill_slug=specialist,
        governance_required=specialist in contracts.governance_required_specialists(ROOT),
        reason="test",
    )


def test_compatibility_specialist_identity_is_derived_from_machine_registry():
    assert VALID_SPECIALISTS == contracts.valid_specialist_ids(ROOT)
    source = inspect.getsource(__import__("orchestra_runtime.models", fromlist=["VALID_SPECIALISTS"]))
    assert "VALID_SPECIALISTS = frozenset({" not in source
    assert "VALID_SPECIALISTS = valid_specialist_ids()" in source


def test_compatibility_command_routes_are_derived_from_machine_routing_contract():
    assert services.DEFAULT_COMMAND_ROUTES == contracts.command_route_map(ROOT)
    assert services.DEFAULT_AMBIGUITY_FALLBACK == contracts.command_route_record(
        "__canonical-promotion-unknown__", ROOT
    )["specialist"]
    source = inspect.getsource(services)
    assert "DEFAULT_COMMAND_ROUTES = {" not in source
    assert "DEFAULT_COMMAND_ROUTES = command_route_map()" in source


def test_router_governance_required_specialists_are_machine_derived():
    assert services.DEFAULT_GOVERNANCE_REQUIRED_SPECIALISTS == contracts.governance_required_specialists(ROOT)
    source = inspect.getsource(services.RouterService)
    assert "{\"dagger\", \"cipher\", \"the-steward\", \"the-governor\"}" not in source
    assert "DEFAULT_GOVERNANCE_REQUIRED_SPECIALISTS" in source


def test_default_governance_validator_rules_match_machine_policy():
    validator = GovernanceValidator()
    actual = tuple(
        {
            "rule_id": rule.name,
            "skill_slugs": list(rule.skill_slugs),
            "command_names": list(rule.command_names),
            "validator_key": rule.validator_key,
            "dry_run_required": rule.name in validator._dry_run_required_rules,
        }
        for rule in validator._rules
    )
    expected = tuple(
        {
            "rule_id": str(record["rule_id"]),
            "skill_slugs": list(record.get("skill_slugs", [])),
            "command_names": list(record.get("command_names", [])),
            "validator_key": str(record.get("validator_key", "")),
            "dry_run_required": record.get("dry_run_required") is True,
        }
        for record in contracts.runtime_validation_rule_records(ROOT)
    )
    assert actual == expected


def test_default_governance_rules_fail_closed_on_duplicate_rule_identity(monkeypatch):
    records = (
        {
            "rule_id": "duplicate-rule",
            "skill_slugs": ["cipher"],
            "command_names": [],
            "validator_key": "governance_validated",
            "dry_run_required": False,
        },
        {
            "rule_id": "duplicate-rule",
            "skill_slugs": ["the-governor"],
            "command_names": [],
            "validator_key": "governance_validated",
            "dry_run_required": False,
        },
    )
    monkeypatch.setattr(services, "_DEFAULT_RUNTIME_VALIDATION_RULE_RECORDS", records)

    with pytest.raises(RuntimeInitializationError, match="machine governance validation rule is invalid"):
        services._default_governance_rules()


def test_default_governance_rules_fail_closed_when_machine_policy_has_no_runtime_rules(monkeypatch):
    monkeypatch.setattr(services, "_DEFAULT_RUNTIME_VALIDATION_RULE_RECORDS", ())

    with pytest.raises(RuntimeInitializationError, match="machine governance policy contains no runtime validation rules"):
        services._default_governance_rules()


def test_machine_dry_run_requirement_is_enforced_without_rule_name_special_case():
    validator = GovernanceValidator()
    decision = _decision("dagger", "dagger")

    blocked = validator.validate(
        decision,
        _context(destructive_validated=True, governance_validated=True, dry_run=False),
    )
    assert blocked.allowed is False
    assert blocked.status == "BLOCKED_PENDING_VALIDATION"
    assert "destructive execution requires dry-run mode" in blocked.reasons

    approved = validator.validate(
        decision,
        _context(destructive_validated=True, governance_validated=True, dry_run=True),
    )
    assert approved.allowed is True
    assert approved.status == "APPROVED"

    source = inspect.getsource(services.GovernanceValidator)
    assert 'rule.name == "destructive-skill-approval"' not in source
    assert "rule.name in self._dry_run_required_rules" in source


def test_machine_policy_does_not_require_dry_run_for_high_risk_security_rule():
    validator = GovernanceValidator()
    result = validator.validate(
        _decision("security-check", "cipher"),
        _context(destructive_validated=False, governance_validated=True, dry_run=False),
    )
    assert result.allowed is True
    assert result.status == "APPROVED"


def test_runtime_services_assert_complete_machine_contracts_before_deriving_defaults():
    source = inspect.getsource(services)
    assert "assert_machine_contracts()" in source
    assert source.index("assert_machine_contracts()") < source.index("DEFAULT_COMMAND_ROUTES = command_route_map()")
