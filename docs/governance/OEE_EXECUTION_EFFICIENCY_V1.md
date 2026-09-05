# Orchestra Execution Efficiency V1

Status: OEE-0 through OEE-8 COMPLETE_CANONICAL_VERIFIED

## Invariant

```text
MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY
```

Execution efficiency is a constraint on redundant work, not permission to skip required evidence, implementation quality, security, governance, validation, or human gates.

## OEE-0 boundary

OEE-0 installs the machine contract and validation primitives only. It does not rewrite Conductor dispatch, resume UIEF, or authorize later OEE phases.

The canonical machine record is:

`machine/governance/execution-budget.v1.json`

Schema:

`machine/schemas/execution-budget.v1.schema.json`

Runtime domain primitives:

`orchestra_runtime/domain/orchestration/execution_efficiency.py`

## Evidence budget

Work progresses through E0-E5:

1. E0 ORIENTATION
2. E1 INPUT_INTEGRITY
3. E2 TARGETED_ANALYSIS
4. E3 IMPLEMENTATION
5. E4 QUALIFICATION
6. E5 PROMOTION

A higher tier may not begin until all required prior tiers are complete.

## Default execution budget

- maximum parallel specialists: 1
- specialist retry limit after the initial attempt: 1
- owner-first routing required
- broad search requires exhaustion of narrower search levels
- reusable evidence must remain bound to exact source identity
- full validation requires a stable candidate
- passive CI waiting must not consume active model reasoning
- autonomous campaigns load one phase at a time
- optional review cannot become blocking without explicit authority

## Search escalation

```text
EXACT_PATH
-> EXACT_SYMBOL
-> BOUNDED_DIRECTORY
-> REPOSITORY_WIDE
-> EXTERNAL
```

Escalation may advance by one level only after the narrower level is insufficient.

## Validation escalation

```text
SYNTAX_SCHEMA
-> DIRECT_TESTS
-> SUBSYSTEM
-> REPOSITORY_QUALIFICATION
-> PROTECTED_GATES
```

Expensive validation is deferred until the candidate is stable.

## Earliest decisive evidence

A decisive stop signal records:

- owner
- evidence_sufficient
- stop_required
- downstream_execution_allowed
- reason
- evidence_refs

When evidence is sufficient and stop is required, downstream execution must be false.

## Existing authority is preserved

Conductor owns routing and sequencing. Arbiter retains transition/stop authority. Overseer retains validation evidence authority. The Tuner retains evidence freshness/invalidation coordination. Scribe records durable measurements. The Governor remains legal/compliance governance and is not converted into an execution owner.

OEE does not create a new specialist or expand existing authority.

## OEE-1 through OEE-8 continuation

The post-OEE-0 continuation operationalizes the existing budget rather than creating another governance layer.

- OEE-1: owner-first specialist invocation and retry/fan-out budget.
- OEE-2: earliest decisive evidence stop enforcement.
- OEE-3: exact-source evidence reuse and narrow-to-broad search escalation.
- OEE-4: stable-candidate validation escalation.
- OEE-5: passive CI wait boundary and continuous-watch prohibition.
- OEE-6: phase-local minimum sufficient context packs.
- OEE-7: controlled replay of the UIEF-5 usage-exhaustion incident.
- OEE-8: integration disposition and explicit UIEF resume decision.

The OEE-7 replay intentionally stops at the UIEF-4 responsive contradiction during E1 input integrity. It does not continue to provenance search, downstream specialists, implementation analysis, full validation, or CI watch work after that decisive blocker.

OEE-8 does not automatically resume UIEF. The canonical disposition keeps UIEF blocked pending Cloak-owned responsive-contract repair, provenance revalidation, and UIEF-5 source requalification.

## Canonical qualification

OEE-0:
- source PR #792
- qualified source head `8903874688dc5bf5311689411f951afef16a968a`
- signed materialization PR #793
- canonical PR #794
- canonical commit `1927d3f0672198ddc67cc32624d38c2b14c434e8`

OEE-1 through OEE-8:
- source PR #795
- qualified source head `3986a04598bf1146270e1d65445373643e34a93f`
- signed materialization PR #797
- signed materialization commit `dbe3f777265c6843695babce7bbd229c44b753e2`
- canonical PR #798
- canonical commit `75100c3ad0fd9a11c69f2b9b7c5172edd8841cd2`

The OEE-1 through OEE-8 source head passed Governance Check, Required Analysis Compatibility, validate, Cross-platform Validation, cosmic-ray-confidence, and signed-materialization. OEE is therefore complete canonical verified.

The OEE-7 replay preserved the same safe blocker disposition while reducing redundant work. OEE completion removes the execution-efficiency gap but does not repair UIEF input contradictions or grant a UIEF resume transition.
