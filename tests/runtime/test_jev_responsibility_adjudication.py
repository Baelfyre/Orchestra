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
    ResponsibilityAdjudicationResult,
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


@pytest.mark.parametrize(("domain", "owner"), tuple(AUTHORITY_DOMAIN_OWNERS.items()))
def test_clear_domain_mapped_single_owner_route_bypasses_optional_advice(
    domain: str, owner: str
) -> None:
    task = _task(domains=(domain,), primary_owner=owner)
    context = _context(task=task, workflow=_workflow(task, (owner,)))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "OWNERSHIP_CONFLICT")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert result.decision == "NO_ADVICE"
    assert result.context_digest == context.binding_digest


def test_unmapped_single_owner_route_remains_advisable_when_requested() -> None:
    task = _task(primary_owner=None)
    workflow = replace(_workflow(task, ("cloak",)), primary_owner="cloak")
    context = _context(task=task, workflow=workflow)
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "OWNERSHIP_CONFLICT")

    unrequested = evaluate_responsibility_advice(context, advice, conductor_requested=False)
    requested = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert unrequested.decision == "NO_ADVICE"
    assert requested.decision == "OWNERSHIP_CONFLICT"


def test_explicit_task_owner_mismatching_domain_map_remains_advisable() -> None:
    task = _task(primary_owner="cloak")
    context = _context(task=task, workflow=_workflow(task, ("cloak",)))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "CONDUCTOR_RECHECK_RECOMMENDED")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert result.decision == "CONDUCTOR_RECHECK_RECOMMENDED"


def test_task_and_workflow_owner_mismatch_remains_advisable_when_requested() -> None:
    task = _task(primary_owner="cipher")
    workflow = replace(_workflow(task, ("cloak",)), primary_owner="cloak")
    context = _context(task=task, workflow=workflow)
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "OWNERSHIP_CONFLICT")

    result = evaluate_responsibility_advice(context, advice, conductor_requested=True)

    assert result.decision == "OWNERSHIP_CONFLICT"
    assert result.context_digest == context.binding_digest


def test_critic_owner_is_included_in_the_context_roles() -> None:
    task = replace(_task(), critic_owner="scribe", critic_domain="DOCUMENTATION")
    context = _context(task=task)

    assert context.binding_digest is not None


def test_policy_context_revision_remains_optional() -> None:
    context = _context(policy_revision=None)

    assert context.binding_digest is not None


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


@pytest.mark.parametrize(
    ("project_id", "error", "message"),
    (
        (None, TypeError, "project_id must be a string"),
        ("  ", ValueError, "project_id must be non-empty"),
        ("x" * 513, ValueError, "project_id exceeds 512 characters"),
        ("bad\nvalue", ValueError, "project_id must not contain control characters"),
    ),
)
def test_identity_text_fields_reject_malformed_values(project_id, error, message) -> None:
    with pytest.raises(error, match=message):
        ProjectWorkItemIdentity(project_id=project_id, work_item_id="work-item")


@pytest.mark.parametrize(
    ("identity_fields", "message"),
    (
        ({"kind": "URL", "artifact_id": "artifact"}, "unsupported source identity kind"),
        (
            {
                "kind": "GIT_COMMIT_TREE",
                "repository": "example/project",
                "commit_sha": "a" * 40,
                "tree_sha": "b" * 40,
                "artifact_id": "unexpected",
            },
            "Git source identity cannot contain artifact fields",
        ),
        (
            {
                "kind": "GIT_COMMIT_TREE",
                "repository": "invalid-repository",
                "commit_sha": "a" * 40,
                "tree_sha": "b" * 40,
            },
            "source_identity.repository is invalid",
        ),
        (
            {"kind": "ARTIFACT_DIGEST", "artifact_id": "artifact"},
            "artifact digest identity requires only an algorithm and digest",
        ),
        (
            {
                "kind": "ARTIFACT_DIGEST",
                "artifact_id": "artifact",
                "digest_algorithm": "md5",
                "digest": "c" * 64,
            },
            "only explicitly identified SHA-256 artifact digests are supported",
        ),
        (
            {
                "kind": "ARTIFACT_VERSION",
                "artifact_id": "artifact",
                "version": "v1",
                "digest_algorithm": "sha256",
            },
            "artifact version identity requires only a version",
        ),
    ),
)
def test_source_identity_rejects_unsupported_or_inconsistent_shapes(identity_fields, message) -> None:
    with pytest.raises(ValueError, match=message):
        ResponsibilitySourceIdentity(**identity_fields)


@pytest.mark.parametrize(
    ("mutate", "error", "message"),
    (
        (lambda context: replace(context, task_profile=None), TypeError, "task_profile must be TaskProfile"),
        (
            lambda context: replace(context, workflow_profile=None),
            TypeError,
            "workflow_profile must be AgenticWorkflowProfile",
        ),
        (
            lambda context: replace(context, project_work_item_identity="untrusted"),
            TypeError,
            "project_work_item_identity must be ProjectWorkItemIdentity or None",
        ),
        (
            lambda context: replace(context, source_identity="untrusted"),
            TypeError,
            "source_identity must be ResponsibilitySourceIdentity or None",
        ),
        (
            lambda context: replace(context, specialist_authorities="not-a-list"),
            TypeError,
            "specialist_authorities must be a tuple or list",
        ),
        (
            lambda context: replace(context, specialist_authorities=(object(),)),
            TypeError,
            "specialist_authorities entries must be SpecialistAuthority",
        ),
        (
            lambda context: replace(
                context,
                specialist_authorities=tuple(
                    _authority("cipher") for _ in range(len(EXPECTED_SPECIALISTS) + 1)
                ),
            ),
            ValueError,
            "specialist_authorities exceeds the canonical specialist count",
        ),
        (
            lambda context: replace(
                context, specialist_authorities=(_authority("cipher"), _authority("cipher"))
            ),
            ValueError,
            "specialist_authorities contains duplicate slugs",
        ),
    ),
)
def test_context_rejects_malformed_types_and_authority_records(mutate, error, message) -> None:
    with pytest.raises(error, match=message):
        mutate(_context())


def test_missing_required_authority_record_prevents_advice_binding() -> None:
    context = _context()
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ROUTE_SUPPORTED")
    incomplete = replace(
        context,
        specialist_authorities=tuple(
            authority for authority in context.specialist_authorities if authority.slug != "cipher"
        ),
    )

    assert incomplete.binding_digest is None
    assert evaluate_responsibility_advice(
        incomplete, advice, conductor_requested=True
    ).decision == "NO_ADVICE"
    with pytest.raises(ValueError, match="context is insufficiently bound"):
        ResponsibilityAdjudicationAdvice.for_context(incomplete, "ROUTE_SUPPORTED")


def test_advice_and_result_reject_malformed_decisions_and_digests() -> None:
    with pytest.raises(ValueError, match="context_digest must use the sha256 prefix"):
        ResponsibilityAdjudicationAdvice(context_digest="a" * 64, recommendation="ABSTAIN")
    with pytest.raises(TypeError, match="context must be ResponsibilityAdjudicationContext"):
        ResponsibilityAdjudicationAdvice.for_context(None, "ABSTAIN")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported responsibility adjudication decision"):
        ResponsibilityAdjudicationResult("UNKNOWN", None)
    with pytest.raises(ValueError, match="context_digest must use the sha256 prefix"):
        ResponsibilityAdjudicationResult("NO_ADVICE", "a" * 64)


def test_context_repr_and_advice_serialization_keep_expected_fields() -> None:
    context = _context(task=_task(goal="synthetic private task text"))
    advice = ResponsibilityAdjudicationAdvice.for_context(context, "ABSTAIN")

    assert "synthetic private task text" not in repr(context)
    assert advice.to_dict() == {
        "contract": "orchestra.jev.responsibility-adjudication.v1",
        "context_digest": context.binding_digest,
        "recommendation": "ABSTAIN",
    }


def test_evaluation_rejects_malformed_call_arguments() -> None:
    context = _context()
    with pytest.raises(TypeError, match="context must be ResponsibilityAdjudicationContext"):
        evaluate_responsibility_advice(None, None, conductor_requested=True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="advice must be ResponsibilityAdjudicationAdvice or None"):
        evaluate_responsibility_advice(context, "ROUTE_SUPPORTED", conductor_requested=True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="conductor_requested must be an exact boolean"):
        evaluate_responsibility_advice(context, None, conductor_requested=1)  # type: ignore[arg-type]
