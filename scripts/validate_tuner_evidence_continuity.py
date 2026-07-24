"""Deterministic Phase 2 invalidation, artifact, and continuity validator."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "tests" / "behavior" / "tuner-evidence-continuity-fixtures.json"
SUPPORTED_CANONICALIZATION = "orchestra-evidence-v1"
SUPPORTED_PACKET_STATUSES = {"FROZEN", "STALE", "CONTRADICTED", "INCOMPLETE"}
PREEXISTING_STATES = {"PRESENT_TRACKED", "PRESENT_UNTRACKED", "PRESENT_IGNORED"}
ARTIFACT_STATES = {"ABSENT", *PREEXISTING_STATES}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PACKET_BOOLEAN_FIELDS = {
    "contract_hash_current",
    "contract_revision_current",
    "branch_matches",
    "commit_matches",
    "tracked_patch_matches",
    "staged_patch_matches",
    "untracked_manifest_complete",
    "added_blob_hashes_complete",
    "working_tree_fingerprint_matches",
    "artifact_lifecycle_complete",
    "external_action_required",
    "external_action_authorized",
    "dagger_requested",
    "dagger_authorized",
    "scope_expansion",
    "human_tradeoff_required",
    "unsafe_or_prohibited",
}
AUTHORITY_BOOLEAN_FIELDS = {
    "external_action_required",
    "external_action_authorized",
    "dagger_requested",
    "dagger_authorized",
    "scope_expansion",
    "human_tradeoff_required",
    "unsafe_or_prohibited",
}
PACKET_STRING_LIST_FIELDS = {
    "open_invalidation_events",
    "required_reentry",
    "completed_reentry",
}
REQUIRED_FIXTURE_IDS = {
    "current-evidence-auto-continue",
    "obsolete-contract-hash",
    "tracked-patch-mismatch",
    "staged-patch-mismatch",
    "untracked-manifest-incomplete",
    "added-blob-omitted",
    "open-invalidation-event",
    "manual-reentry-incomplete",
    "manual-reentry-complete",
    "delegated-reentry-within-envelope",
    "delegated-scope-expansion",
    "minimal-security-reentry",
    "generated-artifact-uninspected",
    "preexisting-ignored-artifact-preserved",
    "cleanup-without-authority",
    "unknown-canonicalization-fails-closed",
    "unknown-packet-status-fails-closed",
    "dagger-remains-blocked",
    "external-action-default-deny",
    "malformed-dagger-authorization",
    "malformed-external-authorization",
    "malformed-artifact-inspection",
    "malformed-artifact-cleanup",
    "artifact-missing-content-hash",
    "artifact-invalid-state",
    "malformed-reentry-list",
    "unknown-reentry-trigger",
    "missing-reentry-owner",
    "malformed-reentry-edge",
    "cyclic-reentry-graph",
}


class ContinuityContractError(ValueError):
    pass


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{field} must be an array of non-empty strings"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not _non_empty_string(item):
            errors.append(f"{field}[{index}] must be a non-empty string")
    return errors


def _validate_packet_schema(packet: Mapping[str, Any]) -> tuple[list[str], bool]:
    errors: list[str] = []
    authority_malformed = False

    for field in sorted(PACKET_BOOLEAN_FIELDS):
        if field not in packet or type(packet.get(field)) is not bool:
            errors.append(f"{field} must be a JSON boolean")
            if field in AUTHORITY_BOOLEAN_FIELDS:
                authority_malformed = True

    for field in sorted(PACKET_STRING_LIST_FIELDS):
        errors.extend(_validate_string_list(packet.get(field), field))

    artifact_records = packet.get("artifact_records")
    if not isinstance(artifact_records, list):
        errors.append("artifact_records must be an array")
    else:
        for index, record in enumerate(artifact_records):
            if not isinstance(record, Mapping):
                errors.append(f"artifact_records[{index}] must be an object")

    return errors, authority_malformed


def _validated_contract_owners(contract_owners: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(contract_owners, Mapping):
        raise ContinuityContractError("contract_owners must be an object")
    normalized: dict[str, str] = {}
    for contract, owner in contract_owners.items():
        if not _non_empty_string(contract) or not _non_empty_string(owner):
            raise ContinuityContractError(
                "contract_owners keys and values must be non-empty strings"
            )
        normalized[str(contract)] = str(owner)
    return normalized


def minimal_reentry(
    trigger_contracts: Sequence[str],
    dependency_edges: Sequence[Sequence[str]],
    contract_owners: Mapping[str, str],
) -> list[str]:
    """Return only owners reachable through declared invalidation dependencies."""
    if (
        not isinstance(trigger_contracts, Sequence)
        or isinstance(trigger_contracts, (str, bytes))
        or not trigger_contracts
    ):
        raise ContinuityContractError("trigger_contracts must be a non-empty array")

    owners = _validated_contract_owners(contract_owners)
    adjacency: dict[str, list[str]] = {}
    graph_nodes: set[str] = set()

    for edge in dependency_edges:
        if not isinstance(edge, Sequence) or isinstance(edge, (str, bytes)) or len(edge) != 2:
            raise ContinuityContractError(f"invalid dependency edge: {edge!r}")
        source, target = edge
        if not _non_empty_string(source) or not _non_empty_string(target):
            raise ContinuityContractError(f"invalid dependency edge: {edge!r}")
        source_text, target_text = str(source), str(target)
        graph_nodes.update({source_text, target_text})
        adjacency.setdefault(source_text, []).append(target_text)

    normalized_triggers: list[str] = []
    for trigger in trigger_contracts:
        if not _non_empty_string(trigger):
            raise ContinuityContractError("trigger_contracts entries must be non-empty strings")
        trigger_text = str(trigger)
        if trigger_text not in graph_nodes:
            raise ContinuityContractError(f"unknown trigger contract: {trigger_text}")
        if trigger_text not in owners:
            raise ContinuityContractError(f"missing owner for trigger contract: {trigger_text}")
        normalized_triggers.append(trigger_text)

    missing_graph_owners = sorted(node for node in graph_nodes if node not in owners)
    if missing_graph_owners:
        raise ContinuityContractError(
            f"missing owner for declared contracts: {missing_graph_owners}"
        )

    queue = deque(normalized_triggers)
    seen = set(queue)
    affected_contracts: set[str] = set()
    while queue:
        source = queue.popleft()
        for target in sorted(set(adjacency.get(source, []))):
            if target in seen:
                continue
            seen.add(target)
            affected_contracts.add(target)
            queue.append(target)

    return sorted({owners[contract] for contract in affected_contracts})


def _artifact_schema_errors(record: Mapping[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    for field in (
        "artifact_id",
        "collaboration_session_id",
        "producer_role",
        "producing_command",
        "path",
        "artifact_type",
    ):
        if not _non_empty_string(record.get(field)):
            errors.append(f"artifact {label}: {field} must be a non-empty string")

    revision = record.get("contract_packet_revision")
    if not isinstance(revision, (str, int)) or isinstance(revision, bool) or not str(revision).strip():
        errors.append(
            f"artifact {label}: contract_packet_revision must be a non-empty string or integer"
        )

    for state_field in ("state_before", "state_after"):
        if record.get(state_field) not in ARTIFACT_STATES:
            errors.append(f"artifact {label}: invalid {state_field}")

    for bool_field in (
        "cleanup_performed",
        "retention_required",
        "inspection_required",
        "inspection_completed",
    ):
        if type(record.get(bool_field)) is not bool:
            errors.append(f"artifact {label}: {bool_field} must be a JSON boolean")

    state_after = record.get("state_after")
    content_hash = record.get("content_hash")
    if state_after == "ABSENT":
        if content_hash not in {None, ""}:
            errors.append(f"artifact {label}: absent artifact must not carry content_hash")
    elif state_after in ARTIFACT_STATES:
        if not isinstance(content_hash, str) or not SHA256_RE.fullmatch(content_hash):
            errors.append(
                f"artifact {label}: present artifact requires a lowercase SHA-256 content_hash"
            )

    inspection_required = record.get("inspection_required")
    inspection_completed = record.get("inspection_completed")
    inspection_owner = record.get("inspection_owner")
    if inspection_required is True or inspection_completed is True:
        if not _non_empty_string(inspection_owner):
            errors.append(f"artifact {label}: inspection_owner is required")
    elif inspection_owner is not None and not isinstance(inspection_owner, str):
        errors.append(f"artifact {label}: inspection_owner must be a string or null")

    if inspection_required is True and inspection_completed is not True:
        errors.append(f"artifact {label}: required generated-artifact inspection is incomplete")

    cleanup_performed = record.get("cleanup_performed")
    cleanup_authority = record.get("cleanup_authority")
    if cleanup_performed is True:
        for field in ("cleanup_authority", "cleanup_condition", "cleanup_evidence"):
            if not _non_empty_string(record.get(field)):
                errors.append(f"artifact {label}: {field} is required for cleanup")

    if (
        record.get("state_before") in PREEXISTING_STATES
        and cleanup_performed is True
        and not _non_empty_string(cleanup_authority)
    ):
        errors.append(f"artifact {label}: pre-existing artifact cleanup lacks authority")
    if record.get("retention_required") is True and cleanup_performed is True:
        errors.append(f"artifact {label}: retained evidence artifact was cleaned")

    binding = record.get("freshness_binding")
    if not isinstance(binding, Mapping):
        errors.append(f"artifact {label}: freshness_binding must be an object")
    else:
        for field in ("baseline_sha", "current_commit_sha", "contract_hash"):
            if not _non_empty_string(binding.get(field)):
                errors.append(
                    f"artifact {label}: freshness_binding.{field} must be non-empty"
                )

    return errors


def validate_artifact_records(records: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return ["artifact_records must be an array"]
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"artifact record {index}: must be an object")
            continue
        label = str(record.get("artifact_id") or record.get("path") or index)
        errors.extend(_artifact_schema_errors(record, label))
    return errors


def evaluate_continuity(packet: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Apply Phase 2 fail-closed transition precedence without domain decisions."""
    if not isinstance(packet, Mapping):
        return "STOP", ["packet must be an object"]

    schema_findings, authority_malformed = _validate_packet_schema(packet)
    if authority_malformed:
        return "STOP", schema_findings

    if packet.get("unsafe_or_prohibited") is True:
        return "STOP", ["unsafe or prohibited condition"]
    if packet.get("scope_expansion") is True or packet.get("human_tradeoff_required") is True:
        return "ESCALATE_HUMAN", ["scope expansion or human tradeoff required"]
    if (
        packet.get("external_action_required") is True
        and packet.get("external_action_authorized") is not True
    ):
        return "ESCALATE_HUMAN", ["external action remains default-deny"]
    if packet.get("dagger_requested") is True and packet.get("dagger_authorized") is not True:
        return "STOP", ["Dagger remains blocked without explicit authorization"]

    findings: list[str] = list(schema_findings)
    status = packet.get("packet_status")
    if status not in SUPPORTED_PACKET_STATUSES:
        findings.append("unknown or malformed packet status")
    elif status != "FROZEN":
        findings.append(f"packet status is {status}, not FROZEN")

    if packet.get("identity_canonicalization_version") != SUPPORTED_CANONICALIZATION:
        findings.append("unknown identity canonicalization")

    boolean_requirements = {
        "contract_hash_current": "contract hash is stale",
        "contract_revision_current": "contract revision is stale",
        "branch_matches": "evidence branch differs",
        "commit_matches": "evidence commit differs",
        "tracked_patch_matches": "tracked patch hash differs",
        "staged_patch_matches": "staged patch hash differs",
        "untracked_manifest_complete": "untracked manifest is incomplete",
        "added_blob_hashes_complete": "added-file identities are incomplete",
        "working_tree_fingerprint_matches": "working-tree fingerprint differs",
        "artifact_lifecycle_complete": "artifact lifecycle evidence is incomplete",
    }
    for field, message in boolean_requirements.items():
        if packet.get(field) is not True:
            findings.append(message)

    open_events = packet.get("open_invalidation_events")
    if isinstance(open_events, list) and open_events:
        findings.append("open invalidation events remain")

    required = packet.get("required_reentry")
    completed = packet.get("completed_reentry")
    if isinstance(required, list) and isinstance(completed, list):
        required_sorted = sorted(set(required))
        completed_sorted = sorted(set(completed))
        if required_sorted != completed_sorted:
            findings.append("required specialist re-entry is incomplete")

    artifact_records = packet.get("artifact_records")
    if isinstance(artifact_records, list):
        findings.extend(validate_artifact_records(artifact_records))

    if findings:
        return "WAIT_FOR_EVIDENCE", findings
    return "AUTO_CONTINUE", []


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ContinuityContractError("fixtures must be a top-level list")
    return value


def validate_fixtures(fixtures: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for fixture in fixtures:
        fixture_id = fixture.get("id")
        if not fixture_id:
            errors.append("fixture missing id")
            continue
        fixture_id = str(fixture_id)
        if fixture_id in seen:
            errors.append(f"duplicate fixture id: {fixture_id}")
        seen.add(fixture_id)

        packet = fixture.get("packet")
        if not isinstance(packet, Mapping):
            errors.append(f"{fixture_id}: missing packet object")
            continue
        expected = fixture.get("expected_disposition")
        actual, findings = evaluate_continuity(packet)
        if actual != expected:
            errors.append(f"{fixture_id}: expected {expected}, got {actual}: {findings}")

        if "expected_minimal_reentry" in fixture or "expected_reentry_error" in fixture:
            try:
                actual_reentry = minimal_reentry(
                    fixture.get("trigger_contracts", []),
                    fixture.get("dependency_edges", []),
                    fixture.get("contract_owners", {}),
                )
            except ContinuityContractError as exc:
                expected_error = fixture.get("expected_reentry_error")
                if not expected_error or str(expected_error) not in str(exc):
                    errors.append(f"{fixture_id}: {exc}")
            else:
                if "expected_reentry_error" in fixture:
                    errors.append(
                        f"{fixture_id}: expected re-entry error "
                        f"{fixture.get('expected_reentry_error')!r}, got {actual_reentry}"
                    )
                elif actual_reentry != fixture.get("expected_minimal_reentry"):
                    errors.append(
                        f"{fixture_id}: expected re-entry {fixture.get('expected_minimal_reentry')}, "
                        f"got {actual_reentry}"
                    )

    missing = sorted(REQUIRED_FIXTURE_IDS - seen)
    if missing:
        errors.append(f"missing required Phase 2 fixtures: {missing}")
    return errors


def validate_repository_contract(root: Path) -> list[str]:
    errors: list[str] = []
    checks = {
        "skills/arbiter/SKILL.md": ("Phase 2 Evidence Freshness Enforcement", "WAIT_FOR_EVIDENCE"),
        "skills/overseer/SKILL.md": ("Phase 2 Evidence Binding", "contract hash"),
        "skills/ponytail/SKILL.md": ("Phase 2 Complete Handoff Delta", "untracked"),
        "skills/the-tuner/SKILL.md": ("Phase 2 Invalidation and Evidence Reconciliation", "minimal re-entry"),
        "skills/conductor/SKILL.md": ("Phase 2 Re-entry Routing", "Conductor remains"),
        "docs/governance/EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md": (
            "GeneratedArtifactLifecycleRecord",
            "InvalidationEvent",
            "manual mode",
            "delegated mode",
            "exact JSON booleans",
            "unknown trigger",
        ),
    }
    for relative, tokens in checks.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in content:
                errors.append(f"{relative}: missing required token `{token}`")
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate The Tuner Phase 2 evidence continuity contract.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        fixtures = _load_fixtures(args.fixtures)
        errors = validate_fixtures(fixtures)
        errors.extend(validate_repository_contract(args.repo_root.resolve()))
    except (OSError, json.JSONDecodeError, ContinuityContractError) as exc:
        errors = [str(exc)]

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] The Tuner Phase 2 evidence continuity contract is deterministic and fail-closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
