# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Synthetic tests for the offline, non-authorizing responsibility JEV contract."""

from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.domain.adaptive import (
    AUTHORITY_DOMAIN_OWNERS,
    EXPECTED_SPECIALISTS,
    AgenticWorkflowProfile,
    ProjectWorkItemIdentity,
    ResponsibilityAdjudicationAdvice,
    ResponsibilityAdjudicationContext,
    ResponsibilitySourceIdentity,
    SpecialistAuthority,
    TaskProfile,
    evaluate_responsibility_advice,
)


def _task(
    *,
    domains: tuple[str, ...] = ("SECURITY",),
    risk_level: str = "MEDIUM",
    primary_owner: str | None = "cipher",
    goal: str = "Review the task responsibility and proposed route.",
    protected_action_required: bool = False,
    protected_action_authorized: bool = False,
) -> TaskProfile:
    return TaskProfile(
        task_id="work-item-17",
        goal=goal,
        execution_mode="AUDIT",
        risk_level=risk_level,
        authority_domains=domains,
        primary_owner=primary_owner,
        dependency_depth=0,
        independent_subtasks=0,
        parallelizable=False,
        mutation_required=False,
        implementation_required=False,
        validation_required=False,
        transition_required=False,
        external_state_required=False,
        protected_action_required=protected_action_required,
        protected_action_authorized=protected_action_authorized,
        objective_verifier_available=False,
        critic_owner=None,
        critic_domain=None,
        reentry_specialists=(),
        current_source_identity="workspace@manifest-version-4",
    )


def _workflow(
    task: TaskProfile,
    specialists: tuple[str, ...] | None = None,
) -> AgenticWorkflowProfile:
    selected = specialists or tuple(
        dict.fromkeys(AUTHORITY_DOMAIN_OWNERS[domain] for domain in task.authority_domains)
    )
    primary_owner = task.primary_owner or AUTHORITY_DOMAIN_OWNERS[task.authority_domains[0]]
    patterns = ("ROUTING",) if len(selected) == 1 else ("ROUTING", "PLANNING")
    mode = "SINGLE_OWNER" if len(selected) == 1 else "SEQUENTIAL_MULTI_AGENT"
    return AgenticWorkflowProfile(
        profile_id="workflow-profile-17",
        source_task_id=task.task_id,
        primary_owner=primary_owner,
        required_specialists=selected,
        selected_patterns=patterns,
        sequence=selected,
        parallel_groups=(),
        concurrency_mode=mode,
        max_parallel_specialists=1,
        human_gate_required=False,
        escalation_reasons=(),
        stop_conditions=("OBJECTIVE_PASS",),
        critic_contract_id=None,
    )


def _authority(slug: str) -> SpecialistAuthority:
    # These values are synthetic shape fixtures, not source or trust evidence.
    return SpecialistAuthority.from_mapping(
        {
            "slug": slug,
            "authority_class": "SYNTHETIC_TEST_AUTHORITY",
            "source_path": f"skills/{slug}/SKILL.md",
            "source_blob_sha": "0" * 40,
            "observe_classes": ["task_scope"],
            "decide_classes": ["responsibility"],
            "mutate_classes": [],
            "can_dispatch": slug == "conductor",
            "can_transition": slug == "arbiter",
            "can_validate": slug == "overseer",
            "can_coordinate": slug == "the-tuner",
            "can_implement": slug == "ponytail",
            "can_execute_protected_action_without_external_authority": False,
        }
    )


def _context(
    *,
    task: TaskProfile | None = None,
    workflow: AgenticWorkflowProfile | None = None,
    authorities: tuple[SpecialistAuthority, ...] | None = None,
    project_identity: ProjectWorkItemIdentity | None = ProjectWorkItemIdentity(
        "synthetic-project", "work-item-17"
    ),
    source_identity: ResponsibilitySourceIdentity | None = ResponsibilitySourceIdentity(
        kind="ARTIFACT_VERSION", artifact_id="workspace-snapshot", version="manifest-version-4"
    ),
    registry_revision: str | None = "synthetic-registry-revision-4",
    policy_revision: str | None = "synthetic-policy-revision-2",
) -> ResponsibilityAdjudicationContext:
    actual_task = task or _task()
    actual_workflow = workflow or _workflow(actual_task)
    actual_authorities = authorities or tuple(
        _authority(slug) for slug in sorted(EXPECTED_SPECIALISTS)
    )
    return ResponsibilityAdjudicationContext(
        task_profile=actual_task,
        workflow_profile=actual_workflow,
        specialist_authorities=actual_authorities,
        project_work_item_identity=project_identity,
        source_identity=source_identity,
        authority_registry_revision=registry_revision,
        project_policy_context_revision=policy_revision,
    )


def test_contract_is_versioned_separately_from_post_mitigation_jev() -> None:
    from orchestra_runtime.domain.adaptive import (
        JEV_ADJUDICATION_CONTRACT,
        RESPONSIBILITY_ADJUDICATION_CONTRACT,
    )

    assert RESPONSIBILITY_ADJUDICATION_CONTRACT == "orchestra.jev.responsibility-adjudication.v1"
    assert RESPONSIBILITY_ADJUDICATION_CONTRACT != JEV_ADJUDICATION_CONTRACT


def test_missing_project_source_or_registry_identity_returns_no_advice() -> None:
    context = _context()
    for incomplete in (
        replace(context, project_work_item_identity=None),
        replace(context, source_identity=None),
        replace(context, authority_registry_revision=None),
    ):
        result = evaluate_responsibility_advice(
            incomplete, None, conductor_requested=True
        )
        assert result.decision == "NO_ADVICE"
        assert result.context_digest is None
        assert result.trust_qualification == "UNQUALIFIED"


def test_non_git_artifact_version_is_bound_without_becoming_a_git_sha() -> None:
    identity = ResponsibilitySourceIdentity(
        kind="ARTIFACT_VERSION", artifact_id="offline-project", version="snapshot-r9"
    )
    context = _context(source_identity=identity)

    assert context.binding_digest is not None
    assert identity.to_dict() == {
        "kind": "ARTIFACT_VERSION",
        "artifact_id": "offline-project",
        "version": "snapshot-r9",
    }
    assert "commit_sha" not in identity.to_dict()
    assert "tree_sha" not in identity.to_dict()


def test_git_and_artifact_source_identities_have_distinct_shapes() -> None:
    git_identity = ResponsibilitySourceIdentity(
        kind="GIT_COMMIT_TREE",
        repository="example/project",
        commit_sha="a" * 40,
        tree_sha="b" * 40,
    )
    digest_identity = ResponsibilitySourceIdentity(
        kind="ARTIFACT_DIGEST",
        artifact_id="build-output",
        digest_algorithm="sha256",
        digest="c" * 64,
    )

    assert git_identity.to_dict()["commit_sha"] == "a" * 40
    assert digest_identity.to_dict()["kind"] == "ARTIFACT_DIGEST"
    with pytest.raises(ValueError, match="non-Git source identity"):
        ResponsibilitySourceIdentity(
            kind="ARTIFACT_VERSION",
            artifact_id="build-output",
            version="v2",
            commit_sha="a" * 40,
        )


def test_unknown_specialist_roles_fail_closed() -> None:
    task = _task()
    unknown_route = replace(
        _workflow(task),
        primary_owner="made-up-specialist",
        required_specialists=("made-up-specialist",),
        sequence=("made-up-specialist",),
    )

    with pytest.raises(ValueError, match="unknown specialist roles"):
        _context(task=task, workflow=unknown_route)


def test_malformed_or_untrusted_provenance_cannot_upgrade_context_trust() -> None:
    context = _context()
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ROUTE_SUPPORTED")
    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert context.trust_qualification == "UNQUALIFIED"
    assert result.trust_qualification == "UNQUALIFIED"
    with pytest.raises(TypeError):
        ResponsibilityAdjudicationAdvice(
            context_digest=context.binding_digest or "",
            recommendation="ROUTE_SUPPORTED",
            trust_qualification="QUALIFIED",  # type: ignore[call-arg]
        )


@pytest.mark.parametrize(
    "changed_context",
    [
        lambda c: replace(c, task_profile=replace(c.task_profile, goal="A changed goal.")),
        lambda c: replace(c, task_profile=replace(c.task_profile, risk_level="HIGH")),
        lambda c: replace(
            c, task_profile=replace(c.task_profile, protected_action_required=True)
        ),
        lambda c: replace(
            c,
            workflow_profile=replace(
                c.workflow_profile,
                primary_owner="clockwork",
                required_specialists=("clockwork", "scribe"),
                sequence=("clockwork", "scribe"),
            ),
        ),
        lambda c: replace(c, authority_registry_revision="synthetic-registry-revision-5"),
        lambda c: replace(c, project_policy_context_revision="synthetic-policy-revision-3"),
        lambda c: replace(
            c,
            source_identity=ResponsibilitySourceIdentity(
                kind="ARTIFACT_VERSION", artifact_id="workspace-snapshot", version="manifest-version-5"
            ),
        ),
        lambda c: replace(
            c,
            project_work_item_identity=ProjectWorkItemIdentity(
                "synthetic-project", "work-item-18"
            ),
        ),
    ],
    ids=("goal", "risk", "constraints", "route", "registry", "policy", "source", "work-item"),
)
def test_material_context_changes_make_prior_advice_stale(changed_context) -> None:
    task = _task(domains=("SECURITY", "DOCUMENTATION"))
    context = _context(task=task, workflow=_workflow(task, ("cipher", "scribe")))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "CONDUCTOR_RECHECK_RECOMMENDED")
    changed = changed_context(context)

    assert changed.binding_digest != context.binding_digest
    result = evaluate_responsibility_advice(changed, advice, conductor_requested=True)
    assert result.decision == "STALE"


def test_authority_description_content_change_makes_prior_advice_stale() -> None:
    task = _task(domains=("SECURITY", "DOCUMENTATION"))
    context = _context(task=task, workflow=_workflow(task, ("cipher", "scribe")))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ROUTE_SUPPORTED")
    authorities = tuple(
        replace(authority, source_blob_sha="1" * 40)
        if authority.slug == "cipher"
        else authority
        for authority in context.specialist_authorities
    )
    changed = replace(context, specialist_authorities=authorities)

    assert changed.binding_digest != context.binding_digest
    assert evaluate_responsibility_advice(
        changed, advice, conductor_requested=True
    ).decision == "STALE"


def test_clear_single_owner_route_bypasses_optional_advice() -> None:
    context = _context()
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "OWNERSHIP_CONFLICT")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert result.decision == "NO_ADVICE"
    assert result.context_digest == context.binding_digest


def test_multi_specialist_route_does_not_automatically_request_advice() -> None:
    task = _task(domains=("SECURITY", "DOCUMENTATION"))
    context = _context(task=task, workflow=_workflow(task, ("cipher", "scribe")))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ROUTE_SUPPORTED")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=False)

    assert result.decision == "NO_ADVICE"


def test_conductor_requested_contested_cross_domain_advice_remains_non_authorizing() -> None:
    task = _task(domains=("SECURITY", "DOCUMENTATION"))
    context = _context(task=task, workflow=_workflow(task, ("cipher", "scribe")))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "OWNERSHIP_CONFLICT")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert result.decision == "OWNERSHIP_CONFLICT"
    assert result.may_authorize is False
    assert result.may_dispatch is False
    assert result.may_activate_tuner is False
    assert result.may_issue_completion_credit is False
    assert result.may_block_read_only_assessment is False


def test_alteredego_read_only_cipher_assessment_needs_no_effectful_approval() -> None:
    task = _task(
        goal="Read-only Cipher security assessment",
        protected_action_required=True,
        protected_action_authorized=False,
    )
    context = _context(
        task=task,
        project_identity=ProjectWorkItemIdentity("AlteredEgo", "security-assessment-1"),
    )

    result = evaluate_responsibility_advice(context, None, conductor_requested=True)

    assert context.binding_digest is not None
    assert result.decision == "NO_ADVICE"
    assert result.may_block_read_only_assessment is False
    assert result.may_authorize is False


def test_unavailable_advice_and_malformed_recommendations_fail_closed() -> None:
    context = _context()
    assert evaluate_responsibility_advice(
        context, None, conductor_requested=True
    ).decision == "NO_ADVICE"
    with pytest.raises(ValueError, match="unsupported responsibility recommendation"):
        ResponsibilityAdjudicationAdvice.for_context(context, "APPROVE_ACTION")


def test_task_profile_and_workflow_must_be_bound_to_each_other() -> None:
    task = _task()
    workflow = replace(_workflow(task), source_task_id="different-work-item")

    with pytest.raises(ValueError, match="must bind to the supplied task profile"):
        _context(task=task, workflow=workflow)


def test_result_serialization_keeps_every_authority_effect_false() -> None:
    context = _context()
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ABSTAIN")
    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)
    serialized = result.to_dict()

    assert serialized["trust_qualification"] == "UNQUALIFIED"
    assert all(
        serialized[field] is False
        for field in (
            "may_authorize",
            "may_dispatch",
            "may_activate_tuner",
            "may_issue_completion_credit",
            "may_block_read_only_assessment",
        )
    )
