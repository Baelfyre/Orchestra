# Quality Standards

Use these concepts as review guidance. This skill does not certify compliance with ISO, IEEE, ISTQB, or any other standard.

## Quality Assurance Purpose

- Build confidence that process and product evidence support the project objective.
- Prevent defects through testable requirements, appropriate reviews, and feedback loops.
- Keep quality decisions traceable to evidence and risk.

## Verification vs Validation

- Verification asks whether specified requirements and design were implemented correctly.
- Validation asks whether the delivered behavior meets user and stakeholder needs in its intended context.
- Keep evidence for each distinct.

## Test Levels

- Unit: isolated behavior with controlled dependencies.
- Integration: interfaces and collaboration among components or external systems.
- System: end-to-end behavior of the assembled system.
- Acceptance: stakeholder-facing evidence against agreed criteria.

## Test Types

- Select functional and non-functional tests from the objective and risk.
- Consider usability, accessibility, security, performance, compatibility, recovery, installation, and data integrity only when relevant.

## Risk-Based Testing

- Prioritize by impact, likelihood, exposure, change surface, defect history, and detectability.
- Test critical user and data paths before low-impact variants.
- Record residual risk when coverage is incomplete.

## Test Evidence

- Record revision, environment, data, command or procedure, expected result, actual result, and outcome.
- Keep logs, screenshots, reports, or traces only when they support a decision and protect sensitive data.
- Never convert a planned or unrun test into a pass.

## Defect Management

- Capture reproducible steps, expected and actual behavior, environment, evidence, severity rationale, scope, and regression risk.
- Separate duplicate symptoms from root cause until evidence connects them.

## Regression and Smoke Testing

- Use smoke tests for rapid confirmation that critical paths are available after a build or deployment.
- Select regression coverage from changed behavior, dependencies, prior defects, and critical workflows.
- Retire redundant tests when risk is covered elsewhere.

## Acceptance Criteria

- Make criteria observable, unambiguous, bounded, and linked to the requirement or user goal.
- Include relevant error, permission, data, and boundary behavior.
- Avoid vague words without measurable meaning.

## Release Readiness and Quality Gates

- Define required evidence, blocking severity, ownership, waiver authority, and residual-risk acceptance.
- A green build alone is not release readiness.
- Record blocked and not-run checks explicitly.

## Public Reference Links

Use these clean URLs as learning anchors. Do not reproduce restricted standard text.

- https://www.iso.org/standard/81291.html
- https://www.iso.org/standard/79428.html
- https://ieeexplore.ieee.org/document/9687477
- https://www.iso.org/standard/78176.html
- https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/
- https://standards.ieee.org/ieee/1012/7324/

Describe reviews as aligned with general testing principles unless formal audit evidence supports a stronger claim.
