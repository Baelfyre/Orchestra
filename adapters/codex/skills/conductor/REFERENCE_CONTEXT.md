# Portable Reference Context

Generated from canonical Orchestra sources. Indented snapshots are code-only context; file references inside snapshots are not package navigation targets.

<a id="execution-modes-policy"></a>
## Source: docs/routing/EXECUTION_MODES_POLICY.md

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
    - **NOT_REQUIRED**: FAST mode tasks without compliance impact.
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

<a id="skill-index"></a>
## Source: SKILL_INDEX.md

    # Skill Index

    ## Purpose

    Lightweight routing index. Load a specialist `SKILL.md` only when it will execute or governance requires it.

    ## Execution Modes

    - **Ideation**: no edits
    - **Prototype**: local experiment
    - **Implementation**: development
    - **Audit**: read-only review
    - **Release**: public or deployment work

    ## Risk Levels

    - **Low**: safe formatting or docs
    - **Medium**: ordinary implementation or validation
    - **High**: security, persistence, or compliance
    - **Extreme**: destructive or production-impacting work

    ## Progression Modes

    - **DIRECT**: one specialist
    - **MANUAL**: pause and confirm
    - **DELEGATED**: authorized envelope
    - **LEGACY_FALLBACK**: fail-closed manual pause


    ## Skill Lookup Table

    | Skill | Canonical Purpose | Precise Triggers | Avoid When | Governance vs Execution | Context Dependencies | Output Formats |
    | --- | --- | --- | --- | --- | --- | --- |
    | `the-steward` | Business alignment, scope, requirements, SDLC sufficiency | roadmap fit, acceptance criteria, scope boundary, required SDLC artifact sufficiency | legal, licensing, privacy-obligation, IP review | Governance decision owner | `docs/governance/GOVERNANCE_LAYER.md` | Governance Review |
    | `the-governor` | Legal, regulatory, privacy-obligation, IP, licensing governance | privacy policy impact, ToS impact, license compatibility, IP clearance, compliance obligations | business alignment or scope review | Governance decision owner | `docs/governance/GOVERNANCE_LAYER.md` | Governance Review |
    | `arbiter` | Continuity, source-of-truth, branch, handoff, merge-readiness | handoff readiness, branch uncertainty, merge readiness, missing validation evidence, continuation state conflict | normal implementation or normal QA execution | Continuity owner | git status, diffs, validation outputs | Continuity Review,Governance Effectiveness Review |
    | `conductor` | Routing and sequencing | ambiguous ownership, cross-domain sequencing, access-routing split, workflow orchestration | one obvious specialist owns full task | Routing owner | `SKILL_INDEX.md`; `ROUTING_MAP.md` only for ambiguity | Routing Plan,Prompts |
    | `the-tuner` | Cross-domain contract coordination | multi-domain gap, conflict, or staleness | single-owner work | Coordination only | protocol | Collaboration Review,Cross-Layer Contract Packet,Contradiction Report,Re-entry Recommendation |
    | `clockwork` | Architecture, layering, service boundaries, refactor structure | architecture redesign, layering drift, service boundary change, refactor strategy | straightforward code edit already designed | Technical review owner | none by default | Compact,Full |
    | `cipher` | Technical security and privacy-control review | authorization model, secrets handling, RBAC, threat exposure, privacy-control design | legal/privacy-obligation governance or offensive testing | Technical review owner | security-sensitive slice only | Caveman,Full Security Review |
    | `cloak` | UI/UX, accessibility, responsive layout, interaction design | accessibility remediation, layout design, user-flow clarity, responsive behavior | backend logic, DB design, security policy | Technical review owner | frontend slice only | QUICK_UI_HANDOFF,DOCUMENT_REVIEW,FORMAL_UI_AUDIT |
    | `chronicler` | Database and persistence semantics | migration semantics, schema design, ORM behavior, data integrity, normalization | UI review or general QA | Technical review owner | persistence slice only | Caveman,Normalization Output |
    | `overseer` | QA strategy, validation evidence, release readiness | test strategy, validation plan, CI readiness, regression evidence, release validation | architecture design or destructive testing | Validation owner | test and validation evidence | Caveman,Full QA Review,Delegated Unit Evidence |
    | `dagger` | Guarded destructive-path and resilience simulation | chaos simulation, guarded negative-path validation, resilience stress path | routine QA, security policy, implementation | Guarded execution specialist | `scripts/dagger_guardrail.py` | Caveman |
    | `weaver` | Diagrams and visual models | UML, ERD, Mermaid, PlantUML, workflow visualization | code implementation or policy review | Technical artifact owner | diagram target domain only | Mermaid,PlantUML |
    | `scribe` | Documentation production and editing | README rewrite, changelog prose, docs cleanup, source-backed narrative | business alignment decisions or architecture ownership | Execution owner for docs | source material only | Mode 1,Mode 2,Mode 3 |
    | `ponytail` | Implementation after design is ready | scoped code edit, bug fix with known owner, minimal safe implementation | architecture, security, DB, governance, or ambiguous ownership | Execution owner | active file slice plus routed specialist guidance | IMPLEMENTATION_PLAN,CODE_REVIEW,QUICK_FIX |

    ## Avoid-When Notes

    - **the-steward**: avoid for legal, regulatory, privacy-obligation, licensing, or IP review
    - **the-governor**: avoid for business alignment or scope review
    - **arbiter**: avoid for feature implementation, architecture design, or replacing normal QA
    - **conductor**: avoid when single obvious specialist suffices
    - **cipher**: avoid for offensive or destructive testing
    - **cloak**: avoid for backend logic, persistence, or security policy
    - **dagger**: avoid for ordinary QA, implementation, or production execution
    - **chronicler**: avoid for UI or general QA
    - **overseer**: avoid for architecture ownership or destructive testing
    - **weaver**: avoid for code implementation or policy review
    - **scribe**: avoid for architecture, database, or governance decisions
    - **clockwork**: avoid for layout tweaks or documentation writing
    - **ponytail**: avoid for architecture, UI/UX decisions, security policy, database semantics, or governance

    ## Canonical References

    - [Governance Layer](docs/governance/GOVERNANCE_LAYER.md)
    - [Routing Map](ROUTING_MAP.md)

<a id="minimal-prompt-format"></a>
## Source: docs/routing/MINIMAL_PROMPT_FORMAT.md

    # Minimal Prompt Format

    ## Purpose
    Define Conductor's minimum safe downstream task packet.

    ## Prompt Assembly Principle
    Include only context required by the selected mode. Do not load full READMEs, governance files, skills, or routing maps without a direct trigger.

    ## Standard Prompt Package
    Every assembled prompt must include the following metadata block:

    - **Task**: The immediate goal to accomplish.
    - **Intent**: What the user ultimately wants (e.g., bug fix, feature, audit).
    - **Selected Skill**: The executing specialist slug.
    - **Execution Mode**: FAST, STANDARD, GOVERNED, AUDIT, or DESTRUCTIVE.
    - **Risk Level**: Low, Medium, High, or Extreme.
    - **Required Context**: Absolute paths to minimal context documents.
    - **CONDITIONAL Context**: Conditionally included paths based on domain overlap.
    - **Constraints**: Task boundaries, do-nots, and style locks.
    - **Governance Status**: Current standing of the request.
    - **Expected Output**: The desired artifact or standard response format.
    - **Validation Requirements**: What tests, checks, or commands must be run post-execution.
    - **Result Status**: The success identifier to return.
    - **Coordination**: Active Tuner session, contract state, and re-entry.

    ## Execution Mode Formats
    The layout of the prompt package adapts to the execution mode selected during intake.

    ## FAST mode Format
    **Use**: Ideation, prototype, simple Q&A.
    **Include**: Task, Intent, Selected Skill, Result Status.
    **Exclude**: Deep governance, detailed validation, and Tuner metadata.

    ## STANDARD mode Format
    **Use**: Routine feature development, documentation, general backend/frontend implementation.
    **Include**: All standard package fields. Minimal required context (e.g., standard testing context).
    **Exclude**: Formal governance audit steps unless explicitly triggered.

    ## GOVERNED mode Format
    **Use**: Security-sensitive logic, database persistence, access control.
    **Include**: All standard package fields, Governance Status, explicit conditional contexts (Security, Database).
    **Exclude**: Broad UI/UX context (unless UI touches security/auth).

    ## AUDIT mode Format
    **Use**: Formal compliance, release reviews, read-only inspections.
    **Include**: Task, Intent, `docs/governance/GOVERNANCE_LAYER.md`, Risk Level, Constraints, Expected Output.
    **Exclude**: Implementation commands, destructive operation context.

    ## DESTRUCTIVE mode Format
    **Use**: Chaos, negative path, resilience testing (e.g., `dagger`).
    **Include**: Task, Intent, Destructive-operation context, Explicit Authorization checks, Validation Requirements.
    **Rule**: Destructive-operation prompts must never proceed without explicit user authorization and required guardrail validation (`scripts/dagger_guardrail.py`).

    ## Required Exclusions
    The prompt package **must not** include full README content, full governance files, full skill files, or full routing maps unless they are directly required by the selected mode and relevant task context categories.

    ## Governance Status Values
    Governance status must be explicitly marked as one of the following:
    - `NOT_REQUIRED`
    - `CONDITIONAL`
    - `REQUIRED`
    - `BLOCKED_PENDING_AUTHORIZATION`

    ## Examples

    ### Simple Q&A
    - Task: Explain the application entry point.
    - Mode: FAST
    - Required Context: Core manifest only.
    - Governance: NOT_REQUIRED.

    ### Documentation update
    - Task: Update setup instructions in README.
    - Mode: STANDARD
    - Required Context: Documentation context.
    - Governance: NOT_REQUIRED.

    ### Code implementation
    - Task: Add retry logic to the HTTP client.
    - Mode: STANDARD
    - Required Context: Backend/implementation context.
    - Governance: CONDITIONAL.

    ### Governance review
    - Task: Assess the project for GDPR compliance risks.
    - Mode: AUDIT
    - Required Context: `docs/governance/GOVERNANCE_LAYER.md`.
    - Governance: REQUIRED.

    ### Destructive operation request
    - Task: Run fuzz testing on the auth endpoint.
    - Mode: DESTRUCTIVE
    - Required Context: Destructive-operation context.
    - Governance: BLOCKED_PENDING_AUTHORIZATION (until user confirms).

    ## Validation Requirements
    - All downstream output must pass `git diff --check`.
    - The final token cost should be flagged if it exceeds standard baseline limits.

    ## Non-Goals
    - Restricting human user input formats.
    - Rewriting the base execution logic of any individual specialist.

    ## Canonical References
    - [Router-First Architecture](ROUTER_FIRST_ARCHITECTURE.md)
    - [Context Retrieval Rules](CONTEXT_RETRIEVAL_RULES.md)
    - [Governance Layer](../governance/GOVERNANCE_LAYER.md)

    ## Format Result
    MINIMAL_PROMPT_FORMAT_DEFINED

<a id="governance-decision-protocol"></a>
## Source: docs/governance/GOVERNANCE_DECISION_PROTOCOL.md

    # Governance Decision Protocol

    This document is canonical shared governance decision contract for Orchestra.
    Load it only when governance decision must be produced, interpreted, or enforced.
    Do not load it for ordinary route classification.

    ## Shared Decision Model

    Canonical values and shared meanings:

    - `APPROVED`: Required governance review passed; work may proceed to the next governed stage subject to any stated constraints.
    - `ADVISORY_ONLY`: Non-blocking guidance was provided; exploration may continue without satisfying required actions first.
    - `REVISION_REQUIRED`: Identified changes or missing evidence must be addressed before the governed transition may proceed.
    - `BLOCKED`: Work cannot proceed through the governed transition until the blocking condition is resolved and reviewed again.
    - `NOT_APPLICABLE`: This governance review does not apply to the request and creates no additional gate.

    These values define generic pipeline meaning only.
    Specialists may add role-specific nuance without redefining shared meanings.

    ## Shared Compact Output Contract

    Canonical compact fields:

    - `REVIEWER`
    - `PROJECT_CONTEXT`
    - `DECISION`
    - `REASON`
    - `RISKS`
    - `REQUIRED_ACTIONS`

    Specialists may add role-specific fields in their own output formats.

    ## Shared Gate Contract

    - Conductor stops on `BLOCKED`.
    - Conductor pauses on `REVISION_REQUIRED`.
    - Conductor pauses on `human_review_required: true`.
    - Conductor pauses on Arbiter `HOLD` or `BLOCKED`.
    - Execution specialists cannot bypass governance.
    - Governance authorities produce decisions and constraints, not implementation.

    ## Canonical Separation of Concerns

    | Specialist | Governance Decision Ownership | Technical Review Ownership | Execution Ownership | Routing Ownership | Validation Ownership | Continuity Ownership |
    | --- | --- | --- | --- | --- | --- | --- |
    | `the-steward` | Business alignment, scope, requirements, acceptance criteria, SDLC sufficiency | None | None | None | None | None |
    | `the-governor` | Legal, regulatory, licensing, privacy-obligation, IP, compliance governance | None | None | None | None | None |
    | `arbiter` | Continuation and transition governance | Validation-state interpretation | None | None | Merge, handoff, source-of-truth evidence gating | Handoff, branch, merge, source-of-truth, unresolved validation |
    | `conductor` | None | None | None | Route and sequence selection only | None | Pause routing when Arbiter gate unresolved |
    | `cipher` | None | Technical security, privacy-control, authorization, secrets, threat review | None | None | Security evidence inputs only | None |
    | `overseer` | None | QA strategy, validation planning, test evidence review | None | None | Test execution planning and validation evidence | None |
    | `clockwork` | None | Architecture, layering, service boundaries, refactor structure | None | None | Architecture evidence inputs only | None |
    | `chronicler` | None | Database and persistence semantics, schema, migrations, ORM behavior | None | None | Persistence evidence inputs only | None |
    | `cloak` | None | UI/UX, accessibility, responsive layout, interaction design | None | None | UX evidence inputs only | None |
    | `scribe` | None | Documentation quality only when asked | Documentation production and editing | None | Documentation evidence inputs only | None |
    | `ponytail` | None | None | Implementation only after design and governance are ready | None | Local implementation validation only | None |
    | `dagger` | None | Controlled destructive-path and resilience review | Guarded destructive simulation only | None | Guardrail evidence only | None |
    | `weaver` | None | Diagram and visual-model notation | Diagram production | None | Diagram evidence inputs only | None |
    | Other execution specialists | None | Domain-specific technical review inside their scope | Domain execution inside their scope | None | Domain evidence inputs only | None |

    Clarifications:

    - Governor owns legal, regulatory, licensing, privacy-obligation, and IP governance.
    - Cipher owns technical security and privacy-control analysis.
    - Steward owns business alignment, scope, requirements, acceptance criteria, and required SDLC artifact sufficiency.
    - Scribe produces and edits documentation but does not decide business alignment.
    - Arbiter owns continuity, source-of-truth, branch, handoff, and merge-readiness decisions.
    - Overseer owns QA strategy, test execution planning, and validation evidence.
    - Clockwork owns architecture and layering.
    - Chronicler owns database and persistence semantics.
    - Ponytail owns implementation only after design and governance are ready.
    - Conductor owns routing and sequencing only.

    ## Delegated Execution Transition Dispositions

    `docs/governance/DELEGATED_EXECUTION_POLICY.md` is the canonical contract for envelopes, dispositions, evidence, remediation, checkpointing, capacity, authority, invalidation, and fallback.

    ### Decision Versus Disposition Separation

    Governance decision asks if work is acceptable; transition disposition asks what workflow does next.

    ```
    Governance decision:
      Is the work acceptable under the applicable governance review?

    Transition disposition:
      What may the workflow do next under the active envelope?
    ```

    An `APPROVED` governance decision does not authorize automatic continuation without valid evidence and boundary checks.

    ### Transition Disposition Values

    Additive values defined in `DELEGATED_EXECUTION_POLICY.md`:

    - `AUTO_CONTINUE` - Unit accepted; next approved unit begins.
    - `AUTO_REMEDIATE_AND_REVALIDATE` - Deterministic in-scope defect corrected and revalidated.
    - `WAIT_FOR_EVIDENCE` - Required evidence missing or stale; execution pauses until produced.
    - `WAIT_FOR_CAPACITY` - Host capacity limit reached; resumable checkpoint produced.
    - `ESCALATE_HUMAN` - Requires human intent, policy, authority, or compliance resolution.
    - `STOP` - Unsafe, prohibited, or authority-invalid condition; execution halts.

    ### Automatic Progression Requirements

    Requires valid envelope, current evidence, no stop/escalation condition, and no scope expansion. Prompt text and adapter metadata cannot create or expand an envelope.

    ### Fail-Closed Rule

    Unknown, malformed, missing, or unsupported transition dispositions must fail closed and produce `ESCALATE_HUMAN`. Never default to automatic continuation.
