from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from orchestra_runtime.adapters import CodexAdapter
from orchestra_runtime.domain.orchestration.ui_fidelity import (
    MINIMAL_SAFE,
    UI_CONTRACT_FIDELITY,
    PonytailFidelityExecution,
    UIDeviationRecord,
    enforce_ponytail_fidelity_execution,
)
from orchestra_runtime.models import ContextPackage
from orchestra_runtime.repositories import ManifestRepository
from orchestra_runtime.services import ContextAssembler


ROOT = Path(__file__).resolve().parents[2]
PROFILE = json.loads((ROOT / "machine/ui/ui-implementation-profile.v1.json").read_text(encoding="utf-8"))
UIX9_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
SKILL_MD = ROOT / "skills" / "ponytail" / "SKILL.md"
GUIDE_SOURCE = ROOT / "skills" / "ponytail" / "FRONTEND_FIDELITY_EXECUTION_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "ponytail" / "FRONTEND_FIDELITY_EXECUTION_GUIDE.md"
OUTPUT_FORMATS_SOURCE = ROOT / "skills" / "ponytail" / "OUTPUT_FORMATS.md"
OUTPUT_FORMATS_CODEX = ROOT / "adapters" / "codex" / "skills" / "ponytail" / "OUTPUT_FORMATS.md"


def _context(prompt: str, metadata: dict | None = None) -> ContextPackage:
    repository = ManifestRepository(ROOT)
    adapter = CodexAdapter(repository)
    return ContextAssembler(repository).assemble(adapter, prompt, metadata)


def _valid_fidelity_context() -> ContextPackage:
    return _context(
        "Implement the accepted UI design contract with macro composition and states.",
        {
            "ui_implementation_profile": copy.deepcopy(PROFILE),
            "execution_mode": "HOST_NATIVE",
        },
    )


def test_ui_contract_fidelity_preserves_required_semantics() -> None:
    context = _valid_fidelity_context()
    execution = enforce_ponytail_fidelity_execution(
        context,
        {
            "preserved_compositions": [
                "desktop-macro-grid",
                "action-bar-visual-hierarchy",
                "split-pane-responsive-collapse",
            ],
            "preserved_hierarchies": ["action-bar-visual-hierarchy"],
            "preserved_states": ["default", "hover", "focus-visible", "active"],
            "preserved_responsive": ["split-pane-responsive-collapse"],
            "project_native_reuse": ["native-command-palette"],
            "deviations": [],
            "motion_implemented": False,
        },
    )

    assert execution.profile == UI_CONTRACT_FIDELITY
    assert set(execution.preserved_compositions) == {
        "desktop-macro-grid",
        "action-bar-visual-hierarchy",
        "split-pane-responsive-collapse",
    }
    assert execution.static_review_ready is True
    assert execution.requires_upstream_reentry is False
    assert "native-command-palette" in execution.project_native_reuse


def test_minimal_safe_remains_minimal() -> None:
    context = _context("Fix a typo in the button label.", {"risk_mode": "FAST"})
    execution = enforce_ponytail_fidelity_execution(
        context,
        {
            "project_native_reuse": ["button"],
        },
    )

    assert execution.profile == MINIMAL_SAFE
    assert execution.preserved_compositions == ()
    assert execution.preserved_hierarchies == ()
    assert execution.deviations == ()
    assert execution.static_review_ready is True
    assert execution.requires_upstream_reentry is False
    assert execution.project_native_reuse == ("button",)


def test_project_native_reuse_is_preferred_and_tracked() -> None:
    context = _valid_fidelity_context()
    execution = enforce_ponytail_fidelity_execution(
        context,
        {
            "preserved_compositions": [
                "desktop-macro-grid",
                "action-bar-visual-hierarchy",
                "split-pane-responsive-collapse",
            ],
            "project_native_reuse": ["components/palette/CommandPalette.tsx", "tokens/spacing.json"],
            "deviations": [],
        },
    )
    assert "components/palette/CommandPalette.tsx" in execution.project_native_reuse
    assert "tokens/spacing.json" in execution.project_native_reuse


def test_required_deviations_are_explicitly_recorded() -> None:
    context = _valid_fidelity_context()
    deviation = UIDeviationRecord(
        requirement_or_reference="composition:split-pane-responsive-collapse",
        deviation="Collapse pane at 768px instead of 800px",
        reason="Match established project-native breakpoint system",
        impact="Consistent tablet presentation across application pages",
        evidence="Observed breakpoint tokens in styles/breakpoints.css",
        requires_upstream_reentry=False,
    )

    execution = enforce_ponytail_fidelity_execution(
        context,
        {
            "preserved_compositions": [
                "desktop-macro-grid",
                "action-bar-visual-hierarchy",
            ],
            "deviations": [deviation],
        },
    )

    assert len(execution.deviations) == 1
    assert execution.deviations[0].deviation == "Collapse pane at 768px instead of 800px"
    assert execution.static_review_ready is True
    assert execution.requires_upstream_reentry is False


def test_deviation_with_upstream_reentry_marks_not_static_review_ready() -> None:
    context = _valid_fidelity_context()
    reentry_deviation = UIDeviationRecord(
        requirement_or_reference="pattern:cuir-workspace-split-pane",
        deviation="Cannot render virtualized split pane due to missing platform container query support",
        reason="Runtime platform target lacks container query API",
        impact="Split pane layout requires design re-entry for fallback layout",
        evidence="Browser runtime compatibility test failed",
        requires_upstream_reentry=True,
    )

    execution = enforce_ponytail_fidelity_execution(
        context,
        {
            "preserved_compositions": [
                "desktop-macro-grid",
                "action-bar-visual-hierarchy",
                "split-pane-responsive-collapse",
            ],
            "deviations": [reentry_deviation],
        },
    )

    assert execution.static_review_ready is False
    assert execution.requires_upstream_reentry is True


def test_malformed_deviation_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires non-empty"):
        UIDeviationRecord(
            requirement_or_reference="",
            deviation="Something",
            reason="Reason",
            impact="Impact",
            evidence="Evidence",
            requires_upstream_reentry=False,
        ).validate()

    with pytest.raises(ValueError, match="requires boolean"):
        UIDeviationRecord(
            requirement_or_reference="ref",
            deviation="dev",
            reason="reason",
            impact="impact",
            evidence="evidence",
            requires_upstream_reentry="not-a-bool",  # type: ignore[arg-type]
        ).validate()


def test_ponytail_cannot_self_select_or_downgrade_profile() -> None:
    context = _valid_fidelity_context()

    # Self-selection in payload
    with pytest.raises(ValueError, match="cannot select or self-assign"):
        enforce_ponytail_fidelity_execution(context, {"selected_by": "ponytail"})

    # Downgrade attempt from UI_CONTRACT_FIDELITY to MINIMAL_SAFE
    with pytest.raises(ValueError, match="cannot downgrade UI_CONTRACT_FIDELITY to MINIMAL_SAFE"):
        enforce_ponytail_fidelity_execution(context, {"profile": MINIMAL_SAFE})

    # Self-selection from MINIMAL_SAFE to UI_CONTRACT_FIDELITY
    minimal_ctx = _context("Fix a button label.")
    with pytest.raises(ValueError, match="cannot self-select UI_CONTRACT_FIDELITY"):
        enforce_ponytail_fidelity_execution(minimal_ctx, {"profile": UI_CONTRACT_FIDELITY})


def test_complex_composition_cannot_be_replaced_for_code_size_reduction() -> None:
    context = _valid_fidelity_context()
    with pytest.raises(ValueError, match="cannot be replaced with a simpler composition solely for code-size reduction"):
        enforce_ponytail_fidelity_execution(
            context,
            {
                "preserved_compositions": ["desktop-macro-grid"],
                "simplified_composition_for_code_size": True,
            },
        )


def test_omitted_required_composition_without_deviation_fails_closed() -> None:
    context = _valid_fidelity_context()
    with pytest.raises(ValueError, match="must be preserved or recorded as an authorized deviation"):
        enforce_ponytail_fidelity_execution(
            context,
            {
                "preserved_compositions": ["desktop-macro-grid"],  # Missing action-bar and split-pane
                "deviations": [],
            },
        )


def test_missing_required_fidelity_evidence_fails_closed() -> None:
    context = {
        "ui_implementation_profile": UI_CONTRACT_FIDELITY,
        "ui_fidelity_context": {
            "design_contract_ref": "ref",
            "cloak_handoff_ref": "ref",
            "clockwork_boundary_ref": "ref",
            "pattern_refs": [{"pattern_id": "p1"}],
            # missing composition_refs
            "required_fidelity": {"preserve_macro_composition": True},
        },
    }
    with pytest.raises(ValueError, match="missing required fidelity evidence"):
        enforce_ponytail_fidelity_execution(context, {})



def test_ponytail_cannot_invent_unresolved_design_requirements() -> None:
    context = _valid_fidelity_context()
    with pytest.raises(ValueError, match="cannot invent unresolved design requirements"):
        enforce_ponytail_fidelity_execution(
            context,
            {
                "preserved_compositions": [
                    "desktop-macro-grid",
                    "action-bar-visual-hierarchy",
                    "split-pane-responsive-collapse",
                ],
                "invented_design_requirements": ["invented sidebar accordion behavior"],
            },
        )


def test_generic_execution_mode_cannot_be_contaminated() -> None:
    context = _valid_fidelity_context()

    # Contaminated execution_mode in execution payload
    with pytest.raises(ValueError, match="Generic execution_mode cannot be contaminated"):
        enforce_ponytail_fidelity_execution(context, {"execution_mode": UI_CONTRACT_FIDELITY})

    # Contaminated execution_mode in context metadata
    contaminated_ctx = _context("Implement UI.", {"execution_mode": UI_CONTRACT_FIDELITY})
    with pytest.raises(ValueError, match="Generic execution_mode cannot be contaminated"):
        enforce_ponytail_fidelity_execution(contaminated_ctx, {})

    # Contaminated profile value in execution payload
    with pytest.raises(ValueError, match="Generic execution_mode cannot be contaminated"):
        enforce_ponytail_fidelity_execution(context, {"profile": "HOST_NATIVE"})


def test_uief3_cannot_create_uifidelity_handoff_or_start_uief4() -> None:
    context = _valid_fidelity_context()

    with pytest.raises(ValueError, match="cannot create UIFidelityHandoff or initiate UIEF-4"):
        enforce_ponytail_fidelity_execution(context, {"creates_uifidelity_handoff": True})

    with pytest.raises(ValueError, match="cannot create UIFidelityHandoff or initiate UIEF-4"):
        enforce_ponytail_fidelity_execution(context, {"ui_fidelity_handoff": {"intent": "unauthorized"}})

    with pytest.raises(ValueError, match="cannot create UIFidelityHandoff or initiate UIEF-4"):
        enforce_ponytail_fidelity_execution(context, {"starts_uief4": True})


def test_motion_implemented_without_design_contract_fails_closed() -> None:
    context = _valid_fidelity_context()
    with pytest.raises(ValueError, match="Motion implemented without explicit design contract requirement"):
        enforce_ponytail_fidelity_execution(
            context,
            {
                "preserved_compositions": [
                    "desktop-macro-grid",
                    "action-bar-visual-hierarchy",
                    "split-pane-responsive-collapse",
                ],
                "motion_implemented": True,
                "motion_required": False,
            },
        )


def test_frozen_historical_ponytail_identity_preserved() -> None:
    manifest_data = json.loads(UIX9_MANIFEST.read_text(encoding="utf-8"))
    ponytail_entries = [
        entry for entry in manifest_data.get("materials", [])
        if entry.get("path") == "skills/ponytail/SKILL.md"
    ]
    assert len(ponytail_entries) == 1, "skills/ponytail/SKILL.md must be registered in uix9 manifest"
    expected_digest = ponytail_entries[0]["canonical_blob_digest"]
    skill_content = SKILL_MD.read_bytes().replace(b"\r\n", b"\n")
    actual_digest = hashlib.sha256(skill_content).hexdigest()
    assert actual_digest == expected_digest, (
        f"skills/ponytail/SKILL.md was modified! Expected digest {expected_digest} but found {actual_digest}"
    )


def test_codex_parity_mirrors_exist_and_byte_identical() -> None:
    assert GUIDE_SOURCE.exists(), "skills/ponytail/FRONTEND_FIDELITY_EXECUTION_GUIDE.md must exist"
    assert GUIDE_CODEX.exists(), "adapters/codex/skills/ponytail/FRONTEND_FIDELITY_EXECUTION_GUIDE.md must exist"
    guide_source_bytes = GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    guide_codex_bytes = GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert guide_source_bytes == guide_codex_bytes, "Guide must be byte-identical between skills/ and adapters/"

    assert OUTPUT_FORMATS_SOURCE.exists(), "skills/ponytail/OUTPUT_FORMATS.md must exist"
    assert OUTPUT_FORMATS_CODEX.exists(), "adapters/codex/skills/ponytail/OUTPUT_FORMATS.md must exist"
    out_source_bytes = OUTPUT_FORMATS_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    out_codex_bytes = OUTPUT_FORMATS_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert out_source_bytes == out_codex_bytes, "OUTPUT_FORMATS.md must be byte-identical between skills/ and adapters/"
    assert "FRONTEND_FIDELITY_EXECUTION" in OUTPUT_FORMATS_SOURCE.read_text(encoding="utf-8")
