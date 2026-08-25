from __future__ import annotations

from copy import deepcopy

import jsonschema
import pytest

from scripts.adaptive_padayon_bridge import BRIDGE_SCHEMA, build_promotion_envelope, load_json


def _candidate() -> dict:
    return {
        "schema_version": "orchestra.adaptive-shadow-candidate.v1",
        "learner_rule_version": "orchestra.adaptive-shadow-rules.v1",
        "candidate_id": "candidate-workflow-001",
        "scope": {
            "scope_type": "specialist",
            "user_key": "local-user-key",
            "project_key": "orderly",
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


def test_bridge_emits_privacy_minimized_non_authorizing_envelope() -> None:
    envelope = build_promotion_envelope(
        _candidate(),
        category="DESIGN_UI_UX",
        repositories=["Baelfyre/Orderly"],
        use_cases=["frontend_fidelity"],
        privacy_reviewed=True,
        created_at="2026-08-26T00:00:00Z",
    )
    jsonschema.Draft202012Validator(load_json(BRIDGE_SCHEMA)).validate(envelope)
    assert envelope["pattern"]["scope"]["projects"] == ["orderly"]
    assert envelope["pattern"]["scope"]["specialists"] == ["cloak"]
    assert "user_key" not in str(envelope)
    assert "task_session_key" not in str(envelope)
    assert envelope["authority"]["automatic_promotion"] is False
    assert envelope["intake"]["canonical_write_authorized"] is False


def test_bridge_requires_explicit_privacy_review() -> None:
    with pytest.raises(ValueError, match="privacy review"):
        build_promotion_envelope(_candidate(), category="WORKFLOW")


def test_bridge_rejects_blocked_shadow_candidate() -> None:
    candidate = deepcopy(_candidate())
    candidate["status"] = "BLOCKED_BY_EXPLICIT_PREFERENCE"
    candidate["explicit_conflict_ref"] = "explicit-preference-001"
    with pytest.raises(ValueError, match="only active A3 CANDIDATE"):
        build_promotion_envelope(candidate, category="WORKFLOW", privacy_reviewed=True)


def test_bridge_requires_signal_ref_digest_parity() -> None:
    candidate = deepcopy(_candidate())
    candidate["supporting_signal_digests"] = ["a" * 64, "b" * 64, "c" * 64]
    with pytest.raises(ValueError, match="one-to-one parity"):
        build_promotion_envelope(candidate, category="WORKFLOW", privacy_reviewed=True)
