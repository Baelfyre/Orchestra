#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Validate AQ11 remediation-effectiveness pilot contract and repository parity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json"
REGISTRY_PATH = ROOT / "machine/governance/adapt-qa-phase-separation.v1.json"
README_PATH = ROOT / "README.json"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md"
EXACT_INVENTORY = (
    "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
    "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json",
    "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
    "orchestra_runtime/domain/adaptive/remediation_effectiveness.py",
    "scripts/validation/validate_aq11.py", "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq11.py",
)
REQUIRED_CLASSES = (
    "PROVENANCE_OWNERSHIP", "AGGREGATE_CONCURRENCY", "CALIBRATION_EVIDENCE_INTEGRITY",
    "AUTHORITY_BOUNDARY", "RUNTIME_INTEGRATION", "GATE_COVERAGE_TRUTHFULNESS",
)
AUTHORITY_KEYS = {
    "creates_execution_authority", "creates_transition_authority", "creates_whitelist_authority",
    "changes_protected_policy", "lowers_assurance_thresholds", "activates_provider",
    "activates_telemetry", "mutates_production", "authorizes_release",
    "authorizes_critiqual_cud10_admission",
}


def req(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: Any, message: str) -> dict[str, Any]:
    req(isinstance(value, dict), message)
    return value


def validate() -> None:
    contract = mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "AQ11 contract root must be object")
    schema = mapping(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), "AQ11 schema root must be object")
    req(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "AQ11 schema draft drift")
    req(schema.get("type") == "object" and schema.get("additionalProperties") is False, "AQ11 schema root must be strict object")
    props = mapping(schema.get("properties"), "AQ11 schema properties missing")
    constants = {
        "schema_version": "orchestra.aq11-remediation-effectiveness-pilot.v1",
        "phase": "AQ11_REMEDIATION_EFFECTIVENESS_PILOT",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }
    for key, expected in constants.items():
        req(contract.get(key) == expected, f"AQ11 contract {key} drift")
        req(mapping(props.get(key), f"AQ11 schema {key} missing").get("const") == expected, f"AQ11 schema {key} drift")
    req(tuple(contract.get("implementation_inventory", ())) == EXACT_INVENTORY, "AQ11 exact implementation inventory drift")
    req(tuple(contract.get("required_escape_classes", ())) == REQUIRED_CLASSES, "AQ11 required escape-class drift")
    boundary = mapping(contract.get("pilot_boundary"), "AQ11 pilot boundary missing")
    req(boundary.get("target_repository") == "Baelfyre/CritiQual", "AQ11 target repository drift")
    req(boundary.get("observed_canonical_sha") == "166bbac50a4f02e222aa15ff914c60cec658b7c0", "AQ11 CritiQual baseline drift")
    req(boundary.get("incident_reference") == "Baelfyre/Padayon#441", "AQ11 incident reference drift")
    req(boundary.get("mode") == "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT", "AQ11 mode drift")
    req(boundary.get("cud10_state") == "READY_NOT_STARTED_HELD_BY_CURRENT_USER", "AQ11 CUD10 hold drift")
    req(boundary.get("source_mutation_allowed") is False, "AQ11 cannot authorize CritiQual mutation")
    req(boundary.get("production_evidence_allowed") is False, "AQ11 cannot authorize production evidence")
    req(boundary.get("organic_effectiveness_claimed") is False, "AQ11 cannot claim organic effectiveness")
    policy = mapping(contract.get("effectiveness_policy"), "AQ11 effectiveness policy missing")
    req(policy.get("minimum_case_count") == 6 and policy.get("minimum_effectiveness_bps") == 10000, "AQ11 effectiveness threshold drift")
    req(policy.get("claim_scope") == "CONTROLLED_PILOT_ONLY", "AQ11 claim scope drift")
    refs = contract.get("reference_cases")
    req(isinstance(refs, list) and len(refs) == 6, "AQ11 reference-case count drift")
    req({item.get("escape_class") for item in refs if isinstance(item, dict)} == set(REQUIRED_CLASSES), "AQ11 reference cases must cover exact classes")
    authority = mapping(contract.get("authority"), "AQ11 authority missing")
    req(set(authority) == AUTHORITY_KEYS and all(value is False for value in authority.values()), "AQ11 authority must remain fully non-authorizing")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase = next((item for item in registry.get("phases", []) if item.get("phase_id") == "AQ11"), None)
    req(isinstance(phase, dict), "AQ11 phase registry entry missing")
    req(phase.get("status") == "HUMAN_APPROVED_REGISTERED", "AQ11 phase registry status drift")
    req(tuple(phase.get("implementation_paths", ())) == EXACT_INVENTORY, "AQ11 registered implementation inventory drift")

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))["machine_contracts"]
    expected_readme = {
        "adaptive_assurance_aq11_contract": "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json",
        "adaptive_assurance_aq11_schema": "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
        "adaptive_assurance_aq11_runtime": "orchestra_runtime/domain/adaptive/remediation_effectiveness.py",
        "adaptive_assurance_aq11_validator": "scripts/validation/validate_aq11.py",
        "adaptive_assurance_aq11_validation": "tests/runtime/test_adaptive_assurance_aq11.py",
        "adaptive_assurance_aq11_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
    }
    for key, expected in expected_readme.items():
        req(readme.get(key) == expected, f"README AQ11 reference drift: {key}")
    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    req('{"Name": "validate_aq11.py", "Path": "scripts/validation/validate_aq11.py"}' in run_tests, "AQ11 validator not registered in behavior suite")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in ("EVIDENCE_ONLY_NON_AUTHORIZING", "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT", "CUD10", "organic effectiveness", "Baelfyre/Padayon#441"):
        req(marker in doc, f"AQ11 architecture documentation missing {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AQ11_REMEDIATION_EFFECTIVENESS_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ11_REMEDIATION_EFFECTIVENESS_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
