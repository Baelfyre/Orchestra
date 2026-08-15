from dataclasses import replace

import pytest

from orchestra_runtime.coordination import (
    COORDINATION_CANONICALIZATION_VERSION,
    CollaborationDependency,
    CollaborationParticipant,
    CoordinationValidationResult,
    DependencyKind,
    InvalidationRule,
    InvalidationTargetKind,
    SpecialistParticipationRole,
    _authority_reference,
    _canonical_json,
    _exact_bool,
    _git_object_id,
    _identifier,
    _non_negative_sequence,
    _ordered_text,
    _positive_revision,
    _relative_path,
    _repository_identity,
    _text,
)
from orchestra_runtime.errors import InvalidCoordinationContractError

from coordination_support import build_graph


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda: _canonical_json({"bad": object()}), "INVALID_COORDINATION_CANONICAL_JSON"),
        (lambda: _text(None, "field"), "EMPTY_COORDINATION_FIELD"),
        (lambda: _identifier("bad space", "field"), "INVALID_COORDINATION_IDENTIFIER"),
        (lambda: _git_object_id("abc"), "INVALID_BASELINE_SHA"),
        (lambda: _ordered_text((), "values", allow_empty=False), "EMPTY_COORDINATION_COLLECTION"),
        (lambda: _exact_bool(1, "flag"), "INVALID_COORDINATION_BOOLEAN"),
        (lambda: _positive_revision(0), "INVALID_COORDINATION_REVISION"),
        (lambda: _non_negative_sequence(-1), "INVALID_COORDINATION_SEQUENCE"),
        (lambda: _relative_path("/absolute/path"), "UNSAFE_COORDINATION_PATH"),
        (lambda: _relative_path("src/../secret"), "UNSAFE_COORDINATION_PATH"),
        (lambda: _authority_reference("the-tuner", "owner"), "TUNER_AUTHORITY_EXPANSION"),
    ],
)
def test_coordination_scalar_guards_fail_closed(call, reason):
    with pytest.raises(InvalidCoordinationContractError) as exc:
        call()
    assert exc.value.reason_code == reason


def test_repository_identity_canonicalizes_all_supported_forms_and_rejects_bad_urls():
    canonical = "local-repository-sha256:" + "a" * 64
    windows_path = "C:" + "/Users/Example/repo"
    assert _repository_identity(canonical.upper()) == canonical
    assert _repository_identity("file:///tmp/secret").startswith("file-sha256:")
    assert _repository_identity(windows_path).startswith("local-repository-sha256:")
    assert _repository_identity("git@GitHub.COM:Baelfyre/Orchestra.git") == "ssh://github.com/Baelfyre/Orchestra.git"
    assert _repository_identity("https://GitHub.COM:443/Baelfyre/Orchestra?token=x#frag") == "https://github.com:443/Baelfyre/Orchestra"
    assert _repository_identity("relative-repo-name").startswith("local-repository-sha256:")

    with pytest.raises(InvalidCoordinationContractError) as missing_host:
        _repository_identity("https:///Baelfyre/Orchestra")
    assert missing_host.value.reason_code == "INVALID_REPOSITORY_IDENTITY"

    with pytest.raises(InvalidCoordinationContractError) as bad_port:
        _repository_identity("https://github.com:notaport/Baelfyre/Orchestra")
    assert bad_port.value.reason_code == "INVALID_REPOSITORY_IDENTITY"


def test_coordination_validation_result_integrity_guards_and_serialization():
    with pytest.raises(InvalidCoordinationContractError) as duplicate:
        CoordinationValidationResult(False, "blocked", ("same", "same"), ("a", "b"))
    assert duplicate.value.reason_code == "INVALID_COORDINATION_VALIDATION_RESULT"

    with pytest.raises(InvalidCoordinationContractError) as allowed_blocked:
        CoordinationValidationResult(True, "ready", ("block",), ("reason",))
    assert allowed_blocked.value.reason_code == "INVALID_COORDINATION_VALIDATION_RESULT"

    with pytest.raises(InvalidCoordinationContractError) as cardinality:
        CoordinationValidationResult(False, "blocked", ("one", "two"), ("one",))
    assert cardinality.value.reason_code == "INVALID_COORDINATION_VALIDATION_RESULT"

    result = CoordinationValidationResult(False, "blocked", ("missing-evidence",), ("receipt missing",))
    assert result.status == "BLOCKED"
    assert result.to_dict() == {
        "allowed": False,
        "status": "BLOCKED",
        "blocker_codes": ["MISSING-EVIDENCE"],
        "reasons": ["receipt missing"],
    }


def test_participant_role_review_and_accountability_guards():
    with pytest.raises(InvalidCoordinationContractError) as duplicate:
        CollaborationParticipant(
            "clockwork",
            (SpecialistParticipationRole.COLLABORATOR, SpecialistParticipationRole.COLLABORATOR),
        )
    assert duplicate.value.reason_code == "DUPLICATE_PARTICIPATION_ROLE"

    with pytest.raises(InvalidCoordinationContractError) as missing:
        CollaborationParticipant("clockwork", ())
    assert missing.value.reason_code == "MISSING_PARTICIPATION_ROLE"

    with pytest.raises(InvalidCoordinationContractError) as review:
        CollaborationParticipant("clockwork", (SpecialistParticipationRole.COLLABORATOR,), review_order=-1)
    assert review.value.reason_code == "INVALID_REVIEW_ORDER"

    with pytest.raises(InvalidCoordinationContractError) as mismatch:
        CollaborationParticipant(
            "clockwork",
            (SpecialistParticipationRole.COLLABORATOR,),
            accountable_layers=("architecture",),
        )
    assert mismatch.value.reason_code == "ACCOUNTABLE_ROLE_MISMATCH"

    participant = CollaborationParticipant(
        "ClockWork",
        (SpecialistParticipationRole.COLLABORATOR,),
        collaborating_layers=("Implementation",),
        required=False,
        review_order=2,
    )
    assert participant.specialist_slug == "clockwork"
    assert participant.to_dict()["review_order"] == 2


def test_invalidation_rule_requires_complete_subset_and_serializes():
    with pytest.raises(InvalidCoordinationContractError) as incomplete:
        InvalidationRule(InvalidationTargetKind.EVIDENCE, (), ("overseer",), ("overseer",))
    assert incomplete.value.reason_code == "INCOMPLETE_INVALIDATION_RULE"

    with pytest.raises(InvalidCoordinationContractError) as subset:
        InvalidationRule(
            InvalidationTargetKind.EVIDENCE,
            ("evidence.one",),
            ("overseer",),
            ("arbiter",),
        )
    assert subset.value.reason_code == "INVALID_REENTRY_SET"

    rule = InvalidationRule(
        InvalidationTargetKind.EVIDENCE,
        ("evidence.one",),
        ("overseer", "ponytail"),
        ("overseer",),
    )
    assert rule.to_dict()["target_kind"] == "EVIDENCE"


def test_dependency_self_duplicate_rules_affected_set_and_lookup_edges():
    with pytest.raises(InvalidCoordinationContractError) as self_edge:
        CollaborationDependency("dep.self", "clockwork", "clockwork", DependencyKind.REQUIRES)
    assert self_edge.value.reason_code == "SELF_COORDINATION_DEPENDENCY"

    rule = InvalidationRule(
        InvalidationTargetKind.EVIDENCE,
        ("evidence.one",),
        ("clockwork", "ponytail"),
        ("clockwork",),
    )
    with pytest.raises(InvalidCoordinationContractError) as duplicate:
        CollaborationDependency(
            "dep.duplicate",
            "clockwork",
            "ponytail",
            DependencyKind.REQUIRES,
            invalidation_rules=(rule, rule),
        )
    assert duplicate.value.reason_code == "DUPLICATE_INVALIDATION_RULE"

    foreign = InvalidationRule(
        InvalidationTargetKind.EVIDENCE,
        ("evidence.one",),
        ("arbiter",),
        ("arbiter",),
    )
    with pytest.raises(InvalidCoordinationContractError) as invalid_set:
        CollaborationDependency(
            "dep.foreign",
            "clockwork",
            "ponytail",
            DependencyKind.REQUIRES,
            invalidation_rules=(foreign,),
        )
    assert invalid_set.value.reason_code == "INVALID_INVALIDATION_SPECIALIST_SET"

    dependency = CollaborationDependency(
        "dep.valid",
        "clockwork",
        "ponytail",
        DependencyKind.REQUIRES,
        ("section.arch",),
        ("architecture-changed",),
        True,
        (rule,),
    )
    assert dependency.invalidation_rule_for(InvalidationTargetKind.EVIDENCE) == rule
    assert dependency.invalidation_rule_for(InvalidationTargetKind.REVIEW) is None
    assert dependency.to_dict()["blocking"] is True


def test_collaboration_graph_empty_duplicate_unknown_layer_owner_role_and_version_edges():
    graph = build_graph()

    with pytest.raises(InvalidCoordinationContractError) as no_participants:
        replace(graph, participants=())
    assert no_participants.value.reason_code == "INVALID_COLLABORATION_PARTICIPANTS"

    with pytest.raises(InvalidCoordinationContractError) as duplicate_participant:
        replace(graph, participants=graph.participants + (graph.participants[0],))
    assert duplicate_participant.value.reason_code == "INVALID_COLLABORATION_PARTICIPANTS"

    with pytest.raises(InvalidCoordinationContractError) as duplicate_dependency:
        replace(graph, dependencies=graph.dependencies + (graph.dependencies[0],))
    assert duplicate_dependency.value.reason_code == "DUPLICATE_COORDINATION_DEPENDENCY"

    with pytest.raises(InvalidCoordinationContractError) as no_layers:
        replace(graph, affected_layers=())
    assert no_layers.value.reason_code == "MISSING_AFFECTED_LAYERS"

    participants = tuple(
        replace(item, collaborating_layers=item.collaborating_layers + ("unknown",))
        if item.specialist_slug == "clockwork"
        else item
        for item in graph.participants
    )
    with pytest.raises(InvalidCoordinationContractError) as unknown_layer:
        replace(graph, participants=participants)
    assert unknown_layer.value.reason_code == "UNKNOWN_AFFECTED_LAYER"

    with pytest.raises(InvalidCoordinationContractError) as unknown_owner:
        replace(graph, visual_model_owner="missing-specialist")
    assert unknown_owner.value.reason_code == "UNKNOWN_COORDINATION_OWNER"

    with pytest.raises(InvalidCoordinationContractError) as role_mismatch:
        replace(graph, visual_model_owner="clockwork")
    assert role_mismatch.value.reason_code == "COORDINATION_OWNER_ROLE_MISMATCH"

    with pytest.raises(InvalidCoordinationContractError) as bad_version:
        replace(graph, canonicalization_version=COORDINATION_CANONICALIZATION_VERSION + "-bad")
    assert bad_version.value.reason_code == "UNSUPPORTED_COORDINATION_VERSION"

    assert graph.accountable_owner_for("architecture") == "clockwork"
    assert graph.accountable_owner_for("nonexistent") is None
    assert graph.to_dict()["fingerprint"] == graph.fingerprint