from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.evaluate_unified_testing_efficacy import (
    StudyError,
    baseline_disposition,
    build_packet,
    evaluate_study,
    load_json,
    utm_disposition,
)


ROOT = Path(__file__).resolve().parents[2]
STUDY_PATH = ROOT / "machine" / "benchmarking" / "utm-efficacy-study.v1.json"
RESULT_PATH = ROOT / "machine" / "benchmarking" / "utm-efficacy-result.v1.json"


def _study() -> dict:
    return load_json(STUDY_PATH)


def test_committed_result_matches_deterministic_evaluation() -> None:
    result = evaluate_study(_study())
    committed = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert result == committed


def test_calibration_establishes_incremental_core_value_without_false_blocks() -> None:
    result = evaluate_study(_study())
    assert result["case_count"] == 15
    assert result["baseline_metrics"]["decision_accuracy"] == {"count": 8, "total": 15, "rate": 0.5333}
    assert result["baseline_metrics"]["risk_detection"] == {"count": 4, "total": 11, "rate": 0.3636}
    assert result["baseline_metrics"]["false_negatives"] == {"count": 7, "total": 11, "rate": 0.6364}

    assert result["utm_metrics"]["decision_accuracy"] == {"count": 15, "total": 15, "rate": 1.0}
    assert result["utm_metrics"]["risk_detection"] == {"count": 11, "total": 11, "rate": 1.0}
    assert result["utm_metrics"]["false_positives"] == {"count": 0, "total": 4, "rate": 0.0}
    assert result["utm_metrics"]["false_negatives"] == {"count": 0, "total": 11, "rate": 0.0}
    assert result["utm_metrics"]["structural_violation_detection"] == {"count": 7, "total": 7, "rate": 1.0}
    assert result["utm_metrics"]["missing_evidence_detection"] == {"count": 2, "total": 2, "rate": 1.0}
    assert result["accuracy_gain_over_baseline"] == 0.4667
    assert result["all_preregistered_thresholds_passed"] is True
    assert result["evidence_recommendation"] == "ADOPT_OPTIONAL"


def test_measurement_boundaries_do_not_invent_live_efficiency_claims() -> None:
    result = evaluate_study(_study())
    boundaries = result["measurement_boundaries"]
    assert boundaries["operator_effort_time"] == "UNMEASURED"
    assert boundaries["live_host_token_cost"] == "UNMEASURED"
    assert boundaries["live_host_latency"] == "UNMEASURED"
    assert boundaries["cross_host_consistency"] == "NOT_APPLICABLE_NO_HOST_EXECUTION"
    assert boundaries["live_model_calls"] == 0
    assert boundaries["provider_calls"] == 0
    assert result["complexity_snapshot"]["runtime_integration"] is False
    assert result["complexity_snapshot"]["second_test_engine"] is False
    assert result["complexity_snapshot"]["new_runtime_dependencies"] == 0


def test_all_clean_controls_remain_complete_and_non_authorizing() -> None:
    study = _study()
    subject_sha = study["frozen_subject"]["revision_sha"]
    for case in study["cases"]:
        if case["category"] != "CLEAN":
            continue
        packet = build_packet(case, subject_sha)
        baseline = baseline_disposition(packet)
        utm, authority_clear = utm_disposition(packet)
        assert baseline == "READINESS_EVIDENCE_COMPLETE"
        assert utm == "READINESS_EVIDENCE_COMPLETE"
        assert authority_clear is True


@pytest.mark.parametrize(
    "case_id",
    [
        "C05_MISSING_SECURITY",
        "C06_MISSING_REGRESSION",
        "C10_DUPLICATE_EVIDENCE",
        "C11_EVIDENCE_FOR_NA",
        "C12_T0_NA",
        "C13_STAGE_DECLARATION_MISSING",
        "C14_OWNER_DRIFT",
    ],
)
def test_cross_stage_contract_detects_cases_the_distributed_proxy_cannot(case_id: str) -> None:
    study = _study()
    case = next(item for item in study["cases"] if item["case_id"] == case_id)
    packet = build_packet(case, study["frozen_subject"]["revision_sha"])
    assert baseline_disposition(packet) == "READINESS_EVIDENCE_COMPLETE"
    utm, authority_clear = utm_disposition(packet)
    assert utm in {"WAIT_FOR_EVIDENCE", "INVALID_PACKET"}
    assert authority_clear is True


def test_preregistration_controls_fail_closed_if_weakened() -> None:
    study = _study()
    study["preregistration"]["selective_exclusion_prohibited"] = False
    with pytest.raises(StudyError, match="selective_exclusion_prohibited"):
        evaluate_study(study)


def test_runtime_integration_or_second_engine_drift_fails_closed() -> None:
    study = _study()
    study["complexity_snapshot"]["runtime_integration"] = True
    with pytest.raises(StudyError, match="non-default"):
        evaluate_study(study)

    study = _study()
    study["complexity_snapshot"]["second_test_engine"] = True
    with pytest.raises(StudyError, match="second test engine"):
        evaluate_study(study)


def test_case_identity_and_required_stage_integrity_fail_closed() -> None:
    study = _study()
    study["cases"].append(deepcopy(study["cases"][0]))
    with pytest.raises(StudyError, match="duplicate case_id"):
        evaluate_study(study)

    study = _study()
    study["cases"][0]["required_stages"] = ["T9"]
    with pytest.raises(StudyError, match="require T0 and T9"):
        evaluate_study(study)
