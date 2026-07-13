from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .models import Command, ContextPackage, ExecutionResult, RouteDecision, Skill, ValidationResult

if TYPE_CHECKING:
    from .authority import AuthorityDecision, AuthorityProvenance, AuthorityScope, Constraint, TargetSelector
    from .capabilities import CapabilityDecision, RuntimeCapabilityGrant, RuntimeCapabilityManifest
    from .delegation import DelegationDecision, DelegationRequest
    from .lifecycle import LifecycleSignal, LifecycleSnapshot, StructuredTerminalResult


class IIDEAdapter(ABC):
    @property
    @abstractmethod
    def adapter_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def provide_context(self, prompt: str, metadata: dict | None = None) -> ContextPackage:
        raise NotImplementedError

    @abstractmethod
    def expose_commands(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def parse_command(self, prompt: str, metadata: dict | None = None) -> Command:
        raise NotImplementedError


class ISkillRegistry(ABC):
    @abstractmethod
    def load_skills(self) -> tuple[Skill, ...]:
        raise NotImplementedError

    @abstractmethod
    def get_skill(self, slug: str) -> Skill | None:
        raise NotImplementedError


class IRouterService(ABC):
    @abstractmethod
    def route(self, command: Command, context: ContextPackage) -> RouteDecision:
        raise NotImplementedError


class IGovernanceValidator(ABC):
    @abstractmethod
    def validate(self, decision: RouteDecision, context: ContextPackage) -> ValidationResult:
        raise NotImplementedError


class IRuntimeExecutor(ABC):
    @abstractmethod
    def execute(self, adapter: IIDEAdapter, prompt: str, metadata: dict | None = None) -> ExecutionResult:
        raise NotImplementedError


class IAuditSink(ABC):
    @abstractmethod
    def write(self, entry: dict) -> str:
        raise NotImplementedError


class IAuthorityEvaluator(ABC):
    @abstractmethod
    def validate_root(self, scope: AuthorityScope) -> AuthorityScope:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        scope: AuthorityScope,
        target: TargetSelector,
        operation: str,
        constraints: tuple[Constraint, ...],
        *,
        run_id: str,
        decision_id: str,
    ) -> AuthorityDecision:
        raise NotImplementedError

    @abstractmethod
    def intersect(
        self,
        parent: AuthorityScope,
        requested: AuthorityScope,
        provenance: AuthorityProvenance,
    ) -> AuthorityScope:
        raise NotImplementedError


class ICapabilityResolver(ABC):
    @abstractmethod
    def build_manifest(
        self,
        run_id: str,
        grants: tuple[RuntimeCapabilityGrant, ...],
        provenance: AuthorityProvenance,
        *,
        manifest_id: str,
        policy_version: str,
    ) -> RuntimeCapabilityManifest:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        manifest: RuntimeCapabilityManifest,
        capability_id: str,
        operation: str,
        constraints: tuple[Constraint, ...],
        *,
        decision_id: str,
    ) -> CapabilityDecision:
        raise NotImplementedError

    @abstractmethod
    def intersect(
        self,
        parent_manifest: RuntimeCapabilityManifest,
        requested_grants: tuple[RuntimeCapabilityGrant, ...],
        child_run_id: str,
        provenance: AuthorityProvenance,
        *,
        manifest_id: str,
    ) -> RuntimeCapabilityManifest:
        raise NotImplementedError


class IDelegationValidator(ABC):
    @abstractmethod
    def validate(self, request: DelegationRequest) -> DelegationDecision:
        raise NotImplementedError


class ILifecycleController(ABC):
    @abstractmethod
    def initialize(self, run_id: str) -> LifecycleSnapshot:
        raise NotImplementedError

    @abstractmethod
    def apply(self, snapshot: LifecycleSnapshot, signal: LifecycleSignal) -> LifecycleSnapshot:
        raise NotImplementedError

    @abstractmethod
    def terminal_result(self, snapshot: LifecycleSnapshot) -> StructuredTerminalResult | None:
        raise NotImplementedError
