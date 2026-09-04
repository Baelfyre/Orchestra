from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.adapters import CodexAdapter
from orchestra_runtime.domain.orchestration.ui_fidelity import MINIMAL_SAFE, UI_CONTRACT_FIDELITY
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
