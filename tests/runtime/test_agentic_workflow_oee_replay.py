from __future__ import annotations

from pathlib import Path

from orchestra_runtime.application.use_cases.agentic_workflow import plan_agentic_workflow
from orchestra_runtime.infrastructure.machine.agentic_workflow import load_agentic_workflow_contracts
from orchestra_runtime.infrastructure.machine.execution_efficiency import load_execution_budget_contract
from orchestra_runtime.machine_contracts import load_specialist_registry

ROOT = Path(__file__).resolve().parents[2]


def test_awf_replay_preserves_oee7_decisive_owner_and_minimum_specialist_set():
    task = {
        "schema_version": "orchestra.task-profile.v1",
        "task_id": "UIEF5_20260905_USAGE_EXHAUSTION",
        "goal": "Determine whether the upstream responsive handoff is decision-sufficient for UIEF-5.",
        "execution_mode": "AUDIT",
        "risk_level": "MEDIUM",
        "authority_domains": ["UI_UX"],
        "primary_owner": "cloak",
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
        "current_source_identity": "75100c3ad0fd9a11c69f2b9b7c5172edd8841cd2",
        "human_gate_requirements": [],
    }
    contracts = load_agentic_workflow_contracts(ROOT)
    result = plan_agentic_workflow(
        task_profile=task,
        specialist_authority_view=contracts["authority_view"],
        specialist_registry=load_specialist_registry(ROOT),
        execution_budget=load_execution_budget_contract(ROOT),
    )
    profile = result["workflow_profile"]
    assert profile["required_specialists"] == ["cloak"]
    assert "the-tuner" not in profile["required_specialists"]
    assert "clockwork" not in profile["required_specialists"]
    assert "ponytail" not in profile["required_specialists"]
    assert "overseer" not in profile["required_specialists"]
    assert profile["stop_conditions"][0] == "DECISIVE_BLOCKER"
