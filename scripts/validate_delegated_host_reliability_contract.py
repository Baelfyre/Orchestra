import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "orchestra-delegated-host-reliability-v1"
PROTOCOL_REVISION = "delegated-host-reliability-v1"
SIMULATED = "SIMULATED_REPOSITORY_EVIDENCE"
LIVE = "LIVE_HOST_EVIDENCE"
LIVE_PENDING = "PENDING_LOCAL_HOST_VALIDATION"
HOSTS = {
    "codex": "ACTIVE",
    "antigravity": "ACTIVE",
    "claude-code": "SCAFFOLD_ONLY",
}
DISPOSITIONS = {
    "AUTO_CONTINUE",
    "WAIT_FOR_EVIDENCE",
    "WAIT_FOR_CAPACITY",
    "ESCALATE_HUMAN",
    "STOP",
}
CASE_FIELDS = {
    "id",
    "host_from",
    "host_to",
    "host_from_maturity",
    "host_to_maturity",
    "evidence_level",
    "repo_commit_sha",
    "runtime_bundle_sha256",
    "correlation_id",
    "run_id",
    "checkpoint_id",
    "capacity_handoff_id",
    "approved_base_sha",
    "input_envelope_sha256",
    "evidence_packet_sha256",
    "output_envelope_sha256",
    "resume_attempt",
    "expected_disposition",
    "authority_preserved",
    "context_minimized",
    "side_effect_replayed",
    "identity_current",
    "checkpoint_complete",
    "capacity_available",
    "result",
}
REQUIRED_SCENARIOS = {
    "codex-same-host-reset-resume",
    "antigravity-same-host-reset-resume",
    "codex-to-antigravity-portable-handoff",
    "capacity-interruption-with-valid-checkpoint",
    "stale-repository-revision",
    "stale-runtime-bundle",
    "incomplete-checkpoint",
    "claude-code-scaffold-runtime-request",
    "authority-expansion-on-resume",
    "duplicate-checkpoint-consumption",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_sha256(value, allow_none=False):
    if value is None:
        return allow_none
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def _validate_case(case):
    errors = []
    case_id = case.get("id", "<unknown>") if isinstance(case, dict) else "<invalid>"
    if not isinstance(case, dict) or set(case) != CASE_FIELDS:
        return [f"{case_id}: case must contain exactly the required fields"]

    if not _nonempty(case_id):
        errors.append("case id must be non-empty")
    for host_field, maturity_field in (
        ("host_from", "host_from_maturity"),
        ("host_to", "host_to_maturity"),
    ):
        host = case[host_field]
        if host not in HOSTS:
            errors.append(f"{case_id}: unknown {host_field} {host!r}")
        elif case[maturity_field] != HOSTS[host]:
            errors.append(
                f"{case_id}: {maturity_field} must match declared host maturity"
            )

    if case["evidence_level"] not in {SIMULATED, LIVE}:
        errors.append(f"{case_id}: invalid evidence_level")
    if case["evidence_level"] == LIVE:
        errors.append(
            f"{case_id}: repository fixtures must not fabricate LIVE_HOST_EVIDENCE"
        )

    for field in ("repo_commit_sha", "approved_base_sha"):
        if not isinstance(case[field], str) or not SHA40.fullmatch(case[field]):
            errors.append(f"{case_id}: {field} must be a lowercase 40-character SHA")
    for field in (
        "runtime_bundle_sha256",
        "input_envelope_sha256",
        "evidence_packet_sha256",
    ):
        if not _valid_sha256(case[field]):
            errors.append(f"{case_id}: {field} must be a lowercase SHA-256")
    if not _valid_sha256(case["output_envelope_sha256"], allow_none=True):
        errors.append(
            f"{case_id}: output_envelope_sha256 must be null or a lowercase SHA-256"
        )

    for field in ("correlation_id", "run_id", "checkpoint_id", "result"):
        if not _nonempty(case[field]):
            errors.append(f"{case_id}: {field} must be non-empty")
    if case["capacity_handoff_id"] is not None and not _nonempty(
        case["capacity_handoff_id"]
    ):
        errors.append(f"{case_id}: capacity_handoff_id must be null or non-empty")
    if not isinstance(case["resume_attempt"], int) or case["resume_attempt"] < 1:
        errors.append(f"{case_id}: resume_attempt must be a positive integer")
    for field in (
        "authority_preserved",
        "context_minimized",
        "side_effect_replayed",
        "identity_current",
        "checkpoint_complete",
        "capacity_available",
    ):
        if not isinstance(case[field], bool):
            errors.append(f"{case_id}: {field} must be boolean")

    disposition = case["expected_disposition"]
    if disposition not in DISPOSITIONS:
        errors.append(f"{case_id}: unknown expected_disposition")
        return errors

    active_pair = (
        case["host_from_maturity"] == "ACTIVE"
        and case["host_to_maturity"] == "ACTIVE"
    )
    safe_identity = (
        case["identity_current"]
        and case["checkpoint_complete"]
        and case["authority_preserved"]
        and case["context_minimized"]
        and not case["side_effect_replayed"]
    )

    if disposition == "AUTO_CONTINUE":
        if not active_pair:
            errors.append(f"{case_id}: AUTO_CONTINUE requires active source and destination hosts")
        if not safe_identity:
            errors.append(f"{case_id}: AUTO_CONTINUE requires current complete safe identity")
        if not case["capacity_available"]:
            errors.append(f"{case_id}: AUTO_CONTINUE requires available capacity")
        if case["output_envelope_sha256"] is None:
            errors.append(f"{case_id}: AUTO_CONTINUE requires an output envelope identity")
        if case["repo_commit_sha"] != case["approved_base_sha"]:
            errors.append(f"{case_id}: AUTO_CONTINUE requires approved repository lineage")

    elif disposition == "WAIT_FOR_CAPACITY":
        if not active_pair or not safe_identity:
            errors.append(f"{case_id}: WAIT_FOR_CAPACITY requires otherwise-valid active-host evidence")
        if case["capacity_available"]:
            errors.append(f"{case_id}: WAIT_FOR_CAPACITY requires unavailable capacity")
        if case["output_envelope_sha256"] is not None:
            errors.append(f"{case_id}: WAIT_FOR_CAPACITY must not claim an output envelope")

    elif disposition == "WAIT_FOR_EVIDENCE":
        if case["identity_current"] and case["checkpoint_complete"]:
            errors.append(f"{case_id}: WAIT_FOR_EVIDENCE requires stale identity or incomplete checkpoint")
        if case["output_envelope_sha256"] is not None:
            errors.append(f"{case_id}: WAIT_FOR_EVIDENCE must not claim an output envelope")

    elif disposition == "ESCALATE_HUMAN":
        if active_pair:
            errors.append(f"{case_id}: ESCALATE_HUMAN host-maturity fixture requires a non-active host")
        if case["output_envelope_sha256"] is not None:
            errors.append(f"{case_id}: ESCALATE_HUMAN must not claim an output envelope")

    elif disposition == "STOP":
        unsafe = (
            not case["authority_preserved"]
            or case["side_effect_replayed"]
            or case["resume_attempt"] > 1
        )
        if not unsafe:
            errors.append(f"{case_id}: STOP fixture must demonstrate an unsafe continuation invariant")
        if case["output_envelope_sha256"] is not None:
            errors.append(f"{case_id}: STOP must not claim an output envelope")

    return errors


def validate_fixtures(data):
    errors = []
    if not isinstance(data, dict):
        return ["fixtures: root must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("fixtures: invalid schema_version")
    if data.get("protocol_revision") != PROTOCOL_REVISION:
        errors.append("fixtures: invalid protocol_revision")
    if data.get("declared_hosts") != HOSTS:
        errors.append("fixtures: declared_hosts must match current Orchestra host maturity")
    if set(data.get("allowed_dispositions", ())) != DISPOSITIONS:
        errors.append("fixtures: allowed_dispositions must match the Phase C disposition set")

    simulation = data.get("repository_simulation")
    if simulation != {
        "status": "SIMULATED_CONTRACT_VALIDATED",
        "evidence_level": SIMULATED,
    }:
        errors.append("fixtures: repository_simulation must remain explicitly simulated")

    live = data.get("live_validation")
    if not isinstance(live, dict):
        errors.append("fixtures: live_validation must be an object")
    else:
        if live.get("status") != LIVE_PENDING:
            errors.append(
                "fixtures: repository evidence must not claim live installed-host validation complete"
            )
        if live.get("records") != []:
            errors.append(
                "fixtures: repository fixture must not contain fabricated live-host evidence records"
            )

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixtures: cases must be a non-empty list")
        return errors
    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(set(ids)):
        errors.append("fixtures: case ids must be unique")
    if set(ids) != REQUIRED_SCENARIOS:
        errors.append("fixtures: required Phase C scenario coverage is incomplete or unknown")
    dispositions = {case.get("expected_disposition") for case in cases if isinstance(case, dict)}
    if dispositions != DISPOSITIONS:
        errors.append("fixtures: all five Phase C dispositions must be covered")
    for case in cases:
        errors.extend(_validate_case(case))
    return errors


def validate(repo_root):
    paths = {
        "protocol": repo_root / "docs/validation/DELEGATED_HOST_RELIABILITY_PROTOCOL.md",
        "checklist": repo_root / "docs/validation/checklists/DELEGATED_HOST_RELIABILITY_CHECKLIST.md",
        "fixtures": repo_root / "tests/behavior/delegated-host-reliability-fixtures.json",
    }
    errors = []
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"missing required {label}: {path.relative_to(repo_root).as_posix()}")
    if errors:
        return errors

    protocol = paths["protocol"].read_text(encoding="utf-8")
    checklist = paths["checklist"].read_text(encoding="utf-8")
    for token in (
        "PENDING_LOCAL_HOST_VALIDATION",
        "SIMULATED_REPOSITORY_EVIDENCE",
        "LIVE_HOST_EVIDENCE",
        "codex",
        "antigravity",
        "claude-code",
        "SCAFFOLD_ONLY",
        "AUTO_CONTINUE",
        "WAIT_FOR_EVIDENCE",
        "WAIT_FOR_CAPACITY",
        "ESCALATE_HUMAN",
        "STOP",
        "repository-only run MUST NOT set Phase C to `COMPLETE`",
    ):
        if token not in protocol:
            errors.append(f"protocol: missing {token!r}")
    for token in (
        "Codex active-host reset/resume",
        "Antigravity active-host reset/resume",
        "Claude Code scaffold/package compatibility",
        "Phase C remains `PENDING_LOCAL_HOST_VALIDATION`",
    ):
        if token not in checklist:
            errors.append(f"checklist: missing {token!r}")

    data = json.loads(paths["fixtures"].read_text(encoding="utf-8"))
    errors.extend(validate_fixtures(data))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate delegated Phase C host reliability repository evidence."
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print(
        "[PASS] Delegated host reliability repository evidence is deterministic; live host validation remains pending."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
