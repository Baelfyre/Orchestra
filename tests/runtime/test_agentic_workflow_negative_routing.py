from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import RouterService, SkillRegistry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "agentic-workflow" / "awf-negative-routing.v1.json"


def _router() -> RouterService:
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    return RouterService(registry)


def _context(prompt: str) -> ContextPackage:
    return ContextPackage(
        adapter_name="negative-calibration",
        prompt=prompt,
        project_root=ROOT,
        available_commands=(
            "conductor",
            "the-steward",
            "the-governor",
            "arbiter",
            "overseer",
            "the-tuner",
            "cipher",
            "cloak",
            "dagger",
            "chronicler",
            "weaver",
            "scribe",
            "clockwork",
            "ponytail",
        ),
        manifest_version="negative-calibration",
        metadata={},
    )


def test_awf_negative_routing_corpus_avoids_false_activation():
    suite = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert suite["schema_version"] == "orchestra.awf-negative-routing.v1"
    assert len(suite["cases"]) >= 20

    router = _router()
    for case in suite["cases"]:
        prompt = case["prompt"]
        decision = router.route(
            Command("conductor", prompt, "negative-calibration"),
            _context(prompt),
        )
        task = decision.metadata["agentic_task_profile"]
        profile = decision.metadata["agentic_workflow_profile"]
        expected = case["expect"]
        avoid = case["avoid"]

        for key, value in expected.items():
            actual = profile[key] if key in profile else task[key]
            assert actual == value, f"{case['id']} expected {key}={value!r}, got {actual!r}"

        for domain in avoid.get("authority_domains", []):
            assert domain not in task["authority_domains"], (
                f"{case['id']} falsely activated authority domain {domain}: {task['authority_domains']}"
            )

        for specialist in avoid.get("specialists", []):
            assert specialist not in profile["required_specialists"], (
                f"{case['id']} falsely selected specialist {specialist}: "
                f"{profile['required_specialists']}"
            )

        for pattern in avoid.get("patterns", []):
            assert pattern not in profile["selected_patterns"], (
                f"{case['id']} falsely selected pattern {pattern}: {profile['selected_patterns']}"
            )

        assert profile["max_parallel_specialists"] == 1
        assert profile["authority_expansion"] is False
        assert profile["topology_change_requires_human_approval"] is False
