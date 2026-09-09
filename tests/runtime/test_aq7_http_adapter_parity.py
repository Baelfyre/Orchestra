from __future__ import annotations

import json
import sqlite3

import pytest

from orchestra_runtime.application.dto.tenant_administration import ChangeMemberRoleCommand
from orchestra_runtime.application.services.tenant_administration import TenantAdministrationService
from orchestra_runtime.domain.governance.tenant_administration import (
    AuditEvent,
    AuthenticationRequiredError,
    AuthorizationDeniedError,
    InvalidRequestError,
    LastAdministratorError,
    Principal,
    StaleVersionError,
    TenantMember,
    TenantAdministrationError,
    TenantMemberNotFoundError,
    apply_role_change,
)
from orchestra_runtime.entrypoints.api.tenant_administration import (
    HttpRequest,
    StaticBearerAuthenticator,
    TenantAdministrationHttpEndpoint,
)
from orchestra_runtime.infrastructure.persistence.repositories.tenant_members import (
    InMemoryTenantMemberRepository,
    SQLiteTenantMemberRepository,
)


MEMBERS = (
    TenantMember("tenant-a", "member-1", "admin", 1),
    TenantMember("tenant-a", "member-2", "member", 1),
    TenantMember("tenant-b", "member-1", "admin", 1),
)


class AuditCollector:
    def __init__(self) -> None:
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)


def build_app(kind: str, *, repository=None, audit_sink=None):
    if repository is None:
        repository = (
            InMemoryTenantMemberRepository(MEMBERS)
            if kind == "memory"
            else SQLiteTenantMemberRepository(members=MEMBERS)
        )
    audit_sink = audit_sink or AuditCollector()
    service = TenantAdministrationService(repository, audit_sink)
    authenticator = StaticBearerAuthenticator(
        {
            "admin-a": Principal("operator-a", "tenant-a", "admin"),
            "admin-b": Principal("operator-b", "tenant-b", "admin"),
            "member-a": Principal("member-a", "tenant-a", "member"),
        }
    )
    return TenantAdministrationHttpEndpoint(service, authenticator), repository, audit_sink


def close_if_sql(repository) -> None:
    if isinstance(repository, SQLiteTenantMemberRepository):
        repository.close()


def request(
    *,
    token: str | None = "admin-a",
    tenant: str = "tenant-a",
    member: str = "member-2",
    role: str = "admin",
    version: object = 1,
    body: bytes | str | object | None = None,
    method: str = "PUT",
    headers: dict[str, str] | None = None,
) -> HttpRequest:
    if body is None:
        body = json.dumps({"role": role, "version": version})
    request_headers = dict(headers or {})
    if token is not None:
        request_headers.setdefault("authorization", f"Bearer {token}")
    return HttpRequest(
        method,
        f"/tenants/{tenant}/members/{member}/role",
        request_headers,
        body,
    )


def result_for(kind: str, current_version: object = 1):
    endpoint, repository, sink = build_app(kind)
    try:
        response = endpoint.handle(request(version=current_version))
        return response.status, dict(response.headers), response.json(), sink
    finally:
        close_if_sql(repository)


def test_success_response_and_audit_serialization_match_across_adapters():
    memory = result_for("memory")
    sql = result_for("sql")

    assert memory[:3] == sql[:3]
    assert memory[0] == 200
    assert memory[2] == {
        "audit_event": {
            "action": "TENANT_MEMBER_ROLE_CHANGED",
            "actor_id": "operator-a",
            "member_id": "member-2",
            "new_role": "admin",
            "previous_role": "member",
            "tenant_id": "tenant-a",
            "version": 2,
        },
        "member": {
            "member_id": "member-2",
            "role": "admin",
            "tenant_id": "tenant-a",
            "version": 2,
        },
    }
    assert memory[3].events[0].to_dict() == memory[2]["audit_event"]


def test_stale_version_mapping_matches_across_adapters():
    outputs = []
    for kind in ("memory", "sql"):
        endpoint, repository, _ = build_app(kind)
        try:
            assert endpoint.handle(request(version=1)).status == 200
            response = endpoint.handle(request(role="member", version=1))
            outputs.append((response.status, response.json()))
        finally:
            close_if_sql(repository)
    assert outputs[0] == outputs[1]
    assert outputs[0] == (
        409,
        {"error": {"code": "STALE_VERSION", "message": "resource version is stale"}},
    )


@pytest.mark.parametrize("member", ["member-1", "missing-member"])
def test_cross_tenant_denial_does_not_enumerate_target(member: str):
    responses = []
    for kind in ("memory", "sql"):
        endpoint, repository, sink = build_app(kind)
        try:
            response = endpoint.handle(request(token="admin-b", member=member))
            responses.append(response)
            assert sink.events == []
        finally:
            close_if_sql(repository)
    assert responses[0].status == responses[1].status == 403
    assert responses[0].body == responses[1].body
    assert responses[0].json() == {
        "error": {"code": "AUTHORIZATION_DENIED", "message": "request is not authorized"}
    }


def test_last_administrator_is_a_shared_domain_invariant():
    members = (TenantMember("tenant-a", "member-1", "admin", 1),)
    responses = []
    for kind in ("memory", "sql"):
        repository = (
            InMemoryTenantMemberRepository(members)
            if kind == "memory"
            else SQLiteTenantMemberRepository(members=members)
        )
        endpoint, repository, _ = build_app(kind, repository=repository)
        try:
            response = endpoint.handle(request(member="member-1", role="member"))
            responses.append((response.status, response.json()))
        finally:
            close_if_sql(repository)
    assert responses[0] == responses[1]
    assert responses[0] == (
        409,
        {"error": {"code": "LAST_ADMINISTRATOR_REQUIRED", "message": "the last tenant administrator cannot be removed"}},
    )


def test_missing_dependency_fails_closed_before_mutation():
    sink = AuditCollector()
    endpoint, repository, _ = build_app("memory", repository=None, audit_sink=sink)
    endpoint.service.repository = None
    response = endpoint.handle(request())
    assert response.status == 503
    assert response.json()["error"]["code"] == "MISSING_DEPENDENCY"
    assert sink.events == []


def test_authentication_and_route_errors_are_explicit_and_safe():
    endpoint, repository, _ = build_app("memory")
    try:
        missing = endpoint.handle(request(token=None))
        invalid = endpoint.handle(request(token="not-valid"))
        wrong_scheme = endpoint.handle(request(token=None, headers={"Authorization": "Basic abc"}))
        method = endpoint.handle(request(method="POST"))
        route = endpoint.handle(HttpRequest("PUT", "/not-a-route", {}, b""))
    finally:
        close_if_sql(repository)

    assert missing.status == invalid.status == wrong_scheme.status == 401
    assert missing.json() == invalid.json() == wrong_scheme.json()
    assert missing.headers["WWW-Authenticate"] == "Bearer"
    assert method.status == 405
    assert method.headers["Allow"] == "PUT"
    assert route.status == 404


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"\xff",
        '{"role":"admin"}',
        '{"role":"admin","version":1,"extra":true}',
        '{"role":"manager","version":1}',
        '{"role":"admin","version":0}',
        '{"role":"admin","version":true}',
        '{"role":"member","version":1,"role":"admin"}',
        "[]",
    ],
)
def test_input_validation_fails_closed(body):
    endpoint, repository, _ = build_app("memory")
    try:
        response = endpoint.handle(request(body=body))
    finally:
        close_if_sql(repository)
    assert response.status == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_domain_and_dto_reject_invalid_values():
    with pytest.raises(InvalidRequestError):
        Principal("bad subject", "tenant-a", "admin")
    with pytest.raises(InvalidRequestError):
        TenantMember("tenant-a", "member-1", "owner", 1)
    with pytest.raises(InvalidRequestError):
        TenantMember("tenant-a", "member-1", "admin", 0)
    with pytest.raises(InvalidRequestError):
        ChangeMemberRoleCommand.from_payload("tenant-a", "member-1", {"role": "admin"})
    member = TenantMember("tenant-a", "member-1", "member", 1)
    with pytest.raises(InvalidRequestError):
        apply_role_change(member, "owner", 1)
    with pytest.raises(InvalidRequestError):
        apply_role_change(member, "member", 1)
    with pytest.raises(InvalidRequestError):
        apply_role_change(member, "admin", True)
    with pytest.raises(LastAdministratorError):
        apply_role_change(TenantMember("tenant-a", "member-1", "admin", 1), "member", 1)


def test_repository_contract_covers_missing_and_stale_updates():
    for kind in ("memory", "sql"):
        repository = (
            InMemoryTenantMemberRepository(MEMBERS)
            if kind == "memory"
            else SQLiteTenantMemberRepository(members=MEMBERS)
        )
        try:
            assert repository.get("tenant-a", "missing") is None
            assert repository.count_administrators("tenant-a") == 1
            with pytest.raises(TenantMemberNotFoundError):
                repository.update_role("tenant-a", "missing", "admin", 1)
            with pytest.raises(StaleVersionError):
                repository.update_role("tenant-a", "member-2", "admin", 99)
        finally:
            close_if_sql(repository)


def test_external_sqlite_connection_is_supported_without_changing_semantics():
    connection = sqlite3.connect(":memory:")
    repository = SQLiteTenantMemberRepository(connection=connection, members=MEMBERS)
    assert repository.get("tenant-a", "member-2") == MEMBERS[1]
    repository.close()


def test_application_service_authorization_is_before_target_lookup():
    endpoint, repository, _ = build_app("memory")
    try:
        command = ChangeMemberRoleCommand("tenant-a", "missing", "admin", 1)
        with pytest.raises(AuthenticationRequiredError):
            endpoint.service.change_role(command, None)
        with pytest.raises(AuthorizationDeniedError):
            endpoint.service.change_role(command, Principal("member-a", "tenant-a", "member"))
    finally:
        close_if_sql(repository)


def test_unexpected_adapter_error_is_not_exposed():
    class ExplodingService:
        def change_role(self, command, principal):
            raise RuntimeError("secret backend detail")

    endpoint, repository, _ = build_app("memory")
    endpoint.service = ExplodingService()
    try:
        response = endpoint.handle(request())
    finally:
        close_if_sql(repository)
    assert response.status == 500
    assert "secret backend detail" not in response.body
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "request could not be completed"}
    }



def test_authorized_missing_target_maps_to_not_found():
    endpoint, repository, _ = build_app("memory")
    try:
        response = endpoint.handle(request(member="missing-member"))
    finally:
        close_if_sql(repository)
    assert response.status == 404
    assert response.json() == {
        "error": {"code": "MEMBER_NOT_FOUND", "message": "member was not found"}
    }


def test_boundary_defensive_branches_are_safe():
    with pytest.raises(InvalidRequestError):
        HttpRequest("", "/not-a-route", {})
    with pytest.raises(InvalidRequestError):
        HttpRequest("PUT", "", {})

    request_with_unmatched_headers = HttpRequest(
        "PUT", "/not-a-route", {"first": "1", "second": "2"}
    )
    assert request_with_unmatched_headers.header("missing") is None

    endpoint, repository, _ = build_app("memory")
    try:
        invalid_body = endpoint.handle(request(body=object()))
        assert invalid_body.status == 400

        class BaseErrorService:
            def change_role(self, command, principal):
                raise TenantAdministrationError("internal base error")

        endpoint.service = BaseErrorService()
        base_error = endpoint.handle(request())
    finally:
        close_if_sql(repository)
    assert base_error.status == 500
    assert base_error.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "request could not be completed"}
    }


def test_missing_audit_dependency_fails_closed():
    endpoint, repository, _ = build_app("memory")
    endpoint.service.audit_sink = None
    try:
        response = endpoint.handle(request())
    finally:
        close_if_sql(repository)
    assert response.status == 503
    assert response.json()["error"]["code"] == "MISSING_DEPENDENCY"


def test_invalid_audit_and_repository_inputs_are_rejected():
    with pytest.raises(InvalidRequestError):
        AuditEvent("actor-a", "tenant-a", "member-1", "member", "admin", 0)
    with pytest.raises(TypeError):
        InMemoryTenantMemberRepository((object(),))
    duplicate = TenantMember("tenant-a", "member-1", "admin", 1)
    with pytest.raises(ValueError):
        InMemoryTenantMemberRepository((duplicate, duplicate))
    with pytest.raises(TypeError):
        SQLiteTenantMemberRepository(members=(object(),))
