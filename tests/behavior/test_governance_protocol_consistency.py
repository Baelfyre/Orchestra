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
        Path("docs/governance/GOVERNANCE_REVIEW_FLOW.md"),
        Path("docs/governance/DELEGATED_EXECUTION_POLICY.md"),
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


# Phase A: Delegated execution policy tests

def test_phase_a_passes_real_repo():
    """Positive: real repo passes all Phase A delegated execution policy checks."""
    result = run_validator(ROOT)
    assert_true("phase-a real repo pass", result.returncode == 0)


def test_missing_delegated_policy_fails():
    """Negative: validator fails when DELEGATED_EXECUTION_POLICY.md is absent."""
    temp, repo_root = make_repo_copy()
    try:
        (repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md").unlink()
        result = run_validator(repo_root)
        assert_true(
            "missing delegated policy fail",
            result.returncode == 1 and "DELEGATED_EXECUTION_POLICY.md: file does not exist" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_missing_transition_disposition_fails():
    """Negative: validator fails when a transition disposition is removed from the policy."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("`AUTO_REMEDIATE_AND_REVALIDATE`", "REMOVED_DISPOSITION"),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "missing transition disposition fail",
            result.returncode == 1 and "AUTO_REMEDIATE_AND_REVALIDATE" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_changed_legacy_governance_decision_meaning_fails():
    """Negative: validator fails when an existing governance decision meaning is altered."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "`BLOCKED`: Work cannot proceed through the governed transition until the blocking condition is resolved and reviewed again.",
                "`BLOCKED`: Work is always allowed to proceed.",
            ),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "changed legacy decision meaning fail",
            result.returncode == 1 and "BLOCKED" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_missing_remediation_limit_fails():
    """Negative: validator fails when the remediation limit fields are absent from the policy."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("maximum_remediation_attempts_per_unit", "REMOVED_LIMIT"),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "missing remediation limit fail",
            result.returncode == 1 and "maximum_remediation_attempts_per_unit" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_missing_external_action_default_deny_fails():
    """Negative: validator fails when the external-action default-deny statement is absent."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("default-deny", "REMOVED_DENY"),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "missing external-action default-deny fail",
            result.returncode == 1 and "default-deny" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_missing_capacity_handoff_requirement_fails():
    """Negative: validator fails when the capacity-wait resumable-lifecycle-state statement is absent."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "`WAIT_FOR_CAPACITY` is a resumable lifecycle state",
                "REMOVED_CAPACITY_HANDOFF",
            ),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "missing capacity handoff requirement fail",
            result.returncode == 1 and "WAIT_FOR_CAPACITY" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_false_runtime_active_claim_fails():
    """Negative: validator fails when the policy falsely claims Phase B/runtime enforcement is active."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md"
        content = path.read_text(encoding="utf-8")
        path.write_text(
            content + "\nContinuous automatic progression is now active.\n",
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "false runtime active claim fail",
            result.returncode == 1 and "Continuous automatic progression is now active" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_protocol_missing_delegated_section_fails():
    """Negative: validator fails when GOVERNANCE_DECISION_PROTOCOL.md lacks the delegated section."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "## Delegated Execution Transition Dispositions",
                "## REMOVED_SECTION",
            ),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "protocol missing delegated section fail",
            result.returncode == 1 and "Delegated Execution Transition Dispositions" in result.stdout,
        )
    finally:
        temp.cleanup()


def test_unknown_transition_not_auto_continue():
    """Negative: validator fails when the fail-closed rule is removed from the protocol."""
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("### Fail-Closed Rule", "### REMOVED_RULE"),
            encoding="utf-8",
        )
        result = run_validator(repo_root)
        assert_true(
            "unknown transition not auto-continue fail",
            result.returncode == 1 and "Fail-Closed Rule" in result.stdout,
        )
    finally:
        temp.cleanup()


def main():
    test_passes_real_repo()
    test_missing_protocol_fails()
    test_duplicate_heading_in_layer_fails()
    test_missing_decision_meaning_fails()
    test_missing_unique_layer_section_fails()
    test_missing_governor_field_fails()
    # Phase A tests
    test_phase_a_passes_real_repo()
    test_missing_delegated_policy_fails()
    test_missing_transition_disposition_fails()
    test_changed_legacy_governance_decision_meaning_fails()
    test_missing_remediation_limit_fails()
    test_missing_external_action_default_deny_fails()
    test_missing_capacity_handoff_requirement_fails()
    test_false_runtime_active_claim_fails()
    test_protocol_missing_delegated_section_fails()
    test_unknown_transition_not_auto_continue()
    print("Governance protocol consistency tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
