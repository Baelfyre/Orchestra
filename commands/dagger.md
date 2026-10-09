---
name: dagger
description: "Run controlled pressure fuzzing, destructive local failure tests, and negative validations."
---
# Dagger Command

You are now invoking the Dagger specialist. Load and follow the exact instructions defined here:

**[skills/dagger/SKILL.md](../skills/dagger/SKILL.md)**

> [!CAUTION]
> **GATED CAPABILITY:** Destructive, fuzz, adversarial, or failure-mode testing requires explicit user approval, non-production scope, and a passing Dagger guardrail result before execution.
>
> You MUST explicitly ask the user for authorization before performing these tests. You MUST fail closed when approval, scope, dry-run, or rollback requirements are missing. Use `scripts/dagger_guardrail.py` as a validation-only gate. Phase 2 allows simulation only and blocks live destructive execution. Do not proceed in a production environment.

Before executing, verify the user's request falls within this specialist's documented scope. If the request is outside scope, do not execute it. Return `SPECIALIST_REROUTE_REQUIRED` and recommend the correct specialist or Conductor.
