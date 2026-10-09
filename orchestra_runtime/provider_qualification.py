from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Any, Mapping


VSCODE_PROVIDER_OBSERVATION_VERSION = "orchestra.vscode-provider-observation.v1"
PROVIDER_QUALIFICATION_RECEIPT_VERSION = "orchestra.provider-qualification-receipt.v1"
VSCODE_PROVIDER_QUALIFICATION_FIXTURE_ID = "vscode-provider-qualification-fixture-v1"
VSCODE_PROVIDER_QUALIFICATION_FIXTURE_SHA256 = "010ab2a84c45bf6aa30e056fdaf5bb1d7fd61e224499fb2055744746a391b569"
_PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_TEXT_RE = re.compile(r"^[^\r\n\x00]+$")


class VSCodeHarness(str, Enum):
    LOCAL = "local"
    COPILOT = "copilot"
    CLAUDE = "claude"
    CODEX = "codex"


class VSCodeExecutionEnvironment(str, Enum):
    CURRENT_WORKSPACE = "CURRENT_WORKSPACE"
    ISOLATED_WORKTREE = "ISOLATED_WORKTREE"
    REMOTE = "REMOTE"
    CLOUD = "CLOUD"


class VSCodeObservationResult(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


class ProviderQualificationClassification(str, Enum):
    STATIC_CONFIGURATION_ONLY = "STATIC_CONFIGURATION_ONLY"
    LIVE_HOST_ROUTED_MODEL_OBSERVED = "LIVE_HOST_ROUTED_MODEL_OBSERVED"
    LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED = "LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED"
    LIVE_MODEL_PATH_FAILED = "LIVE_MODEL_PATH_FAILED"


class ProviderQualificationContractError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _safe_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text or _SAFE_TEXT_RE.fullmatch(text) is None:
        raise ProviderQualificationContractError(
            f"{field} must be a non-empty safe string",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    return text


def _provider_id(value: object, field: str) -> str:
    text = str(value or "").strip().casefold()
    if not text or _PROVIDER_ID_RE.fullmatch(text) is None:
        raise ProviderQualificationContractError(
            f"{field} must be a canonical provider identifier",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    return text


def _git_sha(value: object, field: str) -> str:
    text = str(value or "").strip().casefold()
    if _GIT_SHA_RE.fullmatch(text) is None:
        raise ProviderQualificationContractError(
            f"{field} must be an exact lowercase 40-character Git SHA",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    return text


def _sha256(value: object, field: str) -> str:
    text = str(value or "").strip().casefold()
    if _SHA256_RE.fullmatch(text) is None:
        raise ProviderQualificationContractError(
            f"{field} must be a SHA-256 digest",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    return text


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ProviderQualificationContractError(
            f"{field} must be an array",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    items = tuple(_safe_text(item, field) for item in value)
    if len(set(items)) != len(items):
        raise ProviderQualificationContractError(
            f"{field} must not contain duplicates",
            "INVALID_VSCODE_PROVIDER_OBSERVATION",
        )
    return items


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class VSCodeProviderObservation:
    schema_version: str
    host_id: str
    harness_id: VSCodeHarness
    provider_source_id: str
    provider_id: str
    model_id: str
    execution_environment: VSCodeExecutionEnvironment
    repository_sha: str
    fixture_id: str
    fixture_sha256: str
    live_model_execution: bool
    session_target_observed: bool
    model_identity_observed: bool
    provider_source_observed: bool
    fixture_result_observed: bool
    worktree_clean_before: bool
    worktree_clean_after: bool
    result: VSCodeObservationResult
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != VSCODE_PROVIDER_OBSERVATION_VERSION:
            raise ProviderQualificationContractError(
                "unsupported VS Code provider observation version",
                "UNSUPPORTED_VSCODE_PROVIDER_OBSERVATION_VERSION",
            )
        if self.host_id != "vscode":
            raise ProviderQualificationContractError(
                "host_id must equal vscode",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            )
        try:
            harness = VSCodeHarness(self.harness_id)
            environment = VSCodeExecutionEnvironment(self.execution_environment)
            result = VSCodeObservationResult(self.result)
        except ValueError as exc:
            raise ProviderQualificationContractError(
                "unsupported VS Code harness, environment, or observation result",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            ) from exc
        object.__setattr__(self, "harness_id", harness)
        object.__setattr__(self, "execution_environment", environment)
        object.__setattr__(self, "result", result)
        object.__setattr__(self, "provider_source_id", _provider_id(self.provider_source_id, "provider_source_id"))
        object.__setattr__(self, "provider_id", _provider_id(self.provider_id, "provider_id"))
        object.__setattr__(self, "model_id", _safe_text(self.model_id, "model_id"))
        object.__setattr__(self, "repository_sha", _git_sha(self.repository_sha, "repository_sha"))
        object.__setattr__(self, "fixture_id", _safe_text(self.fixture_id, "fixture_id"))
        object.__setattr__(self, "fixture_sha256", _sha256(self.fixture_sha256, "fixture_sha256"))
        object.__setattr__(self, "evidence_refs", _string_tuple(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "limitations", _string_tuple(self.limitations, "limitations"))

        if (
            self.fixture_id != VSCODE_PROVIDER_QUALIFICATION_FIXTURE_ID
            or self.fixture_sha256 != VSCODE_PROVIDER_QUALIFICATION_FIXTURE_SHA256
        ):
            raise ProviderQualificationContractError(
                "observation must bind the canonical frozen VS Code qualification fixture",
                "VSCODE_QUALIFICATION_FIXTURE_MISMATCH",
            )

        source_provider_requirements = {"anthropic": "anthropic", "chatgpt": "openai"}
        required_provider = source_provider_requirements.get(self.provider_source_id)
        if required_provider is not None and self.provider_id != required_provider:
            raise ProviderQualificationContractError(
                "provider_source_id conflicts with provider_id",
                "VSCODE_PROVIDER_SOURCE_PROVIDER_MISMATCH",
            )

        booleans = (
            "live_model_execution",
            "session_target_observed",
            "model_identity_observed",
            "provider_source_observed",
            "fixture_result_observed",
            "worktree_clean_before",
            "worktree_clean_after",
        )
        if any(type(getattr(self, field)) is not bool for field in booleans):
            raise ProviderQualificationContractError(
                "observation flags must be booleans",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            )

        if not self.live_model_execution:
            if self.result is not VSCodeObservationResult.NOT_RUN:
                raise ProviderQualificationContractError(
                    "non-live observation must use NOT_RUN",
                    "INVALID_VSCODE_PROVIDER_OBSERVATION",
                )
            return

        if self.result is VSCodeObservationResult.NOT_RUN:
            raise ProviderQualificationContractError(
                "live observation must use PASS or FAIL",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            )
        if not self.evidence_refs:
            raise ProviderQualificationContractError(
                "live observation requires evidence_refs",
                "LIVE_PROVIDER_EVIDENCE_REQUIRED",
            )
        required_observations = (
            self.session_target_observed,
            self.model_identity_observed,
            self.provider_source_observed,
        )
        if not all(required_observations):
            raise ProviderQualificationContractError(
                "live observation requires explicit harness, model, and provider-source evidence",
                "LIVE_PROVIDER_IDENTITY_INCOMPLETE",
            )
        if self.result is VSCodeObservationResult.PASS:
            if not self.fixture_result_observed:
                raise ProviderQualificationContractError(
                    "passing live observation requires fixture result evidence",
                    "LIVE_PROVIDER_FIXTURE_RESULT_REQUIRED",
                )
            if not self.worktree_clean_before or not self.worktree_clean_after:
                raise ProviderQualificationContractError(
                    "passing live qualification requires clean repository state before and after",
                    "LIVE_PROVIDER_REPOSITORY_STATE_UNSAFE",
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "VSCodeProviderObservation":
        if not isinstance(payload, Mapping):
            raise ProviderQualificationContractError(
                "observation root must be an object",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            )
        allowed = {
            "schema_version",
            "host_id",
            "harness_id",
            "provider_source_id",
            "provider_id",
            "model_id",
            "execution_environment",
            "repository_sha",
            "fixture_id",
            "fixture_sha256",
            "live_model_execution",
            "session_target_observed",
            "model_identity_observed",
            "provider_source_observed",
            "fixture_result_observed",
            "worktree_clean_before",
            "worktree_clean_after",
            "result",
            "evidence_refs",
            "limitations",
        }
        if set(payload) != allowed:
            raise ProviderQualificationContractError(
                "observation fields must match the v1 contract exactly",
                "INVALID_VSCODE_PROVIDER_OBSERVATION",
            )
        return cls(**payload)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "host_id": self.host_id,
            "harness_id": self.harness_id.value,
            "provider_source_id": self.provider_source_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "execution_environment": self.execution_environment.value,
            "repository_sha": self.repository_sha,
            "fixture_id": self.fixture_id,
            "fixture_sha256": self.fixture_sha256,
            "live_model_execution": self.live_model_execution,
            "session_target_observed": self.session_target_observed,
            "model_identity_observed": self.model_identity_observed,
            "provider_source_observed": self.provider_source_observed,
            "fixture_result_observed": self.fixture_result_observed,
            "worktree_clean_before": self.worktree_clean_before,
            "worktree_clean_after": self.worktree_clean_after,
            "result": self.result.value,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }

    @property
    def observation_digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ProviderQualificationReceipt:
    schema_version: str
    classification: ProviderQualificationClassification
    host_id: str
    harness_id: str
    provider_source_id: str
    provider_id: str
    model_id: str
    repository_sha: str
    fixture_id: str
    fixture_sha256: str
    observation_digest: str
    live_model_path_observed: bool
    provider_native_harness_path_observed: bool
    automatic_routing_authorized: bool
    provider_execution_authority: bool
    release_authorized: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "classification": self.classification.value,
            "host_id": self.host_id,
            "harness_id": self.harness_id,
            "provider_source_id": self.provider_source_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "repository_sha": self.repository_sha,
            "fixture_id": self.fixture_id,
            "fixture_sha256": self.fixture_sha256,
            "observation_digest": self.observation_digest,
            "live_model_path_observed": self.live_model_path_observed,
            "provider_native_harness_path_observed": self.provider_native_harness_path_observed,
            "automatic_routing_authorized": self.automatic_routing_authorized,
            "provider_execution_authority": self.provider_execution_authority,
            "release_authorized": self.release_authorized,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }


_NATIVE_HARNESS_SOURCES = {
    (VSCodeHarness.CLAUDE, "anthropic", "anthropic"),
    (VSCodeHarness.CODEX, "chatgpt", "openai"),
}


def qualify_vscode_provider_observation(
    observation: VSCodeProviderObservation | Mapping[str, Any],
) -> ProviderQualificationReceipt:
    obs = (
        observation
        if isinstance(observation, VSCodeProviderObservation)
        else VSCodeProviderObservation.from_dict(observation)
    )

    native = False
    if not obs.live_model_execution:
        classification = ProviderQualificationClassification.STATIC_CONFIGURATION_ONLY
        live = False
    elif obs.result is VSCodeObservationResult.FAIL:
        classification = ProviderQualificationClassification.LIVE_MODEL_PATH_FAILED
        live = False
    else:
        live = True
        native = (
            obs.harness_id,
            obs.provider_source_id,
            obs.provider_id,
        ) in _NATIVE_HARNESS_SOURCES
        classification = (
            ProviderQualificationClassification.LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED
            if native
            else ProviderQualificationClassification.LIVE_HOST_ROUTED_MODEL_OBSERVED
        )

    return ProviderQualificationReceipt(
        schema_version=PROVIDER_QUALIFICATION_RECEIPT_VERSION,
        classification=classification,
        host_id=obs.host_id,
        harness_id=obs.harness_id.value,
        provider_source_id=obs.provider_source_id,
        provider_id=obs.provider_id,
        model_id=obs.model_id,
        repository_sha=obs.repository_sha,
        fixture_id=obs.fixture_id,
        fixture_sha256=obs.fixture_sha256,
        observation_digest=obs.observation_digest,
        live_model_path_observed=live,
        provider_native_harness_path_observed=native,
        automatic_routing_authorized=False,
        provider_execution_authority=False,
        release_authorized=False,
        evidence_refs=obs.evidence_refs,
        limitations=obs.limitations,
    )
