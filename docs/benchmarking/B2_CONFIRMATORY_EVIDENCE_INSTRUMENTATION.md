# B2 Confirmatory Evidence Instrumentation

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Unit: B2.3.1 Executor Evidence Implementation + B2.3.2 Zero-Call Fixture Validation
State: SOURCE_CANDIDATE_ZERO_LIVE_CALLS
Canonical predecessor: 5ab0a042109cdc2aa7eca01b4d356e5c96c888d5
Live model calls authorized by this unit: 0
B2.4 instrumentation pilot: NOT AUTHORIZED
B2.5 confirmatory execution: NOT AUTHORIZED
A5 execution-effective promotion: NOT AUTHORIZED
B4: BLOCKED
```

This unit implements the evidence-repair contract frozen in `B2_CONFIRMATORY_MEASUREMENT_DESIGN.md`. It changes only the non-production B2 topology benchmark measurement surface. It does not attach A5 to Conductor or `RuntimeExecutor`, change production routing, activate parallelism, execute a pilot, or establish topology benefit.

## Recomputable specialist handoffs

Each synthetic specialist call now retains:

- exact `response_text`;
- `response_encoding = UTF-8`;
- exact UTF-8 byte count;
- SHA-256 of the raw UTF-8 response bytes;
- the existing canonical response digest;
- exact prompt digest;
- ordered `prior_advisory_inputs` references.

Each prior-advisory reference records the source call index, specialist identity, UTF-8 byte count, and raw-byte SHA-256. The fixed finalizer records `advisory_inputs` in the same canonical specialist-name ordering used to construct its prompt.

The executor records a deterministic context-transfer ledger:

```text
downstream_specialist_handoff_bytes
+ finalizer_advisory_bytes
= recomputed_context_transfer_bytes
```

`communication.context_transfer_bytes` is derived from that ledger. The pure recomputation helper rejects any externally supplied reported value that does not equal the recomputed value.

Synthetic specialist advisories are retained only up to 16,384 UTF-8 bytes per specialist. Exceeding the ceiling yields `INVALID_RUN / MEASUREMENT_CAPTURE_FAILURE`; the oversized raw text is not retained or truncated. Only its observed byte count and SHA-256 are kept for diagnosis.

## Exact Codex counter provenance

The shared Codex parser already retains the decoded event stream. B2.3.1 leaves that shared adapter unchanged and, inside the A5 benchmark executor, copies the exact `turn.completed.usage` object from the parsed event before the A5 call evidence is assembled.

Every B2 call now records:

- exact `turn_completed_usage` object;
- canonical SHA-256 digest of that object;
- input, cached-input, output, and reasoning-output counters;
- derived `non_cached_input_tokens`;
- counter identity fields;
- deterministic `counter_stability_key`;
- `counter_stability_classification = null` at single-run capture time.

The counter identity binds:

```text
counter_id
prompt_digest
role
specialist
cli_version
model
reasoning_effort
transport
workspace_identity
```

The executor rejects `cached_input_tokens > input_tokens` rather than coercing or estimating counters.

## Cross-run stability classification

`classify_counter_stability()` is deliberately pure and cross-run. It requires repeated evidence records sharing a stability key and returns exactly one of:

- `STABLE_EXACT`
- `CACHE_STATE_VARIANT`
- `INPUT_COUNTER_VARIANT`
- `UNSTABLE_ATTRIBUTION`

A single run is never self-certified as stable. Cross-run reconciliation must apply the classifier after repeated first-stage control groups are collected.

Host token efficiency remains claim-ineligible unless all repeated first-stage control groups required by the future frozen measurement plan classify `STABLE_EXACT`. Failure of that gate does not invalidate independently recomputable context-transfer evidence.

## Workspace identity

The existing Git-worktree preflight remains mandatory. B2.3.1 additionally derives a workspace identity digest from the resolved workspace path and the verified `is_inside_work_tree=true` state. That identity becomes part of every counter-stability key.

## Zero-call fixture validation

The focused suite remains:

```text
tests/runtime/test_comparative_benchmark_a5_topology_executor.py
```

It now covers:

1. exact UTF-8 bytes and raw-byte SHA-256 retention;
2. context-transfer component recomputation;
3. mismatch rejection;
4. 16,384-byte advisory-ceiling rejection before the next call;
5. exact `turn.completed.usage` preservation and digest binding;
6. `STABLE_EXACT` classification;
7. `CACHE_STATE_VARIANT` classification;
8. `INPUT_COUNTER_VARIANT` classification;
9. `UNSTABLE_ATTRIBUTION` classification;
10. cached-input greater than input rejection;
11. integration through injected fake call/version/Git runners only.

These tests use synthetic fixtures and injected runners. They make zero model calls and authorize none.

## Historical evidence boundary

B2.3.1 does not rewrite the valid B2 calibration. Historical B2.1 and B2.2 records remain unchanged. The calibration remains evidence that all 20 recorded runs completed and that no quality difference was observed, while topology benefit remains `NOT_ESTABLISHED`.

The new instrumentation exists so future pilot and confirmatory evidence can be independently recomputed rather than inferred from unrecoverable handoff content or assumed-stable host counters.

## Next gate

After exact-head validation and canonicalization of this implementation, B2.4 may become eligible for a **separately frozen and separately human-authorized instrumentation pilot**. Eligibility still requires an exact-host zero-call preflight, a frozen two-task pilot plan, explicit resource ceilings, and a fresh human live-execution authorization.

Nothing in B2.3.1 or its CI validation grants that authority.
