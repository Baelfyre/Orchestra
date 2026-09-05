from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestra_runtime.application.use_cases.agentic_workflow import plan_agentic_workflow
from orchestra_runtime.domain.adaptive import TaskProfile, parse_authority_view, select_agentic_workflow
from orchestra_runtime.domain.adaptive import task_profile as task_module
from orchestra_runtime.domain.adaptive import topology_validator as topology_module
from orchestra_runtime.domain.adaptive.topology_validator import (
    AgenticWorkflowProfile,
    CriticContract,
    SpecialistAuthority,
)
from orchestra_runtime.infrastructure.machine import agentic_workflow as machine_awf
from orchestra_runtime.domain.orchestration.execution_efficiency import validate_execution_budget
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    load_execution_budget_contract,
)
from orchestra_runtime.machine_contracts import load_specialist_registry

ROOT = Path(__file__).resolve().parents[2]


def _task(**overrides):
    data = {
        "schema_version": "orchestra.task-profile.v1",
        "task_id": "edge",
        "goal": "Exercise an adaptive workflow contract edge.",
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
        "external_state_required": False,
        "protected_action_required": False,
        "protected_action_authorized": False,
        "objective_verifier_available": True,
        "critic_owner": None,
        "critic_domain": None,
        "reentry_specialists": [],
        "current_source_identity": "edge-source",
        "human_gate_requirements": [],
    }
    data.update(overrides)
    return data


def _contracts():
    return machine_awf.load_agentic_workflow_contracts(ROOT)


def _authorities():
    return parse_authority_view(_contracts()["authority_view"])


def _budget():
    return validate_execution_budget(load_execution_budget_contract(ROOT))


def _workflow_profile(**overrides):
    data = {
        "profile_id": "profile.edge",
        "source_task_id": "edge",
        "primary_owner": "cloak",
        "required_specialists": ("cloak",),
        "selected_patterns": ("ROUTING",),
        "sequence": ("cloak",),
        "parallel_groups": (),
        "concurrency_mode": "SINGLE_OWNER",
        "max_parallel_specialists": 1,
        "human_gate_required": False,
        "escalation_reasons": (),
        "stop_conditions": ("OBJECTIVE_PASS",),
        "critic_contract_id": None,
    }
    data.update(overrides)
    return AgenticWorkflowProfile(**data)


@pytest.mark.parametrize(
    ("value", "field", "maximum", "exc"),
    [
        (None, "field", 4, TypeError),
        ("", "field", 4, ValueError),
        ("12345", "field", 4, ValueError),
        ("bad\n", "field", 8, ValueError),
    ],
)
def test_task_text_rejects_invalid_values(value, field, maximum, exc):
    with pytest.raises(exc):
        task_module._text(value, field, max_length=maximum)


def test_task_helper_rejection_branches():
    with pytest.raises(ValueError, match="canonical identifier"):
        task_module._identifier("bad value", "id")
    with pytest.raises(TypeError, match="integer"):
        task_module._bounded_int(True, "count")
    with pytest.raises(ValueError, match="between"):
        task_module._bounded_int(65, "count")
    with pytest.raises(TypeError, match="list or tuple"):
        task_module._unique_strings("not-a-list", "items", max_items=2)
    with pytest.raises(ValueError, match="exceeds"):
        task_module._unique_strings(["a", "b", "c"], "items", max_items=2)
    with pytest.raises(ValueError, match="duplicate"):
        task_module._unique_strings(["a", "a"], "items", max_items=2)


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": "wrong"},
        {"execution_mode": "UNKNOWN"},
        {"risk_level": "UNKNOWN"},
        {"authority_domains": []},
        {"authority_domains": ["UI_UX", "UI_UX"]},
        {"authority_domains": ["UNKNOWN"]},
        {"critic_owner": "cipher", "critic_domain": None},
        {"critic_owner": None, "critic_domain": "SECURITY"},
        {"protected_action_required": False, "protected_action_authorized": True},
        {"parallelizable": 1},
        {"dependency_depth": -1},
        {"reentry_specialists": ["cipher", "cipher"]},
        {"human_gate_requirements": ["x", "x"]},
    ],
)
def test_task_profile_fails_closed_on_malformed_contract(overrides):
    data = _task(**overrides)
    with pytest.raises((TypeError, ValueError)):
        TaskProfile.from_mapping(data)


def test_task_profile_rejects_non_mapping_and_excessive_reentry():
    with pytest.raises(TypeError, match="mapping"):
        TaskProfile.from_mapping([])
    with pytest.raises(ValueError, match="reentry_specialists"):
        TaskProfile.from_mapping(_task(reentry_specialists=[f"s{i}" for i in range(15)]))


def test_topology_helpers_and_specialist_authority_fail_closed():
    with pytest.raises(ValueError, match="non-empty"):
        topology_module._clean("", "field")
    with pytest.raises(ValueError, match="exceeds"):
        topology_module._strings(["a", "b"], "field", max_items=1)
    with pytest.raises(ValueError, match="must not be empty"):
        topology_module._strings([], "field", max_items=1, nonempty=True)
    with pytest.raises(ValueError, match="duplicate"):
        topology_module._strings(["a", "a"], "field", max_items=2)

    with pytest.raises(TypeError, match="mapping"):
        SpecialistAuthority.from_mapping([])
    sample = deepcopy(_contracts()["authority_view"]["specialists"][0])
    sample["can_dispatch"] = 1
    with pytest.raises(TypeError, match="exact boolean"):
        SpecialistAuthority.from_mapping(sample)
    sample = deepcopy(_contracts()["authority_view"]["specialists"][0])
    sample["source_blob_sha"] = "short"
    with pytest.raises(ValueError, match="Git blob SHA"):
        SpecialistAuthority.from_mapping(sample)
    sample["source_blob_sha"] = "g" * 40
    with pytest.raises(ValueError, match="Git blob SHA"):
        SpecialistAuthority.from_mapping(sample)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"schema_version": "wrong"},
        {"max_iterations": True},
        {"max_iterations": 4},
        {"can_block": 1},
        {"can_transition": True, "critic_owner": "cipher"},
    ],
)
def test_critic_contract_fails_closed(kwargs):
    data = {
        "contract_id": "critic.edge",
        "critic_owner": "cipher",
        "evaluation_domain": "SECURITY",
        "evidence_owner": "cipher",
        "can_block": True,
        "can_request_revision": True,
        "can_transition": False,
        "max_iterations": 1,
    }
    data.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        CriticContract(**data)


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": "wrong"},
        {"selected_by": "ponytail"},
        {"topology_effective": False},
        {"topology_change_requires_human_approval": True},
        {"authority_expansion": True},
        {"human_gate_required": 1},
        {"max_parallel_specialists": True},
        {"max_parallel_specialists": 0},
        {"required_specialists": ()},
        {"sequence": ("cipher",)},
        {"selected_patterns": ("ROUTING", "UNKNOWN")},
        {"selected_patterns": ("PLANNING", "ROUTING")},
        {"selected_patterns": ("PLANNING",)},
        {
            "required_specialists": ("cloak", "cipher"),
            "sequence": ("cloak", "cipher"),
            "selected_patterns": ("ROUTING", "MULTI_AGENT"),
            "parallel_groups": (("cloak",),),
            "concurrency_mode": "PARALLEL_MULTI_AGENT",
            "max_parallel_specialists": 2,
        },
        {
            "required_specialists": ("cloak", "cipher"),
            "sequence": ("cloak", "cipher"),
            "selected_patterns": ("ROUTING", "MULTI_AGENT"),
            "parallel_groups": (("cloak", "scribe"),),
            "concurrency_mode": "PARALLEL_MULTI_AGENT",
            "max_parallel_specialists": 2,
        },
        {
            "required_specialists": ("cloak", "cipher"),
            "sequence": ("cloak", "cipher"),
            "selected_patterns": ("ROUTING", "MULTI_AGENT"),
            "parallel_groups": (("cloak", "cipher"),),
            "concurrency_mode": "PARALLEL_MULTI_AGENT",
            "max_parallel_specialists": 1,
        },
        {"concurrency_mode": "UNKNOWN"},
        {
            "required_specialists": ("cloak", "cipher"),
            "sequence": ("cloak", "cipher"),
            "concurrency_mode": "SINGLE_OWNER",
        },
        {"concurrency_mode": "PARALLEL_MULTI_AGENT"},
        {
            "required_specialists": ("cloak", "cipher"),
            "sequence": ("cloak", "cipher"),
            "parallel_groups": (("cloak", "cipher"),),
            "concurrency_mode": "PARALLEL_MULTI_AGENT",
            "max_parallel_specialists": 2,
        },
        {"human_gate_required": True, "escalation_reasons": ()},
    ],
)
def test_workflow_profile_fails_closed_on_invalid_topology(overrides):
    with pytest.raises((TypeError, ValueError)):
        _workflow_profile(**overrides)


def test_valid_parallel_profile_covers_parallel_contract_path():
    profile = _workflow_profile(
        required_specialists=("cloak", "cipher"),
        sequence=("cloak", "cipher"),
        selected_patterns=("ROUTING", "MULTI_AGENT"),
        parallel_groups=(("cloak", "cipher"),),
        concurrency_mode="PARALLEL_MULTI_AGENT",
        max_parallel_specialists=2,
    )
    assert profile.to_dict()["parallel_groups"] == [["cloak", "cipher"]]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"),
        ("source_of_truth", "wrong"),
        ("generation_policy", "wrong"),
        ("specialists", "wrong"),
    ],
)
def test_authority_view_header_rejections(field, value):
    data = deepcopy(_contracts()["authority_view"])
    data[field] = value
    with pytest.raises((TypeError, ValueError)):
        parse_authority_view(data)


def test_authority_view_rejects_non_mapping_duplicates_wrong_set_and_authority_drift():
    with pytest.raises(TypeError, match="mapping"):
        parse_authority_view([])

    base = _contracts()["authority_view"]

    data = deepcopy(base)
    data["specialists"].append(deepcopy(data["specialists"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        parse_authority_view(data)

    data = deepcopy(base)
    data["specialists"] = data["specialists"][:-1]
    with pytest.raises(ValueError, match="canonical 14"):
        parse_authority_view(data)

    checks = [
        ("can_dispatch", "cloak", "Conductor"),
        ("can_transition", "cloak", "Arbiter"),
        ("can_validate", "cloak", "Overseer"),
        ("can_coordinate", "cloak", "Tuner"),
        ("can_implement", "cloak", "Ponytail"),
        ("can_execute_protected_action_without_external_authority", "cloak", "protected"),
    ]
    for flag, slug, match in checks:
        data = deepcopy(base)
        item = next(x for x in data["specialists"] if x["slug"] == slug)
        item[flag] = True
        with pytest.raises(ValueError, match=match):
            parse_authority_view(data)


def test_selector_rejects_invalid_types_unknown_owners_and_supports_routing_only():
    authorities = _authorities()
    budget = _budget()

    with pytest.raises(TypeError, match="TaskProfile"):
        select_agentic_workflow({}, authorities, budget)
    with pytest.raises(TypeError, match="ExecutionBudget"):
        select_agentic_workflow(TaskProfile.from_mapping(_task()), authorities, {})

    task = TaskProfile.from_mapping(_task(primary_owner="unknown"))
    with pytest.raises(ValueError, match="primary owner"):
        select_agentic_workflow(task, authorities, budget)

    task = TaskProfile.from_mapping(_task(reentry_specialists=["unknown"]))
    with pytest.raises(ValueError, match="re-entry specialist"):
        select_agentic_workflow(task, authorities, budget)

    task = TaskProfile.from_mapping(_task(critic_owner="unknown", critic_domain="SECURITY"))
    with pytest.raises(ValueError, match="critic owner"):
        select_agentic_workflow(task, authorities, budget)

    routing = TaskProfile.from_mapping(_task(authority_domains=["ROUTING"], primary_owner=None))
    profile, critic = select_agentic_workflow(routing, authorities, budget)
    assert profile.required_specialists == ("conductor",)
    assert profile.selected_patterns == ("ROUTING",)
    assert critic is None


def test_selector_covers_terminal_owners_critic_variants_and_explicit_human_gate():
    authorities = _authorities()
    budget = _budget()

    task = TaskProfile.from_mapping(
        _task(
            authority_domains=["IMPLEMENTATION", "VALIDATION", "TRANSITION", "COORDINATION"],
            primary_owner="ponytail",
            implementation_required=False,
            validation_required=False,
            transition_required=False,
        )
    )
    profile, _ = select_agentic_workflow(task, authorities, budget)
    assert profile.required_specialists == ("the-tuner", "ponytail", "overseer", "arbiter")

    task = TaskProfile.from_mapping(
        _task(
            authority_domains=["IMPLEMENTATION"],
            primary_owner="ponytail",
            critic_owner="scribe",
            critic_domain="DOCUMENTATION",
            human_gate_requirements=["EXPLICIT_EXISTING_GATE"],
        )
    )
    profile, critic = select_agentic_workflow(task, authorities, budget)
    assert profile.human_gate_required is True
    assert critic is not None
    assert critic.can_block is False
    assert critic.evidence_owner == "scribe"

    task = TaskProfile.from_mapping(
        _task(
            authority_domains=["TRANSITION"],
            primary_owner="arbiter",
            critic_owner="arbiter",
            critic_domain="TRANSITION",
        )
    )
    _, critic = select_agentic_workflow(task, authorities, budget)
    assert critic is not None and critic.can_transition is True


def test_selector_parallel_branch_is_bounded_by_workflow_contract(monkeypatch):
    authorities = _authorities()
    canonical = _budget()
    defaults = dict(canonical.defaults)
    defaults["max_parallel_specialists"] = 2
    widened_for_test = replace(canonical, defaults=defaults)
    monkeypatch.setattr(type(widened_for_test), "validate", lambda self: None)

    task = TaskProfile.from_mapping(
        _task(
            authority_domains=["UI_UX", "ARCHITECTURE"],
            dependency_depth=1,
            independent_subtasks=2,
            parallelizable=True,
        )
    )
    profile, _ = select_agentic_workflow(task, authorities, widened_for_test)
    assert profile.concurrency_mode == "PARALLEL_MULTI_AGENT"
    assert profile.parallel_groups == (("cloak", "clockwork"),)


def test_application_use_case_rejects_registry_shape_and_set_mismatch():
    contracts = _contracts()
    budget = load_execution_budget_contract(ROOT).to_dict() if hasattr(load_execution_budget_contract(ROOT), "to_dict") else json.loads((ROOT / "machine" / "governance" / "execution-budget.v1.json").read_text(encoding="utf-8"))

    with pytest.raises(TypeError, match="specialists must be a list"):
        plan_agentic_workflow(
            task_profile=_task(),
            specialist_authority_view=contracts["authority_view"],
            specialist_registry={"specialists": "wrong"},
            execution_budget=budget,
        )

    with pytest.raises(ValueError, match="identical specialist sets"):
        plan_agentic_workflow(
            task_profile=_task(),
            specialist_authority_view=contracts["authority_view"],
            specialist_registry={"specialists": [{"slug": "cloak"}]},
            execution_budget=budget,
        )


def test_machine_loader_fail_closed_branches(tmp_path, monkeypatch):
    missing = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="missing"):
        machine_awf._load_json(missing)

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        machine_awf._load_json(malformed)

    not_object = tmp_path / "list.json"
    not_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        machine_awf._load_json(not_object)

    monkeypatch.setattr(
        machine_awf,
        "parse_authority_view",
        lambda _value: {
            "conductor": SimpleNamespace(
                source_path="skills/conductor/SKILL.md",
                source_blob_sha="0" * 40,
                slug="conductor",
            )
        },
    )
    with pytest.raises(ValueError, match="source binding is stale"):
        machine_awf.load_agentic_workflow_authority_view(ROOT)


@pytest.mark.parametrize(
    "value",
    [
        {"schema_version": "wrong", "owner": "conductor", "patterns": [], "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-patterns.v1", "owner": "wrong", "patterns": [], "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-patterns.v1", "owner": "conductor", "patterns": "wrong", "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-patterns.v1", "owner": "conductor", "patterns": [], "topology_change_requires_human_approval": False},
        {
            "schema_version": "orchestra.agentic-patterns.v1",
            "owner": "conductor",
            "patterns": [{"name": name} for name in topology_module.PATTERN_ORDER],
            "topology_change_requires_human_approval": True,
        },
    ],
)
def test_pattern_contract_loader_rejections(monkeypatch, value):
    monkeypatch.setattr(machine_awf, "_load_json", lambda _path: value)
    with pytest.raises((TypeError, ValueError)):
        machine_awf.load_agentic_pattern_contract(ROOT)


@pytest.mark.parametrize(
    "value",
    [
        {"schema_version": "wrong", "owner": "conductor", "invariants": [], "authority_expansion": False, "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-composition-invariants.v1", "owner": "wrong", "invariants": [], "authority_expansion": False, "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-composition-invariants.v1", "owner": "conductor", "invariants": "wrong", "authority_expansion": False, "topology_change_requires_human_approval": False},
        {"schema_version": "orchestra.agentic-composition-invariants.v1", "owner": "conductor", "invariants": [], "authority_expansion": False, "topology_change_requires_human_approval": False},
        {
            "schema_version": "orchestra.agentic-composition-invariants.v1",
            "owner": "conductor",
            "invariants": [{"id": item, "hard": False} for item in topology_module.REQUIRED_COMPOSITION_INVARIANT_IDS],
            "authority_expansion": False,
            "topology_change_requires_human_approval": False,
        },
        {
            "schema_version": "orchestra.agentic-composition-invariants.v1",
            "owner": "conductor",
            "invariants": [{"id": item, "hard": True} for item in topology_module.REQUIRED_COMPOSITION_INVARIANT_IDS],
            "authority_expansion": True,
            "topology_change_requires_human_approval": False,
        },
        {
            "schema_version": "orchestra.agentic-composition-invariants.v1",
            "owner": "conductor",
            "invariants": [{"id": item, "hard": True} for item in topology_module.REQUIRED_COMPOSITION_INVARIANT_IDS],
            "authority_expansion": False,
            "topology_change_requires_human_approval": True,
        },
    ],
)
def test_invariant_contract_loader_rejections(monkeypatch, value):
    monkeypatch.setattr(machine_awf, "_load_json", lambda _path: value)
    with pytest.raises((TypeError, ValueError)):
        machine_awf.load_agentic_composition_invariants(ROOT)


def test_machine_error_projection_returns_structured_failure(monkeypatch):
    monkeypatch.setattr(
        machine_awf,
        "load_agentic_workflow_contracts",
        lambda _root=None: (_ for _ in ()).throw(ValueError("broken")),
    )
    assert machine_awf.agentic_workflow_errors(ROOT) == (
        "AGENTIC_WORKFLOW_CONTRACT_INVALID:broken",
    )
