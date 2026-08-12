from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PACKS = {
    "the-steward": [
        "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md",
        "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md",
        "examples/governed-change-review-example.md",
    ],
    "the-governor": [
        "AUTHORITATIVE_SOURCE_VERIFICATION_GUIDE.md",
        "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
        "examples/governed-change-review-example.md",
    ],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required SK9 governance knowledge markers: {missing}")


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
            if source_file.read_bytes() != codex_file.read_bytes():
                raise AssertionError(f"{slug} source/Codex support parity failed: {relative}")
            mirrored += 1

    steward_skill = read(ROOT / "skills" / "the-steward" / "SKILL.md")
    require(
        steward_skill,
        "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md",
        "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md",
        "examples/governed-change-review-example.md",
    )

    traceability = read(ROOT / "skills" / "the-steward" / "REQUIREMENTS_TRACEABILITY_ACCEPTANCE_GUIDE.md")
    require(traceability, "Bidirectional traceability", "ORPHAN_CHANGE", "STALE_EVIDENCE", "superseding record")

    change_control = read(ROOT / "skills" / "the-steward" / "SCOPE_CHANGE_CONTROL_SDLC_GUIDE.md")
    require(change_control, "IN_SCOPE_CORRECTION", "SCOPE_CHANGE", "POLICY_CHANGE", "A tracker entry is evidence of state, not authority")

    governor_skill = read(ROOT / "skills" / "the-governor" / "SKILL.md")
    require(
        governor_skill,
        "AUTHORITATIVE_SOURCE_VERIFICATION_GUIDE.md",
        "LICENSE_PRIVACY_IP_COMPLIANCE_GUIDE.md",
        "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md",
        "examples/governed-change-review-example.md",
    )

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
