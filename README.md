<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra Hero Banner" width="100%" />

  <p>
    <strong>Project-agnostic governance and orchestration framework for AI-assisted development.</strong>
  </p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> •
    <a href="docs/governance/GOVERNANCE_LAYER.md">Governance</a> •
    <a href="SKILL_INDEX.md">Skills</a> •
    <a href="docs/setup/VALIDATION.md">Validation</a>
  </p>
  <p>
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="validate" />
    </a>
  </p>
</div>

---

## At a Glance

| Layer | Role | Purpose |
|---|---|---|
| Governance | The Steward | Business, scope, SDLC, requirements, and value alignment |
| Governance | The Governor | Legal risk, privacy, IP, licensing, security, and compliance review |
| Orchestration | Conductor | Routes approved work to the correct specialist skills |
| Execution | Specialist Skills | Performs focused implementation, documentation, QA, security, or design work |

## Core Concept

Orchestra uses freedom-first, need-based governance. Users can ideate freely. Governance review is invoked when the task requires alignment review, implementation readiness, audit, risk review, or release validation. The governance layer does not assume what rules apply to every project. Before review, The Steward and The Governor establish the Governance Basis of Review based on the active operating mode and supplied context. If the scope is unclear and review is required, governance returns `REVISION_REQUIRED` instead of assuming.

## Architecture

```mermaid
flowchart LR
    classDef input fill:#101010,stroke:#555,color:#f5f5f5,stroke-width:1.5px
    classDef gov fill:#2b2112,stroke:#d4af37,color:#fff2b2,stroke-width:2px
    classDef orch fill:#201433,stroke:#9d6cff,color:#eadfff,stroke-width:2px
    classDef exec fill:#102436,stroke:#58a6ff,color:#d8ecff,stroke-width:2px
    classDef stop fill:#321414,stroke:#ff6b6b,color:#ffdada,stroke-width:2px

    Request([User Request]):::input
    Context([Project Context]):::input

    subgraph Orchestra[Orchestra]
      subgraph G[Governance Layer]
        Steward{{The Steward<br/>Business • Scope • SDLC}}:::gov
        Governor{{The Governor<br/>Privacy • IP • Compliance}}:::gov
      end

      subgraph O[Orchestration Component]
        Conductor((<br/>Conductor)):::orch
      end

      subgraph E[Execution Layer]
        Skills[[Specialist Skills]]:::exec
        Validate[[Validation]]:::exec
      end
    end

    Output([Release or Response]):::input
    Revision([Revision Required<br/>or Blocked]):::stop

    Request --> Context --> Steward --> Governor --> Conductor --> Skills --> Validate --> Output
    Steward -.-> Revision
    Governor -.-> Revision
```

---

## Governance Layer

The Governance Layer sits above the Conductor. Orchestra uses freedom-first, need-based governance. Users can ideate freely. Governance review is invoked when the task requires alignment review, implementation readiness, audit, risk review, or release validation.

The Steward and The Governor are entirely context-driven. They do not pre-assume what rules apply to every project, nor do they apply every governance rule universally. If the project scope is unclear or missing, governance returns `REVISION_REQUIRED` instead of assuming. Conversely, if a risk area does not apply to the current context, the authority returns `NOT_APPLICABLE`.

> [!IMPORTANT]
> If a request violates alignment, fails scope verification, or breaches compliance boundaries, the Steward or Governor issues a `REVISION_REQUIRED` or `BLOCKED` status. The Conductor will immediately halt execution.

### Operating Modes

Conductor uses 5 distinct operating modes to scale governance dynamically, ensuring that ideation and dynamic prototyping are not restricted:

1. **Ideation Mode**: Brainstorming, exploration, planning, concept development, prompt refinement. Returns `ADVISORY_ONLY` or `NOT_APPLICABLE`.
2. **Prototype Mode**: Local experiments, throwaway proofs-of-concept. Lightweight checks only.
3. **Implementation Mode**: Making file, code, documentation, or architecture changes. Uses fast path by default. Escalate to expanded review only if risk triggers are met.
4. **Audit Mode**: Explicit request for a review, compliance check, or risk assessment. Context-heavy.
5. **Release Mode**: Production deployment, public release, client delivery, or open-source distribution. Strictest path. Escalate uncertain issues for human review.

### Interpret the Decision

| Decision | Meaning | User Action |
|---|---|---|
| **APPROVED** | Work can proceed | Let the conductor route the task |
| **ADVISORY_ONLY** | Advice given, exploration unblocked | Continue brainstorming or prototyping freely |
| **REVISION_REQUIRED** | More context or correction is needed | Add missing details and resubmit |
| **BLOCKED** | Work should not proceed as requested | Resolve the blocking issue first |
| **NOT_APPLICABLE** | Governance check is not needed | Continue with the fast path |

---

## Governance Authorities and Specialist Skills

### Governance Authorities

| Authority | Focus |
|---|---|
| <img src="./assets/readme/icons/the-steward.png" width="16" /> **The Steward** | Business alignment, scope boundaries, and software development lifecycle (SDLC) documentation. |
| <img src="./assets/readme/icons/the-governor.png" width="16" /> **The Governor** | Evaluates legal compliance, privacy risks, intellectual property (IP), licensing, and security policies. |

### Specialist Skills

| Skill | Focus |
|---|---|
| <img src="./assets/readme/icons/amalgam-conductor.png" width="16" /> **Conductor** | Routing and orchestration |
| <img src="./assets/readme/icons/clockwork-meister.png" width="16" /> **Clockwork** | Architecture, OOP, refactoring |
| <img src="./assets/readme/icons/cloak-meister.png" width="16" /> **Cloak** | UI, UX, layout, accessibility |
| <img src="./assets/readme/icons/scribe-meister.png" width="16" /> **Scribe** | Documentation and technical writing |
| <img src="./assets/readme/icons/meister-weaver.png" width="16" /> **Weaver** | Visual modeling and diagram specialist |
| <img src="./assets/readme/icons/meister-chronicler.png" width="16" /> **Chronicler** | Database architect and schema auditor |
| <img src="./assets/readme/icons/acme-overseer.png" width="16" /> **Overseer** | QA, testing, release readiness |
| <img src="./assets/readme/icons/cipher-meister.png" width="16" /> **Cipher** | Security and privacy evidence |
| <img src="./assets/readme/icons/hidden-dagger.png" width="16" /> **Dagger** | Controlled resilience tester |

For details on all execution skills, routing logic, and behavioral constraints, see the [Specialist Skill Index](SKILL_INDEX.md).

---

## Installation

To set up Orchestra as an installable AI workflow plugin:

### Antigravity Setup
```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

### Codex Setup
Clone this repository directly into your Codex plugins directory:
```sh
git clone https://github.com/Baelfyre/Orchestra.git
```

For manual configurations or environment setup details, see the [Installation Guide](docs/setup/INSTALLATION.md).

---

## Quick Start Usage

### 1. Start with a project context

The governance layer does not assume what rules apply. Provide enough context for The Steward and The Governor to know what they are reviewing.

Minimum context:
- **Project Type**: e.g., open-source repo, internal tool
- **Goal**: What the task should accomplish
- **Release Target**: e.g., local only, public release
- **Data Use**: e.g., no user data, sensitive data
- **Dependencies**: e.g., libraries, assets
- **Constraints**: e.g., files to preserve, style rules

### 2. Use the standard prompt pattern

Add this template to the top of your request:

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

### 3. Review the IDE output and Iterate

Follow this feedback loop:
1. Send the refined prompt to the IDE.
2. Let the IDE inspect files and propose changes.
3. Review changed files and validation results.
4. Approve, revise, or ask for another iteration.
5. Commit only after validation passes.

> [!NOTE]
> When unsure which specialist to use, start with **Conductor**. It can route the task to the correct specialist. Use a specialist directly only when the task is narrow and obvious (e.g., UI only, QA only).

---

## Output Mode Behavior

Output from Conductor and its specialists automatically adapts to your intent:
- **Compact mode** is the default for normal iterative tasks.
- **Full mode** is used only when explicitly requested for formal audits, deep reviews, or comprehensive planning.
- **Specialized modes** (like Diagram formats) are automatically selected when the artifact type is clear.
- **Clarification** is only asked when output intent is ambiguous.

---

## Token-Efficient Usage

> [!TIP]
> For best token efficiency:
> - Start with a refined prompt.
> - Provide only relevant project context.
> - Ask for changed files, summary, validation, risks, and next step.
> - Do not request expanded governance analysis unless the task is MEDIUM or HIGH risk.
> - Use fast path for typo fixes, formatting edits, and local documentation cleanup.
> - Link to detailed governance docs instead of repeating them in your prompt.

---

## Documentation Map

| Area | Start Here | Purpose |
|---|---|---|
| Governance | [Governance Layer](docs/governance/GOVERNANCE_LAYER.md) | Understand The Steward, The Governor, risk scaling, and release gates |
| Skills | [Skill Index](SKILL_INDEX.md) | Review available specialists and routing behavior |
| Installation | [Installation Guide](docs/setup/INSTALLATION.md) | Set up the plugin in Antigravity or Codex |
| Validation | [Validation Guide](docs/setup/VALIDATION.md) | Run structure and manifest checks |
| Contributing | [Contributing Guide](docs/CONTRIBUTING.md) | Guidelines for contributing and safety policies |
| Disclaimer | [Disclaimer](docs/meta/DISCLAIMER.md) | Understand legal and operational limitations |

## Validation & Enforceable Governance

Before releasing, staging, or pushing changes, run the centralized behavior validation suite:

```powershell
# Run all validation checks (structure, manifest, stale references, and locking tests)
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\behavior\run-tests.ps1
```

### Governance Verification Workflow
- **Centralized Test Runner (`run-tests.ps1`)**: Verifies project directory structure, manifest definitions against skill frontmatter, stale reference checks, Codex skill adapter alignment, and lock/guardrail regression cases.
- **Opt-In Runtime Guardrails**: Scans staged or modified files for security risks (secrets, copyleft licenses, PII leaks, destructive commands, or stale naming conventions).
  - *Warning-Only Mode (Default)*: Scans are advisory and exit with code `0`.
  - *Strict Enforcement*: Set `$env:ORCHESTRA_ENFORCE_GUARDRAILS = "true"` to fail the build (exit code `1`) upon safety violations.
- **Workspace State Locking**: Manages a `.amalgam/lock.json` file during workflow executions to prevent concurrent agent collisions, automatically detecting and cleaning stale locks based on process ID (PID) liveness.

For full configuration and usage instructions, see the [Validation & Enforceable Governance Guide](docs/setup/VALIDATION.md).

---

## Limitations

- **Instruction-Level Enforcement:** The framework operates at the instruction and documentation level. There are no automated runtime blocks preventing a developer or agent from executing unapproved actions.
- **Project Profile Requirement:** Governance relies entirely on the accuracy and completeness of the provided project context profile.

## Collapsed Repository Structure

GitHub displays repository files above the README by default. This README keeps detailed documentation layered into linked files and collapsed sections to reduce scrolling.

<details> <summary>Repository structure</summary>

```
skills/
├── chronicler/
├── cipher/
├── cloak/
├── clockwork/
├── conductor/
├── dagger/
├── overseer/
├── scribe/
├── the-governor/
├── the-steward/
└── weaver/

docs/
├── CONTRIBUTING.md
├── governance/
│   ├── GOVERNANCE_LAYER.md
│   ├── GOVERNOR.md
│   ├── STEWARD.md
│   ├── GOVERNANCE_REVIEW_FLOW.md
│   └── RELEASE_GATES.md
├── meta/
│   ├── CHANGELOG.md
│   └── DISCLAIMER.md
├── project/
│   ├── FOUNDATION.md
│   ├── ROADMAP.md
│   ├── PLUGIN_READINESS.md
│   ├── MANIFEST_SCHEMA.md
│   └── V1_READINESS_CHECKLIST.md
└── setup/
    ├── INSTALLATION.md
    ├── LOCAL_ONLY_GUIDE.md
    ├── COMPATIBILITY.md
    └── VALIDATION.md

tests/behavior/
└── GOVERNANCE_SCENARIOS.md

assets/readme/
└── orchestra-governance-banner.svg
```

</details>

## Disclaimer

> [!CAUTION]
> The Governor and Steward skills validate compliance frameworks, scope, and best practices. They do not provide legal advice or absolute security guarantees. Please read [docs/meta/DISCLAIMER.md](docs/meta/DISCLAIMER.md) for full terms.
