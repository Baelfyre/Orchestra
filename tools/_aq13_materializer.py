#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Temporary self-retiring AQ13 repository-wiring materializer."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "2fc2d9ce9fc263813981e4dc8c88d1e4f604f036"
BRANCH = "feat/aq13-staged-rollout-evaluation-20260911"
HELPERS = (
    ROOT / "tools/_aq13_materializer.py",
    ROOT / ".github/workflows/_aq13-materialize.yml",
)
EXACT = {
    "CHANGELOG.md",
    "README.json",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md",
    "machine/adaptive/aq13-staged-rollout-evaluation.v1.json",
    "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json",
    "orchestra_runtime/domain/adaptive/staged_rollout.py",
    "scripts/validation/validate_aq13.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq13.py",
}


def run(*args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True, env=env)


def out(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def main() -> None:
    if out("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("unexpected AQ13 materializer branch")
    run("git", "merge-base", "--is-ancestor", BASE, "HEAD")
    run("git", "config", "user.name", "JEO")
    run("git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com")

    readme_path = ROOT / "README.json"
    readme = json.loads(readme_path.read_text(encoding="utf-8"))
    contracts = readme["machine_contracts"]
    contracts.update({
        "adaptive_assurance_aq13_contract": "machine/adaptive/aq13-staged-rollout-evaluation.v1.json",
        "adaptive_assurance_aq13_schema": "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json",
        "adaptive_assurance_aq13_runtime": "orchestra_runtime/domain/adaptive/staged_rollout.py",
        "adaptive_assurance_aq13_validator": "scripts/validation/validate_aq13.py",
        "adaptive_assurance_aq13_validation": "tests/runtime/test_adaptive_assurance_aq13.py",
        "adaptive_assurance_aq13_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md",
    })
    readme_path.write_text(json.dumps(readme, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    runner_path = ROOT / "tests/behavior/run_tests.py"
    runner = runner_path.read_text(encoding="utf-8")
    aq12 = '        {"Name": "validate_aq12.py", "Path": "scripts/validation/validate_aq12.py"},\n'
    aq13 = '        {"Name": "validate_aq13.py", "Path": "scripts/validation/validate_aq13.py"},\n'
    if aq13 not in runner:
        if aq12 not in runner:
            raise RuntimeError("AQ12 behavior registration anchor missing")
        runner = runner.replace(aq12, aq12 + aq13, 1)
    runner_path.write_text(runner, encoding="utf-8")

    test_path = ROOT / "tests/runtime/test_adaptive_assurance_aq13.py"
    test_text = test_path.read_text(encoding="utf-8")
    test_text = test_text.replace('repository="Baelfyre/Orchestra\\n"', 'repository="Baelfyre/\\nOrchestra"')
    test_path.write_text(test_text, encoding="utf-8")

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    heading = "## Unreleased ADAPT-QA AQ-13 staged non-production rollout evaluation"
    if heading not in changelog:
        entry = """## Unreleased ADAPT-QA AQ-13 staged non-production rollout evaluation

- Adds deterministic evidence-only staged evaluation across SHADOW, CANARY, LIMITED, and EXPANDED non-production evidence stages.
- Makes any critical violation or excessive aggregate regression force revision, while explicit rollback signals force HOLD and insufficient/non-independent/non-deterministic evidence cannot PASS.
- Preserves the Prime Directive, human-owned phase registry, Arbiter transition ownership, existing assurance thresholds, and CritiQual CUD10 hold.
- Makes AQ13 PASS explicitly non-authorizing for production, release/deployment, providers, telemetry, protected policy, whitelist mutation, lifecycle transition, or CUD10 admission.

"""
        changelog_path.write_text(entry + changelog, encoding="utf-8")

    for helper in HELPERS:
        if helper.exists():
            helper.unlink()

    run("git", "add", "-A")
    run("git", "commit", "-m", "feat(aq13): implement staged rollout evaluation")

    run("python", "-B", "scripts/validation/validate_aq13.py")
    run("python", "-B", "-m", "unittest", "tests.runtime.test_adaptive_assurance_aq13")
    run("git", "diff", "--check", BASE)
    changed = {line for line in out("git", "diff", "--name-only", BASE, "HEAD").splitlines() if line}
    if changed != EXACT:
        raise RuntimeError(f"AQ13 exact registered scope mismatch: {sorted(changed)}")
    for helper in HELPERS:
        rel = helper.relative_to(ROOT).as_posix()
        if rel in changed or helper.exists():
            raise RuntimeError(f"temporary AQ13 helper residue: {rel}")
    print("AQ13_BOOTSTRAP_VALIDATION=PASS")
    print("AQ13_CHANGED_PATHS=" + json.dumps(sorted(changed)))
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
