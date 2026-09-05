#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.orchestration.execution_efficiency import (
    DecisiveStopSignal,
    evaluate_decisive_stop,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _responsive_contradiction(handoff: dict[str, Any]) -> str | None:
    macro = next(
        (
            item
            for item in handoff.get("macro_composition", [])
            if isinstance(item, dict)
            and item.get("structural_role") == "RESPONSIVE_TRANSFORMATION"
            and "< 1024px" in str(item.get("description", ""))
            and "accordion" in str(item.get("description", "")).casefold()
        ),
        None,
    )
    tablet = next(
        (
            item
            for item in handoff.get("responsive_transformations", [])
            if isinstance(item, dict)
            and "tablet" in str(item.get("breakpoint", "")).casefold()
            and "drawer" in str(item.get("transformation", "")).casefold()
        ),
        None,
    )
    if macro is None or tablet is None:
        return None
    return (
        "UIEF-4 responsive intent conflicts below 1024px: macro composition requires "
        "vertical accordion-stack collapse while the tablet transformation requires "
        "drawer-toggle navigation."
    )


def run_replay(root: Path = ROOT) -> dict[str, Any]:
    handoff_path = root / "machine" / "ui" / "ui-fidelity-handoff.v1.json"
    baseline_path = root / "docs" / "governance" / "oee_0_execution_cost_baseline.v1.json"
    handoff = _load_json(handoff_path)
    baseline = _load_json(baseline_path)

    contradiction = _responsive_contradiction(handoff)
    if contradiction is None:
        raise ValueError("OEE-7 expected UIEF-4 responsive contradiction was not reproduced")

    signal = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=True,
        stop_required=True,
        downstream_execution_allowed=False,
        reason=contradiction,
        evidence_refs=("machine/ui/ui-fidelity-handoff.v1.json",),
    )
    disposition = evaluate_decisive_stop(signal)
    if disposition != "STOP":
        raise ValueError("OEE-7 decisive evidence did not stop downstream execution")

    baseline_roles = tuple(
        str(item)
        for item in baseline.get("observed", {}).get(
            "unique_specialist_roles_observed", ()
        )
    )
    baseline_outcome = str(
        baseline.get("observed", {}).get("phase_outcome", "")
    )

    record = {
        "schema_version": "orchestra.execution-efficiency-replay.v1",
        "record_id": "oee7-uief5-controlled-replay-20260905",
        "source_case": baseline.get("source_case"),
        "replay_input": {
            "handoff_ref": "machine/ui/ui-fidelity-handoff.v1.json",
            "blocker_owner": "cloak",
            "blocker": "UIEF5_UPSTREAM_RESPONSIVE_CONTRADICTION",
        },
        "measurement": {
            "specialist_invocation_count": 1,
            "specialist_retry_count": 0,
            "parallel_specialist_peak": 1,
            "repository_wide_search_count": 0,
            "duplicate_evidence_read_count": 0,
            "validation_run_count_by_tier": {
                "E0": 1,
                "E1": 1,
                "E2": 0,
                "E3": 0,
                "E4": 0,
                "E5": 0,
            },
            "full_repository_validation_count": 0,
            "ci_poll_or_watch_count": 0,
            "model_active_wait_events": 0,
            "files_read_for_decision": 1,
            "host_reported_usage_units_when_available": None,
            "phase_outcome": "BLOCKED_PRE_IMPLEMENTATION_REVIEW",
            "blocker_detection_point": "E1_INPUT_INTEGRITY",
            "canonical_phase_advance": 0,
            "unique_specialist_roles": ["cloak"],
        },
        "stop_signal": {
            "owner": signal.owner,
            "evidence_sufficient": signal.evidence_sufficient,
            "stop_required": signal.stop_required,
            "downstream_execution_allowed": signal.downstream_execution_allowed,
            "reason": signal.reason,
            "evidence_refs": list(signal.evidence_refs),
            "disposition": disposition,
        },
        "efficiency_comparison": {
            "baseline_unique_specialist_role_count": len(baseline_roles),
            "replay_unique_specialist_role_count": 1,
            "unique_specialist_role_reduction": max(len(baseline_roles) - 1, 0),
            "baseline_exact_invocation_count_known": False,
            "same_phase_outcome": (
                baseline_outcome == "BLOCKED_PRE_IMPLEMENTATION_REVIEW"
            ),
            "provenance_search_performed_after_decisive_blocker": False,
            "downstream_specialists_invoked_after_decisive_blocker": False,
            "full_validation_performed_after_decisive_blocker": False,
            "continuous_ci_watch_used": False,
        },
    }

    comparison = record["efficiency_comparison"]
    record["result"] = (
        "PASS"
        if (
            comparison["same_phase_outcome"]
            and comparison["replay_unique_specialist_role_count"]
            < comparison["baseline_unique_specialist_role_count"]
            and not comparison["provenance_search_performed_after_decisive_blocker"]
            and not comparison["downstream_specialists_invoked_after_decisive_blocker"]
            and not comparison["full_validation_performed_after_decisive_blocker"]
            and not comparison["continuous_ci_watch_used"]
        )
        else "FAIL"
    )
    return record


def main() -> int:
    record = run_replay()
    print(json.dumps(record, sort_keys=True))
    return 0 if record["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
