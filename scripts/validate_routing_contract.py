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
}

VALID_MODES = {"Ideation", "Prototype", "Implementation", "Governed", "Audit", "Release", "Destructive"}
VALID_GOVERNANCE = {"NOT_REQUIRED", "CONDITIONAL", "REQUIRED", "BLOCKED_PENDING_AUTHORIZATION"}
VALID_GATES = {"NONE", "CONTINUITY_REQUIRED", "BLOCKED_PENDING_AUTHORIZATION", "DECISION_PROTOCOL_REQUIRED"}
KNOWN_CONTEXTS = {
    "SKILL_INDEX.md",
    "ROUTING_MAP.md",
    "docs/routing/EXECUTION_MODES_POLICY.md",
    "docs/governance/GOVERNANCE_LAYER.md",
    "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md",
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

    missing_skill_coverage = REQUIRED_SKILLS - primary_coverage
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

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] routing contracts are deterministic and internally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
