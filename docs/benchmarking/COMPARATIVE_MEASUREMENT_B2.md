# Comparative Measurement B2 - A5 Isolated Calibration Readiness

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Current bounded unit: B2.0 Calibration Readiness
State: CALIBRATION_PLAN_FROZEN_NO_EXECUTION
Canonical entry: eed2e870dbfbc2782f941015761886e55c849185
Canonical entry tree: 57cf92b239a05402ecf191537e2e398a236cadb5
Measurement maturity after plan-only validation: MEASUREMENT_NOT_STARTED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
```

B2.0 freezes the next executable measurement boundary without performing a live benchmark. It validates the A5-isolated calibration design, task-class floor, paired all-arm schedule, deterministic randomization, and no-executor `--plan-only` path.

It does not establish A5 benefit, complete measured calibration, provide a production topology scheduler, attach A5 to Conductor dispatch or `RuntimeExecutor`, authorize A6, spend paid provider resources, deploy, or publish a release.

## Why B2.0 is separate from measured calibration

B0 defines calibration as a measured stage with at least five tasks and two repetitions per arm. B1 provides the harness that can collect those measurements. A plan-only fixture can prove that the harness will schedule the experiment correctly, but it cannot measure outcome variance, latency, token use, cost, remediation burden, or empirical topology performance.

Therefore:

```text
PLAN-ONLY VALIDATION != MEASURED CALIBRATION
SYNTHETIC FIXTURE != A5 PERFORMANCE EVIDENCE
MEASUREMENT_NOT_STARTED remains current after B2.0
```

This separation prevents test fixtures from being misreported as adaptive-performance evidence.

## B2 causal variable

The B2 primary experiment changes only the coordination topology.

Every paired arm must use:

```text
communication_mode = DEFAULT
```

The real experimental arms must come from one already-permitted, frozen A5 eligibility envelope. The A5 shadow scorer receives that same frozen candidate set, but it cannot choose which arm runs. Every eligible arm is executed independently by the benchmark harness.

A5 remains structurally shadow-only:

```text
topology_effective = false
shadow_influenced_execution = false
runtime_topology_control = false
```

## Calibration floor

The frozen calibration planning floor is:

```text
minimum tasks = 5
repetitions per arm = 2
all eligible topology arms = executed in every task/repetition block
arm order = randomized reproducibly
communication mode = DEFAULT for every arm
benefit claim = prohibited
```

The planning fixture covers five task structures:

1. `ARCHITECTURE_HEAVY`
2. `DEBUGGING`
3. `VALIDATION_HEAVY`
4. `PARALLEL_FRIENDLY`
5. `HIGH_COORDINATION`

These fixture scenarios are synthetic planning records only. They do not assert that their synthetic topology candidates are currently eligible for any production task.

## Plan-only fixture

The deterministic fixture is:

```text
tests/fixtures/benchmarking/b2-a5-isolated-calibration-plan-only.json
```

It deliberately uses:

- synthetic task identities;
- synthetic starting-state and prompt digests;
- synthetic topology identities;
- `NO_PROVIDER_PLAN_ONLY` and `NO_MODEL_PLAN_ONLY` placeholders;
- no provider credentials;
- no network requirement;
- no allowed task execution.

The fixture exists only to validate the experiment scheduler and manifest boundary.

The regression invokes the runner with an executor path that does not exist and uses `plan_only=True`. Success therefore proves the plan-only path does not invoke the configured executor.

Expected plan size for the current fixture:

```text
5 tasks x 2 repetitions x 3 synthetic arms = 30 planned runs
```

For each of the ten task/repetition blocks, all three configured arms must appear exactly once.

## Real B2 calibration entry gate

Before a real measured B2 calibration may run, the executor input must replace synthetic planning values with evidence-bound identities.

Required entry evidence includes:

1. a validated coordination session;
2. one frozen exact A5 eligibility envelope for the controlled workload;
3. at least two already-permitted topology candidates;
4. a complete required-specialist set;
5. exact topology candidate identities and digests;
6. exact starting-state digest for every task;
7. exact task-prompt digest for every task;
8. identical provider/model/tool/specialist/authority/governance/validation/retry/resource identities across paired arms except for the topology variable;
9. the same candidate set supplied to both benchmark execution and the A5 shadow scorer;
10. a bounded resource ceiling before any paid or metered provider/model execution.

A general authorization to continue the benchmark program is not treated as an unlimited spend ceiling.

## Resource boundary

B2.0 operates in:

```text
NO_SPEND_PLAN_ONLY
```

It authorizes no:

- paid model calls;
- metered provider calls;
- external benchmark compute spend;
- provider credential use;
- production runtime execution.

If the later calibration executor uses paid resources, the resource ceiling must be explicit and machine-bindable before execution. Useful ceiling dimensions include maximum total spend, maximum fresh/billable tokens when exposed, maximum run count, permitted provider/model identity, timeout, and a fail-closed stop on ceiling exhaustion.

## Future measured calibration outputs

When the real calibration gate is satisfied, measured B2 evidence should support evaluation of:

- A5 Top-1 match against the empirically preferred eligible topology;
- Top-k match;
- regret;
- validated governed task success;
- remediation iterations;
- resource consumption when trustworthy;
- latency when trustworthy;
- coordination overhead;
- task-class conditional behavior;
- invalid-run rate and cause.

Calibration exists to validate measurement quality and estimate variance. It cannot establish confirmatory benefit.

## Winner hierarchy remains unchanged

B2 inherits the B0 lexicographic winner hierarchy:

```text
1. Governance valid
2. Task success
3. Validation success
4. Fewer remediation iterations
5. Lower resource consumption
6. Lower latency
7. Lower communication overhead
8. Deterministic baseline tie-break
```

Efficiency cannot compensate for invalid governance, incorrect outcomes, or failed validation.

## Synthetic topology identities are not eligibility evidence

The fixture includes three synthetic topology classes to exercise the planner:

- sequential;
- hierarchical decomposition;
- parallel join.

These are representative test inputs only. Real A5 eligibility is produced by existing deterministic coordination state under the A5 contract. The fixture cannot create eligibility, activate parallelism, omit required specialists, change ownership, or increase any resource ceiling.

## Machine record

The B2.0 readiness contract is:

```text
machine/benchmarking/a5-isolated-calibration-plan.v1.json
```

It records:

- the canonical B1 dependency;
- calibration sample floor;
- real execution entry requirements;
- synthetic fixture boundary;
- no-spend state;
- no-promotion authority boundary;
- the block on measured calibration until real eligibility/workload identity and any required resource ceiling exist.

## Exit condition for B2.0

B2.0 is complete when fresh exact-head repository validation proves:

- the machine readiness record is present;
- the plan-only manifest is schema-valid;
- at least five synthetic planning tasks are present;
- exactly two repetitions per arm are configured;
- every A5-isolated arm uses `DEFAULT` communication;
- every configured arm is scheduled in every task/repetition block;
- repeated plan generation is deterministic for the same seed;
- no executor is invoked by plan-only validation;
- no measured calibration or benefit claim is recorded.

Only after that closeout may the workflow consider a real B2 calibration executor and bounded live-resource authorization.
