# Execution Modes Policy

## Purpose
This document defines the formal execution modes policy for Orchestra. It establishes when the Conductor uses FAST, STANDARD, GOVERNED, AUDIT, or DESTRUCTIVE execution, aligning router-first context loading with governance and safety requirements.

## Scope
This policy applies exclusively to Conductor intent classification, mode selection, and context retrieval. It governs how execution modes escalate based on task complexity and risk.

## Mode Selection Principle
The Conductor must select the execution mode that provides the lowest safe friction. The mode determines which context is loaded, how governance is enforced, and what validation is required before execution.

## Execution Modes

## Risk Mode vs Progression Mode

Execution classification distinguishes **Risk Mode** from **Progression Mode**:

- **Risk Modes**: `FAST | STANDARD | GOVERNED | AUDIT | DESTRUCTIVE` (classify task risk, required context, and governance strictness).
- **Progression Modes**: `DIRECT | MANUAL | DELEGATED | LEGACY_FALLBACK` (classify workflow progression model).
- **Delegated Phase Lifecycle States**:
  `PHASE_AUTHORIZED | UNIT_READY | UNIT_EXECUTING | UNIT_VALIDATING | UNIT_REMEDIATING | WAITING_FOR_EVIDENCE | WAITING_FOR_CAPACITY | ESCALATED | STOPPED | PHASE_VALIDATING | PHASE_READY_FOR_HUMAN_REVIEW`

Delegated phase execution is permitted in `STANDARD` and `GOVERNED` modes when a valid `DelegatedExecutionEnvelope` exists. `AUDIT` mode remains read-only unless remediation is already authorized in the envelope. `DESTRUCTIVE` mode remains fail-closed and cannot auto-continue.

## Risk Mode != Governance Profile

Governance Profile is orthogonal: `HUMAN_GOVERNED` (default), `SEMI_AUTONOMOUS` (through granted PR/CI), or `FULL_AUTONOMOUS` (through granted merge/phase progression). Profiles only reduce effective authority; increases require human authority, children cannot exceed parents, and hard boundaries remain separate. See [Governed Autonomy Modes](../governance/GOVERNED_AUTONOMY_MODES.md).


## FAST mode
- **Purpose**: Rapid execution of simple, low-risk, well-defined tasks.
- **Allowed Task Types**: Syntax formatting, typo fixes, simple UI tweaks, and unambiguous singular code changes.
- **Required Context**: Only the immediate file being edited and the required specialist `SKILL.md` file.
- **Excluded Context**: Full repository index, `GOVERNANCE_LAYER.md`, `ROUTING_MAP.md`, and multi-specialist files.
- **Governance Status**: NOT_REQUIRED.
- **Validation Requirements**: None beyond basic compiler/syntax checks.
- **Escalation Triggers**: If the task requires architectural changes or touches multiple files, escalate to STANDARD mode.
- **Expected Result Status**: Task completed directly.

## STANDARD mode
- **Purpose**: Normal multi-step or multi-file development and feature implementation.
- **Allowed Task Types**: Feature additions, backend logic, standard UI/UX flows, and refactoring within existing architectural boundaries.
- **Required Context**: Immediate files, relevant specialist files, and architectural dependencies.
- **Excluded Context**: `GOVERNANCE_LAYER.md` (unless explicitly triggered) and `ROUTER_DRY_RUN_TEST_CASES.md`.
- **Governance Status**: CONDITIONAL.
- **Validation Requirements**: Local test passing and compilation.
- **Escalation Triggers**: If the task touches security, privacy, database migrations, or compliance domains, escalate to GOVERNED mode.
- **Expected Result Status**: Feature implemented and locally validated.

## GOVERNED mode
- **Purpose**: Execution of tasks that require structural, security, or compliance oversight.
- **Allowed Task Types**: Database migrations, authentication/authorization updates, secret handling, cross-service APIs, and privacy-impacting features.
- **Required Context**: Affected files, `docs/governance/GOVERNANCE_LAYER.md` (only when governance triggers are present), and required domain specialist skills.
- **Excluded Context**: Irrelevant domain skills.
- **Governance Status**: REQUIRED.
- **Validation Requirements**: Full test suite, governance checks, and explicit compliance verification.
- **Escalation Triggers**: If the task requires formal read-only review or is considered too risky for immediate implementation, escalate to AUDIT mode.
- **Expected Result Status**: Implementation verified against governance constraints.

## AUDIT mode
- **Purpose**: Formal read-only review, compliance auditing, and risk assessment.
- **Allowed Task Types**: Security reviews, architecture reviews, compliance audits, and resilience planning.
- **Required Context**: Entire feature slice, `GOVERNANCE_LAYER.md`, and relevant audit specialist skills (e.g., Arbiter, Cipher, Clockwork).
- **Excluded Context**: Implementation-only execution contexts.
- **Governance Status**: REQUIRED.
- **Validation Requirements**: Generation of a formal audit report.
- **Escalation Triggers**: Escalates to DESTRUCTIVE mode if resilience testing requires negative live execution.
- **Expected Result Status**: Audit report delivered. (AUDIT mode is read-only unless the user explicitly approves remediation work.)

## DESTRUCTIVE mode
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
`NOT_REQUIRED` applies to FAST without compliance impact; `CONDITIONAL` to ordinary Standard work; `REQUIRED` to Governed/Audit; and `BLOCKED_PENDING_AUTHORIZATION` to Destructive work.

## Validation Requirements
Risk mode sets validation depth; Governed and Destructive require programmatic guardrails and the applicable full suite.

## Required Exclusions
- FAST mode cannot be used for security, CI/CD, release, destructive, database migration, credential, compliance, or governance tasks.
- AUDIT mode is read-only unless the user explicitly approves remediation work.
- GOVERNED mode must load `docs/governance/GOVERNANCE_LAYER.md` only when governance triggers are present.
- DESTRUCTIVE mode must remain BLOCKED_PENDING_AUTHORIZATION unless explicit user authorization and required guardrail validation are present.

## Non-Goals
This policy governs routing context, safety gates, and classification, not model internals.

## Canonical References
- [Router-First Architecture](ROUTER_FIRST_ARCHITECTURE.md)
- [Context Retrieval Rules](CONTEXT_RETRIEVAL_RULES.md)
- [Governance Layer](../governance/GOVERNANCE_LAYER.md)
- [Governed Autonomy Modes](../governance/GOVERNED_AUTONOMY_MODES.md)
- [Router Validation Benchmarks](../testing/ROUTER_VALIDATION_BENCHMARKS.md)

## Policy Result
EXECUTION_MODES_POLICY_DEFINED
