"""In-memory and SQLite tenant-member repository adapters."""

from __future__ import annotations

from collections.abc import Iterable
import sqlite3

from ....domain.governance.tenant_administration import (
    StaleVersionError,
    TenantMember,
    TenantMemberNotFoundError,
    validate_role,
)


class InMemoryTenantMemberRepository:
    def __init__(self, members: Iterable[TenantMember] = ()) -> None:
        self._members: dict[tuple[str, str], TenantMember] = {}
        for member in members:
            if not isinstance(member, TenantMember):
                raise TypeError("members must contain TenantMember values")
            key = (member.tenant_id, member.member_id)
            if key in self._members:
                raise ValueError("duplicate tenant member")
            self._members[key] = member

    def get(self, tenant_id: str, member_id: str) -> TenantMember | None:
        return self._members.get((tenant_id, member_id))

    def count_administrators(self, tenant_id: str) -> int:
        return sum(
            member.role == "admin"
            for (member_tenant, _), member in self._members.items()
            if member_tenant == tenant_id
        )

    def update_role(
        self,
        tenant_id: str,
        member_id: str,
        role: str,
        expected_version: int,
    ) -> TenantMember:
        key = (tenant_id, member_id)
        current = self._members.get(key)
        if current is None:
            raise TenantMemberNotFoundError()
        if current.version != expected_version:
            raise StaleVersionError()
        updated = TenantMember(tenant_id, member_id, validate_role(role), current.version + 1)
        self._members[key] = updated
        return updated


class SQLiteTenantMemberRepository:
    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
        members: Iterable[TenantMember] = (),
    ) -> None:
        self._connection = connection if connection is not None else sqlite3.connect(":memory:")
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_members (
                tenant_id TEXT NOT NULL,
                member_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
                version INTEGER NOT NULL CHECK (version > 0),
                PRIMARY KEY (tenant_id, member_id)
            )
            """
        )
        self._connection.commit()
        for member in members:
            if not isinstance(member, TenantMember):
                raise TypeError("members must contain TenantMember values")
            self._connection.execute(
                "INSERT INTO tenant_members (tenant_id, member_id, role, version) VALUES (?, ?, ?, ?)",
                (member.tenant_id, member.member_id, member.role, member.version),
            )
        self._connection.commit()

    @staticmethod
    def _member_from_row(row: sqlite3.Row) -> TenantMember:
        return TenantMember(row["tenant_id"], row["member_id"], row["role"], row["version"])

    def get(self, tenant_id: str, member_id: str) -> TenantMember | None:
        row = self._connection.execute(
            "SELECT tenant_id, member_id, role, version FROM tenant_members WHERE tenant_id = ? AND member_id = ?",
            (tenant_id, member_id),
        ).fetchone()
        return None if row is None else self._member_from_row(row)

    def count_administrators(self, tenant_id: str) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM tenant_members WHERE tenant_id = ? AND role = 'admin'",
            (tenant_id,),
        ).fetchone()
        return int(row["count"])

    def update_role(
        self,
        tenant_id: str,
        member_id: str,
        role: str,
        expected_version: int,
    ) -> TenantMember:
        cursor = self._connection.execute(
            "UPDATE tenant_members SET role = ?, version = version + 1 WHERE tenant_id = ? AND member_id = ? AND version = ?",
            (validate_role(role), tenant_id, member_id, expected_version),
        )
        if cursor.rowcount != 1:
            current = self.get(tenant_id, member_id)
            if current is None:
                raise TenantMemberNotFoundError()
            raise StaleVersionError()
        self._connection.commit()
        updated = self.get(tenant_id, member_id)
        if updated is None:
            raise TenantMemberNotFoundError()
        return updated

    def close(self) -> None:
        self._connection.close()


__all__ = ["InMemoryTenantMemberRepository", "SQLiteTenantMemberRepository"]
