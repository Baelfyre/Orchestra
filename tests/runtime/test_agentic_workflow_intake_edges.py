from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from orchestra_runtime.domain.adaptive import build_selection_trace, derive_task_profile
from orchestra_runtime.domain.adaptive import intake as intake_module
from orchestra_runtime.domain.adaptive.topology_validator import AgenticWorkflowProfile
from orchestra_runtime.infrastructure.machine.agentic_workflow import (
    load_agentic_workflow_contracts,
)

ROOT = Path(__file__).resolve().parents[2]


def _policy():
    return deepcopy(load_agentic_workflow_contracts(ROOT)["derivation_policy"])


def test_intake_prompt_and_signal_helpers_fail_closed():
    with pytest.raises(TypeError, match="prompt must be a string"):
        intake_module._clean_prompt(None)
    with pytest.raises(ValueError, match="non-empty"):
        intake_module._clean_prompt("   ")
    with pytest.raises(ValueError, match="4096"):
        intake_module._clean_prompt("x" * 4097)
    with pytest.raises(ValueError, match="signals must be non-empty"):
        intake_module._signal_position("prompt", " ")


@pytest.mark.parametrize("value", [1, "true", []])
def test_exact_boolean_hint_rejects_non_boolean(value):
    with pytest.raises(TypeError, match="exact boolean"):
        intake_module._exact_bool_or_default(value, False, "flag")


@pytest.mark.parametrize("value", [True, "1", -1, 65])
def test_bounded_int_hint_rejects_invalid_values(value):
    with pytest.raises((TypeError, ValueError)):
        intake_module._bounded_nonnegative_int(value, 0, "count")


def test_string_list_hint_rejects_wrong_shape_duplicates_empty_and_excess():
    with pytest.raises(TypeError, match="list or tuple"):
        intake_module._string_list("x", "items", maximum=2)
    with pytest.raises(ValueError, match="unique"):
        intake_module._string_list(["x", "x"], "items", maximum=2)
    with pytest.raises(ValueError, match="unique"):
        intake_module._string_list([""], "items", maximum=2)
    with pytest.raises(ValueError, match="unique"):
        intake_module._string_list(["a", "b", "c"], "items", maximum=2)


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda p: "not-a-mapping", "mapping"),
        (lambda p: {**p, "schema_version": "wrong"}, "schema"),
        (lambda p: {**p, "owner": "ponytail"}, "owner"),
        (lambda p: {**p, "default_execution_mode": "UNKNOWN"}, "execution mode"),
        (lambda p: {**p, "default_risk_level": "UNKNOWN"}, "risk level"),
        (lambda p: {**p, "domain_rules": []}, "domain_rules"),
        (lambda p: {**p, "domain_rules": ["bad"]}, "domain rule"),
        (
            lambda p: {
                **p,
                "domain_rules": [
                    *p["domain_rules"],
                    deepcopy(p["domain_rules"][0]),
                ],
            },
            "domain rule set",
        ),
        (
            lambda p: {
                **p,
                "domain_rules": [
                    {**p["domain_rules"][0], "signals": []},
                    *p["domain_rules"][1:],
                ],
            },
            "domain signals",
        ),
        (lambda p: {**p, "operation_signals": []}, "operation_signals"),
        (
            lambda p: {
                **p,
                "operation_signals": {
                    key: value
                    for key, value in p["operation_signals"].items()
                    if key != "parallel"
                },
            },
            "signal set",
        ),
        (
            lambda p: {
                **p,
                "operation_signals": {
                    **p["operation_signals"],
                    "parallel": [],
                },
            },
            "operation signals",
        ),
        (lambda p: {**p, "governed_domains": []}, "governed_domains"),
        (lambda p: {**p, "governed_domains": ["UNKNOWN"]}, "governed_domains"),
    ],
)
def test_derivation_policy_rejection_matrix(mutator, match):
    base = _policy()
    value = mutator(base)
    with pytest.raises((TypeError, ValueError), match=match):
        intake_module.validate_derivation_policy(value)


def test_derivation_rejects_invalid_metadata_source_domain_and_owner():
    policy = _policy()
    with pytest.raises(TypeError, match="metadata must be a mapping"):
        derive_task_profile(
            prompt="Review responsive screen.",
            metadata=[],
            current_source_identity="main@test",
            policy=policy,
        )
    with pytest.raises(ValueError, match="source_identity"):
        derive_task_profile(
            prompt="Review responsive screen.",
            metadata={},
            current_source_identity="",
            policy=policy,
        )
    with pytest.raises(ValueError, match="unknown authority domain"):
        derive_task_profile(
            prompt="Review responsive screen.",
            metadata={"agentic_authority_domains": ["UNKNOWN"]},
            current_source_identity="main@test",
            policy=policy,
        )
    with pytest.raises(ValueError, match="canonical specialist owner"):
        derive_task_profile(
            prompt="Review responsive screen.",
            metadata={"agentic_primary_owner": "unknown"},
            current_source_identity="main@test",
            policy=policy,
        )


def test_explicit_domain_owner_and_overrides_are_preserved_without_authority_creation():
    policy = _policy()
    result = derive_task_profile(
        prompt="Review responsive screen.",
        metadata={
            "agentic_authority_domains": ["SECURITY"],
            "agentic_primary_owner": "cloak",
            "dependency_depth": 3,
            "independent_subtasks": 2,
            "parallelizable": True,
            "external_state_required": False,
            "objective_verifier_available": True,
            "reentry_specialists": ["cipher"],
            "human_gate_requirements": ["EXISTING_GATE"],
            "agentic_task_id": "explicit-task",
            "agentic_goal": "Explicit goal",
        },
        current_source_identity="main@test",
        policy=policy,
    )
    task = result.task_profile
    assert task.authority_domains == ("UI_UX", "SECURITY")
    assert task.primary_owner == "cloak"
    assert task.dependency_depth == 3
    assert task.independent_subtasks == 2
    assert task.parallelizable is True
    assert task.external_state_required is False
    assert task.objective_verifier_available is True
    assert task.reentry_specialists == ("cipher",)
    assert task.human_gate_requirements == ("EXISTING_GATE",)
    assert task.task_id == "explicit-task"
    assert task.goal == "Explicit goal"
    assert "EXPLICIT_AUTHORITY_DOMAINS_PRESERVED" in result.derivation_reasons


def test_critic_hints_must_be_paired():
    policy = _policy()
    with pytest.raises(ValueError, match="supplied together"):
        derive_task_profile(
            prompt="Review responsive screen.",
            metadata={"critic_owner": "overseer"},
            current_source_identity="main@test",
            policy=policy,
        )


def test_host_native_execution_mode_is_ignored_while_canonical_risk_mode_can_escalate():
    policy = _policy()
    host_native = derive_task_profile(
        prompt="Implement responsive UI.",
        metadata={"execution_mode": "HOST_NATIVE"},
        current_source_identity="main@test",
        policy=policy,
    )
    assert host_native.task_profile.execution_mode == "STANDARD"

    escalated = derive_task_profile(
        prompt="Fix typo.",
        metadata={"risk_mode": "GOVERNED"},
        current_source_identity="main@test",
        policy=policy,
    )
    assert escalated.task_profile.execution_mode == "GOVERNED"


def test_invalid_namespaced_mode_and_risk_hints_fail_closed():
    policy = _policy()
    with pytest.raises(ValueError, match="agentic_execution_mode"):
        derive_task_profile(
            prompt="Fix typo.",
            metadata={"agentic_execution_mode": "UNKNOWN"},
            current_source_identity="main@test",
            policy=policy,
        )
    with pytest.raises(ValueError, match="agentic_risk_level"):
        derive_task_profile(
            prompt="Fix typo.",
            metadata={"agentic_risk_level": "UNKNOWN"},
            current_source_identity="main@test",
            policy=policy,
        )


def test_parallel_signal_is_recorded_but_does_not_change_oee_authority():
    result = derive_task_profile(
        prompt="Analyze UI and security in parallel.",
        metadata={},
        current_source_identity="main@test",
        policy=_policy(),
    )
    assert result.task_profile.parallelizable is True
    assert result.task_profile.authority_domains == ("UI_UX", "SECURITY")


def test_selection_trace_rejects_unknown_source():
    task = derive_task_profile(
        prompt="Review responsive screen.",
        metadata={},
        current_source_identity="main@test",
        policy=_policy(),
    ).task_profile
    profile = AgenticWorkflowProfile(
        profile_id="profile.trace",
        source_task_id=task.task_id,
        primary_owner="cloak",
        required_specialists=("cloak",),
        selected_patterns=("ROUTING",),
        sequence=("cloak",),
        parallel_groups=(),
        concurrency_mode="SINGLE_OWNER",
        max_parallel_specialists=1,
        human_gate_required=False,
        escalation_reasons=(),
        stop_conditions=("OBJECTIVE_PASS",),
        critic_contract_id=None,
    )
    with pytest.raises(ValueError, match="source is invalid"):
        build_selection_trace(task=task, profile=profile, source="UNKNOWN")
