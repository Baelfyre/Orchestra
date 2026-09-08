from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from orchestra_runtime.domain.adaptive import (
    ASSURANCE_ORDER,
    AQ3_AUTHORITY_RULE,
    AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION,
    CANONICAL_SPECIALIST_ORDER,
    FAILURE_CODES,
    FAIL_AQ1_COMPLETION_SCOPE,
    FAIL_AUTHORITY_SCOPE_VIOLATION,
    FAIL_DUPLICATE_EVIDENCE_IDENTITY,
    FAIL_INDEPENDENT_ASSURANCE_REQUIRED,
    FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY,
    FAIL_PROTECTED_GATE_UNSATISFIED,
    FAIL_REQUIRED_ASSURANCE_MISSING,
    FAIL_REQUIRED_DAGGER_OMITTED,
    FAIL_SOURCE_TRUTH_VIOLATION,
    FAIL_STALE_EVIDENCE,
    FAIL_WEAKER_EVIDENCE,
    FAIL_WRONG_SOURCE_EVIDENCE,
    REQUIRED_RECEIPT_FIELDS,
    REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS,
    SpecialistAssuranceContractError,
    SpecialistAssuranceEvidence,
    SpecialistAssuranceReceipt,
    assess_overseer_review,
    build_routing_receipt,
    evaluate_arbiter_progression,
    profile_risk,
    validate_authority_scope,
    validate_concurrency_claim,
    validate_routing_receipt,
    validate_specialist_claim,
)
from orchestra_runtime.domain.adaptive.risk_profiler import DaggerDecision


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq3-specialist-assurance-contract.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "specialist-assurance-contract.v1.schema.json"
SOURCE = "orchestra:aef8d55b4b941066a2c958629eac79729133bd31"


def _profile(**overrides: object):
    values: dict[str, object] = {
        "development_mode": "SPEC_FIRST",
        "material_behavior": "bounded AQ3 contract behavior",
        "authority_boundary": ("IMPLEMENTATION",),
        "changed_domains": (),
        "changed_paths": (),
        "quality_dimensions": (),
        "risk_characteristics": (),
        "invariants": (),
        "protected_gates": (),
    }
    values.update(overrides)
    return profile_risk(**values)


def _receipt(profile, **overrides):
    values = {"source_identities": (SOURCE,)}
    values.update(overrides)
    return build_routing_receipt(profile, **values)


def _scope(assurance_class: str) -> str:
    return {
        "SECURITY_ASSURANCE": "SECURITY",
        "CONCURRENCY_ASSURANCE": "CONCURRENCY",
        "AGGREGATE_INVARIANT_ASSURANCE": "AGGREGATE",
        "ADVERSARIAL_ASSURANCE": "ADVERSARIAL",
        "DOCUMENTATION_RECONCILIATION": "DOCUMENTATION",
    }.get(assurance_class, "CONTRACT")


def _evidence(
    receipt,
    assurance_class: str,
    *,
    evidence_id: str | None = None,
    logical_identity: str | None = None,
    producer: str = "ponytail",
    validator: str = "overseer",
    source_identity: str = SOURCE,
    status: str = "SATISFIED",
    kind: str = "TEST",
    scope: str | None = None,
    source_truth: str = "OBSERVED",
    provenance_qualification: str = "AUTHORITATIVE",
) -> SpecialistAssuranceEvidence:
    return SpecialistAssuranceEvidence(
        evidence_id=evidence_id or f"evidence:{assurance_class.casefold()}",
        assurance_class=assurance_class,
        producer=producer,
        validator=validator,
        source_identity=source_identity,
        scope=scope or _scope(assurance_class),
        kind=kind,
        status=status,
        logical_identity=logical_identity,
        source_truth=source_truth,
        provenance_qualification=provenance_qualification,
    )


def _complete_evidence(receipt, *, producer: str = "ponytail") -> list[SpecialistAssuranceEvidence]:
    return [
        _evidence(receipt, assurance, producer=producer, evidence_id=f"evidence:{index}")
        for index, assurance in enumerate(receipt.required_assurance)
        if assurance != "INDEPENDENT_QA"
    ] + [_evidence(receipt, "INDEPENDENT_QA", producer=producer, evidence_id="evidence:independent")]


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_aq3_machine_contract_is_schema_valid_and_matches_domain_constants() -> None:
    contract = _json(CONTRACT_PATH)
    schema = _json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(contract)) == []
    assert contract["schema_version"] == AQ3_SPECIALIST_ASSURANCE_SCHEMA_VERSION
    assert contract["receipt_fields"] == list(REQUIRED_RECEIPT_FIELDS)
    assert contract["canonical_specialist_order"] == list(CANONICAL_SPECIALIST_ORDER)
    assert contract["canonical_assurance_order"] == list(ASSURANCE_ORDER)
    assert contract["failure_codes"] == list(FAILURE_CODES)
    assert contract["authority"] == {
        "receipt_authorizes_dispatch": False,
        "receipt_authorizes_execution": False,
        "receipt_expands_authority": False,
        "provider_activation": False,
        "production_action": False,
        "arbiter_transition_authority_created": False,
        "dagger_execution_authority_created": False,
    }
    assert AQ3_AUTHORITY_RULE == "WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION"


def test_receipt_round_trip_is_deterministic_and_source_bound() -> None:
    profile = _profile(
        changed_domains=("Domain", "Application"),
        quality_dimensions=("RELIABILITY", "SECURITY"),
        risk_characteristics=("AUTHENTICATION",),
    )
    first = _receipt(profile, source_identities=("source:b", SOURCE))
    second = _receipt(profile, source_identities=(SOURCE, "source:b"))
    assert first.to_dict() == second.to_dict()
    assert first.receipt_fingerprint == second.receipt_fingerprint
    assert first.risk_fingerprint == profile.normalized_risk_fingerprint
    assert validate_routing_receipt(first, profile) == first
    assert SpecialistAssuranceReceipt.from_mapping(first.to_dict()) == first
    json.loads(json.dumps(first.to_dict(), sort_keys=True))


def test_empty_source_identity_and_invalid_receipt_shapes_fail_closed() -> None:
    profile = _profile()
    with pytest.raises(ValueError, match="source_identities"):
        _receipt(profile, source_identities=())
    with pytest.raises(TypeError, match="iterable"):
        _receipt(profile, source_identities=SOURCE)
    with pytest.raises(TypeError, match="AdaptiveRiskProfile"):
        build_routing_receipt(object(), source_identities=(SOURCE,))
    with pytest.raises(TypeError, match="mapping"):
        SpecialistAssuranceReceipt.from_mapping([])
    with pytest.raises(TypeError, match="dagger_decision"):
        SpecialistAssuranceReceipt.from_mapping({"source_identities": [SOURCE]})
    with pytest.raises(TypeError, match="unsupported AQ3 receipt fields"):
        SpecialistAssuranceReceipt.from_mapping({**_receipt(profile).to_dict(), "unexpected": True})
    with pytest.raises(TypeError, match="unsupported Dagger decision fields"):
        SpecialistAssuranceReceipt.from_mapping(
            {
                **_receipt(profile).to_dict(),
                "dagger_decision": {**_receipt(profile).dagger_decision.to_dict(), "unexpected": True},
            }
        )


def test_conductor_receipt_preserves_aq2_and_allows_explicit_bounded_additions() -> None:
    profile = _profile()
    receipt = _receipt(
        profile,
        coordination_additions=("weaver",),
        assurance_additions=("FUNCTIONAL_ASSURANCE",),
    )
    assert "weaver" in receipt.selected_specialists
    assert "FUNCTIONAL_ASSURANCE" in receipt.required_assurance
    assert receipt.authority_expansion is False
    assert receipt.provider_activation is False
    assert receipt.production_action is False
    assert validate_routing_receipt(receipt, profile) == receipt


def test_aq2_required_specialist_and_assurance_removal_is_rejected() -> None:
    profile = _profile(changed_domains=("documentation",))
    receipt = _receipt(profile)
    weakened_specialists = replace(
        receipt,
        selected_specialists=tuple(item for item in receipt.selected_specialists if item != "scribe"),
    )
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_REQUIRED_ASSURANCE_MISSING):
        validate_routing_receipt(weakened_specialists, profile)
    weakened_assurance = replace(
        receipt,
        required_assurance=tuple(item for item in receipt.required_assurance if item != "DOCUMENTATION_RECONCILIATION"),
    )
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_REQUIRED_ASSURANCE_MISSING):
        validate_routing_receipt(weakened_assurance, profile)


def test_required_dagger_cannot_be_omitted_from_concurrent_privilege_mutation() -> None:
    profile = _profile(risk_characteristics=("AUTHORIZATION", "CONCURRENCY", "PRIVILEGE_MUTATION"))
    receipt = _receipt(profile)
    assert receipt.dagger_decision.required is True
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_REQUIRED_DAGGER_OMITTED):
        replace(
            receipt,
            selected_specialists=tuple(item for item in receipt.selected_specialists if item != "dagger"),
        )


def test_dagger_is_rejected_for_harmless_copy_only_work() -> None:
    profile = _profile(changed_domains=("documentation",), changed_paths=("docs/copy.md",))
    receipt = _receipt(profile)
    over_routed = replace(
        receipt,
        selected_specialists=receipt.selected_specialists + ("dagger",),
        dagger_decision=DaggerDecision(required=True, triggered_by=("CONCURRENCY",)),
    )
    with pytest.raises(
        SpecialistAssuranceContractError,
        match=FAIL_OR_WARN_OVERRouting_ACCORDING_TO_CANONICAL_POLICY,
    ):
        validate_routing_receipt(over_routed, profile)


def test_added_specialists_do_not_create_authority() -> None:
    profile = _profile()
    receipt = _receipt(profile, coordination_additions=("ponytail", "the-tuner"))
    assert receipt.selected_specialists[-2:] == ("the-tuner", "ponytail")
    assert receipt.authority_expansion is False
    assert validate_routing_receipt(receipt, profile) == receipt
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        _receipt(profile, coordination_additions=("overseer",))
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        _receipt(profile, assurance_additions=("INDEPENDENT_QA",))


def test_ponytail_self_certification_fails_without_independent_overseer() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    evidence = _complete_evidence(receipt, producer="ponytail")
    evidence = [replace(record, validator="ponytail") for record in evidence]
    review = assess_overseer_review(receipt, evidence, reviewer="ponytail")
    assert review.implementation_contract_satisfied is False
    assert review.invariant_preservation_sufficient is False
    assert FAIL_INDEPENDENT_ASSURANCE_REQUIRED in review.failure_codes


def test_overseer_requires_separate_attribution_and_can_issue_both_decisions() -> None:
    profile = _profile(invariants=("FAILED_VALIDATION_MUST_NOT_BECOME_PASS",))
    receipt = _receipt(profile)
    review = assess_overseer_review(receipt, _complete_evidence(receipt))
    assert review.implementation_contract_satisfied is True
    assert review.invariant_preservation_sufficient is True
    assert review.satisfied is True
    assert review.failure_codes == ()
    assert review.to_dict()["reviewer"] == "overseer"


def test_arbiter_blocks_green_ci_when_concurrency_evidence_is_missing() -> None:
    profile = _profile(risk_characteristics=("CONCURRENCY",))
    receipt = _receipt(profile)
    evidence = [_evidence(receipt, "INDEPENDENT_QA", kind="CI", scope="CI")]
    review = assess_overseer_review(receipt, evidence)
    decision = evaluate_arbiter_progression(receipt, evidence, overseer_review=review)
    assert decision.disposition == "BLOCK"
    assert decision.can_advance is False
    assert FAIL_REQUIRED_ASSURANCE_MISSING in decision.failure_codes


def test_arbiter_compares_required_actual_and_claimed_sets() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    evidence = _complete_evidence(receipt)
    review = assess_overseer_review(receipt, evidence)
    decision = evaluate_arbiter_progression(
        receipt,
        evidence,
        claimed_completion_state="CONTRACT_VERIFIED",
        overseer_review=review,
    )
    assert decision.disposition == "ADVANCE"
    assert decision.can_advance is True
    assert decision.required_assurance_set == receipt.required_assurance
    assert decision.actual_evidence_set == receipt.required_assurance
    assert decision.to_dict()["can_advance"] is True


def test_arbiter_rejects_stale_wrong_source_weaker_and_duplicate_evidence() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    stale = _evidence(receipt, "INDEPENDENT_QA", evidence_id="same", status="STALE")
    wrong = _evidence(receipt, "INDEPENDENT_QA", evidence_id="wrong", source_identity="sha:wrong")
    weaker = _evidence(receipt, "INDEPENDENT_QA", evidence_id="weak", status="WEAKER")
    duplicate = _evidence(receipt, "INDEPENDENT_QA", evidence_id="same", logical_identity="same")
    review = assess_overseer_review(receipt, [stale, wrong, weaker, duplicate])
    decision = evaluate_arbiter_progression(receipt, [stale, wrong, weaker, duplicate], overseer_review=review)
    assert decision.disposition == "BLOCK"
    assert FAIL_STALE_EVIDENCE in decision.failure_codes
    assert FAIL_WRONG_SOURCE_EVIDENCE in decision.failure_codes
    assert FAIL_WEAKER_EVIDENCE in decision.failure_codes
    assert FAIL_DUPLICATE_EVIDENCE_IDENTITY in decision.failure_codes


def test_arbiter_blocks_protected_gate_and_aq1_completion_escalation() -> None:
    profile = _profile(
        risk_characteristics=("HUMAN_DECISION_AUTHORITY",),
        protected_gates=("HUMAN_REVIEW",),
    )
    receipt = _receipt(profile)
    evidence = _complete_evidence(receipt)
    review = assess_overseer_review(receipt, evidence)
    decision = evaluate_arbiter_progression(
        receipt,
        evidence,
        claimed_completion_state="PRODUCT_COMPLETE",
        protected_gates_satisfied=False,
        overseer_review=review,
    )
    assert FAIL_PROTECTED_GATE_UNSATISFIED in decision.failure_codes
    assert FAIL_AQ1_COMPLETION_SCOPE in decision.failure_codes


def test_arbiter_rejects_inferred_claims_and_wrong_context() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    evidence = _complete_evidence(receipt)
    review = assess_overseer_review(receipt, evidence)
    inferred = evaluate_arbiter_progression(
        receipt,
        evidence,
        claimed_source_truth="INFERRED",
        candidate_ref="different-candidate",
        overseer_review=review,
    )
    assert FAIL_AQ1_COMPLETION_SCOPE in inferred.failure_codes
    assert "FAIL_EVIDENCE_BINDING" in inferred.failure_codes
    contract_evidence = _complete_evidence(receipt)
    contract_review = assess_overseer_review(receipt, contract_evidence)
    runtime_claim = evaluate_arbiter_progression(
        receipt,
        contract_evidence,
        claimed_completion_state="RUNTIME_VERIFIED",
        overseer_review=contract_review,
    )
    assert FAIL_AQ1_COMPLETION_SCOPE in runtime_claim.failure_codes


def test_scribe_cannot_infer_historical_intent() -> None:
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_SOURCE_TRUTH_VIOLATION):
        validate_specialist_claim("scribe", claim_type="historical intent", source_truth="INFERRED")
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_SOURCE_TRUTH_VIOLATION):
        validate_specialist_claim("scribe", claim_type="historical intent", source_truth="UNVERIFIED")
    assert validate_specialist_claim("scribe", claim_type="historical intent", source_truth="OBSERVED") is True
    assert (
        validate_specialist_claim(
            "scribe",
            claim_type="historical intent",
            source_truth="DECIDED",
            authoritative_source_ref="decision:1",
        )
        is True
    )
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_SOURCE_TRUTH_VIOLATION):
        validate_specialist_claim("scribe", claim_type="historical intent", source_truth="DECIDED")


def test_cipher_cannot_mutate_global_authority_from_tenant_scope() -> None:
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        validate_authority_scope("cipher", actor_scope="tenant admin", mutation_scope="global")
    assert validate_authority_scope("cipher", actor_scope="tenant admin", mutation_scope="tenant") is True
    assert validate_authority_scope("overseer", actor_scope="tenant admin", mutation_scope="global") is True
    assert validate_authority_scope("cipher", actor_scope="tenant admin", mutation_scope="global", action="READ") is True


def test_chronicler_requires_aggregate_concurrency_analysis() -> None:
    with pytest.raises(SpecialistAssuranceContractError, match=REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS):
        validate_concurrency_claim(
            "chronicler",
            invariant="TENANT_MUST_RETAIN_ACTIVE_ADMIN_AGGREGATE",
            claim_scope="TENANT_WIDE_AGGREGATE",
            evidence_scope="ROW_VERSION",
        )
    assert (
        validate_concurrency_claim(
            "chronicler",
            invariant="TENANT_MUST_RETAIN_ACTIVE_ADMIN_AGGREGATE",
            claim_scope="TENANT_WIDE_AGGREGATE",
            evidence_scope="AGGREGATE",
        )
        is True
    )


def test_source_and_authority_guards_are_strict() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        replace(receipt, selected_by="ponytail")
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        replace(receipt, authority_expansion=True)
    wrong_profile = _profile(changed_domains=("domain",))
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_WRONG_SOURCE_EVIDENCE):
        validate_routing_receipt(receipt, wrong_profile)


def test_receipt_validation_edges_fail_closed() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    with pytest.raises(TypeError, match="must be a string"):
        replace(receipt, next_transition_target=1)
    with pytest.raises(ValueError, match="must be non-empty"):
        replace(receipt, next_transition_target=" ")
    with pytest.raises(ValueError, match="exceeds 256"):
        replace(receipt, next_transition_target="x" * 257)
    with pytest.raises(ValueError, match="unsupported"):
        replace(receipt, development_mode="UNKNOWN")
    with pytest.raises(TypeError, match="iterable"):
        replace(receipt, source_identities=1)
    with pytest.raises(ValueError, match="exceeds 32"):
        replace(receipt, source_identities=tuple(f"source:{index}" for index in range(33)))
    with pytest.raises(ValueError, match="duplicate"):
        replace(receipt, source_identities=(SOURCE, SOURCE))
    with pytest.raises(ValueError, match="exceeds 64"):
        replace(receipt, changed_domains=tuple(f"domain-{index}" for index in range(65)))
    with pytest.raises(ValueError, match="unsupported values"):
        replace(receipt, quality_dimensions=("UNKNOWN",))
    with pytest.raises(ValueError, match="unsupported identifiers"):
        replace(receipt, invariants=("not a valid identifier",))
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        replace(receipt, risk_fingerprint="not-a-fingerprint")
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        replace(receipt, risk_fingerprint="x" * 63)
    with pytest.raises(TypeError, match="DaggerDecision"):
        replace(receipt, dagger_decision=object())
    with pytest.raises(TypeError, match="exact booleans"):
        replace(receipt, authority_expansion=1)
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_REQUIRED_ASSURANCE_MISSING):
        replace(receipt, selected_specialists=("scribe",))
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_REQUIRED_ASSURANCE_MISSING):
        replace(receipt, required_assurance=("FUNCTIONAL_ASSURANCE",))
    with pytest.raises(ValueError, match="selected explicitly"):
        replace(receipt, coordination_additions=("weaver",))
    with pytest.raises(ValueError, match="required explicitly"):
        replace(receipt, assurance_additions=("FUNCTIONAL_ASSURANCE",))
    with pytest.raises(ValueError, match="authority_boundary"):
        replace(receipt, authority_boundary=())
    with pytest.raises(ValueError, match="unsupported AQ3"):
        replace(receipt, schema_version="other.v1")
    with pytest.raises(TypeError, match="SpecialistAssuranceReceipt"):
        validate_routing_receipt(object())
    with pytest.raises(TypeError, match="AdaptiveRiskProfile"):
        validate_routing_receipt(receipt, object())
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_WRONG_SOURCE_EVIDENCE):
        validate_routing_receipt(receipt, replace(profile, changed_domains=("different",)))
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        validate_routing_receipt(
            replace(receipt, selected_specialists=receipt.selected_specialists + ("weaver",)),
            profile,
        )
    with pytest.raises(SpecialistAssuranceContractError, match=FAIL_AUTHORITY_SCOPE_VIOLATION):
        validate_routing_receipt(
            replace(receipt, required_assurance=receipt.required_assurance + ("FUNCTIONAL_ASSURANCE",)),
            profile,
        )


def test_evidence_and_review_edges_fail_closed() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    with pytest.raises(TypeError, match="must be a string"):
        SpecialistAssuranceEvidence(
            evidence_id=1,
            assurance_class="INDEPENDENT_QA",
            producer="ponytail",
            validator="overseer",
            source_identity=SOURCE,
        )
    with pytest.raises(ValueError, match="must be non-empty"):
        SpecialistAssuranceEvidence(
            evidence_id="",
            assurance_class="INDEPENDENT_QA",
            producer="ponytail",
            validator="overseer",
            source_identity=SOURCE,
        )
    with pytest.raises(ValueError, match="exceeds 256"):
        SpecialistAssuranceEvidence(
            evidence_id="x" * 257,
            assurance_class="INDEPENDENT_QA",
            producer="ponytail",
            validator="overseer",
            source_identity=SOURCE,
        )
    with pytest.raises(ValueError, match="unsupported"):
        _evidence(receipt, "INDEPENDENT_QA", status="UNKNOWN")
    with pytest.raises(ValueError, match="unsupported"):
        _evidence(receipt, "INDEPENDENT_QA", scope="UNKNOWN")
    with pytest.raises(TypeError, match="mapping"):
        SpecialistAssuranceEvidence.from_mapping([])
    evidence = _evidence(receipt, "INDEPENDENT_QA", evidence_id="mapped")
    assert SpecialistAssuranceEvidence.from_mapping(evidence.to_dict()) == evidence
    with pytest.raises(TypeError, match="iterable"):
        assess_overseer_review(receipt, SOURCE)
    with pytest.raises(TypeError, match="contain SpecialistAssuranceEvidence"):
        assess_overseer_review(receipt, [object()])
    with pytest.raises(TypeError, match="exact booleans"):
        from orchestra_runtime.domain.adaptive import OverseerAssuranceReview

        OverseerAssuranceReview("overseer", 1, False, (), ())
    with pytest.raises(TypeError, match="iterable"):
        from orchestra_runtime.domain.adaptive import OverseerAssuranceReview

        OverseerAssuranceReview("overseer", False, False, "evidence", ())
    with pytest.raises(ValueError, match="exceeds 128"):
        from orchestra_runtime.domain.adaptive import OverseerAssuranceReview

        OverseerAssuranceReview("overseer", False, False, tuple(f"id:{index}" for index in range(129)), ())


def test_evidence_status_provenance_binding_and_special_scope_edges() -> None:
    profile = _profile()
    receipt = _receipt(profile)
    wrong_status = _evidence(
        receipt,
        "INDEPENDENT_QA",
        evidence_id="wrong-status",
        source_identity="wrong:source",
        status="WRONG_SOURCE",
    )
    inferred = _evidence(receipt, "INDEPENDENT_QA", evidence_id="inferred", source_truth="INFERRED")
    unqualified = _evidence(
        receipt,
        "INDEPENDENT_QA",
        evidence_id="unqualified",
        provenance_qualification="SELF_ASSERTED",
    )
    inconsistent = replace(
        _evidence(receipt, "INDEPENDENT_QA", evidence_id="inconsistent"),
        candidate_ref="other-candidate",
    )
    review = assess_overseer_review(receipt, [wrong_status, inferred, unqualified, inconsistent])
    assert FAIL_WRONG_SOURCE_EVIDENCE in review.failure_codes
    assert FAIL_SOURCE_TRUTH_VIOLATION in review.failure_codes
    assert "FAIL_EVIDENCE_PROVENANCE" in review.failure_codes
    assert "FAIL_EVIDENCE_BINDING" in review.failure_codes

    security_profile = _profile(
        material_behavior="authorization security behavior",
        risk_characteristics=("AUTHENTICATION",),
        quality_dimensions=("SECURITY",),
    )
    security_receipt = _receipt(security_profile)
    ci_security = _evidence(
        security_receipt,
        "SECURITY_ASSURANCE",
        evidence_id="ci-security",
        kind="CI",
        scope="SECURITY",
    )
    security_review = assess_overseer_review(security_receipt, [ci_security])
    assert FAIL_REQUIRED_ASSURANCE_MISSING in security_review.failure_codes

    concurrency_profile = _profile(risk_characteristics=("CONCURRENCY",))
    concurrency_receipt = _receipt(concurrency_profile)
    weak_scope = _evidence(
        concurrency_receipt,
        "CONCURRENCY_ASSURANCE",
        evidence_id="weak-scope",
        scope="CONTRACT",
    )
    assert FAIL_REQUIRED_ASSURANCE_MISSING in assess_overseer_review(concurrency_receipt, [weak_scope]).failure_codes


def test_arbiter_handles_invalid_claim_and_aggregate_row_evidence() -> None:
    profile = _profile(risk_characteristics=("AGGREGATE_INVARIANT",))
    receipt = _receipt(profile)
    evidence = [
        _evidence(
            receipt,
            "AGGREGATE_INVARIANT_ASSURANCE",
            evidence_id="row-aggregate",
            scope="ROW_VERSION",
        ),
    ]
    review = assess_overseer_review(receipt, evidence)
    invalid = evaluate_arbiter_progression(
        receipt,
        evidence,
        claimed_completion_state="NOT_A_STATE",
        overseer_review=review,
    )
    assert invalid.disposition == "BLOCK"
    assert REQUIRE_AGGREGATE_CONCURRENCY_ANALYSIS in invalid.failure_codes
    assert FAIL_AQ1_COMPLETION_SCOPE in invalid.failure_codes
