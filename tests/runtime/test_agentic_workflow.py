from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from orchestra_runtime.application.use_cases.agentic_workflow import plan_agentic_workflow
from orchestra_runtime.infrastructure.machine.agentic_workflow import (
    load_agentic_workflow_contracts,
)
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    load_execution_budget_contract,
)
from orchestra_runtime.machine_contracts import load_specialist_registry

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"


def _task(**overrides):
    data = {
        "schema_version": "orchestra.task-profile.v1",
        "task_id": "awf-test",
        "goal": "Resolve the minimum authoritative workflow.",
        "execution_mode": "GOVERNED",
        "risk_level": "MEDIUM",
        "authority_domains": ["UI_UX"],
        "primary_owner": None,
        "dependency_depth": 0,
        "independent_subtasks": 0,
        "parallelizable": False,
        "mutation_required": False,
        "implementation_required": False,
        "validation_required": False,
        "transition_required": False,
        "external_state_required": True,
        "protected_action_required": False,
        "protected_action_authorized": False,
        "objective_verifier_available": True,
        "critic_owner": None,
        "critic_domain": None,
        "reentry_specialists": [],
        "current_source_identity": "main@example",
        "human_gate_requirements": [],
    }
    data.update(overrides)
    return data


def _plan(task):
    contracts = load_agentic_workflow_contracts(ROOT)
    return plan_agentic_workflow(
        task_profile=task,
        specialist_authority_view=contracts["authority_view"],
        specialist_registry=load_specialist_registry(ROOT),
        execution_budget=load_execution_budget_contract(ROOT),
    )


def test_awf_machine_contracts_are_source_bound_and_complete():
    contracts = load_agentic_workflow_contracts(ROOT)
    authority = contracts["authority_view"]
    assert len(authority["specialists"]) == 14
    dispatch = [item["slug"] for item in authority["specialists"] if item["can_dispatch"]]
    transition = [item["slug"] for item in authority["specialists"] if item["can_transition"]]
    validation = [item["slug"] for item in authority["specialists"] if item["can_validate"]]
    coordination = [item["slug"] for item in authority["specialists"] if item["can_coordinate"]]
    implementation = [item["slug"] for item in authority["specialists"] if item["can_implement"]]
    assert dispatch == ["conductor"]
    assert transition == ["arbiter"]
    assert validation == ["overseer"]
    assert coordination == ["the-tuner"]
    assert implementation == ["ponytail"]
    assert all(not item["can_execute_protected_action_without_external_authority"] for item in authority["specialists"])


def test_uief5_owner_first_replay_selects_only_cloak():
    result = _plan(_task(task_id="uief5-replay"))
    profile = result["workflow_profile"]
    assert profile["primary_owner"] == "cloak"
    assert profile["required_specialists"] == ["cloak"]
    assert profile["selected_patterns"] == ["ROUTING", "TOOL_REACT"]
    assert profile["concurrency_mode"] == "SINGLE_OWNER"
    assert profile["human_gate_required"] is False
    assert profile["topology_change_requires_human_approval"] is False
    assert profile["authority_expansion"] is False


def test_cross_domain_work_selects_multi_agent_semantics_but_preserves_oee_serial_default():
    result = _plan(
        _task(
            task_id="cross-domain",
            authority_domains=["UI_UX", "ARCHITECTURE"],
            dependency_depth=2,
            independent_subtasks=2,
            parallelizable=True,
            mutation_required=True,
            implementation_required=True,
            validation_required=True,
        )
    )
    profile = result["workflow_profile"]
    assert profile["required_specialists"] == [
        "the-tuner",
        "cloak",
        "clockwork",
        "ponytail",
        "overseer",
    ]
    assert profile["selected_patterns"] == [
        "ROUTING",
        "PLANNING",
        "TOOL_REACT",
        "MULTI_AGENT",
    ]
    assert profile["max_parallel_specialists"] == 1
    assert profile["parallel_groups"] == []
    assert profile["concurrency_mode"] == "SEQUENTIAL_MULTI_AGENT"


def test_topology_complexity_does_not_create_human_gate():
    result = _plan(
        _task(
            task_id="adaptive-no-gate",
            authority_domains=["SECURITY", "ARCHITECTURE", "IMPLEMENTATION"],
            dependency_depth=3,
            independent_subtasks=2,
            parallelizable=True,
            mutation_required=True,
            implementation_required=True,
            validation_required=True,
        )
    )
    profile = result["workflow_profile"]
    assert "MULTI_AGENT" in profile["selected_patterns"]
    assert profile["human_gate_required"] is False
    assert profile["topology_change_requires_human_approval"] is False


def test_protected_action_boundary_not_topology_triggers_human_gate():
    result = _plan(
        _task(
            task_id="protected-boundary",
            authority_domains=["IMPLEMENTATION"],
            mutation_required=True,
            implementation_required=True,
            protected_action_required=True,
            protected_action_authorized=False,
        )
    )
    profile = result["workflow_profile"]
    assert profile["human_gate_required"] is True
    assert profile["escalation_reasons"] == [
        "PROTECTED_ACTION_REQUIRES_INDEPENDENT_AUTHORITY"
    ]


def test_authorized_protected_action_does_not_add_second_topology_gate():
    result = _plan(
        _task(
            task_id="authorized-protected-boundary",
            authority_domains=["IMPLEMENTATION"],
            mutation_required=True,
            implementation_required=True,
            protected_action_required=True,
            protected_action_authorized=True,
        )
    )
    profile = result["workflow_profile"]
    assert profile["human_gate_required"] is False
    assert profile["topology_change_requires_human_approval"] is False


def test_explicit_distinct_critic_adds_bounded_reflection_contract():
    result = _plan(
        _task(
            task_id="security-critic",
            authority_domains=["IMPLEMENTATION"],
            mutation_required=True,
            implementation_required=True,
            validation_required=True,
            critic_owner="cipher",
            critic_domain="SECURITY",
        )
    )
    profile = result["workflow_profile"]
    critic = result["critic_contract"]
    assert "REFLECTION_CRITIC" in profile["selected_patterns"]
    assert critic["critic_owner"] == "cipher"
    assert critic["evaluation_domain"] == "SECURITY"
    assert critic["evidence_owner"] == "overseer"
    assert critic["can_transition"] is False
    assert critic["max_iterations"] == 1


def test_invalidation_reentry_activates_tuner_without_new_human_gate():
    result = _plan(
        _task(
            task_id="reentry",
            authority_domains=["IMPLEMENTATION"],
            mutation_required=True,
            implementation_required=True,
            reentry_specialists=["cipher", "clockwork"],
        )
    )
    profile = result["workflow_profile"]
    assert profile["required_specialists"] == ["the-tuner", "ponytail", "cipher", "clockwork"]
    assert "MULTI_AGENT" in profile["selected_patterns"]
    assert profile["human_gate_required"] is False
    assert result["telemetry"]["reentry_specialist_count"] == 2


def test_generated_task_and_workflow_records_validate_against_draft_2020_12_schemas():
    task = _task(task_id="schema-check")
    result = _plan(task)
    task_schema = json.loads((SCHEMAS / "task-profile.v1.schema.json").read_text(encoding="utf-8"))
    workflow_schema = json.loads((SCHEMAS / "agentic-workflow-profile.v1.schema.json").read_text(encoding="utf-8"))
    authority_schema = json.loads((SCHEMAS / "specialist-authority-view.v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(task_schema).validate(result["task_profile"])
    Draft202012Validator(workflow_schema).validate(result["workflow_profile"])
    Draft202012Validator(authority_schema).validate(load_agentic_workflow_contracts(ROOT)["authority_view"])
