# PROJECT_CONTEXT Enforcement Policy

## Purpose

This document defines a context-sensitive policy for when `PROJECT_CONTEXT.md` should remain advisory, when it should be strongly recommended, and when it should become a blocking governance requirement.

The goal is not to make `PROJECT_CONTEXT.md` universally mandatory. The goal is to scale governance according to project type, coordination needs, and real-world risk.

## Enforcement Principle

`PROJECT_CONTEXT.md` enforcement should depend on project classification and risk level.

- low-risk, exploratory, educational, and sandbox work should stay advisory by default
- moderate coordination work should receive stronger recommendations without default blocking
- real-world, real-data, compliance-sensitive, destructive, or release-critical work should require `PROJECT_CONTEXT.md` as a gated validation item

The Steward owns classification and context sufficiency. The Governor should only participate in blocking enforcement after the project is classified as strict-governed, a maintainer explicitly requests strict enforcement, or release governance requires it.

## Project Classification Levels

### Advisory

Use for:

- school projects
- learning repos
- experiments
- prototypes
- throwaway demos
- personal sandbox projects

Behavior:

- missing `PROJECT_CONTEXT.md` should produce a warning or recommendation only
- validation should not block CI by default
- incomplete context should not become a hard failure unless a higher-risk mode is explicitly requested

### Recommended

Use for:

- active internal tools
- portfolio projects intended for reuse
- multi-agent development repos
- projects with moderate coordination needs

Behavior:

- missing `PROJECT_CONTEXT.md` should produce a stronger warning
- validation may report advisory failure or visible warning status
- CI should not block unless maintainers explicitly configure stricter behavior

### Strict-Governed

Use for:

- real-world projects
- production projects
- client-facing projects
- projects with real-world user data
- projects with sensitive business data
- projects with security, legal, financial, medical, or privacy implications
- destructive automation workflows
- release-critical repos

Behavior:

- missing `PROJECT_CONTEXT.md` should be a blocking validation failure
- incomplete `PROJECT_CONTEXT.md` should be a blocking validation failure when required sections are missing
- governance enforcement should be treated as part of release and operational safety, not as optional documentation polish

## Risk Signals

The following signals push a project toward `Strict-Governed` classification:

- real user data
- client data
- production deployment
- legal or compliance exposure
- financial or billing data
- authentication or authorization logic
- destructive actions
- secrets or credential handling
- medical, legal, HR, or education records
- public release or marketplace publication
- multi-agent automation with write permissions

A single signal does not always force strict governance by itself, but multiple signals or any clearly high-risk signal should trigger a Steward recommendation toward `Strict-Governed`.

## Enforcement Modes

### Advisory Mode

- `PROJECT_CONTEXT.md` is recommended, not required
- warnings should explain why more context would help
- validation output should preserve exploration and low-friction workflows

### Recommended Mode

- `PROJECT_CONTEXT.md` is strongly encouraged
- missing or thin context should be visible in governance output
- blocking should remain opt-in unless maintainers explicitly promote the repository to stricter enforcement

### Strict-Governed Mode

- `PROJECT_CONTEXT.md` is required
- required sections must be present and materially complete
- blocking validation is appropriate because project context is part of safety, scope control, and release discipline

## Required Strict-Governed PROJECT_CONTEXT Sections

Strict-governed projects should include at least:

- Project Name
- Project Purpose
- Project Type
- Data Sensitivity
- Primary Users
- Runtime or Deployment Context
- Governance Level
- Safety Boundaries
- Validation Requirements
- Known Non-Goals
- Maintainer Approval Rules

## Recommended Advisory and Recommended Sections

Advisory and recommended projects should include, at minimum:

- Project Name
- Project Purpose
- Project Type
- Current Stage
- User Preferences
- Known Constraints
- Validation Notes

## Steward Decision Workflow

The Steward workflow should be:

1. gather initial context
2. classify project type
3. identify risk signals
4. recommend `Advisory`, `Recommended`, or `Strict-Governed`
5. ask for or accept user direction
6. produce one of the following:
   - `PROJECT_CONTEXT.md`
   - decision summary
   - implementation plan

The Steward owns:

- context classification
- context sufficiency judgment
- initial recommendation of enforcement mode
- the distinction between advisory context and future blocking context

## Governor Escalation Workflow

The Governor should only enforce blocking behavior when one of these is true:

- the project is classified `Strict-Governed`
- the maintainer explicitly requests strict enforcement
- release governance requires it

The Governor should not be used to turn `PROJECT_CONTEXT.md` into a universal requirement for all repositories.

## Validation Behavior

Current-phase policy direction:

- advisory projects should warn, not block
- recommended projects should warn strongly, not block by default
- strict-governed projects should block on missing or materially incomplete `PROJECT_CONTEXT.md`

This document defines policy first. It does not require immediate implementation in `scripts/validate_project_context.py`.

## Examples

### Advisory Example

A school capstone prototype with no real user data and no public deployment path should remain advisory. Missing `PROJECT_CONTEXT.md` should not block CI.

### Recommended Example

A reusable internal automation repo used by multiple agents or contributors should be classified as recommended. Missing `PROJECT_CONTEXT.md` should surface clearly, but remain non-blocking until maintainers opt into stricter governance.

### Strict-Governed Example

A client-facing automation system that handles credentials, user data, destructive operations, or release-critical workflows should be classified as strict-governed. Missing or incomplete `PROJECT_CONTEXT.md` should block validation.

## Non-goals

This policy does not:

- make `PROJECT_CONTEXT.md` universally mandatory
- hard-fail school, trial, prototype, or sandbox repos by default
- modify CI in this phase
- rewrite `scripts/validate_project_context.py` in this phase
- replace the Steward-led decision prompt
- bypass maintainer approval for future enforcement changes

## Future Implementation Checklist

Future work for `scripts/validate_project_context.py` should consider:

- detect `PROJECT_CONTEXT.md` presence
- detect governance level
- validate required sections by governance level
- warn for advisory projects
- warn strongly for recommended projects
- block for strict-governed projects
- allow explicit override only with documented maintainer approval
