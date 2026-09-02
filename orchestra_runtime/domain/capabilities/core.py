from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from ..governance.authority import AuthorityProvenance, Constraint
from ...shared.errors import InvalidCapabilityConfigurationError


IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")


class CapabilityReasonCode(str, Enum):
    ALLOWED = "ALLOWED"
    INVALID_MANIFEST = "INVALID_MANIFEST"
    COLLISION = "COLLISION"
    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    CONSTRAINT_DENIED = "CONSTRAINT_DENIED"
    EMPTY_INTERSECTION = "EMPTY_INTERSECTION"


def _text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise InvalidCapabilityConfigurationError(
            f"{field_name} must be non-empty",
            CapabilityReasonCode.INVALID_MANIFEST,
            {"field": field_name},
        )
    return text


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name).casefold()
    if not IDENTIFIER_PATTERN.fullmatch(text):
        raise InvalidCapabilityConfigurationError(
            f"{field_name} must be a canonical identifier",
            CapabilityReasonCode.INVALID_MANIFEST,
            {"field": field_name},
        )
    return text


@dataclass(frozen=True, slots=True)
class RuntimeCapability:
    capability_id: str
    owner: str
    operations: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        capability_id = _identifier(self.capability_id, "capability_id")
        owner = _identifier(self.owner, "owner")
        operations = tuple(sorted(_identifier(item, "operation") for item in self.operations))
        if not operations or len(set(operations)) != len(operations):
            raise InvalidCapabilityConfigurationError(
                "capability operations must be non-empty and unique",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"capability_id": capability_id},
            )
        object.__setattr__(self, "capability_id", capability_id)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "description", _text(self.description, "description"))

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> RuntimeCapability:
        operations = data.get("operations", ())
        if not isinstance(operations, (list, tuple)):
            operations = ()
        return cls(
            capability_id=str(data.get("capability_id", "")),
            owner=str(data.get("owner", "")),
            operations=tuple(str(item) for item in operations),
            description=str(data.get("description", "")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "owner": self.owner,
            "operations": list(self.operations),
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityGrant:
    capability: RuntimeCapability
    allowed_operations: tuple[str, ...]
    provenance: AuthorityProvenance
    constraints: tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        operations = tuple(sorted(_identifier(item, "allowed operation") for item in self.allowed_operations))
        constraints = tuple(sorted(tuple(self.constraints), key=lambda item: item.key))
        if not operations or len(set(operations)) != len(operations):
            raise InvalidCapabilityConfigurationError(
                "grant operations must be non-empty and unique",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"capability_id": self.capability.capability_id},
            )
        if not set(operations).issubset(self.capability.operations):
            raise InvalidCapabilityConfigurationError(
                "grant operations must be a subset of capability operations",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"capability_id": self.capability.capability_id},
            )
        if len({item.key for item in constraints}) != len(constraints):
            raise InvalidCapabilityConfigurationError(
                "grant constraint keys must be unique",
                CapabilityReasonCode.INVALID_MANIFEST,
                {"capability_id": self.capability.capability_id},
            )
        object.__setattr__(self, "allowed_operations", operations)
        object.__setattr__(self, "constraints", constraints)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> RuntimeCapabilityGrant:
        capability = data.get("capability")
        provenance = data.get("provenance")
        operations = data.get("allowed_operations", ())
        constraints = data.get("constraints", ())
        if not isinstance(capability, dict) or not isinstance(provenance, dict):
            raise InvalidCapabilityConfigurationError("malformed capability grant", CapabilityReasonCode.INVALID_MANIFEST)
        return cls(
            capability=RuntimeCapability.from_dict(capability),
            allowed_operations=tuple(str(item) for item in operations) if isinstance(operations, (list, tuple)) else (),
            provenance=AuthorityProvenance.from_dict(provenance),
            constraints=(
                tuple(Constraint.from_dict(item) for item in constraints if isinstance(item, dict))
                if isinstance(constraints, list)
                else ()
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "capability": self.capability.to_dict(),
            "allowed_operations": list(self.allowed_operations),
            "provenance": self.provenance.to_dict(),
            "constraints": [item.to_dict() for item in self.constraints],
        }


@dataclass(frozen=True, slots=True)
class CapabilityDecision:
    decision_id: str
    run_id: str
    manifest_id: str
    capability_id: str
    operation: str
    requested_constraints: tuple[Constraint, ...]
    allowed: bool
    reason_code: CapabilityReasonCode
    evaluated_grant_id: str | None = None
    evaluated_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "run_id", _text(self.run_id, "run_id"))
        object.__setattr__(self, "manifest_id", _identifier(self.manifest_id, "manifest_id"))
        object.__setattr__(self, "capability_id", _identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "operation", _identifier(self.operation, "operation"))
        constraints = tuple(sorted(tuple(self.requested_constraints), key=lambda item: item.key))
        if len({item.key for item in constraints}) != len(constraints):
            raise InvalidCapabilityConfigurationError(
                "requested constraint keys must be unique",
                CapabilityReasonCode.INVALID_MANIFEST,
            )
        object.__setattr__(self, "requested_constraints", constraints)
        object.__setattr__(self, "reason_code", CapabilityReasonCode(self.reason_code))
        object.__setattr__(self, "evaluated_grant_id", self.evaluated_grant_id.strip() if self.evaluated_grant_id else None)
        object.__setattr__(self, "evaluated_constraints", tuple(sorted(set(self.evaluated_constraints))))

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "capability_id": self.capability_id,
            "operation": self.operation,
            "requested_constraints": [item.to_dict() for item in self.requested_constraints],
            "allowed": self.allowed,
            "reason_code": self.reason_code.value,
            "evaluated_grant_id": self.evaluated_grant_id,
            "evaluated_constraints": list(self.evaluated_constraints),
        }
