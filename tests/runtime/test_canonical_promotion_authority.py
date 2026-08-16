from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from orchestra_runtime import machine_contracts as contracts
from orchestra_runtime import models, services
from orchestra_runtime.errors import RuntimeInitializationError
from orchestra_runtime.models import ContextPackage, RouteDecision, VALID_SPECIALISTS
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import GovernanceValidator, RouterService, SkillRegistry


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


def test_legacy_specialist_identity_import_is_a_derived_compatibility_view():
    assert VALID_SPECIALISTS == contracts.valid_specialist_ids(ROOT)
    source = inspect.getsource(models)
    assert "VALID_SPECIALISTS =" not in source
    assert 'if name == "VALID_SPECIALISTS"' in source
    assert "return valid_specialist_ids()" in source


def test_legacy_service_authority_snapshots_are_absent():
    for name in (
        "DEFAULT_COMMAND_ROUTES",
        "DEFAULT_AMBIGUITY_FALLBACK",
        "DEFAULT_GOVERNANCE_REQUIRED_SPECIALISTS",
        "_DEFAULT_RUNTIME_VALIDATION_RULE_RECORDS",
        "_DEFAULT_DRY_RUN_REQUIRED_RULES",
    ):
        assert not hasattr(services, name)


def test_skill_registry_and_router_read_machine_routing_contract_directly():
    expected_routes = contracts.command_route_map(ROOT)
    expected_fallback = contracts.command_route_record("__legacy-retired-unknown__", ROOT)["specialist"]
    expected_governance = contracts.governance_required_specialists(ROOT)

    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    router = RouterService(registry)

    assert registry._command_routes == expected_routes
    assert router._command_routes == expected_routes
    assert router._fallback_specialist == expected_fallback
    assert router._governance_required_specialists == expected_governance

    source = inspect.getsource(services.RouterService)
    assert "command_route_map()" in source
    assert "command_route_record(" in source
    assert "governance_required_specialists()" in source


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


def test_default_governance_rules_fail_closed_on_duplicate_rule_identity():
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

    with pytest.raises(RuntimeInitializationError, match="machine governance validation rule is invalid"):
        services._default_governance_rules(records)


def test_default_governance_rules_fail_closed_when_machine_policy_has_no_runtime_rules():
    with pytest.raises(RuntimeInitializationError, match="machine governance policy contains no runtime validation rules"):
        services._default_governance_rules(())


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


def test_runtime_services_fail_closed_before_consuming_machine_contracts():
    source = inspect.getsource(services)
    assert "assert_machine_contracts()" in source
    assert source.index("assert_machine_contracts()") < source.index("class SkillRegistry")
    assert source.index("assert_machine_contracts()") < source.index("class RouterService")
    assert source.index("assert_machine_contracts()") < source.index("class GovernanceValidator")
