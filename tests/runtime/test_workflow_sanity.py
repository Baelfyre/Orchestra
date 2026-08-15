from pathlib import Path

from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
    evaluate_arbiter,
)
from orchestra_runtime.machine_contracts import (
    command_route_map,
    governance_required_specialists,
    runtime_validation_rule_records,
)
from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    DEFAULT_COMMAND_ROUTES,
    GovernanceValidator,
    RouterService,
    SkillRegistry,
)
from orchestra_runtime.workflow_contracts import build_workflow_sanity_receipt


ROOT = Path(__file__).resolve().parents[2]


def _route(command_name: str, metadata: dict | None = None):
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    router = RouterService(registry)
    governance = GovernanceValidator()
    command = Command(name=command_name, raw_input=command_name, adapter_name="codex")
    context = ContextPackage(
        adapter_name="codex",
        prompt=command_name,
        project_root=ROOT,
        available_commands=tuple(DEFAULT_COMMAND_ROUTES),
        manifest_version="1.4.0",
        metadata=metadata or {},
    )
    decision = router.route(command, context)
    return decision, governance.validate(decision, context)


def _decision(value="APPROVED", *, human_review_required=False):
    return GovernanceDecisionRecord(
        reviewer="workflow-sanity",
        project_context="workflow-sanity",
        decision=value,
        reason="sanity fixture",
        human_review_required=human_review_required,
        evidence_refs=("receipt:fixture",),
    )


def _arbiter(**overrides):
    values = {
        "project_id": "orchestra",
        "unit_id": "workflow-sanity",
        "governance_decisions": (_decision(),),
    }
    values.update(overrides)
    return evaluate_arbiter(ArbiterKernelInput(**values))


def test_machine_command_routes_match_existing_runtime_table_exactly():
    assert command_route_map(ROOT) == DEFAULT_COMMAND_ROUTES


def test_machine_governance_required_set_matches_runtime_router_behavior():
    expected = governance_required_specialists(ROOT)
    for command_name, specialist in DEFAULT_COMMAND_ROUTES.items():
        route, _ = _route(command_name)
        assert route.skill_slug == specialist
        assert route.governance_required is (specialist in expected)


def test_machine_validation_rules_match_existing_governance_validator():
    runtime_rules = GovernanceValidator()._rules
    machine_rules = runtime_validation_rule_records(ROOT)
    normalized_runtime = [
        {
            "rule_id": rule.name,
            "skill_slugs": list(rule.skill_slugs),
            "command_names": list(rule.command_names),
            "validator_key": rule.validator_key,
            "dry_run_required": rule.name == "destructive-skill-approval",
        }
        for rule in runtime_rules
    ]
    assert list(machine_rules) == normalized_runtime


def test_direct_architecture_workflow_fires_expected_route_and_continuation():
    route, validation = _route("review-architecture")
    arbiter = _arbiter()
    receipt = build_workflow_sanity_receipt(
        route,
        validation,
        arbiter_result=arbiter,
        evidence_refs=("receipt:source", "receipt:validation"),
    )
    assert receipt.route_id == "architecture-structure"
    assert receipt.specialist_id == "clockwork"
    assert receipt.governance_required is False
    assert receipt.validation_status == "NOT_REQUIRED"
    assert receipt.arbiter_disposition == "AUTO_CONTINUE"
    assert receipt.execution_order == (
        "ROUTING",
        "SPECIALIST_RESOLUTION",
        "GOVERNANCE_VALIDATION",
        "ARBITER_KERNEL",
    )
    assert receipt.evidence_refs == ("receipt:source", "receipt:validation")
    assert len(receipt.digest) == 64


def test_unknown_command_falls_back_to_conductor_and_is_receipted():
    route, validation = _route("unknown-cross-domain-command")
    receipt = build_workflow_sanity_receipt(route, validation)
    assert route.skill_slug == "conductor"
    assert receipt.route_id == "ambiguous-overlapping"
    assert receipt.validation_status == "NOT_REQUIRED"


def test_dagger_workflow_fails_closed_without_authority_evidence():
    route, validation = _route("resilience-check")
    receipt = build_workflow_sanity_receipt(route, validation)
    assert receipt.specialist_id == "dagger"
    assert receipt.route_id == "guarded-destructive-simulation"
    assert receipt.governance_required is True
    assert validation.allowed is False
    assert validation.status == "BLOCKED_PENDING_VALIDATION"
    assert "destructive-skill-approval" in receipt.validation_rules


def test_dagger_workflow_passes_only_with_validation_and_dry_run():
    route, validation = _route(
        "resilience-check",
        {"destructive_validated": True, "dry_run": True},
    )
    receipt = build_workflow_sanity_receipt(route, validation)
    assert validation.allowed is True
    assert receipt.validation_status == "APPROVED"
    assert receipt.validation_rules == ("destructive-skill-approval",)


def test_governor_workflow_requires_governance_validation():
    blocked_route, blocked = _route("the-governor")
    assert blocked.allowed is False
    approved_route, approved = _route("the-governor", {"governance_validated": True})
    receipt = build_workflow_sanity_receipt(approved_route, approved)
    assert approved.allowed is True
    assert receipt.specialist_id == "the-governor"
    assert receipt.validation_rules == ("high-risk-skill-approval",)
    assert blocked_route.skill_slug == approved_route.skill_slug


def test_stale_evidence_produces_wait_for_evidence_with_ordered_receipt():
    route, validation = _route("arbiter")
    arbiter = _arbiter(evidence_fresh=False)
    receipt = build_workflow_sanity_receipt(route, validation, arbiter_result=arbiter)
    assert arbiter.disposition is TransitionDisposition.WAIT_FOR_EVIDENCE
    assert receipt.arbiter_disposition == "WAIT_FOR_EVIDENCE"
    assert receipt.arbiter_reason_codes == ("EVIDENCE_STALE",)


def test_human_review_condition_produces_escalation():
    route, validation = _route("arbiter")
    arbiter = evaluate_arbiter(
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="workflow-sanity",
            governance_decisions=(_decision(human_review_required=True),),
        )
    )
    receipt = build_workflow_sanity_receipt(route, validation, arbiter_result=arbiter)
    assert receipt.arbiter_disposition == "ESCALATE_HUMAN"
    assert receipt.arbiter_reason_codes == ("HUMAN_REVIEW_REQUIRED",)


def test_authority_invalid_condition_produces_stop():
    route, validation = _route("arbiter")
    arbiter = _arbiter(authority_valid=False)
    receipt = build_workflow_sanity_receipt(route, validation, arbiter_result=arbiter)
    assert receipt.arbiter_disposition == "STOP"
    assert receipt.arbiter_reason_codes == ("AUTHORITY_INVALID",)


def test_bounded_revision_remediates_then_escalates_on_budget_exhaustion():
    route, validation = _route("arbiter")
    remediation = evaluate_arbiter(
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="workflow-sanity",
            governance_decisions=(_decision("REVISION_REQUIRED"),),
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            remediation_attempt_count=0,
        )
    )
    remediating_receipt = build_workflow_sanity_receipt(
        route,
        validation,
        arbiter_result=remediation,
    )
    assert remediating_receipt.arbiter_disposition == "AUTO_REMEDIATE_AND_REVALIDATE"

    exhausted = evaluate_arbiter(
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="workflow-sanity",
            governance_decisions=(_decision("REVISION_REQUIRED"),),
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            remediation_attempt_count=3,
        )
    )
    exhausted_receipt = build_workflow_sanity_receipt(
        route,
        validation,
        arbiter_result=exhausted,
    )
    assert exhausted_receipt.arbiter_disposition == "ESCALATE_HUMAN"
    assert exhausted_receipt.arbiter_reason_codes == ("REMEDIATION_BUDGET_EXHAUSTED",)
