"""Deterministic OR-GOV-7 ArchitectureValidationContract checks."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.evaluation import (
    VALIDATION_DIMENSIONS,
    evaluate_architecture_validation,
)


SCHEMA = ROOT / "machine" / "schemas" / "architecture-validation-contract.v1.schema.json"
REFS = ("contract:product:rev-1", "contract:capacity:rev-1")
REVISION = "subject:revision-1"
ENVIRONMENT = "staging:runner-ubuntu-24.04"


def _obligations(required: dict[str, tuple[str, ...]] | None = None) -> dict[str, dict[str, Any]]:
    required = required or {}
    return {
        dimension: {
            "applicability": "REQUIRED" if dimension in required else "NOT_REQUIRED",
            **({"criteria": list(required[dimension])} if dimension in required else {}),
        }
        for dimension in VALIDATION_DIMENSIONS
    }


def _evidence(
    evidence_ref: str,
    dimension: str,
    criteria: tuple[str, ...],
    proof_state: str = "PROVEN",
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "evidence_ref": evidence_ref,
        "dimension": dimension,
        "criteria": list(criteria),
        "proof_state": proof_state,
        "contract_refs": list(REFS),
        "exact_revision": REVISION,
        "environment_identity": ENVIRONMENT,
        **overrides,
    }


def _evaluate(
    required: dict[str, tuple[str, ...]],
    evidence: list[dict[str, Any]] | None = None,
    *,
    limitations: tuple[str, ...] = (),
) -> dict[str, Any]:
    return evaluate_architecture_validation(
        contract_refs=REFS,
        exact_revision=REVISION,
        environment_identity=ENVIRONMENT,
        obligations=_obligations(required),
        evidence=evidence or [],
        limitations=limitations,
    )


def test_t1_proven_functional_requirement_requires_matching_current_evidence() -> None:
    result = _evaluate(
        {"functional_validation": ("acceptance:create-report",)},
        [_evidence("test:functional", "functional_validation", ("acceptance:create-report",))],
    )
    assert result["functional_validation"] == "PROVEN"


def test_t2_required_validation_not_run_is_not_proven() -> None:
    result = _evaluate({"functional_validation": ("acceptance:create-report",)})
    assert result["functional_validation"] == "NOT_PROVEN"


def test_t3_executed_requirement_failure_is_failed() -> None:
    result = _evaluate(
        {"functional_validation": ("acceptance:create-report",)},
        [_evidence("test:functional-fail", "functional_validation", ("acceptance:create-report",), "FAILED")],
    )
    assert result["functional_validation"] == "FAILED"


def test_t4_irrelevant_dimension_is_not_required() -> None:
    result = _evaluate({})
    assert result["tenant_isolation_validation"] == "NOT_REQUIRED"


def test_t5_unknown_capacity_target_remains_not_proven_without_invented_target() -> None:
    result = _evaluate(
        {"capacity_validation": ("accepted-capacity-target:UNKNOWN",)},
        limitations=("capacity target is UNKNOWN; measurement is required",),
    )
    assert result["capacity_validation"] == "NOT_PROVEN"
    assert "200" not in json.dumps(result)


def test_t6_exact_capacity_benchmark_can_prove_only_its_accepted_criterion() -> None:
    result = _evaluate(
        {"capacity_validation": ("sustained-rps:300",)},
        [_evidence("benchmark:300-rps", "capacity_validation", ("sustained-rps:300",))],
    )
    assert result["capacity_validation"] == "PROVEN"


def test_t7_benchmark_below_accepted_target_is_failed() -> None:
    result = _evaluate(
        {"capacity_validation": ("sustained-rps:300",)},
        [_evidence("benchmark:180-rps", "capacity_validation", ("sustained-rps:300",), "FAILED")],
    )
    assert result["capacity_validation"] == "FAILED"


def test_t8_wrong_revision_cannot_prove_current_subject_and_history_is_retained() -> None:
    result = _evaluate(
        {"capacity_validation": ("sustained-rps:300",)},
        [_evidence("benchmark:old-revision", "capacity_validation", ("sustained-rps:300",), exact_revision="subject:revision-0")],
    )
    assert result["capacity_validation"] == "NOT_PROVEN"
    assert result["evidence_refs"] == ["benchmark:old-revision"]
    assert result["limitations"]


def test_t9_wrong_environment_cannot_prove_current_claim() -> None:
    result = _evaluate(
        {"performance_validation": ("p95-latency:accepted",)},
        [_evidence("benchmark:other-env", "performance_validation", ("p95-latency:accepted",), environment_identity="ci:runner")],
    )
    assert result["performance_validation"] == "NOT_PROVEN"


def test_t10_test_environment_crash_is_not_proven_not_product_failure() -> None:
    result = _evaluate(
        {"performance_validation": ("p95-latency:accepted",)},
        [_evidence(
            "benchmark:crashed-runner",
            "performance_validation",
            ("p95-latency:accepted",),
            "NOT_PROVEN",
            limitation="runner crashed before workload execution",
        )],
    )
    assert result["performance_validation"] == "NOT_PROVEN"
    assert result["performance_validation"] != "FAILED"


def test_t11_scale_ready_without_capacity_claim_needs_no_arbitrary_load_test() -> None:
    result = _evaluate({})
    assert result["capacity_validation"] == "NOT_REQUIRED"
    assert result["performance_validation"] == "NOT_REQUIRED"


def test_t12_scale_provisioned_target_requires_outcome_evidence_not_presence_only() -> None:
    result = _evaluate(
        {
            "capacity_validation": ("accepted-concurrency:50000",),
            "performance_validation": ("saturation-envelope:accepted",),
        },
        [_evidence("deployment:worker-present", "capacity_validation", ("accepted-concurrency:50000",), "NOT_PROVEN")],
    )
    assert result["capacity_validation"] == "NOT_PROVEN"
    assert result["performance_validation"] == "NOT_PROVEN"


def test_t13_incomplete_migration_backfill_is_failed_when_completion_is_required() -> None:
    result = _evaluate(
        {"migration_validation": ("backfill:100-percent",)},
        [_evidence("migration:backfill-92-percent", "migration_validation", ("backfill:100-percent",), "FAILED")],
    )
    assert result["migration_validation"] == "FAILED"


def test_t14_successful_command_without_completion_validation_is_not_proven() -> None:
    result = _evaluate(
        {"migration_validation": ("backfill:100-percent",)},
        [_evidence(
            "migration:cli-exit-zero",
            "migration_validation",
            ("backfill:100-percent",),
            "NOT_PROVEN",
            limitation="command exited zero; completion query was not run",
        )],
    )
    assert result["migration_validation"] == "NOT_PROVEN"


def test_t15_cross_tenant_access_failure_is_failed() -> None:
    result = _evaluate(
        {"tenant_isolation_validation": ("unauthorized-cross-tenant-denied",)},
        [_evidence("tenant:cross-access", "tenant_isolation_validation", ("unauthorized-cross-tenant-denied",), "FAILED")],
    )
    assert result["tenant_isolation_validation"] == "FAILED"


def test_t16_no_tenant_model_is_not_required() -> None:
    assert _evaluate({})["tenant_isolation_validation"] == "NOT_REQUIRED"


def test_t17_required_failure_behavior_not_tested_is_not_proven_without_dagger() -> None:
    result = _evaluate({"failure_behavior_validation": ("retry-on-timeout",)})
    assert result["failure_behavior_validation"] == "NOT_PROVEN"


def test_t18_safe_failure_path_can_prove_failure_behavior() -> None:
    result = _evaluate(
        {"failure_behavior_validation": ("retry-on-timeout",)},
        [_evidence("test:timeout-retry", "failure_behavior_validation", ("retry-on-timeout",))],
    )
    assert result["failure_behavior_validation"] == "PROVEN"


def test_t19_stale_tuner_evidence_demotes_current_proof_without_rewriting_history() -> None:
    result = _evaluate(
        {"functional_validation": ("acceptance:create-report",)},
        [_evidence(
            "evidence:stale-contract",
            "functional_validation",
            ("acceptance:create-report",),
            evidence_status="STALE",
        )],
    )
    assert result["functional_validation"] == "NOT_PROVEN"
    assert result["evidence_refs"] == ["evidence:stale-contract"]


def test_t20_partial_criteria_remain_not_proven() -> None:
    result = _evaluate(
        {"functional_validation": ("criterion:a", "criterion:b", "criterion:c")},
        [_evidence("test:partial", "functional_validation", ("criterion:a", "criterion:b"))],
    )
    assert result["functional_validation"] == "NOT_PROVEN"


def test_t21_partial_criteria_with_one_failure_are_failed() -> None:
    result = _evaluate(
        {"functional_validation": ("criterion:a", "criterion:b", "criterion:c")},
        [
            _evidence("test:pass", "functional_validation", ("criterion:a", "criterion:b")),
            _evidence("test:fail", "functional_validation", ("criterion:c",), "FAILED"),
        ],
    )
    assert result["functional_validation"] == "FAILED"


def test_t22_capacity_ranges_are_preserved_as_criteria_not_averaged() -> None:
    result = _evaluate(
        {"capacity_validation": ("tenants:100..300",)},
        [_evidence("capacity:range", "capacity_validation", ("tenants:100..300",))],
    )
    assert result["capacity_validation"] == "PROVEN"
    assert "200" not in json.dumps(result)


def test_t23_estimated_target_without_observation_remains_not_proven() -> None:
    result = _evaluate(
        {"capacity_validation": ("storage-growth:ESTIMATED",)},
        [_evidence(
            "capacity:estimate",
            "capacity_validation",
            ("storage-growth:ESTIMATED",),
            "NOT_PROVEN",
            limitation="estimate is not observed evidence",
        )],
    )
    assert result["capacity_validation"] == "NOT_PROVEN"


def test_t24_unsupported_claim_requires_an_accepted_obligation_and_evidence() -> None:
    result = _evaluate({"capacity_validation": ("supports:millions-of-users",)})
    assert result["capacity_validation"] == "NOT_PROVEN"
    assert "million" not in json.dumps(result["evidence_refs"]).lower()


def test_schema_output_and_exact_identity_are_preserved() -> None:
    result = _evaluate(
        {"functional_validation": ("acceptance:create-report",)},
        [_evidence("test:functional", "functional_validation", ("acceptance:create-report",))],
    )
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - CI installs the schema dependency
        assert result["schema_version"] == "orchestra.architecture-validation-contract.v1"
    else:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(result)
    assert result["contract_refs"] == sorted(REFS)
    assert result["exact_revision"] == REVISION
    assert result["environment_identity"] == ENVIRONMENT


def test_fail_closed_for_missing_applicability_and_undeclared_criteria() -> None:
    incomplete = _obligations()
    del incomplete["functional_validation"]
    try:
        evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=incomplete,
            evidence=[],
        )
    except ValueError as exc:
        assert "applicability" in str(exc)
    else:
        raise AssertionError("missing applicability did not fail closed")

    try:
        _evaluate(
            {"functional_validation": ("criterion:a",)},
            [_evidence("test:undeclared", "functional_validation", ("criterion:b",))],
        )
    except ValueError as exc:
        assert "undeclared" in str(exc)
    else:
        raise AssertionError("undeclared criterion did not fail closed")


def test_fail_closed_for_malformed_contract_and_evidence_inputs() -> None:
    def expect_error(action: Any, fragment: str) -> None:
        try:
            action()
        except ValueError as exc:
            assert fragment in str(exc)
        else:
            raise AssertionError(f"expected ValueError containing {fragment!r}")

    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs="not-an-array",
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=_obligations(),
            evidence=[],
        ),
        "array of strings",
    )
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=(),
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=_obligations(),
            evidence=[],
        ),
        "must not be empty",
    )
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=("ref", "ref"),
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=_obligations(),
            evidence=[],
        ),
        "duplicate values",
    )
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision="",
            environment_identity=ENVIRONMENT,
            obligations=_obligations(),
            evidence=[],
        ),
        "exact_revision",
    )
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=[],
            evidence=[],
        ),
        "obligations must be an object",
    )

    unknown = _obligations()
    unknown["unknown_dimension"] = {"applicability": "NOT_REQUIRED"}
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=unknown,
            evidence=[],
        ),
        "unknown dimensions",
    )

    missing_record = _obligations()
    del missing_record["functional_validation"]
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=missing_record,
            evidence=[],
        ),
        "applicability",
    )

    non_mapping = _obligations()
    non_mapping["functional_validation"] = []
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=non_mapping,
            evidence=[],
        ),
        "must be an object",
    )

    invalid_applicability = _obligations()
    invalid_applicability["functional_validation"] = {"applicability": "MAYBE"}
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=invalid_applicability,
            evidence=[],
        ),
        "REQUIRED or NOT_REQUIRED",
    )

    irrelevant_criteria = _obligations()
    irrelevant_criteria["functional_validation"] = {
        "applicability": "NOT_REQUIRED",
        "criteria": ["not-allowed"],
    }
    expect_error(
        lambda: evaluate_architecture_validation(
            contract_refs=REFS,
            exact_revision=REVISION,
            environment_identity=ENVIRONMENT,
            obligations=irrelevant_criteria,
            evidence=[],
        ),
        "must not declare criteria",
    )

    expect_error(
        lambda: _evaluate({}, evidence="not-an-array"),
        "evidence must be an array",
    )
    expect_error(
        lambda: _evaluate({}, evidence=["not-an-object"]),
        "each evidence record",
    )
    expect_error(
        lambda: _evaluate(
            {"functional_validation": ("criterion",)},
            [_evidence("unknown-dimension", "unknown_dimension", ("criterion",))],
        ),
        "unknown dimension",
    )
    expect_error(
        lambda: _evaluate(
            {"functional_validation": ("criterion",)},
            [_evidence("bad-proof", "functional_validation", ("criterion",), "MAYBE")],
        ),
        "proof_state",
    )
    expect_error(
        lambda: _evaluate(
            {},
            [_evidence("irrelevant", "functional_validation", ("criterion",))],
        ),
        "NOT_REQUIRED",
    )
    expect_error(
        lambda: _evaluate(
            {"functional_validation": ("criterion",)},
            [_evidence(
                "bad-freshness",
                "functional_validation",
                ("criterion",),
                evidence_status="MAYBE",
            )],
        ),
        "evidence_status",
    )
    duplicate = _evidence("duplicate", "functional_validation", ("criterion",))
    expect_error(
        lambda: _evaluate(
            {"functional_validation": ("criterion",)},
            [duplicate, duplicate],
        ),
        "duplicate evidence_ref",
    )


def test_evaluator_has_no_execution_or_authority_dependencies() -> None:
    source = ast.parse((ROOT / "orchestra_runtime" / "domain" / "evaluation" / "architecture_validation.py").read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(source):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not imports.intersection({"subprocess", "pathlib", "os", "socket", "sqlite3"})
    assert not any(isinstance(node, ast.Name) and node.id == "open" for node in ast.walk(source))


def _run() -> None:
    tests = [
        test_t1_proven_functional_requirement_requires_matching_current_evidence,
        test_t2_required_validation_not_run_is_not_proven,
        test_t3_executed_requirement_failure_is_failed,
        test_t4_irrelevant_dimension_is_not_required,
        test_t5_unknown_capacity_target_remains_not_proven_without_invented_target,
        test_t6_exact_capacity_benchmark_can_prove_only_its_accepted_criterion,
        test_t7_benchmark_below_accepted_target_is_failed,
        test_t8_wrong_revision_cannot_prove_current_subject_and_history_is_retained,
        test_t9_wrong_environment_cannot_prove_current_claim,
        test_t10_test_environment_crash_is_not_proven_not_product_failure,
        test_t11_scale_ready_without_capacity_claim_needs_no_arbitrary_load_test,
        test_t12_scale_provisioned_target_requires_outcome_evidence_not_presence_only,
        test_t13_incomplete_migration_backfill_is_failed_when_completion_is_required,
        test_t14_successful_command_without_completion_validation_is_not_proven,
        test_t15_cross_tenant_access_failure_is_failed,
        test_t16_no_tenant_model_is_not_required,
        test_t17_required_failure_behavior_not_tested_is_not_proven_without_dagger,
        test_t18_safe_failure_path_can_prove_failure_behavior,
        test_t19_stale_tuner_evidence_demotes_current_proof_without_rewriting_history,
        test_t20_partial_criteria_remain_not_proven,
        test_t21_partial_criteria_with_one_failure_are_failed,
        test_t22_capacity_ranges_are_preserved_as_criteria_not_averaged,
        test_t23_estimated_target_without_observation_remains_not_proven,
        test_t24_unsupported_claim_requires_an_accepted_obligation_and_evidence,
        test_schema_output_and_exact_identity_are_preserved,
        test_fail_closed_for_missing_applicability_and_undeclared_criteria,
        test_fail_closed_for_malformed_contract_and_evidence_inputs,
        test_evaluator_has_no_execution_or_authority_dependencies,
    ]
    for test in tests:
        test()
    print(f"[PASS] {len(tests)} OR-GOV-7 Overseer ArchitectureValidationContract checks")


if __name__ == "__main__":
    _run()
