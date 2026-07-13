import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_governance_protocol_consistency.py"


def run_validator(repo_root: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_true(name, condition):
    if not condition:
        raise AssertionError(name)


def make_repo_copy():
    temp = tempfile.TemporaryDirectory(prefix="governance-protocol-test-")
    repo_root = Path(temp.name)
    for relative in (
        Path("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"),
        Path("docs/governance/GOVERNANCE_LAYER.md"),
        Path("skills/the-steward/SKILL.md"),
        Path("skills/the-steward/OUTPUT_FORMATS.md"),
        Path("skills/the-governor/SKILL.md"),
        Path("skills/the-governor/OUTPUT_FORMATS.md"),
    ):
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    return temp, repo_root


def test_passes_real_repo():
    result = run_validator(ROOT)
    assert_true("real repo pass", result.returncode == 0)


def test_missing_protocol_fails():
    temp, repo_root = make_repo_copy()
    try:
        (repo_root / "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md").unlink()
        result = run_validator(repo_root)
        assert_true("missing protocol fail", result.returncode == 1)
    finally:
        temp.cleanup()


def test_duplicate_heading_in_layer_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_LAYER.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## Decision Model\n", encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("duplicate heading fail", result.returncode == 1 and "stale duplicated content" in result.stdout)
    finally:
        temp.cleanup()


def test_missing_decision_meaning_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"
        content = path.read_text(encoding="utf-8")
        path.write_text(content.replace("Required governance review passed", "Meaning removed"), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing decision meaning fail", result.returncode == 1 and "APPROVED" in result.stdout)
    finally:
        temp.cleanup()


def test_missing_unique_layer_section_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_LAYER.md"
        content = path.read_text(encoding="utf-8")
        start = content.index("### Trigger Mapping Guide")
        end = content.index("### Typical Profiles")
        path.write_text(content[:start] + content[end:], encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing unique layer section fail", result.returncode == 1 and "Trigger Mapping Guide" in result.stdout)
    finally:
        temp.cleanup()


def test_missing_governor_field_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "skills/the-governor/OUTPUT_FORMATS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("HUMAN_REVIEW_REQUIRED", "REMOVED_FIELD"), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing governor field fail", result.returncode == 1 and "HUMAN_REVIEW_REQUIRED" in result.stdout)
    finally:
        temp.cleanup()


def main():
    test_passes_real_repo()
    test_missing_protocol_fails()
    test_duplicate_heading_in_layer_fails()
    test_missing_decision_meaning_fails()
    test_missing_unique_layer_section_fails()
    test_missing_governor_field_fails()
    print("Governance protocol consistency tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
