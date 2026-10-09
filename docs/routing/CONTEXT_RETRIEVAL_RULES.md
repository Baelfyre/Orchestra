# Context Retrieval Rules

## Purpose
To establish a formal context retrieval policy for the Orchestra ecosystem that enables Conductor's router-first execution. This policy ensures only strictly necessary project context is loaded during any given task, mitigating prompt bloat and token-window exhaustion.

## Scope
This policy governs how Conductor and other executing specialists retrieve architectural, governance, and domain-specific context. It applies to all routing decisions and execution phases.

## Retrieval Principle
**Load Only What Is Required.** Conductor must not load full governance files, complete skill files, or full README content by default. Instead, Conductor must assemble the minimal context package necessary to safely execute the requested intent.

## Context Priority Levels
- **Required**: Must be loaded for every task in this category.
- **CONDITIONAL**: Loaded only if specific risk triggers or cross-domain dependencies are met.
- **Optional**: Loaded only upon explicit user request.
- **Avoid unless triggered**: Strictly blocked from loading unless a high-risk or specific operational gate is crossed.

## Context Categories
- **Core manifest context**: Basic plugin definition (e.g., `plugin.json`).
- **Skill index context**: Specialist capabilities and triggers (`SKILL_INDEX.md`).
- **Routing map context**: Cross-domain workflow paths (`ROUTING_MAP.md`).
- **Governance context**: Alignment, scope, legal, and compliance rules (`docs/governance/GOVERNANCE_LAYER.md`).
- **Security context**: RBAC, auth, privacy, and threat models.
- **Documentation context**: Prose, READMEs, SDLC.
- **Testing context**: QA strategy, test plans, and smoke tests.
- **CI/CD context**: Pipeline configuration and release readiness.
- **Database context**: Schema, migrations, ORM, and normalization rules.
- **Frontend/UI context**: Accessibility, layout, and visual hierarchy guidelines.
- **Backend/implementation context**: Layering, OOP boundaries, and refactor patterns.
- **Release/readiness context**: Final deployment checklists and production readiness.
- **Destructive-operation context**: Guardrails, failure modes, and `dagger` execution requirements.

## Task-to-Context Lookup

| Task Type | Required Context | CONDITIONAL Context | Avoid Loading By Default |
|---|---|---|---|
| Simple Q&A | Core manifest context | Skill index context | All other contexts |
| Documentation updates | Documentation context | Governance context | Database, Security, Frontend |
| Code implementation | Backend/implementation context | Database, Frontend/UI context | Governance, Security |
| Refactoring | Backend/implementation context | Testing context | Frontend, Destructive-operation |
| Testing | Testing context | Backend/implementation context | Frontend, Database |
| CI/CD changes | CI/CD context | Security context | Frontend, UI, Documentation |
| Security-sensitive work | Security context, Governance context | Testing context | Frontend/UI, Documentation |
| Governance review | Governance context | Core manifest context | Implementation, Destructive |
| Release readiness | Release/readiness, Governance context | Testing context | Ideation, Prototype context |
| Destructive operations | Destructive-operation context, Security | Governance context | Frontend, Documentation |

## Required Context Rules
- Simple Q&A: Load only the base prompt and core manifest context.
- Documentation updates: Require the documentation context and source material.
- Code implementation: Require the backend/implementation context.
- Refactoring: Require backend/implementation and architecture constraints.
- Testing: Require testing context and validation rules.
- CI/CD changes: Require CI/CD context.
- Security-sensitive work: Require security and governance context.
- Governance review: Require governance context.
- Release readiness: Require release/readiness and full governance context.
- Destructive operations: Require destructive-operation context and safety guardrails.

## CONDITIONAL Context Rules
- If a Code Implementation task touches authentication or database layers, conditionally load Security or Database contexts.
- If a Documentation task involves public release, conditionally load Governance context.
- If a CI/CD change affects deployment targets, conditionally load Security context.

## Avoid-Loading Rules
- Do not load UI/Frontend context during backend refactors.
- Do not load Database context during pure documentation work.
- Do not load Destructive-operation context unless explicit failure-path testing is authorized.
- Do not load full governance context for Ideation or Prototype mode.

## Governance Context Triggers
Conductor will fetch `docs/governance/GOVERNANCE_LAYER.md` when:
- The task is explicitly marked as Audit or Release mode.
- The task touches security-sensitive rules, licensing, or IP.
- The user requests a business alignment or compliance review.

## Destructive Operation Context Triggers
Conductor will fetch destructive testing context only when:
- The user explicitly authorizes negative, fuzz, or chaos testing.
- The `scripts/dagger_guardrail.py` check is passed or simulated.

## Minimal Context Package
By default, the minimal package consists of the Conductor intent classifier and `SKILL_INDEX.md`. The detailed `ROUTING_MAP.md` is added only if the workflow spans multiple domains.

## Non-Goals
- Replacing individual skill execution logic.
- Rewriting established project terminology.
- Altering the strictness of existing safety and governance gates.

## Canonical References
- [Governance Layer](../governance/GOVERNANCE_LAYER.md)
- [Routing Map](../../ROUTING_MAP.md)
- [Skill Index](../../SKILL_INDEX.md)
- [Prompt Load Metrics](../performance/PROMPT_LOAD_METRICS.md)
- [Prompt Load Threshold Policy](../performance/PROMPT_LOAD_THRESHOLD_POLICY.md)

## Retrieval Result
CONTEXT_RETRIEVAL_RULES_DEFINED
