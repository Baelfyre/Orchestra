import json
from pathlib import Path

import pytest

from orchestra_runtime.context_state import (
    ContinuityEvent,
    CurrentProjectState,
    JsonlContinuityStore,
    assert_markdown_parity,
    compile_context,
    render_state_markdown,
)


def _state(**overrides):
    values = {
        "project_id": "orchestra",
        "repository": "Baelfyre/Orchestra",
        "canonical_sha": "1" * 40,
        "phase": "P6",
        "authority_mode": "FULL_AUTONOMOUS_BOUNDED",
        "current_task": "Implement typed continuity state",
        "blockers": ("review-policy", "release-not-yet-authorized"),
        "critical_receipt_refs": ("receipt:host", "receipt:source"),
        "evidence_index_refs": ("evidence:p5", "evidence:p6"),
        "revision": 7,
        "updated_at": "2026-08-15T16:45:00+08:00",
    }
    values.update(overrides)
    return CurrentProjectState(**values)


def test_state_digest_is_stable_across_unordered_sets():
    first = _state()
    second = _state(
        blockers=tuple(reversed(first.blockers)),
        critical_receipt_refs=tuple(reversed(first.critical_receipt_refs)),
        evidence_index_refs=tuple(reversed(first.evidence_index_refs)),
    )
    assert first.to_dict() == second.to_dict()
    assert first.digest == second.digest


def test_context_levels_are_bounded_and_progressively_expand():
    state = _state()
    l0 = compile_context(state, "L0")
    l1 = compile_context(state, "L1")
    l2 = compile_context(state, "L2", event_head_digest="a" * 64)
    assert "current_task" not in l0
    assert "blockers" not in l0
    assert "critical_receipt_refs" not in l0
    assert "current_task" in l1
    assert "evidence_index_refs" not in l1
    assert "evidence_index_refs" in l2
    assert len(json.dumps(l0)) < len(json.dumps(l1)) < len(json.dumps(l2))


def test_l3_refuses_to_invent_history():
    with pytest.raises(ValueError, match="explicitly supplied"):
        compile_context(_state(), "L3")


def test_l3_includes_only_explicit_same_project_history():
    event = ContinuityEvent(
        sequence=1,
        project_id="orchestra",
        event_type="PHASE_STARTED",
        occurred_at="2026-08-15T08:45:00Z",
        payload={"phase": "P6"},
        previous_event_digest=None,
    )
    result = compile_context(_state(), "L3", event_head_digest=event.digest, history=(event,))
    assert result["history"] == [event.to_dict()]


def test_l3_rejects_cross_project_history():
    event = ContinuityEvent(
        sequence=1,
        project_id="orderly",
        event_type="PHASE_STARTED",
        occurred_at="2026-08-15T08:45:00Z",
        payload={"phase": "FBR1"},
        previous_event_digest=None,
    )
    with pytest.raises(ValueError, match="another project"):
        compile_context(_state(), "L3", event_head_digest=event.digest, history=(event,))


def test_jsonl_append_reload_preserves_exact_hash_chain(tmp_path):
    store = JsonlContinuityStore(tmp_path / "events.jsonl", "orchestra")
    first = store.append(event_type="STATE_CREATED", occurred_at="2026-08-15T08:45:00Z", payload={"revision": 1})
    second = store.append(event_type="STATE_UPDATED", occurred_at="2026-08-15T08:46:00Z", payload={"revision": 2})
    loaded = store.load()
    assert loaded == (first, second)
    assert second.previous_event_digest == first.digest


def test_jsonl_sequence_gap_fails_closed(tmp_path):
    path = tmp_path / "events.jsonl"
    event = ContinuityEvent(
        sequence=1,
        project_id="orchestra",
        event_type="STATE_CREATED",
        occurred_at="2026-08-15T08:45:00Z",
        payload={},
        previous_event_digest=None,
    )
    broken = event.to_dict()
    broken["sequence"] = 2
    broken["previous_event_digest"] = "a" * 64
    path.write_text(json.dumps(broken) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sequence gap"):
        JsonlContinuityStore(path, "orchestra").load()


def test_jsonl_hash_chain_tamper_fails_closed(tmp_path):
    store = JsonlContinuityStore(tmp_path / "events.jsonl", "orchestra")
    store.append(event_type="STATE_CREATED", occurred_at="2026-08-15T08:45:00Z", payload={"revision": 1})
    store.append(event_type="STATE_UPDATED", occurred_at="2026-08-15T08:46:00Z", payload={"revision": 2})
    lines = store.path.read_text(encoding="utf-8").splitlines()
    second = json.loads(lines[1])
    second["previous_event_digest"] = "b" * 64
    store.path.write_text(lines[0] + "\n" + json.dumps(second) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash-chain mismatch"):
        store.load()


def test_jsonl_malformed_line_fails_closed(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed continuity JSONL"):
        JsonlContinuityStore(path, "orchestra").load()


def test_jsonl_cross_project_event_fails_closed(tmp_path):
    event = ContinuityEvent(
        sequence=1,
        project_id="orderly",
        event_type="STATE_CREATED",
        occurred_at="2026-08-15T08:45:00Z",
        payload={},
        previous_event_digest=None,
    )
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(event.to_dict()) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="project mismatch"):
        JsonlContinuityStore(path, "orchestra").load()


def test_markdown_render_is_deterministic_and_parity_checked():
    state = _state()
    first = render_state_markdown(state)
    second = render_state_markdown(state)
    assert first == second
    assert state.digest in first
    assert_markdown_parity(state, first)


def test_hand_edited_markdown_fails_parity():
    state = _state()
    rendered = render_state_markdown(state)
    with pytest.raises(ValueError, match="stale or hand-edited"):
        assert_markdown_parity(state, rendered.replace("P6", "P7", 1))


def test_state_rejects_non_exact_git_sha():
    with pytest.raises(ValueError, match="40-character"):
        _state(canonical_sha="1234567")
