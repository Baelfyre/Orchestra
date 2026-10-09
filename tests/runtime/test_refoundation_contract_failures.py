import json
from pathlib import Path

import pytest

from orchestra_runtime import machine_contracts as mc
from orchestra_runtime.compliance_protocol import (
    ComplianceConsumptionReceipt,
    ComplianceExclusion,
    ComplianceQueryReceipt,
    StewardTraceabilityReceipt,
    evaluate_compliance_set_equality,
)
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    evaluate_arbiter,
)
from orchestra_runtime.models import RouteDecision, ValidationResult
from orchestra_runtime.test_evidence import main as test_evidence_main, write_test_evidence
from orchestra_runtime.workflow_contracts import WorkflowSanityReceipt, build_workflow_sanity_receipt


SHA40 = "a" * 40
SHA64 = "b" * 64


def _skill_frontmatter(slug):
    return f"""---
name: {slug}
description: fixture {slug}
slug: {slug}
role: fixture role
primary_use: fixture use
avoid_when: fixture avoid
activation_level: Specialist
depends_on: None
output_formats: [Fixture]
---
fixture
"""


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _machine_repo(tmp_path: Path):
    plugin = {
        "skills": [
            {"slug": "conductor", "skill_path": "skills/conductor/SKILL.md", "icon_path": ""},
            {"slug": "dagger", "skill_path": "skills/dagger/SKILL.md", "icon_path": ""},
        ]
    }
    _write_json(tmp_path / "plugin.json", plugin)
    for slug in ("conductor", "dagger"):
        path = tmp_path / "skills" / slug / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_skill_frontmatter(slug), encoding="utf-8")

    registry = mc.compile_specialist_registry(tmp_path)
    _write_json(tmp_path / "machine/specialists/registry.v1.json", registry)
    routing = {
        "schema_version": mc.ROUTING_CONTRACT_SCHEMA_VERSION,
        "direct_routes": [
            {"route_id": "route-conductor", "target": "conductor", "via": None},
            {"route_id": "route-dagger", "target": "dagger", "via": "conductor", "explicit_authority_required": True},
        ],
        "command_routes": {
            "conductor": {"specialist": "conductor", "route_id": "route-conductor"},
            "dagger": {"specialist": "dagger", "route_id": "route-dagger"},
        },
        "ordered_sequences": [],
        "legacy_aliases": {},
        "ambiguity_fallback": "conductor",
    }
    dispositions = [
        "AUTO_CONTINUE",
        "AUTO_REMEDIATE_AND_REVALIDATE",
        "WAIT_FOR_EVIDENCE",
        "WAIT_FOR_CAPACITY",
        "ESCALATE_HUMAN",
        "STOP",
    ]
    policy = {
        "schema_version": mc.GOVERNANCE_POLICY_SCHEMA_VERSION,
        "governance_decisions": [
            "APPROVED",
            "ADVISORY_ONLY",
            "REVISION_REQUIRED",
            "BLOCKED",
            "NOT_APPLICABLE",
        ],
        "transition_dispositions": dispositions,
        "role_ownership": {},
        "specialist_controls": {},
        "governance_required_specialists": ["dagger"],
        "runtime_validation_rules": [
            {"rule_id": "guard", "skill_slugs": ["dagger"], "command_names": ["dagger"], "validator_key": "ok"}
        ],
        "transition_precedence": [
            "STOP", "ESCALATE_HUMAN", "WAIT_FOR_CAPACITY", "WAIT_FOR_EVIDENCE",
            "AUTO_REMEDIATE_AND_REVALIDATE", "AUTO_CONTINUE",
        ],
        "compatibility_rules": {
            "APPROVED": ["AUTO_CONTINUE"],
            "ADVISORY_ONLY": ["AUTO_CONTINUE"],
            "REVISION_REQUIRED": ["AUTO_REMEDIATE_AND_REVALIDATE"],
            "BLOCKED": ["STOP"],
            "NOT_APPLICABLE": ["AUTO_CONTINUE"],
        },
        "default_remediation": {
            "maximum_remediation_attempts_per_unit": 3,
            "maximum_identical_failure_repetitions": 2,
            "maximum_scope_growth": 0,
        },
    }
    _write_json(tmp_path / "machine/routing/routes.v1.json", routing)
    _write_json(
        tmp_path / "machine/routing/ui-fidelity-routing.v1.json",
        json.loads((Path(__file__).resolve().parents[2] / "machine/routing/ui-fidelity-routing.v1.json").read_text(encoding="utf-8")),
    )
    _write_json(
        tmp_path / "machine/ui/ui-fidelity-handoff.v1.json",
        json.loads((Path(__file__).resolve().parents[2] / "machine/ui/ui-fidelity-handoff.v1.json").read_text(encoding="utf-8")),
    )
    _write_json(
        tmp_path / "machine/ui/ui-engineering-translation.v1.json",
        json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "machine/ui/ui-engineering-translation.v1.json"
            ).read_text(encoding="utf-8")
        ),
    )
    _write_json(tmp_path / "machine/governance/policy.v1.json", policy)
    assert mc.machine_contract_errors(tmp_path) == ()
    return routing, policy


def test_compile_specialist_registry_rejects_manifest_and_frontmatter_drift(tmp_path):
    _write_json(tmp_path / "plugin.json", {"skills": [{"slug": "", "skill_path": ""}]})
    with pytest.raises(ValueError, match="without slug/skill_path"):
        mc.compile_specialist_registry(tmp_path)

    path = tmp_path / "skills/a/SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nname: a\nslug: a\n---\n", encoding="utf-8")
    _write_json(tmp_path / "plugin.json", {"skills": [{"slug": "a", "skill_path": "skills/a/SKILL.md"}]})
    with pytest.raises(ValueError, match="missing specialist frontmatter fields"):
        mc.compile_specialist_registry(tmp_path)

    path.write_text(_skill_frontmatter("other"), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match plugin manifest"):
        mc.compile_specialist_registry(tmp_path)


def test_machine_contract_errors_detect_registry_and_plugin_set_drift(tmp_path):
    _machine_repo(tmp_path)
    registry = mc.load_specialist_registry(tmp_path)
    registry["specialists"].append({"slug": "ghost"})
    _write_json(tmp_path / "machine/specialists/registry.v1.json", registry)
    errors = mc.machine_contract_errors(tmp_path)
    assert "SPECIALIST_REGISTRY_DRIFT" in errors
    assert "SPECIALIST_PLUGIN_SET_MISMATCH" in errors


def test_machine_contract_errors_detect_routing_corruption(tmp_path):
    routing, _ = _machine_repo(tmp_path)
    routing["direct_routes"] = [
        {"route_id": "", "target": "ghost", "via": "ghost"},
        {"route_id": "", "target": "dagger", "via": None, "explicit_authority_required": False},
    ]
    routing["command_routes"] = {
        "bad-record": [],
        "bad-target": {"specialist": "ghost", "route_id": "missing-route"},
    }
    routing["ordered_sequences"] = [
        {"route_id": "sequence", "sequence": ["ghost", "SYMBOL"], "symbolic_nodes": ["SYMBOL"]}
    ]
    routing["legacy_aliases"] = {"old": "ghost"}
    routing["ambiguity_fallback"] = "ghost"
    _write_json(tmp_path / "machine/routing/routes.v1.json", routing)
    errors = mc.machine_contract_errors(tmp_path)
    joined = "\n".join(errors)
    assert "ROUTE_ID_INVALID_OR_DUPLICATE" in joined
    assert "ROUTE_UNKNOWN_SPECIALIST" in joined
    assert "ROUTE_UNKNOWN_VIA" in joined
    assert "DAGGER_ROUTE_MISSING_EXPLICIT_AUTHORITY" in joined
    assert "COMMAND_ROUTE_INVALID" in joined
    assert "COMMAND_ROUTE_UNKNOWN_SPECIALIST" in joined
    assert "COMMAND_ROUTE_UNKNOWN_ROUTE_ID" in joined
    assert "SEQUENCE_UNKNOWN_SPECIALIST" in joined
    assert "ALIAS_UNKNOWN_SPECIALIST" in joined
    assert "AMBIGUITY_FALLBACK_UNKNOWN" in joined


def test_machine_contract_errors_detect_missing_and_invalid_routing_contract(tmp_path):
    _machine_repo(tmp_path)
    _write_json(tmp_path / "machine/routing/routes.v1.json", {
        "schema_version": mc.ROUTING_CONTRACT_SCHEMA_VERSION,
        "direct_routes": [], "command_routes": {}, "ordered_sequences": [], "legacy_aliases": {},
        "ambiguity_fallback": "conductor",
    })
    assert "COMMAND_ROUTES_MISSING" in mc.machine_contract_errors(tmp_path)
    _write_json(tmp_path / "machine/routing/routes.v1.json", {"schema_version": "bad"})
    assert any(item.startswith("ROUTING_CONTRACT_INVALID:") for item in mc.machine_contract_errors(tmp_path))


def test_machine_contract_errors_detect_governance_corruption(tmp_path):
    _, policy = _machine_repo(tmp_path)
    policy["role_ownership"] = {"ghost": ["x"]}
    policy["specialist_controls"] = {"ghost": {}}
    policy["governance_required_specialists"] = ["ghost"]
    policy["runtime_validation_rules"] = [
        {"rule_id": "dup", "skill_slugs": ["ghost"]},
        {"rule_id": "dup", "skill_slugs": []},
    ]
    policy["compatibility_rules"]["APPROVED"] = ["UNKNOWN_DISPOSITION"]
    _write_json(tmp_path / "machine/governance/policy.v1.json", policy)
    errors = mc.machine_contract_errors(tmp_path)
    assert "GOVERNANCE_OWNERSHIP_UNKNOWN_SPECIALIST" in errors
    assert "GOVERNANCE_CONTROL_UNKNOWN_SPECIALIST" in errors
    assert "GOVERNANCE_REQUIRED_UNKNOWN_SPECIALIST" in errors
    assert any(item.startswith("GOVERNANCE_RULE_ID_INVALID_OR_DUPLICATE") for item in errors)
    assert any(item.startswith("GOVERNANCE_RULE_UNKNOWN_SPECIALIST") for item in errors)
    assert "GOVERNANCE_COMPATIBILITY_INVALID:APPROVED" in errors
    with pytest.raises(ValueError, match="machine contract validation failed"):
        mc.assert_machine_contracts(tmp_path)


def test_machine_contract_errors_detect_invalid_governance_policy(tmp_path):
    _machine_repo(tmp_path)
    _write_json(tmp_path / "machine/governance/policy.v1.json", {"schema_version": "bad"})
    assert any(item.startswith("GOVERNANCE_POLICY_INVALID:") for item in mc.machine_contract_errors(tmp_path))


def test_machine_contract_errors_returns_registry_invalid_first(tmp_path):
    _write_json(tmp_path / "plugin.json", {"skills": []})
    _write_json(tmp_path / "machine/specialists/registry.v1.json", {"schema_version": "bad"})
    errors = mc.machine_contract_errors(tmp_path)
    assert len(errors) == 1
    assert errors[0].startswith("SPECIALIST_REGISTRY_INVALID:")


# Compliance remaining integrity branches

def _query():
    return ComplianceQueryReceipt(
        canonical_repository="x/y", registry_version="1", release_sequence=1, release_tag="v1",
        manifest_sha256=SHA64, filters=(("jurisdiction", "PH"),), source_ids=("SRC",),
        obligation_ids=("A", "B"),
    )


def _consume(query, *, sources=("SRC",), obligations=("A", "B"), exclusions=()):
    return ComplianceConsumptionReceipt(
        query_digest=query.digest,
        source_ids=sources,
        obligation_ids=obligations,
        classifications=tuple((item, "OK") for item in obligations),
        verdict="APPROVED",
        exclusions=tuple(exclusions),
    )


def _trace(query, *, digest=None, sources=("SRC",), obligations=("A", "B")):
    return StewardTraceabilityReceipt(
        query_digest=digest or query.digest,
        source_ids=sources,
        obligation_ids=obligations,
        evidence_refs=("receipt:trace",),
    )


def test_compliance_duplicate_filters_exclusions_and_schema_guards():
    with pytest.raises(ValueError, match="duplicate keys"):
        ComplianceQueryReceipt("x/y", "1", 1, "v1", SHA64, (("k", "1"), ("k", "2")), (), ())
    query = _query()
    exclusion = ComplianceExclusion("A", "reason", "ref", "gov")
    with pytest.raises(TypeError, match="exclusions"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("B",), (("B", "OK"),), "APPROVED", [exclusion])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate obligation IDs"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("B",), (("B", "OK"),), "APPROVED", (exclusion, exclusion))
    with pytest.raises(ValueError, match="unsupported compliance consumption schema"):
        ComplianceConsumptionReceipt(query.digest, ("SRC",), ("A", "B"), (("A", "OK"), ("B", "OK")), "APPROVED", schema_version="bad")
    with pytest.raises(ValueError, match="unsupported Steward"):
        StewardTraceabilityReceipt(query.digest, ("SRC",), ("A", "B"), ("ref",), schema_version="bad")


def test_compliance_gate_detects_traceability_digest_and_source_mismatches():
    query = _query()
    consumption = _consume(query, sources=("OTHER",))
    trace = _trace(query, digest="c" * 64, sources=("OTHER",))
    gate = evaluate_compliance_set_equality(query, consumption, trace)
    assert "TRACEABILITY_QUERY_DIGEST_MISMATCH" in gate.error_codes
    assert "CONSUMED_SOURCE_SET_MISMATCH" in gate.error_codes
    assert "TRACEABILITY_SOURCE_SET_MISMATCH" in gate.error_codes
    assert gate.digest


def test_compliance_to_dict_and_digest_surfaces_are_stable():
    query = _query()
    exclusion = ComplianceExclusion("A", "reason", "ref", "gov")
    consumption = _consume(query, obligations=("B",), exclusions=(exclusion,))
    trace = _trace(query)
    gate = evaluate_compliance_set_equality(query, consumption, trace)
    assert query.to_dict()["obligation_count"] == 2
    assert exclusion.to_dict()["obligation_id"] == "A"
    assert consumption.to_dict()["exclusions"][0]["obligation_id"] == "A"
    assert trace.to_dict()["evidence_refs"] == ["receipt:trace"]
    assert gate.to_dict()["ready"] is True
    assert all(len(item) == 64 for item in (query.digest, consumption.digest, trace.digest, gate.digest))


# Workflow receipt boundaries

def _route(**overrides):
    values = dict(
        command_name="review-architecture", skill_slug="clockwork", reason="fixture",
        governance_required=False,
    )
    values.update(overrides)
    return RouteDecision(**values)


def _validation(**overrides):
    values = dict(allowed=True, status="NOT_REQUIRED", reasons=(), evaluated_rules=())
    values.update(overrides)
    return ValidationResult(**values)


def test_workflow_receipt_constructor_guards():
    base = dict(
        command_name="x", route_id="r", specialist_id="conductor", governance_required=False,
        validation_status="OK", validation_rules=(), arbiter_disposition=None,
        arbiter_reason_codes=(), evidence_refs=(), execution_order=("ROUTING",),
    )
    with pytest.raises(ValueError, match="unsupported workflow sanity"):
        WorkflowSanityReceipt(**base, schema_version="bad")
    with pytest.raises(TypeError, match="governance_required"):
        WorkflowSanityReceipt(**{**base, "governance_required": 1})
    with pytest.raises(TypeError, match="validation_rules"):
        WorkflowSanityReceipt(**{**base, "validation_rules": []})
    with pytest.raises(ValueError, match="execution_order must not be empty"):
        WorkflowSanityReceipt(**{**base, "execution_order": ()})


def test_workflow_builder_rejects_wrong_types_and_machine_drift(monkeypatch):
    with pytest.raises(TypeError, match="route must"):
        build_workflow_sanity_receipt("bad", _validation())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="validation must"):
        build_workflow_sanity_receipt(_route(), "bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="arbiter_result"):
        build_workflow_sanity_receipt(_route(), _validation(), arbiter_result="bad")  # type: ignore[arg-type]

    monkeypatch.setattr("orchestra_runtime.workflow_contracts.command_route_record", lambda command: {"specialist": "ponytail", "route_id": "x"})
    with pytest.raises(ValueError, match="disagrees with machine contract"):
        build_workflow_sanity_receipt(_route(), _validation())

    monkeypatch.setattr("orchestra_runtime.workflow_contracts.command_route_record", lambda command: {"specialist": "clockwork", "route_id": "x"})
    monkeypatch.setattr("orchestra_runtime.workflow_contracts.governance_required_specialists", lambda: frozenset({"clockwork"}))
    with pytest.raises(ValueError, match="governance_required"):
        build_workflow_sanity_receipt(_route(), _validation())


def test_workflow_builder_deduplicates_evidence_and_includes_arbiter():
    arbiter = evaluate_arbiter(ArbiterKernelInput(project_id="p", unit_id="u", governance_decisions=(GovernanceDecisionRecord("r", "p", "APPROVED", "ok"),)))
    receipt = build_workflow_sanity_receipt(
        _route(), _validation(), arbiter_result=arbiter,
        evidence_refs=("receipt:a", "", "receipt:a", "receipt:b"),
    )
    assert receipt.evidence_refs == ("receipt:a", "receipt:b")
    assert receipt.arbiter_disposition == "AUTO_CONTINUE"
    assert receipt.to_dict()["execution_order"][-1] == "ARBITER_KERNEL"
    assert len(receipt.digest) == 64


# Test evidence write/CLI paths

def _reports(tmp_path):
    coverage = tmp_path / "coverage.json"
    junit = tmp_path / "junit.xml"
    coverage.write_text(json.dumps({"totals": {
        "num_statements": 100, "covered_lines": 100, "missing_lines": 0,
        "num_branches": 2, "covered_branches": 2, "missing_branches": 0,
    }}), encoding="utf-8")
    junit.write_text('<testsuites tests="2" failures="0" errors="0" skipped="0"/>', encoding="utf-8")
    return coverage, junit


def test_write_test_evidence_uses_environment_and_writes_manifest(tmp_path, monkeypatch):
    coverage, junit = _reports(tmp_path)
    output = tmp_path / "nested/evidence.json"
    monkeypatch.setattr("orchestra_runtime.test_evidence._actual_tested_sha", lambda: SHA40)
    monkeypatch.setenv("SOURCE_HEAD_SHA", SHA40)
    monkeypatch.setenv("RUNTIME_TEST_OUTCOME", "success")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Baelfyre/Orchestra")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF_NAME", "293/merge")
    evidence = write_test_evidence(coverage_path=coverage, junit_path=junit, output_path=output, minimum_statement_coverage=95)
    assert evidence["result"] == "PASS"
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["workflow"]["run_id"] == "123"


def test_test_evidence_cli_returns_pass_and_fail(tmp_path, monkeypatch, capsys):
    coverage, junit = _reports(tmp_path)
    monkeypatch.setattr("orchestra_runtime.test_evidence._actual_tested_sha", lambda: SHA40)
    monkeypatch.setenv("SOURCE_HEAD_SHA", SHA40)
    monkeypatch.setenv("RUNTIME_TEST_OUTCOME", "success")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Baelfyre/Orchestra")
    output = tmp_path / "pass.json"
    assert test_evidence_main(["--coverage", str(coverage), "--junit", str(junit), "--output", str(output), "--minimum-statement-coverage", "95"]) == 0
    assert '"result": "PASS"' in capsys.readouterr().out

    monkeypatch.setenv("RUNTIME_TEST_OUTCOME", "failure")
    output = tmp_path / "fail.json"
    assert test_evidence_main(["--coverage", str(coverage), "--junit", str(junit), "--output", str(output)]) == 1
    assert json.loads(output.read_text(encoding="utf-8"))["result"] == "FAIL"
