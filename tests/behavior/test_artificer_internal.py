import unittest
import tempfile
import json
import shutil
import subprocess
from pathlib import Path
import sys
import re

# Add scripts directory to sys.path so we can import the validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import validate_artificer_internal as val


class TestArtificerInternal(unittest.TestCase):

    def setUp(self):
        # Find real repo root
        self.real_repo_root = Path(__file__).resolve().parent.parent.parent
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir_obj.name)

        # Create minimal valid setup in temp_root
        # 1. Copy required internal and docs/internal files from real repo
        for rel_path in val.REQUIRED_FILES:
            src = self.real_repo_root / rel_path
            dst = self.temp_root / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # 2. Create minimal public files (without "artificer")
        (self.temp_root / "plugin.json").write_text('{"name": "orchestra", "version": "1.0.0"}', encoding="utf-8")
        (self.temp_root / "SKILL_INDEX.md").write_text("Public skills index page.", encoding="utf-8")
        (self.temp_root / "ROUTING_MAP.md").write_text("Public routing map.", encoding="utf-8")
        (self.temp_root / "commands").mkdir(exist_ok=True)
        (self.temp_root / "commands" / "cmd1.md").write_text("command one detail", encoding="utf-8")
        (self.temp_root / "skills").mkdir(exist_ok=True)
        (self.temp_root / "skills" / "skill1.md").write_text("skill one description", encoding="utf-8")
        (self.temp_root / "orchestra_runtime").mkdir(exist_ok=True)
        (self.temp_root / "orchestra_runtime" / "router.py").write_text("def route(): pass", encoding="utf-8")
        (self.temp_root / "adapters" / "codex" / "skills").mkdir(parents=True, exist_ok=True)
        (self.temp_root / "adapters" / "codex" / "skills" / "codex_skill.md").write_text("codex skill detail", encoding="utf-8")

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    # === Passing Cases ===

    def test_complete_valid_contract_passes(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_internal_artificer_references_allowed(self):
        # References to artificer inside internal files is allowed
        # (check_public_non_registration ignores internal directories)
        artificer_md_path = self.temp_root / "internal/artificer/ARTIFICER.md"
        self.assertTrue("artificer" in artificer_md_path.read_text(encoding="utf-8").lower())
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_public_surfaces_without_artificer_references_pass(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_runtime_behavior_tested_false_valid(self):
        # runtime_behavior_tested type must be boolean, which it is
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_explicit_negative_execution_boundary(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_explicit_negative_dependency_installation_boundary(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_explicit_no_self_implementation_boundary(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_explicit_no_self_approval_boundary(self):
        failures = val.validate_repository(self.temp_root)
        self.assertEqual(failures, [])

    def test_valid_cli_returns_0(self):
        script_path = self.real_repo_root / "scripts/validate_artificer_internal.py"
        res = subprocess.run(
            [sys.executable, str(script_path), "--repo-root", str(self.temp_root)],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Validation Passed", res.stdout)

    # === Failing Cases ===

    def test_failure_missing_required_file(self):
        target = self.temp_root / "internal/artificer/ARTIFICER.md"
        target.unlink()
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "does not exist" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_empty_required_file(self):
        target = self.temp_root / "internal/artificer/ARTIFICER.md"
        target.write_text("", encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "is empty" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_invalid_utf8_required_file(self):
        target = self.temp_root / "internal/artificer/ARTIFICER.md"
        target.write_bytes(b"\xff\xfe\xfd")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "decode as utf-8" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_invalid_json_schema_syntax(self):
        target = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        target.write_text("invalid json {", encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "json parsing failed" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_missing_schema_property(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        del schema["properties"]["name"]
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "required field 'name' not present in properties" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_required_field_absent_from_properties(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["required"].append("absent_field")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "required field 'absent_field' not present in properties" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_additional_properties_true(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["additionalProperties"] = True
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "additionalproperties" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_classification_enum_drift(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["classification"]["enum"].remove("REFERENCE_ONLY")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "classification enum mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_deprecated_classification_reintroduced(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["classification"]["enum"].append("REJECTED")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "classification enum mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_duplicate_classification_enum(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["classification"]["enum"].append("REFERENCE_ONLY")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "duplicate values found in enum array" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_added_to_assigned_specialists(self):
        path = self.temp_root / "internal/artificer/PATTERN_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["assigned_specialist"]["enum"].append("artificer")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/PATTERN_SCHEMA.json"
                and "assigned_specialist enum must never contain 'artificer'" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_source_confidence_enum_drift(self):
        path = self.temp_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["source_confidence"]["enum"] = ["HIGH", "LOW"]
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
                and "source confidence enum mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_default_branch_removed_from_required(self):
        path = self.temp_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["required"].remove("default_branch")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
                and "required list mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_invalid_reviewed_commit_sha_pattern(self):
        path = self.temp_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["reviewed_commit_sha"]["pattern"] = "^[0-9a-f]{8}$"
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
                and "reviewed_commit_sha pattern mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_invalid_review_date_format(self):
        path = self.temp_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["review_date"]["format"] = "date-time"
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
                and "review_date format mismatch" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_evidence_category_removed(self):
        path = self.temp_root / "docs/internal/EVIDENCE_REQUIREMENTS.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("SOURCE_CONFIRMED", "SOME_OTHER_THING")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/EVIDENCE_REQUIREMENTS.md"
                and "missing evidence category: source_confirmed" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_evidence_category_duplicated(self):
        path = self.temp_root / "docs/internal/EVIDENCE_REQUIREMENTS.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("- **`SOURCE_CONFIRMED`**", "- **`SOURCE_CONFIRMED`**\n- **`SOURCE_CONFIRMED`**")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/EVIDENCE_REQUIREMENTS.md"
                and "duplicate evidence category: source_confirmed" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_no_execution_boundary_removed(self):
        path = self.temp_root / "internal/artificer/ARTIFICER.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("Artificer must not execute external or untrusted repository code.", "")
        content = content.replace("Artificer must not execute build scripts, run tests, or install packages of external codebases.", "")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "no external code execution" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_external_execution_permission_introduced(self):
        path = self.temp_root / "internal/artificer/ARTIFICER.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("Artificer must not execute build scripts, run tests, or install packages of external codebases.", "")
        content = content.replace("Artificer must not execute external or untrusted repository code.", "Artificer may execute external repository code.")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "no external code execution" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_external_package_installation_permission_introduced(self):
        path = self.temp_root / "internal/artificer/ARTIFICER.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("Artificer must not execute build scripts, run tests, or install packages of external codebases.", "")
        content = content.replace("Artificer must not install external repository dependencies or packages.", "Artificer can install external packages.")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "no external dependency installation" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_cipher_handoff_removed(self):
        path = self.temp_root / "internal/artificer/ARTIFICER.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("Cipher", "SomeOtherSpecialist")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "cipher handoff" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_given_implementation_ownership(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original_content = path.read_text(encoding="utf-8")
        self.assertIn("Map to **Ponytail** for final code changes.", original_content)
        mutated_content = original_content.replace("Map to **Ponytail** for final code changes.", "Map to **Artificer** for final code changes.")
        self.assertNotEqual(original_content, mutated_content)
        path.write_text(mutated_content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "rejection of implementation ownership assigned to artificer" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_allowed_to_approve_its_own_findings(self):
        path = self.temp_root / "internal/artificer/ARTIFICER.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("Artificer must not approve, adjudicate, or clear its own findings.", "Artificer can approve its own findings.")
        path.write_text(content, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "internal/artificer/ARTIFICER.md"
                and "no self-approval" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_added_to_plugin_json(self):
        (self.temp_root / "plugin.json").write_text('{"name": "orchestra", "specialists": ["artificer"]}', encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "plugin.json"
                and "contains forbidden term 'artificer'" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_command_path_created(self):
        (self.temp_root / "commands" / "artificer.md").write_text("forbidden command file", encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target.replace("\\", "/") == "commands/artificer.md"
                and "forbidden artificer path exists" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_adapter_export_created(self):
        (self.temp_root / "adapters" / "codex" / "skills" / "artificer").mkdir(parents=True, exist_ok=True)
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target.replace("\\", "/") == "adapters/codex/skills/artificer"
                and "forbidden artificer path exists" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_artificer_runtime_route_created(self):
        (self.temp_root / "orchestra_runtime" / "router.py").write_text("import artificer", encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target.replace("\\", "/") == "orchestra_runtime/router.py"
                and "contains forbidden term 'artificer'" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_invalid_fixture_cli_returns_1(self):
        (self.temp_root / "internal/artificer/ARTIFICER.md").unlink()
        script_path = self.real_repo_root / "scripts/validate_artificer_internal.py"
        res = subprocess.run(
            [sys.executable, str(script_path), "--repo-root", str(self.temp_root)],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Validation Failed", res.stdout)

    def test_failure_invalid_cli_usage_returns_2(self):
        script_path = self.real_repo_root / "scripts/validate_artificer_internal.py"
        res = subprocess.run(
            [sys.executable, str(script_path), "--repo-root", str(self.temp_root), "--unknown-option"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 2)

    def test_failure_positive_test_permission(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Must never write implementation code, modify plugin configs, or run tests.", original)
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Must never write implementation code or modify plugin configs."
        ).replace(
            "Artificer does not write unit tests or execute test runners.",
            "Artificer may run tests."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_evidence_decision(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer does not decide if a pattern is a duplicate or if evidence is complete.", original)
        mutated = original.replace(
            "Artificer does not decide if a pattern is a duplicate or if evidence is complete.",
            "Artificer decides when evidence is complete."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not decide if evidence is complete statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_licensing_approval(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer reports licensing, but cannot approve license compliance or IP clearance.", original)
        mutated = original.replace(
            "Artificer reports licensing, but cannot approve license compliance or IP clearance.",
            "Artificer may approve licensing compliance and IP clearance."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not approve licensing statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_adversarial_testing(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer does not perform penetration testing or live vulnerability runs.", original)
        mutated = original.replace(
            "Artificer does not perform penetration testing or live vulnerability runs.",
            "Artificer performs live adversarial and penetration testing."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not perform live adversarial testing statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_positive_implementation_permission(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer must not implement UI code.", original)
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Must never modify plugin configs or run tests."
        ).replace(
            "Artificer must not implement UI code.",
            "Artificer may write implementation code."
        ).replace(
            "Artificer does not edit source files of the active repository.",
            "Artificer may modify source files."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not implement source changes statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_mixed_polarity(self):
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Artificer must not implement source code, but Artificer may run tests."
        ).replace(
            "Artificer does not write unit tests or execute test runners.",
            ""
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_and_mixed_polarity(self):
        """A. 'and' mixed polarity: prohibit implement, permit run tests."""
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Artificer must not implement source code and may run tests."
        ).replace(
            "Artificer does not write unit tests or execute test runners.",
            ""
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_comma_mixed_polarity(self):
        """B. Comma-modal mixed polarity: prohibit implement, permit run tests."""
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Artificer must not implement source code, may run tests."
        ).replace(
            "Artificer does not write unit tests or execute test runners.",
            ""
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_inherited_subject_with_mixed_polarity(self):
        """C. Inherited subject after leading non-Artificer clause with mixed 'but may'."""
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "Must never write implementation code, modify plugin configs, or run tests.",
            "Although the repository is documented, Artificer must not implement code, but may run tests."
        ).replace(
            "Artificer does not write unit tests or execute test runners.",
            ""
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_licensing_and_mixed_polarity(self):
        """D. Licensing mixed polarity: prohibit decide evidence, permit approve licensing."""
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer reports licensing, but cannot approve license compliance or IP clearance.", original)
        mutated = original.replace(
            "Artificer does not decide if a pattern is a duplicate or if evidence is complete.",
            "Artificer must not decide evidence completeness and may approve licensing compliance."
        ).replace(
            "Artificer reports licensing, but cannot approve license compliance or IP clearance.",
            ""
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not approve licensing statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_failure_adversarial_while_mixed_polarity(self):
        """E. Adversarial-testing mixed polarity using 'while'."""
        path = self.temp_root / "docs/internal/ARTIFICER_BOUNDARIES.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("Artificer does not perform penetration testing or live vulnerability runs.", original)
        mutated = original.replace(
            "Artificer does not perform penetration testing or live vulnerability runs.",
            "Artificer must not write implementation code while it performs live adversarial testing."
        )
        self.assertNotEqual(original, mutated)
        path.write_text(mutated, encoding="utf-8")
        failures = val.validate_repository(self.temp_root)
        self.assertTrue(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not perform live adversarial testing statement" in failure.reason.lower()
                for failure in failures
            )
        )

    def test_pass_valid_coordinated_prohibition(self):
        """F. Valid coordinated prohibition — object list must not be split."""
        # The real ARTIFICER_BOUNDARIES.md already has proper prohibitions.
        # Confirm no licensing or IP-related failure using the unmodified file.
        failures = val.validate_repository(self.temp_root)
        self.assertFalse(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not approve licensing statement" in failure.reason.lower()
                for failure in failures
            ),
            "Unmodified ARTIFICER_BOUNDARIES.md should not produce a licensing approval failure"
        )

    def test_pass_valid_shared_negative_modality(self):
        """G. Valid shared negative modality — 'run tests or execute test runners'."""
        # The real ARTIFICER_BOUNDARIES.md contains the correct shared prohibition.
        # Confirm no test-execution failure on the unmodified file.
        failures = val.validate_repository(self.temp_root)
        self.assertFalse(
            any(
                failure.target == "docs/internal/ARTIFICER_BOUNDARIES.md"
                and "artificer does not run tests statement" in failure.reason.lower()
                for failure in failures
            ),
            "Unmodified ARTIFICER_BOUNDARIES.md should not produce a test-execution failure"
        )

    def test_quality_gate(self):

        test_file = Path(__file__).resolve()
        content = test_file.read_text(encoding="utf-8")
        methods = re.findall(r"def\s+(test_failure_[a-zA-Z0-9_]+)\(self\):([\s\S]*?)(?=\n\s*def|\n\s*if __name__|$)", content)
        self.assertTrue(len(methods) > 0, "No test_failure_* methods found!")
        for name, body in methods:
            lines = [line.strip() for line in body.split("\n") if line.strip()]
            for line in lines:
                if line == "pass":
                    self.fail(f"Method '{name}' contains bare 'pass' statement")
                if "TODO" in line:
                    self.fail(f"Method '{name}' contains 'TODO' placeholder")
                if "NotImplementedError" in line:
                    self.fail(f"Method '{name}' contains 'NotImplementedError'")
            has_assertion = any(re.search(r"self\.assert[a-zA-Z]", line) for line in lines)
            self.assertTrue(has_assertion, f"Method '{name}' does not contain any self.assert... statement")


if __name__ == "__main__":
    unittest.main()
