from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.application.use_cases.agentic_workflow import plan_agentic_workflow
from orchestra_runtime.infrastructure.machine.agentic_workflow import load_agentic_workflow_contracts
from orchestra_runtime.infrastructure.machine.execution_efficiency import load_execution_budget_contract
from orchestra_runtime.machine_contracts import load_specialist_registry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "agentic-workflow" / "awf-scenarios.v1.json"


def test_awf_regression_scenarios_match_authority_safe_expected_topologies():
    suite = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert suite["schema_version"] == "orchestra.awf-regression-scenarios.v1"
    contracts = load_agentic_workflow_contracts(ROOT)
    registry = load_specialist_registry(ROOT)
    budget = load_execution_budget_contract(ROOT)

    historical = [case for case in suite["cases"] if case["evidence_kind"] == "HISTORICAL_REPLAY"]
    assert [case["id"] for case in historical] == ["uief5-responsive-blocker"]

    for case in suite["cases"]:
        result = plan_agentic_workflow(
            task_profile=case["task"],
            specialist_authority_view=contracts["authority_view"],
            specialist_registry=registry,
            execution_budget=budget,
        )
        profile = result["workflow_profile"]
        expected = case["expected"]
        for key in (
            "required_specialists",
            "selected_patterns",
            "concurrency_mode",
            "human_gate_required",
        ):
            assert profile[key] == expected[key], f"{case['id']} mismatch for {key}"
        assert profile["topology_change_requires_human_approval"] is False
        assert profile["authority_expansion"] is False
