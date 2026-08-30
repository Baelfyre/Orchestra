# Unified Testing Mechanism — T0–T9 Experimental Contract

**Status:** EXPERIMENT_ONLY / implementation candidate  
**Promotion:** PENDING  
**Default mode:** NON_RELEASE  
**Authority:** evidence only; this mechanism grants no merge, release, deployment, policy-activation, destructive, or other protected-action authority.

## Purpose

Orchestra already has strong validation capabilities, but they are distributed across specialists, CI workflows, runtime evidence, security review, UI validation, resilience testing, and merge-readiness contracts. The Unified Testing Mechanism (UTM) does not replace those capabilities. It provides a small revision-bound orchestration contract that answers two questions:

1. Which testing stages apply to this change?
2. Is the required evidence for the exact revision complete, pending, or failed?

```text
UTM != TEST_FRAMEWORK
UTM != SPECIALIST_REPLACEMENT
UTM != RELEASE_AUTHORITY
UTM != MERGE_AUTHORITY
UTM != DEPLOYMENT_AUTHORITY
READINESS_EVIDENCE_COMPLETE != RELEASE_AUTHORIZED
```

## Baseline audit

| Stage | Existing Orchestra capability | Primary ownership | Gap UTM addresses |
| --- | --- | --- | --- |
| T0 Applicability & Evidence Plan | Conductor routes multi-domain work; Overseer defines QA scope and evidence | Conductor + Overseer | No common T0–T9 applicability record |
| T1 Smoke / Sanity | Overseer smoke scope; behavior/runtime CI | Overseer | Evidence is not aggregated under one subject revision |
| T2 Functional | Overseer acceptance/pass-fail criteria; runtime tests | Overseer | No shared stage-level applicability/result contract |
| T3 Integration / Contract | Overseer cross-layer/contract evidence; behavior tests | Overseer | No common aggregation semantics |
| T4 UI / UX / Accessibility / User Validation | Cloak owns UI/UX/accessibility; Overseer owns UI readiness evidence | Cloak + Overseer | Rendered/static evidence can exist outside a unified readiness packet |
| T5 Load / Capacity / Performance | Overseer owns QA criteria; Dagger has safe load/stress scenario guidance | Overseer + Dagger | No common applicability/result record |
| T6 Stress / Resilience / Recovery | Dagger owns controlled resilience/failure scenarios; Overseer owns readiness | Dagger + Overseer | No common applicability/result record |
| T7 Security / Privacy / Abuse Resistance | Cipher owns defensive security/privacy review; Overseer owns readiness | Cipher + Overseer | Security evidence is not aggregated with other stage evidence |
| T8 Regression / Compatibility / Portability | Overseer regression scope; Windows/macOS/Ubuntu and Required Analysis CI | Overseer | Cross-platform evidence is separate from other risk stages |
| T9 Readiness Aggregation / Independent Verification | Overseer owns readiness; merge readiness has a separate exact-head protocol | Overseer | Existing merge protocol is intentionally merge-specific, not a general test lifecycle |

### Audit conclusion

Existing mechanisms **partially solve** every domain-specific stage. The confirmed missing capability is a common applicability/evidence envelope and deterministic aggregate verdict. Therefore UTM is deliberately implemented as a thin coordination layer rather than a second QA engine.

## Canonical stages

```text
T0 Applicability & Evidence Plan
T1 Smoke / Sanity
T2 Functional
T3 Integration / Contract
T4 UI / UX / Accessibility / User Validation
T5 Load / Capacity / Performance
T6 Stress / Resilience / Recovery
T7 Security / Privacy / Abuse Resistance
T8 Regression / Compatibility / Portability
T9 Readiness Aggregation / Independent Verification
```

T0 and T9 are always required. T1–T8 are selectively applicable according to the risk surface. Every `NOT_APPLICABLE` stage requires an explicit rationale and may not masquerade as completed evidence.

## Machine contract

Schema:

`machine/schemas/unified-testing-packet.v1.schema.json`

Runtime aggregator:

`orchestra_runtime/unified_testing.py`

Feature decision:

`machine/features/unified-testing-mechanism.v1.json`

Each packet binds evidence to one exact repository revision. Terminal PASS/FAIL evidence must carry evidence references. Evidence for another revision is stale and fails closed.

Aggregate dispositions:

```text
BLOCKED
WAIT_FOR_EVIDENCE
READINESS_EVIDENCE_COMPLETE
```

`READINESS_EVIDENCE_COMPLETE` means only that every required T0–T9 stage has terminal PASS evidence for the packet revision. It does not authorize a transition.

## Release intent and human sign-off

The default `release_intent` is conceptually `NON_RELEASE`. A packet may explicitly describe a `RELEASE_CANDIDATE`, but this only changes the declared purpose of evidence collection.

Human sign-off is recorded separately as:

```text
NOT_REQUESTED
PENDING
APPROVED
REJECTED
```

Even `RELEASE_CANDIDATE + APPROVED + READINESS_EVIDENCE_COMPLETE` does not grant release authority. The ordinary Orchestra protected-action authority chain still applies.

## Specialist boundaries

- **Conductor**: orchestrates T0 routing and minimum specialist sequence; does not execute domain tests.
- **Overseer**: owns QA strategy, evidence requirements, pass/fail criteria, and T9 readiness review.
- **Cloak**: owns T4 UI/UX/accessibility design evidence; rendered readiness remains Overseer evidence.
- **Dagger**: contributes authorized bounded load/stress/resilience scenarios for T5/T6; never receives execution authority from UTM.
- **Cipher**: contributes defensive security/privacy/abuse-resistance evidence for T7.
- **Ponytail/other implementation owners**: implement tests or fixes when separately routed; UTM does not transfer implementation ownership.

## Fail-closed rules

- Missing required stage evidence -> `WAIT_FOR_EVIDENCE`.
- Pending required evidence -> `WAIT_FOR_EVIDENCE`.
- Any required FAIL -> `BLOCKED`.
- Evidence revision mismatch -> reject packet as stale.
- Duplicate/missing T0–T9 stage declaration -> reject packet.
- T0 or T9 marked not applicable -> reject packet.
- Evidence supplied for a stage declared not applicable -> reject packet.
- Invalid/noncanonical specialist ownership mapping -> reject packet.

## Efficacy requirement before promotion

Permanent adoption is not assumed. The approved pilot must compare the existing baseline workflow with UTM on representative bounded cases and measure at least:

- evidence completeness;
- failure/risk detection;
- false positives and false negatives;
- operator effort/time;
- token or other measurable operational cost when available;
- cross-host consistency where host execution is actually authorized;
- complexity and maintenance burden.

Promotion remains `PENDING` until this evidence supports one of the Feature Admission promotion dispositions. A no-benefit or excessive-complexity result is valid and must be retained.

## Rollback / simplification

During the pilot UTM remains experimental and non-default. If efficacy is weak, the candidate may be simplified, deferred, or removed without changing existing specialist or CI mechanisms. Existing validation contracts remain authoritative for their own domains throughout the experiment.
