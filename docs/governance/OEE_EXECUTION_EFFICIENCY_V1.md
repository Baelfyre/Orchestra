# Orchestra Execution Efficiency V1

Status: OEE-0 canonical; OEE-1 through OEE-8 continuation candidate

## Invariant

```text
MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY
```

Execution efficiency is a constraint on redundant work, not permission to skip required evidence, implementation quality, security, governance, validation, or human gates.

## Canonical foundation

OEE-0 establishes the versioned execution budget and fail-closed primitives.

Canonical machine record:

`machine/governance/execution-budget.v1.json`

Schema:

`machine/schemas/execution-budget.v1.schema.json`

Foundation domain primitives:

`orchestra_runtime/domain/orchestration/execution_efficiency.py`

Continuation domain controls:

`orchestra_runtime/domain/orchestration/execution_efficiency_runtime.py`

Conductor progressive-disclosure guidance:

`skills/conductor/EXECUTION_EFFICIENCY_GUIDE.md`

Codex parity guide:

`adapters/codex/skills/conductor/EXECUTION_EFFICIENCY_GUIDE.md`

## Phase disposition

| Phase | Continuation purpose | Candidate surface |
| --- | --- | --- |
| OEE-0 | Execution cost baseline and guardrail contract | canonical `ExecutionBudget` |
| OEE-1 | Owner-first routing and specialist budget | `SpecialistInvocationPlan` |
| OEE-2 | Earliest decisive evidence stop policy | `evaluate_decisive_progression` |
| OEE-3 | Evidence reuse and search escalation | `EvidenceCacheEntry`, `next_search_stage` |
| OEE-4 | Risk-based validation escalation | `ValidationRequest` |
| OEE-5 | CI wait boundary | `plan_ci_activity` |
| OEE-6 | Phase-local context packs | `PhaseContextPack`, `require_active_phase` |
| OEE-7 | Controlled efficiency replay | `oee_7_uief5_controlled_replay.v1.json` |
| OEE-8 | Integration and UIEF resume gate | `oee_8_integration_closeout.v1.json` |

OEE-1 through OEE-8 remain candidate work until the exact continuation tree qualifies, passes signed materialization, is canonically merged, and `main` is independently read back.

## Evidence budget

Work progresses through E0-E5:

1. E0 ORIENTATION
2. E1 INPUT_INTEGRITY
3. E2 TARGETED_ANALYSIS
4. E3 IMPLEMENTATION
5. E4 QUALIFICATION
6. E5 PROMOTION

A higher tier may not begin until all required prior tiers are complete.

## Owner-first specialist budget

The current decision owner is the only active specialist by default. Supporting specialists may be planned only for an explicit cross-domain authority dependency or a required adversarial review, with evidence recorded before expansion.

The specialist retry limit is one retry after the initial attempt. A second retry is invalid.

Supporting specialists are sequential under the current concurrency ceiling. OEE does not create parallel specialist authority.

## Search escalation

```text
EXACT_PATH
-> EXACT_SYMBOL
-> BOUNDED_DIRECTORY
-> REPOSITORY_WIDE
-> EXTERNAL
```

Escalation may advance by one level only after the narrower level is insufficient. Reusable evidence remains valid only while both the exact source revision and source identity match.

## Validation escalation

```text
SYNTAX_SCHEMA
-> DIRECT_TESTS
-> SUBSYSTEM
-> REPOSITORY_QUALIFICATION
-> PROTECTED_GATES
```

The completed validation history must be the exact ordered prefix for the requested tier. `REPOSITORY_QUALIFICATION` and `PROTECTED_GATES` require a stable candidate.

## Earliest decisive evidence

A decisive stop signal records:

- owner
- evidence_sufficient
- stop_required
- downstream_execution_allowed
- reason
- evidence_refs

When evidence is sufficient and stop is required, downstream execution must be false. Do not invoke downstream specialists, implementation, or expensive validation merely to increase confidence in a decision that is already determined.

## CI wait boundary

Unchanged CI state is not model work. The default state is `IDLE_NO_REASONING`. At a state change or decision point, perform one bounded read using `READ_ONCE` semantics. Repeated watch/poll loops are not the default execution path.

## Phase-local context

Campaign authorization may span multiple phases, but only the active phase context may be loaded. A `PhaseContextPack` binds evidence to source identity and specialist consumers, prevents excluded/ref overlap, and requires evidence usable by the declared owner.

## Controlled replay

OEE-7 uses the UIEF-5 2026-09-05 usage-exhaustion incident as the benchmark case. Historical precision is intentionally bounded to supported facts only. Unknown historical invocation, retry, repository-search, and token totals remain `null` rather than being invented.

The controlled replay must preserve the same or safer `BLOCKED_PRE_IMPLEMENTATION_REVIEW` disposition while demonstrating less redundant execution on measurable dimensions. The current replay uses one active Cloak owner before the decisive stop instead of the four unique specialist roles observed in the historical run, performs no downstream implementation after the blocker, and removes active CI watch behavior.

## UIEF resume gate

OEE completion may reopen UIEF as the next development lane after canonical qualification. It does not resolve UIEF-5 itself.

UIEF-5 remains blocked by its own upstream issues until separately resolved:

- `UIEF5_UPSTREAM_RESPONSIVE_CONTRADICTION`
- `UIEF5_UNRESOLVED_PROVENANCE_REFERENCES`

Therefore:

```text
OEE_COMPLETE != UIEF5_IMPLEMENTATION_UNBLOCKED
```

## Existing authority is preserved

Conductor owns routing and sequencing. Arbiter retains transition/stop authority. Overseer retains validation evidence authority. The Tuner retains evidence freshness/invalidation coordination. Scribe records durable measurements. The Governor remains legal/compliance governance and is not converted into an execution owner.

OEE does not create a new specialist, expand existing specialist authority, authorize release/deployment/policy activation, or bypass destructive/production/human gates.
