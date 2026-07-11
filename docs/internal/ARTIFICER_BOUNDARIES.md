# Artificer & Specialist Boundaries

To maintain a strict separation of concerns, Artificer operates within rigid boundaries. It does not perform implementation or validation actions itself, deferring instead to Orchestra's existing specialists.

## Boundary Matrix

| Specialist | Domain Responsibility | Artificer Boundary (What Artificer Must NOT Do) |
|---|---|---|
| **Artificer** | Intake, static architecture/pattern audit, classification, evolution proposal | Must never write implementation code, modify plugin configs, or run tests. |
| **Cloak** | Frontend styling, UI components, layouts, visual reconstruction, and UX behavior | Artificer must not implement UI code. Cloak does not validate ZIP files or sandbox security. |
| **Cipher** | Encryption, sandboxing, tracking, auth boundaries, secrets, script verification | Artificer does not configure security policy or evaluate sandbox escapes. |
| **Clockwork** | Runtime boundaries, OOP structures, service layering, backend patterns | Artificer does not rewrite backend frameworks or define component interfaces. |
| **Ponytail** | Focus-scoped minimal implementations and refactor edits | Artificer does not edit source files of the active repository. |
| **Overseer** | QA, unit tests, integration validation, CI checks, release readiness | Artificer does not write unit tests or execute test runners. |
| **Dagger** | Authorized adversarial testing, chaos engineering, resilience checks | Artificer does not perform penetration testing or live vulnerability runs. |
| **Arbiter** | Evidence adjudication, duplicate resolution, transition safety validation | Artificer does not decide if a pattern is a duplicate or if evidence is complete. |
| **The Governor** | Legal compliance, license verification, privacy, copyright validation | Artificer reports licensing, but cannot approve license compliance or IP clearance. |
| **The Steward** | Business alignment, scope, and SDLC planning | Artificer documents recommendations, but cannot redefine project scope or goals. |

## Correct Specialist Mapping

When a design pattern is identified, it must be assigned to the correct specialist based on its functional nature:

- **Safe visual reconstruction / UX**: Map to **Cloak** (e.g., UI widgets, responsive grids, style adaptations).
- **Security-sensitive / CSP / sanitizers / file extraction**: Map to **Cipher** (e.g., zip extractors, script sanitization, sandbox controls).
- **Backend layering / interface design / component boundary**: Map to **Clockwork** (e.g., service registries, adapter interfaces).
- **QA / verification checks / regression testing**: Map to **Overseer** (e.g., test cases, verification scripts).
- **Chaos testing / failure path validation**: Map to **Dagger** (e.g., boundary condition fuzzing).
- **Attribution / copyright headers / licensing compatibility**: Map to **The Governor**.
- **Implementation**: Map to **Ponytail** for final code changes.
