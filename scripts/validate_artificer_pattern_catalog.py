#!/usr/bin/env python3
"""Deterministic validator for the governed Artificer Pattern Catalog."""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import validate_artificer_governance_records
from validate_artificer_records import (
    ValidationFailure,
    ValidatorConfigurationError,
    load_json_without_duplicate_keys,
)


ARTIFICER_DIR = "internal/artificer"
CATALOG_PATH = "docs/internal/PATTERN_CATALOG.md"
PROMOTIONS_DIR = f"{ARTIFICER_DIR}/promotions"
MAX_CATALOG_BYTES = 1_048_576
MARKDOWN_RE = re.compile(r"([\\`*_{}\[\]()#+.!|<>-])")


@dataclass(frozen=True)
class CatalogFailure:
    target: str
    reason: str
    remediation: str


class CatalogProjectionError(Exception):
    """Raised when the canonical Catalog projection cannot be produced."""


@dataclass(frozen=True)
class PromotionProjection:
    catalog_pattern_id: str
    pattern_name: str
    source_repository: str
    source_url: str
    source_bundle_id: str
    audited_commit: str
    source_file: str
    line_range: str
    pattern_record_path: str
    decision_id: str
    proposal_id: str
    promotion_id: str
    promotion_record_path: str
    approval_date: str
    status: str
    assigned_specialist: str
    original_license: str
    attribution_required: bool
    attribution_summary: str
    pattern_classification: str
    pattern_description: str


def _rel(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _failure(target: str, reason: str, remediation: str) -> CatalogFailure:
    return CatalogFailure(target, reason, remediation)


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


def _clean_text(value: object) -> str:
    text = str(value)
    text = text.replace("\r\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = text.replace("::", "&colon;&colon;")
    return text


def _escape_markdown(value: object) -> str:
    return MARKDOWN_RE.sub(r"\\\1", _clean_text(value))


def _table_value(value: object) -> str:
    return _escape_markdown(value)


def _heading_value(value: object) -> str:
    return _escape_markdown(value)


def _inline_value(value: object) -> str:
    return _escape_markdown(value)


def _load_projection_record(
    repo_root: Path, promotion_path: Path
) -> PromotionProjection:
    target = _rel(repo_root, promotion_path)
    try:
        promotion = load_json_without_duplicate_keys(promotion_path)
        intake_path = repo_root / ARTIFICER_DIR / "records" / promotion["source_bundle_id"] / "source-intake.json"
        pattern_path = repo_root / Path(promotion["pattern_record_path"])
        intake = load_json_without_duplicate_keys(intake_path)
        pattern = load_json_without_duplicate_keys(pattern_path)
    except (KeyError, ValueError, ValidatorConfigurationError) as exc:
        detail = _relative_detail(repo_root, exc)
        raise CatalogProjectionError(
            f"{target}: canonical projection could not be produced: {detail}"
        ) from exc

    return PromotionProjection(
        catalog_pattern_id=promotion["catalog_pattern_id"],
        pattern_name=pattern["name"],
        source_repository=intake["repository"],
        source_url=intake["canonical_url"],
        source_bundle_id=promotion["source_bundle_id"],
        audited_commit=intake["reviewed_commit_sha"],
        source_file=pattern["source_file"],
        line_range=pattern["line_range"],
        pattern_record_path=promotion["pattern_record_path"],
        decision_id=promotion["decision_id"],
        proposal_id=promotion["proposal_id"],
        promotion_id=promotion["promotion_id"],
        promotion_record_path=f"{PROMOTIONS_DIR}/{promotion['catalog_pattern_id']}.json",
        approval_date=promotion["approval_date"],
        status=promotion["promotion_status"],
        assigned_specialist=promotion["assigned_specialist"],
        original_license=promotion["license_and_attribution"]["original_license"],
        attribution_required=promotion["license_and_attribution"]["attribution_required"],
        attribution_summary=promotion["license_and_attribution"]["summary"],
        pattern_classification=pattern["classification"],
        pattern_description=pattern["description"],
    )


def _load_promotions(repo_root: Path) -> list[PromotionProjection]:
    promotions_root = repo_root / PROMOTIONS_DIR
    if not promotions_root.is_dir():
        return []
    projections = [
        _load_projection_record(repo_root, path)
        for path in sorted(
            promotions_root.glob("*.json"),
            key=lambda item: (item.name.casefold(), item.name),
        )
    ]
    return sorted(
        projections,
        key=lambda item: (
            item.catalog_pattern_id.casefold(),
            item.catalog_pattern_id,
        ),
    )


def _validate_unique_source_pattern_pairs(
    promotions: list[PromotionProjection],
) -> list[CatalogFailure]:
    failures: list[CatalogFailure] = []
    seen: dict[tuple[str, str], str] = {}
    for promotion in promotions:
        pair = (promotion.source_bundle_id, promotion.pattern_record_path)
        current_target = promotion.promotion_record_path
        first_target = seen.get(pair)
        if first_target is not None:
            reason = (
                "Two promotion records project the same "
                "(source_bundle_id, pattern_record_path) pair"
            )
            remediation = (
                "Keep exactly one promotion record for the source bundle and "
                "pattern pair."
            )
            failures.append(_failure(first_target, reason, remediation))
            failures.append(_failure(current_target, reason, remediation))
        else:
            seen[pair] = current_target
    return failures


def _render_index_row(promotion: PromotionProjection) -> str:
    return (
        f"| {_table_value(promotion.catalog_pattern_id)} | "
        f"{_table_value(promotion.pattern_name)} | "
        f"{_table_value(promotion.source_repository)} | "
        f"{_table_value(promotion.approval_date)} | "
        f"{_table_value(promotion.status)} | "
        f"{_table_value(promotion.assigned_specialist)} |"
    )


def _render_entry(promotion: PromotionProjection) -> list[str]:
    return [
        (
            f"### {_heading_value(promotion.catalog_pattern_id)}: "
            f"{_heading_value(promotion.pattern_name)}"
        ),
        "",
        f"- **Status**: {_inline_value(promotion.status)}",
        f"- **Source Repository**: {_inline_value(promotion.source_repository)}",
        f"- **Source URL**: {_inline_value(promotion.source_url)}",
        f"- **Source Bundle**: {_inline_value(promotion.source_bundle_id)}",
        f"- **Audited Commit**: {_inline_value(promotion.audited_commit)}",
        f"- **Source File**: {_inline_value(promotion.source_file)}",
        f"- **Line Range**: {_inline_value(promotion.line_range)}",
        f"- **Pattern Record**: {_inline_value(promotion.pattern_record_path)}",
        f"- **Decision Record**: {_inline_value(promotion.decision_id)}",
        f"- **Proposal Record**: {_inline_value(promotion.proposal_id)}",
        f"- **Promotion Record**: {_inline_value(promotion.promotion_id)}",
        (
            "- **Promotion Record Path**: "
            f"{_inline_value(promotion.promotion_record_path)}"
        ),
        f"- **Approval Date**: {_inline_value(promotion.approval_date)}",
        f"- **Original License**: {_inline_value(promotion.original_license)}",
        (
            "- **Attribution Required**: "
            f"{_inline_value(str(promotion.attribution_required).lower())}"
        ),
        (
            "- **Attribution Summary**: "
            f"{_inline_value(promotion.attribution_summary)}"
        ),
        (
            "- **Orchestra Specialist Owner**: "
            f"{_inline_value(promotion.assigned_specialist)}"
        ),
        (
            "- **Pattern Classification**: "
            f"{_inline_value(promotion.pattern_classification)}"
        ),
        (
            "- **Pattern Description**: "
            f"{_inline_value(promotion.pattern_description)}"
        ),
    ]


def _map_governance_failures(
    failures: list[ValidationFailure],
) -> list[CatalogFailure]:
    return [
        CatalogFailure(
            failure.target,
            failure.reason,
            failure.remediation,
        )
        for failure in failures
    ]


def render_expected_catalog(repo_root: Path) -> str:
    """Return the deterministic canonical Pattern Catalog Markdown."""
    root = Path(repo_root).resolve()
    governance_failures = validate_artificer_governance_records.validate_repository(root)
    if governance_failures:
        failure = governance_failures[0]
        raise CatalogProjectionError(
            f"{failure.target}: {failure.reason} Remediation: {failure.remediation}"
        )

    promotions = _load_promotions(root)
    duplicate_failures = _validate_unique_source_pattern_pairs(promotions)
    if duplicate_failures:
        failure = sorted(
            duplicate_failures,
            key=lambda item: (
                item.target.casefold(),
                item.target,
                item.reason.casefold(),
                item.reason,
                item.remediation.casefold(),
                item.remediation,
            ),
        )[0]
        raise CatalogProjectionError(
            f"{failure.target}: {failure.reason} Remediation: {failure.remediation}"
        )

    lines = [
        "# Orchestra Pattern Catalog",
        "",
        (
            "This document is the governed human-readable projection of "
            "validated Artificer promotion records."
        ),
        "",
        "> [!IMPORTANT]",
        (
            "> Canonical authority remains with the validated Artificer JSON "
            "records. This Markdown file is manually synchronized and is never "
            "updated automatically by Artificer."
        ),
        ">",
        (
            "> Use `python scripts/validate_artificer_pattern_catalog.py "
            "--print-expected` to preview the canonical Catalog "
            "representation. The command writes only to standard output."
        ),
        "",
        "## Catalog Index",
        "",
        (
            "| ID | Pattern Name | Source Repository | Approval Date | "
            "Status | Assigned Specialist |"
        ),
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if promotions:
        lines.extend(_render_index_row(promotion) for promotion in promotions)
    else:
        lines.append("| | | | | | |")

    lines.extend(["", "---", "", "## Catalog Entries", ""])
    if promotions:
        for index, promotion in enumerate(promotions):
            if index:
                lines.append("")
            lines.extend(_render_entry(promotion))
    else:
        lines.append("*(No patterns have been manually promoted.)*")
    return "\n".join(lines).rstrip() + "\n"


def _validate_catalog_file(repo_root: Path) -> tuple[Path | None, list[CatalogFailure]]:
    root = Path(repo_root).resolve()
    catalog_path = root / CATALOG_PATH
    docs_path = root / "docs"
    internal_path = docs_path / "internal"

    for rel_target, path in (("docs", docs_path), ("docs/internal", internal_path)):
        if path.is_symlink():
            return None, [
                _failure(
                    rel_target,
                    "Catalog ancestor directory must not be a symbolic link",
                    "Replace the symbolic link with a regular repository directory.",
                )
            ]
    if catalog_path.is_symlink():
        return None, [
            _failure(
                CATALOG_PATH,
                "Catalog file must not be a symbolic link",
                "Replace the symbolic link with a regular UTF-8 Markdown file.",
            )
        ]
    if not catalog_path.exists():
        return None, [
            _failure(
                CATALOG_PATH,
                "Catalog file is missing",
                "Restore docs/internal/PATTERN_CATALOG.md as a regular UTF-8 Markdown file.",
            )
        ]
    if not catalog_path.is_file():
        return None, [
            _failure(
                CATALOG_PATH,
                "Catalog path is not a regular file",
                "Replace docs/internal/PATTERN_CATALOG.md with a regular UTF-8 Markdown file.",
            )
        ]
    size = catalog_path.stat().st_size
    if size > MAX_CATALOG_BYTES:
        return None, [
            _failure(
                CATALOG_PATH,
                (
                    "Catalog file exceeds the maximum size of "
                    f"{MAX_CATALOG_BYTES} bytes ({size} bytes)"
                ),
                "Reduce docs/internal/PATTERN_CATALOG.md to the canonical Catalog content.",
            )
        ]
    return catalog_path, []


def _read_catalog_text(repo_root: Path, catalog_path: Path) -> tuple[str | None, list[CatalogFailure]]:
    try:
        raw = catalog_path.read_bytes()
    except OSError as exc:
        return None, [
            _failure(
                CATALOG_PATH,
                f"Catalog file cannot be read: {_relative_detail(repo_root, exc)}",
                "Restore a readable UTF-8 Markdown file at docs/internal/PATTERN_CATALOG.md.",
            )
        ]
    if raw.startswith(b"\xef\xbb\xbf"):
        return None, [
            _failure(
                CATALOG_PATH,
                "Catalog file must not use a UTF-8 byte order mark",
                "Save docs/internal/PATTERN_CATALOG.md as UTF-8 without BOM.",
            )
        ]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [
            _failure(
                CATALOG_PATH,
                f"Catalog file is not valid UTF-8: {_relative_detail(repo_root, exc)}",
                "Save docs/internal/PATTERN_CATALOG.md as valid UTF-8 without BOM.",
            )
        ]
    return text.replace("\r\n", "\n").replace("\r", "\n"), []


def _compare_catalog(
    actual: str, expected: str
) -> CatalogFailure | None:
    if actual == expected:
        return None

    actual_lines = actual.split("\n")
    expected_lines = expected.split("\n")
    common = min(len(actual_lines), len(expected_lines))
    for index in range(common):
        if actual_lines[index] != expected_lines[index]:
            return _failure(
                f"{CATALOG_PATH}:{index + 1}",
                "Catalog line differs from the canonical promotion projection",
                (
                    "Replace the line with the canonical expected content or "
                    "inspect --print-expected."
                ),
            )
    if len(actual_lines) < len(expected_lines):
        line_number = common + 1
        return _failure(
            f"{CATALOG_PATH}:{line_number}",
            f"Catalog is missing canonical content beginning at line {line_number}",
            (
                "Add the canonical expected content beginning at that line or "
                "inspect --print-expected."
            ),
        )
    line_number = common + 1
    return _failure(
        f"{CATALOG_PATH}:{line_number}",
        f"Catalog contains non-canonical content beginning at line {line_number}",
        (
            "Remove the extra content beginning at that line or inspect "
            "--print-expected."
        ),
    )


def validate_repository(repo_root: Path) -> list[CatalogFailure]:
    """Return deterministic Catalog synchronization failures."""
    root = Path(repo_root).resolve()
    try:
        governance_failures = validate_artificer_governance_records.validate_repository(root)
    except ValidatorConfigurationError:
        raise
    failures = _map_governance_failures(governance_failures)
    if failures:
        return sorted(
            failures,
            key=lambda item: (
                item.target.casefold(),
                item.target,
                item.reason.casefold(),
                item.reason,
                item.remediation.casefold(),
                item.remediation,
            ),
        )

    promotions = _load_promotions(root)
    failures.extend(_validate_unique_source_pattern_pairs(promotions))
    catalog_path, catalog_failures = _validate_catalog_file(root)
    failures.extend(catalog_failures)
    if failures:
        return sorted(
            failures,
            key=lambda item: (
                item.target.casefold(),
                item.target,
                item.reason.casefold(),
                item.reason,
                item.remediation.casefold(),
                item.remediation,
            ),
        )
    if catalog_path is None:
        return []

    actual_text, text_failures = _read_catalog_text(root, catalog_path)
    failures.extend(text_failures)
    if actual_text is None or failures:
        return sorted(
            failures,
            key=lambda item: (
                item.target.casefold(),
                item.target,
                item.reason.casefold(),
                item.reason,
                item.remediation.casefold(),
                item.remediation,
            ),
        )

    try:
        expected_text = render_expected_catalog(root)
    except ValidatorConfigurationError:
        raise
    except CatalogProjectionError as exc:
        failures.append(
            _failure(
                CATALOG_PATH,
                _relative_detail(root, exc),
                "Fix the promotion projection inputs and re-run validation.",
            )
        )
        return sorted(
            failures,
            key=lambda item: (
                item.target.casefold(),
                item.target,
                item.reason.casefold(),
                item.reason,
                item.remediation.casefold(),
                item.remediation,
            ),
        )

    mismatch = _compare_catalog(actual_text, expected_text)
    if mismatch is not None:
        failures.append(mismatch)
    return sorted(
        failures,
        key=lambda item: (
            item.target.casefold(),
            item.target,
            item.reason.casefold(),
            item.reason,
            item.remediation.casefold(),
            item.remediation,
        ),
    )


def _print_failure(failure: CatalogFailure) -> None:
    print(f"[FAIL] {failure.target}: {failure.reason}")
    print(f"       Remediation: {failure.remediation}")


def main(argv: list[str] | None = None) -> int:
    """Run Catalog validation or print the expected projection."""
    parser = argparse.ArgumentParser(
        description="Artificer Pattern Catalog synchronization validator."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--print-expected", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parent.parent
    )
    try:
        if args.print_expected:
            sys.stdout.write(render_expected_catalog(repo_root))
            return 0
        failures = validate_repository(repo_root)
    except ValidatorConfigurationError as exc:
        print(f"[FAIL] Configuration error: {_relative_detail(repo_root, exc)}")
        print("       Remediation: Restore valid Phase 3 and Phase 4 schema contracts.")
        return 2
    except CatalogProjectionError as exc:
        print(f"[FAIL] {CATALOG_PATH}: {_relative_detail(repo_root, exc)}")
        print("       Remediation: Fix the promotion projection inputs and re-run validation.")
        return 1

    if failures:
        for failure in failures:
            _print_failure(failure)
        return 1
    print("[PASS] docs/internal/PATTERN_CATALOG.md is synchronized with validated promotion records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
