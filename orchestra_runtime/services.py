from __future__ import annotations

from collections.abc import Callable, Iterable
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re

from .authority import (
    AuthorityEvaluator,
    AuthorityProvenance,
    AuthorityScope,
    Constraint,
    ProvenanceSource,
    TargetSelector,
    authority_decision_event,
    initialization_failure_event,
    root_authority_event,
)
from .capabilities import (
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    RuntimeCapabilityManifest,
    capability_decision_event,
    capability_manifest_event,
)
from .delegation import (
    DelegationPolicy,
    DelegationRequest,
    DelegationResolution,
    DelegationValidator,
    delegation_accepted_event,
    delegation_rejected_event,
)
from .errors import (
    DelegationRejectedError,
    RuntimeAuditError,
    RuntimeBindingError,
    RuntimeContractError,
    RuntimeInitializationError,
)

from .factories import SkillFactory
from .interfaces import (
    IAuditSink,
    IAuthorityEvaluator,
    ICapabilityResolver,
    IDelegationValidator,
    IGovernanceValidator,
    IIDEAdapter,
    ILifecycleController,
    IRouterService,
    IRuntimeExecutor,
    ISkillRegistry,
)
from .lifecycle import (
    LifecycleController,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleSnapshot,
    LifecycleState,
    StructuredTerminalResult,
    lifecycle_rejection_event,
    lifecycle_transition_event,
    terminal_result_event,
)
from .models import (
    Command,
    ContextPackage,
    ExecutionResult,
    GovernanceRule,
    RouteDecision,
    RunIdentity,
    RuntimeAuditEvent,
    ValidationResult,
)
from .repositories import ManifestRepository, SkillSourceRepository


DEFAULT_COMMAND_ROUTES = {
    "conductor": "conductor",
    "arbiter": "arbiter",
    "clockwork": "clockwork",
    "review-architecture": "clockwork",
    "cloak": "cloak",
    "review-ui": "cloak",
    "chronicler": "chronicler",
    "review-db": "chronicler",
    "scribe": "scribe",
    "review-docs": "scribe",
    "weaver": "weaver",
    "diagram-check": "weaver",
    "overseer": "overseer",
    "qa-check": "overseer",
    "cipher": "cipher",
    "security-check": "cipher",
    "dagger": "dagger",
    "resilience-check": "dagger",
    "ponytail": "ponytail",
    "the-steward": "the-steward",
    "the-governor": "the-governor",
}

COMPATIBILITY_POLICY_ID = "orchestra.runtime.compatibility"
COMPATIBILITY_POLICY_VERSION = "1"
RUNTIME_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
ROUTE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")


def _stable_id(prefix: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}.{sha256(encoded).hexdigest()[:24]}"


def _runtime_identifier(value: object, field_name: str, *, route: bool = False) -> str:
    text = str(value).strip().casefold()
    pattern = ROUTE_IDENTIFIER_PATTERN if route else RUNTIME_IDENTIFIER_PATTERN
    if not text or not pattern.fullmatch(text):
        raise RuntimeInitializationError(
            f"{field_name} must be a canonical identifier",
            "INVALID_RUNTIME_POLICY",
            {"field": field_name},
        )
    return text


class AuthorityMode(str, Enum):
    ACTIVE = "ACTIVE"
    COMPATIBILITY = "COMPATIBILITY"


@dataclass(frozen=True, slots=True)
class RuntimePolicyBinding:
    command_name: str
    skill_slug: str
    authority_target: TargetSelector
    authority_operation: str
    capability_id: str
    capability_operation: str
    authority_constraints: tuple[Constraint, ...] = ()
    capability_constraints: tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        authority_constraints = tuple(sorted(tuple(self.authority_constraints), key=lambda item: item.key))
        capability_constraints = tuple(sorted(tuple(self.capability_constraints), key=lambda item: item.key))
        if len({item.key for item in authority_constraints}) != len(authority_constraints):
            raise RuntimeInitializationError(
                "authority binding constraints must be unique",
                "INVALID_RUNTIME_POLICY",
            )
        if len({item.key for item in capability_constraints}) != len(capability_constraints):
            raise RuntimeInitializationError(
                "capability binding constraints must be unique",
                "INVALID_RUNTIME_POLICY",
            )
        if not isinstance(self.authority_target, TargetSelector):
            raise RuntimeInitializationError(
                "runtime binding requires an exact authority target",
                "INVALID_RUNTIME_POLICY",
            )
        object.__setattr__(self, "command_name", _runtime_identifier(self.command_name, "command_name", route=True))
        object.__setattr__(self, "skill_slug", _runtime_identifier(self.skill_slug, "skill_slug", route=True))
        object.__setattr__(self, "authority_operation", _runtime_identifier(self.authority_operation, "authority_operation"))
        object.__setattr__(self, "capability_id", _runtime_identifier(self.capability_id, "capability_id"))
        object.__setattr__(self, "capability_operation", _runtime_identifier(self.capability_operation, "capability_operation"))
        object.__setattr__(self, "authority_constraints", authority_constraints)
        object.__setattr__(self, "capability_constraints", capability_constraints)

    def to_dict(self) -> dict[str, object]:
        return {
            "command_name": self.command_name,
            "skill_slug": self.skill_slug,
            "authority_target": self.authority_target.to_dict(),
            "authority_operation": self.authority_operation,
            "capability_id": self.capability_id,
            "capability_operation": self.capability_operation,
            "authority_constraints": [item.to_dict() for item in self.authority_constraints],
            "capability_constraints": [item.to_dict() for item in self.capability_constraints],
        }


@dataclass(frozen=True, slots=True)
class RuntimeExecutionPolicy:
    policy_id: str
    policy_version: str
    bindings: tuple[RuntimePolicyBinding, ...]

    def __post_init__(self) -> None:
        policy_id = _runtime_identifier(self.policy_id, "policy_id")
        policy_version = str(self.policy_version).strip()
        bindings = tuple(sorted(tuple(self.bindings), key=lambda item: (item.command_name, item.skill_slug)))
        keys = tuple((item.command_name, item.skill_slug) for item in bindings)
        if not policy_version or not bindings or len(set(keys)) != len(keys):
            raise RuntimeInitializationError(
                "runtime execution policy requires unique finite bindings",
                "INVALID_RUNTIME_POLICY",
                {"policy_id": policy_id},
            )
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "bindings", bindings)

    def binding_for(self, command_name: str, skill_slug: str) -> RuntimePolicyBinding | None:
        key = (str(command_name).strip().casefold(), str(skill_slug).strip().casefold())
        return next((item for item in self.bindings if (item.command_name, item.skill_slug) == key), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "bindings": [item.to_dict() for item in self.bindings],
        }


@dataclass(frozen=True, slots=True)
class RuntimeOperationResult:
    state: LifecycleState
    output: str
    reason_code: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        state = LifecycleState(self.state)
        if state not in {
            LifecycleState.WAITING,
            LifecycleState.COMPLETED,
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
            LifecycleState.TIMED_OUT,
        }:
            raise RuntimeInitializationError(
                "runtime operation returned an unsupported lifecycle state",
                "INVALID_OPERATION_RESULT",
                {"state": state.value},
            )
        reason_code = str(self.reason_code).strip()
        evidence_refs = tuple(sorted({str(item).strip() for item in self.evidence_refs if str(item).strip()}))
        if not reason_code:
            raise RuntimeInitializationError(
                "runtime operation result requires a reason code",
                "INVALID_OPERATION_RESULT",
            )
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "output", str(self.output))
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "evidence_refs", evidence_refs)


class SkillRegistry(ISkillRegistry):
    def __init__(
        self,
        manifest_repository: ManifestRepository,
        skill_repository: SkillSourceRepository,
        command_routes: dict[str, str] | None = None,
    ):
        self._manifest_repository = manifest_repository
        self._skill_repository = skill_repository
        self._command_routes = command_routes or DEFAULT_COMMAND_ROUTES
        self._cache: dict[str, object] | None = None

    def load_skills(self) -> tuple:
        if self._cache is None:
            manifest = self._manifest_repository.load_manifest()
            commands = tuple(manifest.get("commands", []))
            skill_map = {}
            for manifest_entry in manifest.get("skills", []):
                slug = manifest_entry.get("slug", "")
                skill_path = self._skill_repository.get_skill_path(slug)
                frontmatter = self._skill_repository.parse_frontmatter(skill_path)
                mapped_commands = tuple(
                    command
                    for command in commands
                    if self._command_routes.get(command, command) == slug
                )
                skill_map[slug] = SkillFactory.create(manifest_entry, frontmatter, skill_path, mapped_commands)
            self._cache = skill_map
        return tuple(self._cache.values())

    def get_skill(self, slug: str):
        self.load_skills()
        assert self._cache is not None
        return self._cache.get(slug)


class RouterService(IRouterService):
    def __init__(self, skill_registry: ISkillRegistry, command_routes: dict[str, str] | None = None):
        self._skill_registry = skill_registry
        self._command_routes = command_routes or DEFAULT_COMMAND_ROUTES

    def route(self, command: Command, context: ContextPackage) -> RouteDecision:
        skill_slug = self._command_routes.get(command.name, "conductor")
        skill = self._skill_registry.get_skill(skill_slug) or self._skill_registry.get_skill("conductor")
        if skill is None:
            raise ValueError(f"Unable to resolve skill for command '{command.name}'")

        governance_required = skill.slug in {"dagger", "cipher", "the-steward", "the-governor"}
        reason = (
            f"{context.adapter_name} command '{command.name}' maps to skill '{skill.slug}' via runtime router"
        )
        return RouteDecision(
            command_name=command.name,
            skill_slug=skill.slug,
            governance_required=governance_required,
            reason=reason,
            metadata={"skill_path": str(skill.skill_path)},
        )


class ContextAssembler:
    def __init__(self, manifest_repository: ManifestRepository):
        self._manifest_repository = manifest_repository

    def assemble(self, adapter: IIDEAdapter, prompt: str, metadata: dict | None = None) -> ContextPackage:
        context = adapter.provide_context(prompt, metadata)
        merged_metadata = dict(context.metadata)
        merged_metadata.setdefault("governance_validated", False)
        merged_metadata.setdefault("destructive_validated", False)
        merged_metadata.setdefault("dry_run", False)
        return ContextPackage(
            adapter_name=context.adapter_name,
            prompt=context.prompt,
            project_root=context.project_root,
            available_commands=context.available_commands,
            manifest_version=context.manifest_version,
            metadata=merged_metadata,
        )


class GovernanceValidator(IGovernanceValidator):
    def __init__(self, rules: Iterable[GovernanceRule] | None = None):
        self._rules = tuple(
            rules
            or (
                GovernanceRule(
                    name="destructive-skill-approval",
                    description="Destructive skills require explicit validation and dry-run mode.",
                    skill_slugs=("dagger",),
                    command_names=("resilience-check", "dagger"),
                    validator_key="destructive_validated",
                ),
                GovernanceRule(
                    name="high-risk-skill-approval",
                    description="High-risk security and governance skills require explicit validation.",
                    skill_slugs=("cipher", "the-steward", "the-governor"),
                    command_names=("security-check",),
                    validator_key="governance_validated",
                ),
            )
        )

    def validate(self, decision: RouteDecision, context: ContextPackage) -> ValidationResult:
        triggered_rules: list[str] = []
        reasons: list[str] = []
        for rule in self._rules:
            skill_match = decision.skill_slug in rule.skill_slugs
            command_match = decision.command_name in rule.command_names
            if not (skill_match or command_match):
                continue

            triggered_rules.append(rule.name)
            if rule.validator_key and not context.metadata.get(rule.validator_key):
                reasons.append(f"{rule.name} blocked execution")
            if rule.name == "destructive-skill-approval" and not context.metadata.get("dry_run"):
                reasons.append("destructive execution requires dry-run mode")

        if reasons:
            return ValidationResult(
                allowed=False,
                status="BLOCKED_PENDING_VALIDATION",
                reasons=tuple(dict.fromkeys(reasons)),
                evaluated_rules=tuple(triggered_rules),
            )

        status = "APPROVED" if triggered_rules else "NOT_REQUIRED"
        return ValidationResult(
            allowed=True,
            status=status,
            reasons=(),
            evaluated_rules=tuple(triggered_rules),
        )


class InMemoryAuditSink(IAuditSink):
    def __init__(self):
        self.entries: list[dict[str, object]] = []

    def write(self, entry: dict[str, object]) -> str:
        stored = deepcopy(dict(entry))
        entry_id = str(stored.get("event_id") or _stable_id("audit", stored))
        stored["id"] = entry_id
        self.entries.append(stored)
        return entry_id


class AuditLogger:
    def __init__(self, sink: IAuditSink):
        self._sink = sink

    def _write(self, entry: dict[str, object], related_id: str) -> str:
        try:
            return self._sink.write(deepcopy(entry))
        except RuntimeAuditError:
            raise
        except Exception as exc:
            raise RuntimeAuditError(
                "runtime audit sink write failed",
                "AUDIT_SINK_FAILURE",
                {"related_id": related_id},
            ) from exc

    def record_event(self, event: RuntimeAuditEvent) -> str:
        self._write(event.to_dict(), event.event_id)
        return event.event_id

    def record(self, result: ExecutionResult, context: ContextPackage) -> str:
        entry = {
            "adapter": result.adapter_name,
            "command": result.command_name,
            "route": result.route.skill_slug,
            "validation": result.validation.status,
            "success": result.success,
            "run_id": result.run_identity.run_id if result.run_identity else None,
            "authority_mode": result.authority_mode,
            "lifecycle_state": result.lifecycle_state,
            "project_root": str(context.project_root),
        }
        return self._write(entry, result.run_identity.run_id if result.run_identity else result.command_name)


def _compatibility_bindings() -> tuple[RuntimePolicyBinding, ...]:
    return tuple(sorted((
        RuntimePolicyBinding(
            command_name=command_name,
            skill_slug=skill_slug,
            authority_target=TargetSelector(f"specialist:{skill_slug}"),
            authority_operation="execute",
            capability_id=f"runtime.execute.{skill_slug}",
            capability_operation="execute",
        )
        for command_name, skill_slug in DEFAULT_COMMAND_ROUTES.items()
    ), key=lambda item: (item.command_name, item.skill_slug)))


@dataclass(frozen=True, slots=True)
class RuntimeComposition:
    mode: AuthorityMode
    run_identity: RunIdentity
    root_authority: AuthorityScope
    capability_manifest: RuntimeCapabilityManifest
    authority_evaluator: IAuthorityEvaluator
    capability_resolver: ICapabilityResolver
    lifecycle_controller: ILifecycleController
    delegation_validator: IDelegationValidator
    audit_logger: AuditLogger
    policy: RuntimeExecutionPolicy
    delegation_decision_id: str | None = None

    def __post_init__(self) -> None:
        try:
            mode = AuthorityMode(self.mode)
        except (TypeError, ValueError) as exc:
            raise RuntimeInitializationError(
                "authority mode must be explicit",
                "INVALID_AUTHORITY_MODE",
            ) from exc
        required = (
            ("run_identity", self.run_identity, RunIdentity),
            ("root_authority", self.root_authority, AuthorityScope),
            ("capability_manifest", self.capability_manifest, RuntimeCapabilityManifest),
            ("authority_evaluator", self.authority_evaluator, IAuthorityEvaluator),
            ("capability_resolver", self.capability_resolver, ICapabilityResolver),
            ("lifecycle_controller", self.lifecycle_controller, ILifecycleController),
            ("delegation_validator", self.delegation_validator, IDelegationValidator),
            ("audit_logger", self.audit_logger, AuditLogger),
            ("policy", self.policy, RuntimeExecutionPolicy),
        )
        invalid = next((name for name, value, expected in required if not isinstance(value, expected)), None)
        if invalid:
            raise RuntimeInitializationError(
                "runtime composition is incomplete",
                "MISSING_ACTIVE_CONFIGURATION",
                {"field": invalid},
            )
        if self.capability_manifest.run_identity != self.run_identity:
            raise RuntimeInitializationError(
                "capability manifest does not belong to the runtime run",
                "RUN_MANIFEST_MISMATCH",
                {"run_id": self.run_identity.run_id},
            )
        if self.root_authority.provenance != self.capability_manifest.provenance:
            raise RuntimeInitializationError(
                "authority and capability provenance must match",
                "PROVENANCE_MISMATCH",
                {"run_id": self.run_identity.run_id},
            )
        mismatched_grant = next(
            (grant for grant in self.capability_manifest.grants if grant.provenance != self.capability_manifest.provenance),
            None,
        )
        if mismatched_grant is not None:
            raise RuntimeInitializationError(
                "capability grant provenance must match the manifest",
                "CAPABILITY_GRANT_PROVENANCE_MISMATCH",
                {
                    "capability_id": mismatched_grant.capability.capability_id,
                    "manifest_id": self.capability_manifest.manifest_id,
                },
            )
        if (
            self.policy.policy_version != self.capability_manifest.policy_version
            or self.policy.policy_version != self.root_authority.provenance.policy_version
        ):
            raise RuntimeInitializationError(
                "runtime policy versions do not match",
                "POLICY_VERSION_MISMATCH",
                {"policy_id": self.policy.policy_id},
            )
        grants_by_id = {
            grant.capability.capability_id: grant
            for grant in self.capability_manifest.grants
        }
        owner_mismatch = next(
            (
                (binding, grants_by_id[binding.capability_id])
                for binding in self.policy.bindings
                if binding.capability_id in grants_by_id
                and grants_by_id[binding.capability_id].capability.owner != binding.skill_slug
            ),
            None,
        )
        if owner_mismatch is not None:
            binding, grant = owner_mismatch
            raise RuntimeInitializationError(
                "runtime binding skill must own its capability",
                "CAPABILITY_OWNER_MISMATCH",
                {
                    "capability_id": binding.capability_id,
                    "capability_owner": grant.capability.owner,
                    "skill_slug": binding.skill_slug,
                },
            )

        decision_id = self.delegation_decision_id.strip() if self.delegation_decision_id else None
        if self.run_identity.parent_run_id:
            provenance = self.root_authority.provenance
            if (
                provenance.source_type is not ProvenanceSource.ACCEPTED_DELEGATION
                or provenance.parent_run_id != self.run_identity.parent_run_id
                or provenance.parent_decision_id != decision_id
                or self.root_authority.parent_scope_id is None
            ):
                raise RuntimeInitializationError(
                    "delegated runtime composition has invalid parent identity",
                    "INVALID_DELEGATED_COMPOSITION",
                    {"run_id": self.run_identity.run_id},
                )
        elif (
            decision_id is not None
            or self.root_authority.parent_scope_id is not None
            or self.root_authority.provenance.source_type
            not in {ProvenanceSource.TRUSTED_COMPOSITION, ProvenanceSource.TRUSTED_REPOSITORY_POLICY}
        ):
            raise RuntimeInitializationError(
                "root runtime composition requires trusted root authority",
                "UNTRUSTED_RUNTIME_COMPOSITION",
                {"run_id": self.run_identity.run_id},
            )

        if mode is AuthorityMode.COMPATIBILITY:
            if self.policy.policy_id != COMPATIBILITY_POLICY_ID or self.policy.bindings != _compatibility_bindings():
                raise RuntimeInitializationError(
                    "compatibility mode requires the finite repository policy",
                    "INVALID_COMPATIBILITY_POLICY",
                )
        elif self.policy.policy_id == COMPATIBILITY_POLICY_ID:
            raise RuntimeInitializationError(
                "compatibility policy requires explicit compatibility mode",
                "INVALID_AUTHORITY_MODE",
            )
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "delegation_decision_id", decision_id)


def build_compatibility_composition(
    skill_registry: ISkillRegistry,
    audit_sink: IAuditSink,
    *,
    run_id: str,
) -> RuntimeComposition:
    if not isinstance(skill_registry, ISkillRegistry) or not isinstance(audit_sink, IAuditSink):
        raise RuntimeInitializationError(
            "compatibility composition requires trusted runtime services",
            "MISSING_ACTIVE_CONFIGURATION",
        )
    provenance = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        COMPATIBILITY_POLICY_ID,
        COMPATIBILITY_POLICY_VERSION,
        "runtime-composition",
    )
    bindings = _compatibility_bindings()
    policy = RuntimeExecutionPolicy(COMPATIBILITY_POLICY_ID, COMPATIBILITY_POLICY_VERSION, bindings)
    scope = AuthorityScope(
        "runtime.compatibility.root",
        tuple({item.authority_target for item in bindings}),
        ("execute",),
        (),
        provenance,
    )
    resolver = CapabilityResolver()
    grants = tuple(
        RuntimeCapabilityGrant(
            RuntimeCapability(
                f"runtime.execute.{skill_slug}",
                skill_slug,
                ("execute",),
                f"Execute the supported {skill_slug} runtime route.",
            ),
            ("execute",),
            provenance,
        )
        for skill_slug in sorted(set(DEFAULT_COMMAND_ROUTES.values()))
    )
    manifest = resolver.build_manifest(
        run_id,
        grants,
        provenance,
        manifest_id="runtime.compatibility.manifest",
        policy_version=COMPATIBILITY_POLICY_VERSION,
    )
    authority_evaluator = AuthorityEvaluator()
    lifecycle_controller = LifecycleController()
    delegation_validator = DelegationValidator(
        authority_evaluator,
        resolver,
        skill_registry,
        DelegationPolicy(
            "runtime.compatibility.delegation",
            COMPATIBILITY_POLICY_VERSION,
            1,
            allowed_context_keys=("destructive_validated", "dry_run", "governance_validated"),
            sensitive_context_keys=("credential", "secret", "token"),
        ),
    )
    return RuntimeComposition(
        AuthorityMode.COMPATIBILITY,
        manifest.run_identity,
        scope,
        manifest,
        authority_evaluator,
        resolver,
        lifecycle_controller,
        delegation_validator,
        AuditLogger(audit_sink),
        policy,
    )


class RuntimeExecutor(IRuntimeExecutor):
    def __init__(
        self,
        skill_registry: ISkillRegistry,
        router: IRouterService,
        governance: IGovernanceValidator,
        context_assembler: ContextAssembler,
        composition: RuntimeComposition,
        operation: Callable[[str, RouteDecision, ValidationResult], RuntimeOperationResult] | None = None,
    ):
        if not isinstance(composition, RuntimeComposition):
            raise RuntimeInitializationError(
                "runtime executor requires explicit trusted composition",
                "MISSING_ACTIVE_CONFIGURATION",
            )
        if operation is not None and not callable(operation):
            raise RuntimeInitializationError(
                "runtime operation must be callable",
                "INVALID_OPERATION",
            )
        self._skill_registry = skill_registry
        self._router = router
        self._governance = governance
        self._context_assembler = context_assembler
        self._composition = composition
        self._operation = operation or self._default_operation
        self._lifecycle_snapshots: dict[str, LifecycleSnapshot] = {}
        self._last_lifecycle_snapshot: LifecycleSnapshot | None = None

    @property
    def composition(self) -> RuntimeComposition:
        return self._composition

    @property
    def last_lifecycle_snapshot(self) -> LifecycleSnapshot | None:
        return self._last_lifecycle_snapshot

    def execute(self, adapter: IIDEAdapter, prompt: str, metadata: dict | None = None) -> ExecutionResult:
        return self._execute(adapter, prompt, metadata, self._composition, ())

    def execute_delegation_request(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        request: DelegationRequest,
        metadata: dict | None = None,
    ) -> ExecutionResult:
        resolution = self._composition.delegation_validator.validate(
            request,
            self._composition.root_authority,
            self._composition.capability_manifest,
        )
        return self.execute_delegated(adapter, prompt, resolution, metadata)

    def execute_delegated(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        resolution: DelegationResolution,
        metadata: dict | None = None,
    ) -> ExecutionResult:
        if not isinstance(resolution, DelegationResolution):
            raise DelegationRejectedError(
                "child execution requires a delegation resolution",
                "INVALID_REQUEST",
            )
        event = delegation_accepted_event(resolution) if resolution.decision.allowed else delegation_rejected_event(resolution)
        delegation_event_id = self._composition.audit_logger.record_event(event)
        if not resolution.decision.allowed:
            raise DelegationRejectedError(
                "rejected delegation cannot create a child run",
                resolution.decision.reason_code,
                {"decision_id": resolution.decision.decision_id},
            )

        decision = resolution.decision
        scope = resolution.effective_scope
        manifest = resolution.effective_manifest
        assert scope is not None and manifest is not None
        if (
            decision.parent_run_id != self._composition.run_identity.run_id
            or decision.child_run_id != manifest.run_identity.run_id
            or manifest.run_identity.parent_run_id != decision.parent_run_id
            or scope.parent_scope_id != self._composition.root_authority.scope_id
            or scope.provenance.parent_decision_id != decision.decision_id
        ):
            failure = initialization_failure_event(
                _stable_id(
                    "event",
                    {"type": "INITIALIZATION_FAILED", "decision_id": decision.decision_id, "reason": "INVALID_PARENT"},
                ),
                decision.parent_run_id,
                decision.decision_id,
                "INVALID_PARENT",
            )
            self._composition.audit_logger.record_event(failure)
            raise DelegationRejectedError(
                "accepted delegation does not belong to this parent run",
                "INVALID_PARENT",
                {"decision_id": decision.decision_id},
            )

        child_composition = RuntimeComposition(
            self._composition.mode,
            manifest.run_identity,
            scope,
            manifest,
            self._composition.authority_evaluator,
            self._composition.capability_resolver,
            self._composition.lifecycle_controller,
            self._composition.delegation_validator,
            self._composition.audit_logger,
            self._composition.policy,
            decision.decision_id,
        )
        allowed_keys = {item.casefold() for item in decision.effective_context_keys}
        child_metadata = {
            str(key): value
            for key, value in (metadata or {}).items()
            if str(key).casefold() in allowed_keys
        }
        return self._execute(adapter, prompt, child_metadata, child_composition, (delegation_event_id,))

    def _execute(
        self,
        adapter: IIDEAdapter,
        prompt: str,
        metadata: dict | None,
        composition: RuntimeComposition,
        initial_event_ids: tuple[str, ...],
    ) -> ExecutionResult:
        snapshot, event_ids = self._initialize(composition, initial_event_ids)
        context = self._context_assembler.assemble(adapter, prompt, metadata)
        command = adapter.parse_command(prompt, metadata)
        decision = self._router.route(command, context)
        binding = composition.policy.binding_for(decision.command_name, decision.skill_slug)
        if binding is None:
            error = RuntimeBindingError(
                "routed work has no trusted runtime binding",
                "MISSING_RUNTIME_BINDING",
                {"command": decision.command_name, "skill": decision.skill_slug},
            )
            validation = ValidationResult(False, "RUNTIME_BINDING_DENIED", (error.reason_code,), ())
            output = f"{adapter.adapter_name} adapter denied unbound runtime route '{decision.command_name}'"
            return self._block(
                adapter.adapter_name,
                command,
                decision,
                validation,
                output,
                context,
                composition,
                snapshot,
                event_ids,
                None,
                None,
                error.reason_code,
            )

        authority_decision_id = _stable_id(
            "authority-decision",
            {
                "run_id": composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "scope_id": composition.root_authority.scope_id,
            },
        )
        authority_decision = composition.authority_evaluator.evaluate(
            composition.root_authority,
            binding.authority_target,
            binding.authority_operation,
            binding.authority_constraints,
            run_id=composition.run_identity.run_id,
            decision_id=authority_decision_id,
        )
        if authority_decision.run_id != composition.run_identity.run_id:
            raise RuntimeInitializationError(
                "authority evaluator returned the wrong run identity",
                "AUTHORITY_DECISION_MISMATCH",
            )
        authority_event = authority_decision_event(
            _stable_id("event", {"type": "AUTHORITY_DECIDED", "decision": authority_decision.to_dict()}),
            authority_decision,
        )
        event_ids.append(composition.audit_logger.record_event(authority_event))
        if not authority_decision.allowed:
            validation = ValidationResult(False, "AUTHORITY_DENIED", (authority_decision.reason_code.value,), ())
            output = f"{adapter.adapter_name} adapter denied runtime authority for '{decision.command_name}'"
            return self._block(
                adapter.adapter_name,
                command,
                decision,
                validation,
                output,
                context,
                composition,
                snapshot,
                event_ids,
                authority_decision.decision_id,
                None,
                authority_decision.reason_code.value,
            )

        capability_decision_id = _stable_id(
            "capability-decision",
            {
                "run_id": composition.run_identity.run_id,
                "binding": binding.to_dict(),
                "manifest_id": composition.capability_manifest.manifest_id,
            },
        )
        capability_decision = composition.capability_resolver.evaluate(
            composition.capability_manifest,
            binding.capability_id,
            binding.capability_operation,
            binding.capability_constraints,
            decision_id=capability_decision_id,
        )
        if capability_decision.run_id != composition.run_identity.run_id:
            raise RuntimeInitializationError(
                "capability resolver returned the wrong run identity",
                "CAPABILITY_DECISION_MISMATCH",
            )
        capability_event = capability_decision_event(
            _stable_id("event", {"type": "CAPABILITY_DECIDED", "decision": capability_decision.to_dict()}),
            capability_decision,
        )
        event_ids.append(composition.audit_logger.record_event(capability_event))
        if not capability_decision.allowed:
            validation = ValidationResult(False, "CAPABILITY_DENIED", (capability_decision.reason_code.value,), ())
            output = f"{adapter.adapter_name} adapter denied runtime capability for '{decision.command_name}'"
            return self._block(
                adapter.adapter_name,
                command,
                decision,
                validation,
                output,
                context,
                composition,
                snapshot,
                event_ids,
                authority_decision.decision_id,
                capability_decision.decision_id,
                capability_decision.reason_code.value,
            )

        validation = self._governance.validate(decision, context)
        if not validation.allowed:
            output = self._build_output(adapter.adapter_name, decision, validation)
            return self._block(
                adapter.adapter_name,
                command,
                decision,
                validation,
                output,
                context,
                composition,
                snapshot,
                event_ids,
                authority_decision.decision_id,
                capability_decision.decision_id,
                "GOVERNANCE_DENIED",
            )

        activation = self._signal(
            composition,
            snapshot,
            LifecycleSignalType.ACTIVATE,
            LifecycleState.ACTIVE,
            "RUNTIME_ACTIVATED",
            "",
            (authority_event.event_id, capability_event.event_id),
        )
        snapshot = self._transition(composition, snapshot, activation, event_ids)

        try:
            operation_result = self._operation(adapter.adapter_name, decision, validation)
            if not isinstance(operation_result, RuntimeOperationResult):
                raise TypeError("runtime operation must return RuntimeOperationResult")
        except Exception as exc:
            operation_result = RuntimeOperationResult(
                LifecycleState.FAILED,
                "runtime operation failed",
                "RUNTIME_EXCEPTION",
                (type(exc).__name__,),
            )

        signal_type = {
            LifecycleState.WAITING: LifecycleSignalType.WAIT,
            LifecycleState.COMPLETED: LifecycleSignalType.COMPLETE,
            LifecycleState.FAILED: LifecycleSignalType.FAIL,
            LifecycleState.CANCELLED: LifecycleSignalType.CANCEL,
            LifecycleState.TIMED_OUT: LifecycleSignalType.TIME_OUT,
        }[operation_result.state]
        outcome_signal = self._signal(
            composition,
            snapshot,
            signal_type,
            operation_result.state,
            operation_result.reason_code,
            operation_result.output,
            tuple(event_ids) + operation_result.evidence_refs,
        )
        snapshot = self._transition(composition, snapshot, outcome_signal, event_ids)
        if snapshot.state.terminal:
            event_ids.append(composition.audit_logger.record_event(terminal_result_event(snapshot)))
        return self._result(
            adapter.adapter_name,
            command,
            decision,
            validation,
            operation_result.output,
            context,
            composition,
            snapshot,
            event_ids,
            authority_decision.decision_id,
            capability_decision.decision_id,
        )

    def _initialize(
        self,
        composition: RuntimeComposition,
        initial_event_ids: tuple[str, ...],
    ) -> tuple[LifecycleSnapshot, list[str]]:
        run_id = composition.run_identity.run_id
        existing = self._lifecycle_snapshots.get(run_id)
        if existing is not None:
            raise RuntimeInitializationError(
                "runtime run identity is already initialized",
                "RUN_ALREADY_INITIALIZED",
                {"run_id": run_id, "current_state": existing.state.value},
            )
        event_ids = list(initial_event_ids)
        try:
            if composition.run_identity.parent_run_id is None:
                validated_scope = composition.authority_evaluator.validate_root(composition.root_authority)
                if validated_scope != composition.root_authority:
                    raise RuntimeInitializationError(
                        "authority evaluator changed trusted root authority",
                        "ROOT_AUTHORITY_MISMATCH",
                    )
            rebuilt_manifest = composition.capability_resolver.build_manifest(
                composition.run_identity.run_id,
                composition.capability_manifest.grants,
                composition.capability_manifest.provenance,
                manifest_id=composition.capability_manifest.manifest_id,
                policy_version=composition.capability_manifest.policy_version,
            )
            if rebuilt_manifest != composition.capability_manifest:
                raise RuntimeInitializationError(
                    "capability resolver changed the trusted manifest",
                    "CAPABILITY_MANIFEST_MISMATCH",
                )
            initialized = composition.lifecycle_controller.initialize(composition.run_identity.run_id)
            if initialized.run_identity.run_id != composition.run_identity.run_id or initialized.state is not LifecycleState.INITIALIZING:
                raise RuntimeInitializationError(
                    "lifecycle controller returned invalid initialization state",
                    "LIFECYCLE_INITIALIZATION_MISMATCH",
                )
            snapshot = LifecycleSnapshot(composition.run_identity, LifecycleState.INITIALIZING)
            self._lifecycle_snapshots[run_id] = snapshot
            self._last_lifecycle_snapshot = snapshot
            if composition.run_identity.parent_run_id is None:
                root_event = root_authority_event(
                    _stable_id(
                        "event",
                        {"type": "ROOT_AUTHORITY_CREATED", "run_id": composition.run_identity.run_id, "scope": composition.root_authority.to_dict()},
                    ),
                    composition.run_identity.run_id,
                    composition.root_authority,
                )
                event_ids.append(composition.audit_logger.record_event(root_event))
            manifest_event = capability_manifest_event(
                _stable_id(
                    "event",
                    {"type": "CAPABILITY_MANIFEST_CREATED", "manifest": composition.capability_manifest.to_dict()},
                ),
                composition.capability_manifest,
            )
            event_ids.append(composition.audit_logger.record_event(manifest_event))
            return snapshot, event_ids
        except RuntimeAuditError:
            raise
        except Exception as exc:
            error = exc if isinstance(exc, RuntimeContractError) else RuntimeInitializationError(
                "trusted runtime initialization failed",
                "RUNTIME_INITIALIZATION_FAILED",
                {"error_type": type(exc).__name__},
            )
            failure = initialization_failure_event(
                _stable_id(
                    "event",
                    {
                        "type": "INITIALIZATION_FAILED",
                        "run_id": composition.run_identity.run_id,
                        "reason": error.reason_code,
                    },
                ),
                composition.run_identity.run_id,
                composition.policy.policy_id,
                error.reason_code,
            )
            composition.audit_logger.record_event(failure)
            raise error

    def _block(
        self,
        adapter_name: str,
        command: Command,
        route: RouteDecision,
        validation: ValidationResult,
        output: str,
        context: ContextPackage,
        composition: RuntimeComposition,
        snapshot: LifecycleSnapshot,
        event_ids: list[str],
        authority_decision_id: str | None,
        capability_decision_id: str | None,
        reason_code: str,
    ) -> ExecutionResult:
        block_signal = self._signal(
            composition,
            snapshot,
            LifecycleSignalType.BLOCK,
            LifecycleState.BLOCKED,
            reason_code,
            output,
            tuple(event_ids),
        )
        snapshot = self._transition(composition, snapshot, block_signal, event_ids)
        event_ids.append(composition.audit_logger.record_event(terminal_result_event(snapshot)))
        return self._result(
            adapter_name,
            command,
            route,
            validation,
            output,
            context,
            composition,
            snapshot,
            event_ids,
            authority_decision_id,
            capability_decision_id,
        )

    def _transition(
        self,
        composition: RuntimeComposition,
        previous: LifecycleSnapshot,
        signal: LifecycleSignal,
        event_ids: list[str],
    ) -> LifecycleSnapshot:
        try:
            current = composition.lifecycle_controller.apply(previous, signal)
        except RuntimeContractError as error:
            rejection = lifecycle_rejection_event(previous, signal, error)
            event_ids.append(composition.audit_logger.record_event(rejection))
            self._lifecycle_snapshots[previous.run_identity.run_id] = previous
            self._last_lifecycle_snapshot = previous
            raise
        self._lifecycle_snapshots[current.run_identity.run_id] = current
        self._last_lifecycle_snapshot = current
        transition = lifecycle_transition_event(previous, signal, current)
        event_ids.append(composition.audit_logger.record_event(transition))
        return current

    @staticmethod
    def _signal(
        composition: RuntimeComposition,
        snapshot: LifecycleSnapshot,
        signal_type: LifecycleSignalType,
        requested_state: LifecycleState,
        reason_code: str,
        output: str,
        evidence_refs: tuple[str, ...],
    ) -> LifecycleSignal:
        terminal_result = (
            StructuredTerminalResult(
                composition.run_identity.run_id,
                requested_state,
                reason_code,
                output,
                evidence_refs,
            )
            if requested_state.terminal
            else None
        )
        payload = {
            "run_id": composition.run_identity.run_id,
            "signal_type": signal_type.value,
            "expected_state": snapshot.state.value,
            "requested_state": requested_state.value,
            "reason_code": reason_code,
            "output": output,
            "evidence_refs": list(evidence_refs),
        }
        return LifecycleSignal(
            _stable_id("lifecycle-signal", payload),
            composition.run_identity.run_id,
            signal_type,
            snapshot.state,
            requested_state,
            reason_code,
            "runtime-executor",
            composition.root_authority.provenance,
            evidence_refs,
            terminal_result,
        )

    @staticmethod
    def _default_operation(
        adapter_name: str,
        decision: RouteDecision,
        validation: ValidationResult,
    ) -> RuntimeOperationResult:
        return RuntimeOperationResult(
            LifecycleState.COMPLETED,
            RuntimeExecutor._build_output(adapter_name, decision, validation),
            "EXECUTION_COMPLETED",
        )

    def _result(
        self,
        adapter_name: str,
        command: Command,
        route: RouteDecision,
        validation: ValidationResult,
        output: str,
        context: ContextPackage,
        composition: RuntimeComposition,
        snapshot: LifecycleSnapshot,
        event_ids: list[str],
        authority_decision_id: str | None,
        capability_decision_id: str | None,
    ) -> ExecutionResult:
        common = dict(
            success=snapshot.state is LifecycleState.COMPLETED,
            adapter_name=adapter_name,
            command_name=command.name,
            route=route,
            validation=validation,
            output=output,
            run_identity=composition.run_identity,
            authority_decision_id=authority_decision_id,
            capability_decision_id=capability_decision_id,
            authority_mode=composition.mode.value,
            lifecycle_state=snapshot.state.value,
            terminal_result=composition.lifecycle_controller.terminal_result(snapshot),
            runtime_audit_event_ids=tuple(event_ids),
        )
        provisional = ExecutionResult(audit_entry_id="", **common)
        audit_entry_id = composition.audit_logger.record(provisional, context)
        return ExecutionResult(audit_entry_id=audit_entry_id, **common)

    @staticmethod
    def _build_output(adapter_name: str, decision: RouteDecision, validation: ValidationResult) -> str:
        if validation.allowed:
            return (
                f"{adapter_name} adapter routed '{decision.command_name}' to '{decision.skill_slug}' "
                f"with governance status {validation.status}"
            )
        return (
            f"{adapter_name} adapter blocked '{decision.command_name}' for '{decision.skill_slug}' "
            f"with governance status {validation.status}"
        )
