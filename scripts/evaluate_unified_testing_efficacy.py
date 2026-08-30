#!/usr/bin/env python3
"""Deterministic offline efficacy evaluator for Orchestra's experimental UTM.

This evaluator compares:
1. DISTRIBUTED_EVIDENCE_PROXY_V1 — item-level aggregate checks only; and
2. the canonical UTM validate_packet()/aggregate_packet() contract.

It performs no model/provider calls, grants no authority, and treats malformed
UTM packets as fail-closed not-ready outcomes.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping

from orchestra_runtime.unified_testing import (
    SCHEMA_VERSION as UTM_PACKET_SCHEMA_VERSION,
    STAGE_IDS,
    STAGE_NAMES,
    STAGE_OWNERS,
    aggregate_packet,
)


STUDY_SCHEMA_VERSION = "orchestra.unified-testing-efficacy-study.v1"
RESULT_SCHEMA_VERSION = "orchestra.unified-testing-efficacy-result.v1"
PROGRAM_ID = "orchestra.unified-testing-mechanism-efficacy.v1"
BASELINE_ID = "DISTRIBUTED_EVIDENCE_PROXY_V1"
UTM_ID = "CANONICAL_UTM_AGGREGATOR_V1"
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MUTATIONS = {
    "NONE",
    "REMOVE_EVIDENCE",
    "SET_RESULT",
    "SET_STALE_REVISION",
    "DUPLICATE_EVIDENCE",
    "ADD_EVIDENCE_FOR_NA",
    "MAKE_NOT_APPLICABLE",
    "REMOVE_STAGE_DECLARATION",
    "SET_OWNERS",
    "REMOVE_TERMINAL_REFS",
}


class StudyError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StudyError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StudyError(f"cannot load JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rate(count: int, total: int) -> float:
    require(total > 0, "metric denominator must be positive")
    return round(count / total, 4)


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and _GIT_SHA_RE.fullmatch(value) is not None


def validate_study(study: Mapping[str, Any]) -> None:
    require(study.get("schema_version") == STUDY_SCHEMA_VERSION, "unsupported study schema_version")
    require(study.get("program_id") == PROGRAM_ID, "unexpected program_id")
    require(study.get("stage") == "CALIBRATION", "this evaluator accepts CALIBRATION only")

    subject = study.get("frozen_subject")
    require(isinstance(subject, Mapping), "frozen_subject must be an object")
    require(subject.get("repository") == "Baelfyre/Orchestra", "unexpected frozen repository")
    require(_is_sha(subject.get("revision_sha")), "frozen_subject.revision_sha must be exact lowercase Git SHA")
    require(_is_sha(subject.get("tree_sha")), "frozen_subject.tree_sha must be exact lowercase Git SHA")
    require(_is_sha(subject.get("baseline_parent_sha")), "frozen_subject.baseline_parent_sha must be exact lowercase Git SHA")
    require(_is_sha(subject.get("baseline_parent_tree")), "frozen_subject.baseline_parent_tree must be exact lowercase Git SHA")

    baseline = study.get("baseline_proxy")
    require(isinstance(baseline, Mapping) and baseline.get("id") == BASELINE_ID, "unexpected baseline proxy")
    utm = study.get("utm_evaluator")
    require(isinstance(utm, Mapping) and utm.get("id") == UTM_ID, "unexpected UTM evaluator")

    prereg = study.get("preregistration")
    require(isinstance(prereg, Mapping), "preregistration must be an object")
    for field in (
        "all_attempts_retained",
        "outcome_based_retry_prohibited",
        "selective_exclusion_prohibited",
        "post_start_metric_change_prohibited",
        "negative_inconclusive_preserved",
    ):
        require(prereg.get(field) is True, f"preregistration.{field} must be true")
    thresholds = prereg.get("thresholds")
    require(isinstance(thresholds, Mapping), "preregistration.thresholds must be an object")

    boundaries = study.get("measurement_boundaries")
    require(isinstance(boundaries, Mapping), "measurement_boundaries must be an object")
    require(boundaries.get("live_model_calls") == 0, "live_model_calls must be zero")
    require(boundaries.get("provider_calls") == 0, "provider_calls must be zero")

    complexity = study.get("complexity_snapshot")
    require(isinstance(complexity, Mapping), "complexity_snapshot must be an object")
    require(complexity.get("new_runtime_dependencies") == 0, "efficacy study assumes zero new runtime dependencies")
    require(complexity.get("second_test_engine") is False, "UTM must not become a second test engine")
    require(complexity.get("runtime_integration") is False, "UTM must remain non-default during efficacy calibration")

    cases = study.get("cases")
    require(isinstance(cases, list) and len(cases) >= 10, "at least ten efficacy cases are required")
    seen: set[str] = set()
    for case in cases:
        require(isinstance(case, Mapping), "every case must be an object")
        case_id = case.get("case_id")
        require(isinstance(case_id, str) and case_id, "case_id must be non-empty")
        require(case_id not in seen, f"duplicate case_id: {case_id}")
        seen.add(case_id)
        required_stages = case.get("required_stages")
        require(isinstance(required_stages, list), f"{case_id}.required_stages must be an array")
        require(len(set(required_stages)) == len(required_stages), f"{case_id}.required_stages cannot contain duplicates")
        require(set(required_stages).issubset(set(STAGE_IDS)), f"{case_id}.required_stages contains unknown stage")
        require({"T0", "T9"}.issubset(set(required_stages)), f"{case_id} base fixture must require T0 and T9")
        require(isinstance(case.get("expected_readiness_evidence_complete"), bool), f"{case_id} expected result must be boolean")
        require(case.get("category") in {"CLEAN", "EVIDENCE_COMPLETENESS", "RISK_SIGNAL", "STRUCTURAL_INTEGRITY"}, f"{case_id} category invalid")
        mutation = case.get("mutation")
        require(isinstance(mutation, Mapping), f"{case_id}.mutation must be an object")
        require(mutation.get("kind") in _MUTATIONS, f"{case_id} mutation kind invalid")


def build_packet(case: Mapping[str, Any], subject_sha: str) -> dict[str, Any]:
    required = set(case["required_stages"])
    stages: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    for stage_id in STAGE_IDS:
        applicable = stage_id in required
        stages.append(
            {
                "stage_id": stage_id,
                "name": STAGE_NAMES[stage_id],
                "applicability": "REQUIRED" if applicable else "NOT_APPLICABLE",
                "owners": list(STAGE_OWNERS[stage_id]),
                "rationale": (
                    "Required for this bounded efficacy fixture."
                    if applicable
                    else "No relevant risk surface in this bounded efficacy fixture."
                ),
                "evidence_requirements": [f"evidence:{stage_id.lower()}"] if applicable else [],
            }
        )
        if applicable:
            evidence.append(
                {
                    "stage_id": stage_id,
                    "revision_sha": subject_sha,
                    "result": "PASS",
                    "evidence_refs": [f"artifact:{stage_id.lower()}"],
                    "limitations": [],
                }
            )

    packet: dict[str, Any] = {
        "schema_version": UTM_PACKET_SCHEMA_VERSION,
        "packet_id": f"utm.efficacy.{case['case_id'].lower()}",
        "subject": {"repository": "Baelfyre/Orchestra", "revision_sha": subject_sha},
        "release_intent": "NON_RELEASE",
        "stages": stages,
        "evidence": evidence,
        "human_signoff": {"status": "NOT_REQUESTED", "decision_owner": None, "evidence_refs": []},
    }
    apply_mutation(packet, case["mutation"])
    return packet


def _stage(packet: dict[str, Any], stage_id: str) -> dict[str, Any]:
    return next(item for item in packet["stages"] if item["stage_id"] == stage_id)


def _evidence(packet: dict[str, Any], stage_id: str) -> dict[str, Any]:
    return next(item for item in packet["evidence"] if item["stage_id"] == stage_id)


def apply_mutation(packet: dict[str, Any], mutation: Mapping[str, Any]) -> None:
    kind = mutation["kind"]
    if kind == "NONE":
        return

    stage_id = mutation.get("stage_id")
    require(stage_id in STAGE_IDS, f"{kind} requires a canonical stage_id")

    if kind == "REMOVE_EVIDENCE":
        packet["evidence"] = [item for item in packet["evidence"] if item["stage_id"] != stage_id]
    elif kind == "SET_RESULT":
        item = _evidence(packet, stage_id)
        result = mutation.get("result")
        require(result in {"PASS", "FAIL", "PENDING"}, "SET_RESULT result invalid")
        item["result"] = result
        if result == "PENDING":
            item["evidence_refs"] = []
    elif kind == "SET_STALE_REVISION":
        stale = "a" * 40
        if stale == packet["subject"]["revision_sha"]:
            stale = "b" * 40
        _evidence(packet, stage_id)["revision_sha"] = stale
    elif kind == "DUPLICATE_EVIDENCE":
        packet["evidence"].append(deepcopy(_evidence(packet, stage_id)))
    elif kind == "ADD_EVIDENCE_FOR_NA":
        packet["evidence"].append(
            {
                "stage_id": stage_id,
                "revision_sha": packet["subject"]["revision_sha"],
                "result": "PASS",
                "evidence_refs": [f"artifact:{stage_id.lower()}"],
                "limitations": [],
            }
        )
    elif kind == "MAKE_NOT_APPLICABLE":
        item = _stage(packet, stage_id)
        item["applicability"] = "NOT_APPLICABLE"
        item["evidence_requirements"] = []
        packet["evidence"] = [entry for entry in packet["evidence"] if entry["stage_id"] != stage_id]
    elif kind == "REMOVE_STAGE_DECLARATION":
        packet["stages"] = [item for item in packet["stages"] if item["stage_id"] != stage_id]
    elif kind == "SET_OWNERS":
        owners = mutation.get("owners")
        require(isinstance(owners, list) and owners, "SET_OWNERS requires owners")
        _stage(packet, stage_id)["owners"] = list(owners)
    elif kind == "REMOVE_TERMINAL_REFS":
        _evidence(packet, stage_id)["evidence_refs"] = []
    else:  # pragma: no cover - validate_study guards this
        raise StudyError(f"unsupported mutation kind: {kind}")


def baseline_disposition(packet: Mapping[str, Any]) -> str:
    """Evaluate only independent evidence-item signals.

    This intentionally does not inspect the T0-T9 applicability plan because
    that cross-stage contract is the capability under evaluation.
    """

    subject = packet.get("subject")
    if not isinstance(subject, Mapping):
        return "INVALID_EVIDENCE"
    subject_sha = str(subject.get("revision_sha") or "").strip().lower()
    if _GIT_SHA_RE.fullmatch(subject_sha) is None:
        return "INVALID_EVIDENCE"

    evidence = packet.get("evidence")
    if not isinstance(evidence, list):
        return "INVALID_EVIDENCE"

    pending = False
    for item in evidence:
        if not isinstance(item, Mapping):
            return "INVALID_EVIDENCE"
        result = item.get("result")
        if result not in {"PASS", "FAIL", "PENDING"}:
            return "INVALID_EVIDENCE"
        revision = str(item.get("revision_sha") or "").strip().lower()
        if revision != subject_sha:
            return "INVALID_EVIDENCE"
        refs = item.get("evidence_refs")
        if not isinstance(refs, list):
            return "INVALID_EVIDENCE"
        if result in {"PASS", "FAIL"} and not refs:
            return "INVALID_EVIDENCE"
        if result == "FAIL":
            return "BLOCKED"
        if result == "PENDING":
            pending = True
    return "WAIT_FOR_EVIDENCE" if pending else "READINESS_EVIDENCE_COMPLETE"


def utm_disposition(packet: Mapping[str, Any]) -> tuple[str, bool]:
    try:
        verdict = aggregate_packet(packet)
    except (ValueError, TypeError, KeyError):
        return "INVALID_PACKET", True

    authority_clear = all(
        getattr(verdict, field) is False
        for field in (
            "release_authorized",
            "merge_authorized",
            "deployment_authorized",
            "policy_activation_authorized",
        )
    )
    return verdict.disposition, authority_clear


def _metrics(rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    complete_key = f"{arm}_complete"
    clean = [row for row in rows if row["expected_complete"]]
    unsafe = [row for row in rows if not row["expected_complete"]]
    structural = [row for row in rows if row["category"] == "STRUCTURAL_INTEGRITY"]
    missing = [row for row in rows if row["category"] == "EVIDENCE_COMPLETENESS"]

    correct = sum(row[complete_key] == row["expected_complete"] for row in rows)
    detected = sum(not row[complete_key] for row in unsafe)
    false_positive = sum(not row[complete_key] for row in clean)
    false_negative = sum(row[complete_key] for row in unsafe)
    structural_detected = sum(not row[complete_key] for row in structural)
    missing_detected = sum(not row[complete_key] for row in missing)

    return {
        "decision_accuracy": {"count": correct, "total": len(rows), "rate": _rate(correct, len(rows))},
        "risk_detection": {"count": detected, "total": len(unsafe), "rate": _rate(detected, len(unsafe))},
        "false_positives": {"count": false_positive, "total": len(clean), "rate": _rate(false_positive, len(clean))},
        "false_negatives": {"count": false_negative, "total": len(unsafe), "rate": _rate(false_negative, len(unsafe))},
        "structural_violation_detection": {
            "count": structural_detected,
            "total": len(structural),
            "rate": _rate(structural_detected, len(structural)),
        },
        "missing_evidence_detection": {
            "count": missing_detected,
            "total": len(missing),
            "rate": _rate(missing_detected, len(missing)),
        },
    }


def evaluate_study(study: Mapping[str, Any]) -> dict[str, Any]:
    validate_study(study)
    subject_sha = study["frozen_subject"]["revision_sha"]

    rows: list[dict[str, Any]] = []
    all_authority_clear = True
    for case in study["cases"]:
        packet = build_packet(case, subject_sha)
        baseline = baseline_disposition(packet)
        utm, authority_clear = utm_disposition(packet)
        baseline_complete = baseline == "READINESS_EVIDENCE_COMPLETE"
        utm_complete = utm == "READINESS_EVIDENCE_COMPLETE"
        all_authority_clear = all_authority_clear and authority_clear
        rows.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "expected_complete": case["expected_readiness_evidence_complete"],
                "baseline_disposition": baseline,
                "baseline_complete": baseline_complete,
                "utm_disposition": utm,
                "utm_complete": utm_complete,
                "baseline_correct": baseline_complete == case["expected_readiness_evidence_complete"],
                "utm_correct": utm_complete == case["expected_readiness_evidence_complete"],
                "utm_authority_clear": authority_clear,
            }
        )

    baseline_metrics = _metrics(rows, "baseline")
    utm_metrics = _metrics(rows, "utm")
    accuracy_gain = round(
        utm_metrics["decision_accuracy"]["rate"] - baseline_metrics["decision_accuracy"]["rate"], 4
    )

    thresholds = study["preregistration"]["thresholds"]
    threshold_results = {
        "utm_decision_accuracy_min": utm_metrics["decision_accuracy"]["rate"] >= thresholds["utm_decision_accuracy_min"],
        "utm_accuracy_gain_over_baseline_min": accuracy_gain >= thresholds["utm_accuracy_gain_over_baseline_min"],
        "utm_risk_detection_min": utm_metrics["risk_detection"]["rate"] >= thresholds["utm_risk_detection_min"],
        "utm_false_positive_rate_max": utm_metrics["false_positives"]["rate"] <= thresholds["utm_false_positive_rate_max"],
        "utm_false_negative_rate_max": utm_metrics["false_negatives"]["rate"] <= thresholds["utm_false_negative_rate_max"],
        "utm_structural_violation_detection_min": (
            utm_metrics["structural_violation_detection"]["rate"]
            >= thresholds["utm_structural_violation_detection_min"]
        ),
        "utm_missing_evidence_detection_min": (
            utm_metrics["missing_evidence_detection"]["rate"]
            >= thresholds["utm_missing_evidence_detection_min"]
        ),
        "authority_boundaries_preserved": all_authority_clear,
        "zero_live_model_calls": study["measurement_boundaries"]["live_model_calls"] == 0,
        "zero_provider_calls": study["measurement_boundaries"]["provider_calls"] == 0,
        "no_new_runtime_dependencies": study["complexity_snapshot"]["new_runtime_dependencies"] == 0,
        "not_second_test_engine": study["complexity_snapshot"]["second_test_engine"] is False,
        "runtime_integration_remains_disabled": study["complexity_snapshot"]["runtime_integration"] is False,
    }

    passed = all(threshold_results.values())
    recommendation = "ADOPT_OPTIONAL" if passed else "DEFER"

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "study_id": study["study_id"],
        "stage": study["stage"],
        "frozen_subject": deepcopy(study["frozen_subject"]),
        "case_count": len(rows),
        "case_results": rows,
        "baseline_metrics": baseline_metrics,
        "utm_metrics": utm_metrics,
        "accuracy_gain_over_baseline": accuracy_gain,
        "threshold_results": threshold_results,
        "all_preregistered_thresholds_passed": passed,
        "evidence_recommendation": recommendation,
        "recommendation_boundary": (
            "ADOPT_OPTIONAL is evidence advice only. It does not itself mutate the Feature Decision Record "
            "or grant merge, release, deployment, policy, destructive, or other protected-action authority."
        ),
        "measurement_boundaries": deepcopy(study["measurement_boundaries"]),
        "complexity_snapshot": deepcopy(study["complexity_snapshot"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-result", type=Path)
    args = parser.parse_args()

    result = evaluate_study(load_json(args.study))

    if args.check_result is not None:
        expected = load_json(args.check_result)
        if expected != result:
            raise StudyError("committed efficacy result does not match deterministic evaluation")

    if args.output is not None:
        write_json(args.output, result)
    elif args.check_result is None:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
