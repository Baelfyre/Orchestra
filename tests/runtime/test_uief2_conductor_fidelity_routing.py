from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.adapters import CodexAdapter
from orchestra_runtime.domain.orchestration.ui_fidelity import (
    MINIMAL_SAFE,
    UI_CONTRACT_FIDELITY,
    classify_ui_fidelity,
)
from orchestra_runtime.machine_contracts import load_ui_fidelity_routing_contract
from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import ContextAssembler, RouterService, SkillRegistry


ROOT = Path(__file__).resolve().parents[2]
PROFILE = json.loads((ROOT / "machine/ui/ui-implementation-profile.v1.json").read_text(encoding="utf-8"))


def _context(prompt: str, metadata: dict | None = None) -> ContextPackage:
    repository = ManifestRepository(ROOT)
    adapter = CodexAdapter(repository)
    return ContextAssembler(repository).assemble(adapter, prompt, metadata)


def _router() -> RouterService:
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    return RouterService(registry)


def _classify(prompt: str, metadata: dict | None = None, contract: dict | None = None):
    return classify_ui_fidelity(prompt, metadata, contract or load_ui_fidelity_routing_contract(ROOT))


def test_uief2_machine_contract_is_schema_valid_and_loaded() -> None:
    schema = json.loads((ROOT / "machine/schemas/ui-fidelity-routing.v1.schema.json").read_text(encoding="utf-8"))
    contract = load_ui_fidelity_routing_contract(ROOT)
    jsonschema.Draft202012Validator(schema).validate(contract)
    assert contract["selected_by"] == "conductor"
    assert contract["profiles"] == [MINIMAL_SAFE, UI_CONTRACT_FIDELITY]


def test_material_trigger_selects_fidelity_and_forbids_fast_with_bounded_context() -> None:
    prompt = "Implement the accepted Figma design with responsive reordering and interaction states."
    context = _context(
        prompt,
        {
            "ui_implementation_profile": copy.deepcopy(PROFILE),
            "execution_mode": "HOST_NATIVE",
            "unrelated_corpus": ["must not be forwarded"],
        },
    )

    assert context.metadata["ui_implementation_profile"] == UI_CONTRACT_FIDELITY
    assert context.metadata["fast_mode_prohibited"] is True
    assert context.metadata["execution_mode"] == "HOST_NATIVE"
    assert set(context.metadata["ui_fidelity_context"]) == {
        "profile",
        "design_contract_ref",
        "cloak_handoff_ref",
        "pattern_refs",
        "composition_refs",
        "clockwork_boundary_ref",
        "required_fidelity",
        "allowed_deviations",
        "selection_reason",
        "selected_by",
        "authority",
    }
    assert "unrelated_corpus" not in context.metadata["ui_fidelity_context"]

    command = Command("conductor", prompt, "codex")
    decision = _router().route(command, context)
    assert decision.metadata["ui_implementation_profile"] == UI_CONTRACT_FIDELITY
    assert decision.metadata["fast_mode_prohibited"] is True


def test_multiple_fidelity_triggers_are_deterministic() -> None:
    prompt = "Preserve the UI design contract, CUIR pattern references, visual hierarchy, and responsive transformation."
    first = _context(prompt, {"ui_implementation_profile": copy.deepcopy(PROFILE)})
    second = _context(prompt, {"ui_implementation_profile": copy.deepcopy(PROFILE)})

    assert first.metadata["ui_fidelity_trigger_ids"] == second.metadata["ui_fidelity_trigger_ids"]
    assert first.metadata["ui_fidelity_context"] == second.metadata["ui_fidelity_context"]


def test_trivial_ui_change_remains_fast_eligible_and_loads_no_fidelity_context() -> None:
    context = _context(
        "Fix the typo in the submit button label.",
        {"risk_mode": "FAST", "ui_fidelity_context": {"unrelated_corpus": ["stale"]}},
    )

    assert context.metadata["ui_implementation_profile"] == MINIMAL_SAFE
    assert context.metadata["fast_mode_prohibited"] is False
    assert "ui_fidelity_context" not in context.metadata
    assert context.metadata["risk_mode"] == "FAST"


def test_material_trigger_cannot_enter_fast_even_for_small_request() -> None:
    with pytest.raises(ValueError, match="FAST_MODE_PROHIBITED"):
        _context(
            "Change one small file to preserve the accepted visual hierarchy.",
            {"ui_implementation_profile": copy.deepcopy(PROFILE), "risk_mode": "FAST"},
        )


def test_profile_selection_and_downgrade_authority_fail_closed() -> None:
    ponytail_profile = copy.deepcopy(PROFILE)
    ponytail_profile["selected_by"] = "ponytail"
    with pytest.raises(ValueError, match="only be selected by conductor"):
        _context("Implement the accepted UI design contract.", {"ui_implementation_profile": ponytail_profile})

    downgrade = copy.deepcopy(PROFILE)
    downgrade["profile"] = MINIMAL_SAFE
    with pytest.raises(ValueError, match="conflicts with a material"):
        _context("Preserve the accepted visual hierarchy.", {"ui_implementation_profile": downgrade})


def test_missing_required_fidelity_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires conductor-selected profile evidence"):
        _context("Implement the accepted Figma design.")


def test_mapping_evidence_is_considered_without_broadening_forwarded_context() -> None:
    context = _context(
        "Implement the accepted UI design contract.",
        {
            "ui_implementation_profile": copy.deepcopy(PROFILE),
            "ui_fidelity_evidence": {"visual_hierarchy": True, "unrelated_corpus": ["drop"]},
        },
    )
    assert context.metadata["ui_implementation_profile"] == UI_CONTRACT_FIDELITY
    assert "unrelated_corpus" not in context.metadata["ui_fidelity_context"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda profile: profile.clear(), "missing required evidence"),
        (lambda profile: profile.update(selection_reason=""), "requires a selection reason"),
        (lambda profile: profile.update(design_contract_ref=""), "requires design_contract_ref"),
        (lambda profile: profile.update(pattern_refs=[]), "requires non-empty pattern_refs"),
        (lambda profile: profile.update(required_fidelity=None), "requires required_fidelity evidence"),
        (
            lambda profile: profile["required_fidelity"].update(preserve_visual_hierarchy=False),
            "preserve_visual_hierarchy=true",
        ),
        (lambda profile: profile.update(authority=None), "requires authority boundaries"),
        (
            lambda profile: profile["authority"].update(ponytail_can_downgrade=True),
            "authority boundary ponytail_can_downgrade must be false",
        ),
    ],
)
def test_invalid_fidelity_profile_evidence_fails_closed(mutate, message: str) -> None:
    profile = copy.deepcopy(PROFILE)
    mutate(profile)
    with pytest.raises(ValueError, match=message):
        _classify("Implement the accepted UI design contract.", {"ui_implementation_profile": profile})


def test_malformed_profile_payload_and_profile_name_fail_closed() -> None:
    with pytest.raises(ValueError, match="object or a canonical profile name"):
        _classify("Fix a button label.", {"ui_implementation_profile": 7})
    with pytest.raises(ValueError, match="must be MINIMAL_SAFE"):
        _classify("Fix a button label.", {"ui_implementation_profile": {"profile": "UNSAFE"}})


def test_malformed_trigger_contract_fails_closed() -> None:
    contract = copy.deepcopy(load_ui_fidelity_routing_contract(ROOT))
    contract["triggers"][0]["prompt_terms"] = "not-a-list"
    with pytest.raises(ValueError, match="prompt_terms must be a list"):
        _classify("anything", contract=contract)


def test_minimal_profile_boundaries_are_checked_without_selecting_fidelity() -> None:
    assert _classify("Fix a button label.", {"ui_implementation_profile": {"profile": None}}).selected_profile == MINIMAL_SAFE

    contract = copy.deepcopy(load_ui_fidelity_routing_contract(ROOT))
    contract["profiles"].append("UNSAFE")
    with pytest.raises(ValueError, match="conflicting UI profile"):
        _classify("Fix a button label.", {"ui_implementation_profile": {"profile": "UNSAFE"}}, contract=contract)

    with pytest.raises(ValueError, match="only be selected by conductor"):
        _classify("Fix a button label.", {"ui_implementation_profile": {"selected_by": "ponytail"}})

    safe_authority = {
        key: False
        for key in load_ui_fidelity_routing_contract(ROOT)["authority_false_fields"]
    }
    assert _classify(
        "Fix a button label.",
        {"ui_implementation_profile": {"authority": safe_authority}},
    ).selected_profile == MINIMAL_SAFE

    unsafe_authority = dict(safe_authority)
    unsafe_authority["ponytail_can_self_select"] = True
    with pytest.raises(ValueError, match="authority boundary ponytail_can_self_select must be false"):
        _classify("Fix a button label.", {"ui_implementation_profile": {"authority": unsafe_authority}})
