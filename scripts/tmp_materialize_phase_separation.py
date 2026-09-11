#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DECISION_ID = "ORCHESTRA_ADAPT_QA_PHASE_SEPARATION_FRAMEWORK_AQ10_AQ14_HUMAN_POLICY_20260911"
AUTHORITY_URL = "https://github.com/Baelfyre/Padayon/blob/384f78dd27da52a3fff99fe40379ae3c3273e12f/projects/orchestra/10-approved/decisions/ADAPT_QA_Phase_Separation_Framework_AQ10_AQ14_Human_Policy_Decision_20260911.md"

PHASES = {
    "AQ10": [
        "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md",
        "machine/adaptive/aq10-defect-escape-rca.v1.json", "machine/schemas/aq10-defect-escape-rca.v1.schema.json",
        "orchestra_runtime/domain/adaptive/defect_escape_rca.py", "scripts/validation/validate_aq10.py",
        "tests/behavior/run_tests.py", "tests/runtime/test_adaptive_assurance_aq10.py",
    ],
    "AQ11": [
        "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
        "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json", "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
        "orchestra_runtime/domain/adaptive/remediation_effectiveness.py", "scripts/validation/validate_aq11.py",
        "tests/behavior/run_tests.py", "tests/runtime/test_adaptive_assurance_aq11.py",
    ],
    "AQ12": [
        "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",
        "machine/adaptive/aq12-adversarial-self-test.v1.json", "machine/schemas/aq12-adversarial-self-test.v1.schema.json",
        "orchestra_runtime/domain/adaptive/adversarial_self_test.py", "scripts/validation/validate_aq12.py",
        "tests/behavior/run_tests.py", "tests/runtime/test_adaptive_assurance_aq12.py",
    ],
    "AQ13": [
        "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md",
        "machine/adaptive/aq13-staged-rollout-evaluation.v1.json", "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json",
        "orchestra_runtime/domain/adaptive/staged_rollout.py", "scripts/validation/validate_aq13.py",
        "tests/behavior/run_tests.py", "tests/runtime/test_adaptive_assurance_aq13.py",
    ],
    "AQ14": [
        "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md",
        "machine/adaptive/aq14-effectiveness-qualification.v1.json", "machine/schemas/aq14-effectiveness-qualification.v1.schema.json",
        "orchestra_runtime/domain/adaptive/effectiveness_qualification.py", "scripts/validation/validate_aq14.py",
        "tests/behavior/run_tests.py", "tests/runtime/test_adaptive_assurance_aq14.py",
    ],
}

ANCHORS = {
    phase: [p for p in paths if p not in {"CHANGELOG.md", "README.json", "tests/behavior/run_tests.py"}]
    for phase, paths in PHASES.items()
}

registry = {
    "schema_version": "orchestra.adapt-qa-phase-separation.v1",
    "policy_id": DECISION_ID,
    "authority_class": "HUMAN_POLICY",
    "authority_source": AUTHORITY_URL,
    "historical_gates": ["prai", "aq5", "aq7"],
    "phases": [
        {
            "phase_id": phase,
            "status": "HUMAN_APPROVED_REGISTERED",
            "implementation_paths": paths,
            "anchor_paths": ANCHORS[phase],
        }
        for phase, paths in PHASES.items()
    ],
    "invariants": {
        "exact_registered_phase_set": "HISTORICAL_GATE_NOT_APPLICABLE_WHEN_PHASE_SEPARATION_REQUIRES_IT",
        "partial_registered_phase_set": "APPLICABLE",
        "registered_phase_superset": "APPLICABLE",
        "registered_phase_plus_unknown_path": "APPLICABLE",
        "unregistered_future_phase": "APPLICABLE",
        "duplicate_or_unsafe_path": "FAIL_CLOSED",
        "registry_mutation_authority": "HUMAN_POLICY",
        "phase_registration_is_lifecycle_whitelist": False,
        "phase_separation_is_assurance_bypass": False,
    },
}
(ROOT / "machine/governance/adapt-qa-phase-separation.v1.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/Baelfyre/Orchestra/machine/schemas/adapt-qa-phase-separation.v1.schema.json",
    "title": "Orchestra ADAPT-QA phase separation registry",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "policy_id", "authority_class", "authority_source", "historical_gates", "phases", "invariants"],
    "properties": {
        "schema_version": {"const": "orchestra.adapt-qa-phase-separation.v1"},
        "policy_id": {"type": "string", "minLength": 1},
        "authority_class": {"const": "HUMAN_POLICY"},
        "authority_source": {"type": "string", "minLength": 1},
        "historical_gates": {"type": "array", "uniqueItems": True, "items": {"enum": ["prai", "aq5", "aq7"]}, "minItems": 3, "maxItems": 3},
        "phases": {
            "type": "array", "minItems": 1, "uniqueItems": True,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["phase_id", "status", "implementation_paths", "anchor_paths"],
                "properties": {
                    "phase_id": {"type": "string", "pattern": "^AQ[0-9]+$"},
                    "status": {"const": "HUMAN_APPROVED_REGISTERED"},
                    "implementation_paths": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                    "anchor_paths": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                },
            },
        },
        "invariants": {"type": "object"},
    },
}
(ROOT / "machine/schemas/adapt-qa-phase-separation.v1.schema.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

policy = f'''# ADAPT-QA Phase Separation Policy\n\n**Policy authority:** `{DECISION_ID}`  \n**Authority class:** `HUMAN_POLICY`  \n**Canonical authority:** `{AUTHORITY_URL}`\n\n## Purpose\n\nThis policy provides a reusable, deterministic separation mechanism between historical exact-scope assurance inventories and later human-approved ADAPT-QA phases. It prevents complete later-phase work from being misclassified as a partial mutation of an earlier phase without weakening historical gates.\n\n## Deterministic rule\n\n```text\nEXACT COMPLETE REGISTERED PHASE INVENTORY -> NOT_APPLICABLE to historical exact inventories when phase separation is required\nPARTIAL / MIXED / SUPERSET / UNKNOWN / DUPLICATE -> APPLICABLE or FAIL CLOSED\nUNREGISTERED FUTURE PHASE -> APPLICABLE\n```\n\nThe machine registry is `machine/governance/adapt-qa-phase-separation.v1.json`. Registry mutation is protected `HUMAN_POLICY`; autonomous runs may consume approved entries but may not add or broaden them.\n\n## Registered phases\n\nAQ10 through AQ14 are registered exactly as approved by the primary maintainer. Each phase contains exactly nine implementation paths. Any implementation need outside the applicable inventory freezes that phase for fresh human review. AQ15 and later phases remain unregistered.\n\n## Non-authority\n\nPhase separation is not a lifecycle whitelist, assurance bypass, threshold reduction, release authority, deployment authority, provider authority, credential authority, telemetry authority, or production authority. PRAI, Covenant, specialist review, signed materialization, tree attestation, repository rulesets, and human-only whitelist boundaries remain unchanged.\n'''
(ROOT / "docs/governance/ADAPT_QA_PHASE_SEPARATION_POLICY.md").write_text(policy, encoding="utf-8")

classifier_path = ROOT / "scripts/validation/classify_adaptive_assurance_scope.py"
text = classifier_path.read_text(encoding="utf-8")
if "import json\n" not in text:
    text = text.replace("import argparse\n", "import argparse\nimport json\n")
if "from pathlib import Path\n" not in text:
    text = text.replace("from collections.abc import Iterable\n", "from collections.abc import Iterable\nfrom pathlib import Path\n")
marker = 'NOT_APPLICABLE = "NOT_APPLICABLE"\n'
insert = '''NOT_APPLICABLE = "NOT_APPLICABLE"\n\nROOT = Path(__file__).resolve().parents[2]\nADAPT_QA_PHASE_SEPARATION_REGISTRY_PATH = ROOT / "machine/governance/adapt-qa-phase-separation.v1.json"\n'''
if "ADAPT_QA_PHASE_SEPARATION_REGISTRY_PATH" not in text:
    text = text.replace(marker, insert, 1)

gov_marker = '        "machine/schemas/governance-policy.schema.json",\n'
if '"machine/governance/adapt-qa-phase-separation.v1.json"' not in text:
    text = text.replace(gov_marker, gov_marker + '        "machine/governance/adapt-qa-phase-separation.v1.json",\n        "machine/schemas/adapt-qa-phase-separation.v1.schema.json",\n', 1)

normalize_end = '''    if not normalized:\n        raise ValueError("at least one changed path is required")\n    return tuple(sorted(normalized))\n'''
loader = '''    if not normalized:\n        raise ValueError("at least one changed path is required")\n    return tuple(sorted(normalized))\n\n\ndef load_registered_phase_scopes() -> dict[str, tuple[frozenset[str], frozenset[str]]]:\n    try:\n        raw = json.loads(ADAPT_QA_PHASE_SEPARATION_REGISTRY_PATH.read_text(encoding="utf-8"))\n    except (OSError, json.JSONDecodeError) as exc:\n        raise ValueError(f"invalid ADAPT-QA phase separation registry: {{exc}}") from exc\n    if not isinstance(raw, dict) or raw.get("schema_version") != "orchestra.adapt-qa-phase-separation.v1":\n        raise ValueError("invalid ADAPT-QA phase separation registry schema_version")\n    if raw.get("authority_class") != "HUMAN_POLICY":\n        raise ValueError("ADAPT-QA phase separation registry must be HUMAN_POLICY")\n    phases = raw.get("phases")\n    if not isinstance(phases, list) or not phases:\n        raise ValueError("ADAPT-QA phase separation registry requires phases")\n    result: dict[str, tuple[frozenset[str], frozenset[str]]] = {{}}\n    for entry in phases:\n        if not isinstance(entry, dict):\n            raise ValueError("ADAPT-QA phase entry must be an object")\n        phase_id = entry.get("phase_id")\n        if not isinstance(phase_id, str) or not phase_id.startswith("AQ") or phase_id in result:\n            raise ValueError("ADAPT-QA phase_id must be unique AQ identifier")\n        implementation = frozenset(normalize_paths(entry.get("implementation_paths", ())))\n        anchors = frozenset(normalize_paths(entry.get("anchor_paths", ())))\n        if not anchors or not anchors.issubset(implementation):\n            raise ValueError(f"{{phase_id}} anchor_paths must be non-empty subset of implementation_paths")\n        result[phase_id] = (implementation, anchors)\n    return result\n'''
if "def load_registered_phase_scopes" not in text:
    if normalize_end not in text:
        raise SystemExit("normalize insertion marker missing")
    text = text.replace(normalize_end, loader, 1)

aq9_marker = '''    if normalized_set.intersection(AQ9_SCOPE_ANCHOR_PATHS):\n        return APPLICABLE\n'''
phase_logic = '''    if normalized_set.intersection(AQ9_SCOPE_ANCHOR_PATHS):\n        return APPLICABLE\n\n    # Human-approved reusable ADAPT-QA phase separation. Exact complete\n    # registered phase scopes are separated from historical inventories; any\n    # anchor-bearing subset or mixed/superset scope remains fail-closed.\n    for _phase_id, (registered_paths, anchor_paths) in load_registered_phase_scopes().items():\n        if normalized_set == registered_paths:\n            return NOT_APPLICABLE\n        if normalized_set.intersection(anchor_paths):\n            return APPLICABLE\n'''
if "registered phase scopes are separated" not in text:
    if aq9_marker not in text:
        raise SystemExit("AQ9 classifier marker missing")
    text = text.replace(aq9_marker, phase_logic, 1)
classifier_path.write_text(text, encoding="utf-8")

test_path = ROOT / "tests/behavior/test_protected_aq8_assurance_scope_policy.py"
test = test_path.read_text(encoding="utf-8")
if "load_registered_phase_scopes," not in test:
    test = test.replace("    classify_paths,\n", "    classify_paths,\n    load_registered_phase_scopes,\n", 1)

constant_marker = '''AQ9_POLICY_AMENDMENT_PATHS = (\n    "CHANGELOG.md",\n    "README.json",\n    "docs/governance/AQ9_ASSURANCE_SCOPE_POLICY.md",\n    "scripts/validation/classify_adaptive_assurance_scope.py",\n    "tests/behavior/test_protected_aq8_assurance_scope_policy.py",\n)\n'''
constants = constant_marker + '''\nADAPT_QA_PHASE_SEPARATION_POLICY_PATHS = (\n    "CHANGELOG.md",\n    "README.json",\n    "docs/governance/ADAPT_QA_PHASE_SEPARATION_POLICY.md",\n    "machine/governance/adapt-qa-phase-separation.v1.json",\n    "machine/schemas/adapt-qa-phase-separation.v1.schema.json",\n    "scripts/validation/classify_adaptive_assurance_scope.py",\n    "tests/behavior/test_protected_aq8_assurance_scope_policy.py",\n)\n'''
if "ADAPT_QA_PHASE_SEPARATION_POLICY_PATHS" not in test:
    if constant_marker not in test:
        raise SystemExit("test constant marker missing")
    test = test.replace(constant_marker, constants, 1)

func_marker = "\ndef test_historical_implementation_inventories_remain_separate() -> None:\n"
funcs = '''\ndef test_registered_aq10_aq14_exact_scopes_are_phase_separated() -> None:\n    registry = load_registered_phase_scopes()\n    _assert_equal("registered future phases", tuple(sorted(registry)), ("AQ10", "AQ11", "AQ12", "AQ13", "AQ14"))\n    for phase_id, (implementation, anchors) in registry.items():\n        _assert_equal(f"{{phase_id}} exact inventory size", len(implementation), 9)\n        _assert_equal(f"{{phase_id}} anchors subset", anchors.issubset(implementation), True)\n        for assurance in HISTORICAL_GATES:\n            _assert_equal(f"{{assurance}} {{phase_id}} exact scope", classify_paths(tuple(implementation), assurance), NOT_APPLICABLE)\n\n\ndef test_registered_future_phase_partial_and_superset_scopes_fail_closed() -> None:\n    registry = load_registered_phase_scopes()\n    for phase_id, (implementation, anchors) in registry.items():\n        anchor = sorted(anchors)[0]\n        partial = tuple(path for path in sorted(implementation) if path != sorted(implementation)[-1])\n        if anchor not in partial:\n            partial = ("CHANGELOG.md", anchor)\n        superset = (*tuple(sorted(implementation)), f"unexpected-{{phase_id.lower()}}-surface.txt")\n        for assurance in HISTORICAL_GATES:\n            _assert_equal(f"{{assurance}} {{phase_id}} partial", classify_paths(partial, assurance), APPLICABLE)\n            _assert_equal(f"{{assurance}} {{phase_id}} superset", classify_paths(superset, assurance), APPLICABLE)\n\n\ndef test_unregistered_aq15_remains_fail_closed() -> None:\n    future = ("CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ15.md")\n    for assurance in HISTORICAL_GATES:\n        _assert_equal(f"{{assurance}} AQ15 unregistered", classify_paths(future, assurance), APPLICABLE)\n\n\ndef test_phase_separation_policy_amendment_is_governance_only() -> None:\n    for assurance in HISTORICAL_GATES:\n        _assert_equal(\n            f"{{assurance}} reusable phase separation policy amendment",\n            classify_paths(ADAPT_QA_PHASE_SEPARATION_POLICY_PATHS, assurance),\n            NOT_APPLICABLE,\n        )\n\n'''
if "test_registered_aq10_aq14_exact_scopes_are_phase_separated" not in test:
    if func_marker not in test:
        raise SystemExit("test function insertion marker missing")
    test = test.replace(func_marker, funcs + func_marker, 1)

main_marker = '''    test_unregistered_future_aq_phase_remains_fail_closed()\n    test_historical_implementation_inventories_remain_separate()\n'''
main_replace = '''    test_unregistered_future_aq_phase_remains_fail_closed()\n    test_registered_aq10_aq14_exact_scopes_are_phase_separated()\n    test_registered_future_phase_partial_and_superset_scopes_fail_closed()\n    test_unregistered_aq15_remains_fail_closed()\n    test_phase_separation_policy_amendment_is_governance_only()\n    test_historical_implementation_inventories_remain_separate()\n'''
if "test_registered_aq10_aq14_exact_scopes_are_phase_separated()" not in test.split("def main() -> None:", 1)[-1]:
    if main_marker not in test:
        raise SystemExit("test main marker missing")
    test = test.replace(main_marker, main_replace, 1)
test_path.write_text(test, encoding="utf-8")

readme_path = ROOT / "README.json"
readme = readme_path.read_text(encoding="utf-8")
if '"adapt_qa_phase_separation_policy"' not in readme:
    cap_marker = '  "capabilities": {\n'
    entry = '''  "capabilities": {\n    "adapt_qa_phase_separation_policy": {\n      "status": "HUMAN_POLICY_CANONICALIZATION_CANDIDATE",\n      "purpose": "Deterministically separates exact human-approved later ADAPT-QA phase inventories from historical assurance inventories without weakening fail-closed behavior.",\n      "machine_sources": [\n        "machine/governance/adapt-qa-phase-separation.v1.json",\n        "machine/schemas/adapt-qa-phase-separation.v1.schema.json"\n      ],\n      "human_sources": [\n        "docs/governance/ADAPT_QA_PHASE_SEPARATION_POLICY.md"\n      ],\n      "registered_phases": ["AQ10", "AQ11", "AQ12", "AQ13", "AQ14"],\n      "registry_mutation_authority": "HUMAN_POLICY",\n      "unregistered_future_phases": "FAIL_CLOSED_APPLICABLE",\n      "authority_note": "Phase registration is not a lifecycle whitelist or assurance bypass; AQ15+ and inventory expansion require fresh human governance authority."\n    },\n'''
    if cap_marker not in readme:
        raise SystemExit("README capability marker missing")
    readme = readme.replace(cap_marker, entry, 1)
readme_path.write_text(readme, encoding="utf-8")

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
heading = "## Unreleased governance policy: reusable ADAPT-QA phase separation\n"
if not changelog.startswith(heading):
    note = f'''{heading}\n- Adds a human-authorized, data-driven phase registry for exact AQ10-AQ14 implementation inventories so historical PRAI/AQ5/AQ7 exact-scope gates can distinguish complete later phases without one-off classifier branches.\n- Keeps partial, mixed, superset, duplicate, unknown, and unregistered AQ15+ scopes fail-closed `APPLICABLE` or invalid.\n- Makes registry mutation protected `HUMAN_POLICY` under Padayon decision `{DECISION_ID}` at canonical commit `384f78dd27da52a3fff99fe40379ae3c3273e12f`.\n- Preserves all existing assurance thresholds, human-only whitelist authority, PRAI/Covenant/specialist boundaries, signed-materialization/tree-attestation controls, and release/deployment/provider/credential/telemetry/production boundaries.\n\n'''
    changelog = note + changelog
changelog_path.write_text(changelog, encoding="utf-8")

# Validate the registry's exact inventories before CI consumes it.
assert tuple(sorted(PHASES)) == ("AQ10", "AQ11", "AQ12", "AQ13", "AQ14")
assert all(len(paths) == 9 and len(set(paths)) == 9 for paths in PHASES.values())
print("ADAPT_QA_PHASE_SEPARATION_MATERIALIZED=PASS")
