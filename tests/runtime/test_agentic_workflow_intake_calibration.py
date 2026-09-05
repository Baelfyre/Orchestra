from __future__ import annotations

import json
from pathlib import Path

from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import RouterService, SkillRegistry

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "agentic-workflow" / "awf-intake-calibration.v1.json"


def _router() -> RouterService:
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    return RouterService(registry)


def _context(prompt: str) -> ContextPackage:
    return ContextPackage(
        adapter_name="calibration",
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
        manifest_version="calibration",
        metadata={},
    )


def test_awf_higher_calibration_corpus_matches_expected_topology():
    suite = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert suite["schema_version"] == "orchestra.awf-intake-calibration.v1"
    assert len(suite["cases"]) >= 15

    router = _router()
    for case in suite["cases"]:
        prompt = case["prompt"]
        decision = router.route(
            Command("conductor", prompt, "calibration"),
            _context(prompt),
        )
        task = decision.metadata["agentic_task_profile"]
        profile = decision.metadata["agentic_workflow_profile"]
        trace = decision.metadata["agentic_selection_trace"]
        telemetry = decision.metadata["agentic_workflow_telemetry"]
        expected = case["expected"]

        for key in ("authority_domains", "primary_owner", "execution_mode", "risk_level"):
            assert task[key] == expected[key], f"{case['id']} task mismatch: {key}"

        for key in (
            "required_specialists",
            "selected_patterns",
            "concurrency_mode",
            "human_gate_required",
        ):
            assert profile[key] == expected[key], f"{case['id']} profile mismatch: {key}"

        assert profile["max_parallel_specialists"] == suite["invariants"]["max_parallel_specialists"]
        assert profile["parallel_groups"] == []
        assert profile["topology_change_requires_human_approval"] is suite["invariants"]["topology_change_requires_human_approval"]
        assert profile["authority_expansion"] is suite["invariants"]["authority_expansion"]
        assert trace["selected_specialists"] == expected["required_specialists"]
        assert trace["selected_patterns"] == expected["selected_patterns"]
        assert trace["human_gate_required"] is expected["human_gate_required"]
        assert telemetry["max_parallel_specialists"] == 1
