from __future__ import annotations

from pathlib import Path

import pytest

from orchestra_runtime.adaptive.context import (
    AdaptiveContextPacket,
    AdaptiveInvocationContext,
    AdaptiveRuntimeExecutor,
    StoreBackedAdaptiveContextProvider,
)
from orchestra_runtime.adaptive.models import (
    AdaptivePattern,
    AdaptiveProfile,
    AdaptiveScope,
    ADAPTIVE_MEMORY_RULE_VERSION,
)
from orchestra_runtime.adaptive.observations import append_explicit_preference
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

USER = "fixture-user"
PROJECT = "Baelfyre/Orchestra"
T0 = "2026-08-18T01:00:00Z"
T1 = "2026-08-18T01:01:00Z"


def route(slug: str = "scribe") -> RouteDecision:
    return RouteDecision(slug, slug, False, "edge route")


def project_scope(user: str = USER, project: str = PROJECT) -> AdaptiveScope:
    return AdaptiveScope("project", user, project_key=project)


def pattern(
    *,
    pattern_id: str,
    scope: AdaptiveScope | None = None,
    subject: str = "docs.response_style",
    value: str = "compact",
    status: str = "candidate",
    evidence_class: str = "INFERRED_CANDIDATE",
    confidence: float = 0.5,
    updated_at: str = T0,
) -> AdaptivePattern:
    return AdaptivePattern(
        pattern_id=pattern_id,
        scope=scope or project_scope(),
        subject_key=subject,
        value=value,
        status=status,
        evidence_class=evidence_class,
        evidence_refs=(f"edge:{pattern_id}",),
        observation_count=1,
        confidence=confidence,
        created_at=T0,
        updated_at=updated_at,
    )


@pytest.mark.parametrize(
    ("kwargs", "error_type", "match"),
    (
        ({"user_key": 3}, TypeError, "user_key must be a string"),
        ({"user_key": " "}, ValueError, "user_key must be non-empty"),
        ({"user_key": USER, "project_key": 3}, TypeError, "project_key must be a string"),
        ({"user_key": USER, "task_session_key": " "}, ValueError, "task_session_key must be non-empty"),
        ({"user_key": USER, "max_items": True}, ValueError, "max_items must be a positive integer"),
        ({"user_key": USER, "max_items": "16"}, ValueError, "max_items must be a positive integer"),
        ({"user_key": USER, "max_items": 0}, ValueError, "max_items must be a positive integer"),
        ({"user_key": USER, "max_outcome_evidence": True}, ValueError, "max_outcome_evidence must be a non-negative integer"),
        ({"user_key": USER, "max_outcome_evidence": "8"}, ValueError, "max_outcome_evidence must be a non-negative integer"),
        ({"user_key": USER, "max_outcome_evidence": -1}, ValueError, "max_outcome_evidence must be a non-negative integer"),
        ({"user_key": USER, "min_candidate_confidence": True}, TypeError, "min_candidate_confidence must be numeric"),
        ({"user_key": USER, "min_candidate_confidence": "0.5"}, TypeError, "min_candidate_confidence must be numeric"),
        ({"user_key": USER, "min_candidate_confidence": -0.1}, ValueError, "min_candidate_confidence must be between 0 and 1"),
        ({"user_key": USER, "min_candidate_confidence": 1.1}, ValueError, "min_candidate_confidence must be between 0 and 1"),
    ),
)
def test_a2_invocation_validation_edges(kwargs, error_type, match):
    with pytest.raises(error_type, match=match):
        AdaptiveInvocationContext(**kwargs)


def test_a2_invocation_normalizes_valid_bounds_and_refs():
    invocation = AdaptiveInvocationContext(
        USER,
        project_key=PROJECT,
        max_items=1,
        max_outcome_evidence=0,
        min_candidate_confidence=0,
        repository_refs=("repo:b", "repo:a", "repo:a"),
        current_instruction_refs=("instruction:b", "instruction:a"),
    )
    assert invocation.repository_refs == ("repo:a", "repo:b")
    assert invocation.current_instruction_refs == ("instruction:a", "instruction:b")
    assert invocation.min_candidate_confidence == 0.0


@pytest.mark.parametrize(
    ("kwargs", "error_type", "match"),
    (
        ({"schema_version": "bad"}, ValueError, "unsupported adaptive context schema"),
        ({"specialist_slug": " "}, ValueError, "specialist_slug must be non-empty"),
        ({"command_name": 3}, TypeError, "command_name must be a string"),
        ({"status": "ACTIVE"}, ValueError, "status must be ADVISORY or DETERMINISTIC_FALLBACK"),
        ({"reason_code": " "}, ValueError, "reason_code must be non-empty"),
        ({"advisory_only": False}, ValueError, "must remain advisory_only"),
    ),
)
def test_a2_packet_validation_edges(kwargs, error_type, match):
    values = {
        "specialist_slug": "scribe",
        "command_name": "scribe",
        "status": "ADVISORY",
        "reason_code": "EDGE_OK",
    }
    values.update(kwargs)
    with pytest.raises(error_type, match=match):
        AdaptiveContextPacket(**values)


def test_a2_packet_normalizes_identifiers_and_reference_sets():
    packet = AdaptiveContextPacket(
        " Scribe ",
        " Scribe ",
        "advisory",
        "EDGE_OK",
        repository_refs=("repo:b", "repo:a", "repo:a"),
        current_instruction_refs=("instruction:b", "instruction:a"),
    )
    assert packet.specialist_slug == "scribe"
    assert packet.command_name == "scribe"
    assert packet.status == "ADVISORY"
    assert packet.repository_refs == ("repo:a", "repo:b")
    assert packet.current_instruction_refs == ("instruction:a", "instruction:b")


def test_a2_provider_constructor_and_fallback_edges(tmp_path: Path):
    with pytest.raises(TypeError, match="store must be JsonlAdaptiveStore"):
        StoreBackedAdaptiveContextProvider(object())  # type: ignore[arg-type]

    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    provider = StoreBackedAdaptiveContextProvider(store)
    invocation = AdaptiveInvocationContext(USER, project_key=PROJECT)

    blocked = provider.compile(
        route(),
        ValidationResult(False, "BLOCKED", ("edge",), ("edge-rule",)),
        invocation,
    )
    assert blocked.reason_code == "GOVERNANCE_NOT_APPROVED"

    mismatch = provider.compile(
        route(),
        ValidationResult(True, "APPROVED"),
        AdaptiveInvocationContext("other-user", project_key=PROJECT),
    )
    assert mismatch.reason_code == "USER_SCOPE_MISMATCH"

    no_profile = provider.compile(
        route(),
        ValidationResult(True, "APPROVED"),
        invocation,
    )
    assert no_profile.reason_code == "NO_VALID_PROFILE"


def test_a2_profile_current_edges():
    current = AdaptiveProfile(
        profile_id="profile-current",
        user_key=USER,
        generated_at=T0,
        patterns=(),
        source_head_digest=None,
    )
    incompatible = AdaptiveProfile(
        profile_id="profile-incompatible",
        user_key=USER,
        generated_at=T0,
        patterns=(),
        source_head_digest=None,
        memory_rule_version="orchestra.adaptive-memory-rules.v999",
    )
    assert StoreBackedAdaptiveContextProvider._profile_is_current(current, ()) is True
    assert StoreBackedAdaptiveContextProvider._profile_is_current(incompatible, ()) is False
    assert current.memory_rule_version == ADAPTIVE_MEMORY_RULE_VERSION


@pytest.mark.parametrize(
    ("record", "threshold", "expected"),
    (
        (pattern(pattern_id="deprecated", status="deprecated", confidence=0.5), 0.0, None),
        (pattern(pattern_id="rejected", status="rejected", confidence=0.5), 0.0, None),
        (
            pattern(
                pattern_id="explicit-current",
                scope=AdaptiveScope("task_session", USER, project_key=PROJECT, task_session_key="task-1"),
                status="confirmed",
                evidence_class="EXPLICIT_CURRENT_INSTRUCTION",
                confidence=1.0,
            ),
            None,
            "EXPLICIT_CURRENT_INSTRUCTION",
        ),
        (
            pattern(
                pattern_id="explicit-scoped",
                status="confirmed",
                evidence_class="EXPLICIT_SCOPED_PREFERENCE",
                confidence=1.0,
            ),
            None,
            "EXPLICIT_SCOPED_PREFERENCE",
        ),
        (
            pattern(
                pattern_id="confirmed-learned",
                status="confirmed",
                evidence_class="INFERRED_CANDIDATE",
                confidence=0.8,
            ),
            None,
            "CONFIRMED_LEARNED_PATTERN",
        ),
        (pattern(pattern_id="candidate-no-threshold", confidence=0.8), None, None),
        (pattern(pattern_id="candidate-below-threshold", confidence=0.4), 0.5, None),
        (pattern(pattern_id="candidate-allowed", confidence=0.8), 0.5, "INFERRED_CANDIDATE"),
        (
            pattern(
                pattern_id="feedback",
                status="confirmed",
                evidence_class="USER_FEEDBACK",
                confidence=0.5,
            ),
            None,
            None,
        ),
    ),
)
def test_a2_pattern_classification_edges(record, threshold, expected):
    invocation = AdaptiveInvocationContext(
        USER,
        project_key=PROJECT,
        task_session_key="task-1",
        min_candidate_confidence=threshold,
    )
    assert StoreBackedAdaptiveContextProvider._classify_pattern(record, invocation) == expected


def test_a2_pattern_lower_precedence_does_not_replace_existing_winner(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    provider = StoreBackedAdaptiveContextProvider(store)
    explicit = pattern(
        pattern_id="explicit",
        scope=AdaptiveScope("global_user", USER),
        status="confirmed",
        evidence_class="EXPLICIT_SCOPED_PREFERENCE",
        confidence=1.0,
        value="explicit",
    )
    candidate = pattern(
        pattern_id="candidate",
        scope=project_scope(),
        confidence=0.9,
        updated_at=T1,
        value="candidate",
    )
    profile = AdaptiveProfile(
        profile_id="profile-precedence",
        user_key=USER,
        generated_at=T1,
        patterns=(explicit, candidate),
        source_head_digest=None,
    )
    selected = provider._select_patterns(
        profile,
        "scribe",
        AdaptiveInvocationContext(USER, project_key=PROJECT, min_candidate_confidence=0.5),
    )
    assert len(selected) == 1
    assert selected[0].value == "explicit"


@pytest.mark.parametrize(
    ("record_scope", "specialist", "invocation", "expected"),
    (
        (project_scope("other-user"), "scribe", AdaptiveInvocationContext(USER, project_key=PROJECT), False),
        (project_scope(USER, "Baelfyre/Other"), "scribe", AdaptiveInvocationContext(USER, project_key=PROJECT), False),
        (
            AdaptiveScope("specialist", USER, project_key=PROJECT, specialist_slug="scribe"),
            "beatrice",
            AdaptiveInvocationContext(USER, project_key=PROJECT),
            False,
        ),
        (
            AdaptiveScope("task_session", USER, project_key=PROJECT, task_session_key="task-1"),
            "scribe",
            AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-2"),
            False,
        ),
        (
            AdaptiveScope("task_session", USER, project_key=PROJECT, task_session_key="task-1"),
            "scribe",
            AdaptiveInvocationContext(USER, project_key=PROJECT, task_session_key="task-1"),
            True,
        ),
    ),
)
def test_a2_scope_match_edges(record_scope, specialist, invocation, expected):
    assert StoreBackedAdaptiveContextProvider._scope_matches(record_scope, specialist, invocation) is expected


def test_a2_current_profile_head_and_outcome_zero_bound(tmp_path: Path):
    store = JsonlAdaptiveStore(USER, root=tmp_path / "adaptive")
    append_explicit_preference(
        store,
        scope=project_scope(),
        subject_key="docs.response_style",
        value="compact",
        occurred_at=T0,
        source_ref="edge:explicit",
    )
    observations = store.load_observations()
    profile = AdaptiveProfile(
        profile_id="profile-head",
        user_key=USER,
        generated_at=T1,
        patterns=(
            pattern(
                pattern_id="explicit-head",
                status="confirmed",
                evidence_class="EXPLICIT_SCOPED_PREFERENCE",
                confidence=1.0,
            ),
        ),
        source_head_digest=observations[-1].digest,
    )
    store.write_profile(profile)
    packet = StoreBackedAdaptiveContextProvider(store).compile(
        route(),
        ValidationResult(True, "APPROVED"),
        AdaptiveInvocationContext(USER, project_key=PROJECT, max_items=1, max_outcome_evidence=0),
    )
    assert packet.status == "ADVISORY"
    assert len(packet.items) == 1
    assert packet.outcome_evidence == ()


def build_edge_executor(tmp_path: Path, *, operation=None, provider=None, run_id="a2-edge-runtime"):
    root = Path(__file__).resolve().parents[2]
    store = JsonlAdaptiveStore(USER, root=tmp_path / "runtime-adaptive")
    manifests = ManifestRepository(root)
    skills = SkillRegistry(manifests, SkillSourceRepository(root))
    return AdaptiveRuntimeExecutor(
        skills,
        RouterService(skills),
        GovernanceValidator(),
        ContextAssembler(manifests),
        build_compatibility_composition(skills, InMemoryAuditSink(), run_id=run_id),
        operation=operation,
        adaptive_provider=provider or StoreBackedAdaptiveContextProvider(store),
    )


def test_a2_executor_provider_contract_rejects_missing_compiler():
    with pytest.raises(TypeError, match="adaptive_provider must implement compile"):
        AdaptiveRuntimeExecutor(None, None, None, None, None, adaptive_provider=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="adaptive_provider must implement compile"):
        AdaptiveRuntimeExecutor(None, None, None, None, None, adaptive_provider=object())  # type: ignore[arg-type]


def test_a2_executor_without_invocation_uses_base_operation(tmp_path: Path):
    captured = {}

    def operation(adapter_name, decision, validation):
        captured["metadata"] = dict(decision.metadata)
        return RuntimeOperationResult(LifecycleState.COMPLETED, "completed", "EDGE_COMPLETED")

    root = Path(__file__).resolve().parents[2]
    executor = build_edge_executor(tmp_path, operation=operation, run_id="a2-edge-base-operation")
    result = executor.execute(AdapterFactory.create("codex", root), "@Orchestra rerun the prompt")
    assert result.success is True
    assert "adaptive_context" not in captured["metadata"]


def test_a2_delegation_request_with_context_fails_before_base_validation(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    executor = build_edge_executor(tmp_path, run_id="a2-edge-delegation-request")
    with pytest.raises(ValueError, match="not enabled for delegated execution"):
        executor.execute_delegation_request(
            AdapterFactory.create("codex", root),
            "@Orchestra rerun the prompt",
            None,  # type: ignore[arg-type]
            adaptive_context=AdaptiveInvocationContext(USER, project_key=PROJECT),
        )
