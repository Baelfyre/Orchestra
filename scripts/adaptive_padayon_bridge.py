#!/usr/bin/env python3
"""Padayon reference adapter for Orchestra portable adaptive memory.

Orchestra's learning core is storage-agnostic. This adapter selects Padayon as
one optional GIT_JSON backend, emits a portable candidate, and never writes to
Padayon or marks the local A3 candidate promoted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema

from orchestra_runtime.adaptive.portable_memory import (
    CATEGORIES,
    MemoryBackendDescriptor,
    build_portable_memory_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
PADAYON_ADAPTER_SCHEMA = ROOT / "machine" / "schemas" / "padayon-memory-promotion-candidate.schema.json"
PADAYON_BACKEND = MemoryBackendDescriptor(
    backend_id="padayon",
    adapter_kind="GIT_JSON",
    record_format="JSON",
    config_ref="machine/adaptive/memory-backends.v1.json#padayon",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
    envelope = build_portable_memory_candidate(
        candidate,
        backend=PADAYON_BACKEND,
        category=category,
        repositories=repositories,
        projects=projects,
        use_cases=use_cases,
        specialists=specialists,
        tags=tags,
        created_at=created_at,
        privacy_reviewed=privacy_reviewed,
    )
    schema = load_json(PADAYON_ADAPTER_SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(envelope)
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

    envelope = build_promotion_envelope(
        load_json(args.candidate),
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
