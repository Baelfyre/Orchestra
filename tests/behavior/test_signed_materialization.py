#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "signed_materialization_validator",
    ROOT / "scripts" / "validate_signed_materialization.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


def policy() -> dict:
    return json.loads((ROOT / "machine" / "governance" / "policy.v1.json").read_text(encoding="utf-8"))


def event() -> dict:
    return {
        "action": "opened",
        "number": 321,
        "repository": {"full_name": "Baelfyre/Orchestra"},
        "pull_request": {
            "base": {"ref": "materialize/example", "sha": "1" * 40},
            "head": {"ref": "feature/example", "sha": "2" * 40},
        },
    }


class SignedMaterializationTests(unittest.TestCase):
    def build(self, *, event_doc=None, policy_doc=None, checked_head="2" * 40, tree="3" * 40, paths=None):
        return mod.build_evidence(
            event=event_doc or event(),
            policy=policy_doc or policy(),
            checked_head_sha=checked_head,
            checked_head_tree=tree,
            changed_paths=paths or ["README.md"],
        )

    def test_current_policy_builds_non_authorizing_evidence(self):
        evidence = self.build()
        self.assertEqual(mod.DISPOSITION, evidence["disposition"])
        self.assertFalse(evidence["authority"]["canonical_merge_readiness"])
        self.assertFalse(evidence["authority"]["project_state_promotion"])
        self.assertFalse(evidence["authority"]["release"])
        self.assertFalse(evidence["authority"]["bypass"])
        self.assertEqual("ISOLATED_SIGNING_TARGET_NOT_CANONICAL", evidence["base"]["role"])

    def test_canonical_main_cannot_be_materialization_target(self):
        payload = event()
        payload["pull_request"]["base"]["ref"] = "main"
        with self.assertRaises(mod.MaterializationValidationError):
            self.build(event_doc=payload)

    def test_exact_head_mismatch_is_rejected(self):
        with self.assertRaises(mod.MaterializationValidationError):
            self.build(checked_head="4" * 40)

    def test_materialization_cannot_gain_canonical_readiness(self):
        payload = policy()
        payload["repository_change_transport"]["api_authored_unsigned_tree"]["materialization_pr_is_canonical_readiness"] = True
        with self.assertRaises(mod.MaterializationValidationError):
            self.build(policy_doc=payload)

    def test_materialization_cannot_reuse_canonical_checks(self):
        payload = policy()
        payload["repository_change_transport"]["api_authored_unsigned_tree"]["canonical_required_checks_reusable_from_materialization"] = True
        with self.assertRaises(mod.MaterializationValidationError):
            self.build(policy_doc=payload)

    def test_empty_changed_paths_are_rejected(self):
        with self.assertRaises(mod.MaterializationValidationError):
            mod.build_evidence(
                event=event(),
                policy=policy(),
                checked_head_sha="2" * 40,
                checked_head_tree="3" * 40,
                changed_paths=[],
            )

    def test_workflow_routing_separates_materialization_from_main(self):
        validate = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        mutation = (ROOT / ".github" / "workflows" / "mutation-confidence.yml").read_text(encoding="utf-8")
        cosmic = (ROOT / ".github" / "workflows" / "cosmic-ray-confidence.yml").read_text(encoding="utf-8")
        materialization = (ROOT / ".github" / "workflows" / "signed-materialization.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:\n    branches:\n      - main", validate)
        self.assertIn("pull_request:\n    branches:\n      - main", mutation)
        self.assertIn("pull_request:\n    branches:\n      - main", cosmic)
        self.assertIn('pull_request:\n    branches:\n      - "materialize/**"', materialization)
        self.assertIn("python scripts/validate_signed_materialization.py", materialization)
        self.assertNotIn("tests/runtime", materialization)
        self.assertNotIn("mutmut", materialization)
        self.assertNotIn("cosmic-ray", materialization)


if __name__ == "__main__":
    unittest.main()
