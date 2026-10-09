# Covenant system-intent judgment guide

Use this guide when The Steward supplies evidence to The Covenant. This is a
governance judgment, not an implementation review.

## Required judgment

Record:

- REVIEWER: STEWARD
- DECISION: APPROVED, ADVISORY_ONLY, REVISION_REQUIRED, BLOCKED, or NOT_APPLICABLE
- PRIME_DIRECTIVE_ALIGNMENT: ALIGNED, CONFLICT, UNKNOWN, or NOT_APPLICABLE
- PROJECT_GOAL_ALIGNMENT: ALIGNED, CONFLICT, UNKNOWN, or NOT_APPLICABLE
- CRITICAL_FLOW_ALIGNMENT: ALIGNED, CONTRADICTIONS, UNKNOWN, or NOT_APPLICABLE
- SYSTEM_INVARIANT_ALIGNMENT: ALIGNED, CONTRADICTIONS, UNKNOWN, or NOT_APPLICABLE
- UNINTENDED_BEHAVIOR: observed user or system outcomes that violate intent
- CONSTRAINTS: product, scope, acceptance, or complexity constraints
- EVIDENCE_REFERENCES: durable references to the reviewed context and result

Judge the completed system against the verified problem, intended users,
Project Context, ProductIntentContract, goals, requirements, acceptance
criteria, critical end-to-end flows, project-level invariants, prohibited
outcomes, scope, and complexity/value alignment.

Answer this question directly:

Does the completed system remain faithful to why the project exists and what
outcomes it is supposed to preserve?

## Boundaries

Do not decide architecture, persistence, security mechanisms, validation
method, legal applicability, privacy obligation, licensing, or IP ownership.
Record evidence and route those decisions to Clockwork, Chronicler, Cipher,
Overseer, or The Governor. Do not treat Governor approval, PRAI PASS, or a
specialist PASS as evidence that the user/problem flow is coherent.

If the flow, invariant, goal, or context is unknown, do not infer alignment.
Return UNKNOWN with evidence references so the Covenant can return
WAIT_FOR_EVIDENCE. If the requested scope cannot preserve the verified
outcome, return REVISION_REQUIRED. A Prime Directive conflict remains a
constitutional BLOCKED result.

## Reconciliation

The Steward may accept a narrower design only after reviewing evidence that it
preserves the Prime Directive and the verified project goals and critical
flows. Acceptance must be explicit, durable, and bound to the exact candidate
and basis revision.
