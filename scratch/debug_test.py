import os
import sys
import json
from pathlib import Path
sys.path.insert(0, r"c:\+conductor\scripts")
from validate_artificer_records import validate_repository

repo = Path(r"c:\+conductor")
records_dir = repo / "internal/artificer/records"

# We'll just run validate_repository against the actual current state of +conductor
# since I haven't put anything in its records dir?
# No, let's create a temp dir and run validate_repository on it.

import tempfile
import shutil

temp_dir = tempfile.mkdtemp()
repo_root = Path(temp_dir)
schema_dir = repo_root / "internal" / "artificer"
schema_dir.mkdir(parents=True)
real_schema_dir = repo / "internal" / "artificer"
shutil.copy2(real_schema_dir / "SOURCE_INTAKE_SCHEMA.json", schema_dir / "SOURCE_INTAKE_SCHEMA.json")
shutil.copy2(real_schema_dir / "PATTERN_SCHEMA.json", schema_dir / "PATTERN_SCHEMA.json")
records_dir = schema_dir / "records"
records_dir.mkdir()
with open(records_dir / "README.md", "w", encoding="utf-8") as f:
    f.write("# Records Registry")

def _valid_intake():
    return {
        "repository": "test/repo",
        "repository_owner": "test",
        "canonical_url": "https://example.com/test/repo",
        "license": "MIT",
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

bundle = "test__repo__a1b2c3d4e5f6"

def setup_bundle():
    d = records_dir / bundle
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    with open(d / "source-intake.json", "w", encoding="utf-8") as f:
        json.dump(_valid_intake(), f)

print("--- test_pass_runtime_boolean_true_and_false ---")
setup_bundle()
i = _valid_intake()
i["runtime_behavior_tested"] = False
with open(records_dir / bundle / "source-intake.json", "w") as f: json.dump(i, f)
(records_dir / bundle / "patterns").mkdir()
failures = validate_repository(repo_root)
for f in failures: print(f.reason)

print("--- test_pass_omitted_default_branch ---")
setup_bundle()
i = _valid_intake()
if "default_branch" in i: del i["default_branch"]
with open(records_dir / bundle / "source-intake.json", "w") as f: json.dump(i, f)
(records_dir / bundle / "patterns").mkdir()
failures = validate_repository(repo_root)
for f in failures: print(f.reason)

print("--- test_pass_git_url_and_trailing_slash_url ---")
setup_bundle()
i = _valid_intake()
i["canonical_url"] = "https://example.com/test/repo.git/"
with open(records_dir / bundle / "source-intake.json", "w") as f: json.dump(i, f)
(records_dir / bundle / "patterns").mkdir()
failures = validate_repository(repo_root)
for f in failures: print(f.reason)

print("--- test_failure_missing_patterns_directory ---")
setup_bundle()
failures = validate_repository(repo_root)
for f in failures: print(f.reason)

shutil.rmtree(temp_dir)
