# Delegated Execution Policy

This document is the single canonical source of truth for Orchestra's delegated
phase governance contracts. It defines the execution envelope, transition
dispositions, evidence standards, automatic remediation, checkpointing, capacity
waiting, external-action authority, envelope invalidation, and legacy fallback.

Do not duplicate the full contract defined here in role skills, routing files, or
governance layer documents. Phase B will add concise role-specific behavior that
references this canonical policy.

Load this document only when a delegated phase envelope must be issued,
evaluated, or enforced.

## Phase A Status

Phase A defines the canonical contracts required for delegated autonomous
governance. It does not activate instruction-level autonomous behavior across
skills and adapters. Phase B instruction-level behavior and Phase D optional
runtime enforcement are not yet implemented.

Do not claim that continuous automatic progression is already active.

---

## 1. Terminology

**Delegated execution** - Execution that proceeds automatically inside authority
previously granted by a human, without requiring repeated approval for each
internal unit.

**Delegated phase** - A bounded sequence of approved internal units, governed by
one execution envelope, that may proceed automatically when all boundary and
evidence conditions are satisfied.

**Execution envelope** - The complete, human-authorized specification of what
work is permitted in a delegated phase. The envelope defines allowed paths,
behaviors, roles, validation gates, escalation triggers, and completion
conditions. The envelope is reduction-only and cannot grant authority beyond
existing repository policy.

**Internal unit** - A discrete, bounded work item within an approved delegated
phase. Each unit has defined objectives, paths, outputs, validation, and
completion conditions.

**Approved unit plan** - The ordered list, dependency graph, or derivation
constraints that define which internal units are authorized and in what
sequence.

**Evidence packet** - A compact, structured record produced after each internal
unit. It documents the repository state, changed paths, implementation summary,
validation results, scope audit, and security checks required to authorize a
transition.

**Transition decision record** - A structured record that captures the governance
decision, continuity result, transition disposition, reason, evidence references,
and next eligible unit for each unit boundary.

**Checkpoint** - A compact, durable record of the last verified state after an
accepted unit. Used to resume a delegated phase after a capacity wait or
interruption without repeating completed work.

**Automatic remediation** - Bounded correction of a deterministic in-scope defect
that does not require a new intent, architecture, policy, legal, privacy,
security, licensing, IP, or compliance decision, and remains inside the envelope's
allowed paths and remediation limits.

**Standing external-action authority** - Explicit, action-specific, phase-bounded
authorization for a particular external operation. Default-deny. Must be granted
explicitly and is listed in the envelope. Not implied by governance approval.

**Capacity wait** - A resumable lifecycle state in which the current phase pauses
because the executing host cannot safely complete the next unit and its focused
validation. Not a new approval request.

**Envelope invalidation** - A condition that voids the envelope's authorization
and requires a new human decision before work may continue.

**Human escalation** - Routing of a decision to a human because it involves
missing intent, scope expansion, policy choice, authority ambiguity, legal or
compliance uncertainty, or a contradiction that the executing system cannot
resolve within the envelope.

**Hard stop** - Immediate termination of delegated execution because an unsafe,
prohibited, destructive, or protected condition was detected. Cannot be
auto-resolved.

---

## 2. Authority Principles

The following principles are invariant. They cannot be overridden by an
envelope, prompt, adapter metadata, or validation result.

- Authority creation remains human-controlled.
- Execution may progress automatically only inside previously delegated authority.
- Governance approval is not runtime authority.
- Validation is evidence of conformance, not authority expansion.
- Prompt text and adapter metadata cannot create or widen an envelope.
- A valid envelope does not automatically authorize external actions. Each
  external action requires an explicit standing authority flag set to `true`.
- Unknown, malformed, or unsupported transition dispositions must fail closed.
  They must never default to automatic continuation.

---

## 3. DelegatedExecutionEnvelope Contract

A `DelegatedExecutionEnvelope` is the human-authorized specification for a
delegated phase. It must contain at least the following fields.

```
schema_version              string, e.g. "phase-a-v1"
envelope_id                 unique identifier for this envelope
envelope_hash               immutable identity token or rule; changes invalidate
issued_by                   identity of the authorizing human or human-controlled process
issued_at                   ISO-8601 timestamp
expires_at                  ISO-8601 expiry timestamp, or explicit non-expiring boundary
project_id                  project identifier
phase_id                    phase identifier, e.g. "phase-a"
phase_objective             human-readable statement of the phase objective
repository_identity         canonical remote URL and repository name
canonical_branch            the authorized working branch
approved_base_sha           the exact commit SHA the human reviewed and approved
lineage_rule                how authorized descendants are identified
approved_unit_plan          reference or inline list of approved internal units
allowed_paths               list of authorized file paths or globs
allowed_file_operations     e.g. [create, modify]; delete requires explicit authorization
allowed_behaviors           list of permitted specialist actions
allowed_roles               list of permitted specialist roles or capability boundaries
maximum_delegation_depth    maximum nesting depth for sub-envelopes (default 0)
protected_repositories      repositories that must not be modified
prohibited_paths            file paths or globs that must not be touched
prohibited_actions          actions that are explicitly forbidden in this phase
required_focused_validation validation that must pass before each unit transition
required_phase_validation   validation that must pass before phase completion
automatic_remediation       inline AutomaticRemediationPolicy
automatic_progression       inline AutomaticProgressionPolicy
capacity_policy             inline CapacityPolicy
evidence_freshness_policy   inline EvidenceFreshnessPolicy
checkpoint_policy           inline CheckpointPolicy
external_action_authority   inline ExternalActionAuthorityPolicy
human_escalation_triggers   list of conditions that require human escalation
envelope_invalidation_triggers list of conditions that void this envelope
audit_requirements          evidence retention and audit-trail requirements
completion_conditions       list of conditions that mark the phase complete
```

The envelope is **reduction-only**. It cannot grant authority beyond the
trusted runtime authority granted by the human who issued it, nor beyond
existing repository policy.

---

## 4. ApprovedUnitPlan Contract

The envelope must contain or reference one of the following:

1. An explicit ordered unit list.
2. An approved dependency graph.
3. Strict derivation constraints that cannot create materially new objectives.

Each internal unit must include:

```
unit_id                     unique identifier within the phase
objective                   human-readable statement of unit intent
dependencies                list of unit_ids that must be accepted before this unit
allowed_paths               paths this unit is permitted to touch
expected_outputs            artifacts, files, or changes expected on completion
required_focused_validation validation commands required to close this unit
completion_conditions       conditions that mark this unit accepted
next_eligible_units         unit_ids that may begin after this unit is accepted
```

Conductor may sequence approved units. Conductor must not invent new product,
architecture, policy, or scope objectives not already present in the approved
unit plan.

---

## 5. ExecutionEvidencePacket Contract

A compact, structured evidence packet must be produced for every internal unit.
Evidence that does not correspond to the current authorized state is stale and
must not authorize a transition.

```
schema_version              string, e.g. "phase-a-v1"
evidence_id                 unique identifier for this packet
envelope_id                 identifier of the governing envelope
phase_id                    phase identifier
unit_id                     unit identifier
repository_identity         canonical remote URL and repository name
branch                      branch at evidence collection time
approved_base_sha           the envelope's approved base SHA
current_commit_sha          the commit SHA at evidence collection, or "uncommitted"
working_tree_fingerprint    deterministic fingerprint of the working tree when uncommitted
changed_paths               list of paths changed since approved_base_sha
implementation_summary      brief description of work performed
validation_commands         exact commands run
validation_results          structured pass/fail results for each command
skipped_checks              checks omitted with justification
known_limitations           issues that persist after this unit
scope_audit_result          PASS or FAIL with details
protected_repository_result PASS or FAIL with details
security_and_secret_result  PASS or FAIL with details
design_contradiction_state  NONE or PENDING with description
evidence_producer           identity of the system that produced this packet
evidence_timestamp          ISO-8601 timestamp of evidence collection
freshness_reference         envelope_id, branch, and commit or fingerprint this evidence covers
```

A unit must not receive `AUTO_CONTINUE` based on evidence from:

- an earlier commit than the current authorized state;
- a different working-tree fingerprint than the current state;
- a different branch;
- a different envelope.

---

## 6. TransitionDecisionRecord Contract

A transition decision record must be produced at each unit boundary.

```
schema_version              string, e.g. "phase-a-v1"
transition_id               unique identifier for this decision
envelope_id                 governing envelope identifier
phase_id                    phase identifier
unit_id                     unit identifier
governance_decision         one of: APPROVED, ADVISORY_ONLY, REVISION_REQUIRED,
                            BLOCKED, NOT_APPLICABLE
continuity_result           one of: READY, READY_WITH_MINOR_FIXES, HOLD, BLOCKED
transition_disposition      one of: AUTO_CONTINUE, AUTO_REMEDIATE_AND_REVALIDATE,
                            WAIT_FOR_EVIDENCE, WAIT_FOR_CAPACITY,
                            ESCALATE_HUMAN, STOP
reason_code                 brief code describing the disposition reason
evidence_references         list of evidence_ids supporting this decision
remediation_authority       specialist role authorized for remediation, if applicable
remediation_attempt_count   number of remediation attempts consumed for this unit
next_eligible_unit          unit_id to begin on AUTO_CONTINUE, or null
resume_requirements         what must be satisfied before resuming on a wait state
decision_producer           identity of the system that produced this record
decision_timestamp          ISO-8601 timestamp
```

### 6.1 Preserved Governance Decisions

The following governance decision values are canonical and their meanings are
unchanged from `GOVERNANCE_DECISION_PROTOCOL.md`. They must not be redefined
here.

| Decision | Meaning |
|---|---|
| `APPROVED` | Required governance review passed; work may proceed to the next governed stage subject to any stated constraints. |
| `ADVISORY_ONLY` | Non-blocking guidance was provided; exploration may continue without satisfying required actions first. |
| `REVISION_REQUIRED` | Identified changes or missing evidence must be addressed before the governed transition may proceed. |
| `BLOCKED` | Work cannot proceed through the governed transition until the blocking condition is resolved and reviewed again. |
| `NOT_APPLICABLE` | This governance review does not apply to the request and creates no additional gate. |

### 6.2 Transition Dispositions

The following transition dispositions are **additive** to the existing governance
decision vocabulary. They govern what the workflow may do next under the active
envelope, separately from whether the work is acceptable under governance review.

| Disposition | Meaning |
|---|---|
| `AUTO_CONTINUE` | The unit is accepted. The next approved internal unit may begin automatically. |
| `AUTO_REMEDIATE_AND_REVALIDATE` | A deterministic in-scope defect was detected. The authorized specialist may correct it within the envelope and rerun focused validation. |
| `WAIT_FOR_EVIDENCE` | Required evidence is missing, stale, incomplete, or mismatched. Execution pauses until current evidence is produced. Not a new approval request. |
| `WAIT_FOR_CAPACITY` | The executing host cannot safely complete the next unit and its focused validation. A resumable checkpoint must be produced. Not a new approval request. |
| `ESCALATE_HUMAN` | A decision requires human intent, scope, architecture, policy, legal, privacy, security, licensing, compliance, or external-action authorization that the executing system cannot resolve within the envelope. |
| `STOP` | An unsafe, prohibited, destructive, protected, secret-exposing, or authority-invalid condition was detected. Execution must halt immediately. |

### 6.3 Decision Versus Disposition Separation

```
Governance decision:
  Is the work acceptable under the applicable governance review?

Transition disposition:
  What may the workflow do next under the active envelope?
```

These are separate evaluations. A governance decision of `APPROVED` does not
automatically produce `AUTO_CONTINUE`. The transition evaluation must also
confirm that evidence is current, boundary checks pass, and no higher-priority
stop or escalation condition is present.

---

## 7. Transition Precedence

Transition evaluation must apply the following rules in strict priority order.
A lower-priority disposition cannot override a higher-priority one.

1. **STOP** - unsafe, prohibited, destructive, protected-repository, secret-exposing,
   or authority-invalid conditions.
2. **ESCALATE_HUMAN** - missing intent, contradiction, scope expansion, policy
   choice, unresolved legal, privacy, security, licensing, or compliance
   uncertainty, or unauthorized external action required.
3. **WAIT_FOR_CAPACITY** - insufficient execution capacity with a valid checkpoint
   path.
4. **WAIT_FOR_EVIDENCE** - missing, stale, incomplete, or mismatched evidence
   where current evidence can be produced within the envelope.
5. **AUTO_REMEDIATE_AND_REVALIDATE** - deterministic in-scope defect with valid
   remediation authority and remaining remediation attempts.
6. **AUTO_CONTINUE** - complete valid unit with current evidence and no unresolved
   gate.

No lower-priority transition may override a higher-priority stop or escalation
condition.

---

## 8. Governance-to-Disposition Compatibility Map

The following table documents the typical mapping from governance and continuity
results to required transition evaluation. Exact disposition depends on full
evaluation of all precedence rules, not only the governance decision.

| Governance or continuity result | Required transition evaluation |
|---|---|
| `APPROVED` inside a valid envelope, evidence current, all boundary checks pass | `AUTO_CONTINUE` |
| `NOT_APPLICABLE` with no unresolved gate | `AUTO_CONTINUE` |
| `ADVISORY_ONLY` that does not alter intent | `AUTO_CONTINUE` |
| `REVISION_REQUIRED` for a deterministic in-scope correction with authority and budget | `AUTO_REMEDIATE_AND_REVALIDATE` |
| `REVISION_REQUIRED` for missing intent, scope change, architecture, or policy choice | `ESCALATE_HUMAN` |
| Arbiter `READY` | `AUTO_CONTINUE` |
| Arbiter `READY_WITH_MINOR_FIXES`, correction authority exists and budget remains | `AUTO_REMEDIATE_AND_REVALIDATE` |
| Arbiter `HOLD` for producible evidence | `WAIT_FOR_EVIDENCE` |
| Insufficient trusted host capacity | `WAIT_FOR_CAPACITY` |
| Governance `BLOCKED` | `STOP` unless a subsequent human-authorized phase resolves the block |
| `human_review_required: true` | `ESCALATE_HUMAN` |
| Unknown, malformed, missing, or unsupported disposition | Manual fail-closed pause and `ESCALATE_HUMAN`; never automatic continuation |

---

## 9. AutomaticRemediationPolicy

Automatic remediation is permitted only when all of the following conditions are
satisfied:

- The intended behavior is already defined in the envelope or an approved
  canonical document.
- The defect is reproducible or supported by current evidence.
- The correction remains inside the envelope's allowed paths and behaviors.
- The correction does not alter approved intent.
- The required specialist has remediation authority.
- No new architecture, policy, legal, privacy, security, retention, licensing,
  IP, or compliance decision is required.
- The remediation limit for this unit has not been reached.

### Default Limits

```
maximum_remediation_attempts_per_unit:   3
maximum_identical_failure_repetitions:   2
maximum_scope_growth:                    0
```

### Remediation Escalation

Stop automatic remediation and produce `ESCALATE_HUMAN` when any of the
following occurs:

- The same failure repeats beyond the identical-failure limit.
- Successive corrections do not produce measurable progress.
- A correction causes a material unrelated regression.
- The correction requires a file or behavior outside the envelope.
- Requirements and validation expectations conflict.
- Architecture or policy must change.
- The remediation budget is exhausted.

Automatic remediation must not widen scope, weaken a validator, weaken a safety
boundary, or override a governance decision.

---

## 10. Focused and Phase Validation

### 10.1 Internal Unit Gate (Focused Validation)

The following checks must pass before a unit may receive `AUTO_CONTINUE`:

```
focused syntax or type validation
focused lint
relevant unit, contract, governance, security, persistence, or behavior tests
unit diff check (git diff --check)
unit scope check (only allowed paths touched)
current evidence packet produced
```

Passing focused validation permits only the next approved internal unit. It does
**not** authorize commit, push, merge, release, deployment, production, or
infrastructure actions.

### 10.2 Phase Gate (Phase Validation)

The following checks must pass before phase completion may be declared:

```
complete required behavior validation
strict governance validation
runtime regression validation when required by repository policy
adapter parity validation when adapter files are in scope
prompt-load validation
security and secret checks
exact-scope audit (no unauthorized files changed)
skipped-test review
final diff check
phase evidence package produced
```

---

## 11. Baseline Lineage

The following lineage identities are distinct:

```
approved_base_sha           the commit SHA the human reviewed and approved
current_execution_sha       the commit SHA at the current execution point,
                            or "uncommitted" for working-tree changes
remote_comparison_sha       the current remote main SHA for drift detection
working_tree_fingerprint    deterministic fingerprint of uncommitted changes
```

The envelope may remain valid when current work is an authorized descendant of
the approved baseline (committed) or an authorized uncommitted continuation
(working-tree).

### Envelope Invalidation Triggers

The envelope must be invalidated and a new human decision obtained when:

- Repository history is rewritten unexpectedly.
- Unrelated remote changes enter the working branch.
- The branch is rebased onto an unreviewed baseline.
- Protected files change outside the envelope.
- Repository identity or canonical branch changes.
- Evidence no longer matches the current repository state.
- The envelope hash or immutable identity does not match the issued record.

---

## 12. CheckpointPolicy and CapacityHandoffRecord

### 12.1 CheckpointPolicy

A checkpoint must be produced after every accepted internal unit. The checkpoint
must contain:

```
envelope_id                 governing envelope identifier
phase_id                    phase identifier
last_completed_unit         unit_id of the most recently accepted unit
next_eligible_unit          unit_id to begin on resume
branch                      branch at checkpoint time
approved_base_sha           envelope's approved base SHA
current_execution_sha       commit or working-tree fingerprint at checkpoint time
working_tree_state          clean or list of changed paths
changed_paths               cumulative list of paths changed since base SHA
validation_completed        list of validation checks that have passed
validation_remaining        list of validation checks still required
known_limitations           issues that persist after the completed unit
next_exact_action           precise description of the first action on resume
```

### 12.2 WAIT_FOR_CAPACITY

`WAIT_FOR_CAPACITY` is a resumable lifecycle state, not a new approval request.
The envelope remains valid during a capacity wait, provided no invalidation
trigger fires.

A capacity handoff record must include:

```
envelope_validity           VALID or INVALID with reason
last_completed_unit         unit_id of the most recently accepted unit
current_incomplete_unit     unit_id in progress at the time of the wait, if any
current_branch              branch at handoff time
current_sha                 commit or working-tree fingerprint at handoff time
working_tree_state          clean or list of changed paths
uncommitted_changes         list of paths with uncommitted work
validation_completed        checks that have passed
validation_remaining        checks still required
exact_next_action           precise description of the first action on resume
known_blockers              issues preventing resumption
resume_prerequisites        conditions that must be satisfied before resuming
```

Do not begin a new unit when there is insufficient host capacity to complete the
unit and its focused validation safely.

When no trusted host capacity signal exists, use a conservative one-unit-at-a-time
policy and checkpoint after every unit.

---

## 13. ExternalActionAuthorityPolicy

Standing external-action authority is:

- **explicit** - must be named in the envelope;
- **action-specific** - each external action type requires its own flag;
- **repository-specific** - scoped to the exact repository and branch stated;
- **phase-bounded or time-bounded** - expires when the phase completes or the
  envelope expires;
- **revocable** - may be withdrawn by the issuing human at any time;
- **non-transferable** - cannot be delegated to a sub-envelope without explicit
  human authorization;
- **default-deny** - absent or ambiguous authorization means the action is not
  permitted.

The following action flags are defined. Each defaults to `false` and must be
set to `true` explicitly in the envelope to permit the action.

```
stage:                      false
commit:                     false
push_feature_branch:        false
create_draft_pr:            false
merge:                      false
tag:                        false
release:                    false
deploy:                     false
production_mutation:        false
infrastructure_mutation:    false
destructive_action:         false
```

For Phase A, every external action flag is `false`.

Validation evidence cannot set external action flags to `true`. Prompt text
and adapter metadata cannot set external action flags to `true`.

---

## 14. LegacyHostFallbackPolicy

When a receiving host or adapter does not support delegated phase execution:

```
Recognized transition disposition present, valid envelope confirmed:
  Apply the disposition inside the envelope's constraints.

Transition disposition absent because host is legacy:
  Use existing manual pause behavior. Do not interpret absence as AUTO_CONTINUE.

Unknown, malformed, or unsupported disposition:
  Fail closed. Do not continue automatically. Escalate for human review.
```

Never interpret an absent or unknown disposition as `AUTO_CONTINUE`.

---

## 15. Delegated Phase State Machine

The following state model bounds delegated phase execution. No state permits
automatic scope expansion or external action outside the envelope.

```
PHASE_AUTHORIZED
  -> UNIT_READY
  -> UNIT_EXECUTING
  -> UNIT_VALIDATING

UNIT_VALIDATING
  -> UNIT_ACCEPTED        (focused validation passes, disposition AUTO_CONTINUE)
  -> CHECKPOINTED
  -> NEXT UNIT_READY

UNIT_VALIDATING
  -> UNIT_REMEDIATING     (disposition AUTO_REMEDIATE_AND_REVALIDATE)
  -> UNIT_VALIDATING

UNIT_VALIDATING
  -> WAITING_FOR_EVIDENCE (disposition WAIT_FOR_EVIDENCE)

UNIT_READY or UNIT_VALIDATING
  -> WAITING_FOR_CAPACITY (disposition WAIT_FOR_CAPACITY)
  -> CHECKPOINTED

ANY NON-TERMINAL STATE
  -> ESCALATED            (disposition ESCALATE_HUMAN)

ANY NON-TERMINAL STATE
  -> STOPPED              (disposition STOP)

ALL APPROVED UNITS ACCEPTED
  -> PHASE_VALIDATING     (phase gate runs)
  -> PHASE_READY_FOR_HUMAN_REVIEW
```

Transitions from `WAITING_FOR_EVIDENCE` and `WAITING_FOR_CAPACITY` return to
`UNIT_VALIDATING` or `UNIT_READY` when the wait condition is resolved, using the
last checkpoint as the resume point.

---

## 16. Token-Efficiency Requirements

The executing system must apply the following practices to preserve context
capacity during a delegated phase:

- Load the complete envelope once and reference it by `envelope_id` afterward.
- Pass only the current unit, relevant files, delta state, and required
  validation to specialists.
- Use compact evidence packets instead of full terminal transcripts.
- Retain only concise failure excerpts, not full session logs.
- Checkpoint after every accepted unit.
- Keep durable decisions in `DECISION_LOG.md`.
- Keep current execution state in `PROJECT_STATE.md` or a dedicated
  phase-state artifact.
- Avoid repeating full prompts, histories, and completed-unit details.
- Do not reload unrelated specialist or governance context.
- Resume from the last valid checkpoint rather than reconstructing the full
  conversation.

---

## 17. Scope and Non-Goals

Phase A defines contracts only. The following are **not** implemented by this
document:

- Instruction-level autonomous behavior in role skills or adapters (Phase B).
- Host reliability evaluation (Phase C).
- Typed runtime enforcement (Phase D, conditional on separate authorization).
- Release preparation, commit, push, pull request, merge, tag, or deployment
  (Phase E and separately governed).

See `docs/project/DELEGATED_GOVERNANCE_IMPLEMENTATION_PLAN.md` for the
multi-phase implementation roadmap.

---

*Canonical references: `GOVERNANCE_DECISION_PROTOCOL.md`, `GOVERNANCE_LAYER.md`,
`GOVERNANCE_REVIEW_FLOW.md`, `docs/project/DELEGATED_GOVERNANCE_IMPLEMENTATION_PLAN.md`*
