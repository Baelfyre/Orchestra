# Fictional Bounded Load and Recovery Review

## Safety gate

- Environment: isolated local release-candidate stack
- Production connectivity: blocked
- Authorization: fictional owner approved planning only
- Data: synthetic tenants and disposable orders
- Ceiling: 20 requests/second, 12 concurrent clients, 10 minutes maximum
- Stop conditions: error rate above 2%, p95 above 800 ms for two windows, queue depth above 100, or generator CPU above 70%
- Mode: `PLANNED`; no traffic generated

## Overseer baseline

- Supplied objective: p95 below 500 ms and error rate below 1% at 10 requests/second for the checkout read path
- Recovery objective: queue returns to baseline within 3 minutes after load removal

## Workload model

- Open arrival model, 80% catalog reads and 20% checkout reads
- Two-minute warm-up, five-minute measurement, three-minute recovery window
- Synthetic key distribution includes hot and cold catalog items
- Planned steps: 2, 5, and 10 requests/second; higher steps require new approval

## Expected safe behavior

- No duplicate checkout effects
- Bounded queue and connection-pool wait
- Explicit rejection rather than indefinite hanging
- No retry amplification
- Queue and pool return to baseline inside the recovery objective

## Evidence required

- Target commit and configuration hash
- Generator CPU, sockets, and dropped-sample count
- Request count, throughput, error classes, latency histogram, p50/p95/p99
- Queue depth/age, pool active/waiting, retries, and durable checkout state
- Stop event, recovery timeline, cleanup proof, and residual-state check

## Current result

No execution occurred. Capacity and recovery remain `NEEDS_EVIDENCE`. The scenario must not be reported as passed.

## Handoff

- Overseer: confirm objective and readiness use
- Clockwork: confirm queue/pool ownership if a defect appears
- Chronicler: confirm transaction evidence for duplicate or partial checkout state
- Ponytail: implement only after an owned defect is confirmed
