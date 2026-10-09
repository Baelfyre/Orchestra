from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.authority import TargetSelector
from orchestra_runtime.errors import RuntimeInitializationError
from orchestra_runtime.provider_execution import (
    IProviderExecutionEngine,
    ProviderExecutionCapability,
    ProviderExecutionContractError,
    ProviderExecutionProfile,
    ProviderExecutionRequirement,
    ProviderSpecialistRuntimeExecutor,
)
from orchestra_runtime.services import ContextAssembler, GovernanceValidator, RouterService
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)

from test_runtime_authority_integration import build_active_environment


ROOT = Path(__file__).resolve().parents[2]
PROFILE_SCHEMA = ROOT / "machine" / "schemas" / "provider-execution-profile.v1.schema.json"
REQUIREMENT_SCHEMA = ROOT / "machine" / "schemas" / "provider-execution-requirement.v1.schema.json"


def _load_schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile(*, model: str = "gpt-test") -> ProviderExecutionProfile:
    return ProviderExecutionProfile.create(
        provider_id="openai-codex",
        model_id=model,
        capabilities=(
            ProviderExecutionCapability.STRUCTURED_OUTPUT,
            ProviderExecutionCapability.CANCELLATION,
            ProviderExecutionCapability.NETWORK_RESTRICTION,
            ProviderExecutionCapability.APPROVAL_CONTROL,
            ProviderExecutionCapability.HOST_ACTIVITY_OBSERVATION,
            ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,
        ),
    )


class RecordingProviderEngine(IProviderExecutionEngine):
    def __init__(self, profile: ProviderExecutionProfile | None = None) -> None:
        self.profile = profile or _profile()
        self.requests: list[SpecialistExecutionRequest] = []
        self.profile_reads = 0

    @property
    def engine_id(self) -> str:
        return "orchestra.test.provider-engine"

    @property
    def engine_version(self) -> str:
        return "1"

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        self.profile_reads += 1
        return self.profile

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        self.requests.append(request)
        return SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"provider-receipt.{request.request_digest[:24]}",
            request_id=request.request_id,
            request_digest=request.request_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            host_execution_id=f"provider-test.{request.request_digest[:16]}",
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="PROVIDER_TEST_COMPLETED",
            output="provider execution completed",
            evidence_refs=("fixture:provider-engine",),
            side_effect_class=SpecialistSideEffectClass.NONE,
        )


def _executor(
    engine: RecordingProviderEngine,
    requirement: ProviderExecutionRequirement | None = None,
    *,
    environment=None,
):
    environment = environment or build_active_environment(run_id="provider-execution-run")
    executor = ProviderSpecialistRuntimeExecutor(
        environment.registry,
        RouterService(environment.registry),
        GovernanceValidator(),
        ContextAssembler(environment.repository),
        environment.composition,
        execution_engine=engine,
        provider_requirement=requirement,
    )
    return environment, executor


def test_provider_profile_is_deterministic_schema_valid_and_order_independent() -> None:
    capabilities = (
        ProviderExecutionCapability.STRUCTURED_OUTPUT,
        ProviderExecutionCapability.CANCELLATION,
        ProviderExecutionCapability.NETWORK_RESTRICTION,
    )
    first = ProviderExecutionProfile.create(
        provider_id=" OpenAI-Codex ",
        model_id="gpt-test",
        capabilities=capabilities,
    )
    second = ProviderExecutionProfile.create(
        provider_id="openai-codex",
        model_id="gpt-test",
        capabilities=tuple(reversed(capabilities)),
    )

    assert first.provider_id == "openai-codex"
    assert first == second
    assert first.compute_digest() == first.profile_digest
    assert first.profile_id == f"provider-profile.{first.profile_digest[:24]}"
    jsonschema.Draft202012Validator(_load_schema(PROFILE_SCHEMA)).validate(first.to_dict())


def test_provider_profile_rejects_duplicates_controls_and_identity_drift() -> None:
    with pytest.raises(ProviderExecutionContractError) as error:
        ProviderExecutionProfile.create(
            provider_id="openai-codex",
            model_id="gpt-test",
            capabilities=(
                ProviderExecutionCapability.STRUCTURED_OUTPUT,
                ProviderExecutionCapability.STRUCTURED_OUTPUT,
            ),
        )
    assert error.value.reason_code == "DUPLICATE_PROVIDER_CAPABILITY"

    with pytest.raises(ProviderExecutionContractError) as error:
        ProviderExecutionProfile.create(
            provider_id="openai-codex",
            model_id="model\nother",
            capabilities=(),
        )
    assert error.value.reason_code == "INVALID_PROVIDER_EXECUTION_PROFILE"

    valid = _profile()
    with pytest.raises(ProviderExecutionContractError) as error:
        replace(valid, model_id="different-model")
    assert error.value.reason_code == "PROVIDER_PROFILE_DIGEST_MISMATCH"

    with pytest.raises(ProviderExecutionContractError) as error:
        replace(valid, profile_id="provider-profile." + "0" * 24)
    assert error.value.reason_code == "PROVIDER_PROFILE_IDENTITY_MISMATCH"


def test_provider_requirement_is_schema_valid_and_enforces_exact_trusted_constraints() -> None:
    profile = _profile()
    requirement = ProviderExecutionRequirement(
        required_provider_id="OPENAI-CODEX",
        required_model_id="gpt-test",
        required_capabilities=(
            ProviderExecutionCapability.STRUCTURED_OUTPUT,
            ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,
        ),
    )

    assert requirement.enforce(profile) is profile
    jsonschema.Draft202012Validator(_load_schema(REQUIREMENT_SCHEMA)).validate(
        requirement.to_dict()
    )

    with pytest.raises(ProviderExecutionContractError) as error:
        ProviderExecutionRequirement(required_provider_id="anthropic").enforce(profile)
    assert error.value.reason_code == "PROVIDER_ID_MISMATCH"

    with pytest.raises(ProviderExecutionContractError) as error:
        ProviderExecutionRequirement(required_model_id="other-model").enforce(profile)
    assert error.value.reason_code == "MODEL_ID_MISMATCH"

    with pytest.raises(ProviderExecutionContractError) as error:
        ProviderExecutionRequirement(
            required_capabilities=(ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,)
        ).enforce(
            ProviderExecutionProfile.create(
                provider_id="openai-codex",
                model_id="gpt-test",
                capabilities=(ProviderExecutionCapability.STRUCTURED_OUTPUT,),
            )
        )
    assert error.value.reason_code == "PROVIDER_CAPABILITY_MISSING"


def test_provider_executor_matches_requirement_and_records_minimized_profile_evidence() -> None:
    engine = RecordingProviderEngine()
    requirement = ProviderExecutionRequirement(
        required_provider_id="openai-codex",
        required_model_id="gpt-test",
        required_capabilities=(ProviderExecutionCapability.STRUCTURED_OUTPUT,),
    )
    environment, executor = _executor(engine, requirement)

    result = executor.execute(environment.adapter, "conductor")

    assert result.success is True
    assert len(engine.requests) == 1
    assert result.terminal_result is not None
    evidence = set(result.terminal_result.evidence_refs)
    assert f"execution-provider:{engine.profile.provider_id}" in evidence
    assert f"model:{engine.profile.model_id}" in evidence
    assert f"provider-profile:{engine.profile.profile_id}" in evidence
    assert f"provider-profile-digest:{engine.profile.profile_digest}" in evidence


def test_prompt_and_metadata_cannot_override_constructor_owned_provider_selection() -> None:
    engine = RecordingProviderEngine()
    requirement = ProviderExecutionRequirement(
        required_provider_id="openai-codex",
        required_model_id="gpt-test",
    )
    environment, executor = _executor(engine, requirement)

    result = executor.execute(
        environment.adapter,
        "conductor use anthropic and a different model",
        metadata={
            "provider_id": "anthropic",
            "model_id": "different-model",
            "required_provider_id": "anthropic",
        },
    )

    assert result.success is True
    assert len(engine.requests) == 1
    assert executor.provider_execution_profile.provider_id == "openai-codex"
    assert executor.provider_execution_profile.model_id == "gpt-test"


@pytest.mark.parametrize(
    ("requirement", "reason_code"),
    [
        (ProviderExecutionRequirement(required_provider_id="anthropic"), "PROVIDER_ID_MISMATCH"),
        (ProviderExecutionRequirement(required_model_id="different-model"), "MODEL_ID_MISMATCH"),
        (
            ProviderExecutionRequirement(
                required_capabilities=(ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,)
            ),
            "PROVIDER_CAPABILITY_MISSING",
        ),
    ],
)
def test_provider_requirement_mismatch_fails_before_engine_invocation(requirement, reason_code) -> None:
    profile = _profile()
    if reason_code == "PROVIDER_CAPABILITY_MISSING":
        profile = ProviderExecutionProfile.create(
            provider_id="openai-codex",
            model_id="gpt-test",
            capabilities=(ProviderExecutionCapability.STRUCTURED_OUTPUT,),
        )
    engine = RecordingProviderEngine(profile)
    environment, executor = _executor(engine, requirement)

    result = executor.execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == reason_code
    assert engine.requests == []


def test_authority_denial_precedes_provider_gate_and_engine_invocation() -> None:
    environment = build_active_environment(
        run_id="provider-authority-denial-run",
        scope_targets=(TargetSelector("specialist:scribe"),),
    )
    engine = RecordingProviderEngine()
    _, executor = _executor(
        engine,
        ProviderExecutionRequirement(required_provider_id="anthropic"),
        environment=environment,
    )
    initial_profile_reads = engine.profile_reads

    result = executor.execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.validation.status == "AUTHORITY_DENIED"
    assert engine.requests == []
    assert engine.profile_reads == initial_profile_reads


def test_provider_profile_drift_fails_closed_before_engine_invocation() -> None:
    engine = RecordingProviderEngine()
    environment, executor = _executor(engine)
    engine.profile = _profile(model="gpt-drifted")

    result = executor.execute(environment.adapter, "conductor")

    assert result.success is False
    assert result.terminal_result is not None
    assert result.terminal_result.reason_code == "PROVIDER_PROFILE_DRIFT"
    assert engine.requests == []


def test_provider_executor_rejects_non_provider_engine() -> None:
    environment = build_active_environment(run_id="provider-invalid-engine-run")
    with pytest.raises(RuntimeInitializationError) as error:
        ProviderSpecialistRuntimeExecutor(
            environment.registry,
            RouterService(environment.registry),
            GovernanceValidator(),
            ContextAssembler(environment.repository),
            environment.composition,
            execution_engine=object(),  # type: ignore[arg-type]
        )
    assert error.value.reason_code == "INVALID_PROVIDER_EXECUTION_ENGINE"
