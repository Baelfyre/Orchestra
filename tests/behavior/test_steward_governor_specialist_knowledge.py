# @codebase_provenance_JEO

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.codex.validate_codex_export import (
    GOVERNOR_PROVENANCE_MARKERS,
    MARKED_SUPPORT_GUIDES,
    NORMALIZED_EXPORT_PARITY_PATHS,
    strip_jeo_support_markers,
)

PACKS = {
    "the-steward": [
        "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md",
        "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md",
        "PRODUCT_INTENT_AND_CAPACITY_ENVELOPE_GUIDE.md",
        "examples/governed-change-review-example.md",
    ],
    "the-governor": [
        "AUTHORITATIVE_SOURCE_VERIFICATION_GUIDE.md",
        "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
        "OUTPUT_FORMATS.md",
        "examples/governed-change-review-example.md",
    ],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required SK9 governance knowledge markers: {missing}")


def test_governor_ai_output_rights_warning_boundary() -> None:
    skill_paths = (
        ROOT / "skills" / "the-governor" / "SKILL.md",
        ROOT / "adapters" / "codex" / "skills" / "the-governor" / "SKILL.md",
    )
    for skill_path in skill_paths:
        skill = read(skill_path)
        review_flag = skill.split("## Human Review Flag", 1)[1].split("## Adaptive Review Path", 1)[0]
        advisory = skill.split("### Narrow AI-output advisory boundary", 1)[1].split("## Adaptive Review Path", 1)[0]
        require(
            skill,
            "Material legal, regulatory, privacy, licensing, or IP uncertainty requiring human authority must be escalated with `human_review_required: true`.",
            "See the [License, Privacy, IP, and Compliance Review Guide](LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md).",
        )
        require(
            review_flag,
            "- public release has compliance implications",
            "Public-release and separate `human_review_required` triggers remain.",
        )
        require(
            advisory,
            "Unparticularized AI-output similarity or incomplete intermediate-generation history may qualify for a scoped `RISKS` warning only under the proportionate-review conditions in the linked License guide.",
            "Public-release and separate `human_review_required` triggers remain.",
        )
        if "human_review_required: false" in review_flag.lower():
            raise AssertionError("The narrow warning must not clear or suppress a human-review flag")

    guide_paths = (
        ROOT / "skills" / "the-governor" / "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        ROOT / "adapters" / "codex" / "skills" / "the-governor" / "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
    )
    for guide_path in guide_paths:
        license_guide = read(guide_path)
        require(
            license_guide,
            "Escalate ambiguous custom licenses, conflicting obligations, and material copyleft or redistribution questions.",
            "when it leaves ownership, permission, or attribution unresolved",
            "inability to reconstruct every intermediate AI-generation step alone is not a material provenance gap",
            "This classification does not clear or displace any separate human-review trigger, including the public-release compliance trigger.",
            "Either unsupported, unparticularized AI-output similarity concerns or inability to reconstruct every intermediate AI-generation step alone may be recorded as a scoped `RISKS` warning only after proportionate review",
            "no concrete conflict or material uncertainty remains",
            "every applicable gate independently passes",
            "no separate `human_review_required` flag is pending",
            "Do not use top-level `ADVISORY_ONLY` for this warning; Covenant maps it to `WAIT_FOR_EVIDENCE`.",
            "A blocking rights/IP finding must record:",
            "affected asset and version, or explicitly `UNKNOWN`",
            "proposed action",
            "applicable control or gate",
            "specific evidence or identified evidence gap",
            "material risk",
            "minimum resolution",
            "Unknown material rights, an open applicable gate, unresolved material facts, or unknown required evidence remain blocking",
            "must not be downgraded to `ADVISORY_ONLY` or a `RISKS`-only warning",
            "A `RISKS` warning is not rights clearance and never satisfies, waives, downgrades, removes, clears, or displaces any gate or separate flag.",
            "Publication remains gated until every required review and approval is complete.",
            "Actual or material conflicts, applicable mandatory clearances, current `human_review_required: true` flags, protected merge/publication approvals, and Steward/Arbiter authority remain unchanged.",
            "only a fresh Governor decision may supersede them.",
        )

    reference = read(ROOT / "docs" / "governance" / "GOVERNOR.md")
    require(reference, "every applicable gate to independently pass", "does not clear or displace the public-release trigger")


def test_governor_marker_support_is_narrow_and_body_is_preserved() -> None:
    governor_guides = {
        (guide[0].as_posix(), guide[1].as_posix())
        for guide in MARKED_SUPPORT_GUIDES
        if guide[0].as_posix().startswith("skills/the-governor/")
    }
    assert governor_guides == {
        ("skills/the-governor/LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md", "the-governor/LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md"),
        ("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md", "the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md"),
        ("skills/the-governor/OUTPUT_FORMATS.md", "the-governor/OUTPUT_FORMATS.md"),
    }
    exporter = read(ROOT / "adapters" / "codex" / "export-codex-skills.ps1")
    dual_markers = exporter.split("$jeoMarkerSupportFiles = @(", 1)[1].split(")", 1)[0]
    provenance_markers = exporter.split("$jeoProvenanceSupportFiles = @(", 1)[1].split(")", 1)[0]
    for relative in (
        "the-governor/LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        "the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
        "the-governor/OUTPUT_FORMATS.md",
    ):
        assert f'"{relative}"' in provenance_markers
        assert relative not in dual_markers
    assert (
        Path("skills/the-governor/OUTPUT_FORMATS.md"),
        Path("adapters/codex/skills/the-governor/OUTPUT_FORMATS.md"),
    ) not in NORMALIZED_EXPORT_PARITY_PATHS

    marker = "<!-- @codebase_provenance_JEO -->\n"
    body = "A marker-like spelling codebase_provenance_JEO without @ stays unchanged.\n"
    assert strip_jeo_support_markers(marker + body, "Governor test", GOVERNOR_PROVENANCE_MARKERS) == body

    for invalid in (
        body + marker,
        marker + body + marker,
        "<!-- @codbase_provenance_JEO -->\n" + body,
    ):
        try:
            strip_jeo_support_markers(invalid, "Governor test", GOVERNOR_PROVENANCE_MARKERS)
        except ValueError:
            continue
        raise AssertionError("Governor marker stripping accepted an unmarked, misplaced, or extra marker")


def main() -> None:
    mirrored = 0
    for slug, support_files in PACKS.items():
        source = ROOT / "skills" / slug
        codex = ROOT / "adapters" / "codex" / "skills" / slug
        for relative in support_files:
            source_file = source / relative
            codex_file = codex / relative
            if not source_file.is_file() or not codex_file.is_file():
                raise AssertionError(f"Missing {slug} support or mirror: {relative}")
            source_content = source_file.read_bytes()
            codex_content = codex_file.read_bytes()
            if slug == "the-governor" and relative in (
                "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
                "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
                "OUTPUT_FORMATS.md",
            ):
                marker = b"<!-- @codebase_provenance_JEO -->"
                if source_content.startswith(marker + b"\r\n"):
                    source_content = source_content[len(marker) + 2:]
                elif source_content.startswith(marker + b"\n"):
                    source_content = source_content[len(marker) + 1:]
                else:
                    raise AssertionError(f"Governor support guide must start with its provenance marker: {relative}")
                if b"@codebase" in source_content:
                    raise AssertionError(f"Governor support source contains an unexpected marker: {relative}")
                if b"@codebase" in codex_content:
                    raise AssertionError(f"Governor support export must omit source provenance markers: {relative}")
                source_content = source_content.replace(b"\r\n", b"\n")
            if source_content != codex_content:
                raise AssertionError(f"{slug} source/Codex support parity failed: {relative}")
            mirrored += 1

    steward_skill = read(ROOT / "skills" / "the-steward" / "SKILL.md")
    require(
        steward_skill,
        "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md",
        "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md",
        "PRODUCT_INTENT_AND_CAPACITY_ENVELOPE_GUIDE.md",
        "examples/governed-change-review-example.md",
    )

    traceability = read(ROOT / "skills" / "the-steward" / "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md")
    require(traceability, "Bidirectional traceability", "ORPHAN_CHANGE", "STALE_EVIDENCE", "superseding record")

    change_control = read(ROOT / "skills" / "the-steward" / "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md")
    require(change_control, "IN_SCOPE_CORRECTION", "SCOPE_CHANGE", "POLICY_CHANGE", "A tracker entry is evidence of state, not authority")

    capacity_guide = read(ROOT / "skills" / "the-steward" / "PRODUCT_INTENT_AND_CAPACITY_ENVELOPE_GUIDE.md")
    require(
        capacity_guide,
        "Problem vs. Requested Solution Decoupling",
        "UNKNOWN IS VALID",
        "To size this without overengineering it",
        "Downstream Handoff to Clockwork",
    )

    governor_skill = read(ROOT / "skills" / "the-governor" / "SKILL.md")
    require(
        governor_skill,
        "AUTHORITATIVE_SOURCE_VERIFICATION_GUIDE.md",
        "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
        "examples/governed-change-review-example.md",
    )
    test_governor_ai_output_rights_warning_boundary()
    test_governor_marker_support_is_narrow_and_body_is_preserved()

    sources = read(ROOT / "skills" / "the-governor" / "AUTHORITATIVE_SOURCE_VERIFICATION_GUIDE.md")
    require(sources, "Source Hierarchy", "effective dates", "APPLICABILITY_UNRESOLVED", "Do not infer jurisdiction")

    review = read(ROOT / "skills" / "the-governor" / "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md")
    require(review, "Scanner labels are leads", "Public availability does not mean unrestricted reuse", "OBLIGATION", "human_review_required: true")

    escalation = read(ROOT / "skills" / "the-governor" / "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    require(escalation, "Escalate a Decision, Not a Topic", "Do not escalate solely", "not release, publication, policy activation")

    steward_example = read(ROOT / "skills" / "the-steward" / "examples" / "governed-change-review-example.md")
    governor_example = read(ROOT / "skills" / "the-governor" / "examples" / "governed-change-review-example.md")
    require(steward_example, "APPROVED_REQUIREMENT_IMPLEMENTATION_UNVERIFIED", "human_review_required: true", "No implementation")
    require(governor_example, "NEEDS_HUMAN_INTERPRETATION", "qualified privacy/legal owner", "No legal conclusion")

    for slug in PACKS:
        patterns = ROOT / "skills" / slug / "patterns"
        if patterns.exists():
            raise AssertionError(f"SK9 audit selected Markdown-only depth; unexpected {slug} patterns directory")

    print(f"Steward/Governor specialist knowledge regression passed for {mirrored} mirrored support files without legal or policy activation.")


if __name__ == "__main__":
    main()
