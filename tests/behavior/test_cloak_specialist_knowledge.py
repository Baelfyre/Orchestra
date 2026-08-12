from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "cloak"
CODEX = ROOT / "adapters" / "codex" / "skills" / "cloak"

REQUIRED_SUPPORT = [
    "ACCESSIBILITY_CHECKLIST.md",
    "CHECKLIST.md",
    "FRONTEND_REVIEW_GUIDE.md",
    "UI_UX_FOUNDATIONS_GUIDE.md",
    "SEMANTIC_HTML_ARIA_KEYBOARD_GUIDE.md",
    "RESPONSIVE_CSS_LAYOUT_GUIDE.md",
    "FORM_FOCUS_VALIDATION_GUIDE.md",
    "DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md",
    "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md",
    "examples/frontend-layout-review-example.md",
    "examples/interaction-flow-review-example.md",
    "examples/navigation-structure-review-example.md",
    "examples/user-flow-review-example.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required Cloak knowledge markers: {missing}")


def main() -> None:
    for relative in REQUIRED_SUPPORT:
        source = SOURCE / relative
        mirror = CODEX / relative
        if not source.is_file():
            raise AssertionError(f"Missing canonical Cloak support file: {relative}")
        if not mirror.is_file():
            raise AssertionError(f"Missing Codex Cloak support file: {relative}")
        if source.read_bytes() != mirror.read_bytes():
            raise AssertionError(f"Cloak source/Codex support parity failed: {relative}")

    semantic = read(SOURCE / "SEMANTIC_HTML_ARIA_KEYBOARD_GUIDE.md")
    require(
        semantic,
        "Native semantics first",
        "aria-labelledby",
        "aria-describedby",
        "aria-expanded",
        "aria-current",
        "aria-invalid",
        "aria-live",
        "Focus management",
        "WAI-ARIA Authoring Practices Guide",
    )

    responsive = read(SOURCE / "RESPONSIVE_CSS_LAYOUT_GUIDE.md")
    require(
        responsive,
        "Flexbox",
        "Grid",
        "Intrinsic sizing literacy",
        "Overflow and clipping",
        "Breakpoints and reflow",
        "Fixed, sticky, and overlay UI",
        "Data-heavy surfaces",
    )

    forms = read(SOURCE / "FORM_FOCUS_VALIDATION_GUIDE.md")
    require(
        forms,
        "Validation timing",
        "aria-invalid",
        "Focus after submission",
        "duplicate submission",
        "Multi-step flows",
        "Sensitive and destructive actions",
    )

    tokens = read(SOURCE / "DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md")
    require(
        tokens,
        "Primitive tokens",
        "Semantic tokens",
        "Theme parity",
        "focus-visible",
        "disabled",
        "read-only",
        "loading",
        "Variant discipline",
    )

    routing = read(SOURCE / "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md")
    require(
        routing,
        "Route experience contract",
        "deep-link",
        "Back and Forward",
        "Component boundary literacy",
        "Permission-aware UX",
        "Clockwork",
        "Cipher",
    )

    skill = read(SOURCE / "SKILL.md")
    for filename in [
        "SEMANTIC_HTML_ARIA_KEYBOARD_GUIDE.md",
        "RESPONSIVE_CSS_LAYOUT_GUIDE.md",
        "FORM_FOCUS_VALIDATION_GUIDE.md",
        "DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md",
        "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md",
    ]:
        if filename not in skill:
            raise AssertionError(f"Cloak progressive disclosure does not reference {filename}")

    for example in [
        "frontend-layout-review-example.md",
        "interaction-flow-review-example.md",
        "navigation-structure-review-example.md",
        "user-flow-review-example.md",
    ]:
        text = read(SOURCE / "examples" / example)
        if len(text) < 1500:
            raise AssertionError(f"Worked example is still too shallow: {example}")
        require(text, "## Scope Reviewed", "## Confirmed Findings", "## Recommendations", "## Handoff", "## Missing Evidence")

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK4 audit selected Markdown-only depth; unexpected Cloak patterns directory was added")

    print(f"Cloak specialist knowledge regression passed for {len(REQUIRED_SUPPORT)} mirrored support files.")


if __name__ == "__main__":
    main()