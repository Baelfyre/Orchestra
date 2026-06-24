# Skill Index

| Name | Slug | Role | Primary Use | Avoid When | Activation | Depends On | Output Formats |
|---|---|---|---|---|---|---|---|
| The Steward | `the-steward` | Business Alignment and Scope Governance Authority | Business alignment, scope, requirements, SDLC documentation | Legal, compliance, IP, licensing review | Governor | None | Governance Review |
| The Governor | `the-governor` | Legal, Compliance, Privacy, and IP Governance Authority | Legal compliance, privacy, IP, copyright, licensing, audit | Business alignment, scope, requirements review | Governor | None | Governance Review |
| Amalgam Conductor | `amalgam-conductor` | Routing and orchestration layer | Project orientation, multi-skill routing, workflow planning | A single obvious specialist suffices | Commander | None | Routing Plan, Prompts |
| Cloak Meister | `cloak-meister` | UI/UX architect and frontend auditor | UI, UX, accessibility, frontend architecture, responsive layout | Database schema or system architecture diagraming is needed | Specialist | None | QUICK_UI_HANDOFF, DOCUMENT_REVIEW, FORMAL_UI_AUDIT |
| Scribe Meister | `scribe-meister` | Documentation compiler and auditor | READMEs, project reports, readiness summaries, handover docs | Source evidence is unavailable to verify claims | Specialist | None | Mode 1, Mode 2, Mode 3 |
| Meister Weaver | `meister-weaver` | Visual modeling and diagram specialist | UML, ERD, architecture, workflow, data-flow diagrams | Resolving UI accessibility or evaluating functional code without diagrams | Specialist | None | Mermaid, PlantUML |
| Meister Chronicler | `meister-chronicler` | Database architect and schema auditor | Schemas, ERDs, constraints, migrations, SQL validation | Evaluating visible UI or system-level testing | Specialist | None | Caveman, Normalization Output |
| Acme Overseer | `acme-overseer` | Quality assurance auditor and release gatekeeper | Test strategy, test cases, defect triage, regression, release readiness | Destructive pressure testing is needed | Specialist | None | Caveman |
| Cipher Meister | `cipher-meister` | Security and privacy auditor | Defensive review, RBAC, data protection, sensitive data handling | Offensive or destructive testing is needed | Specialist | None | Caveman |
| Hidden Dagger | `hidden-dagger` | Controlled resilience tester | Destructive, negative, fuzz, adversarial QA, failure-mode testing | Operating in production, lacking explicit approval, or during early dev | Gated | `amalgam-conductor` | Output |
| Clockwork Meister | `clockwork-meister` | Engineering / Code Structure | OOP architecture, layered architecture, system design, refactoring | Modifying UI layouts, testing security boundaries, or writing documentation | Specialist | None | Compact, Full |

Note: `The Steward` and `The Governor` are governance authorities that evaluate request intent, risk, alignment, and compliance. They do not implement changes or act as execution specialists.

---

*Please review our [Global Disclaimer](docs/meta/DISCLAIMER.md) regarding the use of these AI-assisted tools.*
