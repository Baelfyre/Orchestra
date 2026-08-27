import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_VERSION = "orchestra.repository-recovery-retirement-plan.v1"
ELIGIBLE_ACTION = "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION"


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


def derive_branch_action(branch):
    classification = branch["classification"]
    if not branch["evidence_current"]:
        return "QUARANTINE"
    if branch["open_pr"] or branch["active_role"]:
        return "KEEP"
    if classification in {"ACTIVE", "OPEN_PR", "HISTORICAL_EVIDENCE", "UNMERGED_UNIQUE"}:
        return "KEEP"
    if classification == "UNKNOWN":
        return "QUARANTINE"
    if branch["unique_work"]:
        return "KEEP"
    if classification == "CANONICAL_EQUIVALENT":
        if (
            branch["age_days"] >= max(7, branch["retention_days"])
            and branch["canonical_equivalence_proven"]
            and branch["sealed_evidence"]
        ):
            return ELIGIBLE_ACTION
        return "QUARANTINE"
    if classification == "SUPERSEDED":
        if branch["age_days"] >= max(14, branch["retention_days"]) and branch["sealed_evidence"]:
            return ELIGIBLE_ACTION
        return "QUARANTINE"
    if classification == "RECOVERY_EXPIRED":
        if branch["age_days"] >= max(30, branch["retention_days"]) and branch["sealed_evidence"]:
            return ELIGIBLE_ACTION
        return "QUARANTINE"
    return "QUARANTINE"


def validate_record(record, schema):
    errors = []
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "$"
        errors.append(f"schema {path}: {error.message}")
    if errors:
        return errors

    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
        return errors

    prestate = record["prestate"]
    if prestate["risk_level"] in {"HIGH", "CRITICAL"} and prestate["temporary_ref_policy"] != "TEMPORARY_REF_REQUIRED":
        errors.append("HIGH/CRITICAL pre-state requires TEMPORARY_REF_REQUIRED")
    if prestate["temporary_ref_policy"] == "TEMPORARY_REF_REQUIRED" and prestate["retention_days"] < 30:
        errors.append("required temporary pre-state ref must retain at least 30 days")

    canonical = prestate["canonical_branch"]
    refs = set()
    for branch in record["branches"]:
        ref = branch["ref"]
        if ref in refs:
            errors.append(f"duplicate branch record: {ref}")
            continue
        refs.add(ref)

        classification = branch["classification"]
        if ref == canonical and classification != "ACTIVE":
            errors.append("canonical branch must classify ACTIVE")
        if branch["open_pr"] and classification != "OPEN_PR":
            errors.append(f"{ref}: open PR head must classify OPEN_PR")
        if classification == "OPEN_PR" and not branch["open_pr"]:
            errors.append(f"{ref}: OPEN_PR classification requires open_pr=true")
        if classification == "ACTIVE" and not branch["active_role"]:
            errors.append(f"{ref}: ACTIVE classification requires active_role=true")
        if classification == "UNMERGED_UNIQUE" and not branch["unique_work"]:
            errors.append(f"{ref}: UNMERGED_UNIQUE requires unique_work=true")
        if classification == "CANONICAL_EQUIVALENT" and not branch["canonical_equivalence_proven"]:
            errors.append(f"{ref}: CANONICAL_EQUIVALENT requires proven content/tree equivalence")
        if classification == "HISTORICAL_EVIDENCE" and branch["historical_reason"] is None:
            errors.append(f"{ref}: HISTORICAL_EVIDENCE requires a positive preservation reason")
        if classification != "HISTORICAL_EVIDENCE" and branch["historical_reason"] is not None:
            errors.append(f"{ref}: historical_reason is only valid for HISTORICAL_EVIDENCE")
        if not branch["evidence_current"] and classification != "UNKNOWN":
            errors.append(f"{ref}: stale/missing evidence must classify UNKNOWN")

        expected = derive_branch_action(branch)
        if branch["recommended_action"] != expected:
            errors.append(f"{ref}: recommended_action must equal derived action {expected}")

    actions = {branch["recommended_action"] for branch in record["branches"]}
    if not actions <= {"KEEP", "QUARANTINE", ELIGIBLE_ACTION}:
        errors.append("dry-run action vocabulary may not include deletion")
    return errors


def validate_fixture(fixture, schema):
    errors = []
    if fixture.get("schema_version") != "orchestra-recovery-retirement-fixtures-v1":
        return ["fixture schema_version must equal orchestra-recovery-retirement-fixtures-v1"]
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
        if (not record_errors) != expected_valid:
            errors.append(f"{case_id}: expected valid={expected_valid} but errors were {record_errors}")
    return errors


def validate(root):
    root = Path(root)
    schema_path = root / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json"
    fixture_path = root / "tests/behavior/repository-recovery-retirement-fixtures.json"
    policy_path = root / "docs/governance/PRESTATE_RECOVERY_BRANCH_RETIREMENT.md"
    for path in (schema_path, fixture_path, policy_path):
        if not path.is_file():
            return [f"missing Campaign 5 surface: {path.relative_to(root)}"]
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        fixture = load_json(fixture_path)
    except Exception as exc:
        return [f"Campaign 5 parse/schema failure: {exc}"]

    errors = validate_fixture(fixture, schema)
    policy = policy_path.read_text(encoding="utf-8")
    for term in (
        "FORWARD_ONLY",
        "PRESTATE_EVIDENCE != RECOVERY_AUTHORITY",
        "RETIREMENT_ELIGIBLE != BRANCH_DELETION_AUTHORITY",
        "ANCESTRY != SAFE_DELETION_PROOF",
        "ACTIVE",
        "OPEN_PR",
        "CANONICAL_EQUIVALENT",
        "SUPERSEDED",
        "RECOVERY_EXPIRED",
        "HISTORICAL_EVIDENCE",
        "UNMERGED_UNIQUE",
        "UNKNOWN",
        "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION",
        "BRANCH_DELETION_PERFORMED = false",
    ):
        if term not in policy:
            errors.append(f"recovery/retirement policy missing invariant/term: {term}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Repository recovery and retirement plan v1 is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
