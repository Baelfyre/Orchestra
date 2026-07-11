#!/usr/bin/env python3
import argparse
import os
import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass

REQUIRED_FILES = [
    "internal/artificer/ARTIFICER.md",
    "internal/artificer/OUTPUT_FORMATS.md",
    "internal/artificer/CHECKLIST.md",
    "internal/artificer/PATTERN_SCHEMA.json",
    "internal/artificer/SOURCE_INTAKE_SCHEMA.json",
    "docs/internal/ARTIFICER_WORKFLOW.md",
    "docs/internal/ARTIFICER_BOUNDARIES.md",
    "docs/internal/EXTERNAL_SOURCE_INTAKE.md",
    "docs/internal/PATTERN_CLASSIFICATION.md",
    "docs/internal/EVIDENCE_REQUIREMENTS.md",
    "docs/internal/LICENSE_AND_ATTRIBUTION.md",
    "docs/internal/PATTERN_CATALOG.md",
    "docs/internal/SECURITY_BOUNDARIES.md"
]

@dataclass(frozen=True)
class ValidationFailure:
    target: str
    reason: str
    remediation: str

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)

def parse_args():
    parser = ThrowingArgumentParser(description="Artificer Internal Boundary and Contract Validator")
    parser.add_argument("--repo-root", type=str, default=None, help="Root directory of the repository")
    return parser.parse_args()

def validate_shared_schema(schema_dict, filename) -> list[ValidationFailure]:
    failures = []
    if not isinstance(schema_dict, dict):
        failures.append(ValidationFailure(filename, "Top-level structure is not a JSON object", "Change the top-level schema to a JSON object"))
        return failures

    schema_url = schema_dict.get("$schema")
    if schema_url != "http://json-schema.org/draft-07/schema#":
        failures.append(ValidationFailure(filename, f"Invalid $schema claim: {schema_url}", "Ensure '$schema' is 'http://json-schema.org/draft-07/schema#'"))

    if schema_dict.get("type") != "object":
        failures.append(ValidationFailure(filename, "Top-level 'type' must be 'object'", "Set 'type' to 'object' at the root of the schema"))

    properties = schema_dict.get("properties")
    if not isinstance(properties, dict):
        failures.append(ValidationFailure(filename, "'properties' must be a JSON object", "Define 'properties' as a JSON object"))

    required = schema_dict.get("required")
    if not isinstance(required, list):
        failures.append(ValidationFailure(filename, "'required' must be a list", "Define 'required' as a list of property names"))
    else:
        if isinstance(properties, dict):
            for req_field in required:
                if req_field not in properties:
                    failures.append(ValidationFailure(filename, f"Required field '{req_field}' not present in properties", f"Add '{req_field}' definition to properties"))

    if schema_dict.get("additionalProperties") is not False:
        failures.append(ValidationFailure(filename, "'additionalProperties' must be false", "Set 'additionalProperties' to false"))

    def find_duplicate_enums(node, path=""):
        enum_dupes = []
        if isinstance(node, dict):
            if "enum" in node and isinstance(node["enum"], list):
                enums = node["enum"]
                if len(enums) != len(set(enums)):
                    enum_dupes.append((path or "enum", enums))
            for k, v in node.items():
                enum_dupes.extend(find_duplicate_enums(v, f"{path}.{k}" if path else k))
        elif isinstance(node, list):
            for i, val in enumerate(node):
                enum_dupes.extend(find_duplicate_enums(val, f"{path}[{i}]"))
        return enum_dupes

    dupes = find_duplicate_enums(schema_dict)
    for path, enums in dupes:
        failures.append(ValidationFailure(filename, f"Duplicate values found in enum array at '{path}': {enums}", f"Remove duplicate entries from the enum array at '{path}'"))

    return failures

def check_required_files(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    for relative_path in REQUIRED_FILES:
        full_path = repo_root / relative_path
        if not full_path.exists():
            failures.append(ValidationFailure(relative_path, "File does not exist", f"Create the missing specification file at {relative_path}"))
        elif not full_path.is_file():
            failures.append(ValidationFailure(relative_path, "Not a regular file", f"Ensure {relative_path} is a regular file and not a directory"))
        else:
            try:
                content = full_path.read_text(encoding="utf-8")
                if not content.strip():
                    failures.append(ValidationFailure(relative_path, "File is empty", f"Add content to the required specification file {relative_path}"))
            except UnicodeDecodeError:
                failures.append(ValidationFailure(relative_path, "Cannot decode as UTF-8", f"Convert encoding of {relative_path} to UTF-8"))
    return failures

def validate_pattern_schema(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    pattern_schema_path = repo_root / "internal/artificer/PATTERN_SCHEMA.json"
    if not pattern_schema_path.is_file():
        return failures

    try:
        content = pattern_schema_path.read_text(encoding="utf-8")
        pattern_schema = json.loads(content)
        failures.extend(validate_shared_schema(pattern_schema, "internal/artificer/PATTERN_SCHEMA.json"))

        properties = pattern_schema.get("properties", {})
        required = pattern_schema.get("required", [])

        expected_props = {"name", "description", "source_file", "line_range", "classification", "assigned_specialist", "license_implications"}
        if isinstance(properties, dict) and set(properties.keys()) != expected_props:
            reason = f"Properties mismatch: expected {expected_props}, got {set(properties.keys())}"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Ensure PATTERN_SCHEMA.json defines exactly the required properties"))

        expected_req = {"name", "description", "source_file", "classification", "assigned_specialist"}
        if set(required) != expected_req:
            reason = f"Required list mismatch: expected {expected_req}, got {set(required)}"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Ensure required list matches exactly the mandatory fields"))

        class_enum = properties.get("classification", {}).get("enum", [])
        expected_class_enum = ["REFERENCE_ONLY", "ADAPTED_PATTERN", "CODE_REUSE_REVIEW_REQUIRED", "TEST_CORPUS_CANDIDATE", "REJECTED", "DEFERRED", "DUPLICATE", "OUT_OF_SCOPE"]
        if class_enum != expected_class_enum:
            reason = "classification enum mismatch"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Set classification enum to the exact expected values"))

        spec_enum = properties.get("assigned_specialist", {}).get("enum", [])
        expected_spec_enum = ["cloak", "cipher", "clockwork", "ponytail", "overseer", "dagger", "the-governor", "arbiter", "chronicler", "weaver", "scribe", "the-steward"]
        if spec_enum != expected_spec_enum:
            reason = "assigned_specialist enum mismatch"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Set assigned_specialist enum to the exact expected values"))

        if "artificer" in spec_enum:
            reason = "assigned_specialist enum must never contain 'artificer'"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Remove 'artificer' from the assigned_specialist enum list"))

        lr_pattern = properties.get("line_range", {}).get("pattern")
        if lr_pattern != r"^\d+-\d+$":
            reason = "line_range pattern mismatch"
            failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", reason, "Set line_range pattern to '^\\d+-\\d+$'"))
    except Exception as e:
        failures.append(ValidationFailure("internal/artificer/PATTERN_SCHEMA.json", f"JSON parsing failed: {e}", "Fix the JSON syntax of PATTERN_SCHEMA.json"))

    return failures

def validate_source_intake_schema(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    source_schema_path = repo_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
    if not source_schema_path.is_file():
        return failures

    try:
        content = source_schema_path.read_text(encoding="utf-8")
        source_schema = json.loads(content)
        failures.extend(validate_shared_schema(source_schema, "internal/artificer/SOURCE_INTAKE_SCHEMA.json"))

        properties = source_schema.get("properties", {})
        required = source_schema.get("required", [])

        expected_props = {"repository", "repository_owner", "canonical_url", "license", "default_branch", "reviewed_commit_sha", "review_date", "files_examined", "runtime_behavior_tested", "source_confidence"}
        if isinstance(properties, dict) and set(properties.keys()) != expected_props:
            reason = f"Properties mismatch: expected {expected_props}, got {set(properties.keys())}"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Ensure SOURCE_INTAKE_SCHEMA.json defines exactly the required properties"))

        expected_req = {"repository", "repository_owner", "canonical_url", "license", "reviewed_commit_sha", "review_date", "files_examined", "runtime_behavior_tested", "source_confidence"}
        if set(required) != expected_req:
            reason = f"Required list mismatch: expected {expected_req}, got {set(required)}"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Ensure required list matches exactly the mandatory fields"))

        commit_pattern = properties.get("reviewed_commit_sha", {}).get("pattern")
        if commit_pattern != r"^[0-9a-fA-F]{40}$":
            reason = "reviewed_commit_sha pattern mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set reviewed_commit_sha pattern to '^[0-9a-fA-F]{40}$'"))

        date_format = properties.get("review_date", {}).get("format")
        if date_format != "date":
            reason = "review_date format mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set review_date format to 'date'"))

        rbt_type = properties.get("runtime_behavior_tested", {}).get("type")
        if rbt_type != "boolean":
            reason = "runtime_behavior_tested type mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set runtime_behavior_tested type to 'boolean'"))

        fe_type = properties.get("files_examined", {}).get("type")
        if fe_type != "array":
            reason = "files_examined type mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set files_examined type to 'array'"))

        fe_items = properties.get("files_examined", {}).get("items", {})
        fe_items_ap = fe_items.get("additionalProperties")
        if fe_items_ap is not False:
            reason = "files_examined items additionalProperties mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set files_examined items additionalProperties to false"))

        sc_enum = properties.get("source_confidence", {}).get("enum", [])
        expected_sc_enum = ["HIGH", "MEDIUM", "LOW"]
        if sc_enum != expected_sc_enum:
            reason = "Source confidence enum mismatch"
            failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set source_confidence enum to exactly HIGH, MEDIUM, LOW"))
    except Exception as e:
        failures.append(ValidationFailure("internal/artificer/SOURCE_INTAKE_SCHEMA.json", f"JSON parsing failed: {e}", "Fix the JSON syntax of SOURCE_INTAKE_SCHEMA.json"))

    return failures

def normalize_contract_text(content: str) -> str:
    content = content.lower()
    content = re.sub(r"[`*_#>|-]+", " ", content)
    content = re.sub(r"\s+", " ", content)
    return content.strip()

# Connectors that may introduce a semantically independent action clause.
# 'and' is listed here but handled carefully — it only separates clauses
# when followed by a new modal or subject, not when it chains objects.
_CLAUSE_CONNECTORS = re.compile(
    r'\b(but|yet|although|though|while|whereas|however|and)\b',
    re.IGNORECASE,
)

# Negative modals — these must immediately precede the action in the window.
_NEGATIVES = [
    "must not",
    "does not",
    "do not",
    "cannot",
    "may not",
    "never",
    "is prohibited from",
    "is blocked from",
]

# Positive modals regex — matches positive permission forms.
# 'may' only when NOT followed by 'not' (handled via negative lookahead).
_POSITIVE_RE = re.compile(
    r'\b(?:may(?!\s+not)|can(?!\s+not)|will|is\s+allowed\s+to|is\s+permitted\s+to)\b',
    re.IGNORECASE,
)

def _has_positive_modal(text: str) -> bool:
    """Return True if text contains a positive permission modal."""
    return bool(_POSITIVE_RE.search(text))

def _split_into_sub_clauses(sentence: str) -> list[str]:
    """Split a single (already-split-by-punctuation) sentence into
    action-independent sub-clauses on connectors, while preserving
    coordinated object lists in single-prohibition phrases.

    Two-tier connector strategy:
      - ALWAYS-SPLIT: while, whereas, however, but, yet, although, though
        These always introduce independent clauses — never re-joined.
      - CONDITIONAL: and
        Re-join the next part only when it contains no new modal keyword,
        which preserves 'licensing compliance and IP clearance' while
        splitting 'must not implement source code and may run tests'.
    """
    # Always-split connectors
    _ALWAYS_SPLIT = re.compile(
        r'\b(but|yet|although|though|while|whereas|however)\b',
        re.IGNORECASE,
    )
    # Conditional connector
    _AND = re.compile(r'\band\b', re.IGNORECASE)
    # Modal keywords used to detect independent clauses after 'and'
    _MODAL_RE = re.compile(r'\b(must|may|can|does|do|will|is|never|cannot)\b')

    # First pass: split on always-split connectors
    raw_parts = _ALWAYS_SPLIT.split(sentence)
    strong_parts: list[str] = []
    for p in raw_parts:
        norm = normalize_contract_text(p)
        if norm and norm not in {"but", "yet", "although", "though", "while", "whereas", "however"}:
            strong_parts.append(norm)

    if not strong_parts:
        return []

    # Second pass: split each strong_part further on 'and', then conditionally re-join
    final_parts: list[str] = []
    for sp in strong_parts:
        and_parts_raw = _AND.split(sp)
        and_parts: list[str] = []
        for p in and_parts_raw:
            norm = normalize_contract_text(p)
            if norm:
                and_parts.append(norm)

        if len(and_parts) <= 1:
            final_parts.extend(and_parts)
            continue

        # Conditionally merge: if a part has no modal, treat as object continuation
        merged: list[str] = [and_parts[0]]
        for part in and_parts[1:]:
            if not _MODAL_RE.search(part):
                merged[-1] = merged[-1] + " and " + part
            else:
                merged.append(part)
        final_parts.extend(merged)

    return final_parts


def get_clauses(content: str) -> list[tuple[str, bool]]:
    """Return list of (normalized_clause, has_artificer_subject) tuples.

    Subject inheritance is sequential: once 'artificer' appears in a clause,
    subsequent clauses in the same sentence inherit the subject until a new
    sentence boundary (punctuation) resets it.
    """
    content = re.sub(r"(?:^|\n)\s*#+\s+", ". ", content)
    content = re.sub(r"(?:^|\n)\s*[-*+]\s+", ". ", content)
    # Normalize comma-modal patterns: ", may V", ", can V", etc.
    # Replace with " and [modal]" rather than a sentence boundary (;)
    # so that subject inheritance across the comma is preserved.
    content = re.sub(r",\s+(?=(?:may|can|will|is\s+allowed|is\s+permitted)\b)", " and ", content, flags=re.IGNORECASE)
    raw_sentences = re.split(r'[.;!\?\n]', content)

    clauses = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        sub_clauses = _split_into_sub_clauses(s)
        if not sub_clauses:
            continue
        # Sequential subject inheritance within the sentence
        subject_is_artificer = False
        for sub in sub_clauses:
            if "artificer" in sub:
                subject_is_artificer = True
            clauses.append((sub, subject_is_artificer))
    return clauses

def _action_polarity(clause: str, action_pattern: str) -> str | None:
    """Determine the polarity of a specific action within a clause.

    Returns 'prohibited', 'permitted', or None (action not found or no modal binding).

    Uses two-pass detection:
      1. Look for a direct modal in a 5-token window before each action match.
      2. If no direct window modal, check whether the ENTIRE clause carries a
         governing negative modal (shared-negative list, e.g. 'must not V1, V2, or V3').
         The governing negative is only overridden if a specific positive modal
         re-assigns just this action occurrence in its local window.

    This lets 'must not execute..., run tests, or install packages' count as
    a prohibition on ALL three verbs, while
    'must not implement source code and may run tests' correctly splits.
    """
    WINDOW = 5  # token look-back for direct modal

    tokens = clause.split()
    if not tokens:
        return None

    # Find all positions where action_pattern matches
    action_positions: list[int] = []
    for i, tok in enumerate(tokens):
        if re.search(action_pattern, tok, re.IGNORECASE):
            action_positions.append(i)

    if not action_positions:
        return None

    # Determine clause-level governing negative (applies to all verbs in list)
    clause_neg = any(neg in clause for neg in _NEGATIVES)

    # For each action occurrence, check the window before it
    for pos in action_positions:
        window_start = max(0, pos - WINDOW)
        window_tokens = tokens[window_start:pos]
        window_str = " ".join(window_tokens)

        # Check for direct negative binding in window
        neg_found = any(neg in window_str for neg in _NEGATIVES)

        # Check for direct positive binding in window
        pos_found = _has_positive_modal(window_str)

        if pos_found and neg_found:
            # Both in same local window — positive takes precedence (mixed binding)
            return "permitted"
        if pos_found:
            return "permitted"
        if neg_found:
            return "prohibited"

        # No direct modal in window — fall back to clause-level governing negative.
        # If the clause carries a negative modal elsewhere (governing a verb list),
        # treat this action as also prohibited, UNLESS there is a positive modal
        # for this specific action anywhere in a reasonable wider window.
        if clause_neg:
            # Widen search: look for a positive re-assignment for this specific action
            wider_window = tokens[max(0, pos - 10):pos]
            wider_str = " ".join(wider_window)
            if _has_positive_modal(wider_str):
                return "permitted"
            return "prohibited"

    return None

def has_artificer_prohibition(
    content: str,
    action_pattern: str,
    object_pattern: str | None = None,
) -> bool:
    """Return True if any Artificer-subject clause contains an
    action-bound prohibition for the given action (and optional object).
    """
    clauses = get_clauses(content)
    for clause, has_subject in clauses:
        if not has_subject:
            continue
        if object_pattern and not re.search(object_pattern, clause, re.IGNORECASE):
            continue
        if not re.search(action_pattern, clause, re.IGNORECASE):
            continue
        polarity = _action_polarity(clause, action_pattern)
        if polarity == "prohibited":
            return True
    return False

def has_artificer_permission(
    content: str,
    action_pattern: str,
    object_pattern: str | None = None,
) -> bool:
    """Return True if any Artificer-subject clause contains an
    action-bound positive permission for the given action (and optional object).
    """
    clauses = get_clauses(content)
    for clause, has_subject in clauses:
        if not has_subject:
            continue
        if object_pattern and not re.search(object_pattern, clause, re.IGNORECASE):
            continue
        if not re.search(action_pattern, clause, re.IGNORECASE):
            continue
        polarity = _action_polarity(clause, action_pattern)
        if polarity == "permitted":
            return True
    return False

def check_prohibition_contract(
    content: str,
    action_pattern: str,
    object_pattern: str | None = None,
) -> bool:
    if not has_artificer_prohibition(content, action_pattern, object_pattern):
        return False
    if has_artificer_permission(content, action_pattern, object_pattern):
        return False
    return True


def check_artificer_md(content):
    missing = []
    if not (re.search(r"maintainer-only", content, re.IGNORECASE) or re.search(r"maintainer explicitly", content, re.IGNORECASE)):
        missing.append("maintainer-only activation")
    if not re.search(r"internal", content, re.IGNORECASE):
        missing.append("internal visibility")
    if not re.search(r"read-only", content, re.IGNORECASE):
        missing.append("read-only external-source auditing")

    if not check_prohibition_contract(content, r"execute", r"code|script|binary|test|runner"):
        missing.append("no external code execution")
    if not check_prohibition_contract(content, r"install", r"dependency|package"):
        missing.append("no external dependency installation")
    if not check_prohibition_contract(content, r"implement", r"recommendation|proposal|own|change|ui"):
        missing.append("no self-implementation")
    if not check_prohibition_contract(content, r"approve|adjudicate|clear", r"finding|evidence|own"):
        missing.append("no self-approval")
    if not (check_prohibition_contract(content, r"register", r"public|manifest") or check_prohibition_contract(content, r"visibility|blocked", r"public|manifest|routing")):
        missing.append("no manifest registration")
    if not (check_prohibition_contract(content, r"expose|route", r"runtime|adapter") or check_prohibition_contract(content, r"visibility|blocked", r"runtime|adapter")):
        missing.append("no runtime route")

    if not (re.search(r"cipher", content, re.IGNORECASE) and (re.search(r"hand", content, re.IGNORECASE) or re.search(r"off", content, re.IGNORECASE))):
        missing.append("Cipher handoff for security-relevant findings")
    return missing

def check_security_boundaries_md(content):
    missing = []
    if not re.search(r"no code execution", content, re.IGNORECASE):
        missing.append("No Code Execution")
    if not re.search(r"no script following", content, re.IGNORECASE):
        missing.append("No Script Following")
    if not re.search(r"read-only scope", content, re.IGNORECASE):
        missing.append("Read-Only Scope")
    if not (re.search(r"secret.*credentials", content, re.IGNORECASE) or re.search(r"secret.*handling", content, re.IGNORECASE)):
        missing.append("Secret & Credentials Handling")
    if not re.search(r"dependency isolation", content, re.IGNORECASE):
        missing.append("Dependency Isolation")
    if not re.search(r"dynamic verification isolation", content, re.IGNORECASE):
        missing.append("Dynamic Verification Isolation")
    if not re.search(r"untrusted evidence", content, re.IGNORECASE):
        missing.append("Untrusted evidence statement")
    if not (re.search(r"outside.*workspace", content, re.IGNORECASE) or re.search(r"never run in the same host environment as the active Orchestra workspace", content, re.IGNORECASE)):
        missing.append("Execution outside the active Orchestra workspace statement")
    return missing

def check_artificer_boundaries_md(content):
    missing = []
    specialists = ["Artificer", "Cloak", "Cipher", "Clockwork", "Ponytail", "Overseer", "Dagger", "Arbiter", "The Governor", "The Steward"]
    for spec in specialists:
        if not re.search(re.escape(spec), content, re.IGNORECASE):
            missing.append(f"Boundary entry for {spec}")

    if re.search(r"map to\s+\*?\*?artificer\*?\*?\s+for.*code\s+changes|implementation\s+is\s+owned\s+by\s+artificer|artificer\s+implements", content, re.IGNORECASE):
        missing.append("rejection of implementation ownership assigned to Artificer")

    # 1. Implementation or source modification
    if not check_prohibition_contract(content, r"implement|write|modify|edit", r"code|source|change|interface|config"):
        missing.append("Artificer does not implement source changes statement")

    # 2. Test execution or test ownership
    if not check_prohibition_contract(content, r"run|write|execute", r"test|test runner|test suite"):
        missing.append("Artificer does not run tests statement")

    # 3. Evidence-completeness decisions
    if not check_prohibition_contract(content, r"decide|approve|adjudicate|determine", r"evidence|complete|completeness|duplicate"):
        missing.append("Artificer does not decide if evidence is complete statement")

    # 4. Licensing or IP approval
    if not check_prohibition_contract(content, r"approve|clear|authorize|verify", r"license|licensing|compliance|copyright|ip"):
        missing.append("Artificer does not approve licensing statement")

    # 5. Live adversarial or penetration testing
    if not check_prohibition_contract(content, r"perform|run|conduct|execute", r"adversarial|penetration|vulnerability|live security"):
        missing.append("Artificer does not perform live adversarial testing statement")

    return missing

def check_evidence_requirements_md(content):
    missing = []
    categories = [
        "SOURCE_CONFIRMED",
        "DOCUMENTATION_CLAIM",
        "STATIC_ANALYSIS",
        "EXISTING_TEST_EVIDENCE",
        "RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION",
        "INFERENCE",
        "UNVERIFIED"
    ]
    for cat in categories:
        pattern = r"-\s+\*\*`?" + re.escape(cat) + r"`?\*\*"
        matches = re.findall(pattern, content)
        if len(matches) == 0:
            missing.append(f"Missing evidence category: {cat}")
        elif len(matches) > 1:
            missing.append(f"Duplicate evidence category: {cat}")

    if not (re.search(r"pinned commit", content, re.IGNORECASE) or re.search(r"traceability", content, re.IGNORECASE)):
        missing.append("Pinned commit traceability statement")
    if not (re.search(r"file.*line", content, re.IGNORECASE) or re.search(r"line range", content, re.IGNORECASE)):
        missing.append("File and line-range evidence statement")
    if not (re.search(r"no-execution", content, re.IGNORECASE) or re.search(r"never execute", content, re.IGNORECASE) or re.search(r"never attempt to create.*evidence by executing", content, re.IGNORECASE)):
        missing.append("Explicit no-execution warning statement")
    if not (re.search(r"separately authorized", content, re.IGNORECASE) or re.search(r"dedicated.*task", content, re.IGNORECASE)):
        missing.append("Runtime evidence separately authorized statement")

    return missing

def check_artificer_workflow_md(content):
    missing = []
    stages = [
        "Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6", "Stage 7"
    ]
    for stage in stages:
        if stage not in content:
            missing.append(f"Workflow stage header or text: {stage}")

    gov_roles = ["Arbiter", "The Governor", "The Steward", "Maintainer"]
    for role in gov_roles:
        if not re.search(re.escape(role), content, re.IGNORECASE):
            missing.append(f"Governance review role: {role}")

    if not (re.search(r"specialist-owned", content, re.IGNORECASE) or re.search(r"owned by.*specialist", content, re.IGNORECASE)):
        missing.append("Specialist-owned implementation statement")

    return missing

def check_output_formats_md(content):
    missing = []
    audit_fields = [
        "repository URL", "commit SHA", "license", "lines of code examined",
        "classification", "assigned specialist", "attribution obligation",
        "compatibility verdict", "security & risk log"
    ]
    for field in audit_fields:
        if not re.search(re.escape(field).replace(r"\ ", r"\s+"), content, re.IGNORECASE):
            missing.append(f"Individual Source Audit field: {field}")

    proposal_fields = [
        "summary of source audits", "selected design patterns", "owner specialist",
        "verification & testing plan", "arbiter.*status", "governor.*status"
    ]
    for field in proposal_fields:
        if not re.search(field, content, re.IGNORECASE):
            missing.append(f"Evolution Proposal field: {field.replace('.*', ' ')}")

    return missing

def check_documentation_contracts(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    doc_checks = [
        ("internal/artificer/ARTIFICER.md", check_artificer_md),
        ("docs/internal/SECURITY_BOUNDARIES.md", check_security_boundaries_md),
        ("docs/internal/ARTIFICER_BOUNDARIES.md", check_artificer_boundaries_md),
        ("docs/internal/EVIDENCE_REQUIREMENTS.md", check_evidence_requirements_md),
        ("docs/internal/ARTIFICER_WORKFLOW.md", check_artificer_workflow_md),
        ("internal/artificer/OUTPUT_FORMATS.md", check_output_formats_md)
    ]
    for rel_path, check_fn in doc_checks:
        full_path = repo_root / rel_path
        if full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8")
                missing_concepts = check_fn(content)
                if missing_concepts:
                    reason = f"Missing core concepts: {', '.join(missing_concepts)}"
                    failures.append(ValidationFailure(rel_path, reason, f"Restore the missing boundary statement or concept in {rel_path}"))
            except Exception as e:
                failures.append(ValidationFailure(rel_path, f"Failed to check file: {e}", f"Fix validation check for {rel_path}"))
    return failures

def check_public_non_registration(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    forbidden_paths = [
        "commands/artificer.md",
        "skills/artificer",
        "orchestra_runtime/artificer.py",
        "orchestra_runtime/artificer",
        "adapters/codex/skills/artificer"
    ]
    for rel_path in forbidden_paths:
        full_path = repo_root / rel_path
        if full_path.exists():
            failures.append(ValidationFailure(rel_path, "Forbidden Artificer path exists", f"Delete the forbidden path at {rel_path}"))

    targets = [
        "plugin.json",
        "SKILL_INDEX.md",
        "ROUTING_MAP.md",
        "commands",
        "skills",
        "orchestra_runtime",
        "adapters/codex/skills"
    ]
    files_to_scan = []
    for target in targets:
        full_path = Path(repo_root) / target
        if not full_path.exists():
            continue
        if full_path.is_file():
            files_to_scan.append(full_path)
        elif full_path.is_dir():
            for root, dirs, files in os.walk(full_path):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
                for file in files:
                    if file.endswith(".pyc") or file.startswith("."):
                        continue
                    files_to_scan.append(Path(root) / file)

    for file_path in files_to_scan:
        rel_path = os.path.relpath(file_path, repo_root)
        try:
            content = file_path.read_text(encoding="utf-8")
            if "artificer" in content.lower():
                failures.append(ValidationFailure(rel_path, "Contains forbidden term 'artificer'", "Remove all public references to 'artificer' in this file"))
        except Exception:
            pass

    return failures

def validate_repository(repo_root: Path) -> list[ValidationFailure]:
    failures = []
    failures.extend(check_required_files(repo_root))
    failures.extend(validate_pattern_schema(repo_root))
    failures.extend(validate_source_intake_schema(repo_root))
    failures.extend(check_documentation_contracts(repo_root))
    failures.extend(check_public_non_registration(repo_root))
    return failures

def main() -> int:
    try:
        args = parse_args()
    except argparse.ArgumentError as e:
        print(f"Invalid CLI usage: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unrecoverable error: {e}", file=sys.stderr)
        return 2

    if args.repo_root:
        repo_root = Path(args.repo_root)
    else:
        repo_root = Path(__file__).resolve().parent.parent

    # Run actual checks to print sectioned output
    print("[1] Required Internal Files")
    req_fails = check_required_files(repo_root)
    req_failed_targets = {f.target for f in req_fails}
    for rel_path in REQUIRED_FILES:
        if rel_path not in req_failed_targets:
            print(f"[PASS] {rel_path}: File exists and is non-empty.")
    for f in req_fails:
        print(f"[FAIL] {f.target}: {f.reason}.")

    print("\n[2] JSON Schema Contracts")
    pattern_fails = validate_pattern_schema(repo_root)
    source_fails = validate_source_intake_schema(repo_root)
    schema_fails = pattern_fails + source_fails
    schema_failed_targets = {f.target for f in schema_fails}

    pattern_schema_rel = "internal/artificer/PATTERN_SCHEMA.json"
    if pattern_schema_rel not in schema_failed_targets:
        print(f"[PASS] {pattern_schema_rel}: Schema is valid and compliant.")
    else:
        for f in pattern_fails:
            print(f"[FAIL] {f.target}: {f.reason}.")

    source_schema_rel = "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
    if source_schema_rel not in schema_failed_targets:
        print(f"[PASS] {source_schema_rel}: Schema is valid and compliant.")
    else:
        for f in source_fails:
            print(f"[FAIL] {f.target}: {f.reason}.")

    print("\n[3] Documentation Boundary Contracts")
    doc_fails = check_documentation_contracts(repo_root)
    doc_failed_targets = {f.target for f in doc_fails}
    doc_checks_paths = [
        "internal/artificer/ARTIFICER.md",
        "docs/internal/SECURITY_BOUNDARIES.md",
        "docs/internal/ARTIFICER_BOUNDARIES.md",
        "docs/internal/EVIDENCE_REQUIREMENTS.md",
        "docs/internal/ARTIFICER_WORKFLOW.md",
        "internal/artificer/OUTPUT_FORMATS.md"
    ]
    for rel_path in doc_checks_paths:
        if rel_path not in doc_failed_targets:
            print(f"[PASS] {rel_path}: All boundary and contract statements verified.")
        else:
            for f in doc_fails:
                if f.target == rel_path:
                    print(f"[FAIL] {f.target}: {f.reason}.")

    print("\n[4] Public Non-Registration")
    non_reg_fails = check_public_non_registration(repo_root)
    for f in non_reg_fails:
        print(f"[FAIL] {f.target}: {f.reason}.")
    if not non_reg_fails:
        print("[PASS] Public non-registration: Artificer is absent from all public surfaces.")

    print("\n[5] Summary")
    all_failures = req_fails + schema_fails + doc_fails + non_reg_fails
    if all_failures:
        print(f"Validation Failed: {len(all_failures)} failures detected.")
        for f in all_failures:
            print(f"  - {f.target}: {f.reason}")
            print(f"    Remediation: {f.remediation}")
        return 1
    else:
        print("Validation Passed: All Artificer internal contracts are valid.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
