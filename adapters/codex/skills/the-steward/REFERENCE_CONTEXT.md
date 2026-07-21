# Portable Reference Context

Generated from canonical Orchestra sources. Indented snapshots are code-only context; file references inside snapshots are not package navigation targets.

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

<a id="project-context-decision-prompt"></a>
## Source: docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md

    # PROJECT_CONTEXT Decision Prompt

    ## Purpose

    This document defines a Steward-led prompt workflow for deciding whether a repository needs `PROJECT_CONTEXT.md`, what scope it should cover, and whether it should remain advisory or later move toward governed enforcement.

    `PROJECT_CONTEXT.md` exists to preserve project-specific context, boundaries, assumptions, constraints, and operating rules so governance review does not rely on guesswork.

    This phase is decision support only. It does not make `PROJECT_CONTEXT.md` mandatory, and it does not modify CI enforcement. For context-sensitive enforcement modes after classification, see `docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md`.

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

    The Steward should recommend, not impose, the governance level unless project risk or release policy clearly requires `Strict-Governed`. Use the optional ruleset in `docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md` to frame the default recommendation, then let the user or maintainer confirm or override it.

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

    When drafting the file itself, start from `docs/templates/PROJECT_CONTEXT_TEMPLATE.md` and trim or annotate sections to match the chosen governance level.

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
    5. present governance options and allow user or maintainer direction
    6. produce the requested output without changing CI or declaring `PROJECT_CONTEXT.md` mandatory

    ## Non-goal for This Phase

    This prompt does not convert `PROJECT_CONTEXT.md` into a hard governance gate.

    Any later move toward strict enforcement should be a separate maintainer decision and may involve The Governor only when enforcement, release gating, or higher-risk governance policy is explicitly requested.

<a id="project-context-enforcement-policy"></a>
## Source: docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md

    # PROJECT_CONTEXT Enforcement Policy

    ## Purpose

    This document defines a context-sensitive policy for when `PROJECT_CONTEXT.md` should remain advisory, when it should be strongly recommended, and when it should become a blocking governance requirement.

    The goal is not to make `PROJECT_CONTEXT.md` universally mandatory. The goal is to scale governance according to project type, coordination needs, and real-world risk.

    `PROJECT_CONTEXT.md` is recommended for governed projects, but not every project should be treated as `Strict-Governed`. Governance level is project-type dependent, user-confirmed, and only enforceable when strict governance is declared or clearly required by policy.

    ## Enforcement Principle

    `PROJECT_CONTEXT.md` enforcement should depend on project classification and risk level.

    - low-risk, exploratory, educational, and sandbox work should stay advisory by default
    - moderate coordination work should receive stronger recommendations without default blocking
    - real-world, real-data, compliance-sensitive, destructive, or release-critical work should require `PROJECT_CONTEXT.md` as a gated validation item

    The Steward owns classification and context sufficiency. The Steward should recommend, not automatically impose, a governance level unless project risk clearly requires strict governance. The user or maintainer confirms the intended governance level. The Governor should only participate in blocking enforcement after the project is classified as strict-governed, a maintainer explicitly requests strict enforcement, or release governance requires it.

    ## Optional Project Governance Ruleset

    Use this ruleset to choose the default governance level before turning `PROJECT_CONTEXT.md` into an enforcement gate.

    | Project Type | Recommended Governance Level | Validation Behavior |
    | --- | --- | --- |
    | School project | Advisory | Warning only |
    | Learning repo | Advisory | Warning only |
    | Prototype | Advisory | Warning only |
    | Sandbox or trial project | Advisory | Warning only |
    | Portfolio project intended for reuse | Recommended | Strong warning, non-blocking |
    | Internal tool | Recommended | Strong warning unless configured strict |
    | Multi-agent development repo | Recommended or Strict-Governed | Depends on write permissions and risk |
    | Real-world application | Strict-Governed | Blocking validation |
    | Production project | Strict-Governed | Blocking validation |
    | Client-facing project | Strict-Governed | Blocking validation |
    | Project using real-world user or client data | Strict-Governed | Blocking validation |
    | Compliance-sensitive project | Strict-Governed | Blocking validation |
    | Destructive automation workflow | Strict-Governed | Blocking validation |
    | Release-critical repo | Strict-Governed | Blocking validation |

    This table is a default decision aid, not a universal override. Maintainers may choose a stricter path earlier, and The Governor may enforce stricter behavior only when `Strict-Governed` is declared or a release policy clearly requires it.

    ## Project Classification Levels

    ### Advisory

    Use for:

    - school projects
    - learning repos
    - experiments
    - prototypes
    - throwaway demos
    - personal sandbox projects

    Behavior:

    - missing `PROJECT_CONTEXT.md` should produce a warning or recommendation only
    - validation should not block CI by default
    - incomplete context should not become a hard failure unless a higher-risk mode is explicitly requested

    ### Recommended

    Use for:

    - active internal tools
    - portfolio projects intended for reuse
    - multi-agent development repos
    - projects with moderate coordination needs

    Behavior:

    - missing `PROJECT_CONTEXT.md` should produce a stronger warning
    - validation may report advisory failure or visible warning status
    - CI should not block unless maintainers explicitly configure stricter behavior

    ### Strict-Governed

    Use for:

    - real-world projects
    - production projects
    - client-facing projects
    - projects with real-world user data
    - projects with sensitive business data
    - projects with security, legal, financial, medical, or privacy implications
    - destructive automation workflows
    - release-critical repos

    Behavior:

    - missing `PROJECT_CONTEXT.md` should be a blocking validation failure
    - incomplete `PROJECT_CONTEXT.md` should be a blocking validation failure when required sections are missing
    - governance enforcement should be treated as part of release and operational safety, not as optional documentation polish
    - strict mode should be treated as opt-in or policy-triggered, not as the universal default for every repository

    ## Risk Signals

    The following signals push a project toward `Strict-Governed` classification:

    - real user data
    - client data
    - production deployment
    - legal or compliance exposure
    - financial or billing data
    - authentication or authorization logic
    - destructive actions
    - secrets or credential handling
    - medical, legal, HR, or education records
    - public release or marketplace publication
    - multi-agent automation with write permissions

    A single signal does not always force strict governance by itself, but multiple signals or any clearly high-risk signal should trigger a Steward recommendation toward `Strict-Governed`.

    ## Enforcement Modes

    ### Advisory Mode

    - `PROJECT_CONTEXT.md` is recommended, not required
    - warnings should explain why more context would help
    - validation output should preserve exploration and low-friction workflows

    ### Recommended Mode

    - `PROJECT_CONTEXT.md` is strongly encouraged
    - missing or thin context should be visible in governance output
    - blocking should remain opt-in unless maintainers explicitly promote the repository to stricter enforcement

    ### Strict-Governed Mode

    - `PROJECT_CONTEXT.md` is required
    - required sections must be present and materially complete
    - blocking validation is appropriate because project context is part of safety, scope control, and release discipline

    ## Required Strict-Governed PROJECT_CONTEXT Sections

    Strict-governed projects should include at least:

    - Project Name
    - Project Purpose
    - Project Type
    - Data Sensitivity
    - Primary Users
    - Runtime or Deployment Context
    - Governance Level
    - Safety Boundaries
    - Validation Requirements
    - Known Non-Goals
    - Maintainer Approval Rules

    ## Recommended Advisory and Recommended Sections

    Advisory and recommended projects should include, at minimum:

    - Project Name
    - Project Purpose
    - Project Type
    - Current Stage
    - User Preferences
    - Known Constraints
    - Validation Notes

    Use `docs/templates/PROJECT_CONTEXT_TEMPLATE.md` as the shared starting point. Low-risk projects may keep strict-only sections lightweight or mark them `Unknown` or `Not yet decided` without being blocked by default.

    ## Steward Decision Workflow

    The Steward workflow should be:

    1. gather initial context
    2. classify project type
    3. identify risk signals
    4. recommend `Advisory`, `Recommended`, or `Strict-Governed`
    5. present the recommendation as guidance and allow user or maintainer direction
    6. produce one of the following:
       - `PROJECT_CONTEXT.md`
       - decision summary
       - implementation plan

    The Steward owns:

    - context classification
    - context sufficiency judgment
    - initial recommendation of enforcement mode
    - the distinction between advisory context and future blocking context

    ## Governor Escalation Workflow

    The Governor should only enforce blocking behavior when one of these is true:

    - the project is classified `Strict-Governed`
    - the maintainer explicitly requests strict enforcement
    - release governance requires it

    The Governor should not be used to turn `PROJECT_CONTEXT.md` into a universal requirement for all repositories.

    ## Validation Behavior

    Current-phase policy direction:

    - advisory projects should warn, not block
    - recommended projects should warn strongly, not block by default
    - strict-governed projects should block on missing or materially incomplete `PROJECT_CONTEXT.md`

    The current Python validator should follow this policy at the governance-level and required-section level without turning advisory repositories into universal hard failures.

    ## Examples

    ### Advisory Example

    A school capstone prototype with no real user data and no public deployment path should remain advisory. Missing `PROJECT_CONTEXT.md` should not block CI.

    ### Recommended Example

    A reusable internal automation repo used by multiple agents or contributors should be classified as recommended. Missing `PROJECT_CONTEXT.md` should surface clearly, but remain non-blocking until maintainers opt into stricter governance.

    ### Strict-Governed Example

    A client-facing automation system that handles credentials, user data, destructive operations, or release-critical workflows should be classified as strict-governed. Missing or incomplete `PROJECT_CONTEXT.md` should block validation.

    ## Non-goals

    This policy does not:

    - make `PROJECT_CONTEXT.md` universally mandatory
    - force every repository into `Strict-Governed`
    - hard-fail school, trial, prototype, or sandbox repos by default
    - modify CI in this phase
    - replace the Steward-led decision prompt
    - bypass maintainer approval for future enforcement changes

    ## Future Implementation Checklist

    Further validator improvements may consider:

    - detect `PROJECT_CONTEXT.md` presence
    - detect governance level
    - validate required sections by governance level
    - warn for advisory projects
    - warn strongly for recommended projects
    - block for strict-governed projects
    - allow explicit override only with documented maintainer approval

<a id="project-context-template"></a>
## Source: docs/templates/PROJECT_CONTEXT_TEMPLATE.md

    # PROJECT_CONTEXT Template

    > Use this template as a starting point for `PROJECT_CONTEXT.md`.
    >
    > - Advisory projects may keep this lightweight.
    > - Strict-Governed projects must fill every required section before relying on this file for blocking governance enforcement.
    > - Do not invent context.
    > - If a detail is unknown, write `Unknown` or `Not yet decided` instead of guessing.

    <!-- Guidance: Keep the structure stable so validators and future maintainers can find the expected sections quickly. -->
    <!-- Guidance: Advisory and recommended repositories may keep strict-only sections short, but they should not remove the headings without a project-specific reason. -->

    ## Project Name
    Unknown

    ## Project Purpose
    Not yet decided

    ## Project Type
    Unknown

    ## Current Stage
    Not yet decided

    ## Primary Users
    Unknown

    ## Data Sensitivity
    Unknown

    ## Runtime or Deployment Context
    Unknown

    ## Governance Level
    - Advisory
    - Recommended
    - Strict-Governed

    Guidance:
    - Choose Advisory for school, prototype, sandbox, learning, or trial projects.
    - Choose Recommended for reusable, internal, or moderate-coordination projects.
    - Choose Strict-Governed for real-world, production, client-facing, real-data, compliance-sensitive, destructive, or release-critical projects.

    ## Safety Boundaries
    Unknown

    ## Validation Requirements
    Not yet decided

    ## Known Constraints
    Unknown

    ## Known Non-Goals
    Unknown

    ## Maintainer Approval Rules
    Not yet decided

    ## User or Maintainer Preferences
    Unknown

    ## Last Reviewed
    Not yet decided
