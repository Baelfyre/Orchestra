import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "behavior" / "specialist-hardening-evaluation-fixtures.json"
PACKS = {
    "weaver": "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md",
    "conductor": "ROUTING_EVALUATION_GUIDE.md",
    "the-tuner": "COORDINATION_EVALUATION_GUIDE.md",
    "arbiter": "CONTINUITY_EVALUATION_GUIDE.md",
}


def require(text, *needles):
    missing = [item for item in needles if item not in text]
    if missing:
        raise AssertionError(f"Missing SK10 hardening markers: {missing}")


def main():
    for slug, guide in PACKS.items():
        source = ROOT / "skills" / slug
        codex = ROOT / "adapters" / "codex" / "skills" / slug
        assert (source / guide).read_bytes() == (codex / guide).read_bytes(), f"Parity failed: {slug}/{guide}"
        assert guide in (source / "SKILL.md").read_text(encoding="utf-8")

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    assert data["schema_version"] == "1.0.0"
    assert len(scenarios) == 10
    ids = [case["id"] for case in scenarios]
    assert len(ids) == len(set(ids))
    assert {case["owner"] for case in scenarios} == set(PACKS)
    assert {case["tuner"] for case in scenarios} == {"ACTIVATE", "BYPASS"}
    for case in scenarios:
        assert set(case) == {"id", "owner", "tuner", "condition", "expected", "protected_action"}
        assert case["condition"] and case["expected"]

    by_id = {case["id"]: case for case in scenarios}
    assert by_id["dagger-without-grant"]["expected"] == "STOP"
    assert by_id["green-checks-release-claim"]["protected_action"] is True
    assert by_id["contradictory-contracts"]["expected"] == "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED"
    assert by_id["stale-head-after-green"]["expected"] == "WAIT_FOR_EVIDENCE"

    require((ROOT / "skills/weaver/MODEL_TRACEABILITY_INVALIDATION_GUIDE.md").read_text(encoding="utf-8"), "DIAGRAM_STALE", "SOURCE_CONTRADICTION", "never invent")
    require((ROOT / "skills/conductor/ROUTING_EVALUATION_GUIDE.md").read_text(encoding="utf-8"), "Dagger without authorization", "single-owner task", "does not authorize")
    require((ROOT / "skills/the-tuner/COORDINATION_EVALUATION_GUIDE.md").read_text(encoding="utf-8"), "without choosing a winner", "Re-entry Minimality", "does not dispatch")
    require((ROOT / "skills/arbiter/CONTINUITY_EVALUATION_GUIDE.md").read_text(encoding="utf-8"), "WAIT_FOR_EVIDENCE", "ESCALATE_HUMAN", "API success alone")
    print("SK10 specialist hardening evaluation passed for 10 adversarial scenarios and 4 mirrored guides.")


if __name__ == "__main__":
    main()
