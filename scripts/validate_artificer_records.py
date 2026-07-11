#!/usr/bin/env python3
"""Artificer Record-Instance Validator (Phase 3).

Validates committed source-intake and pattern-record JSON instances against
the Phase 1 schemas without network access, subprocess execution, or
external dependencies.

Exit codes:
  0 = all record bundles valid
  1 = one or more record-instance or cross-record violations
  2 = invalid CLI usage or validator/schema configuration failure
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_DIR = "internal/artificer"
SOURCE_INTAKE_SCHEMA_PATH = f"{SCHEMA_DIR}/SOURCE_INTAKE_SCHEMA.json"
PATTERN_SCHEMA_PATH = f"{SCHEMA_DIR}/PATTERN_SCHEMA.json"
RECORDS_DIR = "internal/artificer/records"
RECORDS_README = f"{RECORDS_DIR}/README.md"
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MiB

# Draft-7 keywords supported as validation rules.
SUPPORTED_VALIDATION_KEYWORDS = frozenset(
    [
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "pattern",
        "format",
    ]
)

# Annotation keywords — present in schemas but never treated as validation rules.
ANNOTATION_KEYWORDS = frozenset(["$schema", "title", "description"])

# Supported types
SUPPORTED_TYPES = frozenset(["object", "array", "string", "boolean"])

# Supported formats
SUPPORTED_FORMATS = frozenset(["uri", "date"])

# Pattern classifications that require license_implications.
LICENSE_REQUIRED_CLASSIFICATIONS = frozenset(
    ["ADAPTED_PATTERN", "CODE_REUSE_REVIEW_REQUIRED", "TEST_CORPUS_CANDIDATE"]
)

# Control characters (NUL and ASCII control range)
_CONTROL_RE = re.compile(r"[\x00-\x1f]")

# ---------------------------------------------------------------------------
# Structured failure model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationFailure:
    target: str
    reason: str
    remediation: str


class ValidatorConfigurationError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------


def load_json_without_duplicate_keys(path: Path) -> dict:
    """Load a JSON file and reject duplicate keys, non-UTF-8 encoding,
    empty files, files exceeding the size limit, symbolic links, and
    top-level non-objects.

    Returns a dict on success.
    Raises ValidatorConfigurationError for configuration-level problems.
    Raises ValueError for record-level problems (malformed/invalid content).
    """
    if path.is_symlink():
        raise ValueError(f"{path}: symbolic links are not permitted for record files")

    if not path.is_file():
        raise ValueError(f"{path}: file does not exist or is not a regular file")

    size = path.stat().st_size
    if size == 0:
        raise ValueError(f"{path}: file is empty")
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"{path}: file exceeds maximum size of {MAX_FILE_SIZE} bytes ({size} bytes)"
        )

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"{path}: cannot read file: {exc}") from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: file is not valid UTF-8: {exc}") from exc

    seen_keys: list[str] = []

    def object_pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(
                    f"{path}: duplicate JSON key '{key}'"
                )
            result[key] = value
            seen_keys.append(key)
        return result

    try:
        data = json.loads(text, object_pairs_hook=object_pairs_hook)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: malformed JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top-level JSON value must be an object, got {type(data).__name__}"
        )

    return data


# ---------------------------------------------------------------------------
# Schema subset validator
# ---------------------------------------------------------------------------

def validate_schema_configuration(schema: dict, schema_target: str) -> None:
    """Validate that the schema is well-formed against our internal constraints."""
    if schema.get("$schema") != "http://json-schema.org/draft-07/schema#":
        raise ValidatorConfigurationError(f"{schema_target}: non-Draft-7 $schema")

    def check_node(node: object, path: str) -> None:
        if not isinstance(node, dict):
            return

        for key in node:
            if key not in ANNOTATION_KEYWORDS and key not in SUPPORTED_VALIDATION_KEYWORDS:
                raise ValidatorConfigurationError(f"{schema_target} at {path}: unsupported keyword '{key}'")

        t = node.get("type")
        if t is not None:
            if t not in ("object", "array", "string", "boolean"):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: unsupported schema type '{t}'")

        fmt = node.get("format")
        if fmt is not None:
            if fmt not in ("uri", "date"):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: unsupported format '{fmt}'")

        pat = node.get("pattern")
        if pat is not None:
            try:
                re.compile(pat)
            except re.error as e:
                raise ValidatorConfigurationError(f"{schema_target} at {path}: invalid regex '{pat}': {e}")

        props = node.get("properties")
        if props is not None:
            if not isinstance(props, dict):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: 'properties' must be an object")
            for k, v in props.items():
                check_node(v, f"{path}.properties.{k}")

        req = node.get("required")
        if req is not None:
            if not isinstance(req, list):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: 'required' must be an array")
            if props is not None:
                for r in req:
                    if r not in props:
                        raise ValidatorConfigurationError(f"{schema_target} at {path}: required field '{r}' not declared in properties")

        items = node.get("items")
        if items is not None:
            if not isinstance(items, dict):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: 'items' must be an object")
            check_node(items, f"{path}.items")

        en = node.get("enum")
        if en is not None:
            if not isinstance(en, list):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: 'enum' must be an array")

        addp = node.get("additionalProperties")
        if addp is not None:
            if not isinstance(addp, bool):
                raise ValidatorConfigurationError(f"{schema_target} at {path}: 'additionalProperties' must be a boolean")

    check_node(schema, "$")


def _validate_type(value: object, expected_type: str, path: str) -> list[str]:
    """Return error strings for type mismatches."""
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
    }
    py_type = type_map.get(expected_type)
    if py_type is None:
        return [f"{path}: unsupported schema type '{expected_type}'"]
    # Booleans are a subtype of int in Python — disambiguate
    if expected_type == "boolean":
        if not isinstance(value, bool):
            return [f"{path}: expected boolean, got {type(value).__name__}"]
    elif expected_type == "string":
        if not isinstance(value, str):
            return [f"{path}: expected string, got {type(value).__name__}"]
    elif expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object, got {type(value).__name__}"]
    elif expected_type == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array, got {type(value).__name__}"]
    return []


def _validate_format(value: str, fmt: str, path: str) -> list[str]:
    """Validate string format constraints."""
    if fmt == "uri":
        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                return [f"{path}: value '{value}' does not parse as a URI"]
        except Exception:
            return [f"{path}: value '{value}' is not a valid URI"]
    elif fmt == "date":
        try:
            date.fromisoformat(value)
        except (ValueError, TypeError):
            return [f"{path}: value '{value}' is not a valid ISO date (YYYY-MM-DD)"]
    return []


def validate_instance(
    instance: object, schema: dict, target: str = "$"
) -> list[ValidationFailure]:
    """Apply a Draft-7 schema subset to an instance.

    Returns a list of ValidationFailure objects.
    """
    failures = []

    def _validate(value: object, node: dict, path: str) -> None:
        if not isinstance(node, dict):
            return

        # type
        if "type" in node:
            errs = _validate_type(value, node["type"], path)
            for err in errs:
                failures.append(
                    ValidationFailure(
                        target=target,
                        reason=err,
                        remediation=f"Correct the value at '{path}' to match the schema type '{node['type']}'.",
                    )
                )
                return  # Can't validate further if type is wrong

        # enum
        if "enum" in node and isinstance(node["enum"], list):
            if value not in node["enum"]:
                failures.append(
                    ValidationFailure(
                        target=target,
                        reason=f"{path}: value {value!r} is not one of the allowed enum values {node['enum']}",
                        remediation=f"Set '{path}' to one of: {', '.join(str(e) for e in node['enum'])}.",
                    )
                )

        # pattern
        if "pattern" in node and isinstance(value, str):
            try:
                if not re.search(node["pattern"], value):
                    failures.append(
                        ValidationFailure(
                            target=target,
                            reason=f"{path}: value '{value}' does not match pattern '{node['pattern']}'",
                            remediation=f"Update the value at '{path}' to match the required pattern.",
                        )
                    )
            except re.error as exc:
                failures.append(
                    ValidationFailure(
                        target=target,
                        reason=f"{path}: schema pattern '{node['pattern']}' is invalid regex: {exc}",
                        remediation="Fix the schema pattern.",
                    )
                )

        # format
        if "format" in node and isinstance(value, str):
            errs = _validate_format(value, node["format"], path)
            for err in errs:
                failures.append(
                    ValidationFailure(
                        target=target,
                        reason=err,
                        remediation=f"Fix the value at '{path}' to satisfy format '{node['format']}'.",
                    )
                )

        # properties + required + additionalProperties
        if isinstance(value, dict):
            props = node.get("properties", {})
            required = node.get("required", [])
            additional = node.get("additionalProperties", True)

            for req in required:
                if req not in value:
                    failures.append(
                        ValidationFailure(
                            target=target,
                            reason=f"{path}: missing required field '{req}'",
                            remediation=f"Add the required field '{req}' to the record.",
                        )
                    )

            for key, child_value in value.items():
                if key in props:
                    _validate(child_value, props[key], f"{path}.{key}")
                elif additional is False:
                    failures.append(
                        ValidationFailure(
                            target=target,
                            reason=f"{path}: unexpected additional property '{key}'",
                            remediation=f"Remove the property '{key}' or add it to the schema.",
                        )
                    )

        # items (array)
        if isinstance(value, list) and "items" in node:
            for i, item in enumerate(value):
                _validate(item, node["items"], f"{path}[{i}]")

    _validate(instance, schema, "$")
    return failures


# ---------------------------------------------------------------------------
# Slug normalization and bundle ID derivation
# ---------------------------------------------------------------------------


def slugify(s: str) -> str:
    """Normalize a string to a safe slug.

    Rules:
    - Convert to lowercase
    - Preserve a-z, 0-9, '.', '_', '-'
    - Replace other runs of characters with '-'
    - Trim leading and trailing '-'
    """
    s = s.lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    return s.strip("-")


def derive_bundle_id(repository: str, reviewed_commit_sha: str) -> str:
    """Derive the expected bundle directory name from repository and SHA."""
    parts = repository.split("/", 1)
    owner = slugify(parts[0]) if len(parts) >= 1 else ""
    repo = slugify(parts[1]) if len(parts) >= 2 else ""
    sha12 = reviewed_commit_sha[:12].lower()
    return f"{owner}__{repo}__{sha12}"


# ---------------------------------------------------------------------------
# Safe path validation
# ---------------------------------------------------------------------------

_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def validate_safe_file_path(value: str, path_field: str, target: str) -> list[ValidationFailure]:
    """Validate that a file path is safe, relative, and POSIX-style."""
    failures = []

    def _fail(reason: str, rem: str) -> None:
        failures.append(ValidationFailure(target=target, reason=reason, remediation=rem))

    if not value or not value.strip():
        _fail(
            f"{path_field}: file path must be non-empty",
            "Provide a non-empty relative file path.",
        )
        return failures

    if _CONTROL_RE.search(value):
        _fail(
            f"{path_field}: '{value}' contains NUL or control characters",
            "Remove control characters from the file path.",
        )
        return failures

    if "\\" in value:
        _fail(
            f"{path_field}: '{value}' contains backslashes; use '/' separators",
            "Replace backslashes with forward slashes.",
        )
        return failures

    if value.startswith("/"):
        _fail(
            f"{path_field}: '{value}' is absolute; must be relative",
            "Use a relative path without a leading '/'.",
        )
        return failures

    if _WINDOWS_DRIVE_RE.match(value):
        _fail(
            f"{path_field}: '{value}' contains a Windows drive prefix",
            "Use a POSIX-style relative path.",
        )
        return failures

    parts = value.split("/")
    for part in parts:
        if part == "..":
            _fail(
                f"{path_field}: '{value}' contains parent traversal '..'",
                "Remove '..' components from the path.",
            )
            return failures
        if part == ".":
            _fail(
                f"{path_field}: '{value}' contains '.' path component",
                "Remove '.' path components.",
            )
            return failures

    # Check for bundle-directory traversal (record isolation)
    if "internal/artificer/records" in value:
        _fail(
            f"{path_field}: '{value}' references the record registry path",
            "File paths must not reference the internal record registry.",
        )

    return failures


# ---------------------------------------------------------------------------
# Line range helpers
# ---------------------------------------------------------------------------


def parse_line_range(range_str: str) -> tuple[int, int] | None:
    """Parse 'start-end' string into (start, end) ints. Returns None on failure."""
    parts = range_str.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        return None
    return (start, end)


def is_range_covered(
    pattern_start: int, pattern_end: int, examined_ranges: list[tuple[int, int]]
) -> bool:
    """Return True if [pattern_start, pattern_end] is covered by at least one examined range."""
    for (es, ee) in examined_ranges:
        if es <= pattern_start and pattern_end <= ee:
            return True
    return False


# ---------------------------------------------------------------------------
# Section 1: Registry layout
# ---------------------------------------------------------------------------


def validate_registry_layout(repo_root: Path) -> list[ValidationFailure]:
    """Verify registry directory exists and contains only README.md and bundle dirs."""
    failures = []
    records_path = repo_root / RECORDS_DIR

    # README must exist
    readme_path = repo_root / RECORDS_README
    if not readme_path.is_file():
        failures.append(
            ValidationFailure(
                target=RECORDS_README,
                reason="Records README.md is missing from the registry root.",
                remediation=f"Create {RECORDS_README} documenting the registry layout.",
            )
        )

    if not records_path.is_dir():
        # If records dir itself is missing, not much else to check
        return failures

    # Check that the registry root contains only README.md and directories
    for entry in records_path.iterdir():
        if entry.name == "README.md":
            continue
        if entry.is_dir():
            # Bundle directories are allowed — validated later
            continue
        # Any other file at the registry root is unexpected
        rel = str(entry.relative_to(repo_root)).replace("\\", "/")
        failures.append(
            ValidationFailure(
                target=rel,
                reason=f"Unexpected file '{entry.name}' found at registry root; only README.md and bundle directories are allowed.",
                remediation="Remove the unexpected file or move it into a bundle directory.",
            )
        )

    return failures


# ---------------------------------------------------------------------------
# Section 2 & 3: Source-intake and pattern instance validation
# ---------------------------------------------------------------------------


def _validate_source_intake_semantics(
    instance: dict, target: str
) -> list[ValidationFailure]:
    """Enforce source-intake semantic rules after schema validation."""
    failures = []

    def _fail(reason: str, rem: str) -> None:
        failures.append(ValidationFailure(target=target, reason=reason, remediation=rem))

    # Non-empty required strings
    for field in [
        "repository",
        "repository_owner",
        "canonical_url",
        "license",
        "reviewed_commit_sha",
        "review_date",
        "source_confidence",
    ]:
        val = instance.get(field, "")
        if isinstance(val, str) and not val.strip():
            _fail(
                f"'{field}' must not be empty after trimming",
                f"Provide a non-empty value for '{field}'.",
            )

    # Optional default_branch — non-empty when present
    if "default_branch" in instance:
        db = instance["default_branch"]
        if isinstance(db, str) and not db.strip():
            _fail(
                "'default_branch' must be non-empty when present",
                "Provide a non-empty branch name or omit 'default_branch'.",
            )

    # Repository format: owner/repository
    repo = instance.get("repository", "")
    if isinstance(repo, str):
        parts = repo.split("/")
        if len(parts) != 2:
            _fail(
                f"'repository' must be in 'owner/repository' format, got '{repo}'",
                "Use exactly one '/' separator, e.g. 'example-org/example-repo'.",
            )
        else:
            owner_part, repo_part = parts
            if not owner_part.strip() or not repo_part.strip():
                _fail(
                    f"'repository' owner or repository component is empty in '{repo}'",
                    "Provide non-empty owner and repository components.",
                )
            elif owner_part == "." or owner_part == "..":
                _fail(
                    f"'repository' owner component '{owner_part}' is invalid",
                    "Use a valid owner name, not '.' or '..'.",
                )
            elif repo_part == "." or repo_part == "..":
                _fail(
                    f"'repository' name component '{repo_part}' is invalid",
                    "Use a valid repository name, not '.' or '..'.",
                )

    # Repository owner consistency
    repo_owner = instance.get("repository_owner", "")
    if isinstance(repo, str) and "/" in repo and isinstance(repo_owner, str):
        expected_owner = repo.split("/")[0]
        if expected_owner.lower() != repo_owner.lower():
            _fail(
                f"'repository_owner' '{repo_owner}' does not match owner component '{expected_owner}' of 'repository'",
                "Set 'repository_owner' to the owner component of 'repository'.",
            )

    # Canonical URL structure
    canonical_url = instance.get("canonical_url", "")
    if isinstance(canonical_url, str) and canonical_url.strip():
        try:
            parsed = urlparse(canonical_url)
            if parsed.scheme != "https":
                _fail(
                    f"'canonical_url' must use https scheme, got '{parsed.scheme}'",
                    "Use an https:// URL.",
                )
            if not parsed.netloc:
                _fail(
                    "'canonical_url' must have a non-empty hostname",
                    "Provide a complete URL with hostname.",
                )
            if parsed.username or parsed.password:
                _fail(
                    "'canonical_url' must not contain credentials (username or password)",
                    "Remove credentials from the URL.",
                )
            if parsed.query:
                _fail(
                    "'canonical_url' must not contain a query string",
                    "Remove the query string from the URL.",
                )
            if parsed.fragment:
                _fail(
                    "'canonical_url' must not contain a fragment",
                    "Remove the fragment from the URL.",
                )
            # Path must end with owner/repository
            if isinstance(repo, str) and "/" in repo:
                path_clean = parsed.path.rstrip("/").removesuffix(".git")
                expected_suffix = "/" + repo
                if not path_clean.endswith(expected_suffix):
                    _fail(
                        f"'canonical_url' path must end with '{repo}' (with optional .git or trailing slash), got path '{parsed.path}'",
                        f"Set the URL path to match 'owner/repository': {repo}.",
                    )
        except Exception as exc:
            _fail(
                f"'canonical_url' could not be parsed: {exc}",
                "Provide a valid URL.",
            )

    # Review date — real ISO calendar date
    review_date = instance.get("review_date", "")
    if isinstance(review_date, str) and review_date.strip():
        try:
            date.fromisoformat(review_date)
        except (ValueError, TypeError):
            _fail(
                f"'review_date' '{review_date}' is not a valid ISO calendar date (YYYY-MM-DD)",
                "Use a valid calendar date in YYYY-MM-DD format.",
            )

    # Files examined
    files_examined = instance.get("files_examined")
    if isinstance(files_examined, list):
        if len(files_examined) == 0:
            _fail(
                "'files_examined' must contain at least one entry",
                "Add at least one file path to 'files_examined'.",
            )
        seen_paths: set[str] = set()
        for i, entry in enumerate(files_examined):
            if not isinstance(entry, dict):
                continue
            fp = entry.get("file_path", "")
            if not isinstance(fp, str):
                continue
            # Safe path checks
            path_failures = validate_safe_file_path(
                fp, f"files_examined[{i}].file_path", target
            )
            failures.extend(path_failures)

            # Uniqueness
            fp_normalized = fp  # case-sensitive POSIX comparison
            if fp_normalized in seen_paths:
                _fail(
                    f"files_examined[{i}].file_path '{fp}' is a duplicate",
                    "Remove or merge duplicate file path entries in 'files_examined'.",
                )
            else:
                seen_paths.add(fp_normalized)

            # Line ranges
            line_ranges = entry.get("line_ranges")
            if line_ranges is not None:
                if not isinstance(line_ranges, list) or len(line_ranges) == 0:
                    _fail(
                        f"files_examined[{i}].line_ranges must contain at least one entry when present",
                        "Add at least one range string or omit 'line_ranges'.",
                    )
                else:
                    seen_ranges: set[str] = set()
                    for j, rng in enumerate(line_ranges):
                        if not isinstance(rng, str):
                            continue
                        if rng in seen_ranges:
                            _fail(
                                f"files_examined[{i}].line_ranges[{j}] '{rng}' is a duplicate",
                                "Remove duplicate range entries.",
                            )
                            continue
                        seen_ranges.add(rng)
                        parsed_range = parse_line_range(rng)
                        if parsed_range is None:
                            _fail(
                                f"files_examined[{i}].line_ranges[{j}] '{rng}' is not a valid range",
                                "Use 'start-end' integer format, e.g. '10-50'.",
                            )
                        else:
                            start, end = parsed_range
                            if start < 1 or end < 1:
                                _fail(
                                    f"files_examined[{i}].line_ranges[{j}] '{rng}' contains non-positive line numbers",
                                    "Line numbers must be positive integers.",
                                )
                            elif start > end:
                                _fail(
                                    f"files_examined[{i}].line_ranges[{j}] '{rng}' has start > end",
                                    "Start line must be less than or equal to end line.",
                                )

    return failures


def validate_source_intake_instance(
    bundle_path: Path, schema: dict
) -> list[ValidationFailure]:
    """Validate source-intake.json in a bundle directory."""
    intake_path = bundle_path / "source-intake.json"
    rel = str(intake_path.relative_to(bundle_path.parent.parent)).replace("\\", "/")

    if not intake_path.exists():
        return [
            ValidationFailure(
                target=rel,
                reason="source-intake.json is missing from bundle",
                remediation=f"Create {rel} conforming to SOURCE_INTAKE_SCHEMA.json.",
            )
        ]

    try:
        instance = load_json_without_duplicate_keys(intake_path)
    except (ValueError, ValidatorConfigurationError) as exc:
        return [
            ValidationFailure(
                target=rel,
                reason=str(exc),
                remediation="Fix the JSON file and re-validate.",
            )
        ]

    failures = validate_instance(instance, schema, target=rel)
    failures.extend(_validate_source_intake_semantics(instance, rel))
    return failures


def _validate_pattern_semantics(
    pattern: dict,
    target: str,
    examined_files: dict[str, list[tuple[int, int]]],
    bundle_pattern_names: set[str],
) -> list[ValidationFailure]:
    """Enforce pattern-instance semantic rules."""
    failures = []

    def _fail(reason: str, rem: str) -> None:
        failures.append(ValidationFailure(target=target, reason=reason, remediation=rem))

    # Name: non-empty, max 128 chars
    name = pattern.get("name", "")
    if isinstance(name, str):
        if not name.strip():
            _fail("'name' must be non-empty", "Provide a pattern name.")
        elif len(name) > 128:
            _fail(
                f"'name' length {len(name)} exceeds maximum of 128 characters",
                "Shorten the pattern name to 128 characters or fewer.",
            )

    # Description: non-empty
    desc = pattern.get("description", "")
    if isinstance(desc, str) and not desc.strip():
        _fail("'description' must be non-empty", "Provide a pattern description.")

    # Source file: safe path
    source_file = pattern.get("source_file", "")
    if isinstance(source_file, str):
        path_failures = validate_safe_file_path(source_file, "source_file", target)
        failures.extend(path_failures)

        # Must be in examined files
        if source_file and source_file not in examined_files:
            _fail(
                f"'source_file' '{source_file}' is not declared in the bundle's files_examined",
                "Add the source file to 'files_examined' in source-intake.json or correct 'source_file'.",
            )

    # Line range: required for committed records
    line_range_str = pattern.get("line_range")
    if line_range_str is None:
        _fail(
            "'line_range' is required for committed pattern records",
            "Add a 'line_range' field in 'start-end' format.",
        )
    elif isinstance(line_range_str, str):
        parsed = parse_line_range(line_range_str)
        if parsed is None:
            _fail(
                f"'line_range' '{line_range_str}' is not a valid 'start-end' format",
                "Use integer 'start-end' format, e.g. '35-48'.",
            )
        else:
            ps, pe = parsed
            if ps < 1 or pe < 1:
                _fail(
                    f"'line_range' '{line_range_str}' contains non-positive line numbers",
                    "Line numbers must be positive integers.",
                )
            elif ps > pe:
                _fail(
                    f"'line_range' '{line_range_str}' has start > end",
                    "Start line must be less than or equal to end line.",
                )
            else:
                # Coverage check
                if isinstance(source_file, str) and source_file in examined_files:
                    examined_ranges = examined_files[source_file]
                    if not examined_ranges:
                        _fail(
                            f"Pattern source file '{source_file}' has no examined line ranges in source-intake.json",
                            "Define covering line_ranges in source-intake.json.",
                        )
                    elif not is_range_covered(ps, pe, examined_ranges):
                        _fail(
                            f"'line_range' '{line_range_str}' is not covered by any examined range "
                            f"for '{source_file}' in source-intake.json",
                            "Ensure the pattern range falls within an examined line range.",
                        )

    # Classification
    classification = pattern.get("classification", "")
    if (
        isinstance(classification, str)
        and classification in LICENSE_REQUIRED_CLASSIFICATIONS
    ):
        li = pattern.get("license_implications")
        if li is None:
            _fail(
                f"'license_implications' is required for classification '{classification}'",
                "Add a non-empty 'license_implications' field to document licensing risk.",
            )
        elif isinstance(li, str) and not li.strip():
            _fail(
                f"'license_implications' must be non-empty for classification '{classification}'",
                "Provide meaningful license implications text.",
            )

    # When license_implications is present for other classifications, must be non-empty
    if classification not in LICENSE_REQUIRED_CLASSIFICATIONS:
        li = pattern.get("license_implications")
        if li is not None and isinstance(li, str) and not li.strip():
            _fail(
                "'license_implications' must be non-empty when present",
                "Provide meaningful license implications text or omit the field.",
            )

    return failures


def validate_pattern_instances(
    bundle_path: Path,
    schema: dict,
    examined_files: dict[str, list[tuple[int, int]]],
) -> list[ValidationFailure]:
    """Validate all pattern JSON files under <bundle>/patterns/."""
    failures = []
    patterns_dir = bundle_path / "patterns"
    bundle_rel = str(bundle_path.parent.parent).replace("\\", "/")

    if not patterns_dir.is_dir():
        rel = str((bundle_path / "patterns").relative_to(bundle_path.parent.parent)).replace("\\", "/")
        return [
            ValidationFailure(
                target=rel,
                reason="patterns/ directory is missing from bundle",
                remediation="Create the patterns/ directory (it may be empty).",
            )
        ]

    # Check for nested directories or non-JSON files
    pattern_name_set: set[str] = set()  # case-folded for uniqueness
    pattern_slug_set: set[str] = set()  # expected filenames

    for entry in sorted(patterns_dir.iterdir()):
        rel = str(entry.relative_to(bundle_path.parent.parent)).replace("\\", "/")
        if entry.is_dir():
            failures.append(
                ValidationFailure(
                    target=rel,
                    reason=f"Nested directory '{entry.name}' found in patterns/; only .json files are allowed",
                    remediation="Remove nested directories from the patterns/ directory.",
                )
            )
            continue
        if entry.suffix != ".json":
            failures.append(
                ValidationFailure(
                    target=rel,
                    reason=f"Non-JSON file '{entry.name}' found in patterns/",
                    remediation="Remove non-JSON files from the patterns/ directory.",
                )
            )
            continue

        # Load and validate
        try:
            instance = load_json_without_duplicate_keys(entry)
        except (ValueError, ValidatorConfigurationError) as exc:
            failures.append(
                ValidationFailure(
                    target=rel,
                    reason=str(exc),
                    remediation="Fix the JSON file and re-validate.",
                )
            )
            continue

        schema_failures = validate_instance(instance, schema, target=rel)
        failures.extend(schema_failures)

        # Semantic checks
        semantic_failures = _validate_pattern_semantics(
            instance, rel, examined_files, pattern_slug_set
        )
        failures.extend(semantic_failures)

        # Filename must match slugified name
        name = instance.get("name", "")
        if isinstance(name, str) and name.strip():
            slug = slugify(name)
            if not slug:
                failures.append(
                    ValidationFailure(
                        target=rel,
                        reason=f"Pattern name '{name}' results in an empty slug",
                        remediation="Use a name containing alphanumeric characters.",
                    )
                )
            else:
                expected_filename = slug + ".json"
                if entry.name != expected_filename:
                    failures.append(
                        ValidationFailure(
                            target=rel,
                            reason=f"Pattern filename '{entry.name}' does not match expected '{expected_filename}' derived from pattern name '{name}'",
                            remediation=f"Rename the file to '{expected_filename}'.",
                        )
                    )

            # Uniqueness (case-folded)
            name_folded = name.casefold()
            if name_folded in pattern_name_set:
                failures.append(
                    ValidationFailure(
                        target=rel,
                        reason=f"Duplicate case-folded pattern name '{name}' in bundle",
                        remediation="Use unique pattern names within a bundle.",
                    )
                )
            else:
                pattern_name_set.add(name_folded)

    return failures


# ---------------------------------------------------------------------------
# Section 4: Cross-record integrity
# ---------------------------------------------------------------------------


def validate_cross_record_integrity(
    bundle_path: Path,
) -> list[ValidationFailure]:
    """Enforce bundle-level integrity rules."""
    failures = []

    def _fail(target: str, reason: str, rem: str) -> None:
        failures.append(ValidationFailure(target=target, reason=reason, remediation=rem))

    rel_bundle = str(bundle_path.relative_to(bundle_path.parent.parent)).replace("\\", "/")

    # Bundle must contain exactly source-intake.json and patterns/
    allowed = {"source-intake.json", "patterns"}
    for entry in bundle_path.iterdir():
        if entry.name not in allowed:
            rel = str(entry.relative_to(bundle_path.parent.parent)).replace("\\", "/")
            _fail(
                rel,
                f"Unexpected entry '{entry.name}' in bundle directory",
                "Remove unexpected files or directories from the bundle.",
            )

    # Load source-intake to derive expected bundle ID
    intake_path = bundle_path / "source-intake.json"
    if not intake_path.is_file():
        # Missing intake — already reported in Section 2
        return failures

    try:
        intake = load_json_without_duplicate_keys(intake_path)
    except (ValueError, ValidatorConfigurationError):
        # Already reported in Section 2
        return failures

    repository = intake.get("repository", "")
    sha = intake.get("reviewed_commit_sha", "")

    if isinstance(repository, str) and "/" in repository and isinstance(sha, str) and len(sha) == 40:
        expected_id = derive_bundle_id(repository, sha)
        actual_id = bundle_path.name
        if actual_id != expected_id:
            _fail(
                rel_bundle,
                f"Bundle directory name '{actual_id}' does not match expected '{expected_id}' derived from repository '{repository}' and SHA '{sha[:12]}'",
                f"Rename the bundle directory to '{expected_id}'.",
            )

    return failures


# ---------------------------------------------------------------------------
# Bundle validator (combines all sections)
# ---------------------------------------------------------------------------


def _build_examined_files_index(intake: dict) -> dict[str, list[tuple[int, int]]]:
    """Build a mapping: file_path -> list of (start, end) tuples from examined line ranges."""
    index: dict[str, list[tuple[int, int]]] = {}
    for entry in intake.get("files_examined", []):
        if not isinstance(entry, dict):
            continue
        fp = entry.get("file_path")
        if not isinstance(fp, str) or not fp:
            continue
        ranges = []
        for rng in entry.get("line_ranges", []):
            if isinstance(rng, str):
                parsed = parse_line_range(rng)
                if parsed:
                    ranges.append(parsed)
        index[fp] = ranges
    return index


def validate_record_bundle(
    bundle_path: Path,
    source_intake_schema: dict,
    pattern_schema: dict,
) -> list[ValidationFailure]:
    """Validate a single record bundle (all sections)."""
    failures = []

    # Section 2: Source-intake
    intake_failures = validate_source_intake_instance(bundle_path, source_intake_schema)
    failures.extend(intake_failures)

    # Build examined files index for pattern coverage checks
    intake_path = bundle_path / "source-intake.json"
    examined_files: dict[str, list[tuple[int, int]]] = {}
    if intake_path.is_file():
        try:
            intake = load_json_without_duplicate_keys(intake_path)
            examined_files = _build_examined_files_index(intake)
        except (ValueError, ValidatorConfigurationError):
            pass

    # Section 3: Pattern instances
    pattern_failures = validate_pattern_instances(
        bundle_path, pattern_schema, examined_files
    )
    failures.extend(pattern_failures)

    # Section 4: Cross-record integrity
    cross_failures = validate_cross_record_integrity(bundle_path)
    failures.extend(cross_failures)

    return failures


# ---------------------------------------------------------------------------
# Repository-level validator
# ---------------------------------------------------------------------------


def _load_schema(repo_root: Path, rel_path: str) -> dict:
    """Load and validate a schema file. Raises ValidatorConfigurationError on problems."""
    schema_path = repo_root / Path(rel_path)

    if not schema_path.is_file():
        raise ValidatorConfigurationError(
            f"Schema file missing: {rel_path}"
        )

    try:
        schema = load_json_without_duplicate_keys(schema_path)
    except (ValueError, ValidatorConfigurationError) as exc:
        raise ValidatorConfigurationError(
            f"Schema file invalid: {rel_path}: {exc}"
        ) from exc

    validate_schema_configuration(schema, rel_path)

    return schema


def validate_repository(repo_root: Path) -> list[ValidationFailure]:
    """Run all Phase 3 validation checks. Returns structured failures without I/O."""
    failures: list[ValidationFailure] = []

    # Load schemas (raises ValidatorConfigurationError if missing/invalid)
    source_intake_schema = _load_schema(repo_root, SOURCE_INTAKE_SCHEMA_PATH)
    pattern_schema = _load_schema(repo_root, PATTERN_SCHEMA_PATH)

    # Section 1: Registry layout
    layout_failures = validate_registry_layout(repo_root)
    failures.extend(layout_failures)

    records_path = repo_root / RECORDS_DIR
    if not records_path.is_dir():
        return failures

    # Validate each bundle directory
    for entry in sorted(records_path.iterdir()):
        if entry.name == "README.md":
            continue
        if not entry.is_dir():
            continue

        # Validate bundle ID format before full validation
        # (bundle ID format: slug__slug__sha12)
        bundle_id = entry.name
        bundle_id_re = re.compile(r"^[a-z0-9._-]+__[a-z0-9._-]+__[0-9a-f]{12}$")
        if not bundle_id_re.match(bundle_id):
            rel = str(entry.relative_to(repo_root)).replace("\\", "/")
            failures.append(
                ValidationFailure(
                    target=rel,
                    reason=f"Bundle directory name '{bundle_id}' does not match expected format '<owner-slug>__<repo-slug>__<sha12>'",
                    remediation="Rename the directory to match the bundle ID derivation formula.",
                )
            )
            continue

        bundle_failures = validate_record_bundle(
            entry, source_intake_schema, pattern_schema
        )
        failures.extend(bundle_failures)

    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_failure(failure: ValidationFailure) -> None:
    print(f"[FAIL] {failure.target}: {failure.reason}")
    print(f"       Remediation: {failure.remediation}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Artificer Record-Instance Validator"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Root directory of the repository (default: auto-detected from script location)",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            return 0
        return 2

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent

    print("[1] Record Registry Layout")
    print("[2] Source-Intake Instances")
    print("[3] Pattern Instances")
    print("[4] Cross-Record Integrity")

    try:
        failures = validate_repository(repo_root)
    except ValidatorConfigurationError as exc:
        print(f"[FAIL] Configuration error: {exc}")
        print("       Remediation: Restore the schema files and re-run validation.")
        return 2

    records_path = repo_root / RECORDS_DIR

    # Section 1
    layout_targets = set()
    bundle_dirs = []
    if records_path.is_dir():
        for entry in sorted(records_path.iterdir()):
            if entry.name != "README.md" and entry.is_dir():
                bundle_dirs.append(entry)

    readme_path = repo_root / RECORDS_README
    if readme_path.is_file():
        print(f"[PASS] {RECORDS_README}: Registry README exists.")
    # (failures will be printed below)

    if not bundle_dirs:
        print(f"[PASS] {RECORDS_DIR}: Empty registry — no bundles to validate.")

    # Print all failures
    if failures:
        print()
        for failure in failures:
            _print_failure(failure)
        print()
        print(f"[5] Summary")
        print(f"Validation Failed: {len(failures)} issue(s) found.")
        return 1

    print()
    print(f"[5] Summary")
    print("Validation Passed: All Artificer record instances are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
