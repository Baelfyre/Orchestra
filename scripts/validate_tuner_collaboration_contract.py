import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_STATUSES = {
    "BYPASSED", "COLLECTING", "INCOMPLETE", "CONTRADICTED",
    "READY", "FROZEN", "STALE", "SUPERSEDED", "CLOSED",
}
REQUIRED_GATES = {
    "NONE",
    "CROSS_LAYER_CONTRACT_REQUIRED",
    "CROSS_LAYER_CONTRACT_INCOMPLETE",
    "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED",
    "CROSS_LAYER_CONTRACT_READY",
    "CROSS_LAYER_CONTRACT_STALE",
    "SPECIALIST_REENTRY_REQUIRED",
}
REQUIRED_ACTIVATION_DECISIONS = {
    "BYPASS_SINGLE_OWNER",
    "ACTIVATE_MULTI_DOMAIN",
    "ACTIVATE_LATE_BOUNDARY_CROSSING",
    "ACTIVATE_CONTRADICTION",
    "ACTIVATE_MISSING_OWNER",
    "ACTIVATE_STALE_CONTRACT",
}
REQUIRED_FIXTURE_IDS = {
    "direct-scribe-bypass", "direct-ponytail-bypass",
    "multi-domain-contract-activation", "late-domain-boundary-activation",
    "missing-validation-owner", "cipher-cloak-contradiction",
    "complete-contract-ready", "security-rule-invalidates-architecture",
    "manual-mode-stale-contract", "delegated-envelope-boundary",
    "generated-artifact-lifecycle-missing", "change-identity-required-phase2",
    "dagger-remains-blocked", "unknown-status-fails-closed",
}
REQUIRED_PROTOCOL_TOKENS = {
    "CollaborationSession", "CollaborationGraph", "SpecialistDomainContract",
    "CrossLayerContractPacket", "SpecialistHandoffDelta", "InvalidationEvent",
    "CrossSpecialistContradiction", "GeneratedArtifactLifecycleRecord",
    "CROSS_LAYER_CONTRACT_INCOMPLETE",
    "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED",
    "CROSS_LAYER_CONTRACT_READY", "CROSS_LAYER_CONTRACT_STALE",
    "SPECIALIST_REENTRY_REQUIRED",
}
REQUIRED_BOUNDARIES = {
    "Tuner cannot create or widen authority.",
    "Tuner cannot override The Steward or The Governor.",
    "Tuner cannot issue an Arbiter transition disposition.",
    "Tuner cannot validate its own work.",
    "Conductor remains the exclusive router.",
    "Arbiter remains the continuation and transition-decision authority.",
    "Overseer remains the validation strategy and evidence owner.",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate The Tuner collaboration contract.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_frontmatter(content):
    match = re.search(r"(?s)^---\r?\n(.*?)\r?\n---", content)
    if not match:
        return {}
    result = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def validate(repo_root):
    errors = []
    plugin = load_json(repo_root / "plugin.json")
    entries = {item.get("slug"): item for item in plugin.get("skills", [])}
    tuner_entry = entries.get("the-tuner")
    if not tuner_entry:
        errors.append("plugin.json: missing the-tuner registration")
    else:
        expected = {
            "name": "the-tuner",
            "role": "Cross-Specialist Coordination Specialist",
            "activation_level": "Specialist",
            "depends_on": "conductor",
            "skill_path": "skills/the-tuner/SKILL.md",
        }
        for key, value in expected.items():
            if tuner_entry.get(key) != value:
                errors.append(f"plugin.json: the-tuner {key} must be {value!r}")

    required_paths = [
        repo_root / "skills/the-tuner/SKILL.md",
        repo_root / "skills/the-tuner/OUTPUT_FORMATS.md",
        repo_root / "docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md",
        repo_root / "tests/behavior/tuner-collaboration-fixtures.json",
    ]
    for path in required_paths:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(repo_root).as_posix()}")
    if errors:
        return errors

    skill = required_paths[0].read_text(encoding="utf-8")
    fm = parse_frontmatter(skill)
    for key, value in {
        "name": "the-tuner",
        "slug": "the-tuner",
        "role": "Cross-Specialist Coordination Specialist",
        "activation_level": "Specialist",
        "depends_on": "conductor",
    }.items():
        if fm.get(key) != value:
            errors.append(f"skills/the-tuner/SKILL.md: {key} must be {value!r}")

    for phrase in REQUIRED_BOUNDARIES:
        if phrase not in skill:
            errors.append(f"skills/the-tuner/SKILL.md: missing `{phrase}`")

    protocol = required_paths[2].read_text(encoding="utf-8")
    for token in REQUIRED_PROTOCOL_TOKENS:
        if token not in protocol:
            errors.append(f"coordination protocol: missing `{token}`")
    for phrase in (
        "Conductor remains the exclusive router",
        "The Tuner detects but never resolves a contradiction",
        "A frozen contract is not an implementation authorization by itself",
        "Full contract-hash, staged-patch, untracked-file, added-blob, and artifact-lifecycle enforcement is reserved for Phase 2",
    ):
        if phrase not in protocol:
            errors.append(f"coordination protocol: missing boundary phrase `{phrase}`")

    outputs = required_paths[1].read_text(encoding="utf-8")
    for heading in (
        "## Collaboration Review", "## Cross-Layer Contract Packet",
        "## Contradiction Report", "## Re-entry Recommendation",
    ):
        if heading not in outputs:
            errors.append(f"OUTPUT_FORMATS.md: missing `{heading}`")

    index = (repo_root / "SKILL_INDEX.md").read_text(encoding="utf-8")
    routing = (repo_root / "ROUTING_MAP.md").read_text(encoding="utf-8")
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    conductor = (repo_root / "skills/conductor/SKILL.md").read_text(encoding="utf-8")
    arbiter = (repo_root / "skills/arbiter/SKILL.md").read_text(encoding="utf-8")
    overseer = (repo_root / "skills/overseer/SKILL.md").read_text(encoding="utf-8")
    ponytail = (repo_root / "skills/ponytail/SKILL.md").read_text(encoding="utf-8")

    checks = [
        ("SKILL_INDEX.md", "| `the-tuner` |", index),
        ("ROUTING_MAP.md", "`the-tuner`", routing),
        ("AGENTS.md", "Cross-Specialist Coordination Layer", agents),
        ("Conductor", "CROSS_LAYER_CONTRACT_READY", conductor),
        ("Arbiter", "blocking coordination state", arbiter),
        ("Overseer", "acceptance matrix", overseer),
        ("Ponytail", "behavioral handoff delta", ponytail),
    ]
    for label, token, content in checks:
        if token not in content:
            errors.append(f"{label}: missing `{token}`")

    fixtures = load_json(required_paths[3])
    if not isinstance(fixtures, list):
        return errors + ["tuner fixtures must be a top-level list"]
    seen = set()
    for fixture in fixtures:
        fixture_id = fixture.get("id")
        if not fixture_id:
            errors.append("fixture missing id")
            continue
        if fixture_id in seen:
            errors.append(f"duplicate fixture id: {fixture_id}")
        seen.add(fixture_id)
        for field in (
            "category", "request", "activation_decision", "primary_router",
            "required_specialists", "expected_status", "expected_gate",
            "expected_reentry", "authority_assertions",
        ):
            if field not in fixture:
                errors.append(f"{fixture_id}: missing `{field}`")
        if fixture.get("activation_decision") not in REQUIRED_ACTIVATION_DECISIONS:
            errors.append(f"{fixture_id}: invalid activation decision")
        if fixture.get("expected_status") not in REQUIRED_STATUSES:
            errors.append(f"{fixture_id}: invalid status")
        if fixture.get("expected_gate") not in REQUIRED_GATES:
            errors.append(f"{fixture_id}: invalid gate")
        if fixture.get("primary_router") == "the-tuner":
            errors.append(f"{fixture_id}: the-tuner must never be primary router")
        if fixture.get("activation_decision") == "BYPASS_SINGLE_OWNER":
            if "the-tuner" in fixture.get("required_specialists", []):
                errors.append(f"{fixture_id}: bypass must not activate the-tuner")
        else:
            if fixture.get("primary_router") != "conductor":
                errors.append(f"{fixture_id}: active coordination must remain with conductor")
            if "the-tuner" not in fixture.get("required_specialists", []):
                errors.append(f"{fixture_id}: active coordination must include the-tuner")
        if fixture.get("expected_status") == "CONTRADICTED" and fixture.get("expected_gate") != "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED":
            errors.append(f"{fixture_id}: contradicted state must use contradiction gate")
        if fixture.get("expected_status") == "READY" and fixture.get("expected_gate") != "CROSS_LAYER_CONTRACT_READY":
            errors.append(f"{fixture_id}: ready state must use ready gate")

    missing = REQUIRED_FIXTURE_IDS - seen
    if missing:
        errors.append(f"missing required Tuner fixtures: {sorted(missing)}")
    return errors


def main(argv=None):
    args = parse_args(argv)
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] The Tuner collaboration contract is deterministic and internally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
