from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "scribe"
CODEX = ROOT / "adapters" / "codex" / "skills" / "scribe"

REQUIRED_SUPPORT = [
    "AUDIT_CHECKLIST.md",
    "DOCUMENTATION_STANDARDS.md",
    "OUTPUT_FORMATS.md",
    "OUTPUT_TEMPLATES.md",
    "SOURCE_BACKED_DOCUMENTATION_GUIDE.md",
    "MARKDOWN_TECHNICAL_SYNTAX_GUIDE.md",
    "CHANGELOG_ADR_GUIDE.md",
    "API_VERSIONED_DOCUMENTATION_GUIDE.md",
    "LINK_CLAIM_VALIDATION_GUIDE.md",
    "examples/final-submission-readiness-example.md",
    "examples/project-documentation-audit-example.md",
    "examples/readme-audit-example.md",
    "examples/system-readiness-doc-example.md",
    "examples/source-backed-api-change-example.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required Scribe knowledge markers: {missing}")


def main() -> None:
    for relative in REQUIRED_SUPPORT:
        source = SOURCE / relative
        mirror = CODEX / relative
        if not source.is_file() or not mirror.is_file():
            raise AssertionError(f"Missing Scribe support or mirror: {relative}")
        if source.read_bytes() != mirror.read_bytes():
            raise AssertionError(f"Scribe source/Codex support parity failed: {relative}")

    skill = read(SOURCE / "SKILL.md")
    for filename in [
        "MARKDOWN_TECHNICAL_SYNTAX_GUIDE.md",
        "CHANGELOG_ADR_GUIDE.md",
        "API_VERSIONED_DOCUMENTATION_GUIDE.md",
        "LINK_CLAIM_VALIDATION_GUIDE.md",
    ]:
        if filename not in skill:
            raise AssertionError(f"Scribe progressive disclosure misses {filename}")
    require(skill, "source revision and last-verified date", "generated heading anchors")

    markdown = read(SOURCE / "MARKDOWN_TECHNICAL_SYNTAX_GUIDE.md")
    require(markdown, "CommonMark", "GitHub-Flavored Markdown", "Heading fragments", "language identifier", "alternative text")

    decisions = read(SOURCE / "CHANGELOG_ADR_GUIDE.md")
    require(decisions, "Unreleased", "merged change is not automatically published", "Superseded", "link both directions")

    api = read(SOURCE / "API_VERSIONED_DOCUMENTATION_GUIDE.md")
    require(api, "OpenAPI/AsyncAPI", "error envelope", "supported-previous", "canonical URLs", "sunset/removal date")

    claims = read(SOURCE / "LINK_CLAIM_VALIDATION_GUIDE.md")
    require(claims, "Claim Ledger", "VERIFIED_CURRENT", "fragment/anchor existence", "authoritative sources", "invalidates dependent documentation evidence")

    example = read(SOURCE / "examples" / "source-backed-api-change-example.md")
    require(example, "`DOCUMENTATION_PLANNED`", "Release evidence: `NOT_FOUND`", "must remain under `Unreleased`", "no release or documentation-site publication occurred")

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK8 audit selected Markdown-only depth; unexpected Scribe patterns directory")

    print(f"Scribe specialist knowledge regression passed for {len(REQUIRED_SUPPORT)} mirrored support files without publication.")


if __name__ == "__main__":
    main()
