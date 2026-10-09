# Evidence-Gated Decision Hierarchy

The machine contract at [`machine/adaptive/evidence-gated-decision-hierarchy.v1.json`](../../machine/adaptive/evidence-gated-decision-hierarchy.v1.json) composes Orchestra's existing assurance, specialist, governance, authority, and transition contracts. It is a non-authorizing flow map; it does not replace AQ evaluators, PRAI, Covenant, the protected policy, or Arbiter.

## Ordered flow

```text
ROUTING
→ ASSESSMENT
→ VERIFICATION
→ IMPACT/RISK
→ MITIGATION
→ ADJUDICATION (optional advisory input)
→ GOVERNANCE
→ AUTHORITY (resolve existing grants)
→ TRANSITION (Arbiter)
→ IMPLEMENTATION (bounded Conductor plan, Ponytail)
→ REVALIDATION (fresh evidence, PRAI, Covenant when applicable, Arbiter closeout)
```

Keep the evidence types separate:

```text
finding ≠ verified fact
verified fact ≠ risk judgment
risk judgment ≠ mitigation
mitigation ≠ adjudication
adjudication ≠ governance
governance ≠ execution authority
execution authority ≠ implementation
implementation ≠ verified remediation
```

`NOT_REQUIRED` records a routing or eligibility disposition. It cannot satisfy a substantive review. A specialist `PASS` is review evidence, verification is evidence about observable behavior, and neither creates governance approval or authority. The assessor cannot certify its own finding when independent verification is required. Candidate mutation invalidates evidence tied to the previous candidate.

## Assessment and verification

Assessment identifies a possible condition. Verification establishes whether it is observable or reproducible. Overseer defines evidence sufficiency and evaluates actual impact from the resulting evidence. Active verification runs only when an existing contract requires it and its separate authorization is present.

During routing, Conductor establishes source identity through AQ1, derives risk, depth, and protected-gate requirements through AQ2, then applies AQ3 specialist routing. The Tuner coordinates only when cross-specialist contracts require it; it does not route, validate, or authorize.

| Area | Assessment | Verification | Evidence and impact review |
| --- | --- | --- | --- |
| Security | Cipher performs read-only assessment | Dagger performs active or adversarial checks only when separately required and authorized | Overseer evaluates evidence sufficiency, severity, blast radius, and residual risk |
| UI/UX | Cloak assesses interaction, accessibility, and responsive behavior | Browser, accessibility, and runtime evidence verifies the finding | Overseer evaluates user impact and evidence sufficiency |
| Architecture | Clockwork assesses boundaries and dependencies | Deterministic structural or runtime checks verify applicable claims | Overseer evaluates evidence sufficiency and impact |

Relevant domain specialists develop mitigation options. Conductor turns an approved, bounded plan into implementation instructions; Ponytail implements only that plan. Required domain and empirical verification is repeated against the changed candidate before post-run assurance and closeout.

## Adaptive assurance

Risk, audit depth, autonomy, and protected status remain separate axes. Task risk provides a floor; AQ2, AQ3, AQ4, and PRAI requirements combine with that floor and may raise it. Unknown or contradictory evidence raises assurance or blocks progression at the existing evaluator.

| Task risk | Task-risk depth floor | Verification |
| --- | --- | --- |
| LOW and explicitly harmless | LIGHT | Not required by this floor |
| LOW otherwise | STANDARD | Targeted verification required |
| MEDIUM | STANDARD | Targeted verification required |
| HIGH | DEEP | Required evidence union |
| CRITICAL, retained for compatibility | DEEP | Required evidence union |

The runtime task plan uses `orchestra.agentic-assurance-plan.v2`. It reports the task-risk floor separately from the resolved assurance union. AQ2, AQ3, AQ4, and PRAI are unresolved at the current RouterService composition point because their evaluated requirement records are not inputs there. The plan therefore reports `FLOOR_ONLY`, leaves `resolved_assurance_requirements` null, and uses null rather than false when the known floor does not settle targeted verification. A known true requirement remains true even while other sources are unresolved.

Structured `agentic_task_profile` metadata is an untrusted classification claim. Conductor still derives risk and protected-action signals from the actual prompt; the resolved risk is the maximum of the derived and declared risks, and required operation flags merge upward. Profile metadata cannot supply protected-action authorization. Risk provenance records both inputs.

The current RouterService context does not include a trusted candidate SHA/tree pair. Its plan is marked `UNBOUND`; project paths, manifest versions, and arbitrary source strings are not candidate identities. When a trusted exact repository/head/tree tuple is available to the plan composer, the binding records those fields and a canonical identity digest. A missing or mismatched binding cannot satisfy current assurance requirements and never grants authority.

An explicitly harmless LIGHT task floor is limited to a single routing, business-scope, or documentation domain with no mutation, implementation, validation, external-state action, protected action, human gate, re-entry, critic, or dependency complexity. This floor does not imply that unresolved AQ/PRAI requirements are absent.

### Assurance-plan v2 consumer migration

Assurance-plan v2 is a consumer migration. It removes the v1 `risk_depth_floor` field, so a consumer that hard-codes that key is not wire-compatible with v2. A consumer that needs only the old floor semantics should read `task_risk_floor.audit_depth`. The v2 `task_risk_floor` object also carries `source`, `risk_level`, and `targeted_verification_required`; it is the minimum task-risk contribution, not the complete resolved requirement set.

The v1 top-level `targeted_verification_required` reflected the task-risk floor. In v2, `task_risk_floor.targeted_verification_required` retains that floor-only meaning, while the plan-level `targeted_verification_required` reflects the combined requirements and is tri-state. It is `true` when any known input requires targeted verification, `false` only when all required sources are resolved and none requires it, and `null` when sources remain unresolved and no known input already requires it.

Consumers determine resolution from `requirement_resolution_state` and the source lists. `requirement_sources` names the required AQ2, AQ3, AQ4, and PRAI inputs. `available_requirement_sources` and `unresolved_requirement_sources` show which records were supplied. `FLOOR_ONLY` means none is available, `PARTIAL` means at least one but not all are available, and `RESOLVED` means all are available. `resolved_assurance_requirements` is `null` for `FLOOR_ONLY` and `PARTIAL`; only `RESOLVED` carries the final `audit_depth` and `targeted_verification_required` union. `known_requirement_union` is a lower bound while inputs are unresolved, not a substitute for the resolved result.

An unresolved AQ2/AQ3/AQ4/PRAI requirement is unknown, not `false` or `NOT_REQUIRED`. Downstream enforcement may consume `resolved_assurance_requirements` as complete only when `requirement_resolution_state` is `RESOLVED`. A floor that does not require targeted verification therefore cannot establish that targeted verification is unnecessary: the combined result remains `null` until unresolved sources are supplied, unless a known source already makes it `true`.

Before reusing a plan, validate its `candidate_freshness` against the current trusted candidate. The serialized state is `UNBOUND` or `BOUND`; a bound record includes `repository`, `candidate_sha`, `tree_sha`, and `source_state_identity`, which is `sha256:` followed by the digest of the canonical identity. The v2 payload does not serialize a `STALE` state: a bound plan is stale for current use when any identity field or digest no longer matches. Candidate mutation invalidates the prior binding. `UNBOUND` or stale plans cannot satisfy current resolved-assurance requirements. `candidate_freshness.may_authorize` remains `false`.

The plan remains non-authorizing: `authority_model` is `EVIDENCE_ONLY_NON_AUTHORIZING`, `may_authorize` is `false`, and `is_authorization_source` is `false`. It is not governance approval, execution authority, or an Arbiter transition. The assurance plan defines what assurance is required; it is not evidence that any required specialist review, empirical verification, validation, or other assurance activity has been completed. Completion must be established separately through the applicable evidence and receipt mechanisms. Owner-first routing and existing workflow selection remain compatible. Consumers must migrate serialized field access and semantics; v1 consumers that hard-code the removed `risk_depth_floor` field are not wire-compatible.

The following field excerpts show the migration for a LOW task whose task-risk floor is LIGHT. They are not complete plan objects:

```json
{
  "risk_depth_floor": "LIGHT",
  "targeted_verification_required": false
}
```

```json
{
  "schema_version": "orchestra.agentic-assurance-plan.v2",
  "task_risk_floor": {
    "source": "TASK_PROFILE_RISK_LEVEL",
    "risk_level": "LOW",
    "audit_depth": "LIGHT",
    "targeted_verification_required": false
  },
  "requirement_resolution_state": "FLOOR_ONLY",
  "requirement_sources": ["AQ2", "AQ3", "AQ4", "PRAI"],
  "available_requirement_sources": [],
  "unresolved_requirement_sources": ["AQ2", "AQ3", "AQ4", "PRAI"],
  "resolved_assurance_requirements": null,
  "known_requirement_union": {
    "audit_depth_lower_bound": "LIGHT",
    "targeted_verification_required": null
  },
  "targeted_verification_required": null,
  "candidate_freshness": {
    "binding_version": "orchestra.candidate-freshness-binding.v1",
    "state": "UNBOUND",
    "repository": null,
    "candidate_sha": null,
    "tree_sha": null,
    "source_state_identity": null,
    "may_authorize": false
  }
}
```

When all four requirement sources are available, the state is `RESOLVED`, `unresolved_requirement_sources` is empty, and consumers needing the final requirement read `resolved_assurance_requirements`, for example `{"audit_depth":"DEEP","targeted_verification_required":true}`. Do not map v1 `risk_depth_floor` directly to this final union, and check candidate freshness before reusing either plan version.

## Governance, authority, and autonomy

Steward and Governor retain their respective governance decisions. Covenant reconciles cross-governance evidence when applicable and cannot vote, authorize, or override either owner. Existing trusted grants and policy are resolved at the authority boundary; the composition contract issues no grant. Arbiter remains the sole transition owner.

`HUMAN_GOVERNED`, `SEMI_AUTONOMOUS`, and `FULL_AUTONOMOUS` retain their existing meanings. Full autonomy may traverse already-authorized satisfied gates when exact candidate identity, current evidence, required reviews and empirical verification, governance state, execution envelope, and Arbiter transition all pass. It cannot bypass missing or protected gates.

A protected policy or authority change freezes the candidate, preserves evidence, produces the required recommendation, and terminates the run. Any continuation requires human authority in a fresh authorized execution context.

## Optional JEV advisory

No tracked supported JEV integration was found for this contract. The advisory insertion point is after verified findings, risk, and mitigation options and before governance. JEV cannot authorize execution, replace required review, reduce AQ2 risk, create governance or transition authority, or mutate the candidate. Its absence does not block the hierarchy.

## Existing contracts

The stage references in the machine contract link to AQ1-AQ8, PRAI, Covenant, the protected-governance protocol, governed autonomy, the source Conductor and specialist skills, and the existing Arbiter kernel. This hierarchy adds no second risk, authorization, or transition engine.
