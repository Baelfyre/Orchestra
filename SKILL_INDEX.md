# Skill Index

| Name | Slug | Role | Primary Use | Avoid When | Activation | Depends On | Output Formats |
|---|---|---|---|---|---|---|---|
| The Steward, Business Alignment | `the-steward` | Business Alignment and Scope Governance Authority | Business alignment, scope, requirements, SDLC documentation | Legal, compliance, IP, licensing review | Governor | None | Governance Review |
| The Governor, Legal and Compliance | `the-governor` | Legal, Compliance, Privacy, and IP Governance Authority | Legal compliance, privacy, IP, copyright, licensing, audit | Business alignment, scope, requirements review | Governor | None | Governance Review |
| Conductor, Routing | `conductor` | Routing and orchestration layer | Project orientation, multi-skill routing, workflow planning, access/visibility routing | A single obvious specialist suffices | Commander | None | Routing Plan, Prompts |
| Arbiter, Continuity and Validation | `arbiter` | Workflow Continuity, Validation, and Transition Governance Specialist | Continuity review, validation-state review, branch and merge readiness, source-of-truth checks, handoff readiness, access/visibility closeout | Designing architecture, implementing features, writing documentation content, or replacing normal QA ownership | Governance | `conductor` | Continuity Review |
| Cloak, UI and Accessibility | `cloak` | UI/UX architect and frontend auditor | UI, UX, accessibility, frontend architecture, responsive layout | Database schema or system architecture diagraming is needed | Specialist | None | QUICK_UI_HANDOFF, DOCUMENT_REVIEW, FORMAL_UI_AUDIT |
| Scribe, Documentation | `scribe` | Documentation compiler and auditor | READMEs, project reports, readiness summaries, handover docs | Architecture decisions, database design, normalization analysis, UI design, diagram generation, or code implementation | Specialist | None | Mode 1, Mode 2, Mode 3 |
| Weaver, Visual Modeling | `weaver` | Visual modeling and diagram specialist | UML, ERD, architecture, workflow, data-flow diagrams | Resolving UI accessibility or evaluating functional code without diagrams | Specialist | None | Mermaid, PlantUML |
| Chronicler, Database and Schema | `chronicler` | Database architect and schema auditor | Schemas, ERDs, constraints, migrations, SQL validation | Evaluating visible UI or system-level testing | Specialist | None | Caveman, Normalization Output |
| Overseer, QA and Release Readiness | `overseer` | Quality assurance auditor and release gatekeeper | Test strategy, test cases, defect triage, regression, release readiness, persona validation | Destructive pressure testing is needed | Specialist | None | Caveman, Full QA Review |
| Cipher, Security and Privacy | `cipher` | Security and privacy auditor | Defensive review, RBAC, data protection, sensitive data handling, visibility/access-control | Offensive or destructive testing is needed | Specialist | None | Caveman, Full Security Review |
| Dagger, Resilience Testing | `dagger` | Controlled resilience tester | Destructive, negative, fuzz, adversarial QA, failure-mode testing | Operating in production, lacking explicit approval, or during early dev | Gated | `conductor` | Caveman |
| Clockwork, Architecture and Refactoring | `clockwork` | Engineering / Code Structure | OOP architecture, layered architecture, system design, refactoring | Modifying UI layouts, testing security boundaries, or writing documentation | Specialist | None | Compact, Full |
| Ponytail, Implementation | `ponytail` | Implementation and Navigation Specialist | Implementation, code editing, validation | Architecture design, UI/UX decisions, security policies | Specialist | None | IMPLEMENTATION_PLAN, CODE_REVIEW, QUICK_FIX |


Note: `The Steward` and `The Governor` are governance authorities that evaluate request intent, risk, alignment, and compliance. They do not implement changes or act as execution specialists.

---

*Please review our [Global Disclaimer](docs/meta/DISCLAIMER.md) regarding the use of these AI-assisted tools.*
