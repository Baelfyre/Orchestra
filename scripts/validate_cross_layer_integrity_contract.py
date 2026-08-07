import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED_STATUSES = {
    "CROSS_LAYER_ALIGNMENT_CONFIRMED",
    "CROSS_LAYER_ALIGNMENT_GAPS_FOUND",
    "CROSS_LAYER_CONTRACT_INCOMPLETE",
    "CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED",
    "CROSS_LAYER_EVIDENCE_INSUFFICIENT",
    "CROSS_LAYER_CONTRACT_STALE",
    "SPECIALIST_REENTRY_REQUIRED",
}
OWNERS = {"clockwork", "chronicler", "cloak", "cipher", "overseer", "the-tuner"}
VALID_REENTRY = OWNERS | {"conductor", "arbiter"}
SEVERITIES = {"CRITICAL", "MAJOR", "MINOR", "CLEANUP"}
FINDING_FIELDS = {
    "finding_id", "severity", "owner", "affected_stages", "evidence",
    "impact", "minimal_remediation", "required_validation",
}
WORKFLOW_KINDS = {"HAPPY_PATH", "FAILURE_PATH"}
PROFILE_SPECS = {
    "backend_persistence": {
        "stages": (
            "SERVICE_INPUT", "DOMAIN_VALIDATION", "TRANSACTION_BOUNDARY",
            "REPOSITORY_OPERATION", "MAPPING_OR_QUERY", "SCHEMA_CONSTRAINT",
            "PERSISTENCE_EXECUTION", "COMMIT_OR_ROLLBACK",
            "READBACK_OR_PROJECTION", "SERVICE_RESULT",
        ),
        "evidence": {
            "contract_mapping", "validation_and_constraint_parity",
            "transaction_semantics", "query_mapping", "error_mapping",
            "concurrency_and_idempotency", "executable_workflow",
        },
        "required_cases": {
            "backend-persistence-happy-path", "backend-contract-mapping-gap",
            "backend-owner-contract-missing", "backend-persistence-contradiction",
            "backend-evidence-missing", "backend-contract-stale",
            "backend-transaction-reentry",
        },
    },
    "cross_module_logic": {
        "stages": (
            "ENTRYPOINT", "INPUT_CONTRACT", "MODULE_A_DECISION",
            "HANDOFF_PAYLOAD", "MODULE_B_DECISION",
            "SHARED_STATE_OR_SIDE_EFFECT", "RESULT_PROPAGATION",
            "ERROR_PROPAGATION", "FINAL_OBSERVABLE_OUTCOME",
        ),
        "evidence": {
            "input_contract", "handoff_contract", "control_flow",
            "state_and_side_effects", "error_propagation",
            "dependency_direction", "executable_workflow",
        },
        "required_cases": {
            "cross-module-happy-path", "cross-module-flow-gap",
            "cross-module-owner-contract-missing", "cross-module-contradiction",
            "cross-module-evidence-missing", "cross-module-contract-stale",
            "cross-module-side-effect-reentry",
        },
    },
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _canonical_text_bytes(path):
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _validate_contract_identity(identity, protocol_bytes):
    errors = []
    if not isinstance(identity, dict):
        return ["fixtures: contract_identity must be an object"]
    required = {"approved_baseline", "contract_revision", "protocol_sha256", "source_branch"}
    if set(identity) != required:
        return ["fixtures: contract_identity must contain exactly the required fields"]
    if not re.fullmatch(r"[0-9a-f]{40}", str(identity["approved_baseline"])):
        errors.append("fixtures: approved_baseline must be a 40-character lowercase commit SHA")
    if not _nonempty(identity["contract_revision"]):
        errors.append("fixtures: contract_revision must be non-empty")
    if not _nonempty(identity["source_branch"]):
        errors.append("fixtures: source_branch must be non-empty")
    expected_hash = hashlib.sha256(protocol_bytes).hexdigest()
    if identity["protocol_sha256"] != expected_hash:
        errors.append("fixtures: protocol_sha256 does not match the canonical cross-module audit protocol")
    return errors


def _validate_finding(profile_name, case_id, finding, finding_owner, stages):
    if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
        return [f"{profile_name}/{case_id}: non-confirmed result requires a complete finding object"]
    errors = []
    if finding.get("owner") != finding_owner or finding_owner not in OWNERS:
        errors.append(f"{profile_name}/{case_id}: finding owner must be one valid singular owner")
    if not _nonempty(finding.get("finding_id")):
        errors.append(f"{profile_name}/{case_id}: finding_id must be non-empty")
    if finding.get("severity") not in SEVERITIES:
        errors.append(f"{profile_name}/{case_id}: finding severity is invalid")
    affected = finding.get("affected_stages")
    if (
        not isinstance(affected, list)
        or not affected
        or len(affected) != len(set(affected))
        or any(stage not in stages for stage in affected)
    ):
        errors.append(f"{profile_name}/{case_id}: affected_stages must be a unique non-empty profile stage list")
    refs = finding.get("evidence")
    if not isinstance(refs, list) or not refs or any(not _nonempty(ref) for ref in refs):
        errors.append(f"{profile_name}/{case_id}: finding evidence must contain non-empty references")
    for field in ("impact", "minimal_remediation", "required_validation"):
        if not _nonempty(finding.get(field)):
            errors.append(f"{profile_name}/{case_id}: finding {field} must be non-empty")
    return errors


def _validate_workflows(profile_name, profile, stages):
    errors = []
    workflows = profile.get("executable_workflows")
    workflow_map = {}
    if not isinstance(workflows, list) or not workflows:
        return [f"{profile_name}: executable_workflows must be a non-empty list"], workflow_map
    for workflow in workflows:
        if not isinstance(workflow, dict):
            errors.append(f"{profile_name}: every executable workflow must be an object")
            continue
        workflow_id = workflow.get("id")
        if not _nonempty(workflow_id) or workflow_id in workflow_map:
            errors.append(f"{profile_name}: missing or duplicate workflow id {workflow_id!r}")
            continue
        workflow_map[workflow_id] = workflow
        if workflow.get("kind") not in WORKFLOW_KINDS:
            errors.append(f"{profile_name}/{workflow_id}: unknown workflow kind")
        if not _nonempty(workflow.get("case_id")):
            errors.append(f"{profile_name}/{workflow_id}: case_id must be non-empty")
        if not _nonempty(workflow.get("expected_final_state")):
            errors.append(f"{profile_name}/{workflow_id}: expected_final_state must be non-empty")
        trace = workflow.get("trace")
        if not isinstance(trace, list):
            errors.append(f"{profile_name}/{workflow_id}: trace must be a list")
            continue
        seen_stages = [entry.get("stage") if isinstance(entry, dict) else None for entry in trace]
        if tuple(seen_stages) != stages:
            errors.append(f"{profile_name}/{workflow_id}: trace must contain profile stages in exact order")
            continue
        for entry in trace:
            stage = entry["stage"]
            if set(entry) != {"stage", "owner", "source_ref", "evidence_ref", "result"}:
                errors.append(f"{profile_name}/{workflow_id}/{stage}: trace entry fields are incomplete or unknown")
                continue
            if entry["owner"] not in OWNERS:
                errors.append(f"{profile_name}/{workflow_id}/{stage}: invalid stage owner")
            for field in ("source_ref", "evidence_ref", "result"):
                if not _nonempty(entry[field]):
                    errors.append(f"{profile_name}/{workflow_id}/{stage}: {field} must be non-empty")
    return errors, workflow_map


def _validate_profile(profile_name, profile, spec):
    errors = []
    stages = spec["stages"]
    evidence_fields = spec["evidence"]
    if tuple(profile.get("stages", ())) != stages:
        errors.append(f"{profile_name}: stages must match the canonical profile order")
    if set(profile.get("required_evidence", ())) != evidence_fields:
        errors.append(f"{profile_name}: required_evidence is incomplete or unknown")

    workflow_errors, workflow_map = _validate_workflows(profile_name, profile, stages)
    errors.extend(workflow_errors)

    seen_cases = set()
    covered_statuses = set()
    referenced_workflows = set()
    cases = profile.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + [f"{profile_name}: cases must be a non-empty list"]

    for case in cases:
        if not isinstance(case, dict):
            errors.append(f"{profile_name}: every case must be an object")
            continue
        case_id = case.get("id")
        if not _nonempty(case_id) or case_id in seen_cases:
            errors.append(f"{profile_name}: missing or duplicate case id {case_id!r}")
            continue
        seen_cases.add(case_id)

        status = case.get("expected_status")
        owner = case.get("finding_owner")
        finding = case.get("finding")
        evidence = case.get("evidence")
        reentry = case.get("expected_reentry")
        workflow_id = case.get("workflow_id")

        if status not in REQUIRED_STATUSES:
            errors.append(f"{profile_name}/{case_id}: unknown status")
        else:
            covered_statuses.add(status)

        if (
            not isinstance(evidence, dict)
            or set(evidence) != evidence_fields
            or not all(isinstance(value, bool) for value in evidence.values())
        ):
            errors.append(f"{profile_name}/{case_id}: evidence must contain exactly the profile boolean fields")
            continue

        if (
            not isinstance(reentry, list)
            or len(reentry) != len(set(reentry))
            or any(item not in VALID_REENTRY for item in reentry)
        ):
            errors.append(f"{profile_name}/{case_id}: expected_reentry must be a unique valid specialist list")

        if workflow_id is not None:
            if workflow_id not in workflow_map:
                errors.append(f"{profile_name}/{case_id}: workflow_id does not reference an executable workflow")
            else:
                referenced_workflows.add(workflow_id)

        if evidence["executable_workflow"] and not workflow_id:
            errors.append(f"{profile_name}/{case_id}: executable evidence requires workflow_id")
        if not evidence["executable_workflow"] and workflow_id is not None:
            errors.append(f"{profile_name}/{case_id}: missing executable evidence cannot reference a workflow")

        if status == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            if owner is not None or finding is not None or not all(evidence.values()) or reentry:
                errors.append(f"{profile_name}/{case_id}: confirmed alignment requires complete evidence and no finding or re-entry")
        else:
            errors.extend(_validate_finding(profile_name, case_id, finding, owner, stages))

        if status == "CROSS_LAYER_EVIDENCE_INSUFFICIENT" and all(evidence.values()):
            errors.append(f"{profile_name}/{case_id}: insufficient evidence must identify a missing evidence field")
        if status == "CROSS_LAYER_CONTRACT_STALE" and reentry != ["the-tuner", "overseer", "arbiter"]:
            errors.append(f"{profile_name}/{case_id}: stale identity must re-enter Tuner, Overseer, and Arbiter")
        if status == "CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED" and "conductor" not in reentry:
            errors.append(f"{profile_name}/{case_id}: contradiction must route back through Conductor")
        if status == "SPECIALIST_REENTRY_REQUIRED" and not reentry:
            errors.append(f"{profile_name}/{case_id}: re-entry status requires an explicit specialist set")

    missing_cases = spec["required_cases"] - seen_cases
    if missing_cases:
        errors.append(f"{profile_name}: missing required cases {sorted(missing_cases)}")
    missing_statuses = REQUIRED_STATUSES - covered_statuses
    if missing_statuses:
        errors.append(f"{profile_name}: statuses lack cases {sorted(missing_statuses)}")

    present_kinds = {workflow.get("kind") for workflow in workflow_map.values()}
    if not WORKFLOW_KINDS <= present_kinds:
        errors.append(f"{profile_name}: both happy-path and failure-path workflows are required")
    unreferenced = set(workflow_map) - referenced_workflows
    if unreferenced:
        errors.append(f"{profile_name}: unreferenced executable workflows {sorted(unreferenced)}")
    return errors


def validate_fixtures(data, protocol_bytes=None):
    errors = []
    if data.get("schema_version") != "orchestra-cross-layer-integrity-v1":
        errors.append("fixtures: invalid schema_version")
    if set(data.get("statuses", ())) != REQUIRED_STATUSES:
        errors.append("fixtures: deterministic status set is incomplete or unknown")
    if protocol_bytes is not None:
        errors.extend(_validate_contract_identity(data.get("contract_identity"), protocol_bytes))

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_SPECS):
        errors.append("fixtures: profiles must contain exactly backend_persistence and cross_module_logic")
        return errors

    for name, spec in PROFILE_SPECS.items():
        errors.extend(_validate_profile(name, profiles[name], spec))
    return errors


def validate(repo_root):
    errors = []
    paths = {
        "protocol": repo_root / "docs/validation/CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md",
        "backend_checklist": repo_root / "docs/validation/checklists/BACKEND_PERSISTENCE_INTEGRITY_CHECKLIST.md",
        "module_checklist": repo_root / "docs/validation/checklists/CROSS_MODULE_LOGIC_INTEGRITY_CHECKLIST.md",
        "fixtures": repo_root / "tests/behavior/cross-layer-integrity-fixtures.json",
    }
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"missing required {label}: {path.relative_to(repo_root).as_posix()}")
    if errors:
        return errors

    protocol_bytes = _canonical_text_bytes(paths["protocol"])
    protocol = protocol_bytes.decode("utf-8")
    backend_checklist = paths["backend_checklist"].read_text(encoding="utf-8")
    module_checklist = paths["module_checklist"].read_text(encoding="utf-8")

    required_protocol_tokens = [
        "Backend-to-persistence workflow",
        "Cross-module logical-flow workflow",
        "Passing unit tests alone is insufficient",
        "exactly one specialist",
        *REQUIRED_STATUSES,
        *PROFILE_SPECS["backend_persistence"]["stages"],
        *PROFILE_SPECS["cross_module_logic"]["stages"],
    ]
    for token in required_protocol_tokens:
        if token not in protocol:
            errors.append(f"protocol: missing {token!r}")

    for token in ("`COMMIT_OR_ROLLBACK`", "Clockwork owns service", "Chronicler owns schema"):
        if token not in backend_checklist:
            errors.append(f"backend checklist: missing {token!r}")
    for token in ("`HANDOFF_PAYLOAD`", "dependency direction", "Clockwork owns cross-module"):
        if token not in module_checklist:
            errors.append(f"cross-module checklist: missing {token!r}")

    errors.extend(validate_fixtures(load_json(paths["fixtures"]), protocol_bytes))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate backend-persistence and cross-module integrity audit contracts.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Cross-layer backend-persistence and cross-module integrity contracts are deterministic and complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
