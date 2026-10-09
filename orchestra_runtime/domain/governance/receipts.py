"""Exact-state governance receipt contracts; no I/O or authority lookup occurs here."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import re


GOVERNANCE_RECEIPT_SCHEMA_VERSION = "orchestra.governance-receipt.v1"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SCOPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _identifier(value: object, name: str) -> str:
    value = _text(value, name).casefold()
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{name} must be canonical")
    return value


def _sha(value: object, length: int, name: str) -> str:
    value = _text(value, name).casefold()
    pattern = _SHA40 if length == 40 else _SHA256
    if not pattern.fullmatch(value):
        raise ValueError(f"{name} must be a {length}-character SHA digest")
    return value


def _items(values: object, name: str, pattern: re.Pattern[str]) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{name} must be an array")
    normalized = tuple(sorted({_text(item, name) for item in values}))
    if not normalized or len(normalized) != len(values):
        raise ValueError(f"{name} must be non-empty and unique")
    if any(not pattern.fullmatch(item) or "*" in item or "?" in item for item in normalized):
        raise ValueError(f"{name} must contain exact canonical values")
    return normalized


def _json_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def evidence_digest(references: tuple[str, ...] | list[str]) -> str:
    return _json_digest(list(_items(references, "evidence_references", _REFERENCE)))


def _time(value: object, name: str) -> datetime:
    text = _text(value, name)
    try:
        result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return result


class ReceiptProvenance(str, Enum):
    CANONICAL_HUMAN_GOVERNANCE_STORE = "CANONICAL_HUMAN_GOVERNANCE_STORE"
    UNTRUSTED_SOURCE = "UNTRUSTED_SOURCE"


class ReceiptConsumptionSemantics(str, Enum):
    SINGLE_USE = "SINGLE_USE"


class GovernanceValidationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    DENIED = "DENIED"


@dataclass(frozen=True, slots=True)
class GovernanceReceipt:
    schema_version: str
    decision_or_receipt_id: str
    human_authority_source: str
    human_authority_id: str
    repository: str
    candidate_base: str
    candidate_head: str
    candidate_tree: str
    protected_rule: str
    allowed_operations: tuple[str, ...]
    allowed_scope: tuple[str, ...]
    evidence_references: tuple[str, ...]
    evidence_digest: str
    issued_at: str
    expires_at: str
    issued_execution_context_id: str
    execution_context_binding: str
    fresh_execution_context_required: bool
    consumption_semantics: ReceiptConsumptionSemantics

    def __post_init__(self) -> None:
        if self.schema_version != GOVERNANCE_RECEIPT_SCHEMA_VERSION:
            raise ValueError("unsupported governance receipt schema")
        object.__setattr__(self, "decision_or_receipt_id", _identifier(self.decision_or_receipt_id, "receipt_id"))
        if self.human_authority_source != "HUMAN_GOVERNANCE_DECISION":
            raise ValueError("human_authority_source must be HUMAN_GOVERNANCE_DECISION")
        authority_id = _text(self.human_authority_id, "human_authority_id")
        if not _REFERENCE.fullmatch(authority_id):
            raise ValueError("human_authority_id must be a bounded reference")
        object.__setattr__(self, "human_authority_id", authority_id)
        repository = _text(self.repository, "repository").casefold()
        if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", repository):
            raise ValueError("repository must be owner/repository")
        object.__setattr__(self, "repository", repository)
        for name in ("candidate_base", "candidate_head", "candidate_tree"):
            object.__setattr__(self, name, _sha(getattr(self, name), 40, name))
        object.__setattr__(self, "protected_rule", _identifier(self.protected_rule, "protected_rule"))
        operations = tuple(_identifier(item, "allowed_operations") for item in self.allowed_operations)
        if not operations or len(set(operations)) != len(operations):
            raise ValueError("allowed_operations must be non-empty and unique")
        object.__setattr__(self, "allowed_operations", tuple(sorted(operations)))
        object.__setattr__(self, "allowed_scope", _items(self.allowed_scope, "allowed_scope", _SCOPE))
        refs = _items(self.evidence_references, "evidence_references", _REFERENCE)
        object.__setattr__(self, "evidence_references", refs)
        digest = _sha(self.evidence_digest, 64, "evidence_digest")
        if digest != evidence_digest(refs):
            raise ValueError("evidence_digest does not match evidence references")
        object.__setattr__(self, "evidence_digest", digest)
        issued, expires = _time(self.issued_at, "issued_at"), _time(self.expires_at, "expires_at")
        if expires <= issued:
            raise ValueError("expires_at must be later than issued_at")
        object.__setattr__(self, "issued_at", self.issued_at.strip())
        object.__setattr__(self, "expires_at", self.expires_at.strip())
        issued_context = _identifier(self.issued_execution_context_id, "issued_execution_context_id")
        bound_context = _identifier(self.execution_context_binding, "execution_context_binding")
        if issued_context == bound_context:
            raise ValueError("receipt must bind to a fresh execution context")
        object.__setattr__(self, "issued_execution_context_id", issued_context)
        object.__setattr__(self, "execution_context_binding", bound_context)
        if self.fresh_execution_context_required is not True:
            raise ValueError("fresh_execution_context_required must be true")
        object.__setattr__(self, "consumption_semantics", ReceiptConsumptionSemantics(self.consumption_semantics))

    @classmethod
    def from_dict(cls, value: object) -> GovernanceReceipt:
        fields = {
            "schema_version", "decision_or_receipt_id", "human_authority_source", "human_authority_id",
            "repository", "candidate_base", "candidate_head", "candidate_tree", "protected_rule",
            "allowed_operations", "allowed_scope", "evidence_references", "evidence_digest", "issued_at",
            "expires_at", "issued_execution_context_id", "execution_context_binding",
            "fresh_execution_context_required", "consumption_semantics",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise ValueError("receipt contains missing or unknown fields")
        arrays = ("allowed_operations", "allowed_scope", "evidence_references")
        if any(not isinstance(value[name], list) for name in arrays):
            raise TypeError("receipt scope and evidence fields must be arrays")
        if not isinstance(value["fresh_execution_context_required"], bool):
            raise TypeError("fresh_execution_context_required must be boolean")
        scalars = fields - set(arrays) - {"fresh_execution_context_required", "consumption_semantics"}
        if any(not isinstance(value[name], str) for name in scalars):
            raise TypeError("receipt scalar fields must be strings")
        return cls(
            **{name: value[name] for name in scalars},
            allowed_operations=tuple(value["allowed_operations"]),
            allowed_scope=tuple(value["allowed_scope"]),
            evidence_references=tuple(value["evidence_references"]),
            fresh_execution_context_required=value["fresh_execution_context_required"],
            consumption_semantics=ReceiptConsumptionSemantics(value["consumption_semantics"]),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "decision_or_receipt_id": self.decision_or_receipt_id,
            "human_authority_source": self.human_authority_source,
            "human_authority_id": self.human_authority_id,
            "repository": self.repository,
            "candidate_base": self.candidate_base,
            "candidate_head": self.candidate_head,
            "candidate_tree": self.candidate_tree,
            "protected_rule": self.protected_rule,
            "allowed_operations": list(self.allowed_operations),
            "allowed_scope": list(self.allowed_scope),
            "evidence_references": list(self.evidence_references),
            "evidence_digest": self.evidence_digest,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "issued_execution_context_id": self.issued_execution_context_id,
            "execution_context_binding": self.execution_context_binding,
            "fresh_execution_context_required": self.fresh_execution_context_required,
            "consumption_semantics": self.consumption_semantics.value,
        }

    @property
    def digest(self) -> str:
        return _json_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ResolvedGovernanceReceipt:
    receipt: GovernanceReceipt
    provenance: ReceiptProvenance
    canonical_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.receipt, GovernanceReceipt):
            raise TypeError("resolved receipt must be typed")
        object.__setattr__(self, "provenance", ReceiptProvenance(self.provenance))
        object.__setattr__(self, "canonical_digest", _sha(self.canonical_digest, 64, "canonical_digest"))


@dataclass(frozen=True, slots=True)
class GovernanceReceiptRequest:
    repository: str
    candidate_base: str
    candidate_head: str
    candidate_tree: str
    protected_rule: str
    operation_id: str
    requested_scope: tuple[str, ...]
    evidence_digest: str
    execution_context_id: str

    def __post_init__(self) -> None:
        repository = _text(self.repository, "repository").casefold()
        if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", repository):
            raise ValueError("repository must be owner/repository")
        object.__setattr__(self, "repository", repository)
        for name in ("candidate_base", "candidate_head", "candidate_tree"):
            object.__setattr__(self, name, _sha(getattr(self, name), 40, name))
        object.__setattr__(self, "protected_rule", _identifier(self.protected_rule, "protected_rule"))
        object.__setattr__(self, "operation_id", _identifier(self.operation_id, "operation_id"))
        object.__setattr__(self, "requested_scope", _items(self.requested_scope, "requested_scope", _SCOPE))
        object.__setattr__(self, "evidence_digest", _sha(self.evidence_digest, 64, "evidence_digest"))
        object.__setattr__(self, "execution_context_id", _identifier(self.execution_context_id, "execution_context_id"))


@dataclass(frozen=True, slots=True)
class GovernanceValidationResult:
    status: GovernanceValidationStatus
    reason_code: str
    receipt_id: str | None = None
    receipt_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", GovernanceValidationStatus(self.status))
        object.__setattr__(self, "reason_code", _identifier(self.reason_code, "reason_code"))
        if self.receipt_id:
            object.__setattr__(self, "receipt_id", _identifier(self.receipt_id, "receipt_id"))
        if self.receipt_digest:
            object.__setattr__(self, "receipt_digest", _sha(self.receipt_digest, 64, "receipt_digest"))
        if self.status is GovernanceValidationStatus.VERIFIED and (
            not self.receipt_id or not self.receipt_digest
        ):
            raise ValueError("verified governance validation must identify its canonical receipt")

    @property
    def allowed(self) -> bool:
        return self.status is GovernanceValidationStatus.VERIFIED


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    decision_id: str
    authorized: bool
    operation_id: str
    execution_context_id: str
    reason_code: str
    receipt_id: str | None = None
    receipt_digest: str | None = None
    repository: str | None = None
    candidate_base: str | None = None
    candidate_head: str | None = None
    candidate_tree: str | None = None
    allowed_scope: tuple[str, ...] = ()
    evidence_digest: str | None = None

    def __post_init__(self) -> None:
        for name in ("decision_id", "operation_id", "execution_context_id", "reason_code"):
            object.__setattr__(self, name, _identifier(getattr(self, name), name))
        if not isinstance(self.authorized, bool):
            raise TypeError("authorized must be boolean")
        if self.receipt_id:
            object.__setattr__(self, "receipt_id", _identifier(self.receipt_id, "receipt_id"))
        if self.receipt_digest is not None:
            object.__setattr__(self, "receipt_digest", _sha(self.receipt_digest, 64, "receipt_digest"))
        if self.repository:
            repository = _text(self.repository, "repository").casefold()
            if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", repository):
                raise ValueError("repository must be owner/repository")
            object.__setattr__(self, "repository", repository)
        for name in ("candidate_base", "candidate_head", "candidate_tree"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _sha(value, 40, name))
        scope = _items(self.allowed_scope, "allowed_scope", _SCOPE) if self.allowed_scope else ()
        object.__setattr__(self, "allowed_scope", scope)
        if self.evidence_digest is not None:
            object.__setattr__(self, "evidence_digest", _sha(self.evidence_digest, 64, "evidence_digest"))
        if self.authorized and (
            not self.receipt_id or not self.receipt_digest or not self.repository or not scope or not self.evidence_digest
            or any(getattr(self, name) is None for name in ("candidate_base", "candidate_head", "candidate_tree"))
        ):
            raise ValueError("authorization must retain exact receipt, candidate, scope, and evidence")

    @classmethod
    def denied(cls, operation_id: str, execution_context_id: str, reason_code: str) -> AuthorizationDecision:
        decision_id = _json_digest([operation_id, execution_context_id, reason_code])
        return cls(decision_id, False, operation_id, execution_context_id, reason_code)


@dataclass(frozen=True, slots=True)
class GovernanceReceiptAuditEvent:
    receipt_reference: str
    operation_id: str
    execution_context_id: str
    repository: str
    candidate_head: str
    candidate_tree: str
    validation_status: GovernanceValidationStatus
    reason_code: str
    receipt_id: str | None = None
    receipt_digest: str | None = None

    def __post_init__(self) -> None:
        reference = _text(self.receipt_reference, "receipt_reference")
        if not _REFERENCE.fullmatch(reference):
            raise ValueError("receipt_reference must be bounded")
        object.__setattr__(self, "receipt_reference", reference)
        object.__setattr__(self, "operation_id", _identifier(self.operation_id, "operation_id"))
        object.__setattr__(self, "execution_context_id", _identifier(self.execution_context_id, "execution_context_id"))
        repository = _text(self.repository, "repository").casefold()
        if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", repository):
            raise ValueError("repository must be owner/repository")
        object.__setattr__(self, "repository", repository)
        object.__setattr__(self, "candidate_head", _sha(self.candidate_head, 40, "candidate_head"))
        object.__setattr__(self, "candidate_tree", _sha(self.candidate_tree, 40, "candidate_tree"))
        object.__setattr__(self, "validation_status", GovernanceValidationStatus(self.validation_status))
        object.__setattr__(self, "reason_code", _identifier(self.reason_code, "reason_code"))
        if self.receipt_id:
            object.__setattr__(self, "receipt_id", _identifier(self.receipt_id, "receipt_id"))
        if self.receipt_digest:
            object.__setattr__(self, "receipt_digest", _sha(self.receipt_digest, 64, "receipt_digest"))

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt_reference": self.receipt_reference, "receipt_id": self.receipt_id,
            "receipt_digest": self.receipt_digest, "operation_id": self.operation_id,
            "execution_context_id": self.execution_context_id, "repository": self.repository,
            "candidate_head": self.candidate_head, "candidate_tree": self.candidate_tree,
            "validation_status": self.validation_status.value, "reason_code": self.reason_code,
        }

    @property
    def event_id(self) -> str:
        return f"governance-receipt-event.{_json_digest(self.to_dict())[:24]}"


@dataclass(frozen=True, slots=True)
class GovernanceReceiptVerification:
    validation: GovernanceValidationResult
    authorization: AuthorizationDecision

    def __post_init__(self) -> None:
        if not isinstance(self.validation, GovernanceValidationResult):
            raise TypeError("validation must be a GovernanceValidationResult")
        if not isinstance(self.authorization, AuthorizationDecision):
            raise TypeError("authorization must be an AuthorizationDecision")
        if self.validation.allowed != self.authorization.authorized:
            raise ValueError("governance validation and authorization outcomes must agree")
        if self.authorization.authorized and (
            self.validation.receipt_id != self.authorization.receipt_id
            or self.validation.receipt_digest != self.authorization.receipt_digest
        ):
            raise ValueError("authorization must retain its verified receipt identity")
