from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.domain.orchestration.ui_fidelity import validate_ui_fidelity_handoff
from orchestra_runtime.machine_contracts import load_ui_fidelity_handoff_contract


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "machine" / "ui" / "ui-implementation-profile.v1.json"
HANDOFF_PATH = ROOT / "machine" / "ui" / "ui-fidelity-handoff.v1.json"
CUIR3_PATH = ROOT / "machine" / "knowledge" / "cloak-ui-reference-cuir3.v1.json"
HISTORICAL_BLOCKER = (
    ROOT / "tests" / "fixtures" / "oee" / "uief5-responsive-contradiction-20260905.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(reference: str) -> Path:
    value = str(reference).split("#", 1)[0].strip()
    assert value
    assert "://" not in value
    return ROOT / value


def _profile_references(profile: dict) -> list[str]:
    refs = [
        profile["design_contract_ref"],
        profile["cloak_handoff_ref"],
        profile["clockwork_boundary_ref"],
    ]
    refs.extend(item["reference_ref"] for item in profile["pattern_refs"])
    refs.extend(item["reference_ref"] for item in profile["composition_refs"])
    return refs


def _handoff_references(handoff: dict) -> list[str]:
    refs = [
        handoff["design_contract_ref"],
        handoff["ui_implementation_profile_ref"],
    ]
    refs.extend(item["reference_ref"] for item in handoff["provenance_refs"])
    refs.extend(item["reference_ref"] for item in handoff["macro_composition"] if item.get("reference_ref"))
    refs.extend(item["reference_ref"] for item in handoff["selected_pattern_refs"])
    refs.extend(item["reference_ref"] for item in handoff["asset_requirements"] if item.get("reference_ref"))
    return refs


def test_canonical_uief_reference_paths_exist() -> None:
    profile = _load(PROFILE_PATH)
    handoff = _load(HANDOFF_PATH)
    refs = _profile_references(profile) + _handoff_references(handoff)
    missing = [ref for ref in refs if not _repo_path(ref).is_file()]
    assert missing == []


def test_canonical_cuir_pattern_ids_exist_in_canonical_catalog() -> None:
    profile = _load(PROFILE_PATH)
    handoff = _load(HANDOFF_PATH)
    catalog = _load(CUIR3_PATH)
    known = {item["pattern_id"] for item in catalog["patterns"]}

    profile_ids = {
        item["pattern_id"]
        for item in profile["pattern_refs"]
        if item["source_kind"] == "CUIR_NORMALIZED"
    }
    handoff_ids = {
        item["pattern_id"]
        for item in handoff["selected_pattern_refs"]
        if item["source_kind"] == "CUIR_NORMALIZED"
    }
    provenance_ids = {
        item["provenance_id"]
        for item in handoff["provenance_refs"]
        if item["source_kind"] == "CUIR_NORMALIZED"
    }

    assert profile_ids
    assert handoff_ids
    assert provenance_ids
    assert profile_ids <= known
    assert handoff_ids <= known
    assert provenance_ids <= known


def test_reference_contract_does_not_invent_project_or_provider_sources() -> None:
    profile = _load(PROFILE_PATH)
    handoff = _load(HANDOFF_PATH)
    source_kinds = {
        item["source_kind"]
        for item in profile["pattern_refs"] + handoff["selected_pattern_refs"] + handoff["provenance_refs"]
    }
    assert source_kinds == {"CUIR_NORMALIZED"}

    serialized = json.dumps({"profile": profile, "handoff": handoff})
    for forbidden in (
        "docs/specs/",
        "components/palette/CommandPalette.tsx",
        "PUBLIC-PROVIDER-ANTHROPIC-CANVAS-001",
        "OBSERVED-PROVIDER-SIDECAR-DRAWER-001",
        "CUIR-3-WORKSPACE-SPLIT-PANE-001",
        "assets/icons/command.svg",
        "tokens/color.json",
    ):
        assert forbidden not in serialized


def test_live_responsive_contract_is_internally_consistent() -> None:
    handoff = _load(HANDOFF_PATH)
    responsive_macro = next(
        item
        for item in handoff["macro_composition"]
        if item["composition_id"] == "split-pane-responsive-collapse"
    )
    description = responsive_macro["description"].casefold()
    assert "drawer" in description
    assert "accordion" not in description

    tablet = next(
        item for item in handoff["responsive_transformations"]
        if "tablet" in item["breakpoint"].casefold()
    )
    mobile = next(
        item for item in handoff["responsive_transformations"]
        if "mobile" in item["breakpoint"].casefold()
    )
    assert "drawer" in tablet["transformation"].casefold()
    assert "drawer" in mobile["transformation"].casefold()


def test_historical_oee_replay_fixture_preserves_original_contradiction() -> None:
    historical = _load(HISTORICAL_BLOCKER)
    responsive_macro = next(
        item
        for item in historical["macro_composition"]
        if item["structural_role"] == "RESPONSIVE_TRANSFORMATION"
    )
    tablet = next(
        item for item in historical["responsive_transformations"]
        if "tablet" in item["breakpoint"].casefold()
    )
    assert "accordion" in responsive_macro["description"].casefold()
    assert "drawer" in tablet["transformation"].casefold()


def test_generated_ponytail_context_uses_real_clockwork_boundary_reference() -> None:
    handoff = validate_ui_fidelity_handoff(load_ui_fidelity_handoff_contract(ROOT))
    context = handoff.to_ponytail_context()["ui_fidelity_context"]
    reference = context["clockwork_boundary_ref"]
    assert _repo_path(reference).is_file()
    assert reference == "docs/project/UI_EXECUTION_FIDELITY_PLAN.md"
