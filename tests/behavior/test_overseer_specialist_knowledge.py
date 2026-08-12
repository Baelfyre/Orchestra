from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "overseer"
CODEX = ROOT / "adapters" / "codex" / "skills" / "overseer"

REQUIRED_SUPPORT = [
    "OUTPUT_FORMATS.md",
    "QA_REVIEW_GUIDE.md",
    "QUALITY_STANDARDS.md",
    "RELEASE_READINESS_TEMPLATES.md",
    "TESTING_CHECKLIST.md",
    "USER_TESTING_FOUNDATIONS_GUIDE.md",
    "TEST_LEVEL_CONTRACT_GUIDE.md",
    "PROPERTY_MUTATION_COVERAGE_GUIDE.md",
    "FLAKY_ISOLATION_TEST_DATA_GUIDE.md",
    "CI_BROWSER_PERFORMANCE_MATRIX_GUIDE.md",
    "examples/defect-triage-example.md",
    "examples/regression-readiness-example.md",
    "examples/release-readiness-example.md",
    "examples/test-case-audit-example.md",
    "examples/test-plan-review-example.md",
    "examples/risk-based-validation-matrix-example.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required Overseer knowledge markers: {missing}")


def main() -> None:
    for relative in REQUIRED_SUPPORT:
        source = SOURCE / relative
        mirror = CODEX / relative
        if not source.is_file():
            raise AssertionError(f"Missing canonical Overseer support file: {relative}")
        if not mirror.is_file():
            raise AssertionError(f"Missing Codex Overseer support file: {relative}")
        if source.read_bytes() != mirror.read_bytes():
            raise AssertionError(f"Overseer source/Codex support parity failed: {relative}")

    skill = read(SOURCE / "SKILL.md")
    for filename in [
        "TEST_LEVEL_CONTRACT_GUIDE.md",
        "PROPERTY_MUTATION_COVERAGE_GUIDE.md",
        "FLAKY_ISOLATION_TEST_DATA_GUIDE.md",
        "CI_BROWSER_PERFORMANCE_MATRIX_GUIDE.md",
    ]:
        if filename not in skill:
            raise AssertionError(f"Overseer progressive disclosure does not reference {filename}")
    require(skill, "exact revision, environment", "large matrix as proof")

    levels = read(SOURCE / "TEST_LEVEL_CONTRACT_GUIDE.md")
    require(
        levels,
        "Unit",
        "Integration",
        "Contract",
        "System/E2E",
        "provider and consumer revisions",
        "test doubles",
    )

    advanced = read(SOURCE / "PROPERTY_MUTATION_COVERAGE_GUIDE.md")
    require(
        advanced,
        "generator domain",
        "minimized counterexample",
        "survived mutant",
        "equivalent mutant",
        "branch",
        "High coverage can coexist with weak assertions",
    )

    flaky = read(SOURCE / "FLAKY_ISOLATION_TEST_DATA_GUIDE.md")
    require(
        flaky,
        "first failing attempt",
        "timing-only sleeps",
        "Quarantine Contract",
        "expiry/review date",
        "parallel identifier collisions",
        "Test Data Lifecycle",
    )

    matrix = read(SOURCE / "CI_BROWSER_PERFORMANCE_MATRIX_GUIDE.md")
    require(
        matrix,
        "full Cartesian matrix",
        "skipped/cancelled visibility",
        "browser engines",
        "real-device evidence",
        "percentile latency",
        "generator is not saturated",
    )

    example = read(SOURCE / "examples" / "risk-based-validation-matrix-example.md")
    require(
        example,
        "`PLANNED_UNEXECUTED`",
        "No result below is reported as passed",
        "Risk-Based Validation Matrix",
        "Evidence Identity",
        "Coverage percentage alone cannot close the risk",
    )

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK7 audit selected Markdown-only depth; unexpected Overseer patterns directory was added")

    print(
        "Overseer specialist knowledge regression passed for "
        f"{len(REQUIRED_SUPPORT)} mirrored support files with evidence states preserved."
    )


if __name__ == "__main__":
    main()
