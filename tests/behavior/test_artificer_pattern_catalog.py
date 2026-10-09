#!/usr/bin/env python3
"""Behavior coverage for Artificer Phase 4C-B Pattern Catalog validation."""

import contextlib
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_artificer_pattern_catalog as validator  # noqa: E402

from test_artificer_governance_records import (  # noqa: E402
    BUNDLE,
    OTHER_BUNDLE,
    OTHER_PATTERN_PATH,
    PATTERN_PATH,
    SHA,
    add_source_bundle,
    fixture_repo,
    read_json,
    update_json,
    write_json,
)


PASSING_SCENARIOS = (
    "empty promotion registry and canonical empty Catalog",
    "one approved promotion",
    "APPROVED lifecycle",
    "IMPLEMENTING lifecycle",
    "IMPLEMENTED lifecycle",
    "RETIRED lifecycle",
    "multiple promotion projections in canonical order",
    "repeated rendering produces identical output",
    "opposite promotion-file creation orders",
    "opposite JSON key insertion orders",
    "Markdown-special characters",
    "repeated spaces and tabs preserved",
    "CRLF Catalog accepted after logical normalization",
    "exactly one final newline",
    "--print-expected produces canonical stdout only",
    "--print-expected does not mutate repository state",
)

INDEX_ROW = "| catalog\\-pattern | Reference Pattern | owner/repository | 2026\\-07\\-04 | APPROVED | ponytail |"
HEADING_LINE = "### catalog\\-pattern: Reference Pattern"

NEGATIVE_SCENARIOS = (
    "missing Catalog",
    "symlinked Catalog",
    "symlinked docs ancestor",
    "symlinked docs/internal ancestor",
    "non-regular Catalog path",
    "oversized Catalog",
    "invalid UTF-8",
    "UTF-8 BOM",
    "missing final newline",
    "extra final newline",
    "trailing whitespace",
    "missing index row",
    "extra index row",
    "duplicate index row",
    "missing Catalog entry",
    "extra Catalog entry",
    "duplicate Catalog entry",
    "incorrect index order",
    "incorrect entry order",
    "stale Catalog ID",
    "stale pattern name",
    "stale source repository",
    "stale approval date",
    "stale lifecycle status",
    "stale assigned specialist",
    "stale source URL",
    "stale source bundle",
    "stale audited commit",
    "stale source file",
    "stale line range",
    "stale pattern-record path",
    "stale decision ID",
    "stale proposal ID",
    "stale promotion ID",
    "stale promotion-record path",
    "stale license",
    "stale attribution flag",
    "stale attribution summary",
    "stale pattern classification",
    "stale pattern description",
    "promotion exists while Catalog remains empty",
    "Catalog entry exists without a promotion",
    "two promotions target the same source pattern pair",
    "Phase 4B governance precondition failure",
    "missing schema configuration",
    "malformed schema configuration",
    "unsupported schema configuration",
    "invalid CLI arguments",
)


def snapshot_tree(root: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file() and not path.is_symlink():
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def empty_catalog_text() -> str:
    return (
        "# Orchestra Pattern Catalog\n\n"
        "This document is the governed human-readable projection of validated Artificer promotion records.\n\n"
        "> [!IMPORTANT]\n"
        "> Canonical authority remains with the validated Artificer JSON records. This Markdown file is manually synchronized and is never updated automatically by Artificer.\n"
        ">\n"
        "> Use `python scripts/validate_artificer_pattern_catalog.py --print-expected` to preview the canonical Catalog representation. The command writes only to standard output.\n\n"
        "## Catalog Index\n\n"
        "| ID | Pattern Name | Source Repository | Approval Date | Status | Assigned Specialist |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| | | | | | |\n\n"
        "---\n\n"
        "## Catalog Entries\n\n"
        "*(No patterns have been manually promoted.)*\n"
    )


def add_complete_chain(
    root: Path,
    *,
    bundle_id: str,
    catalog_id: str,
    promotion_id: str,
    decision_id: str,
    proposal_id: str,
    audit_id: str,
    pattern_slug: str,
    pattern_name: str,
    status: str = "APPROVED",
    repository: str = "owner/repository-two",
    source_file: str = "src/other.py",
    line_range: str = "30-40",
    classification: str = "ADAPTED_PATTERN",
    description: str = "Second source-backed pattern.",
) -> dict[str, Path]:
    add_source_bundle(root, bundle_id, repository=repository)
    source = root / "internal/artificer/records" / bundle_id
    pattern_rel = f"internal/artificer/records/{bundle_id}/patterns/{pattern_slug}.json"
    update_json(
        source / "patterns/reference-pattern.json",
        lambda data: data.update(
            {
                "name": pattern_name,
                "description": description,
                "source_file": source_file,
                "line_range": line_range,
                "classification": classification,
            }
        ),
    )
    update_json(
        source / "source-intake.json",
        lambda data: data.__setitem__(
            "files_examined", [{"file_path": source_file, "line_ranges": [line_range]}]
        ),
    )
    pattern_path = source / "patterns" / f"{pattern_slug}.json"
    (source / "patterns/reference-pattern.json").rename(pattern_path)
    paths = {
        "audit": root / f"internal/artificer/reviews/{bundle_id}/audit-report.json",
        "decision": root / f"internal/artificer/decisions/{bundle_id}/{pattern_slug}.json",
        "proposal": root / f"internal/artificer/proposals/{proposal_id}.json",
        "promotion": root / f"internal/artificer/promotions/{catalog_id}.json",
        "pattern": pattern_path,
    }
    audit = {
        "schema_version": "1.0",
        "audit_report_id": audit_id,
        "source_bundle_id": bundle_id,
        "source_intake_path": f"internal/artificer/records/{bundle_id}/source-intake.json",
        "source_repository": repository,
        "reviewed_commit_sha": SHA,
        "audit_date": "2026-07-02",
        "executive_summary": "Audit summary.",
        "findings": [
            {
                "finding_id": f"finding-{catalog_id}",
                "pattern_record_path": pattern_rel,
                "title": "Finding",
                "finding": "Observed behavior.",
                "recommendation": "Use concept only.",
                "assigned_specialist": "ponytail",
                "risk_level": "LOW",
                "evidence": [
                    {
                        "bucket": "SOURCE_CONFIRMED",
                        "source_file": source_file,
                        "line_range": line_range,
                        "summary": "Observed.",
                    }
                ],
            }
        ],
        "license_analysis": {
            "detected_license": "MIT",
            "compatibility_assessment": "COMPATIBLE",
            "governor_review_required": False,
            "summary": "Recorded only.",
        },
        "security_review": {
            "external_execution_performed": False,
            "summary": "No external execution.",
        },
        "limitations": ["Static source evidence only."],
    }
    decision = {
        "schema_version": "1.0",
        "decision_id": decision_id,
        "source_bundle_id": bundle_id,
        "pattern_record_path": pattern_rel,
        "audit_report_id": audit_id,
        "decision_status": "APPROVED",
        "assigned_specialist": "ponytail",
        "reviews": {
            reviewer: {
                "status": status_value,
                "rationale": "Reviewed.",
                "review_date": "2026-07-03",
            }
            for reviewer, status_value in {
                "arbiter": "APPROVED",
                "governor": "NOT_REQUIRED",
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
    proposal = {
        "schema_version": "1.1",
        "proposal_id": proposal_id,
        "title": "Proposal",
        "objective": "Adapt concept.",
        "proposal_date": "2026-07-03",
        "source_audit_ids": [audit_id],
        "selected_patterns": [
            {
                "decision_id": decision_id,
                "pattern_record_path": pattern_rel,
                "target_component": "validator",
                "evolution_mechanism": "CONCEPTUAL_ADAPTATION",
                "owner_specialist": "ponytail",
                "rationale": "Approved concept.",
            }
        ],
        "verification_plan": "Run tests.",
        "governance_handoff": "Maintainer review.",
        "reviews": {
            "arbiter": {
                "status": "APPROVED",
                "rationale": "Reviewed.",
                "review_date": "2026-07-03",
            },
            "governor": {
                "status": "NOT_REQUIRED",
                "rationale": "Not required.",
                "review_date": "2026-07-03",
            },
            "steward": {
                "status": "APPROVED",
                "rationale": "Reviewed.",
                "review_date": "2026-07-03",
            },
        },
        "maintainer_decision": {
            "status": "APPROVED",
            "rationale": "Approved.",
            "decision_date": "2026-07-03",
        },
        "proposal_status": "APPROVED",
    }
    promotion = {
        "schema_version": "1.0",
        "promotion_id": promotion_id,
        "catalog_pattern_id": catalog_id,
        "decision_id": decision_id,
        "proposal_id": proposal_id,
        "source_bundle_id": bundle_id,
        "pattern_record_path": pattern_rel,
        "approval_date": "2026-07-04",
        "promotion_status": status,
        "assigned_specialist": "ponytail",
        "source_traceability": {
            "repository": repository,
            "reviewed_commit_sha": SHA,
            "source_file": source_file,
            "line_range": line_range,
        },
        "license_and_attribution": {
            "original_license": "MIT",
            "attribution_required": True,
            "summary": "Retain attribution.",
        },
        "automatic_promotion": False,
    }
    write_json(paths["audit"], audit)
    write_json(paths["decision"], decision)
    write_json(paths["proposal"], proposal)
    write_json(paths["promotion"], promotion)
    return paths


class PatternCatalogTests(unittest.TestCase):
    def with_repo(self, chain: str = "complete") -> tuple[Path, dict[str, Path]]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        paths = fixture_repo(root, chain)
        catalog_path = root / "docs/internal/PATTERN_CATALOG.md"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(validator.render_expected_catalog(root), encoding="utf-8")
        return root, paths

    def assert_no_absolute_path_leak(self, root: Path, *values: object) -> None:
        leak = str(root)
        for value in values:
            self.assertNotIn(leak, str(value))

    def assert_failure(
        self,
        root: Path,
        failures: list[validator.CatalogFailure],
        *,
        target_contains: str,
        reason_contains: str,
        remediation_contains: str,
    ) -> None:
        self.assertTrue(failures, "Expected validation to fail")
        matching = [
            failure
            for failure in failures
            if target_contains in failure.target and reason_contains in failure.reason
        ]
        self.assertTrue(
            matching,
            f"Expected failure target={target_contains!r} reason={reason_contains!r}, got {failures!r}",
        )
        self.assertIn(remediation_contains, matching[0].remediation)
        self.assert_no_absolute_path_leak(
            root,
            matching[0].target,
            matching[0].reason,
            matching[0].remediation,
        )

    def run_main(self, root: Path, *argv: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = validator.main(["--repo-root", str(root), *argv])
        self.assert_no_absolute_path_leak(root, stdout.getvalue(), stderr.getvalue())
        return code, stdout.getvalue(), stderr.getvalue()

    def test_passing_render_and_validation_scenarios(self) -> None:
        scenarios = [
            ("empty promotion registry and canonical empty Catalog", "empty", None, None),
            ("one approved promotion", "complete", None, None),
            ("APPROVED lifecycle", "complete", lambda root, paths: None, "APPROVED"),
            (
                "IMPLEMENTING lifecycle",
                "complete",
                lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("promotion_status", "IMPLEMENTING")),
                "IMPLEMENTING",
            ),
            (
                "IMPLEMENTED lifecycle",
                "complete",
                lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("promotion_status", "IMPLEMENTED")),
                "IMPLEMENTED",
            ),
            (
                "RETIRED lifecycle",
                "complete",
                lambda root, paths: update_json(paths["promotion"], lambda data: data.__setitem__("promotion_status", "RETIRED")),
                "RETIRED",
            ),
            (
                "multiple promotion projections in canonical order",
                "complete",
                lambda root, paths: add_complete_chain(
                    root,
                    bundle_id=OTHER_BUNDLE,
                    catalog_id="a-catalog-pattern",
                    promotion_id="promotion-2",
                    decision_id="decision-2",
                    proposal_id="proposal-2",
                    audit_id="audit-2",
                    pattern_slug="another-pattern",
                    pattern_name="Another Pattern",
                ),
                None,
            ),
        ]
        for name, chain, mutate, expected_status in scenarios:
            with self.subTest(name=name):
                root, paths = self.with_repo(chain)
                if mutate is not None:
                    mutate(root, paths)
                expected = validator.render_expected_catalog(root)
                (root / "docs/internal/PATTERN_CATALOG.md").write_text(expected, encoding="utf-8")
                failures = validator.validate_repository(root)
                self.assertEqual(failures, [])
                code, stdout, stderr = self.run_main(root)
                self.assertEqual(code, 0)
                self.assertEqual(stderr, "")
                self.assertEqual(
                    stdout,
                    "[PASS] docs/internal/PATTERN_CATALOG.md is synchronized with validated promotion records.\n",
                )
                if expected_status is not None:
                    self.assertIn(f"- **Status**: {expected_status}", expected)

    def test_projection_stability_and_markdown_scenarios(self) -> None:
        scenarios = [
            (
                "repeated rendering produces identical output",
                lambda root, paths: (
                    self.assertEqual(
                        validator.render_expected_catalog(root),
                        validator.render_expected_catalog(root),
                    )
                ),
            ),
            (
                "opposite promotion-file creation orders",
                lambda root, paths: (
                    add_complete_chain(
                        root,
                        bundle_id=OTHER_BUNDLE,
                        catalog_id="z-catalog-pattern",
                        promotion_id="promotion-2",
                        decision_id="decision-2",
                        proposal_id="proposal-2",
                        audit_id="audit-2",
                        pattern_slug="late-pattern",
                        pattern_name="Late Pattern",
                    ),
                    add_complete_chain(
                        root,
                        bundle_id="owner__repository__cccccccccccc",
                        catalog_id="a-catalog-pattern",
                        promotion_id="promotion-3",
                        decision_id="decision-3",
                        proposal_id="proposal-3",
                        audit_id="audit-3",
                        pattern_slug="early-pattern",
                        pattern_name="Early Pattern",
                        repository="owner/repository-three",
                    ),
                ),
            ),
            (
                "opposite JSON key insertion orders",
                lambda root, paths: paths["promotion"].write_text(
                    json.dumps(
                        {
                            "automatic_promotion": False,
                            "license_and_attribution": {
                                "summary": "Retain attribution.",
                                "attribution_required": True,
                                "original_license": "MIT",
                            },
                            "source_traceability": {
                                "line_range": "10-20",
                                "source_file": "src/example.py",
                                "reviewed_commit_sha": SHA,
                                "repository": "owner/repository",
                            },
                            "assigned_specialist": "ponytail",
                            "promotion_status": "APPROVED",
                            "approval_date": "2026-07-04",
                            "pattern_record_path": PATTERN_PATH,
                            "source_bundle_id": BUNDLE,
                            "proposal_id": "proposal-1",
                            "decision_id": "decision-1",
                            "catalog_pattern_id": "catalog-pattern",
                            "promotion_id": "promotion-1",
                            "schema_version": "1.0",
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                ),
            ),
            (
                "Markdown-special characters",
                lambda root, paths: (
                    update_json(
                        paths["promotion"],
                        lambda data: data["license_and_attribution"].__setitem__(
                            "summary", 'Uses :: [link](x) <html> *stars* | pipes'
                        ),
                    ),
                    update_json(
                        root / PATTERN_PATH,
                        lambda data: data.update(
                            {
                                "name": "# Heading *Name*",
                                "description": "Text with | pipe and > quote",
                            }
                        ),
                    ),
                ),
            ),
            (
                "repeated spaces and tabs preserved",
                lambda root, paths: update_json(
                    root / PATTERN_PATH,
                    lambda data: data.__setitem__(
                        "description", "Tabs\tstay and  repeated  spaces stay"
                    ),
                ),
            ),
            (
                "CRLF Catalog accepted after logical normalization",
                lambda root, paths: (
                    (root / "docs/internal/PATTERN_CATALOG.md").write_bytes(
                        validator.render_expected_catalog(root).replace("\n", "\r\n").encode("utf-8")
                    )
                ),
            ),
            (
                "exactly one final newline",
                lambda root, paths: (
                    self.assertTrue(validator.render_expected_catalog(root).endswith("\n")),
                    self.assertFalse(validator.render_expected_catalog(root).endswith("\n\n")),
                ),
            ),
        ]
        for name, mutate in scenarios:
            with self.subTest(name=name):
                root, paths = self.with_repo("complete")
                mutate(root, paths)
                if name != "CRLF Catalog accepted after logical normalization":
                    expected = validator.render_expected_catalog(root)
                    (root / "docs/internal/PATTERN_CATALOG.md").write_text(expected, encoding="utf-8")
                failures = validator.validate_repository(root)
                self.assertEqual(failures, [])

    def test_print_expected_scenarios(self) -> None:
        scenarios = [
            "--print-expected produces canonical stdout only",
            "--print-expected does not mutate repository state",
        ]
        for name in scenarios:
            with self.subTest(name=name):
                root, paths = self.with_repo("complete")
                before = snapshot_tree(root)
                code, stdout, stderr = self.run_main(root, "--print-expected")
                after = snapshot_tree(root)
                self.assertEqual(code, 0)
                self.assertEqual(stderr, "")
                self.assertEqual(stdout, validator.render_expected_catalog(root))
                self.assertEqual(before, after)

    def test_catalog_file_safety_failures(self) -> None:
        scenarios = [
            {
                "name": "missing Catalog",
                "mutate": lambda root, paths: (root / "docs/internal/PATTERN_CATALOG.md").unlink(),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "Catalog file is missing",
                "remediation": "Restore docs/internal/PATTERN_CATALOG.md",
            },
            {
                "name": "symlinked Catalog",
                "mutate": self.make_symlink_catalog,
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "symbolic link",
                "remediation": "regular UTF-8 Markdown file",
            },
            {
                "name": "symlinked docs ancestor",
                "mutate": self.make_symlink_docs,
                "target": "docs",
                "reason": "ancestor directory",
                "remediation": "regular repository directory",
            },
            {
                "name": "symlinked docs/internal ancestor",
                "mutate": self.make_symlink_docs_internal,
                "target": "docs/internal",
                "reason": "ancestor directory",
                "remediation": "regular repository directory",
            },
            {
                "name": "non-regular Catalog path",
                "mutate": lambda root, paths: (
                    (root / "docs/internal/PATTERN_CATALOG.md").unlink(),
                    (root / "docs/internal/PATTERN_CATALOG.md").mkdir(),
                ),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "not a regular file",
                "remediation": "regular UTF-8 Markdown file",
            },
            {
                "name": "oversized Catalog",
                "mutate": lambda root, paths: (
                    root / "docs/internal/PATTERN_CATALOG.md"
                ).write_bytes(b"x" * (validator.MAX_CATALOG_BYTES + 1)),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "exceeds the maximum size",
                "remediation": "canonical Catalog content",
            },
            {
                "name": "invalid UTF-8",
                "mutate": lambda root, paths: (
                    root / "docs/internal/PATTERN_CATALOG.md"
                ).write_bytes(b"\xff"),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "not valid UTF-8",
                "remediation": "valid UTF-8 without BOM",
            },
            {
                "name": "UTF-8 BOM",
                "mutate": lambda root, paths: (
                    root / "docs/internal/PATTERN_CATALOG.md"
                ).write_bytes(b"\xef\xbb\xbf" + validator.render_expected_catalog(root).encode("utf-8")),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "byte order mark",
                "remediation": "without BOM",
            },
            {
                "name": "missing final newline",
                "mutate": lambda root, paths: (
                    root / "docs/internal/PATTERN_CATALOG.md"
                ).write_text(validator.render_expected_catalog(root).removesuffix("\n"), encoding="utf-8"),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "missing canonical content",
                "remediation": "canonical expected content",
            },
            {
                "name": "extra final newline",
                "mutate": lambda root, paths: (
                    root / "docs/internal/PATTERN_CATALOG.md"
                ).write_text(validator.render_expected_catalog(root) + "\n", encoding="utf-8"),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "non-canonical content",
                "remediation": "Remove the extra content",
            },
            {
                "name": "trailing whitespace",
                "mutate": lambda root, paths: self.replace_line(
                    root,
                    INDEX_ROW,
                    f"{INDEX_ROW} ",
                ),
                "target": "docs/internal/PATTERN_CATALOG.md",
                "reason": "line differs",
                "remediation": "canonical expected content",
            },
        ]
        for case in scenarios:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("complete")
                case["mutate"](root, paths)
                failures = validator.validate_repository(root)
                self.assert_failure(
                    root,
                    failures,
                    target_contains=case["target"],
                    reason_contains=case["reason"],
                    remediation_contains=case["remediation"],
                )

    def test_catalog_sync_mismatch_failures(self) -> None:
        scenarios = [
            {
                "name": "missing index row",
                "mutate": lambda root, paths: self.replace_line(
                    root,
                    INDEX_ROW,
                    "",
                ),
            },
            {
                "name": "extra index row",
                "mutate": lambda root, paths: self.insert_after(
                    root,
                    INDEX_ROW,
                    "| extra | Extra | owner/repository | 2026-07-04 | APPROVED | ponytail |",
                ),
            },
            {
                "name": "duplicate index row",
                "mutate": lambda root, paths: self.insert_after(
                    root,
                    INDEX_ROW,
                    INDEX_ROW,
                ),
            },
            {
                "name": "missing Catalog entry",
                "mutate": lambda root, paths: self.remove_block(
                    root, re.escape(HEADING_LINE)
                ),
            },
            {
                "name": "extra Catalog entry",
                "mutate": lambda root, paths: self.append_text(
                    root,
                    "\n### extra: Extra\n\n- **Status**: APPROVED\n",
                ),
            },
            {
                "name": "duplicate Catalog entry",
                "mutate": lambda root, paths: self.append_text(
                    root,
                    "\n### catalog\\-pattern: Reference Pattern\n\n- **Status**: APPROVED\n",
                ),
            },
            {
                "name": "incorrect index order",
                "mutate": lambda root, paths: self.make_two_promotions_out_of_order(root),
            },
            {
                "name": "incorrect entry order",
                "mutate": lambda root, paths: self.make_two_entries_out_of_order(root),
            },
            {"name": "stale Catalog ID", "mutate": lambda root, paths: self.replace_text(root, "catalog\\-pattern", "stale-id", 1)},
            {"name": "stale pattern name", "mutate": lambda root, paths: self.replace_text(root, "Reference Pattern", "Stale Pattern", 1)},
            {"name": "stale source repository", "mutate": lambda root, paths: self.replace_text(root, "owner/repository", "other/repo", 1)},
            {"name": "stale approval date", "mutate": lambda root, paths: self.replace_text(root, "2026\\-07\\-04", "2026-07-09", 1)},
            {"name": "stale lifecycle status", "mutate": lambda root, paths: self.replace_text(root, "APPROVED", "IMPLEMENTED", 1)},
            {"name": "stale assigned specialist", "mutate": lambda root, paths: self.replace_text(root, "ponytail", "cloak", 1)},
            {"name": "stale source URL", "mutate": lambda root, paths: self.replace_text(root, "https://example\\.test/owner/repository", "https://example.test/other/repo", 1)},
            {"name": "stale source bundle", "mutate": lambda root, paths: self.replace_text(root, "owner\\_\\_repository\\_\\_aaaaaaaaaaaa", "owner__repository__bbbbbbbbbbbb", 1)},
            {"name": "stale audited commit", "mutate": lambda root, paths: self.replace_text(root, SHA, "b" * 40, 1)},
            {"name": "stale source file", "mutate": lambda root, paths: self.replace_text(root, "src/example\\.py", "src/other.py", 1)},
            {"name": "stale line range", "mutate": lambda root, paths: self.replace_text(root, "10\\-20", "1-2", 1)},
            {"name": "stale pattern-record path", "mutate": lambda root, paths: self.replace_text(root, "internal/artificer/records/owner\\_\\_repository\\_\\_aaaaaaaaaaaa/patterns/reference\\-pattern\\.json", "wrong.json", 1)},
            {"name": "stale decision ID", "mutate": lambda root, paths: self.replace_text(root, "decision\\-1", "decision-9", 1)},
            {"name": "stale proposal ID", "mutate": lambda root, paths: self.replace_text(root, "proposal\\-1", "proposal-9", 1)},
            {"name": "stale promotion ID", "mutate": lambda root, paths: self.replace_text(root, "promotion\\-1", "promotion-9", 1)},
            {"name": "stale promotion-record path", "mutate": lambda root, paths: self.replace_text(root, "internal/artificer/promotions/catalog\\-pattern\\.json", "internal/artificer/promotions/other.json", 1)},
            {"name": "stale license", "mutate": lambda root, paths: self.replace_text(root, "MIT", "Apache-2.0", 1)},
            {"name": "stale attribution flag", "mutate": lambda root, paths: self.replace_text(root, "true", "false", 1)},
            {"name": "stale attribution summary", "mutate": lambda root, paths: self.replace_text(root, "Retain attribution\\.", "Different summary.", 1)},
            {"name": "stale pattern classification", "mutate": lambda root, paths: self.replace_text(root, "REFERENCE\\_ONLY", "ADAPTED_PATTERN", 1)},
            {"name": "stale pattern description", "mutate": lambda root, paths: self.replace_text(root, "Source\\-backed pattern\\.", "Stale description.", 1)},
            {
                "name": "promotion exists while Catalog remains empty",
                "mutate": lambda root, paths: (root / "docs/internal/PATTERN_CATALOG.md").write_text(empty_catalog_text(), encoding="utf-8"),
            },
            {
                "name": "Catalog entry exists without a promotion",
                "mutate": lambda root, paths: self.append_text(
                    root,
                    "\n### stale: Stale Entry\n\n- **Status**: APPROVED\n",
                ),
            },
        ]
        for case in scenarios:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("complete")
                case["mutate"](root, paths)
                failures = validator.validate_repository(root)
                self.assert_failure(
                    root,
                    failures,
                    target_contains="docs/internal/PATTERN_CATALOG.md",
                    reason_contains="Catalog",
                    remediation_contains="print-expected",
                )

    def test_governance_and_cli_failures(self) -> None:
        scenarios = [
            {
                "name": "two promotions target the same source pattern pair",
                "mutate": self.make_duplicate_source_pair,
                "exit_code": 1,
                "target": "internal/artificer/promotions",
                "reason": "same (source_bundle_id, pattern_record_path) pair",
            },
            {
                "name": "Phase 4B governance precondition failure",
                "mutate": lambda root, paths: update_json(
                    paths["promotion"],
                    lambda data: data.__setitem__("decision_id", "missing"),
                ),
                "exit_code": 1,
                "target": "internal/artificer/promotions/catalog-pattern.json",
                "reason": "approved decision",
            },
            {
                "name": "missing schema configuration",
                "mutate": lambda root, paths: (root / "internal/artificer/PROMOTION_RECORD_SCHEMA.json").unlink(),
                "exit_code": 2,
                "target": "Configuration error",
                "reason": "Schema file missing",
            },
            {
                "name": "malformed schema configuration",
                "mutate": lambda root, paths: (root / "internal/artificer/PROMOTION_RECORD_SCHEMA.json").write_text("{", encoding="utf-8"),
                "exit_code": 2,
                "target": "Configuration error",
                "reason": "Schema file invalid",
            },
            {
                "name": "unsupported schema configuration",
                "mutate": lambda root, paths: update_json(
                    root / "internal/artificer/PROMOTION_RECORD_SCHEMA.json",
                    lambda data: data.__setitem__("minLength", 1),
                ),
                "exit_code": 2,
                "target": "Configuration error",
                "reason": "unsupported keyword",
            },
        ]
        for case in scenarios:
            with self.subTest(name=case["name"]):
                root, paths = self.with_repo("complete")
                case["mutate"](root, paths)
                code, stdout, stderr = self.run_main(root)
                self.assertEqual(code, case["exit_code"])
                self.assertEqual(stderr, "")
                self.assertIn(case["target"], stdout)
                self.assertIn(case["reason"], stdout)

        root, paths = self.with_repo("complete")
        code, stdout, stderr = self.run_main(root, "--write")
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("usage:", stderr)

    def make_symlink_catalog(self, root: Path, paths: dict[str, Path]) -> None:
        actual = root / "docs/internal/real-catalog.md"
        actual.write_text(validator.render_expected_catalog(root), encoding="utf-8")
        catalog = root / "docs/internal/PATTERN_CATALOG.md"
        catalog.unlink()
        os.symlink(actual, catalog)

    def make_symlink_docs(self, root: Path, paths: dict[str, Path]) -> None:
        original = root / "docs"
        target = root / "real-docs"
        shutil.move(str(original), str(target))
        os.symlink(target, original)

    def make_symlink_docs_internal(self, root: Path, paths: dict[str, Path]) -> None:
        original = root / "docs/internal"
        target = root / "docs/real-internal"
        shutil.move(str(original), str(target))
        os.symlink(target, original)

    def replace_text(self, root: Path, pattern: str, replacement: str, count: int) -> None:
        path = root / "docs/internal/PATTERN_CATALOG.md"
        text = path.read_text(encoding="utf-8")
        updated = text.replace(pattern, replacement, count)
        path.write_text(updated, encoding="utf-8")

    def replace_line(self, root: Path, old: str, new: str) -> None:
        path = root / "docs/internal/PATTERN_CATALOG.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def insert_after(self, root: Path, needle: str, addition: str) -> None:
        path = root / "docs/internal/PATTERN_CATALOG.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(needle, f"{needle}\n{addition}", 1), encoding="utf-8")

    def append_text(self, root: Path, text: str) -> None:
        path = root / "docs/internal/PATTERN_CATALOG.md"
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def remove_block(self, root: Path, heading_pattern: str) -> None:
        path = root / "docs/internal/PATTERN_CATALOG.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if re.search(heading_pattern, line))
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if lines[index].startswith("### "):
                end = index
                break
        remaining = lines[:start] + lines[end:]
        path.write_text("\n".join(remaining).rstrip() + "\n", encoding="utf-8")

    def make_two_promotions_out_of_order(self, root: Path) -> None:
        add_complete_chain(
            root,
            bundle_id=OTHER_BUNDLE,
            catalog_id="a-catalog-pattern",
            promotion_id="promotion-2",
            decision_id="decision-2",
            proposal_id="proposal-2",
            audit_id="audit-2",
            pattern_slug="another-pattern",
            pattern_name="Another Pattern",
        )
        expected = validator.render_expected_catalog(root)
        first = "| a\\-catalog\\-pattern | Another Pattern | owner/repository-two | 2026\\-07\\-04 | APPROVED | ponytail |"
        second = INDEX_ROW
        text = expected.replace(first, "__A__").replace(second, first).replace("__A__", second)
        (root / "docs/internal/PATTERN_CATALOG.md").write_text(text, encoding="utf-8")

    def make_two_entries_out_of_order(self, root: Path) -> None:
        add_complete_chain(
            root,
            bundle_id=OTHER_BUNDLE,
            catalog_id="a-catalog-pattern",
            promotion_id="promotion-2",
            decision_id="decision-2",
            proposal_id="proposal-2",
            audit_id="audit-2",
            pattern_slug="another-pattern",
            pattern_name="Another Pattern",
        )
        expected = validator.render_expected_catalog(root)
        entry_a = (
            "### a\\-catalog\\-pattern: Another Pattern\n\n"
            "- **Status**: APPROVED\n"
        )
        entry_b = (
            "### catalog\\-pattern: Reference Pattern\n\n"
            "- **Status**: APPROVED\n"
        )
        text = expected.replace(entry_a, "__A__").replace(entry_b, entry_a).replace("__A__", entry_b)
        (root / "docs/internal/PATTERN_CATALOG.md").write_text(text, encoding="utf-8")

    def make_duplicate_source_pair(self, root: Path, paths: dict[str, Path]) -> None:
        data = read_json(paths["promotion"])
        data["promotion_id"] = "promotion-2"
        data["catalog_pattern_id"] = "dup-catalog"
        write_json(root / "internal/artificer/promotions/dup-catalog.json", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
