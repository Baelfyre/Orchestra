# Governance Review Flow

Every request passes through this flow before execution begins. Review depth scales to project risk and the active operating mode.

## Governance Strictness Derivation Note

Governance strictness is derived from the highest applicable trigger, not from a new input field. `Operating Mode` identifies task intent, while `Release Stage` identifies lifecycle state. The flow below does not change: the derived strictness only explains why a given request stays on a lightweight path or escalates to stricter governance depth.

```text
Governance Strictness Level = max(applicable mode baseline, release trigger, risk trigger, compliance/data trigger, continuity trigger)
```

## Standard User Flow

```
Request
↓
Intent Classification
↓
Mode Selection (Ideation, Prototype, Implementation, Audit, Release)
↓
Need-Based Governance Review (if applicable)
↓
Arbiter Continuity Review (if transition, validation, branch, source-of-truth, or handoff risk exists)
â†“
Conductor Routing or Advisory Response
↓
Validation when files change
↓
User Review
```

## Flow Diagram

```
Request
  │
  ▼
┌───────────────────────┐
│ Intent Classification │  Determine user objective
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│    Mode Selection     │  Select: Ideation, Prototype, Implementation,
└──────────┬────────────┘          Audit, or Release mode
           │
           ▼
┌───────────────────────┐
│ Governance Basis check│  Establish review dimensions if required
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│      Need-Based       │  Ideation/Prototype → ADVISORY_ONLY / NOT_APPLICABLE
│   Governance Review   │  Audit/Release → strict validation
└──────────┬────────────┘  Low-risk → Fast path (NOT_APPLICABLE)
           │
     BLOCKED ──► STOP
     REVISION_REQUIRED ──► RETURN for revision
     ADVISORY_ONLY ──► Conductor Routing / Advisory Response
     NOT_APPLICABLE ──► Conductor Routing
     APPROVED ──► Conductor Routing
           │
           ▼
┌───────────────────────┐
│   Conductor   │  Route request (if approved/applicable)
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│       Execution       │  Specialists perform work
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│      Validation       │  QA check if files changed
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│     Release Gate      │  Final compliance check before release
└───────────────────────┘
```

## Fast Path (LOW Risk)

For trivial or low-risk requests:
- Steward returns `NOT_APPLICABLE` or lightweight `APPROVED`.
- Governor returns `NOT_APPLICABLE` or lightweight `APPROVED`.
- Conductor proceeds immediately.
- Governance adds near-zero token overhead.

## Continuity Path

Arbiter runs only when continuation safety is uncertain:
- interrupted task
- token or context exhaustion risk
- branch switch or divergence
- workspace or IDE transition
- unclear source of truth
- failed or missing validation
- handoff
- merge or pull request preparation

Arbiter returns `READY`, `READY_WITH_MINOR_FIXES`, `HOLD`, or `BLOCKED`. `HOLD` and `BLOCKED` pause continuation until the required evidence, validation, or remediation is complete.

## Standard Path (MEDIUM Risk)

- Steward checks scope, requirements, acceptance criteria.
- Governor checks license compat, basic privacy, attribution.
- Compact output format used.

## Expanded Path (HIGH Risk)

- Steward checks full alignment, stakeholders, traceability, roadmap.
- Governor checks full compliance, ToS/PP, human review flag.
- Expanded output format used when findings exist.

## Release Path

- Release Mode includes final release-gate review before public release, client delivery, production deployment, app store submission, or open-source distribution.
- For app release workflows, The Governor must review the [App Release Compliance Gate](APP_RELEASE_COMPLIANCE_GATE.md).
- Missing required privacy, data inventory, retention, deletion, account deletion documentation when accounts exist, platform disclosures, or IP clearance artifacts must return `REVISION_REQUIRED` or `BLOCKED`, depending on release context and severity.
- Release Mode is task intent. `production` is release-stage state. They are related inputs, but they are not synonyms.

## Re-submission

When `REVISION_REQUIRED`:
1. Address all findings.
2. Fill documentation gaps.
3. Re-submit for review.
4. Review restarts from the authority that issued the revision.

## Missing Context

When project context is incomplete:
```
DECISION: REVISION_REQUIRED
REASON: Project context incomplete.
REQUIRED_ACTIONS: [Provide project type, release target, data collection status]
```
The system does not default to HIGH-risk assumptions for unknown projects.

## Delegated Execution Flow (Phase B Feature Branch, Draft PR #190)

The following flow describes the behavior for delegated autonomous
governance. Phase B instruction-level behavior is implemented on the feature
branch, under correction in draft PR #190, and is not canonical until merged.
Remote and host reliability remain pending until separately authorized.
Phase A contracts are merged; Phase C and Phase D are not started. Phase B has not been merged, released, or deployed.


```
Phase envelope approved by human
  ->  Internal unit execution begins
  ->  Unit work performed within envelope boundaries
  ->  Focused evidence collected (validation commands, scope audit, security check)
  ->  Arbiter transition evaluation
        APPROVED + evidence current + no gate  ->  AUTO_CONTINUE
        Deterministic in-scope defect + budget remains  ->  AUTO_REMEDIATE_AND_REVALIDATE
        Missing or stale evidence  ->  WAIT_FOR_EVIDENCE
        Insufficient host capacity  ->  WAIT_FOR_CAPACITY
        Missing intent, scope change, policy, or contradiction  ->  ESCALATE_HUMAN
        Unsafe or prohibited condition  ->  STOP
  ->  On AUTO_CONTINUE: checkpoint produced, next unit begins
  ->  On WAIT_*: resumable state held, no new approval required
  ->  On ESCALATE_HUMAN: human decision obtained, phase resumes or is revised
  ->  On STOP: phase halts, human review required

All approved units accepted
  ->  Phase validation gate runs
  ->  PHASE_READY_FOR_HUMAN_REVIEW returned
```

Canonical releases continue to use the standard manual flow until Phase B is
merged. The feature branch implements the delegated flow above for maintainer
review. Governance specialist and Arbiter re-entry rules in
`GOVERNANCE_LAYER.md` apply to both flows.

See `docs/governance/DELEGATED_EXECUTION_POLICY.md` for the canonical contract
and `docs/project/DELEGATED_GOVERNANCE_IMPLEMENTATION_PLAN.md` for the
multi-phase implementation roadmap.
