
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

## Canonical Governance Decision Protocol

`GOVERNANCE_LAYER.md` is governance-context routing and operating-policy document.
`GOVERNANCE_DECISION_PROTOCOL.md` is canonical shared governance decision contract.

Load `GOVERNANCE_DECISION_PROTOCOL.md` only when governance decision must be produced, interpreted, or enforced.
Do not load it for ordinary route classification.

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
| `Project Type` | `school`, `personal`, local `research` | `GSL-0` to `GSL-2` |
| `Project Type` | `internal`, team `open-source` | `GSL-2` to `GSL-3` |
| `Project Type` | `commercial`, `client-facing`, public `open-source` | `GSL-3` to `GSL-4` |
| `Operating Mode` | intent classification | Sets mode baseline |
| `Release Stage` | `prototype` | `GSL-1` |
| `Release Stage` | `development` | `GSL-2` |
| `Release Stage` | `staging` | `GSL-3` |
| `Release Stage` | `production` / `maintenance` | `GSL-4` to `GSL-5` |
| Risk Level | `LOW` / `MEDIUM` / `HIGH` | `LOW`: `GSL-1`-`2`; `MEDIUM`: `GSL-2`-`3`; `HIGH`: `GSL-3`-`4` |
| `Data Sensitivity` | `none`, `low` | `GSL-0` to `GSL-2` |
| `Data Sensitivity` | `medium`, `sensitive` | `GSL-2` to `GSL-3` |
| `Data Sensitivity` | `high`, `PII`, `financial`, `health` | `GSL-4` to `GSL-5` |
| `Public Exposure` | local, private, internal | `GSL-0` to `GSL-2` |
| `Public Exposure` | demo, beta, public claims | `GSL-3` |
| `Public Exposure` | public release, production | `GSL-4` to `GSL-5` |
| Compliance/Legal | attribution, dependencies | `GSL-1` to `GSL-2` |
| Compliance/Legal | privacy, license, IP clearance | `GSL-3` to `GSL-4` |
| Compliance/Legal | regulated domain, `human_review_required: true` | `GSL-5` |
| Destructive Potential | none | No raise |
| Destructive Potential | local simulation, Dagger review | `GSL-3` to `GSL-4` |
| Destructive Potential | live destructive requested | High strictness; Dagger simulation-only unless approved |
| Continuity Gaps | none | No raise |
| Continuity Gaps | missing validation, branch uncertainty | `GSL-2` to `GSL-3` |
| Continuity Gaps | evidence dispute, merge risk | `GSL-4` to `GSL-5` |

### Typical Profiles

| Governance Strictness Level | Typical Profile |
|---|---|
| `GSL-0` | Ideation, brainstorming, rough planning |
| `GSL-1` | School work, personal sandbox, local prototype |
| `GSL-2` | Normal governed implementation with known context |
| `GSL-3` | Elevated governance (audit, staging, public claims) |
| `GSL-4` | Release-critical, production-facing, client delivery |
| `GSL-5` | Maximum governance (compliance domain, human review, destructive risk) |

### Specialist Involvement by GSL

| Governance Strictness Level | Steward | Governor | Arbiter | Overseer | Dagger |
|---|---|---|---|---|---|
| `GSL-0` | Context hygiene | Not required | Conflict only | Optional | Not used |
| `GSL-1` | Light hygiene | Advisory | Optional | Basic | Not used |
| `GSL-2` | Required hygiene | Conditional | Conflict resolution | Standard | Simulation only |
| `GSL-3` | Full hygiene review | Required for release/compliance | Required for continuation gaps | Strict | Simulation if risky |
| `GSL-4` | Required & blocking | Required & blocking | Required for evidence/merge risk | Strict + evidence | Simulation required |
| `GSL-5` | Maximum gate | Maximum authority | Required for disputes | Strict release | Proof required; live blocked |

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


## Phase-Level Delegated Governance

Orchestra supports a delegated execution model where a human authorizes a bounded envelope permitting internal units to proceed automatically under governance boundaries.

### Freedom-First and Need-Based Governance in Delegated Phases

Freedom-first, need-based governance applies. Specialists (Steward, Governor, Arbiter) re-enter when material governing facts change, not for every unchanged internal unit.

### Governance Specialist Re-Entry Triggers

Specialists re-enter when:
- Product, legal, privacy, licensing, IP, or compliance facts emerge.
- Scope or intent changes.
- A design contradiction is detected.
- An authority boundary is approached.
- The envelope approaches expiry or an invalidation condition fires.

### Canonical Policy Reference

`docs/governance/DELEGATED_EXECUTION_POLICY.md` is the single canonical source for envelopes, dispositions, evidence standards, remediation, checkpointing, capacity, authority, invalidation, and fallback. `GOVERNANCE_DECISION_PROTOCOL.md` defines decision-versus-disposition separation.

### Phase Implementation Status

| Phase | Description | Status |
|---|---|---|
| Phase A | Contract design: envelopes, dispositions, evidence, remediation, checkpointing, capacity, authority, invalidation, fallback | **Defined (`DELEGATED_EXECUTION_POLICY.md`)** |
| Phase B | Instruction-level behavior: skill/adapter updates to consume dispositions and loop | **Implemented & Locally Validated** |
| Phase C | Host reliability evaluation: validate host envelope preservation and checkpointing | **Not yet implemented** |
| Phase D | Optional typed runtime enforcement: typed models for envelopes, units, evidence | **Not yet implemented** |
| Phase E | Release preparation: commit, push, PR, merge, tag, release, deployment | **Separately governed** |

Phase B instruction-level behavior implemented and locally validated; remote and host reliability remain pending until separately authorized.

## Enforcement Limitation

Current enforcement is route-level instruction governance. Conductor follows governance gates before routing, but no automated runtime/CI blocker exists yet.

Phase A defines contract foundations. Phase B instruction-level behavior is implemented and locally validated. Phase D optional typed runtime enforcement is Not yet implemented.



---

*See [GOVERNANCE_DECISION_PROTOCOL.md](GOVERNANCE_DECISION_PROTOCOL.md), [STEWARD.md](STEWARD.md), [GOVERNOR.md](GOVERNOR.md), [GOVERNANCE_REVIEW_FLOW.md](GOVERNANCE_REVIEW_FLOW.md), and [RELEASE_GATES.md](RELEASE_GATES.md) for details.*

