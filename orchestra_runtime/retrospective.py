from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .correlation import validate_correlation_id

RETROSPECTIVE_SCHEMA_VERSION = "1.0.0"
VALID_PHASE_STATUSES = frozenset({"COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "TIMED_OUT"})


def derive_retrospective_id(phase_id: str, execution_envelope_ref: str) -> str:
    pid = str(phase_id or "").strip()
    env_ref = str(execution_envelope_ref or "").strip()
    if not pid:
        raise ValueError("phase_id must be a non-empty string")
    if not env_ref:
        raise ValueError("execution_envelope_ref must be a non-empty string")
    return f"retro-{pid}-{env_ref}"


def derive_evidence_fingerprint(data: bytes | str) -> str:
    if isinstance(data, str):
        payload = data.encode("utf-8")
    else:
        payload = bytes(data)
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class OrchestraPhaseRetrospective:
    retrospective_id: str
    phase_id: str
    execution_envelope_ref: str
    phase_status: str
    total_units_planned: int
    units_accepted: int
    remediation_cycle_count: int
    capacity_wait_count: int
    human_escalation_count: int
    evidence_fingerprint: str
    created_at: str
    schema_version: str = RETROSPECTIVE_SCHEMA_VERSION
    correlation_id: str | None = None
    outcome_summary: str | None = None
    known_limitations: tuple[str, ...] | None = None
    follow_up_candidates: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.schema_version != RETROSPECTIVE_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version '{self.schema_version}', expected '{RETROSPECTIVE_SCHEMA_VERSION}'"
            )

        pid = str(self.phase_id or "").strip()
        if not pid:
            raise ValueError("phase_id must be a non-empty string")
        object.__setattr__(self, "phase_id", pid)

        env_ref = str(self.execution_envelope_ref or "").strip()
        if not env_ref:
            raise ValueError("execution_envelope_ref must be a non-empty string")
        object.__setattr__(self, "execution_envelope_ref", env_ref)

        cat = str(self.created_at or "").strip()
        if not cat:
            raise ValueError("created_at must be a non-empty string")
        object.__setattr__(self, "created_at", cat)

        expected_id = derive_retrospective_id(pid, env_ref)
        rid = str(self.retrospective_id or "").strip()
        if rid != expected_id:
            raise ValueError(
                f"retrospective_id '{rid}' does not match derived identity '{expected_id}'"
            )
        object.__setattr__(self, "retrospective_id", rid)

        status = str(self.phase_status or "").strip()
        if status not in VALID_PHASE_STATUSES:
            raise ValueError(
                f"invalid phase_status '{status}', must be one of {sorted(VALID_PHASE_STATUSES)}"
            )
        object.__setattr__(self, "phase_status", status)

        if not isinstance(self.total_units_planned, int) or isinstance(self.total_units_planned, bool) or self.total_units_planned < 0:
            raise ValueError("total_units_planned must be a non-negative integer")

        if not isinstance(self.units_accepted, int) or isinstance(self.units_accepted, bool) or self.units_accepted < 0:
            raise ValueError("units_accepted must be a non-negative integer")

        if self.units_accepted > self.total_units_planned:
            raise ValueError(
                f"units_accepted ({self.units_accepted}) cannot exceed total_units_planned ({self.total_units_planned})"
            )

        if not isinstance(self.remediation_cycle_count, int) or isinstance(self.remediation_cycle_count, bool) or self.remediation_cycle_count < 0:
            raise ValueError("remediation_cycle_count must be a non-negative integer")

        if not isinstance(self.capacity_wait_count, int) or isinstance(self.capacity_wait_count, bool) or self.capacity_wait_count < 0:
            raise ValueError("capacity_wait_count must be a non-negative integer")

        if not isinstance(self.human_escalation_count, int) or isinstance(self.human_escalation_count, bool) or self.human_escalation_count < 0:
            raise ValueError("human_escalation_count must be a non-negative integer")

        fp = str(self.evidence_fingerprint or "").strip()
        if not fp:
            raise ValueError("evidence_fingerprint must be a non-empty string")
        object.__setattr__(self, "evidence_fingerprint", fp)

        if self.correlation_id is not None:
            cid = validate_correlation_id(self.correlation_id)
            object.__setattr__(self, "correlation_id", cid)

        if self.outcome_summary is not None:
            summary = str(self.outcome_summary).strip()
            object.__setattr__(self, "outcome_summary", summary)

        if self.known_limitations is not None:
            limitations = tuple(str(item).strip() for item in self.known_limitations if str(item).strip())
            object.__setattr__(self, "known_limitations", limitations)

        if self.follow_up_candidates is not None:
            candidates = tuple(str(item).strip() for item in self.follow_up_candidates if str(item).strip())
            object.__setattr__(self, "follow_up_candidates", candidates)


def should_generate_phase_retrospective(
    *,
    total_units_planned: int,
    phase_status: str,
    remediation_cycle_count: int = 0,
    capacity_wait_count: int = 0,
    human_escalation_count: int = 0,
    maintainer_decision_ref: str | None = None,
    governance_phase_gate: bool = False,
) -> bool:
    if governance_phase_gate or (maintainer_decision_ref and str(maintainer_decision_ref).strip()):
        return True

    status = str(phase_status or "").strip()
    is_non_completed_terminal = status in {"FAILED", "BLOCKED", "CANCELLED", "TIMED_OUT"}
    has_material_signal = (
        remediation_cycle_count > 0
        or capacity_wait_count > 0
        or human_escalation_count > 0
        or is_non_completed_terminal
    )

    if total_units_planned > 1 and has_material_signal:
        return True

    return False


def build_phase_retrospective(
    *,
    phase_id: str,
    execution_envelope_ref: str,
    phase_status: str,
    total_units_planned: int,
    units_accepted: int,
    created_at: str,
    evidence_fingerprint: str,
    remediation_cycle_count: int = 0,
    capacity_wait_count: int = 0,
    human_escalation_count: int = 0,
    correlation_id: str | None = None,
    outcome_summary: str | None = None,
    known_limitations: tuple[str, ...] | None = None,
    follow_up_candidates: tuple[str, ...] | None = None,
) -> OrchestraPhaseRetrospective:
    rid = derive_retrospective_id(phase_id, execution_envelope_ref)
    return OrchestraPhaseRetrospective(
        retrospective_id=rid,
        phase_id=phase_id,
        execution_envelope_ref=execution_envelope_ref,
        phase_status=phase_status,
        total_units_planned=total_units_planned,
        units_accepted=units_accepted,
        remediation_cycle_count=remediation_cycle_count,
        capacity_wait_count=capacity_wait_count,
        human_escalation_count=human_escalation_count,
        evidence_fingerprint=evidence_fingerprint,
        created_at=created_at,
        schema_version=RETROSPECTIVE_SCHEMA_VERSION,
        correlation_id=correlation_id,
        outcome_summary=outcome_summary,
        known_limitations=known_limitations,
        follow_up_candidates=follow_up_candidates,
    )


def maybe_build_phase_retrospective(
    *,
    phase_id: str,
    execution_envelope_ref: str,
    phase_status: str,
    total_units_planned: int,
    units_accepted: int,
    created_at: str,
    evidence_fingerprint: str,
    remediation_cycle_count: int = 0,
    capacity_wait_count: int = 0,
    human_escalation_count: int = 0,
    correlation_id: str | None = None,
    outcome_summary: str | None = None,
    known_limitations: tuple[str, ...] | None = None,
    follow_up_candidates: tuple[str, ...] | None = None,
    maintainer_decision_ref: str | None = None,
    governance_phase_gate: bool = False,
) -> OrchestraPhaseRetrospective | None:
    if not should_generate_phase_retrospective(
        total_units_planned=total_units_planned,
        phase_status=phase_status,
        remediation_cycle_count=remediation_cycle_count,
        capacity_wait_count=capacity_wait_count,
        human_escalation_count=human_escalation_count,
        maintainer_decision_ref=maintainer_decision_ref,
        governance_phase_gate=governance_phase_gate,
    ):
        return None

    return build_phase_retrospective(
        phase_id=phase_id,
        execution_envelope_ref=execution_envelope_ref,
        phase_status=phase_status,
        total_units_planned=total_units_planned,
        units_accepted=units_accepted,
        created_at=created_at,
        evidence_fingerprint=evidence_fingerprint,
        remediation_cycle_count=remediation_cycle_count,
        capacity_wait_count=capacity_wait_count,
        human_escalation_count=human_escalation_count,
        correlation_id=correlation_id,
        outcome_summary=outcome_summary,
        known_limitations=known_limitations,
        follow_up_candidates=follow_up_candidates,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for key, value in pairs:
        if key in res:
            raise ValueError(f"duplicate JSON key rejected: '{key}'")
        res[key] = value
    return res


def serialize_phase_retrospective(retrospective: OrchestraPhaseRetrospective) -> bytes:
    if not isinstance(retrospective, OrchestraPhaseRetrospective):
        raise TypeError("expected OrchestraPhaseRetrospective instance")

    payload: dict[str, Any] = {
        "schema_version": retrospective.schema_version,
        "retrospective_id": retrospective.retrospective_id,
        "phase_id": retrospective.phase_id,
        "execution_envelope_ref": retrospective.execution_envelope_ref,
        "phase_status": retrospective.phase_status,
        "total_units_planned": retrospective.total_units_planned,
        "units_accepted": retrospective.units_accepted,
        "remediation_cycle_count": retrospective.remediation_cycle_count,
        "capacity_wait_count": retrospective.capacity_wait_count,
        "human_escalation_count": retrospective.human_escalation_count,
        "evidence_fingerprint": retrospective.evidence_fingerprint,
        "created_at": retrospective.created_at,
    }

    if retrospective.correlation_id is not None:
        payload["correlation_id"] = retrospective.correlation_id

    if retrospective.outcome_summary is not None:
        payload["outcome_summary"] = retrospective.outcome_summary

    if retrospective.known_limitations is not None:
        payload["known_limitations"] = list(retrospective.known_limitations)

    if retrospective.follow_up_candidates is not None:
        payload["follow_up_candidates"] = list(retrospective.follow_up_candidates)

    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)
    return text.encode("utf-8")


def serialize_phase_retrospective_to_str(retrospective: OrchestraPhaseRetrospective) -> str:
    return serialize_phase_retrospective(retrospective).decode("utf-8")


def _parse_retrospective_dict(raw: dict[str, Any]) -> OrchestraPhaseRetrospective:
    if not isinstance(raw, dict):
        raise ValueError("JSON payload must be a dictionary object")

    known_keys = {
        "schema_version",
        "retrospective_id",
        "phase_id",
        "execution_envelope_ref",
        "phase_status",
        "total_units_planned",
        "units_accepted",
        "remediation_cycle_count",
        "capacity_wait_count",
        "human_escalation_count",
        "evidence_fingerprint",
        "created_at",
        "correlation_id",
        "outcome_summary",
        "known_limitations",
        "follow_up_candidates",
    }
    unknown = set(raw.keys()) - known_keys
    if unknown:
        raise ValueError(f"unknown field(s) rejected: {sorted(unknown)}")

    required_keys = {
        "schema_version",
        "retrospective_id",
        "phase_id",
        "execution_envelope_ref",
        "phase_status",
        "total_units_planned",
        "units_accepted",
        "remediation_cycle_count",
        "capacity_wait_count",
        "human_escalation_count",
        "evidence_fingerprint",
        "created_at",
    }
    missing = required_keys - set(raw.keys())
    if missing:
        raise ValueError(f"missing required field(s): {sorted(missing)}")

    schema_ver = str(raw["schema_version"]).strip()
    if schema_ver != RETROSPECTIVE_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version '{schema_ver}'")

    limitations = raw.get("known_limitations")
    limitations_tuple = tuple(limitations) if isinstance(limitations, list) else None

    candidates = raw.get("follow_up_candidates")
    candidates_tuple = tuple(candidates) if isinstance(candidates, list) else None

    return OrchestraPhaseRetrospective(
        schema_version=schema_ver,
        retrospective_id=str(raw["retrospective_id"]),
        phase_id=str(raw["phase_id"]),
        execution_envelope_ref=str(raw["execution_envelope_ref"]),
        phase_status=str(raw["phase_status"]),
        total_units_planned=raw["total_units_planned"],
        units_accepted=raw["units_accepted"],
        remediation_cycle_count=raw["remediation_cycle_count"],
        capacity_wait_count=raw["capacity_wait_count"],
        human_escalation_count=raw["human_escalation_count"],
        evidence_fingerprint=str(raw["evidence_fingerprint"]),
        created_at=str(raw["created_at"]),
        correlation_id=raw.get("correlation_id"),
        outcome_summary=raw.get("outcome_summary"),
        known_limitations=limitations_tuple,
        follow_up_candidates=candidates_tuple,
    )


def deserialize_phase_retrospective(payload: bytes | str) -> OrchestraPhaseRetrospective:
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ValueError(f"invalid UTF-8 bytes payload: {err}") from err
        try:
            raw = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"non-finite constant rejected: {c}")),
            )
        except Exception as err:
            raise ValueError(f"invalid JSON payload: {err}") from err
    elif isinstance(payload, str):
        try:
            raw = json.loads(
                payload,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"non-finite constant rejected: {c}")),
            )
        except Exception as err:
            raise ValueError(f"invalid JSON payload: {err}") from err
    else:
        raise TypeError("expected bytes or str payload")

    return _parse_retrospective_dict(raw)
