# Documentation Standards

Use only the sections relevant to the document. Evidence and project requirements override generic structure.

## Source-Backed Documentation
- Map important claims to source evidence, specialist output, or verified project artifacts.
- Mark unverified, draft, planned, blocked, skipped, or not-run items explicitly.
- Do not present proposals, assumptions, or planned work as completed behavior.
- Record source revision, last-verified date, and effective date where claims can drift.

## Markdown and Rendering

- Use one document title, hierarchical headings without skipped levels, fenced code blocks with language identifiers, and blank lines that render consistently under the target CommonMark/GFM implementation.
- Prefer descriptive link text and repository-relative links for versioned local content. Keep explicit HTML rare and renderer-tested.
- Keep tables simple, escape literal pipes, and provide a list or prose alternative when a wide table harms accessibility or narrow rendering.
- Treat generated heading anchors as renderer-specific. Validate fragments after renaming headings.

## README

- State purpose, target user, current status, and primary capabilities.
- Provide tested prerequisites, setup, run, test, and build commands.
- Explain configuration without exposing secrets.
- Link architecture, database, API, and contribution details instead of duplicating them.
- Mark limitations, known issues, and unsupported platforms honestly.

## Requirements

- Give each requirement a stable identifier when traceability matters.
- Write observable, testable statements with one obligation per item.
- Separate functional behavior from quality constraints and external rules.
- Record source, priority, acceptance evidence, dependencies, and unresolved assumptions.
- Avoid vague terms such as fast, intuitive, secure, or user-friendly without criteria.

## Architecture Summary

- State scope, system boundary, major components, responsibilities, data stores, and external systems.
- Describe current behavior separately from proposals.
- Link diagrams and architecture decisions to code or configuration evidence.
- Record important constraints, tradeoffs, trust boundaries, and failure behavior.

## System Readiness

- Map readiness criteria to verified evidence.
- Separate passed, failed, blocked, and not-run checks.
- Include build, test, integration, security, accessibility, data, deployment, and documentation status only when relevant.
- Name blockers, owners, and next actions without inventing completion dates.

## Testing Documentation

- State scope, environment, data, command, result, and date or revision when needed.
- Distinguish automated, manual, smoke, regression, and acceptance evidence.
- Do not convert planned tests into passed tests.
- Link failures and skipped checks to known issues or follow-up work.

## User Guide

- Organize around user goals and prerequisites.
- Provide numbered tasks, expected results, recovery guidance, and screenshots only when maintained.
- Use interface labels exactly as shown.
- Include accessibility or role limitations relevant to task completion.

## Developer Guide

- Document supported environment, repository structure, setup, architecture boundaries, test commands, data setup, and debugging entrypoints.
- Explain generated files and files that must remain local.
- Prefer commands verified in the current repository.

## Change Log

- Record user-visible changes by release or milestone.
- Separate added, changed, fixed, deprecated, removed, and security items when useful.
- Link changes to verified commits, issues, or release evidence.
- Do not use the change log as a raw commit dump.
- Keep an `Unreleased` or pending section when the repository uses one; move entries only when release evidence exists.
- Distinguish deprecation from removal and include migration guidance when user action is required.

## Decision Log

- Record context, decision, alternatives, rationale, consequences, status, and date.
- Preserve superseded decisions and link replacements.
- Avoid presenting an unapproved proposal as a decision.
- Give ADRs stable identifiers and immutable accepted content; supersede with a new decision that links both directions.

## API and Versioned Documentation

- Derive operations, schemas, examples, errors, authentication references, and compatibility claims from the reviewed API contract and implementation evidence.
- Label example values and redact credentials or personal data. Verify examples against the documented version where executable validation is available.
- Keep current, previous-supported, and archived documentation visibly distinct. Define version selector, canonical URL, redirects, deprecation, migration, and sunset behavior from approved policy.

## Link and Claim Validation

- Check local targets, case sensitivity, fragments, reference definitions, image/media paths, redirects, and external-source authority.
- Report inaccessible external links as unverified rather than silently replacing or deleting supported claims.
- Revalidate commands, versions, dates, status badges, screenshots, and release claims after their source revision changes.

## Final Project or Release Submission

- Follow the rubric and required format before generic best practices.
- Map objectives and requirements to implementation and test evidence.
- Include scope, limitations, architecture, database, testing, known issues, and contribution records only when required.
- Verify file names, links, diagrams, screenshots, citations, and build instructions.
- Remove secrets, personal data, temporary prompts, and local Codex configuration.
