import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

PRIME_DIRECTIVE_TEXT = (
    "Orchestra shall permit an AI-assisted action or lifecycle transition only within explicit, "
    "reduction-only authority and current applicable evidence. It shall never infer permission from "
    "capability, routing, confidence, learned state, validation success, mergeability, or prior success. "
    "A permanent capability shall be promoted only when proportional evidence shows that it solves an "
    "Orchestra-owned problem whose benefit justifies its complexity and risk without weakening these boundaries."
)

INITIAL_DISPOSITIONS = {"ADMIT", "EXPERIMENT_ONLY", "DEFER", "REJECT"}
PROMOTION_DISPOSITIONS = {
    "ADOPT",
    "ADOPT_SIMPLIFIED",
    "ADOPT_OPTIONAL",
    "REPLACE_WITH_CONFIGURATION",
    "EXPERIMENT_ONLY",
    "DEFER",
    "REJECT_NO_MEASURABLE_VALUE",
    "REJECT_COMPLEXITY_EXCEEDS_BENEFIT",
}
INLINE_CLASSES = {
    "TRIVIAL_TRUTH_CORRECTION",
    "PARITY_REFRESH",
    "TEST_RESTORING_ACCEPTED_BEHAVIOR",
    "BOUNDED_BUG_FIX_ACCEPTED_REQUIREMENT",
}
INLINE_CLASSES_REQUIRING_ACCEPTED_REQUIREMENT = {
    "TEST_RESTORING_ACCEPTED_BEHAVIOR",
    "BOUNDED_BUG_FIX_ACCEPTED_REQUIREMENT",
}
INLINE_FORBIDDEN_FLAGS = {
    "NEW_CAPABILITY",
    "GOVERNANCE_OR_POLICY_CHANGE",
    "AUTHORITY_CHANGE_OR_EXPANSION",
    "TRUST_BOUNDARY_CHANGE",
    "NEW_DEPENDENCY_OR_INTEGRATION",
    "PROTECTED_ACTION_SEMANTICS_CHANGE",
    "PUBLIC_API_OR_COMPATIBILITY_EXPANSION",
    "SCOPE_OR_INTENT_EXPANSION",
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


def classify_inline_rationale(case):
    change_class = str(case.get("change_class", ""))
    rationale = str(case.get("rationale", "")).strip()
    accepted_refs = case.get("accepted_requirement_refs")
    flags = case.get("flags")

    if change_class not in INLINE_CLASSES or not rationale:
        return "FULL_RECORD_REQUIRED"
    if not isinstance(accepted_refs, list) or not isinstance(flags, list):
        return "FULL_RECORD_REQUIRED"
    if set(flags) & INLINE_FORBIDDEN_FLAGS:
        return "FULL_RECORD_REQUIRED"
    if change_class in INLINE_CLASSES_REQUIRING_ACCEPTED_REQUIREMENT and not accepted_refs:
        return "FULL_RECORD_REQUIRED"
    return "INLINE_RATIONALE_ALLOWED"


def _schema_errors(schema, record):
    validator = Draft202012Validator(schema)
    return sorted(validator.iter_errors(record), key=lambda error: list(error.path))


def validate_fixtures(schema, data):
    errors = []
    if data.get("schema_version") != "orchestra.feature-admission-fixtures.v1":
        errors.append("fixture schema_version must equal orchestra.feature-admission-fixtures.v1")

    base_record = data.get("base_record")
    if not isinstance(base_record, dict):
        errors.append("base_record must be an object")
        return errors
    if _schema_errors(schema, base_record):
        errors.append("base_record must validate against FeatureDecisionRecord schema")

    for case in data.get("valid_record_cases", []):
        record = materialize_record_case(data, case)
        case_errors = _schema_errors(schema, record)
        if case_errors:
            errors.append(f"{case.get('id')}: expected valid record")

    for case in data.get("invalid_record_cases", []):
        record = materialize_record_case(data, case)
        case_errors = _schema_errors(schema, record)
        if not case_errors:
            errors.append(f"{case.get('id')}: expected schema rejection")

    for case in data.get("inline_rationale_cases", []):
        actual = classify_inline_rationale(case)
        if actual != case.get("expected"):
            errors.append(f"{case.get('id')}: expected {case.get('expected')} but got {actual}")

    return errors


def validate(root):
    root = Path(root)
    schema_path = root / "machine/schemas/feature-decision-record.v1.schema.json"
    fixture_path = root / "tests/behavior/feature-decision-record-fixtures.json"
    prime_path = root / "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md"
    admission_path = root / "docs/governance/FEATURE_ADMISSION_POLICY.md"
    governance_index_path = root / "docs/governance/README.md"
    readme_index_path = root / "README.json"
    errors = []

    for path in (schema_path, fixture_path, prime_path, admission_path, governance_index_path, readme_index_path):
        if not path.is_file():
            errors.append(f"missing required Feature Admission surface: {path.relative_to(root)}")
    if errors:
        return errors

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        readme_index = json.loads(readme_index_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"Feature Admission JSON/schema parse failure: {exc}"]

    errors.extend(validate_fixtures(schema, fixtures))

    prime = prime_path.read_text(encoding="utf-8")
    admission = admission_path.read_text(encoding="utf-8")
    governance_index = governance_index_path.read_text(encoding="utf-8")

    if PRIME_DIRECTIVE_TEXT not in prime:
        errors.append("Prime Directive exact constitutional text is missing or drifted")

    required_prime_terms = (
        "CAPABILITY != AUTHORITY",
        "VALIDATION_SUCCESS != AUTHORITY",
        "ADMISSION != PROMOTION",
        "AUTONOMOUS_SELF_AMENDMENT = PROHIBITED",
        "Greater autonomy removes unnecessary pauses, not safeguards",
    )
    for term in required_prime_terms:
        if term not in prime:
            errors.append(f"Prime Directive missing invariant term: {term}")

    for disposition in sorted(INITIAL_DISPOSITIONS | PROMOTION_DISPOSITIONS):
        if disposition not in admission:
            errors.append(f"Feature Admission policy missing disposition: {disposition}")

    for term in (
        "ADMIT != promotion",
        "ADMIT != merge authority",
        "ADOPT != release or activation authority",
        "FEATURE_DECISION_RECORD != execution authority",
        "FULL_RECORD_REQUIRED",
    ):
        if term not in admission:
            errors.append(f"Feature Admission policy missing boundary: {term}")

    for path in ("docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md", "docs/governance/FEATURE_ADMISSION_POLICY.md"):
        if path not in governance_index:
            errors.append(f"governance documentation index missing {path}")

    capability = readme_index.get("capabilities", {}).get("prime_directive_feature_admission_v1")
    if not isinstance(capability, dict):
        errors.append("README.json missing prime_directive_feature_admission_v1 capability index")
    else:
        if capability.get("machine_sources") != ["machine/schemas/feature-decision-record.v1.schema.json"]:
            errors.append("README.json Feature Admission machine source mismatch")
        human_sources = capability.get("human_sources")
        if not isinstance(human_sources, list) or set(human_sources) != {
            "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md",
            "docs/governance/FEATURE_ADMISSION_POLICY.md",
        }:
            errors.append("README.json Feature Admission human source mismatch")
        if capability.get("runtime_integration") is not False:
            errors.append("README.json must record Feature Admission v1 as no runtime integration")

    governance = readme_index.get("governance", {})
    if governance.get("prime_directive") != "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md":
        errors.append("README.json governance.prime_directive mismatch")
    if governance.get("feature_admission_policy") != "docs/governance/FEATURE_ADMISSION_POLICY.md":
        errors.append("README.json governance.feature_admission_policy mismatch")

    machine_contracts = readme_index.get("machine_contracts", {})
    if machine_contracts.get("feature_decision_record_schema") != "machine/schemas/feature-decision-record.v1.schema.json":
        errors.append("README.json machine_contracts feature decision schema mismatch")

    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Prime Directive and Feature Admission v1 contract is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
