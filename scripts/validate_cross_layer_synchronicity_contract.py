import argparse
import hashlib
import json
import re
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
    "missing-owner-contract", "contradictory-api-requirement",
}
OWNERS = {"clockwork", "chronicler", "cloak", "cipher", "overseer", "the-tuner"}
VALID_REENTRY = OWNERS | {"conductor", "arbiter"}
SEVERITIES = {"CRITICAL", "MAJOR", "MINOR", "CLEANUP"}
FINDING_FIELDS = {
    "finding_id", "severity", "owner", "affected_stages", "evidence",
    "impact", "minimal_remediation", "required_validation",
}
WORKFLOW_KINDS = {"HAPPY_PATH", "FAILURE_PATH"}


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
        errors.append("fixtures: contract_identity must contain exactly the required fields")
        return errors
    if not re.fullmatch(r"[0-9a-f]{40}", str(identity["approved_baseline"])):
        errors.append("fixtures: approved_baseline must be a 40-character lowercase commit SHA")
    if not _nonempty(identity["contract_revision"]):
        errors.append("fixtures: contract_revision must be non-empty")
    if not _nonempty(identity["source_branch"]):
        errors.append("fixtures: source_branch must be non-empty")
    expected_hash = hashlib.sha256(protocol_bytes).hexdigest()
    if identity["protocol_sha256"] != expected_hash:
        errors.append(
            "fixtures: protocol_sha256 does not match docs/validation/"
            "CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md"
        )
    return errors


def _validate_workflows(workflows):
    errors = []
    workflow_map = {}
    if not isinstance(workflows, list) or not workflows:
        return ["fixtures: executable_workflows must be a non-empty list"], workflow_map

    for workflow in workflows:
        if not isinstance(workflow, dict):
            errors.append("fixtures: every executable workflow must be an object")
            continue
        workflow_id = workflow.get("id")
        if not _nonempty(workflow_id) or workflow_id in workflow_map:
            errors.append(f"fixtures: missing or duplicate workflow id {workflow_id!r}")
            continue
        workflow_map[workflow_id] = workflow

        if workflow.get("kind") not in WORKFLOW_KINDS:
            errors.append(f"{workflow_id}: unknown workflow kind")
        if not _nonempty(workflow.get("case_id")):
            errors.append(f"{workflow_id}: case_id must be non-empty")
        if not _nonempty(workflow.get("expected_final_state")):
            errors.append(f"{workflow_id}: expected_final_state must be non-empty")

        trace = workflow.get("trace")
        if not isinstance(trace, list):
            errors.append(f"{workflow_id}: trace must be a list")
            continue
        stages = [entry.get("stage") if isinstance(entry, dict) else None for entry in trace]
        if tuple(stages) != REQUIRED_STAGES:
            errors.append(f"{workflow_id}: trace must contain the canonical stages in exact order")
            continue
        for index, entry in enumerate(trace):
            stage = REQUIRED_STAGES[index]
            if set(entry) != {"stage", "owner", "source_ref", "evidence_ref", "result"}:
                errors.append(f"{workflow_id}/{stage}: trace entry fields are incomplete or unknown")
                continue
            if entry["owner"] not in OWNERS:
                errors.append(f"{workflow_id}/{stage}: invalid stage owner")
            for field in ("source_ref", "evidence_ref", "result"):
                if not _nonempty(entry[field]):
                    errors.append(f"{workflow_id}/{stage}: {field} must be non-empty")
    return errors, workflow_map


def _validate_finding(case_id, finding, finding_owner):
    errors = []
    if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
        return [f"{case_id}: non-confirmed result requires a complete finding object"]
    if finding.get("owner") != finding_owner or finding_owner not in OWNERS:
        errors.append(f"{case_id}: finding owner must be one valid singular owner")
    if not _nonempty(finding.get("finding_id")):
        errors.append(f"{case_id}: finding_id must be non-empty")
    if finding.get("severity") not in SEVERITIES:
        errors.append(f"{case_id}: finding severity is invalid")

    affected_stages = finding.get("affected_stages")
    if (
        not isinstance(affected_stages, list)
        or not affected_stages
        or len(affected_stages) != len(set(affected_stages))
        or any(stage not in REQUIRED_STAGES for stage in affected_stages)
    ):
        errors.append(f"{case_id}: affected_stages must be a unique non-empty canonical stage list")

    evidence_refs = finding.get("evidence")
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(not _nonempty(reference) for reference in evidence_refs)
    ):
        errors.append(f"{case_id}: finding evidence must contain non-empty references")

    for field in ("impact", "minimal_remediation", "required_validation"):
        if not _nonempty(finding.get(field)):
            errors.append(f"{case_id}: finding {field} must be non-empty")
    return errors


def validate_fixtures(data, protocol_bytes=None):
    errors = []
    if data.get("schema_version") != "orchestra-synchronicity-v1":
        errors.append("fixtures: invalid schema_version")
    if tuple(data.get("workflow_stages", ())) != REQUIRED_STAGES:
        errors.append("fixtures: workflow stages must match the canonical order")
    if set(data.get("statuses", ())) != REQUIRED_STATUSES:
        errors.append("fixtures: deterministic status set is incomplete or unknown")
    if set(data.get("required_evidence", ())) != REQUIRED_EVIDENCE:
        errors.append("fixtures: required evidence set is incomplete or unknown")
    if protocol_bytes is not None:
        errors.extend(_validate_contract_identity(data.get("contract_identity"), protocol_bytes))

    workflow_errors, workflow_map = _validate_workflows(data.get("executable_workflows"))
    errors.extend(workflow_errors)

    seen = set()
    covered_statuses = set()
    referenced_workflows = set()
    for case in data.get("cases", []):
        if not isinstance(case, dict):
            errors.append("fixtures: every case must be an object")
            continue
        case_id = case.get("id")
        if not case_id or case_id in seen:
            errors.append(f"fixtures: missing or duplicate case id {case_id!r}")
            continue
        seen.add(case_id)

        status = case.get("expected_status")
        owner = case.get("finding_owner")
        evidence = case.get("evidence")
        reentry = case.get("expected_reentry")
        workflow_id = case.get("workflow_id")
        finding = case.get("finding")

        if status not in REQUIRED_STATUSES:
            errors.append(f"{case_id}: unknown status")
        else:
            covered_statuses.add(status)

        if (
            not isinstance(evidence, dict)
            or set(evidence) != REQUIRED_EVIDENCE
            or not all(isinstance(value, bool) for value in evidence.values())
        ):
            errors.append(f"{case_id}: evidence must contain exactly the required boolean fields")
            continue

        if (
            not isinstance(reentry, list)
            or len(reentry) != len(set(reentry))
            or any(item not in VALID_REENTRY for item in reentry)
        ):
            errors.append(f"{case_id}: expected_reentry must be a unique valid specialist list")

        if workflow_id is not None:
            if workflow_id not in workflow_map:
                errors.append(f"{case_id}: workflow_id does not reference an executable workflow")
            else:
                referenced_workflows.add(workflow_id)

        if evidence["executable_workflow"] and not workflow_id:
            errors.append(f"{case_id}: executable evidence requires workflow_id")
        if not evidence["executable_workflow"] and workflow_id is not None:
            errors.append(f"{case_id}: missing executable evidence cannot reference a workflow")

        if status == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            if owner is not None or finding is not None or not all(evidence.values()) or reentry:
                errors.append(
                    f"{case_id}: confirmed alignment requires complete evidence and no finding or re-entry"
                )
        else:
            errors.extend(_validate_finding(case_id, finding, owner))

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
    missing_statuses = REQUIRED_STATUSES - covered_statuses
    if missing_statuses:
        errors.append(f"fixtures: statuses lack executable cases {sorted(missing_statuses)}")

    required_workflow_kinds = {"HAPPY_PATH", "FAILURE_PATH"}
    present_kinds = {workflow.get("kind") for workflow in workflow_map.values()}
    if not required_workflow_kinds <= present_kinds:
        errors.append("fixtures: both happy-path and failure-path executable workflows are required")
    if set(workflow_map) - referenced_workflows:
        errors.append(
            f"fixtures: unreferenced executable workflows {sorted(set(workflow_map) - referenced_workflows)}"
        )
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

    protocol_bytes = _canonical_text_bytes(paths["protocol"])
    protocol = protocol_bytes.decode("utf-8")
    checklist = paths["checklist"].read_text(encoding="utf-8")
    for token in (
        *REQUIRED_STAGES,
        *REQUIRED_STATUSES,
        "exactly one specialist",
        "Passing unit tests alone is insufficient",
    ):
        if token not in protocol:
            errors.append(f"protocol: missing {token!r}")
    for token in (
        "Authorized, unauthorized, and edge-case personas",
        "Human Git and merge gates remain explicit",
    ):
        if token not in checklist:
            errors.append(f"checklist: missing {token!r}")

    required_references = {
        "ROUTING_MAP.md": "Frontend/backend synchronicity",
        "skills/conductor/SKILL.md": "Synchronicity routing",
        "skills/the-tuner/SKILL.md": "CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md",
        "docs/setup/VALIDATION.md": "validate_cross_layer_synchronicity_contract.py",
    }
    for relative, token in required_references.items():
        path = repo_root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing required reference file")
            continue
        content = path.read_text(encoding="utf-8")
        if token not in content:
            errors.append(f"{relative}: missing {token!r}")

    errors.extend(validate_fixtures(load_json(paths["fixtures"]), protocol_bytes))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate the cross-layer synchronicity contract."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print(
        "[PASS] Cross-layer frontend-to-backend synchronicity contract "
        "is deterministic and complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
