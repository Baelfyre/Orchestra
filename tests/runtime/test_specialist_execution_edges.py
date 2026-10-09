from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from orchestra_runtime.errors import RuntimeInitializationError
from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.lifecycle import LifecycleState
from orchestra_runtime.models import RouteDecision, ValidationResult
from orchestra_runtime.services import ContextAssembler, GovernanceValidator, RouterService
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SPECIALIST_EXECUTION_REQUEST_VERSION,
    SpecialistExecutionConstraint,
    SpecialistExecutionContractError,
    SpecialistExecutionMode,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistRuntimeExecutor,
    SpecialistSideEffectClass,
)

from test_runtime_authority_integration import build_active_environment


ROOT = Path(__file__).resolve().parents[2]


def _request(*, constraints: tuple[SpecialistExecutionConstraint, ...] = ()) -> SpecialistExecutionRequest:
    return SpecialistExecutionRequest.create(
        run_id="edge-run",
        parent_run_id="parent-run",
        correlation_id="corr-edge-run",
        adapter_name="codex",
        command_name="review-docs",
        specialist="scribe",
        project_root=str(ROOT),
        skill_source_path="skills/scribe/SKILL.md",
        skill_source_digest="1" * 64,
        task_input="review the documentation boundary",
        authority_decision_ref="authority-decision.edge",
        capability_decision_ref="capability-decision.edge",
        governance_status="NOT_REQUIRED",
        evaluated_governance_rules=("RULE_B", "RULE_A"),
        execution_constraints=constraints,
        execution_mode=SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    )


def _receipt(
    request: SpecialistExecutionRequest,
    *,
    status: SpecialistExecutionStatus = SpecialistExecutionStatus.COMPLETED,
    side_effect_class: SpecialistSideEffectClass = SpecialistSideEffectClass.NONE,
) -> SpecialistExecutionReceipt:
    return SpecialistExecutionReceipt(
        receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
        receipt_id="receipt.edge",
        request_id=request.request_id,
        request_digest=request.request_digest,
        run_id=request.run_id,
        adapter_name=request.adapter_name,
        command_name=request.command_name,
        specialist=request.specialist,
        engine_id="edge-engine",
        engine_version="1",
        host_execution_id="edge-host-execution",
        status=status,
        reason_code=f"EDGE_{status.value}",
        output=f"edge:{status.value}",
        evidence_refs=("evidence:b", "evidence:a", "evidence:a"),
        side_effect_class=side_effect_class,
        host_identity="codex-test-host",
        sandbox_identity="read-only",
        approval_policy_identity="never",
        artifact_refs=("artifact:b", "artifact:a"),
        changed_paths=(),
        started_at="2026-08-29T00:00:00Z",
        completed_at="2026-08-29T00:00:01Z",
    )


@pytest.mark.parametrize(
    ("constraint", "reason"),
    [
        (SpecialistExecutionConstraint("AUTHORITY", "path", "EXACT", ("README.md",)), None),
    ],
)
def test_constraint_reference_normalizes(constraint, reason) -> None:
    assert constraint.source == "AUTHORITY"
    assert constraint.to_dict()["values"] == ["README.md"]
    assert reason is None


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SpecialistExecutionConstraint("OTHER", "path", "EXACT", ("README.md",)),
        lambda: SpecialistExecutionConstraint("AUTHORITY", "path", "PREFIX", ("README.md",)),
        lambda: SpecialistExecutionConstraint("AUTHORITY", "path", "EXACT", ()),
        lambda: SpecialistExecutionConstraint("AUTHORITY", "path", "EXACT", ("README.md", "docs/README.md")),
    ],
)
def test_invalid_constraints_fail_closed(factory) -> None:
    with pytest.raises(SpecialistExecutionContractError) as error:
        factory()
    assert error.value.reason_code == "INVALID_SPECIALIST_EXECUTION_CONSTRAINT"


def test_empty_constraint_text_fails_closed() -> None:
    with pytest.raises(SpecialistExecutionContractError) as error:
        SpecialistExecutionConstraint("AUTHORITY", " ", "EXACT", ("README.md",))
    assert error.value.reason_code == "INVALID_SPECIALIST_EXECUTION_CONTRACT"


def test_request_rejects_version_digest_skill_input_duplicate_and_identity_drift() -> None:
    valid = _request()

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, request_version="orchestra.specialist-execution-request.v0")
    assert error.value.reason_code == "UNSUPPORTED_SPECIALIST_EXECUTION_REQUEST_VERSION"

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, request_digest="bad")
    assert error.value.reason_code == "INVALID_REQUEST_DIGEST"

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, skill_source_digest="bad")
    assert error.value.reason_code == "INVALID_SKILL_SOURCE_DIGEST"

    with pytest.raises(SpecialistExecutionContractError) as error:
        SpecialistExecutionRequest.create(
            run_id="edge-run",
            parent_run_id=None,
            correlation_id=None,
            adapter_name="codex",
            command_name="review-docs",
            specialist="scribe",
            project_root=str(ROOT),
            skill_source_path="skills/scribe/SKILL.md",
            skill_source_digest="1" * 64,
            task_input=" ",
            authority_decision_ref="authority-decision.edge",
            capability_decision_ref="capability-decision.edge",
            governance_status="NOT_REQUIRED",
            evaluated_governance_rules=(),
            execution_constraints=(),
            execution_mode=SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
        )
    assert error.value.reason_code == "EMPTY_SPECIALIST_TASK_INPUT"

    duplicate = (
        SpecialistExecutionConstraint("AUTHORITY", "path", "ALLOWED_SET", ("README.md",)),
        SpecialistExecutionConstraint("AUTHORITY", "path", "ALLOWED_SET", ("docs/README.md",)),
    )
    with pytest.raises(SpecialistExecutionContractError) as error:
        _request(constraints=duplicate)
    assert error.value.reason_code == "DUPLICATE_SPECIALIST_EXECUTION_CONSTRAINT"

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, task_input="different input")
    assert error.value.reason_code == "REQUEST_DIGEST_MISMATCH"

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, request_id="specialist-request." + "0" * 24)
    assert error.value.reason_code == "REQUEST_IDENTITY_MISMATCH"


def test_request_to_dict_preserves_non_null_lineage_and_canonical_sorting() -> None:
    request = _request(
        constraints=(
            SpecialistExecutionConstraint("CAPABILITY", "z", "ALLOWED_SET", ("b", "a")),
            SpecialistExecutionConstraint("AUTHORITY", "a", "EXACT", ("x",)),
        )
    )
    payload = request.to_dict()
    assert payload["request_version"] == SPECIALIST_EXECUTION_REQUEST_VERSION
    assert payload["parent_run_id"] == "parent-run"
    assert payload["correlation_id"] == "corr-edge-run"
    assert payload["evaluated_governance_rules"] == ["RULE_A", "RULE_B"]
    assert [item["source"] for item in payload["execution_constraints"]] == ["AUTHORITY", "CAPABILITY"]


def test_receipt_rejects_version_and_digest_drift_and_serializes_optional_identity() -> None:
    request = _request()
    valid = _receipt(request)

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, receipt_version="orchestra.specialist-execution-receipt.v0")
    assert error.value.reason_code == "UNSUPPORTED_SPECIALIST_EXECUTION_RECEIPT_VERSION"

    with pytest.raises(SpecialistExecutionContractError) as error:
        replace(valid, request_digest="bad")
    assert error.value.reason_code == "INVALID_REQUEST_DIGEST"

    payload = valid.to_dict()
    assert payload["host_identity"] == "codex-test-host"
    assert payload["sandbox_identity"] == "read-only"
    assert payload["approval_policy_identity"] == "never"
    assert payload["started_at"] == "2026-08-29T00:00:00Z"
    assert payload["completed_at"] == "2026-08-29T00:00:01Z"
    assert payload["evidence_refs"] == ["evidence:a", "evidence:b"]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("request_id", "specialist-request." + "0" * 24, "REQUEST_IDENTITY_MISMATCH"),
        ("adapter_name", "antigravity", "ADAPTER_IDENTITY_MISMATCH"),
        ("engine_id", "other-engine", "ENGINE_IDENTITY_MISMATCH"),
        ("engine_version", "2", "ENGINE_VERSION_MISMATCH"),
    ],
)
def test_receipt_identity_edges_fail_closed(field: str, value: str, reason: str) -> None:
    request = _request()
    receipt = replace(_receipt(request), **{field: value})
    with pytest.raises(SpecialistExecutionContractError) as error:
        receipt.assert_matches(request, engine_id="edge-engine", engine_version="1")
    assert error.value.reason_code == reason


class StatusEngine(ISpecialistExecutionEngine):
    def __init__(self, status: SpecialistExecutionStatus) -> None:
        self.status = status

    @property
    def engine_id(self) -> str:
        return "status-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        receipt = _receipt(request, status=self.status)
        return replace(receipt, engine_id=self.engine_id, engine_version=self.engine_version)


class MalformedEngine(ISpecialistExecutionEngine):
    @property
    def engine_id(self) -> str:
        return "malformed-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request):
        return object()


def _executor(engine, *, mode=SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE):
    environment = build_active_environment(run_id=f"edge-executor-{mode.value.casefold()}")
    executor = SpecialistRuntimeExecutor(
        environment.registry,
        RouterService(environment.registry),
        GovernanceValidator(),
        ContextAssembler(environment.repository),
        environment.composition,
        execution_engine=engine,
        execution_mode=mode,
    )
    return environment, executor


def test_executor_constructor_rejects_invalid_engine_and_host_native_without_engine() -> None:
    environment = build_active_environment(run_id="invalid-engine-run")
    with pytest.raises(RuntimeInitializationError) as error:
        SpecialistRuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            environment.composition,
            execution_engine=object(),  # type: ignore[arg-type]
        )
    assert error.value.reason_code == "INVALID_SPECIALIST_EXECUTION_ENGINE"

    environment = build_active_environment(run_id="missing-host-engine-run")
    with pytest.raises(RuntimeInitializationError) as error:
        SpecialistRuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            environment.composition,
            execution_engine=None,
            execution_mode=SpecialistExecutionMode.HOST_NATIVE,
        )
    assert error.value.reason_code == "ENGINE_NOT_CONFIGURED"


def test_internal_operation_without_bound_input_fails_closed() -> None:
    environment, executor = _executor(StatusEngine(SpecialistExecutionStatus.COMPLETED))
    operation = executor._execute_specialist(
        environment.adapter.adapter_name,
        RouteDecision("conductor", "conductor", False, "edge"),
        ValidationResult(True, "NOT_REQUIRED"),
    )
    assert operation.state is LifecycleState.FAILED
    assert operation.reason_code == "ENGINE_NOT_CONFIGURED"


def test_malformed_engine_receipt_fails_closed() -> None:
    environment, executor = _executor(MalformedEngine())
    result = executor.execute(environment.adapter, "conductor")
    assert result.success is False
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == "MALFORMED_EXECUTION_RECEIPT"


@pytest.mark.parametrize(
    ("status", "state"),
    [
        (SpecialistExecutionStatus.FAILED, LifecycleState.FAILED),
        (SpecialistExecutionStatus.CANCELLED, LifecycleState.CANCELLED),
        (SpecialistExecutionStatus.TIMED_OUT, LifecycleState.TIMED_OUT),
    ],
)
def test_engine_terminal_status_maps_to_existing_lifecycle(status, state) -> None:
    environment, executor = _executor(StatusEngine(status))
    result = executor.execute(environment.adapter, "conductor")
    assert result.success is False
    assert result.lifecycle_state == state.value
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == f"EDGE_{status.value}"
