from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .authority import AuthorityProvenance, AuthorityScope
from .capabilities import RuntimeCapabilityGrant
from .errors import DelegationDepthViolationError, DelegationRejectedError
from .models import RunIdentity


class DelegationReasonCode(str, Enum):
    ACCEPTED = "ACCEPTED"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_SPECIALIST = "UNKNOWN_SPECIALIST"
    INVALID_PARENT = "INVALID_PARENT"
    DEPTH_EXCEEDED = "DEPTH_EXCEEDED"
    AUTHORITY_REJECTED = "AUTHORITY_REJECTED"
    CAPABILITY_REJECTED = "CAPABILITY_REJECTED"
    CONTEXT_REJECTED = "CONTEXT_REJECTED"


def _text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise DelegationRejectedError(
            f"{field_name} must be non-empty",
            DelegationReasonCode.INVALID_REQUEST,
            {"field": field_name},
        )
    return text


def _unique(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted((_text(item, field_name) for item in values), key=lambda item: (item.casefold(), item)))
    if len(set(normalized)) != len(normalized):
        raise DelegationRejectedError(
            f"{field_name} values must be unique",
            DelegationReasonCode.INVALID_REQUEST,
            {"field": field_name},
        )
    return normalized


@dataclass(frozen=True, slots=True)
class DelegationTask:
    objective: str
    acceptance_criteria: tuple[str, ...]

    def __post_init__(self) -> None:
        criteria = _unique(tuple(self.acceptance_criteria), "acceptance_criteria")
        if not criteria:
            raise DelegationRejectedError("acceptance criteria are required", DelegationReasonCode.INVALID_REQUEST)
        object.__setattr__(self, "objective", _text(self.objective, "objective"))
        object.__setattr__(self, "acceptance_criteria", criteria)

    def to_dict(self) -> dict[str, object]:
        return {"objective": self.objective, "acceptance_criteria": list(self.acceptance_criteria)}


@dataclass(frozen=True, slots=True)
class DelegationRequest:
    request_id: str
    parent_run: RunIdentity
    child_run: RunIdentity
    specialist_slug: str
    task: DelegationTask
    requested_scope: AuthorityScope
    requested_capabilities: tuple[RuntimeCapabilityGrant, ...]
    context_allowlist: tuple[str, ...]
    sensitive_context_exclusions: tuple[str, ...]
    depth: int
    provenance: AuthorityProvenance

    def __post_init__(self) -> None:
        if self.child_run.parent_run_id != self.parent_run.run_id:
            raise DelegationRejectedError(
                "child run must reference parent run",
                DelegationReasonCode.INVALID_PARENT,
            )
        if not isinstance(self.depth, int) or isinstance(self.depth, bool) or self.depth < 1:
            raise DelegationDepthViolationError(
                "delegation depth must be a positive integer",
                DelegationReasonCode.DEPTH_EXCEEDED,
            )
        capabilities = tuple(sorted(tuple(self.requested_capabilities), key=lambda item: item.capability.capability_id))
        if not capabilities or len({item.capability.capability_id for item in capabilities}) != len(capabilities):
            raise DelegationRejectedError(
                "requested capabilities must be non-empty and unique",
                DelegationReasonCode.CAPABILITY_REJECTED,
            )
        allowlist = _unique(tuple(self.context_allowlist), "context_allowlist")
        exclusions = _unique(tuple(self.sensitive_context_exclusions), "sensitive_context_exclusions")
        if set(allowlist).intersection(exclusions):
            raise DelegationRejectedError(
                "sensitive context cannot be allowlisted",
                DelegationReasonCode.CONTEXT_REJECTED,
            )
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "specialist_slug", _text(self.specialist_slug, "specialist_slug").casefold())
        object.__setattr__(self, "requested_capabilities", capabilities)
        object.__setattr__(self, "context_allowlist", allowlist)
        object.__setattr__(self, "sensitive_context_exclusions", exclusions)

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "parent_run": self.parent_run.to_dict(),
            "child_run": self.child_run.to_dict(),
            "specialist_slug": self.specialist_slug,
            "task": self.task.to_dict(),
            "requested_scope": self.requested_scope.to_dict(),
            "requested_capabilities": [item.to_dict() for item in self.requested_capabilities],
            "context_allowlist": list(self.context_allowlist),
            "sensitive_context_exclusions": list(self.sensitive_context_exclusions),
            "depth": self.depth,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class DelegationDecision:
    decision_id: str
    request_id: str
    parent_run_id: str
    allowed: bool
    specialist_registered: bool
    reason_code: DelegationReasonCode
    provenance: AuthorityProvenance
    child_run_id: str | None = None
    authority_decision_id: str | None = None
    capability_decision_ids: tuple[str, ...] = ()
    effective_scope_id: str | None = None
    effective_manifest_id: str | None = None
    effective_context_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        decision_id = _text(self.decision_id, "decision_id")
        request_id = _text(self.request_id, "request_id")
        parent_run_id = _text(self.parent_run_id, "parent_run_id")
        child_run_id = self.child_run_id.strip() if self.child_run_id else None
        authority_decision_id = self.authority_decision_id.strip() if self.authority_decision_id else None
        capability_decision_ids = _unique(tuple(self.capability_decision_ids), "capability_decision_ids")
        effective_context_keys = _unique(tuple(self.effective_context_keys), "effective_context_keys")
        effective_scope_id = self.effective_scope_id.strip() if self.effective_scope_id else None
        effective_manifest_id = self.effective_manifest_id.strip() if self.effective_manifest_id else None
        if self.allowed and not all((child_run_id, authority_decision_id, capability_decision_ids, effective_scope_id, effective_manifest_id)):
            raise DelegationRejectedError(
                "accepted delegation requires effective child references",
                DelegationReasonCode.INVALID_REQUEST,
            )
        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        object.__setattr__(self, "reason_code", DelegationReasonCode(self.reason_code))
        object.__setattr__(self, "child_run_id", child_run_id)
        object.__setattr__(self, "authority_decision_id", authority_decision_id)
        object.__setattr__(self, "capability_decision_ids", capability_decision_ids)
        object.__setattr__(self, "effective_scope_id", effective_scope_id)
        object.__setattr__(self, "effective_manifest_id", effective_manifest_id)
        object.__setattr__(self, "effective_context_keys", effective_context_keys)

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "parent_run_id": self.parent_run_id,
            "child_run_id": self.child_run_id,
            "allowed": self.allowed,
            "specialist_registered": self.specialist_registered,
            "authority_decision_id": self.authority_decision_id,
            "capability_decision_ids": list(self.capability_decision_ids),
            "effective_scope_id": self.effective_scope_id,
            "effective_manifest_id": self.effective_manifest_id,
            "effective_context_keys": list(self.effective_context_keys),
            "reason_code": self.reason_code.value,
            "provenance": self.provenance.to_dict(),
        }
