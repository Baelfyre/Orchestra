import os
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path to import the validator
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
        
        # Create minimal required schemas
        self.schema_dir = self.repo_root / "internal" / "artificer"
        self.schema_dir.mkdir(parents=True)
        
        self.source_intake_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "repository": {"type": "string"},
                "repository_owner": {"type": "string"},
                "canonical_url": {"type": "string", "format": "uri"},
                "license": {"type": "string"},
                "default_branch": {"type": "string"},
                "reviewed_commit_sha": {"type": "string", "pattern": "^[0-9a-fA-F]{40}$"},
                "review_date": {"type": "string", "format": "date"},
                "files_examined": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "line_ranges": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^\\d+-\\d+$"}
                            }
                        },
                        "required": ["file_path"],
                        "additionalProperties": False
                    }
                },
                "runtime_behavior_tested": {"type": "boolean"},
                "source_confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]}
            },
            "required": [
                "repository",
                "repository_owner",
                "canonical_url",
                "license",
                "reviewed_commit_sha",
                "review_date",
                "files_examined",
                "runtime_behavior_tested",
                "source_confidence"
            ],
            "additionalProperties": False
        }
        
        self.pattern_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "source_file": {"type": "string"},
                "line_range": {"type": "string", "pattern": "^\\d+-\\d+$"},
                "classification": {"type": "string", "enum": ["REFERENCE_ONLY", "ADAPTED_PATTERN", "CODE_REUSE_REVIEW_REQUIRED"]},
                "assigned_specialist": {"type": "string", "enum": ["cloak", "cipher"]},
                "license_implications": {"type": "string"}
            },
            "required": ["name", "description", "source_file", "classification", "assigned_specialist"],
            "additionalProperties": False
        }
        
        with open(self.schema_dir / "SOURCE_INTAKE_SCHEMA.json", "w", encoding="utf-8") as f:
            json.dump(self.source_intake_schema, f)
            
        with open(self.schema_dir / "PATTERN_SCHEMA.json", "w", encoding="utf-8") as f:
            json.dump(self.pattern_schema, f)
            
        # Create records directory and README
        self.records_dir = self.schema_dir / "records"
        self.records_dir.mkdir()
        with open(self.records_dir / "README.md", "w", encoding="utf-8") as f:
            f.write("# Records Registry")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_valid_bundle(self, bundle_id="test-owner__test-repo__abcdef123456"):
        bundle_dir = self.records_dir / bundle_id
        bundle_dir.mkdir()
        
        intake_data = {
            "repository": "test-owner/test-repo",
            "repository_owner": "test-owner",
            "canonical_url": "https://github.com/test-owner/test-repo",
            "license": "MIT",
            "reviewed_commit_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "review_date": "2024-01-01",
            "files_examined": [
                {
                    "file_path": "src/main.py",
                    "line_ranges": ["10-50"]
                }
            ],
            "runtime_behavior_tested": False,
            "source_confidence": "HIGH"
        }
        
        with open(bundle_dir / "source-intake.json", "w", encoding="utf-8") as f:
            json.dump(intake_data, f)
            
        patterns_dir = bundle_dir / "patterns"
        patterns_dir.mkdir()
        
        pattern_data = {
            "name": "Test Pattern",
            "description": "A test pattern.",
            "source_file": "src/main.py",
            "line_range": "15-25",
            "classification": "REFERENCE_ONLY",
            "assigned_specialist": "cloak"
        }
        
        with open(patterns_dir / "test-pattern.json", "w", encoding="utf-8") as f:
            json.dump(pattern_data, f)
            
        return bundle_dir

    def test_valid_repository(self):
        """A properly formatted repository with a valid bundle should pass."""
        self._create_valid_bundle()
        failures = validate_repository(self.repo_root)
        self.assertEqual(len(failures), 0, f"Expected 0 failures, got {len(failures)}: {failures}")

    def test_missing_readme(self):
        """Missing records README should trigger a failure."""
        (self.records_dir / "README.md").unlink()
        failures = validate_repository(self.repo_root)
        self.assertTrue(any(f.target == "internal/artificer/records/README.md" for f in failures))

    def test_invalid_bundle_name(self):
        """Bundle name must match slugification of owner, repo, and sha12."""
        bundle_dir = self._create_valid_bundle("invalid-bundle-name")
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("does not match expected format" in f.reason for f in failures))

    def test_duplicate_keys_in_json(self):
        """JSON files with duplicate keys should fail."""
        bundle_dir = self._create_valid_bundle()
        # Manually write invalid JSON with duplicate key
        with open(bundle_dir / "source-intake.json", "w", encoding="utf-8") as f:
            f.write('{"repository": "owner/repo", "repository": "owner2/repo2"}')
            
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("duplicate JSON key 'repository'" in f.reason for f in failures))

    def test_missing_source_intake(self):
        """Missing source-intake.json should fail."""
        bundle_dir = self._create_valid_bundle()
        (bundle_dir / "source-intake.json").unlink()
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("source-intake.json is missing" in f.reason for f in failures))

    def test_source_intake_schema_violation(self):
        """Schema violations in source-intake.json should be caught."""
        bundle_dir = self._create_valid_bundle()
        with open(bundle_dir / "source-intake.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["source_confidence"] = "INVALID_ENUM"
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("is not one of the allowed enum values" in f.reason for f in failures))

    def test_invalid_canonical_url(self):
        """canonical_url must be a valid https URI without credentials/query/fragment."""
        bundle_dir = self._create_valid_bundle()
        with open(bundle_dir / "source-intake.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["canonical_url"] = "http://github.com/test-owner/test-repo" # wrong scheme
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("must use https scheme" in f.reason for f in failures))

    def test_line_range_not_covered(self):
        """Pattern line_range must be within files_examined line_ranges."""
        bundle_dir = self._create_valid_bundle()
        pattern_file = bundle_dir / "patterns" / "test-pattern.json"
        with open(pattern_file, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["line_range"] = "60-70" # Outside of 10-50
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("is not covered by any examined range" in f.reason for f in failures))

    def test_missing_license_implications(self):
        """Certain classifications require license_implications."""
        bundle_dir = self._create_valid_bundle()
        pattern_file = bundle_dir / "patterns" / "test-pattern.json"
        with open(pattern_file, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["classification"] = "ADAPTED_PATTERN"
            # Missing license_implications
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("'license_implications' is required for classification" in f.reason for f in failures))

    def test_invalid_pattern_filename(self):
        """Pattern filename must match slugified name."""
        bundle_dir = self._create_valid_bundle()
        pattern_file = bundle_dir / "patterns" / "test-pattern.json"
        pattern_file.rename(bundle_dir / "patterns" / "wrong-name.json")
        
        failures = validate_repository(self.repo_root)
        self.assertTrue(any("Pattern filename 'wrong-name.json' does not match expected" in f.reason for f in failures))

    def test_unsupported_schema_keyword(self):
        """Schemas containing unsupported validation keywords should cause a configuration error."""
        with open(self.schema_dir / "PATTERN_SCHEMA.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["allOf"] = [] # Unsupported keyword
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
        with self.assertRaises(ValidatorConfigurationError) as context:
            validate_repository(self.repo_root)
        self.assertTrue("unsupported validation keywords" in str(context.exception))

    def test_slugify(self):
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("test_name.123"), "test_name.123")
        self.assertEqual(slugify("!@#$"), "")
        self.assertEqual(slugify("-leading-trailing-"), "leading-trailing")

if __name__ == "__main__":
    unittest.main()
