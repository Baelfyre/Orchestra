from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from orchestra_runtime.adaptive.context import (
    AdaptiveInvocationContext,
    AdaptiveRuntimeExecutor,
    StoreBackedAdaptiveContextProvider,
)
from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import append_explicit_preference, append_inferred_candidate
from orchestra_runtime.adaptive.profile import materialize_profile
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
    RuntimeOperationResult,
    SkillRegistry,
    build_compatibility_composition,
)

ROOT = Path(__file__).resolve().parents[2]
USER = "fixture-user"
PROJECT = "Baelfyre/Orchestra"
TIMES = tuple(f"2026-08-18T00:0{i}:00Z" for i in range(8))


def scope(kind: str, *, specialist: str | None = None) -> AdaptiveScope:
    return AdaptiveScope(
        kind,
        USER,
        project_key=None if kind == "global_user" else PROJECT,
        specialist_slug=specialist,
        task_session_key="task-1" if kind == "task_session" else None,
    )


def route(slug: str) -> RouteDecision:
    return RouteDecision(slug, slug, False, "test route")


def seed_store(tmp_path: Path) -> JsonlAdaptiveStore:
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    records = (
        (scope("project"), "project-compact", False, "project"),
        (scope("specialist", specialist="scribe"), "scribe-compact", False, "scribe"),
        (scope("task_session", specialist="scribe"), "task-compact", True, "current"),
    )
    for index, (record_scope, value, current, source) in enumerate(records):
        append_explicit_preference(
            store,
            scope=record_scope,
            subject_key="docs.response_style",
            value=value,
            occurred_at=TIMES[index],
            source_ref=f"test:{source}",
            current_instruction=current,
        )
    append_inferred_candidate(
        store,
        scope=scope("project"),
        subject_key="docs.example_density",
        value="low",
        confidence=0.7,
        evidence_refs=("test:evidence",),
        occurred_at=TIMES[3],
        source_ref="test:candidate",
    )
    for index, (record_scope, source) in enumerate(
        (
            (scope("specialist", specialist="scribe"), "scribe"),
            (scope("project"), "project"),
        ),
        start=4,
    ):
        store.append(
            event_type="GOVERNED_OUTCOME_RECORDED",
            scope=record_scope,
            subject_key="workflow.phase_outcome",
            evidence_class="GOVERNED_OUTCOME",
            source_type="orchestra_phase_retrospective",
            source_ref=f"retrospective:{source}",
            occurred_at=TIMES[index],
            payload={"phase_id": "A2", "phase_status": "accepted"},
        )
    profile = materialize_profile(USER, store.load_observations(), generated_at=TIMES[6])
    store.write_profile(profile)
    return store


def build_executor(store, *, operation=None, governance=None, provider=None, run_id="a2-test"):
    manifests = ManifestRepository(ROOT)
    skills = SkillRegistry(manifests, SkillSourceRepository(ROOT))
    return AdaptiveRuntimeExecutor(
        skills,
        RouterService(skills),
        governance or GovernanceValidator(),
        ContextAssembler(manifests),
        build_compatibility_composition(skills, InMemoryAuditSink(), run_id=run_id),
        operation=operation,
        adaptive_provider=provider or StoreBackedAdaptiveContextProvider(store),
    )


def test_a2_precedence_scope_isolation_and_candidate_threshold(tmp_path: Path):
    provider = StoreBackedAdaptiveContextProvider(seed_store(tmp_path))
    validation = ValidationResult(True, "APPROVED")
    scribe = provider.compile(
        route("scribe"),
        validation,
        AdaptiveInvocationContext(
            USER,
            project_key=PROJECT,
            task_session_key="task-1",
            min_candidate_confidence=0.6,
        ),
    )
    items = {item.subject_key: item for item in scribe.items}
    assert items["docs.response_style"].value == "task-compact"
    assert items["docs.response_style"].precedence == "EXPLICIT_CURRENT_INSTRUCTION"
    assert items["docs.example_density"].precedence == "INFERRED_CANDIDATE"
    assert {item.source_ref for item in scribe.outcome_evidence} == {
        "retrospective:scribe",
        "retrospective:project",
    }

    beatrice = provider.compile(
        route("beatrice"),
        validation,
        AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-1"),
    )
    other = {item.subject_key: item for item in beatrice.items}
    assert other["docs.response_style"].value == "project-compact"
    assert "docs.example_density" not in other
    assert all(item.scope.specialist_slug != "scribe" for item in beatrice.items)
    assert {item.source_ref for item in beatrice.outcome_evidence} == {"retrospective:project"}


def test_a2_privacy_stale_profile_and_schema(tmp_path: Path):
    with pytest.raises(ValueError, match="credential-like"):
        AdaptiveInvocationContext(
            USER,
            project_key=PROJECT,
            repository_refs=("Bearer abcdefghijklmnopqrstuvwxyz0123456789",),
        )

    store = seed_store(tmp_path)
    provider = StoreBackedAdaptiveContextProvider(store)
    packet = provider.compile(
        route("scribe"),
        ValidationResult(True, "APPROVED"),
        AdaptiveInvocationContext(USER, project_key=PROJECT, min_candidate_confidence=0.6),
    )
    schema = json.loads((ROOT / "machine/schemas/adaptive-context.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(packet.to_dict())

    append_explicit_preference(
        store,
        scope=scope("project"),
        subject_key="docs.detail_level",
        value="bounded",
        occurred_at=TIMES[7],
        source_ref="test:later",
    )
    stale = provider.compile(
        route("scribe"),
        ValidationResult(True, "APPROVED"),
        AdaptiveInvocationContext(USER, project_key=PROJECT),
    )
    assert stale.status == "DETERMINISTIC_FALLBACK"
    assert stale.reason_code == "STALE_OR_INCOMPATIBLE_PROFILE"
    assert stale.items == ()
    assert stale.outcome_evidence == ()


def test_a2_runtime_attaches_only_after_governance_and_preserves_route(tmp_path: Path):
    store = seed_store(tmp_path)
    captured = {}

    def operation(adapter_name, decision, validation):
        captured["packet"] = decision.metadata["adaptive_context"]
        return RuntimeOperationResult(LifecycleState.COMPLETED, "completed", "TEST_COMPLETED")

    executor = build_executor(store, operation=operation, run_id="a2-route")
    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_context=AdaptiveInvocationContext(USER, project_key=PROJECT),
    )
    assert result.success is True
    assert captured["packet"]["advisory_only"] is True
    assert result.route.skill_slug == "conductor"
    assert "adaptive_context" not in result.route.metadata
    assert result.authority_decision_id and result.capability_decision_id

    class SpyProvider:
        calls = 0

        def compile(self, decision, validation, invocation):
            self.calls += 1
            raise AssertionError("provider must not run")

    class BlockingGovernance:
        def validate(self, decision, context):
            return ValidationResult(False, "BLOCKED_PENDING_VALIDATION", ("blocked",), ("test",))

    spy = SpyProvider()
    blocked = build_executor(
        store,
        governance=BlockingGovernance(),
        provider=spy,
        run_id="a2-blocked",
    ).execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_context=AdaptiveInvocationContext(USER, project_key=PROJECT),
    )
    assert blocked.success is False
    assert spy.calls == 0


def test_a2_provider_failure_and_delegation_boundary(tmp_path: Path):
    store = seed_store(tmp_path)
    captured = {}

    class FailingProvider:
        def compile(self, decision, validation, invocation):
            raise RuntimeError("private-secret-diagnostic")

    def operation(adapter_name, decision, validation):
        captured["packet"] = decision.metadata["adaptive_context"]
        return RuntimeOperationResult(LifecycleState.COMPLETED, "completed", "TEST_COMPLETED")

    executor = build_executor(
        store,
        operation=operation,
        provider=FailingProvider(),
        run_id="a2-fallback",
    )
    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "@Orchestra rerun the prompt",
        adaptive_context=AdaptiveInvocationContext(USER, project_key=PROJECT),
    )
    assert result.success is True
    assert captured["packet"]["reason_code"] == "ADAPTIVE_CONTEXT_UNAVAILABLE"
    assert "private-secret-diagnostic" not in json.dumps(captured["packet"])

    with pytest.raises(ValueError, match="not enabled for delegated execution"):
        executor.execute_delegated(
            AdapterFactory.create("codex", ROOT),
            "@Orchestra rerun the prompt",
            None,  # type: ignore[arg-type]
            adaptive_context=AdaptiveInvocationContext(USER, project_key=PROJECT),
        )
