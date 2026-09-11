#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Validate AQ13 staged non-production rollout contract and repository parity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq13-staged-rollout-evaluation.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json"
REGISTRY_PATH = ROOT / "machine/governance/adapt-qa-phase-separation.v1.json"
README_PATH = ROOT / "README.json"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md"
EXACT_INVENTORY = (
    "CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md",
    "machine/adaptive/aq13-staged-rollout-evaluation.v1.json",
    "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json",
    "orchestra_runtime/domain/adaptive/staged_rollout.py",
    "scripts/validation/validate_aq13.py", "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq13.py",
)
REQUIRED_STAGES = (
    ("SHADOW", 1, 10),
    ("CANARY", 2, 10),
    ("LIMITED", 3, 10),
    ("EXPANDED", 4, 10),
)
AUTHORITY_KEYS = {
    "creates_execution_authority", "creates_transition_authority", "creates_whitelist_authority",
    "changes_protected_policy", "lowers_assurance_thresholds", "activates_provider",
    "activates_telemetry", "mutates_production", "authorizes_release",
    "authorizes_critiqual_cud10_admission",
}
BASE = "2fc2d9ce9fc263813981e4dc8c88d1e4f604f036"


def req(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: Any, message: str) -> dict[str, Any]:
    req(isinstance(value, dict), message)
    return value


def validate() -> None:
    contract = mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "AQ13 contract root must be object")
    schema = mapping(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), "AQ13 schema root must be object")
    req(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "AQ13 schema draft drift")
    req(schema.get("type") == "object" and schema.get("additionalProperties") is False, "AQ13 schema root must be strict object")
    props = mapping(schema.get("properties"), "AQ13 schema properties missing")
    constants = {
        "schema_version": "orchestra.aq13-staged-rollout-evaluation.v1",
        "phase": "AQ13_STAGED_NON_PRODUCTION_ROLLOUT_EVALUATION",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }
    for key, expected in constants.items():
        req(contract.get(key) == expected, f"AQ13 contract {key} drift")
        req(mapping(props.get(key), f"AQ13 schema {key} missing").get("const") == expected, f"AQ13 schema {key} drift")
    req(tuple(contract.get("implementation_inventory", ())) == EXACT_INVENTORY, "AQ13 exact implementation inventory drift")

    boundary = mapping(contract.get("rollout_boundary"), "AQ13 rollout boundary missing")
    req(boundary.get("target_repository") == "Baelfyre/Orchestra", "AQ13 target repository drift")
    req(boundary.get("canonical_start_sha") == BASE, "AQ13 canonical start drift")
    req(boundary.get("mode") == "CONTROLLED_NON_PRODUCTION_STAGED_ROLLOUT_EVALUATION", "AQ13 mode drift")
    req(boundary.get("environment_scope") == "NON_PRODUCTION_ONLY", "AQ13 environment scope drift")
    req(boundary.get("cud10_state") == "READY_NOT_STARTED_HELD_BY_CURRENT_USER", "AQ13 CUD10 hold drift")
    for key in (
        "protected_policy_mutation_allowed", "production_mutation_allowed", "provider_activation_allowed",
        "telemetry_activation_allowed", "release_or_deploy_allowed",
    ):
        req(boundary.get(key) is False, f"AQ13 boundary must keep {key}=false")

    stages = contract.get("required_stages")
    req(isinstance(stages, list) and len(stages) == 4, "AQ13 required-stage count drift")
    observed_stages = tuple(
        (item.get("stage_id"), item.get("sequence"), item.get("minimum_observations"))
        for item in stages if isinstance(item, dict)
    )
    req(observed_stages == REQUIRED_STAGES, "AQ13 staged rollout order or minimum evidence drift")

    policy = mapping(contract.get("rollout_policy"), "AQ13 rollout policy missing")
    req(policy.get("minimum_total_observations") == 40, "AQ13 minimum total observations drift")
    req(policy.get("maximum_regression_rate_bps") == 500, "AQ13 regression threshold drift")
    req(policy.get("maximum_critical_violations") == 0, "AQ13 critical threshold drift")
    req(policy.get("independent_evidence_required") is True, "AQ13 independent evidence requirement drift")
    req(policy.get("deterministic_replay_required") is True, "AQ13 deterministic replay requirement drift")
    req(policy.get("rollback_on_any_critical_violation") is True, "AQ13 critical rollback rule drift")
    req(policy.get("rollback_signal_forces_hold") is True, "AQ13 rollback hold rule drift")
    req(policy.get("claim_scope") == "CONTROLLED_NON_PRODUCTION_EVALUATION_ONLY", "AQ13 claim scope drift")
    req(tuple(contract.get("disposition_precedence", ())) == ("REVISION_REQUIRED", "HOLD", "WAIT_FOR_EVIDENCE", "PASS"), "AQ13 disposition precedence drift")

    authority = mapping(contract.get("authority"), "AQ13 authority missing")
    req(set(authority) == AUTHORITY_KEYS and all(value is False for value in authority.values()), "AQ13 authority must remain fully non-authorizing")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase = next((item for item in registry.get("phases", []) if item.get("phase_id") == "AQ13"), None)
    req(isinstance(phase, dict), "AQ13 phase registry entry missing")
    req(phase.get("status") == "HUMAN_APPROVED_REGISTERED", "AQ13 phase registry status drift")
    req(tuple(phase.get("implementation_paths", ())) == EXACT_INVENTORY, "AQ13 registered implementation inventory drift")

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))["machine_contracts"]
    expected_readme = {
        "adaptive_assurance_aq13_contract": "machine/adaptive/aq13-staged-rollout-evaluation.v1.json",
        "adaptive_assurance_aq13_schema": "machine/schemas/aq13-staged-rollout-evaluation.v1.schema.json",
        "adaptive_assurance_aq13_runtime": "orchestra_runtime/domain/adaptive/staged_rollout.py",
        "adaptive_assurance_aq13_validator": "scripts/validation/validate_aq13.py",
        "adaptive_assurance_aq13_validation": "tests/runtime/test_adaptive_assurance_aq13.py",
        "adaptive_assurance_aq13_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ13.md",
    }
    for key, expected in expected_readme.items():
        req(readme.get(key) == expected, f"README AQ13 reference drift: {key}")

    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    req('{"Name": "validate_aq13.py", "Path": "scripts/validation/validate_aq13.py"}' in run_tests, "AQ13 validator not registered in behavior suite")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "EVIDENCE_ONLY_NON_AUTHORIZING", "CONTROLLED_NON_PRODUCTION_STAGED_ROLLOUT_EVALUATION",
        "CUD10", "rollback", "Prime Directive", "SHADOW", "CANARY", "LIMITED", "EXPANDED",
    ):
        req(marker in doc, f"AQ13 architecture documentation missing {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AQ13_STAGED_ROLLOUT_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ13_STAGED_ROLLOUT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
