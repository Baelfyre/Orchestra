from __future__ import annotations

import json

import pytest

from orchestra_runtime import context_state as legacy_context
from orchestra_runtime.domain.context import state as domain_context


def _state(**overrides):
    values = {
        "project_id": "orchestra",
        "repository": "Baelfyre/Orchestra",
        "canonical_sha": "a" * 40,
        "phase": "AR-2",
        "authority_mode": "FULL_AUTONOMOUS_BOUNDED",
        "current_task": "Extract context domain state",
        "blockers": ("release-held",),
        "critical_receipt_refs": ("receipt:source",),
        "evidence_index_refs": ("evidence:architecture",),
        "revision": 3,
        "updated_at": "2026-09-02T05:45:00+08:00",
    }
    values.update(overrides)
    return domain_context.CurrentProjectState(**values)


def test_legacy_context_domain_exports_preserve_object_identity():
    assert legacy_context.CONTEXT_STATE_SCHEMA_VERSION is domain_context.CONTEXT_STATE_SCHEMA_VERSION
    assert legacy_context.CurrentProjectState is domain_context.CurrentProjectState
    assert legacy_context.ContinuityEvent is domain_context.ContinuityEvent


def test_domain_project_state_preserves_canonicalization_and_digest_behavior():
    state = _state(
        blockers=("z-last", "a-first"),
        critical_receipt_refs=("receipt:b", "receipt:a"),
        evidence_index_refs=("evidence:b", "evidence:a"),
    )

    assert state.canonical_sha == "a" * 40
    assert state.updated_at == "2026-09-01T21:45:00Z"
    assert state.blockers == ("a-first", "z-last")
    assert state.critical_receipt_refs == ("receipt:a", "receipt:b")
    assert state.evidence_index_refs == ("evidence:a", "evidence:b")
    assert len(state.digest) == 64
    assert domain_context.CurrentProjectState.from_dict(state.to_dict()) == state


def test_domain_continuity_event_preserves_hash_chain_contract():
    first = domain_context.ContinuityEvent(
        sequence=1,
        project_id="orchestra",
        event_type="AR2_CONTEXT_STARTED",
        occurred_at="2026-09-01T21:45:00Z",
        payload={"phase": "AR-2", "unit": "domain-context"},
        previous_event_digest=None,
    )
    second = domain_context.ContinuityEvent(
        sequence=2,
        project_id="orchestra",
        event_type="AR2_CONTEXT_CHECKPOINT",
        occurred_at="2026-09-01T21:46:00Z",
        payload={"status": "qualified"},
        previous_event_digest=first.digest,
    )

    assert len(first.digest) == 64
    assert second.previous_event_digest == first.digest
    assert domain_context.ContinuityEvent.from_dict(second.to_dict()) == second
    assert json.loads(json.dumps(second.to_dict()))["sequence"] == 2


def test_domain_context_rejects_invalid_state_and_event_inputs():
    with pytest.raises(ValueError, match="owner/name"):
        _state(repository="Orchestra")

    with pytest.raises(ValueError, match="duplicate"):
        _state(blockers=("same", "same"))

    with pytest.raises(ValueError, match="only the first event"):
        domain_context.ContinuityEvent(
            sequence=2,
            project_id="orchestra",
            event_type="BROKEN",
            occurred_at="2026-09-01T21:45:00Z",
            payload={},
            previous_event_digest=None,
        )
