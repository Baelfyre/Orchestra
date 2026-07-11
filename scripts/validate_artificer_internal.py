#!/usr/bin/env python3
import argparse
import os
import sys
import json
import re
from pathlib import Path

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


def parse_args():
    parser = argparse.ArgumentParser(description="Artificer Internal Boundary and Contract Validator")
    parser.add_argument("--repo-root", type=str, default=None, help="Root directory of the repository")
    return parser.parse_args()


def validate_shared_schema(schema_dict, filename):
    failures = []
    if not isinstance(schema_dict, dict):
        failures.append((filename, "Top-level structure is not a JSON object", "Change the top-level schema to a JSON object"))
        return failures

    schema_url = schema_dict.get("$schema")
    if schema_url != "http://json-schema.org/draft-07/schema#":
        failures.append((filename, f"Invalid $schema claim: {schema_url}", "Ensure '$schema' is 'http://json-schema.org/draft-07/schema#'"))

    if schema_dict.get("type") != "object":
        failures.append((filename, "Top-level 'type' must be 'object'", "Set 'type' to 'object' at the root of the schema"))

    properties = schema_dict.get("properties")
    if not isinstance(properties, dict):
        failures.append((filename, "'properties' must be a JSON object", "Define 'properties' as a JSON object"))

    required = schema_dict.get("required")
    if not isinstance(required, list):
        failures.append((filename, "'required' must be a list", "Define 'required' as a list of property names"))
    else:
        if isinstance(properties, dict):
            for req_field in required:
                if req_field not in properties:
                    failures.append((filename, f"Required field '{req_field}' not present in properties", f"Add '{req_field}' definition to properties"))

    if schema_dict.get("additionalProperties") is not False:
        failures.append((filename, "'additionalProperties' must be false", "Set 'additionalProperties' to false"))

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
        failures.append((filename, f"Duplicate values found in enum array at '{path}': {enums}", f"Remove duplicate entries from the enum array at '{path}'"))

    return failures


def check_artificer_md(content):
    missing = []
    if not (re.search(r"maintainer-only", content, re.IGNORECASE) or re.search(r"maintainer explicitly", content, re.IGNORECASE)):
        missing.append("maintainer-only activation")
    if not re.search(r"internal", content, re.IGNORECASE):
        missing.append("internal visibility")
    if not re.search(r"read-only", content, re.IGNORECASE):
        missing.append("read-only external-source auditing")
    if not (re.search(r"no public routing", content, re.IGNORECASE) or re.search(r"blocked from.*routing", content, re.IGNORECASE) or re.search(r"routing restrictions", content, re.IGNORECASE)):
        missing.append("no public routing")
    if not (re.search(r"plugin\.json", content, re.IGNORECASE) or re.search(r"public manifest", content, re.IGNORECASE)):
        missing.append("no manifest registration")
    if not (re.search(r"orchestra_runtime", content, re.IGNORECASE) or re.search(r"runtime command", content, re.IGNORECASE)):
        missing.append("no runtime route")
    if not re.search(r"adapter", content, re.IGNORECASE):
        missing.append("no adapter export")
    if not (re.search(r"execute", content, re.IGNORECASE) or re.search(r"no code execution", content, re.IGNORECASE)):
        missing.append("no external code execution")
    if not (re.search(r"install", content, re.IGNORECASE) or re.search(r"dependency", content, re.IGNORECASE)):
        missing.append("no external dependency installation")
    if not (re.search(r"copy", content, re.IGNORECASE) or re.search(r"cherry-pick", content, re.IGNORECASE)):
        missing.append("no automatic code copying or cherry-picking")
    if not (re.search(r"propose", content, re.IGNORECASE) or re.search(r"non-goals", content, re.IGNORECASE)):
        missing.append("no self-implementation")
    if not (re.search(r"non-goals", content, re.IGNORECASE) or re.search(r"do not", content, re.IGNORECASE)):
        missing.append("no self-approval")
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

    if not (re.search(r"implement", content, re.IGNORECASE) or re.search(r"write.*code", content, re.IGNORECASE)):
        missing.append("Artificer does not implement source changes statement")
    if not re.search(r"run tests", content, re.IGNORECASE):
        missing.append("Artificer does not run tests statement")
    if not (re.search(r"evidence is complete", content, re.IGNORECASE) or re.search(r"approve evidence", content, re.IGNORECASE)):
        missing.append("Artificer does not decide if evidence is complete statement")
    if not (re.search(r"approve license", content, re.IGNORECASE) or re.search(r"approve licensing", content, re.IGNORECASE)):
        missing.append("Artificer does not approve licensing statement")
    if not (re.search(r"adversarial testing", content, re.IGNORECASE) or re.search(r"penetration testing", content, re.IGNORECASE) or re.search(r"vulnerability", content, re.IGNORECASE)):
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


def main():
    args = parse_args()
    if args.repo_root:
        repo_root = Path(args.repo_root)
    else:
        repo_root = Path(__file__).resolve().parent.parent

    failures = []

    # [1] Required Internal Files
    print("[1] Required Internal Files")
    for relative_path in REQUIRED_FILES:
        full_path = repo_root / relative_path
        if not full_path.exists():
            failures.append((relative_path, "File does not exist", f"Create the missing specification file at {relative_path}"))
            print(f"[FAIL] {relative_path}: File does not exist.")
        elif not full_path.is_file():
            failures.append((relative_path, "Not a regular file", f"Ensure {relative_path} is a regular file and not a directory"))
            print(f"[FAIL] {relative_path}: Not a regular file.")
        else:
            try:
                content = full_path.read_text(encoding="utf-8")
                if not content.strip():
                    failures.append((relative_path, "File is empty", f"Add content to the required specification file {relative_path}"))
                    print(f"[FAIL] {relative_path}: File is empty.")
                else:
                    print(f"[PASS] {relative_path}: File exists and is non-empty.")
            except UnicodeDecodeError:
                failures.append((relative_path, "Cannot decode as UTF-8", f"Convert encoding of {relative_path} to UTF-8"))
                print(f"[FAIL] {relative_path}: Cannot decode as UTF-8.")

    # [2] JSON Schema Contracts
    print("\n[2] JSON Schema Contracts")
    pattern_schema_path = repo_root / "internal/artificer/PATTERN_SCHEMA.json"
    if pattern_schema_path.is_file():
        try:
            pattern_schema = json.loads(pattern_schema_path.read_text(encoding="utf-8"))
            shared_fails = validate_shared_schema(pattern_schema, "internal/artificer/PATTERN_SCHEMA.json")
            for f_target, f_reason, f_remedy in shared_fails:
                failures.append((f_target, f_reason, f_remedy))
                print(f"[FAIL] {f_target}: {f_reason}.")

            properties = pattern_schema.get("properties", {})
            required = pattern_schema.get("required", [])

            expected_props = {"name", "description", "source_file", "line_range", "classification", "assigned_specialist", "license_implications"}
            if isinstance(properties, dict) and set(properties.keys()) != expected_props:
                reason = f"Properties mismatch: expected {expected_props}, got {set(properties.keys())}"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Ensure PATTERN_SCHEMA.json defines exactly the required properties"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            expected_req = {"name", "description", "source_file", "classification", "assigned_specialist"}
            if set(required) != expected_req:
                reason = f"Required list mismatch: expected {expected_req}, got {set(required)}"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Ensure required list matches exactly the mandatory fields"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            class_enum = properties.get("classification", {}).get("enum", [])
            expected_class_enum = ["REFERENCE_ONLY", "ADAPTED_PATTERN", "CODE_REUSE_REVIEW_REQUIRED", "TEST_CORPUS_CANDIDATE", "REJECTED", "DEFERRED", "DUPLICATE", "OUT_OF_SCOPE"]
            if class_enum != expected_class_enum:
                reason = f"Classification enum mismatch: expected {expected_class_enum}, got {class_enum}"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Set classification enum to the exact expected values"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            spec_enum = properties.get("assigned_specialist", {}).get("enum", [])
            expected_spec_enum = ["cloak", "cipher", "clockwork", "ponytail", "overseer", "dagger", "the-governor", "arbiter", "chronicler", "weaver", "scribe", "the-steward"]
            if spec_enum != expected_spec_enum:
                reason = f"Assigned specialist enum mismatch: expected {expected_spec_enum}, got {spec_enum}"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Set assigned_specialist enum to the exact expected values"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            if "artificer" in spec_enum:
                reason = "assigned_specialist enum must never contain 'artificer'"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Remove 'artificer' from the assigned_specialist enum list"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            lr_pattern = properties.get("line_range", {}).get("pattern")
            if lr_pattern != r"^\d+-\d+$":
                reason = f"line_range pattern mismatch: expected r'^\\d+-\\d+$', got {lr_pattern!r}"
                failures.append(("internal/artificer/PATTERN_SCHEMA.json", reason, "Set line_range pattern to '^\\d+-\\d+$'"))
                print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: {reason}.")

            if not shared_fails and len(failures) == 0:
                print("[PASS] internal/artificer/PATTERN_SCHEMA.json: Schema is valid and compliant.")
        except Exception as e:
            failures.append(("internal/artificer/PATTERN_SCHEMA.json", f"JSON parsing failed: {e}", "Fix the JSON syntax of PATTERN_SCHEMA.json"))
            print(f"[FAIL] internal/artificer/PATTERN_SCHEMA.json: JSON parsing failed.")

    source_schema_path = repo_root / "internal/artificer/SOURCE_INTAKE_SCHEMA.json"
    if source_schema_path.is_file():
        try:
            source_schema = json.loads(source_schema_path.read_text(encoding="utf-8"))
            shared_fails = validate_shared_schema(source_schema, "internal/artificer/SOURCE_INTAKE_SCHEMA.json")
            for f_target, f_reason, f_remedy in shared_fails:
                failures.append((f_target, f_reason, f_remedy))
                print(f"[FAIL] {f_target}: {f_reason}.")

            properties = source_schema.get("properties", {})
            required = source_schema.get("required", [])

            expected_props = {"repository", "repository_owner", "canonical_url", "license", "default_branch", "reviewed_commit_sha", "review_date", "files_examined", "runtime_behavior_tested", "source_confidence"}
            if isinstance(properties, dict) and set(properties.keys()) != expected_props:
                reason = f"Properties mismatch: expected {expected_props}, got {set(properties.keys())}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Ensure SOURCE_INTAKE_SCHEMA.json defines exactly the required properties"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            expected_req = {"repository", "repository_owner", "canonical_url", "license", "reviewed_commit_sha", "review_date", "files_examined", "runtime_behavior_tested", "source_confidence"}
            if set(required) != expected_req:
                reason = f"Required list mismatch: expected {expected_req}, got {set(required)}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Ensure required list matches exactly the mandatory fields"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            commit_pattern = properties.get("reviewed_commit_sha", {}).get("pattern")
            if commit_pattern != r"^[0-9a-fA-F]{40}$":
                reason = f"reviewed_commit_sha pattern mismatch: expected '^[0-9a-fA-F]{40}$', got {commit_pattern!r}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set reviewed_commit_sha pattern to '^[0-9a-fA-F]{40}$'"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            date_format = properties.get("review_date", {}).get("format")
            if date_format != "date":
                reason = f"review_date format mismatch: expected 'date', got {date_format!r}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set review_date format to 'date'"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            rbt_type = properties.get("runtime_behavior_tested", {}).get("type")
            if rbt_type != "boolean":
                reason = f"runtime_behavior_tested type mismatch: expected 'boolean', got {rbt_type!r}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set runtime_behavior_tested type to 'boolean'"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            fe_type = properties.get("files_examined", {}).get("type")
            if fe_type != "array":
                reason = f"files_examined type mismatch: expected 'array', got {fe_type!r}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set files_examined type to 'array'"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            fe_items = properties.get("files_examined", {}).get("items", {})
            fe_items_ap = fe_items.get("additionalProperties")
            if fe_items_ap is not False:
                reason = f"files_examined items additionalProperties must be false, got {fe_items_ap}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set files_examined items additionalProperties to false"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            sc_enum = properties.get("source_confidence", {}).get("enum", [])
            expected_sc_enum = ["HIGH", "MEDIUM", "LOW"]
            if sc_enum != expected_sc_enum:
                reason = f"Source confidence enum mismatch: expected {expected_sc_enum}, got {sc_enum}"
                failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", reason, "Set source_confidence enum to exactly HIGH, MEDIUM, LOW"))
                print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: {reason}.")

            if not shared_fails and len(failures) == 0:
                print("[PASS] internal/artificer/SOURCE_INTAKE_SCHEMA.json: Schema is valid and compliant.")
        except Exception as e:
            failures.append(("internal/artificer/SOURCE_INTAKE_SCHEMA.json", f"JSON parsing failed: {e}", "Fix the JSON syntax of SOURCE_INTAKE_SCHEMA.json"))
            print(f"[FAIL] internal/artificer/SOURCE_INTAKE_SCHEMA.json: JSON parsing failed.")

    # [3] Documentation Boundary Contracts
    print("\n[3] Documentation Boundary Contracts")
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
                    failures.append((rel_path, reason, f"Restore the missing boundary statement or concept in {rel_path}"))
                    print(f"[FAIL] {rel_path}: {reason}.")
                else:
                    print(f"[PASS] {rel_path}: All boundary and contract statements verified.")
            except Exception as e:
                failures.append((rel_path, f"Failed to check file: {e}", f"Fix validation check for {rel_path}"))
                print(f"[FAIL] {rel_path}: Failed to check file.")

def check_public_non_registration(repo_root):
    failures = []
    forbidden_paths = [
        "commands/artificer.md",
        "skills/artificer",
        "orchestra_runtime/artificer.py",
        "orchestra_runtime/artificer",
        "adapters/codex/skills/artificer"
    ]
    for rel_path in forbidden_paths:
        full_path = Path(repo_root) / rel_path
        if full_path.exists():
            failures.append((rel_path, "Forbidden Artificer path exists", f"Delete the forbidden path at {rel_path}"))

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
                failures.append((rel_path, "Contains forbidden term 'artificer'", "Remove all public references to 'artificer' in this file"))
        except Exception:
            pass

    return failures


# Inside main:
    # [4] Public Non-Registration
    print("\n[4] Public Non-Registration")
    non_reg_fails = check_public_non_registration(repo_root)
    for f_target, f_reason, f_remedy in non_reg_fails:
        failures.append((f_target, f_reason, f_remedy))
        print(f"[FAIL] {f_target}: {f_reason}.")

    if len(non_reg_fails) == 0:
        print("[PASS] Public non-registration: Artificer is absent from all public surfaces.")

    # [5] Summary
    print("\n[5] Summary")
    if failures:
        print(f"Validation Failed: {len(failures)} failures detected.")
        for f_target, f_reason, f_remedy in failures:
            print(f"  - {f_target}: {f_reason}")
            print(f"    Remediation: {f_remedy}")
        sys.exit(1)
    else:
        print("Validation Passed: All Artificer internal contracts are valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
