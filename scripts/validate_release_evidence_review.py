# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Read-only evidence classification for release review; never authorizes publication."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = "machine/schemas/release-evidence-review.v1.schema.json"
GATE_PATH = "docs/governance/RELEASE_GATES.md"
APP_PATH = "docs/governance/APP_RELEASE_COMPLIANCE_GATE.md"
DECISION_PATH = "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"
POLICY_PATH = "machine/governance/policy.v1.json"
DELEGATED_PATH = "docs/governance/DELEGATED_EXECUTION_POLICY.md"
PROTECTED_PATH = "docs/governance/PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md"
QUALIFICATION_PATH = "docs/governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md"

# Candidate-bound, policy-reviewed exception proposal. This does not grant rights or release authority.
EXCEPTION_HEAD = "665ec5536641683eab4c2739fb20b60835a7beed"
EXCEPTION_TREE = "e165cbc7687cdf3c115b4077d949030f0914843f"
EXCEPTION_GATES = {"IP/copyright cleared", "Human legal review completed (if flagged)"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def policy_fingerprint(root=ROOT):
    """Bind the review to the exact governing bytes, not to a claimed policy label."""
    digest = hashlib.sha256()
    for relative in (
        GATE_PATH, APP_PATH, DECISION_PATH, POLICY_PATH,
        DELEGATED_PATH, PROTECTED_PATH, QUALIFICATION_PATH,
    ):
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update((Path(root) / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def release_gate_inventory(root=ROOT):
    """Derive expected gates from the existing policy table, not user-supplied IDs."""
    content = (Path(root) / GATE_PATH).read_text(encoding="utf-8")
    section = content.split("## Pre-Release Checklist", 1)[1].split("\nFor release gating,", 1)[0]
    gates = {}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) != 3 or columns[0] == "Gate" or set(columns[0]) <= {"-", " "}:
            continue
        name, _, required = columns
        if not required.startswith("Yes") or name in gates:
            raise ValueError("release gate table contains an invalid or duplicate gate")
        conditional = any(term in name.lower() or term in required.lower()
                          for term in ("if flagged", "if needed", "when applicable"))
        gates[name] = {"conditional": conditional}
    if len(gates) < 15:
        raise ValueError("release gate inventory is missing or unexpectedly small")
    return gates


def validate_review(record, root=ROOT):
    """Return (errors, disposition); semantic checks cannot authenticate external claims."""
    root = Path(root)
    schema = load_json(root / SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = []
    for error in sorted(Draft202012Validator(schema).iter_errors(record),
                        key=lambda value: str(value.path)):
        errors.append(f"schema {'.'.join(map(str, error.path)) or '$'}: {error.message}")
    if errors:
        return errors, "INVALID_EVIDENCE"

    expected_policy = policy_fingerprint(root)
    if record["policy_fingerprint"] != expected_policy:
        errors.append("stale or mismatched governing policy fingerprint")

    expected_gates = release_gate_inventory(root)
    actual_names = [gate["name"] for gate in record["gates"]]
    if len(actual_names) != len(set(actual_names)):
        errors.append("duplicate release gate")
    if set(actual_names) != set(expected_gates):
        errors.append("release gate inventory differs from required policy inventory")

    evidence = {item["id"]: item for item in record["evidence"]}
    if len(evidence) != len(record["evidence"]):
        errors.append("duplicate evidence id")
    for item in record["evidence"]:
        if item["head_sha"] != record["candidate"]["head_sha"]:
            errors.append(f"stale candidate head in evidence {item['id']}")
        if item["policy_fingerprint"] != expected_policy:
            errors.append(f"stale policy in evidence {item['id']}")
        if item["kind"] == "CI_CHECK" and (
            item["check_status"] != "completed"
            or item["check_conclusion"] != "success"
            or item["status"] != "PASS"
        ):
            errors.append(f"CI evidence {item['id']} is not a successful completed check")

    unresolved_human = False
    has_failure = False
    has_pending = False
    qualified_exceptions = []
    for gate in record["gates"]:
        name = gate["name"]
        conditional = expected_gates.get(name, {}).get("conditional", False)
        if name == "App Release Compliance Gate reviewed" and record["candidate"]["release_channel"] != "PRIVATE_INTERNAL":
            conditional = False
        decision = gate["relevance"]
        if decision == "NOT_APPLICABLE":
            if not conditional:
                errors.append(f"required gate cannot be marked not applicable: {name}")
            if gate["validation"] != "NOT_APPLICABLE" or gate["compliance"] != "NOT_APPLICABLE":
                errors.append(f"N/A gate has inconsistent validation/compliance: {name}")
            if not gate["relevance_evidence_refs"]:
                errors.append(f"N/A gate needs positive applicability evidence: {name}")
            elif not any(evidence.get(ref, {}).get("kind") in {"REPOSITORY_SOURCE", "OWNER_ATTESTATION", "INDEPENDENT_REVIEW", "HUMAN_DECISION"} for ref in gate["relevance_evidence_refs"]):
                errors.append(f"N/A relevance needs non-CI applicability evidence: {name}")
            if len(gate["rationale"].strip()) < 12:
                errors.append(f"N/A gate needs a substantive rationale: {name}")
        elif decision == "REQUIRED":
            if not gate["relevance_evidence_refs"]:
                errors.append(f"required gate missing applicability evidence: {name}")
            elif not any(evidence.get(ref, {}).get("kind") in {
                "REPOSITORY_SOURCE", "OWNER_ATTESTATION", "INDEPENDENT_REVIEW", "HUMAN_DECISION"
            } for ref in gate["relevance_evidence_refs"]):
                errors.append(f"required gate lacks non-CI applicability evidence: {name}")
            if gate["validation"] == "NOT_APPLICABLE" or gate["compliance"] == "NOT_APPLICABLE":
                errors.append(f"required gate cannot skip validation/compliance: {name}")
        else:
            has_pending = True
            if gate["validation"] == "PASS" or gate["compliance"] == "PASS":
                errors.append(f"unknown relevance cannot be treated as passed: {name}")

        for field in ("relevance_evidence_refs", "validation_evidence_refs", "compliance_evidence_refs"):
            for ref in gate[field]:
                item = evidence.get(ref)
                if item is None or item["status"] != "PASS":
                    errors.append(f"missing or unsuccessful evidence {ref} for {name}/{field}")
        for status_field, ref_field in (
            ("validation", "validation_evidence_refs"),
            ("compliance", "compliance_evidence_refs"),
        ):
            if gate[status_field] == "PASS" and not gate[ref_field]:
                errors.append(f"unsupported {status_field} pass: {name}")

        sensitive = any(token in name.lower() for token in (
            "legal", "privacy", "ip/copyright", "license", "terms", "app release compliance",
        ))
        if (sensitive and decision == "REQUIRED" and gate["compliance"] == "PASS"
                and not any(evidence.get(ref, {}).get("kind") in {
                    "INDEPENDENT_REVIEW", "OWNER_ATTESTATION", "HUMAN_DECISION"
                } for ref in gate["compliance_evidence_refs"])):
            errors.append(f"sensitive compliance cannot be established by CI alone: {name}")

        if gate["compliance"] == "EXCEPTION_QUALIFIED":
            # Unlike PASS, this records an independently reviewed risk exception.
            # It is available only for this exact candidate and these two controls.
            exception = gate["bounded_exception"]
            qualified_exceptions.append((name, exception))
            if name not in EXCEPTION_GATES or decision != "REQUIRED":
                errors.append(f"exception not permitted for gate: {name}")
            if (record["candidate"]["head_sha"] != EXCEPTION_HEAD
                    or record["candidate"]["tree_sha"] != EXCEPTION_TREE
                    or record["candidate"]["release_channel"] != "PLUGIN_DISTRIBUTION"):
                errors.append(f"exception candidate/channel mismatch: {name}")
            if exception is not None:
                if (exception["candidate_head_sha"] != record["candidate"]["head_sha"]
                        or exception["candidate_tree_sha"] != record["candidate"]["tree_sha"]
                        or exception["release_channel"] != record["candidate"]["release_channel"]):
                    errors.append(f"exception evidence not bound to candidate: {name}")
                try:
                    expiry = datetime.fromisoformat(exception["expires_at"].replace("Z", "+00:00"))
                    if (expiry.utcoffset() is None
                            or not datetime.now(timezone.utc) < expiry <= datetime.now(timezone.utc) + timedelta(days=45)):
                        errors.append(f"exception expiry invalid or outside 45-day limit: {name}")
                except (ValueError, TypeError):
                    errors.append(f"exception expiry not a valid timezone-aware timestamp: {name}")
                for key, kind in (
                    ("owner_decision_ref", "HUMAN_DECISION"),
                    ("independent_review_ref", "INDEPENDENT_REVIEW"),
                    ("governor_reconsideration_ref", "INDEPENDENT_REVIEW"),
                ):
                    ref = exception[key]
                    item = evidence.get(ref)
                    if (item is None or item["kind"] != kind or item["status"] != "PASS"
                            or ref not in gate["compliance_evidence_refs"]):
                        errors.append(f"missing attributable exception evidence {key}: {name}")
                if exception["owner_decision_ref"] != gate["human_decision_ref"]:
                    errors.append(f"exception owner decision differs from gate human decision: {name}")
                if not exception["escalation_ref"].startswith("https://github.com/Baelfyre/Orchestra/issues/1003"):
                    errors.append(f"unexpected escalation source: {name}")
        elif gate.get("bounded_exception") is not None:
            errors.append(f"exception attachment without exception-qualified compliance: {name}")

        human_ref = gate["human_decision_ref"]
        if name == "Human legal review completed (if flagged)" and decision == "REQUIRED" and not human_ref:
            unresolved_human = True
        if human_ref is not None:
            item = evidence.get(human_ref)
            if item is None or item["kind"] != "HUMAN_DECISION" or item["status"] != "PASS":
                errors.append(f"invalid human decision reference: {name}")
        if gate["human_judgment_required"] and not human_ref:
            unresolved_human = True
        if gate["validation"] == "FAIL" or gate["compliance"] == "FAIL":
            has_failure = True
        if decision == "UNKNOWN" or "PENDING" in (gate["validation"], gate["compliance"]):
            has_pending = True

    if record["publication_authorized"] is not False:
        errors.append("evidence review must never grant publication authority")
    if errors:
        return errors, "INVALID_EVIDENCE"

    remediation = record["remediation"]
    limits = load_json(root / POLICY_PATH)["default_remediation"]
    max_attempts = limits["maximum_remediation_attempts_per_unit"]
    if record["protected_policy_change"] or remediation["would_change_governing_gate"]:
        return [], "ESCALATE_HUMAN"
    if record["unresolved_conflicts"] or unresolved_human:
        return [], "ESCALATE_HUMAN"
    if has_failure:
        if (remediation["deterministic_in_scope"]
                and remediation["authorized"]
                and not remediation["scope_growth"]
                and remediation["attempts_used"] < max_attempts):
            return [], "AUTO_REMEDIATE_AND_REVALIDATE"
        return [], "ESCALATE_HUMAN"
    if has_pending:
        return [], "WAIT_FOR_EVIDENCE"
    return [], "EVIDENCE_READY_FOR_FINAL_REVIEW"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        errors, disposition = validate_review(load_json(args.record))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"INVALID_EVIDENCE: {exc}")
        return 2
    if errors:
        for error in errors:
            print(f"INVALID_EVIDENCE: {error}")
        return 2
    print(f"RELEASE_REVIEW_DISPOSITION={disposition}")
    print("RELEASE_PUBLICATION_AUTHORIZED=false")
    # Exit zero means this record is internally ready for *human review*, not for release.
    # Pending remediation, missing evidence, and escalation must not appear CI-green.
    if disposition == "EVIDENCE_READY_FOR_FINAL_REVIEW":
        return 0
    if disposition == "ESCALATE_HUMAN":
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
