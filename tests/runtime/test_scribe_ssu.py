from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SCRIBE = ROOT / "skills" / "scribe"
CODEX_SCRIBE = ROOT / "adapters" / "codex" / "skills" / "scribe"

GUIDES = (
    "DOMAIN_NARRATIVE_MODELING_GUIDE.md",
    "REQUIREMENTS_TRACEABILITY_GUIDE.md",
    "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md",
    "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md",
)
EXAMPLES = (
    "spec-to-system-example.md",
    "system-to-docs-research-example.md",
    "reconcile-documentation-drift-example.md",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def body_without_frontmatter(text: str) -> str:
    match = re.match(r"(?s)^---\r?\n.*?\r?\n---\r?\n?", text)
    return text[match.end() :].strip() if match else text.strip()


def test_scribe_skill_exposes_ssu_progressive_disclosure_and_modes():
    text = read(SCRIBE / "SKILL.md")

    for guide in GUIDES:
        assert f"]({guide})" in text
    for mode in ("SPEC_TO_SYSTEM", "SYSTEM_TO_DOCS", "RECONCILE"):
        assert mode in text

    assert "Domain narrative" in text
    assert "research/capstone" in text
    assert "documentation-system reconciliation" in text
    assert "must not automatically convert nouns into classes" in text
    for owner in ("Clockwork", "Chronicler", "Weaver", "Overseer", "Cipher", "Cloak"):
        assert owner in text


def test_new_scribe_guides_have_exact_codex_portable_mirrors():
    for guide in GUIDES:
        source = SCRIBE / guide
        exported = CODEX_SCRIBE / guide
        assert source.is_file(), guide
        assert exported.is_file(), guide
        assert read(source) == read(exported), guide


def test_changed_scribe_support_files_have_exact_codex_mirrors():
    for name in ("OUTPUT_TEMPLATES.md", "AUDIT_CHECKLIST.md"):
        assert read(SCRIBE / name) == read(CODEX_SCRIBE / name), name


def test_codex_scribe_skill_preserves_normalized_body_and_simple_frontmatter():
    source = read(SCRIBE / "SKILL.md")
    exported = read(CODEX_SCRIBE / "SKILL.md")

    frontmatter = re.match(r"(?s)^---\r?\n(.*?)\r?\n---", exported)
    assert frontmatter is not None
    lines = [line for line in frontmatter.group(1).splitlines() if line.strip()]
    assert lines == [
        "name: scribe",
        "description: Documentation and Knowledge Transfer Specialist. See SKILL_INDEX.md.",
    ]
    assert body_without_frontmatter(source) == body_without_frontmatter(exported)


def test_ssu_examples_cover_all_documentation_directions_and_are_portable():
    expected_markers = {
        "spec-to-system-example.md": ("SPEC_TO_SYSTEM", "Domain Narrative", "MISSING_EVIDENCE"),
        "system-to-docs-research-example.md": ("SYSTEM_TO_DOCS", "IMPLEMENTED", "empirical"),
        "reconcile-documentation-drift-example.md": ("RECONCILE", "DOC_DRIFT", "IMPLEMENTATION_DRIFT"),
    }

    for name in EXAMPLES:
        source = SCRIBE / "examples" / name
        exported = CODEX_SCRIBE / "examples" / name
        assert source.is_file(), name
        assert exported.is_file(), name
        text = read(source)
        assert text == read(exported), name
        for marker in expected_markers[name]:
            assert marker in text, (name, marker)


def test_research_guide_preserves_institutional_authority_and_evidence_ceiling():
    text = read(SCRIBE / "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md")
    assert "Those requirements are authoritative for the submission" in text
    assert "Do not hardcode one institution's Chapter 1 to Chapter 5 structure" in text
    assert "Do not write results, discussion, or conclusions before corresponding evidence exists" in text
    assert "Never transform `IMPLEMENTED` into `VALIDATED`" in text


def test_reconciliation_guide_distinguishes_documentation_and_implementation_drift():
    text = read(SCRIBE / "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md")
    for marker in (
        "DOC_DRIFT",
        "IMPLEMENTATION_DRIFT",
        "MISSING_EVIDENCE",
        "MISSING_DOCUMENTATION",
        "UNDOCUMENTED_IMPLEMENTATION",
        "ORPHANED_REQUIREMENT",
        "VALIDATION_GAP",
        "STALE_OR_UNSUPPORTED_RESEARCH_CLAIM",
    ):
        assert marker in text


def test_routing_map_recognizes_scribe_lifecycle_documentation_without_expanding_authority():
    source = read(ROOT / "ROUTING_MAP.md")
    exported = read(ROOT / "adapters" / "codex" / "skills" / "conductor" / "ROUTING_MAP.md")

    for text in (source, exported):
        assert "## Scribe Lifecycle Documentation Routing" in text
        assert "SPEC_TO_SYSTEM" in text
        assert "SYSTEM_TO_DOCS" in text
        assert "RECONCILE" in text
        assert "Documentation routing does not make Scribe the authority" in text
        assert "Formal UML/model decisions route to Weaver" in text
        assert "architecture decisions to Clockwork" in text
        assert "persistence/entity-storage decisions to Chronicler" in text
