#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
# @codebase_verified_JEO
"""Validate AQ9 deep-assurance contract, configuration, and repository parity."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tomllib

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine/adaptive/aq9-deep-assurance.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq9-deep-assurance.v1.schema.json"
COSMIC_RAY_PATH = ROOT / "cosmic-ray.toml"
RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
README_PATH = ROOT / "README.json"
DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"

EXACT_INVENTORY = (
    "CHANGELOG.md",
    "README.json",
    "cosmic-ray.toml",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md",
    "machine/adaptive/aq9-deep-assurance.v1.json",
    "machine/schemas/aq9-deep-assurance.v1.schema.json",
    "scripts/validation/validate_aq9.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq9.py",
)
FAMILIES = ("MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ")
BASE_MUTATION_TARGETS = {
    "orchestra_runtime/evidence.py",
    "orchestra_runtime/governance_kernel.py",
    "orchestra_runtime/preexecution.py",
}
AQ9_MUTATION_TARGET = "scripts/validation/classify_adaptive_assurance_scope.py"
REQUIRED_TEST_SURFACES = {
    "tests/runtime/test_evidence_kernel.py",
    "tests/runtime/test_governance_kernel.py",
    "tests/runtime/test_preexecution.py",
    "tests/behavior/test_protected_aq8_assurance_scope_policy.py",
    "tests/runtime/test_adaptive_assurance_aq9.py",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)

    _require(contract["schema_version"] == "orchestra.aq9-deep-assurance.v1", "AQ9 schema version drift")
    _require(contract["phase"] == "AQ9_DEEP_ASSURANCE", "AQ9 phase drift")
    _require(contract["owner"] == "overseer", "AQ9 owner drift")
    _require(contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING", "AQ9 authority model drift")
    _require(tuple(contract["implementation_inventory"]) == EXACT_INVENTORY, "AQ9 exact implementation inventory drift")
    _require(tuple(contract["assurance_families"]) == FAMILIES, "AQ9 assurance-family drift")
    _require(contract["property"]["cases"] == 64, "AQ9 property bound drift")
    _require(contract["metamorphic"]["cases"] == 32, "AQ9 metamorphic bound drift")
    _require(contract["bounded_fuzz"]["cases"] == 256, "AQ9 fuzz bound drift")
    _require(contract["bounded_fuzz"]["seed"] == 20260911, "AQ9 deterministic seed drift")
    _require(contract["bounded_fuzz"]["max_generated_paths"] == 12, "AQ9 fuzz path bound drift")
    _require(all(value is False for value in contract["authority"].values()), "AQ9 authority must remain non-authorizing")

    cosmic = tomllib.loads(COSMIC_RAY_PATH.read_text(encoding="utf-8"))["cosmic-ray"]
    module_paths = tuple(cosmic["module-path"])
    _require(len(module_paths) == len(set(module_paths)), "Cosmic Ray mutation targets contain duplicates")
    _require(BASE_MUTATION_TARGETS.issubset(module_paths), "AQ9 removed a pre-existing Cosmic Ray target")
    _require(AQ9_MUTATION_TARGET in module_paths, "AQ9 classifier is not an actual Cosmic Ray mutation target")
    _require(float(cosmic["timeout"]) >= 90.0, "AQ9 lowered the existing Cosmic Ray timeout")
    test_command = cosmic["test-command"]
    for path in REQUIRED_TEST_SURFACES:
        _require(path in test_command, f"Cosmic Ray test command is missing {path}")

    mutation = contract["mutation"]
    _require(set(mutation["required_existing_targets"]) == BASE_MUTATION_TARGETS, "AQ9 mutation baseline contract drift")
    _require(mutation["aq9_added_targets"] == [AQ9_MUTATION_TARGET], "AQ9 added mutation target drift")
    _require(set(mutation["test_surfaces"]) == REQUIRED_TEST_SURFACES, "AQ9 mutation test-surface drift")
    _require(mutation["score_policy"] == "PRESERVE_EXISTING_SCOREABLE_COMPATIBILITY_GATE", "AQ9 mutation score policy drift")

    run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
    _require(
        '"Name": "validate_aq9.py", "Path": "scripts/validation/validate_aq9.py"' in run_tests,
        "AQ9 validator is not registered in behavior validation",
    )

    readme = json.loads(README_PATH.read_text(encoding="utf-8"))
    machine_contracts = readme["machine_contracts"]
    _require(machine_contracts["adaptive_assurance_aq9_contract"] == "machine/adaptive/aq9-deep-assurance.v1.json", "README AQ9 contract reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_schema"] == "machine/schemas/aq9-deep-assurance.v1.schema.json", "README AQ9 schema reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_validator"] == "scripts/validation/validate_aq9.py", "README AQ9 validator reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_validation"] == "tests/runtime/test_adaptive_assurance_aq9.py", "README AQ9 runtime-test reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_documentation"] == "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md", "README AQ9 architecture reference drift")

    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in ("MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ", "EVIDENCE_ONLY_NON_AUTHORIZING"):
        _require(marker in doc, f"AQ9 architecture reference is missing {marker}")


def main() -> int:
    try:
        validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, jsonschema.ValidationError, tomllib.TOMLDecodeError) as exc:
        print(f"AQ9_DEEP_ASSURANCE_VALIDATION=FAIL: {exc}", file=sys.stderr)
        return 1
    print("AQ9_DEEP_ASSURANCE_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
