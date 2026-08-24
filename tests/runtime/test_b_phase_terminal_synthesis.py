from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_b3_terminal_result_and_b4_b5_dispositions_are_consistent() -> None:
    b2 = load("machine/benchmarking/b2-5-confirmatory-reconciliation.v1.json")
    b3 = load("machine/benchmarking/b3-confirmatory-reconciliation.v1.json")
    b4 = load("machine/benchmarking/b4-controlled-interaction-disposition.v1.json")
    b5 = load("machine/benchmarking/b5-final-evidence-synthesis.v1.json")

    assert b3["execution"] == {
        "planned_runs": 450,
        "accepted_runs": 450,
        "invalid_runs": 0,
        "live_model_calls_consumed": 450,
        "accepted_total_tokens": 8885182,
        "session_status": "COMPLETE",
        "stop_reason": None,
    }
    assert b3["b3_terminal_conclusion"]["murmurs_benefit"] == "CONFIRMATORY_BENEFIT_NOT_ESTABLISHED"
    assert not b3["primary_analysis"]["practical_threshold_pass"]
    assert not b3["primary_analysis"]["bootstrap_lower_bound_pass"]
    assert not b3["primary_analysis"]["sign_test_pass"]
    assert b2["b2_terminal_conclusion"]["b4_isolated_b2_benefit_prerequisite"] == "NOT_SATISFIED"
    assert b4["status"] == "NOT_ELIGIBLE_NO_EXECUTION"
    assert b4["decision"]["live_model_calls_consumed"] == 0
    assert b5["separate_conclusions"] == {
        "a5_topology_benefit": "CONFIRMATORY_BENEFIT_NOT_ESTABLISHED",
        "murmurs_benefit": "CONFIRMATORY_BENEFIT_NOT_ESTABLISHED",
        "a5_murmurs_interaction": "NOT_RUN_NOT_ELIGIBLE",
    }
    assert b5["resource_history"]["total_b_phase_model_calls"] == 911
