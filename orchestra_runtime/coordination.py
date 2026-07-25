from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
from types import MappingProxyType
from urllib.parse import urlsplit, urlunsplit

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
GIT_OBJECT_ID_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_REPOSITORY_DIGEST_PATTERN = re.compile(
    r"^(?:file-sha256|local-remote-sha256|local-repository-sha256):[0-9a-f]{64}$"
)
WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:(?:[/\\]|$)")
EXTERNAL_AUTHORITY_PREFIXES = ("human:", "governance:", "external:")
KNOWN_AUTHORITY_REFERENCES = frozenset(
    {"conductor", "arbiter", "overseer", "the-steward", "the-governor"}
)


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCoordinationContractError(
            "coordination identity must be canonical JSON",
            "INVALID_COORDINATION_CANONICAL_JSON",
        ) from exc


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


def _git_object_id(value: object, field_name: str = "baseline_sha") -> str:
    text = _text(value, field_name).casefold()
    if not GIT_OBJECT_ID_PATTERN.fullmatch(text):
        raise InvalidCoordinationContractError(
            f"{field_name} must be a canonical 40- or 64-character Git object ID",
            "INVALID_BASELINE_SHA",
            {"field": field_name},
        )
    return text


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name).casefold()
    if not SHA256_PATTERN.fullmatch(text):
        raise InvalidCoordinationContractError(
            f"{field_name} must be a SHA-256 digest",
            "INVALID_COORDINATION_SHA256",
            {"field": field_name},
        )
    return text


def _unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise InvalidCoordinationContractError(
            f"{field_name} values must be unique",
            "DUPLICATE_COORDINATION_VALUE",
            {"field": field_name},
        )
    return values


def _sorted_identifiers(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_identifier(item, field_name) for item in values)
    return tuple(sorted(_unique(normalized, field_name)))


def _ordered_identifiers(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_identifier(item, field_name) for item in values)
    return _unique(normalized, field_name)


def _sorted_text(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_text(item, field_name) for item in values)
    return tuple(sorted(_unique(normalized, field_name)))


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
    return _unique(normalized, field_name)


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


def _non_negative_sequence(value: object, field_name: str = "sequence") -> int:
    if type(value) is not int or value < 0:
        raise InvalidCoordinationContractError(
            f"{field_name} must be a non-negative integer",
            "INVALID_COORDINATION_SEQUENCE",
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
        or WINDOWS_DRIVE_PATTERN.match(text)
        or ":" in text.split("/", 1)[0]
    ):
        raise InvalidCoordinationContractError(
            "artifact path must be repository-relative",
            "UNSAFE_COORDINATION_PATH",
            {"path": text},
        )
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidCoordinationContractError(
            "artifact path must not contain traversal or empty segments",
            "UNSAFE_COORDINATION_PATH",
            {"path": text},
        )
    return PurePosixPath(*parts).as_posix()


def _repository_identity(value: object) -> str:
    raw = _text(value, "repository_identity")
    lowered = raw.casefold()
    if CANONICAL_REPOSITORY_DIGEST_PATTERN.fullmatch(lowered):
        return lowered

    if "://" in raw:
        parsed = urlsplit(raw)
        scheme = parsed.scheme.casefold()
        if scheme == "file":
            return f"file-sha256:{sha256(raw.encode('utf-8')).hexdigest()}"
        if not parsed.hostname:
            raise InvalidCoordinationContractError(
                "repository URL must include a hostname",
                "INVALID_REPOSITORY_IDENTITY",
            )
        try:
            port = parsed.port
        except ValueError as exc:
            raise InvalidCoordinationContractError(
                "repository URL contains an invalid port",
                "INVALID_REPOSITORY_IDENTITY",
            ) from exc
        host = parsed.hostname.casefold()
        if port is not None:
            host = f"{host}:{port}"
        return urlunsplit((scheme, host, parsed.path, "", ""))

    if WINDOWS_DRIVE_PATTERN.match(raw) or raw.startswith(("/", "\\", ".")):
        return f"local-repository-sha256:{sha256(raw.encode('utf-8')).hexdigest()}"

    scp_like = re.fullmatch(r"(?:(?:[^@/\s]+)@)?([^:/\s]+):(.+)", raw)
    if scp_like:
        host, path = scp_like.groups()
        return f"ssh://{host.casefold()}/{path.lstrip('/')}"

    return f"local-repository-sha256:{sha256(raw.encode('utf-8')).hexdigest()}"


def _authority_reference(value: object, field_name: str) -> str:
    reference = _identifier(value, field_name)
    if reference == "the-tuner":
        raise InvalidCoordinationContractError(
            "The Tuner cannot hold operational or resolution authority",
            "TUNER_AUTHORITY_EXPANSION",
            {"field": field_name},
        )
    return reference


def _is_external_authority(reference: str) -> bool:
    return reference.startswith(EXTERNAL_AUTHORITY_PREFIXES)


class ActivationDecision(str, Enum):
    BYPASS_SINGLE_OWNER = "BYPASS_SINGLE_OWNER"
    ACTIVATE_MULTI_DOMAIN = "ACTIVATE_MULTI_DOMAIN"
    ACTIVATE_LATE_BOUNDARY_CROSSING = "ACTIVATE_LATE_BOUNDARY_CROSSING"
    ACTIVATE_CONTRADICTION = "ACTIVATE_CONTRADICTION"
    ACTIVATE_MISSING_OWNER = "ACTIVATE_MISSING_OWNER"
    ACTIVATE_STALE_CONTRACT = "ACTIVATE_STALE_CONTRACT"


class ExecutionMode(str, Enum):
    IDEATION = "IDEATION"
    PROTOTYPE = "PROTOTYPE"
    IMPLEMENTATION = "IMPLEMENTATION"
    AUDIT = "AUDIT"
    RELEASE = "RELEASE"


class ProgressionMode(str, Enum):
    MANUAL = "MANUAL"
    DELEGATED = "DELEGATED"


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


class ArtifactRetentionRequirement(str, Enum):
    NONE_REQUIRED = "NONE_REQUIRED"
    RETAIN_REQUIRED = "RETAIN_REQUIRED"
    CLEANUP_ALLOWED = "CLEANUP_ALLOWED"
    CLEANUP_REQUIRED = "CLEANUP_REQUIRED"


class EvidenceStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


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
        raw_roles = tuple(SpecialistParticipationRole(item) for item in self.participation_roles)
        if len(set(raw_roles)) != len(raw_roles):
            raise InvalidCoordinationContractError(
                "participant roles must be unique",
                "DUPLICATE_PARTICIPATION_ROLE",
                {"specialist_slug": specialist_slug},
            )
        roles = tuple(sorted(raw_roles, key=lambda item: item.value))
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
class InvalidationRule:
    target_kind: InvalidationTargetKind
    target_refs: tuple[str, ...]
    affected_specialist_refs: tuple[str, ...]
    required_reentry_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        target_kind = InvalidationTargetKind(self.target_kind)
        target_refs = _sorted_identifiers(self.target_refs, "target_ref")
        affected = _sorted_identifiers(self.affected_specialist_refs, "affected_specialist_ref")
        reentry = _sorted_identifiers(self.required_reentry_refs, "required_reentry_ref")
        if not target_refs or not affected or not reentry:
            raise InvalidCoordinationContractError(
                "invalidation rule requires targets, affected specialists, and re-entry owners",
                "INCOMPLETE_INVALIDATION_RULE",
            )
        if not set(reentry).issubset(set(affected)):
            raise InvalidCoordinationContractError(
                "invalidation rule re-entry owners must be affected specialists",
                "INVALID_REENTRY_SET",
            )
        object.__setattr__(self, "target_kind", target_kind)
        object.__setattr__(self, "target_refs", target_refs)
        object.__setattr__(self, "affected_specialist_refs", affected)
        object.__setattr__(self, "required_reentry_refs", reentry)

    def to_dict(self) -> dict[str, object]:
        return {
            "target_kind": self.target_kind.value,
            "target_refs": list(self.target_refs),
            "affected_specialist_refs": list(self.affected_specialist_refs),
            "required_reentry_refs": list(self.required_reentry_refs),
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
    invalidation_rules: tuple[InvalidationRule, ...] = ()

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
        rules = tuple(sorted(tuple(self.invalidation_rules), key=lambda item: item.target_kind.value))
        rule_kinds = tuple(item.target_kind for item in rules)
        if len(set(rule_kinds)) != len(rule_kinds):
            raise InvalidCoordinationContractError(
                "dependency may define only one invalidation rule per target kind",
                "DUPLICATE_INVALIDATION_RULE",
                {"dependency_id": dependency_id},
            )
        allowed = {source, target}
        for rule in rules:
            if not set(rule.affected_specialist_refs).issubset(allowed):
                raise InvalidCoordinationContractError(
                    "invalidation rule may affect only specialists declared by the dependency edge",
                    "INVALID_INVALIDATION_SPECIALIST_SET",
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
        object.__setattr__(self, "invalidation_rules", rules)

    def invalidation_rule_for(self, target_kind: InvalidationTargetKind) -> InvalidationRule | None:
        return next((item for item in self.invalidation_rules if item.target_kind is target_kind), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency_id": self.dependency_id,
            "source_specialist": self.source_specialist,
            "target_specialist": self.target_specialist,
            "dependency_kind": self.dependency_kind.value,
            "contract_section_refs": list(self.contract_section_refs),
            "invalidation_triggers": list(self.invalidation_triggers),
            "blocking": self.blocking,
            "invalidation_rules": [item.to_dict() for item in self.invalidation_rules],
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
    change_identity_ref: str = ""
    declared_reference_refs: tuple[str, ...] = ()
    canonicalization_version: str = COORDINATION_CANONICALIZATION_VERSION
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        contract_id = _identifier(self.contract_id, "contract_id")
        session_id = _identifier(self.session_id, "session_id")
        revision = _positive_revision(self.revision)
        objective = _text(self.objective, "objective")
        acceptance_criteria = _ordered_identifiers(self.acceptance_criteria, "acceptance_criterion")
        baseline_sha = _git_object_id(self.baseline_sha)
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
        change_identity_ref = _identifier(self.change_identity_ref, "change_identity_ref")
        declared_reference_refs = _sorted_identifiers(
            self.declared_reference_refs,
            "declared_reference_ref",
        )
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
        object.__setattr__(self, "change_identity_ref", change_identity_ref)
        object.__setattr__(self, "declared_reference_refs", declared_reference_refs)
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
            "change_identity_ref": self.change_identity_ref,
            "declared_reference_refs": list(self.declared_reference_refs),
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
    retention_requirement: ArtifactRetentionRequirement
    cleanup_authority_ref: str
    contract_revision: int
    change_identity_ref: str
    evidence_ref: str | None = None
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        artifact_id = _identifier(self.artifact_id, "artifact_id")
        session_id = _identifier(self.session_id, "session_id")
        path = _relative_path(self.path)
        producer = _identifier(self.producer_ref, "producer_ref")
        source = _identifier(self.source_ref, "source_ref")
        before = ArtifactLifecycleState(self.pre_execution_state)
        current = ArtifactLifecycleState(self.current_state)
        retention = ArtifactRetentionRequirement(self.retention_requirement)
        cleanup_authority = _authority_reference(self.cleanup_authority_ref, "cleanup_authority_ref")
        revision = _positive_revision(self.contract_revision)
        change_identity = _identifier(self.change_identity_ref, "change_identity_ref")
        evidence = _optional_identifier(self.evidence_ref, "evidence_ref")

        if before not in {ArtifactLifecycleState.ABSENT, ArtifactLifecycleState.PREEXISTING}:
            raise InvalidCoordinationContractError(
                "pre_execution_state must be ABSENT or PREEXISTING",
                "INVALID_ARTIFACT_PRE_EXECUTION_STATE",
                {"artifact_id": artifact_id},
            )
        if before is ArtifactLifecycleState.PREEXISTING and current is ArtifactLifecycleState.GENERATED:
            raise InvalidCoordinationContractError(
                "preexisting artifact cannot become GENERATED",
                "INVALID_ARTIFACT_STATE_TRANSITION",
                {"artifact_id": artifact_id},
            )
        if retention is ArtifactRetentionRequirement.NONE_REQUIRED and current not in {
            ArtifactLifecycleState.ABSENT,
            ArtifactLifecycleState.RETAIN,
        }:
            raise InvalidCoordinationContractError(
                "NONE_REQUIRED artifact must remain absent or use the explicit retain sentinel",
                "INVALID_ARTIFACT_RETENTION_STATE",
                {"artifact_id": artifact_id},
            )
        if retention is ArtifactRetentionRequirement.RETAIN_REQUIRED and current in {
            ArtifactLifecycleState.CLEANUP_PENDING,
            ArtifactLifecycleState.CLEANED,
        }:
            raise InvalidCoordinationContractError(
                "retention-required artifact cannot be pending cleanup or cleaned",
                "INVALID_ARTIFACT_RETENTION_STATE",
                {"artifact_id": artifact_id},
            )
        if current in {ArtifactLifecycleState.CLEANUP_PENDING, ArtifactLifecycleState.CLEANED} and retention not in {
            ArtifactRetentionRequirement.CLEANUP_ALLOWED,
            ArtifactRetentionRequirement.CLEANUP_REQUIRED,
        }:
            raise InvalidCoordinationContractError(
                "cleanup states require explicit cleanup authority in the retention requirement",
                "INVALID_ARTIFACT_RETENTION_STATE",
                {"artifact_id": artifact_id},
            )
        if current is ArtifactLifecycleState.RETAIN and retention is ArtifactRetentionRequirement.CLEANUP_REQUIRED:
            raise InvalidCoordinationContractError(
                "cleanup-required artifact cannot remain retained",
                "INVALID_ARTIFACT_RETENTION_STATE",
                {"artifact_id": artifact_id},
            )
        if retention is ArtifactRetentionRequirement.NONE_REQUIRED and evidence is not None:
            raise InvalidCoordinationContractError(
                "none-required artifact must use the explicit no-evidence representation",
                "UNEXPECTED_ARTIFACT_EVIDENCE",
                {"artifact_id": artifact_id},
            )
        if retention is not ArtifactRetentionRequirement.NONE_REQUIRED and evidence is None:
            raise InvalidCoordinationContractError(
                "retained or cleanup-managed artifact requires evidence",
                "MISSING_ARTIFACT_EVIDENCE",
                {"artifact_id": artifact_id},
            )

        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "producer_ref", producer)
        object.__setattr__(self, "source_ref", source)
        object.__setattr__(self, "pre_execution_state", before)
        object.__setattr__(self, "current_state", current)
        object.__setattr__(self, "retention_requirement", retention)
        object.__setattr__(self, "cleanup_authority_ref", cleanup_authority)
        object.__setattr__(self, "contract_revision", revision)
        object.__setattr__(self, "change_identity_ref", change_identity)
        object.__setattr__(self, "evidence_ref", evidence)
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
            "retention_requirement": self.retention_requirement.value,
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
        owner = _authority_reference(self.required_resolution_owner_ref, "required_resolution_owner_ref")
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
class CoordinationEvidenceRecord:
    evidence_id: str
    session_id: str
    owner_ref: str
    contract_fingerprint: str
    contract_revision: int
    baseline_sha: str
    change_identity_ref: str
    status: EvidenceStatus = EvidenceStatus.CURRENT
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        evidence_id = _identifier(self.evidence_id, "evidence_id")
        session_id = _identifier(self.session_id, "session_id")
        owner = _identifier(self.owner_ref, "owner_ref")
        if owner != "overseer":
            raise InvalidCoordinationContractError(
                "coordination evidence must be owned by Overseer",
                "INVALID_EVIDENCE_OWNER",
                {"evidence_id": evidence_id},
            )
        contract_fingerprint = _sha256(self.contract_fingerprint, "contract_fingerprint")
        revision = _positive_revision(self.contract_revision, "contract_revision")
        baseline_sha = _git_object_id(self.baseline_sha)
        change_identity_ref = _identifier(self.change_identity_ref, "change_identity_ref")
        status = EvidenceStatus(self.status)
        object.__setattr__(self, "evidence_id", evidence_id)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "owner_ref", owner)
        object.__setattr__(self, "contract_fingerprint", contract_fingerprint)
        object.__setattr__(self, "contract_revision", revision)
        object.__setattr__(self, "baseline_sha", baseline_sha)
        object.__setattr__(self, "change_identity_ref", change_identity_ref)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "fingerprint", _fingerprint(self._identity_payload()))

    def _identity_payload(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "session_id": self.session_id,
            "owner_ref": self.owner_ref,
            "contract_fingerprint": self.contract_fingerprint,
            "contract_revision": self.contract_revision,
            "baseline_sha": self.baseline_sha,
            "change_identity_ref": self.change_identity_ref,
            "status": self.status.value,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "fingerprint": self.fingerprint}


_ACCEPTED_SIGNAL_CONSTRUCTION_TOKEN = object()


def _contract_status_for(status: CollaborationStatus) -> ContractReadiness:
    return {
        CollaborationStatus.COLLECTING: ContractReadiness.COLLECTING,
        CollaborationStatus.INCOMPLETE: ContractReadiness.INCOMPLETE,
        CollaborationStatus.CONTRADICTED: ContractReadiness.CONTRADICTED,
        CollaborationStatus.READY: ContractReadiness.READY_FOR_FREEZE,
        CollaborationStatus.FROZEN: ContractReadiness.FROZEN,
        CollaborationStatus.STALE: ContractReadiness.STALE,
        CollaborationStatus.SUPERSEDED: ContractReadiness.SUPERSEDED,
        CollaborationStatus.CLOSED: ContractReadiness.CLOSED,
    }[CollaborationStatus(status)]


def _contract_fingerprint_family(contract: CrossLayerContractPacket) -> frozenset[str]:
    return frozenset(contract.with_status(status).fingerprint for status in ContractReadiness)


def _evidence_blockers_for_records(
    evidence_by_id: dict[str, CoordinationEvidenceRecord],
    evidence_refs: tuple[str, ...],
    contract: CrossLayerContractPacket,
    current_revision: int,
    baseline_sha: str,
    change_identity_ref: str,
) -> tuple[tuple[str, str], ...]:
    blockers: list[tuple[str, str]] = []
    if not evidence_refs:
        return (("MISSING_COORDINATION_EVIDENCE", "transition requires current Overseer evidence"),)
    for evidence_ref in evidence_refs:
        evidence = evidence_by_id.get(evidence_ref)
        if evidence is None:
            blockers.append(("UNKNOWN_COORDINATION_EVIDENCE", f"unknown evidence reference: {evidence_ref}"))
            continue
        if evidence.status is not EvidenceStatus.CURRENT:
            blockers.append(("STALE_COORDINATION_EVIDENCE", f"evidence is not current: {evidence_ref}"))
        if evidence.owner_ref != "overseer":
            blockers.append(("INVALID_EVIDENCE_OWNER", f"evidence is not owned by Overseer: {evidence_ref}"))
        if evidence.contract_fingerprint != contract.fingerprint:
            blockers.append(("EVIDENCE_CONTRACT_MISMATCH", f"evidence targets another contract: {evidence_ref}"))
        if evidence.contract_revision != current_revision:
            blockers.append(("STALE_COORDINATION_EVIDENCE", f"evidence targets another revision: {evidence_ref}"))
        if evidence.baseline_sha != baseline_sha:
            blockers.append(("EVIDENCE_BASELINE_MISMATCH", f"evidence targets another baseline: {evidence_ref}"))
        if evidence.change_identity_ref != change_identity_ref:
            blockers.append(
                ("EVIDENCE_CHANGE_IDENTITY_MISMATCH", f"evidence targets another change identity: {evidence_ref}")
            )
    return tuple(sorted(set(blockers)))


@dataclass(frozen=True, slots=True, init=False)
class AcceptedCoordinationSignal:
    signal_id: str
    signal_fingerprint: str
    sequence: int
    signal_type: CoordinationSignalType
    expected_status: CollaborationStatus
    requested_status: CollaborationStatus
    reason_code: str
    source_component: str
    source_revision: int
    evidence_refs: tuple[str, ...]
    prior_contract_fingerprint: str
    resulting_status: CollaborationStatus
    resulting_contract_status: ContractReadiness
    resulting_contract_fingerprint: str
    _trusted_provenance: bool = field(init=False, repr=False, compare=False)

    def __init__(
        self,
        signal_id: str,
        signal_fingerprint: str,
        sequence: int,
        signal_type: CoordinationSignalType,
        expected_status: CollaborationStatus,
        requested_status: CollaborationStatus,
        reason_code: str,
        source_component: str,
        source_revision: int,
        evidence_refs: tuple[str, ...],
        prior_contract_fingerprint: str,
        resulting_status: CollaborationStatus,
        resulting_contract_status: ContractReadiness,
        resulting_contract_fingerprint: str,
        *,
        _construction_token: object | None = None,
    ) -> None:
        if _construction_token is not _ACCEPTED_SIGNAL_CONSTRUCTION_TOKEN:
            raise InvalidCoordinationContractError(
                "accepted coordination signals may be minted only by CoordinationController",
                "UNTRUSTED_ACCEPTED_SIGNAL_PROVENANCE",
            )
        object.__setattr__(self, "signal_id", _identifier(signal_id, "signal_id"))
        object.__setattr__(self, "signal_fingerprint", _sha256(signal_fingerprint, "signal_fingerprint"))
        object.__setattr__(self, "sequence", _non_negative_sequence(sequence))
        object.__setattr__(self, "signal_type", CoordinationSignalType(signal_type))
        object.__setattr__(self, "expected_status", CollaborationStatus(expected_status))
        object.__setattr__(self, "requested_status", CollaborationStatus(requested_status))
        object.__setattr__(self, "reason_code", _identifier(reason_code, "reason_code").upper())
        object.__setattr__(self, "source_component", _identifier(source_component, "source_component"))
        object.__setattr__(self, "source_revision", _positive_revision(source_revision, "source_revision"))
        object.__setattr__(self, "evidence_refs", _sorted_identifiers(evidence_refs, "evidence_ref"))
        object.__setattr__(
            self,
            "prior_contract_fingerprint",
            _sha256(prior_contract_fingerprint, "prior_contract_fingerprint"),
        )
        object.__setattr__(self, "resulting_status", CollaborationStatus(resulting_status))
        object.__setattr__(self, "resulting_contract_status", ContractReadiness(resulting_contract_status))
        object.__setattr__(
            self,
            "resulting_contract_fingerprint",
            _sha256(resulting_contract_fingerprint, "resulting_contract_fingerprint"),
        )
        object.__setattr__(self, "_trusted_provenance", True)

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "signal_fingerprint": self.signal_fingerprint,
            "sequence": self.sequence,
            "signal_type": self.signal_type.value,
            "expected_status": self.expected_status.value,
            "requested_status": self.requested_status.value,
            "reason_code": self.reason_code,
            "source_component": self.source_component,
            "source_revision": self.source_revision,
            "evidence_refs": list(self.evidence_refs),
            "prior_contract_fingerprint": self.prior_contract_fingerprint,
            "resulting_status": self.resulting_status.value,
            "resulting_contract_status": self.resulting_contract_status.value,
            "resulting_contract_fingerprint": self.resulting_contract_fingerprint,
        }


def _accepted_coordination_signal(
    signal: CoordinationSignal,
    sequence: int,
    prior_contract: CrossLayerContractPacket,
    resulting_contract: CrossLayerContractPacket,
) -> AcceptedCoordinationSignal:
    return AcceptedCoordinationSignal(
        signal.signal_id,
        signal.fingerprint,
        sequence,
        signal.signal_type,
        signal.expected_status,
        signal.requested_status,
        signal.reason_code,
        signal.source_component,
        signal.source_revision,
        signal.evidence_refs,
        prior_contract.fingerprint,
        signal.requested_status,
        resulting_contract.status,
        resulting_contract.fingerprint,
        _construction_token=_ACCEPTED_SIGNAL_CONSTRUCTION_TOKEN,
    )


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
    execution_mode: ExecutionMode
    progression_mode: ProgressionMode
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
    manual_authorization_reference: str | None = None
    delegated_envelope_id: str | None = None
    evidence_records: tuple[CoordinationEvidenceRecord, ...] = ()
    accepted_signals: tuple[AcceptedCoordinationSignal, ...] = ()
    last_signal_id: str | None = None
    accepted_signal_fingerprint: str | None = None
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        session_id = _identifier(self.session_id, "session_id")
        task_id = _identifier(self.task_id, "task_id")
        repository_identity = _repository_identity(self.repository_identity)
        branch = _text(self.branch, "branch")
        baseline_sha = _git_object_id(self.baseline_sha)
        execution_mode = ExecutionMode(self.execution_mode)
        progression_mode = ProgressionMode(self.progression_mode)
        manual_reference = _optional_identifier(
            self.manual_authorization_reference,
            "manual_authorization_reference",
        )
        delegated_envelope = _optional_identifier(self.delegated_envelope_id, "delegated_envelope_id")
        if progression_mode is ProgressionMode.MANUAL:
            if manual_reference is None or delegated_envelope is not None:
                raise InvalidCoordinationContractError(
                    "manual progression requires only manual_authorization_reference",
                    "INVALID_COORDINATION_AUTHORITY_BINDING",
                    {"session_id": session_id},
                )
        elif delegated_envelope is None or manual_reference is not None:
            raise InvalidCoordinationContractError(
                "delegated progression requires only delegated_envelope_id",
                "INVALID_COORDINATION_AUTHORITY_BINDING",
                {"session_id": session_id},
            )

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
        evidence_records = tuple(sorted(tuple(self.evidence_records), key=lambda item: item.evidence_id))
        accepted_signals = tuple(sorted(tuple(self.accepted_signals), key=lambda item: item.sequence))

        for collection, label, id_field in (
            (handoffs, "handoff", "delta_id"),
            (invalidations, "invalidation", "event_id"),
            (artifacts, "artifact", "artifact_id"),
            (contradictions, "contradiction", "contradiction_id"),
            (evidence_records, "evidence", "evidence_id"),
        ):
            identifiers = tuple(getattr(item, id_field) for item in collection)
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

        signal_ids = tuple(item.signal_id for item in accepted_signals)
        signal_sequences = tuple(item.sequence for item in accepted_signals)
        if len(set(signal_ids)) != len(signal_ids) or signal_sequences != tuple(range(len(accepted_signals))):
            raise InvalidCoordinationContractError(
                "accepted signals require unique IDs and contiguous monotonic sequence",
                "INVALID_ACCEPTED_SIGNAL_LEDGER",
                {"session_id": session_id},
            )
        if any(not getattr(item, "_trusted_provenance", False) for item in accepted_signals):
            raise InvalidCoordinationContractError(
                "accepted signal ledger contains untrusted provenance",
                "UNTRUSTED_ACCEPTED_SIGNAL_PROVENANCE",
                {"session_id": session_id},
            )

        participant_ids = {item.specialist_slug for item in self.graph.participants}
        dependency_by_id = {item.dependency_id: item for item in self.graph.dependencies}
        dependency_ids = set(dependency_by_id)
        section_ids = {item.section_id for item in self.contract.section_records}
        artifact_ids = {item.artifact_id for item in artifacts}
        evidence_ids = {item.evidence_id for item in evidence_records}
        acceptance_ids = set(self.contract.acceptance_criteria)

        section_owners = set()
        required_reviewers = set()
        for section in self.contract.section_records:
            accountable_owner = self.graph.accountable_owner_for(section.layer)
            if section.owner_specialist not in participant_ids:
                raise InvalidCoordinationContractError(
                    "contract section owner must be a graph participant",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"section_id": section.section_id},
                )
            if section.owner_specialist == "the-tuner" or section.owner_specialist != accountable_owner:
                raise InvalidCoordinationContractError(
                    "contract section owner must equal the graph accountable owner",
                    "CONTRACT_SECTION_OWNER_MISMATCH",
                    {"section_id": section.section_id},
                )
            if section.revision != current_revision:
                raise InvalidCoordinationContractError(
                    "contract section revision must equal the current packet revision",
                    "STALE_CONTRACT_SECTION_REVISION",
                    {"section_id": section.section_id},
                )
            if not set(section.dependency_refs).issubset(dependency_ids):
                raise InvalidCoordinationContractError(
                    "contract section references an unknown dependency",
                    "UNKNOWN_COORDINATION_DEPENDENCY",
                    {"section_id": section.section_id},
                )
            if not set(section.acceptance_criteria_refs).issubset(acceptance_ids):
                raise InvalidCoordinationContractError(
                    "contract section references an unknown acceptance criterion",
                    "UNKNOWN_ACCEPTANCE_CRITERION",
                    {"section_id": section.section_id},
                )
            if not set(section.required_reviewer_refs).issubset(participant_ids):
                raise InvalidCoordinationContractError(
                    "contract section reviewer must be a graph participant",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"section_id": section.section_id},
                )
            section_owners.add(section.owner_specialist)
            required_reviewers.update(section.required_reviewer_refs)

        if set(self.contract.owner_refs) != section_owners:
            raise InvalidCoordinationContractError(
                "contract owner references must exactly match section ownership",
                "CONTRACT_OWNER_REFERENCE_MISMATCH",
                {"session_id": session_id},
            )
        if not required_reviewers.issubset(set(self.contract.reviewer_refs)):
            raise InvalidCoordinationContractError(
                "contract reviewer references do not cover section reviewers",
                "CONTRACT_REVIEWER_REFERENCE_MISMATCH",
                {"session_id": session_id},
            )
        if not set(self.contract.reviewer_refs).issubset(participant_ids):
            raise InvalidCoordinationContractError(
                "contract reviewer must be a graph participant",
                "UNKNOWN_COORDINATION_PARTICIPANT",
                {"session_id": session_id},
            )

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

        declared_refs = set(self.contract.declared_reference_refs)
        for event in invalidations:
            dependency = dependency_by_id.get(event.trigger_ref)
            if dependency is None:
                raise InvalidCoordinationContractError(
                    "invalidation trigger must reference a declared dependency",
                    "UNDECLARED_INVALIDATION_DEPENDENCY",
                    {"event_id": event.event_id},
                )
            rule = dependency.invalidation_rule_for(event.target_kind)
            if rule is None:
                raise InvalidCoordinationContractError(
                    "dependency does not declare this invalidation target kind",
                    "UNDECLARED_INVALIDATION_RULE",
                    {"event_id": event.event_id},
                )
            if (
                not set(event.target_refs).issubset(set(rule.target_refs))
                or event.affected_specialist_refs != rule.affected_specialist_refs
                or event.required_reentry_refs != rule.required_reentry_refs
            ):
                raise InvalidCoordinationContractError(
                    "invalidation event exceeds the dependency's declared propagation rule",
                    "INVALID_INVALIDATION_PROPAGATION",
                    {"event_id": event.event_id},
                )
            valid_targets = {
                InvalidationTargetKind.CONTRACT_SECTION: section_ids,
                InvalidationTargetKind.ARTIFACT: artifact_ids,
                InvalidationTargetKind.EVIDENCE: evidence_ids,
            }.get(event.target_kind, declared_refs)
            if not set(event.target_refs).issubset(valid_targets):
                raise InvalidCoordinationContractError(
                    "invalidation event references an undeclared target",
                    "UNKNOWN_INVALIDATION_TARGET",
                    {"event_id": event.event_id},
                )
            if event.status is InvalidationStatus.OPEN and event.source_revision != current_revision:
                raise InvalidCoordinationContractError(
                    "open invalidation must originate from the current session revision",
                    "INVALID_INVALIDATION_REVISION",
                    {"event_id": event.event_id},
                )
            if event.status is InvalidationStatus.RESOLVED:
                if event.source_revision >= current_revision or event.resolved_by_revision != current_revision:
                    raise InvalidCoordinationContractError(
                        "resolved invalidation must originate from an older revision and resolve at the current revision",
                        "INVALID_INVALIDATION_REVISION",
                        {"event_id": event.event_id},
                    )
                for evidence_ref in event.evidence_refresh_refs:
                    evidence = next((item for item in evidence_records if item.evidence_id == evidence_ref), None)
                    if evidence is None:
                        raise InvalidCoordinationContractError(
                            "resolved invalidation references unknown refreshed evidence",
                            "UNKNOWN_COORDINATION_EVIDENCE",
                            {"event_id": event.event_id, "evidence_id": evidence_ref},
                        )
                    if (
                        evidence.status is not EvidenceStatus.CURRENT
                        or evidence.contract_revision != current_revision
                        or evidence.baseline_sha != baseline_sha
                        or evidence.change_identity_ref != self.contract.change_identity_ref
                        or evidence.contract_fingerprint not in _contract_fingerprint_family(self.contract)
                    ):
                        raise InvalidCoordinationContractError(
                            "resolved invalidation requires current evidence bound to the refreshed contract",
                            "INVALID_INVALIDATION_REFRESH_EVIDENCE",
                            {"event_id": event.event_id, "evidence_id": evidence_ref},
                        )
            if event.status is InvalidationStatus.SUPERSEDED and event.source_revision >= current_revision:
                raise InvalidCoordinationContractError(
                    "superseded invalidation must originate from an older revision",
                    "INVALID_INVALIDATION_REVISION",
                    {"event_id": event.event_id},
                )

        for artifact in artifacts:
            if artifact.producer_ref not in participant_ids:
                raise InvalidCoordinationContractError(
                    "artifact producer must be a graph participant",
                    "UNKNOWN_COORDINATION_PARTICIPANT",
                    {"artifact_id": artifact.artifact_id},
                )
            allowed_cleanup = {"conductor", self.graph.continuity_owner}
            if artifact.cleanup_authority_ref not in allowed_cleanup and not _is_external_authority(
                artifact.cleanup_authority_ref
            ):
                raise InvalidCoordinationContractError(
                    "artifact cleanup authority must be Conductor, continuity owner, or explicit external authority",
                    "INVALID_CLEANUP_AUTHORITY",
                    {"artifact_id": artifact.artifact_id},
                )
            if artifact.contract_revision != current_revision:
                raise InvalidCoordinationContractError(
                    "artifact lifecycle record is bound to a stale contract revision",
                    "STALE_ARTIFACT_REVISION",
                    {"artifact_id": artifact.artifact_id},
                )
            if artifact.change_identity_ref != self.contract.change_identity_ref:
                raise InvalidCoordinationContractError(
                    "artifact lifecycle record must bind to the current change identity",
                    "ARTIFACT_CHANGE_IDENTITY_MISMATCH",
                    {"artifact_id": artifact.artifact_id},
                )
            if artifact.source_ref not in section_ids and artifact.source_ref not in declared_refs:
                raise InvalidCoordinationContractError(
                    "artifact lifecycle source must resolve to a current contract section or declared reference",
                    "UNKNOWN_ARTIFACT_SOURCE",
                    {"artifact_id": artifact.artifact_id},
                )
            if artifact.evidence_ref is not None:
                evidence = next((item for item in evidence_records if item.evidence_id == artifact.evidence_ref), None)
                if evidence is None:
                    raise InvalidCoordinationContractError(
                        "artifact lifecycle record references unknown evidence",
                        "UNKNOWN_ARTIFACT_EVIDENCE",
                        {"artifact_id": artifact.artifact_id},
                    )
                if (
                    evidence.owner_ref != "overseer"
                    or evidence.status is not EvidenceStatus.CURRENT
                    or evidence.contract_revision != current_revision
                    or evidence.baseline_sha != baseline_sha
                    or evidence.change_identity_ref != self.contract.change_identity_ref
                    or evidence.contract_fingerprint not in _contract_fingerprint_family(self.contract)
                ):
                    raise InvalidCoordinationContractError(
                        "artifact evidence must be current and bound to the active contract identity",
                        "INVALID_ARTIFACT_EVIDENCE",
                        {"artifact_id": artifact.artifact_id, "evidence_id": artifact.evidence_ref},
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
            owner = contradiction.required_resolution_owner_ref
            if owner not in participant_ids and owner not in KNOWN_AUTHORITY_REFERENCES and not _is_external_authority(owner):
                raise InvalidCoordinationContractError(
                    "contradiction resolution owner is not an approved authority reference",
                    "INVALID_CONTRADICTION_AUTHORITY",
                    {"contradiction_id": contradiction.contradiction_id},
                )
            if owner == "the-tuner":
                raise InvalidCoordinationContractError(
                    "The Tuner cannot resolve contradictions",
                    "TUNER_AUTHORITY_EXPANSION",
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

        for evidence in evidence_records:
            if evidence.baseline_sha != baseline_sha:
                raise InvalidCoordinationContractError(
                    "evidence baseline does not match the collaboration session",
                    "EVIDENCE_BASELINE_MISMATCH",
                    {"evidence_id": evidence.evidence_id},
                )
            if evidence.contract_revision != current_revision:
                raise InvalidCoordinationContractError(
                    "evidence revision does not match the collaboration session",
                    "STALE_COORDINATION_EVIDENCE",
                    {"evidence_id": evidence.evidence_id},
                )
            if evidence.change_identity_ref != self.contract.change_identity_ref:
                raise InvalidCoordinationContractError(
                    "evidence change identity does not match the contract",
                    "EVIDENCE_CHANGE_IDENTITY_MISMATCH",
                    {"evidence_id": evidence.evidence_id},
                )

        status = CollaborationStatus(self.status)
        last_signal_id = _optional_identifier(self.last_signal_id, "last_signal_id")
        accepted_fingerprint = _optional_text(
            self.accepted_signal_fingerprint,
            "accepted_signal_fingerprint",
        )
        if accepted_fingerprint is not None:
            accepted_fingerprint = _sha256(accepted_fingerprint, "accepted_signal_fingerprint")
        if not accepted_signals:
            if (
                last_signal_id is not None
                or accepted_fingerprint is not None
                or status is not CollaborationStatus.COLLECTING
                or self.contract.status is not ContractReadiness.COLLECTING
            ):
                raise InvalidCoordinationContractError(
                    "non-initial collaboration state requires accepted transition provenance",
                    "MISSING_COORDINATION_TRANSITION_PROVENANCE",
                    {"session_id": session_id},
                )
        else:
            evidence_by_id = {item.evidence_id: item for item in evidence_records}
            replay_status = CollaborationStatus.COLLECTING
            replay_contract = self.contract.with_status(ContractReadiness.COLLECTING)
            for receipt in accepted_signals:
                if receipt.expected_status is not replay_status:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger does not preserve the prior collaboration status",
                        "INVALID_ACCEPTED_SIGNAL_LEDGER",
                        {"signal_id": receipt.signal_id},
                    )
                if receipt.source_component not in SIGNAL_SOURCE_POLICY[receipt.signal_type]:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger contains an unauthorized source",
                        "UNAUTHORIZED_COORDINATION_SIGNAL_SOURCE",
                        {"signal_id": receipt.signal_id},
                    )
                if receipt.source_revision != current_revision:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger contains a stale source revision",
                        "STALE_COORDINATION_SIGNAL",
                        {"signal_id": receipt.signal_id},
                    )
                if receipt.requested_status is not SIGNAL_DESTINATIONS[receipt.signal_type]:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger contains a signal/status mismatch",
                        "COORDINATION_SIGNAL_STATUS_MISMATCH",
                        {"signal_id": receipt.signal_id},
                    )
                if receipt.requested_status not in COORDINATION_TRANSITIONS[replay_status]:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger contains an illegal transition",
                        "INVALID_COORDINATION_TRANSITION",
                        {"signal_id": receipt.signal_id},
                    )
                target_contract_status = _contract_status_for(receipt.requested_status)
                target_contract = self.contract.with_status(target_contract_status)
                if (
                    receipt.prior_contract_fingerprint != replay_contract.fingerprint
                    or receipt.resulting_status is not receipt.requested_status
                    or receipt.resulting_contract_status is not target_contract_status
                    or receipt.resulting_contract_fingerprint != target_contract.fingerprint
                ):
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger does not preserve the contract transition chain",
                        "INVALID_ACCEPTED_SIGNAL_LEDGER",
                        {"signal_id": receipt.signal_id},
                    )
                reconstructed = CoordinationSignal(
                    receipt.signal_id,
                    session_id,
                    receipt.signal_type,
                    receipt.expected_status,
                    receipt.requested_status,
                    receipt.reason_code,
                    receipt.source_component,
                    receipt.source_revision,
                    receipt.evidence_refs,
                )
                if reconstructed.fingerprint != receipt.signal_fingerprint:
                    raise InvalidCoordinationContractError(
                        "accepted signal ledger fingerprint does not match transition identity",
                        "INVALID_ACCEPTED_SIGNAL_LEDGER",
                        {"signal_id": receipt.signal_id},
                    )
                if receipt.signal_type in EVIDENCE_REQUIRED_SIGNALS:
                    blockers = _evidence_blockers_for_records(
                        evidence_by_id,
                        receipt.evidence_refs,
                        target_contract,
                        current_revision,
                        baseline_sha,
                        self.contract.change_identity_ref,
                    )
                    if blockers:
                        raise InvalidCoordinationContractError(
                            "accepted signal ledger lacks current transition evidence",
                            "COORDINATION_EVIDENCE_REQUIRED",
                            {"signal_id": receipt.signal_id, "blocker_codes": ",".join(code for code, _ in blockers)},
                        )
                replay_status = receipt.requested_status
                replay_contract = target_contract

            last_receipt = accepted_signals[-1]
            if last_signal_id is None:
                last_signal_id = last_receipt.signal_id
            if accepted_fingerprint is None:
                accepted_fingerprint = last_receipt.signal_fingerprint
            if (
                last_signal_id != last_receipt.signal_id
                or accepted_fingerprint != last_receipt.signal_fingerprint
                or status is not replay_status
                or self.contract.status is not replay_contract.status
                or self.contract.fingerprint != replay_contract.fingerprint
            ):
                raise InvalidCoordinationContractError(
                    "accepted signal ledger does not match the current collaboration state",
                    "INVALID_ACCEPTED_SIGNAL_LEDGER",
                    {"session_id": session_id},
                )

        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "repository_identity", repository_identity)
        object.__setattr__(self, "branch", branch)
        object.__setattr__(self, "baseline_sha", baseline_sha)
        object.__setattr__(self, "execution_mode", execution_mode)
        object.__setattr__(self, "progression_mode", progression_mode)
        object.__setattr__(self, "manual_authorization_reference", manual_reference)
        object.__setattr__(self, "delegated_envelope_id", delegated_envelope)
        object.__setattr__(self, "activation_decision", activation_decision)
        object.__setattr__(self, "activation_reason", activation_reason)
        object.__setattr__(self, "handoff_deltas", handoffs)
        object.__setattr__(self, "invalidation_events", invalidations)
        object.__setattr__(self, "artifact_lifecycle_records", artifacts)
        object.__setattr__(self, "contradictions", contradictions)
        object.__setattr__(self, "evidence_records", evidence_records)
        object.__setattr__(self, "accepted_signals", accepted_signals)
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

    def evidence_by_id(self) -> dict[str, CoordinationEvidenceRecord]:
        return {item.evidence_id: item for item in self.evidence_records}

    def accepted_signal_by_id(self) -> dict[str, AcceptedCoordinationSignal]:
        return {item.signal_id: item for item in self.accepted_signals}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "repository_identity": self.repository_identity,
            "branch": self.branch,
            "baseline_sha": self.baseline_sha,
            "execution_mode": self.execution_mode.value,
            "progression_mode": self.progression_mode.value,
            "manual_authorization_reference": self.manual_authorization_reference,
            "delegated_envelope_id": self.delegated_envelope_id,
            "activation_decision": self.activation_decision.value,
            "activation_reason": self.activation_reason,
            "graph": self.graph.to_dict(),
            "contract": self.contract.to_dict(),
            "handoff_deltas": [item.to_dict() for item in self.handoff_deltas],
            "invalidation_events": [item.to_dict() for item in self.invalidation_events],
            "artifact_lifecycle_records": [item.to_dict() for item in self.artifact_lifecycle_records],
            "contradictions": [item.to_dict() for item in self.contradictions],
            "evidence_records": [item.to_dict() for item in self.evidence_records],
            "accepted_signals": [item.to_dict() for item in self.accepted_signals],
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

SIGNAL_SOURCE_POLICY = MappingProxyType(
    {
        CoordinationSignalType.MARK_INCOMPLETE: frozenset({"conductor", "arbiter", "overseer", "the-tuner"}),
        CoordinationSignalType.MARK_CONTRADICTED: frozenset({"conductor", "arbiter", "the-tuner"}),
        CoordinationSignalType.MARK_READY: frozenset({"arbiter"}),
        CoordinationSignalType.FREEZE: frozenset({"arbiter"}),
        CoordinationSignalType.INVALIDATE: frozenset({"conductor", "arbiter", "overseer", "the-tuner"}),
        CoordinationSignalType.REOPEN_COLLECTION: frozenset({"conductor", "arbiter"}),
        CoordinationSignalType.SUPERSEDE: frozenset({"arbiter"}),
        CoordinationSignalType.CLOSE: frozenset({"arbiter"}),
    }
)

EVIDENCE_REQUIRED_SIGNALS = frozenset(
    {
        CoordinationSignalType.MARK_READY,
        CoordinationSignalType.FREEZE,
        CoordinationSignalType.CLOSE,
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
    def _readiness_blockers(
        self,
        session: CollaborationSession,
        contract: CrossLayerContractPacket | None = None,
    ) -> tuple[tuple[str, str], ...]:
        contract = contract or session.contract
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

        section_layers = {item.layer for item in contract.section_records}
        missing_sections = tuple(sorted(set(contract.affected_layers) - section_layers))
        if missing_sections:
            blockers.append(
                (
                    "MISSING_CONTRACT_SECTION",
                    f"affected layers lack contract sections: {', '.join(missing_sections)}",
                )
            )

        if not contract.acceptance_criteria:
            blockers.append(("MISSING_ACCEPTANCE_CRITERIA", "contract requires acceptance criteria"))
        if not contract.prohibited_scope:
            blockers.append(("MISSING_PROHIBITED_SCOPE", "contract requires explicit prohibited scope"))
        if not contract.validation_requirements:
            blockers.append(
                (
                    "MISSING_VALIDATION_REQUIREMENTS",
                    "contract requires explicit validation requirements",
                )
            )
        if not contract.artifact_lifecycle_refs:
            blockers.append(
                (
                    "MISSING_ARTIFACT_LIFECYCLE",
                    "contract requires an explicit artifact lifecycle record or none-required record",
                )
            )
        if contract.open_decisions:
            blockers.append(("OPEN_CONTRACT_DECISIONS", "contract still contains open decisions"))
        if session.open_invalidations:
            blockers.append(("OPEN_INVALIDATION", "open invalidation events require specialist re-entry"))
        if session.open_contradictions:
            blockers.append(("OPEN_CONTRADICTION", "open contradictions require external resolution"))

        return tuple(sorted(blockers))

    def _evidence_blockers(
        self,
        session: CollaborationSession,
        contract: CrossLayerContractPacket,
        evidence_refs: tuple[str, ...],
    ) -> tuple[tuple[str, str], ...]:
        return _evidence_blockers_for_records(
            session.evidence_by_id(),
            evidence_refs,
            contract,
            session.current_revision,
            session.baseline_sha,
            contract.change_identity_ref,
        )

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
        if readiness_required:
            matching_evidence = tuple(
                item.evidence_id
                for item in session.evidence_records
                if item.contract_fingerprint == session.contract.fingerprint
            )
            blockers += self._evidence_blockers(session, session.contract, matching_evidence)
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

        prior_receipt = session.accepted_signal_by_id().get(signal.signal_id)
        if prior_receipt is not None:
            if prior_receipt.signal_fingerprint == signal.fingerprint:
                return session
            raise ConflictingCoordinationSignalError(
                "signal identifier conflicts with a previously accepted coordination signal",
                "CONFLICTING_COORDINATION_SIGNAL",
                {"signal_id": signal.signal_id},
            )

        if signal.source_component not in SIGNAL_SOURCE_POLICY[signal.signal_type]:
            raise InvalidCoordinationSignalError(
                "source component is not authorized for this coordination signal",
                "UNAUTHORIZED_COORDINATION_SIGNAL_SOURCE",
                {"signal_type": signal.signal_type.value, "source_component": signal.source_component},
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

        contract_status = _contract_status_for(signal.requested_status)
        target_contract = session.contract.with_status(contract_status)
        if signal.signal_type in EVIDENCE_REQUIRED_SIGNALS:
            evidence_blockers = self._evidence_blockers(session, target_contract, signal.evidence_refs)
            if evidence_blockers:
                raise CoordinationReadinessError(
                    "coordination transition lacks current Overseer evidence",
                    "COORDINATION_EVIDENCE_REQUIRED",
                    {"blocker_codes": ",".join(code for code, _ in evidence_blockers)},
                )

        receipt = _accepted_coordination_signal(
            signal,
            len(session.accepted_signals),
            session.contract,
            target_contract,
        )
        updated = replace(
            session,
            contract=target_contract,
            status=signal.requested_status,
            accepted_signals=session.accepted_signals + (receipt,),
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
    receipt = current.accepted_signal_by_id().get(signal.signal_id)
    if (
        previous.session_id != signal.session_id
        or current.session_id != previous.session_id
        or signal.expected_status is not previous.status
        or signal.source_revision != previous.current_revision
        or signal.requested_status is not current.status
        or receipt is None
        or receipt.signal_fingerprint != signal.fingerprint
        or receipt.resulting_contract_fingerprint != current.contract.fingerprint
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


def _stable_rejected_signal_identity(signal: object) -> str:
    to_dict = getattr(signal, "to_dict", None)
    if callable(to_dict):
        try:
            return _fingerprint({"type": type(signal).__qualname__, "payload": to_dict()})
        except Exception:
            pass
    return _fingerprint(
        {
            "module": type(signal).__module__,
            "type": type(signal).__qualname__,
        }
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
    signal_fingerprint = getattr(signal, "fingerprint", None) or _stable_rejected_signal_identity(signal)
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
