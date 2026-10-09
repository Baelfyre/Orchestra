from dataclasses import FrozenInstanceError
import inspect
import json
from pathlib import Path

import pytest

from orchestra_runtime.authority import (
    AuthorityDecision,
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityReasonCode,
    AuthorityScope,
    Constraint,
    ConstraintKind,
    ProvenanceSource,
    TargetSelector,
    authority_decision_event,
    initialization_failure_event,
    load_trusted_authority,
    root_authority_event,
)
from orchestra_runtime.errors import (
    AuthorityDeniedError,
    CapabilityCollisionError,
    CapabilityDeniedError,
    ConflictingTerminalSignalError,
    DelegationDepthViolationError,
    DelegationRejectedError,
    InvalidAuthorityConfigurationError,
    InvalidCapabilityConfigurationError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
)
from orchestra_runtime.models import AuditEventType, RunIdentity, RuntimeAuditEvent


def root_provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.TRUSTED_REPOSITORY_POLICY,
        "policy.root",
        "1.0",
        "runtime.composition",
    )


def root_scope() -> AuthorityScope:
    return AuthorityScope(
        "scope.root",
        (TargetSelector("repository:orchestra"),),
        ("write", "read"),
        (Constraint.allowed_set("environment", ["test", "dev"]),),
        root_provenance(),
    )


def test_shared_models_are_immutable_and_deterministic():
    run = RunIdentity("run-root")
    event = RuntimeAuditEvent(
        "event-1",
        AuditEventType.ROOT_AUTHORITY_CREATED,
        run.run_id,
        "scope.root",
        "CREATED",
        provenance_ids=("policy.root", "policy.root"),
        details=(("scope", "scope.root"), ("mode", "trusted")),
    )

    assert run.to_dict() == {"run_id": "run-root", "parent_run_id": None}
    assert event.to_dict()["details"] == {"mode": "trusted", "scope": "scope.root"}
    assert event.provenance_ids == ("policy.root",)
    with pytest.raises(FrozenInstanceError):
        run.run_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="differ"):
        RunIdentity("same", "same")


@pytest.mark.parametrize(
    "error_type",
    [
        InvalidAuthorityConfigurationError,
        AuthorityDeniedError,
        InvalidCapabilityConfigurationError,
        CapabilityCollisionError,
        CapabilityDeniedError,
        DelegationRejectedError,
        DelegationDepthViolationError,
        InvalidLifecycleTransitionError,
        InvalidLifecycleSignalError,
        ConflictingTerminalSignalError,
    ],
)
def test_error_taxonomy_carries_immutable_context(error_type):
    error = error_type("blocked", "STABLE_REASON", {"target": "safe", "operation": "read"})

    assert error.reason_code == "STABLE_REASON"
    assert error.context == (("operation", "read"), ("target", "safe"))
    assert isinstance(error.context, tuple)


def test_authority_provenance_rejects_unstructured_delegation():
    with pytest.raises(InvalidAuthorityConfigurationError) as exc_info:
        AuthorityProvenance(ProvenanceSource.ACCEPTED_DELEGATION, "child", "1", "runtime")

    assert exc_info.value.reason_code == AuthorityReasonCode.UNTRUSTED_PROVENANCE.value


def test_constraints_normalize_mutable_inputs_and_intersect_deterministically():
    values = ["prod", "dev", "dev"]
    allowed = Constraint.allowed_set("environment", values)
    values.append("test")

    assert allowed.values == ("dev", "prod")
    assert allowed.kind is ConstraintKind.ALLOWED_SET
    assert allowed.permits(Constraint.exact("environment", "dev"))
    assert allowed.intersect(Constraint.allowed_set("environment", ["stage", "prod"])) == Constraint.exact(
        "environment", "prod"
    )
    assert allowed.intersect(Constraint.exact("environment", "test")) is None


def test_authority_scope_is_exact_immutable_and_serializable():
    targets = [TargetSelector("repository:orchestra")]
    operations = ["write", "read"]
    scope = AuthorityScope("Scope.Root", targets, operations, (), root_provenance())
    targets.append(TargetSelector("repository:other"))
    operations.append("delete")

    assert scope.scope_id == "scope.root"
    assert scope.operations == ("read", "write")
    assert [item.value for item in scope.targets] == ["repository:orchestra"]
    assert AuthorityScope.from_dict(scope.to_dict()) == scope
    with pytest.raises(FrozenInstanceError):
        scope.operations = ()  # type: ignore[misc]
    with pytest.raises(InvalidAuthorityConfigurationError, match="exact"):
        TargetSelector("repository:*")


def test_authority_decision_serialization_uses_stable_enum_strings():
    decision = AuthorityDecision(
        "decision-1",
        "run-1",
        "scope.root",
        TargetSelector("repository:orchestra"),
        "read",
        (),
        True,
        AuthorityReasonCode.ALLOWED,
        matched_targets=("repository:orchestra",),
        matched_operations=("read",),
        provenance_id="policy.root",
    )

    assert decision.to_dict()["reason_code"] == "ALLOWED"
    assert decision == decision


def write_authority_policy(repo_root: Path, scope: AuthorityScope | None = None) -> Path:
    path = repo_root / "config" / "authority.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"authority_scope": (scope or root_scope()).to_dict()}), encoding="utf-8")
    return path.relative_to(repo_root)


def test_trusted_authority_loader_accepts_contained_repository_policy(tmp_path: Path):
    relative = write_authority_policy(tmp_path)

    loaded = load_trusted_authority(tmp_path, relative)

    assert loaded == root_scope()


@pytest.mark.parametrize("content", ["", "{broken", "[]"])
def test_trusted_authority_loader_rejects_empty_malformed_or_non_object_json(tmp_path: Path, content: str):
    path = tmp_path / "authority.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(InvalidAuthorityConfigurationError):
        load_trusted_authority(tmp_path, Path("authority.json"))


def test_trusted_authority_loader_rejects_missing_traversal_absolute_and_untrusted_provenance(tmp_path: Path):
    with pytest.raises(InvalidAuthorityConfigurationError, match="missing"):
        load_trusted_authority(tmp_path, Path("missing.json"))
    with pytest.raises(InvalidAuthorityConfigurationError, match="under repository"):
        load_trusted_authority(tmp_path, Path("../outside.json"))
    with pytest.raises(InvalidAuthorityConfigurationError, match="under repository"):
        load_trusted_authority(tmp_path, tmp_path / "absolute.json")

    delegated = AuthorityScope(
        "scope.child",
        root_scope().targets,
        root_scope().operations,
        root_scope().constraints,
        AuthorityProvenance(
            ProvenanceSource.ACCEPTED_DELEGATION,
            "delegation.accepted",
            "1",
            "runtime",
            "parent-run",
            "parent-decision",
        ),
        "scope.root",
    )
    relative = write_authority_policy(tmp_path, delegated)
    with pytest.raises(InvalidAuthorityConfigurationError, match="repository provenance"):
        load_trusted_authority(tmp_path, relative)


def test_trusted_authority_loader_rejects_symlink_escape(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"authority_scope": root_scope().to_dict()}), encoding="utf-8")
    link = repo_root / "authority.json"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")

    with pytest.raises(InvalidAuthorityConfigurationError, match="escapes"):
        load_trusted_authority(repo_root, Path("authority.json"))


def test_authority_evaluator_allows_exact_target_operation_and_constraints():
    evaluator = AuthorityEvaluator()
    decision = evaluator.evaluate(
        evaluator.validate_root(root_scope()),
        TargetSelector("repository:orchestra"),
        "read",
        (Constraint.exact("environment", "dev"),),
        run_id="run-1",
        decision_id="decision-allow",
    )

    assert evaluator.enforce(decision) is decision
    assert decision.reason_code is AuthorityReasonCode.ALLOWED


@pytest.mark.parametrize(
    ("target", "operation", "constraints", "reason"),
    [
        ("repository:other", "read", (Constraint.exact("environment", "dev"),), AuthorityReasonCode.TARGET_NOT_ALLOWED),
        ("repository:orchestra/sub", "read", (Constraint.exact("environment", "dev"),), AuthorityReasonCode.TARGET_NOT_ALLOWED),
        ("repository:orchestra", "delete", (Constraint.exact("environment", "dev"),), AuthorityReasonCode.OPERATION_NOT_ALLOWED),
        ("repository:orchestra", "read", (Constraint.exact("environment", "prod"),), AuthorityReasonCode.CONSTRAINT_DENIED),
    ],
)
def test_authority_evaluator_denies_by_default(target, operation, constraints, reason):
    evaluator = AuthorityEvaluator()
    decision = evaluator.evaluate(
        root_scope(),
        TargetSelector(target),
        operation,
        constraints,
        run_id="run-1",
        decision_id="decision-deny",
    )

    assert decision.allowed is False
    assert decision.reason_code is reason
    with pytest.raises(AuthorityDeniedError) as exc_info:
        evaluator.enforce(decision)
    assert exc_info.value.reason_code == reason.value


def test_authority_intersection_is_restrictive_and_fails_closed():
    evaluator = AuthorityEvaluator()
    provenance = AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation.accepted",
        "1",
        "runtime",
        "parent-run",
        "parent-decision",
    )
    requested = AuthorityScope(
        "scope.child",
        (TargetSelector("repository:orchestra"),),
        ("read",),
        (Constraint.exact("environment", "dev"),),
        root_provenance(),
    )

    child = evaluator.intersect(root_scope(), requested, provenance)

    assert child.parent_scope_id == "scope.root"
    assert child.operations == ("read",)
    assert child.constraints == (Constraint.exact("environment", "dev"),)

    empty = AuthorityScope("scope.empty", (TargetSelector("repository:other"),), ("read",), (), root_provenance())
    with pytest.raises(InvalidAuthorityConfigurationError) as exc_info:
        evaluator.intersect(root_scope(), empty, provenance)
    assert exc_info.value.reason_code == AuthorityReasonCode.EMPTY_INTERSECTION.value


def test_authority_events_are_typed_and_input_surface_excludes_prompt_metadata():
    evaluator = AuthorityEvaluator()
    decision = evaluator.evaluate(
        root_scope(),
        TargetSelector("repository:orchestra"),
        "read",
        (Constraint.exact("environment", "dev"),),
        run_id="run-1",
        decision_id="decision-1",
    )

    assert root_authority_event("event-root", "run-1", root_scope()).event_type is AuditEventType.ROOT_AUTHORITY_CREATED
    assert authority_decision_event("event-decision", decision).event_type is AuditEventType.AUTHORITY_DECIDED
    assert initialization_failure_event("event-fail", "run-1", "policy", "INVALID").event_type is AuditEventType.INITIALIZATION_FAILED
    parameters = inspect.signature(evaluator.evaluate).parameters
    assert "prompt" not in parameters
    assert "metadata" not in parameters


def test_authority_invalid_construction_branches_are_typed():
    with pytest.raises(InvalidAuthorityConfigurationError):
        TargetSelector("")
    with pytest.raises(InvalidAuthorityConfigurationError):
        AuthorityScope("bad id!", root_scope().targets, ("read",), (), root_provenance())
    with pytest.raises(InvalidAuthorityConfigurationError):
        Constraint("mode", ConstraintKind.EXACT, ("one", "two"))
    with pytest.raises(InvalidAuthorityConfigurationError):
        AuthorityScope("scope", root_scope().targets * 2, ("read",), (), root_provenance())
    with pytest.raises(InvalidAuthorityConfigurationError):
        AuthorityScope(
            "scope",
            root_scope().targets,
            ("read",),
            (Constraint.exact("mode", "safe"), Constraint.exact("mode", "safe")),
            root_provenance(),
        )
    with pytest.raises(InvalidAuthorityConfigurationError):
        AuthorityDecision(
            "decision",
            "run",
            "scope",
            TargetSelector("target"),
            "read",
            (Constraint.exact("mode", "safe"), Constraint.exact("mode", "safe")),
            True,
            AuthorityReasonCode.ALLOWED,
            provenance_id="policy",
        )


def test_authority_constraint_mismatch_and_unconstrained_evaluation():
    mode = Constraint.exact("mode", "safe")
    assert mode.permits(Constraint.exact("environment", "safe")) is False
    assert mode.intersect(Constraint.exact("environment", "safe")) is None

    scope = AuthorityScope("scope", (TargetSelector("target"),), ("read",), (), root_provenance())
    decision = AuthorityEvaluator().evaluate(
        scope,
        TargetSelector("target"),
        "read",
        (),
        run_id="run",
        decision_id="decision",
    )
    assert decision.allowed is True


def test_authority_loader_rejects_missing_block_malformed_scope_and_invalid_root(tmp_path: Path):
    missing = tmp_path / "missing-block.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(InvalidAuthorityConfigurationError, match="missing authority_scope"):
        load_trusted_authority(tmp_path, Path("missing-block.json"))

    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"authority_scope": {"scope_id": "scope"}}), encoding="utf-8")
    with pytest.raises(InvalidAuthorityConfigurationError):
        load_trusted_authority(tmp_path, Path("malformed.json"))

    with pytest.raises(InvalidAuthorityConfigurationError, match="root"):
        load_trusted_authority(tmp_path / "missing-root", Path("policy.json"))


def test_root_validation_and_intersection_require_correct_provenance():
    delegated = AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation",
        "1",
        "runtime",
        "parent-run",
        "parent-decision",
    )
    child = AuthorityScope("child", root_scope().targets, ("read",), (), delegated, "scope.root")
    evaluator = AuthorityEvaluator()
    with pytest.raises(InvalidAuthorityConfigurationError, match="trusted root"):
        evaluator.validate_root(child)
    with pytest.raises(InvalidAuthorityConfigurationError, match="accepted delegation"):
        evaluator.intersect(root_scope(), root_scope(), root_provenance())


def test_runtime_contract_error_rejects_empty_reason_and_duplicate_context():
    with pytest.raises(ValueError, match="reason_code"):
        AuthorityDeniedError("denied", "")
    with pytest.raises(ValueError, match="unique"):
        AuthorityDeniedError("denied", "DENIED", (("key", "one"), ("key", "two")))
