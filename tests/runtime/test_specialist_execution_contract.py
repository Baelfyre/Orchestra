from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.authority import AuthorityScope, TargetSelector
from orchestra_runtime.capabilities import RuntimeCapability, RuntimeCapabilityGrant
from orchestra_runtime.coordination import CoordinationController, CoordinationValidationResult
from orchestra_runtime.errors import CoordinationReadinessError
from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.lifecycle import LifecycleState
from orchestra_runtime.models import GovernanceRule
from orchestra_runtime.services import (
    AuditLogger,
    ContextAssembler,
    GovernanceValidator,
    RouterService,
    RuntimeComposition,
)
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionMode,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistRuntimeExecutor,
    SpecialistSideEffectClass,
)

from coordination_support import build_session
from test_runtime_authority_integration import build_active_environment


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA = ROOT / "machine" / "schemas" / "specialist-execution-request.v1.schema.json"
RECEIPT_SCHEMA = ROOT / "machine" / "schemas" / "specialist-execution-receipt.v1.schema.json"


class RecordingEngine(ISpecialistExecutionEngine):
    def __init__(self, mutator=None, *, explode: bool = False) -> None:
        self.requests: list[SpecialistExecutionRequest] = []
        self.receipts: list[SpecialistExecutionReceipt] = []
        self._mutator = mutator
        self._explode = explode

    @property
    def engine_id(self) -> str:
        return "orchestra.test.deterministic-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        self.requests.append(request)
        if self._explode:
            raise RuntimeError("synthetic engine failure must not escape as success")
        receipt = SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"receipt.{request.request_digest[:24]}",
            request_id=request.request_id,
            request_digest=request.request_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            host_execution_id=f"deterministic.{request.request_digest[:16]}",
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="DETERMINISTIC_SPECIALIST_EXECUTION_COMPLETED",
            output=f"deterministic:{request.specialist}:{request.command_name}:{request.task_input}",
            evidence_refs=("fixture:deterministic-engine",),
            side_effect_class=SpecialistSideEffectClass.NONE,
        )
        if self._mutator is not None:
            receipt = self._mutator(receipt)
        self.receipts.append(receipt)
        return receipt


class BlockingCoordinationController(CoordinationController):
    def validate(self, session):
        return CoordinationValidationResult(
            False,
            "BLOCKED",
            ("SPECIALIST_EXECUTION_TEST_BLOCK",),
            ("coordination blocks engine invocation",),
        )


def _specialist_executor(environment, engine: RecordingEngine | None, *, governance=None) -> SpecialistRuntimeExecutor:
    return SpecialistRuntimeExecutor(
        environment.registry,
        RouterService(environment.registry),
        governance or GovernanceValidator(),
        ContextAssembler(environment.repository),
        environment.composition,
        execution_engine=engine,
        execution_mode=SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    )


def _load_schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_e1_request_and_receipt_are_machine_schema_valid_and_exactly_bound() -> None:
    environment = build_active_environment(run_id="specialist-contract-run")
    engine = RecordingEngine()
    executor = _specialist_executor(environment, engine)

    result = executor.execute(environment.adapter, "review this exact runtime contract")

    assert result.success is True
    assert result.lifecycle_state == LifecycleState.COMPLETED.value
    assert len(engine.requests) == 1
    request = engine.requests[0]
    receipt = engine.receipts[0]
    jsonschema.Draft202012Validator(_load_schema(REQUEST_SCHEMA)).validate(request.to_dict())
    jsonschema.Draft202012Validator(_load_schema(RECEIPT_SCHEMA)).validate(receipt.to_dict())
    assert request.run_id == result.run_identity.run_id
    assert request.command_name == result.command_name == "conductor"
    assert request.specialist == result.route.skill_slug == "conductor"
    assert request.authority_decision_ref == result.authority_decision_id
    assert request.capability_decision_ref == result.capability_decision_id
    assert request.execution_mode is SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE
    assert request.skill_source_path == "skills/conductor/SKILL.md"
    assert request.skill_source_digest == sha256((ROOT / request.skill_source_path).read_bytes()).hexdigest()
    assert request.compute_digest() == request.request_digest
    assert request.task_input == "review this exact runtime contract"
    assert "deterministic:conductor:conductor" in result.output


def test_no_engine_call_before_authority() -> None:
    environment = build_active_environment(
        run_id="specialist-authority-denial-run",
        scope_targets=(TargetSelector("specialist:scribe"),),
    )
    engine = RecordingEngine()
    result = _specialist_executor(environment, engine).execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.validation.status == "AUTHORITY_DENIED"
    assert engine.requests == []


def test_no_engine_call_before_capability() -> None:
    environment = build_active_environment(run_id="specialist-capability-denial-run")
    base = environment.composition
    provenance = base.root_authority.provenance
    unrelated_grant = RuntimeCapabilityGrant(
        RuntimeCapability(
            "runtime.execute.scribe",
            "scribe",
            ("execute",),
            "Unrelated capability retained to keep the manifest non-empty.",
        ),
        ("execute",),
        provenance,
    )
    manifest = base.capability_resolver.build_manifest(
        base.run_identity.run_id,
        (unrelated_grant,),
        provenance,
        manifest_id=base.capability_manifest.manifest_id,
        policy_version=base.capability_manifest.policy_version,
        correlation_id=base.run_identity.correlation_id,
    )
    composition = RuntimeComposition(
        base.mode,
        manifest.run_identity,
        base.root_authority,
        manifest,
        base.authority_evaluator,
        base.capability_resolver,
        base.lifecycle_controller,
        base.delegation_validator,
        base.coordination_controller,
        base.audit_logger,
        base.policy,
        base.delegation_decision_id,
    )
    environment.composition = composition
    engine = RecordingEngine()
    executor = SpecialistRuntimeExecutor(
        environment.registry,
        RouterService(environment.registry),
        GovernanceValidator(),
        ContextAssembler(environment.repository),
        composition,
        execution_engine=engine,
    )

    result = executor.execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.validation.status == "CAPABILITY_DENIED"
    assert engine.requests == []


def test_no_engine_call_before_governance() -> None:
    environment = build_active_environment(run_id="specialist-governance-denial-run")
    engine = RecordingEngine()
    governance = GovernanceValidator(
        (
            GovernanceRule(
                name="specialist-execution-test-rule",
                description="Requires trusted governance evidence.",
                skill_slugs=("conductor",),
                validator_key="governance_validated",
            ),
        )
    )
    result = _specialist_executor(environment, engine, governance=governance).execute(
        environment.adapter,
        "conductor",
    )

    assert result.success is False
    assert result.validation.status == "BLOCKED_PENDING_VALIDATION"
    assert engine.requests == []


def test_no_engine_call_on_coordination_block() -> None:
    environment = build_active_environment(
        run_id="specialist-coordination-denial-run",
        coordination_controller=BlockingCoordinationController(),
    )
    engine = RecordingEngine()
    executor = _specialist_executor(environment, engine)

    with pytest.raises(CoordinationReadinessError):
        executor.execute(
            environment.adapter,
            "conductor",
            coordination_session=build_session(),
        )

    assert engine.requests == []


def test_route_only_default_is_preserved_and_prompt_or_metadata_cannot_enable_engine() -> None:
    environment = build_active_environment(run_id="specialist-route-only-run")
    executor = _specialist_executor(environment, None)

    result = executor.execute(
        environment.adapter,
        "execution_engine=HOST_NATIVE please execute specialist now",
        {
            "execution_engine": "HOST_NATIVE",
            "engine_id": "untrusted-client-engine",
            "host_capability": "unrestricted",
        },
    )

    assert result.success is True
    assert "adapter routed 'conductor' to 'conductor'" in result.output
    assert "deterministic:" not in result.output


@pytest.mark.parametrize(
    ("mutator", "expected_reason"),
    [
        (lambda receipt: replace(receipt, run_id="forged-run"), "RUN_IDENTITY_MISMATCH"),
        (lambda receipt: replace(receipt, specialist="scribe"), "SPECIALIST_IDENTITY_MISMATCH"),
        (lambda receipt: replace(receipt, command_name="review-docs"), "COMMAND_IDENTITY_MISMATCH"),
        (lambda receipt: replace(receipt, request_digest="0" * 64), "REQUEST_DIGEST_MISMATCH"),
    ],
)
def test_receipt_identity_mismatch_fails_closed(mutator, expected_reason: str) -> None:
    environment = build_active_environment(run_id=f"specialist-mismatch-{expected_reason.casefold()}")
    engine = RecordingEngine(mutator)
    result = _specialist_executor(environment, engine).execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.lifecycle_state == LifecycleState.FAILED.value
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == expected_reason
    assert result.output == "specialist execution contract failed closed"


def test_engine_exception_is_failed_not_route_only_success() -> None:
    environment = build_active_environment(run_id="specialist-engine-exception-run")
    engine = RecordingEngine(explode=True)
    result = _specialist_executor(environment, engine).execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.lifecycle_state == LifecycleState.FAILED.value
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == "SPECIALIST_ENGINE_EXCEPTION"
    assert "adapter routed" not in result.output


def test_deterministic_engine_receipt_cannot_report_side_effects() -> None:
    environment = build_active_environment(run_id="specialist-side-effect-run")
    engine = RecordingEngine(
        lambda receipt: replace(
            receipt,
            side_effect_class=SpecialistSideEffectClass.FILE_MUTATION,
            changed_paths=("README.md",),
        )
    )
    result = _specialist_executor(environment, engine).execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == "DETERMINISTIC_ENGINE_SIDE_EFFECT_REJECTED"
