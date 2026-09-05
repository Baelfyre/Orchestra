from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_oee7_replay_record_preserves_supported_historical_precision() -> None:
    replay = _load("docs/governance/oee_7_uief5_controlled_replay.v1.json")
    historical = replay["historical_observed"]
    controlled = replay["oee_replay"]
    comparison = replay["comparison"]

    assert replay["result"] == "OEE_7_EFFICIENCY_EVIDENCE_PASS"
    assert historical["canonical_phase_advance"] == 0
    assert historical["disposition"] == "BLOCKED_PRE_IMPLEMENTATION_REVIEW"
    assert set(historical["unique_specialist_roles_observed"]) == {
        "clockwork",
        "overseer",
        "cloak",
        "arbiter",
    }
    assert historical["exact_historical_invocation_count"] is None
    assert historical["exact_historical_retry_count"] is None
    assert historical["exact_historical_repository_wide_search_count"] is None
    assert historical["exact_historical_token_or_usage_units"] is None

    assert controlled["owner_first_specialist"] == "cloak"
    assert controlled["active_specialist_count_before_decisive_stop"] == 1
    assert controlled["decisive_stop"]["downstream_execution_allowed"] is False
    assert controlled["active_ci_watch"] is False
    assert controlled["disposition"] == historical["disposition"]

    assert comparison["same_or_safer_disposition"] is True
    assert comparison["historical_unique_specialist_roles"] == 4
    assert comparison["replay_active_specialists_before_stop"] == 1
    assert comparison["unsupported_precision_claims_made"] is False


def test_oee8_closeout_covers_exact_phase_set_and_preserves_uief_blockers() -> None:
    closeout = _load("docs/governance/oee_8_integration_closeout.v1.json")
    phases = closeout["phases"]

    assert closeout["status"] == "OEE_PROGRAM_COMPLETE_CANDIDATE"
    assert [item["phase"] for item in phases] == [f"OEE-{index}" for index in range(9)]
    assert phases[0]["status"] == "COMPLETE_CANONICAL_VERIFIED"
    assert all(item["evidence"] for item in phases)

    resume = closeout["resume_disposition"]
    assert resume["oee_program_ready_for_canonical_qualification"] is True
    assert resume["uief_lane_may_reopen_after_oee_canonicalization"] is True
    assert resume["uief_5_implementation_unblocked"] is False
    assert set(resume["remaining_uief_5_blockers"]) == {
        "UIEF5_UPSTREAM_RESPONSIVE_CONTRADICTION",
        "UIEF5_UNRESOLVED_PROVENANCE_REFERENCES",
    }

    assert all(value is False for value in closeout["authority"].values())
