import os
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import inspect
import subprocess
import ast

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts"))

from validate_artificer_records import (
    ValidatorConfigurationError,
    validate_repository,
    slugify,
    derive_bundle_id
)

class TestArtificerRecordsValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        self.schema_dir = self.repo_root / "internal" / "artificer"
        self.schema_dir.mkdir(parents=True)

        real_schema_dir = Path(__file__).resolve().parent.parent.parent / "internal" / "artificer"
        shutil.copy2(real_schema_dir / "SOURCE_INTAKE_SCHEMA.json", self.schema_dir / "SOURCE_INTAKE_SCHEMA.json")
        shutil.copy2(real_schema_dir / "PATTERN_SCHEMA.json", self.schema_dir / "PATTERN_SCHEMA.json")

        self.records_dir = self.schema_dir / "records"
        self.records_dir.mkdir()
        with open(self.records_dir / "README.md", "w", encoding="utf-8") as f:
            f.write("# Records Registry")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _valid_intake(self):
        return {
            "repository": "test/repo",
            "repository_owner": "test",
            "canonical_url": "https://example.com/test/repo",
            "license": "MIT",
            "default_branch": "main",
            "reviewed_commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            "review_date": "2026-07-11",
            "files_examined": [
                {
                    "file_path": "src/main.py",
                    "line_ranges": ["10-20"]
                }
            ],
            "runtime_behavior_tested": True,
            "source_confidence": "HIGH"
        }

    def _valid_pattern(self):
        return {
            "name": "Test Pattern",
            "description": "A test pattern",
            "source_file": "src/main.py",
            "line_range": "10-20",
            "classification": "REFERENCE_ONLY",
            "assigned_specialist": "cloak",
            "license_implications": "Requires attribution."
        }

    def _write_intake(self, bundle_id: str, data: dict):
        d = self.records_dir / bundle_id
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "source-intake.json", "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _write_pattern(self, bundle_id: str, filename: str, data: dict):
        d = self.records_dir / bundle_id / "patterns"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _create_valid_bundle(
        self,
        *,
        bundle_id: str = "test__repo__a1b2c3d4e5f6",
        include_pattern: bool = False,
    ) -> Path:
        self._write_intake(bundle_id, self._valid_intake())

        patterns_dir = self.records_dir / bundle_id / "patterns"
        patterns_dir.mkdir(parents=True, exist_ok=True)

        if include_pattern:
            self._write_pattern(
                bundle_id,
                "test-pattern.json",
                self._valid_pattern(),
            )

        return self.records_dir / bundle_id

    def assert_failure(
        self,
        failures,
        *,
        target_contains: str | None = None,
        reason_contains: str,
    ):
        matches = [
            failure
            for failure in failures
            if reason_contains.casefold() in failure.reason.casefold()
            and (
                target_contains is None
                or target_contains.casefold() in failure.target.casefold()
            )
        ]

        self.assertTrue(
            matches,
            f"Expected failure containing {reason_contains!r}; got: {failures}",
        )

    # ----------------------------------------------------------------------- #
    # PASSING TESTS
    # ----------------------------------------------------------------------- #

    def test_pass_empty_registry(self):
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_valid_intake_zero_patterns(self):
        self._create_valid_bundle(include_pattern=False)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_valid_one_pattern_bundle(self):
        self._create_valid_bundle(include_pattern=True)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_multiple_pattern_bundle(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        p1 = self._valid_pattern()
        p1["name"] = "Pattern 1"
        self._write_pattern(bundle_id, "pattern-1.json", p1)
        p2 = self._valid_pattern()
        p2["name"] = "Pattern 2"
        self._write_pattern(bundle_id, "pattern-2.json", p2)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_exact_and_contained_line_range_coverage(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        p1 = self._valid_pattern()
        p1["name"] = "Exact"
        p1["line_range"] = "10-20"
        self._write_pattern(bundle_id, "exact.json", p1)
        p2 = self._valid_pattern()
        p2["name"] = "Contained"
        p2["line_range"] = "12-15"
        self._write_pattern(bundle_id, "contained.json", p2)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_runtime_boolean_true_and_false(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        i = self._valid_intake()
        i["runtime_behavior_tested"] = False
        self._write_intake(bundle_id, i)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_failure_missing_default_branch(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        i = self._valid_intake()
        del i["default_branch"]
        self._write_intake(bundle_id, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(
            failures,
            target_contains="source-intake.json",
            reason_contains="missing required field 'default_branch'",
        )

    def test_failure_blank_default_branch_requires_a_value(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        intake = self._valid_intake()
        intake["default_branch"] = "  "
        self._write_intake(bundle_dir.name, intake)
        failures = validate_repository(self.repo_root)
        self.assert_failure(
            failures,
            target_contains="source-intake.json",
            reason_contains="default_branch' must be non-empty after trimming",
        )
        self.assertNotIn("omit", "\n".join(failure.remediation for failure in failures))

    def test_pass_git_url_and_trailing_slash_url(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        i = self._valid_intake()
        i["canonical_url"] = "https://example.com/test/repo.git/"
        self._write_intake(bundle_id, i)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_optional_license_implications_reference_only(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        p = self._valid_pattern()
        p["classification"] = "REFERENCE_ONLY"
        if "license_implications" in p:
            del p["license_implications"]
        self._write_pattern(bundle_id, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    def test_pass_multiple_patterns_sharing_one_examined_file(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        bundle_id = bundle_dir.name
        p1 = self._valid_pattern()
        p1["name"] = "p1"
        self._write_pattern(bundle_id, "p1.json", p1)
        p2 = self._valid_pattern()
        p2["name"] = "p2"
        p2["line_range"] = "11-12"
        self._write_pattern(bundle_id, "p2.json", p2)
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0)

    # ----------------------------------------------------------------------- #
    # FAILING TESTS
    # ----------------------------------------------------------------------- #

    def test_failure_missing_readme(self):
        (self.records_dir / "README.md").unlink()
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="README.md", reason_contains="missing")

    def test_failure_unexpected_registry_root_file(self):
        with open(self.records_dir / "unexpected.txt", "w") as f:
            f.write("test")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="unexpected.txt", reason_contains="unexpected file")

    def test_failure_malformed_bundle_id(self):
        self._write_intake("bad_bundle", self._valid_intake())
        (self.records_dir / "bad_bundle" / "patterns").mkdir()
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="bad_bundle", reason_contains="does not match expected format")

    def test_failure_missing_intake(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        (bundle_dir / "source-intake.json").unlink()
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="missing")

    def test_failure_missing_patterns_directory(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        (bundle_dir / "patterns").rmdir()
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains=bundle_dir.name, reason_contains="patterns/ directory is missing")

    def test_failure_unexpected_bundle_entry(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        with open(bundle_dir / "unexpected.txt", "w") as f:
            f.write("test")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="unexpected.txt", reason_contains="Unexpected entry")

    def test_failure_nested_pattern_directory(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        (bundle_dir / "patterns" / "nested").mkdir()
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="nested", reason_contains="Nested directory")

    def test_failure_non_json_pattern_file(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        with open(bundle_dir / "patterns" / "test.txt", "w") as f:
            f.write("test")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test.txt", reason_contains="Non-JSON file")

    # JSON Parsing Tests
    def test_failure_invalid_utf8(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "wb") as f:
            f.write(b"\xff\xfe")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="not valid UTF-8")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "wb") as f:
            f.write(b"\xff\xfe")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="not valid UTF-8")

    def test_failure_empty_json(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "w") as f:
            f.write("")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="file is empty")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "w") as f:
            f.write("")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="file is empty")

    def test_failure_malformed_json(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "w") as f:
            f.write("{bad")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="malformed JSON")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "w") as f:
            f.write("{bad")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="malformed JSON")

    def test_failure_duplicate_json_key(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "w") as f:
            f.write('{"repository": "a", "repository": "b"}')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="duplicate json key")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "w") as f:
            f.write('{"name": "a", "name": "b"}')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="duplicate json key")

    def test_failure_top_level_array(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "w") as f:
            f.write('[]')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="top-level json value must be an object")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "w") as f:
            f.write('[]')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="top-level json value must be an object")

    def test_failure_oversized_file(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "source-intake.json", "w") as f:
            f.write('{"repository": "' + "a" * (5 * 1024 * 1024) + '"}')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="exceeds maximum size")

        self._create_valid_bundle(include_pattern=True)
        with open(bundle_dir / "patterns" / "test-pattern.json", "w") as f:
            f.write('{"name": "' + "a" * (5 * 1024 * 1024) + '"}')
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="exceeds maximum size")

    def test_failure_symlink(self):
        try:
            target = self.temp_dir / Path("dummy")
            target.write_text("dummy")
            link = self.temp_dir / Path("link")
            os.symlink(target, link)
            link.unlink()
            target.unlink()
            can_symlink = True
        except OSError:
            can_symlink = False

        if not can_symlink:
            self.skipTest("Symlink creation is unavailable on this platform")

        bundle_dir = self._create_valid_bundle(include_pattern=True)
        (bundle_dir / "source-intake.json").unlink()
        target = bundle_dir / "real.json"
        with open(target, "w") as f: f.write('{}')
        os.symlink(target, bundle_dir / "source-intake.json")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="symbolic links are not permitted")

        bundle_dir = self._create_valid_bundle(include_pattern=True)
        (bundle_dir / "patterns" / "test-pattern.json").unlink()
        target = bundle_dir / "real.json"
        with open(target, "w") as f: f.write('{}')
        os.symlink(target, bundle_dir / "patterns" / "test-pattern.json")
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="symbolic links are not permitted")

    # Schema/Intake Mutation Tests
    def test_failure_missing_required_field(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        del i["repository"]
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="missing required field")

    def test_failure_wrong_field_type(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["repository"] = 123
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="expected string, got int")

    def test_failure_unexpected_additional_property(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["bad"] = "value"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="unexpected additional property 'bad'")

    def test_failure_invalid_enum(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["source_confidence"] = "INVALID"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="is not one of the allowed enum values")

    def test_failure_governance_outcome_classification(self):
        for classification in ("REJECTED", "DEFERRED", "DUPLICATE"):
            with self.subTest(classification=classification):
                bundle_dir = self._create_valid_bundle(include_pattern=True)
                pattern = self._valid_pattern()
                pattern["classification"] = classification
                self._write_pattern(bundle_dir.name, "test-pattern.json", pattern)
                failures = validate_repository(self.repo_root)
                self.assert_failure(
                    failures,
                    target_contains="test-pattern.json",
                    reason_contains="is not one of the allowed enum values",
                )

    def test_failure_invalid_sha_pattern(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["reviewed_commit_sha"] = "short"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="does not match pattern")

    def test_failure_non_https_url(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["canonical_url"] = "http://example.com/a/b"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must use https scheme")

    def test_failure_url_credentials(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["canonical_url"] = "https://user:pass@example.com/a/b"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must not contain credentials")

    def test_failure_url_query(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["canonical_url"] = "https://example.com/a/b?q=1"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must not contain a query string")

    def test_failure_url_fragment(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["canonical_url"] = "https://example.com/a/b#frag"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must not contain a fragment")

    def test_failure_url_repository_mismatch(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["canonical_url"] = "https://example.com/different/repo"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="path must end with")

    def test_failure_invalid_calendar_date(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["review_date"] = "bad"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="not a valid ISO calendar date")

    def test_failure_repository_owner_mismatch(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["repository_owner"] = "different"
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="does not match owner component")

    def test_failure_empty_files_examined(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["files_examined"] = []
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must contain at least one entry")

    def test_failure_duplicate_examined_file(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["files_examined"].append({"file_path": "src/main.py", "line_ranges": ["20-30"]})
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="is a duplicate")

    # Unsafe Path Tests
    def test_failure_unsafe_paths(self):
        unsafe_paths = [
            ("/absolute/path", "is absolute"),
            (r"C:\repo\file.py", "contains backslashes"),
            ("src\\main.py", "contains backslashes"),
            ("./src/main.py", "contains '.' path component"),
            ("../src/main.py", "contains parent traversal"),
        ]
        for path_value, expected_reason in unsafe_paths:
            with self.subTest(path_value=path_value):
                bundle_dir = self._create_valid_bundle()
                i = self._valid_intake()
                i["files_examined"][0]["file_path"] = path_value
                self._write_intake(bundle_dir.name, i)
                failures = validate_repository(self.repo_root)
                self.assert_failure(failures, target_contains="source-intake.json", reason_contains=expected_reason)

    # Line Range Tests
    def test_failure_malformed_reversed_non_positive_line_ranges(self):
        cases = [
            ("a-b", "is not a valid range"),
            ("20-10", "has start > end"),
            ("0-5", "contains non-positive line numbers"),
        ]
        for range_value, expected_reason in cases:
            with self.subTest(range_value=range_value):
                bundle_dir = self._create_valid_bundle()
                i = self._valid_intake()
                i["files_examined"][0]["line_ranges"] = [range_value]
                self._write_intake(bundle_dir.name, i)
                failures = validate_repository(self.repo_root)
                self.assert_failure(failures, target_contains="source-intake.json", reason_contains=expected_reason)

    def test_failure_duplicate_line_range(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["files_examined"][0]["line_ranges"] = ["10-20", "10-20"]
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="is a duplicate")

    def test_failure_empty_line_ranges(self):
        bundle_dir = self._create_valid_bundle()
        i = self._valid_intake()
        i["files_examined"][0]["line_ranges"] = []
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="source-intake.json", reason_contains="must contain at least one entry")

    def test_failure_non_covering_ranges(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        i = self._valid_intake()
        i["files_examined"][0]["line_ranges"] = ["100-200"]
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="not covered by any examined range")

    # Pattern Tests
    def test_failure_filename_mismatch(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        self._write_pattern(bundle_dir.name, "mismatch.json", self._valid_pattern())
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="mismatch.json", reason_contains="does not match expected")

    def test_failure_duplicate_case_folded_pattern_names(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        p1 = self._valid_pattern()
        p1["name"] = "test1"
        self._write_pattern(bundle_dir.name, "test1.json", p1)
        p2 = self._valid_pattern()
        p2["name"] = "TEST1"
        self._write_pattern(bundle_dir.name, "test2.json", p2)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test2.json", reason_contains="does not match expected")
        self.assert_failure(failures, target_contains="test2.json", reason_contains="Duplicate case-folded pattern name")

    def test_failure_missing_source_file_mapping(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        p = self._valid_pattern()
        p["source_file"] = "missing.py"
        self._write_pattern(bundle_dir.name, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="is not declared in the bundle's files_examined")

    def test_failure_missing_pattern_line_range(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        p = self._valid_pattern()
        if "line_range" in p:
            del p["line_range"]
        self._write_pattern(bundle_dir.name, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="is required for committed")

    def test_failure_no_examined_line_ranges_for_a_pattern(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        i = self._valid_intake()
        if "line_ranges" in i["files_examined"][0]:
            del i["files_examined"][0]["line_ranges"]
        self._write_intake(bundle_dir.name, i)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="has no examined line ranges in source-intake.json")

    def test_failure_pattern_outside_examined_coverage(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        p = self._valid_pattern()
        p["line_range"] = "5-25"
        self._write_pattern(bundle_dir.name, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="not covered by any examined range")

    def test_failure_missing_license_implications(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        p = self._valid_pattern()
        p["classification"] = "CODE_REUSE_REVIEW_REQUIRED"
        if "license_implications" in p:
            del p["license_implications"]
        self._write_pattern(bundle_dir.name, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="is required for classification")

    def test_failure_artificer_assigned_as_specialist(self):
        bundle_dir = self._create_valid_bundle(include_pattern=True)
        p = self._valid_pattern()
        p["assigned_specialist"] = "artificer"
        self._write_pattern(bundle_dir.name, "test-pattern.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="test-pattern.json", reason_contains="is not one of the allowed enum values")

    def test_failure_empty_slug_pattern_name(self):
        bundle_dir = self._create_valid_bundle(include_pattern=False)
        p = self._valid_pattern()
        p["name"] = "   "
        self._write_pattern(bundle_dir.name, "empty.json", p)
        failures = validate_repository(self.repo_root)
        self.assert_failure(failures, target_contains="empty.json", reason_contains="must be non-empty")

    # Schema configuration Tests
    def test_failure_missing_schema(self):
        os.unlink(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json")
        with self.assertRaises(ValidatorConfigurationError):
            validate_repository(self.repo_root)

    def test_failure_unsupported_keyword(self):
        d = json.loads((self.schema_dir / "SOURCE_INTAKE_SCHEMA.json").read_text(encoding="utf-8"))
        d["allOf"] = []
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w") as f:
            json.dump(d, f)
        with self.assertRaises(ValidatorConfigurationError):
            validate_repository(self.repo_root)

    def test_failure_unsupported_schema_type(self):
        d = json.loads((self.schema_dir / "SOURCE_INTAKE_SCHEMA.json").read_text(encoding="utf-8"))
        d["properties"]["repository"]["type"] = "integer"
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w") as f:
            json.dump(d, f)
        with self.assertRaises(ValidatorConfigurationError):
            validate_repository(self.repo_root)

    def test_failure_unsupported_schema_format(self):
        d = json.loads((self.schema_dir / "SOURCE_INTAKE_SCHEMA.json").read_text(encoding="utf-8"))
        d["properties"]["repository"]["format"] = "email"
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w") as f:
            json.dump(d, f)
        with self.assertRaises(ValidatorConfigurationError):
            validate_repository(self.repo_root)

    def test_failure_invalid_schema_regex(self):
        d = json.loads((self.schema_dir / "SOURCE_INTAKE_SCHEMA.json").read_text(encoding="utf-8"))
        d["properties"]["repository"]["pattern"] = "["
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w") as f:
            json.dump(d, f)
        with self.assertRaises(ValidatorConfigurationError):
            validate_repository(self.repo_root)

    def test_failure_cli_exit_codes(self):
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "validate_artificer_records.py")

        # Valid fixture
        self._create_valid_bundle(include_pattern=True)
        r = subprocess.run([sys.executable, script, "--repo-root", str(self.repo_root)], capture_output=True)
        self.assertEqual(r.returncode, 0)

        # Invalid record
        self._write_intake("bad_bundle", self._valid_intake())
        (self.records_dir / "bad_bundle" / "patterns").mkdir()
        r = subprocess.run([sys.executable, script, "--repo-root", str(self.repo_root)], capture_output=True)
        self.assertEqual(r.returncode, 1)
        shutil.rmtree(self.records_dir / "bad_bundle")

        # Invalid schema configuration
        d = json.loads((self.schema_dir / "SOURCE_INTAKE_SCHEMA.json").read_text(encoding="utf-8"))
        d["allOf"] = []
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w") as f:
            json.dump(d, f)
        r = subprocess.run([sys.executable, script, "--repo-root", str(self.repo_root)], capture_output=True)
        self.assertEqual(r.returncode, 2)

        # Invalid option
        r = subprocess.run([sys.executable, script, "--unknown-option"], capture_output=True)
        self.assertEqual(r.returncode, 2)

        # Help option
        r = subprocess.run([sys.executable, script, "--help"], capture_output=True)
        self.assertEqual(r.returncode, 0)

    def test_quality_gate(self):
        class ASTVisitor(ast.NodeVisitor):
            def __init__(self):
                self.has_assert = False
                self.calls_validator = False
                self.has_generic_len = False

            def visit_Assert(self, node):
                self.has_assert = True
                self.generic_check(node.test)
                self.generic_check(node)
                self.generic_call_check(node)
                self.generic_compare_check(node)
                self.generic_call_check(node.test)
                self.generic_compare_check(node.test)
                self.generic_call_len_failures(node.test)
                self.generic_call_len_failures(node)
                self.generic_greater_len(node)
                self.generic_greater_len(node.test)
                self.generic_len_failures(node)
                self.generic_len_failures(node.test)

            def generic_len_failures(self, n):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "len":
                    if isinstance(n.args[0], ast.Name) and n.args[0].id == "failures":
                        self.has_generic_len = True

            def generic_greater_len(self, n):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "assertGreater":
                    if isinstance(n.args[0], ast.Call) and isinstance(n.args[0].func, ast.Name) and n.args[0].func.id == "len":
                        self.has_generic_len = True

            def generic_call_len_failures(self, n):
                for child in ast.walk(n):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "len":
                        if child.args and isinstance(child.args[0], ast.Name) and child.args[0].id == "failures":
                            self.has_generic_len = True

            def generic_check(self, n):
                pass

            def generic_call_check(self, n):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "assertTrue":
                    pass

            def generic_compare_check(self, n):
                if isinstance(n, ast.Compare) and isinstance(n.left, ast.Call):
                    if isinstance(n.left.func, ast.Name) and n.left.func.id == "len":
                        self.has_generic_len = True

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == "validate_repository":
                    self.calls_validator = True
                if isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert"):
                    self.has_assert = True
                self.generic_call_len_failures(node)
                self.generic_greater_len(node)
                self.generic_len_failures(node)
                self.generic_compare_check(node)
                self.generic_call_check(node)
                self.generic_check(node)
                self.generic_call_check(node)
                self.generic_call_len_failures(node)

        methods = [m for m in dir(self) if m.startswith("test_failure_")]
        for m in methods:
            source = inspect.getsource(getattr(self, m))
            self.assertFalse("pass" in source.split(), f"test_quality_gate failed: {m} contains pass")
            self.assertFalse("TODO" in source, f"test_quality_gate failed: {m} contains TODO")
            self.assertFalse("NotImplementedError" in source, f"test_quality_gate failed: {m} contains NotImplementedError")
            import textwrap
            tree = ast.parse(textwrap.dedent(source))
            visitor = ASTVisitor()
            for node in ast.walk(tree):
                visitor.visit(node)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                    visitor.calls_validator = True
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "assertRaises":
                    visitor.has_assert = True
                    visitor.calls_validator = True

            self.assertTrue(visitor.calls_validator, f"test_quality_gate failed: {m} does not call validate_repository or CLI")
            self.assertTrue(visitor.has_assert, f"test_quality_gate failed: {m} contains no assert")
            self.assertFalse(visitor.has_generic_len, f"test_quality_gate failed: {m} uses generic len(failures) > 0")


if __name__ == "__main__":
    unittest.main()
