"""Pure AQ-4 assurance manifest and evidence receipt contracts.

AQ-4 consumes qualified AQ-1/AQ-2/AQ-3 values. It validates deterministic
manifest identity, evidence-slot coverage, provenance, and sufficiency without
performing I/O, dispatch, lifecycle transitions, or promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

from .assurance import (
    COMPLETION_STATES,
    DEVELOPMENT_MODES,
    EVIDENCE_LAYERS,
    EVIDENCE_SCOPES,
    PROVENANCE_QUALIFICATIONS,
    SOURCE_TRUTH_LABELS,
)
from .risk_profiler import (
    ASSURANCE_ORDER,
    AdaptiveRiskProfile,
    QUALITY_DIMENSIONS,
    RISK_CHARACTERISTICS,
    RiskProfileInput,
    profile_risk,
)
from .specialist_assurance import (
    CANONICAL_SPECIALIST_ORDER,
    SpecialistAssuranceReceipt,
    validate_routing_receipt,
)


AQ4_CONTRACT_SCHEMA_VERSION = "orchestra.assurance-manifests-receipts.v1"
AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION = "orchestra.assurance-manifest.v1"
AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION = "orchestra.evidence-receipt.v1"
AQ4_AUTHORITY_RULE = "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION"
AQ4_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
MAX_FINAL_PR_PATHS = 9

ASSURANCE_MANIFEST_FIELDS = (
    "schema_version",
    "manifest_id",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "work_item_ref",
    "development_mode",
    "change_class",
    "quality_dimensions",
    "risk_characteristics",
    "invariants",
    "risk_fingerprint",
    "selected_specialists",
    "required_assurance",
    "completion_target",
    "protected_gates",
    "authority_boundary",
    "required_evidence_slots",
    "generated_at",
    "manifest_digest",
)
EVIDENCE_SLOT_FIELDS = (
    "slot_id",
    "assurance_class",
    "required_layer",
    "required_scope",
    "required_validator",
    "required_source_truth",
    "required_provenance",
    "covered_risks",
    "covered_invariants",
    "candidate_binding_required",
    "tree_binding_required",
    "freshness_binding_required",
    "independence_required",
)
EVIDENCE_RECEIPT_FIELDS = (
    "schema_version",
    "receipt_id",
    "manifest_id",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "work_item_ref",
    "gate_id",
    "gate_type",
    "command_or_workflow",
    "result",
    "observed_at",
    "producer",
    "validator",
    "source_truth",
    "provenance_qualification",
    "evidence_layer",
    "evidence_scope",
    "covered_risks",
    "covered_invariants",
    "limitations",
    "evidence_digest",
)
OPTIONAL_RECEIPT_IDENTITY_FIELDS = (
    "workflow_run_id",
    "job_or_check_id",
    "exit_code",
    "logical_identity",
)

ALLOWED_RECEIPT_RESULTS = ("PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE")
REQUIRED_NEGATIVE_TESTS = tuple(f"AQ4-N{index}" for index in range(1, 19))
REQUIRED_PROPERTY_TESTS = (
    "DETERMINISM",
    "ORDER_INVARIANCE",
    "ASSURANCE_MONOTONICITY",
    "AUTHORITY_NON_EXPANSION",
    "IDENTITY_MONOTONICITY",
    "CONTRADICTION_MONOTONICITY",
    "DUPLICATE_NORMALIZATION",
)

FAIL_UNKNOWN_ASSURANCE_TYPE = "AQ4-N1_UNKNOWN_ASSURANCE_TYPE"
FAIL_REQUIRED_MANIFEST_FIELD = "AQ4-N2_MISSING_REQUIRED_MANIFEST_FIELD"
FAIL_REQUIRED_RECEIPT_FIELD = "AQ4-N3_MISSING_REQUIRED_RECEIPT_FIELD"
FAIL_RECEIPT_CANDIDATE_BINDING = "AQ4-N4_RECEIPT_CANDIDATE_MISMATCH"
FAIL_RECEIPT_TREE_BINDING = "AQ4-N5_RECEIPT_TREE_MISMATCH"
FAIL_PASS_NONZERO_EXIT = "AQ4-N6_PASS_WITH_NONZERO_EXIT"
FAIL_WRONG_SOURCE = "AQ4-N7_WRONG_REPOSITORY_OR_SOURCE"
FAIL_STALE_EVIDENCE = "AQ4-N8_STALE_CANDIDATE_OR_FRESHNESS_BINDING"
FAIL_CONTRADICTORY_EVIDENCE = "AQ4-N9_CONTRADICTORY_EVIDENCE"
FAIL_INDEPENDENT_EVIDENCE_REUSE = "AQ4-N10_REUSED_INDEPENDENT_EVIDENCE"
FAIL_BROAD_COVERAGE = "AQ4-N11_BROADER_COVERAGE_THAN_GATE"
FAIL_LOWER_EVIDENCE_LAYER = "AQ4-N12_LOWER_EVIDENCE_LAYER"
FAIL_SELF_CERTIFIED_INDEPENDENT = "AQ4-N13_IMPLEMENTER_SELF_CERTIFIED"
FAIL_CALLER_AUTHORED_PROVENANCE = "AQ4-N14_CALLER_AUTHORED_PROVENANCE"
FAIL_WEAKENED_PREDECESSOR_ASSURANCE = "AQ4-N15_WEAKENED_AQ2_AQ3_ASSURANCE"
FAIL_AUTHORITY_EXPANSION = "AQ4-N16_AUTHORITY_EXPANSION"
FAIL_SEMANTIC_DRIFT = "AQ4-N17_SCHEMA_RUNTIME_SEMANTIC_DRIFT"
FAIL_DUPLICATE_NOT_ADDITIVE = "AQ4-N18_DUPLICATE_RECEIPT_NOT_ADDITIVE"
FAIL_INVALID_DIGEST = "AQ4_INVALID_DIGEST"
FAIL_REQUIRED_SLOT_UNSATISFIED = "AQ4_REQUIRED_SLOT_UNSATISFIED"
FAIL_INVALID_EXECUTION_METADATA = "AQ4_INVALID_EXECUTION_METADATA"
FAIL_INVALID_FIELD = "AQ4_INVALID_FIELD"

FAILURE_CODES = (
    FAIL_UNKNOWN_ASSURANCE_TYPE,
    FAIL_REQUIRED_MANIFEST_FIELD,
    FAIL_REQUIRED_RECEIPT_FIELD,
    FAIL_RECEIPT_CANDIDATE_BINDING,
    FAIL_RECEIPT_TREE_BINDING,
    FAIL_PASS_NONZERO_EXIT,
    FAIL_WRONG_SOURCE,
    FAIL_STALE_EVIDENCE,
    FAIL_CONTRADICTORY_EVIDENCE,
    FAIL_INDEPENDENT_EVIDENCE_REUSE,
    FAIL_BROAD_COVERAGE,
    FAIL_LOWER_EVIDENCE_LAYER,
    FAIL_SELF_CERTIFIED_INDEPENDENT,
    FAIL_CALLER_AUTHORED_PROVENANCE,
    FAIL_WEAKENED_PREDECESSOR_ASSURANCE,
    FAIL_AUTHORITY_EXPANSION,
    FAIL_SEMANTIC_DRIFT,
    FAIL_DUPLICATE_NOT_ADDITIVE,
    FAIL_INVALID_DIGEST,
    FAIL_REQUIRED_SLOT_UNSATISFIED,
    FAIL_INVALID_EXECUTION_METADATA,
    FAIL_INVALID_FIELD,
)

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_:-]{0,127}$")
_CALLER_PRODUCERS = {"caller", "client", "requester", "author", "consumer"}
_AUTHORITY_EXPANSION_MARKERS = (
    "AQ5",
    "CREDENTIAL",
    "DEPLOY",
    "GLOBAL_AUTHORITY",
    "POLICY_ACTIVATION",
    "PRODUCTION",
    "PROVIDER",
    "PUBLISH",
    "RELEASE",
)


class AssuranceManifestContractError(ValueError):
    """AQ-4 contract failure with a machine-readable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code if not detail else f"{code}: {detail}")


def _fail(code: str, detail: str = "") -> None:
    raise AssuranceManifestContractError(code, detail)


def _text(value: object, field_name: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return normalized


def _values(
    value: object,
    field_name: str,
    *,
    maximum: int = 128,
    casefold: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if len(raw) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} items")
    normalized = [
        _text(item, field_name).casefold() if casefold else _text(item, field_name)
        for item in raw
    ]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(normalized))


def _identifiers(value: object, field_name: str, *, maximum: int = 128) -> tuple[str, ...]:
    normalized = tuple(item.upper() for item in _values(value, field_name, maximum=maximum))
    invalid = [item for item in normalized if _IDENTIFIER_RE.fullmatch(item) is None]
    if invalid:
        raise ValueError(f"{field_name} contains unsupported identifiers: {', '.join(invalid)}")
    return normalized


def _ordered(
    value: object,
    field_name: str,
    order: tuple[str, ...],
    *,
    casefold: bool = False,
) -> tuple[str, ...]:
    raw = _values(value, field_name, maximum=len(order), casefold=casefold)
    normalized_order = tuple(item.casefold() for item in order) if casefold else order
    unknown = sorted(set(raw) - set(normalized_order))
    if unknown:
        code = (
            FAIL_UNKNOWN_ASSURANCE_TYPE
            if field_name in {"assurance_class", "required_assurance"}
            else FAIL_INVALID_FIELD
        )
        _fail(code, f"{field_name}: {', '.join(unknown)}")
    return tuple(
        item for item, normalized in zip(order, normalized_order) if normalized in set(raw)
    )


def _one_of(value: object, choices: tuple[str, ...], field_name: str) -> str:
    normalized = _text(value, field_name)
    if normalized not in choices:
        raise ValueError(f"{field_name} is unsupported: {normalized}")
    return normalized


def _git_sha(value: object, field_name: str) -> str:
    normalized = _text(value, field_name, maximum=40).casefold()
    if _SHA1_RE.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a 40-character lowercase Git SHA")
    return normalized


def _sha256(value: object, field_name: str) -> str:
    normalized = _text(value, field_name, maximum=64).casefold()
    if _SHA256_RE.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


def _timestamp(value: object, field_name: str) -> str:
    normalized = _text(value, field_name, maximum=64)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return normalized


def _timestamp_value(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _optional_identity(value: object, field_name: str) -> str | int | None:
    if value is None:
        return None
    if type(value) is int:
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value
    return _text(value, field_name, maximum=256)


def _exact_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be an exact boolean")
    return value


def _reject_authority_expansion(values: Iterable[str], field_name: str) -> None:
    for value in values:
        if any(marker in value.upper() for marker in _AUTHORITY_EXPANSION_MARKERS):
            _fail(FAIL_AUTHORITY_EXPANSION, f"{field_name} contains authority marker: {value}")


def _list_text(value: object, field_name: str, *, maximum: int = 128) -> tuple[str, ...]:
    return _values(value, field_name, maximum=maximum)


@dataclass(frozen=True, slots=True)
class EvidenceSlot:
    slot_id: str
    assurance_class: str
    required_layer: str
    required_scope: str
    required_validator: str
    required_source_truth: str
    required_provenance: str
    covered_risks: tuple[str, ...] = ()
    covered_invariants: tuple[str, ...] = ()
    candidate_binding_required: bool = True
    tree_binding_required: bool = True
    freshness_binding_required: bool = True
    independence_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "slot_id", _text(self.slot_id, "slot_id", maximum=128))
        object.__setattr__(
            self,
            "assurance_class",
            _ordered((self.assurance_class,), "assurance_class", ASSURANCE_ORDER)[0],
        )
        object.__setattr__(
            self, "required_layer", _one_of(self.required_layer, EVIDENCE_LAYERS, "required_layer")
        )
        object.__setattr__(
            self, "required_scope", _one_of(self.required_scope, EVIDENCE_SCOPES, "required_scope")
        )
        object.__setattr__(
            self,
            "required_validator",
            _text(self.required_validator, "required_validator").casefold(),
        )
        object.__setattr__(
            self,
            "required_source_truth",
            _one_of(self.required_source_truth, SOURCE_TRUTH_LABELS, "required_source_truth"),
        )
        object.__setattr__(
            self,
            "required_provenance",
            _one_of(self.required_provenance, PROVENANCE_QUALIFICATIONS, "required_provenance"),
        )
        object.__setattr__(self, "covered_risks", _identifiers(self.covered_risks, "covered_risks"))
        object.__setattr__(
            self, "covered_invariants", _identifiers(self.covered_invariants, "covered_invariants")
        )
        for field_name in (
            "candidate_binding_required",
            "tree_binding_required",
            "freshness_binding_required",
            "independence_required",
        ):
            object.__setattr__(self, field_name, _exact_bool(getattr(self, field_name), field_name))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "EvidenceSlot":
        if not isinstance(data, Mapping):
            raise TypeError("evidence slot must be a mapping")
        missing = [field for field in EVIDENCE_SLOT_FIELDS if field not in data]
        if missing:
            _fail(FAIL_REQUIRED_MANIFEST_FIELD, "evidence slot fields missing: " + ", ".join(missing))
        unknown = sorted(set(data) - set(EVIDENCE_SLOT_FIELDS))
        if unknown:
            _fail(FAIL_INVALID_FIELD, "unsupported evidence slot fields: " + ", ".join(unknown))
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "assurance_class": self.assurance_class,
            "required_layer": self.required_layer,
            "required_scope": self.required_scope,
            "required_validator": self.required_validator,
            "required_source_truth": self.required_source_truth,
            "required_provenance": self.required_provenance,
            "covered_risks": list(self.covered_risks),
            "covered_invariants": list(self.covered_invariants),
            "candidate_binding_required": self.candidate_binding_required,
            "tree_binding_required": self.tree_binding_required,
            "freshness_binding_required": self.freshness_binding_required,
            "independence_required": self.independence_required,
        }


@dataclass(frozen=True, slots=True)
class AssuranceManifest:
    manifest_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    development_mode: str
    change_class: str
    quality_dimensions: tuple[str, ...]
    risk_characteristics: tuple[str, ...]
    invariants: tuple[str, ...]
    risk_fingerprint: str
    selected_specialists: tuple[str, ...]
    required_assurance: tuple[str, ...]
    completion_target: str
    protected_gates: tuple[str, ...]
    authority_boundary: tuple[str, ...]
    required_evidence_slots: tuple[EvidenceSlot, ...]
    generated_at: str
    manifest_digest: str = ""
    schema_version: str = AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION:
            _fail(FAIL_SEMANTIC_DRIFT, "unsupported AQ4 manifest schema")
        object.__setattr__(self, "manifest_id", _text(self.manifest_id, "manifest_id", maximum=128))
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "candidate_sha", _git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", _git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "work_item_ref", _text(self.work_item_ref, "work_item_ref"))
        object.__setattr__(
            self,
            "development_mode",
            _one_of(self.development_mode, DEVELOPMENT_MODES, "development_mode"),
        )
        object.__setattr__(self, "change_class", _identifiers((self.change_class,), "change_class")[0])
        object.__setattr__(
            self,
            "quality_dimensions",
            _ordered(self.quality_dimensions, "quality_dimensions", QUALITY_DIMENSIONS),
        )
        object.__setattr__(
            self,
            "risk_characteristics",
            _ordered(self.risk_characteristics, "risk_characteristics", RISK_CHARACTERISTICS),
        )
        object.__setattr__(self, "invariants", _identifiers(self.invariants, "invariants"))
        object.__setattr__(self, "risk_fingerprint", _sha256(self.risk_fingerprint, "risk_fingerprint"))
        object.__setattr__(
            self,
            "selected_specialists",
            _ordered(
                self.selected_specialists,
                "selected_specialists",
                CANONICAL_SPECIALIST_ORDER,
                casefold=True,
            ),
        )
        object.__setattr__(
            self,
            "required_assurance",
            _ordered(self.required_assurance, "required_assurance", ASSURANCE_ORDER),
        )
        object.__setattr__(
            self,
            "completion_target",
            _text(self.completion_target, "completion_target", maximum=128),
        )
        object.__setattr__(self, "protected_gates", _identifiers(self.protected_gates, "protected_gates"))
        authority = _identifiers(self.authority_boundary, "authority_boundary")
        if not authority:
            raise ValueError("authority_boundary must be explicit and non-empty")
        _reject_authority_expansion(authority, "authority_boundary")
        object.__setattr__(self, "authority_boundary", authority)
        if isinstance(self.required_evidence_slots, (str, bytes)):
            raise TypeError("required_evidence_slots must be iterable")
        slots = tuple(
            sorted(
                (
                    item if isinstance(item, EvidenceSlot) else EvidenceSlot.from_mapping(item)
                    for item in self.required_evidence_slots
                ),
                key=lambda item: item.slot_id,
            )
        )
        if not slots:
            _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, "manifest requires at least one evidence slot")
        slot_ids = tuple(slot.slot_id for slot in slots)
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("required_evidence_slots must have unique slot_id values")
        object.__setattr__(self, "required_evidence_slots", slots)
        object.__setattr__(self, "generated_at", _timestamp(self.generated_at, "generated_at"))
        provided = self.manifest_digest
        if provided:
            provided = _sha256(provided, "manifest_digest")
        expected = _digest(self._payload_without_digest())
        if provided and provided != expected:
            _fail(FAIL_INVALID_DIGEST, "manifest digest does not match canonical payload")
        object.__setattr__(self, "manifest_digest", provided or expected)

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "development_mode": self.development_mode,
            "change_class": self.change_class,
            "quality_dimensions": list(self.quality_dimensions),
            "risk_characteristics": list(self.risk_characteristics),
            "invariants": list(self.invariants),
            "risk_fingerprint": self.risk_fingerprint,
            "selected_specialists": list(self.selected_specialists),
            "required_assurance": list(self.required_assurance),
            "completion_target": self.completion_target,
            "protected_gates": list(self.protected_gates),
            "authority_boundary": list(self.authority_boundary),
            "required_evidence_slots": [slot.to_dict() for slot in self.required_evidence_slots],
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AssuranceManifest":
        if not isinstance(data, Mapping):
            raise TypeError("AQ4 manifest must be a mapping")
        missing = [field for field in ASSURANCE_MANIFEST_FIELDS if field not in data]
        if missing:
            _fail(FAIL_REQUIRED_MANIFEST_FIELD, "manifest fields missing: " + ", ".join(missing))
        unknown = sorted(set(data) - set(ASSURANCE_MANIFEST_FIELDS))
        if unknown:
            _fail(FAIL_INVALID_FIELD, "unsupported manifest fields: " + ", ".join(unknown))
        values = dict(data)
        values["required_evidence_slots"] = tuple(values["required_evidence_slots"])
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload_without_digest(), "manifest_digest": self.manifest_digest}


@dataclass(frozen=True, slots=True)
class EvidenceReceipt:
    receipt_id: str
    manifest_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    gate_id: str
    gate_type: str
    command_or_workflow: str
    result: str
    observed_at: str
    producer: str
    validator: str
    source_truth: str
    provenance_qualification: str
    evidence_layer: str
    evidence_scope: str
    covered_risks: tuple[str, ...]
    covered_invariants: tuple[str, ...]
    limitations: tuple[str, ...]
    evidence_digest: str = ""
    workflow_run_id: str | int | None = None
    job_or_check_id: str | int | None = None
    exit_code: int | None = None
    logical_identity: str | None = None
    schema_version: str = AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION:
            _fail(FAIL_STALE_EVIDENCE, "unsupported AQ4 evidence receipt schema")
        object.__setattr__(self, "receipt_id", _text(self.receipt_id, "receipt_id", maximum=128))
        object.__setattr__(self, "manifest_id", _text(self.manifest_id, "manifest_id", maximum=128))
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "candidate_sha", _git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", _git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "work_item_ref", _text(self.work_item_ref, "work_item_ref"))
        object.__setattr__(self, "gate_id", _text(self.gate_id, "gate_id", maximum=128))
        object.__setattr__(self, "gate_type", _identifiers((self.gate_type,), "gate_type")[0])
        object.__setattr__(
            self,
            "command_or_workflow",
            _text(self.command_or_workflow, "command_or_workflow", maximum=512),
        )
        object.__setattr__(self, "result", _one_of(self.result, ALLOWED_RECEIPT_RESULTS, "result"))
        if self.result == "PASS":
            if self.gate_type in {"COMMAND", "LOCAL_COMMAND", "TEST"} and self.exit_code is None:
                _fail(FAIL_INVALID_EXECUTION_METADATA, "PASS command/test receipt needs exit_code")
            if self.gate_type in {"CI", "WORKFLOW"} and (
                self.workflow_run_id is None and self.job_or_check_id is None
            ):
                _fail(FAIL_INVALID_EXECUTION_METADATA, "PASS workflow receipt needs run/check identity")
        object.__setattr__(self, "observed_at", _timestamp(self.observed_at, "observed_at"))
        object.__setattr__(self, "producer", _text(self.producer, "producer").casefold())
        object.__setattr__(self, "validator", _text(self.validator, "validator").casefold())
        object.__setattr__(
            self,
            "source_truth",
            _one_of(self.source_truth, SOURCE_TRUTH_LABELS, "source_truth"),
        )
        object.__setattr__(
            self,
            "provenance_qualification",
            _one_of(
                self.provenance_qualification,
                PROVENANCE_QUALIFICATIONS,
                "provenance_qualification",
            ),
        )
        object.__setattr__(
            self, "evidence_layer", _one_of(self.evidence_layer, EVIDENCE_LAYERS, "evidence_layer")
        )
        object.__setattr__(
            self, "evidence_scope", _one_of(self.evidence_scope, EVIDENCE_SCOPES, "evidence_scope")
        )
        object.__setattr__(self, "covered_risks", _identifiers(self.covered_risks, "covered_risks"))
        object.__setattr__(
            self, "covered_invariants", _identifiers(self.covered_invariants, "covered_invariants")
        )
        object.__setattr__(self, "limitations", _list_text(self.limitations, "limitations"))
        object.__setattr__(self, "workflow_run_id", _optional_identity(self.workflow_run_id, "workflow_run_id"))
        object.__setattr__(self, "job_or_check_id", _optional_identity(self.job_or_check_id, "job_or_check_id"))
        if self.exit_code is not None and (type(self.exit_code) is not int or self.exit_code < 0):
            raise ValueError("exit_code must be a non-negative integer")
        if self.result == "PASS" and self.exit_code is not None and self.exit_code != 0:
            _fail(FAIL_PASS_NONZERO_EXIT, "PASS receipt has nonzero exit_code")
        logical = self.logical_identity
        if logical is None:
            run_identity = self.workflow_run_id if self.workflow_run_id is not None else self.job_or_check_id
            logical = f"{self.gate_id}:{run_identity if run_identity is not None else self.command_or_workflow}"
        object.__setattr__(self, "logical_identity", _text(logical, "logical_identity", maximum=256))
        provided = self.evidence_digest
        if provided:
            provided = _sha256(provided, "evidence_digest")
        expected = _digest(self._payload_without_digest())
        if provided and provided != expected:
            _fail(FAIL_INVALID_DIGEST, "evidence digest does not match canonical payload")
        object.__setattr__(self, "evidence_digest", provided or expected)

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "manifest_id": self.manifest_id,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "command_or_workflow": self.command_or_workflow,
            "result": self.result,
            "observed_at": self.observed_at,
            "producer": self.producer,
            "validator": self.validator,
            "source_truth": self.source_truth,
            "provenance_qualification": self.provenance_qualification,
            "evidence_layer": self.evidence_layer,
            "evidence_scope": self.evidence_scope,
            "covered_risks": list(self.covered_risks),
            "covered_invariants": list(self.covered_invariants),
            "limitations": list(self.limitations),
            "workflow_run_id": self.workflow_run_id,
            "job_or_check_id": self.job_or_check_id,
            "exit_code": self.exit_code,
            "logical_identity": self.logical_identity,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "EvidenceReceipt":
        if not isinstance(data, Mapping):
            raise TypeError("AQ4 evidence receipt must be a mapping")
        missing = [field for field in EVIDENCE_RECEIPT_FIELDS if field not in data]
        if missing:
            _fail(FAIL_REQUIRED_RECEIPT_FIELD, "receipt fields missing: " + ", ".join(missing))
        allowed = set(EVIDENCE_RECEIPT_FIELDS) | set(OPTIONAL_RECEIPT_IDENTITY_FIELDS)
        unknown = sorted(set(data) - allowed)
        if unknown:
            _fail(FAIL_INVALID_FIELD, "unsupported receipt fields: " + ", ".join(unknown))
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload_without_digest(), "evidence_digest": self.evidence_digest}


@dataclass(frozen=True, slots=True)
class ManifestEvidenceEvaluation:
    manifest_id: str
    required_assurance: tuple[str, ...]
    satisfied_assurance: tuple[str, ...]
    covered_slot_ids: tuple[str, ...]
    missing_slot_ids: tuple[str, ...]
    missing_assurance: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    duplicate_receipt_ids: tuple[str, ...]
    failure_codes: tuple[str, ...]
    normalized_receipts: tuple[EvidenceReceipt, ...]

    @property
    def assurance_count(self) -> int:
        return len(self.satisfied_assurance)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_ids)

    @property
    def sufficient(self) -> bool:
        return not self.failure_codes and not self.missing_slot_ids and not self.missing_assurance

    @property
    def is_sufficient(self) -> bool:
        return self.sufficient

    @property
    def can_advance(self) -> bool:
        return self.sufficient

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "required_assurance": list(self.required_assurance),
            "satisfied_assurance": list(self.satisfied_assurance),
            "covered_slot_ids": list(self.covered_slot_ids),
            "missing_slot_ids": list(self.missing_slot_ids),
            "missing_assurance": list(self.missing_assurance),
            "evidence_ids": list(self.evidence_ids),
            "duplicate_receipt_ids": list(self.duplicate_receipt_ids),
            "failure_codes": list(self.failure_codes),
            "assurance_count": self.assurance_count,
            "evidence_count": self.evidence_count,
            "sufficient": self.sufficient,
        }


ManifestEvidenceReconciliation = ManifestEvidenceEvaluation
AssuranceManifestValidation = ManifestEvidenceEvaluation

def _coerce_manifest(value: AssuranceManifest | Mapping[str, Any]) -> AssuranceManifest:
    if isinstance(value, AssuranceManifest):
        return value
    if isinstance(value, Mapping):
        return AssuranceManifest.from_mapping(value)
    raise TypeError("manifest must be an AssuranceManifest or mapping")


def _coerce_receipt(value: EvidenceReceipt | Mapping[str, Any]) -> EvidenceReceipt:
    if isinstance(value, EvidenceReceipt):
        return value
    if isinstance(value, Mapping):
        return EvidenceReceipt.from_mapping(value)
    raise TypeError("receipt must be an EvidenceReceipt or mapping")


def _qualified_profile(profile: AdaptiveRiskProfile) -> AdaptiveRiskProfile:
    if not isinstance(profile, AdaptiveRiskProfile):
        raise TypeError("aq2_profile must be an AdaptiveRiskProfile")
    try:
        expected = profile_risk(
            RiskProfileInput(
                development_mode=profile.development_mode,
                material_behavior=profile.material_behavior,
                authority_boundary=profile.authority_boundary,
                changed_domains=profile.changed_domains,
                changed_paths=profile.changed_paths,
                quality_dimensions=profile.quality_dimensions,
                risk_characteristics=profile.risk_characteristics,
                invariants=profile.invariants,
                protected_gates=profile.protected_gates,
            )
        )
    except (TypeError, ValueError) as exc:
        raise AssuranceManifestContractError(
            FAIL_WEAKENED_PREDECESSOR_ASSURANCE,
            "AQ2 profile is not a qualified profiler result",
        ) from exc
    if profile != expected:
        _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "AQ2 profile does not match profiler output")
    return profile


def _slot_map(manifest: AssuranceManifest) -> dict[str, EvidenceSlot]:
    return {slot.slot_id: slot for slot in manifest.required_evidence_slots}


def _ordered_failures(values: Iterable[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(code for code in FAILURE_CODES if code in present)


def validate_assurance_manifest(
    manifest: AssuranceManifest | Mapping[str, Any],
    *,
    current_repository: str | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
    current_authority_boundary: Iterable[str] | None = None,
    aq2_profile: AdaptiveRiskProfile | None = None,
    aq3_receipt: SpecialistAssuranceReceipt | None = None,
) -> AssuranceManifest:
    """Validate identity, predecessor inheritance, slots, and authority."""

    manifest = _coerce_manifest(manifest)
    if current_repository is not None and manifest.repository != _text(current_repository, "current_repository"):
        _fail(FAIL_WRONG_SOURCE, "manifest repository does not match current repository")
    if current_candidate_sha is not None and manifest.candidate_sha != _git_sha(current_candidate_sha, "current_candidate_sha"):
        _fail(FAIL_RECEIPT_CANDIDATE_BINDING, "manifest candidate does not match current candidate")
    if current_tree_sha is not None and manifest.tree_sha != _git_sha(current_tree_sha, "current_tree_sha"):
        _fail(FAIL_RECEIPT_TREE_BINDING, "manifest tree does not match current candidate tree")
    if current_authority_boundary is not None:
        allowed = set(_identifiers(current_authority_boundary, "current_authority_boundary"))
        if not set(manifest.authority_boundary).issubset(allowed):
            _fail(FAIL_AUTHORITY_EXPANSION, "manifest authority exceeds current authorized boundary")

    inherited_assurance: set[str] = set()
    inherited_specialists: set[str] = set()
    inherited_protected: set[str] = set()
    if aq2_profile is not None:
        profile = _qualified_profile(aq2_profile)
        inherited_assurance.update(profile.required_assurance_classes)
        inherited_specialists.update(profile.recommended_specialists)
        inherited_protected.update(profile.protected_gates)
        expected_fields = {
            "development_mode": profile.development_mode,
            "quality_dimensions": profile.quality_dimensions,
            "risk_characteristics": profile.risk_characteristics,
            "invariants": profile.invariants,
            "risk_fingerprint": profile.risk_fingerprint,
            "authority_boundary": profile.authority_boundary,
        }
        for field_name, expected in expected_fields.items():
            if getattr(manifest, field_name) != expected:
                _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, f"manifest is not bound to AQ2 {field_name}")
    if aq3_receipt is not None:
        if aq2_profile is None:
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "AQ3 receipt requires qualified AQ2 profile")
        validate_routing_receipt(aq3_receipt, aq2_profile)
        inherited_assurance.update(aq3_receipt.required_assurance)
        inherited_specialists.update(aq3_receipt.selected_specialists)
        inherited_protected.update(aq3_receipt.protected_gates)
        if manifest.source_ref not in set(aq3_receipt.source_identities):
            _fail(FAIL_WRONG_SOURCE, "manifest source is not bound to AQ3 source identities")
        if not set(aq3_receipt.required_assurance).issubset(set(manifest.required_assurance)):
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "manifest weakens AQ3 required assurance")
        if not set(aq3_receipt.selected_specialists).issubset(set(manifest.selected_specialists)):
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "manifest weakens AQ3 selected specialists")
    if inherited_assurance:
        if not inherited_assurance.issubset(set(manifest.required_assurance)):
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "manifest weakens predecessor assurance")
        if not inherited_specialists.issubset(set(manifest.selected_specialists)):
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "manifest weakens predecessor specialist selection")
        if not inherited_protected.issubset(set(manifest.protected_gates)):
            _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "manifest weakens predecessor protected gates")
    if "INDEPENDENT_QA" not in manifest.required_assurance or "overseer" not in manifest.selected_specialists:
        _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "AQ4 requires inherited independent Overseer assurance")

    slots = _slot_map(manifest)
    required = set(manifest.required_assurance)
    slot_assurance = {slot.assurance_class for slot in slots.values()}
    if not required.issubset(slot_assurance):
        _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, "required assurance class has no evidence slot")
    for slot in slots.values():
        if slot.required_validator not in set(manifest.selected_specialists):
            _fail(
                FAIL_INVALID_EXECUTION_METADATA,
                f"slot {slot.slot_id} validator is not selected",
            )
        if not set(slot.covered_risks).issubset(set(manifest.risk_characteristics)):
            _fail(FAIL_BROAD_COVERAGE, f"slot {slot.slot_id} covers undeclared risk")
        if not set(slot.covered_invariants).issubset(set(manifest.invariants)):
            _fail(FAIL_BROAD_COVERAGE, f"slot {slot.slot_id} covers undeclared invariant")
    independent = [slot for slot in slots.values() if slot.assurance_class == "INDEPENDENT_QA"]
    if not independent or not any(slot.independence_required for slot in independent):
        _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, "INDEPENDENT_QA requires independent slot")
    return manifest


def build_assurance_manifest(
    profile: AdaptiveRiskProfile | None = None,
    receipt: SpecialistAssuranceReceipt | None = None,
    *,
    aq2_profile: AdaptiveRiskProfile | None = None,
    aq3_receipt: SpecialistAssuranceReceipt | None = None,
    manifest_id: str,
    repository: str,
    source_ref: str,
    candidate_sha: str,
    tree_sha: str,
    work_item_ref: str,
    change_class: str,
    completion_target: str,
    required_evidence_slots: Iterable[EvidenceSlot | Mapping[str, Any]],
    generated_at: str,
    development_mode: str | None = None,
    quality_dimensions: Iterable[str] | None = None,
    risk_characteristics: Iterable[str] | None = None,
    invariants: Iterable[str] | None = None,
    risk_fingerprint: str | None = None,
    selected_specialists: Iterable[str] | None = None,
    required_assurance: Iterable[str] | None = None,
    protected_gates: Iterable[str] | None = None,
    authority_boundary: Iterable[str] | None = None,
) -> AssuranceManifest:
    """Build one manifest from qualified predecessor contracts and explicit slots."""

    if profile is not None and aq2_profile is not None and profile != aq2_profile:
        _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "conflicting AQ2 profile arguments")
    if receipt is not None and aq3_receipt is not None and receipt != aq3_receipt:
        _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "conflicting AQ3 receipt arguments")
    profile = aq2_profile or profile
    receipt = aq3_receipt or receipt
    if receipt is not None and profile is None:
        _fail(FAIL_WEAKENED_PREDECESSOR_ASSURANCE, "AQ3 receipt requires AQ2 profile")
    if profile is not None:
        profile = _qualified_profile(profile)
    if receipt is not None:
        validate_routing_receipt(receipt, profile)

    def inherited(name: str, explicit: Any, source: Any) -> Any:
        if explicit is not None:
            return explicit
        if source is None:
            raise TypeError(f"{name} is required when predecessor contract is absent")
        return source

    manifest = AssuranceManifest(
        manifest_id=manifest_id,
        repository=repository,
        source_ref=source_ref,
        candidate_sha=candidate_sha,
        tree_sha=tree_sha,
        work_item_ref=work_item_ref,
        development_mode=inherited(
            "development_mode",
            development_mode,
            None if profile is None else profile.development_mode,
        ),
        change_class=change_class,
        quality_dimensions=inherited(
            "quality_dimensions",
            quality_dimensions,
            None if profile is None else profile.quality_dimensions,
        ),
        risk_characteristics=inherited(
            "risk_characteristics",
            risk_characteristics,
            None if profile is None else profile.risk_characteristics,
        ),
        invariants=inherited(
            "invariants", invariants, None if profile is None else profile.invariants
        ),
        risk_fingerprint=inherited(
            "risk_fingerprint",
            risk_fingerprint,
            None if profile is None else profile.risk_fingerprint,
        ),
        selected_specialists=inherited(
            "selected_specialists",
            selected_specialists,
            None
            if receipt is None and profile is None
            else (receipt.selected_specialists if receipt is not None else profile.recommended_specialists),
        ),
        required_assurance=inherited(
            "required_assurance",
            required_assurance,
            None
            if receipt is None and profile is None
            else (receipt.required_assurance if receipt is not None else profile.required_assurance_classes),
        ),
        completion_target=completion_target,
        protected_gates=inherited(
            "protected_gates",
            protected_gates,
            None
            if receipt is None and profile is None
            else (receipt.protected_gates if receipt is not None else profile.protected_gates),
        ),
        authority_boundary=inherited(
            "authority_boundary",
            authority_boundary,
            None
            if receipt is None and profile is None
            else (receipt.authority_boundary if receipt is not None else profile.authority_boundary),
        ),
        required_evidence_slots=tuple(required_evidence_slots),
        generated_at=generated_at,
    )
    return validate_assurance_manifest(
        manifest,
        current_repository=repository,
        current_candidate_sha=candidate_sha,
        current_tree_sha=tree_sha,
        aq2_profile=profile,
        aq3_receipt=receipt,
    )


_LAYER_RANK = {
    "STATIC": 0,
    "UNIT": 1,
    "DOMAIN": 2,
    "CONTRACT": 3,
    "INTEGRATION": 4,
    "HTTP": 5,
    "RUNTIME": 6,
}
_SCOPE_COVERAGE = {
    "SOURCE": {"SOURCE"},
    "COMPLETION": {"COMPLETION"},
    "DOMAIN": {"DOMAIN"},
    "APPLICATION": {"DOMAIN", "APPLICATION"},
    "API": {"API", "APPLICATION", "DOMAIN"},
    "UI": {"UI", "APPLICATION", "DOMAIN"},
    "UNIT": {"UNIT"},
    "CONTRACT": {"CONTRACT"},
    "INTEGRATION": {"INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"},
    "RUNTIME": {"RUNTIME", "INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"},
    "PERSISTENCE": {"PERSISTENCE"},
    "CONCURRENCY": {"CONCURRENCY"},
    "SECURITY": {"SECURITY"},
    "ADVERSARIAL": {"ADVERSARIAL"},
    "CANONICAL": {"CANONICAL"},
    "PRODUCT": {"PRODUCT"},
    "EMPIRICAL_EFFECTIVENESS": {"EMPIRICAL_EFFECTIVENESS"},
}


def _layer_satisfies(observed: str, required: str) -> bool:
    if observed == required:
        return True
    return (
        observed in _LAYER_RANK
        and required in _LAYER_RANK
        and _LAYER_RANK[observed] >= _LAYER_RANK[required]
    )


def _scope_satisfies(observed: str, required: str) -> bool:
    return required in _SCOPE_COVERAGE.get(observed, {observed})


def _coerce_slot(value: EvidenceSlot | Mapping[str, Any]) -> EvidenceSlot:
    if isinstance(value, EvidenceSlot):
        return value
    if isinstance(value, Mapping):
        return EvidenceSlot.from_mapping(value)
    raise TypeError("slot must be an EvidenceSlot or mapping")


def validate_evidence_receipt(
    receipt: EvidenceReceipt | Mapping[str, Any],
    manifest: AssuranceManifest | Mapping[str, Any] | None = None,
    *,
    slot: EvidenceSlot | Mapping[str, Any] | None = None,
    current_repository: str | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
) -> EvidenceReceipt:
    """Validate one receipt against its manifest slot and current identity."""

    receipt = _coerce_receipt(receipt)
    manifest_obj = _coerce_manifest(manifest) if manifest is not None else None
    slot_obj = _coerce_slot(slot) if slot is not None else None

    if current_repository is not None and receipt.repository != _text(
        current_repository, "current_repository"
    ):
        _fail(FAIL_WRONG_SOURCE, "receipt repository does not match current repository")
    if current_candidate_sha is not None and receipt.candidate_sha != _git_sha(
        current_candidate_sha, "current_candidate_sha"
    ):
        _fail(FAIL_RECEIPT_CANDIDATE_BINDING, "receipt candidate does not match current candidate")
    if current_tree_sha is not None and receipt.tree_sha != _git_sha(
        current_tree_sha, "current_tree_sha"
    ):
        _fail(FAIL_RECEIPT_TREE_BINDING, "receipt tree does not match current candidate tree")

    if manifest_obj is not None:
        validate_assurance_manifest(manifest_obj)
        for field_name in ("manifest_id", "repository", "source_ref", "work_item_ref"):
            if getattr(receipt, field_name) != getattr(manifest_obj, field_name):
                _fail(FAIL_WRONG_SOURCE, f"receipt {field_name} is not manifest-bound")
        if receipt.candidate_sha != manifest_obj.candidate_sha:
            _fail(FAIL_RECEIPT_CANDIDATE_BINDING, "receipt candidate is not manifest-bound")
        if receipt.tree_sha != manifest_obj.tree_sha:
            _fail(FAIL_RECEIPT_TREE_BINDING, "receipt tree is not manifest-bound")
        if _timestamp_value(receipt.observed_at) < _timestamp_value(manifest_obj.generated_at):
            _fail(FAIL_STALE_EVIDENCE, "receipt predates manifest generation")
        if slot_obj is None:
            slot_obj = _slot_map(manifest_obj).get(receipt.gate_id)
            if slot_obj is None:
                _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, f"unknown manifest slot: {receipt.gate_id}")

    if slot_obj is not None:
        if receipt.gate_id != slot_obj.slot_id:
            _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, "receipt gate_id does not identify the supplied slot")
        if receipt.validator != slot_obj.required_validator:
            _fail(FAIL_INVALID_EXECUTION_METADATA, "receipt validator does not match required validator")
        if receipt.source_truth != slot_obj.required_source_truth:
            _fail(FAIL_INVALID_EXECUTION_METADATA, "receipt source truth does not match required source truth")
        if receipt.provenance_qualification != slot_obj.required_provenance:
            _fail(FAIL_INVALID_EXECUTION_METADATA, "receipt provenance does not match required provenance")
        if not _layer_satisfies(receipt.evidence_layer, slot_obj.required_layer):
            _fail(FAIL_LOWER_EVIDENCE_LAYER, "receipt evidence layer is below the required layer")
        if not _scope_satisfies(receipt.evidence_scope, slot_obj.required_scope):
            _fail(FAIL_LOWER_EVIDENCE_LAYER, "receipt evidence scope is below the required scope")
        if not set(receipt.covered_risks).issubset(set(slot_obj.covered_risks)):
            _fail(FAIL_BROAD_COVERAGE, "receipt claims risks beyond its slot")
        if not set(receipt.covered_invariants).issubset(set(slot_obj.covered_invariants)):
            _fail(FAIL_BROAD_COVERAGE, "receipt claims invariants beyond its slot")
        if slot_obj.independence_required:
            if receipt.producer == receipt.validator:
                _fail(FAIL_SELF_CERTIFIED_INDEPENDENT, "independent evidence is self-certified")
            if receipt.provenance_qualification != "AUTHORITATIVE":
                _fail(FAIL_SELF_CERTIFIED_INDEPENDENT, "independent evidence is not authoritative")

    if receipt.producer in _CALLER_PRODUCERS and receipt.provenance_qualification == "AUTHORITATIVE":
        _fail(FAIL_CALLER_AUTHORED_PROVENANCE, "caller-authored provenance cannot be authoritative")
    if manifest_obj is not None and receipt.observed_at < manifest_obj.generated_at:
        _fail(FAIL_STALE_EVIDENCE, "receipt freshness is older than manifest")
    return receipt


def _inherited_values(
    value: Iterable[str] | None,
    fallback: Iterable[str],
) -> tuple[str, ...]:
    return tuple(fallback if value is None else value)


def build_evidence_receipt(
    manifest: AssuranceManifest | Mapping[str, Any],
    *,
    receipt_id: str,
    gate_id: str,
    gate_type: str,
    command_or_workflow: str,
    result: str,
    observed_at: str,
    producer: str,
    validator: str | None = None,
    source_truth: str | None = None,
    provenance_qualification: str | None = None,
    evidence_layer: str | None = None,
    evidence_scope: str | None = None,
    covered_risks: Iterable[str] | None = None,
    covered_invariants: Iterable[str] | None = None,
    limitations: Iterable[str] = (),
    workflow_run_id: str | int | None = None,
    job_or_check_id: str | int | None = None,
    exit_code: int | None = None,
    logical_identity: str | None = None,
) -> EvidenceReceipt:
    """Build one manifest-bound evidence receipt for a declared slot."""

    manifest_obj = validate_assurance_manifest(manifest)
    slot = _slot_map(manifest_obj).get(gate_id)
    if slot is None:
        _fail(FAIL_REQUIRED_SLOT_UNSATISFIED, f"unknown manifest slot: {gate_id}")
    receipt = EvidenceReceipt(
        receipt_id=receipt_id,
        manifest_id=manifest_obj.manifest_id,
        repository=manifest_obj.repository,
        source_ref=manifest_obj.source_ref,
        candidate_sha=manifest_obj.candidate_sha,
        tree_sha=manifest_obj.tree_sha,
        work_item_ref=manifest_obj.work_item_ref,
        gate_id=gate_id,
        gate_type=gate_type,
        command_or_workflow=command_or_workflow,
        result=result,
        observed_at=observed_at,
        producer=producer,
        validator=slot.required_validator if validator is None else validator,
        source_truth=slot.required_source_truth if source_truth is None else source_truth,
        provenance_qualification=(
            slot.required_provenance
            if provenance_qualification is None
            else provenance_qualification
        ),
        evidence_layer=slot.required_layer if evidence_layer is None else evidence_layer,
        evidence_scope=slot.required_scope if evidence_scope is None else evidence_scope,
        covered_risks=_inherited_values(covered_risks, slot.covered_risks),
        covered_invariants=_inherited_values(covered_invariants, slot.covered_invariants),
        limitations=limitations,
        workflow_run_id=workflow_run_id,
        job_or_check_id=job_or_check_id,
        exit_code=exit_code,
        logical_identity=logical_identity,
    )
    return validate_evidence_receipt(receipt, manifest_obj, slot=slot)




def validate_assurance_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate machine-contract semantics against runtime constants."""

    if not isinstance(contract, Mapping):
        raise TypeError("AQ4 machine contract must be a mapping")
    expected = {
        "schema_version": AQ4_CONTRACT_SCHEMA_VERSION,
        "authority_model": AQ4_AUTHORITY_MODEL,
        "manifest_fields": list(ASSURANCE_MANIFEST_FIELDS),
        "evidence_slot_fields": list(EVIDENCE_SLOT_FIELDS),
        "receipt_fields": list(EVIDENCE_RECEIPT_FIELDS),
        "optional_receipt_identity_fields": list(OPTIONAL_RECEIPT_IDENTITY_FIELDS),
        "allowed_results": list(ALLOWED_RECEIPT_RESULTS),
        "development_modes": list(DEVELOPMENT_MODES),
        "evidence_layers": list(EVIDENCE_LAYERS),
        "evidence_scopes": list(EVIDENCE_SCOPES),
        "source_truth_labels": list(SOURCE_TRUTH_LABELS),
        "provenance_qualifications": list(PROVENANCE_QUALIFICATIONS),
        "completion_states": list(COMPLETION_STATES),
        "assurance_order": list(ASSURANCE_ORDER),
        "canonical_specialist_order": list(CANONICAL_SPECIALIST_ORDER),
        "required_negative_tests": list(REQUIRED_NEGATIVE_TESTS),
        "required_property_tests": list(REQUIRED_PROPERTY_TESTS),
    }
    for field_name, expected_value in expected.items():
        if contract.get(field_name) != expected_value:
            _fail(FAIL_SEMANTIC_DRIFT, f"machine contract drift: {field_name}")
    if contract.get("max_final_pr_paths") != MAX_FINAL_PR_PATHS:
        _fail(FAIL_SEMANTIC_DRIFT, "machine contract drift: max_final_pr_paths")
    authority = contract.get("authority")
    expected_authority = {
        "manifest_authorizes_execution": False,
        "manifest_expands_authority": False,
        "receipt_authorizes_transition": False,
        "provider_activation": False,
        "production_action": False,
        "lifecycle_transition": False,
    }
    if authority != expected_authority:
        _fail(FAIL_SEMANTIC_DRIFT, "machine contract drift: authority")
    return contract


validate_machine_contract = validate_assurance_contract
validate_schema_runtime_parity = validate_assurance_contract


def _execution_identity(receipt: EvidenceReceipt) -> tuple[str, str, str] | None:
    execution_id = (
        receipt.workflow_run_id
        if receipt.workflow_run_id is not None
        else receipt.job_or_check_id
    )
    if execution_id is None:
        return None
    kind = "workflow" if receipt.workflow_run_id is not None else "job"
    return (receipt.gate_id, kind, str(execution_id))


def _receipt_sort_key(receipt: EvidenceReceipt) -> tuple[str, str, str]:
    return (receipt.gate_id, receipt.logical_identity, receipt.receipt_id)


def reconcile_manifest_evidence(
    manifest: AssuranceManifest | Mapping[str, Any],
    receipts: Iterable[EvidenceReceipt | Mapping[str, Any]],
) -> ManifestEvidenceEvaluation:
    """Normalize receipts and evaluate complete slot and assurance coverage."""

    manifest = validate_assurance_manifest(manifest)
    if isinstance(receipts, (str, bytes)):
        raise TypeError("receipts must be an iterable of EvidenceReceipt values")

    failures: list[str] = []
    parsed: list[EvidenceReceipt] = []
    try:
        candidates = tuple(receipts)
    except TypeError as exc:
        raise TypeError("receipts must be an iterable of EvidenceReceipt values") from exc

    for candidate in candidates:
        try:
            parsed.append(validate_evidence_receipt(candidate, manifest))
        except AssuranceManifestContractError as exc:
            failures.append(exc.code)
        except (TypeError, ValueError):
            failures.append(FAIL_INVALID_FIELD)

    by_receipt_id: dict[str, EvidenceReceipt] = {}
    normalized: list[EvidenceReceipt] = []
    duplicate_ids: set[str] = set()
    for receipt in parsed:
        previous = by_receipt_id.get(receipt.receipt_id)
        if previous is None:
            by_receipt_id[receipt.receipt_id] = receipt
            normalized.append(receipt)
            continue
        duplicate_ids.add(receipt.receipt_id)
        if previous.to_dict() != receipt.to_dict():
            failures.append(FAIL_CONTRADICTORY_EVIDENCE)

    logical_groups: dict[str, list[EvidenceReceipt]] = {}
    for receipt in normalized:
        logical_groups.setdefault(receipt.logical_identity, []).append(receipt)

    contradictory_logicals: set[str] = set()
    for logical_identity, group in logical_groups.items():
        results = {item.result for item in group}
        if len(results) > 1:
            failures.append(FAIL_CONTRADICTORY_EVIDENCE)
            contradictory_logicals.add(logical_identity)
            continue
        if len(group) > 1:
            slots = [_slot_map(manifest)[item.gate_id] for item in group]
            if any(slot.independence_required for slot in slots):
                failures.append(FAIL_INDEPENDENT_EVIDENCE_REUSE)
            else:
                failures.append(FAIL_DUPLICATE_NOT_ADDITIVE)
            duplicate_ids.update(item.receipt_id for item in group[1:])

    execution_groups: dict[tuple[str, str, str], list[EvidenceReceipt]] = {}
    for receipt in normalized:
        identity = _execution_identity(receipt)
        if identity is not None:
            execution_groups.setdefault(identity, []).append(receipt)
    for group in execution_groups.values():
        if len({item.result for item in group}) > 1:
            failures.append(FAIL_CONTRADICTORY_EVIDENCE)

    normalized = sorted(normalized, key=_receipt_sort_key)
    slot_map = _slot_map(manifest)
    covered_slot_ids = {
        item.gate_id
        for item in normalized
        if item.result == "PASS" and item.logical_identity not in contradictory_logicals
    }
    covered_slot_ids_ordered = tuple(
        slot.slot_id for slot in manifest.required_evidence_slots if slot.slot_id in covered_slot_ids
    )
    missing_slot_ids = tuple(
        slot.slot_id
        for slot in manifest.required_evidence_slots
        if slot.slot_id not in covered_slot_ids
    )
    satisfied_set = {
        slot_map[slot_id].assurance_class for slot_id in covered_slot_ids if slot_id in slot_map
    }
    satisfied_assurance = tuple(
        assurance for assurance in manifest.required_assurance if assurance in satisfied_set
    )
    missing_assurance = tuple(
        assurance
        for assurance in manifest.required_assurance
        if assurance not in set(satisfied_assurance)
    )
    if missing_slot_ids:
        failures.append(FAIL_REQUIRED_SLOT_UNSATISFIED)

    return ManifestEvidenceEvaluation(
        manifest_id=manifest.manifest_id,
        required_assurance=manifest.required_assurance,
        satisfied_assurance=satisfied_assurance,
        covered_slot_ids=covered_slot_ids_ordered,
        missing_slot_ids=missing_slot_ids,
        missing_assurance=missing_assurance,
        evidence_ids=tuple(item.receipt_id for item in normalized),
        duplicate_receipt_ids=tuple(sorted(duplicate_ids)),
        failure_codes=_ordered_failures(failures),
        normalized_receipts=tuple(normalized),
    )


def evaluate_manifest_sufficiency(
    manifest: AssuranceManifest | Mapping[str, Any],
    receipts: Iterable[EvidenceReceipt | Mapping[str, Any]],
) -> ManifestEvidenceEvaluation:
    """Compatibility name for manifest evidence sufficiency evaluation."""

    return reconcile_manifest_evidence(manifest, receipts)


AssuranceEvidenceSlot = EvidenceSlot
AssuranceEvidenceReceipt = EvidenceReceipt
ManifestSufficiencyEvaluation = ManifestEvidenceEvaluation


__all__ = [
    "AQ4_CONTRACT_SCHEMA_VERSION",
    "AQ4_ASSURANCE_MANIFEST_SCHEMA_VERSION",
    "AQ4_EVIDENCE_RECEIPT_SCHEMA_VERSION",
    "AQ4_AUTHORITY_RULE",
    "AQ4_AUTHORITY_MODEL",
    "MAX_FINAL_PR_PATHS",
    "ASSURANCE_MANIFEST_FIELDS",
    "EVIDENCE_SLOT_FIELDS",
    "EVIDENCE_RECEIPT_FIELDS",
    "OPTIONAL_RECEIPT_IDENTITY_FIELDS",
    "ALLOWED_RECEIPT_RESULTS",
    "REQUIRED_NEGATIVE_TESTS",
    "REQUIRED_PROPERTY_TESTS",
    "FAILURE_CODES",
    "FAIL_UNKNOWN_ASSURANCE_TYPE",
    "FAIL_REQUIRED_MANIFEST_FIELD",
    "FAIL_REQUIRED_RECEIPT_FIELD",
    "FAIL_RECEIPT_CANDIDATE_BINDING",
    "FAIL_RECEIPT_TREE_BINDING",
    "FAIL_PASS_NONZERO_EXIT",
    "FAIL_WRONG_SOURCE",
    "FAIL_STALE_EVIDENCE",
    "FAIL_CONTRADICTORY_EVIDENCE",
    "FAIL_INDEPENDENT_EVIDENCE_REUSE",
    "FAIL_BROAD_COVERAGE",
    "FAIL_LOWER_EVIDENCE_LAYER",
    "FAIL_SELF_CERTIFIED_INDEPENDENT",
    "FAIL_CALLER_AUTHORED_PROVENANCE",
    "FAIL_WEAKENED_PREDECESSOR_ASSURANCE",
    "FAIL_AUTHORITY_EXPANSION",
    "FAIL_SEMANTIC_DRIFT",
    "FAIL_DUPLICATE_NOT_ADDITIVE",
    "FAIL_INVALID_DIGEST",
    "FAIL_REQUIRED_SLOT_UNSATISFIED",
    "FAIL_INVALID_EXECUTION_METADATA",
    "FAIL_INVALID_FIELD",
    "AssuranceManifestContractError",
    "EvidenceSlot",
    "AssuranceEvidenceSlot",
    "AssuranceManifest",
    "EvidenceReceipt",
    "AssuranceEvidenceReceipt",
    "ManifestEvidenceEvaluation",
    "ManifestEvidenceReconciliation",
    "ManifestSufficiencyEvaluation",
    "AssuranceManifestValidation",
    "validate_assurance_manifest",
    "build_assurance_manifest",
    "validate_evidence_receipt",
    "build_evidence_receipt",
    "reconcile_manifest_evidence",
    "evaluate_manifest_sufficiency",
    "validate_assurance_contract",
    "validate_machine_contract",
    "validate_schema_runtime_parity",
]
