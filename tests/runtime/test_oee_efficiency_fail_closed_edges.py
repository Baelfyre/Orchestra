from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.domain.orchestration.execution_efficiency_runtime import (
    ContextEvidence,
    EfficiencyPhaseResult,
    EvidenceCacheEntry,
    PhaseContextPack,
    SpecialistInvocationPlan,
    build_owner_first_plan,
    evaluate_evidence_reuse,
    evaluate_program_resume_gate,
    validate_validation_request,
)


def test_validation_history_must_be_exact_prefix_without_duplicates_or_future_stages() -> None:
    with pytest.raises(ValueError, match="cannot skip prerequisites"):
        validate_validation_request(
            "DIRECT_TESTS",
            ("SYNTAX_SCHEMA", "PROTECTED_GATES"),
            candidate_stable=True,
        )
    with pytest.raises(ValueError, match="must be unique"):
        validate_validation_request(
            "SUBSYSTEM",
            ("SYNTAX_SCHEMA", "DIRECT_TESTS", "DIRECT_TESTS"),
            candidate_stable=True,
        )


def test_phase_context_pack_requires_owner_consumable_evidence() -> None:
    pack = PhaseContextPack(
        phase_id="OEE-6",
        owner_specialist="conductor",
        source_revision="revision",
        evidence=(
            ContextEvidence("evidence.one", "blob:one", ("overseer",)),
        ),
    )
    with pytest.raises(ValueError, match="evidence for its owner"):
        pack.validate()


def test_context_evidence_requires_nonempty_unique_consumers() -> None:
    with pytest.raises(ValueError, match="at least one consumer"):
        ContextEvidence("ref", "blob:one", ()).validate()
    with pytest.raises(ValueError, match="values must be unique"):
        ContextEvidence("ref", "blob:one", ("conductor", "conductor")).validate()


def test_specialist_plan_requires_nonempty_identity_and_unique_supporting_specialists() -> None:
    with pytest.raises(ValueError, match="owner_specialist must be non-empty"):
        build_owner_first_plan("")
    with pytest.raises(ValueError, match="values must be unique"):
        build_owner_first_plan(
            "cloak",
            ("clockwork", "clockwork"),
            expansion_reason="CROSS_DOMAIN_AUTHORITY",
            expansion_evidence_refs=("boundary",),
        )


def test_specialist_expansion_rejects_unknown_reason_and_duplicate_evidence() -> None:
    with pytest.raises(ValueError, match="explicit cross-domain or adversarial"):
        build_owner_first_plan(
            "cloak",
            ("clockwork",),
            expansion_reason="BECAUSE_I_WANT_TO",
            expansion_evidence_refs=("boundary",),
        )
    with pytest.raises(ValueError, match="values must be unique"):
        build_owner_first_plan(
            "cloak",
            ("clockwork",),
            expansion_reason="CROSS_DOMAIN_AUTHORITY",
            expansion_evidence_refs=("boundary", "boundary"),
        )


def test_evidence_cache_entry_rejects_empty_identity_fields() -> None:
    entry = EvidenceCacheEntry("e", "cloak", "revision", "blob:one", "blob:content")
    for field in (
        "evidence_id",
        "owner_ref",
        "source_revision",
        "source_identity",
        "content_identity",
    ):
        with pytest.raises(ValueError, match="must be non-empty"):
            replace(entry, **{field: ""}).validate()


def test_evidence_reuse_input_must_be_nonempty() -> None:
    entry = EvidenceCacheEntry("e", "cloak", "revision", "blob:one", "blob:content")
    with pytest.raises(ValueError, match="source_revision must be non-empty"):
        evaluate_evidence_reuse(entry, source_revision="", source_identity="blob:one")
    with pytest.raises(ValueError, match="source_identity must be non-empty"):
        evaluate_evidence_reuse(entry, source_revision="revision", source_identity="")


def test_program_gate_rejects_malformed_phase_result_boolean() -> None:
    results = [
        EfficiencyPhaseResult(f"OEE-{index}", True, (f"evidence.{index}",))
        for index in range(8)
    ]
    results[4] = EfficiencyPhaseResult("OEE-4", 1, ("evidence.4",))
    with pytest.raises(ValueError, match="passed must be a boolean"):
        evaluate_program_resume_gate(results)


def test_failed_phase_may_remain_explicitly_without_pass_evidence() -> None:
    result = EfficiencyPhaseResult("OEE-3", False, ())
    result.validate()
