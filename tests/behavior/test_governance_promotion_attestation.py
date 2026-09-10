#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "promotion_attestation",
    ROOT / "scripts" / "validate_governance_promotion_attestation.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)

BASE = "1" * 40
SOURCE = "2" * 40
TREE = "3" * 40
CARRIER = "4" * 40
CANONICAL = "5" * 40
MATERIALIZE_REF = "materialize/example"


def pr(number, base_ref, base_sha, head_ref, head_sha, *, merged=False, merge_sha=None):
    return {
        "number": number,
        "base": {"ref": base_ref, "sha": base_sha},
        "head": {"ref": head_ref, "sha": head_sha},
        "merged_at": "2026-09-11T00:00:00Z" if merged else None,
        "merge_commit_sha": merge_sha,
    }


SOURCE_PR = pr(10, "main", BASE, "feature/source", SOURCE)
MAT_PR = pr(11, MATERIALIZE_REF, BASE, "feature/source", SOURCE, merged=True, merge_sha=CARRIER)
CANONICAL_PR = pr(12, "main", BASE, MATERIALIZE_REF, CARRIER, merged=True, merge_sha=CANONICAL)

CHECKS = [
    {"name": name, "status": "completed", "conclusion": "success"}
    for name in mod.REQUIRED_SOURCE_CHECKS
] + [{"name": "CodeQL", "status": "completed", "conclusion": "success"}]

RUNS = [
    {"name": "validate", "status": "completed", "conclusion": "success"},
    {"name": "Governance Check", "status": "completed", "conclusion": "success"},
]


def api_fixture(*, source_tree=TREE, carrier_tree=TREE, canonical_tree=TREE, carrier_verified=True, source_checks=None):
    return {
        f"/git/commits/{SOURCE}": {"tree": {"sha": source_tree}, "parents": [{"sha": BASE}], "verification": {"verified": False, "reason": "unsigned"}},
        f"/git/commits/{CARRIER}": {"tree": {"sha": carrier_tree}, "parents": [{"sha": BASE}], "verification": {"verified": carrier_verified, "reason": "valid" if carrier_verified else "unsigned"}},
        f"/git/commits/{CANONICAL}": {"tree": {"sha": canonical_tree}, "parents": [{"sha": BASE}], "verification": {"verified": True, "reason": "valid"}},
        f"/commits/{SOURCE}/pulls?per_page=100": [SOURCE_PR],
        f"/commits/{CANONICAL}/pulls?per_page=100": [CANONICAL_PR],
        "/pulls?state=closed&base=materialize%2Fexample&per_page=100&sort=updated&direction=desc": [MAT_PR],
        "/pulls/10/files?per_page=100": [{"filename": "README.json"}, {"filename": "scripts/example.py"}],
        "/pulls/12/files?per_page=100": [{"filename": "scripts/example.py"}, {"filename": "README.json"}],
        f"/commits/{SOURCE}/check-runs?per_page=100": {"check_runs": source_checks if source_checks is not None else CHECKS},
        f"/actions/runs?head_sha={SOURCE}&event=pull_request&per_page=100": {"workflow_runs": RUNS},
    }


def getter(mapping):
    def get(path):
        if path not in mapping:
            raise AssertionError(f"unexpected API path: {path}")
        return mapping[path]
    return get


class PromotionAttestationTests(unittest.TestCase):
    def test_ordinary_source_pr_requires_full_assurance(self):
        event = {"pull_request": pr(20, "main", BASE, "feature/ordinary", SOURCE)}
        mode, evidence = mod.determine_mode("pull_request", event, get=getter({}))
        self.assertEqual(mod.MODE_FULL, mode)
        self.assertIsNone(evidence)

    def test_signed_tree_identical_promotion_is_attested(self):
        event = {"pull_request": pr(12, "main", BASE, MATERIALIZE_REF, CARRIER)}
        mode, evidence = mod.determine_mode("pull_request", event, get=getter(api_fixture()))
        self.assertEqual(mod.MODE_ATTESTED, mode)
        self.assertEqual(SOURCE, evidence["source_sha"])
        self.assertEqual(TREE, evidence["source_tree"])
        self.assertEqual(CARRIER, evidence["carrier_sha"])
        self.assertEqual(TREE, evidence["carrier_tree"])
        self.assertEqual(["README.json", "scripts/example.py"], evidence["changed_paths"])

    def test_tree_change_fails_closed(self):
        event = {"pull_request": pr(12, "main", BASE, MATERIALIZE_REF, CARRIER)}
        with self.assertRaises(mod.PromotionAttestationError):
            mod.determine_mode(
                "pull_request",
                event,
                get=getter(api_fixture(carrier_tree="6" * 40)),
            )

    def test_unsigned_carrier_fails_closed(self):
        event = {"pull_request": pr(12, "main", BASE, MATERIALIZE_REF, CARRIER)}
        with self.assertRaises(mod.PromotionAttestationError):
            mod.determine_mode(
                "pull_request",
                event,
                get=getter(api_fixture(carrier_verified=False)),
            )

    def test_missing_required_source_check_fails_closed(self):
        event = {"pull_request": pr(12, "main", BASE, MATERIALIZE_REF, CARRIER)}
        checks = [run for run in CHECKS if run["name"] != "runtime-tests"]
        with self.assertRaises(mod.PromotionAttestationError):
            mod.determine_mode(
                "pull_request",
                event,
                get=getter(api_fixture(source_checks=checks)),
            )

    def test_failed_required_source_check_fails_closed(self):
        event = {"pull_request": pr(12, "main", BASE, MATERIALIZE_REF, CARRIER)}
        checks = [dict(run) for run in CHECKS]
        for run in checks:
            if run["name"] == "validate":
                run["conclusion"] = "failure"
        with self.assertRaises(mod.PromotionAttestationError):
            mod.determine_mode(
                "pull_request",
                event,
                get=getter(api_fixture(source_checks=checks)),
            )

    def test_canonical_push_reuses_same_tree_assurance(self):
        event = {"ref": "refs/heads/main", "before": BASE, "after": CANONICAL}
        mode, evidence = mod.determine_mode("push", event, get=getter(api_fixture()))
        self.assertEqual(mod.MODE_ATTESTED, mode)
        self.assertEqual(CANONICAL, evidence["canonical_sha"])
        self.assertEqual(TREE, evidence["canonical_tree"])
        self.assertEqual(BASE, evidence["canonical_parent"])

    def test_unrecognized_main_push_runs_full_assurance(self):
        mapping = {f"/commits/{CANONICAL}/pulls?per_page=100": []}
        event = {"ref": "refs/heads/main", "before": BASE, "after": CANONICAL}
        mode, evidence = mod.determine_mode("push", event, get=getter(mapping))
        self.assertEqual(mod.MODE_FULL, mode)
        self.assertIsNone(evidence)


if __name__ == "__main__":
    unittest.main()
