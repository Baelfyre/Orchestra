# Execution Modes Policy

## Purpose
This document defines the formal execution modes policy for Orchestra. It establishes when the Conductor uses FAST, STANDARD, GOVERNED, AUDIT, or DESTRUCTIVE execution, aligning router-first context loading with governance and safety requirements.

## Scope
This policy applies exclusively to Conductor intent classification, mode selection, and context retrieval. It governs how execution modes escalate based on task complexity and risk.

## Mode Selection Principle
The Conductor must select the execution mode that provides the lowest safe friction. The mode determines which context is loaded, how governance is enforced, and what validation is required before execution.

## Execution Modes

## FAST Mode
- **Purpose**: Rapid execution of simple, low-risk, well-defined tasks.
- **Allowed Task Types**: Syntax formatting, typo fixes, simple UI tweaks, and unambiguous singular code changes.
- **Required Context**: Only the immediate file being edited and the required specialist `SKILL.md` file.
- **Excluded Context**: Full repository index, `GOVERNANCE_LAYER.md`, `ROUTING_MAP.md`, and multi-specialist files.
- **Governance Status**: NOT_REQUIRED.
- **Validation Requirements**: None beyond basic compiler/syntax checks.
- **Escalation Triggers**: If the task requires architectural changes or touches multiple files, escalate to STANDARD mode.
- **Expected Result Status**: Task completed directly.

## STANDARD Mode
- **Purpose**: Normal multi-step or multi-file development and feature implementation.
- **Allowed Task Types**: Feature additions, backend logic, standard UI/UX flows, and refactoring within existing architectural boundaries.
- **Required Context**: Immediate files, relevant specialist files, and architectural dependencies.
- **Excluded Context**: `GOVERNANCE_LAYER.md` (unless explicitly triggered) and `ROUTER_DRY_RUN_TEST_CASES.md`.
- **Governance Status**: CONDITIONAL.
- **Validation Requirements**: Local test passing and compilation.
- **Escalation Triggers**: If the task touches security, privacy, database migrations, or compliance domains, escalate to GOVERNED mode.
- **Expected Result Status**: Feature implemented and locally validated.

## GOVERNED Mode
- **Purpose**: Execution of tasks that require structural, security, or compliance oversight.
- **Allowed Task Types**: Database migrations, authentication/authorization updates, secret handling, cross-service APIs, and privacy-impacting features.
- **Required Context**: Affected files, `docs/governance/GOVERNANCE_LAYER.md` (only when governance triggers are present), and required domain specialist skills.
- **Excluded Context**: Irrelevant domain skills.
- **Governance Status**: REQUIRED.
- **Validation Requirements**: Full test suite, governance checks, and explicit compliance verification.
- **Escalation Triggers**: If the task requires formal read-only review or is considered too risky for immediate implementation, escalate to AUDIT mode.
- **Expected Result Status**: Implementation verified against governance constraints.

## AUDIT Mode
- **Purpose**: Formal read-only review, compliance auditing, and risk assessment.
- **Allowed Task Types**: Security reviews, architecture reviews, compliance audits, and resilience planning.
- **Required Context**: Entire feature slice, `GOVERNANCE_LAYER.md`, and relevant audit specialist skills (e.g., Arbiter, Cipher, Clockwork).
- **Excluded Context**: Implementation-only execution contexts.
- **Governance Status**: REQUIRED.
- **Validation Requirements**: Generation of a formal audit report.
- **Escalation Triggers**: Escalates to DESTRUCTIVE mode if resilience testing requires negative live execution.
- **Expected Result Status**: Audit report delivered. (AUDIT mode is read-only unless the user explicitly approves remediation work.)

## DESTRUCTIVE Mode
- **Purpose**: Execution of high-risk tasks that modify production data, perform destructive negative testing, or bypass normal safety constraints.
- **Allowed Task Types**: Chaos testing, negative path simulation, and authorized live data modification.
- **Required Context**: Target environment context, guardrail scripts, and Dagger skill.
- **Excluded Context**: Standard implementation context.
- **Governance Status**: BLOCKED_PENDING_AUTHORIZATION.
- **Validation Requirements**: Strict guardrail validation, explicit user authorization, and fail-closed state confirmation.
- **Escalation Triggers**: None (terminal escalation mode).
- **Expected Result Status**: Controlled failure path executed or destructive action safely applied.

## Mode Selection Matrix

| Trigger | Mode | Governance Status | Required Context | Validation |
|---|---|---|---|---|
| Syntax fix, typo | FAST | NOT_REQUIRED | Specialist SKILL.md, Target File | Syntax checks |
| Feature addition | STANDARD | CONDITIONAL | Specialist SKILL.md, Architecture | Local tests |
| Auth, DB change | GOVERNED | REQUIRED | GOVERNANCE_LAYER.md, Specialist SKILL.md | Full tests, Governance |
| Security review | AUDIT | REQUIRED | GOVERNANCE_LAYER.md, Full slice | Audit report |
| Chaos testing | DESTRUCTIVE | BLOCKED_PENDING_AUTHORIZATION | Guardrails, Dagger SKILL.md | User Auth, Guardrail tests |

## Escalation Rules
- **FAST to STANDARD**: Escalate if the task scope expands beyond a single isolated file or requires architectural consideration.
- **STANDARD to GOVERNED**: Escalate if the task touches security, privacy, authentication, or structural database state.
- **GOVERNED to AUDIT**: Escalate if the proposed changes are too high-risk for direct implementation and require formal read-only review first.
- **any mode to DESTRUCTIVE**: Any task requiring destructive testing, production modification, or guardrail bypass is immediately placed in a DESTRUCTIVE blocked state.

## Governance Status Mapping
- **NOT_REQUIRED**: Fast mode tasks without compliance impact.
- **CONDITIONAL**: Standard tasks where governance is loaded only if triggers appear.
- **REQUIRED**: Governed and Audit tasks requiring explicit policy adherence.
- **BLOCKED_PENDING_AUTHORIZATION**: Destructive tasks.

## Validation Requirements
Mode selection dictates the stringency of validation. FAST mode relies on compilation, while GOVERNED and DESTRUCTIVE modes require programmatic guardrail validation and full suite testing.

## Required Exclusions
- FAST mode cannot be used for security, CI/CD, release, destructive, database migration, credential, compliance, or governance tasks.
- AUDIT mode is read-only unless the user explicitly approves remediation work.
- GOVERNED mode must load `docs/governance/GOVERNANCE_LAYER.md` only when governance triggers are present.
- DESTRUCTIVE mode must remain BLOCKED_PENDING_AUTHORIZATION unless explicit user authorization and required guardrail validation are present.

## Non-Goals
This policy does not dictate how the underlying LLM functions, but rather strict routing requirements for context provision, safety gating, and intent classification prior to execution.

## Canonical References
- [Router-First Architecture](ROUTER_FIRST_ARCHITECTURE.md)
- [Context Retrieval Rules](CONTEXT_RETRIEVAL_RULES.md)
- [Governance Layer](../governance/GOVERNANCE_LAYER.md)
- [Router Validation Benchmarks](../testing/ROUTER_VALIDATION_BENCHMARKS.md)

## Policy Result
EXECUTION_MODES_POLICY_DEFINED
