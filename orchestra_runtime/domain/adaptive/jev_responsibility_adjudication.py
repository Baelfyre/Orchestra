# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Pure, advisory-only contract for project-adaptive JEV responsibility review.

Typed inputs and their digests are unqualified context, never proof of trusted
host provenance, project policy, routing authority, or permission to act.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Mapping

from ...shared.canonicalization import normalize_git_sha, normalize_sha256, receipt_digest
from .task_profile import TaskProfile
from .topology_validator import EXPECTED_SPECIALISTS, AgenticWorkflowProfile, SpecialistAuthority


RESPONSIBILITY_ADJUDICATION_CONTRACT = "orchestra.jev.responsibility-adjudication.v1"
RESPONSIBILITY_ROUTE_SUPPORTED = "ROUTE_SUPPORTED"
RESPONSIBILITY_CONDUCTOR_RECHECK_RECOMMENDED = "CONDUCTOR_RECHECK_RECOMMENDED"
RESPONSIBILITY_OWNERSHIP_GAP = "OWNERSHIP_GAP"
RESPONSIBILITY_OWNERSHIP_CONFLICT = "OWNERSHIP_CONFLICT"
RESPONSIBILITY_NO_ADVICE = "NO_ADVICE"
RESPONSIBILITY_ABSTAIN = "ABSTAIN"
RESPONSIBILITY_STALE = "STALE"

_ADVICE_RECOMMENDATIONS = frozenset(
    {
        RESPONSIBILITY_ROUTE_SUPPORTED,
        RESPONSIBILITY_CONDUCTOR_RECHECK_RECOMMENDED,
        RESPONSIBILITY_OWNERSHIP_GAP,
        RESPONSIBILITY_OWNERSHIP_CONFLICT,
        RESPONSIBILITY_ABSTAIN,
    }
)
_RESULT_DECISIONS = _ADVICE_RECOMMENDATIONS | {
    RESPONSIBILITY_NO_ADVICE,
    RESPONSIBILITY_STALE,
}
_SOURCE_IDENTITY_KINDS = frozenset(
    {"GIT_COMMIT_TREE", "ARTIFACT_DIGEST", "ARTIFACT_VERSION"}
)
_REPOSITORY_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _text(value: object, field_name: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


@dataclass(frozen=True, slots=True)
class ProjectWorkItemIdentity:
    """Project/work-item identity kept separate from source and Git identity."""

    project_id: str
    work_item_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _text(self.project_id, "project_id"))
        object.__setattr__(self, "work_item_id", _text(self.work_item_id, "work_item_id"))

    def to_dict(self) -> dict[str, str]:
        return {"project_id": self.project_id, "work_item_id": self.work_item_id}


@dataclass(frozen=True, slots=True)
class ResponsibilitySourceIdentity:
    """Typed source identity; validation does not attest that its source is trusted."""

    kind: str
    repository: str | None = None
    commit_sha: str | None = None
    tree_sha: str | None = None
    artifact_id: str | None = None
    digest_algorithm: str | None = None
    digest: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        kind = _text(self.kind, "source_identity.kind", max_length=32).upper()
        if kind not in _SOURCE_IDENTITY_KINDS:
            raise ValueError("unsupported source identity kind")

        if kind == "GIT_COMMIT_TREE":
            if any(
                value is not None
                for value in (self.artifact_id, self.digest_algorithm, self.digest, self.version)
            ):
                raise ValueError("Git source identity cannot contain artifact fields")
            repository = _text(self.repository, "source_identity.repository", max_length=255)
            if not _REPOSITORY_ID_RE.fullmatch(repository):
                raise ValueError("source_identity.repository is invalid")
            object.__setattr__(self, "repository", repository)
            object.__setattr__(
                self, "commit_sha", normalize_git_sha(self.commit_sha, "source_identity.commit_sha")
            )
            object.__setattr__(
                self, "tree_sha", normalize_git_sha(self.tree_sha, "source_identity.tree_sha")
            )
            return

        if self.repository is not None or self.commit_sha is not None or self.tree_sha is not None:
            raise ValueError("non-Git source identity cannot contain Git repository or SHA fields")
        artifact_id = _text(self.artifact_id, "source_identity.artifact_id")
        object.__setattr__(self, "artifact_id", artifact_id)

        if kind == "ARTIFACT_DIGEST":
            if self.version is not None or self.digest_algorithm is None or self.digest is None:
                raise ValueError("artifact digest identity requires only an algorithm and digest")
            algorithm = _text(self.digest_algorithm, "source_identity.digest_algorithm", max_length=32).lower()
            if algorithm != "sha256":
                raise ValueError("only explicitly identified SHA-256 artifact digests are supported")
            object.__setattr__(self, "digest_algorithm", algorithm)
            object.__setattr__(self, "digest", normalize_sha256(self.digest, "source_identity.digest"))
            return

        if self.digest_algorithm is not None or self.digest is not None or self.version is None:
            raise ValueError("artifact version identity requires only a version")
        object.__setattr__(self, "version", _text(self.version, "source_identity.version"))

    def to_dict(self) -> dict[str, str]:
        if self.kind == "GIT_COMMIT_TREE":
            return {
                "kind": self.kind,
                "repository": self.repository or "",
                "commit_sha": self.commit_sha or "",
                "tree_sha": self.tree_sha or "",
            }
        if self.kind == "ARTIFACT_DIGEST":
            return {
                "kind": self.kind,
                "artifact_id": self.artifact_id or "",
                "digest_algorithm": self.digest_algorithm or "",
                "digest": self.digest or "",
            }
        return {
            "kind": self.kind,
            "artifact_id": self.artifact_id or "",
            "version": self.version or "",
        }


def _authority_mapping(authority: SpecialistAuthority) -> dict[str, object]:
    return {
        "slug": authority.slug,
        "authority_class": authority.authority_class,
        "source_path": authority.source_path,
        "source_blob_sha": authority.source_blob_sha,
        "observe_classes": authority.observe_classes,
        "decide_classes": authority.decide_classes,
        "mutate_classes": authority.mutate_classes,
        "can_dispatch": authority.can_dispatch,
        "can_transition": authority.can_transition,
        "can_validate": authority.can_validate,
        "can_coordinate": authority.can_coordinate,
        "can_implement": authority.can_implement,
        "can_execute_protected_action_without_external_authority": (
            authority.can_execute_protected_action_without_external_authority
        ),
    }


@dataclass(frozen=True, slots=True, repr=False)
class ResponsibilityAdjudicationContext:
    """Normalized local inputs bound for stale-advice detection, always unqualified."""

    task_profile: TaskProfile = field(repr=False)
    workflow_profile: AgenticWorkflowProfile = field(repr=False)
    specialist_authorities: tuple[SpecialistAuthority, ...] = field(repr=False)
    project_work_item_identity: ProjectWorkItemIdentity | None = field(repr=False)
    source_identity: ResponsibilitySourceIdentity | None = field(repr=False)
    authority_registry_revision: str | None
    project_policy_context_revision: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.task_profile, TaskProfile):
            raise TypeError("task_profile must be TaskProfile")
        if not isinstance(self.workflow_profile, AgenticWorkflowProfile):
            raise TypeError("workflow_profile must be AgenticWorkflowProfile")
        if self.workflow_profile.source_task_id != self.task_profile.task_id:
            raise ValueError("workflow profile must bind to the supplied task profile")
        if self.project_work_item_identity is not None and not isinstance(
            self.project_work_item_identity, ProjectWorkItemIdentity
        ):
            raise TypeError("project_work_item_identity must be ProjectWorkItemIdentity or None")
        if self.source_identity is not None and not isinstance(
            self.source_identity, ResponsibilitySourceIdentity
        ):
            raise TypeError("source_identity must be ResponsibilitySourceIdentity or None")

        if self.authority_registry_revision is not None:
            object.__setattr__(
                self,
                "authority_registry_revision",
                _text(self.authority_registry_revision, "authority_registry_revision"),
            )
        if self.project_policy_context_revision is not None:
            object.__setattr__(
                self,
                "project_policy_context_revision",
                _text(self.project_policy_context_revision, "project_policy_context_revision"),
            )

        if not isinstance(self.specialist_authorities, (tuple, list)):
            raise TypeError("specialist_authorities must be a tuple or list")
        normalized: list[SpecialistAuthority] = []
        for authority in self.specialist_authorities:
            if not isinstance(authority, SpecialistAuthority):
                raise TypeError("specialist_authorities entries must be SpecialistAuthority")
            normalized.append(SpecialistAuthority.from_mapping(_authority_mapping(authority)))
        if len(normalized) > len(EXPECTED_SPECIALISTS):
            raise ValueError("specialist_authorities exceeds the canonical specialist count")
        slugs = [authority.slug for authority in normalized]
        if len(slugs) != len(set(slugs)):
            raise ValueError("specialist_authorities contains duplicate slugs")
        unknown = set(slugs) - EXPECTED_SPECIALISTS
        route_roles = set(self.workflow_profile.required_specialists) | {
            self.workflow_profile.primary_owner
        }
        route_roles.update(self.task_profile.reentry_specialists)
        if self.task_profile.primary_owner is not None:
            route_roles.add(self.task_profile.primary_owner)
        if self.task_profile.critic_owner is not None:
            route_roles.add(self.task_profile.critic_owner)
        unknown.update(route_roles - EXPECTED_SPECIALISTS)
        if unknown:
            raise ValueError("responsibility context contains unknown specialist roles")
        object.__setattr__(self, "specialist_authorities", tuple(sorted(normalized, key=lambda item: item.slug)))

    @property
    def trust_qualification(self) -> str:
        """Offline caller data is never promoted to trusted host evidence."""

        return "UNQUALIFIED"

    @property
    def binding_digest(self) -> str | None:
        if (
            self.project_work_item_identity is None
            or self.source_identity is None
            or self.authority_registry_revision is None
        ):
            return None
        authority_by_slug = {item.slug: item for item in self.specialist_authorities}
        if not set(self.workflow_profile.required_specialists).issubset(authority_by_slug):
            return None
        workflow = self.workflow_profile.to_dict()
        workflow["schema_version"] = self.workflow_profile.schema_version
        snapshot = {
            "contract": RESPONSIBILITY_ADJUDICATION_CONTRACT,
            "project_work_item_identity": self.project_work_item_identity.to_dict(),
            "source_identity": self.source_identity.to_dict(),
            "task_profile": self.task_profile.to_dict(),
            "workflow_profile": workflow,
            "specialist_authorities": [
                _authority_mapping(item) for item in self.specialist_authorities
            ],
            "authority_registry_revision": self.authority_registry_revision,
            # This opaque revision binds context only; it never proves policy authority.
            "project_policy_context_revision": self.project_policy_context_revision,
        }
        return "sha256:" + receipt_digest(snapshot)

    def __repr__(self) -> str:
        return (
            "ResponsibilityAdjudicationContext("
            f"binding_digest={self.binding_digest!r}, trust_qualification='UNQUALIFIED')"
        )


@dataclass(frozen=True, slots=True)
class ResponsibilityAdjudicationAdvice:
    """Untrusted advisory recommendation bound to one normalized input snapshot."""

    context_digest: str
    recommendation: str

    def __post_init__(self) -> None:
        digest = _text(self.context_digest, "context_digest", max_length=71)
        if not digest.startswith("sha256:"):
            raise ValueError("context_digest must use the sha256 prefix")
        object.__setattr__(self, "context_digest", "sha256:" + normalize_sha256(digest[7:]))
        recommendation = _text(self.recommendation, "recommendation", max_length=64).upper()
        if recommendation not in _ADVICE_RECOMMENDATIONS:
            raise ValueError("unsupported responsibility recommendation")
        object.__setattr__(self, "recommendation", recommendation)

    @classmethod
    def for_context(
        cls,
        context: ResponsibilityAdjudicationContext,
        recommendation: str,
    ) -> ResponsibilityAdjudicationAdvice:
        if not isinstance(context, ResponsibilityAdjudicationContext):
            raise TypeError("context must be ResponsibilityAdjudicationContext")
        digest = context.binding_digest
        if digest is None:
            raise ValueError("context is insufficiently bound for responsibility advice")
        return cls(context_digest=digest, recommendation=recommendation)

    def to_dict(self) -> dict[str, str]:
        return {
            "contract": RESPONSIBILITY_ADJUDICATION_CONTRACT,
            "context_digest": self.context_digest,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class ResponsibilityAdjudicationResult:
    """Local outcome whose fixed boundary fields can never authorize or dispatch."""

    decision: str
    context_digest: str | None

    def __post_init__(self) -> None:
        decision = _text(self.decision, "decision", max_length=64).upper()
        if decision not in _RESULT_DECISIONS:
            raise ValueError("unsupported responsibility adjudication decision")
        object.__setattr__(self, "decision", decision)
        if self.context_digest is not None:
            digest = _text(self.context_digest, "context_digest", max_length=71)
            if not digest.startswith("sha256:"):
                raise ValueError("context_digest must use the sha256 prefix")
            object.__setattr__(self, "context_digest", "sha256:" + normalize_sha256(digest[7:]))

    @property
    def trust_qualification(self) -> str:
        return "UNQUALIFIED"

    @property
    def may_authorize(self) -> bool:
        return False

    @property
    def may_dispatch(self) -> bool:
        return False

    @property
    def may_activate_tuner(self) -> bool:
        return False

    @property
    def may_issue_completion_credit(self) -> bool:
        return False

    @property
    def may_block_read_only_assessment(self) -> bool:
        return False

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": RESPONSIBILITY_ADJUDICATION_CONTRACT,
            "decision": self.decision,
            "context_digest": self.context_digest,
            "trust_qualification": self.trust_qualification,
            "may_authorize": self.may_authorize,
            "may_dispatch": self.may_dispatch,
            "may_activate_tuner": self.may_activate_tuner,
            "may_issue_completion_credit": self.may_issue_completion_credit,
            "may_block_read_only_assessment": self.may_block_read_only_assessment,
        }


def _clear_single_owner_route(context: ResponsibilityAdjudicationContext) -> bool:
    task = context.task_profile
    workflow = context.workflow_profile
    return (
        len(task.authority_domains) == 1
        and len(workflow.required_specialists) == 1
        and workflow.concurrency_mode == "SINGLE_OWNER"
        and workflow.primary_owner == workflow.required_specialists[0]
        and task.primary_owner in (None, workflow.primary_owner)
        and not task.reentry_specialists
        and task.critic_owner is None
        and workflow.critic_contract_id is None
        and not workflow.escalation_reasons
    )


def evaluate_responsibility_advice(
    context: ResponsibilityAdjudicationContext,
    advice: ResponsibilityAdjudicationAdvice | None,
    *,
    conductor_requested: bool,
) -> ResponsibilityAdjudicationResult:
    """Validate optional advice freshness without changing routing or action authority.

    A multi-specialist proposal alone does not request JEV. Conductor must request
    this optional review; clear single-owner routes always bypass it.
    """

    if not isinstance(context, ResponsibilityAdjudicationContext):
        raise TypeError("context must be ResponsibilityAdjudicationContext")
    if advice is not None and not isinstance(advice, ResponsibilityAdjudicationAdvice):
        raise TypeError("advice must be ResponsibilityAdjudicationAdvice or None")
    if type(conductor_requested) is not bool:
        raise TypeError("conductor_requested must be an exact boolean")

    digest = context.binding_digest
    if not conductor_requested or _clear_single_owner_route(context) or digest is None or advice is None:
        return ResponsibilityAdjudicationResult(RESPONSIBILITY_NO_ADVICE, digest)
    if advice.context_digest != digest:
        return ResponsibilityAdjudicationResult(RESPONSIBILITY_STALE, digest)
    return ResponsibilityAdjudicationResult(advice.recommendation, digest)


__all__ = [
    "RESPONSIBILITY_ABSTAIN",
    "RESPONSIBILITY_ADJUDICATION_CONTRACT",
    "RESPONSIBILITY_CONDUCTOR_RECHECK_RECOMMENDED",
    "RESPONSIBILITY_NO_ADVICE",
    "RESPONSIBILITY_OWNERSHIP_CONFLICT",
    "RESPONSIBILITY_OWNERSHIP_GAP",
    "RESPONSIBILITY_ROUTE_SUPPORTED",
    "RESPONSIBILITY_STALE",
    "ProjectWorkItemIdentity",
    "ResponsibilityAdjudicationAdvice",
    "ResponsibilityAdjudicationContext",
    "ResponsibilityAdjudicationResult",
    "ResponsibilitySourceIdentity",
    "evaluate_responsibility_advice",
]
