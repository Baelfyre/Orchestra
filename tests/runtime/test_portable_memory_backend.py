from __future__ import annotations

from copy import deepcopy

import jsonschema
import pytest

from orchestra_runtime.adaptive.portable_memory import (
    MemoryBackendDescriptor,
    PORTABLE_SCHEMA,
    build_portable_memory_candidate,
    _load_json,
)


def _candidate() -> dict:
    return {
        "schema_version": "orchestra.adaptive-shadow-candidate.v1",
        "learner_rule_version": "orchestra.adaptive-shadow-rules.v1",
        "candidate_id": "candidate-workflow-001",
        "scope": {
            "scope_type": "specialist",
            "user_key": "local-user-key",
            "project_key": "example-project",
            "specialist_slug": "cloak",
        },
        "subject_key": "workflow.preserve_existing_structure",
        "candidate_type": "SPECIALIST_STRATEGY_TENDENCY",
        "candidate_value": "adapt-before-rebuild",
        "confidence": 0.91,
        "confidence_method": "BOUNDED_EVIDENCE_ACCUMULATION_V1",
        "distinct_support_count": 2,
        "supporting_signal_refs": ["signal-001", "signal-002"],
        "supporting_signal_digests": ["a" * 64, "b" * 64],
        "first_seen": "2026-08-24T00:00:00Z",
        "last_seen": "2026-08-25T00:00:00Z",
        "status": "CANDIDATE",
        "shadow_only": True,
        "promotion_state": "NOT_PROMOTED",
    }


def test_custom_backend_is_supported_without_core_backend_identity() -> None:
    backend = MemoryBackendDescriptor(
        backend_id="private_store",
        adapter_kind="CUSTOM",
        record_format="JSON",
        config_ref="user://memory/private_store",
    )
    envelope = build_portable_memory_candidate(
        _candidate(),
        backend=backend,
        category="WORKFLOW",
        repositories=["Example/Repo"],
        use_cases=["frontend_fidelity"],
        privacy_reviewed=True,
        created_at="2026-08-26T00:00:00Z",
    )
    jsonschema.Draft202012Validator(_load_json(PORTABLE_SCHEMA)).validate(envelope)
    assert envelope["destination"]["backend_id"] == "private_store"
    assert envelope["destination"]["adapter_kind"] == "CUSTOM"
    assert envelope["destination"]["canonical_write_authorized"] is False
    assert envelope["authority"]["automatic_promotion"] is False


def test_local_user_and_session_keys_are_not_exported() -> None:
    envelope = build_portable_memory_candidate(
        _candidate(),
        backend=MemoryBackendDescriptor("local_json", "LOCAL_JSON"),
        category="WORKFLOW",
        privacy_reviewed=True,
        created_at="2026-08-26T00:00:00Z",
    )
    rendered = str(envelope)
    assert "local-user-key" not in rendered
    assert "user_key" not in rendered
    assert "task_session_key" not in rendered


def test_privacy_review_is_required() -> None:
    with pytest.raises(ValueError, match="privacy review"):
        build_portable_memory_candidate(
            _candidate(),
            backend=MemoryBackendDescriptor("local_json", "LOCAL_JSON"),
            category="WORKFLOW",
        )


def test_blocked_shadow_candidate_cannot_be_ported() -> None:
    candidate = deepcopy(_candidate())
    candidate["status"] = "BLOCKED_BY_EXPLICIT_PREFERENCE"
    candidate["explicit_conflict_ref"] = "explicit-preference-001"
    with pytest.raises(ValueError, match="only active A3 CANDIDATE"):
        build_portable_memory_candidate(
            candidate,
            backend=MemoryBackendDescriptor("local_json", "LOCAL_JSON"),
            category="WORKFLOW",
            privacy_reviewed=True,
        )


def test_signal_ref_digest_parity_is_required() -> None:
    candidate = deepcopy(_candidate())
    candidate["supporting_signal_digests"] = ["a" * 64, "b" * 64, "c" * 64]
    with pytest.raises(ValueError, match="one-to-one parity"):
        build_portable_memory_candidate(
            candidate,
            backend=MemoryBackendDescriptor("local_json", "LOCAL_JSON"),
            category="WORKFLOW",
            privacy_reviewed=True,
        )
