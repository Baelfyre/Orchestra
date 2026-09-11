#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Temporary self-retiring AQ14 wiring and targeted-validation helper."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "34eb2a38a97f6d1acef6bbd206da8795393457de"
BRANCH = "feat/aq14-final-effectiveness-qualification-20260911"
HELPERS = [ROOT / "tools/_aq14_materialize.py", ROOT / ".github/workflows/_aq14-materialize.yml"]
DIAGNOSTIC_LOG = ROOT / "aq14-materialize.log"
EXACT_PATHS = {
    "CHANGELOG.md",
    "README.json",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md",
    "machine/adaptive/aq14-effectiveness-qualification.v1.json",
    "machine/schemas/aq14-effectiveness-qualification.v1.schema.json",
    "orchestra_runtime/domain/adaptive/effectiveness_qualification.py",
    "scripts/validation/validate_aq14.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq14.py",
}


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def out(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected one wiring anchor in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    if out("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("unexpected AQ14 branch")
    run("git", "merge-base", "--is-ancestor", BASE, "HEAD")
    run("git", "config", "user.name", "JEO")
    run("git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com")

    readme = ROOT / "README.json"
    readme_anchor = '    "adaptive_assurance_aq13_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md"\n'
    readme_addition = readme_anchor[:-1] + ',\n' + (
        '    "adaptive_assurance_aq14_contract": "machine/adaptive/aq14-effectiveness-qualification.v1.json",\n'
        '    "adaptive_assurance_aq14_schema": "machine/schemas/aq14-effectiveness-qualification.v1.schema.json",\n'
        '    "adaptive_assurance_aq14_runtime": "orchestra_runtime/domain/adaptive/effectiveness_qualification.py",\n'
        '    "adaptive_assurance_aq14_validator": "scripts/validation/validate_aq14.py",\n'
        '    "adaptive_assurance_aq14_validation": "tests/runtime/test_adaptive_assurance_aq14.py",\n'
        '    "adaptive_assurance_aq14_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md"\n'
    )
    replace_once(readme, readme_anchor, readme_addition)
    json.loads(readme.read_text(encoding="utf-8"))

    run_tests = ROOT / "tests/behavior/run_tests.py"
    test_anchor = '        {"Name": "validate_aq13.py", "Path": "scripts/validation/validate_aq13.py"},\n'
    replace_once(
        run_tests,
        test_anchor,
        test_anchor + '        {"Name": "validate_aq14.py", "Path": "scripts/validation/validate_aq14.py"},\n',
    )

    changelog = ROOT / "CHANGELOG.md"
    heading = "## Unreleased ADAPT-QA AQ-14 final effectiveness qualification\n\n"
    if heading in changelog.read_text(encoding="utf-8"):
        raise RuntimeError("AQ14 changelog entry already present")
    entry = (
        heading
        + "- Adds deterministic final qualification over the exact canonical AQ9-AQ13 evidence chain, pinned to canonical PR/SHA/tree identities.\n"
        + "- Requires PASS dispositions, canonical verification, source/promotion/post-merge assurance, independent deterministic evidence, and zero unresolved critical findings for all five prior phases.\n"
        + "- Fails closed to revision on prior HOLD/revision or critical findings, and waits when assurance evidence is incomplete rather than inferring effectiveness.\n"
        + "- Keeps AQ14 evidence-only and non-authorizing: no organic-effectiveness or production-readiness claim, release/deployment, provider, telemetry, protected-policy, AQ15, or CritiQual CUD10 authority.\n\n"
    )
    changelog.write_text(entry + changelog.read_text(encoding="utf-8"), encoding="utf-8")

    run("python", "-B", "scripts/validation/validate_aq14.py")
    run("python", "-B", "-m", "unittest", "discover", "-s", "tests/runtime", "-p", "test_adaptive_assurance_aq14.py")
    run("python", "-B", "-m", "py_compile", "orchestra_runtime/domain/adaptive/effectiveness_qualification.py", "scripts/validation/validate_aq14.py", "tests/runtime/test_adaptive_assurance_aq14.py")

    run("git", "add", "CHANGELOG.md", "README.json", "tests/behavior/run_tests.py")
    run("git", "commit", "-m", "feat(aq14): wire final effectiveness qualification")

    if DIAGNOSTIC_LOG.exists():
        DIAGNOSTIC_LOG.unlink()
    for helper in HELPERS:
        if helper.exists():
            helper.unlink()
    run("git", "add", "-A")
    run("git", "commit", "-m", "chore(aq14): retire bootstrap wiring")

    run("git", "diff", "--check", BASE)
    changed = set(out("git", "diff", "--name-only", BASE, "HEAD").splitlines())
    if changed != EXACT_PATHS:
        raise RuntimeError(f"AQ14 exact inventory mismatch: {sorted(changed)}")
    print("AQ14_TARGETED_VALIDATION=PASS")
    print("AQ14_EXACT_REGISTERED_INVENTORY=9_OF_9")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
