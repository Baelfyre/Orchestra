from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re

from .errors import AuthorityDeniedError, InvalidAuthorityConfigurationError
from .interfaces import IAuthorityEvaluator
from .models import AuditEventType, RuntimeAuditEvent


IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")


class ProvenanceSource(str, Enum):
    TRUSTED_COMPOSITION = "TRUSTED_COMPOSITION"
    TRUSTED_REPOSITORY_POLICY = "TRUSTED_REPOSITORY_POLICY"
    ACCEPTED_DELEGATION = "ACCEPTED_DELEGATION"


class TargetSelectorType(str, Enum):
    EXACT = "EXACT"


class ConstraintKind(str, Enum):
    EXACT = "EXACT"
    ALLOWED_SET = "ALLOWED_SET"


class AuthorityReasonCode(str, Enum):
    ALLOWED = "ALLOWED"
    INVALID_SCOPE = "INVALID_SCOPE"
    UNTRUSTED_PROVENANCE = "UNTRUSTED_PROVENANCE"
    TARGET_NOT_ALLOWED = "TARGET_NOT_ALLOWED"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    CONSTRAINT_DENIED = "CONSTRAINT_DENIED"
    EMPTY_INTERSECTION = "EMPTY_INTERSECTION"


def _text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise InvalidAuthorityConfigurationError(
            f"{field_name} must be non-empty",
            AuthorityReasonCode.INVALID_SCOPE,
            {"field": field_name},
        )
    return text


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name).casefold()
    if not IDENTIFIER_PATTERN.fullmatch(text):
        raise InvalidAuthorityConfigurationError(
            f"{field_name} must be a canonical identifier",
            AuthorityReasonCode.INVALID_SCOPE,
            {"field": field_name},
        )
    return text


@dataclass(frozen=True, slots=True)
class AuthorityProvenance:
    source_type: ProvenanceSource
    source_id: str
    policy_version: str
    loaded_by: str
    parent_run_id: str | None = None
    parent_decision_id: str | None = None

    def __post_init__(self) -> None:
        source_type = ProvenanceSource(self.source_type)
        source_id = _identifier(self.source_id, "source_id")
        policy_version = _text(self.policy_version, "policy_version")
        loaded_by = _identifier(self.loaded_by, "loaded_by")
        parent_run_id = self.parent_run_id.strip() if self.parent_run_id else None
        parent_decision_id = self.parent_decision_id.strip() if self.parent_decision_id else None
        if source_type is ProvenanceSource.ACCEPTED_DELEGATION:
            if not parent_run_id or not parent_decision_id:
                raise InvalidAuthorityConfigurationError(
                    "accepted delegation provenance requires parent identifiers",
                    AuthorityReasonCode.UNTRUSTED_PROVENANCE,
                )
        elif parent_run_id or parent_decision_id:
            raise InvalidAuthorityConfigurationError(
                "root provenance cannot contain parent identifiers",
                AuthorityReasonCode.UNTRUSTED_PROVENANCE,
            )
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "loaded_by", loaded_by)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        object.__setattr__(self, "parent_decision_id", parent_decision_id)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AuthorityProvenance:
        return cls(
            source_type=ProvenanceSource(str(data.get("source_type", ""))),
            source_id=str(data.get("source_id", "")),
            policy_version=str(data.get("policy_version", "")),
            loaded_by=str(data.get("loaded_by", "")),
            parent_run_id=str(data["parent_run_id"]) if data.get("parent_run_id") else None,
            parent_decision_id=str(data["parent_decision_id"]) if data.get("parent_decision_id") else None,
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "policy_version": self.policy_version,
            "loaded_by": self.loaded_by,
            "parent_run_id": self.parent_run_id,
            "parent_decision_id": self.parent_decision_id,
        }


@dataclass(frozen=True, slots=True)
class TargetSelector:
    value: str
    selector_type: TargetSelectorType = TargetSelectorType.EXACT

    def __post_init__(self) -> None:
        value = _text(self.value, "target")
        if any(token in value for token in ("*", "?")):
            raise InvalidAuthorityConfigurationError(
                "target selectors must be exact",
                AuthorityReasonCode.INVALID_SCOPE,
                {"target": value},
            )
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "selector_type", TargetSelectorType(self.selector_type))

    def to_dict(self) -> dict[str, str]:
        return {"selector_type": self.selector_type.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class Constraint:
    key: str
    kind: ConstraintKind
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        key = _identifier(self.key, "constraint key")
        kind = ConstraintKind(self.kind)
        values = tuple(sorted({_text(value, "constraint value") for value in self.values}, key=lambda item: (item.casefold(), item)))
        if not values or (kind is ConstraintKind.EXACT and len(values) != 1):
            raise InvalidAuthorityConfigurationError(
                "constraint values do not match constraint kind",
                AuthorityReasonCode.INVALID_SCOPE,
                {"constraint": key},
            )
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "values", values)

    @classmethod
    def exact(cls, key: str, value: str) -> Constraint:
        return cls(key=key, kind=ConstraintKind.EXACT, values=(value,))

    @classmethod
    def allowed_set(cls, key: str, values: tuple[str, ...] | list[str]) -> Constraint:
        return cls(key=key, kind=ConstraintKind.ALLOWED_SET, values=tuple(values))

    def permits(self, requested: Constraint) -> bool:
        if self.key != requested.key:
            return False
        return set(requested.values).issubset(self.values)

    def intersect(self, other: Constraint) -> Constraint | None:
        if self.key != other.key:
            return None
        values = tuple(sorted(set(self.values).intersection(other.values), key=lambda item: (item.casefold(), item)))
        if not values:
            return None
        kind = ConstraintKind.EXACT if len(values) == 1 else ConstraintKind.ALLOWED_SET
        return Constraint(self.key, kind, values)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Constraint:
        values = data.get("values", ())
        if not isinstance(values, (list, tuple)):
            values = ()
        return cls(str(data.get("key", "")), ConstraintKind(str(data.get("kind", ""))), tuple(str(item) for item in values))

    def to_dict(self) -> dict[str, object]:
        return {"key": self.key, "kind": self.kind.value, "values": list(self.values)}


@dataclass(frozen=True, slots=True)
class AuthorityScope:
    scope_id: str
    targets: tuple[TargetSelector, ...]
    operations: tuple[str, ...]
    constraints: tuple[Constraint, ...]
    provenance: AuthorityProvenance
    parent_scope_id: str | None = None

    def __post_init__(self) -> None:
        scope_id = _identifier(self.scope_id, "scope_id")
        targets = tuple(sorted(tuple(self.targets), key=lambda item: (item.value.casefold(), item.value)))
        operations = tuple(sorted((_identifier(item, "operation") for item in self.operations)))
        constraints = tuple(sorted(tuple(self.constraints), key=lambda item: item.key))
        if not targets or not operations:
            raise InvalidAuthorityConfigurationError(
                "authority scope requires targets and operations",
                AuthorityReasonCode.INVALID_SCOPE,
                {"scope_id": scope_id},
            )
        if len({item.value for item in targets}) != len(targets) or len(set(operations)) != len(operations):
            raise InvalidAuthorityConfigurationError("authority scope contains duplicates", AuthorityReasonCode.INVALID_SCOPE)
        if len({item.key for item in constraints}) != len(constraints):
            raise InvalidAuthorityConfigurationError("constraint keys must be unique", AuthorityReasonCode.INVALID_SCOPE)
        parent_scope_id = _identifier(self.parent_scope_id, "parent_scope_id") if self.parent_scope_id else None
        if self.provenance.source_type is ProvenanceSource.ACCEPTED_DELEGATION and not parent_scope_id:
            raise InvalidAuthorityConfigurationError(
                "delegated scope requires parent_scope_id",
                AuthorityReasonCode.UNTRUSTED_PROVENANCE,
            )
        object.__setattr__(self, "scope_id", scope_id)
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "constraints", constraints)
        object.__setattr__(self, "parent_scope_id", parent_scope_id)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AuthorityScope:
        targets = data.get("targets", ())
        operations = data.get("operations", ())
        constraints = data.get("constraints", ())
        provenance = data.get("provenance")
        if not isinstance(targets, list) or not isinstance(operations, list) or not isinstance(constraints, list) or not isinstance(provenance, dict):
            raise InvalidAuthorityConfigurationError("malformed authority scope", AuthorityReasonCode.INVALID_SCOPE)
        return cls(
            scope_id=str(data.get("scope_id", "")),
            targets=tuple(TargetSelector(str(item)) if not isinstance(item, dict) else TargetSelector(str(item.get("value", "")), TargetSelectorType(str(item.get("selector_type", "EXACT")))) for item in targets),
            operations=tuple(str(item) for item in operations),
            constraints=tuple(Constraint.from_dict(item) for item in constraints if isinstance(item, dict)),
            provenance=AuthorityProvenance.from_dict(provenance),
            parent_scope_id=str(data["parent_scope_id"]) if data.get("parent_scope_id") else None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "scope_id": self.scope_id,
            "targets": [item.to_dict() for item in self.targets],
            "operations": list(self.operations),
            "constraints": [item.to_dict() for item in self.constraints],
            "provenance": self.provenance.to_dict(),
            "parent_scope_id": self.parent_scope_id,
        }


@dataclass(frozen=True, slots=True)
class AuthorityDecision:
    decision_id: str
    run_id: str
    scope_id: str
    target: TargetSelector
    operation: str
    requested_constraints: tuple[Constraint, ...]
    allowed: bool
    reason_code: AuthorityReasonCode
    matched_targets: tuple[str, ...] = ()
    matched_operations: tuple[str, ...] = ()
    evaluated_constraints: tuple[str, ...] = ()
    provenance_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "run_id", _text(self.run_id, "run_id"))
        object.__setattr__(self, "scope_id", _identifier(self.scope_id, "scope_id"))
        object.__setattr__(self, "operation", _identifier(self.operation, "operation"))
        constraints = tuple(sorted(tuple(self.requested_constraints), key=lambda item: item.key))
        if len({item.key for item in constraints}) != len(constraints):
            raise InvalidAuthorityConfigurationError("requested constraint keys must be unique", AuthorityReasonCode.INVALID_SCOPE)
        object.__setattr__(self, "requested_constraints", constraints)
        object.__setattr__(self, "reason_code", AuthorityReasonCode(self.reason_code))
        object.__setattr__(self, "matched_targets", tuple(sorted(set(self.matched_targets))))
        object.__setattr__(self, "matched_operations", tuple(sorted(set(self.matched_operations))))
        object.__setattr__(self, "evaluated_constraints", tuple(sorted(set(self.evaluated_constraints))))
        object.__setattr__(self, "provenance_id", _identifier(self.provenance_id, "provenance_id"))

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "run_id": self.run_id,
            "scope_id": self.scope_id,
            "target": self.target.to_dict(),
            "operation": self.operation,
            "requested_constraints": [item.to_dict() for item in self.requested_constraints],
            "allowed": self.allowed,
            "reason_code": self.reason_code.value,
            "matched_targets": list(self.matched_targets),
            "matched_operations": list(self.matched_operations),
            "evaluated_constraints": list(self.evaluated_constraints),
            "provenance_id": self.provenance_id,
        }


def _constraint_map(constraints: tuple[Constraint, ...]) -> dict[str, Constraint]:
    result = {item.key: item for item in constraints}
    if len(result) != len(constraints):
        raise InvalidAuthorityConfigurationError("constraint keys must be unique", AuthorityReasonCode.INVALID_SCOPE)
    return result


def _constraints_permit(granted: tuple[Constraint, ...], requested: tuple[Constraint, ...]) -> bool:
    granted_map = _constraint_map(granted)
    requested_map = _constraint_map(requested)
    if set(granted_map) != set(requested_map):
        return not granted_map and not requested_map
    return all(granted_map[key].permits(requested_map[key]) for key in granted_map)


def _intersect_constraints(
    parent: tuple[Constraint, ...],
    requested: tuple[Constraint, ...],
) -> tuple[Constraint, ...]:
    parent_map = _constraint_map(parent)
    requested_map = _constraint_map(requested)
    result: list[Constraint] = []
    for key in sorted(set(parent_map).union(requested_map)):
        if key in parent_map and key in requested_map:
            intersection = parent_map[key].intersect(requested_map[key])
            if intersection is None:
                raise InvalidAuthorityConfigurationError(
                    "authority constraints do not intersect",
                    AuthorityReasonCode.EMPTY_INTERSECTION,
                    {"constraint": key},
                )
            result.append(intersection)
        else:
            result.append(parent_map.get(key) or requested_map[key])
    return tuple(result)


def _load_trusted_json(repo_root: Path, policy_path: Path) -> dict[str, object]:
    try:
        root = Path(repo_root).resolve(strict=True)
    except OSError as exc:
        raise InvalidAuthorityConfigurationError(
            "trusted repository root is invalid",
            AuthorityReasonCode.INVALID_SCOPE,
        ) from exc
    relative = Path(policy_path)
    if not root.is_dir() or relative.is_absolute() or ".." in relative.parts:
        raise InvalidAuthorityConfigurationError(
            "trusted policy path must remain under repository root",
            AuthorityReasonCode.INVALID_SCOPE,
        )
    try:
        resolved = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise InvalidAuthorityConfigurationError(
            "trusted policy file is missing",
            AuthorityReasonCode.INVALID_SCOPE,
            {"policy_path": relative.as_posix()},
        ) from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise InvalidAuthorityConfigurationError(
            "trusted policy path escapes repository root",
            AuthorityReasonCode.INVALID_SCOPE,
        )
    try:
        text = resolved.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError("empty policy")
        payload = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise InvalidAuthorityConfigurationError(
            "trusted policy must be non-empty UTF-8 JSON",
            AuthorityReasonCode.INVALID_SCOPE,
            {"policy_path": relative.as_posix()},
        ) from exc
    if not isinstance(payload, dict):
        raise InvalidAuthorityConfigurationError("trusted policy root must be an object", AuthorityReasonCode.INVALID_SCOPE)
    return payload


class AuthorityEvaluator(IAuthorityEvaluator):
    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        if scope.parent_scope_id or scope.provenance.source_type not in {
            ProvenanceSource.TRUSTED_COMPOSITION,
            ProvenanceSource.TRUSTED_REPOSITORY_POLICY,
        }:
            raise InvalidAuthorityConfigurationError(
                "root authority requires trusted root provenance",
                AuthorityReasonCode.UNTRUSTED_PROVENANCE,
                {"scope_id": scope.scope_id},
            )
        return scope

    def evaluate(
        self,
        scope: AuthorityScope,
        target: TargetSelector,
        operation: str,
        constraints: tuple[Constraint, ...] = (),
        *,
        run_id: str,
        decision_id: str,
    ) -> AuthorityDecision:
        operation = _identifier(operation, "operation")
        constraints = tuple(sorted(tuple(constraints), key=lambda item: item.key))
        target_match = next((item for item in scope.targets if item == target), None)
        if target_match is None:
            reason = AuthorityReasonCode.TARGET_NOT_ALLOWED
        elif operation not in scope.operations:
            reason = AuthorityReasonCode.OPERATION_NOT_ALLOWED
        elif not _constraints_permit(scope.constraints, constraints):
            reason = AuthorityReasonCode.CONSTRAINT_DENIED
        else:
            reason = AuthorityReasonCode.ALLOWED
        return AuthorityDecision(
            decision_id=decision_id,
            run_id=run_id,
            scope_id=scope.scope_id,
            target=target,
            operation=operation,
            requested_constraints=constraints,
            allowed=reason is AuthorityReasonCode.ALLOWED,
            reason_code=reason,
            matched_targets=(target.value,) if target_match else (),
            matched_operations=(operation,) if operation in scope.operations else (),
            evaluated_constraints=tuple(item.key for item in constraints),
            provenance_id=scope.provenance.source_id,
        )

    @staticmethod
    def enforce(decision: AuthorityDecision) -> AuthorityDecision:
        if not decision.allowed:
            raise AuthorityDeniedError(
                "authority decision denied",
                decision.reason_code,
                {"target": decision.target.value, "operation": decision.operation},
            )
        return decision

    def intersect(
        self,
        parent: AuthorityScope,
        requested: AuthorityScope,
        provenance: AuthorityProvenance,
    ) -> AuthorityScope:
        if provenance.source_type is not ProvenanceSource.ACCEPTED_DELEGATION:
            raise InvalidAuthorityConfigurationError(
                "child scope requires accepted delegation provenance",
                AuthorityReasonCode.UNTRUSTED_PROVENANCE,
            )
        targets = tuple(item for item in requested.targets if item in parent.targets)
        operations = tuple(item for item in requested.operations if item in parent.operations)
        if not targets or not operations:
            raise InvalidAuthorityConfigurationError(
                "authority intersection is empty",
                AuthorityReasonCode.EMPTY_INTERSECTION,
            )
        return AuthorityScope(
            requested.scope_id,
            targets,
            operations,
            _intersect_constraints(parent.constraints, requested.constraints),
            provenance,
            parent.scope_id,
        )


def load_trusted_authority(repo_root: Path, policy_path: Path) -> AuthorityScope:
    payload = _load_trusted_json(repo_root, policy_path)
    scope_data = payload.get("authority_scope")
    if not isinstance(scope_data, dict):
        raise InvalidAuthorityConfigurationError("trusted policy is missing authority_scope", AuthorityReasonCode.INVALID_SCOPE)
    try:
        scope = AuthorityScope.from_dict(scope_data)
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, InvalidAuthorityConfigurationError):
            raise
        raise InvalidAuthorityConfigurationError("trusted authority is malformed", AuthorityReasonCode.INVALID_SCOPE) from exc
    if scope.provenance.source_type is not ProvenanceSource.TRUSTED_REPOSITORY_POLICY:
        raise InvalidAuthorityConfigurationError(
            "file policy requires trusted repository provenance",
            AuthorityReasonCode.UNTRUSTED_PROVENANCE,
        )
    return AuthorityEvaluator().validate_root(scope)


def root_authority_event(event_id: str, run_id: str, scope: AuthorityScope) -> RuntimeAuditEvent:
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.ROOT_AUTHORITY_CREATED,
        run_id,
        scope.scope_id,
        AuthorityReasonCode.ALLOWED.value,
        provenance_ids=(scope.provenance.source_id,),
        details=(("scope_id", scope.scope_id),),
    )


def authority_decision_event(event_id: str, decision: AuthorityDecision) -> RuntimeAuditEvent:
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.AUTHORITY_DECIDED,
        decision.run_id,
        decision.decision_id,
        decision.reason_code.value,
        provenance_ids=(decision.provenance_id,),
        details=(("allowed", str(decision.allowed).lower()), ("operation", decision.operation), ("target", decision.target.value)),
    )


def initialization_failure_event(
    event_id: str,
    run_id: str,
    related_id: str,
    reason_code: str,
) -> RuntimeAuditEvent:
    return RuntimeAuditEvent(
        event_id,
        AuditEventType.INITIALIZATION_FAILED,
        run_id,
        related_id,
        reason_code,
    )
