from dataclasses import FrozenInstanceError
import inspect
import json
from pathlib import Path

import pytest

from orchestra_runtime.authority import AuthorityProvenance, Constraint, ProvenanceSource
from orchestra_runtime.capabilities import (
    CapabilityDecision,
    CapabilityReasonCode,
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
    capability_decision_event,
    capability_manifest_event,
    load_trusted_capability_manifest,
)
from orchestra_runtime.errors import CapabilityCollisionError, CapabilityDeniedError, InvalidCapabilityConfigurationError
from orchestra_runtime.models import AuditEventType, RunIdentity


def provenance() -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_REPOSITORY_POLICY, "policy.root", "1", "runtime")


def grant(capability_id: str = "filesystem.read", operations: tuple[str, ...] = ("read",)) -> RuntimeCapabilityGrant:
    capability = RuntimeCapability(capability_id, "clockwork", operations, "Runtime capability")
    return RuntimeCapabilityGrant(capability, operations, provenance(), (Constraint.exact("mode", "safe"),))


def test_capability_grant_requires_subset_and_normalizes_inputs():
    operations = ["READ", "list"]
    capability = RuntimeCapability("Filesystem.Read", "Clockwork", operations, "Read files")
    operations.append("delete")
    capability_grant = RuntimeCapabilityGrant(capability, ["read"], provenance())  # type: ignore[arg-type]

    assert capability.capability_id == "filesystem.read"
    assert capability.operations == ("list", "read")
    assert capability_grant.allowed_operations == ("read",)
    with pytest.raises(InvalidCapabilityConfigurationError, match="subset"):
        RuntimeCapabilityGrant(capability, ("delete",), provenance())


def test_manifest_orders_grants_and_rejects_collisions():
    manifest = RuntimeCapabilityManifest(
        "manifest.root",
        RunIdentity("run-root"),
        "1",
        (grant("zeta"), grant("alpha")),
        provenance(),
    )

    assert [item.capability.capability_id for item in manifest.grants] == ["alpha", "zeta"]
    assert RuntimeCapabilityGrant.from_dict(manifest.grants[0].to_dict()) == manifest.grants[0]
    with pytest.raises(FrozenInstanceError):
        manifest.grants = ()  # type: ignore[misc]
    with pytest.raises(CapabilityCollisionError):
        RuntimeCapabilityManifest(
            "manifest.root",
            RunIdentity("run-root"),
            "1",
            (grant("Tool.Read"), grant("tool.read")),
            provenance(),
        )


def test_manifest_defensively_copies_grant_list_and_serializes():
    grants = [grant()]
    manifest = RuntimeCapabilityManifest("manifest.root", RunIdentity("run-root"), "1", grants, provenance())  # type: ignore[arg-type]
    grants.clear()

    assert len(manifest.grants) == 1
    assert manifest.to_dict()["run_identity"] == {"run_id": "run-root", "parent_run_id": None}


def test_capability_decision_is_immutable_and_serializable():
    decision = CapabilityDecision(
        "decision-1",
        "run-root",
        "manifest.root",
        "filesystem.read",
        "read",
        (),
        True,
        CapabilityReasonCode.ALLOWED,
        "filesystem.read",
    )

    assert decision.to_dict()["reason_code"] == "ALLOWED"
    with pytest.raises(FrozenInstanceError):
        decision.allowed = False  # type: ignore[misc]


def delegated_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation.accepted",
        "1",
        "runtime",
        "run-root",
        "delegation-1",
    )


def manifest() -> RuntimeCapabilityManifest:
    return CapabilityResolver().build_manifest(
        "run-root",
        (grant(),),
        provenance(),
        manifest_id="manifest.root",
        policy_version="1",
    )


def write_capability_policy(repo_root: Path, grants: list[dict[str, object]] | None = None) -> Path:
    path = repo_root / "config" / "capabilities.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "capability_manifest": {
                    "manifest_id": "manifest.root",
                    "run_id": "run-root",
                    "policy_version": "1",
                    "provenance": provenance().to_dict(),
                    "grants": grants if grants is not None else [grant().to_dict()],
                }
            }
        ),
        encoding="utf-8",
    )
    return path.relative_to(repo_root)


def test_trusted_capability_loader_builds_immutable_manifest(tmp_path: Path):
    relative = write_capability_policy(tmp_path)

    loaded = load_trusted_capability_manifest(tmp_path, relative)

    assert loaded == manifest()


def test_trusted_capability_loader_rejects_malformed_grants_and_collisions(tmp_path: Path):
    relative = write_capability_policy(tmp_path, [{"capability": {}}])
    with pytest.raises(InvalidCapabilityConfigurationError):
        load_trusted_capability_manifest(tmp_path, relative)

    duplicate = grant().to_dict()
    relative = write_capability_policy(tmp_path, [duplicate, duplicate])
    with pytest.raises(CapabilityCollisionError):
        load_trusted_capability_manifest(tmp_path, relative)


def test_trusted_capability_loader_rejects_bad_path_and_json(tmp_path: Path):
    with pytest.raises(InvalidCapabilityConfigurationError):
        load_trusted_capability_manifest(tmp_path, Path("../outside.json"))
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    with pytest.raises(InvalidCapabilityConfigurationError):
        load_trusted_capability_manifest(tmp_path, Path("bad.json"))


def test_capability_resolver_allows_and_denies_without_global_state():
    resolver = CapabilityResolver()
    allowed = resolver.evaluate(
        manifest(),
        "filesystem.read",
        "read",
        (Constraint.exact("mode", "safe"),),
        decision_id="decision-allow",
    )
    assert resolver.enforce(allowed) is allowed

    cases = [
        ("missing", "read", (Constraint.exact("mode", "safe"),), CapabilityReasonCode.CAPABILITY_NOT_FOUND),
        ("filesystem.read", "delete", (Constraint.exact("mode", "safe"),), CapabilityReasonCode.OPERATION_NOT_ALLOWED),
        ("filesystem.read", "read", (Constraint.exact("mode", "unsafe"),), CapabilityReasonCode.CONSTRAINT_DENIED),
    ]
    for capability_id, operation, constraints, reason in cases:
        denied = resolver.evaluate(
            manifest(),
            capability_id,
            operation,
            constraints,
            decision_id="decision-deny",
        )
        assert denied.reason_code is reason
        with pytest.raises(CapabilityDeniedError):
            resolver.enforce(denied)


def test_capability_intersection_is_restrictive_and_fails_closed():
    resolver = CapabilityResolver()
    child = resolver.intersect(
        manifest(),
        (RuntimeCapabilityGrant(grant().capability, ("read",), delegated_provenance(), grant().constraints),),
        "run-child",
        delegated_provenance(),
        manifest_id="manifest.child",
    )

    assert child.run_identity == RunIdentity("run-child", "run-root")
    assert child.grants[0].allowed_operations == ("read",)

    unknown = RuntimeCapabilityGrant(
        RuntimeCapability("unknown", "clockwork", ("read",), "Unknown"),
        ("read",),
        delegated_provenance(),
    )
    with pytest.raises(InvalidCapabilityConfigurationError) as exc_info:
        resolver.intersect(manifest(), (unknown,), "run-child", delegated_provenance(), manifest_id="empty")
    assert exc_info.value.reason_code == CapabilityReasonCode.EMPTY_INTERSECTION.value


def test_capability_events_and_inputs_are_typed_and_authority_neutral():
    resolver = CapabilityResolver()
    decision = resolver.evaluate(
        manifest(),
        "filesystem.read",
        "read",
        (Constraint.exact("mode", "safe"),),
        decision_id="decision-1",
    )

    assert capability_manifest_event("event-manifest", manifest()).event_type is AuditEventType.CAPABILITY_MANIFEST_CREATED
    assert capability_decision_event("event-decision", decision).event_type is AuditEventType.CAPABILITY_DECIDED
    parameters = inspect.signature(resolver.evaluate).parameters
    assert "prompt" not in parameters and "metadata" not in parameters

    import orchestra_runtime.capabilities as capabilities

    assert not any("registry" in name.casefold() for name in vars(capabilities))


def test_capability_invalid_construction_branches_are_typed():
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapability("", "clockwork", ("read",), "Read")
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapability("read", "clockwork", ("read", "READ"), "Read")
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapabilityManifest("manifest", RunIdentity("run"), "1", (), provenance())
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapabilityGrant(grant().capability, (), provenance())
    with pytest.raises(InvalidCapabilityConfigurationError):
        CapabilityDecision(
            "decision",
            "run",
            "manifest",
            "read",
            "read",
            (Constraint.exact("mode", "safe"), Constraint.exact("mode", "safe")),
            True,
            CapabilityReasonCode.ALLOWED,
        )


def test_capability_loader_rejects_missing_block_and_untrusted_file_provenance(tmp_path: Path):
    missing = tmp_path / "missing-block.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(InvalidCapabilityConfigurationError, match="missing"):
        load_trusted_capability_manifest(tmp_path, Path("missing-block.json"))

    relative = write_capability_policy(tmp_path)
    payload = json.loads((tmp_path / relative).read_text(encoding="utf-8"))
    payload["capability_manifest"]["provenance"]["source_type"] = "TRUSTED_COMPOSITION"
    (tmp_path / relative).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(InvalidCapabilityConfigurationError, match="repository provenance"):
        load_trusted_capability_manifest(tmp_path, relative)
