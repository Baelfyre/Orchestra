#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "machine" / "knowledge" / "truesheet-specialist-reference.v1.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FEATURE_RE = re.compile(r"TSF-[0-9]{3}")
EXPECTED_SPECIALISTS = {"cloak", "ponytail", "clockwork", "overseer", "scribe"}


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != "orchestra.truesheet-specialist-reference.v1":
        fail("unexpected TrueSheet machine catalog schema")
    if catalog.get("status") != "ACTIVE_ORCHESTRA_NATIVE_REFERENCE":
        fail("TrueSheet machine catalog must remain active")
    if catalog.get("authority_class") != "EXTERNAL_REFERENCE_ONLY":
        fail("external reference must not become Orchestra authority")

    padayon = catalog.get("canonical_padayon_reference", {})
    if padayon.get("repository") != "Baelfyre/Padayon":
        fail("wrong Padayon provenance repository")
    if padayon.get("canonical_commit") != "1fa5b773b04877bcbc3b85e22b6af70a0a8dd738":
        fail("wrong canonical Padayon TrueSheet reference commit")
    if not str(padayon.get("record_path", "")).endswith("Orchestra_TrueSheet_External_Knowledge_Reference_V2.json"):
        fail("wrong canonical Padayon machine record path")

    source = catalog.get("external_source", {})
    if source.get("repository") != "lodev09/react-native-true-sheet":
        fail("wrong external source repository")
    if source.get("reviewed_commit") != "23e119c026e2040d960725bd260e6cd4bf680b95":
        fail("wrong external source commit")
    if source.get("license") != "MIT":
        fail("TrueSheet license must remain MIT in the reviewed reference")
    if source.get("source_drift_at_last_reverification") is not False:
        fail("active catalog cannot claim unresolved source drift")
    if source.get("copied_source_code") is not False or source.get("wholesale_material_copied") is not False:
        fail("Orchestra-native adaptation must not copy source code or wholesale material")

    policy = catalog.get("adaptation_policy", {})
    expected_false = {
        "external_agent_instructions_are_not_orchestra_governance": True,
        "external_test_results_are_not_orchestra_validation_evidence": True,
        "runtime_dependency_added": False,
        "specialist_authority_expanded": False,
    }
    for key, expected in expected_false.items():
        if policy.get(key) is not expected:
            fail(f"adaptation policy changed: {key}")
    if policy.get("conductor_role") != "ROUTING_ONLY":
        fail("Conductor must remain routing-only")
    if policy.get("the_tuner_role") != "CROSS_SPECIALIST_COORDINATION_ONLY":
        fail("The Tuner must remain coordination-only")
    if policy.get("mcp_role") != "NOT_IMPLEMENTED_DEFERRED_FINAL_INTEGRATION_PHASE":
        fail("MCP sequencing boundary changed")

    feature_titles = catalog.get("feature_titles")
    if not isinstance(feature_titles, dict) or len(feature_titles) != 18:
        fail("machine catalog must contain exactly 18 canonical feature IDs")
    expected_features = {f"TSF-{index:03d}" for index in range(1, 19)}
    if set(feature_titles) != expected_features:
        fail("machine feature ID set is incomplete or unexpected")

    specialists = catalog.get("specialists")
    if not isinstance(specialists, dict) or set(specialists) != EXPECTED_SPECIALISTS:
        fail("specialist mapping must contain exactly the five approved specialists")

    for specialist, entry in specialists.items():
        guide = entry.get("guide")
        ids = entry.get("feature_ids")
        if not isinstance(guide, str) or not isinstance(ids, list) or not ids:
            fail(f"invalid specialist mapping: {specialist}")
        if not set(ids) <= expected_features:
            fail(f"specialist {specialist} references undeclared feature IDs")
        source_path = ROOT / guide
        codex_path = ROOT / "adapters" / "codex" / guide
        if not source_path.exists():
            fail(f"missing source specialist guide: {guide}")
        if not codex_path.exists():
            fail(f"missing Codex specialist guide: adapters/codex/{guide}")
        source_text = source_path.read_text(encoding="utf-8")
        codex_text = codex_path.read_text(encoding="utf-8")
        if source_text != codex_text:
            fail(f"source/Codex guide parity mismatch: {specialist}")
        guide_ids = set(FEATURE_RE.findall(source_text))
        if guide_ids != set(ids):
            fail(f"guide feature-ID parity mismatch for {specialist}: {sorted(guide_ids ^ set(ids))}")
        if "machine/knowledge/truesheet-specialist-reference.v1.json" not in source_text:
            fail(f"guide does not point back to machine authority: {specialist}")
        if source.get("reviewed_commit") not in source_text or "MIT" not in source_text:
            fail(f"guide provenance mismatch: {specialist}")

    for forbidden in (
        ROOT / "skills" / "conductor" / "TRUESHEET_REFERENCE.md",
        ROOT / "skills" / "the-tuner" / "TRUESHEET_REFERENCE.md",
        ROOT / "adapters" / "codex" / "skills" / "conductor" / "TRUESHEET_REFERENCE.md",
        ROOT / "adapters" / "codex" / "skills" / "the-tuner" / "TRUESHEET_REFERENCE.md",
    ):
        if forbidden.exists():
            fail(f"routing/coordination role must not receive duplicated TrueSheet knowledge: {forbidden.relative_to(ROOT)}")

    print("TRUESHEET_SPECIALIST_REFERENCE=PASS")
    print(f"FEATURES={len(feature_titles)} SPECIALISTS={len(specialists)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError, OSError) as exc:
        print(f"TRUESHEET_SPECIALIST_REFERENCE=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
