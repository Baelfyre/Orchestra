from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from orchestra_runtime.domain.orchestration.execution_efficiency import (
    CIWaitRequest,
    ContextReference,
    DecisiveStopSignal,
    EvidenceReuseRecord,
    PhaseContextPack,
    SpecialistInvocationRequest,
    authorize_validation_stage,
    evaluate_decisive_stop,
    evaluate_specialist_invocation,
    require_evidence_reuse,
    validate_execution_budget,
)
from orchestra_runtime.infrastructure.machine.execution_efficiency import (
    load_execution_budget_contract,
)


ROOT = Path(__file__).resolve().parents[2]


def _budget():
    return validate_execution_budget(load_execution_budget_contract(ROOT))


def test_oee1_owner_first_primary_route_is_allowed() -> None:
    decision = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="cloak",
            requested_specialist="cloak",
            role="PRIMARY",
            active_parallel_specialists=0,
            retry_number=0,
            justification="",
        ),
        _budget(),
    )
    assert decision.allowed is True
    assert decision.reason_code == "SPECIALIST_INVOCATION_ALLOWED"
    assert decision.blocking_allowed is True


def test_oee1_parallel_and_retry_budgets_fail_closed() -> None:
    parallel = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="cloak",
            requested_specialist="cloak",
            role="PRIMARY",
            active_parallel_specialists=1,
            retry_number=0,
            justification="",
        ),
        _budget(),
    )
    assert parallel.allowed is False
    assert parallel.reason_code == "PARALLEL_SPECIALIST_BUDGET_EXCEEDED"

    retry = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="cloak",
            requested_specialist="cloak",
            role="PRIMARY",
            active_parallel_specialists=0,
            retry_number=2,
            justification="",
        ),
        _budget(),
    )
    assert retry.allowed is False
    assert retry.reason_code == "SPECIALIST_RETRY_BUDGET_EXCEEDED"


def test_oee1_supporting_specialist_requires_material_reason() -> None:
    denied = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="cloak",
            requested_specialist="clockwork",
            role="SUPPORTING",
            active_parallel_specialists=0,
            retry_number=0,
            justification="general second opinion",
        ),
        _budget(),
    )
    assert denied.allowed is False
    assert denied.reason_code == "SECONDARY_SPECIALIST_REASON_REQUIRED"

    allowed = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="cloak",
            requested_specialist="clockwork",
            role="SUPPORTING",
            active_parallel_specialists=0,
            retry_number=0,
            justification="visible intent changes architecture boundaries",
            cross_domain_required=True,
        ),
        _budget(),
    )
    assert allowed.allowed is True


def test_oee1_optional_review_cannot_become_blocking() -> None:
    decision = evaluate_specialist_invocation(
        SpecialistInvocationRequest(
            owner_specialist="clockwork",
            requested_specialist="overseer",
            role="ADVERSARIAL",
            active_parallel_specialists=0,
            retry_number=0,
            justification="optional confidence review",
            adversarial_review_required=True,
            optional_review=True,
            blocking_requested=True,
        ),
        _budget(),
    )
    assert decision.allowed is False
    assert decision.reason_code == "OPTIONAL_REVIEW_CANNOT_BLOCK"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"role": "UNKNOWN"}, "unknown specialist invocation role"),
        ({"active_parallel_specialists": True}, "non-negative integer"),
        ({"retry_number": -1}, "non-negative integer"),
        ({"cross_domain_required": "yes"}, "must be a boolean"),
        (
            {"role": "PRIMARY", "requested_specialist": "clockwork"},
            "primary specialist must be the decision owner",
        ),
        (
            {"role": "SUPPORTING", "requested_specialist": "cloak", "justification": "x"},
            "supporting specialist must differ",
        ),
        (
            {
                "role": "ADVERSARIAL",
                "requested_specialist": "overseer",
                "justification": "x",
            },
            "adversarial specialist requires",
        ),
        (
            {
                "role": "REROUTE",
                "requested_specialist": "clockwork",
                "justification": "x",
            },
            "reroute specialist requires",
        ),
    ],
)
def test_oee1_invocation_request_rejects_malformed_or_unjustified_inputs(
    kwargs, message
) -> None:
    data = dict(
        owner_specialist="cloak",
        requested_specialist="cloak",
        role="PRIMARY",
        active_parallel_specialists=0,
        retry_number=0,
        justification="",
    )
    data.update(kwargs)
    with pytest.raises(ValueError, match=message):
        SpecialistInvocationRequest(**data).validate()


def test_oee1_evaluator_requires_exact_policy_types() -> None:
    with pytest.raises(ValueError, match="request must"):
        evaluate_specialist_invocation([], _budget())
    with pytest.raises(ValueError, match="budget must"):
        evaluate_specialist_invocation(
            SpecialistInvocationRequest(
                "cloak", "cloak", "PRIMARY", 0, 0, ""
            ),
            {},
        )


def test_oee2_decisive_evidence_stops_downstream_execution() -> None:
    signal = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=True,
        stop_required=True,
        downstream_execution_allowed=False,
        reason="responsive contract is contradictory",
        evidence_refs=("machine/ui/ui-fidelity-handoff.v1.json",),
    )
    assert evaluate_decisive_stop(signal) == "STOP"


def test_oee2_non_blocking_evidence_can_continue() -> None:
    signal = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=False,
        stop_required=False,
        downstream_execution_allowed=True,
        reason="input integrity still being evaluated",
        evidence_refs=("machine/ui/ui-fidelity-handoff.v1.json",),
    )
    assert evaluate_decisive_stop(signal) == "CONTINUE"

    conservative = DecisiveStopSignal(
        owner="cloak",
        evidence_sufficient=False,
        stop_required=False,
        downstream_execution_allowed=False,
        reason="authority is unresolved",
        evidence_refs=("authority-record",),
    )
    assert evaluate_decisive_stop(conservative) == "STOP"

    with pytest.raises(ValueError, match="signal must"):
        evaluate_decisive_stop({})


def test_oee3_exact_source_identity_controls_evidence_reuse() -> None:
    digest = sha256(b"handoff").hexdigest()
    record = EvidenceReuseRecord(
        evidence_id="uief4-handoff",
        source_ref="machine/ui/ui-fidelity-handoff.v1.json",
        source_identity="tree:abc",
        content_digest=digest,
        produced_tier="E1",
        allowed_consumers=("cloak", "arbiter"),
    )
    require_evidence_reuse(
        record,
        current_source_identity="tree:abc",
        consumer="arbiter",
    )

    with pytest.raises(ValueError, match="source identity is stale"):
        require_evidence_reuse(
            record,
            current_source_identity="tree:def",
            consumer="arbiter",
        )
    with pytest.raises(ValueError, match="consumer is not authorized"):
        require_evidence_reuse(
            record,
            current_source_identity="tree:abc",
            consumer="clockwork",
        )


@pytest.mark.parametrize(
    ("record", "message"),
    [
        (
            EvidenceReuseRecord(
                "id", "ref", "identity", "bad", "E1", ("cloak",)
            ),
            "SHA-256",
        ),
        (
            EvidenceReuseRecord(
                "id", "ref", "identity", sha256(b"x").hexdigest(), "E9", ("cloak",)
            ),
            "evidence tier",
        ),
        (
            EvidenceReuseRecord(
                "id",
                "ref",
                "identity",
                sha256(b"x").hexdigest(),
                "E1",
                ("cloak", "CLOAK"),
            ),
            "non-empty and unique",
        ),
    ],
)
def test_oee3_reuse_record_fails_closed(record, message) -> None:
    with pytest.raises(ValueError, match=message):
        record.validate()

    with pytest.raises(ValueError, match="record must"):
        require_evidence_reuse(
            {},
            current_source_identity="tree:abc",
            consumer="cloak",
        )


def test_oee4_validation_progresses_only_after_prior_stages() -> None:
    authorize_validation_stage(
        "SYNTAX_SCHEMA",
        (),
        candidate_stable=False,
    )
    authorize_validation_stage(
        "DIRECT_TESTS",
        ("SYNTAX_SCHEMA",),
        candidate_stable=False,
    )
    authorize_validation_stage(
        "REPOSITORY_QUALIFICATION",
        ("SYNTAX_SCHEMA", "DIRECT_TESTS", "SUBSYSTEM"),
        candidate_stable=True,
    )
    authorize_validation_stage(
        "PROTECTED_GATES",
        (
            "SYNTAX_SCHEMA",
            "DIRECT_TESTS",
            "SUBSYSTEM",
            "REPOSITORY_QUALIFICATION",
        ),
        candidate_stable=True,
    )


def test_oee4_validation_rejects_skips_unstable_candidates_and_bad_state() -> None:
    with pytest.raises(ValueError, match="prior stages"):
        authorize_validation_stage(
            "SUBSYSTEM",
            ("SYNTAX_SCHEMA",),
            candidate_stable=False,
        )
    with pytest.raises(ValueError, match="stable candidate"):
        authorize_validation_stage(
            "REPOSITORY_QUALIFICATION",
            ("SYNTAX_SCHEMA", "DIRECT_TESTS", "SUBSYSTEM"),
            candidate_stable=False,
        )
    with pytest.raises(ValueError, match="unknown validation stage"):
        authorize_validation_stage("UNKNOWN", (), candidate_stable=False)
    with pytest.raises(ValueError, match="completed_stages contains unknown"):
        authorize_validation_stage(
            "DIRECT_TESTS",
            ("UNKNOWN",),
            candidate_stable=False,
        )
    with pytest.raises(ValueError, match="must be unique"):
        authorize_validation_stage(
            "SUBSYSTEM",
            ("SYNTAX_SCHEMA", "DIRECT_TESTS", "DIRECT_TESTS"),
            candidate_stable=False,
        )
    with pytest.raises(ValueError, match="candidate_stable must be a boolean"):
        authorize_validation_stage("SYNTAX_SCHEMA", (), candidate_stable=1)


def test_oee5_unchanged_ci_is_passive_and_watch_loops_are_rejected() -> None:
    assert (
        CIWaitRequest(
            previous_state_identity="checks:a",
            current_state_identity="checks:a",
            active_model_reasoning=False,
        ).evaluate()
        == "PASSIVE_WAIT"
    )
    assert (
        CIWaitRequest(
            previous_state_identity="checks:a",
            current_state_identity="checks:b",
            active_model_reasoning=True,
        ).evaluate()
        == "REVIEW_CHANGED_STATE"
    )

    with pytest.raises(ValueError, match="continuous CI watch"):
        CIWaitRequest(
            previous_state_identity="checks:a",
            current_state_identity="checks:a",
            active_model_reasoning=False,
            continuous_watch_requested=True,
        ).evaluate()

    with pytest.raises(ValueError, match="unchanged CI"):
        CIWaitRequest(
            previous_state_identity="checks:a",
            current_state_identity="checks:a",
            active_model_reasoning=True,
        ).evaluate()


@pytest.mark.parametrize(
    "ci_request",
    [
        CIWaitRequest("", "checks:a", False),
        CIWaitRequest("checks:a", "", False),
        CIWaitRequest("checks:a", "checks:a", "no"),
    ],
)
def test_oee5_ci_wait_request_rejects_malformed_state(ci_request) -> None:
    with pytest.raises(ValueError):
        ci_request.evaluate()


def _ref(name: str) -> ContextReference:
    return ContextReference(
        ref=name,
        source_identity=f"sha:{name}",
        purpose=f"needed for {name}",
    )


def test_oee6_phase_context_pack_is_minimum_source_bound_context() -> None:
    pack = PhaseContextPack(
        phase_id="OEE-6",
        owner_specialist="conductor",
        objective="build minimum sufficient context",
        required_refs=(_ref("active"), _ref("budget")),
        conditional_refs=(_ref("history"),),
        unresolved_questions=("Does the exact source identity still match?",),
        allowed_actions=("read exact refs",),
        prohibited_actions=("load full history by default",),
    )
    pack.validate()


def test_oee6_context_pack_rejects_duplicate_or_unbounded_context() -> None:
    with pytest.raises(ValueError, match="at least one required"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(),
        ).validate()

    with pytest.raises(ValueError, match="must be unique"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("same"),),
            conditional_refs=(_ref("same"),),
        ).validate()

    with pytest.raises(ValueError, match="must not overlap"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            allowed_actions=("merge",),
            prohibited_actions=("merge",),
        ).validate()

    with pytest.raises(ValueError, match="historical_context_reason"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            historical_context_included=True,
        ).validate()

    with pytest.raises(ValueError, match="requires historical_context_included"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            historical_context_reason="old decision",
        ).validate()


def test_oee6_context_reference_and_list_fields_fail_closed() -> None:
    with pytest.raises(ValueError):
        ContextReference("", "sha:x", "purpose").validate()

    with pytest.raises(ValueError, match="ContextReference"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=("not-a-ref",),
        ).validate()

    with pytest.raises(ValueError, match="unique non-empty"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            unresolved_questions=("same", "same"),
        ).validate()

    with pytest.raises(ValueError, match="must be a boolean"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            historical_context_included=1,
        ).validate()

def test_oee1_invocation_decision_rejects_malformed_outputs() -> None:
    from orchestra_runtime.domain.orchestration.execution_efficiency import (
        SpecialistInvocationDecision,
    )

    with pytest.raises(ValueError, match="flags must be booleans"):
        SpecialistInvocationDecision(
            allowed=1,
            reason_code="X",
            requested_specialist="cloak",
            role="PRIMARY",
            blocking_allowed=True,
        )

    with pytest.raises(ValueError, match="unknown specialist invocation decision role"):
        SpecialistInvocationDecision(
            allowed=True,
            reason_code="X",
            requested_specialist="cloak",
            role="UNKNOWN",
            blocking_allowed=True,
        )


@pytest.mark.parametrize(
    "consumers",
    [
        (),
        ("",),
    ],
)
def test_oee3_reuse_record_requires_non_empty_consumers(consumers) -> None:
    record = EvidenceReuseRecord(
        "id",
        "ref",
        "identity",
        sha256(b"x").hexdigest(),
        "E1",
        consumers,
    )
    with pytest.raises(ValueError, match="allowed_consumers"):
        record.validate()


@pytest.mark.parametrize(
    ("ref", "identity", "purpose"),
    [
        ("", "sha:x", "purpose"),
        ("ref", "", "purpose"),
        ("ref", "sha:x", ""),
    ],
)
def test_oee6_context_reference_requires_all_identity_fields(
    ref, identity, purpose
) -> None:
    with pytest.raises(ValueError):
        ContextReference(ref, identity, purpose).validate()


@pytest.mark.parametrize(
    ("phase_id", "owner", "objective"),
    [
        ("", "conductor", "objective"),
        ("OEE-6", "", "objective"),
        ("OEE-6", "conductor", ""),
    ],
)
def test_oee6_phase_context_pack_requires_core_identity(
    phase_id, owner, objective
) -> None:
    with pytest.raises(ValueError):
        PhaseContextPack(
            phase_id=phase_id,
            owner_specialist=owner,
            objective=objective,
            required_refs=(_ref("one"),),
        ).validate()


def test_oee6_historical_context_is_allowed_only_with_explicit_reason() -> None:
    PhaseContextPack(
        phase_id="OEE-6",
        owner_specialist="conductor",
        objective="inspect one historical decision",
        required_refs=(_ref("one"),),
        historical_context_included=True,
        historical_context_reason="the current decision explicitly depends on it",
    ).validate()


def test_oee6_list_fields_reject_empty_values() -> None:
    with pytest.raises(ValueError, match="unique non-empty"):
        PhaseContextPack(
            phase_id="OEE-6",
            owner_specialist="conductor",
            objective="x",
            required_refs=(_ref("one"),),
            allowed_actions=("",),
        ).validate()
