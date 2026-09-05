# Adaptive Agentic Workflow Intake N1-N3

Status: IMPLEMENTATION CANDIDATE

Canonical AWF baseline:
- Orchestra main: `7f1e1962817b1b363fbcb1629902d69d50f1daa6`
- AWF source PR: #800
- Qualified source head: `7040618b4faf6998fd88d6bc984677fc42764da4`
- Padayon architecture baseline: `b4b59d04ea37c4f23bb6a54e7d217bd3037eb6ab`

## Objective

Move AWF from structured TaskProfile execution to ordinary-prompt adaptive orchestration without turning natural-language classification into authority.

The invariant remains:

```text
WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION
```

## N1: Automatic TaskProfile derivation

When Conductor receives an ordinary request and no explicit `agentic_task_profile` is supplied, RouterService derives a TaskProfile from:

- the user request text;
- existing canonical `risk_mode` constraints and namespaced `agentic_execution_mode` / `agentic_risk_level` constraints;
- explicit host-provided authority-domain hints;
- explicit protected-action authorization state;
- current source identity;
- re-entry and critic metadata when supplied.

The deterministic machine policy is `machine/workflows/task-profile-derivation.v1.json`.

The policy is deliberately calibratable. It stores domain and operation signals outside the frozen Conductor skill so routing changes do not increase default prompt load or alter specialist source authority.

### Safety rules

- Prompt keywords may identify potential work domains, but never grant authority.
- Host `execution_mode` values used by execution engines, such as `HOST_NATIVE`, are not interpreted as AWF risk modes. Canonical `risk_mode` and namespaced AWF mode/risk hints may escalate the derived result but cannot downgrade it.
- Protected-action authorization is never inferred from text.
- Unknown domains fail to `ROUTING` with Conductor as owner instead of guessing.
- Explicit valid structured TaskProfiles remain supported.
- Automatic derivation can be disabled with exact boolean `agentic_workflow_auto = false`.

## N2: Selection trace

Every AWF plan now emits `orchestra.agentic-selection-trace.v1`.

The trace contains:

- deterministic matched signals;
- derived TaskProfile reason codes;
- selected specialists;
- selected patterns;
- rejected patterns and deterministic rejection reasons;
- human-gate state and underlying escalation reasons;
- the authority invariant.

It does not expose private model reasoning.

## N3: Controlled scenarios

### N3-T1: Single-owner UI review

Prompt:

```text
Review this responsive checkout screen for accessibility and layout issues.
```

Expected:

- authority domain: UI_UX
- primary owner: Cloak
- read-only AUDIT mode
- one specialist
- no Multi-Agent topology
- no human gate

### N3-T2: Multi-domain implementation

Prompt:

```text
Implement a responsive checkout flow with secure payment authorization and validate the change.
```

Expected:

- UI_UX + SECURITY + IMPLEMENTATION + VALIDATION
- Cloak and Cipher domain ownership preserved
- Ponytail implementation after domain owners
- Overseer validation
- The Tuner coordinates cross-domain dependencies
- Multi-Agent semantics allowed
- active OEE parallel ceiling remains one
- no topology-only human gate

### N3-T3: Protected production action

Prompt:

```text
Deploy the checkout change to production.
```

Expected:

- transition ownership resolves to Arbiter
- destructive/critical classification
- protected action required
- `deploy` plus production context is classified as destructive without making the generic word `production` a universal destructive trigger
- authorization remains false unless explicitly supplied by trusted context
- human gate required

## Calibration boundary

N1-N3 are deterministic and evidence-generating.

N4 may adjust signal rules only after controlled or real workflow evidence demonstrates over-routing, under-routing, unnecessary specialist activation, false protected-action escalation, or missed authority domains.

N5 may consider A5 ranking signals, learned recommendations, or concurrency changes only after separate empirical benefit evidence. No such promotion is part of N1-N3.
