import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_routing_contract.py"
FIXTURES = ROOT / "tests" / "behavior" / "router-contract-fixtures.json"


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
    temp = tempfile.TemporaryDirectory(prefix="routing-contract-test-")
    repo_root = Path(temp.name)
    for relative in (
        Path("plugin.json"),
        Path("SKILL_INDEX.md"),
        Path("ROUTING_MAP.md"),
        Path("tests/behavior/router-contract-fixtures.json"),
    ):
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    return temp, repo_root


def test_passes_real_repo():
    result = run_validator(ROOT)
    assert_true("real repo pass", result.returncode == 0)


def test_missing_required_fixture_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures = [fixture for fixture in fixtures if fixture["id"] != "business-vs-legal-overlap"]
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing fixture fail", result.returncode == 1 and "Missing required routing fixtures" in result.stdout)
    finally:
        temp.cleanup()


def test_protocol_loaded_during_classification_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures[0]["required_context"].append("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("protocol over-hydration fail", result.returncode == 1 and "must not load merely to classify a route" in result.stdout)
    finally:
        temp.cleanup()


def test_obvious_single_owner_conductor_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-clockwork":
                fixture["primary_skill"] = "conductor"
                break
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("obvious single-owner conductor fail", result.returncode == 1 and "obvious single-owner work must not stay with conductor" in result.stdout)
    finally:
        temp.cleanup()


def test_governed_implementation_protocol_context_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "governance-sensitive-implementation-sequence":
                fixture["forbidden_context"].remove("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("governed implementation protocol fail", result.returncode == 1 and "must be forbidden" in result.stdout)
    finally:
        temp.cleanup()


def test_direct_dagger_authorization_contradiction_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-dagger":
                fixture["request"] = "Run guarded chaos after explicit approval."
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("direct dagger contradiction fail", result.returncode == 1 and "must not claim approval" in result.stdout)
    finally:
        temp.cleanup()


def main():
    test_passes_real_repo()
    test_missing_required_fixture_fails()
    test_protocol_loaded_during_classification_fails()
    test_obvious_single_owner_conductor_fails()
    test_governed_implementation_protocol_context_fails()
    test_direct_dagger_authorization_contradiction_fails()
    print("Router contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
