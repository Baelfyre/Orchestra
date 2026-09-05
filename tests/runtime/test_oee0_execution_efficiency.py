from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from orchestra_runtime.domain.orchestration.execution_efficiency import (
    EVIDENCE_TIERS,
    SEARCH_ESCALATION,
    VALIDATION_ESCALATION,
    enforce_ci_wait_boundary,
    require_evidence_tier,
    require_search_escalation,
    require_validation_escalation,
    validate_decisive_stop_signal,
    validate_execution_budget,
)
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    execution_budget_errors,
    load_execution_budget_contract,
)


ROOT = Path(__file__).resolve().parents[2]


def _budget() -> dict:
    return load_execution_budget_contract(ROOT)


def test_reference_execution_budget_is_fail_closed() -> None:
    budget = validate_execution_budget(_budget())

    assert budget.owner == "conductor"
    assert budget.defaults["max_parallel_specialists"] == 1
    assert budget.defaults["specialist_retry_limit"] == 1
    assert budget.search_escalation == SEARCH_ESCALATION
    assert budget.validation_escalation == VALIDATION_ESCALATION
    assert tuple(item["tier"] for item in budget.evidence_tiers) == EVIDENCE_TIERS
    assert all(value is False for value in budget.authority.values())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_parallel_specialists", 2),
        ("specialist_retry_limit", 2),
        ("owner_first_routing", False),
        ("full_validation_requires_stable_candidate", False),
        ("ci_wait_must_not_consume_reasoning_budget", False),
    ],
)
def test_execution_budget_rejects_weaker_defaults(field: str, value: object) -> None:
    data = deepcopy(_budget())
    data["defaults"][field] = value
    with pytest.raises(ValueError):
        validate_execution_budget(data)


def test_execution_budget_rejects_authority_expansion() -> None:
    data = deepcopy(_budget())
    data["authority"]["weakens_human_gates"] = True
    with pytest.raises(ValueError, match="weakens_human_gates"):
        validate_execution_budget(data)


def test_evidence_tiers_cannot_be_skipped() -> None:
    require_evidence_tier("E0", ())
    require_evidence_tier("E2", ("E0", "E1"))

    with pytest.raises(ValueError, match="E1"):
        require_evidence_tier("E2", ("E0",))


def test_search_escalation_is_narrow_to_broad() -> None:
    require_search_escalation(
        "EXACT_PATH",
        "EXACT_SYMBOL",
        current_stage_insufficient=True,
    )

    with pytest.raises(ValueError, match="cannot skip"):
        require_search_escalation(
            "EXACT_PATH",
            "REPOSITORY_WIDE",
            current_stage_insufficient=True,
        )

    with pytest.raises(ValueError, match="before current stage is insufficient"):
        require_search_escalation(
            "EXACT_PATH",
            "EXACT_SYMBOL",
            current_stage_insufficient=False,
        )


def test_validation_escalation_defers_expensive_gates() -> None:
    require_validation_escalation(
        "DIRECT_TESTS",
        "SUBSYSTEM",
        current_stage_insufficient=True,
    )

    with pytest.raises(ValueError, match="cannot skip"):
        require_validation_escalation(
            "DIRECT_TESTS",
            "PROTECTED_GATES",
            current_stage_insufficient=True,
        )


def test_decisive_stop_blocks_downstream_execution() -> None:
    signal = validate_decisive_stop_signal(
        {
            "owner": "cloak",
            "evidence_sufficient": True,
            "stop_required": True,
            "downstream_execution_allowed": False,
            "reason": "accepted responsive intent is contradictory",
            "evidence_refs": ["machine/ui/ui-fidelity-handoff.v1.json"],
        }
    )
    assert signal.downstream_execution_allowed is False

    with pytest.raises(ValueError, match="downstream execution must be false"):
        validate_decisive_stop_signal(
            {
                "owner": "cloak",
                "evidence_sufficient": True,
                "stop_required": True,
                "downstream_execution_allowed": True,
                "reason": "accepted responsive intent is contradictory",
                "evidence_refs": ["machine/ui/ui-fidelity-handoff.v1.json"],
            }
        )


def test_unchanged_ci_wait_cannot_consume_active_model_reasoning() -> None:
    enforce_ci_wait_boundary(
        activity="CI_WAIT",
        ci_state_changed=False,
        active_model_reasoning=False,
    )

    with pytest.raises(ValueError, match="unchanged CI"):
        enforce_ci_wait_boundary(
            activity="CI_WAIT",
            ci_state_changed=False,
            active_model_reasoning=True,
        )

    enforce_ci_wait_boundary(
        activity="CI_WAIT",
        ci_state_changed=True,
        active_model_reasoning=True,
    )

def test_decisive_stop_rejects_non_boolean_state() -> None:
    with pytest.raises(ValueError, match="must be a boolean"):
        validate_decisive_stop_signal(
            {
                "owner": "cloak",
                "evidence_sufficient": "true",
                "stop_required": True,
                "downstream_execution_allowed": False,
                "reason": "synthetic",
                "evidence_refs": ["evidence"],
            }
        )


def test_escalation_rejects_backward_and_malformed_transitions() -> None:
    with pytest.raises(ValueError, match="cannot move backward"):
        require_search_escalation(
            "REPOSITORY_WIDE",
            "EXACT_SYMBOL",
            current_stage_insufficient=True,
        )

    with pytest.raises(ValueError, match="must be a boolean"):
        require_validation_escalation(
            "DIRECT_TESTS",
            "SUBSYSTEM",
            current_stage_insufficient=1,
        )


def test_ci_wait_rejects_non_boolean_state() -> None:
    with pytest.raises(ValueError, match="must be booleans"):
        enforce_ci_wait_boundary(
            activity="CI_WAIT",
            ci_state_changed="no",
            active_model_reasoning=False,
        )

def test_execution_budget_adapter_fails_closed_on_missing_contract(tmp_path) -> None:
    assert execution_budget_errors(tmp_path)[0].startswith(
        "EXECUTION_BUDGET_CONTRACT_INVALID:execution budget contract missing:"
    )


def test_execution_budget_adapter_fails_closed_on_invalid_json(tmp_path) -> None:
    path = tmp_path / "machine" / "governance" / "execution-budget.v1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")
    assert execution_budget_errors(tmp_path)[0].startswith(
        "EXECUTION_BUDGET_CONTRACT_INVALID:execution budget contract is invalid JSON:"
    )


def test_execution_budget_adapter_rejects_weakened_contract(tmp_path) -> None:
    path = tmp_path / "machine" / "governance" / "execution-budget.v1.json"
    path.parent.mkdir(parents=True)
    data = deepcopy(_budget())
    data["defaults"]["max_parallel_specialists"] = 2
    import json

    path.write_text(json.dumps(data), encoding="utf-8")
    assert "max_parallel_specialists" in execution_budget_errors(tmp_path)[0]

@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.update({"schema_version": "wrong"}), "schema_version"),
        (lambda d: d.update({"contract_name": "Wrong"}), "contract_name"),
        (lambda d: d.update({"owner": "the-governor"}), "owner must be conductor"),
        (lambda d: d.update({"core_invariant": "weaker"}), "core invariant changed"),
        (lambda d: d["evidence_tiers"][0].update({"name": "WRONG"}), "evidence tiers"),
        (lambda d: d.update({"search_escalation": ["EXTERNAL"]}), "search escalation"),
        (lambda d: d.update({"validation_escalation": ["PROTECTED_GATES"]}), "validation escalation"),
        (lambda d: d["decisive_stop"].update({"rule": "KEEP_GOING"}), "decisive stop rule"),
        (lambda d: d["decisive_stop"].update({"required_fields": []}), "decisive stop required fields"),
        (lambda d: d.update({"measurement_fields": []}), "measurement_fields"),
        (lambda d: d.update({"measurement_fields": ["duplicate", "duplicate"]}), "measurement_fields"),
    ],
)
def test_execution_budget_rejects_contract_drift(mutate, message) -> None:
    data = deepcopy(_budget())
    mutate(data)
    with pytest.raises(ValueError, match=message):
        validate_execution_budget(data)


@pytest.mark.parametrize("field", ["defaults", "decisive_stop", "authority"])
def test_execution_budget_requires_mapping_sections(field: str) -> None:
    data = deepcopy(_budget())
    data[field] = []
    with pytest.raises(ValueError, match=f"{field} must be a mapping"):
        validate_execution_budget(data)


@pytest.mark.parametrize(
    "field",
    ["evidence_tiers", "search_escalation", "validation_escalation", "measurement_fields"],
)
def test_execution_budget_requires_sequence_sections(field: str) -> None:
    data = deepcopy(_budget())
    data[field] = "not-a-sequence"
    with pytest.raises(ValueError, match=f"{field} must be a list or tuple"):
        validate_execution_budget(data)


def test_execution_budget_rejects_non_mapping_tier_item() -> None:
    data = deepcopy(_budget())
    data["evidence_tiers"][0] = "E0"
    with pytest.raises(ValueError, match="evidence_tiers items must be mappings"):
        validate_execution_budget(data)


def test_execution_budget_rejects_non_mapping_root() -> None:
    with pytest.raises(ValueError, match="data must be a mapping"):
        validate_execution_budget([])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("owner", "", "owner is required"),
        ("reason", "", "reason is required"),
        ("evidence_refs", [], "requires evidence_refs"),
        ("evidence_refs", [""], "requires evidence_refs"),
    ],
)
def test_decisive_stop_requires_complete_evidence(field, value, message) -> None:
    data = {
        "owner": "cloak",
        "evidence_sufficient": True,
        "stop_required": True,
        "downstream_execution_allowed": False,
        "reason": "blocked",
        "evidence_refs": ["evidence"],
    }
    data[field] = value
    with pytest.raises(ValueError, match=message):
        validate_decisive_stop_signal(data)


def test_decisive_stop_rejects_non_mapping_and_non_sequence_refs() -> None:
    with pytest.raises(ValueError, match="data must be a mapping"):
        validate_decisive_stop_signal([])

    with pytest.raises(ValueError, match="evidence_refs must be a list or tuple"):
        validate_decisive_stop_signal(
            {
                "owner": "cloak",
                "evidence_sufficient": True,
                "stop_required": True,
                "downstream_execution_allowed": False,
                "reason": "blocked",
                "evidence_refs": "one-ref",
            }
        )


def test_evidence_tier_rejects_unknown_inputs() -> None:
    with pytest.raises(ValueError, match="unknown evidence tier"):
        require_evidence_tier("E9", ())

    with pytest.raises(ValueError, match="completed_tiers contains unknown"):
        require_evidence_tier("E1", ("UNKNOWN",))


def test_escalation_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="unknown escalation stage"):
        require_search_escalation(
            "EXACT_PATH",
            "UNKNOWN",
            current_stage_insufficient=True,
        )

