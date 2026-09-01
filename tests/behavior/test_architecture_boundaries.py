from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validation"))

import validate_architecture_boundaries as architecture  # noqa: E402


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_current_repository_passes(self) -> None:
        self.assertEqual(architecture.validate(ROOT), [])

    def test_new_flat_runtime_module_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            runtime = repo / "orchestra_runtime"
            runtime.mkdir(parents=True)
            (runtime / "__init__.py").write_text("", encoding="utf-8")
            (runtime / "new_feature.py").write_text("VALUE = 1\n", encoding="utf-8")
            policy = self._write_policy(repo)

            violations = architecture.validate(repo, policy)
            self.assertTrue(any("PLACEMENT_NEW_FLAT_MODULE" in item for item in violations))

    def test_domain_cannot_depend_on_infrastructure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            runtime = repo / "orchestra_runtime"
            domain = runtime / "domain"
            domain.mkdir(parents=True)
            (runtime / "__init__.py").write_text("", encoding="utf-8")
            (domain / "__init__.py").write_text("", encoding="utf-8")
            (domain / "policy.py").write_text(
                "from orchestra_runtime.infrastructure import adapter\n",
                encoding="utf-8",
            )
            policy = self._write_policy(repo)

            violations = architecture.validate(repo, policy)
            self.assertTrue(any("DEPENDENCY_DIRECTION" in item for item in violations))

    @staticmethod
    def _write_policy(repo: Path) -> Path:
        policy_path = repo / "machine" / "architecture" / "runtime-boundaries.v1.json"
        policy_path.parent.mkdir(parents=True)
        policy = {
            "schema_version": "orchestra.runtime-architecture-boundaries.v1",
            "runtime_root": "orchestra_runtime",
            "canonical_roots": ["domain", "application", "infrastructure", "entrypoints", "bootstrap", "shared", "resources"],
            "legacy_package_roots": [],
            "legacy_top_level_modules": ["__init__.py"],
            "layers": {
                "domain": {
                    "forbidden_import_prefixes": ["orchestra_runtime.infrastructure", "internal"],
                    "forbidden_stdlib_prefixes": [],
                },
                "application": {"forbidden_import_prefixes": ["orchestra_runtime.infrastructure", "internal"]},
                "infrastructure": {"forbidden_import_prefixes": ["internal"]},
                "entrypoints": {"forbidden_import_prefixes": ["internal"]},
                "bootstrap": {"forbidden_import_prefixes": ["internal"]},
                "shared": {"forbidden_import_prefixes": ["orchestra_runtime.domain", "internal"]},
            },
            "placement": {
                "dto_root": "orchestra_runtime/application/dto",
                "dpo_root": "orchestra_runtime/infrastructure/persistence/dpo",
                "repository_port_root": "orchestra_runtime/application/ports/repositories",
                "repository_implementation_root": "orchestra_runtime/infrastructure/persistence/repositories",
                "runtime_resources_root": "orchestra_runtime/resources",
            },
            "compatibility_facades": {},
            "rules": {},
        }
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        return policy_path


if __name__ == "__main__":
    unittest.main()
