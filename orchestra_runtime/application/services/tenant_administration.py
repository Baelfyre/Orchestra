"""Application orchestration for the tenant administration route."""

from __future__ import annotations

from ..dto.tenant_administration import ChangeMemberRoleCommand, RoleChangeResult
from ..ports.repositories.tenant_members import AuditSink, TenantMemberRepository
from ...domain.governance.tenant_administration import (
    AuditEvent,
    AuthenticationRequiredError,
    AuthorizationDeniedError,
    MissingDependencyError,
    Principal,
    TenantMemberNotFoundError,
    apply_role_change,
)


class TenantAdministrationService:
    """Coordinates authorization, domain invariants, persistence, and audit."""

    def __init__(
        self,
        repository: TenantMemberRepository | None,
        audit_sink: AuditSink | None,
    ) -> None:
        self.repository = repository
        self.audit_sink = audit_sink

    def change_role(
        self,
        command: ChangeMemberRoleCommand,
        principal: Principal | None,
    ) -> RoleChangeResult:
        if principal is None:
            raise AuthenticationRequiredError()
        if not principal.is_administrator or principal.tenant_id != command.tenant_id:
            raise AuthorizationDeniedError()

        repository = self.repository
        audit_sink = self.audit_sink
        if repository is None or audit_sink is None:
            raise MissingDependencyError()

        current = repository.get(command.tenant_id, command.member_id)
        if current is None:
            raise TenantMemberNotFoundError()

        updated = apply_role_change(
            current,
            command.role,
            repository.count_administrators(command.tenant_id),
        )
        persisted = repository.update_role(
            command.tenant_id,
            command.member_id,
            updated.role,
            command.expected_version,
        )
        event = AuditEvent(
            actor_id=principal.subject,
            tenant_id=persisted.tenant_id,
            member_id=persisted.member_id,
            previous_role=current.role,
            new_role=persisted.role,
            version=persisted.version,
        )
        audit_sink.record(event)
        return RoleChangeResult(member=persisted, audit_event=event)


__all__ = ["TenantAdministrationService"]
