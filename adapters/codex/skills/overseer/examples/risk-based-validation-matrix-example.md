# Risk-Based Validation Matrix Example

## Status

`PLANNED_UNEXECUTED`. No result below is reported as passed.

## Change

A fictional checkout service adds an idempotency key to prevent duplicate orders after client retry.

| Risk | Level and evidence | Data/environment | Pass criterion | Owner |
| --- | --- | --- | --- | --- |
| Same key creates two orders | Unit/property plus database integration | Generated keys, concurrent synthetic clients, non-production database | One logical order and stable replay response | Ponytail executes tests from Chronicler contract |
| Consumer omits or repeats key | Contract | Versioned API schema and old/new consumer fixtures | Declared compatibility and exact error envelope | Overseer gate, Clockwork/Cipher contract inputs |
| Retry after timeout duplicates payment | E2E critical journey | Stubbed payment sandbox and controlled timeout | One payment effect, one order, observable recovery | Ponytail executes; Overseer assesses |
| Test passes only after retry | Flake diagnostic | Seed, worker, first failure, all attempts retained | Deterministic pass or visible blocked/quarantined status | Overseer |
| Latency regresses | Performance acceptance | Fixed dataset, warm-up, repeated non-production runs | Recorded percentile/error/throughput bounds hold | Overseer; Dagger only if pressure execution authorized |

## Evidence Identity

Record commit, contract/schema revisions, environment image, dependency versions, fixture/factory revision, seeds, commands, artifact hashes, first and final outcomes, skips, retries, and limitations.

Property generators must preserve valid checkout relationships and shrink to a replayable counterexample. Mutation testing may target duplicate-prevention branches only after the baseline suite passes. Coverage percentage alone cannot close the risk.

## Exit

The phase remains `PLANNED_UNEXECUTED` until every required row has current evidence. A skipped, retried-away, cancelled, stale, or mismatched result is not permission to proceed.
