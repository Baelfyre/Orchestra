# B2.1 A5 Topology Execution Enablement

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Unit: B2.1 Topology Execution Enablement
State: SOURCE_CANDIDATE_ZERO_LIVE_CALLS
Canonical entry: fee39a1feae254dae0de54d21663bed4cc3f1fd2
Canonical entry tree: 4ac379e9f05290f3e282cc66dee46e35ef4a157e
A5 execution-effective selection: NOT AUTHORIZED
A6/A7/A8: NOT AUTHORIZED
B4: BLOCKED
Live B2 model calls: 0
```

B2.1 fixes an experimental-validity gap discovered after the B2.0 plan-only freeze. The shared harness can schedule A5 topology arms, but the existing Antigravity and Codex communication executors do not enact those topology fields. They retain `topology_candidate_id` and `topology_digest` in provenance while performing the same single-model task execution.

Therefore:

```text
DIFFERENT TOPOLOGY LABELS != DIFFERENT TOPOLOGY EXECUTION
PROVENANCE FIELD != EXECUTION MECHANIC
B2 PLAN-ONLY FIXTURE != REAL A5 ELIGIBILITY
A5 SHADOW RANKING != BENCHMARK ARM SELECTION
```

Running B2 with the existing B3 executors would create a false experiment. B2.1 adds a non-production topology executor so later B2 evidence can change only the frozen coordination-order variable while leaving A5 non-effective in production.

## Experimental mechanic

B2.1 supports one deliberately narrow topology dimension:

- required specialists: `Clockwork` and `Overseer`;
- communication: `DEFAULT` only;
- stage mode: sequential only;
- one required specialist per stage;
- candidate difference: specialist stage order and resulting prior-advisory transfer;
- fixed finalizer: identical and outside the topology variable.

The intended first calibration candidates are:

```text
Candidate A
Clockwork -> Overseer -> fixed finalizer

Candidate B
Overseer -> Clockwork -> fixed finalizer
```

These names describe the target calibration design only. B2.1 does **not** itself declare them eligible. The later B2.2 freeze must supply a validated canonical A5 eligibility envelope proving the exact candidate identities are already permitted for the benchmark session.

Parallel execution is intentionally excluded from B2.1. Although A5 schemas can describe a `PARALLEL` stage, the canonical A5 boundary explicitly does not create parallel execution capability. B2.1 fails closed on every parallel candidate instead of using a benchmark adapter to smuggle new runtime capability into the experiment.

## Specialist projections

B2.1 uses compact, versioned benchmark projections instead of embedding entire specialist skill files into every model prompt.

### Clockwork projection

Scope: architecture, dependency direction, structural constraints, ordering risks, and implementation boundaries.

### Overseer projection

Scope: validation sufficiency, evidence integrity, failure conditions, governance preservation, and testable acceptance criteria.

Both projections are advisory and non-authorizing. They are not replacements for canonical specialist runtime instructions, do not grant ownership or authority, and exist only to isolate the coordination-order variable without making full skill-file size a prompt-cost confound.

Machine-pinned projection digests are recorded in `machine/benchmarking/b2-a5-topology-executor-binding.v1.json`.

## Execution sequence

For one benchmark run:

1. Validate the executor request and `A5_ISOLATED` experiment identity.
2. Load one canonical A5 eligibility envelope.
3. Require the manifest eligibility digest and candidate-set order to equal that envelope exactly.
4. Require the requested candidate to exist in the envelope and its canonical digest to match the arm.
5. Require `DEFAULT` communication and the complete `Clockwork + Overseer` required-specialist set.
6. Reject any parallel/multi-specialist stage.
7. Execute stage 1 as one bounded read-only Codex call.
8. Execute stage 2 as one bounded read-only Codex call, supplying stage 1's advisory output.
9. Execute one identical fixed finalizer call with both advisories sorted by canonical specialist name.
10. Validate the final response using `EXACT_JSON_CONFORMANCE_V1`.
11. Aggregate provider-native usage across all model calls into one benchmark-run measurement.
12. Emit the A5 shadow observation for the same frozen eligible set while keeping `topology_effective=false` and `shadow_influenced_execution=false`.

The shared benchmark harness chooses which configured arm executes. The A5 shadow ranker never selects the benchmark arm.

## Codex safety boundary

The live path is designed to reuse the already-qualified Codex measurement surface only after a separate B2.2 host freeze:

```text
provider: openai-codex
CLI: 0.148.0 planned
model: gpt-5.6-sol planned
reasoning: medium planned
transport: jsonl-usage
sandbox: read-only
approval: never
agents: false
web: disabled
shell tool: false
workspace: existing Git worktree required
```

The exact Node/Codex command prefix is deliberately not hard-coded into source because it is host-specific. B2.2 must pin the actual executable paths and cryptographic identities before any live call.

Any Codex tool event rejected by the canonical JSONL parser remains an invalid measurement path.

## Resource accounting

A two-stage B2.1 candidate consumes three model calls per benchmark run:

```text
2 specialist advisory calls
+ 1 fixed finalizer call
= 3 model calls / benchmark run
```

Provider-native `input_tokens`, `cached_input_tokens`, `output_tokens`, and reasoning-output tokens are retained per call. Run-level token fields aggregate all three calls. The run-level total used for the hard resource ceiling is:

```text
sum(input_tokens + output_tokens) across all calls
```

A per-run ceiling is mandatory at executor invocation. If the ceiling is crossed after a specialist call, execution stops before later calls. If the finalizer causes the ceiling to be crossed, the run is invalidated. Automatic retry remains off.

B2.1 freezes no live ceiling and performs no model call.

## A5 shadow observation

The executor feeds the same frozen eligibility envelope to the canonical A5 shadow ranker. For B2.1 execution-enablement tests, the evidence packet is exact-bound and empty; no synthetic performance evidence is invented.

The emitted observation includes:

- eligibility digest;
- shadow decision digest;
- ranked candidate IDs;
- top-ranked candidate ID;
- decision disposition;
- shadow recommendation when one exists;
- `topology_effective=false`;
- `shadow_influenced_execution=false`.

This lets B2 later compare the shadow-ranked order against empirical topology results without letting the ranker control execution.

## Fail-closed boundaries

The executor rejects or invalidates measurement on:

- eligibility-envelope digest mismatch;
- candidate outside the frozen envelope;
- candidate digest mismatch;
- manifest/envelope candidate-set drift;
- non-DEFAULT communication;
- parallel stage;
- required-specialist-set drift;
- task with live execution disabled;
- Codex CLI/model/reasoning drift;
- invalid Git workspace;
- malformed/disallowed Codex JSONL or tool event;
- per-run token-ceiling breach.

No retry is automatic.

## B2.1 exit condition

B2.1 is complete only when the source candidate and later canonical identity prove:

1. topology-arm identity changes actual advisory execution order;
2. the reverse candidate changes which specialist receives prior advisory context;
3. the fixed finalizer remains outside the topology variable;
4. host usage is aggregated over every underlying call;
5. exact candidate/envelope binding fails closed;
6. parallel execution is rejected;
7. a disabled task causes zero model calls;
8. resource-ceiling breach stops the remaining call sequence;
9. A5 shadow output remains non-authorizing;
10. all repository validation gates pass with zero B2 live calls.

## Next gate — B2.2

After B2.1 is canonical, prepare a separate **B2.2 Real Calibration Freeze and Zero-Call Preflight**. It must freeze:

- one validated benchmark coordination session;
- one exact canonical A5 eligibility envelope;
- at least two already-permitted sequential topology candidates;
- one executable B2 task set with adequate topology sensitivity;
- exact starting-state/task-prompt/validation identities;
- the exact Codex command prefix and binary/package digests;
- exact empty Git workspace identity;
- per-run token ceiling;
- cumulative experiment token ceiling;
- maximum underlying model-call count;
- automatic retry OFF;
- stop-on-invalid/identity-drift/tool-event/resource-breach policy.

A zero-live-call preflight must pass after that freeze. Live B2 calibration still requires separate explicit authorization.

## Authority boundary

B2.1 does not:

- make A5 topology-effective;
- attach A5 to Conductor dispatch or `RuntimeExecutor`;
- authorize parallel production execution;
- omit a required specialist;
- change specialist ownership;
- expand authority, capability, governance, provider/privacy, lifecycle, context, or resource ceilings;
- authorize A6, A7, or A8;
- authorize B4;
- release, deploy, activate policy, refresh installed integrations, delete branches, or rewrite history.
