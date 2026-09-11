#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Temporary self-retiring AQ11 materializer and focused qualifier."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "2fa5d648b5b19d483ecbe2342f5a28927a85d28f"
BRANCH = "feat/aq11-remediation-effectiveness-pilot-20260911"
HELPERS = [ROOT / ".github/workflows/_aq11-bootstrap.yml", ROOT / "scripts/_aq11_bootstrap.py"]
INVENTORY = [
    "CHANGELOG.md",
    "README.json",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
    "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json",
    "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
    "orchestra_runtime/domain/adaptive/remediation_effectiveness.py",
    "scripts/validation/validate_aq11.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq11.py",
]
CLASSES = [
    "PROVENANCE_OWNERSHIP",
    "AGGREGATE_CONCURRENCY",
    "CALIBRATION_EVIDENCE_INTEGRITY",
    "AUTHORITY_BOUNDARY",
    "RUNTIME_INTEGRATION",
    "GATE_COVERAGE_TRUTHFULNESS",
]
AUTHORITY_KEYS = [
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
]


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def out(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def dump(path: str, value: object) -> None:
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    if out("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("AQ11 bootstrap invoked on unexpected branch")
    run("git", "merge-base", "--is-ancestor", BASE, "HEAD")
    run("git", "config", "user.name", "JEO")
    run("git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com")

    contract = {
        "schema_version": "orchestra.aq11-remediation-effectiveness-pilot.v1",
        "phase": "AQ11_REMEDIATION_EFFECTIVENESS_PILOT",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "purpose": "Measure bounded before/after remediation effectiveness for known CritiQual development-assurance escape classes without mutating CritiQual, resuming CUD10, or granting lifecycle authority.",
        "implementation_inventory": INVENTORY,
        "pilot_boundary": {
            "target_repository": "Baelfyre/CritiQual",
            "observed_canonical_sha": "166bbac50a4f02e222aa15ff914c60cec658b7c0",
            "incident_reference": "Baelfyre/Padayon#441",
            "mode": "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT",
            "cud10_state": "READY_NOT_STARTED_HELD_BY_CURRENT_USER",
            "source_mutation_allowed": False,
            "production_evidence_allowed": False,
            "organic_effectiveness_claimed": False,
        },
        "required_escape_classes": CLASSES,
        "effectiveness_policy": {
            "minimum_case_count": 6,
            "minimum_effectiveness_bps": 10000,
            "effective_after_results": ["PREVENTED", "DETECTED_BEFORE_TRANSITION"],
            "unresolved_after_results": ["STILL_ESCAPES", "INCONCLUSIVE"],
            "independent_evidence_required": True,
            "recurrence_must_be_false": True,
            "claim_scope": "CONTROLLED_PILOT_ONLY",
        },
        "reference_cases": [
            {"case_id": "CQ-A-REVIEW-SNAPSHOT-PROVENANCE", "escape_class": "PROVENANCE_OWNERSHIP", "before_result": "REPRODUCED_DEFECT", "evidence_basis": "PADAYON_ISSUE_441_FINDING_A"},
            {"case_id": "CQ-B-LAST-ADMIN-CONCURRENCY", "escape_class": "AGGREGATE_CONCURRENCY", "before_result": "REPRODUCED_DEFECT", "evidence_basis": "PADAYON_ISSUE_441_FINDING_B"},
            {"case_id": "CQ-C-CALIBRATION-PASS-EVIDENCE", "escape_class": "CALIBRATION_EVIDENCE_INTEGRITY", "before_result": "REPRODUCED_DEFECT", "evidence_basis": "PADAYON_ISSUE_441_FINDING_C"},
            {"case_id": "CQ-D-GLOBAL-CALIBRATION-AUTHORITY", "escape_class": "AUTHORITY_BOUNDARY", "before_result": "REPRODUCED_DEFECT", "evidence_basis": "PADAYON_ISSUE_441_FINDING_D"},
            {"case_id": "CQ-R-RUNTIME-INTEGRATION", "escape_class": "RUNTIME_INTEGRATION", "before_result": "STATIC_RISK_CONFIRMED", "evidence_basis": "PADAYON_ISSUE_441_RUNTIME_INTEGRATION_THEME"},
            {"case_id": "CQ-G-GATE-COVERAGE-TRUTH", "escape_class": "GATE_COVERAGE_TRUTHFULNESS", "before_result": "STATIC_RISK_CONFIRMED", "evidence_basis": "PADAYON_ISSUE_441_GATE_COVERAGE_THEME"},
        ],
        "fail_closed_conditions": [
            "UNKNOWN_ESCAPE_CLASS_REJECTED",
            "DUPLICATE_CASE_ID_REJECTED",
            "MISSING_REQUIRED_ESCAPE_CLASS_REJECTED",
            "SOURCE_MUTATION_ATTEMPT_REJECTED",
            "PRODUCTION_MODE_REJECTED",
            "STALE_CRITIQUAL_BASELINE_REJECTED",
            "NON_INDEPENDENT_EVIDENCE_CANNOT_COUNT_EFFECTIVE",
            "RECURRENCE_FORCES_REVISION_REQUIRED",
            "PILOT_PASS_DOES_NOT_ADMIT_CUD10",
        ],
        "authority": {key: False for key in AUTHORITY_KEYS},
        "validation": {
            "validator": "scripts/validation/validate_aq11.py",
            "runtime": "orchestra_runtime/domain/adaptive/remediation_effectiveness.py",
            "runtime_test": "tests/runtime/test_adaptive_assurance_aq11.py",
            "behavior_registration": "tests/behavior/run_tests.py",
            "architecture_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
            "schema": "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
            "canonical_start_sha": BASE,
        },
    }
    dump("machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json", contract)

    ref_case = {
        "type": "object",
        "additionalProperties": False,
        "required": ["case_id", "escape_class", "before_result", "evidence_basis"],
        "properties": {
            "case_id": {"type": "string", "minLength": 1},
            "escape_class": {"enum": CLASSES},
            "before_result": {"enum": ["REPRODUCED_DEFECT", "STATIC_RISK_CONFIRMED"]},
            "evidence_basis": {"type": "string", "minLength": 1},
        },
    }
    authority_props = {key: {"const": False} for key in AUTHORITY_KEYS}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://orchestra.local/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
        "title": "Orchestra AQ11 remediation effectiveness pilot",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "phase", "owner", "authority_model", "purpose", "implementation_inventory", "pilot_boundary", "required_escape_classes", "effectiveness_policy", "reference_cases", "fail_closed_conditions", "authority", "validation"],
        "properties": {
            "schema_version": {"const": "orchestra.aq11-remediation-effectiveness-pilot.v1"},
            "phase": {"const": "AQ11_REMEDIATION_EFFECTIVENESS_PILOT"},
            "owner": {"const": "overseer"},
            "authority_model": {"const": "EVIDENCE_ONLY_NON_AUTHORIZING"},
            "purpose": {"type": "string", "minLength": 1},
            "implementation_inventory": {"type": "array", "minItems": 9, "maxItems": 9, "uniqueItems": True, "prefixItems": [{"const": p} for p in INVENTORY], "items": False},
            "pilot_boundary": {
                "type": "object", "additionalProperties": False,
                "required": ["target_repository", "observed_canonical_sha", "incident_reference", "mode", "cud10_state", "source_mutation_allowed", "production_evidence_allowed", "organic_effectiveness_claimed"],
                "properties": {
                    "target_repository": {"const": "Baelfyre/CritiQual"},
                    "observed_canonical_sha": {"const": "166bbac50a4f02e222aa15ff914c60cec658b7c0"},
                    "incident_reference": {"const": "Baelfyre/Padayon#441"},
                    "mode": {"const": "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT"},
                    "cud10_state": {"const": "READY_NOT_STARTED_HELD_BY_CURRENT_USER"},
                    "source_mutation_allowed": {"const": False},
                    "production_evidence_allowed": {"const": False},
                    "organic_effectiveness_claimed": {"const": False},
                },
            },
            "required_escape_classes": {"type": "array", "minItems": 6, "maxItems": 6, "uniqueItems": True, "prefixItems": [{"const": c} for c in CLASSES], "items": False},
            "effectiveness_policy": {
                "type": "object", "additionalProperties": False,
                "required": ["minimum_case_count", "minimum_effectiveness_bps", "effective_after_results", "unresolved_after_results", "independent_evidence_required", "recurrence_must_be_false", "claim_scope"],
                "properties": {
                    "minimum_case_count": {"const": 6},
                    "minimum_effectiveness_bps": {"const": 10000},
                    "effective_after_results": {"const": ["PREVENTED", "DETECTED_BEFORE_TRANSITION"]},
                    "unresolved_after_results": {"const": ["STILL_ESCAPES", "INCONCLUSIVE"]},
                    "independent_evidence_required": {"const": True},
                    "recurrence_must_be_false": {"const": True},
                    "claim_scope": {"const": "CONTROLLED_PILOT_ONLY"},
                },
            },
            "reference_cases": {"type": "array", "minItems": 6, "maxItems": 6, "items": ref_case},
            "fail_closed_conditions": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
            "authority": {"type": "object", "additionalProperties": False, "required": AUTHORITY_KEYS, "properties": authority_props},
            "validation": {
                "type": "object", "additionalProperties": False,
                "required": ["validator", "runtime", "runtime_test", "behavior_registration", "architecture_reference", "schema", "canonical_start_sha"],
                "properties": {
                    "validator": {"const": "scripts/validation/validate_aq11.py"},
                    "runtime": {"const": "orchestra_runtime/domain/adaptive/remediation_effectiveness.py"},
                    "runtime_test": {"const": "tests/runtime/test_adaptive_assurance_aq11.py"},
                    "behavior_registration": {"const": "tests/behavior/run_tests.py"},
                    "architecture_reference": {"const": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md"},
                    "schema": {"const": "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json"},
                    "canonical_start_sha": {"const": BASE},
                },
            },
        },
    }
    dump("machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json", schema)

    write("orchestra_runtime/domain/adaptive/remediation_effectiveness.py", '''"""Deterministic, evidence-only AQ11 remediation effectiveness pilot."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ11_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/CritiQual"
TARGET_CANONICAL_SHA = "166bbac50a4f02e222aa15ff914c60cec658b7c0"
TARGET_INCIDENT = "Baelfyre/Padayon#441"
PILOT_MODE = "CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_ESCAPE_CLASSES = (
    "PROVENANCE_OWNERSHIP",
    "AGGREGATE_CONCURRENCY",
    "CALIBRATION_EVIDENCE_INTEGRITY",
    "AUTHORITY_BOUNDARY",
    "RUNTIME_INTEGRATION",
    "GATE_COVERAGE_TRUTHFULNESS",
)
BEFORE_RESULTS = ("REPRODUCED_DEFECT", "STATIC_RISK_CONFIRMED")
AFTER_RESULTS = ("PREVENTED", "DETECTED_BEFORE_TRANSITION", "STILL_ESCAPES", "INCONCLUSIVE")
EFFECTIVE_AFTER_RESULTS = ("PREVENTED", "DETECTED_BEFORE_TRANSITION")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _items(values: Iterable[str], field_name: str, *, uppercase: bool = False) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(item, f"{field_name} item") for item in values)
    if uppercase:
        result = tuple(item.upper() for item in result)
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
class PilotContext:
    repository: str
    canonical_sha: str
    incident_reference: str
    mode: str
    cud10_state: str
    source_mutation_performed: bool = False
    production_evidence: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _text(self.canonical_sha, "canonical_sha").lower())
        object.__setattr__(self, "incident_reference", _text(self.incident_reference, "incident_reference"))
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ11 pilot repository must remain CritiQual")
        if self.canonical_sha != TARGET_CANONICAL_SHA:
            raise ValueError("AQ11 pilot baseline must match the observed held CritiQual canonical SHA")
        if self.incident_reference != TARGET_INCIDENT:
            raise ValueError("AQ11 pilot incident reference drift")
        if self.mode != PILOT_MODE:
            raise ValueError("AQ11 pilot must remain controlled non-production evidence only")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ11 pilot cannot alter the CUD10 hold state")
        if self.source_mutation_performed:
            raise ValueError("AQ11 pilot cannot mutate CritiQual source")
        if self.production_evidence:
            raise ValueError("AQ11 pilot cannot consume or claim production evidence")


@dataclass(frozen=True, slots=True)
class RemediationCase:
    case_id: str
    escape_class: str
    before_result: str
    after_result: str
    remediation_actions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    independent_evidence: bool
    recurrence_observed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _text(self.case_id, "case_id"))
        escape_class = _text(self.escape_class, "escape_class").upper()
        if escape_class not in REQUIRED_ESCAPE_CLASSES:
            raise ValueError(f"unsupported AQ11 escape_class: {escape_class}")
        object.__setattr__(self, "escape_class", escape_class)
        object.__setattr__(self, "before_result", _choice(self.before_result, BEFORE_RESULTS, "before_result"))
        object.__setattr__(self, "after_result", _choice(self.after_result, AFTER_RESULTS, "after_result"))
        object.__setattr__(self, "remediation_actions", _items(self.remediation_actions, "remediation_actions", uppercase=True))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids, "evidence_ids"))
        if not isinstance(self.independent_evidence, bool):
            raise TypeError("independent_evidence must be boolean")
        if not isinstance(self.recurrence_observed, bool):
            raise TypeError("recurrence_observed must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RemediationCase":
        if not isinstance(value, Mapping):
            raise TypeError("case must be a mapping")
        required = {"case_id", "escape_class", "before_result", "after_result", "remediation_actions", "evidence_ids", "independent_evidence", "recurrence_observed"}
        if set(value) != required:
            raise ValueError("case fields must match the AQ11 remediation contract")
        return cls(
            case_id=value["case_id"], escape_class=value["escape_class"],
            before_result=value["before_result"], after_result=value["after_result"],
            remediation_actions=tuple(value["remediation_actions"]), evidence_ids=tuple(value["evidence_ids"]),
            independent_evidence=value["independent_evidence"], recurrence_observed=value["recurrence_observed"],
        )


@dataclass(frozen=True, slots=True)
class RemediationCaseFinding:
    case_id: str
    escape_class: str
    effective: bool
    after_result: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    authority_granted: bool = False
    cud10_admission_authorized: bool = False


@dataclass(frozen=True, slots=True)
class RemediationPilotSummary:
    disposition: str
    findings: tuple[RemediationCaseFinding, ...]
    case_count: int
    effective_count: int
    unresolved_count: int
    effectiveness_bps: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    cud10_admission_authorized: bool = False
    production_readiness_claimed: bool = False
    organic_effectiveness_claimed: bool = False


def _evaluate_case(case: RemediationCase) -> RemediationCaseFinding:
    effective = (
        case.after_result in EFFECTIVE_AFTER_RESULTS
        and case.independent_evidence
        and not case.recurrence_observed
    )
    reasons: list[str] = []
    if case.after_result == "STILL_ESCAPES":
        reasons.append("AQ11_ESCAPE_REMAINS")
    if case.after_result == "INCONCLUSIVE":
        reasons.append("AQ11_AFTER_EVIDENCE_INCONCLUSIVE")
    if not case.independent_evidence:
        reasons.append("AQ11_INDEPENDENT_EVIDENCE_REQUIRED")
    if case.recurrence_observed:
        reasons.append("AQ11_RECURRENCE_OBSERVED")
    if effective:
        reasons.append("AQ11_CONTROLLED_REMEDIATION_EFFECTIVE")
    return RemediationCaseFinding(
        case_id=case.case_id,
        escape_class=case.escape_class,
        effective=effective,
        after_result=case.after_result,
        reason_codes=tuple(reasons),
        evidence_ids=case.evidence_ids,
    )


def evaluate_remediation_pilot(context: PilotContext, cases: Iterable[RemediationCase]) -> RemediationPilotSummary:
    if not isinstance(context, PilotContext):
        raise TypeError("context must be PilotContext")
    if isinstance(cases, (str, bytes)):
        raise TypeError("cases must be an iterable of RemediationCase")
    materialized = tuple(cases)
    if any(not isinstance(case, RemediationCase) for case in materialized):
        raise TypeError("cases must contain only RemediationCase values")
    if len(materialized) != len(REQUIRED_ESCAPE_CLASSES):
        raise ValueError("AQ11 pilot requires exactly one case for every required escape class")
    case_ids = tuple(case.case_id for case in materialized)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("AQ11 pilot case_id values must be unique")
    classes = tuple(case.escape_class for case in materialized)
    if len(classes) != len(set(classes)) or set(classes) != set(REQUIRED_ESCAPE_CLASSES):
        raise ValueError("AQ11 pilot requires each registered escape class exactly once")
    findings = tuple(sorted((_evaluate_case(case) for case in materialized), key=lambda item: item.case_id))
    effective_count = sum(finding.effective for finding in findings)
    unresolved_count = len(findings) - effective_count
    effectiveness_bps = effective_count * 10000 // len(findings)
    if any(case.after_result == "STILL_ESCAPES" or case.recurrence_observed for case in materialized):
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ11_REMEDIATION_NOT_EFFECTIVE", "AQ11_CUD10_HOLD_PRESERVED")
    elif any(case.after_result == "INCONCLUSIVE" or not case.independent_evidence for case in materialized):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = ("AQ11_EFFECTIVENESS_EVIDENCE_INCOMPLETE", "AQ11_CUD10_HOLD_PRESERVED")
    elif effectiveness_bps == 10000:
        disposition = "PASS"
        reasons = ("AQ11_CONTROLLED_PILOT_PASS", "AQ11_PASS_IS_NON_ADMITTING", "AQ11_CUD10_HOLD_PRESERVED")
    else:
        disposition = "REVISION_REQUIRED"
        reasons = ("AQ11_EFFECTIVENESS_THRESHOLD_NOT_MET", "AQ11_CUD10_HOLD_PRESERVED")
    return RemediationPilotSummary(
        disposition=disposition,
        findings=findings,
        case_count=len(findings),
        effective_count=effective_count,
        unresolved_count=unresolved_count,
        effectiveness_bps=effectiveness_bps,
        reason_codes=reasons,
    )
''')

    write("scripts/validation/validate_aq11.py", '''#!/usr/bin/env python3
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
''')

    write("tests/runtime/test_adaptive_assurance_aq11.py", '''# @codebase_provenance_JEO
# @codebase_rights_JEO
"""AQ11 controlled remediation-effectiveness pilot regressions."""
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

from orchestra_runtime.domain.adaptive.remediation_effectiveness import (  # noqa: E402
    CUD10_HOLD_STATE, PILOT_MODE, REQUIRED_ESCAPE_CLASSES, TARGET_CANONICAL_SHA,
    TARGET_INCIDENT, TARGET_REPOSITORY, PilotContext, RemediationCase,
    evaluate_remediation_pilot,
)
from scripts.validation.classify_adaptive_assurance_scope import NOT_APPLICABLE, classify_paths  # noqa: E402

CONTRACT_PATH = ROOT / "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json"


def context(**overrides):
    data = {
        "repository": TARGET_REPOSITORY, "canonical_sha": TARGET_CANONICAL_SHA,
        "incident_reference": TARGET_INCIDENT, "mode": PILOT_MODE,
        "cud10_state": CUD10_HOLD_STATE, "source_mutation_performed": False,
        "production_evidence": False,
    }
    data.update(overrides)
    return PilotContext(**data)


def cases(after="PREVENTED", independent=True, recurrence=False):
    return tuple(
        RemediationCase(
            case_id=f"CASE-{index}-{escape_class}", escape_class=escape_class,
            before_result="REPRODUCED_DEFECT" if index < 4 else "STATIC_RISK_CONFIRMED",
            after_result=after, remediation_actions=(f"LOCK_{escape_class}",),
            evidence_ids=(f"EVIDENCE-{index}",), independent_evidence=independent,
            recurrence_observed=recurrence,
        )
        for index, escape_class in enumerate(REQUIRED_ESCAPE_CLASSES)
    )


def test_contract_is_draft_2020_12_valid_and_non_authorizing() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert contract["pilot_boundary"]["organic_effectiveness_claimed"] is False
    assert all(value is False for value in contract["authority"].values())


def test_registered_exact_aq11_scope_is_separated_from_historical_gates() -> None:
    inventory = tuple(json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["implementation_inventory"])
    for gate in ("prai", "aq5", "aq7"):
        assert classify_paths(inventory, gate) == NOT_APPLICABLE


def test_controlled_complete_pilot_passes_without_admission_authority() -> None:
    summary = evaluate_remediation_pilot(context(), cases())
    assert summary.disposition == "PASS"
    assert summary.case_count == 6
    assert summary.effective_count == 6
    assert summary.unresolved_count == 0
    assert summary.effectiveness_bps == 10000
    assert summary.authority_granted is False
    assert summary.cud10_admission_authorized is False
    assert summary.production_readiness_claimed is False
    assert summary.organic_effectiveness_claimed is False
    assert "AQ11_PASS_IS_NON_ADMITTING" in summary.reason_codes


def test_pilot_is_order_invariant() -> None:
    baseline = evaluate_remediation_pilot(context(), cases())
    shuffled = list(cases())
    random.Random(20260911).shuffle(shuffled)
    observed = evaluate_remediation_pilot(context(), shuffled)
    assert observed == baseline


def test_remaining_escape_forces_revision_required_and_preserves_hold() -> None:
    sample = list(cases())
    item = sample[0]
    sample[0] = RemediationCase(item.case_id, item.escape_class, item.before_result, "STILL_ESCAPES", item.remediation_actions, item.evidence_ids, True, False)
    summary = evaluate_remediation_pilot(context(), sample)
    assert summary.disposition == "REVISION_REQUIRED"
    assert summary.effectiveness_bps < 10000
    assert summary.cud10_admission_authorized is False
    assert "AQ11_CUD10_HOLD_PRESERVED" in summary.reason_codes


def test_recurrence_forces_revision_required() -> None:
    sample = list(cases())
    item = sample[1]
    sample[1] = RemediationCase(item.case_id, item.escape_class, item.before_result, item.after_result, item.remediation_actions, item.evidence_ids, True, True)
    assert evaluate_remediation_pilot(context(), sample).disposition == "REVISION_REQUIRED"


def test_non_independent_or_inconclusive_evidence_waits() -> None:
    assert evaluate_remediation_pilot(context(), cases(independent=False)).disposition == "WAIT_FOR_EVIDENCE"
    assert evaluate_remediation_pilot(context(), cases(after="INCONCLUSIVE")).disposition == "WAIT_FOR_EVIDENCE"


def test_missing_or_duplicate_required_class_fails_closed() -> None:
    sample = list(cases())
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), sample[:-1])
    duplicate = list(cases())
    duplicate[-1] = RemediationCase(
        duplicate[0].case_id + "-ALT", duplicate[0].escape_class,
        duplicate[-1].before_result, duplicate[-1].after_result,
        duplicate[-1].remediation_actions, duplicate[-1].evidence_ids, True, False,
    )
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), duplicate)


def test_duplicate_case_identity_fails_closed() -> None:
    sample = list(cases())
    last = sample[-1]
    sample[-1] = RemediationCase(sample[0].case_id, last.escape_class, last.before_result, last.after_result, last.remediation_actions, last.evidence_ids, True, False)
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), sample)


def test_unknown_class_and_unsafe_context_are_rejected() -> None:
    with pytest.raises(ValueError):
        RemediationCase("X", "UNKNOWN", "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(ValueError):
        context(source_mutation_performed=True)
    with pytest.raises(ValueError):
        context(production_evidence=True)
    with pytest.raises(ValueError):
        context(canonical_sha="0" * 40)
    with pytest.raises(ValueError):
        context(cud10_state="AUTHORIZED")
''')

    write("docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md", '''# ADAPT-QA AQ11: CritiQual remediation effectiveness pilot

AQ11 implements a deterministic **controlled remediation/effectiveness pilot** over known CritiQual development-assurance escape classes. Its authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`.

## Pilot boundary

The pilot is bound to the observed CritiQual canonical state `166bbac50a4f02e222aa15ff914c60cec658b7c0`, the assurance incident `Baelfyre/Padayon#441`, and mode `CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT`. CritiQual source mutation is not part of AQ11. Production evidence, deployment, providers, telemetry, release activity, and CUD10 execution remain outside scope.

AQ11 evaluates six controlled escape classes: provenance ownership, aggregate concurrency, calibration evidence integrity, authority boundaries, runtime integration, and gate-coverage truthfulness. Each class must have a before-state defect/risk observation and an after-state outcome backed by explicit evidence.

## Effectiveness semantics

A case counts as effective only when its after-state is `PREVENTED` or `DETECTED_BEFORE_TRANSITION`, the evidence is independently produced, and recurrence is not observed. A remaining escape or recurrence yields `REVISION_REQUIRED`. Inconclusive or non-independent evidence yields `WAIT_FOR_EVIDENCE`.

A complete six-of-six controlled pilot may yield `PASS`, but that result means only that the bounded pilot evidence satisfied its declared evaluator. AQ11 makes no organic effectiveness claim about live CritiQual operation and no production-readiness claim.

## CUD10 and authority boundary

CUD10 remains `READY_NOT_STARTED_HELD_BY_CURRENT_USER`. AQ11 cannot admit, resume, or execute CUD10. A pilot `PASS` is explicitly non-admitting and cannot create transition authority, execution authority, whitelist authority, protected-policy authority, threshold-lowering authority, provider/telemetry authority, production mutation authority, release authority, or deployment authority.

The Arbiter and human governance boundaries remain unchanged. Any future decision to admit CritiQual CUD10 requires its own governed evidence and authority outside AQ11.
''')

    readme_path = ROOT / "README.json"
    readme = json.loads(readme_path.read_text(encoding="utf-8"))
    mc = readme["machine_contracts"]
    additions = {
        "adaptive_assurance_aq11_contract": "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json",
        "adaptive_assurance_aq11_schema": "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json",
        "adaptive_assurance_aq11_runtime": "orchestra_runtime/domain/adaptive/remediation_effectiveness.py",
        "adaptive_assurance_aq11_validator": "scripts/validation/validate_aq11.py",
        "adaptive_assurance_aq11_validation": "tests/runtime/test_adaptive_assurance_aq11.py",
        "adaptive_assurance_aq11_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ11.md",
    }
    if any(key in mc for key in additions):
        raise RuntimeError("AQ11 README keys already exist")
    new_mc = {}
    inserted = False
    for key, value in mc.items():
        new_mc[key] = value
        if key == "adaptive_assurance_aq10_documentation":
            new_mc.update(additions)
            inserted = True
    if not inserted:
        raise RuntimeError("AQ10 README insertion anchor missing")
    readme["machine_contracts"] = new_mc
    dump("README.json", readme)

    run_tests_path = ROOT / "tests/behavior/run_tests.py"
    run_tests = run_tests_path.read_text(encoding="utf-8")
    anchor = '        {"Name": "validate_aq10.py", "Path": "scripts/validation/validate_aq10.py"},\n'
    addition = anchor + '        {"Name": "validate_aq11.py", "Path": "scripts/validation/validate_aq11.py"},\n'
    if 'validate_aq11.py' in run_tests:
        raise RuntimeError("AQ11 behavior registration already exists")
    if anchor not in run_tests:
        raise RuntimeError("AQ10 behavior registration anchor missing")
    run_tests_path.write_text(run_tests.replace(anchor, addition, 1), encoding="utf-8")

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    entry = '''## Unreleased ADAPT-QA AQ-11 CritiQual remediation effectiveness pilot

- Adds a deterministic evidence-only controlled pilot for six known CritiQual development-assurance escape classes without mutating CritiQual or resuming CUD10.
- Requires independently supported before/after evidence, treats recurrence or remaining escapes as revision-required, and treats inconclusive/non-independent evidence as wait-for-evidence.
- Binds the pilot to CritiQual canonical `166bbac50a4f02e222aa15ff914c60cec658b7c0` and Padayon incident #441 while explicitly making no organic-effectiveness or production-readiness claim.
- Keeps CUD10 held and makes any AQ11 PASS non-admitting and non-authorizing for policy, release, deployment, provider, telemetry, production, or lifecycle transitions.

'''
    if changelog.startswith("## Unreleased ADAPT-QA AQ-11"):
        raise RuntimeError("AQ11 changelog entry already exists")
    changelog_path.write_text(entry + changelog, encoding="utf-8")

    run("python", "-B", "scripts/validation/validate_aq11.py")
    run("python", "-m", "pytest", "-q", "tests/runtime/test_adaptive_assurance_aq11.py", "tests/behavior/test_protected_aq8_assurance_scope_policy.py")
    run("python", "-m", "py_compile", "orchestra_runtime/domain/adaptive/remediation_effectiveness.py", "scripts/validation/validate_aq11.py", "tests/runtime/test_adaptive_assurance_aq11.py")

    for helper in HELPERS:
        if helper.exists():
            helper.unlink()
    run("git", "add", "-A")
    changed = set(out("git", "diff", "--cached", "--name-only").splitlines())
    if changed != set(INVENTORY):
        raise RuntimeError(f"AQ11 packaging drift: {sorted(changed)}")
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "feat(aq11): add controlled remediation effectiveness pilot")
    print("AQ11_FOCUSED_BOOTSTRAP=PASS")
    print("AQ11_HEAD=" + out("git", "rev-parse", "HEAD"))
    print("AQ11_TREE=" + out("git", "rev-parse", "HEAD^{tree}"))
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
