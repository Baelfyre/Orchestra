from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from orchestra_runtime.domain.orchestration.ui_fidelity import (
    UI_CONTRACT_FIDELITY,
    UI_FIDELITY_HANDOFF_SCHEMA,
    VALID_SOURCE_KINDS,
    UIFidelityHandoff,
    enforce_ponytail_fidelity_execution,
    validate_ui_fidelity_handoff,
)
from orchestra_runtime.machine_contracts import load_ui_fidelity_handoff_contract


ROOT = Path(__file__).resolve().parents[2]
MACHINE_HANDOFF = ROOT / "machine" / "ui" / "ui-fidelity-handoff.v1.json"
UIX9_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
CLOAK_SKILL_MD = ROOT / "skills" / "cloak" / "SKILL.md"
GUIDE_SOURCE = ROOT / "skills" / "cloak" / "UI_FIDELITY_HANDOFF_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "cloak" / "UI_FIDELITY_HANDOFF_GUIDE.md"
OUTPUT_FORMATS_SOURCE = ROOT / "skills" / "cloak" / "OUTPUT_FORMATS.md"
OUTPUT_FORMATS_CODEX = ROOT / "adapters" / "codex" / "skills" / "cloak" / "OUTPUT_FORMATS.md"
FIXTURES = ROOT / "tests" / "fixtures" / "ui"


def _load_fixture(filename: str) -> dict:
    return json.loads((FIXTURES / filename).read_text(encoding="utf-8"))


def test_valid_fidelity_handoff_fixture_parses_and_validates() -> None:
    data = _load_fixture("uief4-valid-fidelity-handoff.json")
    handoff = validate_ui_fidelity_handoff(data)

    assert isinstance(handoff, UIFidelityHandoff)
    assert handoff.schema_version == UI_FIDELITY_HANDOFF_SCHEMA
    assert handoff.owned_by == "cloak"
    assert handoff.contract_id == "uief4-ui-fidelity-handoff-reference"
    assert len(handoff.macro_composition) == 3
    assert len(handoff.selected_pattern_refs) == 2
    assert len(handoff.provenance_refs) == 2
    assert len(handoff.preserve) == 4
    assert len(handoff.avoid) == 4
    assert handoff.authority["implementation_authorized"] is False
    assert handoff.authority["architecture_translation_authorized"] is False
    assert handoff.authority["release_authorized"] is False

    # Verify serialization
    serialized = handoff.to_dict()
    assert serialized["schema_version"] == UI_FIDELITY_HANDOFF_SCHEMA
    assert serialized["owned_by"] == "cloak"
    assert len(serialized["macro_composition"]) == 3
    assert serialized["authority"] == handoff.authority


def test_machine_reference_fixture_loads_and_validates() -> None:
    data = load_ui_fidelity_handoff_contract()
    handoff = validate_ui_fidelity_handoff(data)
    assert handoff.contract_id == "uief4-ui-fidelity-handoff-reference"
    assert handoff.owned_by == "cloak"


def test_handoff_to_ponytail_context_executes_cleanly() -> None:
    data = _load_fixture("uief4-valid-fidelity-handoff.json")
    handoff = validate_ui_fidelity_handoff(data)
    ponytail_ctx = handoff.to_ponytail_context()

    assert ponytail_ctx["ui_implementation_profile"] == UI_CONTRACT_FIDELITY
    assert "ui_fidelity_context" in ponytail_ctx
    inner_ctx = ponytail_ctx["ui_fidelity_context"]
    assert inner_ctx["design_contract_ref"] == handoff.design_contract_ref
    assert inner_ctx["cloak_handoff_ref"] == handoff.contract_id
    assert inner_ctx["clockwork_boundary_ref"] == "docs/project/UI_EXECUTION_FIDELITY_PLAN.md"

    # Enforce through Ponytail execution gate
    execution = enforce_ponytail_fidelity_execution(
        ponytail_ctx,
        {
            "preserved_compositions": [
                "desktop-macro-grid",
                "action-bar-visual-hierarchy",
                "split-pane-responsive-collapse",
            ],
            "project_native_reuse": [],
            "deviations": [],
        },
    )
    assert execution.profile == UI_CONTRACT_FIDELITY
    assert execution.static_review_ready is True
    assert execution.requires_upstream_reentry is False


def test_invalid_missing_binding_fixture_fails() -> None:
    data = _load_fixture("uief4-invalid-missing-binding.json")
    with pytest.raises(ValueError, match="UIFidelityHandoff requires non-empty string design_contract_ref"):
        validate_ui_fidelity_handoff(data)


def test_invalid_ponytail_owner_fixture_fails() -> None:
    data = _load_fixture("uief4-invalid-ponytail-owner.json")
    with pytest.raises(ValueError, match="UIFidelityHandoff must be owned by cloak"):
        validate_ui_fidelity_handoff(data)


def test_invalid_clockwork_translation_fixture_fails() -> None:
    data = _load_fixture("uief4-invalid-clockwork-translation.json")
    with pytest.raises(ValueError, match="cannot embed or initiate UIEF-5 engineering translation"):
        validate_ui_fidelity_handoff(data)

    # Test direct dataclass attribute rejection
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")
    handoff = validate_ui_fidelity_handoff(base_data)
    object.__setattr__(handoff, "clockwork_translation", True)
    with pytest.raises(ValueError, match="cannot embed or initiate UIEF-5 engineering translation"):
        handoff.validate()


def test_invalid_contaminated_execution_mode_fixture_fails() -> None:
    data = _load_fixture("uief4-invalid-contaminated-execution-mode.json")
    with pytest.raises(ValueError, match="Generic execution_mode cannot be contaminated"):
        validate_ui_fidelity_handoff(data)


def test_authority_invariants_strictly_enforced() -> None:
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")

    # Implementation authorized attempt
    bad = copy.deepcopy(base_data)
    bad["authority"]["implementation_authorized"] = True
    with pytest.raises(ValueError, match="cannot authorize implementation"):
        validate_ui_fidelity_handoff(bad)

    # Architecture translation authorized attempt
    bad = copy.deepcopy(base_data)
    bad["authority"]["architecture_translation_authorized"] = True
    with pytest.raises(ValueError, match="cannot authorize implementation"):
        validate_ui_fidelity_handoff(bad)

    # Release authorized attempt
    bad = copy.deepcopy(base_data)
    bad["authority"]["release_authorized"] = True
    with pytest.raises(ValueError, match="cannot authorize implementation"):
        validate_ui_fidelity_handoff(bad)

    # Missing or invalid authority
    bad = copy.deepcopy(base_data)
    bad["authority"] = "not-a-mapping"
    with pytest.raises(ValueError, match="requires mapping authority"):
        validate_ui_fidelity_handoff(bad)

    # Direct dataclass authority tests
    with pytest.raises(ValueError, match="requires mapping authority"):
        UIFidelityHandoff(
            schema_version=UI_FIDELITY_HANDOFF_SCHEMA,
            contract_id="id",
            owned_by="cloak",
            design_contract_ref="ref",
            ui_implementation_profile_ref="ref",
            source_revision_or_contract_identity="ref",
            provenance_refs=(),
            design_intent="intent",
            information_hierarchy=(),
            macro_composition=(),
            selected_pattern_refs=(),
            pattern_application_reason="reason",
            required_regions=(),
            component_roles={},
            visual_relationships={},
            typography_roles={},
            spacing_relationships={},
            responsive_transformations=(),
            interaction_states=(),
            asset_requirements=(),
            preserve=(),
            adapt=(),
            avoid=(),
            unresolved=(),
            authority="not-a-mapping",  # type: ignore[arg-type]
        ).validate()

    with pytest.raises(ValueError, match="must be owned by cloak"):
        UIFidelityHandoff(
            schema_version=UI_FIDELITY_HANDOFF_SCHEMA,
            contract_id="id",
            owned_by="ponytail",
            design_contract_ref="ref",
            ui_implementation_profile_ref="ref",
            source_revision_or_contract_identity="ref",
            provenance_refs=(),
            design_intent="intent",
            information_hierarchy=(),
            macro_composition=(),
            selected_pattern_refs=(),
            pattern_application_reason="reason",
            required_regions=(),
            component_roles={},
            visual_relationships={},
            typography_roles={},
            spacing_relationships={},
            responsive_transformations=(),
            interaction_states=(),
            asset_requirements=(),
            preserve=(),
            adapt=(),
            avoid=(),
            unresolved=(),
            authority={"implementation_authorized": False, "architecture_translation_authorized": False, "release_authorized": False},
        ).validate()


def test_string_field_validations() -> None:
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")

    # Invalid schema version
    bad = copy.deepcopy(base_data)
    bad["schema_version"] = "wrong.schema.version"
    with pytest.raises(ValueError, match="unsupported UIFidelityHandoff schema_version"):
        validate_ui_fidelity_handoff(bad)

    for field in (
        "contract_id",
        "design_contract_ref",
        "ui_implementation_profile_ref",
        "source_revision_or_contract_identity",
        "design_intent",
        "pattern_application_reason",
    ):
        bad = copy.deepcopy(base_data)
        bad[field] = "   "
        with pytest.raises(ValueError, match=f"requires non-empty string {field}"):
            validate_ui_fidelity_handoff(bad)


def test_required_collections_validation() -> None:
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")

    for field in (
        "provenance_refs",
        "information_hierarchy",
        "macro_composition",
        "selected_pattern_refs",
        "required_regions",
        "preserve",
        "avoid",
    ):
        bad = copy.deepcopy(base_data)
        bad[field] = []
        with pytest.raises(ValueError, match=f"requires non-empty collection {field}"):
            validate_ui_fidelity_handoff(bad)

    bad = copy.deepcopy(base_data)
    bad["unresolved"] = "not-a-list"
    with pytest.raises(ValueError, match="requires list or tuple for unresolved"):
        validate_ui_fidelity_handoff(bad)

    # Test mapping type checking
    for map_field in (
        "component_roles",
        "visual_relationships",
        "typography_roles",
        "spacing_relationships",
    ):
        bad = copy.deepcopy(base_data)
        bad[map_field] = "not-a-mapping"
        with pytest.raises(ValueError, match=f"requires mapping for {map_field}"):
            validate_ui_fidelity_handoff(bad)

    # Direct dataclass test for unresolved
    with pytest.raises(ValueError, match="requires unresolved list"):
        handoff = validate_ui_fidelity_handoff(base_data)
        UIFidelityHandoff(
            schema_version=handoff.schema_version,
            contract_id=handoff.contract_id,
            owned_by=handoff.owned_by,
            design_contract_ref=handoff.design_contract_ref,
            ui_implementation_profile_ref=handoff.ui_implementation_profile_ref,
            source_revision_or_contract_identity=handoff.source_revision_or_contract_identity,
            provenance_refs=handoff.provenance_refs,
            design_intent=handoff.design_intent,
            information_hierarchy=handoff.information_hierarchy,
            macro_composition=handoff.macro_composition,
            selected_pattern_refs=handoff.selected_pattern_refs,
            pattern_application_reason=handoff.pattern_application_reason,
            required_regions=handoff.required_regions,
            component_roles=handoff.component_roles,
            visual_relationships=handoff.visual_relationships,
            typography_roles=handoff.typography_roles,
            spacing_relationships=handoff.spacing_relationships,
            responsive_transformations=handoff.responsive_transformations,
            interaction_states=handoff.interaction_states,
            asset_requirements=handoff.asset_requirements,
            preserve=handoff.preserve,
            adapt=handoff.adapt,
            avoid=handoff.avoid,
            unresolved="not-a-tuple",  # type: ignore[arg-type]
            authority=handoff.authority,
        ).validate()


def test_pattern_refs_validation() -> None:
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")

    bad = copy.deepcopy(base_data)
    bad["selected_pattern_refs"] = ["not-a-mapping"]
    with pytest.raises(ValueError, match="selected_pattern_refs items must be mappings"):
        validate_ui_fidelity_handoff(bad)

    bad = copy.deepcopy(base_data)
    bad["selected_pattern_refs"] = [{"pattern_id": "", "source_kind": "CUIR_NORMALIZED", "provenance_id": "P1"}]
    with pytest.raises(ValueError, match="selected_pattern_refs items require pattern_id"):
        validate_ui_fidelity_handoff(bad)

    bad = copy.deepcopy(base_data)
    bad["selected_pattern_refs"] = [{"pattern_id": "p1", "source_kind": "INVALID_KIND", "provenance_id": "P1"}]
    with pytest.raises(ValueError, match="unrecognized source_kind"):
        validate_ui_fidelity_handoff(bad)

    bad = copy.deepcopy(base_data)
    bad["selected_pattern_refs"] = [{"pattern_id": "p1", "source_kind": "CUIR_NORMALIZED", "provenance_id": ""}]
    with pytest.raises(ValueError, match="selected_pattern_refs items require provenance_id"):
        validate_ui_fidelity_handoff(bad)


def test_macro_composition_validation() -> None:
    base_data = _load_fixture("uief4-valid-fidelity-handoff.json")

    bad = copy.deepcopy(base_data)
    bad["macro_composition"] = ["not-a-mapping"]
    with pytest.raises(ValueError, match="macro_composition items must be mappings"):
        validate_ui_fidelity_handoff(bad)

    bad = copy.deepcopy(base_data)
    bad["macro_composition"] = [{"structural_role": "MACRO_LAYOUT"}]
    with pytest.raises(ValueError, match="macro_composition items require composition_id"):
        validate_ui_fidelity_handoff(bad)


def test_validate_ui_fidelity_handoff_requires_mapping() -> None:
    with pytest.raises(ValueError, match="UIFidelityHandoff data must be a mapping"):
        validate_ui_fidelity_handoff("not-a-mapping")  # type: ignore[arg-type]


def test_frozen_cloak_identity_preserved() -> None:
    manifest_data = json.loads(UIX9_MANIFEST.read_text(encoding="utf-8"))
    cloak_entries = [
        entry for entry in manifest_data.get("materials", [])
        if entry.get("path") == "skills/cloak/SKILL.md"
    ]
    assert len(cloak_entries) == 1, "skills/cloak/SKILL.md must be registered in uix9 manifest"
    expected_digest = cloak_entries[0]["canonical_blob_digest"]
    skill_content = CLOAK_SKILL_MD.read_bytes().replace(b"\r\n", b"\n")
    actual_digest = hashlib.sha256(skill_content).hexdigest()
    assert actual_digest == expected_digest, (
        f"skills/cloak/SKILL.md was modified! Expected digest {expected_digest} but found {actual_digest}"
    )


def test_codex_parity_mirrors_exist_and_byte_identical() -> None:
    assert GUIDE_SOURCE.exists(), "skills/cloak/UI_FIDELITY_HANDOFF_GUIDE.md must exist"
    assert GUIDE_CODEX.exists(), "adapters/codex/skills/cloak/UI_FIDELITY_HANDOFF_GUIDE.md must exist"
    guide_source_bytes = GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    guide_codex_bytes = GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert guide_source_bytes == guide_codex_bytes, "Guide must be byte-identical between skills/ and adapters/"

    assert OUTPUT_FORMATS_SOURCE.exists(), "skills/cloak/OUTPUT_FORMATS.md must exist"
    assert OUTPUT_FORMATS_CODEX.exists(), "adapters/codex/skills/cloak/OUTPUT_FORMATS.md must exist"
    out_source_bytes = OUTPUT_FORMATS_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    out_codex_bytes = OUTPUT_FORMATS_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert out_source_bytes == out_codex_bytes, "OUTPUT_FORMATS.md must be byte-identical between skills/ and adapters/"
    assert "UI_FIDELITY_HANDOFF" in OUTPUT_FORMATS_SOURCE.read_text(encoding="utf-8")
