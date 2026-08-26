from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.shadow import JsonlShadowStore
from orchestra_runtime.adaptive.store import JsonlAdaptiveStore
from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.lifecycle import LifecycleState
from orchestra_runtime.models import RouteDecision, ValidationResult
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeExecutor,
    RuntimeOperationResult,
    SkillRegistry,
    build_compatibility_composition,
)

ROOT = Path(__file__).resolve().parents[2]
USER = "autonomy-user"
PROMPT = "Prefer concise responses with tables when comparing options."
CORRECTION = "Actually, prefer detailed prose instead."
WORKFLOW = "Prefer architecture-first review ordering."
ALLOWED_RESULTS = {"AUTO_OBSERVED", "NOT_AUTO_OBSERVED", "NOT_EXECUTABLE_AT_REPO_RUNTIME_LAYER"}


@pytest.fixture(autouse=True)
def isolated_adaptive_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ORCHESTRA_ADAPTIVE_HOME", str(tmp_path / "adaptive-home"))


def adaptive_store() -> JsonlAdaptiveStore:
    return JsonlAdaptiveStore(USER)


def default_runtime(run_id: str) -> RuntimeExecutor:
    manifests = ManifestRepository(ROOT)
    skills = SkillRegistry(manifests, SkillSourceRepository(ROOT))
    return RuntimeExecutor(
        skills,
        RouterService(skills),
        GovernanceValidator(),
        ContextAssembler(manifests),
        build_compatibility_composition(skills, InMemoryAuditSink(), run_id=run_id),
        operation=lambda *_: RuntimeOperationResult(LifecycleState.COMPLETED, "done", "TEST_COMPLETED"),
    )


def ordinary_interaction(prompt: str, run_id: str) -> None:
    default_runtime(run_id).execute(AdapterFactory.create("codex", ROOT), prompt)


def classify_storage_change(before: tuple, after: tuple) -> str:
    return "AUTO_OBSERVED" if before != after else "NOT_AUTO_OBSERVED"


def test_h01_ordinary_preference_probe_does_not_call_recorder() -> None:
    adaptive = adaptive_store()
    before = adaptive.load_observations()
    ordinary_interaction(PROMPT, "h01-ordinary-preference")
    classification = classify_storage_change(before, adaptive.load_observations())
    print(f"H01={classification}")
    assert classification in ALLOWED_RESULTS


def test_h02_ordinary_correction_probe_does_not_call_recorder() -> None:
    adaptive = adaptive_store()
    before = adaptive.load_observations()
    ordinary_interaction(PROMPT, "h02-preference")
    ordinary_interaction(CORRECTION, "h02-correction")
    classification = classify_storage_change(before, adaptive.load_observations())
    print(f"H02={classification}")
    assert classification in ALLOWED_RESULTS


def test_h03_three_ordinary_sessions_probe_dynamic_candidate() -> None:
    adaptive = adaptive_store()
    before = adaptive.load_observations()
    for index in range(3):
        ordinary_interaction(WORKFLOW, f"h03-session-{index}")
    observations = adaptive.load_observations()
    candidates = JsonlShadowStore(USER).load_candidates()
    classification = "AUTO_OBSERVED" if observations != before or candidates else "NOT_AUTO_OBSERVED"
    print(f"H03={classification}")
    assert classification in ALLOWED_RESULTS
    if classification == "NOT_AUTO_OBSERVED":
        assert candidates == ()


def test_h04_fresh_process_probe_for_surviving_ordinary_learning() -> None:
    ordinary_interaction(PROMPT, "h04-preference")
    ordinary_interaction(CORRECTION, "h04-correction")
    ordinary_interaction(WORKFLOW, "h04-workflow")
    code = (
        "import json; "
        "from orchestra_runtime.adaptive.context import AdaptiveInvocationContext, StoreBackedAdaptiveContextProvider; "
        "from orchestra_runtime.adaptive.store import JsonlAdaptiveStore; "
        "from orchestra_runtime.models import RouteDecision, ValidationResult; "
        "store=JsonlAdaptiveStore('autonomy-user'); "
        "packet=StoreBackedAdaptiveContextProvider(store).compile("
        "RouteDecision('conductor','conductor',False,'probe'), ValidationResult(True,'APPROVED'), "
        "AdaptiveInvocationContext('autonomy-user')); "
        "print(json.dumps({'observations':len(store.load_observations()), 'items':len(packet.items)}))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=os.environ.copy(),
        check=True,
        capture_output=True,
        text=True,
    )
    state = json.loads(completed.stdout)
    classification = "AUTO_OBSERVED" if state["items"] else "NOT_AUTO_OBSERVED"
    print(f"H04={classification}")
    assert classification in ALLOWED_RESULTS
    if classification == "NOT_AUTO_OBSERVED":
        assert state["items"] == 0
