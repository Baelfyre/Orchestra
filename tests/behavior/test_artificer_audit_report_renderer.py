#!/usr/bin/env python3
"""Behavior coverage for deterministic Artificer audit rendering."""

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
sys.path.insert(0, str(Path(__file__).resolve().parent))

import render_artificer_audit_report as renderer  # noqa: E402
import test_artificer_governance_records as fixtures  # noqa: E402
from validate_artificer_records import ValidatorConfigurationError  # noqa: E402


AUDIT_REL = (
    f"internal/artificer/reviews/{fixtures.BUNDLE}/audit-report.json"
)
PASSING_SCENARIOS = (
    "valid audit-only governance chain",
    "valid complete governance chain",
    "multiple findings canonical order",
    "multiple evidence items canonical order",
    "empty limitations",
    "Markdown-special characters",
    "exact final newline",
    "repeated runs",
    "opposite JSON key insertion orders",
    "opposite file creation orders",
)
NEGATIVE_SCENARIOS = (
    "missing audit file",
    "malformed audit JSON",
    "schema-invalid audit",
    "invalid source bundle",
    "Phase 4B cross-record failure",
    "absolute audit path",
    "Windows drive path",
    "backslash path",
    "parent traversal",
    "wrong registry",
    "wrong filename",
    "symlinked audit file",
    "symlinked reviews root",
    "symlinked bundle directory",
    "missing schema",
    "malformed schema",
    "unsupported schema configuration",
    "CLI invalid arguments",
)


def reverse_keys(value):
    if isinstance(value, dict):
        return {
            key: reverse_keys(value[key])
            for key in reversed(list(value.keys()))
        }
    if isinstance(value, list):
        return [reverse_keys(item) for item in value]
    return value


class AuditReportRendererTests(unittest.TestCase):
    def with_repo(self, chain: str = "audit"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        return root, fixtures.fixture_repo(root, chain)

    def render(self, root: Path) -> str:
        return renderer.render_audit_report(root, Path(AUDIT_REL))

    def capture_main(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = renderer.main(argv)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def assert_safe_failure(
        self,
        root: Path,
        audit_path: Path | str,
        *,
        target: str,
        reason: str,
        remediation: str,
    ) -> None:
        with self.assertRaises(renderer.AuditRenderError) as raised:
            renderer.render_audit_report(root, audit_path)
        output = str(raised.exception)
        self.assertIn(target, output)
        self.assertIn(reason, output)
        self.assertIn(remediation, output)
        self.assertNotIn(str(root), output)
        self.assertNotIn(root.as_posix(), output)

    def add_second_finding(self, root: Path, paths: dict[str, Path]) -> None:
        pattern_path = (
            root
            / "internal/artificer/records"
            / fixtures.BUNDLE
            / "patterns/alpha-pattern.json"
        )
        fixtures.write_json(
            pattern_path,
            {
                "name": "Alpha Pattern",
                "description": "Second pattern.",
                "source_file": "src/example.py",
                "line_range": "30-40",
                "classification": "REFERENCE_ONLY",
                "assigned_specialist": "cipher",
            },
        )
        audit = fixtures.read_json(paths["audit"])
        audit["findings"].append(
            {
                "finding_id": "alpha",
                "pattern_record_path": (
                    f"internal/artificer/records/{fixtures.BUNDLE}/patterns/"
                    "alpha-pattern.json"
                ),
                "title": "Alpha title",
                "finding": "Alpha finding.",
                "recommendation": "Alpha recommendation.",
                "assigned_specialist": "cipher",
                "risk_level": "MEDIUM",
                "evidence": [
                    {
                        "bucket": "STATIC_ANALYSIS",
                        "source_file": "src/example.py",
                        "line_range": "30-40",
                        "summary": "Zulu evidence.",
                    },
                    {
                        "bucket": "SOURCE_CONFIRMED",
                        "source_file": "src/example.py",
                        "line_range": "2-3",
                        "summary": "Alpha evidence.",
                    },
                ],
            }
        )
        fixtures.write_json(paths["audit"], audit)

    def test_valid_audit_only_and_complete_chains(self):
        for chain in ("audit", "complete"):
            with self.subTest(chain=chain):
                root, _ = self.with_repo(chain)
                output = self.render(root)
                self.assertTrue(output.startswith("# Artificer Audit Report:"))
                headings = [
                    "## Audit Metadata",
                    "## Executive Summary",
                    "## Findings",
                    "## License Analysis",
                    "## Security Review",
                    "## Limitations",
                ]
                self.assertEqual(sorted(output.index(value) for value in headings), [output.index(value) for value in headings])

    def test_findings_evidence_and_limitations_are_canonical(self):
        root, paths = self.with_repo("audit")
        self.add_second_finding(root, paths)
        audit = fixtures.read_json(paths["audit"])
        audit["limitations"] = ["zulu", "Alpha", "alpha"]
        fixtures.write_json(paths["audit"], audit)
        output = self.render(root)

        self.assertLess(output.index("### alpha:"), output.index(r"### finding\-1:"))
        alpha_section = output[output.index("### alpha:"):output.index(r"### finding\-1:")]
        self.assertLess(alpha_section.index(r"SOURCE\_CONFIRMED"), alpha_section.index(r"STATIC\_ANALYSIS"))
        self.assertIn("| Pattern Name | Alpha Pattern |", alpha_section)
        self.assertLess(output.index("- Alpha"), output.index("- alpha"))
        self.assertLess(output.index("- alpha"), output.index("- zulu"))

    def test_empty_limitations_markdown_safety_and_final_newline(self):
        root, paths = self.with_repo("audit")
        audit = fixtures.read_json(paths["audit"])
        audit["limitations"] = []
        audit["executive_summary"] = (
            "Keep  two spaces\tand a tab.\n"
            "Replace only the newline. # heading | <tag> *bold* [link](x) ::directive"
        )
        audit["findings"][0]["title"] = "Title\n## injected"
        fixtures.write_json(paths["audit"], audit)
        output = self.render(root)

        self.assertIn("None recorded.", output)
        self.assertIn("Keep  two spaces\tand a tab", output)
        self.assertIn(r"a tab\. Replace only the newline\.", output)
        self.assertIn(r"\# heading \| \<tag\> \*bold\*", output)
        self.assertIn("&colon;&colon;directive", output)
        self.assertNotIn("::directive", output)
        self.assertIn(r"### finding\-1: Title \#\# injected", output)
        self.assertTrue(output.endswith("\n"))
        self.assertFalse(output.endswith("\n\n"))
        self.assertTrue(all(line == line.rstrip() for line in output.splitlines()))
        self.assertNotIn(str(root), output)

    def test_output_repeats_and_ignores_json_key_order(self):
        root, paths = self.with_repo("audit")
        first = self.render(root)
        self.assertEqual(first, self.render(root))
        fixtures.write_json(paths["audit"], reverse_keys(fixtures.read_json(paths["audit"])))
        pattern = root / fixtures.PATTERN_PATH
        fixtures.write_json(pattern, reverse_keys(fixtures.read_json(pattern)))
        self.assertEqual(first, self.render(root))

    def test_output_ignores_file_creation_order(self):
        outputs = []
        for reverse in (False, True):
            root, paths = self.with_repo("audit")
            self.add_second_finding(root, paths)
            patterns = root / f"internal/artificer/records/{fixtures.BUNDLE}/patterns"
            records = [(path.name, fixtures.read_json(path)) for path in patterns.glob("*.json")]
            shutil.rmtree(patterns)
            patterns.mkdir()
            for name, data in sorted(records, reverse=reverse):
                fixtures.write_json(patterns / name, data)
            outputs.append(self.render(root))
        self.assertEqual(outputs[0], outputs[1])

    def test_invalid_governance_records_fail_closed(self):
        cases = [
            (
                "missing audit file",
                lambda root, paths: paths["audit"].unlink(),
                f"internal/artificer/reviews/{fixtures.BUNDLE}",
                "governance validation failed",
                "required governance JSON record",
            ),
            (
                "malformed audit JSON",
                lambda root, paths: paths["audit"].write_text("{", encoding="utf-8"),
                AUDIT_REL,
                "governance validation failed",
                "Fix the JSON record",
            ),
            (
                "schema-invalid audit",
                lambda root, paths: fixtures.update_json(paths["audit"], lambda value: value.pop("audit_report_id")),
                AUDIT_REL,
                "missing required field",
                "Add the required field",
            ),
            (
                "invalid source bundle",
                lambda root, paths: fixtures.update_json(paths["audit"], lambda value: value.update(source_bundle_id=fixtures.OTHER_BUNDLE)),
                AUDIT_REL,
                "Source bundle",
                "Restore a valid Phase 3 source bundle",
            ),
            (
                "Phase 4B cross-record failure",
                lambda root, paths: fixtures.update_json(paths["audit"], lambda value: value.update(audit_report_id="changed-audit")),
                "internal/artificer/decisions",
                "audit_report_id",
                "existing audit report",
            ),
        ]
        for name, mutate, target, reason, remediation in cases:
            with self.subTest(name=name):
                root, paths = self.with_repo("complete" if "cross-record" in name else "audit")
                mutate(root, paths)
                self.assert_safe_failure(
                    root,
                    Path(AUDIT_REL),
                    target=target,
                    reason=reason,
                    remediation=remediation,
                )

    def test_invalid_audit_paths_fail_with_safe_remediation(self):
        root, paths = self.with_repo("audit")
        cases = [
            ("absolute", paths["audit"], "--audit", "repository-relative POSIX path"),
            ("drive", Path("C:/audit-report.json"), "--audit", "repository-relative POSIX path"),
            ("backslash", r"internal\artificer\reviews\x\audit-report.json", "--audit", "repository-relative POSIX path"),
            ("traversal", Path("internal/artificer/reviews/../audit-report.json"), "--audit", "repository-relative POSIX path"),
            ("wrong registry", Path(f"internal/artificer/records/{fixtures.BUNDLE}/audit-report.json"), "internal/artificer/records", "reviews registry contract"),
            ("wrong filename", Path(f"internal/artificer/reviews/{fixtures.BUNDLE}/report.json"), "report.json", "reviews registry contract"),
        ]
        for name, path, target, reason in cases:
            with self.subTest(name=name):
                self.assert_safe_failure(
                    root,
                    path,
                    target=target,
                    reason=reason,
                    remediation="internal/artificer/reviews/<bundle-id>/audit-report.json",
                )

    def test_symlinked_audit_paths_fail_when_supported(self):
        cases = ("audit file", "reviews root", "bundle directory")
        for case in cases:
            with self.subTest(case=case):
                root, paths = self.with_repo("audit")
                try:
                    if case == "audit file":
                        real = root / "real-audit.json"
                        paths["audit"].replace(real)
                        paths["audit"].symlink_to(real)
                    elif case == "reviews root":
                        reviews = root / "internal/artificer/reviews"
                        real = root / "real-reviews"
                        reviews.replace(real)
                        reviews.symlink_to(real, target_is_directory=True)
                    else:
                        bundle = paths["audit"].parent
                        real = root / "real-bundle"
                        bundle.replace(real)
                        bundle.symlink_to(real, target_is_directory=True)
                except OSError as exc:
                    self.skipTest(f"symbolic links unsupported: {exc}")
                self.assert_safe_failure(
                    root,
                    Path(AUDIT_REL),
                    target="internal/artificer/reviews",
                    reason="governance validation failed",
                    remediation="symbolic link",
                )

    def test_schema_configuration_errors_use_exit_two_without_path_leaks(self):
        cases = [
            ("missing", lambda path: path.unlink()),
            ("malformed", lambda path: path.write_text("{", encoding="utf-8")),
            (
                "unsupported",
                lambda path: fixtures.update_json(path, lambda value: value.update(minLength=1)),
            ),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                root, _ = self.with_repo("audit")
                schema = root / "internal/artificer/AUDIT_REPORT_SCHEMA.json"
                mutate(schema)
                with self.assertRaises(ValidatorConfigurationError):
                    self.render(root)
                code, stdout, stderr = self.capture_main(
                    ["--repo-root", str(root), "--audit", AUDIT_REL]
                )
                self.assertEqual(2, code)
                self.assertEqual("", stdout)
                self.assertIn("Configuration error", stderr)
                self.assertIn("Remediation:", stderr)
                self.assertIn("internal/artificer/AUDIT_REPORT_SCHEMA.json", stderr)
                self.assertNotIn(str(root), stderr)
                self.assertNotIn(root.as_posix(), stderr)

    def test_cli_success_failure_and_invalid_arguments(self):
        root, paths = self.with_repo("audit")
        code, stdout, stderr = self.capture_main(
            ["--repo-root", str(root), "--audit", AUDIT_REL]
        )
        self.assertEqual(0, code)
        self.assertEqual(self.render(root), stdout)
        self.assertEqual("", stderr)

        paths["audit"].write_text("{", encoding="utf-8")
        code, stdout, stderr = self.capture_main(
            ["--repo-root", str(root), "--audit", AUDIT_REL]
        )
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn(AUDIT_REL, stderr)
        self.assertIn("Remediation:", stderr)
        self.assertNotIn(str(root), stderr)

        code, stdout, stderr = self.capture_main([])
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("--audit", stderr)

        invalid_paths = [
            str(paths["audit"]),
            "C:/audit-report.json",
            r"internal\artificer\reviews\x\audit-report.json",
            "internal/artificer/reviews/../audit-report.json",
            f"internal/artificer/records/{fixtures.BUNDLE}/audit-report.json",
            f"internal/artificer/reviews/{fixtures.BUNDLE}/report.json",
        ]
        for audit_path in invalid_paths:
            with self.subTest(audit_path=audit_path):
                valid_root, _ = self.with_repo("audit")
                code, stdout, stderr = self.capture_main(
                    ["--repo-root", str(valid_root), "--audit", audit_path]
                )
                self.assertEqual(2, code)
                self.assertEqual("", stdout)
                self.assertIn("Invalid argument:", stderr)
                self.assertIn("Remediation:", stderr)
                self.assertNotIn(str(valid_root), stderr)


if __name__ == "__main__":
    unittest.main()
