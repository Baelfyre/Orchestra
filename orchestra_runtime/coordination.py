from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
from types import MappingProxyType

from .errors import (
    ConflictingCoordinationSignalError,
    CoordinationReadinessError,
    InvalidCoordinationContractError,
    InvalidCoordinationSignalError,
    InvalidCoordinationTransitionError,
)
from .interfaces import ICoordinationController
from .models import AuditEventType, RuntimeAuditEvent


COORDINATION_CANONICALIZATION_VERSION = "orchestra-coordination-runtime-v1"
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _text(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise InvalidCoordinationContractError(
            f"{field_name} must be non-empty",
            "EMPTY_COORDINATION_FIELD",
            {"field": field_name},
        )
    return text


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name).casefold()
    if not IDENTIFIER_PATTERN.fullmatch(text):
        raise InvalidCoordinationContractError(
            f"{field_name} must be a canonical identifier",
            "INVALID_COORDINATION_IDENTIFIER",
            {"field": field_name},
        )
    return text


def _sha(value: object, field_name: str = "baseline_sha") -> str:
    text = _text(value, field_name).casefold()
    if not SHA_PATTERN.fullmatch(text):
        raise InvalidCoordinationContractError(
            f"{field_name} must be a full 40-character Git SHA",
            "INVALID_BASELINE_SHA",
            {"field": field_name},
        )
    return text


def _sorted_identifiers(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted({_identifier(item, field_name) for item in values}))
    if any(not item for item in normalized):
        raise InvalidCoordinationContractError(
            f"{field_name} contains an empty identifier",
            "EMPTY_COORDINATION_FIELD",
            {"field": field_name},
        )
    return normalized


def _sorted_text(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted({_text(item, field_name) for item in values}))
    return normalized


def _ordered_text(
    values: tuple[str, ...] | list[str],
    field_name: str,
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    normalized = tuple(_text(item, field_name) for item in values)
    if not allow_empty and not normalized:
        raise InvalidCoordinationContractError(
            f"{field_name} must not be empty",
            "EMPTY_COORDINATION_COLLECTION",
            {"field": field_name},
        )
    return normalized


def _exact_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise InvalidCoordinationContractError(
            f"{field_name} must be an exact boolean",
            "INVALID_COORDINATION_BOOLEAN",
            {"field": field_name},
        )
    return value


def _positive_revision(value: object, field_name: str = "revision") -> int:
    if type(value) is not int or value < 1:
        raise InvalidCoordinationContractError(
            f"{field_name} must be a positive integer",
            "INVALID_COORDINATION_REVISION",
            {"field": field_name},
        )
    return value


def _optional_identifier(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _identifier(value, field_name)


def _optional_text(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _relative_path(value: object) -> str:
    text = _text(value, "path").replace("\\", "/")
    if (
        text.startswith("/")
        or text.startswith("//")
        or re.match(r"^[A-Za-z]:", text)
        or ":" in text.split("/", 1)[0]
    ):
        raise InvalidCoordinationContractError(
            "artifact path must be repository-relative",
            "UNSAFE_COORDINATION_PATH",
            {"path": text},
        )
    path = PurePosixPath(text)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise InvalidCoordinationContractError(
            "artifact path must not contain traversal or empty segments",
            "UNSAFE_COORDINATION_PATH",
            {"path": text},
        )
    return path.as_posix()


class ActivationDecision(str, Enum):
    BYPASS_SINGLE_OWNER = "BYPASS_SINGLE_OWNER"
    ACTIVATE_MULTI_DOMAIN = "ACTIVATE_MULTI_DOMAIN"
    ACTIVATE_LATE_BOUNDARY_CROSSING = "ACTIVATE_LATE_BOUNDARY_CROSSING"
    ACTIVATE_CONTRADICTION = "ACTIVATE_CONTRADICTION"
    ACTIVATE_MISSING_OWNER = "ACTIVATE_MISSING_OWNER"
    ACTIVATE_STALE_CONTRACT = "ACTIVATE_STALE_CONTRACT"


class CollaborationStatus(str, Enum):
    BYPASSED = "BYPASSED"
    COLLECTING = "COLLECTING"
    INCOMPLETE = "INCOMPLETE"
    CONTRADICTED = "CONTRADICTED"
    READY = "READY"
    FROZEN = "FROZEN"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    CLOSED = "CLOSED"


class ContractReadiness(str, Enum):
    COLLECTING = "COLLECTING"
    INCOMPLETE = "INCOMPLETE"
    CONTRADICTED = "CONTRADICTED"
    READY_FOR_FREEZE = "READY_FOR_FREEZE"
    FROZEN = "FROZEN"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    CLOSED = "CLOSED"


class CoordinationSignalType(str, Enum):
    MARK_INCOMPLETE = "MARK_INCOMPLETE"
    MARK_CONTRADICTED = "MARK_CONTRADICTED"
    MARK_READY = "MARK_READY"
    FREEZE = "FREEZE"
    INVALIDATE = "INVALIDATE"
    REOPEN_COLLECTION = "REOPEN_COLLECTION"
    SUPERSEDE = "SUPERSEDE"
    CLOSE = "CLOSE"


class InvalidationStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


class InvalidationTargetKind(str, Enum):
    CONTRACT_SECTION = "CONTRACT_SECTION"
    ARTIFACT = "ARTIFACT"
    EVIDENCE = "EVIDENCE"
    REVIEW = "REVIEW"
    DIAGRAM = "DIAGRAM"
    DOCUMENTATION = "DOCUMENTATION"
    IMPLEMENTATION = "IMPLEMENTATION"


class ArtifactLifecycleState(str, Enum):
    ABSENT = "ABSENT"
    PREEXISTING = "PREEXISTING"
    GENERATED = "GENERATED"
    MODIFIED = "MODIFIED"
    RETAIN = "RETAIN"
    CLEANUP_PENDING = "CLEANUP_PENDING"
    CLEANED = "CLEANED"


class SpecialistParticipationRole(str, Enum):
    ACCOUNTABLE_OWNER = "ACCOUNTABLE_OWNER"
    COLLABORATOR = "COLLABORATOR"
    IMPLEMENTATION_OWNER = "IMPLEMENTATION_OWNER"
    VALIDATION_OWNER = "VALIDATION_OWNER"
    CONTINUITY_OWNER = "CONTINUITY_OWNER"
    VISUAL_MODEL_OWNER = "VISUAL_MODEL_OWNER"


class DependencyKind(str, Enum):
    REQUIRES = "REQUIRES"
    INFORMS = "INFORMS"
    INVALIDATES = "INVALIDATES"
    REVIEWS = "REVIEWS"
    GENERATES = "GENERATES"


class ContradictionStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class CoordinationValidationResult:
    allowed: bool
    status: str
    blocker_codes: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        allowed = _exact_bool(self.allowed, "allowed")
        status = _identifier(self.status, "status").upper()
        blocker_codes = tuple(_identifier(item, "blocker_code").upper() for item in self.blocker_codes)
        reasons = tuple(_text(item, "reason") for item in self.reasons)
        if len(set(blocker_codes)) != len(blocker_codes):
            raise InvalidCoordinationContractError(
                "blocker codes must be unique",
                "INVALID_COORDINATION_VALIDATION_RESULT",
            )
        if allowed and blocker_codes:
            raise InvalidCoordinationContractError(
                "allowed validation result cannot include blocker codes",
                "INVALID_COORDINATION_VALIDATION_RESULT",
            )
        if len(blocker_codes) != len(reasons) and blocker_codes:
            raise InvalidCoordinationContractError(
                "blocker codes and reasons must have equal cardinality",
                "INVALID_COORDINATION_VALIDATION_RESULT",
            )
        object.__setattr__(self, "allowed", allowed)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "blocker_codes", blocker_codes)
        object.__setattr__(self, "reasons", reasons)

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "status": self.status,
            "blocker_codes": list(self.blocker_codes),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class CollaborationParticipant:
    specialist_slug: str
    participation_roles: tuple[SpecialistParticipationRole, ...]
    accountable_layers: tuple[str, ...] = ()
    collaborating_layers: tuple[str, ...] = ()
    required: bool = True
    review_order: int = 0

    def __post_init__(self) -> None:
        specialist_slug = _identifier(self.specialist_slug, "specialist_slug")
        roles = tuple(
            sorted(
                {SpecialistParticipationRole(item) for item in self.participation_roles},
                key=lambda item: item.value,
            )
        )
        if not roles:
            raise InvalidCoordinationContractError(
                "participant requires at least one participation role",
                "MISSING_PARTICIPATION_ROLE",
                {"specialist_slug": specialist_slug},
            )
        accountable_layers = _sorted_identifiers(self.accountable_layers, "accountable_layer")
        collaborating_layers = _sorted_identifiers(self.collaborating_layers, "collaborating_layer")
        required = _exact_bool(self.required, "required")
        if type(self.review_order) is not int or self.review_order < 0:
            raise InvalidCoordinationContractError(
                "review_order must be a non-negative integer",
                "INVALID_REVIEW_ORDER",
                {"specialist_slug": specialist_slug},
            )
        if accountable_layers and SpecialistParticipationRole.ACCOUNTABLE_OWNER not in roles:
            raise InvalidCoordinationContractError(
                "accountable layers require ACCOUNTABLE_OWNER role",
                "ACCOUNTABLE_ROLE_MISMATCH",
                {"specialist_slug": specialist_slug},
            )
        object.__setattr__(self, "specialist_slug", specialist_slug)
        object.__setattr__(self, "participation_roles", roles)
        object.__setattr__(self, "accountable_layers", accountable_layers)
        object.__setattr__(self, "collaborating_layers", collaborating_layers)
        object.__setattr__(self, "required", required)

    def to_dict(self) -> dict[str, object]:
        return {
            "specialist_slug": self.specialist_slug,
            "participation_roles": [item.value for item in self.participation_roles],
            "accountable_layers": list(self.accountable_layers),
            "collaborating_layers": list(self.collaborating_layers),
            "required": self.required,
            "review_order": self.review_order,
        }


@dataclass(frozen=True, slots=True)
class CollaborationDependency:
    dependency_id: str
    source_specialist: str
    target_specialist: str
    dependency_kind: DependencyKind
    contract_section_refs: tuple[str, ...] = ()
    invalidation_triggers: tuple[str, ...] = ()
    blocking: bool = True

    def __post_init__(self) -> None:
        dependency_id = _identifier(self.dependency_id, "dependency_id")
        source = _identifier(self.source_specialist, "source_specialist")
        target = _identifier(self.target_specialist, "target_specialist")
        if source == target:
            raise InvalidCoordinationContractError(
                "coordination dependency cannot be a self-edge",
                "SELF_COORDINATION_DEPENDENCY",
                {"dependency_id": dependency_id},
            )
        object.__setattr__(self, "dependency_id", dependency_id)
        object.__setattr__(self, "source_specialist", source)
        object.__setattr__(self, "target_specialist", target)
        object.__setattr__(self, "dependency_kind", DependencyKind(self.dependency_kind))
        object.__setattr__(
            self,
            "contract_section_refs",
            _sorted_identifiers(self.contract_section_refs, "contract_section_ref"),
        )
        object.__setattr__(
            self,
            "invalidation_triggers",
            _sorted_identifiers(self.invalidation_triggers, "invalidation_trigger"),
        )
        object.__setattr__(self, "blocking", _exact_bool(self.blocking, "blocking"))

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency_id": self.dependency_id,
            "source_specialist": self.source_specialist,
            "target_specialist": self.target_specialist,
            "dependency_kind": self.dependency_kind.value,
            "contract_section_refs": list(self.contract_section_refs),
            "invalidation_triggers": list(self.invalidation_triggers),
            "blocking": self.blocking,
        }


def _has_blocking_cycle(
    participants: tuple[CollaborationParticipant, ...],
    dependencies: tuple[CollaborationDependency, ...],
) -> bool:
    graph = {item.specialist_slug: set() for item in participants}
    for dependency in dependencies:
        if dependency.blocking and dependency.dependency_kind is not DependencyKind.REVIEWS:
            graph[dependency.source_specialist].add(dependency.target_specialist)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in graph[node]:
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in sorted(graph))


@dataclass(frozen=True, slots=True)
class CollaborationGraph:
    graph_id: str
    session_id: str
    participants: tuple[CollaborationParticipant, ...]
    dependencies: tuple[CollaborationDependency, ...]
    affected_layers: tuple[str, ...]
    implementation_owner: str | None
    validation_owner: str | None
    continuity_owner: str | None
    visual_model_owner: str | None = None
    revision: int = 1
    canonicalization_version: str = COORDINATION_CANONICALIZATION_VERSION
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        graph_id = _identifier(self.graph_id, "graph_id")
        session_id = _identifier(self.session_id, "session_id")
        participants = tuple(sorted(tuple(self.participants), key=lambda item: item.specialist_slug))
        dependencies = tuple(sorted(tuple(self.dependencies), key=lambda item: item.dependency_id))
        participant_ids = tuple(item.specialist_slug for item in participants)
        if not participants or len(set(participant_ids)) != len(participant_ids):
            raise InvalidCoordinationContractError(
                "collaboration graph requires unique participants",
                "INVALID_COLLABORATION_PARTICIPANTS",
                {"graph_id": graph_id},
            )
        dependency_ids = tuple(item.dependency_id for item in dependencies)
        if len(set(dependency_ids)) != len(dependency_ids):
            raise InvalidCoordinationContractError(
                "collaboration dependencies must have unique identifiers",
                "DUPLICATE_COORDINATION_DEPENDENCY",
                {"graph_id": graph_id},
            )
        participant_set = set(participant_ids)
        for dependency in dependencies:
            if dependency.source_specialist not in participant_set or dependency.target_specialist not in participant_set:
                raise InvalidCoordinationContractError(
                    "dependency references an unknown participant",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"dependency_id": dependency.dependency_id},
                )
        if _has_blocking_cycle(participants, dependencies):
            raise InvalidCoordinationContractError(
                "blocking coordination dependencies must be acyclic",
                "COORDINATION_DEPENDENCY_CYCLE",
                {"graph_id": graph_id},
            )

        affected_layers = _sorted_identifiers(self.affected_layers, "affected_layer")
        if not affected_layers:
            raise InvalidCoordinationContractError(
                "activated collaboration graph requires affected layers",
                "MISSING_AFFECTED_LAYERS",
                {"graph_id": graph_id},
            )

        layer_owners: dict[str, str] = {}
        for participant in participants:
            for layer in participant.accountable_layers:
                if layer in layer_owners:
                    raise InvalidCoordinationContractError(
                        "each affected layer may have only one accountable owner",
                        "DUPLICATE_LAYER_OWNER",
                        {"layer": layer},
                    )
                layer_owners[layer] = participant.specialist_slug
            unknown_layers = set(participant.accountable_layers + participant.collaborating_layers) - set(affected_layers)
            if unknown_layers:
                raise InvalidCoordinationContractError(
                    "participant references a layer outside the affected layer set",
                    "UNKNOWN_AFFECTED_LAYER",
                    {"specialist_slug": participant.specialist_slug},
                )

        implementation_owner = _optional_identifier(self.implementation_owner, "implementation_owner")
        validation_owner = _optional_identifier(self.validation_owner, "validation_owner")
        continuity_owner = _optional_identifier(self.continuity_owner, "continuity_owner")
        visual_model_owner = _optional_identifier(self.visual_model_owner, "visual_model_owner")

        for field_name, owner, role in (
            ("implementation_owner", implementation_owner, SpecialistParticipationRole.IMPLEMENTATION_OWNER),
            ("validation_owner", validation_owner, SpecialistParticipationRole.VALIDATION_OWNER),
            ("continuity_owner", continuity_owner, SpecialistParticipationRole.CONTINUITY_OWNER),
            ("visual_model_owner", visual_model_owner, SpecialistParticipationRole.VISUAL_MODEL_OWNER),
        ):
            if owner is None:
                continue
            if owner not in participant_set:
                raise InvalidCoordinationContractError(
                    f"{field_name} references an unknown participant",
                    "UNKNOWN_COORDINATION_OWNER",
                    {"field": field_name},
                )
            participant = next(item for item in participants if item.specialist_slug == owner)
            if role not in participant.participation_roles:
                raise InvalidCoordinationContractError(
                    f"{field_name} does not hold the required participation role",
                    "COORDINATION_OWNER_ROLE_MISMATCH",
                    {"field": field_name, "specialist_slug": owner},
                )
            if owner == "the-tuner" and field_name in {
                "implementation_owner",
                "validation_owner",
                "continuity_owner",
            }:
                raise InvalidCoordinationContractError(
                    "The Tuner cannot own implementation, validation, or continuity authority",
                    "TUNER_AUTHORITY_EXPANSION",
                    {"field": field_name},
                )

        revision = _positive_revision(self.revision)
        canonicalization_version = _text(self.canonicalization_version, "canonicalization_version")
        if canonicalization_version != COORDINATION_CANONICALIZATION_VERSION:
            raise InvalidCoordinationContractError(
                "unsupported coordination canonicalization version",
                "UNSUPPORTED_COORDINATION_VERSION",
                {"version": canonicalization_version},
            )

        object.__setattr__(self, "graph_id", graph_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "participants", participants)
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "affected_layers", affected_layers)
        object.__setattr__(self, "implementation_owner", implementation_owner)
        object.__setattr__(self, "validation_owner", validation_owner)
        object.__setattr__(self, "continuity_owner", continuity_owner)
        object.__setattr__(self, "visual_model_owner", visual_model_owner)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "canonicalization_version", canonicalization_version)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "graph_id": self.graph_id,
            "session_id": self.session_id,
            "participants": [item.to_dict() for item in self.participants],
            "dependencies": [item.to_dict() for item in self.dependencies],
            "affected_layers": list(self.affected_layers),
            "implementation_owner": self.implementation_owner,
            "validation_owner": self.validation_owner,
            "continuity_owner": self.continuity_owner,
            "visual_model_owner": self.visual_model_owner,
            "revision": self.revision,
            "canonicalization_version": self.canonicalization_version,
        }

    def accountable_owner_for(self, layer: str) -> str | None:
        normalized = _identifier(layer, "layer")
        for participant in self.participants:
            if normalized in participant.accountable_layers:
                return participant.specialist_slug
        return None

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class ContractSectionRecord:
    section_id: str
    layer: str
    owner_specialist: str
    revision: int
    content_identity: str
    dependency_refs: tuple[str, ...] = ()
    acceptance_criteria_refs: tuple[str, ...] = ()
    required_reviewer_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "section_id", _identifier(self.section_id, "section_id"))
        object.__setattr__(self, "layer", _identifier(self.layer, "layer"))
        object.__setattr__(self, "owner_specialist", _identifier(self.owner_specialist, "owner_specialist"))
        object.__setattr__(self, "revision", _positive_revision(self.revision))
        content_identity = _text(self.content_identity, "content_identity").casefold()
        if not re.fullmatch(r"[0-9a-f]{64}", content_identity):
            raise InvalidCoordinationContractError(
                "content_identity must be a SHA-256 digest",
                "INVALID_SECTION_CONTENT_IDENTITY",
                {"section_id": self.section_id},
            )
        object.__setattr__(self, "content_identity", content_identity)
        object.__setattr__(self, "dependency_refs", _sorted_identifiers(self.dependency_refs, "dependency_ref"))
        object.__setattr__(
            self,
            "acceptance_criteria_refs",
            _sorted_identifiers(self.acceptance_criteria_refs, "acceptance_criteria_ref"),
        )
        object.__setattr__(
            self,
            "required_reviewer_refs",
            _sorted_identifiers(self.required_reviewer_refs, "required_reviewer_ref"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "layer": self.layer,
            "owner_specialist": self.owner_specialist,
            "revision": self.revision,
            "content_identity": self.content_identity,
            "dependency_refs": list(self.dependency_refs),
            "acceptance_criteria_refs": list(self.acceptance_criteria_refs),
            "required_reviewer_refs": list(self.required_reviewer_refs),
        }


@dataclass(frozen=True, slots=True)
class CrossLayerContractPacket:
    contract_id: str
    session_id: str
    revision: int
    objective: str
    acceptance_criteria: tuple[str, ...]
    baseline_sha: str
    affected_layers: tuple[str, ...]
    section_records: tuple[ContractSectionRecord, ...]
    assumptions: tuple[str, ...] = ()
    open_decisions: tuple[str, ...] = ()
    prohibited_scope: tuple[str, ...] = ()
    validation_requirements: tuple[str, ...] = ()
    artifact_lifecycle_refs: tuple[str, ...] = ()
    invalidation_dependency_refs: tuple[str, ...] = ()
    owner_refs: tuple[str, ...] = ()
    reviewer_refs: tuple[str, ...] = ()
    status: ContractReadiness = ContractReadiness.COLLECTING
    canonicalization_version: str = COORDINATION_CANONICALIZATION_VERSION
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        contract_id = _identifier(self.contract_id, "contract_id")
        session_id = _identifier(self.session_id, "session_id")
        revision = _positive_revision(self.revision)
        objective = _text(self.objective, "objective")
        acceptance_criteria = _ordered_text(self.acceptance_criteria, "acceptance_criterion")
        baseline_sha = _sha(self.baseline_sha)
        affected_layers = _sorted_identifiers(self.affected_layers, "affected_layer")
        if not affected_layers:
            raise InvalidCoordinationContractError(
                "contract packet requires affected layers",
                "MISSING_AFFECTED_LAYERS",
                {"contract_id": contract_id},
            )
        section_records = tuple(sorted(tuple(self.section_records), key=lambda item: item.section_id))
        section_ids = tuple(item.section_id for item in section_records)
        if len(set(section_ids)) != len(section_ids):
            raise InvalidCoordinationContractError(
                "contract section identifiers must be unique",
                "DUPLICATE_CONTRACT_SECTION",
                {"contract_id": contract_id},
            )
        section_layers = tuple(item.layer for item in section_records)
        if len(set(section_layers)) != len(section_layers):
            raise InvalidCoordinationContractError(
                "each affected layer may have only one contract section",
                "DUPLICATE_CONTRACT_LAYER",
                {"contract_id": contract_id},
            )
        unknown_layers = set(section_layers) - set(affected_layers)
        if unknown_layers:
            raise InvalidCoordinationContractError(
                "contract section references an unknown affected layer",
                "UNKNOWN_CONTRACT_LAYER",
                {"contract_id": contract_id},
            )

        assumptions = _ordered_text(self.assumptions, "assumption")
        open_decisions = _ordered_text(self.open_decisions, "open_decision")
        prohibited_scope = _sorted_text(self.prohibited_scope, "prohibited_scope")
        validation_requirements = _ordered_text(self.validation_requirements, "validation_requirement")
        artifact_lifecycle_refs = _sorted_identifiers(self.artifact_lifecycle_refs, "artifact_lifecycle_ref")
        invalidation_dependency_refs = _sorted_identifiers(
            self.invalidation_dependency_refs,
            "invalidation_dependency_ref",
        )
        owner_refs = _sorted_identifiers(self.owner_refs, "owner_ref")
        reviewer_refs = _sorted_identifiers(self.reviewer_refs, "reviewer_ref")
        status = ContractReadiness(self.status)
        canonicalization_version = _text(self.canonicalization_version, "canonicalization_version")
        if canonicalization_version != COORDINATION_CANONICALIZATION_VERSION:
            raise InvalidCoordinationContractError(
                "unsupported coordination canonicalization version",
                "UNSUPPORTED_COORDINATION_VERSION",
                {"version": canonicalization_version},
            )

        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "objective", objective)
        object.__setattr__(self, "acceptance_criteria", acceptance_criteria)
        object.__setattr__(self, "baseline_sha", baseline_sha)
        object.__setattr__(self, "affected_layers", affected_layers)
        object.__setattr__(self, "section_records", section_records)
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "open_decisions", open_decisions)
        object.__setattr__(self, "prohibited_scope", prohibited_scope)
        object.__setattr__(self, "validation_requirements", validation_requirements)
        object.__setattr__(self, "artifact_lifecycle_refs", artifact_lifecycle_refs)
        object.__setattr__(self, "invalidation_dependency_refs", invalidation_dependency_refs)
        object.__setattr__(self, "owner_refs", owner_refs)
        object.__setattr__(self, "reviewer_refs", reviewer_refs)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "canonicalization_version", canonicalization_version)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "session_id": self.session_id,
            "revision": self.revision,
            "objective": self.objective,
            "acceptance_criteria": list(self.acceptance_criteria),
            "baseline_sha": self.baseline_sha,
            "affected_layers": list(self.affected_layers),
            "section_records": [item.to_dict() for item in self.section_records],
            "assumptions": list(self.assumptions),
            "open_decisions": list(self.open_decisions),
            "prohibited_scope": list(self.prohibited_scope),
            "validation_requirements": list(self.validation_requirements),
            "artifact_lifecycle_refs": list(self.artifact_lifecycle_refs),
            "invalidation_dependency_refs": list(self.invalidation_dependency_refs),
            "owner_refs": list(self.owner_refs),
            "reviewer_refs": list(self.reviewer_refs),
            "status": self.status.value,
            "canonicalization_version": self.canonicalization_version,
        }

    def with_status(self, status: ContractReadiness) -> CrossLayerContractPacket:
        return replace(self, status=status)

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class SpecialistHandoffDelta:
    delta_id: str
    session_id: str
    source_specialist: str
    target_specialist: str
    source_contract_revision: int
    confirmed_decision_refs: tuple[str, ...] = ()
    constraint_refs: tuple[str, ...] = ()
    updated_section_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    open_question_refs: tuple[str, ...] = ()
    required_reviewer_refs: tuple[str, ...] = ()
    invalidation_trigger_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    change_identity_ref: str = ""
    artifact_lifecycle_refs: tuple[str, ...] = ()
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        delta_id = _identifier(self.delta_id, "delta_id")
        session_id = _identifier(self.session_id, "session_id")
        source = _identifier(self.source_specialist, "source_specialist")
        target = _identifier(self.target_specialist, "target_specialist")
        if source == target:
            raise InvalidCoordinationContractError(
                "handoff source and target must differ",
                "SELF_SPECIALIST_HANDOFF",
                {"delta_id": delta_id},
            )
        confirmed = _sorted_identifiers(self.confirmed_decision_refs, "confirmed_decision_ref")
        constraints = _sorted_identifiers(self.constraint_refs, "constraint_ref")
        updated = _sorted_identifiers(self.updated_section_refs, "updated_section_ref")
        assumptions = _ordered_text(self.assumptions, "assumption")
        questions = _sorted_identifiers(self.open_question_refs, "open_question_ref")
        reviewers = _sorted_identifiers(self.required_reviewer_refs, "required_reviewer_ref")
        triggers = _sorted_identifiers(self.invalidation_trigger_refs, "invalidation_trigger_ref")
        evidence = _sorted_identifiers(self.evidence_refs, "evidence_ref")
        change_identity_ref = _identifier(self.change_identity_ref, "change_identity_ref")
        artifacts = _sorted_identifiers(self.artifact_lifecycle_refs, "artifact_lifecycle_ref")
        if not any((confirmed, constraints, updated, assumptions, questions, triggers, evidence, artifacts)):
            raise InvalidCoordinationContractError(
                "handoff delta must preserve decision, constraint, question, evidence, or artifact context",
                "CONTEXT_FREE_HANDOFF",
                {"delta_id": delta_id},
            )
        object.__setattr__(self, "delta_id", delta_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "source_specialist", source)
        object.__setattr__(self, "target_specialist", target)
        object.__setattr__(self, "source_contract_revision", _positive_revision(self.source_contract_revision))
        object.__setattr__(self, "confirmed_decision_refs", confirmed)
        object.__setattr__(self, "constraint_refs", constraints)
        object.__setattr__(self, "updated_section_refs", updated)
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "open_question_refs", questions)
        object.__setattr__(self, "required_reviewer_refs", reviewers)
        object.__setattr__(self, "invalidation_trigger_refs", triggers)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "change_identity_ref", change_identity_ref)
        object.__setattr__(self, "artifact_lifecycle_refs", artifacts)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "delta_id": self.delta_id,
            "session_id": self.session_id,
            "source_specialist": self.source_specialist,
            "target_specialist": self.target_specialist,
            "source_contract_revision": self.source_contract_revision,
            "confirmed_decision_refs": list(self.confirmed_decision_refs),
            "constraint_refs": list(self.constraint_refs),
            "updated_section_refs": list(self.updated_section_refs),
            "assumptions": list(self.assumptions),
            "open_question_refs": list(self.open_question_refs),
            "required_reviewer_refs": list(self.required_reviewer_refs),
            "invalidation_trigger_refs": list(self.invalidation_trigger_refs),
            "evidence_refs": list(self.evidence_refs),
            "change_identity_ref": self.change_identity_ref,
            "artifact_lifecycle_refs": list(self.artifact_lifecycle_refs),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class InvalidationEvent:
    event_id: str
    session_id: str
    source_revision: int
    trigger_ref: str
    target_kind: InvalidationTargetKind
    target_refs: tuple[str, ...]
    affected_specialist_refs: tuple[str, ...]
    required_reentry_refs: tuple[str, ...]
    status: InvalidationStatus = InvalidationStatus.OPEN
    opened_reason_code: str = "CONTRACT_INVALIDATED"
    resolved_by_revision: int | None = None
    evidence_refresh_refs: tuple[str, ...] = ()
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        event_id = _identifier(self.event_id, "event_id")
        session_id = _identifier(self.session_id, "session_id")
        source_revision = _positive_revision(self.source_revision, "source_revision")
        trigger_ref = _identifier(self.trigger_ref, "trigger_ref")
        target_kind = InvalidationTargetKind(self.target_kind)
        target_refs = _sorted_identifiers(self.target_refs, "target_ref")
        affected = _sorted_identifiers(self.affected_specialist_refs, "affected_specialist_ref")
        reentry = _sorted_identifiers(self.required_reentry_refs, "required_reentry_ref")
        if not target_refs or not affected or not reentry:
            raise InvalidCoordinationContractError(
                "invalidation requires targets, affected specialists, and minimal re-entry set",
                "INCOMPLETE_INVALIDATION_EVENT",
                {"event_id": event_id},
            )
        if not set(reentry).issubset(set(affected)):
            raise InvalidCoordinationContractError(
                "required re-entry must be a subset of affected specialists",
                "INVALID_REENTRY_SET",
                {"event_id": event_id},
            )
        status = InvalidationStatus(self.status)
        reason = _identifier(self.opened_reason_code, "opened_reason_code").upper()
        evidence = _sorted_identifiers(self.evidence_refresh_refs, "evidence_refresh_ref")
        resolved = self.resolved_by_revision
        if status is InvalidationStatus.RESOLVED:
            if type(resolved) is not int or resolved <= source_revision or not evidence:
                raise InvalidCoordinationContractError(
                    "resolved invalidation requires a newer revision and refreshed evidence",
                    "INVALID_INVALIDATION_RESOLUTION",
                    {"event_id": event_id},
                )
        elif resolved is not None or evidence:
            raise InvalidCoordinationContractError(
                "open or superseded invalidation cannot carry resolution evidence",
                "INVALID_INVALIDATION_RESOLUTION",
                {"event_id": event_id},
            )
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "source_revision", source_revision)
        object.__setattr__(self, "trigger_ref", trigger_ref)
        object.__setattr__(self, "target_kind", target_kind)
        object.__setattr__(self, "target_refs", target_refs)
        object.__setattr__(self, "affected_specialist_refs", affected)
        object.__setattr__(self, "required_reentry_refs", reentry)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "opened_reason_code", reason)
        object.__setattr__(self, "evidence_refresh_refs", evidence)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "source_revision": self.source_revision,
            "trigger_ref": self.trigger_ref,
            "target_kind": self.target_kind.value,
            "target_refs": list(self.target_refs),
            "affected_specialist_refs": list(self.affected_specialist_refs),
            "required_reentry_refs": list(self.required_reentry_refs),
            "status": self.status.value,
            "opened_reason_code": self.opened_reason_code,
            "resolved_by_revision": self.resolved_by_revision,
            "evidence_refresh_refs": list(self.evidence_refresh_refs),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class ArtifactLifecycleRecord:
    artifact_id: str
    session_id: str
    path: str
    producer_ref: str
    source_ref: str
    pre_execution_state: ArtifactLifecycleState
    current_state: ArtifactLifecycleState
    retention_requirement: str
    cleanup_authority_ref: str
    contract_revision: int
    change_identity_ref: str
    evidence_ref: str
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_id", _identifier(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "session_id", _identifier(self.session_id, "session_id"))
        object.__setattr__(self, "path", _relative_path(self.path))
        object.__setattr__(self, "producer_ref", _identifier(self.producer_ref, "producer_ref"))
        object.__setattr__(self, "source_ref", _identifier(self.source_ref, "source_ref"))
        object.__setattr__(self, "pre_execution_state", ArtifactLifecycleState(self.pre_execution_state))
        object.__setattr__(self, "current_state", ArtifactLifecycleState(self.current_state))
        object.__setattr__(
            self,
            "retention_requirement",
            _identifier(self.retention_requirement, "retention_requirement").upper(),
        )
        object.__setattr__(
            self,
            "cleanup_authority_ref",
            _identifier(self.cleanup_authority_ref, "cleanup_authority_ref"),
        )
        object.__setattr__(self, "contract_revision", _positive_revision(self.contract_revision))
        object.__setattr__(self, "change_identity_ref", _identifier(self.change_identity_ref, "change_identity_ref"))
        object.__setattr__(self, "evidence_ref", _identifier(self.evidence_ref, "evidence_ref"))
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "session_id": self.session_id,
            "path": self.path,
            "producer_ref": self.producer_ref,
            "source_ref": self.source_ref,
            "pre_execution_state": self.pre_execution_state.value,
            "current_state": self.current_state.value,
            "retention_requirement": self.retention_requirement,
            "cleanup_authority_ref": self.cleanup_authority_ref,
            "contract_revision": self.contract_revision,
            "change_identity_ref": self.change_identity_ref,
            "evidence_ref": self.evidence_ref,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class ContradictionRecord:
    contradiction_id: str
    session_id: str
    contract_section_refs: tuple[str, ...]
    specialist_refs: tuple[str, ...]
    impact_refs: tuple[str, ...]
    status: ContradictionStatus
    required_resolution_owner_ref: str
    invalidated_review_refs: tuple[str, ...] = ()
    resolution_ref: str | None = None
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        contradiction_id = _identifier(self.contradiction_id, "contradiction_id")
        session_id = _identifier(self.session_id, "session_id")
        sections = _sorted_identifiers(self.contract_section_refs, "contract_section_ref")
        specialists = _sorted_identifiers(self.specialist_refs, "specialist_ref")
        impacts = _sorted_identifiers(self.impact_refs, "impact_ref")
        if len(sections) < 2 or len(specialists) < 2 or not impacts:
            raise InvalidCoordinationContractError(
                "contradiction requires at least two sections, two specialists, and one impact",
                "INCOMPLETE_CONTRADICTION",
                {"contradiction_id": contradiction_id},
            )
        status = ContradictionStatus(self.status)
        owner = _identifier(self.required_resolution_owner_ref, "required_resolution_owner_ref")
        reviews = _sorted_identifiers(self.invalidated_review_refs, "invalidated_review_ref")
        resolution = _optional_identifier(self.resolution_ref, "resolution_ref")
        if status is ContradictionStatus.RESOLVED and resolution is None:
            raise InvalidCoordinationContractError(
                "resolved contradiction requires a resolution reference",
                "INVALID_CONTRADICTION_RESOLUTION",
                {"contradiction_id": contradiction_id},
            )
        if status is ContradictionStatus.OPEN and resolution is not None:
            raise InvalidCoordinationContractError(
                "open contradiction cannot carry a resolution reference",
                "INVALID_CONTRADICTION_RESOLUTION",
                {"contradiction_id": contradiction_id},
            )
        object.__setattr__(self, "contradiction_id", contradiction_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "contract_section_refs", sections)
        object.__setattr__(self, "specialist_refs", specialists)
        object.__setattr__(self, "impact_refs", impacts)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "required_resolution_owner_ref", owner)
        object.__setattr__(self, "invalidated_review_refs", reviews)
        object.__setattr__(self, "resolution_ref", resolution)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "contradiction_id": self.contradiction_id,
            "session_id": self.session_id,
            "contract_section_refs": list(self.contract_section_refs),
            "specialist_refs": list(self.specialist_refs),
            "impact_refs": list(self.impact_refs),
            "status": self.status.value,
            "required_resolution_owner_ref": self.required_resolution_owner_ref,
            "invalidated_review_refs": list(self.invalidated_review_refs),
            "resolution_ref": self.resolution_ref,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class CoordinationSignal:
    signal_id: str
    session_id: str
    signal_type: CoordinationSignalType
    expected_status: CollaborationStatus
    requested_status: CollaborationStatus
    reason_code: str
    source_component: str
    source_revision: int
    evidence_refs: tuple[str, ...] = ()
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", _identifier(self.signal_id, "signal_id"))
        object.__setattr__(self, "session_id", _identifier(self.session_id, "session_id"))
        object.__setattr__(self, "signal_type", CoordinationSignalType(self.signal_type))
        object.__setattr__(self, "expected_status", CollaborationStatus(self.expected_status))
        object.__setattr__(self, "requested_status", CollaborationStatus(self.requested_status))
        object.__setattr__(self, "reason_code", _identifier(self.reason_code, "reason_code").upper())
        object.__setattr__(self, "source_component", _identifier(self.source_component, "source_component"))
        object.__setattr__(self, "source_revision", _positive_revision(self.source_revision, "source_revision"))
        object.__setattr__(self, "evidence_refs", _sorted_identifiers(self.evidence_refs, "evidence_ref"))
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "session_id": self.session_id,
            "signal_type": self.signal_type.value,
            "expected_status": self.expected_status.value,
            "requested_status": self.requested_status.value,
            "reason_code": self.reason_code,
            "source_component": self.source_component,
            "source_revision": self.source_revision,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class CollaborationSession:
    session_id: str
    task_id: str
    repository_identity: str
    branch: str
    baseline_sha: str
    execution_mode: str
    progression_mode: str
    activation_decision: ActivationDecision
    activation_reason: str
    graph: CollaborationGraph
    contract: CrossLayerContractPacket
    handoff_deltas: tuple[SpecialistHandoffDelta, ...] = ()
    invalidation_events: tuple[InvalidationEvent, ...] = ()
    artifact_lifecycle_records: tuple[ArtifactLifecycleRecord, ...] = ()
    contradictions: tuple[ContradictionRecord, ...] = ()
    status: CollaborationStatus = CollaborationStatus.COLLECTING
    current_revision: int = 1
    last_signal_id: str | None = None
    accepted_signal_fingerprint: str | None = None
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        session_id = _identifier(self.session_id, "session_id")
        task_id = _identifier(self.task_id, "task_id")
        repository_identity = _text(self.repository_identity, "repository_identity")
        branch = _text(self.branch, "branch")
        baseline_sha = _sha(self.baseline_sha)
        execution_mode = _identifier(self.execution_mode, "execution_mode").upper()
        progression_mode = _identifier(self.progression_mode, "progression_mode").upper()
        activation_decision = ActivationDecision(self.activation_decision)
        if activation_decision is ActivationDecision.BYPASS_SINGLE_OWNER:
            raise InvalidCoordinationContractError(
                "single-owner bypass must not create a collaboration session",
                "BYPASS_SESSION_PROHIBITED",
                {"session_id": session_id},
            )
        activation_reason = _text(self.activation_reason, "activation_reason")
        if self.graph.session_id != session_id or self.contract.session_id != session_id:
            raise InvalidCoordinationContractError(
                "graph and contract must belong to the collaboration session",
                "COORDINATION_SESSION_ID_MISMATCH",
                {"session_id": session_id},
            )
        current_revision = _positive_revision(self.current_revision, "current_revision")
        if self.graph.revision != current_revision or self.contract.revision != current_revision:
            raise InvalidCoordinationContractError(
                "session, graph, and contract revisions must match",
                "COORDINATION_REVISION_MISMATCH",
                {"session_id": session_id},
            )
        if self.graph.affected_layers != self.contract.affected_layers:
            raise InvalidCoordinationContractError(
                "graph and contract must cover the same affected layers",
                "COORDINATION_LAYER_MISMATCH",
                {"session_id": session_id},
            )
        if self.contract.baseline_sha != baseline_sha:
            raise InvalidCoordinationContractError(
                "session and contract baseline SHAs must match",
                "COORDINATION_BASELINE_MISMATCH",
                {"session_id": session_id},
            )

        handoffs = tuple(sorted(tuple(self.handoff_deltas), key=lambda item: item.delta_id))
        invalidations = tuple(sorted(tuple(self.invalidation_events), key=lambda item: item.event_id))
        artifacts = tuple(sorted(tuple(self.artifact_lifecycle_records), key=lambda item: item.artifact_id))
        contradictions = tuple(sorted(tuple(self.contradictions), key=lambda item: item.contradiction_id))
        for collection, label in (
            (handoffs, "handoff"),
            (invalidations, "invalidation"),
            (artifacts, "artifact"),
            (contradictions, "contradiction"),
        ):
            identifiers = tuple(
                getattr(item, {
                    "handoff": "delta_id",
                    "invalidation": "event_id",
                    "artifact": "artifact_id",
                    "contradiction": "contradiction_id",
                }[label])
                for item in collection
            )
            if len(set(identifiers)) != len(identifiers):
                raise InvalidCoordinationContractError(
                    f"{label} identifiers must be unique",
                    "DUPLICATE_COORDINATION_RECORD",
                    {"record_type": label},
                )
            if any(item.session_id != session_id for item in collection):
                raise InvalidCoordinationContractError(
                    f"{label} belongs to a different session",
                    "COORDINATION_SESSION_ID_MISMATCH",
                    {"record_type": label},
                )

        participant_ids = {item.specialist_slug for item in self.graph.participants}
        dependency_ids = {item.dependency_id for item in self.graph.dependencies}
        section_ids = {item.section_id for item in self.contract.section_records}
        artifact_ids = {item.artifact_id for item in artifacts}

        for handoff in handoffs:
            if handoff.source_specialist not in participant_ids or handoff.target_specialist not in participant_ids:
                raise InvalidCoordinationContractError(
                    "handoff references an unknown participant",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"delta_id": handoff.delta_id},
                )
            if handoff.source_contract_revision != current_revision:
                raise InvalidCoordinationContractError(
                    "handoff source revision is stale",
                    "STALE_HANDOFF_REVISION",
                    {"delta_id": handoff.delta_id},
                )
        for event in invalidations:
            if not set(event.affected_specialist_refs).issubset(participant_ids):
                raise InvalidCoordinationContractError(
                    "invalidation references an unknown specialist",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"event_id": event.event_id},
                )
            if event.trigger_ref not in dependency_ids:
                raise InvalidCoordinationContractError(
                    "invalidation trigger must reference a declared dependency",
                    "UNDECLARED_INVALIDATION_DEPENDENCY",
                    {"event_id": event.event_id},
                )
        for contradiction in contradictions:
            if not set(contradiction.specialist_refs).issubset(participant_ids):
                raise InvalidCoordinationContractError(
                    "contradiction references an unknown specialist",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"contradiction_id": contradiction.contradiction_id},
                )
            if not set(contradiction.contract_section_refs).issubset(section_ids):
                raise InvalidCoordinationContractError(
                    "contradiction references an unknown contract section",
                    "UNKNOWN_CONTRACT_SECTION",
                    {"contradiction_id": contradiction.contradiction_id},
                )
        if not set(self.contract.artifact_lifecycle_refs).issubset(artifact_ids):
            raise InvalidCoordinationContractError(
                "contract references an unknown artifact lifecycle record",
                "UNKNOWN_ARTIFACT_LIFECYCLE",
                {"session_id": session_id},
            )
        if not set(self.contract.invalidation_dependency_refs).issubset(dependency_ids):
            raise InvalidCoordinationContractError(
                "contract references an unknown invalidation dependency",
                "UNDECLARED_INVALIDATION_DEPENDENCY",
                {"session_id": session_id},
            )

        status = CollaborationStatus(self.status)
        last_signal_id = _optional_identifier(self.last_signal_id, "last_signal_id")
        accepted_fingerprint = _optional_text(
            self.accepted_signal_fingerprint,
            "accepted_signal_fingerprint",
        )
        if bool(last_signal_id) != bool(accepted_fingerprint):
            raise InvalidCoordinationContractError(
                "accepted coordination signal requires both identifier and fingerprint",
                "INVALID_COORDINATION_SIGNAL_IDENTITY",
                {"session_id": session_id},
            )
        if accepted_fingerprint and not re.fullmatch(r"[0-9a-f]{64}", accepted_fingerprint):
            raise InvalidCoordinationContractError(
                "accepted signal fingerprint must be SHA-256",
                "INVALID_COORDINATION_SIGNAL_IDENTITY",
                {"session_id": session_id},
            )

        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "repository_identity", repository_identity)
        object.__setattr__(self, "branch", branch)
        object.__setattr__(self, "baseline_sha", baseline_sha)
        object.__setattr__(self, "execution_mode", execution_mode)
        object.__setattr__(self, "progression_mode", progression_mode)
        object.__setattr__(self, "activation_decision", activation_decision)
        object.__setattr__(self, "activation_reason", activation_reason)
        object.__setattr__(self, "handoff_deltas", handoffs)
        object.__setattr__(self, "invalidation_events", invalidations)
        object.__setattr__(self, "artifact_lifecycle_records", artifacts)
        object.__setattr__(self, "contradictions", contradictions)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "current_revision", current_revision)
        object.__setattr__(self, "last_signal_id", last_signal_id)
        object.__setattr__(self, "accepted_signal_fingerprint", accepted_fingerprint)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    @property
    def open_invalidations(self) -> tuple[InvalidationEvent, ...]:
        return tuple(item for item in self.invalidation_events if item.status is InvalidationStatus.OPEN)

    @property
    def open_contradictions(self) -> tuple[ContradictionRecord, ...]:
        return tuple(item for item in self.contradictions if item.status is ContradictionStatus.OPEN)

    def _identity_payload(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "repository_identity": self.repository_identity,
            "branch": self.branch,
            "baseline_sha": self.baseline_sha,
            "execution_mode": self.execution_mode,
            "progression_mode": self.progression_mode,
            "activation_decision": self.activation_decision.value,
            "activation_reason": self.activation_reason,
            "graph": self.graph.to_dict(),
            "contract": self.contract.to_dict(),
            "handoff_deltas": [item.to_dict() for item in self.handoff_deltas],
            "invalidation_events": [item.to_dict() for item in self.invalidation_events],
            "artifact_lifecycle_records": [item.to_dict() for item in self.artifact_lifecycle_records],
            "contradictions": [item.to_dict() for item in self.contradictions],
            "status": self.status.value,
            "current_revision": self.current_revision,
            "last_signal_id": self.last_signal_id,
            "accepted_signal_fingerprint": self.accepted_signal_fingerprint,
            "canonicalization_version": COORDINATION_CANONICALIZATION_VERSION,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


SIGNAL_DESTINATIONS = MappingProxyType(
    {
        CoordinationSignalType.MARK_INCOMPLETE: CollaborationStatus.INCOMPLETE,
        CoordinationSignalType.MARK_CONTRADICTED: CollaborationStatus.CONTRADICTED,
        CoordinationSignalType.MARK_READY: CollaborationStatus.READY,
        CoordinationSignalType.FREEZE: CollaborationStatus.FROZEN,
        CoordinationSignalType.INVALIDATE: CollaborationStatus.STALE,
        CoordinationSignalType.REOPEN_COLLECTION: CollaborationStatus.COLLECTING,
        CoordinationSignalType.SUPERSEDE: CollaborationStatus.SUPERSEDED,
        CoordinationSignalType.CLOSE: CollaborationStatus.CLOSED,
    }
)

COORDINATION_TRANSITIONS = MappingProxyType(
    {
        CollaborationStatus.COLLECTING: frozenset(
            {
                CollaborationStatus.INCOMPLETE,
                CollaborationStatus.CONTRADICTED,
                CollaborationStatus.READY,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.INCOMPLETE: frozenset(
            {
                CollaborationStatus.COLLECTING,
                CollaborationStatus.CONTRADICTED,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.CONTRADICTED: frozenset(
            {
                CollaborationStatus.COLLECTING,
                CollaborationStatus.SUPERSEDED,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.READY: frozenset(
            {
                CollaborationStatus.FROZEN,
                CollaborationStatus.STALE,
                CollaborationStatus.CONTRADICTED,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.FROZEN: frozenset(
            {
                CollaborationStatus.STALE,
                CollaborationStatus.SUPERSEDED,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.STALE: frozenset(
            {
                CollaborationStatus.COLLECTING,
                CollaborationStatus.CONTRADICTED,
                CollaborationStatus.SUPERSEDED,
                CollaborationStatus.CLOSED,
            }
        ),
        CollaborationStatus.SUPERSEDED: frozenset({CollaborationStatus.CLOSED}),
        CollaborationStatus.CLOSED: frozenset(),
        CollaborationStatus.BYPASSED: frozenset(),
    }
)


class CoordinationController(ICoordinationController):
    def _readiness_blockers(self, session: CollaborationSession) -> tuple[tuple[str, str], ...]:
        blockers: list[tuple[str, str]] = []

        missing_layers = tuple(
            layer for layer in session.graph.affected_layers if session.graph.accountable_owner_for(layer) is None
        )
        if missing_layers:
            blockers.append(
                (
                    "MISSING_ACCOUNTABLE_OWNER",
                    f"affected layers lack accountable owners: {', '.join(missing_layers)}",
                )
            )

        for owner_field in ("implementation_owner", "validation_owner", "continuity_owner"):
            if getattr(session.graph, owner_field) is None:
                blockers.append(
                    (
                        "MISSING_COORDINATION_OWNER",
                        f"{owner_field} is required before contract freeze",
                    )
                )

        section_layers = {item.layer for item in session.contract.section_records}
        missing_sections = tuple(sorted(set(session.contract.affected_layers) - section_layers))
        if missing_sections:
            blockers.append(
                (
                    "MISSING_CONTRACT_SECTION",
                    f"affected layers lack contract sections: {', '.join(missing_sections)}",
                )
            )

        section_owners = {item.owner_specialist for item in session.contract.section_records}
        if not section_owners.issubset(set(session.contract.owner_refs)):
            blockers.append(
                (
                    "MISSING_CONTRACT_OWNER_REFERENCE",
                    "contract owner references do not cover every section owner",
                )
            )

        if not session.contract.acceptance_criteria:
            blockers.append(("MISSING_ACCEPTANCE_CRITERIA", "contract requires acceptance criteria"))
        if not session.contract.prohibited_scope:
            blockers.append(("MISSING_PROHIBITED_SCOPE", "contract requires explicit prohibited scope"))
        if not session.contract.validation_requirements:
            blockers.append(
                (
                    "MISSING_VALIDATION_REQUIREMENTS",
                    "contract requires explicit validation requirements",
                )
            )
        if not session.contract.artifact_lifecycle_refs:
            blockers.append(
                (
                    "MISSING_ARTIFACT_LIFECYCLE",
                    "contract requires an explicit artifact lifecycle record or none-required record",
                )
            )
        if session.contract.open_decisions:
            blockers.append(("OPEN_CONTRACT_DECISIONS", "contract still contains open decisions"))
        if session.open_invalidations:
            blockers.append(("OPEN_INVALIDATION", "open invalidation events require specialist re-entry"))
        if session.open_contradictions:
            blockers.append(("OPEN_CONTRADICTION", "open contradictions require external resolution"))

        return tuple(sorted(blockers))

    def validate(self, session: CollaborationSession) -> CoordinationValidationResult:
        if not isinstance(session, CollaborationSession):
            raise InvalidCoordinationContractError(
                "coordination input must be a CollaborationSession",
                "INVALID_COORDINATION_SESSION",
            )
        blockers = self._readiness_blockers(session)
        readiness_required = session.status in {
            CollaborationStatus.READY,
            CollaborationStatus.FROZEN,
            CollaborationStatus.CLOSED,
        }
        if session.status is CollaborationStatus.CONTRADICTED and not session.open_contradictions:
            blockers += (("MISSING_OPEN_CONTRADICTION", "contradicted status requires an open contradiction"),)
        if session.status is CollaborationStatus.STALE and not session.open_invalidations:
            blockers += (("MISSING_OPEN_INVALIDATION", "stale status requires an open invalidation"),)
        if session.status is CollaborationStatus.FROZEN and session.contract.status is not ContractReadiness.FROZEN:
            blockers += (("CONTRACT_NOT_FROZEN", "frozen session requires frozen contract packet"),)
        if session.status is CollaborationStatus.READY and session.contract.status is not ContractReadiness.READY_FOR_FREEZE:
            blockers += (("CONTRACT_NOT_READY", "ready session requires a ready-for-freeze contract packet"),)
        if session.status is CollaborationStatus.CLOSED and session.contract.status is not ContractReadiness.CLOSED:
            blockers += (("CONTRACT_NOT_CLOSED", "closed session requires closed contract packet"),)

        blockers = tuple(sorted(set(blockers)))
        effective = blockers if readiness_required or session.status in {
            CollaborationStatus.CONTRADICTED,
            CollaborationStatus.STALE,
        } else ()
        if effective:
            return CoordinationValidationResult(
                False,
                "BLOCKED",
                tuple(code for code, _ in effective),
                tuple(reason for _, reason in effective),
            )
        return CoordinationValidationResult(True, "VALID")

    def apply(
        self,
        session: CollaborationSession,
        signal: CoordinationSignal,
    ) -> CollaborationSession:
        if not isinstance(session, CollaborationSession):
            raise InvalidCoordinationContractError(
                "coordination input must be a CollaborationSession",
                "INVALID_COORDINATION_SESSION",
            )
        if not isinstance(signal, CoordinationSignal):
            raise InvalidCoordinationSignalError(
                "coordination input must be a CoordinationSignal",
                "INVALID_COORDINATION_SIGNAL",
            )
        if signal.session_id != session.session_id:
            raise InvalidCoordinationSignalError(
                "signal session_id does not match collaboration session",
                "COORDINATION_SESSION_ID_MISMATCH",
                {"signal_id": signal.signal_id},
            )
        if session.last_signal_id == signal.signal_id:
            if session.accepted_signal_fingerprint == signal.fingerprint:
                return session
            raise ConflictingCoordinationSignalError(
                "signal identifier conflicts with the accepted coordination signal",
                "CONFLICTING_COORDINATION_SIGNAL",
                {"signal_id": signal.signal_id},
            )
        if signal.expected_status is not session.status:
            raise InvalidCoordinationSignalError(
                "signal expected status does not match collaboration session",
                "EXPECTED_COORDINATION_STATUS_MISMATCH",
                {
                    "expected_status": signal.expected_status.value,
                    "current_status": session.status.value,
                },
            )
        if signal.source_revision != session.current_revision:
            raise InvalidCoordinationSignalError(
                "signal source revision does not match collaboration session",
                "STALE_COORDINATION_SIGNAL",
                {
                    "source_revision": str(signal.source_revision),
                    "current_revision": str(session.current_revision),
                },
            )
        required_destination = SIGNAL_DESTINATIONS[signal.signal_type]
        if signal.requested_status is not required_destination:
            raise InvalidCoordinationSignalError(
                "signal type does not match requested collaboration status",
                "COORDINATION_SIGNAL_STATUS_MISMATCH",
                {
                    "signal_type": signal.signal_type.value,
                    "requested_status": signal.requested_status.value,
                },
            )
        if signal.requested_status not in COORDINATION_TRANSITIONS[session.status]:
            raise InvalidCoordinationTransitionError(
                "collaboration status transition is not allowed",
                "INVALID_COORDINATION_TRANSITION",
                {
                    "from_status": session.status.value,
                    "to_status": signal.requested_status.value,
                },
            )

        if signal.requested_status in {CollaborationStatus.READY, CollaborationStatus.FROZEN}:
            blockers = self._readiness_blockers(session)
            if blockers:
                raise CoordinationReadinessError(
                    "coordination session is not ready for the requested transition",
                    "COORDINATION_NOT_READY",
                    {"blocker_codes": ",".join(code for code, _ in blockers)},
                )
        if signal.requested_status is CollaborationStatus.CONTRADICTED and not session.open_contradictions:
            raise CoordinationReadinessError(
                "contradicted status requires an open contradiction record",
                "MISSING_OPEN_CONTRADICTION",
            )
        if signal.requested_status is CollaborationStatus.STALE and not session.open_invalidations:
            raise CoordinationReadinessError(
                "stale status requires an open invalidation event",
                "MISSING_OPEN_INVALIDATION",
            )
        if signal.requested_status is CollaborationStatus.CLOSED and (
            session.open_invalidations or session.open_contradictions or session.status is CollaborationStatus.STALE
        ):
            raise CoordinationReadinessError(
                "stale or blocked collaboration session cannot close successfully",
                "COORDINATION_CLOSEOUT_BLOCKED",
            )

        contract_status = {
            CollaborationStatus.COLLECTING: ContractReadiness.COLLECTING,
            CollaborationStatus.INCOMPLETE: ContractReadiness.INCOMPLETE,
            CollaborationStatus.CONTRADICTED: ContractReadiness.CONTRADICTED,
            CollaborationStatus.READY: ContractReadiness.READY_FOR_FREEZE,
            CollaborationStatus.FROZEN: ContractReadiness.FROZEN,
            CollaborationStatus.STALE: ContractReadiness.STALE,
            CollaborationStatus.SUPERSEDED: ContractReadiness.SUPERSEDED,
            CollaborationStatus.CLOSED: ContractReadiness.CLOSED,
        }[signal.requested_status]

        updated = replace(
            session,
            contract=session.contract.with_status(contract_status),
            status=signal.requested_status,
            last_signal_id=signal.signal_id,
            accepted_signal_fingerprint=signal.fingerprint,
        )
        validation = self.validate(updated)
        if not validation.allowed and updated.status in {
            CollaborationStatus.READY,
            CollaborationStatus.FROZEN,
            CollaborationStatus.CLOSED,
        }:
            raise CoordinationReadinessError(
                "coordination transition produced a blocked state",
                "COORDINATION_NOT_READY",
                {"blocker_codes": ",".join(validation.blocker_codes)},
            )
        return updated


def coordination_transition_event(
    previous: CollaborationSession,
    signal: CoordinationSignal,
    current: CollaborationSession,
) -> RuntimeAuditEvent:
    if (
        previous.session_id != signal.session_id
        or current.session_id != previous.session_id
        or signal.expected_status is not previous.status
        or signal.requested_status is not current.status
        or current.last_signal_id != signal.signal_id
        or current.accepted_signal_fingerprint != signal.fingerprint
    ):
        raise InvalidCoordinationSignalError(
            "coordination transition event requires a matching accepted signal",
            "INVALID_COORDINATION_SIGNAL_IDENTITY",
        )
    event_type = (
        AuditEventType.CONTRACT_FROZEN
        if current.status is CollaborationStatus.FROZEN
        else AuditEventType.CONTRACT_INVALIDATED
        if current.status is CollaborationStatus.STALE
        else AuditEventType.COLLABORATION_SESSION_CLOSED
        if current.status is CollaborationStatus.CLOSED
        else AuditEventType.COLLABORATION_STATUS_TRANSITIONED
    )
    event_id = f"event.{_fingerprint({'type': event_type.value, 'signal': signal.to_dict()})[:24]}"
    return RuntimeAuditEvent(
        event_id,
        event_type,
        current.session_id,
        signal.signal_id,
        signal.reason_code,
        provenance_ids=(signal.source_component,),
        details=(
            ("accepted", "true"),
            ("contract_fingerprint", current.contract.fingerprint),
            ("from_status", previous.status.value),
            ("signal_fingerprint", signal.fingerprint),
            ("to_status", current.status.value),
        ),
    )


def coordination_rejection_event(
    session: CollaborationSession,
    signal: object,
    error: InvalidCoordinationContractError
    | InvalidCoordinationSignalError
    | InvalidCoordinationTransitionError
    | CoordinationReadinessError
    | ConflictingCoordinationSignalError,
) -> RuntimeAuditEvent:
    signal_id = getattr(signal, "signal_id", "invalid-signal")
    signal_fingerprint = getattr(signal, "fingerprint", _fingerprint({"repr": repr(signal)}))
    event_id = f"event.{_fingerprint({'type': AuditEventType.COORDINATION_INPUT_REJECTED.value, 'signal': signal_fingerprint, 'reason': error.reason_code})[:24]}"
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.COORDINATION_INPUT_REJECTED,
        session.session_id,
        str(signal_id),
        error.reason_code,
        provenance_ids=("coordination-controller",),
        details=(
            ("accepted", "false"),
            ("current_status", session.status.value),
            ("signal_fingerprint", signal_fingerprint),
        ),
    )
