from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validation.run_oee7_controlled_replay import run_replay


ROOT = Path(__file__).resolve().parents[2]


def test_oee7_replays_real_uief5_blocker_with_less_orchestration_work() -> None:
    record = run_replay(ROOT)

    assert record["result"] == "PASS"
    assert record["replay_input"]["blocker_owner"] == "cloak"
    assert record["stop_signal"]["disposition"] == "STOP"
    assert record["stop_signal"]["downstream_execution_allowed"] is False

    measurement = record["measurement"]
    assert measurement["specialist_invocation_count"] == 1
    assert measurement["specialist_retry_count"] == 0
    assert measurement["parallel_specialist_peak"] == 1
    assert measurement["repository_wide_search_count"] == 0
    assert measurement["full_repository_validation_count"] == 0
    assert measurement["ci_poll_or_watch_count"] == 0
    assert measurement["blocker_detection_point"] == "E1_INPUT_INTEGRITY"
    assert measurement["canonical_phase_advance"] == 0

    comparison = record["efficiency_comparison"]
    assert comparison["baseline_unique_specialist_role_count"] == 4
    assert comparison["replay_unique_specialist_role_count"] == 1
    assert comparison["unique_specialist_role_reduction"] == 3
    assert comparison["same_phase_outcome"] is True


def test_oee7_stops_before_unrelated_provenance_search() -> None:
    comparison = run_replay(ROOT)["efficiency_comparison"]
    assert comparison["provenance_search_performed_after_decisive_blocker"] is False
    assert comparison["downstream_specialists_invoked_after_decisive_blocker"] is False
    assert comparison["full_validation_performed_after_decisive_blocker"] is False
    assert comparison["continuous_ci_watch_used"] is False


def test_oee7_fails_closed_when_the_expected_blocker_disappears(tmp_path: Path) -> None:
    handoff = json.loads(
        (ROOT / "machine/ui/ui-fidelity-handoff.v1.json").read_text(encoding="utf-8")
    )
    baseline = json.loads(
        (ROOT / "docs/governance/oee_0_execution_cost_baseline.v1.json").read_text(
            encoding="utf-8"
        )
    )

    for item in handoff["macro_composition"]:
        if item.get("structural_role") == "RESPONSIVE_TRANSFORMATION":
            item["description"] = (
                "Horizontal split-pane on viewports >= 1024px; drawer navigation below 1024px."
            )

    handoff_path = tmp_path / "machine/ui/ui-fidelity-handoff.v1.json"
    handoff_path.parent.mkdir(parents=True)
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

    baseline_path = tmp_path / "docs/governance/oee_0_execution_cost_baseline.v1.json"
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    with pytest.raises(ValueError, match="expected UIEF-4 responsive contradiction"):
        run_replay(tmp_path)
