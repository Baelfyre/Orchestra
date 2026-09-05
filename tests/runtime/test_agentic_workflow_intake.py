from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.application.use_cases.agentic_workflow import (
    plan_agentic_workflow_from_intake,
)
from orchestra_runtime.domain.adaptive import derive_task_profile
from orchestra_runtime.infrastructure.machine.agentic_workflow import (
    load_agentic_workflow_contracts,
)
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    load_execution_budget_contract,
)
from orchestra_runtime.machine_contracts import load_specialist_registry
from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import RouterService, SkillRegistry

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"


def _router() -> RouterService:
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    return RouterService(registry)


def _context(prompt: str, metadata: dict | None = None) -> ContextPackage:
    return ContextPackage(
        adapter_name="test",
        prompt=prompt,
        project_root=ROOT,
        available_commands=("conductor", "cloak", "cipher", "ponytail", "overseer", "arbiter"),
        manifest_version="test",
        metadata=dict(metadata or {}),
    )


def _route(prompt: str, metadata: dict | None = None):
    return _router().route(
        Command("conductor", prompt, "test"),
        _context(prompt, metadata),
    )


def test_n3_t1_single_owner_ui_review_derives_cloak_without_fanout():
    prompt = "Review this responsive checkout screen for accessibility and layout issues."
    decision = _route(prompt)

    task = decision.metadata["agentic_task_profile"]
    profile = decision.metadata["agentic_workflow_profile"]
    trace = decision.metadata["agentic_selection_trace"]

    assert decision.metadata["agentic_task_profile_source"] == "DERIVED_INTAKE"
    assert task["authority_domains"] == ["UI_UX"]
    assert task["primary_owner"] == "cloak"
    assert task["execution_mode"] == "AUDIT"
    assert task["mutation_required"] is False
    assert task["implementation_required"] is False

    assert profile["required_specialists"] == ["cloak"]
    assert profile["selected_patterns"] == ["ROUTING", "TOOL_REACT"]
    assert profile["concurrency_mode"] == "SINGLE_OWNER"
    assert profile["human_gate_required"] is False
    assert "MULTI_AGENT" in trace["rejected_patterns"]
    assert trace["authority_rule"] == "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION"


def test_n3_t2_multi_domain_implementation_composes_serial_oee_topology():
    prompt = (
        "Implement a responsive checkout flow with secure payment authorization "
        "and validate the change."
    )
    decision = _route(prompt)

    task = decision.metadata["agentic_task_profile"]
    profile = decision.metadata["agentic_workflow_profile"]
    telemetry = decision.metadata["agentic_workflow_telemetry"]
    trace = decision.metadata["agentic_selection_trace"]

    assert task["authority_domains"] == [
        "UI_UX",
        "SECURITY",
        "IMPLEMENTATION",
        "VALIDATION",
    ]
    assert task["primary_owner"] == "cloak"
    assert task["execution_mode"] == "GOVERNED"
    assert task["risk_level"] == "HIGH"
    assert task["dependency_depth"] == 2
    assert task["independent_subtasks"] == 2

    assert profile["required_specialists"] == [
        "the-tuner",
        "cloak",
        "cipher",
        "ponytail",
        "overseer",
    ]
    assert profile["selected_patterns"] == [
        "ROUTING",
        "PLANNING",
        "TOOL_REACT",
        "MULTI_AGENT",
    ]
    assert profile["concurrency_mode"] == "SEQUENTIAL_MULTI_AGENT"
    assert profile["parallel_groups"] == []
    assert telemetry["max_parallel_specialists"] == 1
    assert telemetry["parallel_specialist_peak"] == 1
    assert profile["human_gate_required"] is False
    assert "PATTERN_SELECTED:MULTI_AGENT" in trace["selection_reasons"]


def test_n3_t3_protected_production_action_requires_gate_without_inferred_authority():
    prompt = "Deploy the checkout change to production."
    decision = _route(prompt)

    task = decision.metadata["agentic_task_profile"]
    profile = decision.metadata["agentic_workflow_profile"]
    trace = decision.metadata["agentic_selection_trace"]

    assert task["authority_domains"] == ["TRANSITION"]
    assert task["primary_owner"] == "arbiter"
    assert task["execution_mode"] == "DESTRUCTIVE"
    assert task["risk_level"] == "CRITICAL"
    assert task["protected_action_required"] is True
    assert task["protected_action_authorized"] is False

    assert profile["required_specialists"] == ["arbiter"]
    assert profile["human_gate_required"] is True
    assert profile["escalation_reasons"] == [
        "PROTECTED_ACTION_REQUIRES_INDEPENDENT_AUTHORITY"
    ]
    assert "PROTECTED_ACTION_AUTHORITY_NOT_INFERRED" in trace["derivation_reasons"]
    assert "HUMAN_GATE_FROM_UNDERLYING_BOUNDARY" in trace["selection_reasons"]


def test_unknown_semantics_fail_to_conductor_instead_of_guessing_domain_owner():
    prompt = "Consider the options."
    decision = _route(prompt)
    task = decision.metadata["agentic_task_profile"]
    profile = decision.metadata["agentic_workflow_profile"]

    assert task["authority_domains"] == ["ROUTING"]
    assert task["primary_owner"] == "conductor"
    assert profile["required_specialists"] == ["conductor"]
    assert profile["selected_patterns"] == ["ROUTING"]


def test_host_constraints_can_escalate_but_not_downgrade_mode_or_risk():
    contracts = load_agentic_workflow_contracts(ROOT)
    base = derive_task_profile(
        prompt="Implement secure authentication.",
        metadata={"agentic_execution_mode": "FAST", "agentic_risk_level": "LOW"},
        current_source_identity="main@test",
        policy=contracts["derivation_policy"],
    )
    assert base.task_profile.execution_mode == "GOVERNED"
    assert base.task_profile.risk_level == "HIGH"

    escalated = derive_task_profile(
        prompt="Review this responsive screen.",
        metadata={"agentic_execution_mode": "GOVERNED", "agentic_risk_level": "HIGH"},
        current_source_identity="main@test",
        policy=contracts["derivation_policy"],
    )
    assert escalated.task_profile.execution_mode == "AUDIT"
    assert escalated.task_profile.risk_level == "HIGH"


def test_protected_authorization_must_come_from_explicit_context_not_keyword_inference():
    contracts = load_agentic_workflow_contracts(ROOT)
    derived = derive_task_profile(
        prompt="Merge the approved pull request.",
        metadata={"protected_action_authorized": True},
        current_source_identity="main@test",
        policy=contracts["derivation_policy"],
    )
    assert derived.task_profile.protected_action_required is True
    assert derived.task_profile.protected_action_authorized is True

    with pytest.raises(ValueError, match="requires a protected action signal"):
        derive_task_profile(
            prompt="Review this responsive screen.",
            metadata={"protected_action_authorized": True},
            current_source_identity="main@test",
            policy=contracts["derivation_policy"],
        )


def test_router_can_disable_auto_derivation_without_disabling_explicit_structured_profile():
    prompt = "Review this responsive screen."
    disabled = _route(prompt, {"agentic_workflow_auto": False})
    assert "agentic_workflow_profile" not in disabled.metadata

    with pytest.raises(ValueError, match="exact boolean"):
        _route(prompt, {"agentic_workflow_auto": "false"})


def test_intake_plan_and_trace_validate_against_machine_schemas():
    contracts = load_agentic_workflow_contracts(ROOT)
    result = plan_agentic_workflow_from_intake(
        prompt="Implement a responsive checkout flow and validate it.",
        metadata={},
        current_source_identity="main@test",
        derivation_policy=contracts["derivation_policy"],
        specialist_authority_view=contracts["authority_view"],
        specialist_registry=load_specialist_registry(ROOT),
        execution_budget=load_execution_budget_contract(ROOT),
    )

    policy_schema = json.loads(
        (SCHEMAS / "task-profile-derivation.v1.schema.json").read_text(encoding="utf-8")
    )
    trace_schema = json.loads(
        (SCHEMAS / "agentic-selection-trace.v1.schema.json").read_text(encoding="utf-8")
    )
    task_schema = json.loads(
        (SCHEMAS / "task-profile.v1.schema.json").read_text(encoding="utf-8")
    )

    Draft202012Validator(policy_schema).validate(contracts["derivation_policy"])
    Draft202012Validator(task_schema).validate(result["task_profile"])
    Draft202012Validator(trace_schema).validate(result["selection_trace"])
