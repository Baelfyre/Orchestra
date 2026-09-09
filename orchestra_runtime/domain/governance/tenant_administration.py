"""Tenant administration domain rules used by the AQ7 parity reference slice."""

from __future__ import annotations

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
ROLE_VALUES = ("admin", "member")


class TenantAdministrationError(Exception):
    """Base class for safe, stable HTTP error mapping."""

    code = "TENANT_ADMINISTRATION_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidRequestError(TenantAdministrationError):
    code = "INVALID_REQUEST"

    def __init__(self, message: str = "request is invalid") -> None:
        super().__init__(message)


class AuthenticationRequiredError(TenantAdministrationError):
    code = "AUTHENTICATION_REQUIRED"

    def __init__(self) -> None:
        super().__init__("authentication is required")


class AuthorizationDeniedError(TenantAdministrationError):
    code = "AUTHORIZATION_DENIED"

    def __init__(self) -> None:
        super().__init__("request is not authorized")


class TenantMemberNotFoundError(TenantAdministrationError):
    code = "MEMBER_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("member was not found")


class LastAdministratorError(TenantAdministrationError):
    code = "LAST_ADMINISTRATOR_REQUIRED"

    def __init__(self) -> None:
        super().__init__("the last tenant administrator cannot be removed")


class StaleVersionError(TenantAdministrationError):
    code = "STALE_VERSION"

    def __init__(self) -> None:
        super().__init__("resource version is stale")


class MissingDependencyError(TenantAdministrationError):
    code = "MISSING_DEPENDENCY"

    def __init__(self) -> None:
        super().__init__("required runtime dependency is unavailable")


def validate_identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise InvalidRequestError(f"{field_name} must be a canonical identifier")
    return value


def validate_role(value: object) -> str:
    if not isinstance(value, str) or value not in ROLE_VALUES:
        raise InvalidRequestError("role must be admin or member")
    return value


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    tenant_id: str
    role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", validate_identifier(self.subject, "subject"))
        object.__setattr__(self, "tenant_id", validate_identifier(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "role", validate_role(self.role))

    @property
    def is_administrator(self) -> bool:
        return self.role == "admin"


@dataclass(frozen=True, slots=True)
class TenantMember:
    tenant_id: str
    member_id: str
    role: str
    version: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_id", validate_identifier(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "member_id", validate_identifier(self.member_id, "member_id"))
        object.__setattr__(self, "role", validate_role(self.role))
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise InvalidRequestError("version must be a positive integer")

    def with_role(self, role: object) -> "TenantMember":
        return TenantMember(self.tenant_id, self.member_id, validate_role(role), self.version + 1)

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "member_id": self.member_id,
            "role": self.role,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class AuditEvent:
    actor_id: str
    tenant_id: str
    member_id: str
    previous_role: str
    new_role: str
    version: int
    action: str = "TENANT_MEMBER_ROLE_CHANGED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "actor_id", validate_identifier(self.actor_id, "actor_id"))
        object.__setattr__(self, "tenant_id", validate_identifier(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "member_id", validate_identifier(self.member_id, "member_id"))
        object.__setattr__(self, "previous_role", validate_role(self.previous_role))
        object.__setattr__(self, "new_role", validate_role(self.new_role))
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise InvalidRequestError("version must be a positive integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "actor_id": self.actor_id,
            "tenant_id": self.tenant_id,
            "member_id": self.member_id,
            "previous_role": self.previous_role,
            "new_role": self.new_role,
            "version": self.version,
        }


def apply_role_change(
    member: TenantMember,
    new_role: object,
    administrator_count: int,
) -> TenantMember:
    role = validate_role(new_role)
    if isinstance(administrator_count, bool) or not isinstance(administrator_count, int):
        raise InvalidRequestError("administrator count must be an integer")
    if role == member.role:
        raise InvalidRequestError("requested role is already set")
    if member.role == "admin" and role == "member" and administrator_count <= 1:
        raise LastAdministratorError()
    return member.with_role(role)


__all__ = [
    "AuditEvent",
    "AuthenticationRequiredError",
    "AuthorizationDeniedError",
    "InvalidRequestError",
    "LastAdministratorError",
    "MissingDependencyError",
    "Principal",
    "ROLE_VALUES",
    "StaleVersionError",
    "TenantAdministrationError",
    "TenantMember",
    "TenantMemberNotFoundError",
    "apply_role_change",
    "validate_identifier",
    "validate_role",
]
