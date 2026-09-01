# Orchestra Governance Overview

Orchestra governance controls whether otherwise authorized work may proceed. It does not create runtime authority, capabilities, specialist ownership, or evidence by itself.

## Constitutional and admission layer

The stable constitutional boundary for Orchestra is defined by:

- [Orchestra Prime Directive](ORCHESTRA_PRIME_DIRECTIVE.md)
- [Feature Admission Policy](FEATURE_ADMISSION_POLICY.md)
- [Candidate Maturity and Feature Freeze](CANDIDATE_MATURITY_FEATURE_FREEZE.md)
- [Qualification Gates, Evaluation, and Independent Audit](QUALIFICATION_GATES_EVALUATION_AUDIT.md)
- [Pre-state, Forward Recovery, and Branch Retirement](PRESTATE_RECOVERY_BRANCH_RETIREMENT.md)

The Prime Directive defines the authority, evidence, specialist-ownership, autonomy, adaptive-intelligence, recovery, and self-amendment invariants that subordinate policies must preserve. Feature Admission adds the separate product/value decision required before new permanent complexity is promoted.

The `FeatureDecisionRecord` machine schema validates record completeness and non-authority boundaries. It does not decide whether Orchestra should own a capability and does not create implementation, merge, release, deployment, policy-activation, or destructive-action authority.

The `CandidateMaturityRecord` schema adds development-candidate maturity and exact Feature Freeze identity without replacing the runtime lifecycle controller. Frozen state, acceptance, and merge readiness remain evidence states rather than authority grants.

The `QualificationGatePlan` schema binds risk-proportional engineering, regression/compatibility, security/governance, controlled-evaluation, and independent-audit obligations to one exact frozen candidate. `QUALIFIED` is evidence completeness; it is not feature acceptance or merge authority.

The `RepositoryRecoveryRetirementPlan` schema records immutable pre-state evidence, forward-only recovery requirements, and conservative branch-retirement classifications. Retirement eligibility remains dry-run evidence for a separate authorization; it never grants branch-deletion authority.

## Current authority split

For exact deterministic governance facts, use the machine contract:

- `../../machine/governance/policy.v1.json`

For human explanation, operating modes, risk scaling, governance roles, and usage guidance, use:

- [Orchestra Prime Directive](ORCHESTRA_PRIME_DIRECTIVE.md)
- [Feature Admission Policy](FEATURE_ADMISSION_POLICY.md)
- [Candidate Maturity and Feature Freeze](CANDIDATE_MATURITY_FEATURE_FREEZE.md)
- [Qualification Gates, Evaluation, and Independent Audit](QUALIFICATION_GATES_EVALUATION_AUDIT.md)
- [Pre-state, Forward Recovery, and Branch Retirement](PRESTATE_RECOVERY_BRANCH_RETIREMENT.md)
- [Governed Autonomy Modes](GOVERNED_AUTONOMY_MODES.md)
- [Governed Autonomous Execution Protocol](GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md)
- [Governed Autonomy Candidate Lifecycle Integration](GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION.md)
- [Governance Layer](GOVERNANCE_LAYER.md)
- [Autonomous Merge Readiness Protocol](AUTONOMOUS_MERGE_READINESS_PROTOCOL.md)
- [Compliance Registry Integration](COMPLIANCE_REGISTRY_INTEGRATION.md)
- [Padayon Post-Restructure Repository Realignment Notice](PADAYON_POST_RESTRUCTURE_REALIGNMENT_NOTICE.md): searchable repository-local continuity guidance for M0-M6 post-restructure source-reality reconciliation and live-source precedence.

The autonomy candidate-lifecycle integration is intentionally thin: it reuses the existing autonomy evaluator to decide whether an already-valid candidate transition needs another human pause. It does not create feature-adoption authority, merge authority, persistence authority, or branch-deletion authority.

Qualification occurs before the human-owned acceptance/promotion decision. Higher autonomy may automate qualification evidence collection and monitoring, but it does not remove a required gate, invent an N/A justification, or self-adopt a capability.

Pre-state and branch-retirement records are likewise non-authorizing. Immutable SHA/tree evidence is the durable historical anchor; temporary refs are risk-proportional, recovery moves forward through a newly validated candidate, and branch classifications may only recommend `KEEP`, `QUARANTINE`, or `ELIGIBLE_FOR_SEPARATE_AUTHORIZATION`.

Older wording in human governance documents may describe Markdown as the primary governance artifact format. That describes the human instruction layer, not the current authority of structured machine state. Current representation policy is:

- Markdown: human explanation, rationale, instructions, and nuanced guidance.
- JSON: canonical structured machine governance/state, receipts, contracts, indexes, provenance, and evidence.
- JSON Schema: deterministic machine-record validation.
- TOON: optional derived and non-authoritative context projection only.

See [Hybrid Context Formats](../HYBRID_CONTEXT_FORMATS.md).

## Precedence

```text
Explicit bounded authority
        ∩
Repository policy
        ∩
Host capability
        ∩
Current phase
        ∩
Current validated evidence
        ↓
Effective permitted action
```

Routing, validation success, PRAP certification, host maturity, Developer Portal discovery, MCP metadata, GitHub mergeability, or a successful prior execution cannot widen that permission set.

## Governance roles

- **The Steward:** business alignment, requirements, scope, SDLC sufficiency, and change control.
- **The Governor:** legal/compliance, privacy obligations, IP, licensing, and source applicability.
- **Arbiter:** continuity, source-of-truth, validation evidence, transition safety, and merge-readiness disputes.
- **Conductor:** routing only. It does not grant governance or runtime permission.
- **The Tuner:** cross-specialist coordination only. It does not become domain authority.

## Fail-closed boundaries

Protected actions, missing required evidence, stale exact-head validation, invalid runtime authority, unresolved ownership conflicts, or other hard governance failures stop or escalate according to the machine policy. Human guidance may explain a decision but cannot override a machine-enforced prohibition without a separately authorized policy change.
