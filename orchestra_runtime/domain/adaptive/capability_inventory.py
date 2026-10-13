# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from typing import Iterable, TypeVar, cast

from orchestra_runtime.domain.adaptive.capability_coverage import CapabilityClaim
from orchestra_runtime.shared import normalize_timestamp


CAPABILITY_INVENTORY_SCHEMA_VERSION = "orchestra.capability-inventory.v1"
_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_RecordT = TypeVar("_RecordT")


class CapabilityResourceKind(str, Enum):
    REGISTERED_SPECIALIST = "REGISTERED_SPECIALIST"
    EXTERNAL_PLUGIN = "EXTERNAL_PLUGIN"
    HOST_NATIVE_TOOL = "HOST_NATIVE_TOOL"
    PUBLIC_REFERENCE = "PUBLIC_REFERENCE"
    PRIVATE_REFERENCE = "PRIVATE_REFERENCE"
    PROSPECTIVE_CANDIDATE = "PROSPECTIVE_CANDIDATE"


class InventoryObservationStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


class InventoryCompatibilityStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


class OperationPermissionStatus(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


class CapabilitySideEffectKind(str, Enum):
    COMMAND = "COMMAND"
    HOOK = "HOOK"
    NETWORK = "NETWORK"
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    CREDENTIAL_ACCESS = "CREDENTIAL_ACCESS"


class SideEffectObservationStatus(str, Enum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


class InventoryFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class CapabilityDiscoveryTriggerKind(str, Enum):
    USER_REQUEST = "USER_REQUEST"
    CAPABILITY_GAP = "CAPABILITY_GAP"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    TOOL_FAILURE = "TOOL_FAILURE"
    STALE_OBSERVATION = "STALE_OBSERVATION"
    ENVIRONMENT_CHANGE = "ENVIRONMENT_CHANGE"


class CapabilityDiscoveryDisposition(str, Enum):
    NO_DISCOVERY = "NO_DISCOVERY"
    CACHE_REUSE_HINT = "CACHE_REUSE_HINT"
    TARGETED_DISCOVERY = "TARGETED_DISCOVERY"


def _identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip().casefold()
    if not _IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return normalized


def _optional_identifier(value: object, field_name: str) -> str | None:
    return None if value is None else _identifier(value, field_name)


def _text(value: object, field_name: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        raise ValueError(f"{field_name} must be non-empty and at most {max_length} characters")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


_EnumT = TypeVar("_EnumT", bound=Enum)


def _enum_value(value: object, enum_type: type[_EnumT], field_name: str) -> _EnumT:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or {enum_type.__name__}")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is unsupported") from exc


def _unique_identifiers(values: object, field_name: str, *, required: bool = True) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    normalized = tuple(_identifier(value, field_name) for value in values)
    if (required and not normalized) or len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique{'' if required else ' optional'} identifiers")
    return tuple(sorted(normalized))


def _references(values: object, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    normalized = tuple(_text(value, field_name) for value in values)
    if (required and not normalized) or len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique{'' if required else ' optional'} references")
    return tuple(sorted(normalized))


def _timestamp(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    return normalize_timestamp(value, field_name)


def _records(values: object, expected_type: type[_RecordT], field_name: str) -> tuple[_RecordT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must contain {expected_type.__name__} records")
    try:
        materialized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be iterable") from exc
    if any(not isinstance(value, expected_type) for value in materialized):
        raise TypeError(f"{field_name} must contain {expected_type.__name__} records")
    return tuple(cast(_RecordT, value) for value in materialized)


@dataclass(frozen=True, slots=True)
class CapabilityInventoryIdentity:
    """Descriptive identity only; these values do not authenticate a host or principal."""

    resource_id: str
    source_id: str
    host_id: str | None = None
    adapter_id: str | None = None
    publisher_id: str | None = None
    user_scope_id: str | None = None
    workspace_scope_id: str | None = None
    distribution_id: str | None = None
    distribution_version: str | None = None
    permission_scope_id: str | None = None
    source_revision: str | None = None
    distribution_digest: str | None = None
    inventory_scope_revision: str | None = None
    recheck_token: str | None = None
    identity_evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("resource_id", "source_id"):
            object.__setattr__(self, field_name, _identifier(getattr(self, field_name), field_name))
        for field_name in (
            "host_id",
            "adapter_id",
            "publisher_id",
            "user_scope_id",
            "workspace_scope_id",
            "distribution_id",
            "distribution_version",
            "permission_scope_id",
            "source_revision",
            "inventory_scope_revision",
        ):
            object.__setattr__(self, field_name, _optional_identifier(getattr(self, field_name), field_name))
        if self.distribution_digest is not None:
            object.__setattr__(self, "distribution_digest", _text(self.distribution_digest, "distribution_digest"))
        if self.recheck_token is not None:
            object.__setattr__(self, "recheck_token", _text(self.recheck_token, "recheck_token"))
        object.__setattr__(self, "identity_evidence_refs", _references(self.identity_evidence_refs, "identity_evidence_ref"))

    @property
    def observation_scope(self) -> tuple[str, str, str, str, str] | None:
        if (
            self.host_id is None
            or self.user_scope_id is None
            or self.workspace_scope_id is None
            or self.permission_scope_id is None
        ):
            return None
        return (
            self.host_id,
            self.user_scope_id,
            self.workspace_scope_id,
            self.permission_scope_id,
            self.resource_id,
        )


@dataclass(frozen=True, slots=True)
class CapabilityInventoryClaim:
    capability_id: str
    claim: CapabilityClaim | str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", _identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "claim", _enum_value(self.claim, CapabilityClaim, "claim"))
        object.__setattr__(self, "evidence_refs", _references(self.evidence_refs, "evidence_ref", required=True))


@dataclass(frozen=True, slots=True)
class OperationPermissionObservation:
    """A recorded permission observation, not an authorization to perform the operation."""

    operation_id: str
    status: OperationPermissionStatus | str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", _identifier(self.operation_id, "operation_id"))
        object.__setattr__(self, "status", _enum_value(self.status, OperationPermissionStatus, "status"))
        object.__setattr__(self, "evidence_refs", _references(self.evidence_refs, "evidence_ref"))
        if self.status in {OperationPermissionStatus.ALLOWED, OperationPermissionStatus.DENIED} and not self.evidence_refs:
            raise ValueError("known permission observations require evidence_refs")


@dataclass(frozen=True, slots=True)
class SideEffectObservation:
    kind: CapabilitySideEffectKind | str
    status: SideEffectObservationStatus | str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _enum_value(self.kind, CapabilitySideEffectKind, "kind"))
        object.__setattr__(self, "status", _enum_value(self.status, SideEffectObservationStatus, "status"))
        object.__setattr__(self, "evidence_refs", _references(self.evidence_refs, "evidence_ref"))
        if self.status in {SideEffectObservationStatus.DECLARED, SideEffectObservationStatus.OBSERVED} and not self.evidence_refs:
            raise ValueError("known side-effect observations require evidence_refs")


@dataclass(frozen=True, slots=True)
class CapabilityInventoryDescriptor:
    """Versioned host-neutral observation; its type and labels do not establish trust."""

    identity: CapabilityInventoryIdentity
    resource_kind: CapabilityResourceKind | str
    observation: InventoryObservationStatus | str
    compatibility: InventoryCompatibilityStatus | str
    capability_claims: tuple[CapabilityInventoryClaim, ...] = ()
    permissions: tuple[OperationPermissionObservation, ...] = ()
    side_effects: tuple[SideEffectObservation, ...] = ()
    observation_evidence_refs: tuple[str, ...] = ()
    compatibility_evidence_refs: tuple[str, ...] = ()
    independent_output_refs: tuple[str, ...] = ()
    review_refs: tuple[str, ...] = ()
    observed_at: str | None = None
    valid_until: str | None = None
    limitations: tuple[str, ...] = ()
    schema_version: str = CAPABILITY_INVENTORY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CapabilityInventoryIdentity):
            raise TypeError("identity must be CapabilityInventoryIdentity")
        if self.schema_version != CAPABILITY_INVENTORY_SCHEMA_VERSION:
            raise ValueError("schema_version is unsupported")
        object.__setattr__(self, "resource_kind", _enum_value(self.resource_kind, CapabilityResourceKind, "resource_kind"))
        object.__setattr__(self, "observation", _enum_value(self.observation, InventoryObservationStatus, "observation"))
        object.__setattr__(self, "compatibility", _enum_value(self.compatibility, InventoryCompatibilityStatus, "compatibility"))
        claims = _records(self.capability_claims, CapabilityInventoryClaim, "capability_claims")
        permissions = _records(self.permissions, OperationPermissionObservation, "permissions")
        side_effects = _records(self.side_effects, SideEffectObservation, "side_effects")
        if len(set(claims)) != len(claims):
            raise ValueError("capability_claims must not contain duplicates")
        if len(set(permissions)) != len(permissions):
            raise ValueError("permissions must not contain duplicates")
        if len(set(side_effects)) != len(side_effects):
            raise ValueError("side_effects must not contain duplicates")
        object.__setattr__(self, "capability_claims", tuple(sorted(claims, key=lambda item: (item.capability_id, item.claim.value, item.evidence_refs))))
        object.__setattr__(self, "permissions", tuple(sorted(permissions, key=lambda item: (item.operation_id, item.status.value, item.evidence_refs))))
        object.__setattr__(self, "side_effects", tuple(sorted(side_effects, key=lambda item: (item.kind.value, item.status.value, item.evidence_refs))))
        for field_name in (
            "observation_evidence_refs",
            "compatibility_evidence_refs",
            "independent_output_refs",
            "review_refs",
        ):
            object.__setattr__(self, field_name, _references(getattr(self, field_name), "evidence_ref"))
        if self.observation in {InventoryObservationStatus.PRESENT, InventoryObservationStatus.ABSENT} and not self.observation_evidence_refs:
            raise ValueError("known inventory observations require observation_evidence_refs")
        if self.compatibility in {InventoryCompatibilityStatus.COMPATIBLE, InventoryCompatibilityStatus.INCOMPATIBLE} and not self.compatibility_evidence_refs:
            raise ValueError("known compatibility observations require compatibility_evidence_refs")
        object.__setattr__(self, "observed_at", _timestamp(self.observed_at, "observed_at"))
        object.__setattr__(self, "valid_until", _timestamp(self.valid_until, "valid_until"))
        if self.observed_at and self.valid_until:
            observed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
            expires = datetime.fromisoformat(self.valid_until.replace("Z", "+00:00"))
            if expires <= observed:
                raise ValueError("valid_until must be later than observed_at")
        if not isinstance(self.limitations, (tuple, list)):
            raise TypeError("limitations must be a list or tuple")
        normalized_limitations = tuple(_text(value, "limitation") for value in self.limitations)
        if len(normalized_limitations) != len(set(normalized_limitations)):
            raise ValueError("limitations must be unique")
        object.__setattr__(self, "limitations", tuple(sorted(normalized_limitations)))


@dataclass(frozen=True, slots=True)
class CapabilityDiscoveryTrigger:
    kind: CapabilityDiscoveryTriggerKind | str
    capability_ids: tuple[str, ...] = ()
    resource_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _enum_value(self.kind, CapabilityDiscoveryTriggerKind, "kind"))
        object.__setattr__(self, "capability_ids", _unique_identifiers(self.capability_ids, "capability_ids", required=False))
        object.__setattr__(self, "resource_ids", _unique_identifiers(self.resource_ids, "resource_ids", required=False))
        if not self.capability_ids and not self.resource_ids:
            raise ValueError("a discovery trigger must identify relevant capabilities or resources")


@dataclass(frozen=True, slots=True)
class CapabilityDiscoveryPlan:
    evaluated_at: str
    disposition: CapabilityDiscoveryDisposition
    trigger_kind: CapabilityDiscoveryTriggerKind | None
    requested_capability_ids: tuple[str, ...]
    requested_resource_ids: tuple[str, ...]
    target_capability_ids: tuple[str, ...]
    target_resource_ids: tuple[str, ...]
    reuse_hint_identities: tuple[CapabilityInventoryIdentity, ...]
    revalidate_identities: tuple[CapabilityInventoryIdentity, ...]
    relevant_observations: tuple[CapabilityInventoryDescriptor, ...]


def _freshness(entry: CapabilityInventoryDescriptor, evaluated_at: datetime) -> InventoryFreshness:
    if entry.observed_at is None or entry.valid_until is None:
        return InventoryFreshness.UNKNOWN
    observed = datetime.fromisoformat(entry.observed_at.replace("Z", "+00:00"))
    expires = datetime.fromisoformat(entry.valid_until.replace("Z", "+00:00"))
    if observed > evaluated_at:
        return InventoryFreshness.UNKNOWN
    if expires <= evaluated_at:
        return InventoryFreshness.STALE
    return InventoryFreshness.CURRENT


def _identity_sort_key(identity: CapabilityInventoryIdentity) -> tuple[str, ...]:
    return tuple(
        value or ""
        for value in (
            identity.host_id,
            identity.user_scope_id,
            identity.workspace_scope_id,
            identity.resource_id,
            identity.source_id,
            identity.adapter_id,
            identity.publisher_id,
            identity.distribution_id,
            identity.distribution_version,
            identity.permission_scope_id,
            identity.source_revision,
            identity.distribution_digest,
            identity.inventory_scope_revision,
            identity.recheck_token,
        )
    )


def plan_capability_discovery(
    trigger: CapabilityDiscoveryTrigger | None,
    cached_observations: Iterable[CapabilityInventoryDescriptor] = (),
    current_identities: Iterable[CapabilityInventoryIdentity] = (),
    *,
    evaluated_at: str,
) -> CapabilityDiscoveryPlan:
    """Plan a narrow lookup from explicit triggers and supplied local observations.

    This function performs no host discovery, I/O, routing, permission grant,
    specialist selection, plugin activation, or execution. Reuse is only a hint;
    it never authenticates an observation or proves current permission.
    """
    if trigger is not None and not isinstance(trigger, CapabilityDiscoveryTrigger):
        raise TypeError("trigger must be CapabilityDiscoveryTrigger or None")
    observations = _records(cached_observations, CapabilityInventoryDescriptor, "cached_observations")
    identities = _records(current_identities, CapabilityInventoryIdentity, "current_identities")
    if len({entry.identity for entry in observations}) != len(observations):
        raise ValueError("cached_observations must have unique identities")
    current_by_scope: dict[tuple[str, str, str, str, str], CapabilityInventoryIdentity] = {}
    for identity in identities:
        scope = identity.observation_scope
        if scope is not None:
            if scope in current_by_scope:
                raise ValueError("current_identities must have unique observation scopes")
            current_by_scope[scope] = identity

    normalized_at = normalize_timestamp(evaluated_at, "evaluated_at")
    evaluation_time = datetime.fromisoformat(normalized_at.replace("Z", "+00:00"))
    if trigger is None:
        return CapabilityDiscoveryPlan(
            normalized_at,
            CapabilityDiscoveryDisposition.NO_DISCOVERY,
            None,
            (),
            (),
            (),
            (),
            (),
            (),
            (),
        )

    active_user_workspaces = {
        (identity.user_scope_id, identity.workspace_scope_id)
        for identity in identities
        if identity.observation_scope is not None
    }
    if len(active_user_workspaces) > 1:
        raise ValueError("current_identities must share one active user/workspace scope")

    requested_capabilities = trigger.capability_ids
    requested_resources = trigger.resource_ids
    relevant = tuple(
        sorted(
            (
                entry
                for entry in observations
                if entry.identity.observation_scope in current_by_scope
                and (
                    entry.identity.resource_id in requested_resources
                    or any(claim.capability_id in requested_capabilities for claim in entry.capability_claims)
                )
            ),
            key=lambda entry: _identity_sort_key(entry.identity),
        )
    )
    force_refresh = trigger.kind in {
        CapabilityDiscoveryTriggerKind.QUALITY_ISSUE,
        CapabilityDiscoveryTriggerKind.TOOL_FAILURE,
        CapabilityDiscoveryTriggerKind.STALE_OBSERVATION,
        CapabilityDiscoveryTriggerKind.ENVIRONMENT_CHANGE,
    }
    reuse_hints: set[CapabilityInventoryIdentity] = set()
    revalidate: set[CapabilityInventoryIdentity] = set()
    reusable_capabilities: set[str] = set()
    for entry in relevant:
        scope = entry.identity.observation_scope
        current = current_by_scope.get(scope) if scope is not None else None
        reusable = (
            not force_refresh
            and current == entry.identity
            and _freshness(entry, evaluation_time) is InventoryFreshness.CURRENT
            and entry.observation is InventoryObservationStatus.PRESENT
            and entry.compatibility is InventoryCompatibilityStatus.COMPATIBLE
            and bool(entry.review_refs)
        )
        if reusable:
            reuse_hints.add(entry.identity)
            claims_by_capability: dict[str, set[CapabilityClaim]] = {}
            for claim in entry.capability_claims:
                if claim.capability_id in requested_capabilities:
                    claims_by_capability.setdefault(claim.capability_id, set()).add(claim.claim)
            for capability_id, claims in claims_by_capability.items():
                if (
                    CapabilityClaim.SUPPORTS in claims
                    or CapabilityClaim.DOES_NOT_SUPPORT in claims
                ) and not {
                    CapabilityClaim.SUPPORTS,
                    CapabilityClaim.DOES_NOT_SUPPORT,
                } <= claims:
                    reusable_capabilities.add(capability_id)
        else:
            revalidate.add(entry.identity)

    target_resources = {identity.resource_id for identity in revalidate}
    target_resources.update(set(requested_resources) - {entry.identity.resource_id for entry in relevant})
    if force_refresh:
        target_resources.update(requested_resources)
    target_capabilities = (
        set(requested_capabilities)
        if force_refresh
        else set(requested_capabilities) - reusable_capabilities
    )
    if not target_resources and not target_capabilities and reuse_hints:
        disposition = CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    else:
        disposition = CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    return CapabilityDiscoveryPlan(
        normalized_at,
        disposition,
        trigger.kind,
        requested_capabilities,
        requested_resources,
        tuple(sorted(target_capabilities)),
        tuple(sorted(target_resources)),
        tuple(sorted(reuse_hints, key=_identity_sort_key)),
        tuple(sorted(revalidate, key=_identity_sort_key)),
        relevant,
    )


__all__ = [
    "CAPABILITY_INVENTORY_SCHEMA_VERSION",
    "CapabilitySideEffectKind",
    "CapabilityDiscoveryDisposition",
    "CapabilityDiscoveryPlan",
    "CapabilityDiscoveryTrigger",
    "CapabilityDiscoveryTriggerKind",
    "CapabilityInventoryClaim",
    "CapabilityInventoryDescriptor",
    "CapabilityInventoryIdentity",
    "CapabilityResourceKind",
    "InventoryCompatibilityStatus",
    "InventoryFreshness",
    "InventoryObservationStatus",
    "OperationPermissionObservation",
    "OperationPermissionStatus",
    "SideEffectObservation",
    "SideEffectObservationStatus",
    "plan_capability_discovery",
]
