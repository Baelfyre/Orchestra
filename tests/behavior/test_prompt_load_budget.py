import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_prompt_load_budget.py"


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


def write_baseline(
    repo_root: Path,
    approved_tokens=2,
    revision=5,
    maximum=10,
    previous=None,
    approval="BOOTSTRAP_PENDING",
    growth=0,
):
    payload = {
        "measurement_method": "utf8_chars_div_4",
        "packages": {
            "demo": {
                "package_name": "Demo",
                "file_list": ["skills/demo/SKILL.md"],
                "approved_baseline_tokens": approved_tokens,
                "revision_percentage": revision,
                "maximum_percentage": maximum,
                "measurement_method": "utf8_chars_div_4",
                "approval_date": "2026-07-12",
                "approved_reference": "Issue #171 bootstrap baseline",
                "change_rationale": "Issue #171 recalibration baseline bootstrap",
                "decision_log_reference": "Issue #171 bootstrap",
                "maintainer_approval": approval,
                "baseline_change": {
                    "previous_baseline_tokens": previous,
                    "new_baseline_tokens": approved_tokens,
                    "growth_percentage": growth,
                    "reason": "Issue #171 recalibration baseline bootstrap" if previous is None else "Approved baseline increase",
                    "alternatives_considered": "Keep advisory checker only",
                    "maintainer_approval": approval,
                    "decision_log_reference": "Issue #171 bootstrap"
                }
            }
        }
    }
    path = repo_root / "docs/performance/PROMPT_LOAD_BASELINE.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_repo(chars: int, approved_tokens=2, revision=5, maximum=10, **baseline_options):
    temp = tempfile.TemporaryDirectory(prefix="prompt-load-budget-test-")
    repo_root = Path(temp.name)
    skill = repo_root / "skills/demo/SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("x" * chars, encoding="utf-8")
    write_baseline(
        repo_root,
        approved_tokens=approved_tokens,
        revision=revision,
        maximum=maximum,
        **baseline_options,
    )
    return temp, repo_root


def test_real_repo_passes():
    result = run_validator(ROOT)
    assert_true("real repo pass", result.returncode == 0)


def test_missing_baseline_fails_config():
    temp = tempfile.TemporaryDirectory(prefix="prompt-load-missing-")
    try:
        result = run_validator(Path(temp.name))
        assert_true("missing baseline config fail", result.returncode == 2 and "CONFIGURATION_ERROR" in result.stdout)
    finally:
        temp.cleanup()


def test_malformed_json_fails_config():
    temp, repo_root = make_repo(chars=8)
    try:
        (repo_root / "docs/performance/PROMPT_LOAD_BASELINE.json").write_text("{", encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("malformed JSON", result.returncode == 2 and "invalid PROMPT_LOAD_BASELINE.json" in result.stdout)
    finally:
        temp.cleanup()


def test_missing_package_file_fails_config():
    temp, repo_root = make_repo(chars=8)
    try:
        (repo_root / "skills/demo/SKILL.md").unlink()
        result = run_validator(repo_root)
        assert_true("missing package file", result.returncode == 2 and "missing file skills/demo/SKILL.md" in result.stdout)
    finally:
        temp.cleanup()


def test_threshold_order_fails_config():
    temp, repo_root = make_repo(chars=8, approved_tokens=2, revision=10, maximum=5)
    try:
        result = run_validator(repo_root)
        assert_true("threshold order fail", result.returncode == 2 and "maximum_percentage must be >=" in result.stdout)
    finally:
        temp.cleanup()


def test_exact_revision_threshold_equality_passes():
    temp, repo_root = make_repo(chars=420, approved_tokens=100, revision=5, maximum=10)
    try:
        result = run_validator(repo_root)
        assert_true("exact revision equality", result.returncode == 0 and "tokens=105" in result.stdout)
    finally:
        temp.cleanup()


def test_one_token_above_revision_threshold_requires_revision():
    temp, repo_root = make_repo(chars=424, approved_tokens=100, revision=5, maximum=10)
    try:
        result = run_validator(repo_root)
        assert_true("one above revision", result.returncode == 1 and "REVISION_REQUIRED" in result.stdout and "tokens=106" in result.stdout)
    finally:
        temp.cleanup()


def test_exact_maximum_threshold_equality_requires_revision_only():
    temp, repo_root = make_repo(chars=440, approved_tokens=100, revision=5, maximum=10)
    try:
        result = run_validator(repo_root)
        assert_true("exact maximum equality", result.returncode == 1 and "REVISION_REQUIRED" in result.stdout and "tokens=110" in result.stdout)
    finally:
        temp.cleanup()


def test_one_token_above_maximum_threshold_blocks():
    temp, repo_root = make_repo(chars=444, approved_tokens=100, revision=5, maximum=10)
    try:
        result = run_validator(repo_root)
        assert_true("one above maximum", result.returncode == 1 and "BLOCKED" in result.stdout and "tokens=111" in result.stdout)
    finally:
        temp.cleanup()


def test_invalid_approval_fails_config():
    temp, repo_root = make_repo(chars=8, approval="looks good")
    try:
        result = run_validator(repo_root)
        assert_true("invalid approval", result.returncode == 2 and "maintainer_approval must be one of" in result.stdout)
    finally:
        temp.cleanup()


def test_pending_non_bootstrap_increase_fails_config():
    temp, repo_root = make_repo(chars=400, approved_tokens=100, previous=90, approval="BOOTSTRAP_PENDING", growth=11.11)
    try:
        result = run_validator(repo_root)
        assert_true("pending non-bootstrap", result.returncode == 2 and "allowed only" in result.stdout)
    finally:
        temp.cleanup()


def test_approved_increase_passes():
    temp, repo_root = make_repo(chars=400, approved_tokens=100, previous=90, approval="APPROVED", growth=11.11)
    try:
        result = run_validator(repo_root)
        assert_true("approved increase", result.returncode == 0 and "[PASS]" in result.stdout)
    finally:
        temp.cleanup()


def test_incorrect_growth_percentage_fails_config():
    temp, repo_root = make_repo(chars=400, approved_tokens=100, previous=90, approval="APPROVED", growth=10)
    try:
        result = run_validator(repo_root)
        assert_true("incorrect growth", result.returncode == 2 and "growth_percentage must equal 11.11" in result.stdout)
    finally:
        temp.cleanup()


def main():
    test_real_repo_passes()
    test_missing_baseline_fails_config()
    test_malformed_json_fails_config()
    test_missing_package_file_fails_config()
    test_threshold_order_fails_config()
    test_exact_revision_threshold_equality_passes()
    test_one_token_above_revision_threshold_requires_revision()
    test_exact_maximum_threshold_equality_requires_revision_only()
    test_one_token_above_maximum_threshold_blocks()
    test_invalid_approval_fails_config()
    test_pending_non_bootstrap_increase_fails_config()
    test_approved_increase_passes()
    test_incorrect_growth_percentage_fails_config()
    print("Prompt-load budget tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
