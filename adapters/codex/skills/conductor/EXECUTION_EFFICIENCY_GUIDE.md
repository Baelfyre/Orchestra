# Conductor Execution Efficiency Guide

## Purpose

Apply Orchestra Execution Efficiency V1 without weakening evidence, implementation quality, governance, security, validation, or human authority.

Core invariant:

```text
MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY
```

This guide is progressive-disclosure context. Load it when Conductor is coordinating multi-step, cross-specialist, governed, autonomous, or validation-heavy work. Do not load it for a trivial direct single-specialist task.

## OEE-1 Owner-first specialist budget

1. Identify the specialist that owns the current decision.
2. Activate only that owner first.
3. Default active parallel specialists to exactly one.
4. A supporting specialist may be planned only when an actual cross-domain authority dependency or required adversarial review exists.
5. Record the expansion reason and evidence before adding the supporting specialist.
6. Supporting specialists are sequenced after the owner unless a future governed contract explicitly changes the concurrency ceiling.
7. Retry a failed specialist invocation at most once. After the retry, use the declared fallback, record capacity unavailability, or stop if the missing specialist is mandatory.
8. Never retry an optional specialist merely because capacity may later recover.

Valid expansion reasons:

- `CROSS_DOMAIN_AUTHORITY`
- `ADVERSARIAL_REVIEW_REQUIRED`

## OEE-2 Earliest decisive evidence

After every authoritative finding, ask whether it already determines the current transition.

If sufficient evidence establishes a blocker:

```text
EARLIEST_DECISIVE_EVIDENCE_WINS
```

Then:

- stop downstream specialist work,
- stop implementation,
- stop expensive validation,
- record the owning specialist and evidence,
- return to the required owner, Arbiter, or human gate.

Do not continue confidence-building work that cannot change the current decision.

## OEE-3 Evidence reuse and search escalation

Reusable evidence must remain bound to the exact consumed source revision and source identity. If either changes, treat the evidence as stale and reread only what is affected.

Search in this order:

```text
EXACT_PATH
-> EXACT_SYMBOL
-> BOUNDED_DIRECTORY
-> REPOSITORY_WIDE
-> EXTERNAL
```

Advance only when the current level is insufficient. Do not repeat equivalent repository-wide searches after absence or contradiction is already established with sufficient evidence.

## OEE-4 Validation escalation

Use this order:

```text
SYNTAX_SCHEMA
-> DIRECT_TESTS
-> SUBSYSTEM
-> REPOSITORY_QUALIFICATION
-> PROTECTED_GATES
```

`REPOSITORY_QUALIFICATION` and `PROTECTED_GATES` require a stable candidate. Do not rerun full qualification for exploratory edits or unchanged candidates.

A failed cheaper prerequisite blocks the more expensive tier until remediated.

## OEE-5 CI wait boundary

Do not use active model reasoning merely to wait for CI.

Prohibited default behavior:

```text
gh pr checks --watch
repeated unchanged polling loops
reasoning turns whose only purpose is waiting
```

At a decision point or after a state-change signal, read CI once. If required checks are still running and no action is possible, yield the reasoning path until a later state read.

## OEE-6 Phase-local context packs

Autonomous campaign authorization may span multiple phases, but working context is phase-local.

For each active phase include only:

- canonical baseline identity,
- active phase authority,
- exact required contracts/evidence,
- applicable specialist ownership,
- current unresolved questions,
- directly relevant validation obligations.

Do not preload later phase implementation detail. Do not duplicate evidence already represented by an exact-source identity. A phase change invalidates the previous phase pack unless explicitly reused by exact identity.

## OEE-7 Controlled replay

Before claiming efficiency improvement, replay a known expensive decision path under these controls.

The replay must preserve the same or safer disposition while showing a material reduction in redundant execution activity. Do not invent historical token totals or command counts that were not measured.

For the UIEF-5 2026-09-05 incident, the supported historical facts are:

- four unique specialist roles were observed: Clockwork, Overseer, Cloak, Arbiter,
- specialist capacity failures/retries occurred,
- broad repository investigation occurred,
- CI watch behavior occurred,
- zero UIEF phases advanced canonically,
- a Cloak-owned upstream responsive contradiction was sufficient to block downstream UIEF-5 implementation.

The replay should reach the same blocker with owner-first Cloak analysis, zero downstream implementation after the decisive stop, and no active CI watch.

## OEE-8 UIEF resume gate

OEE completion does not itself resolve UIEF design/provenance blockers.

UIEF may be reopened as the next development lane only when OEE-0 through OEE-7 have current evidence and the OEE resume gate passes. After reopening, UIEF-5 must still resolve its own upstream responsive/provenance blockers before implementation continues.

## Authority boundary

Execution efficiency changes sequencing and resource use only. It does not:

- grant a specialist new domain authority,
- bypass Arbiter or human transition gates,
- remove required security/governance validation,
- authorize release/deployment/policy activation,
- authorize destructive or production actions,
- convert optional evidence into authoritative evidence,
- create a new specialist.
