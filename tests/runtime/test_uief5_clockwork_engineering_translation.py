from __future__ import annotations

import copy
from pathlib import Path

import pytest

from orchestra_runtime.domain.orchestration.ui_fidelity import (
    UI_CONTRACT_FIDELITY,
    UI_ENGINEERING_TRANSLATION_SCHEMA,
    UIEngineeringTranslation,
    validate_ui_engineering_translation,
    validate_ui_fidelity_handoff,
)
from orchestra_runtime.machine_contracts import (
    load_ui_engineering_translation_contract,
    load_ui_fidelity_handoff_contract,
)


ROOT = Path(__file__).resolve().parents[2]
GUIDE_SOURCE = ROOT / "skills" / "clockwork" / "UI_ENGINEERING_TRANSLATION_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "clockwork" / "UI_ENGINEERING_TRANSLATION_GUIDE.md"
OUTPUT_SOURCE = ROOT / "skills" / "clockwork" / "OUTPUT_FORMATS.md"
OUTPUT_CODEX = ROOT / "adapters" / "codex" / "skills" / "clockwork" / "OUTPUT_FORMATS.md"


def _handoff():
    return validate_ui_fidelity_handoff(load_ui_fidelity_handoff_contract(ROOT))


def _translation_data() -> dict:
    return load_ui_engineering_translation_contract(ROOT)


def test_reference_translation_loads_and_preserves_handoff_compositions() -> None:
    handoff = _handoff()
    translation = validate_ui_engineering_translation(_translation_data(), handoff)

    assert isinstance(translation, UIEngineeringTranslation)
    assert translation.schema_version == UI_ENGINEERING_TRANSLATION_SCHEMA
    assert translation.owned_by == "clockwork"
    assert translation.source_handoff_ref == handoff.contract_id
    assert {item["composition_id"] for item in translation.composition_ownership} == {
        item["composition_id"] for item in handoff.macro_composition
    }
    assert translation.authority["visible_layer_redesign_authorized"] is False
    assert translation.authority["implementation_authorized"] is False
    assert translation.authority["dependency_adoption_authorized"] is False
    assert translation.authority["release_authorized"] is False


def test_translation_serialization_is_stable() -> None:
    translation = validate_ui_engineering_translation(_translation_data(), _handoff())
    serialized = translation.to_dict()

    assert serialized["schema_version"] == UI_ENGINEERING_TRANSLATION_SCHEMA
    assert serialized["owned_by"] == "clockwork"
    assert serialized["component_boundaries"] == list(translation.component_boundaries)
    assert serialized["authority"] == translation.authority


def test_clockwork_cannot_redesign_or_simplify_visible_complexity() -> None:
    base = _translation_data()

    for field in (
        "redesigned_visible_intent",
        "visible_layer_redesign",
        "simplified_visible_complexity_for_architecture",
    ):
        bad = copy.deepcopy(base)
        bad[field] = True
        with pytest.raises(ValueError, match="cannot redesign accepted visible intent"):
            validate_ui_engineering_translation(bad, _handoff())


def test_clockwork_cannot_initiate_uief6() -> None:
    base = _translation_data()

    for field in ("starts_uief6", "cross_specialist_chain"):
        bad = copy.deepcopy(base)
        bad[field] = True
        with pytest.raises(ValueError, match="initiate UIEF-6"):
            validate_ui_engineering_translation(bad, _handoff())


def test_translation_rejects_generic_execution_mode_contamination() -> None:
    bad = copy.deepcopy(_translation_data())
    bad["execution_mode"] = UI_CONTRACT_FIDELITY

    with pytest.raises(ValueError, match="Generic execution_mode cannot be contaminated"):
        validate_ui_engineering_translation(bad, _handoff())


def test_translation_owner_and_authority_are_fail_closed() -> None:
    bad_owner = copy.deepcopy(_translation_data())
    bad_owner["owned_by"] = "cloak"
    with pytest.raises(ValueError, match="must be owned by clockwork"):
        validate_ui_engineering_translation(bad_owner, _handoff())

    for authority_field in (
        "visible_layer_redesign_authorized",
        "implementation_authorized",
        "dependency_adoption_authorized",
        "release_authorized",
    ):
        bad = copy.deepcopy(_translation_data())
        bad["authority"][authority_field] = True
        with pytest.raises(ValueError, match=f"{authority_field} must be false"):
            validate_ui_engineering_translation(bad, _handoff())


def test_translation_must_bind_exact_accepted_handoff() -> None:
    bad = copy.deepcopy(_translation_data())
    bad["source_handoff_ref"] = "different-handoff"

    with pytest.raises(ValueError, match="must match accepted UIFidelityHandoff"):
        validate_ui_engineering_translation(bad, _handoff())


def test_translation_must_preserve_every_accepted_composition_identity() -> None:
    handoff = _handoff()
    bad = copy.deepcopy(_translation_data())
    bad["composition_ownership"] = [
        item for item in bad["composition_ownership"]
        if item["composition_id"] != "split-pane-responsive-collapse"
    ]

    with pytest.raises(
        ValueError,
        match="must preserve accepted composition ownership: split-pane-responsive-collapse",
    ):
        validate_ui_engineering_translation(bad, handoff)


def test_translation_rejects_duplicate_boundary_identity() -> None:
    bad = copy.deepcopy(_translation_data())
    bad["component_boundaries"].append(copy.deepcopy(bad["component_boundaries"][0]))

    with pytest.raises(ValueError, match="duplicate component_id"):
        validate_ui_engineering_translation(bad, _handoff())


def test_translation_requires_non_empty_engineering_boundaries() -> None:
    for field in (
        "component_boundaries",
        "state_ownership",
        "responsive_engineering",
        "composition_ownership",
        "data_flow_boundaries",
        "reusable_component_strategy",
        "integration_boundaries",
        "dependency_boundaries",
        "preserve",
    ):
        bad = copy.deepcopy(_translation_data())
        bad[field] = []
        with pytest.raises(ValueError, match=f"non-empty collection {field}"):
            validate_ui_engineering_translation(bad, _handoff())


def test_clockwork_guide_and_output_codex_parity() -> None:
    assert GUIDE_SOURCE.exists()
    assert GUIDE_CODEX.exists()
    assert GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n") == GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")

    assert OUTPUT_SOURCE.exists()
    assert OUTPUT_CODEX.exists()
    assert OUTPUT_SOURCE.read_bytes().replace(b"\r\n", b"\n") == OUTPUT_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert "UI_ENGINEERING_TRANSLATION" in OUTPUT_SOURCE.read_text(encoding="utf-8")
