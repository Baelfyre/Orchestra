# Comparative Measurement B3 - Murmurs Isolated Calibration Readiness

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B3 Murmurs Isolated Comparative Experiment
Current bounded unit: B3.0 Calibration Readiness
State: PLAN_ONLY_READY_NO_MEASUREMENT
Canonical entry: 6ec1a549370eaf73249eb3ddcffe5e464c5eb4ae
Canonical entry tree: 1b9f835889ae4c81e97a48df5f4fd0b2ada1ddf9
Authoritative benchmark machine state: B0/B1 only
Measurement maturity after plan-only validation: MEASUREMENT_NOT_STARTED
Murmurs benefit: NOT ESTABLISHED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
```

B3.0 validates the Murmurs-isolated calibration schedule without running a model or provider. It proves that the canonical B1 harness can hold topology fixed while scheduling exactly three communication arms: `DEFAULT`, `CAVEMAN`, and `MURMURS`.

It does not measure token use, cost, latency, task quality, semantic preservation, or Murmurs benefit.

## Evidence boundary

```text
PLAN-ONLY VALIDATION != MEASURED CALIBRATION
SYNTHETIC FIXTURE != MURMURS BENEFIT EVIDENCE
CAVEMAN PUBLISHED RESULTS != ORCHESTRA RESULTS
MEASUREMENT_NOT_STARTED remains current after B3.0
```

No new canonical machine measurement record is introduced by B3.0. The authoritative benchmark machine state remains the B0 contract and B1 harness until real B3 run and experiment evidence exists.

## Causal variable

B3 changes only communication mode.

The topology identity is fixed across all arms:

```text
topology_class = FIXED_DETERMINISTIC
same topology_candidate_id
same topology_digest
```

The required communication arms are exactly:

```text
DEFAULT
CAVEMAN
MURMURS
```

The runner rejects missing, additional, duplicate, or topology-varying Murmurs-isolated arms.

## Caveman role

Caveman is the external comparative baseline frozen by B0:

```text
repository: JuliusBrussee/caveman
pinned revision: ae405e872270acc57484693612ae038b16c8f6cd
role: PRIMARY_MURMURS_EXTERNAL_COMPARATIVE_BASELINE
runtime dependency: false
Orchestra authority source: false
```

The Caveman arm must be executed on Orchestra's own controlled workload under the same provider/model and measurement identity as the other arms. Published Caveman percentages cannot be imported as Orchestra benefit evidence.

B3.0 does not vendor Caveman, copy its source, install it, execute it, or introduce it as an Orchestra runtime dependency.

## Calibration floor

B3 inherits the B0 calibration floor:

```text
minimum tasks = 5
repetitions per arm = 2
fixed topology = required
communication arms = DEFAULT / CAVEMAN / MURMURS
arm order = randomized reproducibly
claims allowed = false
```

The plan-only fixture covers five communication-relevant task classes:

1. `SINGLE_DOMAIN`
2. `MULTI_DOMAIN`
3. `DEBUGGING`
4. `DOCUMENTATION_AND_IMPLEMENTATION`
5. `HIGH_COORDINATION`

These are synthetic planning scenarios only.

## Machine-readable plan-only fixture

The fixture is:

```text
tests/fixtures/benchmarking/b3-murmurs-isolated-calibration-plan-only.json
```

It deliberately uses:

- synthetic task identities and digests;
- one synthetic fixed topology identity;
- `NO_PROVIDER_PLAN_ONLY`;
- `NO_MODEL_PLAN_ONLY`;
- no provider credentials;
- no network requirement;
- `execution_allowed=false` for every task.

Expected plan size:

```text
5 tasks x 2 repetitions x 3 communication arms = 30 planned runs
```

Each of the ten task/repetition blocks must contain exactly one `DEFAULT`, one `CAVEMAN`, and one `MURMURS` arm on the same topology identity.

The regression supplies an executor path that does not exist while `plan_only=True`. Successful plan generation therefore proves the executor is not invoked.

## Real B3 calibration entry gate

A real measured B3 calibration must replace all synthetic fixture identities with evidence-bound values and satisfy all B0/B1 controls.

Required entry evidence includes:

1. one fixed deterministic topology that is already permitted for the controlled workload;
2. identical topology candidate identity and digest across all three communication arms;
3. exact starting-state digest for every task;
4. exact task-prompt digest for every task;
5. identical provider and model identity across paired arms;
6. identical specialist set and required-specialist set;
7. identical authority, governance, validation, tool-access, retry, environment, and resource-budget identities;
8. identical system instructions except for the bounded communication mechanism under test;
9. same provider-native counter identity for any token delta claim;
10. a bounded resource ceiling before any paid or metered provider/model execution.

A general benchmark authorization is not interpreted as unlimited spend authority.

## Measurement authority

Provider or host-native counters are authoritative when available.

The following values must remain unavailable rather than estimated when the provider does not expose trustworthy comparable counters:

- input tokens;
- output tokens;
- cached input tokens;
- reasoning tokens;
- fresh or billable tokens;
- monetary cost.

A token or cost delta is valid only when the compared arms share the same provider counter identity.

Repository-side byte counts or token estimates may be descriptive diagnostics, but they cannot substitute for provider-native counters in a live token-savings claim.

## Quality and preservation gates

Efficiency is subordinate to correctness and governance. A Murmurs benefit claim cannot be established if communication reduction causes meaningful regressions in:

- task completion;
- required validation;
- governance boundaries;
- remediation iterations;
- regressions introduced;
- semantic preservation;
- required-information retention;
- handoff integrity;
- required specialist participation.

The B0 lexicographic winner hierarchy remains authoritative:

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

## Resource boundary

B3.0 operates in:

```text
NO_SPEND_PLAN_ONLY
```

It authorizes no:

- paid model call;
- metered provider call;
- external benchmark compute spend;
- provider credential use;
- Caveman installation or execution;
- production runtime execution.

A later live calibration using paid or metered resources requires an explicit machine-bindable ceiling. Useful dimensions include maximum spend, maximum run count, permitted provider/model identity, token ceiling when exposed, timeout, and fail-closed termination when the ceiling is exhausted.

## Future measured calibration outputs

A valid measured calibration should capture at minimum:

- validated governed task outcome;
- remediation iterations;
- validation failures;
- regressions introduced;
- wall-clock latency;
- provider-native token counters when available;
- provider-reported cost when available;
- specialist and cross-specialist message counts;
- handoffs and handoff failures;
- duplicate work and contradiction events;
- context transfer bytes;
- semantic preservation failures;
- required information omissions.

Calibration validates capture quality and estimates variance. It does not establish confirmatory benefit.

## B4 remains blocked

The combined A5 x Murmurs experiment cannot start from plan-only readiness alone.

```text
B4 requires valid measured B2 evidence
AND valid measured B3 evidence
```

B2.0 and B3.0 plan-only fixtures are not sufficient evidence for B4 entry.

## Exit condition for B3.0

B3.0 is complete when fresh exact-head validation proves:

- the plan-only manifest is schema-valid;
- at least five synthetic planning tasks are present;
- exactly two repetitions per arm are configured;
- exactly three communication arms exist;
- those arms are exactly `DEFAULT`, `CAVEMAN`, and `MURMURS`;
- all arms share one identical `FIXED_DETERMINISTIC` topology identity;
- same-counter-identity requirement is preserved;
- repeated plan generation is deterministic for the same seed;
- no executor is invoked;
- no run index or experiment evidence is emitted;
- no token-savings or benefit claim is recorded.

Only after that closeout may the workflow consider a real B3 calibration executor and bounded live-resource authorization.
