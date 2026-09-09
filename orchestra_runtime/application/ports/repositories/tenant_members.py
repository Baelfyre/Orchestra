"""Ports used by tenant administration application services."""

from __future__ import annotations

from typing import Protocol

from ....domain.governance.tenant_administration import AuditEvent, TenantMember


class TenantMemberRepository(Protocol):
    def get(self, tenant_id: str, member_id: str) -> TenantMember | None:
        ...

    def count_administrators(self, tenant_id: str) -> int:
        ...

    def update_role(
        self,
        tenant_id: str,
        member_id: str,
        role: str,
        expected_version: int,
    ) -> TenantMember:
        ...


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None:
        ...


__all__ = ["AuditSink", "TenantMemberRepository"]
