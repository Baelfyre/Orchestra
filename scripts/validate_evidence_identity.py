"""Repository-level validator for Orchestra Phase 2 evidence identity."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_MODULE_PATH = ROOT / "scripts" / "evidence_identity.py"


def _load_identity_module():
    spec = importlib.util.spec_from_file_location("orchestra_evidence_identity", IDENTITY_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/evidence_identity.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Orchestra Phase 2 evidence identity contracts.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--approved-base-sha", default="HEAD")
    parser.add_argument("--evidence-json", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args(argv)


def _require_file(errors: list[str], root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        errors.append(f"missing required file: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def validate_repository_contract(root: Path) -> list[str]:
    errors: list[str] = []
    required_files = {
        "docs/governance/EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md": (
            "orchestra-evidence-v1",
            "tracked_patch_hash",
            "staged_patch_hash",
            "untracked_file_manifest",
            "added_blob_hashes",
            "working_tree_fingerprint",
            "Git clean-filter semantics",
            "Pre-existing artifacts must not be deleted",
        ),
        "docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md": (
            "Phase 2 evidence and continuity enforcement",
            "EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md",
        ),
        "docs/governance/DELEGATED_EXECUTION_POLICY.md": (
            "cross_layer_contract_hash",
            "staged_patch_hash",
            "open_invalidation_events",
        ),
        "skills/overseer/OUTPUT_FORMATS.md": (
            "identity_canonicalization_version",
            "tracked_patch_hash",
            "staged_patch_hash",
            "untracked_file_manifest",
            "artifact_lifecycle_records",
        ),
        "skills/the-tuner/OUTPUT_FORMATS.md": (
            "CURRENT CHANGE IDENTITY",
            "OPEN INVALIDATION EVENTS",
            "EVIDENCE REFRESH REQUIREMENTS",
        ),
        "skills/arbiter/SKILL.md": (
            "Phase 2 Evidence Freshness Enforcement",
            "identity canonicalization",
        ),
        "skills/overseer/SKILL.md": (
            "Phase 2 Evidence Binding",
            "generated-artifact inspection",
        ),
        "skills/ponytail/SKILL.md": (
            "Phase 2 Complete Handoff Delta",
            "added-file identities",
        ),
        "skills/the-tuner/SKILL.md": (
            "Phase 2 Invalidation and Evidence Reconciliation",
            "minimal re-entry set",
        ),
        "skills/conductor/SKILL.md": (
            "Phase 2 Re-entry Routing",
            "stale or incomplete change identity",
        ),
    }

    for relative, tokens in required_files.items():
        content = _require_file(errors, root, relative)
        for token in tokens:
            if content and token not in content:
                errors.append(f"{relative}: missing required token `{token}`")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo_root.resolve()
    errors = validate_repository_contract(root)

    identity = _load_identity_module()
    try:
        current = identity.collect_evidence_identity(root, args.approved_base_sha)
        self_errors = identity.validate_identity_document(current, current)
        errors.extend(f"self-identity: {item}" for item in self_errors)
        if args.evidence_json:
            errors.extend(
                identity.validate_evidence_file(root, args.approved_base_sha, args.evidence_json)
            )
    except Exception as exc:  # Fail closed with a compact diagnostic.
        errors.append(str(exc))
        current = None

    if args.json_output:
        print(
            json.dumps(
                {
                    "status": "FAIL" if errors else "PASS",
                    "errors": errors,
                    "identity": current,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    elif errors:
        for error in errors:
            print(f"[FAIL] {error}")
    else:
        print("[PASS] Evidence identity and freshness contracts are deterministic and current.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
