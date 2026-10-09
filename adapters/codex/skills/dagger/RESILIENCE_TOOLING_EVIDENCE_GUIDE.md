# Resilience Tooling and Evidence Guide

Select tools from the hypothesis and safety envelope. A familiar tool is not evidence of fit, and a tool's dry-run or local mode is not execution authority.

## Tool categories

| Category | Useful for | Selection checks |
|---|---|---|
| Load generator | rate, concurrency, workload mix | open/closed model, pacing, percentiles, generator telemetry, bounded stop |
| Dependency stub/mock | deterministic errors, latency, payloads | protocol fidelity, schedule control, reset, request capture |
| Network fault proxy | delay, reset, refusal in isolated networks | exact target, direction, blast radius, independent removal |
| Container/VM resource control | disposable CPU/memory/IO ceilings | isolation, host impact, cleanup, target observability |
| Application fault hook | precise code-path failure | non-production build, authorization, discoverability, removal |
| Profiler/runtime telemetry | CPU, memory, locks, allocation | overhead, sampling window, privacy, revision compatibility |
| Metrics/tracing/logs | demand, saturation, errors, recovery | clock alignment, cardinality, redaction, retention, gaps |
| Database observability | locks, waits, plans, pools | test credentials, query overhead, tenant/data isolation |

Examples of common ecosystems include k6, JMeter, Locust, Gatling, Vegeta, wrk, autocannon, Toxiproxy, container resource controls, runtime profilers, and OpenTelemetry-compatible telemetry. Mentioning a tool does not authorize installing or running it. Prefer repository-installed tooling and disposable stubs before adding dependencies.

## Selection questions

- Does it model the required rate, concurrency, pacing, payload, and protocol?
- Can it set hard ceilings and stop independently of the target?
- Can configuration be versioned and secrets excluded?
- Can the generator/injector be monitored separately?
- Does it preserve histograms or raw-enough data for tail analysis?
- Can faults be targeted narrowly and removed deterministically?
- Is its overhead known for the measurement window?
- Does the environment already provide it, or would installation require new authority?

## Evidence identity

Record target commit/image/config identity, environment and dataset identity, tool and version, command/config hash, seed, workload/fault model, start/end time, timezone and clock alignment, telemetry queries, sample count, raw artifact locations, sanitization, stop reason, cleanup proof, and operator/approval reference.

Keep planning, execution, and interpretation separate:

- `PLANNED`: scenario defined; no result.
- `APPROVED_NOT_RUN`: execution authorized but absent.
- `EXECUTED_EVIDENCE_INCOMPLETE`: activity occurred; no readiness claim.
- `OBSERVED`: evidence supports the stated observation.
- `CONFIRMED_DEFECT`: reproducible behavior violates an owned requirement.
- `PASS_FOR_TESTED_ENVELOPE`: supplied objective met only for the recorded envelope.

Never promote `PLANNED`, tool output, or a single green aggregate into a readiness result.

## Interpretation

Correlate workload/fault timing with demand, throughput, latency distribution, errors, utilization, saturation, queue/pool state, retries, and durable-state evidence. Disclose sampling loss, generator saturation, missing telemetry, warm-up effects, cache bias, clock error, and environment differences.

## Safety and handoff

Before executable guidance, load `SAFETY_GATES.md` and `TEST_EXECUTION_PROTOCOL.md`. Dagger owns scenario and failure interpretation within supplied requirements. Overseer owns pass/fail gates. Cipher owns security/privacy implications. Clockwork/Chronicler own architecture/persistence conclusions. Ponytail owns implementation. Scribe owns durable documentation.
