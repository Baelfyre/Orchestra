from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .authority import (
    AuthorityProvenance,
    Constraint,
    ProvenanceSource,
    _constraints_permit,
    _intersect_constraints,
    _load_trusted_json,
)
from .domain.capabilities.core import (
    CapabilityDecision,
    CapabilityReasonCode,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    _identifier,
    _text,
)
from .errors import (
    CapabilityCollisionError,
    CapabilityDeniedError,
    InvalidAuthorityConfigurationError,
    InvalidCapabilityConfigurationError,
)
from .interfaces import ICapabilityResolver
from .models import AuditEventType, RunIdentity, RuntimeAuditEvent


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityManifest:
    manifest_id: str
    run_identity: RunIdentity
    policy_version: str
    grants: tuple[RuntimeCapabilityGrant, ...]
    provenance: AuthorityProvenance

    def __post_init__(self) -> None:
        manifest_id = _identifier(self.manifest_id, "manifest_id")
        grants = tuple(
            sorted(
                tuple(self.grants),
                key=lambda item: (item.capability.capability_id.casefold(), item.capability.capability_id),
            )
        )
        identities = [item.capability.capability_id.casefold() for item in grants]
        if not grants:
            raise InvalidCapabilityConfigurationError(
                "capability manifest requires at least one grant",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"manifest_id": manifest_id},
            )
        if len(set(identities)) != len(identities):
            raise CapabilityCollisionError(
                "capability identities collide",
                CapabilityReasonCode.COLLISION,
                {"manifest_id": manifest_id},
            )
        object.__setattr__(self, "manifest_id", manifest_id)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "grants", grants)

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_id": self.manifest_id,
            "run_identity": self.run_identity.to_dict(),
            "policy_version": self.policy_version,
            "grants": [item.to_dict() for item in self.grants],
            "provenance": self.provenance.to_dict(),
        }


class CapabilityResolver(ICapabilityResolver):
    def build_manifest(
        self,
        run_id: str,
        grants: tuple[RuntimeCapabilityGrant, ...],
        provenance: AuthorityProvenance,
        *,
        manifest_id: str,
        policy_version: str,
        correlation_id: str | None = None,
    ) -> RuntimeCapabilityManifest:
        if provenance.source_type not in {
            ProvenanceSource.TRUSTED_COMPOSITION,
            ProvenanceSource.TRUSTED_REPOSITORY_POLICY,
            ProvenanceSource.ACCEPTED_DELEGATION,
        }:
            raise InvalidCapabilityConfigurationError(
                "manifest provenance is not trusted",
                CapabilityReasonCode.INVALID_MANIFEST,
            )
        return RuntimeCapabilityManifest(
            manifest_id,
            RunIdentity(run_id, provenance.parent_run_id, correlation_id=correlation_id),
            policy_version,
            tuple(grants),
            provenance,
        )

    def evaluate(
        self,
        manifest: RuntimeCapabilityManifest,
        capability_id: str,
        operation: str,
        constraints: tuple[Constraint, ...] = (),
        *,
        decision_id: str,
    ) -> CapabilityDecision:
        capability_id = _identifier(capability_id, "capability_id")
        operation = _identifier(operation, "operation")
        constraints = tuple(sorted(tuple(constraints), key=lambda item: item.key))
        grant = next((item for item in manifest.grants if item.capability.capability_id == capability_id), None)
        if grant is None:
            reason = CapabilityReasonCode.CAPABILITY_NOT_FOUND
        elif operation not in grant.allowed_operations:
            reason = CapabilityReasonCode.OPERATION_NOT_ALLOWED
        elif not _constraints_permit(grant.constraints, constraints):
            reason = CapabilityReasonCode.CONSTRAINT_DENIED
        else:
            reason = CapabilityReasonCode.ALLOWED
        return CapabilityDecision(
            decision_id,
            manifest.run_identity.run_id,
            manifest.manifest_id,
            capability_id,
            operation,
            constraints,
            reason is CapabilityReasonCode.ALLOWED,
            reason,
            grant.capability.capability_id if grant else None,
            tuple(item.key for item in constraints),
        )

    @staticmethod
    def enforce(decision: CapabilityDecision) -> CapabilityDecision:
        if not decision.allowed:
            raise CapabilityDeniedError(
                "capability decision denied",
                decision.reason_code,
                {"capability_id": decision.capability_id, "operation": decision.operation},
            )
        return decision

    def intersect(
        self,
        parent_manifest: RuntimeCapabilityManifest,
        requested_grants: tuple[RuntimeCapabilityGrant, ...],
        child_run_id: str,
        provenance: AuthorityProvenance,
        *,
        manifest_id: str,
    ) -> RuntimeCapabilityManifest:
        if provenance.source_type is not ProvenanceSource.ACCEPTED_DELEGATION:
            raise InvalidCapabilityConfigurationError(
                "child manifest requires accepted delegation provenance",
                CapabilityReasonCode.INVALID_MANIFEST,
            )
        parent_grants = {item.capability.capability_id: item for item in parent_manifest.grants}
        effective: list[RuntimeCapabilityGrant] = []
        for requested in requested_grants:
            parent = parent_grants.get(requested.capability.capability_id)
            if parent is None:
                continue
            operations = tuple(sorted(set(parent.allowed_operations).intersection(requested.allowed_operations)))
            if not operations:
                continue
            try:
                constraints = _intersect_constraints(parent.constraints, requested.constraints)
            except InvalidAuthorityConfigurationError as exc:
                raise InvalidCapabilityConfigurationError(
                    "capability constraints do not intersect",
                    CapabilityReasonCode.EMPTY_INTERSECTION,
                    {"capability_id": requested.capability.capability_id},
                ) from exc
            effective.append(RuntimeCapabilityGrant(parent.capability, operations, provenance, constraints))
        if not effective:
            raise InvalidCapabilityConfigurationError(
                "capability intersection is empty",
                CapabilityReasonCode.EMPTY_INTERSECTION,
            )
        return self.build_manifest(
            child_run_id,
            tuple(effective),
            provenance,
            manifest_id=manifest_id,
            policy_version=parent_manifest.policy_version,
            correlation_id=parent_manifest.run_identity.correlation_id,
        )


def load_trusted_capability_manifest(repo_root: Path, policy_path: Path) -> RuntimeCapabilityManifest:
    try:
        payload = _load_trusted_json(repo_root, policy_path)
    except InvalidAuthorityConfigurationError as exc:
        raise InvalidCapabilityConfigurationError(
            "trusted capability policy path or JSON is invalid",
            CapabilityReasonCode.INVALID_MANIFEST,
        ) from exc
    manifest_data = payload.get("capability_manifest")
    if not isinstance(manifest_data, dict):
        raise InvalidCapabilityConfigurationError(
            "trusted policy is missing capability_manifest",
            CapabilityReasonCode.INVALID_MANIFEST,
        )
    provenance_data = manifest_data.get("provenance")
    grants_data = manifest_data.get("grants")
    if not isinstance(provenance_data, dict) or not isinstance(grants_data, list):
        raise InvalidCapabilityConfigurationError("trusted manifest is malformed", CapabilityReasonCode.INVALID_MANIFEST)
    try:
        provenance = AuthorityProvenance.from_dict(provenance_data)
        grants = tuple(RuntimeCapabilityGrant.from_dict(item) for item in grants_data if isinstance(item, dict))
        if len(grants) != len(grants_data):
            raise ValueError("malformed grant")
        manifest = CapabilityResolver().build_manifest(
            str(manifest_data.get("run_id", "")),
            grants,
            provenance,
            manifest_id=str(manifest_data.get("manifest_id", "")),
            policy_version=str(manifest_data.get("policy_version", "")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, (InvalidCapabilityConfigurationError, CapabilityCollisionError)):
            raise
        raise InvalidCapabilityConfigurationError("trusted manifest is malformed", CapabilityReasonCode.INVALID_MANIFEST) from exc
    if provenance.source_type is not ProvenanceSource.TRUSTED_REPOSITORY_POLICY:
        raise InvalidCapabilityConfigurationError(
            "file policy requires trusted repository provenance",
            CapabilityReasonCode.INVALID_MANIFEST,
        )
    return manifest


def capability_manifest_event(event_id: str, manifest: RuntimeCapabilityManifest) -> RuntimeAuditEvent:
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.CAPABILITY_MANIFEST_CREATED,
        manifest.run_identity.run_id,
        manifest.manifest_id,
        CapabilityReasonCode.ALLOWED.value,
        provenance_ids=(manifest.provenance.source_id,),
        details=(("grant_count", str(len(manifest.grants))),),
        parent_run_id=manifest.run_identity.parent_run_id,
    )


def capability_decision_event(event_id: str, decision: CapabilityDecision) -> RuntimeAuditEvent:
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.CAPABILITY_DECIDED,
        decision.run_id,
        decision.decision_id,
        decision.reason_code.value,
        details=(
            ("allowed", str(decision.allowed).lower()),
            ("capability_id", decision.capability_id),
            ("operation", decision.operation),
        ),
    )
