from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.application.use_cases.agentic_workflow import plan_agentic_workflow
from orchestra_runtime.domain.adaptive.agentic_workflow import (
    _build_candidate_freshness_binding,
    _candidate_binding_matches,
    _resolve_assurance_requirement_union,
    minimum_task_audit_depth,
)
from orchestra_runtime.domain.adaptive.task_profile import AUTHORITY_DOMAIN_OWNERS, TaskProfile
from orchestra_runtime.infrastructure.machine.agentic_workflow import (
    load_agentic_workflow_contracts,
)
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    load_execution_budget_contract,
)
from orchestra_runtime.machine_contracts import load_specialist_registry

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "evidence-gated-decision-hierarchy.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "evidence-gated-decision-hierarchy.v1.schema.json"
STAGE_ORDER = [
    "ROUTING",
    "ASSESSMENT",
    "VERIFICATION",
    "IMPACT_RISK",
    "MITIGATION",
    "ADJUDICATION",
    "GOVERNANCE",
    "AUTHORITY",
    "TRANSITION",
    "IMPLEMENTATION",
    "REVALIDATION",
]


def _task(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "orchestra.task-profile.v1",
        "task_id": "decision-hierarchy-test",
        "goal": "Plan a bounded evidence-gated workflow.",
        "execution_mode": "GOVERNED",
        "risk_level": "MEDIUM",
        "authority_domains": ["UI_UX"],
        "primary_owner": None,
        "dependency_depth": 0,
        "independent_subtasks": 0,
        "parallelizable": False,
        "mutation_required": False,
        "implementation_required": False,
        "validation_required": False,
        "transition_required": False,
        "external_state_required": True,
        "protected_action_required": False,
        "protected_action_authorized": False,
        "objective_verifier_available": True,
        "critic_owner": None,
        "critic_domain": None,
        "reentry_specialists": [],
        "current_source_identity": "candidate@example",
        "human_gate_requirements": [],
    }
    data.update(overrides)
    return data


def _plan(task: dict[str, object]) -> dict[str, object]:
    contracts = load_agentic_workflow_contracts(ROOT)
    return plan_agentic_workflow(
        task_profile=task,
        specialist_authority_view=contracts["authority_view"],
        specialist_registry=load_specialist_registry(ROOT),
        execution_budget=load_execution_budget_contract(ROOT),
    )


def test_composition_contract_is_strict_ordered_source_bound_and_non_authorizing() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)

    stages = contract["stages"]
    assert [stage["stage"] for stage in stages] == STAGE_ORDER
    assert all(stage["may_authorize"] is False for stage in stages)
    assert stages[5]["optional"] is True
    assert stages[5]["contract_refs"] == []
    assert stages[0]["coordination"] == {
        "optional_owner": "the-tuner",
        "trigger": "MATERIAL_CROSS_SPECIALIST_CONTRACTS",
        "may_authorize_or_override_owner": False,
    }
    assert all((ROOT / ref).is_file() for stage in stages for ref in stage["contract_refs"])
    assert contract["transition_owner"] == "arbiter"
    assert contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING"
    assert contract["evidence_semantics"]["routing_not_required_is_substantive_review"] is False
    assert contract["evidence_semantics"]["assessor_may_self_verify"] is False
    assert contract["evidence_semantics"]["candidate_mutation_invalidates_prior_candidate_evidence"] is True
    assert contract["runtime_plan_contract"]["schema_version"] == "orchestra.agentic-assurance-plan.v2"
    assert contract["runtime_plan_contract"]["candidate_binding"][
        "unbound_or_stale_satisfies_current_requirements"
    ] is False
    assert contract["runtime_plan_contract"]["plan_may_authorize"] is False
    assert contract["assessment_execution"]["defensive_security_review_side_effect_class"] == "NONE"
    assert contract["assessment_execution"]["assessment_may_mutate"] is False
    assert contract["assessment_execution"]["assessment_may_issue_authorization"] is False
    assert contract["autonomy"]["profiles_reduce_existing_authority_only"] is True
    assert contract["autonomy"]["unsatisfied_or_protected_gate_may_be_bypassed"] is False
    assert contract["protected_change"]["same_run_change_and_continuation_allowed"] is False


@pytest.mark.parametrize(
    ("risk_level", "domain", "expected_depth"),
    [
        ("LOW", "UI_UX", "STANDARD"),
        ("MEDIUM", "UI_UX", "STANDARD"),
        ("HIGH", "SECURITY", "DEEP"),
        ("CRITICAL", "ARCHITECTURE", "DEEP"),
    ],
)
def test_task_risk_floor_requires_targeted_verification_without_replacing_domain_assessment(
    risk_level: str, domain: str, expected_depth: str
) -> None:
    result = _plan(_task(risk_level=risk_level, authority_domains=[domain]))
    assurance = result["assurance_plan"]
    assert assurance["task_risk_floor"]["audit_depth"] == expected_depth
    assert assurance["targeted_verification_required"] is True
    assert assurance["requirement_resolution_state"] == "FLOOR_ONLY"
    assert assurance["resolved_assurance_requirements"] is None
    assert assurance["unresolved_requirement_sources"] == ["AQ2", "AQ3", "AQ4", "PRAI"]
    assert assurance["assessor_may_self_verify"] is False
    assert assurance["evidence_sufficiency_owner"] == "overseer"
    assert AUTHORITY_DOMAIN_OWNERS[domain] in result["workflow_profile"]["required_specialists"]
    assert result["workflow_profile"]["authority_expansion"] is False


def test_explicitly_harmless_low_risk_task_can_use_light_assurance() -> None:
    profile = TaskProfile.from_mapping(
        _task(
            risk_level="LOW",
            authority_domains=["DOCUMENTATION"],
            external_state_required=False,
        )
    )
    assert minimum_task_audit_depth(profile) == "LIGHT"
    assurance = _plan(profile.to_dict())["assurance_plan"]
    assert assurance["task_risk_floor"]["audit_depth"] == "LIGHT"
    assert assurance["task_risk_floor"]["targeted_verification_required"] is False
    assert assurance["requirement_resolution_state"] == "FLOOR_ONLY"
    assert assurance["resolved_assurance_requirements"] is None
    assert assurance["targeted_verification_required"] is None
    assert assurance["evidence_sufficiency_owner"] == "overseer"
    assert assurance["candidate_freshness"]["state"] == "UNBOUND"
    assert assurance["candidate_freshness"]["source_state_identity"] is None


def test_assurance_union_keeps_unknown_sources_unresolved_and_never_lowers_known_needs() -> None:
    floor = {"audit_depth": "LIGHT", "targeted_verification_required": False}
    partial = _resolve_assurance_requirement_union(
        floor,
        {"AQ2": {"audit_depth": "STANDARD", "targeted_verification_required": True}},
    )
    assert partial["resolution_state"] == "PARTIAL"
    assert partial["resolved_assurance_requirements"] is None
    assert partial["targeted_verification_required"] is True
    assert partial["known_requirement_union"]["audit_depth_lower_bound"] == "STANDARD"
    assert partial["unresolved_sources"] == ["AQ3", "AQ4", "PRAI"]

    sources = {
        name: {"audit_depth": "LIGHT", "targeted_verification_required": False}
        for name in ("AQ2", "AQ3", "AQ4", "PRAI")
    }
    sources["AQ3"] = {"audit_depth": "STANDARD", "targeted_verification_required": True}
    sources["PRAI"] = {"audit_depth": "DEEP", "targeted_verification_required": False}
    resolved = _resolve_assurance_requirement_union(floor, sources)
    assert resolved["resolution_state"] == "RESOLVED"
    assert resolved["resolved_assurance_requirements"] == {
        "audit_depth": "DEEP",
        "targeted_verification_required": True,
    }
    assert resolved["unresolved_sources"] == []


def test_candidate_freshness_binding_is_exact_and_unbound_or_stale_never_matches() -> None:
    first = {
        "repository": "Baelfyre/Orchestra",
        "candidate_sha": "a" * 40,
        "tree_sha": "b" * 40,
    }
    binding = _build_candidate_freshness_binding(first)
    assert binding["state"] == "BOUND"
    assert binding["source_state_identity"].startswith("sha256:")
    assert _candidate_binding_matches(binding, first) is True
    assert _candidate_binding_matches(
        binding,
        {**first, "candidate_sha": "c" * 40},
    ) is False
    assert _candidate_binding_matches(
        binding,
        {**first, "tree_sha": "d" * 40},
    ) is False
    assert _candidate_binding_matches(
        binding,
        {**first, "repository": "Baelfyre/Other"},
    ) is False
    assert _candidate_binding_matches(_build_candidate_freshness_binding(None), first) is False


def test_protected_overlay_remains_a_human_gate_and_plan_never_issues_authority() -> None:
    result = _plan(
        _task(
            risk_level="HIGH",
            authority_domains=["SECURITY"],
            mutation_required=True,
            implementation_required=True,
            protected_action_required=True,
            protected_action_authorized=False,
        )
    )
    assert result["workflow_profile"]["human_gate_required"] is True
    assert result["workflow_profile"]["escalation_reasons"] == [
        "PROTECTED_ACTION_REQUIRES_INDEPENDENT_AUTHORITY"
    ]
    assert result["workflow_profile"]["authority_expansion"] is False
    assert result["assurance_plan"]["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING"
    assert "arbiter_transition_decision" not in result
    assert "authorization_decision" not in result


def test_existing_authority_view_keeps_dispatch_validation_and_transition_owners_separate() -> None:
    authority = load_agentic_workflow_contracts(ROOT)["authority_view"]["specialists"]
    assert [item["slug"] for item in authority if item["can_dispatch"]] == ["conductor"]
    assert [item["slug"] for item in authority if item["can_validate"]] == ["overseer"]
    assert [item["slug"] for item in authority if item["can_transition"]] == ["arbiter"]
    assert all(not item["can_execute_protected_action_without_external_authority"] for item in authority)


def test_jev_is_optional_and_advisory_only() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["jev"]["tracked_supported_integration"] is False
    assert contract["jev"]["advisory_insertion_point"]["after"] == [
        "VERIFIED_FINDINGS",
        "RISK_ASSESSMENT",
        "MITIGATION_ALTERNATIVES",
    ]
    assert contract["jev"]["advisory_insertion_point"]["before"] == "GOVERNANCE"
    assert contract["jev"]["absence_blocks_flow"] is False
    assert contract["jev"]["may_authorize_or_replace_review_or_reduce_risk"] is False
    assert contract["jev"]["may_mutate_candidate"] is False

def test_assurance_union_rejects_malformed_floor_and_source_evidence() -> None:
    malformed_cases = (
        ([], None, TypeError),
        ({"audit_depth": "UNKNOWN", "targeted_verification_required": False}, None, ValueError),
        ({"audit_depth": "LIGHT", "targeted_verification_required": 1}, None, ValueError),
        ({"audit_depth": "LIGHT", "targeted_verification_required": False}, [], TypeError),
        ({"audit_depth": "LIGHT", "targeted_verification_required": False}, {1: {}}, ValueError),
        (
            {"audit_depth": "LIGHT", "targeted_verification_required": False},
            {"AQ99": {"audit_depth": "LIGHT", "targeted_verification_required": False}},
            ValueError,
        ),
        (
            {"audit_depth": "LIGHT", "targeted_verification_required": False},
            {"AQ2": {"audit_depth": "LIGHT"}},
            ValueError,
        ),
        (
            {"audit_depth": "LIGHT", "targeted_verification_required": False},
            {"AQ2": {"audit_depth": "UNKNOWN", "targeted_verification_required": False}},
            ValueError,
        ),
        (
            {"audit_depth": "LIGHT", "targeted_verification_required": False},
            {"AQ2": {"audit_depth": "LIGHT", "targeted_verification_required": 1}},
            ValueError,
        ),
    )
    for floor, sources, error in malformed_cases:
        with pytest.raises(error):
            _resolve_assurance_requirement_union(floor, sources)


def test_candidate_binding_validation_and_matcher_fail_closed_branches() -> None:
    invalid_identities = (
        [],
        {"repository": "Baelfyre/Orchestra", "candidate_sha": "a" * 40},
        {"repository": 1, "candidate_sha": "a" * 40, "tree_sha": "b" * 40},
        {"repository": "x" * 256, "candidate_sha": "a" * 40, "tree_sha": "b" * 40},
        {"repository": "not-a-repository", "candidate_sha": "a" * 40, "tree_sha": "b" * 40},
        {"repository": "Baelfyre/Orchestra", "candidate_sha": "bad", "tree_sha": "b" * 40},
        {"repository": "Baelfyre/Orchestra", "candidate_sha": "a" * 40, "tree_sha": "bad"},
    )
    for identity in invalid_identities:
        with pytest.raises((TypeError, ValueError)):
            _build_candidate_freshness_binding(identity)

    valid_identity = {
        "repository": "Baelfyre/Orchestra",
        "candidate_sha": "a" * 40,
        "tree_sha": "b" * 40,
    }
    binding = _build_candidate_freshness_binding(valid_identity)

    assert _candidate_binding_matches([], valid_identity) is False
    assert _candidate_binding_matches({"state": "BOUND"}, valid_identity) is False
    assert _candidate_binding_matches({**binding, "state": "UNBOUND"}, valid_identity) is False
    assert _candidate_binding_matches({**binding, "may_authorize": True}, valid_identity) is False
    assert _candidate_binding_matches(binding, {"repository": "bad"}) is False


def test_task_floor_and_unique_append_type_and_duplicate_branches() -> None:
    from orchestra_runtime.domain.adaptive.agentic_workflow import _append_unique

    with pytest.raises(TypeError, match="TaskProfile"):
        minimum_task_audit_depth(object())

    values = ["cipher"]
    _append_unique(values, "cipher")
    assert values == ["cipher"]
    _append_unique(values, "cloak")
    assert values == ["cipher", "cloak"]
