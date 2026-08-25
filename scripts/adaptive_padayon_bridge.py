#!/usr/bin/env python3
"""Build a non-authorizing Padayon promotion envelope from one A3 candidate.

This tool never writes Padayon and never marks a local candidate promoted. It
only emits a privacy-minimized envelope that Padayon can validate separately.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA = ROOT / "machine" / "schemas" / "adaptive-shadow-candidate.schema.json"
BRIDGE_SCHEMA = ROOT / "machine" / "schemas" / "padayon-memory-promotion-candidate.schema.json"

TYPE_MAP = {
    "USER_PREFERENCE_TENDENCY": "USER_PREFERENCE",
    "WORKFLOW_TENDENCY": "WORKFLOW_PATTERN",
    "SPECIALIST_STRATEGY_TENDENCY": "SPECIALIST_STRATEGY",
}
CATEGORIES = (
    "ARCHITECTURE",
    "CODE_REVIEW",
    "CONTEXT_RETRIEVAL",
    "DESIGN_UI_UX",
    "DOCUMENTATION",
    "REMEDIATION",
    "RESEARCH",
    "TESTING",
    "TOOLING",
    "VALIDATION",
    "WORKFLOW",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = load_json(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_promotion_envelope(
    candidate: dict[str, Any],
    *,
    category: str,
    repositories: list[str] | None = None,
    projects: list[str] | None = None,
    use_cases: list[str] | None = None,
    specialists: list[str] | None = None,
    tags: list[str] | None = None,
    created_at: str | None = None,
    privacy_reviewed: bool = False,
) -> dict[str, Any]:
    _validator(SOURCE_SCHEMA).validate(candidate)

    if candidate["status"] != "CANDIDATE":
        raise ValueError("only active A3 CANDIDATE records may enter the Padayon promotion bridge")
    if not privacy_reviewed:
        raise ValueError("portable promotion requires an explicit privacy review")
    if category not in CATEGORIES:
        raise ValueError(f"unsupported category: {category}")

    source_scope = candidate["scope"]
    mapped_projects = list(projects or [])
    mapped_specialists = list(specialists or [])
    if source_scope.get("project_key"):
        mapped_projects.append(source_scope["project_key"])
    if source_scope.get("specialist_slug"):
        mapped_specialists.append(source_scope["specialist_slug"])

    refs = list(candidate["supporting_signal_refs"])
    digests = list(candidate["supporting_signal_digests"])
    if len(refs) != len(digests):
        raise ValueError("supporting signal refs and digests must have one-to-one parity")

    envelope = {
        "schema_version": "orchestra.padayon-memory-promotion-candidate.v1",
        "source": {
            "system": "ORCHESTRA_ADAPTIVE_A3",
            "candidate_id": candidate["candidate_id"],
            "source_schema_version": candidate["schema_version"],
            "learner_rule_version": candidate["learner_rule_version"],
            "status": candidate["status"],
            "shadow_only": candidate["shadow_only"],
            "promotion_state": candidate["promotion_state"],
        },
        "pattern": {
            "key": candidate["subject_key"],
            "type": TYPE_MAP[candidate["candidate_type"]],
            "category": category,
            "value": candidate["candidate_value"],
            "scope": {
                "repositories": _unique(list(repositories or [])),
                "projects": _unique(mapped_projects),
                "use_cases": _unique(list(use_cases or [])),
                "specialists": _unique(mapped_specialists),
            },
            "tags": _unique(list(tags or [])),
        },
        "evidence": {
            "refs": refs,
            "digests": digests,
            "distinct_support_count": candidate["distinct_support_count"],
            "confidence": candidate["confidence"],
            "confidence_method": candidate["confidence_method"],
            "first_seen": candidate["first_seen"],
            "last_seen": candidate["last_seen"],
        },
        "privacy": {
            "contains_raw_conversation": False,
            "contains_sensitive_data": False,
            "contains_credentials": False,
            "user_key_transferred": False,
            "task_session_key_transferred": False,
            "review_state": "EXPLICITLY_REVIEWED_FOR_PORTABLE_PROMOTION",
        },
        "authority": {
            "execution_authority": False,
            "policy_authority": False,
            "may_override_explicit_instruction": False,
            "may_relax_governance": False,
            "automatic_promotion": False,
        },
        "intake": {
            "destination_repository": "Baelfyre/Padayon",
            "state": "PENDING_GOVERNED_VALIDATION",
            "canonical_write_authorized": False,
            "created_at": created_at or _utc_now(),
        },
    }
    _validator(BRIDGE_SCHEMA).validate(envelope)
    return envelope


def _write(value: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output is None:
        print(payload, end="")
        return
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="A3 adaptive-shadow candidate JSON")
    parser.add_argument("--category", required=True, choices=CATEGORIES)
    parser.add_argument("--repository", action="append", default=[])
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--use-case", action="append", default=[])
    parser.add_argument("--specialist", action="append", default=[])
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--created-at")
    parser.add_argument("--privacy-reviewed", action="store_true", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    candidate = load_json(args.candidate)
    envelope = build_promotion_envelope(
        candidate,
        category=args.category,
        repositories=args.repository,
        projects=args.project,
        use_cases=args.use_case,
        specialists=args.specialist,
        tags=args.tag,
        created_at=args.created_at,
        privacy_reviewed=args.privacy_reviewed,
    )
    _write(envelope, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
