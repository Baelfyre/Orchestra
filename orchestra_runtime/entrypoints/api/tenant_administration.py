"""Framework-neutral HTTP adapter for the AQ7 parity reference slice."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from typing import Any

from ...application.dto.tenant_administration import ChangeMemberRoleCommand
from ...application.services.tenant_administration import TenantAdministrationService
from ...domain.governance.tenant_administration import (
    AuthenticationRequiredError,
    AuthorizationDeniedError,
    InvalidRequestError,
    LastAdministratorError,
    MissingDependencyError,
    Principal,
    StaleVersionError,
    TenantAdministrationError,
    TenantMemberNotFoundError,
)


_ROUTE = re.compile(r"^/tenants/([^/]+)/members/([^/]+)/role$")


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    path: str
    headers: Mapping[str, str]
    body: bytes | str = b""

    def __post_init__(self) -> None:
        if not isinstance(self.method, str) or not self.method.strip():
            raise InvalidRequestError("method is required")
        if not isinstance(self.path, str) or not self.path:
            raise InvalidRequestError("path is required")
        object.__setattr__(self, "method", self.method.upper())

    def header(self, name: str) -> str | None:
        for key, value in self.headers.items():
            if key.casefold() == name.casefold():
                return value
        return None


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: str

    def json(self) -> Any:
        return json.loads(self.body)


class StaticBearerAuthenticator:
    """A test-safe token resolver; production credential verification stays external."""

    def __init__(self, principals: Mapping[str, Principal]) -> None:
        self._principals = dict(principals)

    def authenticate(self, request: HttpRequest) -> Principal:
        value = request.header("Authorization")
        if not isinstance(value, str) or not value.startswith("Bearer "):
            raise AuthenticationRequiredError()
        token = value[7:].strip()
        principal = self._principals.get(token)
        if not token or principal is None:
            raise AuthenticationRequiredError()
        return principal


def _response(
    status: int,
    payload: Mapping[str, object],
    extra_headers: Mapping[str, str] | None = None,
) -> HttpResponse:
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    return HttpResponse(
        status=status,
        headers=headers,
        body=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


def _error(
    status: int,
    code: str,
    message: str,
    extra_headers: Mapping[str, str] | None = None,
) -> HttpResponse:
    return _response(status, {"error": {"code": code, "message": message}}, extra_headers)


def _decode_body(request: HttpRequest) -> object:
    if isinstance(request.body, bytes):
        try:
            text = request.body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidRequestError("body must be UTF-8 JSON") from exc
    elif isinstance(request.body, str):
        text = request.body
    else:
        raise InvalidRequestError("body must be UTF-8 JSON")
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise InvalidRequestError("body must be valid JSON") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRequestError("body contains duplicate JSON fields")
        result[key] = value
    return result


def _map_error(error: TenantAdministrationError) -> HttpResponse:
    if isinstance(error, InvalidRequestError):
        return _error(400, error.code, str(error))
    if isinstance(error, AuthenticationRequiredError):
        return _error(401, error.code, str(error), {"WWW-Authenticate": "Bearer"})
    if isinstance(error, AuthorizationDeniedError):
        return _error(403, error.code, str(error))
    if isinstance(error, TenantMemberNotFoundError):
        return _error(404, error.code, str(error))
    if isinstance(error, (LastAdministratorError, StaleVersionError)):
        return _error(409, error.code, str(error))
    if isinstance(error, MissingDependencyError):
        return _error(503, error.code, str(error))
    return _error(500, "INTERNAL_ERROR", "request could not be completed")


class TenantAdministrationHttpEndpoint:
    """Routes one tenant role mutation through the complete AQ7 reference path."""

    def __init__(
        self,
        service: TenantAdministrationService,
        authenticator: StaticBearerAuthenticator,
    ) -> None:
        self.service = service
        self.authenticator = authenticator

    def handle(self, request: HttpRequest) -> HttpResponse:
        match = _ROUTE.fullmatch(request.path)
        if match is None:
            return _error(404, "ROUTE_NOT_FOUND", "route was not found")
        if request.method != "PUT":
            return _error(405, "METHOD_NOT_ALLOWED", "method is not allowed", {"Allow": "PUT"})
        try:
            principal = self.authenticator.authenticate(request)
            tenant_id, member_id = match.groups()
            command = ChangeMemberRoleCommand.from_payload(
                tenant_id,
                member_id,
                _decode_body(request),
            )
            result = self.service.change_role(command, principal)
            return _response(200, result.to_dict())
        except TenantAdministrationError as error:
            return _map_error(error)
        except Exception:
            return _error(500, "INTERNAL_ERROR", "request could not be completed")


__all__ = [
    "HttpRequest",
    "HttpResponse",
    "StaticBearerAuthenticator",
    "TenantAdministrationHttpEndpoint",
]
