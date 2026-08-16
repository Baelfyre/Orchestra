from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .correlation import validate_correlation_id
from .machine_contracts import valid_specialist_ids

if TYPE_CHECKING:
    from .lifecycle import StructuredTerminalResult


APPROVED_UNIT_PLAN_SCHEMA_VERSION = "1.0.0"

# Backward-compatible runtime surface derived from the canonical machine registry.
# This name is intentionally retained during CANONICAL_PROMOTION_AUTHORITY; it is
# no longer an independently maintained specialist identity authority.
VALID_SPECIALISTS = valid_specialist_ids()


def _validate_repository_relative_path(p: str, field_name: str) -> str:
    path_str = str(p or "").strip()
    if not path_str:
        raise ValueError(f"{field_name} entry must be a non-empty string")

    if path_str.startswith("file://"):
        raise ValueError(f"file-URI path rejected in {field_name}: '{path_str}'")

    if path_str.startswith("/") or path_str.startswith("\\") or (len(path_str) > 1 and path_str[1] == ":"):
        raise ValueError(f"absolute path rejected in {field_name}: '{path_str}'")

    normalized = path_str.replace("\\", "/")
    parts = normalized.split("/")
    if ".." in parts or "." in parts:
        raise ValueError(f"path traversal rejected in {field_name}: '{path_str}'")

    if normalized.startswith(".agents/") or "/.agents/" in normalized:
        raise ValueError(f"persistent .agents/ path mutation rejected in {field_name}: '{path_str}'")

    return normalized


@dataclass(frozen=True, slots=True)
class ApprovedUnitPlan:
    """Canonical ApprovedUnitPlan dataclass matching exact 15-field JSON schema in ORCHESTRA_UNIT_RECORD_EXTENSION.md.

    Universally Required (11):
    - schema_version
    - unit_id
    - unit_revision
    - unit_name
    - phase_id
    - execution_envelope_ref
    - scope_ref
    - responsible_specialist
    - objective
    - expected_outputs
    - validation_requirements

    Conditionally Required (1):
    - allowed_paths (Required for FILE_MUTATION work; optional for non-file work)

    Optional (3):
    - prohibited_paths
    - dependency_unit_ids
    - governance_decision_ref
    """

    unit_id: str
    unit_revision: str | int
    unit_name: str
    phase_id: str
    execution_envelope_ref: str
    scope_ref: str
    responsible_specialist: str
    objective: str
    expected_outputs: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    schema_version: str = APPROVED_UNIT_PLAN_SCHEMA_VERSION
    allowed_paths: tuple[str, ...] | None = None
    prohibited_paths: tuple[str, ...] | None = None
    dependency_unit_ids: tuple[str, ...] | None = None
    governance_decision_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != APPROVED_UNIT_PLAN_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version '{self.schema_version}', expected '{APPROVED_UNIT_PLAN_SCHEMA_VERSION}'"
            )

        uid = str(self.unit_id or "").strip()
        if not uid:
            raise ValueError("unit_id must be a non-empty string")
        object.__setattr__(self, "unit_id", uid)

        if isinstance(self.unit_revision, int):
            if isinstance(self.unit_revision, bool) or self.unit_revision < 0:
                raise ValueError("unit_revision integer must be non-negative")
            rev_str = f"rev-{self.unit_revision}"
        else:
            rev_str = str(self.unit_revision or "").strip()
            if not rev_str:
                raise ValueError("unit_revision must be a non-empty string or non-negative integer")
        object.__setattr__(self, "unit_revision", rev_str)

        uname = str(self.unit_name or "").strip()
        if not uname:
            raise ValueError("unit_name must be a non-empty string")
        object.__setattr__(self, "unit_name", uname)

        pid = str(self.phase_id or "").strip()
        if not pid:
            raise ValueError("phase_id must be a non-empty string")
        object.__setattr__(self, "phase_id", pid)

        env_ref = str(self.execution_envelope_ref or "").strip()
        if not env_ref:
            raise ValueError("execution_envelope_ref must be a non-empty string")
        object.__setattr__(self, "execution_envelope_ref", env_ref)

        sref = str(self.scope_ref or "").strip()
        if not sref:
            raise ValueError("scope_ref must be a non-empty string")
        object.__setattr__(self, "scope_ref", sref)

        spec = str(self.responsible_specialist or "").strip().lower()
        if not spec:
            raise ValueError("responsible_specialist must be a non-empty string")
        object.__setattr__(self, "responsible_specialist", spec)

        obj = str(self.objective or "").strip()
        if not obj:
            raise ValueError("objective must be a non-empty string")
        object.__setattr__(self, "objective", obj)

        if not self.expected_outputs or not isinstance(self.expected_outputs, tuple):
            raise ValueError("expected_outputs must be a non-empty tuple of strings")
        outputs = tuple(str(item).strip() for item in self.expected_outputs if str(item).strip())
        if not outputs:
            raise ValueError("expected_outputs must contain at least one non-empty output string")
        object.__setattr__(self, "expected_outputs", outputs)

        if not self.validation_requirements or not isinstance(self.validation_requirements, tuple):
            raise ValueError("validation_requirements must be a non-empty tuple of strings")
        vreqs = tuple(str(item).strip() for item in self.validation_requirements if str(item).strip())
        if not vreqs:
            raise ValueError("validation_requirements must contain at least one non-empty validation requirement string")
        object.__setattr__(self, "validation_requirements", vreqs)

        if self.allowed_paths is not None:
            if not isinstance(self.allowed_paths, tuple):
                raise ValueError("allowed_paths must be a tuple of strings when provided")
            cleaned_allowed = []
            seen_allowed = set()
            for p in self.allowed_paths:
                norm_p = _validate_repository_relative_path(p, "allowed_paths")
                if norm_p not in seen_allowed:
                    seen_allowed.add(norm_p)
                    cleaned_allowed.append(norm_p)
            allowed_tuple = tuple(cleaned_allowed)
            object.__setattr__(self, "allowed_paths", allowed_tuple)
        else:
            allowed_tuple = None

        if self.prohibited_paths is not None:
            if not isinstance(self.prohibited_paths, tuple):
                raise ValueError("prohibited_paths must be a tuple of strings when provided")
            cleaned_prohibited = []
            seen_prohibited = set()
            for p in self.prohibited_paths:
                norm_p = _validate_repository_relative_path(p, "prohibited_paths")
                if norm_p not in seen_prohibited:
                    seen_prohibited.add(norm_p)
                    cleaned_prohibited.append(norm_p)
            prohibited_tuple = tuple(cleaned_prohibited)
            object.__setattr__(self, "prohibited_paths", prohibited_tuple)

            if allowed_tuple:
                for ap in allowed_tuple:
                    for pp in prohibited_tuple:
                        if ap == pp or ap.startswith(pp.rstrip("/") + "/") or pp.startswith(ap.rstrip("/") + "/"):
                            raise ValueError(f"prohibited path '{pp}' overlaps with allowed path '{ap}'")

        if self.dependency_unit_ids is not None:
            if not isinstance(self.dependency_unit_ids, tuple):
                raise ValueError("dependency_unit_ids must be a tuple of strings when provided")
            deps = []
            seen_deps = set()
            for dep in self.dependency_unit_ids:
                dep_str = str(dep or "").strip()
                if not dep_str:
                    raise ValueError("dependency_unit_ids entry must be a non-empty string")
                if dep_str == uid:
                    raise ValueError(f"self dependency rejected: unit '{uid}' cannot depend on itself")
                if dep_str not in seen_deps:
                    seen_deps.add(dep_str)
                    deps.append(dep_str)
            object.__setattr__(self, "dependency_unit_ids", tuple(deps))

        if self.governance_decision_ref is not None:
            gref = str(self.governance_decision_ref or "").strip()
            if not gref:
                raise ValueError("governance_decision_ref must be a non-empty string when provided")
            object.__setattr__(self, "governance_decision_ref", gref)


def validate_approved_unit_plan_context(
    plan: ApprovedUnitPlan,
    operation_context: str | None = None,
    envelope: OrchestraRuntimeEnvelope | None = None,
    predecessor_evidence: dict[str, Any] | None = None,
) -> ValidationResult:
    """Contextual and authority validator for ApprovedUnitPlan (Design B).

    Enforces:
    - FILE_MUTATION contextual allowed_paths requirement
    - Execution Envelope binding (run_id, phase_id, specialist, scope)
    - Dependency predecessor evidence acceptance
    - Governance reference non-authorizing semantics
    - Escalation classification boundary
    """
    reasons: list[str] = []
    evaluated_rules: list[str] = ["STRUCTURAL_FIELD_CHECK", "PATH_SYNTAX_CHECK"]

    if not isinstance(plan, ApprovedUnitPlan):
        return ValidationResult(allowed=False, status="REJECTED", reasons=("expected ApprovedUnitPlan instance",))

    op = str(operation_context or (envelope.operation if envelope else "") or "").strip().upper()
    if op in {"FILE_MUTATION", "DOCUMENTATION", "WRITE"} or (op and "MUTATION" in op):
        evaluated_rules.append("FILE_MUTATION_ALLOWED_PATHS_CHECK")
        if plan.allowed_paths is None or len(plan.allowed_paths) == 0:
            reasons.append("MISSING_ALLOWED_PATHS: allowed_paths is required for FILE_MUTATION work")

    if envelope is not None:
        evaluated_rules.append("EXECUTION_ENVELOPE_BINDING_CHECK")
        if envelope.run_id != plan.execution_envelope_ref and getattr(envelope, "execution_envelope_ref", None) != plan.execution_envelope_ref:
            reasons.append(f"ENVELOPE_MISMATCH: execution_envelope_ref '{plan.execution_envelope_ref}' does not match envelope '{envelope.run_id}'")
        if envelope.phase_id and envelope.phase_id != plan.phase_id:
            reasons.append(f"PHASE_MISMATCH: plan phase_id '{plan.phase_id}' does not match envelope phase '{envelope.phase_id}'")
        if envelope.specialist and envelope.specialist.lower() != plan.responsible_specialist.lower():
            reasons.append(f"SPECIALIST_MISMATCH: plan specialist '{plan.responsible_specialist}' does not match envelope specialist '{envelope.specialist}'")

    if plan.dependency_unit_ids:
        evaluated_rules.append("DEPENDENCY_ACCEPTANCE_CHECK")
        if predecessor_evidence is not None:
            for dep_id in plan.dependency_unit_ids:
                evidence = predecessor_evidence.get(dep_id)
                if not evidence:
                    reasons.append(f"UNACCEPTED_DEPENDENCY: missing evidence for predecessor '{dep_id}'")
                elif isinstance(evidence, dict):
                    if evidence.get("status") not in {"COMPLETED", "ACCEPTED"}:
                        reasons.append(f"UNACCEPTED_DEPENDENCY: predecessor '{dep_id}' status '{evidence.get('status')}' is unaccepted")
                else:
                    reasons.append(f"UNACCEPTED_DEPENDENCY: predecessor '{dep_id}' evidence must be a mapping with accepted status")

    if reasons:
        has_escalation = any(
            "MISSING_INTENT" in r or "MATERIAL_SCOPE_CHANGE" in r or "POLICY_CONFLICT" in r or "NEW_AUTHORITY" in r
            for r in reasons
        )
        status = "ESCALATE_HUMAN" if has_escalation else "REJECTED"
        return ValidationResult(allowed=False, status=status, reasons=tuple(reasons), evaluated_rules=tuple(evaluated_rules))

    return ValidationResult(allowed=True, status="ACCEPTED", reasons=(), evaluated_rules=tuple(evaluated_rules))


@dataclass(frozen=True)
class Skill:
    slug: str
    name: str
    description: str
    skill_path: Path
    role: str = ""
    activation_level: str = ""
    depends_on: str = ""
    commands: tuple[str, ...] = ()
    output_formats: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Command:
    name: str
    raw_input: str
    adapter_name: str
    arguments: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextPackage:
    adapter_name: str
    prompt: str
    project_root: Path
    available_commands: tuple[str, ...]
    manifest_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    command_name: str
    skill_slug: str
    governance_required: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceRule:
    name: str
    description: str
    skill_slugs: tuple[str, ...] = ()
    command_names: tuple[str, ...] = ()
    validator_key: str = ""
    blocking: bool = True


@dataclass(frozen=True)
class ValidationResult:
    allowed: bool
    status: str
    reasons: tuple[str, ...] = ()
    evaluated_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    adapter_name: str
    command_name: str
    route: RouteDecision
    validation: ValidationResult
    output: str
    audit_entry_id: str
    run_identity: RunIdentity | None = None
    authority_decision_id: str | None = None
    capability_decision_id: str | None = None
    authority_mode: str | None = None
    lifecycle_state: str | None = None
    terminal_result: StructuredTerminalResult | None = None
    runtime_audit_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        event_ids = tuple(str(item).strip() for item in self.runtime_audit_event_ids)
        if any(not item for item in event_ids) or len(set(event_ids)) != len(event_ids):
            raise ValueError("runtime audit event identifiers must be non-empty and unique")
        object.__setattr__(self, "runtime_audit_event_ids", event_ids)
        if self.run_identity is None:
            if any(
                (
                    self.authority_decision_id,
                    self.capability_decision_id,
                    self.authority_mode,
                    self.lifecycle_state,
                    self.terminal_result,
                    event_ids,
                )
            ):
                raise ValueError("runtime evidence requires run identity")
            return

        mode = str(self.authority_mode or "").strip()
        state = str(self.lifecycle_state or "").strip()
        if mode not in {"ACTIVE", "COMPATIBILITY"}:
            raise ValueError("runtime evidence requires a valid authority mode")
        valid_states = {
            "INITIALIZING",
            "ACTIVE",
            "WAITING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "TIMED_OUT",
            "BLOCKED",
        }
        if state not in valid_states:
            raise ValueError("runtime evidence requires a valid lifecycle state")
        terminal_states = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "BLOCKED"}
        if state in terminal_states:
            if (
                self.terminal_result is None
                or self.terminal_result.run_id != self.run_identity.run_id
                or self.terminal_result.state.value != state
            ):
                raise ValueError("terminal runtime evidence must match lifecycle state")
        elif self.terminal_result is not None:
            raise ValueError("non-terminal runtime evidence cannot include a terminal result")
        object.__setattr__(self, "authority_mode", mode)
        object.__setattr__(self, "lifecycle_state", state)


class AuditEventType(str, Enum):
    ROOT_AUTHORITY_CREATED = "ROOT_AUTHORITY_CREATED"
    AUTHORITY_DECIDED = "AUTHORITY_DECIDED"
    CAPABILITY_MANIFEST_CREATED = "CAPABILITY_MANIFEST_CREATED"
    CAPABILITY_DECIDED = "CAPABILITY_DECIDED"
    DELEGATION_ACCEPTED = "DELEGATION_ACCEPTED"
    DELEGATION_REJECTED = "DELEGATION_REJECTED"
    LIFECYCLE_TRANSITIONED = "LIFECYCLE_TRANSITIONED"
    TERMINAL_RESULT_RECORDED = "TERMINAL_RESULT_RECORDED"
    INITIALIZATION_FAILED = "INITIALIZATION_FAILED"
    COLLABORATION_SESSION_OPENED = "COLLABORATION_SESSION_OPENED"
    COLLABORATION_STATUS_TRANSITIONED = "COLLABORATION_STATUS_TRANSITIONED"
    CONTRACT_FROZEN = "CONTRACT_FROZEN"
    CONTRACT_INVALIDATED = "CONTRACT_INVALIDATED"
    SPECIALIST_REENTRY_RECOMMENDED = "SPECIALIST_REENTRY_RECOMMENDED"
    COLLABORATION_SESSION_CLOSED = "COLLABORATION_SESSION_CLOSED"
    COORDINATION_INPUT_REJECTED = "COORDINATION_INPUT_REJECTED"


@dataclass(frozen=True, slots=True)
class RunIdentity:
    run_id: str
    parent_run_id: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        run_id = self.run_id.strip()
        parent_run_id = self.parent_run_id.strip() if self.parent_run_id else None
        if not run_id:
            raise ValueError("run_id must be non-empty")
        if parent_run_id == run_id:
            raise ValueError("parent_run_id must differ from run_id")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        if self.correlation_id is not None:
            cid = validate_correlation_id(self.correlation_id)
            object.__setattr__(self, "correlation_id", cid)

    def to_dict(self) -> dict[str, str | None]:
        data: dict[str, str | None] = {"run_id": self.run_id, "parent_run_id": self.parent_run_id}
        if self.correlation_id is not None:
            data["correlation_id"] = self.correlation_id
        return data


@dataclass(frozen=True, slots=True)
class RuntimeAuditEvent:
    event_id: str
    event_type: AuditEventType
    run_id: str
    related_id: str
    reason_code: str
    provenance_ids: tuple[str, ...] = ()
    details: tuple[tuple[str, str], ...] = ()
    parent_run_id: str | None = None

    def __post_init__(self) -> None:
        event_id = self.event_id.strip()
        run_id = self.run_id.strip()
        related_id = self.related_id.strip()
        reason_code = self.reason_code.strip()
        if not all((event_id, run_id, related_id, reason_code)):
            raise ValueError("audit event identifiers and reason_code must be non-empty")
        event_type = AuditEventType(self.event_type)
        provenance_ids = tuple(sorted({item.strip() for item in self.provenance_ids if item.strip()}))
        details = tuple(sorted((str(key).strip(), str(value)) for key, value in self.details))
        if any(not key for key, _ in details) or len({key for key, _ in details}) != len(details):
            raise ValueError("audit detail keys must be non-empty and unique")
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "related_id", related_id)
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "provenance_ids", provenance_ids)
        object.__setattr__(self, "details", details)
        object.__setattr__(self, "parent_run_id", self.parent_run_id.strip() if self.parent_run_id else None)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "related_id": self.related_id,
            "reason_code": self.reason_code,
            "provenance_ids": list(self.provenance_ids),
            "details": {key: value for key, value in self.details},
        }


class EnvelopeMessageType(str, Enum):
    EXECUTION_RESULT = "execution_result"
    TRANSITION_DECISION = "transition_decision"
    AUDIT_EVENT = "audit_event"


@dataclass(frozen=True, slots=True)
class OrchestraRuntimeEnvelope:
    schema_version: str
    message_type: EnvelopeMessageType
    timestamp: str
    run_id: str
    specialist: str
    operation: str | None = None
    status: str | None = None
    disposition: str | None = None
    reason_code: str | None = None
    event_type: str | None = None
    details: dict[str, Any] | None = None
    parent_run_id: str | None = None
    collaboration_session_id: str | None = None
    phase_id: str | None = None
    unit_id: str | None = None
    authority_decision_ref: str | None = None
    capability_decision_ref: str | None = None
    governance_decision_ref: str | None = None
    evidence_fingerprint: str | None = None
    correlation_id: str | None = None
    summary: str | None = None
    data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        schema_version = self.schema_version.strip() if isinstance(self.schema_version, str) else ""
        if not schema_version:
            raise ValueError("schema_version must be non-empty")

        try:
            msg_type = EnvelopeMessageType(self.message_type)
        except ValueError:
            raise ValueError(f"unsupported message_type: {self.message_type}")

        timestamp = self.timestamp.strip() if isinstance(self.timestamp, str) else ""
        if not timestamp:
            raise ValueError("timestamp must be non-empty")

        run_id = self.run_id.strip() if isinstance(self.run_id, str) else ""
        if not run_id:
            raise ValueError("run_id must be non-empty")

        specialist = self.specialist.strip() if isinstance(self.specialist, str) else ""
        if not specialist:
            raise ValueError("specialist must be non-empty")

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "message_type", msg_type)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "specialist", specialist)

        if self.correlation_id is not None:
            cid = validate_correlation_id(self.correlation_id)
            object.__setattr__(self, "correlation_id", cid)

        if msg_type == EnvelopeMessageType.EXECUTION_RESULT:
            operation = self.operation.strip() if isinstance(self.operation, str) else ""
            status = self.status.strip() if isinstance(self.status, str) else ""
            reason_code = self.reason_code.strip() if isinstance(self.reason_code, str) else ""
            if not all((operation, status, reason_code)):
                raise ValueError("execution_result variant requires non-empty operation, status, and reason_code")

            prohibited = (
                ("disposition", self.disposition),
                ("event_type", self.event_type),
                ("details", self.details),
                ("collaboration_session_id", self.collaboration_session_id),
                ("phase_id", self.phase_id),
                ("unit_id", self.unit_id),
            )
            for name, val in prohibited:
                if val is not None:
                    raise ValueError(f"execution_result variant prohibits field '{name}'")

            object.__setattr__(self, "operation", operation)
            object.__setattr__(self, "status", status)
            object.__setattr__(self, "reason_code", reason_code)

        elif msg_type == EnvelopeMessageType.TRANSITION_DECISION:
            operation = self.operation.strip() if isinstance(self.operation, str) else ""
            disposition = self.disposition.strip() if isinstance(self.disposition, str) else ""
            reason_code = self.reason_code.strip() if isinstance(self.reason_code, str) else ""
            if not all((operation, disposition, reason_code)):
                raise ValueError("transition_decision variant requires non-empty operation, disposition, and reason_code")

            prohibited = (
                ("status", self.status),
                ("event_type", self.event_type),
                ("details", self.details),
                ("parent_run_id", self.parent_run_id),
                ("collaboration_session_id", self.collaboration_session_id),
                ("authority_decision_ref", self.authority_decision_ref),
                ("capability_decision_ref", self.capability_decision_ref),
            )
            for name, val in prohibited:
                if val is not None:
                    raise ValueError(f"transition_decision variant prohibits field '{name}'")

            object.__setattr__(self, "operation", operation)
            object.__setattr__(self, "disposition", disposition)
            object.__setattr__(self, "reason_code", reason_code)

        elif msg_type == EnvelopeMessageType.AUDIT_EVENT:
            event_type = self.event_type.strip() if isinstance(self.event_type, str) else ""
            if not event_type:
                raise ValueError("audit_event variant requires non-empty event_type")
            if self.details is None or not isinstance(self.details, dict):
                raise ValueError("audit_event variant requires details mapping")

            prohibited = (
                ("operation", self.operation),
                ("status", self.status),
                ("disposition", self.disposition),
                ("reason_code", self.reason_code),
                ("data", self.data),
                ("phase_id", self.phase_id),
                ("unit_id", self.unit_id),
                ("authority_decision_ref", self.authority_decision_ref),
                ("capability_decision_ref", self.capability_decision_ref),
                ("governance_decision_ref", self.governance_decision_ref),
                ("evidence_fingerprint", self.evidence_fingerprint),
            )
            for name, val in prohibited:
                if val is not None:
                    raise ValueError(f"audit_event variant prohibits field '{name}'")

            object.__setattr__(self, "event_type", event_type)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "message_type": self.message_type.value if isinstance(self.message_type, Enum) else str(self.message_type),
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "specialist": self.specialist,
        }

        optional_fields = [
            "operation",
            "status",
            "disposition",
            "reason_code",
            "event_type",
            "details",
            "parent_run_id",
            "collaboration_session_id",
            "phase_id",
            "unit_id",
            "authority_decision_ref",
            "capability_decision_ref",
            "governance_decision_ref",
            "evidence_fingerprint",
            "correlation_id",
            "summary",
            "data",
        ]
        for name in optional_fields:
            val = getattr(self, name)
            if val is not None:
                result[name] = val
        return result
