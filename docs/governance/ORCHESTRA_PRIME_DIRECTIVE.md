# Orchestra Prime Directive

**Contract:** `ORCHESTRA_PRIME_DIRECTIVE_V1`
**Role:** Constitutional governance policy for Orchestra
**Authority class:** `HUMAN_POLICY`
**Runtime authority:** None created by this document

## Purpose

Orchestra exists to make AI-assisted software engineering reliable through explicit specialist ownership, bounded authority, deterministic safeguards, validation, evidence, and auditable state transitions. The Prime Directive defines the stable constitutional boundary that subordinate policies, runtime components, automation, adaptive systems, and development workflows must preserve.

This document is intentionally narrower and more stable than repository mechanics. It does not encode branch names, merge methods, CI context names, retry counts, retention periods, experiment call ceilings, or provider-specific behavior. Those belong to subordinate policy and may evolve without rewriting Orchestra's constitutional principles.

## Prime Directive

> Orchestra shall permit an AI-assisted action or lifecycle transition only within explicit, reduction-only authority and current applicable evidence. It shall never infer permission from capability, routing, confidence, learned state, validation success, mergeability, or prior success. A permanent capability shall be promoted only when proportional evidence shows that it solves an Orchestra-owned problem whose benefit justifies its complexity and risk without weakening these boundaries.

## Constitutional invariants

1. **Authority is explicit, scoped, and reduction-only.** Authority must originate from an accepted governing source and may be narrowed through delegation; it may not be silently widened.
2. **A child grant cannot exceed its parent grant.** Delegation, specialist routing, subprocesses, tools, and downstream project policy cannot create authority their parent did not possess.
3. **Capability is not authority.** Routing, tool availability, governance approval, validation success, confidence, learned state, compatibility, mergeability, prior success, and platform capability do not independently create permission.
4. **The most restrictive applicable control wins.** Effective permission is the intersection of current explicit authority, repository policy, project policy where applicable, host capability, phase scope, and current evidence.
5. **Unknown governing state fails closed.** Missing, stale, malformed, contradictory, or unsupported policy or evidence cannot be converted into approval.
6. **Specialist ownership remains intact.** Orchestration may coordinate or sequence specialists but may not silently transfer domain ownership or treat another specialist's confidence as authority.
7. **Evidence is state-bound.** Evidence belongs to the exact source, policy, candidate, configuration, and environment identity it validates and becomes stale when a material bound identity changes.
8. **Greater autonomy removes unnecessary pauses, not safeguards.** Human-Governed, Semi-Autonomous, and Full-Autonomous operation vary who may advance a satisfied gate; they do not erase required gates.
9. **Adaptive intelligence is advisory within deterministic eligibility.** Learned or inferred state may help preserve legitimate preferences and context, but it cannot create eligibility, relax governance, expand authority, or self-promote.
10. **Protected actions remain separately authorized.** Constitutional change, authority expansion, policy activation, release or publication, deployment or production mutation, destructive operations, force push, and history rewrite require their own applicable authority.
11. **Permanent capability requires proportional evidence of Orchestra-owned value.** Implementation correctness alone does not prove that a capability belongs in Orchestra.
12. **Negative and inconclusive evidence remains evidence.** Failed hypotheses, no-benefit findings, protocol-invalid results, and rejected proposals must not be rewritten into positive claims.
13. **Recovery is forward-only and auditable by default.** Ordinary recovery creates a new governed state transition rather than rewriting trusted history.
14. **A state-changing action is incomplete until independently read back.** API success, tool success, or an intended write is not final evidence that the resulting canonical state is correct.
15. **Orchestra cannot autonomously weaken or redefine its own governing rules.** Prime Directive wording and constitutional amendments are human-policy decisions and cannot be changed through learned state, runtime inference, autonomous remediation, or validation success.

## Semantic boundaries

The following equivalences are forbidden:

```text
CAPABILITY != AUTHORITY
ROUTING != AUTHORITY
CONFIDENCE != AUTHORITY
LEARNED_STATE != AUTHORITY
GOVERNANCE_APPROVAL != EXECUTION_AUTHORITY
VALIDATION_SUCCESS != AUTHORITY
MERGEABILITY != MERGE_AUTHORITY
PRIOR_SUCCESS != CURRENT_AUTHORITY
ADMISSION != PROMOTION
PROMOTION != MERGE_AUTHORITY
ADOPTION != RELEASE_OR_ACTIVATION_AUTHORITY
```

A system may be technically able to perform an operation while Orchestra correctly refuses it. Likewise, a candidate may be correct and validated while Orchestra correctly declines to make it permanent because its measurable value does not justify its complexity or risk.

## Relationship to existing governance

The Prime Directive sits above, but does not replace, Orchestra's current governance kernel and runtime policies.

- `machine/governance/policy.v1.json` remains the machine-readable policy source for existing governance vocabulary, ownership, precedence, validation, and remediation behavior.
- `docs/governance/GOVERNANCE_LAYER.md` remains the detailed governance architecture.
- `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md` remains the merge-specific exact-head evidence gate.
- `docs/governance/FEATURE_ADMISSION_POLICY.md` adds the product/value admission and promotion boundary required by this directive.

Subordinate policy may become stricter. It may not reinterpret this document as permission to expand authority or weaken a constitutional invariant.

## Feature promotion rule

Before a new permanent capability is promoted, Orchestra must have an accountable `FeatureDecisionRecord` or an explicitly eligible inline rationale under the Feature Admission policy. The decision process must distinguish:

```text
IMPLEMENTED
!= VALIDATED
!= EVIDENCE_SUPPORTED
!= WORTH_ADOPTING
!= MERGE_READY
!= RELEASED_OR_ACTIVATED
```

The Feature Admission validator may establish record completeness and deterministic contract conformance. It does not decide whether Orchestra should own a capability; that remains a governed human-policy judgment.

## Amendment rule

A Prime Directive amendment is a constitutional change.

Required boundary:

```text
PRIME_DIRECTIVE_AMENDMENT = HUMAN_POLICY
AUTONOMOUS_SELF_AMENDMENT = PROHIBITED
VALIDATION_SUCCESS = NOT_AMENDMENT_AUTHORITY
LEARNED_STATE = NOT_AMENDMENT_AUTHORITY
```

An amendment requires explicit human authorization, a bounded candidate, current evidence, ordinary repository governance, and independent canonical readback after any accepted state change. A more autonomous profile does not waive this boundary.

## Non-authority statement

This document constrains behavior; it does not grant implementation, Git, merge, release, deployment, production, policy-activation, destructive-operation, integration-refresh, force-push, history-rewrite, or constitutional-amendment authority.
