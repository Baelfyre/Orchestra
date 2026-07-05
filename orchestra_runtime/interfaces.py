from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Command, ContextPackage, ExecutionResult, RouteDecision, Skill, ValidationResult


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
