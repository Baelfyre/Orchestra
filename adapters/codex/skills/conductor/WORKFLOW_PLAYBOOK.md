# Workflow Playbook

Verify exact skill availability before routing. Replace capability labels with installed skill names when possible.

## Contents

- [New Project Scan](#new-project-scan)
- [UI Improvement](#ui-improvement)
- [Diagram Review](#diagram-review)
- [Database Cleanup](#database-cleanup)
- [OOP Refactor](#oop-refactor)
- [Quality Review](#quality-review)
- [Security and Privacy Review](#security-and-privacy-review)
- [Dagger Gated Resilience](#dagger-gated-resilience)
- [Documentation Cleanup](#documentation-cleanup)
- [Final Submission Readiness](#final-submission-readiness)
- [Portfolio Polish](#portfolio-polish)

## New Project Scan

### When to use
Use when the repository or task is unfamiliar and the user wants orientation or a plan.

### Required skills
- Conductor only initially; add one architecture or domain specialist after detection.

### Step-by-step execution
1. Read user instructions and repository guidance.
2. Inspect root manifests, source roots, docs index, diagrams, and Git status.
3. Identify primary and secondary project types with evidence.
4. Route the stated goal to the smallest specialist stack.

### Expected outputs
- Evidence-backed project profile, scoped skill stack, sequence, risks, and prompts.

### Verification checklist
- [ ] No whole-repository scan without need.
- [ ] Exact skill names verified.
- [ ] No project files changed.
- [ ] Confidence and missing context stated.

## UI Improvement

### When to use
Use for layout, interaction, accessibility, responsiveness, JavaFX screens, or visual hierarchy.

### Required skills
- `cloak`; frontend, React, or JavaFX specialist only for implementation.

### Step-by-step execution
1. Inspect the rendered artifact and relevant component or view files.
2. Produce confirmed UX findings and prioritize the smallest fix.
3. Implement with the matching framework specialist when requested.
4. Run build or compile plus rendered desktop/mobile checks.

### Expected outputs
- UX review, bounded patch, and visual or behavioral verification.

### Verification checklist
- [ ] Existing theme and structure preserved.
- [ ] Accessibility basics retained.
- [ ] Requested viewport or window states checked.
- [ ] No unrelated redesign.

## Diagram Review

### When to use
Use for ERD, UML, sequence, architecture, deployment, or documentation diagrams.

### Required skills
- `weaver`; relevant domain specialist for semantic correctness; `cloak` only for user-facing presentation or readability.

### Step-by-step execution
1. Identify diagram type, audience, scope, notation, and source of truth.
2. Review clarity and domain correctness separately.
3. Propose Mermaid, PlantUML, or tool-specific revisions.
4. Render or parse the corrected artifact when possible.

### Expected outputs
- Severity-ranked review, corrected guidance, and missing evidence.

### Verification checklist
- [ ] No entities or components invented.
- [ ] Relationships and notation validated.
- [ ] Diagram agrees with available source artifacts.
- [ ] Original preserved unless overwrite was requested.

## Database Cleanup

### When to use
Use for schema consistency, constraints, normalization, migrations, seed data, or live-data repair.

### Required skills
- `chronicler`; `overseer`; `cipher` when access or sensitive data is involved.

### Step-by-step execution
1. Determine whether the target is a design artifact, migration, seed, or live database.
2. Inspect affected rows, tables, constraints, and application paths.
3. Propose the narrowest repair and obtain approval for mutations.
4. Capture pre-state, apply the approved change, and verify post-state.

### Expected outputs
- Evidence, migration or repair plan, validation queries, and rollback notes.

### Verification checklist
- [ ] Backup or rollback path identified.
- [ ] Pre-state and post-state compared.
- [ ] Constraints and application behavior verified.
- [ ] No secrets exposed.

## OOP Refactor

### When to use
Use when a demonstrated responsibility, coupling, cohesion, inheritance, or layering problem blocks change or testing.

### Required skills
- Available Java/OOP or architecture specialist; `overseer`.

### Step-by-step execution
1. Trace the affected use case through current classes.
2. Identify the smallest concrete design problem.
3. Refactor without speculative interfaces or layers.
4. Compile and run the narrowest behavior check.

### Expected outputs
- Focused design finding, small diff, and regression evidence.

### Verification checklist
- [ ] Public behavior preserved unless change was requested.
- [ ] No unnecessary abstraction added.
- [ ] Dependency direction improved or unchanged.
- [ ] Focused tests pass.

## Quality Review

### When to use
Use for QA, testing, test plans or cases, defects, regression, smoke tests, acceptance criteria, verification, validation, quality gates, or release readiness.

### Required skills
- `overseer`

### Step-by-step execution
1. Identify the quality objective and available test evidence.
2. Review requirements testability, acceptance criteria, test structure, and coverage.
3. Identify defect, regression, and release risks.
4. Recommend priority fixes and reproducible retest steps.

### Expected outputs
- Evidence-based quality review, missing evidence, priority fixes, and release recommendation.

### Verification checklist
- [ ] Test results and pass/fail claims are not invented.
- [ ] Missing evidence is marked.
- [ ] Dagger is not used as the normal QA route.

## Security and Privacy Review

### When to use
Use for security, privacy, data protection, authentication, authorization, RBAC, secrets, API or dependency risk, sensitive data, or secure SDLC review.

### Required skills
- `cipher`; add Codex Security only when source-level scanning is required.

### Step-by-step execution
1. Identify protected assets, data, trust boundaries, and supplied evidence.
2. Review relevant authentication, authorization, sensitive data, secrets, dependencies, logging, and privacy controls.
3. Separate confirmed risks from assumptions and validate reachable paths when code is available.
4. Recommend defensive fixes, verification, and documentation updates.

### Expected outputs
- Security/privacy review, risk findings, missing evidence, and defensive remediation plan.

### Verification checklist
- [ ] No offensive exploit chain is produced.
- [ ] Vulnerabilities are not invented.
- [ ] Scanner claims are validated when a scanner is used.
- [ ] Privacy risks are separated from legal advice.

## Dagger Gated Resilience

### When to use
Recommend only for an explicitly requested adversarial test or a mature QA, staging, release-candidate, pre-production, or final-readiness project with high-risk gaps. Invoke only after the user chooses it and the safety gate passes.

### Required skills
- `dagger`

### Recommended prerequisites
- `overseer` for normal QA coverage
- `cipher` for security/privacy risk
- `chronicler` for database constraints
- `cloak` for UI/frontend validation

### Step-by-step execution
1. Confirm project maturity, authorization, non-production isolation, scope, disposable data, backup, rollback, cleanup, and stop conditions.
2. Obtain explicit approval before risky execution.
3. Create the smallest destructive or negative test plan.
4. Run or recommend only approved tests and capture evidence.
5. Score resilience provisionally when evidence is incomplete.
6. Recommend fixes and exact retest steps.

### Expected outputs
- Safety gate, approved test plan, scorecard, confirmed failures, suspected weaknesses, missing evidence, and retest plan.

### Verification checklist
- [ ] Production and real user data are excluded.
- [ ] User approval is recorded before risky tests.
- [ ] No offensive exploit chain is produced.
- [ ] Untested areas and cleanup are recorded.

## Documentation Cleanup

### When to use
Use for README files, reports, design logs, handoffs, or project documentation.

### Required skills
- `scribe`; domain specialist for fact verification.

### Step-by-step execution
1. Identify audience, rubric, and source of truth.
2. Verify commands and technical claims.
3. Remove duplication and repair only required sections.
4. Validate links, formatting, diagrams, and examples.

### Expected outputs
- Concise, accurate documentation and a validation summary.

### Verification checklist
- [ ] Commands tested or marked unverified.
- [ ] Claims trace to current artifacts.
- [ ] Local Codex files excluded.
- [ ] No unnecessary auxiliary documents created.

## Final Submission Readiness

### When to use
Use before formal submission, release handoff, or evaluation.

### Required skills
- Testing, documentation, UX, security, or domain specialists only where the rubric or changed surface requires them.

### Step-by-step execution
1. Read the rubric or acceptance criteria.
2. Map each criterion to evidence.
3. Run focused build, tests, smoke checks, and document validation.
4. List blockers and obtain approval before publication actions.

### Expected outputs
- Readiness matrix, verified evidence, blockers, and shortest completion path.

### Verification checklist
- [ ] Required artifacts present.
- [ ] Build and required tests pass.
- [ ] Security-sensitive paths reviewed when relevant.
- [ ] Git status shown before any commit recommendation.
- [ ] No commit, push, or PR performed automatically.

## Portfolio Polish

### When to use
Use when improving presentation, accessibility, project narrative, or demo readiness for a portfolio.

### Required skills
- `cloak`; frontend specialist; `scribe` when project copy changes.

### Step-by-step execution
1. Identify target audience and desired action.
2. Review task flow, hierarchy, accessibility, responsive behavior, and evidence of outcomes.
3. Implement only high-impact issues.
4. Build, render, and verify links and representative viewports.

### Expected outputs
- Prioritized polish plan, scoped implementation, and demo verification.

### Verification checklist
- [ ] Project remains authentic and technically accurate.
- [ ] Accessibility and mobile layout checked.
- [ ] Media and performance risks measured.
- [ ] No broad redesign without evidence.
