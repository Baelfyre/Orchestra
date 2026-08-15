# Control Plane Re-foundation P0-P1: Machine Contracts and Evidence Kernel

Status: `IMPLEMENTED_CANDIDATE_PENDING_CI`
Parent issue: `#273`
Child issue: `#274`
Frozen baseline: `5bb2ab300c089fdecadf82b093ff34b30b8a6de2`

## Purpose

This first vertical slice establishes a machine-verifiable trust boundary for two failure classes observed during governed cross-project operation:

1. an agent-supplied or synthesized full Git SHA being accepted as canonical evidence; and
2. a non-zero validation command being narrated as `PASS`.

The slice deliberately does not redesign all governance at once. It creates the primitive receipt contracts that later phases can bind into Padayon promotion, Arbiter decisions, compliance consumption, host parity, and context compilation.

## Architectural rule

`Agents reason. Machines attest.`

For this slice:

- JSON is the machine wire/state representation;
- JSON Schema documents the versioned external contract;
- frozen Python dataclasses enforce the same critical invariants without a new dependency;
- canonical JSON serialization plus SHA-256 provides stable receipt identity;
- Markdown remains explanatory and has no authority over receipt values.

## Source-state receipt

`SourceStateReceipt` binds:

- repository;
- canonical branch;
- exact live canonical SHA;
- verification timestamp and method;
- optional PR number and exact PR head;
- optional merge/squash SHA;
- optional tree SHA.

All Git object identifiers are exact 40-character hexadecimal values. Abbreviated SHAs are rejected. A canonical closeout receipt that contains a merge/squash SHA requires that value to equal the observed live canonical SHA.

Callers must use `assert_canonical_sha()` / `assert_pr_head()` when comparing a candidate tracker or agent claim to the receipt. Prefix equality has no authority.

## Validation-execution receipt

`ValidationExecutionReceipt` binds:

- a stable command identifier;
- argv-style command data;
- integer process exit code;
- start and finish timestamps;
- SHA-256 digests of stdout and stderr;
- optional pre/post Git heads;
- optional bounded evidence reference.

The `verdict` is a derived property:

- `exit_code == 0` -> `PASS`
- otherwise -> `FAIL`

There is intentionally no constructor field that allows a host agent to inject a verdict. `assert_claimed_verdict()` exists only to compare prose/agent claims against the machine result and fails closed on disagreement.

## Why no new structured-output framework yet

Orchestra already has deterministic JSON serialization, immutable dataclass-based runtime models, and a Python 3.12 runtime test suite. Adding Pydantic, BAML, Guardrails, TypeChat, or another framework before Orchestra owns its contracts would create dependency and migration risk without solving the core trust-boundary problem.

Third-party tools remain candidates for later evaluation under #273. The invariant and schema ownership stays with Orchestra.

## Regression fixtures represented

The tests encode incident-shaped values rather than generic examples:

- correct Orderly FBR0 PR head vs a different full SHA sharing the same seven-character prefix;
- correct Orderly FBR0 canonical merge/main vs a different full SHA sharing the same seven-character prefix;
- `git diff --check`-style exit code `2` with an attempted agent claim of `PASS`.

These cases must remain permanent regressions.

## Deferred to subsequent phases

Not included here:

- Padayon compare-and-swap / write leases;
- current Padayon Orderly SHA correction;
- Arbiter Analyst / Kernel split;
- Compliance Registry query/consumption receipts;
- routing receipts;
- host capability schema;
- JSONL event store / Context Compiler;
- deterministic Markdown projections;
- remediation circuit breakers;
- OS/sandbox hard enforcement;
- release/version mutation.
