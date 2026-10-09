import copy
import importlib.util
import json
import sys
from pathlib import Path


SCHEMA_VERSION = "orchestra-governed-autonomy-candidate-lifecycle-v1"
ALLOWED_TRANSITIONS = {
    ("PROPOSED", "IMPLEMENTING"),
    ("IMPLEMENTING", "FROZEN_CANDIDATE"),
    ("FROZEN_CANDIDATE", "ACCEPTED"),
    ("ACCEPTED", "MERGE_READY"),
    ("MERGE_READY", "MERGE_APPLIED_UNVERIFIED"),
    ("MERGE_APPLIED_UNVERIFIED", "MERGED_VERIFIED"),
    ("MERGED_VERIFIED", "RETIRED"),
}
DISPOSITIONS = {
    "AUTO_CONTINUE",
    "AUTO_REMEDIATE_AND_REVALIDATE",
    "WAIT_FOR_EVIDENCE",
    "ESCALATE_HUMAN",
    "STOP",
}


def load_autonomy_validator(root):
    path = Path(root) / "scripts/validate_governed_autonomy_modes_contract.py"
    spec = importlib.util.spec_from_file_location("governed_autonomy_modes_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def materialize_case(data, case):
    snapshot = copy.deepcopy(data["base_transition_snapshot"])
    snapshot.update(copy.deepcopy(case.get("overrides", {})))
    return snapshot


def evaluate_candidate_transition(snapshot, autonomy_validator):
    profile = autonomy_validator.selected_profile(snapshot)
    if profile not in autonomy_validator.PROFILES:
        return "STOP"

    guard_snapshot = copy.deepcopy(snapshot)
    guard_snapshot["action"] = "validate"
    guard = autonomy_validator.evaluate(guard_snapshot)
    if guard != "AUTO_CONTINUE":
        return guard

    previous_state = str(snapshot.get("candidate_previous_state", ""))
    state = str(snapshot.get("candidate_state", ""))
    if (previous_state, state) not in ALLOWED_TRANSITIONS:
        return "STOP"
    if snapshot.get("candidate_identity_current") is not True:
        return "WAIT_FOR_EVIDENCE"

    if previous_state == "PROPOSED":
        if snapshot.get("admission_basis_current") is not True:
            return "WAIT_FOR_EVIDENCE"
        if snapshot.get("implementation_authority_current") is not True:
            return "ESCALATE_HUMAN"
        return "AUTO_CONTINUE"

    if previous_state == "IMPLEMENTING":
        if snapshot.get("freeze_complete") is not True:
            return "WAIT_FOR_EVIDENCE"
        return "AUTO_CONTINUE"

    if previous_state == "FROZEN_CANDIDATE":
        if snapshot.get("qualification_evidence_current") is not True:
            return "WAIT_FOR_EVIDENCE"
        qualification = str(snapshot.get("qualification_disposition", ""))
        if qualification == "QUALIFICATION_PENDING":
            return "WAIT_FOR_EVIDENCE"
        if qualification == "BLOCKED":
            return "STOP"
        if qualification != "QUALIFIED":
            return "STOP"
        if snapshot.get("acceptance_decision_current") is not True:
            return "ESCALATE_HUMAN"
        if snapshot.get("acceptance_decision_human_owned") is not True:
            return "ESCALATE_HUMAN"
        return "AUTO_CONTINUE"

    if previous_state == "ACCEPTED":
        if snapshot.get("merge_readiness_evidence_current") is not True:
            return "WAIT_FOR_EVIDENCE"
        if profile == "HUMAN_GOVERNED" and snapshot.get("major_phase_progression_authorized") is not True:
            return "ESCALATE_HUMAN"
        return "AUTO_CONTINUE"

    if previous_state == "MERGE_READY":
        if snapshot.get("merge_applied_observed") is True:
            return "AUTO_CONTINUE"
        if profile != "FULL_AUTONOMOUS":
            return "ESCALATE_HUMAN"
        if snapshot.get("exact_candidate_pr_merge_grant") is not True:
            return "ESCALATE_HUMAN"
        merge_snapshot = copy.deepcopy(snapshot)
        merge_snapshot["action"] = "merge"
        return autonomy_validator.evaluate(merge_snapshot)

    if previous_state == "MERGE_APPLIED_UNVERIFIED":
        if snapshot.get("canonical_readback_verified") is not True:
            return "WAIT_FOR_EVIDENCE"
        if snapshot.get("independent_verification_current") is not True:
            return "WAIT_FOR_EVIDENCE"
        return "AUTO_CONTINUE"

    if previous_state == "MERGED_VERIFIED":
        if snapshot.get("closeout_evidence_current") is not True:
            return "WAIT_FOR_EVIDENCE"
        if snapshot.get("retirement_grants_branch_deletion") is not False:
            return "STOP"
        return "AUTO_CONTINUE"
    return "STOP"


def validate_fixture(data, autonomy_validator):
    errors = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    base = data.get("base_transition_snapshot")
    if not isinstance(base, dict):
        errors.append("base_transition_snapshot must be an object")
        return errors
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors
    seen = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id or case_id in seen:
            errors.append("cases must have unique non-empty ids")
            continue
        seen.add(case_id)
        expected = case.get("expected_disposition")
        if expected not in DISPOSITIONS:
            errors.append(f"{case_id}: unknown expected disposition")
            continue
        actual = evaluate_candidate_transition(materialize_case(data, case), autonomy_validator)
        if actual != expected:
            errors.append(f"{case_id}: expected {expected} but evaluator returned {actual}")
    return errors


def validate(root):
    root = Path(root)
    fixture_path = root / "tests/behavior/governed-autonomy-candidate-lifecycle-fixtures.json"
    integration_path = root / "docs/governance/GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION.md"
    maturity_path = root / "docs/governance/CANDIDATE_MATURITY_FEATURE_FREEZE.md"
    autonomy_path = root / "docs/governance/GOVERNED_AUTONOMY_MODES.md"
    protocol_path = root / "docs/governance/GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md"
    qualification_path = root / "docs/governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md"

    errors = []
    for path in (fixture_path, integration_path, maturity_path, autonomy_path, protocol_path, qualification_path):
        if not path.is_file():
            errors.append(f"missing required lifecycle surface: {path.relative_to(root)}")
    if errors:
        return errors

    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        autonomy_validator = load_autonomy_validator(root)
    except Exception as exc:
        return [f"candidate lifecycle parse/import failure: {exc}"]

    errors.extend(f"base autonomy contract: {error}" for error in autonomy_validator.validate(root))
    errors.extend(validate_fixture(data, autonomy_validator))

    integration = integration_path.read_text(encoding="utf-8")
    maturity = maturity_path.read_text(encoding="utf-8")
    autonomy = autonomy_path.read_text(encoding="utf-8")
    protocol = protocol_path.read_text(encoding="utf-8")
    qualification = qualification_path.read_text(encoding="utf-8")

    for term in (
        "AUTONOMY_CHANGES_PAUSES_NOT_PREREQUISITES",
        "CANDIDATE_TRANSITION != PERSISTENCE_AUTHORITY",
        "FULL_AUTONOMOUS != FEATURE_ADOPTION_AUTHORITY",
        "EXACT_CANDIDATE_PR_MERGE_GRANT",
        "MERGE_READY != MERGE_AUTHORITY",
        "RETIRED != BRANCH_DELETION_AUTHORITY",
    ):
        if term not in integration:
            errors.append(f"candidate lifecycle integration missing invariant: {term}")
    for term in ("PROPOSED", "FROZEN_CANDIDATE", "ACCEPTED", "MERGE_READY", "MERGE_APPLIED_UNVERIFIED", "MERGED_VERIFIED", "RETIRED"):
        if term not in maturity:
            errors.append(f"candidate maturity contract missing state: {term}")
    if "Governed Autonomy Candidate Lifecycle Integration" not in autonomy:
        errors.append("Governed Autonomy Modes missing lifecycle integration reference")
    if "Candidate-maturity integration" not in protocol:
        errors.append("Governed Autonomous Execution Protocol missing lifecycle integration section")
    if "QUALIFIED != ACCEPTED" not in qualification:
        errors.append("qualification policy missing acceptance separation")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Governed autonomy candidate lifecycle integration v1 is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
