# Conductor Execution Efficiency Guide

Status: OEE-1 through OEE-6 operational guidance

Use this guide for governed, ambiguous, cross-domain, delegated, or multi-specialist work. Do not load it for an obvious direct single-specialist route.

Core invariant:

```text
MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY
```

Efficiency never permits skipping required governance, security, validation, authority, or implementation-quality checks.

## OEE-1 Owner-first routing

1. Identify the owner of the current decision or output.
2. Invoke that owner first.
3. Keep at most one specialist active at a time by default.
4. Do not pre-hydrate supporting specialists.
5. Add a different specialist only when one of these is explicit:
   - a material cross-domain ownership boundary;
   - adversarial review is required by the phase;
   - the current specialist returns `SPECIALIST_REROUTE_REQUIRED`.
6. A specialist gets at most one retry after its initial attempt.
7. An optional review cannot become blocking without explicit authority.
8. Prefer sequential handoff over parallel fan-out.

The presence of several potentially useful specialists is not sufficient reason to invoke them.

## OEE-2 Earliest decisive evidence

When sufficient authoritative evidence establishes a stop condition:

```text
EARLIEST_DECISIVE_EVIDENCE_WINS
```

Record:

- owner;
- evidence sufficiency;
- stop requirement;
- downstream execution allowed;
- reason;
- exact evidence references.

If `evidence_sufficient=true` and `stop_required=true`, downstream execution must be false.

After a decisive stop:

- do not load downstream specialists;
- do not continue implementation analysis;
- do not broaden repository searches unless required to characterize the blocker;
- do not run expensive qualification;
- return to the owning authority or human gate.

## OEE-3 Evidence reuse and search escalation

Reusable evidence must remain bound to exact source identity.

A reusable evidence record includes:

- evidence identifier;
- source reference;
- exact source identity;
- content digest;
- evidence tier;
- allowed consumers.

If source identity changes, invalidate the cached evidence and reread it.

Search escalation is strictly:

```text
EXACT_PATH
-> EXACT_SYMBOL
-> BOUNDED_DIRECTORY
-> REPOSITORY_WIDE
-> EXTERNAL
```

Advance one level only when the narrower level is insufficient. Do not repeat an equivalent search against unchanged source identity unless new evidence justifies it.

## OEE-4 Risk-based validation

Validation order is:

```text
SYNTAX_SCHEMA
-> DIRECT_TESTS
-> SUBSYSTEM
-> REPOSITORY_QUALIFICATION
-> PROTECTED_GATES
```

All prior required stages must pass before the next stage.

`REPOSITORY_QUALIFICATION` and `PROTECTED_GATES` require a stable candidate. Do not repeatedly run full/native/mutation/security matrices while the implementation is still changing.

Validation success remains evidence only and creates no execution, merge, release, deployment, or policy authority.

## OEE-5 CI wait boundary

Do not use continuous CI watch loops as model reasoning work.

When CI state is unchanged:

- stop active reasoning;
- record passive wait;
- return control to the host or caller.

When CI state changes, inspect the changed state once and act only on a concrete failure or completed gate.

Continuous `--watch` style polling is prohibited by the execution budget.

## OEE-6 Phase-local context packs

Load minimum sufficient context for the current phase.

A phase context pack contains:

- phase identifier;
- one owner specialist;
- one bounded objective;
- required exact-source references;
- conditional references that are not loaded until triggered;
- unresolved questions;
- allowed actions;
- prohibited actions.

Do not automatically load historical context. Historical context requires an explicit reason and must still be relevant to the current decision.

Required and conditional references must be unique and source-identity bound.

## Execution order

For an OEE-governed phase:

1. E0 ORIENTATION
2. E1 INPUT_INTEGRITY
3. route one owner
4. E2 TARGETED_ANALYSIS
5. stop immediately on decisive evidence
6. E3 IMPLEMENTATION only if E0-E2 pass
7. progressively validate the stable candidate
8. E4 QUALIFICATION
9. E5 PROMOTION only under existing authority

## Compact efficiency decision

```text
Execution Efficiency:
Owner:
Active specialist count:
Requested specialist:
Invocation role:
Invocation reason:
Retry number:
Current evidence tier:
Decisive blocker:
Search stage:
Validation stage:
Candidate stable:
CI disposition:
Context pack:
Next action:
```

Do not add fields merely to make the output look comprehensive. Record only decision-changing information.
