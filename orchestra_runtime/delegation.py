from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re

from .authority import AuthorityProvenance, AuthorityScope, Constraint, ProvenanceSource
from .capabilities import RuntimeCapabilityGrant, RuntimeCapabilityManifest
from .errors import DelegationDepthViolationError, DelegationRejectedError
from .interfaces import IAuthorityEvaluator, ICapabilityResolver, IDelegationValidator, ISkillRegistry
from .models import AuditEventType, RunIdentity, RuntimeAuditEvent


IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")


class DelegationReasonCode(str, Enum):
    ACCEPTED = "ACCEPTED"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_SPECIALIST = "UNKNOWN_SPECIALIST"
    INVALID_PARENT = "INVALID_PARENT"
    DEPTH_EXCEEDED = "DEPTH_EXCEEDED"
    AUTHORITY_REJECTED = "AUTHORITY_REJECTED"
    CAPABILITY_REJECTED = "CAPABILITY_REJECTED"
    CONTEXT_REJECTED = "CONTEXT_REJECTED"


def _stable_id(prefix: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}.{sha256(encoded).hexdigest()[:24]}"


def _text(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
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


def _constraint_reduction(parent: tuple[Constraint, ...], requested: tuple[Constraint, ...]) -> bool:
    requested_by_key = {item.key: item for item in requested}
    return all(item.key in requested_by_key and item.permits(requested_by_key[item.key]) for item in parent)


@dataclass(frozen=True, slots=True)
class DelegationPolicy:
    policy_id: str
    policy_version: str
    max_depth: int
    allowed_context_keys: tuple[str, ...] = ()
    sensitive_context_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        policy_id = _text(self.policy_id, "policy_id").casefold()
        if not IDENTIFIER_PATTERN.fullmatch(policy_id):
            raise DelegationRejectedError("policy_id must be a canonical identifier", DelegationReasonCode.INVALID_REQUEST)
        if not isinstance(self.max_depth, int) or isinstance(self.max_depth, bool) or self.max_depth < 1:
            raise DelegationDepthViolationError(
                "maximum delegation depth must be a positive integer",
                DelegationReasonCode.DEPTH_EXCEEDED,
            )
        allowed = _unique(tuple(self.allowed_context_keys), "allowed_context_keys")
        sensitive = _unique(tuple(self.sensitive_context_keys), "sensitive_context_keys")
        if {item.casefold() for item in allowed}.intersection(item.casefold() for item in sensitive):
            raise DelegationRejectedError(
                "allowed and sensitive context keys must not overlap",
                DelegationReasonCode.CONTEXT_REJECTED,
            )
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "allowed_context_keys", allowed)
        object.__setattr__(self, "sensitive_context_keys", sensitive)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "max_depth": self.max_depth,
            "allowed_context_keys": list(self.allowed_context_keys),
            "sensitive_context_keys": list(self.sensitive_context_keys),
        }


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
        reason_code = DelegationReasonCode(self.reason_code)
        if self.allowed and (
            reason_code is not DelegationReasonCode.ACCEPTED
            or not self.specialist_registered
            or self.provenance.source_type is not ProvenanceSource.ACCEPTED_DELEGATION
            or not all((child_run_id, authority_decision_id, capability_decision_ids, effective_scope_id, effective_manifest_id))
        ):
            raise DelegationRejectedError(
                "accepted delegation requires effective child references",
                DelegationReasonCode.INVALID_REQUEST,
            )
        if not self.allowed and (
            reason_code is DelegationReasonCode.ACCEPTED
            or any((child_run_id, authority_decision_id, capability_decision_ids, effective_scope_id, effective_manifest_id, effective_context_keys))
        ):
            raise DelegationRejectedError(
                "rejected delegation cannot contain effective child references",
                DelegationReasonCode.INVALID_REQUEST,
            )
        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        object.__setattr__(self, "reason_code", reason_code)
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


@dataclass(frozen=True, slots=True)
class DelegationResolution:
    decision: DelegationDecision
    effective_scope: AuthorityScope | None = None
    effective_manifest: RuntimeCapabilityManifest | None = None

    def __post_init__(self) -> None:
        if self.decision.allowed:
            if self.effective_scope is None or self.effective_manifest is None:
                raise DelegationRejectedError(
                    "accepted resolution requires effective child contracts",
                    DelegationReasonCode.INVALID_REQUEST,
                )
            if (
                self.effective_scope.scope_id != self.decision.effective_scope_id
                or self.effective_manifest.manifest_id != self.decision.effective_manifest_id
                or self.effective_manifest.run_identity.run_id != self.decision.child_run_id
                or self.effective_scope.provenance != self.decision.provenance
                or self.effective_manifest.provenance != self.decision.provenance
            ):
                raise DelegationRejectedError(
                    "effective child contracts do not match delegation decision",
                    DelegationReasonCode.INVALID_REQUEST,
                )
        elif self.effective_scope is not None or self.effective_manifest is not None:
            raise DelegationRejectedError(
                "rejected resolution cannot contain effective child contracts",
                DelegationReasonCode.INVALID_REQUEST,
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.to_dict(),
            "effective_scope": self.effective_scope.to_dict() if self.effective_scope else None,
            "effective_manifest": self.effective_manifest.to_dict() if self.effective_manifest else None,
        }


class DelegationValidator(IDelegationValidator):
    def __init__(
        self,
        authority_evaluator: IAuthorityEvaluator,
        capability_resolver: ICapabilityResolver,
        skill_registry: ISkillRegistry,
        policy: DelegationPolicy,
    ) -> None:
        self._authority_evaluator = authority_evaluator
        self._capability_resolver = capability_resolver
        self._skill_registry = skill_registry
        self._policy = policy

    def validate(
        self,
        request: DelegationRequest,
        parent_scope: AuthorityScope,
        parent_manifest: RuntimeCapabilityManifest,
    ) -> DelegationResolution:
        if (
            parent_manifest.run_identity.run_id != request.parent_run.run_id
            or request.requested_scope.provenance != parent_scope.provenance
            or request.provenance != parent_scope.provenance
        ):
            return self._reject(request, DelegationReasonCode.INVALID_PARENT, False)

        specialist_registered = self._skill_registry.get_skill(request.specialist_slug) is not None
        if not specialist_registered:
            return self._reject(request, DelegationReasonCode.UNKNOWN_SPECIALIST, False)
        if request.depth > self._policy.max_depth:
            return self._reject(request, DelegationReasonCode.DEPTH_EXCEEDED, True)
        if not self._context_allowed(request):
            return self._reject(request, DelegationReasonCode.CONTEXT_REJECTED, True)
        if not self._authority_reduction(parent_scope, request.requested_scope):
            return self._reject(request, DelegationReasonCode.AUTHORITY_REJECTED, True)
        if not self._capability_reduction(parent_manifest, request):
            return self._reject(request, DelegationReasonCode.CAPABILITY_REJECTED, True)

        decision_id = self._decision_id(request, DelegationReasonCode.ACCEPTED)
        provenance = AuthorityProvenance(
            ProvenanceSource.ACCEPTED_DELEGATION,
            _stable_id("delegation", {"request_id": request.request_id, "decision_id": decision_id}),
            self._policy.policy_version,
            "delegation-validator",
            request.parent_run.run_id,
            decision_id,
        )
        manifest_id = _stable_id(
            "manifest",
            {"request_id": request.request_id, "child_run_id": request.child_run.run_id, "policy": self._policy.to_dict()},
        )
        effective_scope = self._authority_evaluator.intersect(parent_scope, request.requested_scope, provenance)
        effective_manifest = self._capability_resolver.intersect(
            parent_manifest,
            request.requested_capabilities,
            request.child_run.run_id,
            provenance,
            manifest_id=manifest_id,
        )
        authority_decision_id = _stable_id("authority", {"decision_id": decision_id, "scope_id": effective_scope.scope_id})
        capability_decision_ids = tuple(
            _stable_id("capability", {"decision_id": decision_id, "capability_id": item.capability.capability_id})
            for item in effective_manifest.grants
        )
        decision = DelegationDecision(
            decision_id,
            request.request_id,
            request.parent_run.run_id,
            True,
            True,
            DelegationReasonCode.ACCEPTED,
            provenance,
            child_run_id=request.child_run.run_id,
            authority_decision_id=authority_decision_id,
            capability_decision_ids=capability_decision_ids,
            effective_scope_id=effective_scope.scope_id,
            effective_manifest_id=effective_manifest.manifest_id,
            effective_context_keys=request.context_allowlist,
        )
        return DelegationResolution(decision, effective_scope, effective_manifest)

    def _decision_id(self, request: DelegationRequest, reason_code: DelegationReasonCode) -> str:
        return _stable_id(
            "delegation-decision",
            {"request": request.to_dict(), "policy": self._policy.to_dict(), "reason_code": reason_code.value},
        )

    def _reject(
        self,
        request: DelegationRequest,
        reason_code: DelegationReasonCode,
        specialist_registered: bool,
    ) -> DelegationResolution:
        return DelegationResolution(
            DelegationDecision(
                self._decision_id(request, reason_code),
                request.request_id,
                request.parent_run.run_id,
                False,
                specialist_registered,
                reason_code,
                request.provenance,
            )
        )

    def _context_allowed(self, request: DelegationRequest) -> bool:
        requested = {item.casefold() for item in request.context_allowlist}
        allowed = {item.casefold() for item in self._policy.allowed_context_keys}
        sensitive = {item.casefold() for item in self._policy.sensitive_context_keys}.union(
            item.casefold() for item in request.sensitive_context_exclusions
        )
        return requested.issubset(allowed) and requested.isdisjoint(sensitive)

    @staticmethod
    def _authority_reduction(parent: AuthorityScope, requested: AuthorityScope) -> bool:
        return (
            requested.scope_id != parent.scope_id
            and set(requested.targets).issubset(parent.targets)
            and set(requested.operations).issubset(parent.operations)
            and _constraint_reduction(parent.constraints, requested.constraints)
        )

    @staticmethod
    def _capability_reduction(parent: RuntimeCapabilityManifest, request: DelegationRequest) -> bool:
        parent_grants = {item.capability.capability_id: item for item in parent.grants}
        for requested in request.requested_capabilities:
            granted = parent_grants.get(requested.capability.capability_id)
            if (
                granted is None
                or requested.capability != granted.capability
                or requested.capability.owner != request.specialist_slug
                or requested.provenance != granted.provenance
                or not set(requested.allowed_operations).issubset(granted.allowed_operations)
                or not _constraint_reduction(granted.constraints, requested.constraints)
            ):
                return False
        return True


def delegation_accepted_event(resolution: DelegationResolution) -> RuntimeAuditEvent:
    decision = resolution.decision
    if not decision.allowed or decision.child_run_id is None:
        raise DelegationRejectedError("accepted event requires accepted resolution", DelegationReasonCode.INVALID_REQUEST)
    return RuntimeAuditEvent(
        _stable_id("event", {"type": AuditEventType.DELEGATION_ACCEPTED.value, "decision": decision.to_dict()}),
        AuditEventType.DELEGATION_ACCEPTED,
        decision.child_run_id,
        decision.decision_id,
        decision.reason_code.value,
        provenance_ids=(decision.provenance.source_id,),
        details=(
            ("effective_manifest_id", decision.effective_manifest_id or ""),
            ("effective_scope_id", decision.effective_scope_id or ""),
            ("specialist_registered", "true"),
        ),
        parent_run_id=decision.parent_run_id,
    )


def delegation_rejected_event(resolution: DelegationResolution) -> RuntimeAuditEvent:
    decision = resolution.decision
    if decision.allowed:
        raise DelegationRejectedError("rejected event requires rejected resolution", DelegationReasonCode.INVALID_REQUEST)
    return RuntimeAuditEvent(
        _stable_id("event", {"type": AuditEventType.DELEGATION_REJECTED.value, "decision": decision.to_dict()}),
        AuditEventType.DELEGATION_REJECTED,
        decision.parent_run_id,
        decision.decision_id,
        decision.reason_code.value,
        provenance_ids=(decision.provenance.source_id,),
        details=(
            ("request_id", decision.request_id),
            ("specialist_registered", str(decision.specialist_registered).lower()),
        ),
    )
