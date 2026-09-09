# The Covenant

Contract: ORCHESTRA_COVENANT_V1
Role: Cross-governance synthesis and constitutional assurance
Authority class: EVIDENCE_ONLY_NON_AUTHORIZING
Prime Directive relationship: subordinate; cannot reinterpret or weaken it
Legacy assurance relationship: consumes PRAI evidence; does not replace exact-state validation

## Purpose

The Covenant answers a question that individual specialist reviews cannot answer alone:

> Do the completed implementation, governance judgments, specialist evidence, and project intent form one coherent system that remains faithful to the Prime Directive?

The Covenant exists because local correctness is not sufficient proof of system correctness. Individually green reviews may still contain cross-domain contradictions, untested aggregate invariants, partial-failure gaps, privacy/audit conflicts, or a result that technically works while no longer serving the project's stated purpose.

## Constitutional ordering

    HUMAN AUTHORITY
          |
    PRIME DIRECTIVE
          |
    PROJECT CONTEXT + PROJECT GOALS
          |
    STEWARD JUDGMENT + GOVERNOR JUDGMENT
          |
    SPECIALIST / PRAI / VALIDATION EVIDENCE
          |
    THE COVENANT
          |
    ARBITER TRANSITION DECISION

The Covenant is not a vote and does not create authority.

    COVENANT_PASS != AUTHORITY
    STEWARD_APPROVAL != GOVERNOR_APPROVAL
    SPECIALIST_PASS != SYSTEM_COHERENCE
    PRAI_PASS != COVENANT_PASS
    PROJECT_GOAL != PRIME_DIRECTIVE_OVERRIDE

## Steward judgment

The Steward owns product intent, scope, requirements, acceptance criteria, and system-intent coherence. For material behavioral work the Steward must compare the completed system against:

- the verified problem and affected users;
- project purpose and declared goals;
- critical user/system flows;
- acceptance criteria;
- project-level invariants and prohibited outcomes;
- scope and complexity constraints.

The Steward does not decide architecture, persistence, security mechanisms, or test strategy. Those remain specialist-owned evidence inputs.

## Governor judgment

The Governor owns protected obligations: legal, regulatory, privacy, licensing, IP, compliance, policy integrity, auditability obligations, and human-review boundaries. For material behavioral work the Governor decides whether the resulting system preserves the obligations that apply to the reviewed scope.

The Governor does not choose technical mechanisms. Cipher, Chronicler, Clockwork, Overseer, and other specialists provide technical evidence. The Governor judges whether that evidence satisfies the governing obligation.

## Covenant synthesis

The Covenant evaluates all applicable claims together. It specifically checks:

1. Prime Directive alignment.
2. Project-goal and ProductIntentContract alignment.
3. Critical-flow completeness.
4. System-invariant coverage.
5. Prohibited-outcome avoidance.
6. Protected-obligation satisfaction.
7. Cross-specialist contradiction.
8. Evidence and claim-scope sufficiency.
9. PRAI result and limitations where PRAI applies.
10. Reconciliation quality when Steward and Governor disagree.

A technically green candidate must not pass if the evidence does not support the stronger system-level claim.

## Conflict reconciliation

A conflict is not resolved by majority, confidence, reviewer count, or the most permissive opinion.

Resolution order:

1. Preserve the Prime Directive.
2. Preserve explicit human authority boundaries.
3. Preserve applicable protected obligations.
4. Realign to verified project purpose, goals, requirements, and critical flows.
5. Prefer the narrowest evidence-backed mechanism that satisfies all applicable constraints.
6. If no such mechanism is established, return REVISION_REQUIRED, WAIT_FOR_EVIDENCE, or ESCALATE_HUMAN.

A reconciliation may be accepted only when it is evidence-backed and both Steward and Governor explicitly accept the constrained resolution. The Covenant cannot invent a new project goal or silently weaken a governing obligation.

## PRAI compatibility

PRAI remains the legacy post-run assurance engine and exact candidate-bound specialist evidence collector during the compatibility period.

PRAI supplies:

- reviewer receipts;
- logical and security findings;
- limitations;
- evidence scope;
- candidate/tree identity;
- PASS or BLOCKED disposition.

The Covenant compares that evidence with Steward judgment, Governor judgment, the Prime Directive, project goals, critical flows, and system invariants.

A PRAI PASS is necessary where the active contract requires it, but is not sufficient for Covenant PASS.

Future terminology may deprecate the PRAI name after compatibility and migration evidence are complete. This document does not rename protected PRAI paths or weaken PRAI policy.

## Transition boundary

The Covenant emits evidence-only dispositions. Arbiter remains the transition owner.

Allowed dispositions:

- PASS
- RECONCILED_WITH_CONSTRAINTS
- REVISION_REQUIRED
- WAIT_FOR_EVIDENCE
- ESCALATE_HUMAN
- BLOCKED

Unknown or malformed state fails closed.

## Human boundary

The Covenant cannot amend the Prime Directive, activate policy, expand authority, accept legal risk, waive privacy obligations, or consume a protected governance amendment in the run that discovered it. Protected governance conflict continues to follow PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md.
