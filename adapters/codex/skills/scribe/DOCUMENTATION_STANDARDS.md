# Documentation Standards

Use only the sections relevant to the document. Evidence and project requirements override generic structure.

## Source-Backed Documentation
- Map important claims to source evidence, specialist output, or verified project artifacts.
- Mark unverified, draft, planned, blocked, skipped, or not-run items explicitly.
- Do not present proposals, assumptions, or planned work as completed behavior.

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

## Decision Log

- Record context, decision, alternatives, rationale, consequences, status, and date.
- Preserve superseded decisions and link replacements.
- Avoid presenting an unapproved proposal as a decision.

## Final Project or Release Submission

- Follow the rubric and required format before generic best practices.
- Map objectives and requirements to implementation and test evidence.
- Include scope, limitations, architecture, database, testing, known issues, and contribution records only when required.
- Verify file names, links, diagrams, screenshots, citations, and build instructions.
- Remove secrets, personal data, temporary prompts, and local Codex configuration.
