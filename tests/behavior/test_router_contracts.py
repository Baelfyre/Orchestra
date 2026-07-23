import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_routing_contract.py"
FIXTURES = ROOT / "tests" / "behavior" / "router-contract-fixtures.json"
DELEGATED_TRACE_FIXTURE = ROOT / "tests" / "behavior" / "delegated-phase-trace-fixtures.json"
TUNER_FIXTURES = ROOT / "tests" / "behavior" / "tuner-collaboration-fixtures.json"
CANONICAL_DISPOSITIONS = (
    "STOP",
    "ESCALATE_HUMAN",
    "WAIT_FOR_CAPACITY",
    "WAIT_FOR_EVIDENCE",
    "AUTO_REMEDIATE_AND_REVALIDATE",
    "AUTO_CONTINUE",
)
CANONICAL_EXTERNAL_FLAGS = {
    "stage", "commit", "push_feature_branch", "create_draft_pr", "merge", "tag",
    "release", "deploy", "production_mutation", "infrastructure_mutation", "destructive_action",
}
EVIDENCE_FIELDS = {
    "schema_version", "evidence_id", "envelope_id", "phase_id", "unit_id",
    "repository_identity", "branch", "approved_base_sha", "current_commit_sha",
    "working_tree_fingerprint", "changed_paths", "implementation_summary",
    "validation_commands", "validation_results", "skipped_checks", "known_limitations",
    "scope_audit_result", "protected_repository_result", "security_and_secret_result",
    "design_contradiction_state", "evidence_producer", "evidence_timestamp", "freshness_reference",
}
TRANSITION_FIELDS = {
    "schema_version", "transition_id", "envelope_id", "phase_id", "unit_id",
    "governance_decision", "continuity_result", "transition_disposition", "reason_code",
    "evidence_references", "remediation_authority", "remediation_attempt_count",
    "next_eligible_unit", "resume_requirements", "decision_producer", "decision_timestamp",
}
CHECKPOINT_FIELDS = {
    "envelope_id", "phase_id", "last_completed_unit", "next_eligible_unit", "branch",
    "approved_base_sha", "current_execution_sha", "working_tree_state", "changed_paths",
    "validation_completed", "validation_remaining", "known_limitations", "next_exact_action",
}


def run_validator(repo_root: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_true(name, condition):
    if not condition:
        raise AssertionError(name)


def make_repo_copy():
    temp = tempfile.TemporaryDirectory(prefix="routing-contract-test-")
    repo_root = Path(temp.name)
    for relative in (
        Path("plugin.json"),
        Path("SKILL_INDEX.md"),
        Path("ROUTING_MAP.md"),
        Path("tests/behavior/router-contract-fixtures.json"),
    ):
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    return temp, repo_root


def test_passes_real_repo():
    result = run_validator(ROOT)
    assert_true("real repo pass", result.returncode == 0)


def test_missing_required_fixture_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures = [fixture for fixture in fixtures if fixture["id"] != "business-vs-legal-overlap"]
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing fixture fail", result.returncode == 1 and "Missing required routing fixtures" in result.stdout)
    finally:
        temp.cleanup()


def test_protocol_loaded_during_classification_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures[0]["required_context"].append("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("protocol over-hydration fail", result.returncode == 1 and "must not load merely to classify a route" in result.stdout)
    finally:
        temp.cleanup()


def test_obvious_single_owner_conductor_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-clockwork":
                fixture["primary_skill"] = "conductor"
                break
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("obvious single-owner conductor fail", result.returncode == 1 and "obvious single-owner work must not stay with conductor" in result.stdout)
    finally:
        temp.cleanup()


def test_governed_implementation_protocol_context_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "governance-sensitive-implementation-sequence":
                fixture["forbidden_context"].remove("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("governed implementation protocol fail", result.returncode == 1 and "must be forbidden" in result.stdout)
    finally:
        temp.cleanup()


def test_direct_dagger_authorization_contradiction_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-dagger":
                fixture["request"] = "Run guarded chaos after explicit approval."
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("direct dagger contradiction fail", result.returncode == 1 and "must not claim approval" in result.stdout)
    finally:
        temp.cleanup()


def load_codex_validator():
    path = ROOT / "adapters" / "codex" / "validate_codex_export.py"
    spec = importlib.util.spec_from_file_location("validate_codex_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_integrity_cases():
    validator = load_codex_validator()
    with tempfile.TemporaryDirectory(prefix="codex-reference-contract-") as temp_name:
        temp_root = Path(temp_name)

        canonical = temp_root / "canonical"
        canonical_skill = canonical / "skills/conductor/SKILL.md"
        canonical_target = canonical / "docs/routing/EXECUTION_MODES_POLICY.md"
        canonical_skill.parent.mkdir(parents=True)
        canonical_target.parent.mkdir(parents=True)
        canonical_target.write_text("# Policy\n", encoding="utf-8")
        canonical_skill.write_text("[policy](../../docs/routing/EXECUTION_MODES_POLICY.md)\n", encoding="utf-8")
        assert_true(
            "valid canonical reference passes",
            validator.validate_local_references(canonical_skill, canonical, canonical) == 0,
        )

        for label, depth in (("tracked", ()), ("arbitrary-depth", ("unrelated", "deep", "package"))):
            package = temp_root.joinpath(label, *depth)
            skill = package / "skills/conductor/SKILL.md"
            target = skill.parent / "REFERENCE_CONTEXT.md"
            skill.parent.mkdir(parents=True)
            target.write_text("# Context\n", encoding="utf-8")
            skill.write_text("[context](REFERENCE_CONTEXT.md#policy)\n", encoding="utf-8")
            assert_true(
                f"valid {label} package reference passes",
                validator.validate_local_references(skill, package, package) == 0,
            )

        negative_cases = {
            "missing target": "[missing](missing.md)\n",
            "wrong depth": "[wrong](../docs/missing.md)\n",
            "bare external filename": "Use `EXTERNAL_POLICY.md`.\n",
            "path escape": "[escape](../../../../outside.md)\n",
        }
        for label, content in negative_cases.items():
            package = temp_root / f"negative-{label.replace(' ', '-')}"
            skill = package / "skills/conductor/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(content, encoding="utf-8")
            assert_true(
                f"{label} fails",
                validator.validate_local_references(skill, package, package) > 0,
            )


def evaluate_delegated_trace(trace, repo_root=ROOT):
    errors = []
    events = ["PHASE_AUTHORIZED"]
    policy = (repo_root / "docs/governance/DELEGATED_EXECUTION_POLICY.md").read_text(encoding="utf-8")
    conductor = (repo_root / "skills/conductor/SKILL.md").read_text(encoding="utf-8")
    arbiter = (repo_root / "skills/arbiter/SKILL.md").read_text(encoding="utf-8")

    precedence_positions = []
    for index, disposition in enumerate(CANONICAL_DISPOSITIONS, 1):
        marker = f"{index}. **{disposition}**"
        if marker not in policy:
            errors.append(f"policy missing precedence marker {marker}")
        else:
            precedence_positions.append(policy.index(marker))
        if disposition not in conductor or disposition not in arbiter:
            errors.append(f"Phase B instruction contracts missing {disposition}")
    if precedence_positions != sorted(precedence_positions):
        errors.append("transition precedence order differs from canonical policy")

    envelope = trace.get("envelope", {})
    flags = envelope.get("external_action_authority", {})
    if set(flags) != CANONICAL_EXTERNAL_FLAGS:
        errors.append("external-action flag vocabulary is noncanonical")
    if any(value is not False for value in flags.values()):
        errors.append("external-action authority must remain false")

    units = envelope.get("approved_unit_plan", [])
    evidence_by_unit = {item.get("unit_id"): item for item in trace.get("evidence_packets", [])}
    transition_by_unit = {item.get("unit_id"): item for item in trace.get("transition_records", [])}
    input_by_unit = {item.get("unit_id"): item for item in trace.get("transition_inputs", [])}
    checkpoint_by_unit = {item.get("last_completed_unit"): item for item in trace.get("checkpoint_records", [])}
    completed = set()

    for unit_index, unit in enumerate(units):
        unit_id = unit.get("unit_id")
        expected_next = unit.get("next_eligible_units", [])
        expected_next = expected_next[0] if expected_next else None
        if not set(unit.get("dependencies", [])).issubset(completed):
            errors.append(f"{unit_id}: dependency ordering invalid")

        events.extend((f"UNIT_READY({unit_id})", f"UNIT_VALIDATING({unit_id})"))
        evidence = evidence_by_unit.get(unit_id)
        if not evidence or set(evidence) != EVIDENCE_FIELDS:
            errors.append(f"{unit_id}: evidence schema incomplete")
            continue

        expected_freshness = "|".join((
            envelope.get("envelope_id", ""),
            envelope.get("canonical_branch", ""),
            envelope.get("current_commit_sha", ""),
        ))
        lineage_checks = {
            "envelope_id": envelope.get("envelope_id"),
            "phase_id": envelope.get("phase_id"),
            "repository_identity": envelope.get("repository_identity"),
            "branch": envelope.get("canonical_branch"),
            "approved_base_sha": envelope.get("approved_base_sha"),
            "current_commit_sha": envelope.get("current_commit_sha"),
            "freshness_reference": expected_freshness,
        }
        for field, expected in lineage_checks.items():
            if evidence.get(field) != expected:
                errors.append(f"{unit_id}: stale or mismatched evidence {field}")
        if any(result.get("result") != "PASS" for result in evidence.get("validation_results", [])):
            errors.append(f"{unit_id}: focused validation failed")
        for field in ("scope_audit_result", "protected_repository_result", "security_and_secret_result"):
            if evidence.get(field) != "PASS":
                errors.append(f"{unit_id}: {field} failed")
        if evidence.get("design_contradiction_state") != "NONE":
            errors.append(f"{unit_id}: design contradiction unresolved")

        transition = transition_by_unit.get(unit_id)
        if not transition or set(transition) != TRANSITION_FIELDS:
            errors.append(f"{unit_id}: transition schema incomplete")
            continue
        for field, expected in (("envelope_id", envelope.get("envelope_id")), ("phase_id", envelope.get("phase_id")), ("unit_id", unit_id)):
            if transition.get(field) != expected:
                errors.append(f"{unit_id}: transition {field} mismatch")
        if evidence.get("evidence_id") not in transition.get("evidence_references", []):
            errors.append(f"{unit_id}: transition does not reference current evidence")
        if transition.get("next_eligible_unit") != expected_next:
            errors.append(f"{unit_id}: wrong next eligible unit")

        active_conditions = input_by_unit.get(unit_id, {}).get("active_conditions", [])
        unsupported_conditions = sorted(set(active_conditions) - set(CANONICAL_DISPOSITIONS))
        if not active_conditions or unsupported_conditions:
            errors.append(f"{unit_id}: unsupported precedence input")
        else:
            required_disposition = next(
                disposition for disposition in CANONICAL_DISPOSITIONS if disposition in active_conditions
            )
            if transition.get("transition_disposition") != required_disposition:
                errors.append(f"{unit_id}: lower-priority disposition overrides {required_disposition}")

        checkpoint = checkpoint_by_unit.get(unit_id)
        if not checkpoint or set(checkpoint) != CHECKPOINT_FIELDS:
            errors.append(f"{unit_id}: checkpoint missing or incomplete")
            continue
        checkpoint_checks = {
            "envelope_id": envelope.get("envelope_id"),
            "phase_id": envelope.get("phase_id"),
            "last_completed_unit": unit_id,
            "next_eligible_unit": expected_next,
            "branch": envelope.get("canonical_branch"),
            "approved_base_sha": envelope.get("approved_base_sha"),
            "current_execution_sha": envelope.get("current_commit_sha"),
        }
        for field, expected in checkpoint_checks.items():
            if checkpoint.get(field) != expected:
                errors.append(f"{unit_id}: checkpoint {field} mismatch")

        events.extend((f"UNIT_ACCEPTED({unit_id})", f"CHECKPOINTED({unit_id})"))
        if expected_next:
            events.append(f"AUTO_CONTINUE({expected_next})")
        completed.add(unit_id)

    phase_validation = trace.get("phase_validation")
    if not phase_validation:
        errors.append("phase validation missing")
    else:
        requirements = phase_validation.get("requirements", [])
        results = phase_validation.get("results", {})
        if not requirements or any(results.get(requirement) != "PASS" for requirement in requirements):
            errors.append("phase validation incomplete or failed")
        else:
            events.extend(("PHASE_VALIDATING", "PHASE_READY_FOR_HUMAN_REVIEW"))

    if trace.get("expected_owner_relay_event_count") != 0 or len(trace.get("owner_relay_events", [])) != 0:
        errors.append("owner relay count mismatch")
    if trace.get("expected_steward_review_count") != 1 or trace.get("steward_review_count") != 1:
        errors.append("Steward review count mismatch")
    if trace.get("expected_governor_review_count") != 1 or trace.get("governor_review_count") != 1:
        errors.append("Governor review count mismatch")
    if events != trace.get("expected_event_sequence"):
        errors.append("event sequence mismatch")
    if not events or events[-1] != trace.get("expected_terminal_phase_state"):
        errors.append("terminal phase state mismatch")
    return errors, events


def test_delegated_three_unit_contract_trace():
    trace = json.loads(DELEGATED_TRACE_FIXTURE.read_text(encoding="utf-8"))
    errors, events = evaluate_delegated_trace(trace)
    assert_true(f"valid delegated trace passes: {errors}", not errors)
    assert_true("phase gate derives terminal state", events[-1] == "PHASE_READY_FOR_HUMAN_REVIEW")


def test_delegated_trace_negative_cases():
    source = json.loads(DELEGATED_TRACE_FIXTURE.read_text(encoding="utf-8"))
    mutations = {
        "wrong next unit": lambda item: item["transition_records"][0].update(next_eligible_unit="unit-3"),
        "stale evidence": lambda item: item["evidence_packets"][0].update(current_commit_sha="stale-sha"),
        "wrong branch": lambda item: item["evidence_packets"][0].update(branch="wrong-branch"),
        "wrong envelope": lambda item: item["transition_records"][0].update(envelope_id="wrong-envelope"),
        "missing checkpoint": lambda item: item["checkpoint_records"].pop(0),
        "owner relay event present": lambda item: item["owner_relay_events"].append("OWNER_APPROVAL"),
        "noncanonical external flag": lambda item: item["envelope"]["external_action_authority"].update(push=False),
        "external flag set true": lambda item: item["envelope"]["external_action_authority"].update(stage=True),
        "missing phase validation": lambda item: item.pop("phase_validation"),
        "failed phase validation": lambda item: item["phase_validation"]["results"].update(behavior="FAIL"),
        "lower priority overrides STOP": lambda item: item["transition_inputs"][0]["active_conditions"].append("STOP"),
    }
    for label, mutate in mutations.items():
        trace = copy.deepcopy(source)
        mutate(trace)
        errors, _ = evaluate_delegated_trace(trace)
        assert_true(f"negative trace rejected: {label}", bool(errors))


def test_tuner_routing_activation_and_bypass():
    router_fixtures = {item["id"]: item for item in json.loads(FIXTURES.read_text(encoding="utf-8"))}
    for fixture_id in ("direct-scribe", "direct-ponytail"):
        fixture = router_fixtures[fixture_id]
        assert_true(f"{fixture_id} bypasses the-tuner", "the-tuner" not in fixture["supporting_skills"])
        assert_true(f"{fixture_id} forbids the-tuner", "the-tuner" in fixture["forbidden_skills"])

    for fixture_id in ("multi-domain-tuner-coordination", "late-boundary-crossing-tuner"):
        fixture = router_fixtures[fixture_id]
        assert_true(f"{fixture_id} remains routed by conductor", fixture["primary_skill"] == "conductor")
        assert_true(f"{fixture_id} activates the-tuner", "the-tuner" in fixture["supporting_skills"])
        assert_true(f"{fixture_id} requires contract gate", fixture["expected_gate"] == "CROSS_LAYER_CONTRACT_REQUIRED")

    tuner_fixtures = json.loads(TUNER_FIXTURES.read_text(encoding="utf-8"))
    assert_true("Tuner fixture suite is present", len(tuner_fixtures) >= 14)


def main():
    test_passes_real_repo()
    test_missing_required_fixture_fails()
    test_protocol_loaded_during_classification_fails()
    test_obvious_single_owner_conductor_fails()
    test_governed_implementation_protocol_context_fails()
    test_direct_dagger_authorization_contradiction_fails()
    test_reference_integrity_cases()
    test_delegated_three_unit_contract_trace()
    test_delegated_trace_negative_cases()
    test_tuner_routing_activation_and_bypass()
    print("Router contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
