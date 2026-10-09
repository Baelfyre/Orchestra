from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import re

from .presentation import PresentationMode


COMMUNICATION_MEASUREMENT_SCHEMA_VERSION = "orchestra.communication-measurement.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TokenMeasurementSource(str, Enum):
    HOST_REPORTED = "HOST_REPORTED"
    UNAVAILABLE = "UNAVAILABLE"


def _text(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _optional_count(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _count(value, field_name)


def _digest(value: object, field_name: str) -> str:
    digest = _text(value, field_name).lower()
    if not _SHA256.fullmatch(digest):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return digest


@dataclass(frozen=True, slots=True)
class CommunicationMeasurement:
    scenario_id: str
    mode: PresentationMode
    implementation_revision: str
    progress_messages: int
    model_progress_calls: int
    user_visible_bytes: int
    context_bytes_admitted: int
    tool_result_bytes_admitted: int
    repeated_reads: int
    task_outcome: str
    validation_digest: str
    governance_digest: str
    token_source: TokenMeasurementSource = TokenMeasurementSource.UNAVAILABLE
    token_counter_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    elapsed_communication_ms: int | None = None

    def __post_init__(self) -> None:
        scenario_id = _text(self.scenario_id, "scenario_id")
        mode = PresentationMode(self.mode)
        implementation_revision = _text(self.implementation_revision, "implementation_revision")
        task_outcome = _text(self.task_outcome, "task_outcome")
        validation_digest = _digest(self.validation_digest, "validation_digest")
        governance_digest = _digest(self.governance_digest, "governance_digest")
        token_source = TokenMeasurementSource(self.token_source)

        for field_name in (
            "progress_messages",
            "model_progress_calls",
            "user_visible_bytes",
            "context_bytes_admitted",
            "tool_result_bytes_admitted",
            "repeated_reads",
        ):
            object.__setattr__(self, field_name, _count(getattr(self, field_name), field_name))

        elapsed = _optional_count(self.elapsed_communication_ms, "elapsed_communication_ms")
        input_tokens = _optional_count(self.input_tokens, "input_tokens")
        output_tokens = _optional_count(self.output_tokens, "output_tokens")
        counter_id = None if self.token_counter_id is None else _text(self.token_counter_id, "token_counter_id")

        if token_source is TokenMeasurementSource.HOST_REPORTED:
            if counter_id is None or input_tokens is None or output_tokens is None:
                raise ValueError("HOST_REPORTED token measurements require counter identity and both token counts")
        elif counter_id is not None or input_tokens is not None or output_tokens is not None:
            raise ValueError("UNAVAILABLE token measurements cannot carry token counts or counter identity")

        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "implementation_revision", implementation_revision)
        object.__setattr__(self, "task_outcome", task_outcome)
        object.__setattr__(self, "validation_digest", validation_digest)
        object.__setattr__(self, "governance_digest", governance_digest)
        object.__setattr__(self, "token_source", token_source)
        object.__setattr__(self, "token_counter_id", counter_id)
        object.__setattr__(self, "input_tokens", input_tokens)
        object.__setattr__(self, "output_tokens", output_tokens)
        object.__setattr__(self, "elapsed_communication_ms", elapsed)

    @property
    def outcome_fingerprint(self) -> tuple[str, str, str]:
        return (self.task_outcome, self.validation_digest, self.governance_digest)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": COMMUNICATION_MEASUREMENT_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "mode": self.mode.value,
            "implementation_revision": self.implementation_revision,
            "progress_messages": self.progress_messages,
            "model_progress_calls": self.model_progress_calls,
            "user_visible_bytes": self.user_visible_bytes,
            "context_bytes_admitted": self.context_bytes_admitted,
            "tool_result_bytes_admitted": self.tool_result_bytes_admitted,
            "repeated_reads": self.repeated_reads,
            "task_outcome": self.task_outcome,
            "validation_digest": self.validation_digest,
            "governance_digest": self.governance_digest,
            "token_source": self.token_source.value,
            "token_counter_id": self.token_counter_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "elapsed_communication_ms": self.elapsed_communication_ms,
        }


@dataclass(frozen=True, slots=True)
class CommunicationComparison:
    scenario_id: str
    outcome_parity: bool
    progress_message_delta: int
    model_progress_call_delta: int
    user_visible_byte_delta: int
    context_byte_delta: int
    tool_result_byte_delta: int
    repeated_read_delta: int
    elapsed_communication_ms_delta: int | None
    input_token_delta: int | None
    output_token_delta: int | None
    token_comparison_available: bool
    token_counter_id: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "outcome_parity": self.outcome_parity,
            "progress_message_delta": self.progress_message_delta,
            "model_progress_call_delta": self.model_progress_call_delta,
            "user_visible_byte_delta": self.user_visible_byte_delta,
            "context_byte_delta": self.context_byte_delta,
            "tool_result_byte_delta": self.tool_result_byte_delta,
            "repeated_read_delta": self.repeated_read_delta,
            "elapsed_communication_ms_delta": self.elapsed_communication_ms_delta,
            "input_token_delta": self.input_token_delta,
            "output_token_delta": self.output_token_delta,
            "token_comparison_available": self.token_comparison_available,
            "token_counter_id": self.token_counter_id,
        }


def compare_communication_measurements(
    baseline: CommunicationMeasurement,
    candidate: CommunicationMeasurement,
) -> CommunicationComparison:
    if baseline.scenario_id != candidate.scenario_id:
        raise ValueError("communication measurements must refer to the same scenario_id")

    token_comparable = (
        baseline.token_source is TokenMeasurementSource.HOST_REPORTED
        and candidate.token_source is TokenMeasurementSource.HOST_REPORTED
        and baseline.token_counter_id == candidate.token_counter_id
    )

    elapsed_delta = None
    if baseline.elapsed_communication_ms is not None and candidate.elapsed_communication_ms is not None:
        elapsed_delta = candidate.elapsed_communication_ms - baseline.elapsed_communication_ms

    input_delta = None
    output_delta = None
    counter_id = None
    if token_comparable:
        input_delta = candidate.input_tokens - baseline.input_tokens
        output_delta = candidate.output_tokens - baseline.output_tokens
        counter_id = baseline.token_counter_id

    return CommunicationComparison(
        scenario_id=baseline.scenario_id,
        outcome_parity=baseline.outcome_fingerprint == candidate.outcome_fingerprint,
        progress_message_delta=candidate.progress_messages - baseline.progress_messages,
        model_progress_call_delta=candidate.model_progress_calls - baseline.model_progress_calls,
        user_visible_byte_delta=candidate.user_visible_bytes - baseline.user_visible_bytes,
        context_byte_delta=candidate.context_bytes_admitted - baseline.context_bytes_admitted,
        tool_result_byte_delta=candidate.tool_result_bytes_admitted - baseline.tool_result_bytes_admitted,
        repeated_read_delta=candidate.repeated_reads - baseline.repeated_reads,
        elapsed_communication_ms_delta=elapsed_delta,
        input_token_delta=input_delta,
        output_token_delta=output_delta,
        token_comparison_available=token_comparable,
        token_counter_id=counter_id,
    )


def communication_measurement_digest(measurement: CommunicationMeasurement) -> str:
    payload = json.dumps(measurement.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()
