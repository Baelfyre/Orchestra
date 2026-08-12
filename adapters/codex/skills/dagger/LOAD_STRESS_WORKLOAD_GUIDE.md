# Load, Stress, Soak, and Workload Modeling Guide

Use this guide to define a bounded non-production workload before selecting a generator or interpreting results. It does not authorize traffic generation.

## Start with the question

- Load: Does the target meet an existing acceptance objective under a representative workload?
- Stress: Where does a bounded limit appear, and does failure remain safe?
- Spike: Does a controlled arrival-rate change cause unsafe queueing, rejection, or recovery?
- Soak: Does a time-bounded steady workload reveal retention, leak, drift, or exhaustion?
- Capacity: What combination of throughput, latency, error, and saturation is sustainable inside the approved envelope?

Do not use one test type as evidence for another. A short throughput run does not prove soak stability; a closed-model virtual-user result does not establish an open arrival-rate capacity.

## Workload model

Record:

- actor and operation mix;
- open arrival rate or closed active-user population;
- think time, pacing, and iteration boundaries;
- request/payload distribution and data cardinality;
- cache state and repeated-key bias;
- warm-up, ramp, steady-state, and recovery windows;
- rate, concurrency, payload, duration, and total-work ceilings;
- expected response distribution and acceptance objective.

An open model emits work independently of response completion and exposes queue growth. A closed model waits for actors to finish and can reduce offered load when the target slows. Choose based on real demand, not convenience.

## Measurement literacy

Capture sample count, throughput, success/rejection/error classes, latency histogram and relevant percentiles, utilization, saturation, queue/pool state, retry volume, and recovery. Keep warm-up and teardown outside the measurement window unless they are the scenario.

Check coordinated omission: if the generator waits through a slow response instead of recording requests that should have arrived, tail latency can appear falsely low. Check generator saturation separately through its CPU, memory, sockets, timers, dropped samples, and network limits.

## Bounded ramp pattern

1. Establish an idle and low-load baseline.
2. Apply the smallest approved step.
3. Hold long enough for the chosen metric window.
4. Compare demand, throughput, latency, errors, saturation, and queue growth.
5. Stop on the first threshold or invariant breach.
6. Remove load and observe recovery through the approved window.

Never continue merely to find a larger failure after a stop condition has fired.

## Interpretation traps

- Average latency hides tails and multimodal behavior.
- Throughput alone can rise while errors or dropped work rise.
- A successful client response does not prove durable state or exactly-once effects.
- Cache-heavy repeated data can make the workload unrepresentative.
- A generator-side bottleneck can look like target capacity.
- A single run without configuration identity or variance is weak evidence.
- Comparing different revisions, datasets, environments, or workload models without disclosure is invalid.

## Safety gate

Planning stays `PLANNING_ONLY` until `SAFETY_GATES.md` identifies the isolated target, owner, data, ceiling, duration, telemetry, abort control, rollback, cleanup, and explicit execution approval. Production and public third-party targets remain excluded.

## Handoff

Dagger defines the bounded failure scenario. Overseer owns acceptance and readiness. Clockwork owns architecture conclusions. Ponytail owns implementation. Cipher owns security/privacy meaning. Scribe owns durable runbooks or reports.
