from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re

from .errors import RuntimeContractError, RuntimeInitializationError
from .interfaces import ISpecialistExecutionEngine
from .lifecycle import LifecycleState
from .services import ContextAssembler, RuntimeComposition, RuntimeOperationResult
from .specialist_execution import (
    SpecialistExecutionMode,
    SpecialistRuntimeExecutor,
)


PROVIDER_EXECUTION_PROFILE_VERSION = "orchestra.provider-execution-profile.v1"
PROVIDER_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProviderExecutionCapability(str, Enum):
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    CANCELLATION = "CANCELLATION"
    READ_ONLY_SANDBOX_CONTROL = "READ_ONLY_SANDBOX_CONTROL"
    NETWORK_RESTRICTION = "NETWORK_RESTRICTION"
    APPROVAL_CONTROL = "APPROVAL_CONTROL"
    HOST_ACTIVITY_OBSERVATION = "HOST_ACTIVITY_OBSERVATION"


class ProviderExecutionContractError(RuntimeContractError):
    pass


def _provider_id(value: object, field_name: str) -> str:
    text = str(value or "").strip().casefold()
    if not text or not PROVIDER_IDENTIFIER_PATTERN.fullmatch(text):
        raise ProviderExecutionContractError(
            f"{field_name} must be a canonical provider identifier",
            "INVALID_PROVIDER_EXECUTION_PROFILE",
            {"field": field_name},
        )
    return text


def _model_id(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text or any(character in text for character in ("\r", "\n", "\x00")):
        raise ProviderExecutionContractError(
            f"{field_name} must be a non-empty safe model identifier",
            "INVALID_PROVIDER_EXECUTION_PROFILE",
            {"field": field_name},
        )
    return text


def _capabilities(values: tuple[ProviderExecutionCapability | str, ...]) -> tuple[ProviderExecutionCapability, ...]:
    try:
        normalized = tuple(ProviderExecutionCapability(item) for item in values)
    except (TypeError, ValueError) as exc:
        raise ProviderExecutionContractError(
            "provider execution capability is unsupported",
            "UNSUPPORTED_PROVIDER_CAPABILITY",
        ) from exc
    if len(set(normalized)) != len(normalized):
        raise ProviderExecutionContractError(
            "provider execution capabilities must be unique",
            "DUPLICATE_PROVIDER_CAPABILITY",
        )
    return tuple(sorted(normalized, key=lambda item: item.value))


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderExecutionProfile:
    profile_version: str
    profile_id: str
    provider_id: str
    model_id: str
    capabilities: tuple[ProviderExecutionCapability, ...]
    profile_digest: str

    def __post_init__(self) -> None:
        if self.profile_version != PROVIDER_EXECUTION_PROFILE_VERSION:
            raise ProviderExecutionContractError(
                "unsupported provider execution profile version",
                "UNSUPPORTED_PROVIDER_EXECUTION_PROFILE_VERSION",
            )
        provider_id = _provider_id(self.provider_id, "provider_id")
        model_id = _model_id(self.model_id, "model_id")
        capabilities = _capabilities(tuple(self.capabilities))
        profile_digest = str(self.profile_digest or "").strip().casefold()
        if not SHA256_PATTERN.fullmatch(profile_digest):
            raise ProviderExecutionContractError(
                "profile_digest must be a SHA-256 digest",
                "INVALID_PROVIDER_PROFILE_DIGEST",
            )
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "profile_digest", profile_digest)
        if self.profile_digest != self.compute_digest():
            raise ProviderExecutionContractError(
                "provider execution profile digest does not match its payload",
                "PROVIDER_PROFILE_DIGEST_MISMATCH",
            )
        expected_id = f"provider-profile.{self.profile_digest[:24]}"
        if self.profile_id != expected_id:
            raise ProviderExecutionContractError(
                "provider execution profile identifier does not match its digest",
                "PROVIDER_PROFILE_IDENTITY_MISMATCH",
            )

    @classmethod
    def create(
        cls,
        *,
        provider_id: str,
        model_id: str,
        capabilities: tuple[ProviderExecutionCapability | str, ...],
    ) -> ProviderExecutionProfile:
        normalized_provider = _provider_id(provider_id, "provider_id")
        normalized_model = _model_id(model_id, "model_id")
        normalized_capabilities = _capabilities(capabilities)
        payload = {
            "profile_version": PROVIDER_EXECUTION_PROFILE_VERSION,
            "provider_id": normalized_provider,
            "model_id": normalized_model,
            "capabilities": [item.value for item in normalized_capabilities],
        }
        profile_digest = _digest(payload)
        return cls(
            PROVIDER_EXECUTION_PROFILE_VERSION,
            f"provider-profile.{profile_digest[:24]}",
            normalized_provider,
            normalized_model,
            normalized_capabilities,
            profile_digest,
        )

    def digest_payload(self) -> dict[str, object]:
        return {
            "profile_version": self.profile_version,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "capabilities": [item.value for item in self.capabilities],
        }

    def compute_digest(self) -> str:
        return _digest(self.digest_payload())

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_version": self.profile_version,
            "profile_id": self.profile_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "capabilities": [item.value for item in self.capabilities],
            "profile_digest": self.profile_digest,
        }

    @property
    def evidence_refs(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                (
                    f"execution-provider:{self.provider_id}",
                    f"model:{self.model_id}",
                    f"provider-profile:{self.profile_id}",
                    f"provider-profile-digest:{self.profile_digest}",
                )
            )
        )


@dataclass(frozen=True, slots=True)
class ProviderExecutionRequirement:
    required_provider_id: str | None = None
    required_model_id: str | None = None
    required_capabilities: tuple[ProviderExecutionCapability, ...] = ()

    def __post_init__(self) -> None:
        provider_id = (
            _provider_id(self.required_provider_id, "required_provider_id")
            if self.required_provider_id is not None
            else None
        )
        model_id = (
            _model_id(self.required_model_id, "required_model_id")
            if self.required_model_id is not None
            else None
        )
        capabilities = _capabilities(tuple(self.required_capabilities))
        object.__setattr__(self, "required_provider_id", provider_id)
        object.__setattr__(self, "required_model_id", model_id)
        object.__setattr__(self, "required_capabilities", capabilities)

    @property
    def empty(self) -> bool:
        return (
            self.required_provider_id is None
            and self.required_model_id is None
            and not self.required_capabilities
        )

    def enforce(self, profile: ProviderExecutionProfile) -> ProviderExecutionProfile:
        if not isinstance(profile, ProviderExecutionProfile):
            raise ProviderExecutionContractError(
                "provider requirement requires a valid provider execution profile",
                "INVALID_PROVIDER_EXECUTION_PROFILE",
            )
        if self.required_provider_id is not None and profile.provider_id != self.required_provider_id:
            raise ProviderExecutionContractError(
                "configured execution provider does not satisfy the trusted requirement",
                "PROVIDER_ID_MISMATCH",
                {
                    "required_provider_id": self.required_provider_id,
                    "configured_provider_id": profile.provider_id,
                },
            )
        if self.required_model_id is not None and profile.model_id != self.required_model_id:
            raise ProviderExecutionContractError(
                "configured model does not satisfy the trusted requirement",
                "MODEL_ID_MISMATCH",
                {
                    "required_model_id": self.required_model_id,
                    "configured_model_id": profile.model_id,
                },
            )
        missing = tuple(
            item.value for item in self.required_capabilities if item not in profile.capabilities
        )
        if missing:
            raise ProviderExecutionContractError(
                "configured provider is missing a required execution capability",
                "PROVIDER_CAPABILITY_MISSING",
                {"missing_capabilities": ",".join(missing)},
            )
        return profile

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "required_capabilities": [item.value for item in self.required_capabilities],
        }
        if self.required_provider_id is not None:
            data["required_provider_id"] = self.required_provider_id
        if self.required_model_id is not None:
            data["required_model_id"] = self.required_model_id
        return data


class IProviderExecutionEngine(ISpecialistExecutionEngine, ABC):
    """Provider-aware host engine whose profile is descriptive and non-authorizing."""

    @property
    @abstractmethod
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        raise NotImplementedError


class ProviderSpecialistRuntimeExecutor(SpecialistRuntimeExecutor):
    """Explicit host-native specialist executor with a trusted provider requirement gate.

    Provider capability describes what the configured host engine can represent. It
    never creates or widens Orchestra authority, runtime capability grants, governance
    disposition, specialist scope, sandbox permission, or protected-action authority.
    """

    def __init__(
        self,
        skill_registry,
        router,
        governance,
        context_assembler: ContextAssembler,
        composition: RuntimeComposition,
        *,
        execution_engine: IProviderExecutionEngine,
        provider_requirement: ProviderExecutionRequirement | None = None,
    ) -> None:
        if not isinstance(execution_engine, IProviderExecutionEngine):
            raise RuntimeInitializationError(
                "provider specialist execution requires IProviderExecutionEngine",
                "INVALID_PROVIDER_EXECUTION_ENGINE",
            )
        profile = execution_engine.provider_execution_profile
        if not isinstance(profile, ProviderExecutionProfile):
            raise RuntimeInitializationError(
                "provider execution engine returned an invalid provider profile",
                "INVALID_PROVIDER_EXECUTION_PROFILE",
            )
        if provider_requirement is not None and not isinstance(
            provider_requirement, ProviderExecutionRequirement
        ):
            raise RuntimeInitializationError(
                "provider requirement must be ProviderExecutionRequirement",
                "INVALID_PROVIDER_EXECUTION_REQUIREMENT",
            )
        self._provider_execution_profile = profile
        self._provider_requirement = provider_requirement or ProviderExecutionRequirement()
        super().__init__(
            skill_registry,
            router,
            governance,
            context_assembler,
            composition,
            execution_engine=execution_engine,
            execution_mode=SpecialistExecutionMode.HOST_NATIVE,
        )

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        return self._provider_execution_profile

    @property
    def provider_requirement(self) -> ProviderExecutionRequirement:
        return self._provider_requirement

    def _execute_specialist(self, adapter_name, decision, validation) -> RuntimeOperationResult:
        engine = self.execution_engine
        try:
            if not isinstance(engine, IProviderExecutionEngine):
                raise ProviderExecutionContractError(
                    "provider execution engine is unavailable at the operation boundary",
                    "INVALID_PROVIDER_EXECUTION_ENGINE",
                )
            current_profile = engine.provider_execution_profile
            if not isinstance(current_profile, ProviderExecutionProfile):
                raise ProviderExecutionContractError(
                    "provider execution engine returned an invalid profile",
                    "INVALID_PROVIDER_EXECUTION_PROFILE",
                )
            if current_profile != self._provider_execution_profile:
                raise ProviderExecutionContractError(
                    "provider execution profile changed after runtime initialization",
                    "PROVIDER_PROFILE_DRIFT",
                    {
                        "expected_profile_id": self._provider_execution_profile.profile_id,
                        "current_profile_id": current_profile.profile_id,
                    },
                )
            self._provider_requirement.enforce(current_profile)
        except ProviderExecutionContractError as exc:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "provider execution requirement failed closed",
                exc.reason_code,
                self._provider_execution_profile.evidence_refs,
            )

        result = super()._execute_specialist(adapter_name, decision, validation)
        return RuntimeOperationResult(
            result.state,
            result.output,
            result.reason_code,
            (*result.evidence_refs, *current_profile.evidence_refs),
        )
