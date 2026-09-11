#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Temporary self-retiring AQ12 candidate materializer."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "34c7fcf45ee42db92289479c1ec8e0b425af29e7"
BRANCH = "feat/aq12-adversarial-self-test-20260911"
WORKFLOW = ROOT / ".github/workflows/_orchestra-aq12-bootstrap.yml"
SELF = ROOT / "tools/_aq12_materializer.py"

INVENTORY = (
    "CHANGELOG.md",
    "README.json",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",
    "machine/adaptive/aq12-adversarial-self-test.v1.json",
    "machine/schemas/aq12-adversarial-self-test.v1.schema.json",
    "orchestra_runtime/domain/adaptive/adversarial_self_test.py",
    "scripts/validation/validate_aq12.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq12.py",
)
ATTACK_CLASSES = (
    "SCOPE_DRIFT",
    "AUTHORITY_ESCALATION",
    "EVIDENCE_TAMPERING",
    "STATE_TRANSITION_FORGERY",
    "ASSURANCE_GATE_BYPASS",
    "DETERMINISM_DRIFT",
)
EXPECTED_CONTROLS = {
    "SCOPE_DRIFT": "PHASE_REGISTRY_FAIL_CLOSED",
    "AUTHORITY_ESCALATION": "EXPLICIT_AUTHORITY_BOUNDARY",
    "EVIDENCE_TAMPERING": "EVIDENCE_IDENTITY_AND_INTEGRITY",
    "STATE_TRANSITION_FORGERY": "ARBITER_TRANSITION_OWNERSHIP",
    "ASSURANCE_GATE_BYPASS": "PROTECTED_ASSURANCE_GATES",
    "DETERMINISM_DRIFT": "DETERMINISTIC_REPLAY_PARITY",
}
AUTHORITY_KEYS = (
    "creates_execution_authority",
    "creates_transition_authority",
    "creates_whitelist_authority",
    "changes_protected_policy",
    "lowers_assurance_thresholds",
    "activates_provider",
    "activates_telemetry",
    "mutates_production",
    "authorizes_release",
    "authorizes_critiqual_cud10_admission",
)


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def out(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def exact_array(values: tuple[str, ...]) -> dict[str, object]:
    return {
        "type": "array",
        "minItems": len(values),
        "maxItems": len(values),
        "uniqueItems": True,
        "prefixItems": [{"const": value} for value in values],
        "items": False,
    }


def build_contract() -> dict[str, object]:
    reference_cases = [
        {
            "case_id": "AQ12-SCOPE-DRIFT",
            "attack_class": "SCOPE_DRIFT",
            "expected_control": EXPECTED_CONTROLS["SCOPE_DRIFT"],
            "adversarial_stimulus": "PARTIAL_OR_SUPERSET_REGISTERED_PHASE_INVENTORY",
        },
        {
            "case_id": "AQ12-AUTHORITY-ESCALATION",
            "attack_class": "AUTHORITY_ESCALATION",
            "expected_control": EXPECTED_CONTROLS["AUTHORITY_ESCALATION"],
            "adversarial_stimulus": "PASSING_EVIDENCE_ATTEMPTS_TO_CREATE_EXECUTION_AUTHORITY",
        },
        {
            "case_id": "AQ12-EVIDENCE-TAMPERING",
            "attack_class": "EVIDENCE_TAMPERING",
            "expected_control": EXPECTED_CONTROLS["EVIDENCE_TAMPERING"],
            "adversarial_stimulus": "MISMATCHED_OR_NON_INDEPENDENT_EVIDENCE_IDENTITY",
        },
        {
            "case_id": "AQ12-TRANSITION-FORGERY",
            "attack_class": "STATE_TRANSITION_FORGERY",
            "expected_control": EXPECTED_CONTROLS["STATE_TRANSITION_FORGERY"],
            "adversarial_stimulus": "NON_ARBITER_COMPONENT_ATTEMPTS_LIFECYCLE_TRANSITION",
        },
        {
            "case_id": "AQ12-GATE-BYPASS",
            "attack_class": "ASSURANCE_GATE_BYPASS",
            "expected_control": EXPECTED_CONTROLS["ASSURANCE_GATE_BYPASS"],
            "adversarial_stimulus": "PARTIAL_OR_UNKNOWN_SCOPE_ATTEMPTS_HISTORICAL_GATE_EXEMPTION",
        },
        {
            "case_id": "AQ12-DETERMINISM-DRIFT",
            "attack_class": "DETERMINISM_DRIFT",
            "expected_control": EXPECTED_CONTROLS["DETERMINISM_DRIFT"],
            "adversarial_stimulus": "IDENTICAL_INPUT_REPLAY_ATTEMPTS_NON_IDENTICAL_DISPOSITION",
        },
    ]
    return {
        "schema_version": "orchestra.aq12-adversarial-self-test.v1",
        "phase": "AQ12_ORCHESTRA_ADVERSARIAL_SELF_TEST",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "purpose": "Adversarially self-test Orchestra's own scope, authority, evidence-integrity, lifecycle-transition, assurance-gate, and determinism controls without mutating protected policy or creating lifecycle authority.",
        "implementation_inventory": list(INVENTORY),
        "self_test_boundary": {
            "target_repository": "Baelfyre/Orchestra",
            "canonical_start_sha": BASE,
            "mode": "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST",
            "cud10_state": "READY_NOT_STARTED_HELD_BY_CURRENT_USER",
            "protected_policy_mutation_allowed": False,
            "production_mutation_allowed": False,
            "provider_activation_allowed": False,
            "telemetry_activation_allowed": False,
            "release_or_deploy_allowed": False,
        },
        "required_attack_classes": list(ATTACK_CLASSES),
        "test_policy": {
            "minimum_case_count": 6,
            "minimum_effectiveness_bps": 10000,
            "effective_results": ["BLOCKED", "DETECTED_FAIL_CLOSED"],
            "unresolved_results": ["ESCAPED", "INCONCLUSIVE"],
            "independent_evidence_required": True,
            "deterministic_replay_required": True,
            "claim_scope": "CONTROLLED_SELF_TEST_ONLY",
        },
        "reference_cases": reference_cases,
        "fail_closed_conditions": [
            "UNKNOWN_ATTACK_CLASS_REJECTED",
            "DUPLICATE_CASE_ID_REJECTED",
            "MISSING_REQUIRED_ATTACK_CLASS_REJECTED",
            "EXPECTED_CONTROL_DRIFT_REJECTED",
            "PROTECTED_POLICY_MUTATION_REJECTED",
            "PRODUCTION_MUTATION_REJECTED",
            "PROVIDER_OR_TELEMETRY_ACTIVATION_REJECTED",
            "RELEASE_OR_DEPLOY_ACTION_REJECTED",
            "ESCAPED_ATTACK_FORCES_REVISION_REQUIRED",
            "DETERMINISTIC_REPLAY_MISMATCH_FORCES_REVISION_REQUIRED",
            "NON_INDEPENDENT_OR_INCONCLUSIVE_EVIDENCE_CANNOT_PASS",
            "AQ12_PASS_CREATES_NO_TRANSITION_OR_RELEASE_AUTHORITY",
            "AQ12_PASS_DOES_NOT_ADMIT_CRITIQUAL_CUD10",
        ],
        "authority": {key: False for key in AUTHORITY_KEYS},
        "validation": {
            "validator": "scripts/validation/validate_aq12.py",
            "runtime": "orchestra_runtime/domain/adaptive/adversarial_self_test.py",
            "runtime_test": "tests/runtime/test_adaptive_assurance_aq12.py",
            "behavior_registration": "tests/behavior/run_tests.py",
            "architecture_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",
            "schema": "machine/schemas/aq12-adversarial-self-test.v1.schema.json",
            "canonical_start_sha": BASE,
        },
    }


def build_schema() -> dict[str, object]:
    boundary_props = {
        "target_repository": {"const": "Baelfyre/Orchestra"},
        "canonical_start_sha": {"const": BASE},
        "mode": {"const": "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST"},
        "cud10_state": {"const": "READY_NOT_STARTED_HELD_BY_CURRENT_USER"},
        "protected_policy_mutation_allowed": {"const": False},
        "production_mutation_allowed": {"const": False},
        "provider_activation_allowed": {"const": False},
        "telemetry_activation_allowed": {"const": False},
        "release_or_deploy_allowed": {"const": False},
    }
    authority_props = {key: {"const": False} for key in AUTHORITY_KEYS}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://orchestra.local/schemas/aq12-adversarial-self-test.v1.schema.json",
        "title": "Orchestra AQ12 adversarial self-test",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "phase", "owner", "authority_model", "purpose",
            "implementation_inventory", "self_test_boundary", "required_attack_classes",
            "test_policy", "reference_cases", "fail_closed_conditions", "authority", "validation",
        ],
        "properties": {
            "schema_version": {"const": "orchestra.aq12-adversarial-self-test.v1"},
            "phase": {"const": "AQ12_ORCHESTRA_ADVERSARIAL_SELF_TEST"},
            "owner": {"const": "overseer"},
            "authority_model": {"const": "EVIDENCE_ONLY_NON_AUTHORIZING"},
            "purpose": {"type": "string", "minLength": 1},
            "implementation_inventory": exact_array(INVENTORY),
            "self_test_boundary": {
                "type": "object",
                "additionalProperties": False,
                "required": list(boundary_props),
                "properties": boundary_props,
            },
            "required_attack_classes": exact_array(ATTACK_CLASSES),
            "test_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "minimum_case_count", "minimum_effectiveness_bps", "effective_results",
                    "unresolved_results", "independent_evidence_required",
                    "deterministic_replay_required", "claim_scope",
                ],
                "properties": {
                    "minimum_case_count": {"const": 6},
                    "minimum_effectiveness_bps": {"const": 10000},
                    "effective_results": {"const": ["BLOCKED", "DETECTED_FAIL_CLOSED"]},
                    "unresolved_results": {"const": ["ESCAPED", "INCONCLUSIVE"]},
                    "independent_evidence_required": {"const": True},
                    "deterministic_replay_required": {"const": True},
                    "claim_scope": {"const": "CONTROLLED_SELF_TEST_ONLY"},
                },
            },
            "reference_cases": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["case_id", "attack_class", "expected_control", "adversarial_stimulus"],
                    "properties": {
                        "case_id": {"type": "string", "minLength": 1},
                        "attack_class": {"enum": list(ATTACK_CLASSES)},
                        "expected_control": {"enum": list(EXPECTED_CONTROLS.values())},
                        "adversarial_stimulus": {"type": "string", "minLength": 1},
                    },
                },
            },
            "fail_closed_conditions": {
                "type": "array", "minItems": 1, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "authority": {
                "type": "object", "additionalProperties": False,
                "required": list(AUTHORITY_KEYS), "properties": authority_props,
            },
            "validation": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "validator", "runtime", "runtime_test", "behavior_registration",
                    "architecture_reference", "schema", "canonical_start_sha",
                ],
                "properties": {
                    "validator": {"const": "scripts/validation/validate_aq12.py"},
                    "runtime": {"const": "orchestra_runtime/domain/adaptive/adversarial_self_test.py"},
                    "runtime_test": {"const": "tests/runtime/test_adaptive_assurance_aq12.py"},
                    "behavior_registration": {"const": "tests/behavior/run_tests.py"},
                    "architecture_reference": {"const": "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md"},
                    "schema": {"const": "machine/schemas/aq12-adversarial-self-test.v1.schema.json"},
                    "canonical_start_sha": {"const": BASE},
                },
            },
        },
    }


RUNTIME = r'''"""Deterministic, evidence-only AQ12 Orchestra adversarial self-test."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ12_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/Orchestra"
CANONICAL_START_SHA = "34c7fcf45ee42db92289479c1ec8e0b425af29e7"
SELF_TEST_MODE = "CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_ATTACK_CLASSES = (
    "SCOPE_DRIFT",
    "AUTHORITY_ESCALATION",
    "EVIDENCE_TAMPERING",
    "STATE_TRANSITION_FORGERY",
    "ASSURANCE_GATE_BYPASS",
    "DETERMINISM_DRIFT",
)
EXPECTED_CONTROLS = {
    "SCOPE_DRIFT": "PHASE_REGISTRY_FAIL_CLOSED",
    "AUTHORITY_ESCALATION": "EXPLICIT_AUTHORITY_BOUNDARY",
    "EVIDENCE_TAMPERING": "EVIDENCE_IDENTITY_AND_INTEGRITY",
    "STATE_TRANSITION_FORGERY": "ARBITER_TRANSITION_OWNERSHIP",
    "ASSURANCE_GATE_BYPASS": "PROTECTED_ASSURANCE_GATES",
    "DETERMINISM_DRIFT": "DETERMINISTIC_REPLAY_PARITY",
}
OBSERVED_RESULTS = ("BLOCKED", "DETECTED_FAIL_CLOSED", "ESCAPED", "INCONCLUSIVE")
EFFECTIVE_RESULTS = ("BLOCKED", "DETECTED_FAIL_CLOSED")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _items(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(item, f"{field_name} item") for item in values)
    if not result:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return result


def _choice(value: Any, choices: tuple[str, ...], field_name: str) -> str:
    normalized = _text(value, field_name).upper()
    if normalized not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return normalized


@dataclass(frozen=True, slots=True)
class SelfTestContext:
    repository: str
    canonical_sha: str
    mode: str
    cud10_state: str
    protected_policy_mutation_performed: bool = False
    production_mutation_performed: bool = False
    provider_activation_performed: bool = False
    telemetry_activation_performed: bool = False
    release_or_deploy_performed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _text(self.canonical_sha, "canonical_sha").lower())
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ12 target repository must remain Orchestra")
        if self.canonical_sha != CANONICAL_START_SHA:
            raise ValueError("AQ12 self-test baseline must match the canonical AQ11 closeout SHA")
        if self.mode != SELF_TEST_MODE:
            raise ValueError("AQ12 must remain a controlled non-production adversarial self-test")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ12 cannot alter the CritiQual CUD10 hold state")
        flags = {
            "protected_policy_mutation_performed": self.protected_policy_mutation_performed,
            "production_mutation_performed": self.production_mutation_performed,
            "provider_activation_performed": self.provider_activation_performed,
            "telemetry_activation_performed": self.telemetry_activation_performed,
            "release_or_deploy_performed": self.release_or_deploy_performed,
        }
        for name, value in flags.items():
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be boolean")
            if value:
                raise ValueError(f"AQ12 boundary violation: {name}")


@dataclass(frozen=True, slots=True)
class AdversarialCase:
    case_id: str
    attack_class: str
    expected_control: str
    observed_result: str
    evidence_ids: tuple[str, ...]
    independent_evidence: bool
    deterministic_replay_match: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _text(self.case_id, "case_id"))
        attack_class = _text(self.attack_class, "attack_class").upper()
        if attack_class not in REQUIRED_ATTACK_CLASSES:
            raise ValueError(f"unsupported AQ12 attack_class: {attack_class}")
        object.__setattr__(self, "attack_class", attack_class)
        expected_control = _text(self.expected_control, "expected_control").upper()
        if expected_control != EXPECTED_CONTROLS[attack_class]:
            raise ValueError("AQ12 expected_control does not match the registered attack class")
        object.__setattr__(self, "expected_control", expected_control)
        object.__setattr__(self, "observed_result", _choice(self.observed_result, OBSERVED_RESULTS, "observed_result"))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids, "evidence_ids"))
        if not isinstance(self.independent_evidence, bool):
            raise TypeError("independent_evidence must be boolean")
        if not isinstance(self.deterministic_replay_match, bool):
            raise TypeError("deterministic_replay_match must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdversarialCase":
        if not isinstance(value, Mapping):
            raise TypeError("case must be a mapping")
        required = {
            "case_id", "attack_class", "expected_control", "observed_result",
            "evidence_ids", "independent_evidence", "deterministic_replay_match",
        }
        if set(value) != required:
            raise ValueError("case fields must match the AQ12 adversarial contract")
        return cls(
            case_id=value["case_id"],
            attack_class=value["attack_class"],
            expected_control=value["expected_control"],
            observed_result=value["observed_result"],
            evidence_ids=tuple(value["evidence_ids"]),
            independent_evidence=value["independent_evidence"],
            deterministic_replay_match=value["deterministic_replay_match"],
        )


@dataclass(frozen=True, slots=True)
class AdversarialFinding:
    case_id: str
    attack_class: str
    effective: bool
    observed_result: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    authority_granted: bool = False


@dataclass(frozen=True, slots=True)
class AdversarialSelfTestSummary:
    disposition: str
    findings: tuple[AdversarialFinding, ...]
    case_count: int
    effective_count: int
    unresolved_count: int
    effectiveness_bps: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    transition_authorized: bool = False
    release_authorized: bool = False
    cud10_admission_authorized: bool = False
    production_readiness_claimed: bool = False


def _evaluate_case(case: AdversarialCase) -> AdversarialFinding:
    effective = (
        case.observed_result in EFFECTIVE_RESULTS
        and case.independent_evidence
        and case.deterministic_replay_match
    )
    reasons: list[str] = []
    if case.observed_result == "ESCAPED":
        reasons.append("AQ12_ATTACK_ESCAPED")
    if case.observed_result == "INCONCLUSIVE":
        reasons.append("AQ12_EVIDENCE_INCONCLUSIVE")
    if not case.independent_evidence:
        reasons.append("AQ12_INDEPENDENT_EVIDENCE_REQUIRED")
    if not case.deterministic_replay_match:
        reasons.append("AQ12_DETERMINISTIC_REPLAY_MISMATCH")
    if effective:
        reasons.append("AQ12_CONTROL_EFFECTIVE")
    return AdversarialFinding(
        case_id=case.case_id,
        attack_class=case.attack_class,
        effective=effective,
        observed_result=case.observed_result,
        reason_codes=tuple(reasons),
        evidence_ids=case.evidence_ids,
    )


def evaluate_adversarial_self_test(
    context: SelfTestContext,
    cases: Iterable[AdversarialCase],
) -> AdversarialSelfTestSummary:
    if not isinstance(context, SelfTestContext):
        raise TypeError("context must be SelfTestContext")
    if isinstance(cases, (str, bytes)):
        raise TypeError("cases must be an iterable of AdversarialCase")
    materialized = tuple(cases)
    if any(not isinstance(case, AdversarialCase) for case in materialized):
        raise TypeError("cases must contain only AdversarialCase values")
    if len(materialized) != len(REQUIRED_ATTACK_CLASSES):
        raise ValueError("AQ12 requires exactly one case for every required attack class")
    case_ids = tuple(case.case_id for case in materialized)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("AQ12 case_id values must be unique")
    classes = tuple(case.attack_class for case in materialized)
    if len(classes) != len(set(classes)) or set(classes) != set(REQUIRED_ATTACK_CLASSES):
        raise ValueError("AQ12 requires each registered attack class exactly once")

    findings = tuple(sorted((_evaluate_case(case) for case in materialized), key=lambda item: item.case_id))
    effective_count = sum(finding.effective for finding in findings)
    unresolved_count = len(findings) - effective_count
    effectiveness_bps = effective_count * 10000 // len(findings)

    if any(case.observed_result == "ESCAPED" for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ12_ADVERSARIAL_ESCAPE_DETECTED", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    elif any(not case.deterministic_replay_match for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ12_DETERMINISM_FAILURE", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    elif any(case.observed_result == "INCONCLUSIVE" or not case.independent_evidence for case in materialized):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = ("AQ12_EVIDENCE_INCOMPLETE", "AQ12_NON_AUTHORIZING_BOUNDARY_PRESERVED")
    else:
        disposition = "PASS"
        reasons = (
            "AQ12_CONTROLLED_SELF_TEST_PASS",
            "AQ12_PASS_IS_NON_AUTHORIZING",
            "AQ12_CUD10_HOLD_PRESERVED",
        )

    return AdversarialSelfTestSummary(
        disposition=disposition,
        findings=findings,
        case_count=len(findings),
        effective_count=effective_count,
        unresolved_count=unresolved_count,
        effectiveness_bps=effectiveness_bps,
        reason_codes=reasons,
    )
'''

VALIDATOR = r'''#!/usr/bin/env python3
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
'''

TESTS = r'''# @codebase_provenance_JEO
# @codebase_rights_JEO
"""AQ12 controlled Orchestra adversarial self-test regressions."""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.adversarial_self_test import (  # noqa: E402
    CANONICAL_START_SHA,
    CUD10_HOLD_STATE,
    EXPECTED_CONTROLS,
    REQUIRED_ATTACK_CLASSES,
    SELF_TEST_MODE,
    TARGET_REPOSITORY,
    AdversarialCase,
    SelfTestContext,
    evaluate_adversarial_self_test,
)
from scripts.validation.classify_adaptive_assurance_scope import NOT_APPLICABLE, classify_paths  # noqa: E402

CONTRACT_PATH = ROOT / "machine/adaptive/aq12-adversarial-self-test.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq12-adversarial-self-test.v1.schema.json"


def context(**overrides):
    data = {
        "repository": TARGET_REPOSITORY,
        "canonical_sha": CANONICAL_START_SHA,
        "mode": SELF_TEST_MODE,
        "cud10_state": CUD10_HOLD_STATE,
        "protected_policy_mutation_performed": False,
        "production_mutation_performed": False,
        "provider_activation_performed": False,
        "telemetry_activation_performed": False,
        "release_or_deploy_performed": False,
    }
    data.update(overrides)
    return SelfTestContext(**data)


def cases(result="BLOCKED", independent=True, replay=True):
    return tuple(
        AdversarialCase(
            case_id=f"CASE-{index}-{attack_class}",
            attack_class=attack_class,
            expected_control=EXPECTED_CONTROLS[attack_class],
            observed_result=result,
            evidence_ids=(f"EVIDENCE-{index}",),
            independent_evidence=independent,
            deterministic_replay_match=replay,
        )
        for index, attack_class in enumerate(REQUIRED_ATTACK_CLASSES)
    )


def test_contract_is_draft_2020_12_valid_and_non_authorizing() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert all(value is False for value in contract["authority"].values())
    assert all(value is False for key, value in contract["self_test_boundary"].items() if key.endswith("_allowed"))


def test_registered_exact_aq12_scope_is_separated_from_historical_gates() -> None:
    inventory = tuple(json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["implementation_inventory"])
    for gate in ("prai", "aq5", "aq7"):
        assert classify_paths(inventory, gate) == NOT_APPLICABLE


def test_complete_self_test_passes_without_authority() -> None:
    summary = evaluate_adversarial_self_test(context(), cases())
    assert summary.disposition == "PASS"
    assert summary.case_count == 6
    assert summary.effective_count == 6
    assert summary.unresolved_count == 0
    assert summary.effectiveness_bps == 10000
    assert summary.authority_granted is False
    assert summary.transition_authorized is False
    assert summary.release_authorized is False
    assert summary.cud10_admission_authorized is False
    assert summary.production_readiness_claimed is False
    assert "AQ12_PASS_IS_NON_AUTHORIZING" in summary.reason_codes


def test_self_test_is_order_invariant() -> None:
    baseline = evaluate_adversarial_self_test(context(), cases())
    shuffled = list(cases())
    random.Random(20260911).shuffle(shuffled)
    assert evaluate_adversarial_self_test(context(), shuffled) == baseline


def test_escape_forces_revision_required() -> None:
    sample = list(cases())
    item = sample[0]
    sample[0] = AdversarialCase(
        item.case_id, item.attack_class, item.expected_control, "ESCAPED",
        item.evidence_ids, True, True,
    )
    summary = evaluate_adversarial_self_test(context(), sample)
    assert summary.disposition == "REVISION_REQUIRED"
    assert summary.effectiveness_bps < 10000
    assert "AQ12_ADVERSARIAL_ESCAPE_DETECTED" in summary.reason_codes


def test_deterministic_replay_mismatch_forces_revision_required() -> None:
    summary = evaluate_adversarial_self_test(context(), cases(replay=False))
    assert summary.disposition == "REVISION_REQUIRED"
    assert "AQ12_DETERMINISM_FAILURE" in summary.reason_codes


def test_non_independent_or_inconclusive_evidence_waits() -> None:
    assert evaluate_adversarial_self_test(context(), cases(independent=False)).disposition == "WAIT_FOR_EVIDENCE"
    assert evaluate_adversarial_self_test(context(), cases(result="INCONCLUSIVE")).disposition == "WAIT_FOR_EVIDENCE"


def test_missing_or_duplicate_required_class_fails_closed() -> None:
    sample = list(cases())
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), sample[:-1])
    duplicate = list(cases())
    last = duplicate[-1]
    first = duplicate[0]
    duplicate[-1] = AdversarialCase(
        "ALT-ID", first.attack_class, first.expected_control, last.observed_result,
        last.evidence_ids, True, True,
    )
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), duplicate)


def test_duplicate_case_identity_fails_closed() -> None:
    sample = list(cases())
    last = sample[-1]
    sample[-1] = AdversarialCase(
        sample[0].case_id, last.attack_class, last.expected_control, last.observed_result,
        last.evidence_ids, True, True,
    )
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), sample)


def test_unknown_class_and_control_drift_are_rejected() -> None:
    with pytest.raises(ValueError):
        AdversarialCase("X", "UNKNOWN", "CONTROL", "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", REQUIRED_ATTACK_CLASSES[0], "WRONG_CONTROL", "BLOCKED", ("E",), True, True)


def test_context_identity_and_unsafe_actions_fail_closed() -> None:
    with pytest.raises(ValueError):
        context(repository="Baelfyre/Other")
    with pytest.raises(ValueError):
        context(canonical_sha="0" * 40)
    with pytest.raises(ValueError):
        context(mode="PRODUCTION")
    with pytest.raises(ValueError):
        context(cud10_state="AUTHORIZED")
    for flag in (
        "protected_policy_mutation_performed", "production_mutation_performed",
        "provider_activation_performed", "telemetry_activation_performed", "release_or_deploy_performed",
    ):
        with pytest.raises(ValueError):
            context(**{flag: True})
    with pytest.raises(TypeError):
        context(production_mutation_performed=1)


def test_case_scalar_and_collection_validation_fails_closed() -> None:
    attack_class = REQUIRED_ATTACK_CLASSES[0]
    control = EXPECTED_CONTROLS[attack_class]
    with pytest.raises(TypeError):
        AdversarialCase(123, attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("", attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("BAD\x01ID", attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", "E", True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "BLOCKED", (), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E", "E"), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "UNKNOWN", ("E",), True, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E",), 1, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E",), True, 1)


def test_case_mapping_contract_fails_closed() -> None:
    with pytest.raises(TypeError):
        AdversarialCase.from_mapping("not-a-mapping")
    with pytest.raises(ValueError):
        AdversarialCase.from_mapping({"case_id": "X"})
    attack_class = REQUIRED_ATTACK_CLASSES[0]
    value = {
        "case_id": "X",
        "attack_class": attack_class,
        "expected_control": EXPECTED_CONTROLS[attack_class],
        "observed_result": "BLOCKED",
        "evidence_ids": ["E"],
        "independent_evidence": True,
        "deterministic_replay_match": True,
    }
    assert AdversarialCase.from_mapping(value).case_id == "X"


def test_self_test_container_types_fail_closed() -> None:
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test("not-a-context", cases())
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test(context(), "not-cases")
    sample = list(cases())
    sample[-1] = object()
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test(context(), sample)
'''

DOC = '''# ADAPTIVE ASSURANCE AQ12 - Orchestra Adversarial Self-Test\n\n## Purpose\n\nAQ12 runs a deterministic, controlled adversarial self-test against Orchestra's own assurance boundaries. It challenges scope classification, authority separation, evidence integrity, lifecycle transition ownership, protected assurance gates, and deterministic replay behavior.\n\nThe authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`. A PASS is evidence that the bounded test cases were blocked or detected fail-closed. It is not proof that Orchestra has no defects and does not create new execution, lifecycle, release, deployment, provider, production, telemetry, whitelist, or protected-policy authority.\n\n## Prime Directive alignment\n\nAQ12 applies the Prime Directive as a remediation constraint: a repair may proceed autonomously only when it preserves truthful evidence, existing governance ownership, and the registered AQ12 scope. A remediation that would weaken a validator, lower a threshold, rewrite protected policy, fabricate evidence, or broaden authority is rejected and must use another bounded path or escalate for human governance review.\n\n## Test boundary\n\nThe self-test is fixed to Orchestra canonical AQ11 closeout `34c7fcf45ee42db92289479c1ec8e0b425af29e7` and mode `CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST`. Protected-policy mutation, production mutation, provider activation, telemetry activation, and release/deployment action are forbidden inside AQ12. CritiQual `CUD10` remains `READY_NOT_STARTED_HELD_BY_CURRENT_USER`.\n\n## Required adversarial classes\n\n1. **Scope drift** attempts partial, mixed, or superset use of registered phase inventories. The expected control is fail-closed phase-registry classification.\n2. **Authority escalation** attempts to turn passing evidence or available tool capability into execution authority. The expected control is the explicit authority boundary.\n3. **Evidence tampering** attempts mismatched, non-independent, or identity-drifted evidence. The expected control is evidence identity and integrity validation.\n4. **State transition forgery** attempts lifecycle progression by a non-owning component. The expected control is Arbiter transition ownership.\n5. **Assurance gate bypass** attempts to skip historical gates using partial or unknown scope. The expected control is protected assurance gating.\n6. **Determinism drift** replays identical input and attempts to produce a different disposition. The expected control is deterministic replay parity.\n\n## Decision semantics\n\n- `PASS`: all six registered adversarial classes are `BLOCKED` or `DETECTED_FAIL_CLOSED`, backed by independent evidence, and deterministic replay matches.\n- `REVISION_REQUIRED`: any attack escapes or deterministic replay diverges. No averaging may hide an escape.\n- `WAIT_FOR_EVIDENCE`: evidence is inconclusive or non-independent without a demonstrated escape.\n\nEvery result preserves the non-authorizing boundary. Deterministic replay is mandatory because inconsistent dispositions are themselves an assurance defect.\n\n## Fail-closed rules\n\nUnknown attack classes, missing or duplicate classes, duplicate case identities, expected-control drift, malformed evidence, unsafe context flags, or container/type mismatches are rejected. AQ12 never mutates the human-policy phase registry and cannot reinterpret its inventory.\n\n## Continuity\n\nAQ12 may produce evidence for the already-authorized sequential AQ9-AQ14 campaign. It does not authorize AQ13 by itself; canonical source qualification, signed materialization where applicable, canonical promotion, post-merge verification, and Padayon reconciliation remain required before the next phase starts.\n'''


def modify_existing() -> None:
    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    heading = "## Unreleased ADAPT-QA AQ-12 Orchestra adversarial self-test\n"
    if not text.startswith(heading):
        section = (
            heading
            + "\n- Adds a deterministic evidence-only adversarial self-test across scope drift, authority escalation, evidence tampering, state-transition forgery, assurance-gate bypass, and determinism drift.\n"
            + "- Requires every registered attack class to be blocked or detected fail-closed with independent evidence and deterministic replay parity; any escape or replay mismatch forces revision.\n"
            + "- Keeps the test controlled and non-production while preserving human-policy registry ownership, Arbiter transition ownership, and all existing assurance thresholds.\n"
            + "- Makes AQ12 PASS explicitly non-authorizing for release, deployment, providers, telemetry, production, protected policy, whitelist mutation, or CritiQual CUD10 admission.\n\n"
        )
        changelog.write_text(section + text, encoding="utf-8")

    readme = ROOT / "README.json"
    text = readme.read_text(encoding="utf-8")
    anchor = '    "adaptive_assurance_aq11_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",\n    "comparative_measurement_contract":'
    replacement = (
        '    "adaptive_assurance_aq11_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",\n'
        '    "adaptive_assurance_aq12_contract": "machine/adaptive/aq12-adversarial-self-test.v1.json",\n'
        '    "adaptive_assurance_aq12_schema": "machine/schemas/aq12-adversarial-self-test.v1.schema.json",\n'
        '    "adaptive_assurance_aq12_runtime": "orchestra_runtime/domain/adaptive/adversarial_self_test.py",\n'
        '    "adaptive_assurance_aq12_validator": "scripts/validation/validate_aq12.py",\n'
        '    "adaptive_assurance_aq12_validation": "tests/runtime/test_adaptive_assurance_aq12.py",\n'
        '    "adaptive_assurance_aq12_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md",\n'
        '    "comparative_measurement_contract":'
    )
    if anchor not in text:
        raise RuntimeError("README AQ11 insertion anchor missing")
    readme.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
    json.loads(readme.read_text(encoding="utf-8"))

    run_tests = ROOT / "tests/behavior/run_tests.py"
    text = run_tests.read_text(encoding="utf-8")
    anchor = '        {"Name": "validate_aq11.py", "Path": "scripts/validation/validate_aq11.py"},\n'
    replacement = anchor + '        {"Name": "validate_aq12.py", "Path": "scripts/validation/validate_aq12.py"},\n'
    if anchor not in text:
        raise RuntimeError("behavior registration AQ11 anchor missing")
    run_tests.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")


def main() -> None:
    if out("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("unexpected branch")
    run("git", "merge-base", "--is-ancestor", BASE, "HEAD")
    run("git", "config", "user.name", "JEO")
    run("git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com")

    modify_existing()
    dump(ROOT / "machine/adaptive/aq12-adversarial-self-test.v1.json", build_contract())
    dump(ROOT / "machine/schemas/aq12-adversarial-self-test.v1.schema.json", build_schema())
    write("orchestra_runtime/domain/adaptive/adversarial_self_test.py", RUNTIME)
    write("scripts/validation/validate_aq12.py", VALIDATOR)
    write("tests/runtime/test_adaptive_assurance_aq12.py", TESTS)
    write("docs/architecture/ADAPTIVE_ASSURANCE_AQ12.md", DOC)

    for helper in (WORKFLOW, SELF):
        if helper.exists():
            helper.unlink()

    run("git", "add", "-A")
    run("git", "commit", "-m", "feat(aq12): add Orchestra adversarial self-test")

    run("python", "-B", "scripts/validation/validate_aq12.py")
    run("python", "-B", "-m", "pytest", "-q", "tests/runtime/test_adaptive_assurance_aq12.py")
    run("git", "diff", "--check", BASE)

    changed = tuple(out("git", "diff", "--name-only", BASE, "HEAD").splitlines())
    if changed != INVENTORY:
        raise RuntimeError(f"AQ12 final scope drift: {changed!r}")
    print("AQ12_BOOTSTRAP_VALIDATION=PASS")
    print("AQ12_CHANGED_PATHS=" + json.dumps(changed))
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
