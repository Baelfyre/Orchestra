"""Pure AQ-5 repository QA-compliance evaluation.

AQ-5 consumes AQ-4 manifests and evidence receipts. It checks that declared
paths, semantic risk, completion claims, protected gates, and executed-test
coverage agree with source-bound evidence. The result is descriptive and
never grants authority or performs I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .assurance import (
    CLAIM_SCOPE_BY_STATE,
    COMPLETION_STATES,
    REQUIRED_EVIDENCE_LAYERS,
)
from .assurance_manifest import (
    ASSURANCE_ORDER,
    EvidenceReceipt,
    AssuranceManifest,
    AssuranceManifestContractError,
    FAIL_INVALID_EXECUTION_METADATA,
    FAIL_PASS_NONZERO_EXIT,
    FAIL_RECEIPT_CANDIDATE_BINDING,
    FAIL_RECEIPT_TREE_BINDING,
    FAIL_STALE_EVIDENCE,
    FAIL_WRONG_SOURCE,
    MAX_FINAL_PR_PATHS,
    reconcile_manifest_evidence,
    validate_assurance_manifest,
)
from .risk_profiler import QUALITY_DIMENSIONS, RISK_CHARACTERISTICS, RISK_RULES


AQ5_CONTRACT_SCHEMA_VERSION = "orchestra.qa-compliance.v1"
AQ5_DECISION_SCHEMA_VERSION = "orchestra.qa-compliance-decision.v1"
AQ5_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
AQ5_PHASE = "AQ5_REPOSITORY_QA_COMPLIANCE"

QA_COMPLIANCE_FIELDS = (
    "schema_version",
    "decision_id",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "work_item_ref",
    "manifest_id",
    "result",
    "compliant",
    "failure_codes",
    "changed_paths",
    "declared_paths",
    "semantic_risks",
    "required_assurance",
    "satisfied_assurance",
    "covered_slot_ids",
    "missing_slot_ids",
    "missing_assurance",
    "evidence_receipt_ids",
    "gate_ids",
    "completion_state",
    "generated_at",
    "decision_digest",
)

ALLOWED_DECISION_RESULTS = ("PASS", "FAIL", "BLOCKED")
REQUIRED_NEGATIVE_FIXTURES = (
    "F1_SECURITY_NO_EVIDENCE",
    "F2_CONCURRENCY_NO_EVIDENCE",
    "F3_RUNTIME_ONLY_OPENAPI",
    "F4_PRODUCT_COMPLETE_WITHOUT_CALLER",
    "F5_PASS_NONZERO_EXIT",
    "F6_OLD_CANDIDATE_SHA",
    "F7_UNEXECUTED_TEST_CLAIM",
    "F8_TEST_DOES_NOT_REACH_CHANGED_CODE",
    "F9_CHANGED_PATH_OMITTED",
    "F10_POLICY_SELF_MODIFICATION",
)

FAIL_SECURITY_NO_EVIDENCE = "AQ5-F1_SECURITY_NO_EVIDENCE"
FAIL_CONCURRENCY_NO_EVIDENCE = "AQ5-F2_CONCURRENCY_NO_EVIDENCE"
FAIL_RUNTIME_ONLY_OPENAPI = "AQ5-F3_RUNTIME_ONLY_OPENAPI"
FAIL_PRODUCT_COMPLETE_WITHOUT_CALLER = "AQ5-F4_PRODUCT_COMPLETE_WITHOUT_CALLER"
FAIL_PASS_NONZERO_EXIT_CLAIM = "AQ5-F5_PASS_NONZERO_EXIT"
FAIL_OLD_CANDIDATE_SHA = "AQ5-F6_OLD_CANDIDATE_SHA"
FAIL_UNEXECUTED_TEST_CLAIM = "AQ5-F7_UNEXECUTED_TEST_CLAIM"
FAIL_TEST_DOES_NOT_REACH_CHANGED_CODE = "AQ5-F8_TEST_DOES_NOT_REACH_CHANGED_CODE"
FAIL_CHANGED_PATH_OMITTED = "AQ5-F9_CHANGED_PATH_OMITTED"
FAIL_POLICY_SELF_MODIFICATION = "AQ5-F10_POLICY_SELF_MODIFICATION"

FAIL_AQ4_INVALID = "AQ5_AQ4_INPUT_INVALID"
FAIL_AQ4_EVIDENCE_INSUFFICIENT = "AQ5_AQ4_EVIDENCE_INSUFFICIENT"
FAIL_SOURCE_BINDING = "AQ5_SOURCE_BINDING_MISMATCH"
FAIL_TREE_BINDING = "AQ5_TREE_BINDING_MISMATCH"
FAIL_SEMANTIC_RISK_UNDECLARED = "AQ5_SEMANTIC_RISK_UNDECLARED"
FAIL_REQUIRED_ASSURANCE_MISSING = "AQ5_REQUIRED_ASSURANCE_MISSING"
FAIL_COMPLETION_SCOPE = "AQ5_COMPLETION_SCOPE_INSUFFICIENT"
FAIL_GATE_EVIDENCE_MISSING = "AQ5_PROTECTED_GATE_EVIDENCE_MISSING"
FAIL_POLICY_INPUT_INVALID = "AQ5_POLICY_INPUT_INVALID"
FAIL_TEST_INPUT_INVALID = "AQ5_TEST_INPUT_INVALID"
FAIL_INVALID_INPUT = "AQ5_INVALID_INPUT"
FAIL_SCOPE_LIMIT = "AQ5_SCOPE_EXCEEDS_MAX_FINAL_PR_PATHS"

QUALITY_ASSURANCE_MAP = {
    "FUNCTIONAL_SUITABILITY": "FUNCTIONAL_ASSURANCE",
    "PERFORMANCE_EFFICIENCY": "PERFORMANCE_ASSURANCE",
    "COMPATIBILITY": "COMPATIBILITY_ASSURANCE",
    "INTERACTION_CAPABILITY": "INTERACTION_ASSURANCE",
    "RELIABILITY": "RELIABILITY_ASSURANCE",
    "SECURITY": "SECURITY_ASSURANCE",
    "MAINTAINABILITY": "MAINTAINABILITY_ASSURANCE",
    "FLEXIBILITY": "FLEXIBILITY_ASSURANCE",
    "SAFETY": "SAFETY_ASSURANCE",
    "PROVENANCE": "PROVENANCE_ASSURANCE",
    "AUTHORITY_TRUST": "AUTHORITY_TRUST_ASSURANCE",
    "PRIVACY": "PRIVACY_ASSURANCE",
    "TENANT_WORKSPACE_ISOLATION": "TENANT_ISOLATION_ASSURANCE",
    "DATA_OWNERSHIP": "DATA_OWNERSHIP_ASSURANCE",
    "CONCURRENCY": "CONCURRENCY_ASSURANCE",
    "STATE_TRANSITIONS": "STATE_TRANSITION_ASSURANCE",
    "RETRY_IDEMPOTENCY": "RETRY_IDEMPOTENCY_ASSURANCE",
    "RECOVERY_ROLLBACK": "RECOVERY_ROLLBACK_ASSURANCE",
    "EXTERNAL_INPUT": "EXTERNAL_INPUT_ASSURANCE",
    "EXTERNAL_DEPENDENCY": "EXTERNAL_PROVIDER_ASSURANCE",
    "MIGRATION": "MIGRATION_ASSURANCE",
    "DESTRUCTIVE_LIFECYCLE": "DESTRUCTIVE_LIFECYCLE_ASSURANCE",
    "HUMAN_AUTHORITY": "HUMAN_AUTHORITY_ASSURANCE",
    "OBSERVABILITY": "OBSERVABILITY_ASSURANCE",
}

PROTECTED_POLICY_PREFIXES = (
    ".github/workflows/governance-check.yml",
    ".github/workflows/qa-compliance.yml",
    "machine/governance/",
    "machine/adaptive/aq5-qa-compliance.v1.json",
    "machine/schemas/qa-compliance.v1.schema.json",
    "scripts/validation/validate_governance",
    "scripts/validation/validate_qa_compliance.py",
    "orchestra_runtime/domain/adaptive/qa_compliance.py",
)

REQUIRED_INVARIANTS = (
    "AQ4_MANIFEST_AND_RECEIPTS_MUST_BE_SEMANTICALLY_VALID",
    "CURRENT_SOURCE_CANDIDATE_TREE_MUST_MATCH_AQ4",
    "CHANGED_PATHS_MUST_EQUAL_DECLARED_PATHS",
    "SEMANTIC_RISK_MUST_BE_DECLARED_AND_ASSURED",
    "SECURITY_NEEDS_SECURITY_EVIDENCE",
    "CONCURRENCY_NEEDS_CONCURRENCY_EVIDENCE",
    "RUNTIME_NEEDS_HTTP_AND_RUNTIME_EVIDENCE",
    "PRODUCT_COMPLETE_NEEDS_CALLER_AND_INTEGRATION_EVIDENCE",
    "PASS_WITH_NONZERO_EXIT_MUST_FAIL",
    "UNEXECUTED_TEST_CLAIMS_MUST_FAIL",
    "POLICY_SELF_MODIFICATION_MUST_FAIL",
    "AQ5_DECISION_DOES_NOT_AUTHORIZE_TRANSITION",
)

AUTHORITY = {
    "decision_authorizes_execution": False,
    "decision_expands_authority": False,
    "decision_authorizes_transition": False,
    "provider_activation": False,
    "production_action": False,
    "lifecycle_transition": False,
}


class QaComplianceContractError(ValueError):
    """A fail-closed AQ-5 contract violation."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def _fail(code: str, detail: str = "") -> None:
    raise QaComplianceContractError(code, detail)


def _text(value: object, field_name: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        _fail(FAIL_INVALID_INPUT, f"{field_name} must be a bounded non-empty string")
    return value.strip()


def _sha(value: object, field_name: str) -> str:
    value = _text(value, field_name, 64).casefold()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        _fail(FAIL_INVALID_INPUT, f"{field_name} must be a lowercase Git SHA")
    return value


def _timestamp(value: object, field_name: str) -> str:
    value = _text(value, field_name, 64)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise QaComplianceContractError(FAIL_INVALID_INPUT, f"invalid {field_name}") from exc
    if parsed.tzinfo is None:
        _fail(FAIL_INVALID_INPUT, f"{field_name} must include a timezone")
    return value


def _values(value: object, field_name: str, maximum: int = 256) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or value is None:
        _fail(FAIL_INVALID_INPUT, f"{field_name} must be an iterable of strings")
    try:
        values = tuple(_text(item, field_name, maximum) for item in value)  # type: ignore[union-attr]
    except TypeError as exc:
        raise QaComplianceContractError(FAIL_INVALID_INPUT, f"{field_name} is not iterable") from exc
    if len(values) != len(set(values)):
        _fail(FAIL_INVALID_INPUT, f"{field_name} must not contain duplicates")
    return tuple(sorted(values))


def _paths(value: object, field_name: str) -> tuple[str, ...]:
    values = _values(value, field_name, 1024)
    normalized: list[str] = []
    for raw in values:
        path = raw.replace("\\", "/")
        if path.startswith("/") or re.match(r"^[A-Za-z]:/", path) or path.startswith("./"):
            _fail(FAIL_INVALID_INPUT, f"{field_name} contains an invalid path")
        if ".." in path.split("/") or not path:
            _fail(FAIL_INVALID_INPUT, f"{field_name} contains an invalid path")
        normalized.append(path)
    if len(normalized) != len(set(normalized)):
        _fail(FAIL_INVALID_INPUT, f"{field_name} contains duplicate normalized paths")
    return tuple(sorted(normalized))


def _identifiers(value: object, field_name: str) -> tuple[str, ...]:
    return _values(value, field_name, 256)


def _assurance(values: object, field_name: str) -> tuple[str, ...]:
    result = _identifiers(values, field_name)
    unknown = set(result) - set(ASSURANCE_ORDER)
    if unknown:
        _fail(FAIL_INVALID_INPUT, f"{field_name} contains unknown assurance")
    return tuple(item for item in ASSURANCE_ORDER if item in result)


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _decision_payload(
    *,
    schema_version: str,
    decision_id: str,
    repository: str,
    source_ref: str,
    candidate_sha: str,
    tree_sha: str,
    work_item_ref: str,
    manifest_id: str,
    result: str,
    failure_codes: tuple[str, ...],
    changed_paths: tuple[str, ...],
    declared_paths: tuple[str, ...],
    semantic_risks: tuple[str, ...],
    required_assurance: tuple[str, ...],
    satisfied_assurance: tuple[str, ...],
    covered_slot_ids: tuple[str, ...],
    missing_slot_ids: tuple[str, ...],
    missing_assurance: tuple[str, ...],
    evidence_receipt_ids: tuple[str, ...],
    gate_ids: tuple[str, ...],
    completion_state: str | None,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "decision_id": decision_id,
        "repository": repository,
        "source_ref": source_ref,
        "candidate_sha": candidate_sha,
        "tree_sha": tree_sha,
        "work_item_ref": work_item_ref,
        "manifest_id": manifest_id,
        "result": result,
        "compliant": result == "PASS",
        "failure_codes": list(failure_codes),
        "changed_paths": list(changed_paths),
        "declared_paths": list(declared_paths),
        "semantic_risks": list(semantic_risks),
        "required_assurance": list(required_assurance),
        "satisfied_assurance": list(satisfied_assurance),
        "covered_slot_ids": list(covered_slot_ids),
        "missing_slot_ids": list(missing_slot_ids),
        "missing_assurance": list(missing_assurance),
        "evidence_receipt_ids": list(evidence_receipt_ids),
        "gate_ids": list(gate_ids),
        "completion_state": completion_state,
        "generated_at": generated_at,
    }


@dataclass(frozen=True, slots=True)
class QaComplianceDecision:
    schema_version: str
    decision_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    manifest_id: str
    result: str
    failure_codes: tuple[str, ...]
    changed_paths: tuple[str, ...]
    declared_paths: tuple[str, ...]
    semantic_risks: tuple[str, ...]
    required_assurance: tuple[str, ...]
    satisfied_assurance: tuple[str, ...]
    covered_slot_ids: tuple[str, ...]
    missing_slot_ids: tuple[str, ...]
    missing_assurance: tuple[str, ...]
    evidence_receipt_ids: tuple[str, ...]
    gate_ids: tuple[str, ...]
    completion_state: str | None
    generated_at: str
    decision_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != AQ5_DECISION_SCHEMA_VERSION:
            _fail(FAIL_INVALID_INPUT, "unsupported AQ5 decision schema")
        for field_name in (
            "decision_id",
            "repository",
            "source_ref",
            "work_item_ref",
            "manifest_id",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(self, "candidate_sha", _sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", _sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "result", self.result if self.result in ALLOWED_DECISION_RESULTS else "")
        if not self.result:
            _fail(FAIL_INVALID_INPUT, "result is not an allowed decision result")
        object.__setattr__(self, "failure_codes", _unique(_values(self.failure_codes, "failure_codes")))
        for field_name in ("changed_paths", "declared_paths"):
            object.__setattr__(self, field_name, _paths(getattr(self, field_name), field_name))
        object.__setattr__(self, "semantic_risks", _identifiers(self.semantic_risks, "semantic_risks"))
        for field_name in ("required_assurance", "satisfied_assurance", "missing_assurance"):
            object.__setattr__(self, field_name, _assurance(getattr(self, field_name), field_name))
        for field_name in (
            "covered_slot_ids",
            "missing_slot_ids",
            "evidence_receipt_ids",
            "gate_ids",
        ):
            object.__setattr__(self, field_name, _identifiers(getattr(self, field_name), field_name))
        if self.completion_state is not None:
            object.__setattr__(self, "completion_state", _text(self.completion_state, "completion_state", 64))
            if self.completion_state not in COMPLETION_STATES:
                _fail(FAIL_INVALID_INPUT, "unknown completion_state")
        object.__setattr__(self, "generated_at", _timestamp(self.generated_at, "generated_at"))
        object.__setattr__(self, "decision_digest", _sha256(self.decision_digest))
        if self.decision_digest != _digest(self._payload()):
            _fail(FAIL_INVALID_INPUT, "decision_digest does not match canonical decision")
        if self.result == "PASS" and self.failure_codes:
            _fail(FAIL_INVALID_INPUT, "PASS decisions cannot contain failure_codes")

    def _payload(self) -> dict[str, Any]:
        return _decision_payload(
            schema_version=self.schema_version,
            decision_id=self.decision_id,
            repository=self.repository,
            source_ref=self.source_ref,
            candidate_sha=self.candidate_sha,
            tree_sha=self.tree_sha,
            work_item_ref=self.work_item_ref,
            manifest_id=self.manifest_id,
            result=self.result,
            failure_codes=self.failure_codes,
            changed_paths=self.changed_paths,
            declared_paths=self.declared_paths,
            semantic_risks=self.semantic_risks,
            required_assurance=self.required_assurance,
            satisfied_assurance=self.satisfied_assurance,
            covered_slot_ids=self.covered_slot_ids,
            missing_slot_ids=self.missing_slot_ids,
            missing_assurance=self.missing_assurance,
            evidence_receipt_ids=self.evidence_receipt_ids,
            gate_ids=self.gate_ids,
            completion_state=self.completion_state,
            generated_at=self.generated_at,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "QaComplianceDecision":
        if not isinstance(data, Mapping):
            raise TypeError("AQ5 decision must be a mapping")
        unknown = set(data) - set(QA_COMPLIANCE_FIELDS)
        if unknown:
            _fail(FAIL_INVALID_INPUT, "unsupported decision fields: " + ", ".join(sorted(unknown)))
        result = data.get("result", "")
        compliant = data.get("compliant")
        if type(compliant) is not bool or compliant != (result == "PASS"):
            _fail(FAIL_INVALID_INPUT, "compliant must match result")
        return cls(
            schema_version=data.get("schema_version", ""),
            decision_id=data.get("decision_id", ""),
            repository=data.get("repository", ""),
            source_ref=data.get("source_ref", ""),
            candidate_sha=data.get("candidate_sha", ""),
            tree_sha=data.get("tree_sha", ""),
            work_item_ref=data.get("work_item_ref", ""),
            manifest_id=data.get("manifest_id", ""),
            result=result,
            failure_codes=tuple(data.get("failure_codes", ())),
            changed_paths=tuple(data.get("changed_paths", ())),
            declared_paths=tuple(data.get("declared_paths", ())),
            semantic_risks=tuple(data.get("semantic_risks", ())),
            required_assurance=tuple(data.get("required_assurance", ())),
            satisfied_assurance=tuple(data.get("satisfied_assurance", ())),
            covered_slot_ids=tuple(data.get("covered_slot_ids", ())),
            missing_slot_ids=tuple(data.get("missing_slot_ids", ())),
            missing_assurance=tuple(data.get("missing_assurance", ())),
            evidence_receipt_ids=tuple(data.get("evidence_receipt_ids", ())),
            gate_ids=tuple(data.get("gate_ids", ())),
            completion_state=data.get("completion_state"),
            generated_at=data.get("generated_at", ""),
            decision_digest=data.get("decision_digest", ""),
        )

    @property
    def compliant(self) -> bool:
        return self.result == "PASS" and not self.failure_codes

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload()
        payload["decision_digest"] = self.decision_digest
        return payload


def _sha256(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        _fail(FAIL_INVALID_INPUT, "decision_digest must be a SHA-256 digest")
    return value


def _coerce_manifest(value: AssuranceManifest | Mapping[str, Any]) -> AssuranceManifest:
    if isinstance(value, AssuranceManifest):
        return value
    if isinstance(value, Mapping):
        return AssuranceManifest.from_mapping(value)
    raise TypeError("manifest must be an AssuranceManifest or mapping")


def _receipt_values(value: object) -> tuple[object, ...]:
    if isinstance(value, Mapping):
        if "receipts" in value:
            value = value["receipts"]
        else:
            return (value,)
    if isinstance(value, (str, bytes)) or value is None:
        raise TypeError("receipts must be an iterable")
    return tuple(value)  # type: ignore[arg-type]


def _append(failures: list[str], *codes: str) -> None:
    for code in codes:
        if code and code not in failures:
            failures.append(code)


def _risk_assurance(label: str) -> str | None:
    if label in QUALITY_ASSURANCE_MAP:
        return QUALITY_ASSURANCE_MAP[label]
    rule = RISK_RULES.get(label)
    return None if rule is None else rule[0][0]


def _is_policy_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in PROTECTED_POLICY_PREFIXES)


def _make_decision(
    manifest: AssuranceManifest,
    *,
    result: str,
    failures: Iterable[str],
    changed_paths: tuple[str, ...],
    declared_paths: tuple[str, ...],
    semantic_risks: tuple[str, ...],
    satisfied_assurance: tuple[str, ...],
    covered_slot_ids: tuple[str, ...],
    missing_slot_ids: tuple[str, ...],
    missing_assurance: tuple[str, ...],
    evidence_receipt_ids: tuple[str, ...],
    gate_ids: tuple[str, ...],
    completion_state: str | None,
    generated_at: str,
) -> QaComplianceDecision:
    failure_codes = _unique(failures)
    seed = _decision_payload(
        schema_version=AQ5_DECISION_SCHEMA_VERSION,
        decision_id="pending",
        repository=manifest.repository,
        source_ref=manifest.source_ref,
        candidate_sha=manifest.candidate_sha,
        tree_sha=manifest.tree_sha,
        work_item_ref=manifest.work_item_ref,
        manifest_id=manifest.manifest_id,
        result=result,
        failure_codes=failure_codes,
        changed_paths=changed_paths,
        declared_paths=declared_paths,
        semantic_risks=semantic_risks,
        required_assurance=manifest.required_assurance,
        satisfied_assurance=satisfied_assurance,
        covered_slot_ids=covered_slot_ids,
        missing_slot_ids=missing_slot_ids,
        missing_assurance=missing_assurance,
        evidence_receipt_ids=evidence_receipt_ids,
        gate_ids=gate_ids,
        completion_state=completion_state,
        generated_at=generated_at,
    )
    decision_id = "qa5-" + _digest(seed)[:20]
    payload = dict(seed)
    payload["decision_id"] = decision_id
    digest = _digest(payload)
    return QaComplianceDecision(
        schema_version=AQ5_DECISION_SCHEMA_VERSION,
        decision_id=decision_id,
        repository=manifest.repository,
        source_ref=manifest.source_ref,
        candidate_sha=manifest.candidate_sha,
        tree_sha=manifest.tree_sha,
        work_item_ref=manifest.work_item_ref,
        manifest_id=manifest.manifest_id,
        result=result,
        failure_codes=failure_codes,
        changed_paths=changed_paths,
        declared_paths=declared_paths,
        semantic_risks=semantic_risks,
        required_assurance=manifest.required_assurance,
        satisfied_assurance=satisfied_assurance,
        covered_slot_ids=covered_slot_ids,
        missing_slot_ids=missing_slot_ids,
        missing_assurance=missing_assurance,
        evidence_receipt_ids=evidence_receipt_ids,
        gate_ids=gate_ids,
        completion_state=completion_state,
        generated_at=generated_at,
        decision_digest=digest,
    )


def evaluate_qa_compliance(
    manifest: AssuranceManifest | Mapping[str, Any],
    receipts: Iterable[EvidenceReceipt | Mapping[str, Any]] | Mapping[str, Any],
    *,
    current_repository: str | None = None,
    current_source_ref: str | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
    changed_paths: Iterable[str] = (),
    declared_paths: Iterable[str] = (),
    semantic_risks: Iterable[str] | None = None,
    protected_gate_ids: Iterable[str] = (),
    completion_state: str | None = None,
    runtime_claimed: bool = False,
    caller_authority_ref: str | None = None,
    integration_evidence_ids: Iterable[str] = (),
    completion_evidence_ids: Iterable[str] = (),
    executed_test_ids: Iterable[str] = (),
    test_coverage: Mapping[str, Iterable[str]] | None = None,
    test_coverage_paths: Mapping[str, Iterable[str]] | None = None,
    test_claimed: bool = False,
    policy_modified_paths: Iterable[str] = (),
    policy_self_modification: bool = False,
    policy_paths: Iterable[str] = (),
    current_authority_boundary: Iterable[str] | None = None,
    evaluated_at: str | None = None,
    actual_changed_paths: Iterable[str] | None = None,
    manifest_declared_paths: Iterable[str] | None = None,
    claimed_risks: Iterable[str] | None = None,
) -> QaComplianceDecision:
    """Evaluate AQ-5 claims against a source-bound AQ-4 manifest and receipts."""

    manifest_obj = _coerce_manifest(manifest)
    failures: list[str] = []
    repository = (
        manifest_obj.repository
        if current_repository is None
        else _text(current_repository, "current_repository")
    )
    source_ref = (
        manifest_obj.source_ref
        if current_source_ref is None
        else _text(current_source_ref, "current_source_ref")
    )
    candidate_sha = (
        manifest_obj.candidate_sha
        if current_candidate_sha is None
        else _sha(current_candidate_sha, "current_candidate_sha")
    )
    tree_sha = (
        manifest_obj.tree_sha
        if current_tree_sha is None
        else _sha(current_tree_sha, "current_tree_sha")
    )
    generated_at = manifest_obj.generated_at if evaluated_at is None else _timestamp(evaluated_at, "evaluated_at")

    if current_source_ref is not None and manifest_obj.source_ref != source_ref:
        _append(failures, FAIL_SOURCE_BINDING)
    if current_candidate_sha is not None and manifest_obj.candidate_sha != candidate_sha:
        _append(failures, FAIL_OLD_CANDIDATE_SHA)
    if current_tree_sha is not None and manifest_obj.tree_sha != tree_sha:
        _append(failures, FAIL_TREE_BINDING)

    try:
        validate_assurance_manifest(
            manifest_obj,
            current_repository=repository,
            current_candidate_sha=candidate_sha,
            current_tree_sha=tree_sha,
            current_authority_boundary=current_authority_boundary,
        )
    except AssuranceManifestContractError as exc:
        _append(failures, FAIL_AQ4_INVALID, exc.code)
    except (TypeError, ValueError):
        _append(failures, FAIL_AQ4_INVALID)

    try:
        receipt_values = _receipt_values(receipts)
    except (TypeError, ValueError):
        receipt_values = ()
        _append(failures, FAIL_AQ4_INVALID)

    evidence = None
    try:
        evidence = reconcile_manifest_evidence(manifest_obj, receipt_values)
    except AssuranceManifestContractError as exc:
        _append(failures, FAIL_AQ4_INVALID, exc.code)
    except (TypeError, ValueError):
        _append(failures, FAIL_AQ4_INVALID)
    if evidence is None:
        normalized_receipts: tuple[EvidenceReceipt, ...] = ()
        satisfied_assurance: tuple[str, ...] = ()
        covered_slot_ids: tuple[str, ...] = ()
        missing_slot_ids = tuple(slot.slot_id for slot in manifest_obj.required_evidence_slots)
        missing_assurance = manifest_obj.required_assurance
        evidence_ids: tuple[str, ...] = ()
    else:
        normalized_receipts = evidence.normalized_receipts
        satisfied_assurance = evidence.satisfied_assurance
        covered_slot_ids = evidence.covered_slot_ids
        missing_slot_ids = evidence.missing_slot_ids
        missing_assurance = evidence.missing_assurance
        evidence_ids = evidence.evidence_ids
        _append(failures, *evidence.failure_codes)
        if FAIL_RECEIPT_CANDIDATE_BINDING in evidence.failure_codes or FAIL_STALE_EVIDENCE in evidence.failure_codes:
            _append(failures, FAIL_OLD_CANDIDATE_SHA)
        if FAIL_RECEIPT_TREE_BINDING in evidence.failure_codes:
            _append(failures, FAIL_TREE_BINDING)
        if FAIL_WRONG_SOURCE in evidence.failure_codes:
            _append(failures, FAIL_SOURCE_BINDING)
        if not evidence.sufficient:
            _append(failures, FAIL_AQ4_EVIDENCE_INSUFFICIENT)

    raw_changed_paths = changed_paths if actual_changed_paths is None else actual_changed_paths
    raw_declared_paths = declared_paths if manifest_declared_paths is None else manifest_declared_paths
    normalized_changed_paths = _paths(raw_changed_paths, "changed_paths")
    normalized_declared_paths = _paths(raw_declared_paths, "declared_paths")
    if normalized_changed_paths != normalized_declared_paths:
        _append(failures, FAIL_CHANGED_PATH_OMITTED)
    if len(normalized_changed_paths) > MAX_FINAL_PR_PATHS:
        _append(failures, FAIL_SCOPE_LIMIT)

    risk_values = semantic_risks
    if risk_values is None:
        risk_values = tuple(
            dict.fromkeys((*manifest_obj.quality_dimensions, *manifest_obj.risk_characteristics))
        )
    if claimed_risks is not None:
        risk_values = claimed_risks
    normalized_risks = _identifiers(risk_values, "semantic_risks")
    known_semantics = set(QUALITY_DIMENSIONS) | set(RISK_CHARACTERISTICS)
    declared_semantics = set(manifest_obj.quality_dimensions) | set(manifest_obj.risk_characteristics)
    for risk in normalized_risks:
        if risk not in known_semantics or risk not in declared_semantics:
            _append(failures, FAIL_SEMANTIC_RISK_UNDECLARED)
            continue
        assurance = _risk_assurance(risk)
        if assurance is None or assurance not in set(manifest_obj.required_assurance):
            _append(failures, FAIL_REQUIRED_ASSURANCE_MISSING)
        elif assurance not in set(satisfied_assurance):
            _append(failures, FAIL_REQUIRED_ASSURANCE_MISSING)

    pass_layers = {receipt.evidence_layer for receipt in normalized_receipts if receipt.result == "PASS"}
    security_semantics = {
        "SECURITY",
        "AUTHENTICATION",
        "AUTHORIZATION",
        "PRIVILEGE_MUTATION",
        "MULTI_TENANT",
    }
    concurrency_semantics = {"CONCURRENCY", "MULTI_ACTOR", "AGGREGATE_INVARIANT"}
    if security_semantics.intersection(normalized_risks) and "SECURITY" not in pass_layers:
        _append(failures, FAIL_SECURITY_NO_EVIDENCE)
    if concurrency_semantics.intersection(normalized_risks) and "CONCURRENCY" not in pass_layers:
        _append(failures, FAIL_CONCURRENCY_NO_EVIDENCE)
    if "PROVENANCE" in normalized_risks and "PROVENANCE" not in pass_layers:
        _append(failures, FAIL_REQUIRED_ASSURANCE_MISSING)

    requested_gate_values = tuple(protected_gate_ids)
    requested_gates = _identifiers(
        requested_gate_values if requested_gate_values else manifest_obj.protected_gates,
        "protected_gate_ids",
    )
    slot_ids = {slot.slot_id.casefold() for slot in manifest_obj.required_evidence_slots}
    pass_gate_ids = {
        receipt.gate_id.casefold()
        for receipt in normalized_receipts
        if receipt.result == "PASS"
    }
    for gate_id in requested_gates:
        gate_key = gate_id.casefold()
        if gate_key in slot_ids and gate_key not in pass_gate_ids:
            _append(failures, FAIL_GATE_EVIDENCE_MISSING)
        elif gate_key not in slot_ids and requested_gate_values:
            _append(failures, FAIL_GATE_EVIDENCE_MISSING)

    normalized_completion_state = None
    normalized_caller_authority_ref = None
    if caller_authority_ref is not None:
        normalized_caller_authority_ref = _text(caller_authority_ref, "caller_authority_ref")
    if type(runtime_claimed) is not bool or type(test_claimed) is not bool:
        _append(failures, FAIL_INVALID_INPUT)
    if completion_state is not None:
        completion_value = _text(completion_state, "completion_state", 64)
        if completion_value not in COMPLETION_STATES:
            _append(failures, FAIL_COMPLETION_SCOPE)
        else:
            normalized_completion_state = completion_value
            required_layers = set(REQUIRED_EVIDENCE_LAYERS[normalized_completion_state])
            if not required_layers.issubset(pass_layers):
                _append(failures, FAIL_COMPLETION_SCOPE)
            if normalized_completion_state == "RUNTIME_VERIFIED" and not {
                "HTTP",
                "RUNTIME",
            }.issubset(pass_layers):
                _append(failures, FAIL_RUNTIME_ONLY_OPENAPI)
            if normalized_completion_state == "PRODUCT_COMPLETE":
                integration_ids = _identifiers(
                    tuple(dict.fromkeys(integration_evidence_ids)),
                    "integration_evidence_ids",
                )
                completion_ids = _identifiers(
                    tuple(dict.fromkeys(completion_evidence_ids)),
                    "completion_evidence_ids",
                )
                if (
                    not normalized_caller_authority_ref
                    or not integration_ids
                    or not completion_ids
                    or not set(integration_ids + completion_ids).issubset(set(evidence_ids))
                    or not {"INTEGRATION", "HTTP", "RUNTIME"}.intersection(pass_layers)
                ):
                    _append(failures, FAIL_PRODUCT_COMPLETE_WITHOUT_CALLER)
            elif normalized_completion_state == "RUNTIME_VERIFIED":
                if not {"HTTP", "RUNTIME"}.issubset(pass_layers):
                    _append(failures, FAIL_COMPLETION_SCOPE)

    if runtime_claimed and not {"HTTP", "RUNTIME"}.issubset(pass_layers):
        _append(failures, FAIL_RUNTIME_ONLY_OPENAPI, FAIL_COMPLETION_SCOPE)

    coverage = test_coverage if test_coverage is not None else test_coverage_paths
    executed_test_values = tuple(executed_test_ids)
    if test_claimed or coverage is not None or executed_test_values:
        executed_ids = _identifiers(executed_test_values, "executed_test_ids")
        if not isinstance(coverage, Mapping) or not executed_ids:
            _append(failures, FAIL_UNEXECUTED_TEST_CLAIM)
        else:
            covered_paths: set[str] = set()
            for test_id in executed_ids:
                if test_id not in coverage:
                    _append(failures, FAIL_UNEXECUTED_TEST_CLAIM)
                    continue
                try:
                    covered_paths.update(_paths(coverage[test_id], f"test_coverage[{test_id}]"))
                except (TypeError, ValueError):
                    _append(failures, FAIL_UNEXECUTED_TEST_CLAIM)
            if not set(normalized_changed_paths).issubset(covered_paths):
                _append(failures, FAIL_TEST_DOES_NOT_REACH_CHANGED_CODE)

    for code in (FAIL_PASS_NONZERO_EXIT, FAIL_INVALID_EXECUTION_METADATA):
        if evidence is not None and code in evidence.failure_codes:
            _append(
                failures,
                FAIL_PASS_NONZERO_EXIT_CLAIM if code == FAIL_PASS_NONZERO_EXIT else FAIL_UNEXECUTED_TEST_CLAIM,
            )

    normalized_policy_paths = _paths(policy_modified_paths, "policy_modified_paths")
    policy_path_values = tuple(policy_paths)
    normalized_policy_prefixes = (
        _paths(policy_path_values, "policy_paths") if policy_path_values else ()
    )
    if type(policy_self_modification) is not bool:
        _append(failures, FAIL_POLICY_INPUT_INVALID)
    if policy_self_modification or any(_is_policy_path(path) for path in normalized_policy_paths):
        _append(failures, FAIL_POLICY_SELF_MODIFICATION)
    if normalized_policy_prefixes and any(
        any(path == prefix or path.startswith(prefix) for prefix in normalized_policy_prefixes)
        for path in normalized_changed_paths
    ):
        _append(failures, FAIL_POLICY_SELF_MODIFICATION)

    result = "PASS" if not failures else "FAIL"
    return _make_decision(
        manifest_obj,
        result=result,
        failures=failures,
        changed_paths=normalized_changed_paths,
        declared_paths=normalized_declared_paths,
        semantic_risks=normalized_risks,
        satisfied_assurance=satisfied_assurance,
        covered_slot_ids=covered_slot_ids,
        missing_slot_ids=missing_slot_ids,
        missing_assurance=missing_assurance,
        evidence_receipt_ids=evidence_ids,
        gate_ids=requested_gates,
        completion_state=normalized_completion_state,
        generated_at=generated_at,
    )


def validate_qa_compliance(
    manifest: AssuranceManifest | Mapping[str, Any],
    receipts: Iterable[EvidenceReceipt | Mapping[str, Any]] | Mapping[str, Any],
    **kwargs: Any,
) -> QaComplianceDecision:
    """Compatibility name for the pure AQ-5 evaluator."""

    return evaluate_qa_compliance(manifest, receipts, **kwargs)


def assert_qa_compliance(
    decision_or_manifest: QaComplianceDecision | AssuranceManifest | Mapping[str, Any],
    receipts: Iterable[EvidenceReceipt | Mapping[str, Any]] | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> QaComplianceDecision:
    """Return a compliant decision or raise a fail-closed contract error."""

    if isinstance(decision_or_manifest, QaComplianceDecision):
        decision = decision_or_manifest
    elif receipts is not None:
        decision = evaluate_qa_compliance(decision_or_manifest, receipts, **kwargs)
    else:
        _fail(FAIL_INVALID_INPUT, "assert_qa_compliance needs receipts")
    if not decision.compliant:
        _fail(FAIL_INVALID_INPUT, "AQ5 decision is not compliant")
    return decision


def validate_qa_compliance_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the machine AQ-5 contract against runtime constants."""

    if not isinstance(contract, Mapping):
        raise TypeError("AQ5 machine contract must be a mapping")
    constraints = {
        "pure_domain": True,
        "network_access": False,
        "provider_access": False,
        "repository_mutation": False,
        "test_execution": False,
        "promotion_or_transition": False,
        "aq6_plus_implementation": False,
    }
    expected = {
        "schema_version": AQ5_CONTRACT_SCHEMA_VERSION,
        "phase": AQ5_PHASE,
        "owner": "overseer",
        "authority_model": AQ5_AUTHORITY_MODEL,
        "decision_schema_version": AQ5_DECISION_SCHEMA_VERSION,
        "decision_fields": list(QA_COMPLIANCE_FIELDS),
        "required_negative_fixtures": list(REQUIRED_NEGATIVE_FIXTURES),
        "required_invariants": list(REQUIRED_INVARIANTS),
        "max_final_pr_paths": MAX_FINAL_PR_PATHS,
        "quality_assurance_map": dict(QUALITY_ASSURANCE_MAP),
        "completion_claim_scopes": dict(CLAIM_SCOPE_BY_STATE),
        "required_completion_layers": {
            state: list(layers) for state, layers in REQUIRED_EVIDENCE_LAYERS.items()
        },
        "protected_policy_prefixes": list(PROTECTED_POLICY_PREFIXES),
        "authority": dict(AUTHORITY),
        "constraints": constraints,
    }
    unknown = set(contract) - set(expected)
    if unknown:
        _fail(FAIL_INVALID_INPUT, "unsupported contract fields: " + ", ".join(sorted(unknown)))
    for field_name, expected_value in expected.items():
        if contract.get(field_name) != expected_value:
            _fail(FAIL_INVALID_INPUT, f"machine contract drift: {field_name}")
    return contract


validate_machine_contract = validate_qa_compliance_contract
validate_schema_runtime_parity = validate_qa_compliance_contract
evaluate_repository_qa_compliance = evaluate_qa_compliance
QAComplianceDecision = QaComplianceDecision


__all__ = [
    "AQ5_CONTRACT_SCHEMA_VERSION",
    "AQ5_DECISION_SCHEMA_VERSION",
    "AQ5_AUTHORITY_MODEL",
    "AQ5_PHASE",
    "QA_COMPLIANCE_FIELDS",
    "ALLOWED_DECISION_RESULTS",
    "REQUIRED_NEGATIVE_FIXTURES",
    "REQUIRED_INVARIANTS",
    "QUALITY_ASSURANCE_MAP",
    "PROTECTED_POLICY_PREFIXES",
    "AUTHORITY",
    "QaComplianceContractError",
    "QaComplianceDecision",
    "QAComplianceDecision",
    "evaluate_qa_compliance",
    "evaluate_repository_qa_compliance",
    "validate_qa_compliance",
    "assert_qa_compliance",
    "validate_qa_compliance_contract",
    "validate_machine_contract",
    "validate_schema_runtime_parity",
    "FAIL_SECURITY_NO_EVIDENCE",
    "FAIL_CONCURRENCY_NO_EVIDENCE",
    "FAIL_RUNTIME_ONLY_OPENAPI",
    "FAIL_PRODUCT_COMPLETE_WITHOUT_CALLER",
    "FAIL_PASS_NONZERO_EXIT_CLAIM",
    "FAIL_OLD_CANDIDATE_SHA",
    "FAIL_UNEXECUTED_TEST_CLAIM",
    "FAIL_TEST_DOES_NOT_REACH_CHANGED_CODE",
    "FAIL_CHANGED_PATH_OMITTED",
    "FAIL_POLICY_SELF_MODIFICATION",
    "FAIL_AQ4_INVALID",
    "FAIL_AQ4_EVIDENCE_INSUFFICIENT",
    "FAIL_SOURCE_BINDING",
    "FAIL_TREE_BINDING",
    "FAIL_SEMANTIC_RISK_UNDECLARED",
    "FAIL_REQUIRED_ASSURANCE_MISSING",
    "FAIL_COMPLETION_SCOPE",
    "FAIL_GATE_EVIDENCE_MISSING",
    "FAIL_POLICY_INPUT_INVALID",
    "FAIL_TEST_INPUT_INVALID",
    "FAIL_INVALID_INPUT",
    "FAIL_SCOPE_LIMIT",
]
