"""Deterministic Phase 2 invalidation, artifact, and continuity validator."""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "tests" / "behavior" / "tuner-evidence-continuity-fixtures.json"
SUPPORTED_CANONICALIZATION = "orchestra-evidence-v1"
SUPPORTED_PACKET_STATUSES = {"FROZEN", "STALE", "CONTRADICTED", "INCOMPLETE"}
PREEXISTING_STATES = {"PRESENT_TRACKED", "PRESENT_UNTRACKED", "PRESENT_IGNORED"}
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
}


class ContinuityContractError(ValueError):
    pass


def minimal_reentry(
    trigger_contracts: Sequence[str],
    dependency_edges: Sequence[Sequence[str]],
    contract_owners: Mapping[str, str],
) -> list[str]:
    """Return only owners reachable through declared invalidation dependencies."""
    adjacency: dict[str, list[str]] = {}
    for edge in dependency_edges:
        if not isinstance(edge, Sequence) or isinstance(edge, (str, bytes)) or len(edge) != 2:
            raise ContinuityContractError(f"invalid dependency edge: {edge!r}")
        source, target = str(edge[0]), str(edge[1])
        adjacency.setdefault(source, []).append(target)

    queue = deque(str(item) for item in trigger_contracts)
    seen = set(queue)
    affected_contracts: set[str] = set()
    while queue:
        source = queue.popleft()
        for target in sorted(adjacency.get(source, [])):
            if target in seen:
                continue
            seen.add(target)
            affected_contracts.add(target)
            queue.append(target)

    missing = sorted(contract for contract in affected_contracts if contract not in contract_owners)
    if missing:
        raise ContinuityContractError(f"missing owner for invalidated contracts: {missing}")
    return sorted({contract_owners[contract] for contract in affected_contracts})


def validate_artifact_records(records: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, record in enumerate(records):
        label = str(record.get("artifact_id") or record.get("path") or index)
        state_before = record.get("state_before")
        cleanup_performed = bool(record.get("cleanup_performed"))
        cleanup_authority = record.get("cleanup_authority")
        retention_required = bool(record.get("retention_required"))
        inspection_required = bool(record.get("inspection_required"))
        inspection_completed = bool(record.get("inspection_completed"))
        contract_hash = record.get("contract_hash")

        if not record.get("path"):
            errors.append(f"artifact {label}: missing path")
        if state_before not in {"ABSENT", *PREEXISTING_STATES}:
            errors.append(f"artifact {label}: invalid state_before")
        if state_before in PREEXISTING_STATES and cleanup_performed and not cleanup_authority:
            errors.append(f"artifact {label}: pre-existing artifact cleanup lacks authority")
        if retention_required and cleanup_performed:
            errors.append(f"artifact {label}: retained evidence artifact was cleaned")
        if inspection_required and not inspection_completed:
            errors.append(f"artifact {label}: required generated-artifact inspection is incomplete")
        if inspection_completed and not contract_hash:
            errors.append(f"artifact {label}: inspected artifact lacks contract binding")
    return errors


def evaluate_continuity(packet: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Apply Phase 2 fail-closed transition precedence without domain decisions."""
    findings: list[str] = []

    if packet.get("unsafe_or_prohibited"):
        return "STOP", ["unsafe or prohibited condition"]
    if packet.get("scope_expansion") or packet.get("human_tradeoff_required"):
        return "ESCALATE_HUMAN", ["scope expansion or human tradeoff required"]
    if packet.get("external_action_required") and not packet.get("external_action_authorized"):
        return "ESCALATE_HUMAN", ["external action remains default-deny"]
    if packet.get("dagger_requested") and not packet.get("dagger_authorized"):
        return "STOP", ["Dagger remains blocked without explicit authorization"]

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

    open_events = packet.get("open_invalidation_events", [])
    if open_events:
        findings.append("open invalidation events remain")

    required = sorted(set(packet.get("required_reentry", [])))
    completed = sorted(set(packet.get("completed_reentry", [])))
    if required != completed:
        findings.append("required specialist re-entry is incomplete")

    findings.extend(validate_artifact_records(packet.get("artifact_records", [])))

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

        if "expected_minimal_reentry" in fixture:
            try:
                actual_reentry = minimal_reentry(
                    fixture.get("trigger_contracts", []),
                    fixture.get("dependency_edges", []),
                    fixture.get("contract_owners", {}),
                )
            except ContinuityContractError as exc:
                errors.append(f"{fixture_id}: {exc}")
            else:
                if actual_reentry != fixture.get("expected_minimal_reentry"):
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
