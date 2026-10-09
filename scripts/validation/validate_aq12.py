#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Validate AQ12 adversarial self-test contract and repository parity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq12-adversarial-self-test.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq12-adversarial-self-test.v1.schema.json"
REGISTRY_PATH = ROOT / "machine/governance/adapt-qa-phase-separation.v1.json"
README_PATH = ROOT / "README.json"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md"
EXACT_INVENTORY = (
    "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",
    "machine/adaptive/aq12-adversarial-self-test.v1.json",
    "machine/schemas/aq12-adversarial-self-test.v1.schema.json",
    "orchestra_runtime/domain/adaptive/adversarial_self_test.py",
    "scripts/validation/validate_aq12.py", "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq12.py",
)
REQUIRED_CLASSES = (
    "SCOPE_DRIFT", "AUTHORITY_ESCALATION", "EVIDENCE_TAMPERING",
    "STATE_TRANSITION_FORGERY", "ASSURANCE_GATE_BYPASS", "DETERMINISM_DRIFT",
)
EXPECTED_CONTROLS = {
    "SCOPE_DRIFT": "PHASE_REGISTRY_FAIL_CLOSED",
    "AUTHORITY_ESCALATION": "EXPLICIT_AUTHORITY_BOUNDARY",
    "EVIDENCE_TAMPERING": "EVIDENCE_IDENTITY_AND_INTEGRITY",
    "STATE_TRANSITION_FORGERY": "ARBITER_TRANSITION_OWNERSHIP",
    "ASSURANCE_GATE_BYPASS": "PROTECTED_ASSURANCE_GATES",
    "DETERMINISM_DRIFT": "DETERMINISTIC_REPLAY_PARITY",
}
AUTHORITY_KEYS = {
    "creates_execution_authority", "creates_transition_authority", "creates_whitelist_authority",
    "changes_protected_policy", "lowers_assurance_thresholds", "activates_provider",
    "activates_telemetry", "mutates_production", "authorizes_release",
    "authorizes_critiqual_cud10_admission",
}
BASE = "34c7fcf45ee42db92289479c1ec8e0b425af29e7"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: Any, message: str) -> dict[str, Any]:
    req(isinstance(value, dict), message)
    return value


def validate() -> None:
    contract = mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "AQ12 contract root must be object")
    schema = mapping(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), "AQ12 schema root must be object")
    req(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "AQ12 schema draft drift")
    req(schema.get("type") == "object" and schema.get("additionalProperties") is False, "AQ12 schema root must be strict object")
    props = mapping(schema.get("properties"), "AQ12 schema properties missing")
    constants = {
        "schema_version": "orchestra.aq12-adversarial-self-test.v1",
        "phase": "AQ12_ORCHESTRA_ADVERSARIAL_SELF_TEST",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }
    for key, expected in constants.items():
        req(contract.get(key) == expected, f"AQ12 contract {key} drift")
        req(mapping(props.get(key), f"AQ12 schema {key} missing").get("const") == expected, f"AQ12 schema {key} drift")
    req(tuple(contract.get("implementation_inventory", ())) == EXACT_INVENTORY, "AQ12 exact implementation inventory drift")
    req(tuple(contract.get("required_attack_classes", ())) == REQUIRED_CLASSES, "AQ12 required attack-class drift")

    boundary = mapping(contract.get("self_test_boundary"), "AQ12 self-test boundary missing")
    req(boundary.get("target_repository") == "Baelfyre/Orchestra", "AQ12 target repository drift")
    req(boundary.get("canonical_start_sha") == BASE, "AQ12 canonical start drift")
    req(boundary.get("mode") == "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST", "AQ12 mode drift")
    req(boundary.get("cud10_state") == "READY_NOT_STARTED_HELD_BY_CURRENT_USER", "AQ12 CUD10 hold drift")
    for key in (
        "protected_policy_mutation_allowed", "production_mutation_allowed", "provider_activation_allowed",
        "telemetry_activation_allowed", "release_or_deploy_allowed",
    ):
        req(boundary.get(key) is False, f"AQ12 boundary must keep {key}=false")

    policy = mapping(contract.get("test_policy"), "AQ12 test policy missing")
    req(policy.get("minimum_case_count") == 6 and policy.get("minimum_effectiveness_bps") == 10000, "AQ12 effectiveness threshold drift")
    req(policy.get("independent_evidence_required") is True, "AQ12 independent evidence requirement drift")
    req(policy.get("deterministic_replay_required") is True, "AQ12 deterministic replay requirement drift")
    req(policy.get("claim_scope") == "CONTROLLED_SELF_TEST_ONLY", "AQ12 claim scope drift")

    refs = contract.get("reference_cases")
    req(isinstance(refs, list) and len(refs) == 6, "AQ12 reference-case count drift")
    req({item.get("attack_class") for item in refs if isinstance(item, dict)} == set(REQUIRED_CLASSES), "AQ12 reference cases must cover exact classes")
    for item in refs:
        req(isinstance(item, dict), "AQ12 reference case must be object")
        req(item.get("expected_control") == EXPECTED_CONTROLS[item.get("attack_class")], "AQ12 reference control drift")

    authority = mapping(contract.get("authority"), "AQ12 authority missing")
    req(set(authority) == AUTHORITY_KEYS and all(value is False for value in authority.values()), "AQ12 authority must remain fully non-authorizing")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase = next((item for item in registry.get("phases", []) if item.get("phase_id") == "AQ12"), None)
    req(isinstance(phase, dict), "AQ12 phase registry entry missing")
    req(phase.get("status") == "HUMAN_APPROVED_REGISTERED", "AQ12 phase registry status drift")
    req(tuple(phase.get("implementation_paths", ())) == EXACT_INVENTORY, "AQ12 registered implementation inventory drift")

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))["machine_contracts"]
    expected_readme = {
        "adaptive_assurance_aq12_contract": "machine/adaptive/aq12-adversarial-self-test.v1.json",
        "adaptive_assurance_aq12_schema": "machine/schemas/aq12-adversarial-self-test.v1.schema.json",
        "adaptive_assurance_aq12_runtime": "orchestra_runtime/domain/adaptive/adversarial_self_test.py",
        "adaptive_assurance_aq12_validator": "scripts/validation/validate_aq12.py",
        "adaptive_assurance_aq12_validation": "tests/runtime/test_adaptive_assurance_aq12.py",
        "adaptive_assurance_aq12_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",
    }
    for key, expected in expected_readme.items():
        req(readme.get(key) == expected, f"README AQ12 reference drift: {key}")

    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    req('{"Name": "validate_aq12.py", "Path": "scripts/validation/validate_aq12.py"}' in run_tests, "AQ12 validator not registered in behavior suite")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "EVIDENCE_ONLY_NON_AUTHORIZING", "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST",
        "CUD10", "deterministic replay", "Prime Directive",
    ):
        req(marker in doc, f"AQ12 architecture documentation missing {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AQ12_ADVERSARIAL_SELF_TEST_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ12_ADVERSARIAL_SELF_TEST_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
