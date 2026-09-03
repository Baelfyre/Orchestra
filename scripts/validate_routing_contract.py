import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SKILLS = {
    "the-steward",
    "the-governor",
    "arbiter",
    "conductor",
    "the-tuner",
    "clockwork",
    "cipher",
    "cloak",
    "chronicler",
    "overseer",
    "dagger",
    "weaver",
    "scribe",
    "ponytail",
}

REQUIRED_FIXTURE_IDS = {
    "business-vs-legal-overlap",
    "privacy-obligation-vs-privacy-control",
    "arbiter-vs-overseer-overlap",
    "steward-vs-scribe-overlap",
    "clockwork-vs-ponytail-overlap",
    "chronicler-vs-overseer-overlap",
    "cloak-vs-cipher-overlap",
    "governance-sensitive-implementation-sequence",
    "ambiguous-cross-domain-retained-by-conductor",
    "destructive-blocked-pending-authorization",
    "governance-decision-enforcement",
    "multi-domain-tuner-coordination",
    "late-boundary-crossing-tuner",
    "scribe-system-to-docs",
    "scribe-spec-to-system",
    "scribe-problem-to-specification",
    "scribe-domain-model-discovery",
    "scribe-capstone-existing-system",
    "scribe-reconcile-docs-code",
    "scribe-implemented-system-docs",
    "scribe-approved-requirements-guidance",
    "scribe-database-table-reroute",
    "scribe-unsupported-validation-promotion",
    "scribe-copyrighted-template-reroute",
    "or-gov5-vague-scale",
    "or-gov5-premature-redis",
    "or-gov5-exact-capacity",
    "or-gov5-partial-capacity",
    "or-gov5-prototype-unknown-workload",
    "or-gov5-possible-future-organizations",
    "or-gov5-single-tenant",
    "or-gov5-live-tenant-migration",
    "or-gov5-development-nullable-column",
    "or-gov5-requested-feature",
    "or-gov5-trivial-ui-copy",
    "or-gov5-capacity-changed",
    "or-gov5-unsupported-capacity-claim",
    "or-gov5-existing-architecture-sufficient",
    "or-gov5-unauthorized-dagger",
    "or-gov5-unknown-production-presence",
    "or-gov5-compound-redis-future-growth",
    "or-gov5-compound-live-tenant-model",
    "or-gov5-compound-prove-500-rps",
}

VALID_MODES = {"Ideation", "Prototype", "Implementation", "Governed", "Audit", "Release", "Destructive"}
VALID_GOVERNANCE = {"NOT_REQUIRED", "CONDITIONAL", "REQUIRED", "BLOCKED_PENDING_AUTHORIZATION"}
VALID_GATES = {"NONE", "CONTINUITY_REQUIRED", "BLOCKED_PENDING_AUTHORIZATION", "DECISION_PROTOCOL_REQUIRED", "CROSS_LAYER_CONTRACT_REQUIRED"}
KNOWN_CONTEXTS = {
    "SKILL_INDEX.md",
    "ROUTING_MAP.md",
    "docs/routing/EXECUTION_MODES_POLICY.md",
    "docs/governance/GOVERNANCE_LAYER.md",
    "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md",
    "docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md",
}

SSU_FIXTURE_EXPECTATIONS = {
    "scribe-system-to-docs": ("SYSTEM_TO_DOCS", "documentation-system-to-docs", "SCRIBE_RECONSTRUCTION"),
    "scribe-spec-to-system": ("SPEC_TO_SYSTEM", "documentation-spec-to-system", "SCRIBE_LEADS_SPECIFICATION"),
    "scribe-problem-to-specification": ("SPEC_TO_SYSTEM", "documentation-spec-to-system", "SCRIBE_LEADS_SPECIFICATION"),
    "scribe-domain-model-discovery": ("SPEC_TO_SYSTEM", "documentation-domain-narrative", "SCRIBE_CONCEPT_DISCOVERY_THEN_SPECIALIST_REROUTE"),
    "scribe-capstone-existing-system": ("SYSTEM_TO_DOCS", "documentation-system-to-docs", "SCRIBE_RECONSTRUCTION"),
    "scribe-reconcile-docs-code": ("RECONCILE", "documentation-reconcile", "RECONCILIATION_WITH_EXPLICIT_DRIFT"),
    "scribe-implemented-system-docs": ("SYSTEM_TO_DOCS", "documentation-system-to-docs", "SCRIBE_RECONSTRUCTION"),
    "scribe-approved-requirements-guidance": ("SPEC_TO_SYSTEM", "documentation-spec-to-system", "SCRIBE_LEADS_THEN_IMPLEMENTATION"),
    "scribe-database-table-reroute": ("Audit", "documentation-domain-narrative", "SPECIALIST_REROUTE_REQUIRED"),
    "scribe-unsupported-validation-promotion": ("Audit", "documentation-reconcile", "MISSING_EVIDENCE"),
    "scribe-copyrighted-template-reroute": ("Governed", "documentation", "SPECIALIST_REROUTE_REQUIRED"),
}

OR_GOV5_FIXTURE_EXPECTATIONS = {
    "or-gov5-vague-scale": {
        "intake": {"change_materiality": "ARCHITECTURAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "PROMPT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward", "clockwork"],
    },
    "or-gov5-premature-redis": {
        "intake": {"change_materiality": "ARCHITECTURAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "PROMPT_REQUIRED", "complexity_delta": "MATERIAL", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "REQUESTED_SOLUTION", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward", "clockwork"],
    },
    "or-gov5-exact-capacity": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "KNOWN", "capacity_context_disposition": "SUFFICIENT", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-partial-capacity": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "PARTIAL", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-prototype-unknown-workload": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "MEASUREMENT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-possible-future-organizations": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "POSSIBLE", "persistence_impact": "NONE", "product_decision": "STRATEGIC_CHANGE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-single-tenant": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-live-tenant-migration": {
        "intake": {"change_materiality": "PRODUCTION_CRITICAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "MEASUREMENT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "CONFIRMED", "persistence_impact": "HIGH_RISK", "product_decision": "NONE", "security_impact": "POSSIBLE", "validation_impact": "CONTRACT_DERIVED"},
        "route": ["chronicler", "cipher"],
    },
    "or-gov5-development-nullable-column": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "DEVELOPMENT_ONLY", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["chronicler"],
    },
    "or-gov5-requested-feature": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "REQUESTED_SOLUTION", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward"],
    },
    "or-gov5-trivial-ui-copy": {
        "intake": {"change_materiality": "TRIVIAL", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["cloak"],
    },
    "or-gov5-capacity-changed": {
        "intake": {"change_materiality": "ARCHITECTURAL", "capacity_relevance": "CHANGED", "capacity_context_disposition": "PARTIAL", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "CONTRACT_DERIVED"},
        "route": ["the-steward", "clockwork"],
    },
    "or-gov5-unsupported-capacity-claim": {
        "intake": {"change_materiality": "ARCHITECTURAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "BLOCKING_FOR_CLAIM", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "EMPIRICAL_REQUIRED"},
        "route": ["overseer"],
    },
    "or-gov5-existing-architecture-sufficient": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "KNOWN", "capacity_context_disposition": "SUFFICIENT", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["clockwork"],
    },
    "or-gov5-unauthorized-dagger": {
        "intake": {"change_materiality": "PRODUCTION_CRITICAL", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["dagger"],
    },
    "or-gov5-unknown-production-presence": {
        "intake": {"change_materiality": "PRODUCTION_CRITICAL", "capacity_relevance": "NONE", "capacity_context_disposition": "NOT_REQUIRED", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "PRODUCTION_COMPATIBILITY", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "CONTRACT_DERIVED"},
        "route": ["chronicler"],
    },
    "or-gov5-compound-redis-future-growth": {
        "intake": {"change_materiality": "ARCHITECTURAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "PROMPT_REQUIRED", "complexity_delta": "MATERIAL", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "REQUESTED_SOLUTION", "security_impact": "NONE", "validation_impact": "NORMAL"},
        "route": ["the-steward", "clockwork"],
    },
    "or-gov5-compound-live-tenant-model": {
        "intake": {"change_materiality": "PRODUCTION_CRITICAL", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "MEASUREMENT_REQUIRED", "complexity_delta": "MATERIAL", "tenancy_impact": "CONFIRMED", "persistence_impact": "HIGH_RISK", "product_decision": "NONE", "security_impact": "MATERIAL", "validation_impact": "CONTRACT_DERIVED"},
        "route": ["clockwork", "chronicler", "cipher"],
    },
    "or-gov5-compound-prove-500-rps": {
        "intake": {"change_materiality": "STANDARD", "capacity_relevance": "UNKNOWN", "capacity_context_disposition": "BLOCKING_FOR_CLAIM", "complexity_delta": "NONE", "tenancy_impact": "NONE", "persistence_impact": "NONE", "product_decision": "NONE", "security_impact": "NONE", "validation_impact": "EMPIRICAL_REQUIRED"},
        "route": ["overseer"],
    },
}

INTAKE_ENUMS = {
    "change_materiality": {"TRIVIAL", "STANDARD", "ARCHITECTURAL", "PRODUCTION_CRITICAL"},
    "capacity_relevance": {"NONE", "KNOWN", "UNKNOWN", "CHANGED"},
    "capacity_context_disposition": {"NOT_REQUIRED", "SUFFICIENT", "PARTIAL", "PROMPT_REQUIRED", "MEASUREMENT_REQUIRED", "BLOCKING_FOR_CLAIM"},
    "complexity_delta": {"NONE", "LOW", "MATERIAL"},
    "tenancy_impact": {"NONE", "POSSIBLE", "CONFIRMED"},
    "persistence_impact": {"NONE", "DEVELOPMENT_ONLY", "PRODUCTION_COMPATIBILITY", "HIGH_RISK"},
    "product_decision": {"NONE", "REQUESTED_SOLUTION", "STRATEGIC_CHANGE"},
    "security_impact": {"NONE", "POSSIBLE", "MATERIAL"},
    "validation_impact": {"NORMAL", "CONTRACT_DERIVED", "EMPIRICAL_REQUIRED"},
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate deterministic routing contracts.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_skill_slugs(repo_root: Path):
    plugin = load_json(repo_root / "plugin.json")
    return {entry["slug"] for entry in plugin.get("skills", [])}


def parse_markdown_table_first_column_set(path: Path):
    values = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Skill", "Task Type", "---", "-----------"}:
            continue
        values.update(re.findall(r"`([a-z][a-z0-9-]+)`", cells[0]))
        values.update(re.findall(r"`([a-z][a-z0-9-]+)`", cells[1]))
    return values


def fail(errors, message):
    errors.append(message)


def validate_fixture_schema(fixtures, registered, errors):
    seen = set()
    primary_coverage = set()

    for fixture in fixtures:
        fixture_id = fixture.get("id")
        if not fixture_id or not isinstance(fixture_id, str):
            fail(errors, "Fixture missing string id.")
            continue
        if fixture_id in seen:
            fail(errors, f"Duplicate fixture id: {fixture_id}")
        seen.add(fixture_id)

        for field in (
            "request",
            "expected_intent",
            "expected_mode",
            "primary_skill",
            "governance_status",
            "expected_gate",
            "rationale",
        ):
            if not isinstance(fixture.get(field), str) or not fixture[field].strip():
                fail(errors, f"{fixture_id}: missing non-empty string field `{field}`")

        if fixture.get("expected_mode") not in VALID_MODES:
            fail(errors, f"{fixture_id}: invalid expected_mode {fixture.get('expected_mode')!r}")
        if fixture.get("governance_status") not in VALID_GOVERNANCE:
            fail(errors, f"{fixture_id}: invalid governance_status {fixture.get('governance_status')!r}")
        if fixture.get("expected_gate") not in VALID_GATES:
            fail(errors, f"{fixture_id}: invalid expected_gate {fixture.get('expected_gate')!r}")

        primary = fixture.get("primary_skill")
        if primary not in registered:
            fail(errors, f"{fixture_id}: unknown primary skill {primary!r}")
        else:
            primary_coverage.add(primary)

        for list_field in ("supporting_skills", "required_context", "forbidden_context", "forbidden_skills"):
            value = fixture.get(list_field)
            if not isinstance(value, list):
                fail(errors, f"{fixture_id}: `{list_field}` must be a list")
                continue
            if len(value) != len(set(value)):
                fail(errors, f"{fixture_id}: `{list_field}` contains duplicates")

        for skill in fixture.get("supporting_skills", []):
            if skill not in registered:
                fail(errors, f"{fixture_id}: unknown supporting skill {skill!r}")
        for skill in fixture.get("forbidden_skills", []):
            if skill not in registered:
                fail(errors, f"{fixture_id}: unknown forbidden skill {skill!r}")
        if primary in fixture.get("forbidden_skills", []):
            fail(errors, f"{fixture_id}: primary skill also listed as forbidden")
        for context in fixture.get("required_context", []):
            if context not in KNOWN_CONTEXTS:
                fail(errors, f"{fixture_id}: unknown required context {context!r}")
        for context in fixture.get("forbidden_context", []):
            if context not in KNOWN_CONTEXTS:
                fail(errors, f"{fixture_id}: unknown forbidden context {context!r}")
        overlap = set(fixture.get("required_context", [])) & set(fixture.get("forbidden_context", []))
        if overlap:
            fail(errors, f"{fixture_id}: context both required and forbidden: {sorted(overlap)}")

    missing_required_ids = REQUIRED_FIXTURE_IDS - seen
    if missing_required_ids:
        fail(errors, f"Missing required routing fixtures: {sorted(missing_required_ids)}")

    missing_skill_coverage = (REQUIRED_SKILLS - {"the-tuner"}) - primary_coverage
    if missing_skill_coverage:
        fail(errors, f"Missing primary-skill fixture coverage: {sorted(missing_skill_coverage)}")


def validate_expected_routing_rules(fixtures, errors):
    by_id = {fixture["id"]: fixture for fixture in fixtures if "id" in fixture}

    for fixture_id in (
        "direct-clockwork",
        "direct-cipher",
        "direct-chronicler",
        "direct-steward",
        "direct-governor",
    ):
        if by_id.get(fixture_id, {}).get("primary_skill") == "ponytail":
            fail(errors, f"{fixture_id}: must not default to ponytail")

    for fixture_id in (
        "direct-clockwork",
        "direct-cloak",
        "direct-chronicler",
        "direct-overseer",
        "direct-dagger",
        "direct-scribe",
        "direct-ponytail",
        "direct-weaver",
    ):
        fixture = by_id.get(fixture_id)
        if not fixture:
            continue
        if fixture["primary_skill"] == "conductor":
            fail(errors, f"{fixture_id}: obvious single-owner work must not stay with conductor")
        if "ROUTING_MAP.md" in fixture["required_context"]:
            fail(errors, f"{fixture_id}: ROUTING_MAP.md must be excluded for obvious single-owner work")
        if "docs/governance/GOVERNANCE_LAYER.md" in fixture["required_context"]:
            fail(errors, f"{fixture_id}: governance context must be excluded for ordinary low-risk work")

    for fixture_id in (
        "business-vs-legal-overlap",
        "privacy-obligation-vs-privacy-control",
        "arbiter-vs-overseer-overlap",
        "steward-vs-scribe-overlap",
        "clockwork-vs-ponytail-overlap",
        "chronicler-vs-overseer-overlap",
        "cloak-vs-cipher-overlap",
        "governance-sensitive-implementation-sequence",
        "ambiguous-cross-domain-retained-by-conductor",
        "multi-domain-tuner-coordination",
        "late-boundary-crossing-tuner",
    ):
        fixture = by_id.get(fixture_id)
        if fixture and fixture["primary_skill"] != "conductor":
            fail(errors, f"{fixture_id}: ambiguous or ordered cross-domain work must stay with conductor")

    for fixture_id in ("direct-steward", "direct-governor", "business-vs-legal-overlap", "privacy-obligation-vs-privacy-control", "cloak-vs-cipher-overlap", "governance-sensitive-implementation-sequence", "governance-decision-enforcement"):
        fixture = by_id.get(fixture_id)
        if fixture and "docs/governance/GOVERNANCE_LAYER.md" not in fixture["required_context"]:
            fail(errors, f"{fixture_id}: governance layer must load for defined governance triggers")

    enforcement = by_id.get("governance-decision-enforcement")
    if enforcement and "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md" not in enforcement["required_context"]:
        fail(errors, "governance-decision-enforcement: decision protocol must load for governance decision enforcement")

    governed_implementation = by_id.get("governance-sensitive-implementation-sequence")
    if governed_implementation and "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md" not in governed_implementation["forbidden_context"]:
        fail(errors, "governance-sensitive-implementation-sequence: decision protocol must be forbidden during implementation routing")

    for fixture in fixtures:
        if fixture["id"] != "governance-decision-enforcement" and "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md" in fixture.get("required_context", []):
            fail(errors, f"{fixture['id']}: decision protocol must not load merely to classify a route")

    for fixture in fixtures:
        if fixture.get("id", "").startswith("direct-"):
            if "the-tuner" in fixture.get("supporting_skills", []):
                fail(errors, "{}: obvious single-owner work must bypass the-tuner".format(fixture.get("id")))
            if "docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md" in fixture.get("required_context", []):
                fail(errors, "{}: direct route must not load Tuner protocol context".format(fixture.get("id")))

    for fixture_id in ("multi-domain-tuner-coordination", "late-boundary-crossing-tuner"):
        fixture = by_id.get(fixture_id)
        if fixture:
            if fixture.get("primary_skill") != "conductor":
                fail(errors, f"{fixture_id}: Conductor must remain the primary router")
            if "the-tuner" not in fixture.get("supporting_skills", []):
                fail(errors, f"{fixture_id}: must activate the-tuner")
            if fixture.get("expected_gate") != "CROSS_LAYER_CONTRACT_REQUIRED":
                fail(errors, f"{fixture_id}: must require a cross-layer contract")
            if "docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md" not in fixture.get("required_context", []):
                fail(errors, f"{fixture_id}: must load the canonical Tuner protocol")

    destructive = by_id.get("destructive-blocked-pending-authorization")
    if destructive:
        if destructive["governance_status"] != "BLOCKED_PENDING_AUTHORIZATION":
            fail(errors, "destructive-blocked-pending-authorization: Dagger route must remain blocked pending authorization")
        if destructive["expected_gate"] != "BLOCKED_PENDING_AUTHORIZATION":
            fail(errors, "destructive-blocked-pending-authorization: expected gate must remain blocked pending authorization")

    direct_dagger = by_id.get("direct-dagger")
    if direct_dagger:
        if "authorization has not yet been granted" not in direct_dagger["request"]:
            fail(errors, "direct-dagger: request must not claim approval while gate remains blocked")
        if direct_dagger["expected_gate"] != "BLOCKED_PENDING_AUTHORIZATION":
            fail(errors, "direct-dagger: expected gate must remain blocked pending authorization")

    continuity = by_id.get("arbiter-vs-overseer-overlap")
    if continuity and continuity["expected_gate"] != "CONTINUITY_REQUIRED":
        fail(errors, "arbiter-vs-overseer-overlap: Arbiter HOLD/BLOCKED gate must remain blocking")


def validate_ssu_fixtures(fixtures, errors):
    by_id = {fixture["id"]: fixture for fixture in fixtures if "id" in fixture}

    for fixture_id, (mode, route_id, outcome) in SSU_FIXTURE_EXPECTATIONS.items():
        fixture = by_id.get(fixture_id)
        if not fixture:
            continue
        if fixture.get("primary_skill") != "scribe":
            fail(errors, f"{fixture_id}: Scribe must remain the primary documentation owner")
        if fixture.get("scribe_mode") != mode:
            fail(errors, f"{fixture_id}: expected scribe_mode {mode!r}")
        if fixture.get("expected_route_id") != route_id:
            fail(errors, f"{fixture_id}: expected_route_id must be {route_id!r}")
        if fixture.get("expected_outcome") != outcome:
            fail(errors, f"{fixture_id}: expected_outcome must be {outcome!r}")

    reroute = by_id.get("scribe-database-table-reroute")
    if reroute:
        if reroute.get("reroute_skill") != "chronicler":
            fail(errors, "scribe-database-table-reroute: database-table authority must reroute to chronicler")
        if reroute.get("expected_outcome") != "SPECIALIST_REROUTE_REQUIRED":
            fail(errors, "scribe-database-table-reroute: unsupported database ownership must be rejected")

    unsupported = by_id.get("scribe-unsupported-validation-promotion")
    if unsupported:
        if unsupported.get("required_evidence_state") != "MISSING_EVIDENCE":
            fail(errors, "scribe-unsupported-validation-promotion: untested behavior must remain MISSING_EVIDENCE")
        if "validated" not in unsupported.get("request", "").lower():
            fail(errors, "scribe-unsupported-validation-promotion: fixture must cover an unsupported validation promotion")

    rights = by_id.get("scribe-copyrighted-template-reroute")
    if rights:
        if rights.get("reroute_skill") != "the-governor":
            fail(errors, "scribe-copyrighted-template-reroute: rights uncertainty must escalate to the-governor")
        if rights.get("governance_status") != "REQUIRED":
            fail(errors, "scribe-copyrighted-template-reroute: rights review must remain governance-required")
        if "copyright" not in rights.get("request", "").lower():
            fail(errors, "scribe-copyrighted-template-reroute: fixture must cover copyright/provenance handling")


def validate_or_gov5_fixtures(fixtures, errors):
    by_id = {fixture["id"]: fixture for fixture in fixtures if "id" in fixture}

    for fixture_id, expected in OR_GOV5_FIXTURE_EXPECTATIONS.items():
        fixture = by_id.get(fixture_id)
        if not fixture:
            continue

        intake = fixture.get("architecture_governance_intake")
        if not isinstance(intake, dict):
            fail(errors, f"{fixture_id}: missing architecture_governance_intake object")
            continue

        for field, allowed in INTAKE_ENUMS.items():
            value = intake.get(field)
            if value not in allowed:
                fail(errors, f"{fixture_id}: invalid intake {field} {value!r}")
            if value != expected["intake"][field]:
                fail(errors, f"{fixture_id}: intake {field} must be {expected['intake'][field]!r}")

        route = fixture.get("expected_route")
        if not isinstance(route, list):
            fail(errors, f"{fixture_id}: expected_route must be a list")
        else:
            if route != expected["route"]:
                fail(errors, f"{fixture_id}: expected_route must be {expected['route']!r}")
            if len(route) != len(set(route)):
                fail(errors, f"{fixture_id}: expected_route contains duplicates")
            for skill in route:
                if skill not in REQUIRED_SKILLS:
                    fail(errors, f"{fixture_id}: expected_route names unknown skill {skill!r}")

        if fixture.get("primary_skill") == "ponytail" and fixture_id in {
            "or-gov5-vague-scale",
            "or-gov5-premature-redis",
            "or-gov5-unsupported-capacity-claim",
            "or-gov5-unknown-production-presence",
        }:
            fail(errors, f"{fixture_id}: unresolved intake must not route directly to ponytail")

    unknown_production = by_id.get("or-gov5-unknown-production-presence")
    if unknown_production:
        request = unknown_production.get("request", "").lower()
        if "do not know" not in request and "unknown" not in request:
            fail(errors, "or-gov5-unknown-production-presence: request must preserve unresolved production presence")
        if "chronicler" not in unknown_production.get("supporting_skills", []):
            fail(errors, "or-gov5-unknown-production-presence: Chronicler must be included")
        if "PRODUCTION_PRESENCE_UNRESOLVED" not in unknown_production.get("expected_notes", []):
            fail(errors, "or-gov5-unknown-production-presence: unresolved-production note is required")

    dagger = by_id.get("or-gov5-unauthorized-dagger")
    if dagger:
        if dagger.get("governance_status") != "BLOCKED_PENDING_AUTHORIZATION":
            fail(errors, "or-gov5-unauthorized-dagger: Dagger must remain blocked pending authorization")
        if dagger.get("expected_gate") != "BLOCKED_PENDING_AUTHORIZATION":
            fail(errors, "or-gov5-unauthorized-dagger: expected gate must remain blocked pending authorization")

    for fixture_id in ("or-gov5-unsupported-capacity-claim", "or-gov5-compound-prove-500-rps"):
        fixture = by_id.get(fixture_id)
        if fixture and fixture.get("expected_outcome") != "NOT_PROVEN":
            fail(errors, f"{fixture_id}: unsupported quantified claim must remain NOT_PROVEN")


def main(argv=None):
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    fixture_path = repo_root / "tests" / "behavior" / "router-contract-fixtures.json"
    skill_index_path = repo_root / "SKILL_INDEX.md"
    routing_map_path = repo_root / "ROUTING_MAP.md"

    errors = []

    registered = load_skill_slugs(repo_root)
    missing_registered = REQUIRED_SKILLS - registered
    if missing_registered:
        fail(errors, f"Missing required registered skills: {sorted(missing_registered)}")

    skill_index_skills = parse_markdown_table_first_column_set(skill_index_path)
    routing_map_skills = parse_markdown_table_first_column_set(routing_map_path)
    for skill in REQUIRED_SKILLS:
        if skill not in skill_index_skills:
            fail(errors, f"SKILL_INDEX.md missing skill row for {skill}")
        if skill not in routing_map_skills and skill != "weaver":
            fail(errors, f"ROUTING_MAP.md missing skill reference for {skill}")

    fixtures = load_json(fixture_path)
    if not isinstance(fixtures, list):
        fail(errors, "router-contract-fixtures.json must contain a top-level list")
    else:
        validate_fixture_schema(fixtures, registered, errors)
        validate_expected_routing_rules(fixtures, errors)
        validate_ssu_fixtures(fixtures, errors)
        validate_or_gov5_fixtures(fixtures, errors)

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] routing contracts are deterministic and internally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
