#!/usr/bin/env python3
"""Behavior coverage for Artificer Phase 4B governance-record validation."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_artificer_governance_records as validator  # noqa: E402


BUNDLE = "owner__repository__aaaaaaaaaaaa"
OTHER_BUNDLE = "owner__repository__bbbbbbbbbbbb"
SHA = "a" * 40
PATTERN_PATH = f"internal/artificer/records/{BUNDLE}/patterns/reference-pattern.json"
OTHER_PATTERN_PATH = (
    f"internal/artificer/records/{OTHER_BUNDLE}/patterns/reference-pattern.json"
)

PASSING_SCENARIOS = (
    "empty registries",
    "audit only",
    "audit plus decision",
    "complete chain",
    "compatible license with Governor NOT_REQUIRED",
    "required Governor review with Governor APPROVED",
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def update_json(path: Path, modify) -> None:
    data = read_json(path)
    modify(data)
    write_json(path, data)


def add_source_bundle(
    root: Path,
    bundle_id: str,
    *,
    repository: str = "owner/repository",
    reviewed_commit_sha: str = SHA,
    runtime_behavior_tested: bool = False,
) -> None:
    source = root / "internal/artificer/records" / bundle_id
    intake = {
        "repository": repository,
        "repository_owner": "owner",
        "canonical_url": f"https://example.test/{repository}",
        "license": "MIT",
        "default_branch": "main",
        "reviewed_commit_sha": reviewed_commit_sha,
        "review_date": "2026-07-01",
        "files_examined": [{"file_path": "src/example.py", "line_ranges": ["1-100"]}],
        "runtime_behavior_tested": runtime_behavior_tested,
        "source_confidence": "HIGH",
    }
    pattern = {
        "name": "Reference Pattern",
        "description": "Source-backed pattern.",
        "source_file": "src/example.py",
        "line_range": "10-20",
        "classification": "REFERENCE_ONLY",
        "assigned_specialist": "ponytail",
    }
    write_json(source / "source-intake.json", intake)
    write_json(source / "patterns/reference-pattern.json", pattern)


def fixture_repo(
    root: Path, chain: str = "complete", governor_required: bool = False
) -> dict[str, Path]:
    schemas = [
        "AUDIT_REPORT_SCHEMA.json",
        "GOVERNANCE_DECISION_SCHEMA.json",
        "EVOLUTION_PROPOSAL_SCHEMA.json",
        "PROMOTION_RECORD_SCHEMA.json",
        "SOURCE_INTAKE_SCHEMA.json",
        "PATTERN_SCHEMA.json",
    ]
    for schema in schemas:
        target = root / "internal/artificer" / schema
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "internal/artificer" / schema, target)
    for registry in ("records", "reviews", "decisions", "proposals", "promotions"):
        path = root / "internal/artificer" / registry
        path.mkdir(parents=True, exist_ok=True)
        (path / "README.md").write_text("registry\n", encoding="utf-8")
    add_source_bundle(root, BUNDLE)
    paths = {
        "audit": root / f"internal/artificer/reviews/{BUNDLE}/audit-report.json",
        "decision": root / f"internal/artificer/decisions/{BUNDLE}/reference-pattern.json",
        "proposal": root / "internal/artificer/proposals/proposal-1.json",
        "promotion": root / "internal/artificer/promotions/catalog-pattern.json",
    }
    if chain == "empty":
        return paths
    assessment = "GOVERNOR_REVIEW_REQUIRED" if governor_required else "COMPATIBLE"
    audit = {
        "schema_version": "1.0",
        "audit_report_id": "audit-1",
        "source_bundle_id": BUNDLE,
        "source_intake_path": f"internal/artificer/records/{BUNDLE}/source-intake.json",
        "source_repository": "owner/repository",
        "reviewed_commit_sha": SHA,
        "audit_date": "2026-07-02",
        "executive_summary": "Audit summary.",
        "findings": [
            {
                "finding_id": "finding-1",
                "pattern_record_path": PATTERN_PATH,
                "title": "Finding",
                "finding": "Observed behavior.",
                "recommendation": "Use concept only.",
                "assigned_specialist": "ponytail",
                "risk_level": "LOW",
                "evidence": [
                    {
                        "bucket": "SOURCE_CONFIRMED",
                        "source_file": "src/example.py",
                        "line_range": "10-20",
                        "summary": "Observed.",
                    }
                ],
            }
        ],
        "license_analysis": {
            "detected_license": "MIT",
            "compatibility_assessment": assessment,
            "governor_review_required": governor_required,
            "summary": "Recorded only.",
        },
        "security_review": {
            "external_execution_performed": False,
            "summary": "No external execution.",
        },
        "limitations": ["Static source evidence only."],
    }
    write_json(paths["audit"], audit)
    if chain == "audit":
        return paths
    governor_status = "APPROVED" if governor_required else "NOT_REQUIRED"
    decision = {
        "schema_version": "1.0",
        "decision_id": "decision-1",
        "source_bundle_id": BUNDLE,
        "pattern_record_path": PATTERN_PATH,
        "audit_report_id": "audit-1",
        "decision_status": "APPROVED",
        "assigned_specialist": "ponytail",
        "reviews": {
            reviewer: {
                "status": status,
                "rationale": "Reviewed.",
                "review_date": "2026-07-03",
            }
            for reviewer, status in {
                "arbiter": "APPROVED",
                "governor": governor_status,
                "steward": "APPROVED",
            }.items()
        },
        "maintainer_decision": {
            "status": "APPROVED",
            "rationale": "Approved.",
            "decision_date": "2026-07-03",
        },
        "implementation_restriction": "CONCEPT_ONLY",
        "decision_date": "2026-07-03",
    }
    write_json(paths["decision"], decision)
    if chain == "decision":
        return paths
    proposal = {
        "schema_version": "1.0",
        "proposal_id": "proposal-1",
        "title": "Proposal",
        "objective": "Adapt concept.",
        "source_audit_ids": ["audit-1"],
        "selected_patterns": [
            {
                "decision_id": "decision-1",
                "pattern_record_path": PATTERN_PATH,
                "target_component": "validator",
                "evolution_mechanism": "CONCEPTUAL_ADAPTATION",
                "owner_specialist": "ponytail",
                "rationale": "Approved concept.",
            }
        ],
        "verification_plan": "Run tests.",
        "governance_handoff": "Maintainer review.",
        "proposal_status": "APPROVED",
    }
    write_json(paths["proposal"], proposal)
    if chain == "proposal":
        return paths
    promotion = {
        "schema_version": "1.0",
        "promotion_id": "promotion-1",
        "catalog_pattern_id": "catalog-pattern",
        "decision_id": "decision-1",
        "proposal_id": "proposal-1",
        "source_bundle_id": BUNDLE,
        "pattern_record_path": PATTERN_PATH,
        "approval_date": "2026-07-04",
        "promotion_status": "APPROVED",
        "assigned_specialist": "ponytail",
        "source_traceability": {
            "repository": "owner/repository",
            "reviewed_commit_sha": SHA,
            "source_file": "src/example.py",
            "line_range": "10-20",
        },
        "license_and_attribution": {
            "original_license": "MIT",
            "attribution_required": True,
            "summary": "Retain attribution.",
        },
        "automatic_promotion": False,
    }
    write_json(paths["promotion"], promotion)
    return paths


class GovernanceRecordsTests(unittest.TestCase):
    def with_repo(self, chain: str = "complete", governor_required: bool = False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        return root, fixture_repo(root, chain, governor_required)

    def assert_failure(
        self,
        failures: list[validator.ValidationFailure],
        *,
        target_contains: str,
        reason_contains: str,
        remediation_contains: str | None = None,
    ) -> None:
        self.assertTrue(failures, "Expected validation to fail")

        matching = [
            failure
            for failure in failures
            if target_contains in failure.target
            and reason_contains in failure.reason
            and (
                remediation_contains is None
                or remediation_contains in failure.remediation
            )
        ]

        self.assertTrue(
            matching,
            (
                "Expected a matching validation failure.\n"
                f"target_contains={target_contains!r}\n"
                f"reason_contains={reason_contains!r}\n"
                f"remediation_contains={remediation_contains!r}\n"
                "Actual failures:\n"
                + "\n".join(
                    f"{failure.target}: {failure.reason} | "
                    f"{failure.remediation}"
                    for failure in failures
                )
            ),
        )

    def assert_validation_failure(
        self,
        root: Path,
        *,
        target_contains: str,
        reason_contains: str,
        remediation_contains: str | None = None,
    ) -> None:
        self.assert_failure(
            validator.validate_repository(root),
            target_contains=target_contains,
            reason_contains=reason_contains,
            remediation_contains=remediation_contains,
        )

    def capture_main(self, argv: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = validator.main(argv)
        return exit_code, stdout.getvalue() + stderr.getvalue()

    def assert_relative_output(self, output: str, root: Path, expected_rel_path: str) -> None:
        self.assertIn(expected_rel_path, output)
        self.assertNotIn(str(root), output)
        self.assertNotIn(str(root.resolve()), output)

    def test_passing_empty_and_progressive_chains(self):
        cases = [
            ("empty registries", "empty", False),
            ("audit only", "audit", False),
            ("audit plus decision", "decision", False),
            ("complete chain", "complete", False),
            ("compatible license with Governor NOT_REQUIRED", "complete", False),
            ("required Governor review with Governor APPROVED", "complete", True),
        ]
        for name, chain, governor_required in cases:
            with self.subTest(name=name):
                root, _ = self.with_repo(chain, governor_required)
                self.assertEqual([], validator.validate_repository(root))

    def test_registry_layout_failures(self):
        cases = [
            {
                "name": "missing README",
                "mutate": lambda root, paths: (root / "internal/artificer/reviews/README.md").unlink(),
                "target_contains": "internal/artificer/reviews/README.md",
                "reason_contains": "Registry README.md is missing",
                "remediation_contains": "Create a regular",
            },
            {
                "name": "unexpected root file",
                "mutate": lambda root, paths: (root / "internal/artificer/reviews/unexpected.txt").write_text("x", encoding="utf-8"),
                "target_contains": "internal/artificer/reviews/unexpected.txt",
                "reason_contains": "Registry root permits only bundle directories",
                "remediation_contains": "Move the record",
            },
            {
                "name": "invalid bundle directory",
                "mutate": lambda root, paths: (root / "internal/artificer/reviews/invalid").mkdir(),
                "target_contains": "internal/artificer/reviews/invalid",
                "reason_contains": "Bundle directory name is invalid",
                "remediation_contains": "12-character-lowercase-sha",
            },
            {
                "name": "empty bundle directory",
                "mutate": lambda root, paths: (root / "internal/artificer/reviews/owner__empty__aaaaaaaaaaaa").mkdir(),
                "target_contains": "internal/artificer/reviews/owner__empty__aaaaaaaaaaaa",
                "reason_contains": "Bundle directory is empty",
                "remediation_contains": "required governance JSON record",
            },
            {
                "name": "nested directory",
                "mutate": lambda root, paths: (root / f"internal/artificer/reviews/{BUNDLE}/nested").mkdir(),
                "target_contains": f"internal/artificer/reviews/{BUNDLE}/nested",
                "reason_contains": "Nested directories and symbolic links are not permitted",
                "remediation_contains": "regular JSON file",
            },
            {
                "name": "non-JSON file",
                "mutate": lambda root, paths: (root / f"internal/artificer/decisions/{BUNDLE}/bad.txt").write_text("x", encoding="utf-8"),
                "target_contains": f"internal/artificer/decisions/{BUNDLE}/bad.txt",
                "reason_contains": "Decision records must be named <pattern-slug>.json",
                "remediation_contains": "Rename the record",
            },
            {
                "name": "proposal directory instead of JSON file",
                "mutate": lambda root, paths: (root / "internal/artificer/proposals/bad").mkdir(),
                "target_contains": "internal/artificer/proposals/bad",
                "reason_contains": "Registry permits only regular <safe-id>.json files",
                "remediation_contains": "Replace directories",
            },
            {
                "name": "promotion directory instead of JSON file",
                "mutate": lambda root, paths: (root / "internal/artificer/promotions/bad").mkdir(),
                "target_contains": "internal/artificer/promotions/bad",
                "reason_contains": "Registry permits only regular <safe-id>.json files",
                "remediation_contains": "Replace directories",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo()
                case["mutate"](root, paths)
                self.assert_validation_failure(
                    root,
                    target_contains=case["target_contains"],
                    reason_contains=case["reason_contains"],
                    remediation_contains=case["remediation_contains"],
                )

    def test_find_casefold_duplicate_helper(self):
        self.assertEqual(
            "Proposal-A.json",
            validator.find_casefold_duplicate(
                ["proposal-a.json", "Proposal-A.json"]
            ),
        )
        self.assertIsNone(
            validator.find_casefold_duplicate(["proposal-a.json", "proposal-b.json"])
        )

    def test_registry_case_insensitive_collision_end_to_end_when_supported(self):
        root1, paths1 = self.with_repo("proposal")
        root2, paths2 = self.with_repo("proposal")

        probe = root1 / "CaseProbe"
        probe.write_text("probe", encoding="utf-8")
        case_sensitive = not (root1 / "caseprobe").exists()
        probe.unlink()

        if not case_sensitive:
            self.skipTest(
                "filesystem is case-insensitive in the temporary directory"
            )

        def create_collision_fixture(
            root: Path,
            proposal_path: Path,
            order: list[str],
        ) -> None:
            content = proposal_path.read_bytes()
            proposal_path.unlink()

            for filename in order:
                proposal_path.with_name(filename).write_bytes(content)

        create_collision_fixture(
            root1,
            paths1["proposal"],
            ["proposal-1.json", "Proposal-1.json"],
        )
        create_collision_fixture(
            root2,
            paths2["proposal"],
            ["Proposal-1.json", "proposal-1.json"],
        )

        failures1 = validator.validate_repository(root1)
        failures2 = validator.validate_repository(root2)

        self.assert_failure(
            failures1,
            target_contains="proposal-1.json",
            reason_contains="Case-insensitive filename collision",
            remediation_contains="case sensitivity",
        )

        rendered1 = [
            (item.target, item.reason, item.remediation)
            for item in failures1
        ]
        rendered2 = [
            (item.target, item.reason, item.remediation)
            for item in failures2
        ]

        self.assertEqual(rendered1, rendered2)

    def test_registry_symlink_fails_when_supported(self):
        root, _ = self.with_repo("audit")
        link = root / "internal/artificer/reviews/link"
        try:
            link.symlink_to(root / f"internal/artificer/reviews/{BUNDLE}", target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symbolic links unsupported: {exc}")
        self.assert_validation_failure(
            root,
            target_contains="internal/artificer/reviews/link",
            reason_contains="Symbolic links are not permitted in governance registries",
            remediation_contains="Replace the symbolic link",
        )

    def test_registry_ancestor_symlinks_fail_when_supported(self):
        root, _ = self.with_repo("audit")
        reviews_dir = root / "internal/artificer/reviews"
        temp_reviews = root / "temp_reviews"
        shutil.move(str(reviews_dir), str(temp_reviews))
        try:
            reviews_dir.symlink_to(temp_reviews, target_is_directory=True)
        except OSError as exc:
            shutil.move(str(temp_reviews), str(reviews_dir))
            self.skipTest(f"symbolic links unsupported: {exc}")
        self.assert_validation_failure(
            root,
            target_contains="internal/artificer/reviews",
            reason_contains="Registry directory is missing or is a symbolic link",
            remediation_contains="Create the required internal/artificer/reviews/ directory as a regular directory.",
        )
        reviews_dir.unlink()
        shutil.move(str(temp_reviews), str(reviews_dir))

        records_dir = root / "internal/artificer/records"
        temp_records = root / "temp_records"
        shutil.move(str(records_dir), str(temp_records))
        records_dir.symlink_to(temp_records, target_is_directory=True)
        self.assert_validation_failure(
            root,
            target_contains="internal/artificer/records",
            reason_contains=(
                "Source records directory must not be a symbolic link"
            ),
            remediation_contains="regular repository directory",
        )
        records_dir.unlink()
        shutil.move(str(temp_records), str(records_dir))

        patterns_dir = records_dir / BUNDLE / "patterns"
        temp_patterns = root / "temp_patterns"
        shutil.move(str(patterns_dir), str(temp_patterns))
        patterns_dir.symlink_to(temp_patterns, target_is_directory=True)
        self.assert_validation_failure(
            root,
            target_contains=(
                f"internal/artificer/records/{BUNDLE}/patterns"
            ),
            reason_contains=(
                "Source pattern directory must not be a symbolic link"
            ),
            remediation_contains="regular directory",
        )
        patterns_dir.unlink()
        shutil.move(str(temp_patterns), str(patterns_dir))

    def test_record_safety_schema_and_date_failures(self):
        cases = [
            {
                "name": "empty file",
                "mutate": lambda path: path.write_bytes(b""),
                "reason_contains": "file is empty",
            },
            {
                "name": "malformed JSON",
                "mutate": lambda path: path.write_text("{", encoding="utf-8"),
                "reason_contains": "malformed JSON",
            },
            {
                "name": "duplicate key",
                "mutate": lambda path: path.write_text('{"x": 1, "x": 2}', encoding="utf-8"),
                "reason_contains": "duplicate JSON key",
            },
            {
                "name": "non-UTF-8",
                "mutate": lambda path: path.write_bytes(b"\xff"),
                "reason_contains": "file is not valid UTF-8",
            },
            {
                "name": "oversized file",
                "mutate": lambda path: path.write_bytes(b"x" * (validator.MAX_FILE_SIZE + 1)),
                "reason_contains": "file exceeds maximum size",
            },
            {
                "name": "top-level array",
                "mutate": lambda path: path.write_text("[]", encoding="utf-8"),
                "reason_contains": "top-level JSON value must be an object",
            },
            {
                "name": "missing required field",
                "mutate": lambda path: update_json(path, lambda data: data.pop("audit_date")),
                "reason_contains": "missing required field 'audit_date'",
            },
            {
                "name": "wrong type",
                "mutate": lambda path: update_json(path, lambda data: data.__setitem__("findings", {})),
                "reason_contains": "findings: expected array, got dict",
            },
            {
                "name": "invalid enum",
                "mutate": lambda path: update_json(path, lambda data: data.__setitem__("schema_version", "9")),
                "reason_contains": "schema_version: value '9' is not one of the allowed enum values",
            },
            {
                "name": "unexpected property",
                "mutate": lambda path: update_json(path, lambda data: data.__setitem__("extra", True)),
                "reason_contains": "unexpected additional property 'extra'",
            },
            {
                "name": "invalid date",
                "mutate": lambda path: update_json(path, lambda data: data.__setitem__("audit_date", "2026-02-30")),
                "reason_contains": "audit_date: value '2026-02-30' is not a valid ISO date",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("audit")
                case["mutate"](paths["audit"])
                self.assert_validation_failure(
                    root,
                    target_contains="audit-report.json",
                    reason_contains=case["reason_contains"],
                    remediation_contains="Fix the JSON record"
                    if case["name"] in {"empty file", "malformed JSON", "duplicate key", "non-UTF-8", "oversized file", "top-level array"}
                    else None,
                )

    def test_audit_cross_record_failures(self):
        cases = [
            {
                "name": "bundle mismatch",
                "mutate": lambda root, paths: (
                    add_source_bundle(root, OTHER_BUNDLE),
                    update_json(
                        paths["audit"],
                        lambda data: (
                            data.__setitem__("source_bundle_id", OTHER_BUNDLE),
                            data.__setitem__("source_intake_path", f"internal/artificer/records/{OTHER_BUNDLE}/source-intake.json"),
                            data["findings"][0].__setitem__("pattern_record_path", OTHER_PATTERN_PATH),
                        ),
                    ),
                ),
                "reason_contains": "source_bundle_id does not match the audit-report directory",
                "remediation_contains": "containing bundle ID",
            },
            {
                "name": "missing source bundle",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data.__setitem__("source_bundle_id", "missing__bundle__aaaaaaaaaaaa")),
                "reason_contains": "Source bundle 'missing__bundle__aaaaaaaaaaaa' is missing",
                "remediation_contains": "Restore a valid Phase 3 source bundle",
            },
            {
                "name": "wrong source-intake path",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data.__setitem__("source_intake_path", "wrong.json")),
                "reason_contains": "source_intake_path does not exactly reference the source bundle intake",
                "remediation_contains": "Set source_intake_path",
            },
            {
                "name": "repository mismatch",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data.__setitem__("source_repository", "other/repository")),
                "reason_contains": "source_repository does not match source-intake.json",
                "remediation_contains": "Copy repository exactly",
            },
            {
                "name": "SHA mismatch",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data.__setitem__("reviewed_commit_sha", "b" * 40)),
                "reason_contains": "reviewed_commit_sha does not match source-intake.json",
                "remediation_contains": "reviewed commit SHA exactly",
            },
            {
                "name": "audit date before intake review date",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data.__setitem__("audit_date", "2026-06-30")),
                "reason_contains": "audit_date precedes the source intake review_date",
                "remediation_contains": "on or after the source intake review_date",
            },
            {
                "name": "missing pattern",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0].__setitem__("pattern_record_path", PATTERN_PATH.replace("reference-pattern", "missing-pattern"))),
                "reason_contains": "pattern_record_path does not reference an existing pattern in the same source bundle",
                "remediation_contains": "Reference a pattern JSON record",
            },
            {
                "name": "cross-bundle pattern",
                "mutate": lambda root, paths: (
                    add_source_bundle(root, OTHER_BUNDLE),
                    update_json(paths["audit"], lambda data: data["findings"][0].__setitem__("pattern_record_path", OTHER_PATTERN_PATH)),
                ),
                "reason_contains": "pattern_record_path does not reference an existing pattern in the same source bundle",
                "remediation_contains": "Reference a pattern JSON record",
            },
            {
                "name": "duplicate finding ID",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"].append(dict(data["findings"][0]))),
                "reason_contains": "Duplicate finding_id 'finding-1'",
                "remediation_contains": "Use unique finding IDs",
            },
            {
                "name": "empty evidence",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0].__setitem__("evidence", [])),
                "reason_contains": "evidence must contain at least one item",
                "remediation_contains": "Add at least one traceable evidence item",
            },
            {
                "name": "evidence file not examined",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0]["evidence"][0].__setitem__("source_file", "other.py")),
                "reason_contains": "source_file is not in files_examined",
                "remediation_contains": "Use a source file listed",
            },
            {
                "name": "evidence range not covered",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0]["evidence"][0].__setitem__("line_range", "101-102")),
                "reason_contains": "line_range is outside files_examined coverage",
                "remediation_contains": "covered by source-intake.json files_examined",
            },
            {
                "name": "runtime evidence without authorization",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0]["evidence"][0].__setitem__("bucket", "RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION")),
                "reason_contains": "Runtime-confirmed evidence requires source intake runtime_behavior_tested: true",
                "remediation_contains": "Use a non-runtime evidence bucket",
            },
            {
                "name": "specialist mismatch",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0].__setitem__("assigned_specialist", "cloak")),
                "reason_contains": "assigned_specialist does not match the source pattern",
                "remediation_contains": "Use the source pattern assigned_specialist exactly",
            },
            {
                "name": "Artificer assignment",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"][0].__setitem__("assigned_specialist", "artificer")),
                "reason_contains": "must not assign Artificer",
                "remediation_contains": "Assign a specialist",
            },
            {
                "name": "license mismatch",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["license_analysis"].__setitem__("detected_license", "Apache-2.0")),
                "reason_contains": "license_analysis.detected_license does not match source intake license",
                "remediation_contains": "Copy the license exactly",
            },
            {
                "name": "Governor-review Boolean inconsistency",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["license_analysis"].__setitem__("governor_review_required", True)),
                "reason_contains": "license compatibility assessment and governor_review_required are inconsistent",
                "remediation_contains": "Set governor_review_required false only for COMPATIBLE",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("audit")
                case["mutate"](root, paths)
                self.assert_validation_failure(
                    root,
                    target_contains="audit-report.json",
                    reason_contains=case["reason_contains"],
                    remediation_contains=case["remediation_contains"],
                )

    def test_decision_cross_record_and_status_failures(self):
        def duplicate_decision(paths: dict[str, Path]) -> None:
            copy_path = paths["decision"].with_name("another.json")
            data = read_json(paths["decision"])
            data["decision_id"] = "decision-1"
            write_json(copy_path, data)

        cases = [
            {
                "name": "filename mismatch",
                "mutate": lambda root, paths: paths["decision"].rename(paths["decision"].with_name("wrong.json")),
                "target_contains": "wrong.json",
                "reason_contains": "Decision filename does not match the referenced pattern filename",
                "remediation_contains": "Rename the decision file",
            },
            {
                "name": "missing audit",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data.__setitem__("audit_report_id", "missing")),
                "reason_contains": "audit_report_id does not resolve to an audit report in this source bundle",
                "remediation_contains": "Reference an existing audit report",
            },
            {
                "name": "missing corresponding finding",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: data["findings"].clear()),
                "reason_contains": "Referenced audit report has no finding for pattern_record_path",
                "remediation_contains": "Add a matching audit finding",
            },
            {
                "name": "duplicate decision ID",
                "mutate": lambda root, paths: duplicate_decision(paths),
                "target_contains": "reference-pattern.json",
                "reason_contains": "Duplicate case-insensitive decision_id 'decision-1'",
                "remediation_contains": "Use a unique decision_id",
            },
            {
                "name": "specialist mismatch",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data.__setitem__("assigned_specialist", "cloak")),
                "reason_contains": "assigned_specialist does not match the source pattern",
                "remediation_contains": "Use the source pattern assigned_specialist exactly",
            },
            {
                "name": "review date after decision",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["reviews"]["arbiter"].__setitem__("review_date", "2026-07-04")),
                "reason_contains": "reviews.arbiter.review_date is after decision_date",
                "remediation_contains": "on or before decision_date",
            },
            {
                "name": "Maintainer date mismatch",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["maintainer_decision"].__setitem__("decision_date", "2026-07-04")),
                "reason_contains": "maintainer_decision.decision_date must equal decision_date",
                "remediation_contains": "top-level decision_date",
            },
            {
                "name": "decision before audit",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: (data.__setitem__("decision_date", "2026-07-01"), data["maintainer_decision"].__setitem__("decision_date", "2026-07-01"))),
                "reason_contains": "decision_date precedes the audit_date",
                "remediation_contains": "on or after the audit_date",
            },
            {
                "name": "decision/Maintainer status mismatch",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["maintainer_decision"].__setitem__("status", "REJECTED")),
                "reason_contains": "decision_status must equal maintainer_decision.status",
                "remediation_contains": "statuses identical",
            },
            {
                "name": "final decision with pending reviewer",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["reviews"]["arbiter"].__setitem__("status", "PENDING")),
                "reason_contains": "Final decision retains a PENDING reviewer",
                "remediation_contains": "Complete reviewer statuses",
            },
            {
                "name": "approval with revision-required reviewer",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["reviews"]["arbiter"].__setitem__("status", "REVISION_REQUIRED")),
                "reason_contains": "APPROVED requires arbiter APPROVED",
                "remediation_contains": "Set reviews.arbiter.status to APPROVED",
            },
            {
                "name": "approval with blocked reviewer",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data["reviews"]["arbiter"].__setitem__("status", "BLOCKED")),
                "reason_contains": "APPROVED requires arbiter APPROVED",
                "remediation_contains": "Set reviews.arbiter.status to APPROVED",
            },
            {
                "name": "missing required Governor approval",
                "mutate": lambda root, paths: update_json(paths["audit"], lambda data: (data["license_analysis"].__setitem__("compatibility_assessment", "GOVERNOR_REVIEW_REQUIRED"), data["license_analysis"].__setitem__("governor_review_required", True))),
                "reason_contains": "Governor may not be NOT_REQUIRED when the audit requires Governor review",
                "remediation_contains": "Record Governor APPROVED",
            },
            {
                "name": "approval with implementation blocked",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data.__setitem__("implementation_restriction", "IMPLEMENTATION_BLOCKED")),
                "reason_contains": "APPROVED decision has a blocking reviewer status or implementation restriction",
                "remediation_contains": "Resolve blocking review results",
            },
            {
                "name": "rejected without implementation blocked",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: (data.__setitem__("decision_status", "REJECTED"), data["maintainer_decision"].__setitem__("status", "REJECTED"))),
                "reason_contains": "REJECTED decisions require IMPLEMENTATION_BLOCKED",
                "remediation_contains": "Set implementation_restriction to IMPLEMENTATION_BLOCKED",
            },
            {
                "name": "blocked without implementation blocked",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: (data.__setitem__("decision_status", "BLOCKED"), data["maintainer_decision"].__setitem__("status", "BLOCKED"))),
                "reason_contains": "BLOCKED decisions require IMPLEMENTATION_BLOCKED",
                "remediation_contains": "Set implementation_restriction to IMPLEMENTATION_BLOCKED",
            },
            {
                "name": "approved out-of-scope pattern",
                "mutate": lambda root, paths: update_json(root / f"internal/artificer/records/{BUNDLE}/patterns/reference-pattern.json", lambda data: data.__setitem__("classification", "OUT_OF_SCOPE")),
                "reason_contains": "OUT_OF_SCOPE patterns must not receive APPROVED decisions",
                "remediation_contains": "Use a non-approved decision status",
            },
            {
                "name": "reference-only approval without concept-only restriction",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data.__setitem__("implementation_restriction", "FRESH_IMPLEMENTATION_REQUIRED")),
                "reason_contains": "Approved REFERENCE_ONLY patterns require CONCEPT_ONLY",
                "remediation_contains": "Set implementation_restriction to CONCEPT_ONLY",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("decision")
                case["mutate"](root, paths)
                self.assert_validation_failure(
                    root,
                    target_contains=case.get(
                        "target_contains", "reference-pattern.json"
                    ),
                    reason_contains=case["reason_contains"],
                    remediation_contains=case["remediation_contains"],
                )

    def test_proposal_failures(self):
        cases = [
            {
                "name": "filename mismatch",
                "mutate": lambda root, paths: paths["proposal"].rename(paths["proposal"].with_name("wrong.json")),
                "target_contains": "wrong.json",
                "reason_contains": "Proposal filename does not match proposal_id",
                "remediation_contains": "Rename the file",
            },
            {
                "name": "empty audit list",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("source_audit_ids", [])),
                "reason_contains": "source_audit_ids must contain at least one audit ID",
                "remediation_contains": "Add one or more",
            },
            {
                "name": "duplicate audit ID",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("source_audit_ids", ["audit-1", "audit-1"])),
                "reason_contains": "source_audit_ids contains duplicate audit IDs",
                "remediation_contains": "Remove duplicate",
            },
            {
                "name": "missing audit",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("source_audit_ids", ["missing"])),
                "reason_contains": "source_audit_id 'missing' does not resolve",
                "remediation_contains": "Reference an existing audit_report_id",
            },
            {
                "name": "empty selected-pattern list",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("selected_patterns", [])),
                "reason_contains": "selected_patterns must contain at least one item",
                "remediation_contains": "Add an approved decision",
            },
            {
                "name": "duplicate decision",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("selected_patterns", data["selected_patterns"] * 2)),
                "reason_contains": "selected_patterns[1].decision_id is duplicated",
                "remediation_contains": "Select each decision only once",
            },
            {
                "name": "duplicate pattern",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("selected_patterns", data["selected_patterns"] * 2)),
                "reason_contains": "selected_patterns[1].pattern_record_path is duplicated",
                "remediation_contains": "Select each pattern only once",
            },
            {
                "name": "missing decision",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("decision_id", "missing")),
                "reason_contains": "selected_patterns[0].decision_id does not resolve",
                "remediation_contains": "Reference an existing approved decision",
            },
            {
                "name": "non-approved decision",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: (data.__setitem__("decision_status", "REJECTED"), data["maintainer_decision"].__setitem__("status", "REJECTED"), data.__setitem__("implementation_restriction", "IMPLEMENTATION_BLOCKED"))),
                "reason_contains": "selected_patterns[0] must reference an approved non-blocked decision",
                "remediation_contains": "decision_status APPROVED",
            },
            {
                "name": "audit omitted from source-audit IDs",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("source_audit_ids", ["audit-2"])),
                "reason_contains": "selected_patterns[0] decision audit is absent from source_audit_ids",
                "remediation_contains": "Add the decision audit_report_id",
            },
            {
                "name": "pattern mismatch",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("pattern_record_path", "wrong.json")),
                "reason_contains": "selected_patterns[0].pattern_record_path does not match decision",
                "remediation_contains": "Copy pattern_record_path exactly",
            },
            {
                "name": "specialist mismatch",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("owner_specialist", "cloak")),
                "reason_contains": "selected_patterns[0].owner_specialist does not match decision",
                "remediation_contains": "Use the decision assigned_specialist",
            },
            {
                "name": "Artificer owner",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("owner_specialist", "artificer")),
                "reason_contains": "must not assign Artificer",
                "remediation_contains": "Assign a specialist",
            },
            {
                "name": "invalid conceptual mechanism",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("evolution_mechanism", "SAFE_REWRITE")),
                "reason_contains": "CONCEPT_ONLY decisions permit only CONCEPTUAL_ADAPTATION",
                "remediation_contains": "Use evolution_mechanism CONCEPTUAL_ADAPTATION",
            },
            {
                "name": "invalid fresh-implementation pairing",
                "mutate": lambda root, paths: (
                    update_json(paths["decision"], lambda data: data.__setitem__("implementation_restriction", "FRESH_IMPLEMENTATION_REQUIRED")),
                    update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("evolution_mechanism", "DIRECT_REUSE_REVIEW_REQUIRED")),
                ),
                "reason_contains": "FRESH_IMPLEMENTATION_REQUIRED must not use DIRECT_REUSE_REVIEW_REQUIRED",
                "remediation_contains": "Use SAFE_REWRITE or CONCEPTUAL_ADAPTATION",
            },
            {
                "name": "invalid direct-reuse pairing",
                "mutate": lambda root, paths: (
                    update_json(paths["decision"], lambda data: data.__setitem__("implementation_restriction", "CODE_REUSE_REVIEW_REQUIRED")),
                    update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("evolution_mechanism", "DIRECT_REUSE_REVIEW_REQUIRED")),
                ),
                "reason_contains": "DIRECT_REUSE_REVIEW_REQUIRED requires a code-reuse decision and source classification",
                "remediation_contains": "Use CODE_REUSE_REVIEW_REQUIRED",
            },
            {
                "name": "invalid test-corpus pairing",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"][0].__setitem__("evolution_mechanism", "TEST_CORPUS_ADAPTATION")),
                "reason_contains": "TEST_CORPUS_ADAPTATION requires a TEST_CORPUS_CANDIDATE source pattern",
                "remediation_contains": "Use a test-corpus candidate pattern",
            },
            {
                "name": "blocked decision selection",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: data.__setitem__("implementation_restriction", "IMPLEMENTATION_BLOCKED")),
                "reason_contains": "selected_patterns[0] must reference an approved non-blocked decision",
                "remediation_contains": "decision_status APPROVED",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("proposal")
                case["mutate"](root, paths)
                self.assert_validation_failure(
                    root,
                    target_contains=case.get("target_contains", "proposal-1.json"),
                    reason_contains=case["reason_contains"],
                    remediation_contains=case["remediation_contains"],
                )

    def test_promotion_failures(self):
        def duplicate_promotion(paths: dict[str, Path]) -> None:
            copy_path = paths["promotion"].with_name("another.json")
            data = read_json(paths["promotion"])
            data["catalog_pattern_id"] = "another"
            write_json(copy_path, data)

        cases = [
            {
                "name": "filename mismatch",
                "mutate": lambda root, paths: paths["promotion"].rename(paths["promotion"].with_name("wrong.json")),
                "target_contains": "wrong.json",
                "reason_contains": "Promotion filename does not match catalog_pattern_id",
                "remediation_contains": "Rename the file",
            },
            {
                "name": "duplicate promotion ID",
                "mutate": lambda root, paths: duplicate_promotion(paths),
                "target_contains": "catalog-pattern.json",
                "reason_contains": "Duplicate case-insensitive promotion_id 'promotion-1'",
                "remediation_contains": "Use a unique promotion_id",
            },
            {
                "name": "missing decision",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("decision_id", "missing")),
                "reason_contains": "decision_id must resolve to an approved decision",
                "remediation_contains": "Reference an existing approved governance decision",
            },
            {
                "name": "missing proposal",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("proposal_id", "missing")),
                "reason_contains": "proposal_id must resolve to an approved proposal",
                "remediation_contains": "Reference an existing approved evolution proposal",
            },
            {
                "name": "non-approved decision",
                "mutate": lambda root, paths: update_json(paths["decision"], lambda data: (data.__setitem__("decision_status", "REJECTED"), data["maintainer_decision"].__setitem__("status", "REJECTED"), data.__setitem__("implementation_restriction", "IMPLEMENTATION_BLOCKED"))),
                "reason_contains": "decision_id must resolve to an approved decision",
                "remediation_contains": "Reference an existing approved governance decision",
            },
            {
                "name": "non-approved proposal",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data.__setitem__("proposal_status", "REJECTED")),
                "reason_contains": "proposal_id must resolve to an approved proposal",
                "remediation_contains": "Reference an existing approved evolution proposal",
            },
            {
                "name": "proposal missing the selected pair",
                "mutate": lambda root, paths: update_json(paths["proposal"], lambda data: data["selected_patterns"].clear()),
                "reason_contains": "Proposal does not contain the exact decision and pattern pair",
                "remediation_contains": "Select the referenced decision and pattern",
            },
            {
                "name": "bundle mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("source_bundle_id", OTHER_BUNDLE)),
                "reason_contains": "source_bundle_id does not match the decision",
                "remediation_contains": "Copy source_bundle_id exactly",
            },
            {
                "name": "pattern mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("pattern_record_path", "wrong.json")),
                "reason_contains": "pattern_record_path does not match the decision",
                "remediation_contains": "Copy pattern_record_path exactly",
            },
            {
                "name": "specialist mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("assigned_specialist", "cloak")),
                "reason_contains": "assigned_specialist does not match the decision",
                "remediation_contains": "Copy assigned_specialist exactly",
            },
            {
                "name": "repository mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data["source_traceability"].__setitem__("repository", "other/repo")),
                "reason_contains": "source_traceability.repository does not match source records",
                "remediation_contains": "Copy source repository exactly",
            },
            {
                "name": "SHA mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data["source_traceability"].__setitem__("reviewed_commit_sha", "b" * 40)),
                "reason_contains": "source_traceability.reviewed_commit_sha does not match source records",
                "remediation_contains": "Copy source reviewed_commit_sha exactly",
            },
            {
                "name": "source-file mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data["source_traceability"].__setitem__("source_file", "other.py")),
                "reason_contains": "source_traceability.source_file does not match source records",
                "remediation_contains": "Copy source source_file exactly",
            },
            {
                "name": "line-range mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data["source_traceability"].__setitem__("line_range", "1-2")),
                "reason_contains": "source_traceability.line_range does not match source records",
                "remediation_contains": "Copy source line_range exactly",
            },
            {
                "name": "license mismatch",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data["license_and_attribution"].__setitem__("original_license", "Apache-2.0")),
                "reason_contains": "license_and_attribution.original_license does not match source intake",
                "remediation_contains": "Copy the source intake license exactly",
            },
            {
                "name": "approval before decision date",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("approval_date", "2026-07-01")),
                "reason_contains": "approval_date precedes the governance decision date",
                "remediation_contains": "on or after decision_date",
            },
            {
                "name": "automatic promotion set to true",
                "mutate": lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("automatic_promotion", True)),
                "reason_contains": "automatic_promotion must be false",
                "remediation_contains": "Set automatic_promotion to false",
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo()
                case["mutate"](root, paths)
                self.assert_validation_failure(
                    root,
                    target_contains=case.get("target_contains", "catalog-pattern.json"),
                    reason_contains=case["reason_contains"],
                    remediation_contains=case["remediation_contains"],
                )

    def test_cli_valid_repository_returns_zero(self):
        root, _ = self.with_repo()
        exit_code, output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(0, exit_code)
        self.assertIn("Validation Passed: All Artificer governance records are valid.", output)
        self.assert_relative_output(output, root, "[7] Summary")

    def test_cli_record_violation_returns_one_with_relative_output(self):
        root, paths = self.with_repo("audit")
        update_json(paths["audit"], lambda data: data.__setitem__("source_repository", "wrong/repository"))
        exit_code, output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(1, exit_code)
        self.assertIn("[FAIL]", output)
        self.assertIn("source_repository does not match source-intake.json", output)
        self.assert_relative_output(output, root, f"internal/artificer/reviews/{BUNDLE}/audit-report.json")

    def test_cli_missing_schema_returns_two_with_relative_output(self):
        root, _ = self.with_repo()
        (root / "internal/artificer/AUDIT_REPORT_SCHEMA.json").unlink()
        exit_code, output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(2, exit_code)
        self.assertIn("[FAIL] Configuration error:", output)
        self.assertIn("Schema file missing: internal/artificer/AUDIT_REPORT_SCHEMA.json", output)
        self.assert_relative_output(output, root, "internal/artificer/AUDIT_REPORT_SCHEMA.json")

    def test_cli_malformed_schema_returns_two_with_relative_output(self):
        root, _ = self.with_repo()
        (root / "internal/artificer/AUDIT_REPORT_SCHEMA.json").write_text("{", encoding="utf-8")
        exit_code, output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(2, exit_code)
        self.assertIn("[FAIL] Configuration error:", output)
        self.assertIn("Schema file invalid: internal/artificer/AUDIT_REPORT_SCHEMA.json", output)
        self.assertIn("malformed JSON", output)
        self.assert_relative_output(output, root, "internal/artificer/AUDIT_REPORT_SCHEMA.json")

    def test_cli_unsupported_schema_configuration_returns_two_with_relative_output(self):
        root, _ = self.with_repo()
        schema_path = root / "internal/artificer/AUDIT_REPORT_SCHEMA.json"
        update_json(schema_path, lambda data: data.__setitem__("unsupported_keyword", True))
        exit_code, output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(2, exit_code)
        self.assertIn("[FAIL] Configuration error:", output)
        self.assertIn("unsupported keyword 'unsupported_keyword'", output)
        self.assert_relative_output(output, root, "internal/artificer/AUDIT_REPORT_SCHEMA.json")

    def test_cli_unknown_argument_returns_two(self):
        exit_code, output = self.capture_main(["--unknown"])
        self.assertEqual(2, exit_code)
        self.assertIn("unrecognized arguments: --unknown", output)

    def test_cli_output_is_deterministic_and_failures_are_sorted(self):
        root, paths = self.with_repo("audit")
        update_json(paths["audit"], lambda data: data.__setitem__("source_repository", "wrong/repository"))
        failures = validator.validate_repository(root)
        self.assertEqual(
            failures,
            sorted(
                failures,
                key=lambda item: (
                    item.target.casefold(),
                    item.reason.casefold(),
                    item.remediation.casefold(),
                ),
            ),
        )
        first_code, first_output = self.capture_main(["--repo-root", str(root)])
        second_code, second_output = self.capture_main(["--repo-root", str(root)])
        self.assertEqual(1, first_code)
        self.assertEqual(1, second_code)
        self.assertEqual(first_output, second_output)
        self.assert_relative_output(
            first_output,
            root,
            f"internal/artificer/reviews/{BUNDLE}/audit-report.json",
        )


if __name__ == "__main__":
    unittest.main()
