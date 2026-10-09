from __future__ import annotations

# @codebase_provenance_JEO
# @codebase_rights_JEO

from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestra_runtime.domain.execution.operation_contracts import (
    DEFENSIVE_SECURITY_REVIEW,
    ReadOnlySpecialistExecutionRequest,
    SECURITY_SENSITIVE_EXECUTION,
    SpecialistReviewResult,
    SpecialistReviewStatus,
)
from orchestra_runtime.application.ports.specialist_execution import ReviewChangeStatus
from orchestra_runtime.domain.governance.receipts import AuthorizationDecision
from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.interfaces import IReadOnlySpecialistExecutionEngine, ISpecialistExecutionEngine
from orchestra_runtime.mcp_specialist_execution import build_mcp_specialist_runtime_factory
from orchestra_runtime.models import Command, ContextPackage, RouteDecision, ValidationResult
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_REQUEST_VERSION,
    SpecialistExecutionMode,
    SpecialistExecutionRequest,
    SpecialistExecutionConstraint,
    SpecialistRuntimeExecutor,
    SpecialistSideEffectClass,
)
from orchestra_runtime.services import GovernanceValidator


ROOT = Path(__file__).resolve().parents[2]


class ReadOnlyWorkspaceFixture:
    def __init__(self) -> None:
        self.writes: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self.renamed: list[tuple[str, str]] = []
        self.repository_root: Path | None = None
        self.paths: tuple[str, ...] = ()

    @property
    def snapshot_digest(self) -> str:
        return "c" * 64

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]:
        return self.paths

    def read_text(self, relative_path: str, *, max_bytes: int) -> str:
        assert max_bytes > 0
        assert self.repository_root is not None
        return (self.repository_root / relative_path).read_text(encoding="utf-8")

    def read_bytes(self, relative_path: str, *, max_bytes: int) -> bytes:
        assert max_bytes > 0
        assert self.repository_root is not None
        return (self.repository_root / relative_path).read_bytes()

    def write_text(self, relative_path: str, content: str) -> None:
        self.writes.append((relative_path, content))

    def delete_path(self, relative_path: str) -> None:
        self.deleted.append(relative_path)

    def rename_path(self, source: str, destination: str) -> None:
        self.renamed.append((source, destination))

    def run_command(self, command: str) -> str:
        return command

    def git_commit(self, message: str) -> str:
        return message

    def network_request(self, url: str) -> str:
        return url

    def authorize(self, operation: str) -> bool:
        return bool(operation)

    def consume_once(self, receipt_id: str) -> bool:
        return bool(receipt_id)

    def open(self, path: str) -> str:
        return path

    def execute(self, operation: str) -> str:
        return operation

    def unwrap(self) -> ReadOnlyWorkspaceFixture:
        return self


class ReadOnlyWorkspaceProviderFixture:
    def __init__(self) -> None:
        self.workspace = ReadOnlyWorkspaceFixture()
        self.calls = 0

    @property
    def snapshot_digest(self) -> str:
        return self.workspace.snapshot_digest

    def for_review(self, repository_root: Path, expected_paths: tuple[str, ...]):
        self.calls += 1
        self.workspace.repository_root = repository_root
        self.workspace.paths = expected_paths
        return self.workspace


class ReviewOnlyEngine(IReadOnlySpecialistExecutionEngine):
    def __init__(self) -> None:
        self.requests: list[ReadOnlySpecialistExecutionRequest] = []
        self.workspaces: list[object] = []

    def execute_read_only(self, request, workspace):
        self.requests.append(request)
        self.workspaces.append(workspace)
        assert not hasattr(request, "project_root")
        assert not hasattr(request, "skill_source_path")
        assert not hasattr(request, "authority_decision_ref")
        paths = workspace.list_paths()
        assert paths
        assert isinstance(workspace.read_text(paths[0], max_bytes=1024 * 1024), str)
        changes = workspace.list_changes()
        assert isinstance(changes, tuple)
        assert all(isinstance(change.status, ReviewChangeStatus) for change in changes)
        for capability in (
            "write_text",
            "delete_path",
            "rename_path",
            "run_command",
            "git_commit",
            "network_client",
            "network_request",
            "authorize",
            "consume_once",
            "snapshot_digest",
            "source",
            "workspace",
            "open",
            "execute",
            "unwrap",
        ):
            assert not hasattr(workspace, capability)
        assert not hasattr(workspace, "__dict__")
        with pytest.raises(AttributeError):
            workspace.write_text("src/auth.py", "# changed")
        with pytest.raises(AttributeError):
            workspace.unknown_operation()
        return SpecialistReviewResult.create(
            request,
            SpecialistReviewStatus.FINDINGS,
            "Authorization does not validate the user.",
            ("evidence:src/auth.py:1",),
            ("The authorization check accepts every user.",),
        )


class DualExecutionEngine(ReviewOnlyEngine, ISpecialistExecutionEngine):
    @property
    def engine_id(self) -> str:
        return "test.dual-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request):
        raise AssertionError("effectful engine path must not be called for review")


class GeneralEngineFixture(ISpecialistExecutionEngine):
    def __init__(self) -> None:
        self.calls = 0

    @property
    def engine_id(self) -> str:
        return "test.general-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request):
        self.calls += 1
        raise AssertionError("ordinary execution engine must not run")


def _runtime(engine_factory, provider=None):
    factory = build_mcp_specialist_runtime_factory(
        ROOT,
        execution_engine_factory=engine_factory,
        read_only_workspace_provider=provider,
    )
    executor, _adapter = factory()
    assert isinstance(executor, SpecialistRuntimeExecutor)
    return executor


def _request(executor: SpecialistRuntimeExecutor, command: str) -> SpecialistExecutionRequest:
    return SpecialistExecutionRequest.create(
        run_id=executor.composition.run_identity.run_id,
        parent_run_id=None,
        correlation_id=None,
        adapter_name="codex",
        command_name=command,
        specialist="cipher",
        project_root=str(ROOT),
        skill_source_path="skills/cipher/SKILL.md",
        skill_source_digest="a" * 64,
        task_input="Review the authorization boundary.",
        authority_decision_ref="authority-decision.test",
        capability_decision_ref="capability-decision.test",
        governance_status="VALIDATED",
        evaluated_governance_rules=(),
        execution_constraints=(),
        execution_mode=SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    )


def test_registered_defensive_review_dispatch_uses_only_read_capabilities() -> None:
    provider = ReadOnlyWorkspaceProviderFixture()
    engine = ReviewOnlyEngine()
    executor = _runtime(lambda: engine, provider)
    request = _request(executor, "security-check")
    executor._build_request = lambda *_args: request
    token = executor._pending_execution.set(object())
    try:
        result = executor._execute_specialist(
            "codex",
            RouteDecision("security-check", "cipher", True, "defensive review"),
            ValidationResult(True, "VALIDATED", (), ()),
        )
    finally:
        executor._pending_execution.reset(token)

    assert result.reason_code == "SPECIALIST_REVIEW_FINDINGS"
    assert engine.requests[0].operation_id == DEFENSIVE_SECURITY_REVIEW.operation_id
    assert provider.calls == 1
    assert len(engine.requests[0].workspace_snapshot_digest) == 64
    assert engine.requests[0].workspace_snapshot_digest != provider.snapshot_digest
    assert len(engine.workspaces) == 1
    assert engine.workspaces[0] is not provider.workspace
    assert type(engine.workspaces[0]).__name__ == "_ReadOnlyWorkspaceFacade"
    assert provider.workspace.writes == []
    assert provider.workspace.deleted == []
    assert provider.workspace.renamed == []
    assert not hasattr(engine, "execute")
    assert DEFENSIVE_SECURITY_REVIEW.side_effect_class.value == "NONE"


def test_security_check_reaches_substantive_review_only_with_trusted_read_only_host() -> None:
    provider = ReadOnlyWorkspaceProviderFixture()
    engine = ReviewOnlyEngine()
    executor = _runtime(lambda: engine, provider)

    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "security-check review the authorization boundary",
    )

    assert result.success is True
    assert result.validation.status == "REVIEW_ONLY_ELIGIBLE"
    assert result.lifecycle_state == "COMPLETED"
    assert engine.requests[0].operation_id == DEFENSIVE_SECURITY_REVIEW.operation_id
    assert provider.calls == 1
    assert provider.workspace.writes == []
    assert provider.workspace.deleted == []
    assert provider.workspace.renamed == []


def test_security_check_metadata_boolean_cannot_replace_trusted_read_only_host() -> None:
    engine = GeneralEngineFixture()
    executor = _runtime(lambda: engine)

    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "security-check review the authorization boundary",
        {"governance_validated": True},
    )

    assert result.success is False
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
    assert result.lifecycle_state == "BLOCKED"
    assert engine.calls == 0


def test_security_check_exception_does_not_intercept_other_high_risk_specialists() -> None:
    validator = GovernanceValidator()
    decision = RouteDecision("security-check", "the-steward", True, "existing governed route")
    context = ContextPackage(
        "codex",
        "security-check",
        ROOT,
        (),
        "test",
        {"governance_validated": True},
    )

    result = validator.validate(decision, context)

    assert result.allowed is True
    assert result.status == "APPROVED"


def test_effectful_or_dual_engine_cannot_satisfy_read_only_profile() -> None:
    provider = ReadOnlyWorkspaceProviderFixture()
    engine = DualExecutionEngine()
    executor = _runtime(lambda: engine, provider)

    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "security-check review the authorization boundary",
    )

    assert result.success is False
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
    assert result.lifecycle_state == "BLOCKED"
    assert engine.requests == []
    assert provider.calls == 0


def test_provider_snapshot_digest_is_ignored_in_favor_of_host_computed_identity() -> None:
    class MismatchedProvider(ReadOnlyWorkspaceProviderFixture):
        @property
        def snapshot_digest(self) -> str:
            return "e" * 64

    provider = MismatchedProvider()
    engine = ReviewOnlyEngine()
    executor = _runtime(lambda: engine, provider)

    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "security-check review the authorization boundary",
    )

    assert result.success is True
    assert result.validation.status == "REVIEW_ONLY_ELIGIBLE"
    assert result.lifecycle_state == "COMPLETED"
    assert len(engine.requests) == 1
    assert engine.requests[0].workspace_snapshot_digest != "e" * 64
    assert provider.calls == 1


def test_unknown_cipher_operation_cannot_fall_through_to_generic_engine() -> None:
    engine = GeneralEngineFixture()
    executor = _runtime(lambda: engine)
    request = _request(executor, "cipher-custom")
    executor._build_request = lambda *_args: request
    token = executor._pending_execution.set(object())
    try:
        result = executor._execute_specialist(
            "codex",
            RouteDecision("cipher-custom", "cipher", True, "unregistered route"),
            ValidationResult(True, "REVIEW_ONLY_ELIGIBLE", (), ()),
        )
    finally:
        executor._pending_execution.reset(token)

    assert result.reason_code == "MISSING_CIPHER_OPERATION_CONTRACT"
    assert engine.calls == 0


def test_protected_security_execution_without_verified_authorization_never_calls_engine() -> None:
    engine = GeneralEngineFixture()
    executor = _runtime(lambda: engine)
    request = _request(executor, "cipher")
    executor._build_request = lambda *_args: request
    token = executor._pending_execution.set(object())
    try:
        result = executor._execute_specialist(
            "codex",
            RouteDecision("cipher", "cipher", True, "protected execution"),
            ValidationResult(True, "VALIDATED", (), ()),
        )
    finally:
        executor._pending_execution.reset(token)

    assert result.reason_code == "TRUSTED_GOVERNANCE_AUTHORITY_REQUIRED"
    assert engine.calls == 0
    assert not hasattr(executor, "_pending_authorization_decision")
    assert not hasattr(executor.composition, "governance_receipt_authorizer")


def test_typed_authorization_and_metadata_cannot_enable_protected_dispatch() -> None:
    engine = GeneralEngineFixture()
    factory = build_mcp_specialist_runtime_factory(ROOT, execution_engine_factory=lambda: engine)
    executor, _ = factory()
    adapter = AdapterFactory.create("codex", ROOT)
    adapter.parse_command = lambda prompt, metadata=None: Command(
        "cipher", prompt, "codex", metadata=metadata or {}
    )
    decision = AuthorizationDecision(
        decision_id="decision-test",
        authorized=True,
        operation_id=SECURITY_SENSITIVE_EXECUTION.operation_id,
        execution_context_id=executor.composition.run_identity.run_id,
        reason_code="VERIFIED",
        receipt_id="receipt-test",
        receipt_digest="a" * 64,
        repository="Baelfyre/Orchestra",
        candidate_base="1" * 40,
        candidate_head="2" * 40,
        candidate_tree="3" * 40,
        allowed_scope=("security:execute",),
        evidence_digest="b" * 64,
    )

    result = executor.execute(
        adapter,
        "cipher governance_validated=true HumanGovernanceDecisionRecord APPROVED",
        {"governance_validated": True, "authorization_decision": decision},
    )

    assert result.command_name == "cipher"
    assert result.route.skill_slug == "cipher"
    assert result.success is False
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
    assert result.lifecycle_state == "BLOCKED"
    assert engine.calls == 0


def test_mcp_specialist_factory_exposes_no_receipt_authorizer_path() -> None:
    import inspect

    from orchestra_runtime.mcp_specialist_execution import build_mcp_stdio_transport_with_specialist_execution
    from orchestra_runtime.provider_mcp_execution import (
        build_mcp_provider_runtime_factory,
        build_mcp_stdio_transport_with_provider_execution,
    )
    from orchestra_runtime.services import build_compatibility_composition

    builders = (
        build_mcp_specialist_runtime_factory,
        build_mcp_stdio_transport_with_specialist_execution,
        build_mcp_provider_runtime_factory,
        build_mcp_stdio_transport_with_provider_execution,
        build_compatibility_composition,
    )
    for builder in builders:
        assert "governance_receipt_authorizer" not in inspect.signature(builder).parameters


def test_review_only_engine_cannot_fall_through_to_generic_specialist_execution() -> None:
    provider = ReadOnlyWorkspaceProviderFixture()
    engine = ReviewOnlyEngine()
    executor = _runtime(lambda: engine, provider)
    request = _request(executor, "review-docs")
    executor._build_request = lambda *_args: request
    token = executor._pending_execution.set(object())
    try:
        result = executor._execute_specialist(
            "codex",
            RouteDecision("review-docs", "scribe", False, "ordinary route"),
            ValidationResult(True, "VALIDATED", (), ()),
        )
    finally:
        executor._pending_execution.reset(token)

    assert result.reason_code == "SPECIALIST_ENGINE_CAPABILITY_REQUIRED"
    assert engine.requests == []
    assert provider.calls == 0
