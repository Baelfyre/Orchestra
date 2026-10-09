# User Testing Foundations Guide

## Purpose
This guide provides a token-efficient, practical reference for Overseer to plan, review, audit, and validate user testing and acceptance evidence. It ensures a rigorous, evidence-based approach to usability testing, user validation, and readiness checks.

## Source-of-Truth Rule
- **Never invent** user feedback, test results, participant behavior, pass/fail outcomes, defects, or acceptance status.
- All testing claims must be backed by verifiable evidence.

## User Testing vs QA Testing vs UAT
- **QA Testing**: Checks whether the system meets documented functional and non-functional requirements (Does it work?).
- **User Testing**: Validates usability and user fit. Focuses on whether intended users can complete realistic tasks effectively (Is it usable?).
- **UAT (User Acceptance Testing)**: Checks whether the stakeholder accepts the delivered behavior against agreed criteria for release or submission (Is it accepted?).

## When to Use User Testing
- Use user testing when the goal is to observe real users interacting with the system to identify friction points, confusion, or efficiency issues.

## Participant Definition
- Participant roles should match intended user groups.
- Define explicit criteria for selecting participants to ensure representative feedback.

## User Goals and Task Scenarios
- Task scenarios should be realistic, goal-based, and observable.
- Map tasks directly to specific user goals and acceptance criteria.

## Test Script and Facilitation
- Provide clear context without giving step-by-step instructions.
- Facilitators should avoid leading users toward the desired answer.

## Moderated and Unmoderated Testing
- Understand the distinction and choose appropriately based on the need for deep qualitative insights (moderated) vs. scalable, independent validation (unmoderated).

## Think-Aloud Protocol
- Encourage users to vocalize their thought process during tasks to capture mental models and sources of confusion.

## Observation Notes
- Observations should describe *what happened*, not speculate about what the user was thinking.
- Record exact actions, errors, and direct quotes where applicable.

## Usability Success Criteria
- Success criteria may include: task completion rate, critical error count, assistance needed, time on task, repeated confusion, satisfaction rating, and accessibility barriers.

## Accessibility and Inclusion Checks
- Accessibility issues should be recorded separately when relevant.
- Validate against WCAG guidelines and note any barriers preventing equitable access.

## Test Environment and Device Coverage
- Ensure testing happens in environments and on devices representative of real-world usage.

## Evidence Capture
- Test evidence must include: revision/version, environment, participant type or role, task, expected outcome, observed behavior, actual outcome, issue, severity, and evidence reference when available.
- **Sensitive personal data must not be exposed in test evidence.**

## Defect vs Usability Issue
- **Defect**: The system behaves contrary to the technical requirements or crashes.
- **Usability Issue**: The system functions as coded, but the user cannot figure out how to use it or makes frequent errors.

## Severity and Priority Rating
- Severity should consider impact, frequency, blocking behavior, affected user group, and workaround availability.

## Acceptance Testing and Stakeholder Validation
- A stakeholder comment is not acceptance unless acceptance criteria and approval authority are clear.
- UAT must culminate in formal sign-off.

## Regression After Fixes
- Any fix for a usability issue or defect requires regression testing to ensure no new issues were introduced.

## Readiness Decision
- Readiness statuses should distinguish: passed, failed, blocked, not run, skipped, waived, and needs retest.
- **A planned or unrun test must never be marked as passed.**

## User Testing Review Checklist
- [ ] Are participant profiles defined and appropriate?
- [ ] Are tasks goal-oriented and realistic?
- [ ] Is evidence captured objectively without assumption?
- [ ] Are usability issues and technical defects separated?
- [ ] Is there formal stakeholder sign-off based on criteria?

## Overseer Output Discipline
- Provide clear, actionable testing feedback.
- Do not fabricate test data.
- Ensure all readiness gates are firmly established with clear criteria.
