#!/usr/bin/env python3
"""Deterministic validator for Artificer Phase 4B governance records."""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from validate_artificer_records import (
    MAX_FILE_SIZE,
    ValidationFailure,
    ValidatorConfigurationError,
    is_range_covered,
    load_json_without_duplicate_keys,
    parse_line_range,
    validate_instance,
    validate_schema_configuration,
)


ARTIFICER_DIR = "internal/artificer"
RECORDS_DIR = f"{ARTIFICER_DIR}/records"
REGISTRIES = {
    "reviews": (f"{ARTIFICER_DIR}/reviews", "audit-report.json"),
    "decisions": (f"{ARTIFICER_DIR}/decisions", None),
    "proposals": (f"{ARTIFICER_DIR}/proposals", None),
    "promotions": (f"{ARTIFICER_DIR}/promotions", None),
}
SCHEMAS = {
    "audit": f"{ARTIFICER_DIR}/AUDIT_REPORT_SCHEMA.json",
    "decision": f"{ARTIFICER_DIR}/GOVERNANCE_DECISION_SCHEMA.json",
    "proposal": f"{ARTIFICER_DIR}/EVOLUTION_PROPOSAL_SCHEMA.json",
    "promotion": f"{ARTIFICER_DIR}/PROMOTION_RECORD_SCHEMA.json",
    "intake": f"{ARTIFICER_DIR}/SOURCE_INTAKE_SCHEMA.json",
    "pattern": f"{ARTIFICER_DIR}/PATTERN_SCHEMA.json",
}
IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
BUNDLE_RE = re.compile(r"^[a-z0-9._-]+__[a-z0-9._-]+__[0-9a-f]{12}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
CONTROL_RE = re.compile(r"[\x00-\x1f]")


@dataclass(frozen=True)
class SourceBundle:
    bundle_id: str
    intake: dict
    patterns: dict[str, dict]


def _rel(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _failure(target: str, reason: str, remediation: str) -> ValidationFailure:
    return ValidationFailure(target, reason, remediation)


def _sanitize_configuration_error(
    schema_path: Path, relative_schema_path: str, error: Exception
) -> str:
    detail = str(error)
    path_variants = {
        str(schema_path),
        str(schema_path.resolve()),
        schema_path.as_posix(),
        schema_path.resolve().as_posix(),
    }
    for path_variant in sorted(path_variants, key=len, reverse=True):
        prefix = f"{path_variant}: "
        if detail.startswith(prefix):
            detail = detail[len(prefix) :]
            break
        detail = detail.replace(path_variant, relative_schema_path)
    return detail


def find_casefold_duplicate(values: list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        folded = value.casefold()
        if folded in seen:
            return value
        seen.add(folded)
    return None


def _load_schema(repo_root: Path, path: str) -> dict:
    schema_path = repo_root / path
    if not schema_path.is_file():
        raise ValidatorConfigurationError(f"Schema file missing: {path}")
    try:
        schema = load_json_without_duplicate_keys(schema_path)
    except (ValueError, ValidatorConfigurationError) as exc:
        detail = _sanitize_configuration_error(schema_path, path, exc)
        raise ValidatorConfigurationError(
            f"Schema file invalid: {path}: {detail}"
        ) from exc
    try:
        validate_schema_configuration(schema, path)
    except ValidatorConfigurationError as exc:
        detail = _sanitize_configuration_error(schema_path, path, exc)
        raise ValidatorConfigurationError(
            f"Schema file invalid: {path}: {detail}"
        ) from exc
    return schema


def _load_schemas(repo_root: Path) -> dict[str, dict]:
    return {name: _load_schema(repo_root, path) for name, path in SCHEMAS.items()}


def _safe_path(value: object, field: str, target: str) -> list[ValidationFailure]:
    if not isinstance(value, str) or not value.strip():
        return [_failure(target, f"{field} must be a non-empty repository-relative POSIX path", "Provide a non-empty relative path using '/'.")]
    if CONTROL_RE.search(value) or "\\" in value or value.startswith("/") or WINDOWS_DRIVE_RE.match(value):
        return [_failure(target, f"{field} '{value}' is not a safe repository-relative POSIX path", "Use a relative path with '/' separators and no control characters.")]
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return [_failure(target, f"{field} '{value}' contains an unsafe path component", "Remove empty, '.' and '..' path components.")]
    return []


def _identifier(value: object, field: str, target: str) -> list[ValidationFailure]:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        return [_failure(target, f"{field} must match {IDENTIFIER_RE.pattern}", "Use a lowercase identifier containing only a-z, 0-9, '.', '_' or '-'.")]
    return []


def _date(value: object, field: str, target: str) -> list[ValidationFailure]:
    if not isinstance(value, str):
        return []
    try:
        date.fromisoformat(value)
    except ValueError:
        return [_failure(target, f"{field} '{value}' is not a valid ISO calendar date", "Use YYYY-MM-DD with a real calendar date.")]
    return []


def _nonempty_strings(value: object, target: str, field: str = "") -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if isinstance(value, dict):
        for key, child in value.items():
            failures.extend(_nonempty_strings(child, target, key if not field else f"{field}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_nonempty_strings(child, target, f"{field}[{index}]"))
    elif isinstance(value, str) and not value.strip():
        failures.append(_failure(target, f"{field} must not be empty after trimming", f"Provide a non-empty value for {field}."))
    return failures


def _specialist_allowlist(pattern_schema: dict) -> set[str]:
    return set(pattern_schema["properties"]["assigned_specialist"]["enum"])


def _valid_specialist(value: object, field: str, target: str, allowlist: set[str]) -> list[ValidationFailure]:
    if value == "artificer":
        return [_failure(target, f"{field} must not assign Artificer", "Assign a specialist from PATTERN_SCHEMA.json.")]
    if value not in allowlist:
        return [_failure(target, f"{field} '{value}' is not a valid assigned specialist", "Use an assigned_specialist enum value from PATTERN_SCHEMA.json.")]
    return []


def _load_record(path: Path, schema: dict, repo_root: Path) -> tuple[dict | None, list[ValidationFailure]]:
    target = _rel(repo_root, path)
    try:
        record = load_json_without_duplicate_keys(path)
    except (ValueError, ValidatorConfigurationError) as exc:
        return None, [_failure(target, str(exc), "Fix the JSON record and re-run validation.")]
    failures = validate_instance(record, schema, target)
    failures.extend(_nonempty_strings(record, target))
    return record, failures


def _check_readme(repo_root: Path, root: str) -> list[ValidationFailure]:
    path = repo_root / root / "README.md"
    if path.is_symlink() or not path.is_file():
        return [_failure(f"{root}/README.md", "Registry README.md is missing or is not a regular file", f"Create a regular {root}/README.md file.")]
    if path.stat().st_size == 0:
        return [_failure(f"{root}/README.md", "Registry README.md is empty", "Document the registry layout in README.md.")]
    return []


def _casefold_collisions(entries: list[Path], repo_root: Path) -> list[ValidationFailure]:
    failures = []
    seen_names: list[str] = []
    for entry in entries:
        if find_casefold_duplicate(seen_names + [entry.name]) is not None:
            failures.append(_failure(_rel(repo_root, entry), f"Case-insensitive filename collision for '{entry.name}'", "Use unique names independent of filesystem case sensitivity."))
        seen_names.append(entry.name)
    return failures


def validate_registry_layout(repo_root: Path) -> list[ValidationFailure]:
    """Validate all governance registry layouts without reading record contents."""
    failures: list[ValidationFailure] = []
    for name, (root, fixed_file) in REGISTRIES.items():
        root_path = repo_root / root
        failures.extend(_check_readme(repo_root, root))
        if root_path.is_symlink() or not root_path.is_dir():
            failures.append(_failure(root, "Registry directory is missing or is a symbolic link", f"Create the required {root}/ directory as a regular directory."))
            continue
        entries = sorted((entry for entry in root_path.iterdir() if entry.name != "README.md"), key=lambda item: (item.name.casefold(), item.name))
        failures.extend(_casefold_collisions(entries, repo_root))
        for entry in entries:
            target = _rel(repo_root, entry)
            if entry.is_symlink():
                failures.append(_failure(target, "Symbolic links are not permitted in governance registries", "Replace the symbolic link with a regular file or directory."))
                continue
            if name in {"reviews", "decisions"}:
                if not entry.is_dir():
                    failures.append(_failure(target, "Registry root permits only bundle directories", "Move the record into a valid bundle directory."))
                    continue
                if not BUNDLE_RE.fullmatch(entry.name):
                    failures.append(_failure(target, "Bundle directory name is invalid", "Use <owner-slug>__<repository-slug>__<12-character-lowercase-sha>."))
                children = sorted(entry.iterdir(), key=lambda item: (item.name.casefold(), item.name))
                if not children:
                    failures.append(_failure(target, "Bundle directory is empty", "Add the required governance JSON record."))
                for child in children:
                    child_target = _rel(repo_root, child)
                    if child.is_symlink() or child.is_dir():
                        failures.append(_failure(child_target, "Nested directories and symbolic links are not permitted", "Use a regular JSON file directly in the bundle directory."))
                    elif fixed_file and child.name != fixed_file:
                        failures.append(_failure(child_target, f"Only '{fixed_file}' is permitted in this bundle", f"Rename the file to '{fixed_file}' and remove extra files."))
                    elif not fixed_file and (child.suffix != ".json" or not IDENTIFIER_RE.fullmatch(child.stem)):
                        failures.append(_failure(child_target, "Decision records must be named <pattern-slug>.json using a safe identifier", "Rename the record to a lowercase safe pattern slug ending in .json."))
            else:
                if entry.is_dir() or entry.suffix != ".json" or not IDENTIFIER_RE.fullmatch(entry.stem):
                    failures.append(_failure(target, "Registry permits only regular <safe-id>.json files", "Replace directories or invalid files with a lowercase safe JSON filename."))
    return failures


def _source_index(repo_root: Path, schemas: dict[str, dict]) -> dict[str, SourceBundle]:
    bundles: dict[str, SourceBundle] = {}
    root = repo_root / RECORDS_DIR
    if root.is_symlink() or not root.is_dir():
        return bundles
    for bundle_dir in sorted(root.iterdir(), key=lambda item: (item.name.casefold(), item.name)):
        if bundle_dir.name == "README.md" or not bundle_dir.is_dir() or bundle_dir.is_symlink():
            continue
        intake_path = bundle_dir / "source-intake.json"
        patterns_dir = bundle_dir / "patterns"
        try:
            intake = load_json_without_duplicate_keys(intake_path)
        except (ValueError, ValidatorConfigurationError):
            continue
        if validate_instance(intake, schemas["intake"], _rel(repo_root, intake_path)) or patterns_dir.is_symlink() or not patterns_dir.is_dir():
            continue
        patterns: dict[str, dict] = {}
        for pattern_path in sorted(patterns_dir.glob("*.json"), key=lambda item: (item.name.casefold(), item.name)):
            try:
                pattern = load_json_without_duplicate_keys(pattern_path)
            except (ValueError, ValidatorConfigurationError):
                continue
            if not validate_instance(pattern, schemas["pattern"], _rel(repo_root, pattern_path)):
                patterns[_rel(repo_root, pattern_path)] = pattern
        bundles[bundle_dir.name] = SourceBundle(bundle_dir.name, intake, patterns)
    return bundles


def _source_for(bundle_id: object, index: dict[str, SourceBundle], target: str) -> tuple[SourceBundle | None, list[ValidationFailure]]:
    source = index.get(bundle_id) if isinstance(bundle_id, str) else None
    if source is None:
        return None, [_failure(target, f"Source bundle '{bundle_id}' is missing, malformed, or unreadable", "Restore a valid Phase 3 source bundle before referencing it from governance records.")]
    return source, []


def _examined_ranges(intake: dict) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    for entry in intake.get("files_examined", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("file_path"), str):
            continue
        result[entry["file_path"]] = [parsed for value in entry.get("line_ranges", []) if isinstance(value, str) and (parsed := parse_line_range(value))]
    return result


def _load_audits(repo_root: Path, schemas: dict[str, dict], index: dict[str, SourceBundle], allowlist: set[str]) -> tuple[dict[str, tuple[dict, str]], list[ValidationFailure]]:
    audits: dict[str, tuple[dict, str]] = {}
    failures: list[ValidationFailure] = []
    root = repo_root / REGISTRIES["reviews"][0]
    if root.is_symlink() or not root.is_dir():
        return audits, failures
    seen: set[str] = set()
    for bundle_dir in sorted(root.iterdir(), key=lambda item: (item.name.casefold(), item.name)):
        path = bundle_dir / "audit-report.json"
        if bundle_dir.name == "README.md" or not path.is_file() or path.is_symlink():
            continue
        record, record_failures = _load_record(path, schemas["audit"], repo_root)
        failures.extend(record_failures)
        if record is None:
            continue
        target = _rel(repo_root, path)
        audit_id = record.get("audit_report_id")
        failures.extend(_identifier(audit_id, "audit_report_id", target))
        if isinstance(audit_id, str):
            if audit_id.casefold() in seen:
                failures.append(_failure(target, f"Duplicate case-insensitive audit_report_id '{audit_id}'", "Use a unique audit_report_id."))
            seen.add(audit_id.casefold())
            audits[audit_id] = (record, bundle_dir.name)
        source, source_failures = _source_for(record.get("source_bundle_id"), index, target)
        failures.extend(source_failures)
        if record.get("source_bundle_id") != bundle_dir.name:
            failures.append(_failure(target, "source_bundle_id does not match the audit-report directory", "Set source_bundle_id to the containing bundle ID."))
        if source is None:
            continue
        expected_intake = f"{RECORDS_DIR}/{source.bundle_id}/source-intake.json"
        if record.get("source_intake_path") != expected_intake:
            failures.append(_failure(target, "source_intake_path does not exactly reference the source bundle intake", f"Set source_intake_path to '{expected_intake}'."))
        if record.get("source_repository") != source.intake.get("repository"):
            failures.append(_failure(target, "source_repository does not match source-intake.json", "Copy repository exactly from the source intake."))
        if record.get("reviewed_commit_sha") != source.intake.get("reviewed_commit_sha"):
            failures.append(_failure(target, "reviewed_commit_sha does not match source-intake.json", "Copy the reviewed commit SHA exactly from the source intake."))
        failures.extend(_date(record.get("audit_date"), "audit_date", target))
        if isinstance(record.get("audit_date"), str) and record["audit_date"] < source.intake.get("review_date", ""):
            failures.append(_failure(target, "audit_date precedes the source intake review_date", "Use an audit_date on or after the source intake review_date."))
        license_analysis = record.get("license_analysis", {})
        if isinstance(license_analysis, dict):
            if license_analysis.get("detected_license") != source.intake.get("license"):
                failures.append(_failure(target, "license_analysis.detected_license does not match source intake license", "Copy the license exactly from source-intake.json."))
            assessment = license_analysis.get("compatibility_assessment")
            expected_review = assessment != "COMPATIBLE"
            if isinstance(assessment, str) and license_analysis.get("governor_review_required") is not expected_review:
                failures.append(_failure(target, "license compatibility assessment and governor_review_required are inconsistent", "Set governor_review_required false only for COMPATIBLE; set it true otherwise."))
        security = record.get("security_review", {})
        if isinstance(security, dict) and security.get("external_execution_performed") is not False:
            failures.append(_failure(target, "security_review.external_execution_performed must be false", "Set external_execution_performed to false."))
        examined = _examined_ranges(source.intake)
        finding_ids: set[str] = set()
        for number, finding in enumerate(record.get("findings", [])):
            if not isinstance(finding, dict):
                continue
            finding_id = finding.get("finding_id")
            failures.extend(_identifier(finding_id, f"findings[{number}].finding_id", target))
            if isinstance(finding_id, str):
                if finding_id.casefold() in finding_ids:
                    failures.append(_failure(target, f"Duplicate finding_id '{finding_id}'", "Use unique finding IDs within the audit report."))
                finding_ids.add(finding_id.casefold())
            pattern_path = finding.get("pattern_record_path")
            failures.extend(_safe_path(pattern_path, f"findings[{number}].pattern_record_path", target))
            expected_prefix = f"{RECORDS_DIR}/{source.bundle_id}/patterns/"
            if isinstance(pattern_path, str) and (not pattern_path.startswith(expected_prefix) or pattern_path not in source.patterns):
                failures.append(_failure(target, f"findings[{number}].pattern_record_path does not reference an existing pattern in the same source bundle", "Reference a pattern JSON record from the audit source bundle."))
            failures.extend(_valid_specialist(finding.get("assigned_specialist"), f"findings[{number}].assigned_specialist", target, allowlist))
            pattern = source.patterns.get(pattern_path) if isinstance(pattern_path, str) else None
            if pattern and finding.get("assigned_specialist") != pattern.get("assigned_specialist"):
                failures.append(_failure(target, f"findings[{number}].assigned_specialist does not match the source pattern", "Use the source pattern assigned_specialist exactly."))
            evidence = finding.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                failures.append(_failure(target, f"findings[{number}].evidence must contain at least one item", "Add at least one traceable evidence item."))
                continue
            for evidence_number, item in enumerate(evidence):
                if not isinstance(item, dict):
                    continue
                source_file = item.get("source_file")
                line_range = item.get("line_range")
                if source_file not in examined:
                    failures.append(_failure(target, f"findings[{number}].evidence[{evidence_number}].source_file is not in files_examined", "Use a source file listed in source-intake.json files_examined."))
                parsed = parse_line_range(line_range) if isinstance(line_range, str) else None
                if parsed is None or parsed[0] < 1 or parsed[0] > parsed[1]:
                    failures.append(_failure(target, f"findings[{number}].evidence[{evidence_number}].line_range is invalid", "Use a positive ordered start-end line range."))
                elif source_file in examined and not is_range_covered(*parsed, examined[source_file]):
                    failures.append(_failure(target, f"findings[{number}].evidence[{evidence_number}].line_range is outside files_examined coverage", "Use a line range covered by source-intake.json files_examined."))
                if item.get("bucket") == "RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION" and source.intake.get("runtime_behavior_tested") is not True:
                    failures.append(_failure(target, "Runtime-confirmed evidence requires source intake runtime_behavior_tested: true", "Use a non-runtime evidence bucket or record authorized isolated validation in source intake."))
    return audits, failures


def _load_decisions(repo_root: Path, schemas: dict[str, dict], index: dict[str, SourceBundle], audits: dict[str, tuple[dict, str]], allowlist: set[str]) -> tuple[dict[str, tuple[dict, str]], list[ValidationFailure]]:
    decisions: dict[str, tuple[dict, str]] = {}
    failures: list[ValidationFailure] = []
    root = repo_root / REGISTRIES["decisions"][0]
    if root.is_symlink() or not root.is_dir():
        return decisions, failures
    seen: set[str] = set()
    for bundle_dir in sorted(root.iterdir(), key=lambda item: (item.name.casefold(), item.name)):
        if bundle_dir.name == "README.md" or not bundle_dir.is_dir() or bundle_dir.is_symlink():
            continue
        for path in sorted(bundle_dir.glob("*.json"), key=lambda item: (item.name.casefold(), item.name)):
            record, record_failures = _load_record(path, schemas["decision"], repo_root)
            failures.extend(record_failures)
            if record is None:
                continue
            target = _rel(repo_root, path)
            decision_id = record.get("decision_id")
            failures.extend(_identifier(decision_id, "decision_id", target))
            if isinstance(decision_id, str):
                if decision_id.casefold() in seen:
                    failures.append(_failure(target, f"Duplicate case-insensitive decision_id '{decision_id}'", "Use a unique decision_id."))
                seen.add(decision_id.casefold())
                decisions[decision_id] = (record, bundle_dir.name)
            source, source_failures = _source_for(record.get("source_bundle_id"), index, target)
            failures.extend(source_failures)
            if record.get("source_bundle_id") != bundle_dir.name:
                failures.append(_failure(target, "source_bundle_id does not match the decision directory", "Set source_bundle_id to the containing bundle ID."))
            pattern_path = record.get("pattern_record_path")
            failures.extend(_safe_path(pattern_path, "pattern_record_path", target))
            pattern = source.patterns.get(pattern_path) if source and isinstance(pattern_path, str) else None
            if source and pattern is None:
                failures.append(_failure(target, "pattern_record_path does not reference a pattern in the same source bundle", "Reference an existing pattern record from the decision source bundle."))
            if isinstance(pattern_path, str) and path.name != Path(pattern_path).name:
                failures.append(_failure(target, "Decision filename does not match the referenced pattern filename", f"Rename the decision file to '{Path(pattern_path).name}'."))
            failures.extend(_valid_specialist(record.get("assigned_specialist"), "assigned_specialist", target, allowlist))
            audit_pair = audits.get(record.get("audit_report_id")) if isinstance(record.get("audit_report_id"), str) else None
            if audit_pair is None or audit_pair[1] != bundle_dir.name:
                failures.append(_failure(target, "audit_report_id does not resolve to an audit report in this source bundle", "Reference an existing audit report for the same source bundle."))
                audit = None
            else:
                audit = audit_pair[0]
            if pattern and record.get("assigned_specialist") != pattern.get("assigned_specialist"):
                failures.append(_failure(target, "assigned_specialist does not match the source pattern", "Use the source pattern assigned_specialist exactly."))
            if audit and pattern_path not in {item.get("pattern_record_path") for item in audit.get("findings", []) if isinstance(item, dict)}:
                failures.append(_failure(target, "Referenced audit report has no finding for pattern_record_path", "Add a matching audit finding or reference the correct audit report."))
            if audit and pattern_path:
                audit_specialists = {item.get("assigned_specialist") for item in audit.get("findings", []) if isinstance(item, dict) and item.get("pattern_record_path") == pattern_path}
                if audit_specialists and record.get("assigned_specialist") not in audit_specialists:
                    failures.append(_failure(target, "assigned_specialist does not match the corresponding audit finding", "Use the audit finding assigned_specialist exactly."))
            failures.extend(_date(record.get("decision_date"), "decision_date", target))
            maintainer = record.get("maintainer_decision", {})
            reviews = record.get("reviews", {})
            if isinstance(maintainer, dict) and maintainer.get("decision_date") != record.get("decision_date"):
                failures.append(_failure(target, "maintainer_decision.decision_date must equal decision_date", "Use the top-level decision_date in maintainer_decision."))
            if audit and isinstance(record.get("decision_date"), str) and record["decision_date"] < audit.get("audit_date", ""):
                failures.append(_failure(target, "decision_date precedes the audit_date", "Use a decision_date on or after the audit_date."))
            if isinstance(reviews, dict):
                for reviewer, review in reviews.items():
                    if isinstance(review, dict):
                        failures.extend(_date(review.get("review_date"), f"reviews.{reviewer}.review_date", target))
                        if isinstance(review.get("review_date"), str) and isinstance(record.get("decision_date"), str) and review["review_date"] > record["decision_date"]:
                            failures.append(_failure(target, f"reviews.{reviewer}.review_date is after decision_date", "Use a reviewer date on or before decision_date."))
            if isinstance(maintainer, dict) and record.get("decision_status") != maintainer.get("status"):
                failures.append(_failure(target, "decision_status must equal maintainer_decision.status", "Make the top-level and Maintainer statuses identical."))
            statuses = {name: review.get("status") for name, review in reviews.items() if isinstance(review, dict)} if isinstance(reviews, dict) else {}
            status = record.get("decision_status")
            if status != "PENDING" and "PENDING" in statuses.values():
                failures.append(_failure(target, "Final decision retains a PENDING reviewer", "Complete reviewer statuses before finalizing the decision."))
            restriction = record.get("implementation_restriction")
            if status in {"REJECTED", "BLOCKED"} and restriction != "IMPLEMENTATION_BLOCKED":
                failures.append(_failure(target, f"{status} decisions require IMPLEMENTATION_BLOCKED", "Set implementation_restriction to IMPLEMENTATION_BLOCKED."))
            if audit and isinstance(audit.get("license_analysis"), dict) and audit["license_analysis"].get("governor_review_required") and statuses.get("governor") == "NOT_REQUIRED":
                failures.append(_failure(target, "Governor may not be NOT_REQUIRED when the audit requires Governor review", "Record Governor APPROVED, PENDING, REVISION_REQUIRED, or BLOCKED as appropriate."))
            if status == "APPROVED":
                required = {"arbiter": "APPROVED", "steward": "APPROVED"}
                governor_required = bool(audit and audit.get("license_analysis", {}).get("governor_review_required"))
                required["governor"] = "APPROVED" if governor_required else None
                for reviewer, required_status in required.items():
                    actual = statuses.get(reviewer)
                    if required_status and actual != required_status:
                        failures.append(_failure(target, f"APPROVED requires {reviewer} {required_status}", f"Set reviews.{reviewer}.status to {required_status}."))
                    if reviewer == "governor" and not governor_required and actual not in {"APPROVED", "NOT_REQUIRED"}:
                        failures.append(_failure(target, "APPROVED requires Governor APPROVED or NOT_REQUIRED", "Set reviews.governor.status to APPROVED or NOT_REQUIRED."))
                if any(value in {"REVISION_REQUIRED", "BLOCKED"} for value in statuses.values()) or restriction == "IMPLEMENTATION_BLOCKED":
                    failures.append(_failure(target, "APPROVED decision has a blocking reviewer status or implementation restriction", "Resolve blocking review results and use a non-blocked restriction."))
                if pattern and pattern.get("classification") == "OUT_OF_SCOPE":
                    failures.append(_failure(target, "OUT_OF_SCOPE patterns must not receive APPROVED decisions", "Use a non-approved decision status."))
                if pattern and pattern.get("classification") == "REFERENCE_ONLY" and restriction != "CONCEPT_ONLY":
                    failures.append(_failure(target, "Approved REFERENCE_ONLY patterns require CONCEPT_ONLY", "Set implementation_restriction to CONCEPT_ONLY."))
    return decisions, failures


def _load_proposals(repo_root: Path, schemas: dict[str, dict], index: dict[str, SourceBundle], audits: dict[str, tuple[dict, str]], decisions: dict[str, tuple[dict, str]], allowlist: set[str]) -> tuple[dict[str, dict], list[ValidationFailure]]:
    proposals: dict[str, dict] = {}
    failures: list[ValidationFailure] = []
    root = repo_root / REGISTRIES["proposals"][0]
    if root.is_symlink() or not root.is_dir():
        return proposals, failures
    seen: set[str] = set()
    for path in sorted(root.glob("*.json"), key=lambda item: (item.name.casefold(), item.name)):
        record, record_failures = _load_record(path, schemas["proposal"], repo_root)
        failures.extend(record_failures)
        if record is None:
            continue
        target = _rel(repo_root, path)
        proposal_id = record.get("proposal_id")
        failures.extend(_identifier(proposal_id, "proposal_id", target))
        if isinstance(proposal_id, str):
            if proposal_id.casefold() in seen:
                failures.append(_failure(target, f"Duplicate case-insensitive proposal_id '{proposal_id}'", "Use a unique proposal_id."))
            seen.add(proposal_id.casefold())
            proposals[proposal_id] = record
            if path.name != f"{proposal_id}.json":
                failures.append(_failure(target, "Proposal filename does not match proposal_id", f"Rename the file to '{proposal_id}.json'."))
        audit_ids = record.get("source_audit_ids")
        if not isinstance(audit_ids, list) or not audit_ids:
            failures.append(_failure(target, "source_audit_ids must contain at least one audit ID", "Add one or more referenced audit_report_id values."))
        elif len({item.casefold() for item in audit_ids if isinstance(item, str)}) != len(audit_ids):
            failures.append(_failure(target, "source_audit_ids contains duplicate audit IDs", "Remove duplicate audit IDs."))
        for audit_id in audit_ids if isinstance(audit_ids, list) else []:
            if audit_id not in audits:
                failures.append(_failure(target, f"source_audit_id '{audit_id}' does not resolve", "Reference an existing audit_report_id."))
        selected = record.get("selected_patterns")
        if not isinstance(selected, list) or not selected:
            failures.append(_failure(target, "selected_patterns must contain at least one item", "Add an approved decision and pattern selection."))
            continue
        decision_ids: set[str] = set()
        pattern_paths: set[str] = set()
        for number, item in enumerate(selected):
            if not isinstance(item, dict):
                continue
            decision_id = item.get("decision_id")
            pattern_path = item.get("pattern_record_path")
            if isinstance(decision_id, str) and decision_id.casefold() in decision_ids:
                failures.append(_failure(target, f"selected_patterns[{number}].decision_id is duplicated", "Select each decision only once."))
            if isinstance(decision_id, str):
                decision_ids.add(decision_id.casefold())
            if isinstance(pattern_path, str) and pattern_path.casefold() in pattern_paths:
                failures.append(_failure(target, f"selected_patterns[{number}].pattern_record_path is duplicated", "Select each pattern only once."))
            if isinstance(pattern_path, str):
                pattern_paths.add(pattern_path.casefold())
            pair = decisions.get(decision_id) if isinstance(decision_id, str) else None
            if pair is None:
                failures.append(_failure(target, f"selected_patterns[{number}].decision_id does not resolve", "Reference an existing approved decision."))
                continue
            decision, bundle_id = pair
            if decision.get("decision_status") != "APPROVED" or decision.get("implementation_restriction") == "IMPLEMENTATION_BLOCKED":
                failures.append(_failure(target, f"selected_patterns[{number}] must reference an approved non-blocked decision", "Reference a decision with decision_status APPROVED and a non-blocked restriction."))
            if decision.get("audit_report_id") not in audit_ids:
                failures.append(_failure(target, f"selected_patterns[{number}] decision audit is absent from source_audit_ids", "Add the decision audit_report_id to source_audit_ids."))
            if pattern_path != decision.get("pattern_record_path"):
                failures.append(_failure(target, f"selected_patterns[{number}].pattern_record_path does not match decision", "Copy pattern_record_path exactly from the referenced decision."))
            failures.extend(_valid_specialist(item.get("owner_specialist"), f"selected_patterns[{number}].owner_specialist", target, allowlist))
            if item.get("owner_specialist") != decision.get("assigned_specialist"):
                failures.append(_failure(target, f"selected_patterns[{number}].owner_specialist does not match decision", "Use the decision assigned_specialist as owner_specialist."))
            source = index.get(bundle_id)
            pattern = source.patterns.get(pattern_path) if source and isinstance(pattern_path, str) else None
            mechanism = item.get("evolution_mechanism")
            restriction = decision.get("implementation_restriction")
            if restriction == "CONCEPT_ONLY" and mechanism != "CONCEPTUAL_ADAPTATION":
                failures.append(_failure(target, "CONCEPT_ONLY decisions permit only CONCEPTUAL_ADAPTATION", "Use evolution_mechanism CONCEPTUAL_ADAPTATION."))
            if restriction == "FRESH_IMPLEMENTATION_REQUIRED" and mechanism == "DIRECT_REUSE_REVIEW_REQUIRED":
                failures.append(_failure(target, "FRESH_IMPLEMENTATION_REQUIRED must not use DIRECT_REUSE_REVIEW_REQUIRED", "Use SAFE_REWRITE or CONCEPTUAL_ADAPTATION."))
            if mechanism == "DIRECT_REUSE_REVIEW_REQUIRED" and (restriction != "CODE_REUSE_REVIEW_REQUIRED" or not pattern or pattern.get("classification") != "CODE_REUSE_REVIEW_REQUIRED"):
                failures.append(_failure(target, "DIRECT_REUSE_REVIEW_REQUIRED requires a code-reuse decision and source classification", "Use CODE_REUSE_REVIEW_REQUIRED for both the decision restriction and source pattern classification."))
            if mechanism == "TEST_CORPUS_ADAPTATION" and (not pattern or pattern.get("classification") != "TEST_CORPUS_CANDIDATE"):
                failures.append(_failure(target, "TEST_CORPUS_ADAPTATION requires a TEST_CORPUS_CANDIDATE source pattern", "Use a test-corpus candidate pattern or another evolution mechanism."))
    return proposals, failures


def _load_promotions(repo_root: Path, schemas: dict[str, dict], index: dict[str, SourceBundle], decisions: dict[str, tuple[dict, str]], proposals: dict[str, dict], allowlist: set[str]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    root = repo_root / REGISTRIES["promotions"][0]
    if root.is_symlink() or not root.is_dir():
        return failures
    promotion_ids: set[str] = set()
    catalog_ids: set[str] = set()
    for path in sorted(root.glob("*.json"), key=lambda item: (item.name.casefold(), item.name)):
        record, record_failures = _load_record(path, schemas["promotion"], repo_root)
        failures.extend(record_failures)
        if record is None:
            continue
        target = _rel(repo_root, path)
        for field, seen in (("promotion_id", promotion_ids), ("catalog_pattern_id", catalog_ids)):
            value = record.get(field)
            failures.extend(_identifier(value, field, target))
            if isinstance(value, str):
                if value.casefold() in seen:
                    failures.append(_failure(target, f"Duplicate case-insensitive {field} '{value}'", f"Use a unique {field}."))
                seen.add(value.casefold())
        catalog_id = record.get("catalog_pattern_id")
        if isinstance(catalog_id, str) and path.name != f"{catalog_id}.json":
            failures.append(_failure(target, "Promotion filename does not match catalog_pattern_id", f"Rename the file to '{catalog_id}.json'."))
        pair = decisions.get(record.get("decision_id")) if isinstance(record.get("decision_id"), str) else None
        if pair is None or pair[0].get("decision_status") != "APPROVED":
            failures.append(_failure(target, "decision_id must resolve to an approved decision", "Reference an existing approved governance decision."))
            continue
        decision, bundle_id = pair
        proposal = proposals.get(record.get("proposal_id")) if isinstance(record.get("proposal_id"), str) else None
        if proposal is None or proposal.get("proposal_status") != "APPROVED":
            failures.append(_failure(target, "proposal_id must resolve to an approved proposal", "Reference an existing approved evolution proposal."))
        elif not any(isinstance(item, dict) and item.get("decision_id") == record.get("decision_id") and item.get("pattern_record_path") == record.get("pattern_record_path") for item in proposal.get("selected_patterns", [])):
            failures.append(_failure(target, "Proposal does not contain the exact decision and pattern pair", "Select the referenced decision and pattern in the proposal."))
        if record.get("source_bundle_id") != bundle_id:
            failures.append(_failure(target, "source_bundle_id does not match the decision", "Copy source_bundle_id exactly from the decision."))
        if record.get("pattern_record_path") != decision.get("pattern_record_path"):
            failures.append(_failure(target, "pattern_record_path does not match the decision", "Copy pattern_record_path exactly from the decision."))
        failures.extend(_valid_specialist(record.get("assigned_specialist"), "assigned_specialist", target, allowlist))
        if record.get("assigned_specialist") != decision.get("assigned_specialist"):
            failures.append(_failure(target, "assigned_specialist does not match the decision", "Copy assigned_specialist exactly from the decision."))
        source = index.get(bundle_id)
        pattern = source.patterns.get(record.get("pattern_record_path")) if source and isinstance(record.get("pattern_record_path"), str) else None
        if pattern and record.get("assigned_specialist") != pattern.get("assigned_specialist"):
            failures.append(_failure(target, "assigned_specialist does not match the source pattern", "Use the source pattern assigned_specialist exactly."))
        if proposal:
            selected = next((item for item in proposal.get("selected_patterns", []) if isinstance(item, dict) and item.get("decision_id") == record.get("decision_id") and item.get("pattern_record_path") == record.get("pattern_record_path")), None)
            if selected and record.get("assigned_specialist") != selected.get("owner_specialist"):
                failures.append(_failure(target, "assigned_specialist does not match the proposal owner_specialist", "Use the proposal owner_specialist exactly."))
        if source and pattern:
            trace = record.get("source_traceability", {})
            expected = {"repository": source.intake.get("repository"), "reviewed_commit_sha": source.intake.get("reviewed_commit_sha"), "source_file": pattern.get("source_file"), "line_range": pattern.get("line_range")}
            for key, value in expected.items():
                if not isinstance(trace, dict) or trace.get(key) != value:
                    failures.append(_failure(target, f"source_traceability.{key} does not match source records", f"Copy source {key} exactly from the source record."))
            attribution = record.get("license_and_attribution", {})
            if not isinstance(attribution, dict) or attribution.get("original_license") != source.intake.get("license"):
                failures.append(_failure(target, "license_and_attribution.original_license does not match source intake", "Copy the source intake license exactly."))
        failures.extend(_date(record.get("approval_date"), "approval_date", target))
        if isinstance(record.get("approval_date"), str) and record["approval_date"] < decision.get("decision_date", ""):
            failures.append(_failure(target, "approval_date precedes the governance decision date", "Use an approval_date on or after decision_date."))
        if record.get("automatic_promotion") is not False:
            failures.append(_failure(target, "automatic_promotion must be false", "Set automatic_promotion to false."))
    return failures


def validate_repository(repo_root: Path) -> list[ValidationFailure]:
    """Return deterministic Phase 4B governance-record validation failures."""
    schemas = _load_schemas(repo_root)
    failures = validate_registry_layout(repo_root)
    index = _source_index(repo_root, schemas)
    allowlist = _specialist_allowlist(schemas["pattern"])
    audits, audit_failures = _load_audits(repo_root, schemas, index, allowlist)
    decisions, decision_failures = _load_decisions(repo_root, schemas, index, audits, allowlist)
    proposals, proposal_failures = _load_proposals(repo_root, schemas, index, audits, decisions, allowlist)
    promotion_failures = _load_promotions(repo_root, schemas, index, decisions, proposals, allowlist)
    failures.extend(audit_failures + decision_failures + proposal_failures + promotion_failures)
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


def _print_failure(failure: ValidationFailure) -> None:
    print(f"[FAIL] {failure.target}: {failure.reason}")
    print(f"       Remediation: {failure.remediation}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Artificer Governance-Record Validator")
    parser.add_argument("--repo-root", default=None, help="Repository root (default: derived from script location)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parent.parent
    for number, title in enumerate(("Governance Registry Layout", "Audit Reports", "Governance Decisions", "Evolution Proposals", "Promotion Records", "Cross-Record Integrity"), 1):
        print(f"[{number}] {title}")
    try:
        failures = validate_repository(repo_root)
    except ValidatorConfigurationError as exc:
        print(f"[FAIL] Configuration error: {exc}")
        print("       Remediation: Restore valid Phase 3 and Phase 4 schema contracts.")
        return 2
    if failures:
        for failure in failures:
            _print_failure(failure)
        print("[7] Summary")
        print(f"Validation Failed: {len(failures)} issue(s) found.")
        return 1
    print("[7] Summary")
    print("Validation Passed: All Artificer governance records are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
