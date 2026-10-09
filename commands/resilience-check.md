---
name: resilience-check
description: "DEPRECATED: Legacy alias for Dagger review. Please use /dagger instead."
---
# Resilience Check Command Alias

This is a legacy alias for Dagger review. Load and follow the exact instructions defined here:

**[skills/dagger/SKILL.md](../skills/dagger/SKILL.md)**

> [!CAUTION]
> **GATED CAPABILITY:** Destructive, fuzz, adversarial, or failure-mode testing requires explicit user approval, non-production scope, and a passing Dagger guardrail result before execution.
>
> You MUST fail closed when approval, scope, dry-run, or rollback requirements are missing. Use `scripts/dagger_guardrail.py` as a validation-only gate. Phase 2 allows simulation only and blocks live destructive execution.
