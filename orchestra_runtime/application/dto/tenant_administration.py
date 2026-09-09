"""Transport-neutral DTOs for the tenant administration use case."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ...domain.governance.tenant_administration import (
    AuditEvent,
    InvalidRequestError,
    TenantMember,
    validate_identifier,
    validate_role,
)


@dataclass(frozen=True, slots=True)
class ChangeMemberRoleCommand:
    tenant_id: str
    member_id: str
    role: str
    expected_version: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_id", validate_identifier(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "member_id", validate_identifier(self.member_id, "member_id"))
        object.__setattr__(self, "role", validate_role(self.role))
        if isinstance(self.expected_version, bool) or not isinstance(self.expected_version, int) or self.expected_version < 1:
            raise InvalidRequestError("version must be a positive integer")

    @classmethod
    def from_payload(
        cls,
        tenant_id: str,
        member_id: str,
        payload: object,
    ) -> "ChangeMemberRoleCommand":
        if not isinstance(payload, Mapping) or set(payload) != {"role", "version"}:
            raise InvalidRequestError("payload must contain only role and version")
        return cls(
            tenant_id=tenant_id,
            member_id=member_id,
            role=payload["role"],
            expected_version=payload["version"],
        )


@dataclass(frozen=True, slots=True)
class RoleChangeResult:
    member: TenantMember
    audit_event: AuditEvent

    def to_dict(self) -> dict[str, object]:
        return {
            "member": self.member.to_dict(),
            "audit_event": self.audit_event.to_dict(),
        }


__all__ = ["ChangeMemberRoleCommand", "RoleChangeResult"]
