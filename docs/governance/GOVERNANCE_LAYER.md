# Governance Layer

The Governor, The Steward, and Arbiter form a reusable governance layer that sits above the Conductor. Their purpose is to ensure that any project, product, repository, or future development effort remains aligned with its objectives, documentation requirements, compliance obligations, legal risk boundaries, privacy expectations, IP and copyright concerns, licensing requirements, release readiness standards, and verified continuation state.

## Architecture

```
Governance Layer
├── The Steward    (Business, Scope, SDLC)
├── The Governor   (Legal, Compliance, Privacy, IP)

â”œâ”€â”€ Arbiter        (Continuity, Validation, Transition Safety)

Orchestration Layer
└── Conductor

Execution Layer
├── Skills (Specialists)
├── Agents
├── Tools
└── Implementation Workers
```

## Design Principles

- **Project-Agnostic**: Works with any project type (school, personal, internal, open-source, commercial, client-facing, research).
- **Context-Aware**: Adapts to the specific project context profile.
- **Risk-Scaled**: Adjusts review depth based on project risk level (LOW / MEDIUM / HIGH).
- **Token-Efficient**: Uses compact output by default, expands only when findings exist.
- **Markdown-First**: All governance artifacts are plain Markdown.
- **Skill-Compatible**: Integrates with the Orchestra skill ecosystem.
- **Reusable**: No hard-coded assumptions about any specific project or platform.
- **Continuity-Safe**: Transition, handoff, branch, and merge decisions rely on verified project state instead of memory.

## Project Context Profile

Before governance review, the system identifies the project context:

```
Project Name:
Project Type: [school | personal | internal | open-source | commercial | client-facing | research | other]
Project Purpose:
Target Users:
Internal or Public:
Open Source or Private:
Data Collected: [none | non-sensitive | sensitive | PII | financial | health]
Data Sensitivity: [none | low | medium | high]
Jurisdiction: [not applicable | specify]
Known Legal or Compliance Requirements:
Third-Party Dependencies:
Third-Party Assets:
Release Stage: [prototype | development | staging | production | maintenance]
Risk Level: [LOW | MEDIUM | HIGH]
Required Documentation:
```

## Governance Basis of Review

The Steward and The Governor do not apply absolute or pre-assumed governance rules. Instead, they first establish the **Governance Basis of Review** from the supplied or discoverable context:
- Project Context
- Declared Objectives
- Requirements and Acceptance Criteria
- Release Target
- Data Use
- Jurisdiction or Applicable Rules
- Dependencies and Third-Party Assets
- Documentation Requirements
- Known Constraints

### No-Assumption Rule
The governance layer operates contextually. Authorities do not pre-assume jurisdiction, legal obligations, business goals, or requirements. They must review *only* against what is stated or discoverable in the project context.

### Context-Missing Behavior
If the project context profile is incomplete, unclear, or entirely missing, the Steward and Governor must not guess or make assumptions.
- In **Audit**, **Release**, or high-risk **Implementation** modes, they must return `REVISION_REQUIRED` to request the necessary clarity.
- In **Ideation** or **Prototype** mode, they return `ADVISORY_ONLY` or `NOT_APPLICABLE` to allow exploration to proceed without blocking.

## Freedom-First Development

Conductor prioritizes freedom-first, need-based development. The ecosystem ensures that ideation, brainstorming, prototyping, and concept exploration are not restricted by early governance requirements. Governance checks activate only when a task moves into implementation, when files or architecture change, or when risk triggers are explicitly hit.

## Need-To-Only Governance

The Governor and The Steward operate on a need-to-only basis. They must not interrupt early-stage planning, rough drafting, or prompt refinement. Full formal checks are reserved for high-impact phases (like Release or Audit), while lightweight, non-blocking pathways are used for low-risk work.

Arbiter also operates on a need-to-only basis. It activates when continuation safety is uncertain, including interrupted tasks, token or context exhaustion risk, branch switches, workspace or IDE changes, unclear source of truth, failed or missing validation, handoff, merge preparation, or branch divergence.

## Operating Modes

To support this freedom-first model, the ecosystem defines 5 operating modes:

1. **Ideation Mode**
   - **Purpose**: Brainstorming, comparing options, rough planning, concept development, prompt refinement.
   - **Governance**: Unblocked. Project context is not required. Governance returns `ADVISORY_ONLY` or `NOT_APPLICABLE` and must not block the user.
2. **Prototype Mode**
   - **Purpose**: Local-only experiments, throwaway proofs-of-concept.
   - **Governance**: Dynamic and lightweight. Full context is not required unless the task handles user data, security-sensitive code, or third-party assets.
3. **Implementation Mode**
   - **Purpose**: Modifying source code, database structures, documentation, or architecture.
   - **Governance**: Flexible. Uses fast path by default. Requires minimum context only. Escalate to expanded review only if risk triggers (user data, licensing, security) appear.
4. **Audit Mode**
   - **Purpose**: Explicit requests for compliance audits, risk reviews, or structural assessments.
   - **Governance**: Context-heavy. Requires full Basis of Review context.
5. **Release Mode**
   - **Purpose**: Deploying to production, public releases, client delivery, app store submission, or open-source distribution.
   - **Governance**: Strictest path. Fully enforces compliance, license compatibility, privacy validation, and the [App Release Compliance Gate](APP_RELEASE_COMPLIANCE_GATE.md) for app or public release workflows.

## Usage Pattern

To interact with the governance layer, requests must be structured to explicitly declare the project context:

### 1. Project Context Dimensions

| Context Dimension | Purpose |
|---|---|
| Project Type | Guides review complexity based on environment (e.g., school project, public commercial release) |
| Goal | Defines the target objective for alignment checking |
| Release Target | Establishes where the software will be deployed (e.g., local-only, public SaaS) |
| Data Use | Declares whether PII, financial, health, or non-sensitive data is processed |
| Dependencies | Lists all third-party libraries, assets, APIs, or AI models involved |
| Constraints | Documents structural, legal, or policy constraints that must be preserved |
| Expected Output | Details the target output artifacts (e.g., changed files, validation checks) |

### 2. Standard Prompt Pattern

```text
[@ponytail] use conductor for this task

Project Context:
Project Type:
Goal:
Release Target:
Data Use:
Dependencies or Third-Party Assets:
Constraints:

Task:
Describe the work clearly.

Requirements:
- List what must be changed.
- List what must be preserved.
- List any rules the implementation must follow.

Expected Output:
Changed Files:
Summary:
Validation Results:
Remaining Risks:
Next Recommended Step:
```



## Risk Classification

| Risk Level | Criteria | Review Depth |
|---|---|---|
| `LOW` | School work, personal prototype, no public release, no user data, no commercial use | Lightweight |
| `MEDIUM` | Internal tool, team project, third-party deps, limited exposure | Standard |
| `HIGH` | Public release, PII, payments, AI outputs, legal/health/finance domain, commercial use | Expanded + human review |

## Governance Strictness Levels

Governance Strictness Levels (`GSL-0` through `GSL-5`) are a **derived scale**, not a new required project-context field. They do not replace `Project Type`, `Operating Mode`, `Release Stage`, `Risk Level`, `Data Sensitivity`, or any existing governance decision values. They normalize the existing inputs into a single shorthand for review depth, evidence expectations, and specialist involvement.

Derivation rule:

```text
Governance Strictness Level = max(applicable mode baseline, release trigger, risk trigger, compliance/data trigger, continuity trigger)
```

Interpretation rules:
- `Operating Mode` is the task-intent baseline.
- `Release Stage` is the product or repository lifecycle state.
- Other triggers may raise the derived level above the mode baseline.
- Existing decision meanings remain unchanged: `APPROVED`, `ADVISORY_ONLY`, `REVISION_REQUIRED`, `BLOCKED`, `NOT_APPLICABLE`, `READY`, `READY_WITH_MINOR_FIXES`, and `HOLD` keep their current semantics.

### Mode Baseline

| Operating Mode | Typical Baseline |
|---|---|
| `Ideation` | `GSL-0` |
| `Prototype` | `GSL-1` |
| `Implementation` | `GSL-2` |
| `Audit` | `GSL-3` |
| `Release` | `GSL-4` |

### Trigger Mapping Guide

| Input or Trigger | Typical Signals | Derived Contribution |
|---|---|---|
| `Project Type` | `school`, `personal`, local `research` | Usually `GSL-0` to `GSL-2` |
| `Project Type` | `internal`, team `open-source` development | Usually `GSL-2` to `GSL-3` |
| `Project Type` | `commercial`, `client-facing`, public `open-source` distribution | Usually `GSL-3` to `GSL-4` |
| `Operating Mode` | intent classification only | Sets the baseline before other triggers apply |
| `Release Stage` | `prototype` | Usually `GSL-1` |
| `Release Stage` | `development` | Usually `GSL-2` |
| `Release Stage` | `staging` | Usually `GSL-3` |
| `Release Stage` | `production` or externally committed `maintenance` | Usually `GSL-4`, or `GSL-5` if other high-impact triggers apply |
| `LOW` / `MEDIUM` / `HIGH` Risk Level | existing risk model | `LOW` usually keeps work in `GSL-1` to `GSL-2`; `MEDIUM` often raises to `GSL-2` to `GSL-3`; `HIGH` often raises to `GSL-3` to `GSL-4` |
| `Data Sensitivity` | `none`, `low`, non-sensitive | Usually no raise beyond `GSL-0` to `GSL-2` |
| `Data Sensitivity` | `medium`, `sensitive` | Often raises to `GSL-2` or `GSL-3` |
| `Data Sensitivity` | `high`, `PII`, `financial`, `health` | Often raises to `GSL-4` or `GSL-5` |
| `Public Exposure` | local-only, private, internal-only | Usually no raise beyond `GSL-0` to `GSL-2` |
| `Public Exposure` | client demo, limited external access, public claims, beta | Often raises to `GSL-3` |
| `Public Exposure` | public release, external distribution, production-facing operation | Often raises to `GSL-4` or `GSL-5` |
| `Compliance or Legal Sensitivity` | basic attribution or ordinary dependency review | Usually `GSL-1` to `GSL-2` |
| `Compliance or Legal Sensitivity` | contractual review, privacy review, license compatibility, IP clearance | Often raises to `GSL-3` or `GSL-4` |
| `Compliance or Legal Sensitivity` | regulated domain, uncertain obligations, or `human_review_required: true` | Raises to `GSL-5` |
| `Destructive Potential` | no destructive path in scope | No raise by itself |
| `Destructive Potential` | guarded local simulation, negative-path chaos work, Dagger review | Often raises to `GSL-3` or `GSL-4` when relevant |
| `Destructive Potential` | live destructive path requested | Treat as high strictness. Dagger remains simulation-only here unless separately approved through its own guardrails |
| `Continuity or Validation Gaps` | none | No raise by itself |
| `Continuity or Validation Gaps` | missing validation, unclear source of truth, handoff risk, branch uncertainty | Often raises to `GSL-2` or `GSL-3` |
| `Continuity or Validation Gaps` | unresolved evidence dispute, release handoff uncertainty, blocked source-of-truth conflict | Often raises to `GSL-4` or `GSL-5` until resolved |

### Typical Profiles

| Governance Strictness Level | Typical Profile |
|---|---|
| `GSL-0` | Ideation, brainstorming, rough planning, no blocking governance path |
| `GSL-1` | School work, personal sandbox, local prototype, low-risk exploratory work |
| `GSL-2` | Normal governed implementation with known context and limited exposure |
| `GSL-3` | Elevated governance because of audit scope, staging, public claims, client-facing work, or material risk triggers |
| `GSL-4` | Release-critical, production-facing, client delivery, public distribution, or other blocking governance path |
| `GSL-5` | Maximum governance strictness due to compliance-sensitive domains, human review, destructive risk, or unresolved release evidence conflicts |

### Specialist Involvement by GSL

| Governance Strictness Level | Steward | Governor | Arbiter | Overseer | Dagger |
|---|---|---|---|---|---|
| `GSL-0` | Context hygiene only | Usually not required | Only if conflict exists | Optional | Not used |
| `GSL-1` | Light objective, requirements, and documentation hygiene check | Advisory | Optional | Basic validation | Not used |
| `GSL-2` | Required context, objective, requirements, and documentation hygiene check | Conditional | Conflict resolution if needed | Standard checks | Simulation only if relevant |
| `GSL-3` | Required full objective, scope, requirements, and documentation hygiene review | Required for release/public claims or material compliance triggers | Required for unresolved conflicts or continuation gaps | Strict validation | Guardrail simulation if risky |
| `GSL-4` | Required and blocking objective, scope, requirements, and documentation readiness review | Required and blocking | Required for evidence disputes, handoff risk, merge risk, or release uncertainty | Strict validation plus evidence | Required simulation when destructive potential exists; no live destructive execution |
| `GSL-5` | Maximum strictness for objective, scope, requirements, traceability, and documentation readiness | Maximum gate authority | Required for conflicts or source-of-truth disputes | Strict release readiness | Required guardrail proof; live destructive execution blocked unless separately approved |

`GSL` changes review depth and specialist participation only. It does not create new decision values and does not override existing skill boundaries.

## Authority Flow

1. **Request enters** the system.
2. **The Steward** validates alignment, scope, requirements, documentation (scaled to risk).
3. **The Governor** validates compliance, privacy, IP, licensing, audit readiness (scaled to risk).
4. **Arbiter** validates continuity, source of truth, branch state, validation evidence, and handoff or merge readiness when a transition risk exists.
5. **Conductor** receives the approved request and routes to execution skills.
6. **Execution skills** perform the work.
7. **Validation** confirms outputs.
8. **Release Gate** checks governance compliance before release.

For Release Mode app workflows, The Governor must verify privacy, terms, data inventory, retention, deletion, account deletion documentation when accounts exist, platform disclosures, third-party processor disclosures, and IP clearance when applicable. Missing required artifacts must result in `REVISION_REQUIRED` or `BLOCKED`, depending on release context and severity.

## Decision Model

All governance reviews use the same decision values:

| Decision | Meaning |
|---|---|
| `APPROVED` | Proceed to next stage |
| `ADVISORY_ONLY` | Advice given, exploration unblocked |
| `REVISION_REQUIRED` | Address findings before proceeding |
| `BLOCKED` | Cannot proceed until resolved |
| `NOT_APPLICABLE` | No review needed for this request |

The Governor adds `human_review_required` for uncertain legal, regulatory, privacy, licensing, or IP issues.

Arbiter adds continuation verdicts: `READY`, `READY_WITH_MINOR_FIXES`, `HOLD`, and `BLOCKED`.

For governance-effectiveness calibration, Arbiter may also use `READY_WITH_REQUIRED_FIXES`. This does not replace the continuation verdict set above and does not create a new governance decision meaning.

## Default Output Format

```
REVIEWER: [the-steward | the-governor]
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
REASON: [one-line assessment]
RISKS: [identified risks or "none"]
REQUIRED_ACTIONS: [actions needed or "none"]
```

## Gate Rules

- Conductor stops on `BLOCKED` from either authority.
- Conductor pauses on `human_review_required: true` until human review completes.
- Conductor pauses on Arbiter `HOLD` or `BLOCKED` until required validation, context, or remediation is complete.
- Conductor addresses all findings on `REVISION_REQUIRED`.
- Execution agents cannot bypass governance gates.
- Governance authorities produce decisions, not code.

## Separation of Concerns

| Layer | Owns | Does Not Own |
|---|---|---|
| The Steward | Business goals, scope, requirements, SDLC | Legal, compliance, IP, licensing, implementation |
| The Governor | Legal, compliance, privacy, IP, licensing | Business alignment, scope, implementation |
| Arbiter | Continuity, validation state, branch safety, source of truth, handoff and merge readiness | Feature implementation, architecture design, legal compliance, business scope |
| Conductor | Routing, orchestration, skill selection | Governance decisions, implementation |
| Execution Skills | Implementation, code changes | Governance, routing |

## Enforcement Limitation

Current enforcement is instruction-level governance. The Conductor must follow the governance gate before planning or routing work, but no runtime blocker exists yet. Runtime enforcement may be added later if CI checks, schema validation, or automated release gates become necessary.

---

*See [STEWARD.md](STEWARD.md), [GOVERNOR.md](GOVERNOR.md), [GOVERNANCE_REVIEW_FLOW.md](GOVERNANCE_REVIEW_FLOW.md), and [RELEASE_GATES.md](RELEASE_GATES.md) for details.*

