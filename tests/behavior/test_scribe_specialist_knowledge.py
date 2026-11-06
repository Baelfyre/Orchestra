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
    "ARTIFACT_AUTHORING_AND_BACKEND_SELECTION_GUIDE.md",
    "MARKDOWN_TECHNICAL_SYNTAX_GUIDE.md",
    "CHANGELOG_ADR_GUIDE.md",
    "API_VERSIONED_DOCUMENTATION_GUIDE.md",
    "LINK_CLAIM_VALIDATION_GUIDE.md",
    "DOMAIN_NARRATIVE_MODELING_GUIDE.md",
    "REQUIREMENTS_TRACEABILITY_GUIDE.md",
    "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md",
    "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md",
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
        source_text = read(source)
        if relative == "ARTIFACT_AUTHORING_AND_BACKEND_SELECTION_GUIDE.md":
            marker_header = "<!-- @codebase_provenance_JEO -->\n<!-- @codebase_rights_JEO -->\n"
            if not source_text.startswith(marker_header):
                raise AssertionError("Scribe artifact guide is missing its leading source markers")
            source_text = source_text[len(marker_header):]
        if source_text != read(mirror):
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
    require(
        skill,
        "Documentation, Domain Narrative, and Knowledge Traceability Specialist",
        "SPEC_TO_SYSTEM",
        "SYSTEM_TO_DOCS",
        "RECONCILE",
        "source revision and last-verified date",
        "generated heading anchors",
    )

    domain = read(SOURCE / "DOMAIN_NARRATIVE_MODELING_GUIDE.md")
    require(domain, "Noun extraction is discovery only", "Clockwork", "Chronicler", "Weaver", "UNRESOLVED")

    traceability = read(SOURCE / "REQUIREMENTS_TRACEABILITY_GUIDE.md")
    require(traceability, "Forward trace", "Reverse trace", "MISSING_EVIDENCE", "NOT_APPLICABLE")

    research = read(SOURCE / "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md")
    require(research, "Plan first", "Prototype first", "Existing system", "### Continuous", "Chapter 1-5")

    reconciliation = read(SOURCE / "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md")
    require(reconciliation, "DOC_DRIFT", "IMPLEMENTATION_DRIFT", "observed behavior", "inferred purpose", "historical intent")

    markdown = read(SOURCE / "MARKDOWN_TECHNICAL_SYNTAX_GUIDE.md")
    require(markdown, "CommonMark", "GitHub-Flavored Markdown", "Heading fragments", "language identifier", "alternative text")

    decisions = read(SOURCE / "CHANGELOG_ADR_GUIDE.md")
    require(decisions, "Unreleased", "merged change is not automatically published", "Superseded", "link both directions")

    api = read(SOURCE / "API_VERSIONED_DOCUMENTATION_GUIDE.md")
    require(api, "OpenAPI/AsyncAPI", "error envelope", "supported-previous", "canonical URLs", "sunset/removal date")

    claims = read(SOURCE / "LINK_CLAIM_VALIDATION_GUIDE.md")
    require(claims, "Claim Ledger", "VERIFIED_CURRENT", "fragment/anchor existence", "authoritative sources", "invalidates dependent documentation evidence")

    artifacts = read(SOURCE / "ARTIFACT_AUTHORING_AND_BACKEND_SELECTION_GUIDE.md")
    require(
        artifacts,
        "SUPPORTED",
        "PARTIAL",
        "UNSUPPORTED",
        "UNVERIFIED",
        "Feature support, evidence, and output validation are separate.",
        "Treat as unknown, not supported.",
        "Do not silently drop, flatten, or approximate the requirement.",
        "document outline with section and subsection purpose",
        "workbook and sheet map",
        "narrative/story arc and slide sequence",
        "PowerPoint desktop presentation",
        "PowerPoint for the web presentation",
        "OpenDocument text document",
        "OpenDocument spreadsheet",
        "OpenDocument presentation",
        "intended presentation duration",
        "institution, course, or rubric requirements",
        "Template identity and revision",
        "Document-family structure",
        "story arc from the problem or question through evidence and reasoning to the conclusion",
        "source/input data, formulas or transformations",
        "For every slide, state its purpose, key message, supporting evidence/data",
        "substantive speaker notes",
        "Conversion risks",
        "Validation and confirmation",
        "PDF presentation",
        "Markdown presentation",
        "LaTeX document",
        ".odt",
        ".ods",
        ".odp",
        "local tool availability before comparing backend features",
        "Google account/tenant, authentication or OAuth authorization",
        "Native target format",
        "Qualified interchange format",
        "User-approved fixed format",
        "Excel and Calc calculations and charts",
        "Apache OpenOffice and LibreOffice as separate target products",
        "Apple Keynote",
        "Google's cloud",
        "provider operation",
        "Cloak's artifact visual/accessibility guide",
        "The Governor",
    )

    example = read(SOURCE / "examples" / "source-backed-api-change-example.md")
    require(example, "`DOCUMENTATION_PLANNED`", "Release evidence: `NOT_FOUND`", "must remain under `Unreleased`", "no release or documentation-site publication occurred")

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK8 audit selected Markdown-only depth; unexpected Scribe patterns directory")

    print(f"Scribe specialist knowledge regression passed for {len(REQUIRED_SUPPORT)} mirrored support files without publication.")


if __name__ == "__main__":
    main()
