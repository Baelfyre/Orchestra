import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_VERSION = "orchestra.qualification-gate-plan.v1"
CONTROLLED_EVALUATION_DISPOSITIONS = {
    "ADVERSARIAL_VALIDATION_REQUIRED",
    "SIMULATION_REQUIRED",
    "EXPERIMENT_REQUIRED",
}
MANDATORY_AUDIT_CLASSES = {
    "GOVERNANCE_OR_SECURITY_CHANGE",
    "TRUST_BOUNDARY_CHANGE",
    "ADAPTIVE_PROMOTION",
    "RELEASE_RECOVERY_AUTOMATION",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def deep_merge(base, overrides):
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def materialize_case(fixture, case):
    return deep_merge(fixture["base_record"], case.get("overrides", {}))


def effective_audit_required(record):
    audit = record["independent_audit"]
    if audit["requirement"] == "REQUIRED":
        return True
    if audit["requirement"] == "CONDITIONAL":
        return audit["condition_triggered"] is True
    return False


def minimum_gate_requirements(record):
    factors = record["classification"]["factors"]
    change_class = record["classification"]["change_class"]
    evaluation = record["evaluation"]["disposition"]
    return {
        "engineering_validation": True,
        "regression_compatibility": any(
            (
                factors["runtime_behavior"],
                factors["public_contract"],
                factors["dependency_or_integration"],
                change_class in {
                    "CAPABILITY_CHANGE",
                    "TRUST_BOUNDARY_CHANGE",
                    "ADAPTIVE_PROMOTION",
                    "RELEASE_RECOVERY_AUTOMATION",
                },
            )
        ),
        "security_governance": any(
            (
                factors["dependency_or_integration"],
                factors["governance_or_security"],
                factors["trust_boundary"],
                factors["adaptive_promotion"],
                factors["release_or_recovery_automation"],
                factors["destructive_automation"],
                change_class in MANDATORY_AUDIT_CLASSES,
            )
        ),
        "controlled_evaluation": (
            evaluation in CONTROLLED_EVALUATION_DISPOSITIONS
            or factors["adaptive_promotion"]
        ),
        "independent_audit": effective_audit_required(record),
    }


def derive_qualification(record):
    statuses = [
        gate["status"]
        for gate in record["gates"].values()
        if gate["applicability"] == "REQUIRED"
    ]
    if "FAIL" in statuses:
        return "BLOCKED"
    if statuses and all(status == "PASS" for status in statuses):
        return "QUALIFIED"
    return "QUALIFICATION_PENDING"


def validate_record(record, schema):
    errors = []
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "$"
        errors.append(f"schema {path}: {error.message}")
    if errors:
        return errors

    classification = record["classification"]
    factors = classification["factors"]
    change_class = classification["change_class"]

    if factors["trivial_truth_correction"]:
        risky = [
            name for name, value in factors.items()
            if name != "trivial_truth_correction" and value
        ]
        if change_class != "TRIVIAL_CORRECTION" or risky:
            errors.append("trivial truth correction cannot carry material change factors")

    mandatory_audit = any(
        (
            factors["governance_or_security"],
            factors["trust_boundary"],
            factors["adaptive_promotion"],
            factors["release_or_recovery_automation"],
            factors["destructive_automation"],
            change_class in MANDATORY_AUDIT_CLASSES,
        )
    )
    audit = record["independent_audit"]
    if mandatory_audit and audit["requirement"] != "REQUIRED":
        errors.append("mandatory audit trigger requires REQUIRED independent audit")
    if change_class == "BOUNDED_FIX" and audit["requirement"] == "NOT_REQUIRED":
        errors.append("bounded fix audit policy must be CONDITIONAL or REQUIRED")

    evaluation = record["evaluation"]["disposition"]
    if factors["adaptive_promotion"] and evaluation not in CONTROLLED_EVALUATION_DISPOSITIONS:
        errors.append("adaptive promotion requires controlled evaluation")

    minimums = minimum_gate_requirements(record)
    for gate_name, required in minimums.items():
        if required and record["gates"][gate_name]["applicability"] != "REQUIRED":
            errors.append(f"{gate_name} must be REQUIRED for this candidate")

    audit_required = effective_audit_required(record)
    audit_gate = record["gates"]["independent_audit"]
    expected = "REQUIRED" if audit_required else "NOT_APPLICABLE"
    if audit_gate["applicability"] != expected:
        errors.append("independent audit gate must match effective audit requirement")
    if audit_required and audit["status"] != audit_gate["status"]:
        errors.append("independent audit status must match its gate status")
    if not audit_required and audit["status"] != "NOT_APPLICABLE":
        errors.append("non-required independent audit must be NOT_APPLICABLE")

    if minimums["controlled_evaluation"] and record["gates"]["controlled_evaluation"]["applicability"] != "REQUIRED":
        errors.append("controlled evaluation gate is required by evaluation policy")

    derived = derive_qualification(record)
    if record["qualification"]["disposition"] != derived:
        errors.append(f"qualification disposition must equal derived disposition {derived}")
    return errors


def validate_fixture(fixture, schema):
    errors = []
    if fixture.get("schema_version") != "orchestra-qualification-gate-fixtures-v1":
        return ["fixture schema_version must equal orchestra-qualification-gate-fixtures-v1"]
    base = fixture.get("base_record")
    if not isinstance(base, dict):
        return ["base_record must be an object"]
    base_errors = validate_record(base, schema)
    if base_errors:
        errors.append(f"base_record must be valid: {base_errors}")

    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty list"]
    seen = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id or case_id in seen:
            errors.append("cases must have unique non-empty ids")
            continue
        seen.add(case_id)
        expected_valid = case.get("valid")
        if not isinstance(expected_valid, bool):
            errors.append(f"{case_id}: valid must be boolean")
            continue
        record = materialize_case(fixture, case)
        record_errors = validate_record(record, schema)
        actual_valid = not record_errors
        if actual_valid != expected_valid:
            errors.append(f"{case_id}: expected valid={expected_valid} but errors were {record_errors}")
            continue
        expected_qualification = case.get("expected_qualification")
        if actual_valid and expected_qualification is not None:
            actual = record["qualification"]["disposition"]
            if actual != expected_qualification:
                errors.append(f"{case_id}: expected {expected_qualification} but got {actual}")
    return errors


def validate(root):
    root = Path(root)
    schema_path = root / "machine/schemas/qualification-gate-plan.v1.schema.json"
    fixture_path = root / "tests/behavior/qualification-gate-plan-fixtures.json"
    policy_path = root / "docs/governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md"
    for path in (schema_path, fixture_path, policy_path):
        if not path.is_file():
            return [f"missing Campaign 4 surface: {path.relative_to(root)}"]
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        fixture = load_json(fixture_path)
    except Exception as exc:
        return [f"Campaign 4 parse/schema failure: {exc}"]

    errors = validate_fixture(fixture, schema)
    policy = policy_path.read_text(encoding="utf-8")
    for term in (
        "ENGINEERING_VALIDATION",
        "REGRESSION_COMPATIBILITY",
        "SECURITY_GOVERNANCE",
        "CONTROLLED_EVALUATION",
        "INDEPENDENT_AUDIT",
        "QUALIFICATION_PENDING",
        "QUALIFIED",
        "BLOCKED",
        "QUALIFIED != ACCEPTED",
        "EXPERIMENT_PLAN != LIVE_CALL_AUTHORITY",
        "NEGATIVE_INCONCLUSIVE_PRESERVED = true",
    ):
        if term not in policy:
            errors.append(f"qualification policy missing invariant/term: {term}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Qualification gate plan v1 is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
