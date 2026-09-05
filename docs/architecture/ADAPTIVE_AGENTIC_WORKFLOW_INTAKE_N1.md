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


## Higher calibration corpus

The N3/N4 calibration corpus now contains 18 RouterService-level scenarios covering:

- single-owner UI review;
- security audit;
- persistence implementation and validation;
- architecture refactor;
- documentation mutation;
- diagram creation;
- business-scope review;
- legal/compliance review;
- ambiguous fallback;
- parallel UI/security analysis;
- protected merge;
- production deployment;
- force-push/history rewrite;
- gated Dagger chaos work;
- single-domain UI implementation;
- persistence/security cross-domain implementation;
- false-positive protection for the generic word `production`;
- cross-domain security/UI review.

The calibration invariant is:

```text
TERMINAL_EXECUTION_ROLE != DISTINCT_DOMAIN_DECISION_AUTHORITY
```

Ponytail, Overseer, and Arbiter can be required in a topology without causing The Tuner or Multi-Agent activation by themselves. The Tuner and Multi-Agent semantics are justified by multiple distinct domain-decision owners, explicit re-entry, or independent subtask evidence.

This prevents a simple single-domain implementation from being over-routed merely because implementation and validation stages exist.


## Negative routing calibration

The positive calibration corpus verifies what Orchestra should select. A separate negative-routing corpus verifies what Orchestra must avoid selecting when dangerous or cross-domain terminology is only mentioned, negated, quoted, hypothetical, or scoped to representation work.

The negative corpus contains 20 RouterService-level scenarios covering:

- explicit negation of deploy and merge actions;
- documentation explaining prohibited force-push and history-rewrite operations;
- hypothetical production deployment questions;
- removing the literal word `deploy` from README text;
- documentation-only use of authorization/security terminology;
- quoted security marketing language;
- database terminology inside documentation-only work;
- documentation of frontend architecture without UI redesign or code mutation;
- quoted chaos-test examples that must not activate Dagger;
- quoted `drop table` text that must not activate persistence/destructive execution;
- release notes that must not become release execution;
- deployment-documentation review without deployment;
- security-incident summarization without a Cipher review;
- authentication terminology in documentation-only typo fixes;
- architecture terminology in changelog-only work;
- generic `production` terminology without production mutation;
- negated test execution;
- permission terminology used only as a documentation label;
- screenshot-caption references to database/UI terminology;
- future deployment planning with execution actions explicitly negated.

### Suppression model

The deterministic intake policy now separates active execution intent from four classes of non-executable mention:

1. **Negated spans** such as `do not deploy`, `without changing the database`, or `never force push`.
2. **Quoted/example spans** where dangerous strings are content to discuss rather than commands to execute.
3. **Hypothetical actions** such as `What would happen if we deploy this to production?`.
4. **Representation-only contexts** such as README, documentation, changelog, summary, caption, sentence, label, or term editing.

Representation-only work suppresses unrelated domain-execution signals and routes to Scribe when appropriate. Audit intent may still be preserved for read-only representation review, while documentation edits retain mutation semantics for the documentation artifact itself.

The policy is machine-configured in `machine/workflows/task-profile-derivation.v1.json`. Suppression behavior is therefore calibratable without changing frozen specialist prompts.

### Negative-routing invariants

```text
MENTION != INTENT
NEGATED_ACTION != AUTHORIZED_ACTION
QUOTED_DANGEROUS_TEXT != PROTECTED_ACTION
HYPOTHETICAL_ACTION != EXECUTION_REQUEST
REPRESENTATION_CONTEXT != REFERENCED_DOMAIN_AUTHORITY
```

A false-negative protected-action detection remains a blocking safety defect. A false-positive protected-action or specialist activation is a routing-calibration defect.


## AWF-N5 semantic robustness

Status: IMPLEMENTATION CANDIDATE

N1 through N4 are canonical at Orchestra merge commit `e0b2c0b9a8d4cc6618267ce0340048793613abc5`. N5 extends deterministic intake calibration from exact-token positive/negative cases into sentence-structure and instruction-order robustness.

### Semantic contrast corpus

The N5 corpus contains 30 RouterService-level cases covering:

- paraphrased negation such as `refrain from`, `hold off on`, `avoid`, and `no need to`;
- scoped contrast around `but` and semicolon boundaries;
- later correction of earlier deploy/test instructions;
- hypothetical clauses followed by later active commands;
- quoted text followed by active execution;
- mixed documentation plus validation, implementation, security, and deployment work;
- conditional protected actions;
- same-token different-intent contrast pairs.

The corpus aggregates all mismatches before failing so one evaluation run exposes the full semantic calibration map.

### N5 diagnostic finding

The first diagnostic run found four concrete classes:

1. negation scope leaking across contrast clauses;
2. hypothetical state leaking into later active sentences;
3. representation-only suppression applying to the whole prompt instead of only the representation clause;
4. repeated action directives lacking reliable later-instruction precedence.

The runtime now evaluates semantic suppression per clause and uses later directive state for repeated operation signals.

### N5 invariants

```text
NEGATION_SCOPE_IS_LOCAL
HYPOTHETICAL_SCOPE_IS_LOCAL
REPRESENTATION_SCOPE_IS_LOCAL
MIXED_REPRESENTATION_AND_EXECUTION_MUST_PRESERVE_EXECUTION_INTENT
LATER_SAME_SIGNAL_DIRECTIVE_SUPERSEDES_EARLIER_SAME_SIGNAL_DIRECTIVE
CONDITIONAL_PROTECTED_ACTION_REMAINS_PROTECTED
```

N5 does not expand specialist authority or OEE concurrency. Evidence-gated A5, learned ranking, and concurrency changes remain deferred to N6.
