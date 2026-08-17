from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..evidence import canonical_json_bytes, normalize_sha256, normalize_timestamp, receipt_digest
from .models import (
    AdaptiveObservation,
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
    safe_json_object,
    validate_subject_key,
)
from .store import AdaptiveStoreLayout

SHADOW_SIGNAL_SCHEMA_VERSION = "orchestra.adaptive-shadow-signal.v1"
SHADOW_CANDIDATE_SCHEMA_VERSION = "orchestra.adaptive-shadow-candidate.v1"
SHADOW_COMPARISON_SCHEMA_VERSION = "orchestra.adaptive-shadow-comparison.v1"
SHADOW_CANDIDATE_STATE_SCHEMA_VERSION = "orchestra.adaptive-shadow-candidate-state.v1"
SHADOW_RULE_VERSION = "orchestra.adaptive-shadow-rules.v1"

SIGNAL_TYPES = frozenset(
    {
        "USER_SELECTION",
        "USER_REJECTION",
        "USER_CORRECTION",
        "SPECIALIST_STRATEGY_ACCEPTED",
        "SPECIALIST_STRATEGY_REJECTED",
        "VALIDATION_OUTCOME",
        "REMEDIATION_REQUIRED",
        "ITERATION_OUTCOME",
        "TERMINAL_DISPOSITION",
        "MEASURED_LATENCY",
        "MEASURED_COST",
    }
)
SOURCE_KINDS = frozenset(
    {
        "A1_VALIDATED_OBSERVATION",
        "GOVERNED_RETROSPECTIVE",
        "STRATEGY_DECISION_EVIDENCE",
        "VALIDATION_EVIDENCE",
        "REMEDIATION_EVIDENCE",
        "MEASURED_TELEMETRY",
    }
)
CANDIDATE_TYPES = frozenset(
    {"USER_PREFERENCE_TENDENCY", "WORKFLOW_TENDENCY", "SPECIALIST_STRATEGY_TENDENCY"}
)
CANDIDATE_STATUSES = frozenset(
    {"CANDIDATE", "BLOCKED_BY_EXPLICIT_PREFERENCE", "REJECTED", "DEPRECATED"}
)
COMPARISON_DISPOSITIONS = frozenset(
    {"MATCH", "MISMATCH", "NO_COMPARABLE_DETERMINISTIC_CHOICE", "CANDIDATE_BLOCKED"}
)
_POSITIVE_SIGNAL_TYPES = frozenset(
    {
        "USER_SELECTION",
        "USER_CORRECTION",
        "SPECIALIST_STRATEGY_ACCEPTED",
        "VALIDATION_OUTCOME",
        "REMEDIATION_REQUIRED",
        "ITERATION_OUTCOME",
        "TERMINAL_DISPOSITION",
        "MEASURED_LATENCY",
        "MEASURED_COST",
    }
)
_NEGATIVE_SIGNAL_TYPES = frozenset({"USER_REJECTION", "SPECIALIST_STRATEGY_REJECTED"})
_EXPLICIT_EVIDENCE_CLASSES = frozenset({"EXPLICIT_CURRENT_INSTRUCTION", "EXPLICIT_SCOPED_PREFERENCE"})


def _text(value: object, field_name: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    if len(text) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length {max_length}")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{field_name} must not contain control characters")
    return text


def _scalar(value: Any, field_name: str) -> str | int | float | bool:
    if isinstance(value, bool):
        normalized: str | int | float | bool = value
    elif isinstance(value, (int, float)):
        normalized = value
    elif isinstance(value, str):
        normalized = _text(value, field_name)
    else:
        raise TypeError(f"{field_name} must be a string, number, or boolean")
    safe_json_object({"value": normalized}, field_name)
    return normalized


def _measurement(value: Mapping[str, Any] | None, signal_type: str) -> dict[str, Any] | None:
    measured = signal_type in {"MEASURED_LATENCY", "MEASURED_COST"}
    if not measured:
        if value is not None:
            raise ValueError("measurement is allowed only for measured latency or cost signals")
        return None
    if not isinstance(value, Mapping):
        raise ValueError("measured latency or cost signals require trustworthy measurement")
    payload = dict(value)
    required = {"measurement_status", "metric", "numeric_value", "unit"}
    if set(payload) != required:
        raise ValueError("measurement must contain exactly measurement_status, metric, numeric_value, and unit")
    if payload["measurement_status"] != "TRUSTWORTHY_MEASURED":
        raise ValueError("measurement must be trustworthy and measured")
    expected_metric = "LATENCY" if signal_type == "MEASURED_LATENCY" else "COST"
    if payload["metric"] != expected_metric:
        raise ValueError(f"measurement metric must be {expected_metric}")
    numeric = payload["numeric_value"]
    if isinstance(numeric, bool) or not isinstance(numeric, (int, float)) or numeric < 0:
        raise ValueError("measurement numeric_value must be a non-negative number")
    payload["unit"] = _text(payload["unit"], "measurement.unit", max_length=64)
    return payload


@dataclass(frozen=True, slots=True)
class ShadowSignal:
    signal_id: str
    scope: AdaptiveScope
    signal_type: str
    subject_key: str
    observed_value: str | int | float | bool
    source_kind: str
    source_ref: str
    source_digest: str
    observed_at: str
    measurement: Mapping[str, Any] | None = None
    learner_rule_version: str = SHADOW_RULE_VERSION
    schema_version: str = SHADOW_SIGNAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_SIGNAL_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow signal schema '{self.schema_version}'")
        if self.learner_rule_version != SHADOW_RULE_VERSION:
            raise ValueError(f"unsupported shadow learner rule '{self.learner_rule_version}'")
        if not isinstance(self.scope, AdaptiveScope):
            raise TypeError("scope must be AdaptiveScope")
        signal_type = _text(self.signal_type, "signal_type", max_length=64).upper()
        source_kind = _text(self.source_kind, "source_kind", max_length=64).upper()
        if signal_type not in SIGNAL_TYPES:
            raise ValueError(f"unsupported shadow signal type '{signal_type}'")
        if source_kind not in SOURCE_KINDS:
            raise ValueError(f"unsupported shadow source kind '{source_kind}'")
        if signal_type in {"SPECIALIST_STRATEGY_ACCEPTED", "SPECIALIST_STRATEGY_REJECTED"}:
            if source_kind != "STRATEGY_DECISION_EVIDENCE":
                raise ValueError("specialist strategy signals require strategy decision evidence")
        if signal_type in {"MEASURED_LATENCY", "MEASURED_COST"} and source_kind != "MEASURED_TELEMETRY":
            raise ValueError("measured latency or cost requires measured telemetry")
        object.__setattr__(self, "signal_id", _text(self.signal_id, "signal_id", max_length=256))
        object.__setattr__(self, "signal_type", signal_type)
        object.__setattr__(self, "subject_key", validate_subject_key(self.subject_key))
        object.__setattr__(self, "observed_value", _scalar(self.observed_value, "observed_value"))
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "source_digest", normalize_sha256(self.source_digest, "source_digest"))
        object.__setattr__(self, "observed_at", normalize_timestamp(self.observed_at, "observed_at"))
        object.__setattr__(self, "measurement", _measurement(self.measurement, signal_type))

    @classmethod
    def build(
        cls,
        *,
        scope: AdaptiveScope,
        signal_type: str,
        subject_key: str,
        observed_value: Any,
        source_kind: str,
        source_ref: str,
        source_digest: str,
        observed_at: str,
        measurement: Mapping[str, Any] | None = None,
    ) -> "ShadowSignal":
        normalized_type = _text(signal_type, "signal_type", max_length=64).upper()
        identity = {
            "scope": scope.to_dict(),
            "signal_type": normalized_type,
            "subject_key": validate_subject_key(subject_key),
            "observed_value": _scalar(observed_value, "observed_value"),
            "source_kind": _text(source_kind, "source_kind", max_length=64).upper(),
            "source_ref": _text(source_ref, "source_ref"),
            "source_digest": normalize_sha256(source_digest, "source_digest"),
            "observed_at": normalize_timestamp(observed_at, "observed_at"),
            "measurement": None if measurement is None else dict(measurement),
        }
        return cls(signal_id=f"signal-{receipt_digest(identity)[:24]}", **identity)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ShadowSignal":
        if not isinstance(payload, Mapping):
            raise TypeError("shadow signal payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            learner_rule_version=payload.get("learner_rule_version", ""),
            signal_id=payload.get("signal_id", ""),
            scope=AdaptiveScope.from_dict(payload.get("scope", {})),
            signal_type=payload.get("signal_type", ""),
            subject_key=payload.get("subject_key", ""),
            observed_value=payload.get("observed_value"),
            source_kind=payload.get("source_kind", ""),
            source_ref=payload.get("source_ref", ""),
            source_digest=payload.get("source_digest", ""),
            observed_at=payload.get("observed_at", ""),
            measurement=payload.get("measurement"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "learner_rule_version": self.learner_rule_version,
            "signal_id": self.signal_id,
            "scope": self.scope.to_dict(),
            "signal_type": self.signal_type,
            "subject_key": self.subject_key,
            "observed_value": self.observed_value,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "observed_at": self.observed_at,
        }
        if self.measurement is not None:
            payload["measurement"] = dict(self.measurement)
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ShadowCandidate:
    candidate_id: str
    scope: AdaptiveScope
    subject_key: str
    candidate_type: str
    candidate_value: str | int | float | bool
    confidence: float
    distinct_support_count: int
    supporting_signal_refs: tuple[str, ...]
    supporting_signal_digests: tuple[str, ...]
    first_seen: str
    last_seen: str
    status: str = "CANDIDATE"
    explicit_conflict_ref: str | None = None
    notes: tuple[str, ...] = ()
    confidence_method: str = "BOUNDED_EVIDENCE_ACCUMULATION_V1"
    shadow_only: bool = True
    promotion_state: str = "NOT_PROMOTED"
    learner_rule_version: str = SHADOW_RULE_VERSION
    schema_version: str = SHADOW_CANDIDATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_CANDIDATE_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow candidate schema '{self.schema_version}'")
        if self.learner_rule_version != SHADOW_RULE_VERSION:
            raise ValueError(f"unsupported shadow learner rule '{self.learner_rule_version}'")
        if self.confidence_method != "BOUNDED_EVIDENCE_ACCUMULATION_V1":
            raise ValueError("unsupported confidence method")
        if self.shadow_only is not True or self.promotion_state != "NOT_PROMOTED":
            raise ValueError("shadow candidates cannot become execution or promotion authority")
        if not isinstance(self.scope, AdaptiveScope):
            raise TypeError("scope must be AdaptiveScope")
        candidate_type = _text(self.candidate_type, "candidate_type", max_length=64).upper()
        status = _text(self.status, "status", max_length=64).upper()
        if candidate_type not in CANDIDATE_TYPES:
            raise ValueError(f"unsupported candidate type '{candidate_type}'")
        if status not in CANDIDATE_STATUSES:
            raise ValueError(f"unsupported candidate status '{status}'")
        if isinstance(self.distinct_support_count, bool) or not isinstance(self.distinct_support_count, int):
            raise TypeError("distinct_support_count must be an integer")
        if self.distinct_support_count < 2:
            raise ValueError("durable shadow candidates require at least two distinct supporting signals")
        refs = tuple(sorted({_text(ref, "supporting_signal_ref", max_length=256) for ref in self.supporting_signal_refs}))
        digests = tuple(sorted({normalize_sha256(item, "supporting_signal_digest") for item in self.supporting_signal_digests}))
        if len(refs) != self.distinct_support_count or len(digests) != self.distinct_support_count:
            raise ValueError("distinct support count must equal unique signal refs and digests")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric")
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        conflict = None if self.explicit_conflict_ref is None else _text(
            self.explicit_conflict_ref, "explicit_conflict_ref"
        )
        if status == "BLOCKED_BY_EXPLICIT_PREFERENCE" and conflict is None:
            raise ValueError("blocked candidates require explicit_conflict_ref")
        object.__setattr__(self, "candidate_id", _text(self.candidate_id, "candidate_id", max_length=256))
        object.__setattr__(self, "candidate_type", candidate_type)
        object.__setattr__(self, "subject_key", validate_subject_key(self.subject_key))
        object.__setattr__(self, "candidate_value", _scalar(self.candidate_value, "candidate_value"))
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "supporting_signal_refs", refs)
        object.__setattr__(self, "supporting_signal_digests", digests)
        object.__setattr__(self, "first_seen", normalize_timestamp(self.first_seen, "first_seen"))
        object.__setattr__(self, "last_seen", normalize_timestamp(self.last_seen, "last_seen"))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "explicit_conflict_ref", conflict)
        object.__setattr__(
            self,
            "notes",
            tuple(_text(note, "candidate note") for note in self.notes),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ShadowCandidate":
        if not isinstance(payload, Mapping):
            raise TypeError("shadow candidate payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            learner_rule_version=payload.get("learner_rule_version", ""),
            candidate_id=payload.get("candidate_id", ""),
            scope=AdaptiveScope.from_dict(payload.get("scope", {})),
            subject_key=payload.get("subject_key", ""),
            candidate_type=payload.get("candidate_type", ""),
            candidate_value=payload.get("candidate_value"),
            confidence=payload.get("confidence", -1),
            confidence_method=payload.get("confidence_method", ""),
            distinct_support_count=payload.get("distinct_support_count", 0),
            supporting_signal_refs=tuple(payload.get("supporting_signal_refs", ())),
            supporting_signal_digests=tuple(payload.get("supporting_signal_digests", ())),
            first_seen=payload.get("first_seen", ""),
            last_seen=payload.get("last_seen", ""),
            status=payload.get("status", ""),
            shadow_only=payload.get("shadow_only", False),
            promotion_state=payload.get("promotion_state", ""),
            explicit_conflict_ref=payload.get("explicit_conflict_ref"),
            notes=tuple(payload.get("notes", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "learner_rule_version": self.learner_rule_version,
            "candidate_id": self.candidate_id,
            "scope": self.scope.to_dict(),
            "subject_key": self.subject_key,
            "candidate_type": self.candidate_type,
            "candidate_value": self.candidate_value,
            "confidence": self.confidence,
            "confidence_method": self.confidence_method,
            "distinct_support_count": self.distinct_support_count,
            "supporting_signal_refs": list(self.supporting_signal_refs),
            "supporting_signal_digests": list(self.supporting_signal_digests),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "status": self.status,
            "shadow_only": True,
            "promotion_state": "NOT_PROMOTED",
        }
        if self.explicit_conflict_ref is not None:
            payload["explicit_conflict_ref"] = self.explicit_conflict_ref
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ShadowComparison:
    comparison_id: str
    candidate_ref: str
    candidate_digest: str
    scope: AdaptiveScope
    subject_key: str
    evaluated_at: str
    shadow_recommendation: str | int | float | bool
    actual_deterministic_choice: str | int | float | bool
    actual_choice_ref: str
    disposition: str
    outcome_evidence_refs: tuple[str, ...] = ()
    outcome_evidence_digests: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    execution_controlled_by: str = "DETERMINISTIC_ORCHESTRA"
    shadow_influenced_execution: bool = False
    learner_rule_version: str = SHADOW_RULE_VERSION
    schema_version: str = SHADOW_COMPARISON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SHADOW_COMPARISON_SCHEMA_VERSION:
            raise ValueError(f"unsupported shadow comparison schema '{self.schema_version}'")
        if self.learner_rule_version != SHADOW_RULE_VERSION:
            raise ValueError(f"unsupported shadow learner rule '{self.learner_rule_version}'")
        if self.execution_controlled_by != "DETERMINISTIC_ORCHESTRA" or self.shadow_influenced_execution is not False:
            raise ValueError("shadow comparisons cannot control execution")
        if not isinstance(self.scope, AdaptiveScope):
            raise TypeError("scope must be AdaptiveScope")
        disposition = _text(self.disposition, "disposition", max_length=64).upper()
        if disposition not in COMPARISON_DISPOSITIONS:
            raise ValueError(f"unsupported comparison disposition '{disposition}'")
        refs = tuple(sorted({_text(ref, "outcome_evidence_ref") for ref in self.outcome_evidence_refs}))
        digests = tuple(sorted({normalize_sha256(item, "outcome_evidence_digest") for item in self.outcome_evidence_digests}))
        if len(refs) != len(digests):
            raise ValueError("outcome evidence refs and digests must have equal unique counts")
        object.__setattr__(self, "comparison_id", _text(self.comparison_id, "comparison_id", max_length=256))
        object.__setattr__(self, "candidate_ref", _text(self.candidate_ref, "candidate_ref", max_length=256))
        object.__setattr__(self, "candidate_digest", normalize_sha256(self.candidate_digest, "candidate_digest"))
        object.__setattr__(self, "subject_key", validate_subject_key(self.subject_key))
        object.__setattr__(self, "evaluated_at", normalize_timestamp(self.evaluated_at, "evaluated_at"))
        object.__setattr__(self, "shadow_recommendation", _scalar(self.shadow_recommendation, "shadow_recommendation"))
        object.__setattr__(
            self, "actual_deterministic_choice", _scalar(self.actual_deterministic_choice, "actual_deterministic_choice")
        )
        object.__setattr__(self, "actual_choice_ref", _text(self.actual_choice_ref, "actual_choice_ref"))
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "outcome_evidence_refs", refs)
        object.__setattr__(self, "outcome_evidence_digests", digests)
        object.__setattr__(self, "notes", tuple(_text(note, "comparison note") for note in self.notes))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ShadowComparison":
        if not isinstance(payload, Mapping):
            raise TypeError("shadow comparison payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", ""),
            learner_rule_version=payload.get("learner_rule_version", ""),
            comparison_id=payload.get("comparison_id", ""),
            candidate_ref=payload.get("candidate_ref", ""),
            candidate_digest=payload.get("candidate_digest", ""),
            scope=AdaptiveScope.from_dict(payload.get("scope", {})),
            subject_key=payload.get("subject_key", ""),
            evaluated_at=payload.get("evaluated_at", ""),
            shadow_recommendation=payload.get("shadow_recommendation"),
            actual_deterministic_choice=payload.get("actual_deterministic_choice"),
            actual_choice_ref=payload.get("actual_choice_ref", ""),
            disposition=payload.get("disposition", ""),
            execution_controlled_by=payload.get("execution_controlled_by", ""),
            shadow_influenced_execution=payload.get("shadow_influenced_execution", True),
            outcome_evidence_refs=tuple(payload.get("outcome_evidence_refs", ())),
            outcome_evidence_digests=tuple(payload.get("outcome_evidence_digests", ())),
            notes=tuple(payload.get("notes", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "learner_rule_version": self.learner_rule_version,
            "comparison_id": self.comparison_id,
            "candidate_ref": self.candidate_ref,
            "candidate_digest": self.candidate_digest,
            "scope": self.scope.to_dict(),
            "subject_key": self.subject_key,
            "evaluated_at": self.evaluated_at,
            "shadow_recommendation": self.shadow_recommendation,
            "actual_deterministic_choice": self.actual_deterministic_choice,
            "actual_choice_ref": self.actual_choice_ref,
            "disposition": self.disposition,
            "execution_controlled_by": "DETERMINISTIC_ORCHESTRA",
            "shadow_influenced_execution": False,
        }
        if self.outcome_evidence_refs:
            payload["outcome_evidence_refs"] = list(self.outcome_evidence_refs)
            payload["outcome_evidence_digests"] = list(self.outcome_evidence_digests)
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ShadowStoreLayout:
    root: Path
    user_key: str

    @classmethod
    def build(
        cls,
        user_key: str,
        *,
        root: Path | None = None,
        repository_root: Path | None = None,
    ) -> "ShadowStoreLayout":
        adaptive = AdaptiveStoreLayout.build(user_key, root=root, repository_root=repository_root)
        return cls(root=adaptive.root / "shadow" / "a3", user_key=adaptive.user_key)

    @property
    def signals_path(self) -> Path:
        return self.root / "signals.jsonl"

    @property
    def candidates_path(self) -> Path:
        return self.root / "candidate-state.json"

    @property
    def comparisons_path(self) -> Path:
        return self.root / "comparisons.jsonl"


class JsonlShadowStore:
    """Machine-local A3 shadow store with no runtime routing or execution authority."""

    def __init__(
        self,
        user_key: str,
        *,
        root: Path | None = None,
        repository_root: Path | None = None,
    ):
        self.layout = ShadowStoreLayout.build(user_key, root=root, repository_root=repository_root)
        self.user_key = self.layout.user_key

    def append_signal(self, signal: ShadowSignal) -> ShadowSignal:
        if signal.scope.user_key != self.user_key:
            raise ValueError("shadow signal user mismatch")
        self.layout.root.mkdir(parents=True, exist_ok=True)
        with self.layout.signals_path.open("ab") as handle:
            handle.write(canonical_json_bytes(signal.to_dict()) + b"\n")
        return signal

    def load_signals(self) -> tuple[ShadowSignal, ...]:
        signals = tuple(self._load_jsonl(self.layout.signals_path, ShadowSignal.from_dict, "shadow signal"))
        if any(item.scope.user_key != self.user_key for item in signals):
            raise ValueError("shadow signal store user mismatch")
        return signals

    def write_candidates(self, candidates: Sequence[ShadowCandidate]) -> None:
        ordered = tuple(sorted(candidates, key=lambda item: item.candidate_id))
        if any(item.scope.user_key != self.user_key for item in ordered):
            raise ValueError("shadow candidate user mismatch")
        payload = {
            "schema_version": SHADOW_CANDIDATE_STATE_SCHEMA_VERSION,
            "learner_rule_version": SHADOW_RULE_VERSION,
            "candidates": [item.to_dict() for item in ordered],
        }
        self.layout.root.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.layout.candidates_path, canonical_json_bytes(payload) + b"\n")

    def load_candidates(self) -> tuple[ShadowCandidate, ...]:
        path = self.layout.candidates_path
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed shadow candidate state JSON: {exc.msg}") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("shadow candidate state must be an object")
        if payload.get("schema_version") != SHADOW_CANDIDATE_STATE_SCHEMA_VERSION:
            raise ValueError("unsupported shadow candidate state schema")
        if payload.get("learner_rule_version") != SHADOW_RULE_VERSION:
            raise ValueError("unsupported shadow candidate state learner rule")
        candidates = tuple(ShadowCandidate.from_dict(item) for item in payload.get("candidates", ()))
        if any(item.scope.user_key != self.user_key for item in candidates):
            raise ValueError("shadow candidate state user mismatch")
        return candidates

    def append_comparison(self, comparison: ShadowComparison) -> ShadowComparison:
        if comparison.scope.user_key != self.user_key:
            raise ValueError("shadow comparison user mismatch")
        self.layout.root.mkdir(parents=True, exist_ok=True)
        with self.layout.comparisons_path.open("ab") as handle:
            handle.write(canonical_json_bytes(comparison.to_dict()) + b"\n")
        return comparison

    def load_comparisons(self) -> tuple[ShadowComparison, ...]:
        comparisons = tuple(
            self._load_jsonl(self.layout.comparisons_path, ShadowComparison.from_dict, "shadow comparison")
        )
        if any(item.scope.user_key != self.user_key for item in comparisons):
            raise ValueError("shadow comparison store user mismatch")
        return comparisons

    @staticmethod
    def _load_jsonl(path: Path, loader, label: str) -> list[Any]:
        if not path.exists():
            return []
        records: list[Any] = []
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                raise ValueError(f"{label} JSONL contains blank line at {lineno}")
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed {label} JSONL at line {lineno}: {exc.msg}") from exc
            records.append(loader(payload))
        return records


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def shadow_signal_from_a1_observation(observation: AdaptiveObservation) -> ShadowSignal | None:
    """Translate validated A1 evidence into a non-authorizing A3 shadow signal."""
    if not isinstance(observation, AdaptiveObservation):
        raise TypeError("observation must be AdaptiveObservation")
    event_map = {
        "EXPLICIT_PREFERENCE_SET": "USER_SELECTION",
        "EXPLICIT_PREFERENCE_CORRECTED": "USER_CORRECTION",
        "EXPLICIT_PREFERENCE_REMOVED": "USER_REJECTION",
        "GOVERNED_OUTCOME_RECORDED": "TERMINAL_DISPOSITION",
    }
    signal_type = event_map.get(observation.event_type)
    if signal_type is None:
        return None
    if signal_type == "USER_REJECTION":
        value: Any = "REMOVED"
    elif signal_type == "TERMINAL_DISPOSITION":
        value = observation.payload.get("phase_status")
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError("governed outcome lacks a scalar terminal disposition")
    else:
        if "value" not in observation.payload:
            raise ValueError("explicit preference observation lacks value")
        value = observation.payload["value"]
    return ShadowSignal.build(
        scope=observation.scope,
        signal_type=signal_type,
        subject_key=observation.subject_key,
        observed_value=value,
        source_kind="A1_VALIDATED_OBSERVATION",
        source_ref=f"adaptive-observation:{observation.observation_id}",
        source_digest=observation.digest,
        observed_at=observation.occurred_at,
    )


def extract_a1_shadow_signals(observations: Iterable[AdaptiveObservation]) -> tuple[ShadowSignal, ...]:
    signals: list[ShadowSignal] = []
    for observation in observations:
        signal = shadow_signal_from_a1_observation(observation)
        if signal is not None:
            signals.append(signal)
    return tuple(signals)


def build_shadow_signal(
    *,
    scope: AdaptiveScope,
    signal_type: str,
    subject_key: str,
    observed_value: Any,
    source_kind: str,
    source_ref: str,
    source_digest: str,
    observed_at: str,
    measurement: Mapping[str, Any] | None = None,
) -> ShadowSignal:
    """Build a validated shadow signal from governed evidence; raw conversation is not a source kind."""
    return ShadowSignal.build(
        scope=scope,
        signal_type=signal_type,
        subject_key=subject_key,
        observed_value=observed_value,
        source_kind=source_kind,
        source_ref=source_ref,
        source_digest=source_digest,
        observed_at=observed_at,
        measurement=measurement,
    )


def _candidate_type(signals: Sequence[ShadowSignal]) -> str:
    types = {signal.signal_type for signal in signals}
    if types & {"SPECIALIST_STRATEGY_ACCEPTED", "SPECIALIST_STRATEGY_REJECTED"}:
        return "SPECIALIST_STRATEGY_TENDENCY"
    if types & {"USER_SELECTION", "USER_REJECTION", "USER_CORRECTION"}:
        return "USER_PREFERENCE_TENDENCY"
    return "WORKFLOW_TENDENCY"


def _candidate_identity(scope: AdaptiveScope, subject_key: str, candidate_type: str, value: Any) -> str:
    return f"candidate-{receipt_digest({'scope': scope.to_dict(), 'subject_key': subject_key, 'candidate_type': candidate_type, 'value': value})[:24]}"


def _explicit_patterns(profile: AdaptiveProfile | None) -> dict[tuple[str, str], AdaptivePattern]:
    if profile is None:
        return {}
    return {
        (pattern.scope.identity, pattern.subject_key): pattern
        for pattern in profile.patterns
        if pattern.evidence_class in _EXPLICIT_EVIDENCE_CLASSES and pattern.status == "confirmed"
    }


def learn_shadow_candidates(
    signals: Iterable[ShadowSignal],
    *,
    explicit_profile: AdaptiveProfile | None = None,
    previous_candidates: Iterable[ShadowCandidate] = (),
) -> tuple[ShadowCandidate, ...]:
    """Derive durable shadow candidates without writing A1/A2 state or changing execution."""
    normalized = tuple(signals)
    if normalized:
        users = {item.scope.user_key for item in normalized}
        if len(users) != 1:
            raise ValueError("shadow candidate learning cannot mix users")
    groups: dict[tuple[str, str, str], list[ShadowSignal]] = {}
    for signal in normalized:
        key = (
            signal.scope.identity,
            signal.subject_key,
            json.dumps(signal.observed_value, sort_keys=True, separators=(",", ":")),
        )
        groups.setdefault(key, []).append(signal)

    explicit = _explicit_patterns(explicit_profile)
    previous = {item.candidate_id: item for item in previous_candidates}
    candidates: list[ShadowCandidate] = []
    for grouped in groups.values():
        positives = [item for item in grouped if item.signal_type in _POSITIVE_SIGNAL_TYPES]
        by_digest: dict[str, ShadowSignal] = {}
        for item in sorted(positives, key=lambda signal: (signal.observed_at, signal.signal_id)):
            by_digest.setdefault(item.source_digest, item)
        support = tuple(by_digest.values())
        if len(support) < 2:
            continue
        scope = support[0].scope
        subject_key = support[0].subject_key
        candidate_value = support[0].observed_value
        if any(
            item.scope.identity != scope.identity
            or item.subject_key != subject_key
            or item.observed_value != candidate_value
            for item in support
        ):
            raise ValueError("candidate support crossed scope, subject, or value boundary")

        candidate_type = _candidate_type(grouped)
        candidate_id = _candidate_identity(scope, subject_key, candidate_type, candidate_value)
        prior = previous.get(candidate_id)
        negative = sorted(
            {
                item.source_digest: item
                for item in grouped
                if item.signal_type in _NEGATIVE_SIGNAL_TYPES
            }.values(),
            key=lambda signal: (signal.observed_at, signal.signal_id),
        )
        first_seen = min(item.observed_at for item in support)
        last_seen = max(item.observed_at for item in support)
        status = "CANDIDATE"
        conflict_ref: str | None = None
        notes: list[str] = []

        explicit_pattern = explicit.get((scope.identity, subject_key))
        if explicit_pattern is not None and explicit_pattern.value != candidate_value:
            status = "BLOCKED_BY_EXPLICIT_PREFERENCE"
            conflict_ref = explicit_pattern.pattern_id
            notes.append("conflicting explicit preference dominates shadow candidate")
        elif prior is not None and prior.status == "BLOCKED_BY_EXPLICIT_PREFERENCE":
            if last_seen <= prior.last_seen:
                candidates.append(prior)
                continue
            notes.append("post-block evidence observed; candidate remains shadow-only")
        if negative and negative[-1].observed_at >= last_seen:
            status = "REJECTED"
            conflict_ref = None
            notes.append("latest explicit negative evidence rejects this shadow candidate")
        elif negative:
            notes.append("conflicting negative evidence retained for review")

        confidence = min(0.95, 0.5 + 0.08 * min(len(support), 5))
        confidence = max(0.0, confidence - 0.08 * min(len(negative), 3))
        refs = tuple(item.signal_id for item in support)
        digests = tuple(item.digest for item in support)
        candidates.append(
            ShadowCandidate(
                candidate_id=candidate_id,
                scope=scope,
                subject_key=subject_key,
                candidate_type=candidate_type,
                candidate_value=candidate_value,
                confidence=round(confidence, 6),
                distinct_support_count=len(support),
                supporting_signal_refs=refs,
                supporting_signal_digests=digests,
                first_seen=first_seen,
                last_seen=last_seen,
                status=status,
                explicit_conflict_ref=conflict_ref,
                notes=tuple(notes),
            )
        )
    return tuple(sorted(candidates, key=lambda item: item.candidate_id))


def build_shadow_comparison(
    candidate: ShadowCandidate,
    *,
    actual_deterministic_choice: Any,
    actual_choice_ref: str,
    evaluated_at: str,
    comparable: bool = True,
    outcome_evidence_refs: Sequence[str] = (),
    outcome_evidence_digests: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> ShadowComparison:
    """Compare a shadow recommendation to the already-selected deterministic choice."""
    if not isinstance(candidate, ShadowCandidate):
        raise TypeError("candidate must be ShadowCandidate")
    actual = _scalar(actual_deterministic_choice, "actual_deterministic_choice")
    if candidate.status != "CANDIDATE":
        disposition = "CANDIDATE_BLOCKED"
    elif not comparable:
        disposition = "NO_COMPARABLE_DETERMINISTIC_CHOICE"
    elif candidate.candidate_value == actual:
        disposition = "MATCH"
    else:
        disposition = "MISMATCH"
    identity = {
        "candidate_ref": candidate.candidate_id,
        "candidate_digest": candidate.digest,
        "actual_deterministic_choice": actual,
        "actual_choice_ref": _text(actual_choice_ref, "actual_choice_ref"),
        "evaluated_at": normalize_timestamp(evaluated_at, "evaluated_at"),
        "disposition": disposition,
    }
    return ShadowComparison(
        comparison_id=f"comparison-{receipt_digest(identity)[:24]}",
        candidate_ref=candidate.candidate_id,
        candidate_digest=candidate.digest,
        scope=candidate.scope,
        subject_key=candidate.subject_key,
        evaluated_at=identity["evaluated_at"],
        shadow_recommendation=candidate.candidate_value,
        actual_deterministic_choice=actual,
        actual_choice_ref=identity["actual_choice_ref"],
        disposition=disposition,
        outcome_evidence_refs=tuple(outcome_evidence_refs),
        outcome_evidence_digests=tuple(outcome_evidence_digests),
        notes=tuple(notes),
    )
