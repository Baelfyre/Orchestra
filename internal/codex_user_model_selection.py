from __future__ import annotations

from dataclasses import dataclass

from internal.codex_app_server_bridge import CodexAppServerConfig
from internal.codex_app_server_mutation_assessment import CodexMutationAssessmentConfig


MODEL_SELECTION_SOURCE = "USER_CONFIG"
VALIDATION_MODEL_SELECTION_SOURCE = "EXPLICIT_VALIDATION_INPUT"


@dataclass(frozen=True, slots=True)
class CodexUserModelSelection:
    """Trusted user/host configuration for Codex model selection.

    This object is intentionally separate from task input, MCP metadata, and
    specialist guidance. Model choice is configuration, not execution authority.
    """

    model: str
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        model = self.model.strip()
        if not model:
            raise ValueError("Codex model selection must be explicit and non-empty")
        if any(character in model for character in ("\r", "\n", "\x00")):
            raise ValueError("Codex model selection contains an unsafe control character")
        object.__setattr__(self, "model", model)

        if self.reasoning_effort is not None:
            effort = self.reasoning_effort.strip()
            if not effort:
                raise ValueError("reasoning_effort must be non-empty when supplied")
            if any(character in effort for character in ("\r", "\n", "\x00")):
                raise ValueError("reasoning_effort contains an unsafe control character")
            object.__setattr__(self, "reasoning_effort", effort)

    @property
    def evidence_identity(self) -> str:
        return f"codex-model:{self.model}"


def build_read_only_config(
    selection: CodexUserModelSelection,
    *,
    turn_timeout_seconds: int = 180,
    require_clean_worktree: bool = True,
    allowed_specialists: tuple[str, ...] = ("scribe",),
    allowed_commands: tuple[str, ...] = ("review-docs",),
) -> CodexAppServerConfig:
    """Bind an explicit user-selected model to the bounded read-only bridge."""

    return CodexAppServerConfig(
        model=selection.model,
        reasoning_effort=selection.reasoning_effort,
        turn_timeout_seconds=turn_timeout_seconds,
        require_clean_worktree=require_clean_worktree,
        approval_policy="never",
        sandbox_mode="read-only",
        network_access=False,
        allowed_specialists=allowed_specialists,
        allowed_commands=allowed_commands,
    )


def build_mutation_assessment_config(
    selection: CodexUserModelSelection,
    *,
    turn_timeout_seconds: int = 240,
    writable_root: str = "mutation",
    allowed_relative_paths: tuple[str, ...] = ("mutation/target.md",),
    allowed_specialists: tuple[str, ...] = ("ponytail",),
    allowed_commands: tuple[str, ...] = ("ponytail",),
) -> CodexMutationAssessmentConfig:
    """Bind an explicit user-selected model to the bounded E6-style assessment."""

    return CodexMutationAssessmentConfig(
        model=selection.model,
        reasoning_effort=selection.reasoning_effort,
        turn_timeout_seconds=turn_timeout_seconds,
        approval_policy="never",
        sandbox_mode="workspace-write",
        network_access=False,
        writable_root=writable_root,
        allowed_relative_paths=allowed_relative_paths,
        allowed_specialists=allowed_specialists,
        allowed_commands=allowed_commands,
    )
