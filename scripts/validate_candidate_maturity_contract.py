import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

MATURITY_STATES = (
    "PROPOSED",
    "IMPLEMENTING",
    "FROZEN_CANDIDATE",
    "ACCEPTED",
    "MERGE_READY",
    "MERGE_APPLIED_UNVERIFIED",
    "MERGED_VERIFIED",
    "RETIRED",
)
ALLOWED_TRANSITIONS = {
    None: {"PROPOSED"},
    "PROPOSED": {"IMPLEMENTING"},
    "IMPLEMENTING": {"FROZEN_CANDIDATE"},
    "FROZEN_CANDIDATE": {"ACCEPTED"},
    "ACCEPTED": {"MERGE_READY"},
    "MERGE_READY": {"MERGE_APPLIED_UNVERIFIED"},
    "MERGE_APPLIED_UNVERIFIED": {"MERGED_VERIFIED"},
    "MERGED_VERIFIED": {"RETIRED"},
    "RETIRED": set(),
}
FROZEN_OR_LATER = {
    "FROZEN_CANDIDATE",
    "ACCEPTED",
    "MERGE_READY",
    "MERGE_APPLIED_UNVERIFIED",
    "MERGED_VERIFIED",
    "RETIRED",
}
PREFREEZE_STATES = {"PROPOSED", "IMPLEMENTING"}
EVIDENCE_REQUIRED_STATES = {
    "FROZEN_CANDIDATE",
    "ACCEPTED",
    "MERGE_READY",
    "MERGE_APPLIED_UNVERIFIED",
    "MERGED_VERIFIED",
    "RETIRED",
}
ALLOWED_REMEDIATION_CLASSES = {
    "BUG_FIX",
    "TEST_REMEDIATION",
    "SECURITY_REMEDIATION",
    "GOVERNANCE_REMEDIATION",
    "PROTOCOL_CORRECTION",
    "EVIDENCE_CORRECTION",
    "DOCUMENTATION_TRUTH_CORRECTION",
    "ACCEPTANCE_CRITERIA_REMEDIATION",
}
FORBIDDEN_REMEDIATION_CLASSES = {
    "NEW_FEATURE",
    "UNRELATED_OPTIMIZATION",
    "ARCHITECTURAL_EXPANSION",
    "NICE_TO_HAVE",
    "NEW_INTEGRATION",
    "NEW_SCOPE",
    "DEPENDENCY_OR_POLICY_EXPANSION",
    "VALIDATOR_WEAKENING",
}
FROZEN_DIMENSIONS = {
    "OBJECTIVE",
    "SCOPE",
    "DEPENDENCY_POSTURE",
    "ARCHITECTURE_DECISION",
    "ACCEPTANCE_CRITERIA",
}


def _set_path(document, path, value):
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = copy.deepcopy(value)


def _delete_path(document, path):
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target.pop(parts[-1], None)


def materialize_record_case(data, case):
    record = copy.deepcopy(data["base_record"])
    for key, value in case.get("overrides", {}).items():
        record[key] = copy.deepcopy(value)
    for path, value in case.get("set", {}).items():
        _set_path(record, path, value)
    for path in case.get("delete", []):
        _delete_path(record, path)
    return record


def classify_frozen_change(case):
    change_class = str(case.get("change_class", ""))
    identity_changes = case.get("candidate_identity_changes")
    dimensions = case.get("frozen_dimension_changes")

    if not isinstance(identity_changes, bool) or not isinstance(dimensions, list):
        return "FULL_REVIEW_REQUIRED"
    if any(item not in FROZEN_DIMENSIONS for item in dimensions):
        return "FULL_REVIEW_REQUIRED"
    if change_class in FORBIDDEN_REMEDIATION_CLASSES:
        return "PROHIBITED_AS_REMEDIATION"
    if dimensions:
        return "READMISSION_OR_IMPLEMENTATION_REQUIRED"
    if change_class not in ALLOWED_REMEDIATION_CLASSES:
        return "FULL_REVIEW_REQUIRED"
    if not identity_changes:
        return "INVALID_FROZEN_IDENTITY_REUSE"
    return "BOUNDED_REMEDIATION_NEW_IDENTITY_REQUIRED"


def _schema_errors(schema, record):
    validator = Draft202012Validator(schema)
    return sorted(validator.iter_errors(record), key=lambda error: list(error.path))


def semantic_record_errors(record):
    errors = []
    maturity = record["maturity"]
    freeze = record["freeze"]
    repo = record["repository_identity"]
    state = maturity["state"]
    previous = maturity["previous_state"]

    if state not in ALLOWED_TRANSITIONS.get(previous, set()):
        errors.append(f"invalid recorded maturity transition: {previous!r} -> {state!r}")

    if state in FROZEN_OR_LATER:
        if freeze["status"] != "FROZEN":
            errors.append("FROZEN_CANDIDATE and later states require freeze.status=FROZEN")
        for field in ("candidate_identity", "scope", "acceptance", "authority_reference"):
            if freeze[field] is None:
                errors.append(f"frozen candidate requires freeze.{field}")
    elif state in PREFREEZE_STATES:
        if freeze["status"] != "NOT_FROZEN":
            errors.append("PROPOSED and IMPLEMENTING records must remain NOT_FROZEN")
        for field in ("candidate_identity", "scope", "acceptance", "authority_reference"):
            if freeze[field] is not None:
                errors.append(f"prefreeze candidate must not carry freeze.{field}")

    if freeze["status"] == "FROZEN" and freeze["candidate_identity"] is not None:
        candidate_identity = freeze["candidate_identity"]
        if candidate_identity["base_sha"] != repo["base_sha"]:
            errors.append("freeze candidate base_sha must match repository_identity.base_sha")
        if candidate_identity["base_tree"] != repo["base_tree"]:
            errors.append("freeze candidate base_tree must match repository_identity.base_tree")

    if state in EVIDENCE_REQUIRED_STATES and not maturity["transition_evidence_refs"]:
        errors.append(f"{state} requires transition_evidence_refs")

    disposition = maturity["disposition"]
    successor = record["supersession"]["superseded_by_candidate_id"]
    if disposition == "SUPERSEDED" and not successor:
        errors.append("SUPERSEDED candidate requires superseded_by_candidate_id")
    if disposition != "SUPERSEDED" and successor is not None:
        errors.append("superseded_by_candidate_id is valid only for SUPERSEDED disposition")

    return errors


def validate_fixtures(schema, data):
    errors = []
    if data.get("schema_version") != "orchestra.candidate-maturity-fixtures.v1":
        errors.append("fixture schema_version must equal orchestra.candidate-maturity-fixtures.v1")

    base_record = data.get("base_record")
    if not isinstance(base_record, dict):
        errors.append("base_record must be an object")
        return errors

    if _schema_errors(schema, base_record):
        errors.append("base_record must validate against CandidateMaturityRecord schema")
    if semantic_record_errors(base_record):
        errors.append("base_record must satisfy Candidate Maturity semantic rules")

    for case in data.get("valid_record_cases", []):
        record = materialize_record_case(data, case)
        if _schema_errors(schema, record):
            errors.append(f"{case.get('id')}: expected schema-valid record")
            continue
        semantic_errors = semantic_record_errors(record)
        if semantic_errors:
            errors.append(f"{case.get('id')}: expected semantic-valid record: {semantic_errors}")

    for case in data.get("invalid_record_cases", []):
        record = materialize_record_case(data, case)
        if not _schema_errors(schema, record):
            errors.append(f"{case.get('id')}: expected schema rejection")

    for case in data.get("semantic_invalid_cases", []):
        record = materialize_record_case(data, case)
        if _schema_errors(schema, record):
            errors.append(f"{case.get('id')}: semantic-invalid fixture must remain schema-valid")
            continue
        if not semantic_record_errors(record):
            errors.append(f"{case.get('id')}: expected semantic rejection")

    for case in data.get("frozen_change_cases", []):
        actual = classify_frozen_change(case)
        if actual != case.get("expected"):
            errors.append(f"{case.get('id')}: expected {case.get('expected')} but got {actual}")

    return errors


def validate(root):
    root = Path(root)
    schema_path = root / "machine/schemas/candidate-maturity-record.v1.schema.json"
    fixture_path = root / "tests/behavior/candidate-maturity-record-fixtures.json"
    policy_path = root / "docs/governance/CANDIDATE_MATURITY_FEATURE_FREEZE.md"
    governance_index_path = root / "docs/governance/README.md"
    errors = []

    for path in (schema_path, fixture_path, policy_path, governance_index_path):
        if not path.is_file():
            errors.append(f"missing required Candidate Maturity surface: {path.relative_to(root)}")
    if errors:
        return errors

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"Candidate Maturity JSON/schema parse failure: {exc}"]

    errors.extend(validate_fixtures(schema, fixtures))

    policy = policy_path.read_text(encoding="utf-8")
    governance_index = governance_index_path.read_text(encoding="utf-8")

    required_policy_terms = (
        "RUNTIME_LIFECYCLE != DEVELOPMENT_CANDIDATE_MATURITY",
        "FROZEN_CANDIDATE != ACCEPTED",
        "ACCEPTED != MERGE_READY",
        "MERGE_READY != MERGE_AUTHORITY",
        "FREEZE != AUTHORITY",
        "Any source change after freeze creates a new candidate identity.",
        "BOUNDED_REMEDIATION_NEW_IDENTITY_REQUIRED",
        "RETIRED != BRANCH_DELETION_AUTHORITY",
    )
    for term in required_policy_terms:
        if term not in policy:
            errors.append(f"Candidate Maturity policy missing boundary: {term}")

    for remediation in sorted(ALLOWED_REMEDIATION_CLASSES | FORBIDDEN_REMEDIATION_CLASSES):
        if remediation not in policy:
            errors.append(f"Candidate Maturity policy missing remediation class: {remediation}")

    if "CANDIDATE_MATURITY_FEATURE_FREEZE.md" not in governance_index:
        errors.append("governance documentation index missing CANDIDATE_MATURITY_FEATURE_FREEZE.md")

    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Candidate Maturity and Feature Freeze v1 contract is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
