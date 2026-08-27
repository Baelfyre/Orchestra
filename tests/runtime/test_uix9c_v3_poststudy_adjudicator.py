from __future__ import annotations

from scripts import uix9c_v3_poststudy_adjudicator as post


def _pair(pair_id: str, *, improved: bool = False, regressed: bool = False, failures: list[str] | None = None) -> dict:
    metrics = {
        metric: {
            "baseline": False if metric in post.frozen.TRUE_IS_BETTER else 0,
            "governed": False if metric in post.frozen.TRUE_IS_BETTER else 0,
            "improved": improved,
            "regressed": regressed,
        }
        for metric in post.frozen.PRIMARY_METRICS
    }
    return {
        "pair_id": pair_id,
        "failure_codes": failures or [],
        "metric_comparison": metrics,
    }


def test_all_three_pairs_no_delta_is_no_benefit() -> None:
    classification, failures = post.classify_pair_adjudications(
        [_pair("PAIR_1"), _pair("PAIR_2"), _pair("PAIR_3")]
    )
    assert classification == "NO_BENEFIT_ESTABLISHED"
    assert failures == []


def test_counterbalanced_pair_is_adjudicated_by_arm_not_execution_order(monkeypatch) -> None:
    observations = {
        "A1": {"run_id": "A1"},
        "B1": {"run_id": "B1"},
        "B2": {"run_id": "B2"},
        "A2": {"run_id": "A2"},
        "A3": {"run_id": "A3"},
        "B3": {"run_id": "B3"},
    }
    calls: list[tuple[str, str]] = []

    def fake_pair(baseline, governed):
        calls.append((baseline["run_id"], governed["run_id"]))
        return {"pair_id": f"PAIR_{baseline['run_id'][1]}", "failure_codes": [], "metric_comparison": {}}

    monkeypatch.setattr(post.frozen, "pair_adjudication", fake_pair)
    post.corrected_pair_adjudications(observations)

    assert calls == [("A1", "B1"), ("A2", "B2"), ("A3", "B3")]


def test_identity_failure_is_protocol_invalid() -> None:
    classification, failures = post.classify_pair_adjudications(
        [
            _pair("PAIR_1"),
            _pair("PAIR_2", failures=["ARM_IDENTITY_MISMATCH"]),
            _pair("PAIR_3"),
        ]
    )
    assert classification == "PROTOCOL_INVALID"
    assert failures == ["ARM_IDENTITY_MISMATCH"]


def test_non_null_pattern_remains_conservative() -> None:
    classification, failures = post.classify_pair_adjudications(
        [_pair("PAIR_1", improved=True), _pair("PAIR_2"), _pair("PAIR_3")]
    )
    assert classification == "MIXED_OR_INCONCLUSIVE"
    assert failures == ["NON_NULL_PATTERN_REQUIRES_PREDECLARED_THRESHOLD"]


def test_pair_set_mismatch_fails_closed() -> None:
    classification, failures = post.classify_pair_adjudications([_pair("PAIR_1"), _pair("PAIR_2")])
    assert classification == "PROTOCOL_INVALID"
    assert failures == ["PAIR_SET_MISMATCH"]
