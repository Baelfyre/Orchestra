# PROJECT_CONTEXT Decision Prompt

## Purpose

This document defines a Steward-led prompt workflow for deciding whether a repository needs `PROJECT_CONTEXT.md`, what scope it should cover, and whether it should remain advisory or later move toward governed enforcement.

`PROJECT_CONTEXT.md` exists to preserve project-specific context, boundaries, assumptions, constraints, and operating rules so governance review does not rely on guesswork.

This phase is decision support only. It does not make `PROJECT_CONTEXT.md` mandatory, and it does not modify CI enforcement.

## When to Use This Prompt

Use this prompt when a maintainer, team, or AI operator needs help deciding how much project context governance is appropriate.

Typical cases:

- starting a new project
- onboarding a new AI agent or assistant workflow
- preparing a repository for governed workflows
- clarifying project-specific constraints or operating rules
- deciding whether `PROJECT_CONTEXT.md` should stay advisory or become required later

## Initial Context Intake

The Steward should ask for or infer only the minimum context needed to make a recommendation.

Required intake areas:

- project name
- project purpose
- primary users
- repo type
- active development stage
- sensitive areas
- governance needs
- validation expectations
- user preferences or project-specific rules

Suggested intake structure:

- Project Name:
- Project Purpose:
- Primary Users:
- Repo Type: `[personal | internal | open-source | commercial | client-facing | research | other]`
- Active Development Stage: `[prototype | development | staging | release | maintenance]`
- Sensitive Areas: `[none | user data | secrets | destructive operations | compliance-sensitive domain | release-critical paths | other]`
- Governance Needs:
- Validation Expectations:
- User Preferences or Project Rules:

The Steward must clearly separate:

- user-confirmed context
- inferred context
- missing critical context

## Steward Recommendations

After intake, The Steward should provide one or two recommendations.

### Recommendation 1: Lightweight Advisory PROJECT_CONTEXT.md

Use this when the project is low-to-medium risk, still evolving, single-maintainer, exploratory, or not yet ready for strict governance enforcement.

This option should include:

- core project purpose
- scope boundaries
- required documentation expectations
- important constraints
- validation expectations
- project-specific working rules that reduce ambiguity for future agents

This option does not enforce:

- CI failure on missing `PROJECT_CONTEXT.md`
- repository-wide governance blocking outside the current documented operating modes
- release gating by itself

Recommended status:

- advisory by default
- can become a future gate only if maintainers later request it explicitly

### Recommendation 2: Strict Governed PROJECT_CONTEXT.md

Use this only when the repository appears high-risk, multi-agent, compliance-sensitive, destructive, or release-critical.

This option should include:

- everything in the advisory version
- stronger documentation of scope boundaries and protected areas
- validation expectations that must stay aligned with governance review
- role and responsibility notes where governance decisions affect merge or release readiness
- explicit statement of whether future enforcement is desired

This option does not enforce, in this phase:

- immediate CI hard failure
- automatic repository ruleset changes
- mandatory Governor escalation unless enforcement or release gating is later requested

Recommended status:

- advisory now
- candidate for future governed enforcement only when maintainers explicitly request hard-gate planning

## User Direction

The user may accept a recommendation or override it with a custom direction.

Use this section:

- Preferred governance level:
- Required sections:
- Sections to exclude:
- Tone or format:
- Must-follow project rules:
- Should this remain advisory or become enforceable later?

If the user provides custom direction, The Steward should follow that direction unless critical context is still missing.

## Output Options

After the recommendation and user direction step, The Steward may produce one of these outputs:

- `PROJECT_CONTEXT.md` draft
- governance decision summary
- recommended structure only
- follow-up implementation plan
- CI hard-gate proposal, only when explicitly requested

## Guardrails

- Do not invent project facts.
- Ask for missing critical context if needed.
- Clearly separate inferred context from user-confirmed context.
- Do not make `PROJECT_CONTEXT.md` mandatory without explicit user or maintainer approval.
- Do not modify CI in this phase.
- Escalate to The Governor only when enforcement or release gating is requested.

## Reusable Prompt Template

### Steward PROJECT_CONTEXT.md Decision Prompt

**Initial Context:**
[Summarize known project context.]

**Missing Context:**
[List only critical missing items.]

**Recommendation:**

**Option A: Lightweight Advisory Context**
[Explain when it fits, what it includes, and why it should remain advisory by default.]

**Option B: Strict Governed Context**
[Explain only if justified. State what it includes, what it still does not enforce in this phase, and whether it should remain advisory now or become a future gate later.]

**User Direction:**
- Preferred governance level:
- Required sections:
- Sections to exclude:
- Tone or format:
- Must-follow project rules:
- Should this remain advisory or become enforceable later?

**Final Output Requested:**
[`PROJECT_CONTEXT.md` draft / decision summary / structure only / implementation plan.]

## Steward Workflow Summary

The Steward workflow for this phase is:

1. gather or summarize the initial project context
2. identify only critical missing context
3. recommend a lightweight advisory outline by default
4. recommend a stricter governed outline only when justified by project risk or operating model
5. let the user accept, refine, or override the recommendation
6. produce the requested output without changing CI or declaring `PROJECT_CONTEXT.md` mandatory

## Non-goal for This Phase

This prompt does not convert `PROJECT_CONTEXT.md` into a hard governance gate.

Any later move toward strict enforcement should be a separate maintainer decision and may involve The Governor only when enforcement, release gating, or higher-risk governance policy is explicitly requested.
