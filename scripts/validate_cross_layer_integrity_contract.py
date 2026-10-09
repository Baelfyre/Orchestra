import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

STATUSES = {
    "CROSS_LAYER_ALIGNMENT_CONFIRMED",
    "CROSS_LAYER_ALIGNMENT_GAPS_FOUND",
    "CROSS_LAYER_CONTRACT_INCOMPLETE",
    "CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED",
    "CROSS_LAYER_EVIDENCE_INSUFFICIENT",
    "CROSS_LAYER_CONTRACT_STALE",
    "SPECIALIST_REENTRY_REQUIRED",
}
OWNERS = {"clockwork", "chronicler", "cloak", "cipher", "overseer", "the-tuner"}
REENTRY_OWNERS = OWNERS | {"conductor", "arbiter"}
SEVERITIES = {"CRITICAL", "MAJOR", "MINOR", "CLEANUP"}
FINDING_FIELDS = {
    "finding_id", "severity", "owner", "affected_stages", "evidence",
    "impact", "minimal_remediation", "required_validation",
}
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
    },
}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _canonical_bytes(path):
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_identity(identity, protocol_bytes):
    errors = []
    required = {"approved_baseline", "contract_revision", "protocol_sha256", "source_branch"}
    if not isinstance(identity, dict) or set(identity) != required:
        return ["fixtures: contract_identity must contain exactly the required fields"]
    if not re.fullmatch(r"[0-9a-f]{40}", str(identity["approved_baseline"])):
        errors.append("fixtures: approved_baseline must be a lowercase 40-character SHA")
    if not _nonempty(identity["contract_revision"]):
        errors.append("fixtures: contract_revision must be non-empty")
    if not _nonempty(identity["source_branch"]):
        errors.append("fixtures: source_branch must be non-empty")
    expected = hashlib.sha256(protocol_bytes).hexdigest()
    if identity["protocol_sha256"] != expected:
        errors.append("fixtures: protocol_sha256 does not match the F2 integrity profile protocol")
    return errors


def _validate_workflows(profile_name, profile, stages):
    errors = []
    workflow_map = {}
    workflows = profile.get("executable_workflows")
    if not isinstance(workflows, list) or not workflows:
        return [f"{profile_name}: executable_workflows must be non-empty"], workflow_map
    kinds = set()
    for workflow in workflows:
        if not isinstance(workflow, dict):
            errors.append(f"{profile_name}: workflow must be an object")
            continue
        workflow_id = workflow.get("id")
        if not _nonempty(workflow_id) or workflow_id in workflow_map:
            errors.append(f"{profile_name}: missing or duplicate workflow id")
            continue
        workflow_map[workflow_id] = workflow
        kind = workflow.get("kind")
        if kind not in {"HAPPY_PATH", "FAILURE_PATH"}:
            errors.append(f"{profile_name}/{workflow_id}: invalid workflow kind")
        else:
            kinds.add(kind)
        if not _nonempty(workflow.get("expected_final_state")):
            errors.append(f"{profile_name}/{workflow_id}: expected_final_state must be non-empty")
        trace = workflow.get("trace")
        if not isinstance(trace, list):
            errors.append(f"{profile_name}/{workflow_id}: trace must be a list")
            continue
        seen = [entry.get("stage") if isinstance(entry, dict) else None for entry in trace]
        if tuple(seen) != stages:
            errors.append(f"{profile_name}/{workflow_id}: trace must contain profile stages in exact order")
            continue
        for entry in trace:
            if set(entry) != {"stage", "owner", "source_ref", "evidence_ref", "result"}:
                errors.append(f"{profile_name}/{workflow_id}: trace entry fields are incomplete or unknown")
                continue
            if entry["owner"] not in OWNERS:
                errors.append(f"{profile_name}/{workflow_id}/{entry['stage']}: invalid owner")
            for field in ("source_ref", "evidence_ref", "result"):
                if not _nonempty(entry[field]):
                    errors.append(f"{profile_name}/{workflow_id}/{entry['stage']}: {field} must be non-empty")
    if kinds != {"HAPPY_PATH", "FAILURE_PATH"}:
        errors.append(f"{profile_name}: both happy-path and failure-path workflows are required")
    return errors, workflow_map


def _validate_finding(profile_name, case_id, finding, owner, stages):
    if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
        return [f"{profile_name}/{case_id}: non-confirmed result requires a complete finding object"]
    errors = []
    if owner not in OWNERS or finding.get("owner") != owner:
        errors.append(f"{profile_name}/{case_id}: finding must have one valid singular owner")
    if finding.get("severity") not in SEVERITIES:
        errors.append(f"{profile_name}/{case_id}: invalid severity")
    if not _nonempty(finding.get("finding_id")):
        errors.append(f"{profile_name}/{case_id}: finding_id must be non-empty")
    affected = finding.get("affected_stages")
    if (
        not isinstance(affected, list) or not affected
        or len(affected) != len(set(affected))
        or any(stage not in stages for stage in affected)
    ):
        errors.append(f"{profile_name}/{case_id}: affected_stages must be a unique non-empty profile-stage list")
    refs = finding.get("evidence")
    if not isinstance(refs, list) or not refs or any(not _nonempty(ref) for ref in refs):
        errors.append(f"{profile_name}/{case_id}: finding evidence must be non-empty")
    for field in ("impact", "minimal_remediation", "required_validation"):
        if not _nonempty(finding.get(field)):
            errors.append(f"{profile_name}/{case_id}: {field} must be non-empty")
    return errors


def _validate_profile(name, profile, spec):
    errors = []
    stages = spec["stages"]
    evidence_fields = spec["evidence"]
    if tuple(profile.get("stages", ())) != stages:
        errors.append(f"{name}: stages must match canonical order")
    if set(profile.get("required_evidence", ())) != evidence_fields:
        errors.append(f"{name}: required_evidence is incomplete or unknown")

    workflow_errors, workflow_map = _validate_workflows(name, profile, stages)
    errors.extend(workflow_errors)

    cases = profile.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + [f"{name}: cases must be non-empty"]
    seen_ids = set()
    covered_statuses = set()
    referenced_workflows = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append(f"{name}: case must be an object")
            continue
        case_id = case.get("id")
        if not _nonempty(case_id) or case_id in seen_ids:
            errors.append(f"{name}: missing or duplicate case id")
            continue
        seen_ids.add(case_id)
        status = case.get("expected_status")
        if status not in STATUSES:
            errors.append(f"{name}/{case_id}: unknown status")
        else:
            covered_statuses.add(status)

        evidence = case.get("evidence")
        if (
            not isinstance(evidence, dict)
            or set(evidence) != evidence_fields
            or not all(isinstance(value, bool) for value in evidence.values())
        ):
            errors.append(f"{name}/{case_id}: evidence must contain exactly the profile boolean fields")
            continue

        reentry = case.get("expected_reentry")
        if (
            not isinstance(reentry, list)
            or len(reentry) != len(set(reentry))
            or any(owner not in REENTRY_OWNERS for owner in reentry)
        ):
            errors.append(f"{name}/{case_id}: expected_reentry must be a unique valid specialist list")
            reentry = []

        workflow_id = case.get("workflow_id")
        if workflow_id is not None:
            if workflow_id not in workflow_map:
                errors.append(f"{name}/{case_id}: workflow_id does not reference an executable workflow")
            else:
                referenced_workflows.add(workflow_id)
        if evidence["executable_workflow"] and not workflow_id:
            errors.append(f"{name}/{case_id}: executable evidence requires workflow_id")
        if not evidence["executable_workflow"] and workflow_id is not None:
            errors.append(f"{name}/{case_id}: missing executable evidence cannot reference a workflow")

        owner = case.get("finding_owner")
        finding = case.get("finding")
        if status == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            if owner is not None or finding is not None or reentry or not all(evidence.values()):
                errors.append(f"{name}/{case_id}: confirmed alignment requires complete evidence and no finding or re-entry")
        else:
            errors.extend(_validate_finding(name, case_id, finding, owner, stages))

        if status == "CROSS_LAYER_EVIDENCE_INSUFFICIENT" and all(evidence.values()):
            errors.append(f"{name}/{case_id}: insufficient evidence must identify a missing evidence field")
        if status == "CROSS_LAYER_CONTRACT_STALE" and reentry != ["the-tuner", "overseer", "arbiter"]:
            errors.append(f"{name}/{case_id}: stale identity must re-enter Tuner, Overseer, and Arbiter")
        if status == "CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED" and "conductor" not in reentry:
            errors.append(f"{name}/{case_id}: contradiction must route back through Conductor")
        if status == "SPECIALIST_REENTRY_REQUIRED" and not reentry:
            errors.append(f"{name}/{case_id}: re-entry status requires an explicit specialist set")

    if covered_statuses != STATUSES:
        errors.append(f"{name}: every deterministic status must have a fixture case")
    if set(workflow_map) != referenced_workflows:
        errors.append(f"{name}: every executable workflow must be referenced by at least one case")
    return errors


def validate_fixtures(data, protocol_bytes):
    errors = []
    if data.get("schema_version") != "orchestra-cross-layer-integrity-v1":
        errors.append("fixtures: invalid schema_version")
    if set(data.get("statuses", ())) != STATUSES:
        errors.append("fixtures: deterministic status set is incomplete or unknown")
    errors.extend(_validate_identity(data.get("contract_identity"), protocol_bytes))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_SPECS):
        return errors + ["fixtures: profiles must contain exactly backend_persistence and cross_module_logic"]
    for name, spec in PROFILE_SPECS.items():
        errors.extend(_validate_profile(name, profiles[name], spec))
    return errors


def validate(repo_root):
    parent = repo_root / "docs/validation/CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md"
    protocol = repo_root / "docs/validation/CROSS_LAYER_INTEGRITY_PROFILE_PROTOCOL.md"
    backend = repo_root / "docs/validation/checklists/BACKEND_PERSISTENCE_INTEGRITY_CHECKLIST.md"
    cross_module = repo_root / "docs/validation/checklists/CROSS_MODULE_LOGIC_INTEGRITY_CHECKLIST.md"
    fixtures = repo_root / "tests/behavior/cross-layer-integrity-fixtures.json"
    required = (parent, protocol, backend, cross_module, fixtures)
    missing = [path.relative_to(repo_root).as_posix() for path in required if not path.is_file()]
    if missing:
        return [f"missing required F2 artifact: {path}" for path in missing]

    errors = []
    parent_text = parent.read_text(encoding="utf-8")
    protocol_bytes = _canonical_bytes(protocol)
    protocol_text = protocol_bytes.decode("utf-8")
    backend_text = backend.read_text(encoding="utf-8")
    module_text = cross_module.read_text(encoding="utf-8")

    for status in STATUSES:
        if status not in parent_text or status not in protocol_text:
            errors.append(f"protocol inheritance: missing deterministic status {status}")
    for spec in PROFILE_SPECS.values():
        for stage in spec["stages"]:
            if stage not in protocol_text:
                errors.append(f"profile protocol: missing stage {stage}")
    for token in (
        "Cross-Module Logic Audit Protocol",
        "Passing unit tests alone is insufficient",
        "exactly one specialist",
    ):
        if token not in protocol_text:
            errors.append(f"profile protocol: missing {token!r}")
    for token in ("`COMMIT_OR_ROLLBACK`", "Clockwork owns service/repository architecture findings", "Chronicler owns schema"):
        if token not in backend_text:
            errors.append(f"backend checklist: missing {token!r}")
    for token in ("`HANDOFF_PAYLOAD`", "Dependency direction", "Clockwork owns cross-module"):
        if token not in module_text:
            errors.append(f"cross-module checklist: missing {token!r}")

    errors.extend(validate_fixtures(_load_json(fixtures), protocol_bytes))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate F2 backend-persistence and cross-module integrity profiles.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Cross-layer backend-persistence and cross-module integrity profiles are deterministic and complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
