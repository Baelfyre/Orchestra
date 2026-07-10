from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .factories import SkillFactory
from .interfaces import IAuditSink, IGovernanceValidator, IIDEAdapter, IRouterService, IRuntimeExecutor, ISkillRegistry
from .models import Command, ContextPackage, ExecutionResult, GovernanceRule, RouteDecision, ValidationResult
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
        self.entries: list[dict] = []

    def write(self, entry: dict) -> str:
        entry_id = str(uuid4())
        stored = dict(entry)
        stored["id"] = entry_id
        self.entries.append(stored)
        return entry_id


class AuditLogger:
    def __init__(self, sink: IAuditSink):
        self._sink = sink

    def record(self, result: ExecutionResult, context: ContextPackage) -> str:
        entry = {
            "adapter": result.adapter_name,
            "command": result.command_name,
            "route": result.route.skill_slug,
            "validation": result.validation.status,
            "success": result.success,
            "project_root": str(context.project_root),
        }
        return self._sink.write(entry)


class RuntimeExecutor(IRuntimeExecutor):
    def __init__(
        self,
        skill_registry: ISkillRegistry,
        router: IRouterService,
        governance: IGovernanceValidator,
        context_assembler: ContextAssembler,
        audit_logger: AuditLogger,
    ):
        self._skill_registry = skill_registry
        self._router = router
        self._governance = governance
        self._context_assembler = context_assembler
        self._audit_logger = audit_logger

    def execute(self, adapter: IIDEAdapter, prompt: str, metadata: dict | None = None) -> ExecutionResult:
        context = self._context_assembler.assemble(adapter, prompt, metadata)
        command = adapter.parse_command(prompt, metadata)
        decision = self._router.route(command, context)
        validation = self._governance.validate(decision, context)
        success = validation.allowed
        output = self._build_output(adapter.adapter_name, decision, validation)
        provisional = ExecutionResult(
            success=success,
            adapter_name=adapter.adapter_name,
            command_name=command.name,
            route=decision,
            validation=validation,
            output=output,
            audit_entry_id="",
        )
        audit_entry_id = self._audit_logger.record(provisional, context)
        return ExecutionResult(
            success=success,
            adapter_name=adapter.adapter_name,
            command_name=command.name,
            route=decision,
            validation=validation,
            output=output,
            audit_entry_id=audit_entry_id,
        )

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
