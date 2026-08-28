from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Mapping

from .errors import RuntimeContractError, RuntimeInitializationError
from .interfaces import IIDEAdapter, ISpecialistExecutionEngine, ISkillRegistry
from .lifecycle import LifecycleState
from .models import ContextPackage, RouteDecision, ValidationResult
from .services import (
    ContextAssembler,
    RuntimeComposition,
    RuntimeExecutor,
    RuntimeOperationResult,
    _stable_id,
)


SPECIALIST_EXECUTION_REQUEST_VERSION = "orchestra.specialist-execution-request.v1"
SPECIALIST_EXECUTION_RECEIPT_VERSION = "orchestra.specialist-execution-receipt.v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class SpecialistExecutionMode(str, Enum):
    DETERMINISTIC_TEST_ENGINE = "DETERMINISTIC_TEST_ENGINE"
    HOST_NATIVE = "HOST_NATIVE"


class SpecialistExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class SpecialistSideEffectClass(str, Enum):
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    FILE_MUTATION = "FILE_MUTATION"
    EXTERNAL_MUTATION = "EXTERNAL_MUTATION"
    UNKNOWN = "UNKNOWN"


class SpecialistExecutionContractError(RuntimeContractError):
    pass


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SpecialistExecutionContractError(
            f"{field_name} must be non-empty",
            "INVALID_SPECIALIST_EXECUTION_CONTRACT",
            {"field": field_name},
        )
    return text


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _sorted_unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized = tuple(str(item).strip() for item in values if str(item).strip())
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True, slots=True)
class SpecialistExecutionConstraint:
    source: str
    key: str
    kind: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        source = _text(self.source, "constraint source").upper()
        if source not in {"AUTHORITY", "CAPABILITY"}:
            raise SpecialistExecutionContractError(
                "constraint source must be AUTHORITY or CAPABILITY",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"source": source},
            )
        key = _text(self.key, "constraint key").casefold()
        kind = _text(self.kind, "constraint kind").upper()
        if kind not in {"EXACT", "ALLOWED_SET"}:
            raise SpecialistExecutionContractError(
                "constraint kind is unsupported",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"kind": kind},
            )
        values = _sorted_unique(self.values)
        if not values or (kind == "EXACT" and len(values) != 1):
            raise SpecialistExecutionContractError(
                "constraint values do not match the declared kind",
                "INVALID_SPECIALIST_EXECUTION_CONSTRAINT",
                {"key": key},
            )
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "values", values)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "key": self.key,
            "kind": self.kind,
            "values": list(self.values),
        }


@dataclass(frozen=True, slots=True)
class SpecialistExecutionRequest:
    request_version: str
    request_id: str
    request_digest: str
    run_id: str
    parent_run_id: str | None
    correlation_id: str | None
    adapter_name: str
    command_name: str
    specialist: str
    project_root: str
    skill_source_path: str
    skill_source_digest: str
    task_input: str
    authority_decision_ref: str
    capability_decision_ref: str
    governance_status: str
    evaluated_governance_rules: tuple[str, ...]
    execution_constraints: tuple[SpecialistExecutionConstraint, ...]
    execution_mode: SpecialistExecutionMode

    def __post_init__(self) -> None:
        if self.request_version != SPECIALIST_EXECUTION_REQUEST_VERSION:
            raise SpecialistExecutionContractError(
                "unsupported specialist execution request version",
                "UNSUPPORTED_SPECIALIST_EXECUTION_REQUEST_VERSION",
            )
        for field_name in (
            "request_id",
            "run_id",
            "adapter_name",
            "command_name",
            "specialist",
            "project_root",
            "skill_source_path",
            "authority_decision_ref",
            "capability_decision_ref",
            "governance_status",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        digest = str(self.request_digest).strip().casefold()
        skill_digest = str(self.skill_source_digest).strip().casefold()
        if not SHA256_PATTERN.fullmatch(digest):
            raise SpecialistExecutionContractError(
                "request_digest must be a SHA-256 digest",
                "INVALID_REQUEST_DIGEST",
            )
        if not SHA256_PATTERN.fullmatch(skill_digest):
            raise SpecialistExecutionContractError(
                "skill_source_digest must be a SHA-256 digest",
                "INVALID_SKILL_SOURCE_DIGEST",
            )
        task_input = str(self.task_input)
        if not task_input.strip():
            raise SpecialistExecutionContractError(
                "task_input must be non-empty",
                "EMPTY_SPECIALIST_TASK_INPUT",
            )
        rules = _sorted_unique(self.evaluated_governance_rules)
        constraints = tuple(
            sorted(
                tuple(self.execution_constraints),
                key=lambda item: (item.source, item.key, item.kind, item.values),
            )
        )
        if len({(item.source, item.key) for item in constraints}) != len(constraints):
            raise SpecialistExecutionContractError(
                "execution constraints must be unique per source/key",
                "DUPLICATE_SPECIALIST_EXECUTION_CONSTRAINT",
            )
        mode = SpecialistExecutionMode(self.execution_mode)
        parent_run_id = str(self.parent_run_id).strip() if self.parent_run_id else None
        correlation_id = str(self.correlation_id).strip() if self.correlation_id else None
        object.__setattr__(self, "request_digest", digest)
        object.__setattr__(self, "skill_source_digest", skill_digest)
        object.__setattr__(self, "task_input", task_input)
        object.__setattr__(self, "evaluated_governance_rules", rules)
        object.__setattr__(self, "execution_constraints", constraints)
        object.__setattr__(self, "execution_mode", mode)
        object.__setattr__(self, "parent_run_id", parent_run_id)
        object.__setattr__(self, "correlation_id", correlation_id)
        if self.request_digest != self.compute_digest():
            raise SpecialistExecutionContractError(
                "request digest does not match request payload",
                "REQUEST_DIGEST_MISMATCH",
            )
        expected_id = f"specialist-request.{self.request_digest[:24]}"
        if self.request_id != expected_id:
            raise SpecialistExecutionContractError(
                "request identifier does not match request digest",
                "REQUEST_IDENTITY_MISMATCH",
            )

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        parent_run_id: str | None,
        correlation_id: str | None,
        adapter_name: str,
        command_name: str,
        specialist: str,
        project_root: str,
        skill_source_path: str,
        skill_source_digest: str,
        task_input: str,
        authority_decision_ref: str,
        capability_decision_ref: str,
        governance_status: str,
        evaluated_governance_rules: tuple[str, ...],
        execution_constraints: tuple[SpecialistExecutionConstraint, ...],
        execution_mode: SpecialistExecutionMode,
    ) -> SpecialistExecutionRequest:
        payload = {
            "request_version": SPECIALIST_EXECUTION_REQUEST_VERSION,
            "run_id": str(run_id).strip(),
            "parent_run_id": str(parent_run_id).strip() if parent_run_id else None,
            "correlation_id": str(correlation_id).strip() if correlation_id else None,
            "adapter_name": str(adapter_name).strip(),
            "command_name": str(command_name).strip(),
            "specialist": str(specialist).strip(),
            "project_root": str(project_root).strip(),
            "skill_source_path": str(skill_source_path).strip(),
            "skill_source_digest": str(skill_source_digest).strip().casefold(),
            "task_input": str(task_input),
            "authority_decision_ref": str(authority_decision_ref).strip(),
            "capability_decision_ref": str(capability_decision_ref).strip(),
            "governance_status": str(governance_status).strip(),
            "evaluated_governance_rules": list(_sorted_unique(evaluated_governance_rules)),
            "execution_constraints": [
                item.to_dict()
                for item in sorted(
                    tuple(execution_constraints),
                    key=lambda item: (item.source, item.key, item.kind, item.values),
                )
            ],
            "execution_mode": SpecialistExecutionMode(execution_mode).value,
        }
        request_digest = _digest(payload)
        return cls(
            request_version=SPECIALIST_EXECUTION_REQUEST_VERSION,
            request_id=f"specialist-request.{request_digest[:24]}",
            request_digest=request_digest,
            run_id=payload["run_id"],
            parent_run_id=payload["parent_run_id"],
            correlation_id=payload["correlation_id"],
            adapter_name=payload["adapter_name"],
            command_name=payload["command_name"],
            specialist=payload["specialist"],
            project_root=payload["project_root"],
            skill_source_path=payload["skill_source_path"],
            skill_source_digest=payload["skill_source_digest"],
            task_input=payload["task_input"],
            authority_decision_ref=payload["authority_decision_ref"],
            capability_decision_ref=payload["capability_decision_ref"],
            governance_status=payload["governance_status"],
            evaluated_governance_rules=tuple(payload["evaluated_governance_rules"]),
            execution_constraints=tuple(execution_constraints),
            execution_mode=SpecialistExecutionMode(payload["execution_mode"]),
        )

    def digest_payload(self) -> dict[str, object]:
        return {
            "request_version": self.request_version,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "correlation_id": self.correlation_id,
            "adapter_name": self.adapter_name,
            "command_name": self.command_name,
            "specialist": self.specialist,
            "project_root": self.project_root,
            "skill_source_path": self.skill_source_path,
            "skill_source_digest": self.skill_source_digest,
            "task_input": self.task_input,
            "authority_decision_ref": self.authority_decision_ref,
            "capability_decision_ref": self.capability_decision_ref,
            "governance_status": self.governance_status,
            "evaluated_governance_rules": list(self.evaluated_governance_rules),
            "execution_constraints": [item.to_dict() for item in self.execution_constraints],
            "execution_mode": self.execution_mode.value,
        }

    def compute_digest(self) -> str:
        return _digest(self.digest_payload())

    def to_dict(self) -> dict[str, object]:
        return {
            "request_version": self.request_version,
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            **self.digest_payload() | {},
        }


@dataclass(frozen=True, slots=True)
class SpecialistExecutionReceipt:
    receipt_version: str
    receipt_id: str
    request_id: str
    request_digest: str
    run_id: str
    adapter_name: str
    command_name: str
    specialist: str
    engine_id: str
    engine_version: str
    host_execution_id: str
    status: SpecialistExecutionStatus
    reason_code: str
    output: str
    evidence_refs: tuple[str, ...]
    side_effect_class: SpecialistSideEffectClass
    host_identity: str | None = None
    sandbox_identity: str | None = None
    approval_policy_identity: str | None = None
    artifact_refs: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    started_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if self.receipt_version != SPECIALIST_EXECUTION_RECEIPT_VERSION:
            raise SpecialistExecutionContractError(
                "unsupported specialist execution receipt version",
                "UNSUPPORTED_SPECIALIST_EXECUTION_RECEIPT_VERSION",
            )
        for field_name in (
            "receipt_id",
            "request_id",
            "run_id",
            "adapter_name",
            "command_name",
            "specialist",
            "engine_id",
            "engine_version",
            "host_execution_id",
            "reason_code",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        digest = str(self.request_digest).strip().casefold()
        if not SHA256_PATTERN.fullmatch(digest):
            raise SpecialistExecutionContractError(
                "receipt request_digest must be a SHA-256 digest",
                "INVALID_REQUEST_DIGEST",
            )
        object.__setattr__(self, "request_digest", digest)
        object.__setattr__(self, "status", SpecialistExecutionStatus(self.status))
        object.__setattr__(self, "side_effect_class", SpecialistSideEffectClass(self.side_effect_class))
        object.__setattr__(self, "output", str(self.output))
        object.__setattr__(self, "evidence_refs", _sorted_unique(self.evidence_refs))
        object.__setattr__(self, "artifact_refs", _sorted_unique(self.artifact_refs))
        object.__setattr__(self, "changed_paths", _sorted_unique(self.changed_paths))
        for field_name in (
            "host_identity",
            "sandbox_identity",
            "approval_policy_identity",
            "started_at",
            "completed_at",
        ):
            value = getattr(self, field_name)
            object.__setattr__(self, field_name, str(value).strip() if value else None)

    def assert_matches(
        self,
        request: SpecialistExecutionRequest,
        *,
        engine_id: str,
        engine_version: str,
    ) -> None:
        comparisons = (
            ("request_id", self.request_id, request.request_id, "REQUEST_IDENTITY_MISMATCH"),
            ("request_digest", self.request_digest, request.request_digest, "REQUEST_DIGEST_MISMATCH"),
            ("run_id", self.run_id, request.run_id, "RUN_IDENTITY_MISMATCH"),
            ("adapter_name", self.adapter_name, request.adapter_name, "ADAPTER_IDENTITY_MISMATCH"),
            ("command_name", self.command_name, request.command_name, "COMMAND_IDENTITY_MISMATCH"),
            ("specialist", self.specialist, request.specialist, "SPECIALIST_IDENTITY_MISMATCH"),
            ("engine_id", self.engine_id, str(engine_id).strip(), "ENGINE_IDENTITY_MISMATCH"),
            ("engine_version", self.engine_version, str(engine_version).strip(), "ENGINE_VERSION_MISMATCH"),
        )
        for field_name, actual, expected, reason_code in comparisons:
            if actual != expected:
                raise SpecialistExecutionContractError(
                    f"specialist execution receipt {field_name} does not match the request boundary",
                    reason_code,
                    {"field": field_name},
                )
        if request.execution_mode is SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE:
            if self.side_effect_class is not SpecialistSideEffectClass.NONE or self.changed_paths:
                raise SpecialistExecutionContractError(
                    "deterministic specialist execution receipts cannot report side effects",
                    "DETERMINISTIC_ENGINE_SIDE_EFFECT_REJECTED",
                )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "receipt_version": self.receipt_version,
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "request_digest": self.request_digest,
            "run_id": self.run_id,
            "adapter_name": self.adapter_name,
            "command_name": self.command_name,
            "specialist": self.specialist,
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "host_execution_id": self.host_execution_id,
            "status": self.status.value,
            "reason_code": self.reason_code,
            "output": self.output,
            "evidence_refs": list(self.evidence_refs),
            "side_effect_class": self.side_effect_class.value,
            "artifact_refs": list(self.artifact_refs),
            "changed_paths": list(self.changed_paths),
        }
        for field_name in (
            "host_identity",
            "sandbox_identity",
            "approval_policy_identity",
            "started_at",
            "completed_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                data[field_name] = value
        return data


@dataclass(frozen=True, slots=True)
class _PendingExecutionInput:
    adapter: IIDEAdapter
    prompt: str
    metadata: Mapping[str, object]


class SpecialistRuntimeExecutor(RuntimeExecutor):
    """Opt-in typed specialist execution attachment over the existing trusted runtime gates.

    The base RuntimeExecutor remains unchanged. This subclass binds the task input to an
    executor-local ContextVar before entering the existing runtime. The configured engine
    is called only from the existing post-activation operation boundary, so routing,
    authority, capability, governance, coordination, and lifecycle activation remain
    owned by RuntimeExecutor.
    """

    def __init__(
        self,
        skill_registry: ISkillRegistry,
        router,
        governance,
        context_assembler: ContextAssembler,
        composition: RuntimeComposition,
        *,
        execution_engine: ISpecialistExecutionEngine | None = None,
        execution_mode: SpecialistExecutionMode = SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE,
    ) -> None:
        if execution_engine is not None and not isinstance(execution_engine, ISpecialistExecutionEngine):
            raise RuntimeInitializationError(
                "specialist execution engine must implement ISpecialistExecutionEngine",
                "INVALID_SPECIALIST_EXECUTION_ENGINE",
            )
        if execution_engine is None and SpecialistExecutionMode(execution_mode) is SpecialistExecutionMode.HOST_NATIVE:
            raise RuntimeInitializationError(
                "HOST_NATIVE execution requires an explicit execution engine",
                "ENGINE_NOT_CONFIGURED",
            )
        self._execution_engine = execution_engine
        self._execution_mode = SpecialistExecutionMode(execution_mode)
        self._execution_skill_registry = skill_registry
        self._execution_context_assembler = context_assembler
        self._pending_execution: ContextVar[_PendingExecutionInput | None] = ContextVar(
            f"orchestra-specialist-execution-{id(self)}",
            default=None,
        )
        super().__init__(
            skill_registry,
            router,
            governance,
            context_assembler,
            composition,
            operation=self._execute_specialist if execution_engine is not None else None,
        )

    @property
    def execution_engine(self) -> ISpecialistExecutionEngine | None:
        return self._execution_engine

    @property
    def execution_mode(self) -> SpecialistExecutionMode:
        return self._execution_mode

    def execute(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        metadata: dict | None = None,
        *,
        coordination_session=None,
    ):
        if self._execution_engine is None:
            return super().execute(
                adapter,
                prompt,
                metadata,
                coordination_session=coordination_session,
            )
        token = self._pending_execution.set(
            _PendingExecutionInput(adapter, str(prompt), dict(metadata or {}))
        )
        try:
            return super().execute(
                adapter,
                prompt,
                metadata,
                coordination_session=coordination_session,
            )
        finally:
            self._pending_execution.reset(token)

    def execute_delegated(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        resolution,
        metadata: dict | None = None,
        *,
        coordination_session=None,
    ):
        if self._execution_engine is None:
            return super().execute_delegated(
                adapter,
                prompt,
                resolution,
                metadata,
                coordination_session=coordination_session,
            )
        token = self._pending_execution.set(
            _PendingExecutionInput(adapter, str(prompt), dict(metadata or {}))
        )
        try:
            return super().execute_delegated(
                adapter,
                prompt,
                resolution,
                metadata,
                coordination_session=coordination_session,
            )
        finally:
            self._pending_execution.reset(token)

    def _execute_specialist(
        self,
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> RuntimeOperationResult:
        pending = self._pending_execution.get()
        if pending is None or self._execution_engine is None:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution boundary was not configured",
                "ENGINE_NOT_CONFIGURED",
            )
        try:
            request = self._build_request(pending, adapter_name, decision, validation)
            receipt = self._execution_engine.execute(request)
            if not isinstance(receipt, SpecialistExecutionReceipt):
                raise SpecialistExecutionContractError(
                    "specialist execution engine returned an invalid receipt type",
                    "MALFORMED_EXECUTION_RECEIPT",
                )
            receipt.assert_matches(
                request,
                engine_id=self._execution_engine.engine_id,
                engine_version=self._execution_engine.engine_version,
            )
            state = {
                SpecialistExecutionStatus.COMPLETED: LifecycleState.COMPLETED,
                SpecialistExecutionStatus.FAILED: LifecycleState.FAILED,
                SpecialistExecutionStatus.CANCELLED: LifecycleState.CANCELLED,
                SpecialistExecutionStatus.TIMED_OUT: LifecycleState.TIMED_OUT,
            }[receipt.status]
            refs = _sorted_unique(
                (
                    f"specialist-request:{request.request_id}",
                    f"specialist-request-digest:{request.request_digest}",
                    f"specialist-receipt:{receipt.receipt_id}",
                    *receipt.evidence_refs,
                )
            )
            return RuntimeOperationResult(
                state,
                receipt.output,
                receipt.reason_code,
                refs,
            )
        except RuntimeContractError as exc:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution contract failed closed",
                exc.reason_code,
                (type(exc).__name__,),
            )
        except Exception as exc:
            return RuntimeOperationResult(
                LifecycleState.FAILED,
                "specialist execution engine failed",
                "SPECIALIST_ENGINE_EXCEPTION",
                (type(exc).__name__,),
            )

    def _build_request(
        self,
        pending: _PendingExecutionInput,
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> SpecialistExecutionRequest:
        binding = self.composition.policy.binding_for(decision.command_name, decision.skill_slug)
        if binding is None:
            raise SpecialistExecutionContractError(
                "specialist execution request requires the trusted runtime binding",
                "MISSING_RUNTIME_BINDING",
            )
        context: ContextPackage = self._execution_context_assembler.assemble(
            pending.adapter,
            pending.prompt,
            dict(pending.metadata),
        )
        skill = self._execution_skill_registry.get_skill(decision.skill_slug)
        if skill is None:
            raise SpecialistExecutionContractError(
                "specialist execution request cannot resolve the selected skill",
                "SPECIALIST_IDENTITY_MISMATCH",
            )
        project_root = Path(context.project_root).resolve()
        skill_path = Path(skill.skill_path).resolve()
        try:
            relative_skill_path = skill_path.relative_to(project_root).as_posix()
        except ValueError as exc:
            raise SpecialistExecutionContractError(
                "selected specialist source is outside the project root",
                "UNTRUSTED_SPECIALIST_SOURCE_PATH",
            ) from exc
        if not skill_path.is_file():
            raise SpecialistExecutionContractError(
                "selected specialist source is unavailable",
                "SPECIALIST_SOURCE_UNAVAILABLE",
            )
        constraints = tuple(
            SpecialistExecutionConstraint("AUTHORITY", item.key, item.kind.value, item.values)
            for item in binding.authority_constraints
        ) + tuple(
            SpecialistExecutionConstraint("CAPABILITY", item.key, item.kind.value, item.values)
            for item in binding.capability_constraints
        )
        authority_decision_ref = _stable_id(
            "authority-decision",
            {
                "run_id": self.composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "scope_id": self.composition.root_authority.scope_id,
            },
        )
        capability_decision_ref = _stable_id(
            "capability-decision",
            {
                "run_id": self.composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "manifest_id": self.composition.capability_manifest.manifest_id,
            },
        )
        return SpecialistExecutionRequest.create(
            run_id=self.composition.run_identity.run_id,
            parent_run_id=self.composition.run_identity.parent_run_id,
            correlation_id=self.composition.run_identity.correlation_id,
            adapter_name=adapter_name,
            command_name=decision.command_name,
            specialist=decision.skill_slug,
            project_root=str(project_root),
            skill_source_path=relative_skill_path,
            skill_source_digest=sha256(skill_path.read_bytes()).hexdigest(),
            task_input=pending.prompt,
            authority_decision_ref=authority_decision_ref,
            capability_decision_ref=capability_decision_ref,
            governance_status=validation.status,
            evaluated_governance_rules=validation.evaluated_rules,
            execution_constraints=constraints,
            execution_mode=self._execution_mode,
        )
