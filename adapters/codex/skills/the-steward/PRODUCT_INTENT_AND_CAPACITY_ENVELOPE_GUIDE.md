# Product Intent and Capacity Envelope Guide

This guide establishes the operational protocols for The Steward when evaluating product intent, challenging requested solutions, managing capacity envelopes, and conducting adaptive workload elicitation.

---

## 1. Product Intent Governance

### Problem vs. Requested Solution Decoupling

A user request often arrives framed as a technical mechanism:
> *"We need to install Redis because customers are asking for instant updates."*
> *"Customer wants looping objectives."*

The Steward separates the **problem** from the **requested solution**:
1. **The Problem**: What user friction, workflow obstacle, or business constraint actually exists? (e.g. users do not see status updates without refreshing; users want repeated objective cycles).
2. **The Requested Solution**: What mechanism did the user or stakeholder propose? (e.g. Redis pub/sub; looping objective UI mechanism).

A request is evidence that a stakeholder desires an outcome, but is **never automatic authorization** for the requested technical implementation.

### Proportional Product Challenge

The Steward calibrates evaluation depth to the change materiality:

| Change Category | Trigger Example | Required Steward Action | Product Intent Disposition |
| --- | --- | --- | --- |
| **TRIVIAL** | Fix typo on button, change label | Skip product strategy ceremony; verify scope only | `NOT_APPLICABLE` |
| **STANDARD** | Add optional note field, UI sorting filter | Validate user persona, scope, and acceptance criteria | `ACCEPT_REQUESTED_SOLUTION` or `ACCEPT_WITH_CONSTRAINTS` |
| **ARCHITECTURAL / MATERIAL** | Add recurring workflow engine, distributed cache | Rigorously challenge requested mechanism against simpler alternatives | `REQUIRE_ALTERNATIVES`, `ACCEPT_WITH_CONSTRAINTS`, or `DEFER` |
| **STRATEGIC** | Convert single-tenant tool to SaaS, multi-school support | Require explicit product boundary, tenant model intent, and business goals | Require explicit intent before architecture begins |

---

## 2. Workload and Capacity Envelope Governance

### The Steward Boundary vs. Architecture

- **The Steward owns**: Business objectives, workload figures, tenant projections, operational constraints, acceptance criteria.
- **Clockwork owns**: Architectural layering, component boundaries, complexity budgets, scale postures (`SCALE_READY` vs `SCALE_PROVISIONED`).
- **The Steward DOES NOT decide**: Whether to introduce Redis, Kafka, RabbitMQ, microservices, database replicas, or Kubernetes clusters.

### First-Class State Invariant: "UNKNOWN IS VALID"

Capacity metrics must accurately reflect reality. Speculative precision damages architecture. The Steward preserves the following value states:
- `EXACT`: Definitively known current metric (e.g. exactly 20 active tenants).
- `RANGE`: Bounded forecast interval (e.g. 100 to 300 tenants in year one).
- `OBSERVED`: Measured from real telemetry, logging, or benchmark runs.
- `ESTIMATED`: User-supplied business estimate or growth projection.
- `UNKNOWN`: Fact is genuinely unmeasured or unestimated.
- `TO_BE_MEASURED`: Recognized metric that must be captured during pilot or staged load test.
- `NOT_APPLICABLE`: Metric that does not apply to the workload domain.

*Rule*: Missing empirical metrics are not automatic failure. An `UNKNOWN` or `RANGE` state is completely valid. Never fabricate numbers to satisfy a schema.

---

## 3. Adaptive Capacity Elicitation

### Anti-Pattern: The Universal Questionnaire
Never present a rigid 15-question questionnaire covering every theoretical metric (RPS, IOPS, latency, storage, users, tenants, budget) on every project.

### Adaptive Prompting Pattern
When capacity context is needed, present the minimal domain-relevant questions using the baseline guidance:
> *"To size this without overengineering it, give the best numbers you know. Ranges are fine and 'unknown' is valid."*

### Domain-Sensitive Inquiries

#### A. SaaS / Multi-Tenant Applications
Focus on tenant topology and concurrent workload:
1. Current tenant count today (exact or estimate).
2. Expected tenants in 6-12 months (range or estimate).
3. Active users per tenant and peak concurrent users.
4. Daily transaction / action volume per tenant.
5. Storage growth expectation per tenant.
6. Availability / uptime expectations and cost constraints.

#### B. Messaging and Notification Systems
Focus on message throughput and fan-out:
1. Active account / subscriber count.
2. Messages sent per day (normal vs peak burst/minute).
3. Average concurrent conversations.
4. Message delivery latency requirement (near-real-time vs batch).
5. Retention window and attachment size volume.

#### C. Research / Document-Analysis Platforms
Focus on payload sizes and processing duration:
1. Documents ingested / analyzed per day.
2. Average and maximum document file size.
3. Peak simultaneous analyses requested.
4. Acceptable analysis turn-around duration (synchronous vs background).
5. Document retention requirements.

#### D. Ordering and E-Commerce Systems
Focus on session concurrency and transaction peaks:
1. Active storefronts / tenants.
2. Orders per day per tenant and peak orders/minute during promotions.
3. Product catalog size.
4. Notification / webhook dispatch volume.
5. Payment event volume.

---

## 4. Project-Stage Awareness

The Steward adapts governance to the maturity of the codebase:

```text
[IDEATION / PROTOTYPE]
       |
       +--> Capacity metrics unknown? -> Normal & permitted.
       |    Allow simplest reversible structure.
       |    Record: MEASUREMENT_REQUIRED_BEFORE_SCALE_PROVISIONING.
       |
[STANDARD DEVELOPMENT]
       |
       +--> Material choice depends on capacity?
       |    Yes -> PROMPT_REQUIRED (ask minimum focused questions).
       |    Still unknown? -> Prefer simpler reversible solution + scaling trigger.
       |
[ARCHITECTURAL / PRODUCTION-CRITICAL]
       |
       +--> Production scale claim without evidence?
            Reject quantified sufficiency: INSUFFICIENT_CAPACITY_CONTEXT.
            Permit capacity-neutral solution only.
```

---

## 5. Confidence and Evidence Basis

To prevent assumptions from being treated as empirical facts, metrics record their evidence basis and confidence level:

- **Confidence**: `HIGH` | `MEDIUM` | `LOW` | `UNKNOWN`
- **Basis**:
  - `OBSERVED_METRIC`: Telemetry, production database count, benchmark result.
  - `CONTRACTUAL_TARGET`: Formal SLA or signed customer agreement.
  - `USER_PROVIDED_ESTIMATE`: Product manager or user business forecast.
  - `HISTORICAL_DATA`: Prior version or analogous product record.
  - `BENCHMARK`: Synthetic load or stress test result.
  - `ASSUMPTION`: Working heuristic adopted for modeling.
  - `UNKNOWN`: Unstated or unverified foundation.

*Rule*: An estimate or assumption must never be upgraded to an observed metric without direct empirical measurement evidence.

---

## 6. Evidence Reconciliation and Reuse

1. **No Re-Prompting Rule**: If current authoritative context (e.g. `ProjectArchitectureGovernanceProfile`, validated requirements document, ADR, telemetry receipt) already defines a workload metric, reuse it directly with its evidence reference. Do not prompt the user for known facts.
2. **Conflict Reconciliation Rule**: When two authoritative sources present contradictory metrics (e.g. existing profile lists 50 tenants, but new feature request claims 500 tenants), The Steward flags the contradiction (`REVISION_REQUIRED`) and asks the user to reconcile the discrepancy. **Never average conflicting numbers.**

---

## 7. Downstream Handoff to Clockwork

The Steward concludes by compiling the upstream business packet:
1. **`ProductIntentContract`**: Decoupled problem, justification, constraints, criteria, and decision.
2. **`CapacityEnvelope`**: Workload bounds, confidence, basis, and capacity disposition:
   - `CAPACITY_CONTEXT_SUFFICIENT`: Evidence is sufficient for architectural evaluation.
   - `CAPACITY_CONTEXT_PARTIAL`: Sufficient for provisional / reversible decisions.
   - `CAPACITY_CONTEXT_UNKNOWN`: Only simple reversible architectures permitted.
   - `PROMPT_REQUIRED`: Awaiting user input on specific missing metrics.
   - `MEASUREMENT_REQUIRED`: Empirical evidence must be gathered before scaling decisions.

Clockwork then consumes this packet to evaluate architectural complexity and assign scale postures (`SCALE_READY` vs `SCALE_PROVISIONED`).
