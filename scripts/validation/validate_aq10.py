#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
# @codebase_verified_JEO
"""Validate AQ10 defect-escape RCA contract and repository parity."""

from __future__ import annotations

from json import JSONDecodeError
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq10-defect-escape-rca.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq10-defect-escape-rca.v1.schema.json"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
README_PATH = ROOT / "README.json"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md"
RUNTIME_PATH = ROOT / "orchestra_runtime/domain/adaptive/defect_escape_rca.py"

EXACT_INVENTORY = (
    "CHANGELOG.md",
    "README.json",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md",
    "machine/adaptive/aq10-defect-escape-rca.v1.json",
    "machine/schemas/aq10-defect-escape-rca.v1.schema.json",
    "orchestra_runtime/domain/adaptive/defect_escape_rca.py",
    "scripts/validation/validate_aq10.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq10.py",
)
CAUSES = (
    "COVERAGE_GAP",
    "ASSERTION_GAP",
    "ORACLE_GAP",
    "SCOPE_CLASSIFICATION_GAP",
    "DEPENDENCY_ENVIRONMENT_GAP",
    "ASSURANCE_TOOL_COMPATIBILITY",
    "PROCESS_GOVERNANCE_GAP",
    "UNKNOWN",
)
SIGNAL_MAP = {
    "MISSING_TEST_SURFACE": "COVERAGE_GAP",
    "UNEXERCISED_BRANCH": "COVERAGE_GAP",
    "WEAK_ASSERTION": "ASSERTION_GAP",
    "MISSING_NEGATIVE_ASSERTION": "ASSERTION_GAP",
    "WRONG_EXPECTED_RESULT": "ORACLE_GAP",
    "SELF_ASSERTED_PASS": "ORACLE_GAP",
    "INCORRECT_SCOPE_CLASSIFICATION": "SCOPE_CLASSIFICATION_GAP",
    "UNREGISTERED_PHASE_COLLISION": "SCOPE_CLASSIFICATION_GAP",
    "MISSING_OPTIONAL_DEPENDENCY": "DEPENDENCY_ENVIRONMENT_GAP",
    "ENVIRONMENT_PARITY_MISMATCH": "DEPENDENCY_ENVIRONMENT_GAP",
    "MUTATION_OPERATOR_CRASH": "ASSURANCE_TOOL_COMPATIBILITY",
    "ASSURANCE_TOOL_INCOMPATIBILITY": "ASSURANCE_TOOL_COMPATIBILITY",
    "MISSING_GOVERNANCE_CONTRACT": "PROCESS_GOVERNANCE_GAP",
    "STALE_TRANSACTION_METADATA": "PROCESS_GOVERNANCE_GAP",
    "STALE_RELAY_PROJECTION": "PROCESS_GOVERNANCE_GAP",
    "CAUSE_UNRESOLVED": "UNKNOWN",
}
PREVENTION = {
    "COVERAGE_GAP": ["EXPAND_TARGETED_TEST_COVERAGE"],
    "ASSERTION_GAP": ["STRENGTHEN_ASSERTIONS_AND_NEGATIVE_CASES"],
    "ORACLE_GAP": ["INDEPENDENT_ORACLE_CROSS_CHECK"],
    "SCOPE_CLASSIFICATION_GAP": ["EXACT_SCOPE_REGRESSION_AND_FAIL_CLOSED_CLASSIFICATION"],
    "DEPENDENCY_ENVIRONMENT_GAP": ["DEPENDENCY_FREE_BEHAVIOR_VALIDATION_OR_EXPLICIT_RUNTIME_DEPENDENCY"],
    "ASSURANCE_TOOL_COMPATIBILITY": ["TOOL_COMPATIBILITY_REGRESSION_WITH_UNKNOWN_OUTCOME_FAIL_CLOSED"],
    "PROCESS_GOVERNANCE_GAP": ["CONTRACT_PARITY_AND_COMPILER_GENERATED_RECONCILIATION"],
    "UNKNOWN": ["HUMAN_RCA_REVIEW_REQUIRED"],
}
FAIL_CLOSED = (
    "UNKNOWN_SIGNAL_REJECTED",
    "DUPLICATE_IDENTITY_REJECTED",
    "MALFORMED_OBSERVATION_REJECTED",
    "UNRESOLVED_CAUSE_REQUIRES_HUMAN_REVIEW",
    "NO_AUTOMATIC_POLICY_CHANGE",
)
AUTHORITY_KEYS = {
    "creates_execution_authority",
    "creates_transition_authority",
    "creates_whitelist_authority",
    "changes_protected_policy",
    "lowers_assurance_thresholds",
    "activates_provider",
    "activates_telemetry",
    "mutates_production",
    "authorizes_release",
}
CONTRACT_KEYS = {
    "schema_version",
    "phase",
    "owner",
    "authority_model",
    "purpose",
    "implementation_inventory",
    "taxonomy",
    "signal_map",
    "prevention_actions",
    "reference_incidents",
    "fail_closed_conditions",
    "authority",
    "validation",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _mapping(value: Any, message: str) -> dict[str, Any]:
    _require(isinstance(value, dict), message)
    return value


def validate() -> None:
    contract = _mapping(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), "AQ10 contract root must be an object")
    schema = _mapping(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), "AQ10 schema root must be an object")

    _require(set(contract) == CONTRACT_KEYS, "AQ10 contract top-level key drift")
    _require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "AQ10 schema draft drift")
    _require(schema.get("type") == "object", "AQ10 schema root type drift")
    _require(schema.get("additionalProperties") is False, "AQ10 schema must reject unknown root properties")
    _require(set(schema.get("required", ())) == CONTRACT_KEYS, "AQ10 schema required-key drift")
    properties = _mapping(schema.get("properties"), "AQ10 schema properties must be an object")
    _require(set(properties) == CONTRACT_KEYS, "AQ10 schema property-key drift")

    expected_constants = {
        "schema_version": "orchestra.aq10-defect-escape-rca.v1",
        "phase": "AQ10_DEFECT_ESCAPE_RCA",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }
    for key, expected in expected_constants.items():
        _require(_mapping(properties[key], f"AQ10 schema {key} missing").get("const") == expected, f"AQ10 schema {key} drift")
        _require(contract[key] == expected, f"AQ10 contract {key} drift")

    _require(tuple(contract["implementation_inventory"]) == EXACT_INVENTORY, "AQ10 exact implementation inventory drift")
    _require(tuple(contract["taxonomy"]) == CAUSES, "AQ10 taxonomy drift")
    _require(contract["signal_map"] == SIGNAL_MAP, "AQ10 signal-map drift")
    _require(contract["prevention_actions"] == PREVENTION, "AQ10 prevention-action drift")
    _require(tuple(contract["fail_closed_conditions"]) == FAIL_CLOSED, "AQ10 fail-closed contract drift")
    _require(set(contract["authority"]) == AUTHORITY_KEYS, "AQ10 authority key drift")
    _require(all(value is False for value in contract["authority"].values()), "AQ10 authority must remain non-authorizing")

    incidents = contract["reference_incidents"]
    _require(isinstance(incidents, list) and len(incidents) >= 2, "AQ10 reference incidents missing")
    ids = [item["incident_id"] for item in incidents]
    _require(len(ids) == len(set(ids)), "AQ10 reference incident ids must be unique")
    for incident in incidents:
        _require(incident["expected_root_cause"] in CAUSES, "AQ10 reference incident cause drift")
        _require(bool(incident["escaped_gates"]), "AQ10 reference incident escaped-gate evidence missing")
        _require(bool(incident["signals"]), "AQ10 reference incident signal evidence missing")
        for signal in incident["signals"]:
            _require(signal in SIGNAL_MAP, f"AQ10 reference incident uses unknown signal: {signal}")

    validation = contract["validation"]
    _require(validation["runtime"] == "orchestra_runtime/domain/adaptive/defect_escape_rca.py", "AQ10 runtime reference drift")
    _require(validation["canonical_start_sha"] == "62208416de9c131569aeb116716df6b9dc130f8b", "AQ10 canonical start drift")

    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    _require(
        '"Name": "validate_aq10.py", "Path": "scripts/validation/validate_aq10.py"' in run_tests,
        "AQ10 validator is not registered in behavior validation",
    )

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))
    machine_contracts = readme["machine_contracts"]
    expected_readme = {
        "adaptive_assurance_aq10_contract": "machine/adaptive/aq10-defect-escape-rca.v1.json",
        "adaptive_assurance_aq10_schema": "machine/schemas/aq10-defect-escape-rca.v1.schema.json",
        "adaptive_assurance_aq10_runtime": "orchestra_runtime/domain/adaptive/defect_escape_rca.py",
        "adaptive_assurance_aq10_validator": "scripts/validation/validate_aq10.py",
        "adaptive_assurance_aq10_validation": "tests/runtime/test_adaptive_assurance_aq10.py",
        "adaptive_assurance_aq10_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md",
    }
    for key, value in expected_readme.items():
        _require(machine_contracts.get(key) == value, f"README AQ10 reference drift: {key}")

    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "DEFECT_ESCAPE_RCA",
        "EVIDENCE_ONLY_NON_AUTHORIZING",
        "ASSURANCE_TOOL_COMPATIBILITY",
        "DEPENDENCY_ENVIRONMENT_GAP",
        "HUMAN_RCA_REVIEW_REQUIRED",
    ):
        _require(marker in doc, f"AQ10 architecture reference is missing {marker}")

    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    for marker in (
        "@codebase_provenance_JEO",
        "@codebase_rights_JEO",
        "@codebase_verified_JEO",
        "class DefectEscapeObservation",
        "class DefectEscapeFinding",
        "def classify_defect_escape",
        "def analyze_defect_escapes",
    ):
        _require(marker in runtime, f"AQ10 runtime is missing required marker: {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, JSONDecodeError) as exc:
        print(f"AQ10_DEFECT_ESCAPE_RCA_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ10_DEFECT_ESCAPE_RCA_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
