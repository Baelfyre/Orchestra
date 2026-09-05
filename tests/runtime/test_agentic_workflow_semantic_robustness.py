from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import RouterService, SkillRegistry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "agentic-workflow" / "awf-semantic-robustness.v1.json"


def _router() -> RouterService:
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    return RouterService(registry)


def _context(prompt: str) -> ContextPackage:
    return ContextPackage(
        adapter_name="semantic-robustness",
        prompt=prompt,
        project_root=ROOT,
        available_commands=(
            "conductor","the-steward","the-governor","arbiter","overseer","the-tuner",
            "cipher","cloak","dagger","chronicler","weaver","scribe","clockwork","ponytail",
        ),
        manifest_version="semantic-robustness",
        metadata={},
    )


def test_awf_semantic_robustness_contrast_corpus():
    suite = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert suite["schema_version"] == "orchestra.awf-semantic-robustness.v1"
    assert len(suite["cases"]) >= 30

    router = _router()
    failures: list[str] = []
    for case in suite["cases"]:
        prompt = case["prompt"]
        decision = router.route(
            Command("conductor", prompt, "semantic-robustness"),
            _context(prompt),
        )
        task = decision.metadata["agentic_task_profile"]
        profile = decision.metadata["agentic_workflow_profile"]

        for key, expected in case.get("expect", {}).items():
            actual = profile[key] if key in profile else task[key]
            if actual != expected:
                failures.append(
                    f"{case['id']}: expected {key}={expected!r}, got {actual!r}; "
                    f"domains={task['authority_domains']}; specialists={profile['required_specialists']}; "
                    f"patterns={profile['selected_patterns']}"
                )

        for specialist in case.get("include", {}).get("specialists", []):
            if specialist not in profile["required_specialists"]:
                failures.append(
                    f"{case['id']}: missing specialist {specialist}; "
                    f"selected={profile['required_specialists']}"
                )

        for domain in case.get("include", {}).get("authority_domains", []):
            if domain not in task["authority_domains"]:
                failures.append(
                    f"{case['id']}: missing authority domain {domain}; "
                    f"domains={task['authority_domains']}"
                )

        for specialist in case.get("avoid", {}).get("specialists", []):
            if specialist in profile["required_specialists"]:
                failures.append(
                    f"{case['id']}: forbidden specialist {specialist}; "
                    f"selected={profile['required_specialists']}"
                )

        for domain in case.get("avoid", {}).get("authority_domains", []):
            if domain in task["authority_domains"]:
                failures.append(
                    f"{case['id']}: forbidden authority domain {domain}; "
                    f"domains={task['authority_domains']}"
                )

        for pattern in case.get("avoid", {}).get("patterns", []):
            if pattern in profile["selected_patterns"]:
                failures.append(
                    f"{case['id']}: forbidden pattern {pattern}; "
                    f"patterns={profile['selected_patterns']}"
                )

        if profile["max_parallel_specialists"] != 1:
            failures.append(f"{case['id']}: OEE max_parallel_specialists changed")
        if profile["authority_expansion"] is not False:
            failures.append(f"{case['id']}: authority expansion became true")

    assert not failures, "\n".join(failures)
