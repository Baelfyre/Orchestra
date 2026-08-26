from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from orchestra_runtime.adaptive.context import (
    AdaptiveInvocationContext,
    AdaptiveRuntimeExecutor,
    StoreBackedAdaptiveContextProvider,
)
from orchestra_runtime.adaptive.models import AdaptiveScope
from orchestra_runtime.adaptive.observations import (
    append_explicit_preference,
    append_inferred_candidate,
    append_preference_removal,
)
from orchestra_runtime.adaptive.portable_memory import (
    MemoryBackendDescriptor,
    build_portable_memory_candidate,
)
from orchestra_runtime.adaptive.profile import materialize_profile
from orchestra_runtime.adaptive.shadow import (
    JsonlShadowStore,
    build_shadow_comparison,
    build_shadow_signal,
    extract_a1_shadow_signals,
    learn_shadow_candidates,
)
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
USER = "efficacy-user"
PROJECT = "Baelfyre/Orchestra"
T0 = "2026-08-26T00:00:00Z"
T1 = "2026-08-26T00:01:00Z"
T2 = "2026-08-26T00:02:00Z"
T3 = "2026-08-26T00:03:00Z"
T4 = "2026-08-26T00:04:00Z"
D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64


@pytest.fixture(autouse=True)
def isolated_adaptive_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ORCHESTRA_ADAPTIVE_HOME", str(tmp_path / "adaptive-home"))


def scope(
    scope_type: str = "project",
    *,
    user: str = USER,
    project: str | None = PROJECT,
    specialist: str | None = None,
    task: str | None = None,
) -> AdaptiveScope:
    if scope_type == "global_user":
        project = specialist = task = None
    return AdaptiveScope(
        scope_type=scope_type,
        user_key=user,
        project_key=project,
        specialist_slug=specialist,
        task_session_key=task,
    )


def store(user: str = USER) -> JsonlAdaptiveStore:
    return JsonlAdaptiveStore(user)


def route(slug: str = "scribe") -> RouteDecision:
    return RouteDecision(slug, slug, False, "test route")


def profile_for(adaptive: JsonlAdaptiveStore, generated_at: str = T4):
    profile = materialize_profile(adaptive.user_key, adaptive.load_observations(), generated_at=generated_at)
    adaptive.write_profile(profile)
    return profile


def preference(
    adaptive: JsonlAdaptiveStore,
    *,
    value: object = "compact",
    subject: str = "docs.response_style",
    record_scope: AdaptiveScope | None = None,
    occurred_at: str = T0,
    source_ref: str = "test:preference",
    current_instruction: bool = False,
    correction: bool = False,
):
    return append_explicit_preference(
        adaptive,
        scope=record_scope or scope(user=adaptive.user_key),
        subject_key=subject,
        value=value,
        occurred_at=occurred_at,
        source_ref=source_ref,
        current_instruction=current_instruction,
        correction=correction,
    )


def signal(
    *,
    value: object = "compact",
    subject: str = "docs.response_style",
    record_scope: AdaptiveScope | None = None,
    signal_type: str = "USER_SELECTION",
    source_digest: str = D0,
    occurred_at: str = T0,
    source_ref: str | None = None,
):
    return build_shadow_signal(
        scope=record_scope or scope(),
        signal_type=signal_type,
        subject_key=subject,
        observed_value=value,
        source_kind="A1_VALIDATED_OBSERVATION",
        source_ref=source_ref or f"evidence:{source_digest[:8]}:{occurred_at}",
        source_digest=source_digest,
        observed_at=occurred_at,
    )


def runtime_executor(
    adaptive: JsonlAdaptiveStore,
    *,
    operation,
    governance=None,
    provider=None,
    run_id: str,
) -> AdaptiveRuntimeExecutor:
    manifests = ManifestRepository(ROOT)
    skills = SkillRegistry(manifests, SkillSourceRepository(ROOT))
    return AdaptiveRuntimeExecutor(
        skills,
        RouterService(skills),
        governance or GovernanceValidator(),
        ContextAssembler(manifests),
        build_compatibility_composition(skills, InMemoryAuditSink(), run_id=run_id),
        operation=operation,
        adaptive_provider=provider or StoreBackedAdaptiveContextProvider(adaptive),
    )


def portable_candidate() -> dict:
    candidate = learn_shadow_candidates(
        (
            signal(record_scope=scope(project="orchestra"), source_digest=D0),
            signal(record_scope=scope(project="orchestra"), source_digest=D1, occurred_at=T1),
        )
    )[0]
    return candidate.to_dict()


def test_a01_explicit_preference_is_persisted(tmp_path: Path) -> None:
    adaptive = store()
    preference(adaptive)
    record = json.loads(adaptive.observations_path.read_text(encoding="utf-8"))
    assert record["event_type"] == "EXPLICIT_PREFERENCE_SET"
    assert record["payload"] == {"value": "compact"}
    assert adaptive.load_observations()[0].payload["value"] == "compact"


def test_a02_preference_recovers_across_new_process(tmp_path: Path) -> None:
    adaptive = store()
    preference(adaptive)
    code = (
        "import json; "
        "from orchestra_runtime.adaptive.store import JsonlAdaptiveStore; "
        "records=JsonlAdaptiveStore('efficacy-user').load_observations(); "
        "print(json.dumps([item.to_dict() for item in records], sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=os.environ.copy(),
        check=True,
        capture_output=True,
        text=True,
    )
    recovered = json.loads(completed.stdout)
    assert recovered == [item.to_dict() for item in adaptive.load_observations()]


def test_a03_profile_head_matches_validated_log_head() -> None:
    adaptive = store()
    preference(adaptive)
    profile = profile_for(adaptive)
    assert profile.source_head_digest == adaptive.load_observations()[-1].digest


def test_a04_stale_profile_falls_back_then_recovers() -> None:
    adaptive = store()
    preference(adaptive)
    profile_for(adaptive)
    preference(adaptive, subject="docs.detail_level", value="bounded", occurred_at=T1, source_ref="test:later")
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    stale = provider.compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT)
    )
    assert stale.status == "DETERMINISTIC_FALLBACK"
    assert stale.reason_code == "STALE_OR_INCOMPATIBLE_PROFILE"
    assert stale.items == ()
    recovered = adaptive.recover_profile(generated_at=T2)
    current = provider.compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT)
    )
    assert recovered.source_head_digest == adaptive.load_observations()[-1].digest
    assert {item.subject_key for item in current.items} == {"docs.response_style", "docs.detail_level"}


def test_a05_tampering_jsonl_record_fails_closed() -> None:
    adaptive = store()
    preference(adaptive)
    preference(adaptive, subject="docs.detail_level", value="bounded", occurred_at=T1, source_ref="test:second")
    lines = adaptive.observations_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["payload"]["value"] = "tampered"
    lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    adaptive.observations_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash-chain mismatch"):
        adaptive.load_observations()


def test_a06_compaction_preserves_logical_profile_state_and_invalidates_profile() -> None:
    adaptive = store()
    preference(adaptive)
    adaptive.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=scope(user=USER),
        subject_key="workflow.phase_outcome",
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref="retrospective:test",
        occurred_at=T1,
        payload={"phase_id": "A3", "phase_status": "accepted"},
    )
    before = profile_for(adaptive)
    removed = adaptive.compact(
        lambda observation: observation.event_type != "GOVERNED_OUTCOME_RECORDED",
        occurred_at=T2,
        reason="test-compaction",
    )
    assert removed == 1
    assert adaptive.load_profile() is None
    after = adaptive.recover_profile(generated_at=T3)
    assert after.patterns == before.patterns
    assert after.source_head_digest != before.source_head_digest


def test_b01_global_preference_is_available_at_global_scope() -> None:
    adaptive = store()
    preference(adaptive, record_scope=scope("global_user"))
    profile_for(adaptive)
    packet = StoreBackedAdaptiveContextProvider(adaptive).compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT)
    )
    assert packet.items[0].scope.scope_type == "global_user"


def test_b02_explicit_correction_latest_value_wins() -> None:
    adaptive = store()
    preference(adaptive, value="P1", source_ref="test:p1")
    preference(adaptive, value="P2", occurred_at=T1, source_ref="test:p2", correction=True)
    profile = profile_for(adaptive)
    assert len(profile.patterns) == 1
    assert profile.patterns[0].value == "P2"
    assert profile.patterns[0].status == "confirmed"


def test_b03_explicit_removal_removes_effective_preference() -> None:
    adaptive = store()
    preference(adaptive)
    append_preference_removal(
        adaptive,
        scope=scope(),
        subject_key="docs.response_style",
        occurred_at=T1,
        source_ref="test:remove",
    )
    assert profile_for(adaptive).patterns == ()


def test_b04_project_preference_overrides_global_only_in_matching_project() -> None:
    adaptive = store()
    preference(adaptive, value="P1", record_scope=scope("global_user"), source_ref="test:global")
    preference(adaptive, value="P2", record_scope=scope(), occurred_at=T1, source_ref="test:project")
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    inside = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT))
    outside = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key="Baelfyre/Other"))
    assert inside.items[0].value == "P2"
    assert outside.items[0].value == "P1"


def test_b05_task_session_precedence_does_not_leak() -> None:
    adaptive = store()
    preference(adaptive, value="global", record_scope=scope("global_user"), source_ref="test:global")
    preference(adaptive, value="project", source_ref="test:project")
    preference(
        adaptive,
        value="task",
        record_scope=scope("task_session", task="task-1"),
        occurred_at=T1,
        source_ref="test:task",
    )
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    task = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-1"))
    other_task = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-2"))
    assert task.items[0].value == "task"
    assert other_task.items[0].value == "project"
    assert all(item.value != "task" for item in other_task.items)


def test_b06_current_instruction_outranks_stored_preference() -> None:
    adaptive = store()
    preference(adaptive, value="stored", source_ref="test:stored")
    preference(
        adaptive,
        value="current",
        record_scope=scope("task_session", task="task-1"),
        occurred_at=T1,
        source_ref="test:current",
        current_instruction=True,
    )
    profile_for(adaptive)
    packet = StoreBackedAdaptiveContextProvider(adaptive).compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-1")
    )
    assert packet.items[0].value == "current"
    assert packet.items[0].precedence == "EXPLICIT_CURRENT_INSTRUCTION"


def test_c01_one_supporting_digest_forms_no_candidate() -> None:
    assert learn_shadow_candidates((signal(),)) == ()


def test_c02_two_distinct_supporting_digests_form_candidate() -> None:
    candidates = learn_shadow_candidates((signal(), signal(source_digest=D1, occurred_at=T1)))
    assert len(candidates) == 1
    assert candidates[0].distinct_support_count == 2
    assert candidates[0].status == "CANDIDATE"


def test_c03_duplicate_source_digest_counts_once() -> None:
    candidates = learn_shadow_candidates(
        (
            signal(source_digest=D0),
            signal(source_digest=D0, occurred_at=T1, source_ref="duplicate:digest"),
        )
    )
    assert candidates == ()


def test_c04_three_supports_are_bounded_and_repeatable_in_fresh_homes(tmp_path: Path) -> None:
    signals = (signal(source_digest=D0), signal(source_digest=D1, occurred_at=T1), signal(source_digest=D2, occurred_at=T2))
    results = []
    for root in (tmp_path / "one", tmp_path / "two"):
        shadow = JsonlShadowStore(USER, root=root)
        for item in signals:
            shadow.append_signal(item)
        results.append(learn_shadow_candidates(shadow.load_signals())[0])
    assert results[0].to_dict() == results[1].to_dict()
    assert results[0].digest == results[1].digest
    assert results[0].confidence == 0.74
    assert results[0].confidence <= 1.0


def test_c05_contradictory_values_remain_bounded_shadow_candidates() -> None:
    candidates = learn_shadow_candidates(
        (
            signal(value="compact", source_digest=D0),
            signal(value="compact", source_digest=D1, occurred_at=T1),
            signal(value="detailed", source_digest=D2, occurred_at=T2),
            signal(value="detailed", source_digest=D3, occurred_at=T3),
        )
    )
    assert {item.candidate_value for item in candidates} == {"compact", "detailed"}
    assert all(item.status == "CANDIDATE" and item.shadow_only and item.promotion_state == "NOT_PROMOTED" for item in candidates)


def test_c06_unrelated_subjects_do_not_cross_contaminate() -> None:
    candidates = learn_shadow_candidates(
        (
            signal(subject="docs.response_style", source_digest=D0),
            signal(subject="docs.response_style", source_digest=D1, occurred_at=T1),
            signal(subject="workflow.review_order", value="architecture-first", source_digest=D2, occurred_at=T2),
            signal(subject="workflow.review_order", value="architecture-first", source_digest=D3, occurred_at=T3),
        )
    )
    assert {(item.subject_key, item.candidate_value) for item in candidates} == {
        ("docs.response_style", "compact"),
        ("workflow.review_order", "architecture-first"),
    }


def test_d01_rejection_suppresses_inferred_candidate() -> None:
    rejected = learn_shadow_candidates(
        (
            signal(source_digest=D0),
            signal(source_digest=D1, occurred_at=T1),
            signal(signal_type="USER_REJECTION", source_digest=D2, occurred_at=T2),
        )
    )
    assert len(rejected) == 1
    assert rejected[0].status == "REJECTED"


def test_d02_explicit_preference_blocks_conflicting_candidate() -> None:
    adaptive = store()
    preference(adaptive, value="compact", source_ref="test:explicit")
    profile = profile_for(adaptive)
    candidate = learn_shadow_candidates(
        (signal(value="detailed", source_digest=D0), signal(value="detailed", source_digest=D1, occurred_at=T1)),
        explicit_profile=profile,
    )[0]
    assert candidate.status == "BLOCKED_BY_EXPLICIT_PREFERENCE"
    assert candidate.explicit_conflict_ref == profile.patterns[0].pattern_id


def test_d03_a1_inferred_lifecycle_is_not_reused_as_a3_support() -> None:
    adaptive = store()
    append_inferred_candidate(
        adaptive,
        scope=scope(),
        subject_key="docs.response_style",
        value="compact",
        confidence=0.7,
        evidence_refs=("evidence:one", "evidence:two"),
        occurred_at=T0,
        source_ref="test:a1-inferred",
    )
    assert extract_a1_shadow_signals(adaptive.load_observations()) == ()


def test_d04_governed_outcome_does_not_become_explicit_preference() -> None:
    adaptive = store()
    adaptive.append(
        event_type="GOVERNED_OUTCOME_RECORDED",
        scope=scope(),
        subject_key="workflow.phase_outcome",
        evidence_class="GOVERNED_OUTCOME",
        source_type="orchestra_phase_retrospective",
        source_ref="retrospective:test",
        occurred_at=T0,
        payload={"phase_id": "A3", "phase_status": "accepted"},
    )
    profile = profile_for(adaptive)
    assert profile.patterns == ()
    assert adaptive.load_observations()[0].evidence_class == "GOVERNED_OUTCOME"


def test_d05_a3_outputs_do_not_amplify_their_own_support(tmp_path: Path) -> None:
    signals = (signal(source_digest=D0), signal(source_digest=D1, occurred_at=T1))
    candidate = learn_shadow_candidates(signals)[0]
    comparison = build_shadow_comparison(
        candidate,
        actual_deterministic_choice="detailed",
        actual_choice_ref="deterministic:test",
        evaluated_at=T2,
    )
    shadow = JsonlShadowStore(USER, root=tmp_path / "shadow")
    for item in signals:
        shadow.append_signal(item)
    shadow.write_candidates((candidate,))
    shadow.append_comparison(comparison)
    recomputed = learn_shadow_candidates(shadow.load_signals())[0]
    assert recomputed.digest == candidate.digest
    assert comparison.shadow_influenced_execution is False


def test_e01_separate_users_have_zero_adaptive_visibility() -> None:
    first = store("user-one")
    second = store("user-two")
    preference(first, record_scope=scope("global_user", user="user-one"), value="one")
    preference(second, record_scope=scope("global_user", user="user-two"), value="two")
    profile_for(first)
    profile_for(second)
    first_provider = StoreBackedAdaptiveContextProvider(first)
    own = first_provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext("user-one"))
    foreign = first_provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext("user-two"))
    assert [item.value for item in own.items] == ["one"]
    assert foreign.items == ()
    assert first.layout.root != second.layout.root


def test_e02_same_user_projects_remain_isolated() -> None:
    adaptive = store()
    preference(adaptive, value="one", record_scope=scope(project="Baelfyre/One"), source_ref="test:one")
    preference(adaptive, value="two", record_scope=scope(project="Baelfyre/Two"), occurred_at=T1, source_ref="test:two")
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    one = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key="Baelfyre/One"))
    two = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key="Baelfyre/Two"))
    assert [item.value for item in one.items] == ["one"]
    assert [item.value for item in two.items] == ["two"]


def test_e03_specialist_scopes_remain_isolated() -> None:
    adaptive = store()
    preference(adaptive, value="scribe", record_scope=scope("specialist", specialist="scribe"), source_ref="test:scribe")
    preference(adaptive, value="clockwork", record_scope=scope("specialist", specialist="clockwork"), occurred_at=T1, source_ref="test:clockwork")
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    scribe = provider.compile(route("scribe"), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT))
    clockwork = provider.compile(route("clockwork"), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT))
    assert [item.value for item in scribe.items] == ["scribe"]
    assert [item.value for item in clockwork.items] == ["clockwork"]


def test_e04_task_session_scopes_remain_isolated() -> None:
    adaptive = store()
    preference(adaptive, value="task-one", record_scope=scope("task_session", task="task-1"), source_ref="test:task-one")
    preference(adaptive, value="task-two", record_scope=scope("task_session", task="task-2"), occurred_at=T1, source_ref="test:task-two")
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    one = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-1"))
    two = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-2"))
    assert [item.value for item in one.items] == ["task-one"]
    assert [item.value for item in two.items] == ["task-two"]


def test_e05_storage_is_external_hashed_and_structured_only() -> None:
    raw_user = "raw-user@example.test"
    adaptive = store(raw_user)
    preference(adaptive, record_scope=scope("global_user", user=raw_user), value="compact")
    rendered = adaptive.observations_path.read_text(encoding="utf-8")
    assert ROOT not in adaptive.layout.root.parents
    assert raw_user not in str(adaptive.layout.root)
    assert "raw_conversation" not in rendered
    assert adaptive.layout.root.name != raw_user


def test_f01_default_runtime_path_has_no_adaptive_injection() -> None:
    captured = {}

    def operation(adapter_name, decision, validation):
        captured["metadata"] = dict(decision.metadata)
        return RuntimeOperationResult(LifecycleState.COMPLETED, "done", "TEST_COMPLETED")

    result = runtime_executor(store(), operation=operation, run_id="f01-default").execute(
        AdapterFactory.create("codex", ROOT), "ordinary user interaction"
    )
    assert result.success is True
    assert "adaptive_context" not in captured["metadata"]


def test_f02_opt_in_context_exposes_matching_explicit_preference() -> None:
    adaptive = store()
    preference(adaptive, record_scope=scope("global_user"), value="concise")
    profile_for(adaptive)
    packet = StoreBackedAdaptiveContextProvider(adaptive).compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT)
    )
    assert packet.status == "ADVISORY"
    assert packet.items[0].value == "concise"


def test_f03_inferred_candidate_requires_explicit_threshold() -> None:
    adaptive = store()
    append_inferred_candidate(
        adaptive,
        scope=scope(),
        subject_key="docs.response_style",
        value="compact",
        confidence=0.7,
        evidence_refs=("evidence:one",),
        occurred_at=T0,
        source_ref="test:candidate",
    )
    profile_for(adaptive)
    packet = StoreBackedAdaptiveContextProvider(adaptive).compile(
        route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT)
    )
    assert packet.items == ()


def test_f04_candidate_threshold_is_inclusive_and_bounded() -> None:
    adaptive = store()
    append_inferred_candidate(
        adaptive,
        scope=scope(),
        subject_key="docs.response_style",
        value="compact",
        confidence=0.7,
        evidence_refs=("evidence:one",),
        occurred_at=T0,
        source_ref="test:candidate",
    )
    profile_for(adaptive)
    provider = StoreBackedAdaptiveContextProvider(adaptive)
    below = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, min_candidate_confidence=0.69))
    equal = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, min_candidate_confidence=0.7))
    above = provider.compile(route(), ValidationResult(True, "APPROVED"), AdaptiveInvocationContext(USER, project_key=PROJECT, min_candidate_confidence=0.71))
    assert len(below.items) == len(equal.items) == 1
    assert above.items == ()


def test_f05_adaptive_state_cannot_influence_authority_or_delegation() -> None:
    captured = {}

    def operation(adapter_name, decision, validation):
        captured["packet"] = decision.metadata["adaptive_context"]
        return RuntimeOperationResult(LifecycleState.COMPLETED, "done", "TEST_COMPLETED")

    executor = runtime_executor(store(), operation=operation, run_id="f05-authority")
    result = executor.execute(
        AdapterFactory.create("codex", ROOT),
        "ordinary user interaction",
        adaptive_context=AdaptiveInvocationContext(USER),
    )
    assert result.route.skill_slug == "conductor"
    assert "adaptive_context" not in result.route.metadata
    assert captured["packet"]["advisory_only"] is True
    with pytest.raises(ValueError, match="not enabled for delegated execution"):
        executor.execute_delegated(
            AdapterFactory.create("codex", ROOT),
            "ordinary user interaction",
            None,
            adaptive_context=AdaptiveInvocationContext(USER),
        )


def test_g01_identical_event_sequences_are_deterministic(tmp_path: Path) -> None:
    states = []
    for root in (tmp_path / "one", tmp_path / "two"):
        adaptive = JsonlAdaptiveStore(USER, root=root)
        preference(adaptive, record_scope=scope("global_user"), source_ref="test:global")
        append_inferred_candidate(
            adaptive,
            scope=scope(),
            subject_key="docs.example_density",
            value="low",
            confidence=0.7,
            evidence_refs=("evidence:one",),
            occurred_at=T1,
            source_ref="test:candidate",
        )
        states.append((adaptive.load_observations(), profile_for(adaptive, generated_at=T4)))
    assert [item.to_dict() for item in states[0][0]] == [item.to_dict() for item in states[1][0]]
    assert states[0][1].to_dict() == states[1][1].to_dict()


def test_g02_portable_candidate_requires_privacy_review() -> None:
    candidate = portable_candidate()
    backend = MemoryBackendDescriptor("local_json", "LOCAL_JSON")
    with pytest.raises(ValueError, match="privacy review"):
        build_portable_memory_candidate(candidate, backend=backend, category="WORKFLOW")
    portable = build_portable_memory_candidate(
        candidate,
        backend=backend,
        category="WORKFLOW",
        privacy_reviewed=True,
        created_at=T4,
    )
    assert portable["privacy"]["review_state"] == "EXPLICITLY_REVIEWED_FOR_PORTABLE_PROMOTION"


def test_g03_portable_descriptor_is_non_authorizing() -> None:
    portable = build_portable_memory_candidate(
        portable_candidate(),
        backend=MemoryBackendDescriptor("local_json", "LOCAL_JSON"),
        category="WORKFLOW",
        privacy_reviewed=True,
        created_at=T4,
    )
    assert portable["authority"] == {
        "execution_authority": False,
        "policy_authority": False,
        "may_override_explicit_instruction": False,
        "may_relax_governance": False,
        "automatic_promotion": False,
    }
    assert portable["destination"]["canonical_write_authorized"] is False
