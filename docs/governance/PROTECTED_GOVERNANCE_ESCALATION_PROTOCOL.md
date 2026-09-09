# Protected Governance Escalation Protocol

**Contract:** `ORCHESTRA_PROTECTED_GOVERNANCE_ESCALATION_V1`  
**Authority class:** `HUMAN_POLICY`  
**Status:** Canonical governance amendment  
**Applies to:** autonomous, delegated, semi-autonomous, and human-governed runs that discover a need to change, relax, reinterpret, except, or supersede an active protected governance control

## Purpose

This protocol defines the mandatory path when a run discovers that an active governance rule may itself be causing a defect, blocking a logically valid repair, or conflicting with the Orchestra Prime Directive.

The protocol preserves two requirements at the same time:

1. an autonomous candidate must never rewrite the rule that is currently blocking it merely to obtain a pass; and
2. governance must remain capable of legitimate human-authorized evolution when evidence shows that an existing rule should be amended or narrowly excepted.

## Core invariant

```text
RUN_N_DISCOVERS_GOVERNANCE_CHANGE
!=
RUN_N_EXECUTES_GOVERNANCE_CHANGE

AI_REVIEW_MAY_RECOMMEND_GOVERNANCE_CHANGE
!=
AUTHORITY_TO_EXECUTE_GOVERNANCE_CHANGE

PROTECTED_GOVERNANCE_CHANGE
=
HUMAN_REVIEW_REQUIRED
+ NEW_EXECUTION_CONTEXT_REQUIRED
```

A run that encounters this boundary must stop mutation of the originating candidate and prepare a human-review handoff.

## Trigger conditions

This protocol is mandatory when any of the following occurs:

- PRAI returns `FAIL_POLICY_SELF_MODIFICATION`;
- bounded remediation would modify the policy, validator, workflow, threshold, fixture, manifest, or evidence rule that is currently blocking the same candidate;
- a proposed repair would relax a protected gate, authority boundary, security/privacy requirement, validation rule, release rule, or Prime Directive interpretation;
- specialists conclude that the current rule may be logically inconsistent, obsolete, incomplete, over-broad, or in tension with the Prime Directive;
- the candidate cannot progress without a policy choice, authority expansion, risk acceptance, or protected governance exception;
- a repeated failure appears to be caused by governance topology rather than the implementation under review.

## Immediate stop behavior

When triggered, the originating run must:

1. freeze the exact candidate head, tree, base, changed paths, validation state, and PRAI/decision evidence;
2. stop implementation repair, policy edits, phase progression, merge, release, and downstream activation for that originating candidate;
3. preserve the failing evidence and any proposed governance change as evidence only;
4. route a governance investigation through Conductor;
5. produce a `GovernanceEscalationPacket`;
6. terminate autonomous progression with `ESCALATE_HUMAN` / `HUMAN_GOVERNANCE_REVIEW_REQUIRED`.

The originating run must not create and consume its own exception, approval, amendment, or policy override.

## Candidate freeze

During protected-governance review:

```text
CANDIDATE_FROZEN = TRUE
```

No new repair commit, rebase, amend, force push, scope expansion, phase activation, merge, or policy mutation is allowed on the originating candidate.

If candidate identity changes for any reason, the existing escalation packet becomes stale and must be regenerated against the new exact state.

## Conductor routing

Conductor remains the exclusive router. It does not decide the governance outcome.

Conductor must route only the minimum applicable review set needed to evaluate the governance question. The default review set is:

- **Arbiter** — transition safety, continuity, exact-state identity, candidate freeze, and disposition;
- **Overseer** — evidence sufficiency, validation interpretation, and whether the claimed problem is actually demonstrated;
- **Clockwork** — logical/system architecture and whether the governance rule creates a structural contradiction;
- **The Governor** — policy/compliance interpretation when the proposed change affects governance policy, legal, privacy, IP, licensing, or compliance boundaries.

Conductor adds other specialists only when their owned domain is materially affected:

- **Cipher** for security, authorization, secrets, privacy-control, or threat implications;
- **The Steward** for scope, product intent, acceptance criteria, resource allocation, or program-boundary implications;
- **Chronicler** for persistence/migration/transaction semantics;
- **Dagger** for explicitly authorized resilience/adversarial implications;
- **Cloak** for UI/accessibility governance implications;
- **The Tuner** only for cross-specialist contract coordination; it does not route, approve, or execute.

## Review standard

The review question is not:

> Will changing the rule make CI pass?

The review question is:

> Does preserving the current rule, allowing a bounded exception, or amending the rule best satisfy the Orchestra Prime Directive on the exact current evidence?

Reviewers must compare at least:

- the current rule and its original purpose;
- the exact blocked candidate and failure;
- the proposed deviation or amendment;
- the risk of preserving the current rule;
- the risk of changing the rule;
- authority and scope consequences;
- security/privacy consequences where applicable;
- validation and evidence-integrity consequences;
- forward compatibility and future-phase consequences;
- whether a narrower implementation repair exists.

Passing tests or reviewer consensus never creates execution authority.

## AI recommendation dispositions

AI governance review may recommend exactly one of:

- `DENY` — the current rule should remain; originating candidate remains blocked;
- `REQUEST_MORE_EVIDENCE` — insufficient evidence to support a human decision;
- `RECOMMEND_BOUNDED_EXCEPTION` — the rule is generally sound but a narrowly scoped exception may better satisfy the Prime Directive for this exact case;
- `RECOMMEND_POLICY_AMENDMENT` — the rule itself appears incomplete, incorrect, obsolete, or structurally incompatible and should be changed through a separate governance amendment.

Reviewer disagreement must be preserved in the escalation packet. Conductor must not manufacture consensus by suppressing dissent.

## Human decision gate

Every protected governance escalation requires human review regardless of the active automation profile.

The human decision may be:

- `DENY`;
- `REQUEST_MORE_EVIDENCE`;
- `APPROVE_BOUNDED_EXCEPTION`;
- `APPROVE_POLICY_AMENDMENT`.

Human approval creates authority for a later bounded execution context only. It does not retroactively authorize mutation in the originating run.

## New execution context rule

After a human approval:

```text
RUN_N      = discovery + evidence + recommendation + stop
HUMAN_GATE = explicit decision
RUN_N_PLUS_1 = bounded governance exception/amendment implementation
RUN_N_PLUS_2 = originating candidate reconsideration when required
```

The new run must fresh-read canonical source, policy, evidence, and the human decision record before mutation.

## Bounded exception requirements

A bounded exception must identify:

- exact repository;
- exact originating candidate head/tree/base;
- exact protected rule/control;
- exact allowed deviation;
- exact allowed paths/actions;
- evidence digest/reference;
- human decision identity and date;
- expiration or consumption condition;
- whether it is single-use;
- non-transitive status;
- explicit statement that it does not weaken unrelated controls.

An exception becomes invalid if the bound candidate, rule, scope, or evidence identity materially changes.

Exceptions do not become precedent automatically.

## Policy amendment requirements

A policy amendment is a separate governance change.

It requires:

- explicit human authorization;
- a new bounded branch/candidate;
- current live policy readback;
- specialist review appropriate to the affected rule;
- ordinary repository required checks;
- independent canonical readback after merge;
- a separate re-evaluation of the original blocked candidate against the new canonical policy.

When the amendment changes the assurance mechanism itself, that mechanism must not be represented as independently certifying its own amendment. The amendment is validated by the separate human-governance path, repository checks, independent specialist evidence, and canonical readback.

## GovernanceEscalationPacket

The packet must preserve:

- `schema_version`;
- `escalation_id`;
- `originating_run_id`;
- `repository`;
- `base_sha`;
- `candidate_sha`;
- `tree_sha`;
- `work_item_ref`;
- `phase_id`;
- `trigger_code`;
- `protected_rule`;
- `affected_paths`;
- `failing_evidence_refs`;
- `decision_digest` when available;
- `proposed_governance_change`;
- `prime_directive_analysis`;
- `alternatives_considered`;
- `risk_if_unchanged`;
- `risk_if_changed`;
- `required_reviewers`;
- `reviewer_findings`;
- `dissenting_findings`;
- `ai_recommendation`;
- `human_review_required`;
- `candidate_frozen`;
- `same_run_mutation_forbidden`;
- `next_allowed_action`;
- `generated_at`.

## HumanGovernanceDecisionRecord

A human decision record must preserve:

- `schema_version`;
- `decision_id`;
- `escalation_id`;
- `decision`;
- `human_authority_source`;
- `decision_timestamp`;
- `constraints`;
- `approved_scope`;
- `expiration` when applicable;
- `requires_new_execution_context`;
- `originating_candidate_may_resume`;
- `supersedes` when applicable.

Earlier escalation evidence must never be rewritten. Later decisions link forward to it.

## Transition integration

Protected governance escalation has higher precedence than ordinary automatic remediation.

```text
POLICY_SELF_MODIFICATION_OR_PROTECTED_GOVERNANCE_CONFLICT
    -> ESCALATE_HUMAN
    -> FREEZE_ORIGINATING_CANDIDATE
    -> GOVERNANCE_REVIEW_PACKET
    -> TERMINATE_ORIGINATING_RUN
```

`AUTO_REMEDIATE_AND_REVALIDATE` is not valid for a repair that changes the governance controlling that same blocked candidate.

## PRAI integration

PRAI remains fail-closed.

`FAIL_POLICY_SELF_MODIFICATION` remains a blocking PRAI result. PRAI does not create exceptions and does not authorize policy changes.

The orchestration layer interprets that failure as requiring the protected governance escalation path. The failure therefore means:

```text
PRAI = BLOCKED
ORCHESTRATION = GOVERNANCE_ESCALATION_REQUIRED
HUMAN_REVIEW_REQUIRED = TRUE
SAME_RUN_POLICY_CHANGE = FORBIDDEN
```

This preserves PRAI's independence while allowing governance to evolve through a separate human-authorized path.

## Anti-loop rule

The same originating candidate, protected rule, and materially identical evidence may not repeatedly request governance reconsideration merely to obtain a different outcome.

A repeated escalation requires materially new evidence or a human request for reconsideration.

## Audit and continuity

Every escalation and human decision must be forward-only, auditable, exact-state-bound, and preserved during handoff or context reset.

Missing, stale, contradictory, or malformed escalation/decision records fail closed.

## Canonical outcome

```text
AUTONOMY_HANDLES_IMPLEMENTATION
PRAI_HANDLES_POST_RUN_ASSURANCE
AI_GOVERNANCE_REVIEW_HANDLES_ANALYSIS_AND_RECOMMENDATION
HUMAN_GOVERNANCE_GATE_HANDLES_PROTECTED_RULE_CHANGE_AUTHORITY
NEW_RUN_HANDLES_EXECUTION_OF_THE_APPROVED_CHANGE
```
