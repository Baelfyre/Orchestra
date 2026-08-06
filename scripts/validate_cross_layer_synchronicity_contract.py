import argparse
import json
import sys
from pathlib import Path

REQUIRED_STAGES = (
    "UI_CONTROL", "CLIENT_EVENT", "CLIENT_STATE_OR_FORM_MODEL",
    "SERIALIZED_REQUEST", "API_ROUTE", "BACKEND_HANDLER",
    "SERVICE_OPERATION", "REPOSITORY_AND_PERSISTENCE", "API_RESPONSE",
    "CLIENT_CACHE_OR_STATE_UPDATE", "FINAL_RENDERED_STATE",
)
REQUIRED_STATUSES = {
    "CROSS_LAYER_ALIGNMENT_CONFIRMED", "CROSS_LAYER_ALIGNMENT_GAPS_FOUND",
    "CROSS_LAYER_CONTRACT_INCOMPLETE", "CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED",
    "CROSS_LAYER_EVIDENCE_INSUFFICIENT", "CROSS_LAYER_CONTRACT_STALE",
    "SPECIALIST_REENTRY_REQUIRED",
}
REQUIRED_EVIDENCE = {
    "field_mapping", "validation_parity", "authorization_parity",
    "state_coverage", "accessibility", "executable_workflow",
}
REQUIRED_CASES = {
    "happy-path-aligned", "request-field-mismatch", "missing-executable-evidence",
    "authorization-mismatch", "stale-contract-identity",
    "inaccessible-backend-state", "persistence-scope-expansion",
}
OWNERS = {"clockwork", "chronicler", "cloak", "cipher", "overseer", "the-tuner"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixtures(data):
    errors = []
    if data.get("schema_version") != "orchestra-synchronicity-v1":
        errors.append("fixtures: invalid schema_version")
    if tuple(data.get("workflow_stages", ())) != REQUIRED_STAGES:
        errors.append("fixtures: workflow stages must match the canonical order")
    if set(data.get("statuses", ())) != REQUIRED_STATUSES:
        errors.append("fixtures: deterministic status set is incomplete or unknown")
    if set(data.get("required_evidence", ())) != REQUIRED_EVIDENCE:
        errors.append("fixtures: required evidence set is incomplete or unknown")

    seen = set()
    for case in data.get("cases", []):
        case_id = case.get("id")
        if not case_id or case_id in seen:
            errors.append(f"fixtures: missing or duplicate case id {case_id!r}")
            continue
        seen.add(case_id)
        status = case.get("expected_status")
        owner = case.get("finding_owner")
        evidence = case.get("evidence")
        reentry = case.get("expected_reentry")
        if status not in REQUIRED_STATUSES:
            errors.append(f"{case_id}: unknown status")
        if not isinstance(evidence, dict) or set(evidence) != REQUIRED_EVIDENCE or not all(isinstance(value, bool) for value in evidence.values()):
            errors.append(f"{case_id}: evidence must contain exactly the required boolean fields")
            continue
        if not isinstance(reentry, list) or len(reentry) != len(set(reentry)):
            errors.append(f"{case_id}: expected_reentry must be a unique list")
        if status == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            if owner is not None or not all(evidence.values()) or reentry:
                errors.append(f"{case_id}: confirmed alignment requires complete evidence and no finding or re-entry")
        elif owner not in OWNERS:
            errors.append(f"{case_id}: non-confirmed result requires one valid finding owner")
        if status == "CROSS_LAYER_EVIDENCE_INSUFFICIENT" and all(evidence.values()):
            errors.append(f"{case_id}: insufficient evidence must identify a missing evidence field")
        if status == "CROSS_LAYER_CONTRACT_STALE" and reentry != ["the-tuner", "overseer", "arbiter"]:
            errors.append(f"{case_id}: stale identity must re-enter Tuner, Overseer, and Arbiter")
        if case_id == "authorization-mismatch" and owner != "cipher":
            errors.append("authorization-mismatch: Cipher must own the finding")
        if status == "SPECIALIST_REENTRY_REQUIRED" and not reentry:
            errors.append(f"{case_id}: re-entry status requires an explicit specialist set")

    missing = REQUIRED_CASES - seen
    if missing:
        errors.append(f"fixtures: missing required cases {sorted(missing)}")
    return errors


def validate(repo_root):
    errors = []
    paths = {
        "protocol": repo_root / "docs/validation/CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md",
        "checklist": repo_root / "docs/validation/checklists/FRONTEND_BACKEND_SYNCHRONICITY_CHECKLIST.md",
        "fixtures": repo_root / "tests/behavior/cross-layer-synchronicity-fixtures.json",
    }
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"missing required {label}: {path.relative_to(repo_root).as_posix()}")
    if errors:
        return errors

    protocol = paths["protocol"].read_text(encoding="utf-8")
    checklist = paths["checklist"].read_text(encoding="utf-8")
    for token in (*REQUIRED_STAGES, *REQUIRED_STATUSES, "exactly one specialist", "Passing unit tests alone is insufficient"):
        if token not in protocol:
            errors.append(f"protocol: missing {token!r}")
    for token in ("Authorized, unauthorized, and edge-case personas", "Human Git and merge gates remain explicit"):
        if token not in checklist:
            errors.append(f"checklist: missing {token!r}")

    required_references = {
        "ROUTING_MAP.md": "Frontend/backend synchronicity",
        "skills/conductor/SKILL.md": "Synchronicity routing",
        "skills/the-tuner/SKILL.md": "CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md",
        "docs/setup/VALIDATION.md": "validate_cross_layer_synchronicity_contract.py",
    }
    for relative, token in required_references.items():
        content = (repo_root / relative).read_text(encoding="utf-8")
        if token not in content:
            errors.append(f"{relative}: missing {token!r}")
    errors.extend(validate_fixtures(load_json(paths["fixtures"])))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the cross-layer synchronicity contract.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Cross-layer frontend-to-backend synchronicity contract is deterministic and complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
