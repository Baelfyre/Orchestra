from __future__ import annotations

import pytest

from orchestra_runtime import context_state
from orchestra_runtime.domain import context as domain_context


def _state(**overrides):
    values = {
        "project_id": "orchestra",
        "repository": "Baelfyre/Orchestra",
        "canonical_sha": "a" * 40,
        "phase": "AR-2",
        "authority_mode": "FULL_AUTONOMOUS_BOUNDED",
        "current_task": "Extract domain context semantics",
        "blockers": (),
        "critical_receipt_refs": ("receipt:source",),
        "evidence_index_refs": ("evidence:ar2",),
        "revision": 8,
        "updated_at": "2026-09-02T07:15:00+08:00",
    }
    values.update(overrides)
    return domain_context.CurrentProjectState(**values)


def test_legacy_context_exports_are_canonical_domain_symbols():
    assert context_state.CONTEXT_STATE_SCHEMA_VERSION == domain_context.CONTEXT_STATE_SCHEMA_VERSION
    assert context_state.CurrentProjectState is domain_context.CurrentProjectState
    assert context_state.ContinuityEvent is domain_context.ContinuityEvent
    assert context_state.compile_context is domain_context.compile_context


def test_domain_state_preserves_legacy_normalization_and_digest_behavior():
    state = _state(
        canonical_sha="A" * 40,
        blockers=("z-blocker", "a-blocker"),
        updated_at="2026-09-02T07:15:00+08:00",
    )
    assert state.canonical_sha == "a" * 40
    assert state.blockers == ("a-blocker", "z-blocker")
    assert state.updated_at == "2026-09-01T23:15:00Z"
    assert len(state.digest) == 64


def test_domain_context_compiler_preserves_progressive_levels_and_explicit_history():
    state = _state()
    event = domain_context.ContinuityEvent(
        sequence=1,
        project_id="orchestra",
        event_type="AR2_CONTEXT_EXTRACTION_STARTED",
        occurred_at="2026-09-01T23:15:00Z",
        payload={"unit": "domain/context"},
        previous_event_digest=None,
    )

    l0 = domain_context.compile_context(state, "L0")
    l1 = domain_context.compile_context(state, "L1")
    l2 = domain_context.compile_context(state, "L2", event_head_digest=event.digest)
    l3 = domain_context.compile_context(state, "L3", event_head_digest=event.digest, history=(event,))

    assert "current_task" not in l0
    assert l1["current_task"] == state.current_task
    assert l2["event_head_digest"] == event.digest
    assert l3["history"] == [event.to_dict()]


def test_domain_context_refuses_inferred_l3_history():
    with pytest.raises(ValueError, match="explicitly supplied"):
        domain_context.compile_context(_state(), "L3")


def test_legacy_context_store_rejects_empty_project_identity(tmp_path):
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        context_state.JsonlContinuityStore(tmp_path / "events.jsonl", "   ")


def test_legacy_store_and_markdown_surfaces_remain_available_outside_domain_package(tmp_path):
    state = _state()
    store = context_state.JsonlContinuityStore(tmp_path / "events.jsonl", state.project_id)
    event = store.append(
        event_type="STATE_CREATED",
        occurred_at="2026-09-01T23:15:00Z",
        payload={"revision": state.revision},
    )

    assert isinstance(event, domain_context.ContinuityEvent)
    assert store.load() == (event,)
    rendered = context_state.render_state_markdown(state)
    context_state.assert_markdown_parity(state, rendered)
