#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Validate AQ14 final effectiveness qualification contract and repository parity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq14-effectiveness-qualification.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq14-effectiveness-qualification.v1.schema.json"
REGISTRY_PATH = ROOT / "machine/governance/adapt-qa-phase-separation.v1.json"
README_PATH = ROOT / "README.json"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md"
EXACT_INVENTORY = (
    "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md",
    "machine/adaptive/aq14-effectiveness-qualification.v1.json",
    "machine/schemas/aq14-effectiveness-qualification.v1.schema.json",
    "orchestra_runtime/domain/adaptive/effectiveness_qualification.py",
    "scripts/validation/validate_aq14.py", "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq14.py",
)
REQUIRED_PHASES = ("AQ9", "AQ10", "AQ11", "AQ12", "AQ13")
EXPECTED_IDENTITIES = {
    "AQ9": (907, "b5b6e1761e9ebf265e3e2b3ffbfc17a52c6c99b3", "ac90102a77339baff72b5ca52e512885e47f2819"),
    "AQ10": (913, "2fa5d648b5b19d483ecbe2342f5a28927a85d28f", "e9199f374d5c6b1f32b3c52f826e0141d021b4d3"),
    "AQ11": (916, "34c7fcf45ee42db92289479c1ec8e0b425af29e7", "6832c5050a5319876cded35e4a206dc44c10b050"),
    "AQ12": (919, "2fc2d9ce9fc263813981e4dc8c88d1e4f604f036", "85681748eb895898d8c941c69b0ddd5da1da754c"),
    "AQ13": (922, "34eb2a38a97f6d1acef6bbd206da8795393457de", "60e8410e0031f2977c920f429afccad5f983ce2a"),
}
AUTHORITY_KEYS = {
    "creates_execution_authority", "creates_transition_authority", "creates_whitelist_authority",
    "changes_protected_policy", "lowers_assurance_thresholds", "activates_provider",
    "activates_telemetry", "mutates_production", "authorizes_release", "authorizes_aq15",
    "authorizes_critiqual_cud10_admission",
}
BASE = "34eb2a38a97f6d1acef6bbd206da8795393457de"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: Any, message: str) -> dict[str, Any]:
    req(isinstance(value, dict), message)
    return value


def validate() -> None:
    contract = mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "AQ14 contract root must be object")
    schema = mapping(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), "AQ14 schema root must be object")
    req(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "AQ14 schema draft drift")
    req(schema.get("type") == "object" and schema.get("additionalProperties") is False, "AQ14 schema root must be strict object")
    props = mapping(schema.get("properties"), "AQ14 schema properties missing")
    constants = {
        "schema_version": "orchestra.aq14-effectiveness-qualification.v1",
        "phase": "AQ14_FINAL_ADAPT_QA_EFFECTIVENESS_QUALIFICATION",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }
    for key, expected in constants.items():
        req(contract.get(key) == expected, f"AQ14 contract {key} drift")
        req(mapping(props.get(key), f"AQ14 schema {key} missing").get("const") == expected, f"AQ14 schema {key} drift")

    req(tuple(contract.get("implementation_inventory", ())) == EXACT_INVENTORY, "AQ14 exact implementation inventory drift")
    req(tuple(contract.get("required_phases", ())) == REQUIRED_PHASES, "AQ14 required phase order drift")

    boundary = mapping(contract.get("qualification_boundary"), "AQ14 qualification boundary missing")
    req(boundary.get("target_repository") == "Baelfyre/Orchestra", "AQ14 target repository drift")
    req(boundary.get("canonical_start_sha") == BASE, "AQ14 canonical start drift")
    req(boundary.get("mode") == "CONTROLLED_NON_PRODUCTION_FINAL_EFFECTIVENESS_QUALIFICATION", "AQ14 mode drift")
    req(boundary.get("cud10_state") == "READY_NOT_STARTED_HELD_BY_CURRENT_USER", "AQ14 CUD10 hold drift")
    for key in (
        "protected_policy_mutation_allowed", "production_mutation_allowed", "provider_activation_allowed",
        "telemetry_activation_allowed", "release_or_deploy_allowed", "aq15_authorization_allowed",
    ):
        req(boundary.get(key) is False, f"AQ14 boundary must keep {key}=false")

    phase_evidence = contract.get("phase_evidence")
    req(isinstance(phase_evidence, list) and len(phase_evidence) == 5, "AQ14 phase evidence count drift")
    req(tuple(item.get("phase_id") for item in phase_evidence if isinstance(item, dict)) == REQUIRED_PHASES, "AQ14 phase evidence order drift")
    for item in phase_evidence:
        req(isinstance(item, dict), "AQ14 phase evidence must be object")
        phase = item.get("phase_id")
        expected = EXPECTED_IDENTITIES.get(phase)
        req(expected is not None, "AQ14 unknown phase evidence")
        req((item.get("canonical_pr"), item.get("canonical_sha"), item.get("canonical_tree")) == expected, f"AQ14 {phase} canonical identity drift")
        req(item.get("required_disposition") == "PASS", f"AQ14 {phase} required disposition drift")

    policy = mapping(contract.get("qualification_policy"), "AQ14 qualification policy missing")
    req(policy.get("minimum_phase_count") == 5, "AQ14 phase-count threshold drift")
    for key in (
        "canonical_identity_required", "source_assurance_required", "promotion_assurance_required",
        "post_merge_assurance_required", "independent_evidence_required", "deterministic_evidence_required",
    ):
        req(policy.get(key) is True, f"AQ14 must keep {key}=true")
    req(policy.get("maximum_unresolved_critical_findings") == 0, "AQ14 critical finding ceiling drift")
    req(tuple(policy.get("disposition_precedence", ())) == ("REVISION_REQUIRED", "WAIT_FOR_EVIDENCE", "PASS"), "AQ14 disposition precedence drift")
    req(policy.get("claim_scope") == "CONTROLLED_ADAPT_QA_EVIDENCE_CHAIN_ONLY", "AQ14 claim scope drift")
    req(policy.get("organic_effectiveness_claim_allowed") is False, "AQ14 cannot claim organic effectiveness")
    req(policy.get("production_readiness_claim_allowed") is False, "AQ14 cannot claim production readiness")

    authority = mapping(contract.get("authority"), "AQ14 authority missing")
    req(set(authority) == AUTHORITY_KEYS and all(value is False for value in authority.values()), "AQ14 authority must remain fully non-authorizing")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase = next((item for item in registry.get("phases", []) if item.get("phase_id") == "AQ14"), None)
    req(isinstance(phase, dict), "AQ14 phase registry entry missing")
    req(phase.get("status") == "HUMAN_APPROVED_REGISTERED", "AQ14 phase registry status drift")
    req(tuple(phase.get("implementation_paths", ())) == EXACT_INVENTORY, "AQ14 registered implementation inventory drift")

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))["machine_contracts"]
    expected_readme = {
        "adaptive_assurance_aq14_contract": "machine/adaptive/aq14-effectiveness-qualification.v1.json",
        "adaptive_assurance_aq14_schema": "machine/schemas/aq14-effectiveness-qualification.v1.schema.json",
        "adaptive_assurance_aq14_runtime": "orchestra_runtime/domain/adaptive/effectiveness_qualification.py",
        "adaptive_assurance_aq14_validator": "scripts/validation/validate_aq14.py",
        "adaptive_assurance_aq14_validation": "tests/runtime/test_adaptive_assurance_aq14.py",
        "adaptive_assurance_aq14_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ14.md",
    }
    for key, expected in expected_readme.items():
        req(readme.get(key) == expected, f"README AQ14 reference drift: {key}")

    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    req('{"Name": "validate_aq14.py", "Path": "scripts/validation/validate_aq14.py"}' in run_tests, "AQ14 validator not registered in behavior suite")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "EVIDENCE_ONLY_NON_AUTHORIZING",
        "CONTROLLED_NON_PRODUCTION_FINAL_EFFECTIVENESS_QUALIFICATION",
        "AQ15",
        "CUD10",
        "Prime Directive",
        "production-readiness",
    ):
        req(marker in doc, f"AQ14 architecture documentation missing {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AQ14_EFFECTIVENESS_QUALIFICATION_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ14_EFFECTIVENESS_QUALIFICATION_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
