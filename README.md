<div align="center">
  <img src="./assets/readme/amalgam-governance-banner.svg" alt="Amalgam Conductor Hero Banner" width="100%" />

  <p>
    <strong>Project-agnostic governance and orchestration framework for AI-assisted development.</strong>
  </p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> •
    <a href="docs/governance/GOVERNANCE_LAYER.md">Governance</a> •
    <a href="SKILL_INDEX.md">Skills</a> •
    <a href="docs/setup/VALIDATION.md">Validation</a>
  </p>
</div>

---

## At a Glance

| Layer | Role | Purpose |
|---|---|---|
| Governance | The Steward | Business, scope, SDLC, requirements, and value alignment |
| Governance | The Governor | Legal risk, privacy, IP, licensing, security, and compliance review |
| Orchestration | Amalgam Conductor | Routes approved work to the correct specialist skills |
| Execution | Specialist Skills | Performs focused implementation, documentation, QA, security, or design work |

## Core Concept

Amalgam Conductor uses a governance-first workflow, but the governance layer does not assume what rules apply to every project. Before review, The Steward and The Governor identify the project context, declared objectives, release target, data use, dependencies, documentation requirements, and known constraints. The Steward then checks alignment against the project’s stated goals, scope, requirements, acceptance criteria, and SDLC needs. The Governor checks only the applicable legal-risk, privacy, IP, licensing, security, and compliance areas based on the supplied project context. If the scope is unclear, governance returns REVISION_REQUIRED instead of assuming.

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

    subgraph G[Governance Layer]
      Steward{{The Steward<br/>Business • Scope • SDLC}}:::gov
      Governor{{The Governor<br/>Privacy • IP • Compliance}}:::gov
    end

    subgraph O[Orchestration Layer]
      Conductor((Amalgam<br/>Conductor)):::orch
    end

    subgraph E[Execution Layer]
      Skills[[Specialist Skills]]:::exec
      Validate[[Validation]]:::exec
    end

    Output([Release or Response]):::input
    Revision([Revision Required<br/>or Blocked]):::stop

    Request --> Context --> Steward --> Governor --> Conductor --> Skills --> Validate --> Output
    Steward -.-> Revision
    Governor -.-> Revision
```

---

## Governance Layer

The Governance Layer sits above the Conductor. It intercepts incoming requests, identifies the minimum project context required, and performs a risk-scaled review (LOW, MEDIUM, or HIGH) before any implementation begins. 

The Steward and The Governor are entirely context-driven. They do not pre-assume what rules apply to every project, nor do they apply every governance rule universally. If the project scope is unclear or missing, governance returns `REVISION_REQUIRED` instead of assuming. Conversely, if a risk area does not apply to the current context, the authority returns `NOT_APPLICABLE`.

> [!IMPORTANT]
> If a request violates alignment, fails scope verification, or breaches compliance boundaries, the Steward or Governor issues a `REVISION_REQUIRED` or `BLOCKED` status. The Conductor will immediately halt execution.

### Compact Decision Examples

#### Example 1: Incomplete Project Scope
```yaml
Reviewer: The Steward
Decision: REVISION_REQUIRED
Reason: Project scope is incomplete.
Risks: The request cannot be checked against goals, requirements, or acceptance criteria.
Required Actions:
- Provide project type.
- Provide intended outcome.
- Provide acceptance criteria.
Human Review Required: No.
```

#### Example 2: Non-Applicable Request
```yaml
Reviewer: The Governor
Decision: NOT_APPLICABLE
Reason: The request is a local formatting-only documentation update with no release, user data, licensing, privacy, IP, or security impact.
Risks: None.
Required Actions: None.
Human Review Required: No.
```

### The Steward

Validates business alignment, scope boundaries, and software development lifecycle (SDLC) documentation. It ensures changes stay within the scope of work and meet defined acceptance criteria.

### The Governor

Evaluates legal compliance, privacy risks, intellectual property (IP), licensing, and security policies. It flags high-risk regulatory or legal matters for manual human review and does not provide formal legal advice.

---

## The Amalgam Conductor

The Amalgam Conductor operates in the Orchestration Layer. Once governance clearance is granted:
- It defines execution steps and establishes architectural boundaries.
- It sequences actions to prevent multi-file conflicts and overlapping agent reviews.
- It routes implementation tasks to the correct specialized skills.

## Specialist Skills

| Skill | Focus |
|---|---|
| <img src="assets/icons/amalgam-conductor.png" width="24" align="absmiddle" /> **Amalgam Conductor** | Routing and orchestration |
| <img src="assets/icons/theSteward.png" width="24" align="absmiddle" /> **The Steward** | Business, scope, SDLC, and requirements alignment |
| <img src="assets/icons/theGovernor.png" width="24" align="absmiddle" /> **The Governor** | Privacy, IP, licensing, compliance, and legal-risk review |
| <img src="assets/icons/clockwork-meister.png" width="24" align="absmiddle" /> **Clockwork Meister** | Architecture, OOP, refactoring |
| <img src="assets/icons/cloak-meister.png" width="24" align="absmiddle" /> **Cloak Meister** | UI, UX, layout, accessibility |
| <img src="assets/icons/scribe-meister.png" width="24" align="absmiddle" /> **Scribe Meister** | Documentation and technical writing |
| <img src="assets/icons/acme-overseer.png" width="24" align="absmiddle" /> **Acme Overseer** | QA, testing, release readiness |
| <img src="assets/icons/cipher-meister.png" width="24" align="absmiddle" /> **Cipher Meister** | Security and privacy evidence |

For details on all execution skills, routing logic, and behavioral constraints, see the [Specialist Skill Index](SKILL_INDEX.md).

---

## Installation

To set up Amalgam Conductor as an installable AI workflow plugin:

### Antigravity Setup
```sh
agy plugin install https://github.com/Baelfyre/amalgam-conductor
```

### Codex Setup
Clone this repository directly into your Codex plugins directory:
```sh
git clone https://github.com/Baelfyre/amalgam-conductor.git
```

For manual configurations or environment setup details, see the [Installation Guide](docs/setup/INSTALLATION.md).

## How to Use

The plugin operates on a structured, context-first prompt pattern. 

### Step 1: Provide Project Context
Identify the project context profile (Project Type, Sensitivity, Jurisdiction, etc.) so the Governance Layer can properly scale its review risk.

### Step 2: Use the Governance-First Prompt Pattern
Always structure your requests to invoke the orchestrator with the necessary context and clear execution goals.

## Recommended Prompt Workflow

Use this format to initiate tasks:

```markdown
[@ponytail] use amalgam-conductor for this task

Task:
Describe the work clearly.

Context:
Provide the project type, current files, constraints, and goal.

Requirements:
List what must be changed or preserved.

Expected Output:
Changed Files:
Summary:
Validation Results:
Remaining Risks:
Next Recommended Step:
```

## Token-Efficient Usage

> [!TIP]
> - Start with a refined prompt.
> - Provide only relevant context.
> - Ask for changed files, summary, validation, risks, and next step.
> - Use expanded governance only for medium-risk or high-risk work.
> - Use fast path for typo fixes, formatting, and local documentation cleanup.
> - Link to detailed governance docs instead of repeating them in README.

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

## Validation

Before releasing or pushing changes, verify the plugin structural integrity and manifest alignment:

```powershell
# Verify files, directories, and icon overrides
powershell -ExecutionPolicy Bypass -File .\scripts\validate-structure.ps1

# Verify manifest properties against skill frontmatter
powershell -ExecutionPolicy Bypass -File .\scripts\validate-manifest.ps1
```
For more information, see the [Validation Guide](docs/setup/VALIDATION.md).

---

## Limitations

- **Instruction-Level Enforcement:** The framework operates at the instruction and documentation level. There are no automated runtime blocks preventing a developer or agent from executing unapproved actions.
- **Project Profile Requirement:** Governance relies entirely on the accuracy and completeness of the provided project context profile.

## Collapsed Repository Structure

GitHub displays repository files above the README by default. This README keeps detailed documentation layered into linked files and collapsed sections to reduce scrolling.

<details> <summary>Repository structure</summary>

```
skills/
├── amalgam-conductor/
├── the-governor/
└── the-steward/

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
└── amalgam-governance-banner.svg
```

</details>

## Disclaimer

> [!CAUTION]
> The Governor and Steward skills validate compliance frameworks, scope, and best practices. They do not provide legal advice or absolute security guarantees. Please read [docs/meta/DISCLAIMER.md](docs/meta/DISCLAIMER.md) for full terms.
