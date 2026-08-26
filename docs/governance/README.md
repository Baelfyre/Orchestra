# Orchestra Governance Overview

Orchestra governance controls whether otherwise authorized work may proceed. It does not create runtime authority, capabilities, specialist ownership, or evidence by itself.

## Constitutional and admission layer

The stable constitutional boundary for Orchestra is defined by:

- [Orchestra Prime Directive](ORCHESTRA_PRIME_DIRECTIVE.md)
- [Feature Admission Policy](FEATURE_ADMISSION_POLICY.md)
- [Candidate Maturity and Feature Freeze](CANDIDATE_MATURITY_FEATURE_FREEZE.md)

The Prime Directive defines the authority, evidence, specialist-ownership, autonomy, adaptive-intelligence, recovery, and self-amendment invariants that subordinate policies must preserve. Feature Admission adds the separate product/value decision required before new permanent complexity is promoted.

The `FeatureDecisionRecord` machine schema validates record completeness and non-authority boundaries. It does not decide whether Orchestra should own a capability and does not create implementation, merge, release, deployment, policy-activation, or destructive-action authority.

The `CandidateMaturityRecord` schema adds development-candidate maturity and exact Feature Freeze identity without replacing the runtime lifecycle controller. Frozen state, acceptance, and merge readiness remain evidence states rather than authority grants.

## Current authority split

For exact deterministic governance facts, use the machine contract:

- `../../machine/governance/policy.v1.json`

For human explanation, operating modes, risk scaling, governance roles, and usage guidance, use:

- [Orchestra Prime Directive](ORCHESTRA_PRIME_DIRECTIVE.md)
- [Feature Admission Policy](FEATURE_ADMISSION_POLICY.md)
- [Candidate Maturity and Feature Freeze](CANDIDATE_MATURITY_FEATURE_FREEZE.md)
- [Governance Layer](GOVERNANCE_LAYER.md)
- [Autonomous Merge Readiness Protocol](AUTONOMOUS_MERGE_READINESS_PROTOCOL.md)
- [Compliance Registry Integration](COMPLIANCE_REGISTRY_INTEGRATION.md)

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
