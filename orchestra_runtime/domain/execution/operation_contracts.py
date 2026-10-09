"""Trusted operation classifications and substantive specialist review results."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re
from types import MappingProxyType


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _values(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    normalized = tuple(sorted({_text(value, name) for value in values}))
    if len(normalized) != len(values):
        raise ValueError(f"{name} must be unique")
    return normalized


class OperationKind(str, Enum):
    DEFENSIVE_SECURITY_REVIEW = "DEFENSIVE_SECURITY_REVIEW"
    SECURITY_SENSITIVE_EXECUTION = "SECURITY_SENSITIVE_EXECUTION"


class OperationAuthority(str, Enum):
    REVIEW_ONLY = "REVIEW_ONLY"
    EXPLICIT_AUTHORIZATION_REQUIRED = "EXPLICIT_AUTHORIZATION_REQUIRED"


class SpecialistSideEffectClass(str, Enum):
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    FILE_MUTATION = "FILE_MUTATION"
    EXTERNAL_MUTATION = "EXTERNAL_MUTATION"
    UNKNOWN = "UNKNOWN"


class RoutingDisposition(str, Enum):
    REQUIRED = "REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"


class SpecialistReviewStatus(str, Enum):
    PASS = "PASS"
    FINDINGS = "FINDINGS"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"


DEFENSIVE_REVIEW_HOST_PROFILE_ID = "orchestra.specialist.read-only-review.v1"


@dataclass(frozen=True, slots=True)
class OperationContract:
    operation_id: str
    kind: OperationKind
    side_effect_class: SpecialistSideEffectClass
    authority: OperationAuthority
    may_mutate: bool
    may_issue_authorization: bool
    requires_verified_governance_receipt: bool
    allowed_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        operation_id = _text(self.operation_id, "operation_id").casefold()
        if not _IDENTIFIER.fullmatch(operation_id):
            raise ValueError("operation_id must be canonical")
        kind = OperationKind(self.kind)
        effects = SpecialistSideEffectClass(self.side_effect_class)
        authority = OperationAuthority(self.authority)
        capabilities = _values(self.allowed_capabilities, "allowed_capabilities")
        if kind is OperationKind.DEFENSIVE_SECURITY_REVIEW:
            expected = (
                effects is SpecialistSideEffectClass.NONE
                and authority is OperationAuthority.REVIEW_ONLY
                and self.may_mutate is False
                and self.may_issue_authorization is False
                and self.requires_verified_governance_receipt is False
                and bool(capabilities)
                and all(item.endswith(".read") for item in capabilities)
            )
            if not expected:
                raise ValueError("defensive review must be read-only and non-authorizing")
        elif not (
            authority is OperationAuthority.EXPLICIT_AUTHORIZATION_REQUIRED
            and self.may_mutate is True
            and self.may_issue_authorization is False
            and self.requires_verified_governance_receipt is True
        ):
            raise ValueError("security-sensitive execution requires verified governance authority")
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "side_effect_class", effects)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "allowed_capabilities", capabilities)


DEFENSIVE_SECURITY_REVIEW = OperationContract(
    "defensive-security-review",
    OperationKind.DEFENSIVE_SECURITY_REVIEW,
    SpecialistSideEffectClass.NONE,
    OperationAuthority.REVIEW_ONLY,
    False,
    False,
    False,
    ("evidence.read", "repository.read", "specialist.read"),
)
SECURITY_SENSITIVE_EXECUTION = OperationContract(
    "security-sensitive-execution",
    OperationKind.SECURITY_SENSITIVE_EXECUTION,
    SpecialistSideEffectClass.UNKNOWN,
    OperationAuthority.EXPLICIT_AUTHORIZATION_REQUIRED,
    True,
    False,
    True,
)
REGISTERED_OPERATION_CONTRACTS = MappingProxyType({
    DEFENSIVE_SECURITY_REVIEW.operation_id: DEFENSIVE_SECURITY_REVIEW,
    SECURITY_SENSITIVE_EXECUTION.operation_id: SECURITY_SENSITIVE_EXECUTION,
})
_REGISTERED_ROUTES = MappingProxyType({
    ("security-check", "cipher"): DEFENSIVE_SECURITY_REVIEW.operation_id,
    ("cipher", "cipher"): SECURITY_SENSITIVE_EXECUTION.operation_id,
})


def operation_contract_for_route(command_name: str, specialist: str) -> OperationContract | None:
    """Resolve from trusted route identity only; task text and metadata are never inputs."""
    key = (_text(command_name, "command_name").casefold(), _text(specialist, "specialist").casefold())
    operation_id = _REGISTERED_ROUTES.get(key)
    return REGISTERED_OPERATION_CONTRACTS.get(operation_id) if operation_id else None


@dataclass(frozen=True, slots=True)
class ReadOnlySpecialistExecutionRequest:
    request_id: str
    request_digest: str
    workspace_snapshot_digest: str
    run_id: str
    adapter_name: str
    command_name: str
    specialist: str
    operation_id: str
    task_input: str

    def __post_init__(self) -> None:
        for name in ("request_id", "run_id", "adapter_name", "command_name", "specialist", "operation_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        digest = _text(self.request_digest, "request_digest").casefold()
        if not _SHA256.fullmatch(digest):
            raise ValueError("request_digest must be SHA-256")
        snapshot_digest = _text(self.workspace_snapshot_digest, "workspace_snapshot_digest").casefold()
        if not _SHA256.fullmatch(snapshot_digest):
            raise ValueError("workspace_snapshot_digest must be SHA-256")
        if self.operation_id != DEFENSIVE_SECURITY_REVIEW.operation_id:
            raise ValueError("read-only request requires defensive-security-review")
        object.__setattr__(self, "request_digest", digest)
        object.__setattr__(self, "workspace_snapshot_digest", snapshot_digest)
        object.__setattr__(self, "task_input", _text(self.task_input, "task_input"))


@dataclass(frozen=True, slots=True)
class SpecialistReviewResult:
    review_id: str
    review_digest: str
    request_id: str
    request_digest: str
    workspace_snapshot_digest: str
    operation_id: str
    specialist: str
    status: SpecialistReviewStatus
    conclusion: str
    findings: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("review_id", "request_id", "operation_id", "specialist"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        request_digest = _text(self.request_digest, "request_digest").casefold()
        snapshot_digest = _text(self.workspace_snapshot_digest, "workspace_snapshot_digest").casefold()
        digest = _text(self.review_digest, "review_digest").casefold()
        if (
            not _SHA256.fullmatch(request_digest)
            or not _SHA256.fullmatch(snapshot_digest)
            or not _SHA256.fullmatch(digest)
        ):
            raise ValueError("review digests must be SHA-256")
        if self.operation_id != DEFENSIVE_SECURITY_REVIEW.operation_id:
            raise ValueError("only a defensive review can produce SpecialistReviewResult")
        status = SpecialistReviewStatus(self.status)
        conclusion = _text(self.conclusion, "conclusion")
        findings = _values(self.findings, "findings")
        evidence = _values(self.evidence_refs, "evidence_refs")
        if not evidence:
            raise ValueError("substantive specialist review requires evidence references")
        object.__setattr__(self, "request_digest", request_digest)
        object.__setattr__(self, "workspace_snapshot_digest", snapshot_digest)
        object.__setattr__(self, "review_digest", digest)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "conclusion", conclusion)
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "evidence_refs", evidence)
        if self.review_digest != self.compute_digest():
            raise ValueError("review_digest does not match result")
        if self.review_id != f"specialist-review.{self.review_digest[:24]}":
            raise ValueError("review_id does not match review_digest")

    @classmethod
    def create(
        cls,
        request: ReadOnlySpecialistExecutionRequest,
        status: SpecialistReviewStatus | str,
        conclusion: str,
        evidence_refs: tuple[str, ...],
        findings: tuple[str, ...] = (),
    ) -> SpecialistReviewResult:
        payload = {
            "review_version": "orchestra.specialist-review-result.v1",
            "request_id": request.request_id,
            "request_digest": request.request_digest,
            "workspace_snapshot_digest": request.workspace_snapshot_digest,
            "operation_id": request.operation_id,
            "specialist": request.specialist,
            "status": SpecialistReviewStatus(status).value,
            "conclusion": _text(conclusion, "conclusion"),
            "findings": list(_values(findings, "findings")),
            "evidence_refs": list(_values(evidence_refs, "evidence_refs")),
        }
        digest = _digest(payload)
        return cls(
            f"specialist-review.{digest[:24]}", digest, request.request_id, request.request_digest,
            request.workspace_snapshot_digest, request.operation_id, request.specialist, SpecialistReviewStatus(status),
            payload["conclusion"], tuple(payload["findings"]), tuple(payload["evidence_refs"]),
        )

    def digest_payload(self) -> dict[str, object]:
        return {
            "review_version": "orchestra.specialist-review-result.v1",
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            "workspace_snapshot_digest": self.workspace_snapshot_digest,
            "operation_id": self.operation_id,
            "specialist": self.specialist,
            "status": self.status.value,
            "conclusion": self.conclusion,
            "findings": list(self.findings),
            "evidence_refs": list(self.evidence_refs),
        }

    def compute_digest(self) -> str:
        return _digest(self.digest_payload())

    def assert_matches(self, request: ReadOnlySpecialistExecutionRequest) -> None:
        if (
            self.request_id,
            self.request_digest,
            self.workspace_snapshot_digest,
            self.operation_id,
            self.specialist,
        ) != (
            request.request_id,
            request.request_digest,
            request.workspace_snapshot_digest,
            request.operation_id,
            request.specialist,
        ):
            raise ValueError("specialist review result does not match request")

    def to_dict(self) -> dict[str, object]:
        return {
            "review_version": "orchestra.specialist-review-result.v1",
            "review_id": self.review_id,
            "review_digest": self.review_digest,
            **self.digest_payload(),
        }
