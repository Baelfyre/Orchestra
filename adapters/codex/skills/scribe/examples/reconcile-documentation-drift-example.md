# Scribe `RECONCILE` Documentation Drift Example

## Request

Check whether current documentation still matches the implemented and validated system.

## Direction

`RECONCILE`

## Compared Evidence

- README at reviewed revision states the API accepts `status=pending|complete`.
- Current API contract at the same reviewed revision accepts `pending|processing|complete`.
- Current tests include the `processing` state.
- No evidence indicates that the implementation change was unauthorized.

## Reconciliation Findings

| ID | Type | Documented State | Observed State | Evidence | Owner | Required Action |
|---|---|---|---|---|---|---|
| DRIFT-001 | `DOC_DRIFT` | README lists two states | Contract and tests list three states | Reviewed README, API contract, tests | Scribe | Update documentation after technical truth is confirmed |

This is not automatically `IMPLEMENTATION_DRIFT`. The evidence establishes stale documentation, not a violation of an approved design.

If an approved specification instead prohibited `processing`, Scribe would classify the conflict as potential `IMPLEMENTATION_DRIFT` and route the underlying decision to the appropriate owner before changing the specification or code.

## Unsupported Claim Check

If the README also says "all status transitions are fully validated" but only test definitions are available without qualifying execution evidence, classify that statement as `VALIDATION_GAP` / `MISSING_EVIDENCE`. Do not rewrite it as passed.

## Completion

The reconciliation closes only when the documentation is corrected against verified truth, the implementation/specification conflict is routed and resolved, an explicit deferral/supersession is recorded, or the unresolved evidence gap remains clearly documented.
