from __future__ import annotations

from typing import Any, Iterable

from ..retrospective import OrchestraPhaseRetrospective
from .models import AdaptiveScope
from .store import JsonlAdaptiveStore


def append_explicit_preference(
    store: JsonlAdaptiveStore,
    *,
    scope: AdaptiveScope,
    subject_key: str,
    value: Any,
    occurred_at: str,
    source_ref: str,
    current_instruction: bool = False,
    correction: bool = False,
    expires_at: str | None = None,
):
    return store.append(
        event_type="EXPLICIT_PREFERENCE_CORRECTED" if correction else "EXPLICIT_PREFERENCE_SET",
        scope=scope,
        subject_key=subject_key,
        evidence_class="EXPLICIT_CURRENT_INSTRUCTION" if current_instruction else "EXPLICIT_SCOPED_PREFERENCE",
        source_type="explicit_user_instruction",
        source_ref=source_ref,
        occurred_at=occurred_at,
        payload={"value": value},
        expires_at=expires_at,
    )


def append_preference_removal(
    store: JsonlAdaptiveStore,
    *,
    scope: AdaptiveScope,
    subject_key: str,
    occurred_at: str,
    source_ref: str,
):
    return store.append(
        event_type="EXPLICIT_PREFERENCE_REMOVED",
        scope=scope,
        subject_key=subject_key,
        evidence_class="USER_FEEDBACK",
        source_type="explicit_user_correction",
        source_ref=source_ref,
        occurred_at=occurred_at,
        payload={},
    )


def append_inferred_candidate(
    store: JsonlAdaptiveStore,
    *,
    scope: AdaptiveScope,
    subject_key: str,
    value: Any,
    confidence: float,
    evidence_refs: Iterable[str],
    occurred_at: str,
    source_ref: str,
    expires_at: str | None = None,
):
    """Append an advisory candidate only. A1 provides no automatic promotion API."""
    return store.append(
        event_type="INFERRED_PATTERN_CANDIDATE",
        scope=scope,
        subject_key=subject_key,
        evidence_class="INFERRED_CANDIDATE",
        source_type="governed_pattern_materializer",
        source_ref=source_ref,
        occurred_at=occurred_at,
        payload={"value": value, "confidence": confidence, "evidence_refs": list(evidence_refs)},
        expires_at=expires_at,
    )


def append_retrospective_outcome(
    store: JsonlAdaptiveStore,
    *,
    scope: AdaptiveScope,
    retrospective: OrchestraPhaseRetrospective,
    subject_key: str = "workflow.phase_outcome",
):
    if not isinstance(retrospective, OrchestraPhaseRetrospective):
        raise TypeError("retrospective must be OrchestraPhaseRetrospective")
    return store.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=scope,
        subject_key=subject_key,
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref=f"retrospective:{retrospective.retrospective_id}",
        occurred_at=retrospective.created_at,
        payload={
            "phase_id": retrospective.phase_id,
            "phase_status": retrospective.phase_status,
            "total_units_planned": retrospective.total_units_planned,
            "units_accepted": retrospective.units_accepted,
            "remediation_cycle_count": retrospective.remediation_cycle_count,
            "capacity_wait_count": retrospective.capacity_wait_count,
            "human_escalation_count": retrospective.human_escalation_count,
            "evidence_fingerprint": retrospective.evidence_fingerprint,
        },
    )
