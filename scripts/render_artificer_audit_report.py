#!/usr/bin/env python3
"""Render one validated Artificer audit report as deterministic Markdown."""

import argparse
import re
import sys
from pathlib import Path

import validate_artificer_governance_records
from validate_artificer_records import (
    ValidatorConfigurationError,
    load_json_without_duplicate_keys,
    parse_line_range,
)


AUDIT_PATH_RE = re.compile(
    r"^internal/artificer/reviews/([^/]+)/audit-report\.json$"
)
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
CONTROL_RE = re.compile(r"[\x00-\x1f]")
MARKDOWN_RE = re.compile(r"([\\`*_{}\[\]()#+.!|<>-])")


class AuditRenderError(Exception):
    """Raised when an audit report cannot be safely rendered."""


class AuditArgumentError(AuditRenderError):
    """Raised when a CLI audit-path argument violates the path contract."""


def _clean(value: object) -> str:
    text = str(value)
    text = text.replace("\r\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = text.replace("::", "&colon;&colon;")
    return MARKDOWN_RE.sub(r"\\\1", text)


def _table(rows: list[tuple[str, object]]) -> list[str]:
    result = ["| Field | Value |", "| --- | --- |"]
    result.extend(f"| {_clean(label)} | {_clean(value)} |" for label, value in rows)
    return result


def _audit_error(target: str, reason: str, remediation: str) -> AuditRenderError:
    return AuditRenderError(
        f"{target}: {reason} Remediation: {remediation}"
    )


def _audit_argument_error(
    target: str, reason: str, remediation: str
) -> AuditArgumentError:
    return AuditArgumentError(
        f"{target}: {reason} Remediation: {remediation}"
    )


def _relative_detail(repo_root: Path, value: object) -> str:
    detail = str(value)
    variants = {
        str(repo_root),
        str(repo_root.resolve()),
        repo_root.as_posix(),
        repo_root.resolve().as_posix(),
    }
    for variant in sorted(variants, key=len, reverse=True):
        detail = detail.replace(f"{variant}/", "").replace(f"{variant}\\", "")
        detail = detail.replace(variant, ".")
    return detail


def _validated_audit_path(
    repo_root: Path, audit_path: Path | str
) -> tuple[Path, str]:
    value = audit_path.as_posix() if isinstance(audit_path, Path) else str(audit_path)
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or WINDOWS_DRIVE_RE.match(value)
        or "\\" in value
        or CONTROL_RE.search(value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise _audit_argument_error(
            "--audit",
            "audit path must be a repository-relative POSIX path",
            "Use internal/artificer/reviews/<bundle-id>/audit-report.json.",
        )

    match = AUDIT_PATH_RE.fullmatch(value)
    if not match:
        raise _audit_argument_error(
            value,
            "audit path does not match the reviews registry contract",
            "Use internal/artificer/reviews/<bundle-id>/audit-report.json.",
        )

    root = repo_root.resolve()
    candidate = root.joinpath(*value.split("/"))
    current = root
    for part in value.split("/"):
        current = current / part
        if current.is_symlink():
            raise _audit_error(
                value,
                "audit path or an ancestor directory is a symbolic link",
                "Replace symbolic links with regular repository directories and files.",
            )
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError):
        raise _audit_error(
            value,
            "audit file is missing or resolves outside the repository",
            "Restore the validated audit report beneath internal/artificer/reviews/.",
        ) from None
    if not candidate.is_file():
        raise _audit_error(
            value,
            "audit path is not a regular file",
            "Provide a regular audit-report.json file.",
        )
    return candidate, match.group(1)


def _load_json(path: Path, target: str, repo_root: Path) -> dict:
    try:
        return load_json_without_duplicate_keys(path)
    except (ValueError, ValidatorConfigurationError) as exc:
        raise _audit_error(
            target,
            f"audit record cannot be read: {_relative_detail(repo_root, exc)}",
            "Fix the audit JSON and re-run Phase 4B validation.",
        ) from None


def render_audit_report(repo_root: Path, audit_path: Path) -> str:
    """Return deterministic Markdown for one validated audit report."""
    root = Path(repo_root).resolve()
    failures = validate_artificer_governance_records.validate_repository(root)
    if failures:
        failure = failures[0]
        raise _audit_error(
            failure.target,
            "repository governance validation failed: "
            f"{_relative_detail(root, failure.reason)}",
            _relative_detail(root, failure.remediation),
        )

    audit_file, bundle_id = _validated_audit_path(root, audit_path)
    target = audit_path.as_posix() if isinstance(audit_path, Path) else str(audit_path)
    audit = _load_json(audit_file, target, root)
    if audit.get("source_bundle_id") != bundle_id:
        raise _audit_error(
            target,
            "source_bundle_id does not match the audit bundle directory",
            "Set source_bundle_id to the containing bundle ID.",
        )

    findings = sorted(
        audit["findings"],
        key=lambda item: (item["finding_id"].casefold(), item["finding_id"]),
    )
    lines = [
        f"# Artificer Audit Report: {_clean(audit['source_repository'])}",
        "",
        "## Audit Metadata",
        "",
        *_table(
            [
                ("Audit Report ID", audit["audit_report_id"]),
                ("Source Bundle", audit["source_bundle_id"]),
                ("Source Repository", audit["source_repository"]),
                ("Reviewed Commit", audit["reviewed_commit_sha"]),
                ("Audit Date", audit["audit_date"]),
                ("Source Intake", audit["source_intake_path"]),
            ]
        ),
        "",
        "## Executive Summary",
        "",
        _clean(audit["executive_summary"]),
        "",
        "## Findings",
    ]

    for finding in findings:
        pattern_path = finding["pattern_record_path"]
        pattern = _load_json(
            root.joinpath(*pattern_path.split("/")), pattern_path, root
        )
        evidence = sorted(
            finding["evidence"],
            key=lambda item: (
                item["bucket"].casefold(),
                item["bucket"],
                item["source_file"].casefold(),
                item["source_file"],
                *(parse_line_range(item["line_range"]) or (0, 0)),
                item["summary"].casefold(),
                item["summary"],
            ),
        )
        lines.extend(
            [
                "",
                f"### {_clean(finding['finding_id'])}: {_clean(finding['title'])}",
                "",
                *_table(
                    [
                        ("Pattern Record", pattern_path),
                        ("Pattern Name", pattern["name"]),
                        ("Assigned Specialist", finding["assigned_specialist"]),
                        ("Risk Level", finding["risk_level"]),
                    ]
                ),
                "",
                "#### Finding",
                "",
                _clean(finding["finding"]),
                "",
                "#### Recommendation",
                "",
                _clean(finding["recommendation"]),
                "",
                "#### Evidence",
                "",
                "| Bucket | Source File | Line Range | Summary |",
                "| --- | --- | --- | --- |",
                *(
                    f"| {_clean(item['bucket'])} | {_clean(item['source_file'])} | "
                    f"{_clean(item['line_range'])} | {_clean(item['summary'])} |"
                    for item in evidence
                ),
            ]
        )

    license_analysis = audit["license_analysis"]
    security_review = audit["security_review"]
    limitations = sorted(
        audit["limitations"], key=lambda value: (value.casefold(), value)
    )
    lines.extend(
        [
            "",
            "## License Analysis",
            "",
            *_table(
                [
                    ("Detected License", license_analysis["detected_license"]),
                    (
                        "Compatibility Assessment",
                        license_analysis["compatibility_assessment"],
                    ),
                    (
                        "Governor Review Required",
                        str(license_analysis["governor_review_required"]).lower(),
                    ),
                    ("Summary", license_analysis["summary"]),
                ]
            ),
            "",
            "## Security Review",
            "",
            *_table(
                [
                    (
                        "External Execution Performed",
                        str(security_review["external_execution_performed"]).lower(),
                    ),
                    ("Summary", security_review["summary"]),
                ]
            ),
            "",
            "## Limitations",
            "",
            *(
                [f"- {_clean(value)}" for value in limitations]
                if limitations
                else ["None recorded."]
            ),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a validated Artificer audit report as Markdown."
    )
    parser.add_argument("--audit", required=True)
    parser.add_argument("--repo-root", default=None)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2

    repo_root = (
        Path(args.repo_root)
        if args.repo_root
        else Path(__file__).resolve().parent.parent
    )
    try:
        output = render_audit_report(repo_root, args.audit)
    except AuditArgumentError as exc:
        print(f"Invalid argument: {exc}", file=sys.stderr)
        return 2
    except ValidatorConfigurationError as exc:
        detail = _relative_detail(repo_root, exc)
        print(
            f"Configuration error: {detail} Remediation: Restore valid Phase 3 and Phase 4 schema contracts.",
            file=sys.stderr,
        )
        return 2
    except AuditRenderError as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
