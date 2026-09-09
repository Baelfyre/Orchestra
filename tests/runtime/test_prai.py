from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.domain.adaptive import prai


REPOSITORY = "Baelfyre/Orchestra"
SOURCE_REF = "5454e643745cb1b1ab16b233dd6ad36d08bcb9f2"
CANDIDATE_SHA = "a" * 40
TREE_SHA = "b" * 40
WORK_ITEM = "prai-implementation"
FRESHNESS = "2026-09-09T00:00:00Z"
VERSION = "orchestra-prai-plan-20260908-v1"
CODE_PATHS = (
    "tests/runtime/test_prai.py",
    "tests/behavior/test_prai.py",
)


def receipt(
    role: str,
    *,
    candidate_sha: str = CANDIDATE_SHA,
    tree_sha: str = TREE_SHA,
    result: str = "PASS",
    reviewer: str | None = None,
    producer: str = "independent-review",
    independent: bool = True,
    evidence_refs: tuple[str, ...] | None = None,
    audited_paths: tuple[str, ...] = CODE_PATHS,
    audit_depth: str = "STANDARD",
    provenance: str = "AUTHORITATIVE",
    security_classification: str | None = None,
    logical_identity: str | None = None,
    examined_changed_code: bool = True,
    covered_risks: tuple[str, ...] | None = None,
    covered_invariants: tuple[str, ...] | None = None,
) -> prai.PraiReviewReceipt:
    evidence_refs = evidence_refs or (f"evidence://{role.lower()}",)
    return prai.PraiReviewReceipt(
        receipt_id=f"{role.lower()}-receipt",
        role=role,
        reviewer=reviewer or f"{role.lower()}-reviewer",
        result=result,
        repository=REPOSITORY,
        source_ref=SOURCE_REF,
        candidate_sha=candidate_sha,
        tree_sha=tree_sha,
        work_item_ref=WORK_ITEM,
        audit_depth=audit_depth,
        evidence_refs=evidence_refs,
        audited_paths=audited_paths,
        evidence_layer="specialist-review",
        evidence_scope="UNIT",
        covered_risks=covered_risks or (),
        covered_invariants=covered_invariants or (),
        freshness_ref=FRESHNESS,
        version_ref=VERSION,
        provenance=provenance,
        independent=independent,
        producer=producer,
        validator=f"{role.lower()}-validator",
        claim_scope="UNIT",
        limitations=("bounded to this work unit",),
        examined_changed_code=examined_changed_code,
        security_classification=security_classification,
        logical_identity=logical_identity,
    )


def roles_for(risks: tuple[str, ...]) -> tuple[str, ...]:
    return prai.BASELINE_REVIEWERS + prai.triggered_reviewers(risks)


def assurances_for(risks: tuple[str, ...]) -> tuple[str, ...]:
    return prai.BASELINE_ASSURANCE + tuple(
        f"{role}_ASSURANCE" for role in prai.triggered_reviewers(risks)
    )


def make_unit(
    *,
    risks: tuple[str, ...] = (),
    audit_depth: str = "STANDARD",
    receipt_depth: str | None = None,
    receipt_roles: tuple[str, ...] | None = None,
    changed_paths: tuple[str, ...] = CODE_PATHS,
    logical_impact: str = "LOW",
    security_impact: str = "LOW",
    security_classification: str | None = None,
    invariants: tuple[str, ...] = ("candidate-bound-evidence",),
) -> prai.PraiWorkUnit:
    roles = roles_for(risks)
    refs = tuple(f"evidence://{role.lower()}" for role in roles)
    selected_roles = receipt_roles or roles
    receipts = tuple(
        receipt(
            role,
            audit_depth=receipt_depth or audit_depth,
            audited_paths=changed_paths,
            evidence_refs=(f"evidence://{role.lower()}",),
            security_classification=(
                prai.SECURITY_NO_MATERIAL_IMPACT
                if security_impact == "NONE" and role == "CIPHER"
                else None
            ),
            covered_risks=risks,
            covered_invariants=invariants,
        )
        for role in selected_roles
    )
    return prai.PraiWorkUnit(
        work_item_ref=WORK_ITEM,
        repository=REPOSITORY,
        source_ref=SOURCE_REF,
        candidate_sha=CANDIDATE_SHA,
        tree_sha=TREE_SHA,
        freshness_ref=FRESHNESS,
        changed_paths=changed_paths,
        implementer="ponytail",
        logical_impact=logical_impact,
        security_impact=security_impact,
        audit_depth=audit_depth,
        required_reviewers=roles,
        required_additional_assurance=assurances_for(risks),
        logical_result="PASS",
        security_result="PASS",
        evidence_refs=refs,
        limitations=("PRAI is evidence-only",),
        overseer_sufficiency=True,
        arbiter_disposition="AUTO_CONTINUE",
        review_receipts=receipts,
        risk_characteristics=risks,
        invariants=invariants,
        green_tests=True,
        security_classification=security_classification,
    )


def clone(unit: prai.PraiWorkUnit, **changes: object) -> prai.PraiWorkUnit:
    data = unit.to_dict(include_digest=False)
    for key, value in changes.items():
        if key == "review_receipts":
            data[key] = [
                item.to_dict() if isinstance(item, prai.PraiReviewReceipt) else item
                for item in value  # type: ignore[union-attr]
            ]
        elif isinstance(value, tuple):
            data[key] = list(value)
        else:
            data[key] = value
    return prai.PraiWorkUnit.from_mapping(data)


def evaluate(unit: prai.PraiWorkUnit, **overrides: str | None) -> prai.PraiDecision:
    current: dict[str, str | None] = {
        "current_repository": REPOSITORY,
        "current_source_ref": SOURCE_REF,
        "current_candidate_sha": CANDIDATE_SHA,
        "current_tree_sha": TREE_SHA,
        "current_work_item_ref": WORK_ITEM,
        "current_freshness_ref": FRESHNESS,
    }
    current.update(overrides)
    return prai.evaluate_post_run_assurance(unit, **current)


def blocked(unit: prai.PraiWorkUnit, *codes: str) -> None:
    decision = evaluate(unit)
    assert decision.result == "BLOCKED"
    assert set(codes).issubset(decision.failure_codes)


def replace_receipt(receipt_value: prai.PraiReviewReceipt, **changes: object) -> prai.PraiReviewReceipt:
    data = receipt_value.to_dict(include_digest=False)
    data.update(changes)
    return prai.PraiReviewReceipt.from_mapping(data)


def test_current_standard_unit_passes_and_round_trips() -> None:
    unit = make_unit()
    decision = evaluate(unit)
    assert decision.result == "PASS"
    assert decision.compliant is True
    assert decision.authority_model == prai.PRAI_AUTHORITY_MODEL
    assert decision.authority_expansion is False
    assert prai.PraiWorkUnit.from_mapping(unit.to_dict()) == unit
    assert prai.PraiDecision.from_mapping(decision.to_dict()) == decision


def test_explicit_light_docs_pass_and_security_is_classified() -> None:
    unit = make_unit(
        audit_depth="LIGHT",
        receipt_depth="LIGHT",
        changed_paths=("CHANGELOG.md",),
        logical_impact="NONE",
        security_impact="NONE",
        security_classification=prai.SECURITY_NO_MATERIAL_IMPACT,
    )
    assert evaluate(unit).result == "PASS"
    assert prai.required_audit_depth(unit) == "LIGHT"


def test_depth_and_triggered_reviewers_are_adaptive() -> None:
    assert prai.required_audit_depth(make_unit()) == "STANDARD"
    assert prai.required_audit_depth(
        make_unit(
            changed_paths=("CHANGELOG.md",),
            logical_impact="NONE",
            security_impact="NONE",
            security_classification=prai.SECURITY_NO_MATERIAL_IMPACT,
        )
    ) == "LIGHT"
    assert prai.required_audit_depth(
        make_unit(logical_impact="MEDIUM")
    ) == "DEEP"
    deep = make_unit(risks=("AUTHORIZATION", "CONCURRENCY"), audit_depth="DEEP")
    assert prai.required_audit_depth(deep) == "DEEP"
    assert prai.triggered_reviewers(("AUTHORIZATION", "CONCURRENCY")) == (
        "CHRONICLER",
        "DAGGER",
    )


def test_contract_and_schema_match_runtime() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = json.loads(
        (root / "machine" / "adaptive" / "prai-post-run-assurance.v1.json").read_text(
            encoding="utf-8"
        )
    )
    schema = json.loads(
        (root / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert prai.validate_prai_contract(contract)["schema_version"] == prai.PRAI_CONTRACT_SCHEMA_VERSION
    assert prai.validate_schema_runtime_parity(contract, schema)["schema_version"] == prai.PRAI_CONTRACT_SCHEMA_VERSION
    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(make_unit().to_dict())



def test_schema_runtime_parity_rejects_scope_and_identity_drift() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = json.loads(
        (root / "machine" / "adaptive" / "prai-post-run-assurance.v1.json").read_text(
            encoding="utf-8"
        )
    )
    schema_path = root / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["$defs"]["receipt"]["properties"]["evidence_scope"]["enum"] = ["UNIT"]
    with pytest.raises(ValueError, match=prai.FAIL_SCHEMA_RUNTIME_PARITY):
        prai.validate_schema_runtime_parity(contract, schema)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["$defs"]["receipt"]["properties"]["logical_identity"]["pattern"] = ".*"
    with pytest.raises(ValueError, match=prai.FAIL_SCHEMA_RUNTIME_PARITY):
        prai.validate_schema_runtime_parity(contract, schema)


@pytest.mark.parametrize(
    ("name", "unit", "codes"),
    [
        (
            "green tests with contradictory logical invariant",
            clone(make_unit(), logical_findings=("invariant contradiction",)),
            (prai.FAIL_LOGICAL_CONTRADICTION,),
        ),
        (
            "security-sensitive work without Cipher",
            make_unit(receipt_roles=("CLOCKWORK", "OVERSEER")),
            (prai.FAIL_REQUIRED_SECURITY_ASSURANCE, prai.FAIL_REQUIRED_REVIEWER),
        ),
        (
            "implementer self certification",
            clone(
                make_unit(),
                review_receipts=(
                    receipt("CLOCKWORK", reviewer="ponytail", producer="ponytail"),
                    receipt("CIPHER"),
                    receipt("OVERSEER"),
                ),
            ),
            (prai.FAIL_IMPLEMENTER_SELF_CERTIFICATION, prai.FAIL_NON_INDEPENDENT_EVIDENCE),
        ),
        (
            "stale candidate receipt",
            clone(
                make_unit(),
                review_receipts=(
                    receipt("CLOCKWORK", candidate_sha="c" * 40),
                    receipt("CIPHER"),
                    receipt("OVERSEER"),
                ),
            ),
            (prai.FAIL_STALE_CANDIDATE, prai.FAIL_EVIDENCE_BINDING),
        ),
        (
            "stale tree receipt",
            clone(
                make_unit(),
                review_receipts=(
                    receipt("CLOCKWORK", tree_sha="c" * 40),
                    receipt("CIPHER"),
                    receipt("OVERSEER"),
                ),
            ),
            (prai.FAIL_STALE_TREE, prai.FAIL_EVIDENCE_BINDING),
        ),
        (
            "light for deep trigger",
            make_unit(risks=("AUTHORIZATION",), audit_depth="LIGHT", receipt_depth="LIGHT"),
            (prai.FAIL_REQUIRED_AUDIT_DEPTH,),
        ),
        (
            "security none without classification",
            clone(
                make_unit(logical_impact="NONE", security_impact="NONE"),
                security_classification=None,
                review_receipts=tuple(
                    replace_receipt(item, security_classification=None)
                    for item in make_unit(logical_impact="NONE", security_impact="NONE").review_receipts
                ),
            ),
            (prai.FAIL_SECURITY_CLASSIFICATION,),
        ),
        (
            "broken caller contract",
            clone(make_unit(), caller_contract_issues=("caller mismatch",)),
            (prai.FAIL_CALLER_CONTRACT,),
        ),
        (
            "tenant to global authority expansion",
            clone(make_unit(), authority_expansion=True),
            (prai.FAIL_AUTHORITY_EXPANSION,),
        ),
        (
            "missing Chronicler assurance",
            make_unit(
                risks=("CONCURRENCY",),
                audit_depth="DEEP",
                receipt_depth="DEEP",
                receipt_roles=("CLOCKWORK", "CIPHER", "OVERSEER", "DAGGER"),
            ),
            (prai.FAIL_TRIGGERED_SPECIALIST,),
        ),
        (
            "missing Dagger assurance",
            make_unit(
                risks=("AUTHORIZATION",),
                audit_depth="DEEP",
                receipt_depth="DEEP",
                receipt_roles=("CLOCKWORK", "CIPHER", "OVERSEER"),
            ),
            (prai.FAIL_TRIGGERED_SPECIALIST,),
        ),
        (
            "audit does not examine changed code",
            clone(
                make_unit(),
                review_receipts=tuple(
                    replace_receipt(item, examined_changed_code=False)
                    for item in make_unit().review_receipts
                ),
            ),
            (prai.FAIL_CHANGED_CODE_UNEXAMINED,),
        ),
        (
            "generic green CI substitution",
            clone(
                make_unit(),
                evidence_refs=(
                    "evidence://clockwork",
                    "evidence://cipher",
                    "evidence://overseer",
                    "evidence://ci",
                ),
                review_receipts=make_unit().review_receipts + (receipt("CI"),),
            ),
            (prai.FAIL_GENERIC_CI_SUBSTITUTION,),
        ),
        (
            "self-modifying PRAI policy",
            clone(make_unit(), policy_self_modification=True),
            (prai.FAIL_POLICY_SELF_MODIFICATION,),
        ),
    ],
)
def test_required_negative_fixtures(
    name: str, unit: prai.PraiWorkUnit, codes: tuple[str, ...]
) -> None:
    assert name
    blocked(unit, *codes)


def test_stale_candidate_and_tree_current_identity_block() -> None:
    candidate = evaluate(make_unit(), current_candidate_sha="c" * 40)
    assert candidate.result == "BLOCKED"
    assert prai.FAIL_STALE_CANDIDATE in candidate.failure_codes
    tree = evaluate(make_unit(), current_tree_sha="c" * 40)
    assert tree.result == "BLOCKED"
    assert prai.FAIL_STALE_TREE in tree.failure_codes
    missing = prai.evaluate_post_run_assurance(make_unit())
    assert prai.FAIL_CURRENT_IDENTITY_REQUIRED in missing.failure_codes
    invalid = evaluate(make_unit(), current_candidate_sha="not-a-sha")
    assert prai.FAIL_STALE_CANDIDATE in invalid.failure_codes


def test_stale_audit_reuse_after_repair_is_bound_to_new_candidate() -> None:
    repaired = clone(make_unit(), candidate_sha="c" * 40)
    decision = evaluate(repaired)
    assert decision.result == "BLOCKED"
    assert prai.FAIL_STALE_CANDIDATE in decision.failure_codes
    assert prai.FAIL_EVIDENCE_BINDING in decision.failure_codes


def test_contradictory_and_duplicate_receipts_are_order_invariant() -> None:
    base = make_unit()
    shared = base.review_receipts[0].logical_identity
    conflict_data = base.review_receipts[0].to_dict(include_digest=False)
    conflict_data.update(
        {
            "receipt_id": "clockwork-conflict",
            "result": "FAIL",
            "logical_identity": shared,
        }
    )
    conflict = prai.PraiReviewReceipt.from_mapping(conflict_data)
    conflicted = clone(
        base,
        review_receipts=base.review_receipts + (conflict,),
    )
    first = evaluate(conflicted)
    second = evaluate(
        clone(conflicted, review_receipts=tuple(reversed(conflicted.review_receipts)))
    )
    assert prai.FAIL_CONTRADICTORY_RECEIPT in first.failure_codes
    assert first.to_dict() == second.to_dict()

    duplicate_data = base.review_receipts[0].to_dict(include_digest=False)
    duplicate_data.update(
        {
            "receipt_id": "clockwork-duplicate",
            "logical_identity": shared,
        }
    )
    duplicate = prai.PraiReviewReceipt.from_mapping(duplicate_data)
    duplicated = clone(
        base,
        review_receipts=base.review_receipts + (duplicate,),
    )
    blocked(duplicated, prai.FAIL_DUPLICATE_RECEIPT)


def test_unqualified_independence_and_failed_results_block() -> None:
    base = make_unit()
    unit = clone(
        base,
        review_receipts=(
            receipt("CLOCKWORK", independent=False),
            receipt("CIPHER", result="FAIL"),
            base.review_receipts[2],
        ),
    )
    decision = evaluate(unit)
    assert decision.result == "BLOCKED"
    assert prai.FAIL_NON_INDEPENDENT_EVIDENCE in decision.failure_codes
    assert prai.FAIL_INVALID_RECEIPT_RESULT in decision.failure_codes
    assert prai.FAIL_REQUIRED_LOGICAL_ASSURANCE in decision.failure_codes
    assert prai.FAIL_REQUIRED_SECURITY_ASSURANCE in decision.failure_codes


def test_scope_and_receipt_identity_binding_block() -> None:
    base = make_unit()
    out_of_scope = receipt("CLOCKWORK", evidence_refs=("evidence://not-declared",))
    mismatch_data = base.review_receipts[1].to_dict(include_digest=False)
    mismatch_data.update(
        {
            "receipt_id": "cipher-mismatch",
            "work_item_ref": "different-work",
            "evidence_refs": ["evidence://cipher"],
            "logical_identity": None,
        }
    )
    mismatch = prai.PraiReviewReceipt.from_mapping(mismatch_data)
    blocked(
        clone(
            base,
            review_receipts=(out_of_scope, mismatch, base.review_receipts[2]),
        ),
        prai.FAIL_SCOPE_EXCEEDED,
        prai.FAIL_EVIDENCE_BINDING,
    )


def test_policy_and_security_findings_block() -> None:
    blocked(
        clone(make_unit(), policy_modified_paths=("machine/policy.json",)),
        prai.FAIL_POLICY_SELF_MODIFICATION,
    )
    blocked(
        clone(make_unit(), security_findings=("security finding",)),
        prai.FAIL_SECURITY_FINDING,
    )
    blocked(
        clone(make_unit(), security_result="FAIL"),
        prai.FAIL_SECURITY_FINDING,
    )


def test_aliases_strict_fields_and_digests() -> None:
    base = make_unit()
    receipt_data = base.review_receipts[0].to_dict()
    assert prai.PraiReviewReceipt.from_mapping(receipt_data).role == "CLOCKWORK"
    receipt_data["review_type"] = receipt_data.pop("role")
    with pytest.raises(ValueError):
        prai.PraiReviewReceipt.from_mapping(receipt_data)
    with pytest.raises(ValueError):
        prai.PraiReviewReceipt.from_mapping({**base.review_receipts[0].to_dict(), "unexpected": True})
    with pytest.raises(ValueError):
        prai.PraiReviewReceipt.from_mapping(
            {**base.review_receipts[0].to_dict(), "digest": "0" * 64}
        )

    work_data = base.to_dict(include_digest=False)
    assert prai.PraiWorkUnit.from_mapping(work_data).work_item_ref == WORK_ITEM
    alias_data = base.to_dict(include_digest=False)
    alias_data["receipts"] = alias_data.pop("review_receipts")
    with pytest.raises(ValueError):
        prai.PraiWorkUnit.from_mapping(alias_data)
    alias_data = base.to_dict(include_digest=False)
    alias_data["current_freshness"] = alias_data.pop("freshness_ref")
    with pytest.raises(ValueError):
        prai.PraiWorkUnit.from_mapping(alias_data)
    missing = base.to_dict(include_digest=False)
    missing.pop("authority_boundary")
    with pytest.raises(ValueError):
        prai.PraiWorkUnit.from_mapping(missing)
    with pytest.raises(ValueError):
        prai.PraiWorkUnit.from_mapping({**base.to_dict(), "unexpected": True})
    with pytest.raises(TypeError):
        prai.PraiWorkUnit.from_mapping("not-a-mapping")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        prai.PraiReviewReceipt.from_mapping(
            {**base.review_receipts[0].to_dict(), "role": "UNKNOWN"}
        )


def test_schema_and_runtime_reject_divergent_shapes() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    from jsonschema import Draft202012Validator, ValidationError

    validator = Draft202012Validator(schema)
    canonical = make_unit().to_dict()
    without_digest = dict(canonical)
    without_digest.pop("digest")
    validator.validate(without_digest)
    assert prai.PraiWorkUnit.from_mapping(without_digest).digest
    missing = dict(without_digest)
    missing.pop("authority_boundary")
    with pytest.raises(ValidationError):
        validator.validate(missing)
    with pytest.raises(ValueError):
        prai.PraiWorkUnit.from_mapping(missing)
    invalid_type = dict(without_digest)
    invalid_type["green_tests"] = "true"
    with pytest.raises(ValidationError):
        validator.validate(invalid_type)
    with pytest.raises((TypeError, ValueError)):
        prai.PraiWorkUnit.from_mapping(invalid_type)


def test_unknown_risk_characteristics_fail_closed() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    from jsonschema import Draft202012Validator, ValidationError

    data = make_unit().to_dict()
    data["risk_characteristics"] = ["AUTHORIZATON"]
    with pytest.raises(ValueError, match=prai.FAIL_UNKNOWN_RISK_CHARACTERISTIC):
        prai.PraiWorkUnit.from_mapping(data)
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(data)
    with pytest.raises(ValueError, match=prai.FAIL_UNKNOWN_RISK_CHARACTERISTIC):
        prai.triggered_reviewers(("AUTHORIZATON",))


def test_noncanonical_known_risk_case_fails_closed() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    from jsonschema import Draft202012Validator, ValidationError

    data = make_unit().to_dict()
    data["risk_characteristics"] = ["authorization"]
    with pytest.raises(ValueError, match=prai.FAIL_UNKNOWN_RISK_CHARACTERISTIC):
        prai.PraiWorkUnit.from_mapping(data)
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(data)


def test_evidence_scope_must_cover_claim_scope() -> None:
    data = make_unit().review_receipts[0].to_dict(include_digest=False)
    data["evidence_scope"] = "UNIT"
    data["claim_scope"] = "INTEGRATION"
    data["logical_identity"] = None
    with pytest.raises(ValueError, match=prai.FAIL_EVIDENCE_SCOPE):
        prai.PraiReviewReceipt.from_mapping(data)


def test_logical_identity_cannot_be_spoofed() -> None:
    data = make_unit().review_receipts[0].to_dict(include_digest=False)
    data["logical_identity"] = "f" * 64
    with pytest.raises(ValueError, match=prai.FAIL_LOGICAL_IDENTITY):
        prai.PraiReviewReceipt.from_mapping(data)


def test_protected_prai_path_derives_self_modification() -> None:
    unit = make_unit(changed_paths=("orchestra_runtime/domain/adaptive/prai.py",))
    assert unit.policy_self_modification is False
    assert unit.policy_modified_paths == ()
    blocked(unit, prai.FAIL_POLICY_SELF_MODIFICATION)


def test_pass_receipts_must_cover_all_claimed_dimensions() -> None:
    unit = make_unit(risks=("AUTHORIZATION",))
    cases = (
        {"audited_paths": (CODE_PATHS[0],)},
        {"covered_risks": ()},
        {"covered_invariants": ()},
        {"covered_risks": ("CONCURRENCY",)},
    )
    for changes in cases:
        changed_receipts = list(unit.review_receipts)
        changed_receipts[0] = replace_receipt(
            changed_receipts[0], **changes
        )
        blocked(
            clone(unit, review_receipts=tuple(changed_receipts)),
            prai.FAIL_ASSURANCE_COVERAGE,
        )


def test_satisfied_evidence_and_decision_digest_are_deterministic() -> None:
    unit = make_unit()
    first = evaluate(unit, generated_at=FRESHNESS)
    second = evaluate(
        clone(unit, review_receipts=tuple(reversed(unit.review_receipts))),
        generated_at=FRESHNESS,
    )
    assert first.evidence_receipt_ids == (
        "cipher-receipt",
        "clockwork-receipt",
        "overseer-receipt",
    )
    assert first.satisfied_reviewers == first.required_reviewers
    assert first.satisfied_additional_assurance == first.required_additional_assurance
    assert first.decision_digest == second.decision_digest


def test_security_classification_is_explicit() -> None:
    none = make_unit(
        changed_paths=("CHANGELOG.md",),
        logical_impact="NONE",
        security_impact="NONE",
        security_classification=prai.SECURITY_NO_MATERIAL_IMPACT,
        audit_depth="LIGHT",
        receipt_depth="LIGHT",
    )
    assert evaluate(none).result == "PASS"
    assert receipt("CIPHER").security_classification is None
