# GitHub Copilot Instructions for Orchestra Workspace

When working in an Orchestra workspace, adhere to the following routing and execution architecture:

## 1. Conductor Sole Router
Always route domain requests through the Conductor:
- Do not invent custom multi-agent chains.
- Do not mix domain specialist responsibilities.

## 2. Specialist Ownership
- Architecture / OOP / Refactoring: `clockwork`
- UI / UX / Design: `cloak`
- Security / Access Control / Secrets: `cipher`
- Persistence / DB / Migrations: `chronicler`
- Visual Models / Diagrams: `weaver`
- Documentation / Traceability: `scribe`
- QA / Validation / Readiness: `overseer`
- Chaos / Resilience: `dagger` (simulation only)
- Continuity / Transitions: `arbiter`
- Cross-Domain Coordination: `the-tuner`
- Implementation: `ponytail` (minimal safe diffs)

## 3. Governance
- Business alignment: `the-steward`
- Legal & Compliance: `the-governor`
- The Conductor cannot override governance decisions.

## 4. Invariants
- Host capability does not grant execution authority.
- Do not make broad refactors during targeted bug fixes.
- Run project validations after modifications.
