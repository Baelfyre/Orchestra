from __future__ import annotations

import json
from pathlib import Path

from .domain.governance.authority import (
    IDENTIFIER_PATTERN,
    AuthorityDecision,
    AuthorityProvenance,
    AuthorityReasonCode,
    AuthorityScope,
    Constraint,
    ConstraintKind,
    ProvenanceSource,
    TargetSelector,
    TargetSelectorType,
    _constraint_map,
    _constraints_permit,
    _identifier,
    _intersect_constraints,
    _text,
)
from .errors import AuthorityDeniedError, InvalidAuthorityConfigurationError
from .interfaces import IAuthorityEvaluator
from .models import AuditEventType, RuntimeAuditEvent


# The pure authority entities and deterministic constraint semantics now live in
# orchestra_runtime.domain.governance.authority. This legacy module intentionally
# retains repository-policy loading, application-port inheritance, and audit-event
# projection until their later infrastructure/application extraction phases.


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
        raise InvalidAuthorityConfigurationError(
            "trusted policy root must be an object",
            AuthorityReasonCode.INVALID_SCOPE,
        )
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
        raise InvalidAuthorityConfigurationError(
            "trusted policy is missing authority_scope",
            AuthorityReasonCode.INVALID_SCOPE,
        )
    try:
        scope = AuthorityScope.from_dict(scope_data)
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, InvalidAuthorityConfigurationError):
            raise
        raise InvalidAuthorityConfigurationError(
            "trusted authority is malformed",
            AuthorityReasonCode.INVALID_SCOPE,
        ) from exc
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
        details=(
            ("allowed", str(decision.allowed).lower()),
            ("operation", decision.operation),
            ("target", decision.target.value),
        ),
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
