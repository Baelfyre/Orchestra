# Cross-Specialist Coordination Protocol

## Document status

```text
Protocol status: ACCEPTED_FOR_PHASE_1_IMPLEMENTATION
Protocol version: tuner-protocol-v1
Repository: Baelfyre/Orchestra
Issue: #195
Design branch: design/issue-195-tuner-protocol
Design baseline: 4c9fc6d43abda7f57ba2af2b9e90e1731568519b
Audit gate: READY_FOR_ORCHESTRA_THE_TUNER_COLLABORATION_AUDIT_V2_AUTHORIZATION
Implementation authority: NONE
Commit authority: NONE
Push authority: NONE
PR authority: NONE
Merge authority: NONE
Release authority: NONE
```

This document is the canonical source of truth for Orchestra's cross-specialist coordination protocol. Role skills and adapters must reference this document rather than duplicate its complete schemas. Phase 1 implements instruction-level contracts only; typed runtime enforcement, persistence, SQLite, RPC, release, and deployment remain separately governed.

---

## 1. Problem statement

Orchestra already provides deterministic specialist routing, governance review, delegated execution envelopes, specialist-specific authority boundaries, implementation ownership, validation evidence, continuity review, transition dispositions, and adapter and manifest validation.

The unresolved defect is not lack of specialists. It is the absence of a machine-readable cross-specialist coordination contract.

For a multi-domain task, specialists may each produce locally valid outputs while the complete system-level change remains incomplete, contradictory, missing an owner, based on stale assumptions, bound to obsolete evidence, disconnected from generated artifacts, or inconsistent with the actual staged or untracked change identity.

The accepted audit identified five root gaps:

```text
GAP-01  No shared cross-layer contract representation
GAP-02  No automated cross-specialist invalidation propagation
GAP-03  No canonical contradiction and missing-owner protocol
GAP-04  Incomplete staged-content and untracked-file evidence identity
GAP-05  No backward specialist re-entry mechanism in manual workflows
```

The Tuner protocol addresses these gaps without absorbing the authority of Conductor, Arbiter, Overseer, or any domain specialist.

---

## 2. Design principles

### 2.1 Preserve existing authority

The protocol is additive. It must not redefine existing roles.

```text
Conductor
  remains the exclusive router and workflow sequencer.

The Steward
  remains the business alignment, scope, requirements, and SDLC authority.

The Governor
  remains the legal, regulatory, privacy-obligation, IP, licensing,
  and compliance authority.

Arbiter
  remains the continuity, handoff, evidence-freshness, branch-safety,
  and transition-decision authority.

Overseer
  remains the validation strategy, evidence-quality, and release-readiness owner.

Domain specialists
  remain the exclusive owners of their domain decisions.

Ponytail
  remains the implementation owner after upstream contracts are ready.

Dagger
  remains explicitly gated and unavailable for ordinary coordination.

Caveman
  remains an output-compression convention, not a registered specialist.
```

### 2.2 Tuner does not route

The Tuner may recommend the next route, but only Conductor may dispatch specialists.

### 2.3 Tuner does not decide domain content

The Tuner may assemble, compare, and reference specialist contracts. It may not rewrite a specialist decision or select one domain rule over another.

### 2.4 Tuner does not approve continuation

The Tuner reports coordination state. Arbiter decides whether work may continue.

### 2.5 Tuner does not own validation evidence

The Tuner identifies which evidence is required or stale. Overseer produces and assesses validation evidence.

### 2.6 Simple work stays simple

Obvious single-owner work must bypass the protocol unless the resulting change crosses a domain boundary.

### 2.7 Authority remains external to coordination state

A complete cross-layer contract does not grant implementation, Git, external-action, deployment, or release authority.

### 2.8 Fail closed on uncertainty

Unknown statuses, malformed packets, unresolved ownership, stale contract revisions, or contradictions must never default to implementation readiness.

---

## 3. Proposed role

### 3.1 Canonical identity

```yaml
name: the-tuner
slug: the-tuner
role: Cross-Specialist Coordination Specialist
activation_level: Specialist
depends_on: conductor
primary_use: >
  Cross-domain dependency mapping, specialist-contract assembly,
  ownership completeness, contradiction detection, semantic invalidation,
  contract revision tracking, and re-entry recommendations.
avoid_when: >
  One obvious specialist owns the complete task and no material cross-domain
  dependency or boundary-crossing change exists.
output_formats:
  - Collaboration Review
  - Cross-Layer Contract Packet
  - Contradiction Report
  - Re-entry Recommendation
```

`activation_level: Specialist` is proposed to avoid introducing a new manifest activation class. The Tuner is a coordination specialist that can only be invoked by Conductor.

### 3.2 Tuner may

- map affected layers;
- build a collaboration graph;
- request specialist contract outputs through Conductor;
- assemble immutable references to specialist-owned decisions;
- identify missing owners;
- identify missing acceptance criteria;
- detect cross-contract contradictions;
- track contract revisions;
- propagate semantic invalidation;
- identify stale diagrams, documentation, evidence, and reviews;
- compare post-implementation deltas with the frozen contract;
- recommend specialist re-entry;
- report whether the cross-layer contract is ready, incomplete, contradicted, or stale;
- recommend the next Conductor route.

### 3.3 Tuner may not

- create or widen authority;
- approve governance;
- approve scope;
- approve architecture;
- approve security policy;
- approve database semantics;
- approve UI or UX decisions;
- implement code;
- modify specialist contracts;
- validate its own output as sufficient evidence;
- issue an Arbiter transition disposition;
- stage, commit, push, open a PR, merge, release, deploy, or publish;
- silently resolve contradictions;
- make a product, policy, legal, privacy, security, or architecture tradeoff;
- activate Dagger;
- force coordination overhead onto simple single-owner work.

---

## 4. Activation and bypass

### 4.1 Activation conditions

Conductor must activate The Tuner when any of the following is true:

1. More than one specialist owns a material part of the requested behavior.
2. A task crosses two or more of these layers: governance, architecture, security, persistence, UI or interaction, implementation, validation, documentation, diagram or model, generated artifact, or Git and continuity.
3. A specialist output depends on an assumption owned by another specialist.
4. A proposed implementation changes files outside the primary specialist's declared domain.
5. A post-implementation delta changes a contract, interface, invariant, schema, policy, user flow, initialization order, or validation requirement.
6. A specialist reports missing ownership.
7. Two specialist outputs are potentially contradictory.
8. A generated artifact may differ materially from inspected source.
9. Evidence or documentation may belong to an older contract revision.
10. Manual workflow continuation requires backward specialist re-entry.
11. Conductor cannot establish one coherent ordered sequence from current specialist outputs.

### 4.2 Mandatory bypass

The Tuner must be bypassed when all of the following are true:

```text
one obvious specialist owns the entire task
no governance trigger exists
no material cross-domain dependency exists
no boundary-crossing file or behavior change is expected
no prior specialist contract is invalidated
no generated-artifact or runtime-only risk is introduced
```

Examples:

- correcting a documentation typo through Scribe;
- a localized Ponytail implementation with accepted design and unchanged contracts;
- a standalone Weaver notation correction that does not change domain semantics;
- a focused Overseer test-plan review that does not alter scope or contracts.

### 4.3 Late activation

A task that begins as a direct route must activate The Tuner if the diff crosses into another specialist's domain, a new dependency appears, a contract assumption changes, generated output introduces a new layer, a validation failure reveals a cross-domain cause, or the primary specialist returns `SPECIALIST_REROUTE_REQUIRED`.

Late activation must preserve the original direct-task history and identify the event that changed classification.

### 4.4 Activation output

Conductor records:

```text
activation_decision:
  BYPASS_SINGLE_OWNER
  ACTIVATE_MULTI_DOMAIN
  ACTIVATE_LATE_BOUNDARY_CROSSING
  ACTIVATE_CONTRADICTION
  ACTIVATE_MISSING_OWNER
  ACTIVATE_STALE_CONTRACT
```

The activation decision is procedural. It does not create authority.

---

## 5. Coordination lifecycle

```text
TASK_INTAKE
  -> ROUTE_CLASSIFICATION
  -> [BYPASS_SINGLE_OWNER | TUNER_ACTIVATED]

TUNER_ACTIVATED
  -> COLLABORATION_SESSION_OPEN
  -> LAYER_AND_OWNER_DISCOVERY
  -> COLLABORATION_GRAPH_DRAFTED
  -> SPECIALIST_CONTRACT_COLLECTION
  -> CONTRACT_ASSEMBLY
  -> [INCOMPLETE | CONTRADICTED | READY_FOR_FREEZE]

INCOMPLETE
  -> CONDUCTOR_ROUTES_MISSING_OWNER_OR_INPUT
  -> SPECIALIST_CONTRACT_COLLECTION

CONTRADICTED
  -> CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED
  -> [SPECIALIST_REVISION | HUMAN_DECISION | STOP]

READY_FOR_FREEZE
  -> CONTRACT_FREEZE
  -> IMPLEMENTATION_PACKET
  -> PONYTAIL_IMPLEMENTATION
  -> POST_IMPLEMENTATION_DELTA
  -> [UNCHANGED | REENTRY_REQUIRED | CONTRADICTED]

REENTRY_REQUIRED
  -> CONTRACTS_MARKED_STALE
  -> CONDUCTOR_ROUTES_AFFECTED_SPECIALISTS
  -> CONTRACT_REASSEMBLY
  -> VALIDATION_REQUIREMENT_REFRESH

VALIDATION
  -> OVERSEER_EVIDENCE
  -> TUNER_COORDINATION_FRESHNESS_CHECK
  -> ARBITER_TRANSITION_EVALUATION
  -> [CONTINUE | WAIT | ESCALATE | STOP]

CLOSEOUT
  -> SCRIBE_AND_WEAVER_USE_ACCEPTED_CONTRACT_REVISION
  -> CONTRACT_SESSION_CLOSED
```

---

## 6. Canonical statuses and gates

### 6.1 Collaboration status

```text
BYPASSED
COLLECTING
INCOMPLETE
CONTRADICTED
READY
FROZEN
STALE
SUPERSEDED
CLOSED
```

### 6.2 Required output gates

#### `CROSS_LAYER_CONTRACT_INCOMPLETE`

Return when any required owner, domain contract, acceptance criterion, dependency, validation requirement, artifact lifecycle, or authority reference is missing.

This is blocking.

#### `CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED`

Return when two or more specialist-owned requirements cannot simultaneously be satisfied, or when resolving the conflict requires a tradeoff outside The Tuner's authority.

This is blocking and must route through Conductor.

#### `CROSS_LAYER_CONTRACT_READY`

Return when all affected layers have owners, every required specialist contract is present, dependencies and order are explicit, no unresolved contradiction exists, acceptance criteria are complete, prohibited scope is explicit, validation ownership is explicit, artifact lifecycle requirements are explicit, invalidation triggers are recorded, authority references are valid, and all component contracts cover the same current revision.

This status is a readiness recommendation, not implementation authority.

#### `CROSS_LAYER_CONTRACT_STALE`

Return when the frozen contract no longer covers the current change, source state, generated artifact, or specialist decision revision.

This is blocking until affected contracts are refreshed.

#### `SPECIALIST_REENTRY_REQUIRED`

Return with an exact list of specialists and reasons when a change invalidates prior specialist decisions.

---

## 7. Core data contracts

### 7.1 CollaborationSession

A `CollaborationSession` exists for every activated multi-domain task.

```yaml
schema_version: tuner-protocol-v1
session_id: unique identifier
task_id: issue, request, phase, or locally unique task reference
repository_identity: canonical repository URL and name
branch: active branch
baseline_sha: exact source baseline
execution_mode: Ideation | Prototype | Implementation | Audit | Release
progression_mode: MANUAL | DELEGATED
manual_authorization_reference: nullable
delegated_envelope_id: nullable
activation_decision: enum
activation_reason: human-readable explanation
affected_layers: [layer identifiers]
primary_owner: specialist slug or conductor
required_specialists: [specialist slugs]
optional_specialists: [specialist slugs]
prohibited_specialists: [specialist slugs]
collaboration_status: enum
current_contract_revision: integer
current_contract_hash: nullable immutable hash
opened_by: conductor
opened_at: ISO-8601
updated_at: ISO-8601
closed_at: nullable ISO-8601
```

Authority rule:

```text
MANUAL mode requires manual_authorization_reference.
DELEGATED mode requires delegated_envelope_id.
Neither reference may be invented by The Tuner.
```

### 7.2 CollaborationGraph

The graph separates sequence dependency from invalidation dependency.

```yaml
schema_version: tuner-protocol-v1
graph_id: unique identifier
session_id: CollaborationSession.session_id
graph_revision: integer

nodes:
  - node_id: unique within graph
    specialist: specialist slug
    domain: canonical domain name
    required: boolean
    ownership_scope: exact output or decision owned
    input_contracts: [contract references]
    output_contract_type: contract type
    status: NOT_REQUESTED | REQUESTED | RECEIVED | STALE | SUPERSEDED
    source_references: [path or issue references]

sequence_edges:
  - from_node
    to_node
    relation:
      REQUIRES_BEFORE
      VALIDATES_AFTER
      IMPLEMENTS_AFTER
      DOCUMENTS_AFTER
      VISUALIZES_AFTER
      GOVERNANCE_GATES
    reason

invalidation_edges:
  - source_node
    target_node
    trigger_categories:
      - CONTRACT_CHANGE
      - INTERFACE_CHANGE
      - POLICY_CHANGE
      - SCHEMA_CHANGE
      - USER_FLOW_CHANGE
      - INITIALIZATION_ORDER_CHANGE
      - GENERATED_ARTIFACT_CHANGE
      - VALIDATION_REQUIREMENT_CHANGE
      - AUTHORITY_CHANGE
      - SOURCE_REVISION_CHANGE
    invalidated_outputs
    required_reentry: boolean
    reason
```

Rules:

- Initial sequence edges should form a deterministic executable order.
- Invalidation edges may point backward.
- A node may not be marked complete when a required predecessor is missing or stale.
- A cycle in sequence edges is a contradiction or incomplete decomposition.
- A cycle in invalidation edges is permitted but must be handled as a revalidation set.

### 7.3 SpecialistDomainContract

Each specialist owns and signs its own domain contract. The Tuner stores immutable references and normalized metadata, not rewritten decisions.

```yaml
schema_version: tuner-protocol-v1
contract_id: unique identifier
session_id: CollaborationSession.session_id
specialist: specialist slug
domain: canonical domain
contract_revision: integer
status: DRAFT | ACCEPTED | STALE | SUPERSEDED
valid_against:
  baseline_sha: exact baseline
  collaboration_graph_revision: integer
  dependency_contracts:
    - contract_id
      contract_revision
      contract_hash

authority_reference:
  manual_authorization_reference: nullable
  delegated_envelope_id: nullable

owned_decisions:
  - decision_id
    statement
    rationale
    source_references

constraints:
  - constraint_id
    statement
    severity: REQUIRED | RECOMMENDED
    affected_layers

acceptance_criteria:
  - criterion_id
    statement
    validation_owner
    evidence_type

prohibited_changes:
  - statement
    reason

assumptions:
  - assumption_id
    statement
    owner
    invalidation_trigger

dependencies:
  - specialist
    contract_id
    required_revision
    relationship

required_validation:
  - validation_id
    owner
    command_or_method
    required_artifacts
    pass_condition

generated_artifact_requirements:
  - artifact_type
    lifecycle_reference
    inspection_requirement

invalidation_triggers:
  - trigger_category
    description
    invalidates

known_limitations:
  - statement

produced_by: specialist slug
produced_at: ISO-8601
contract_hash: immutable hash over canonical content
```

The Tuner must never modify `owned_decisions`, `constraints`, or `acceptance_criteria`. A correction must be produced by the owning specialist as a new revision.

### 7.4 CrossLayerContractPacket

The packet is the assembled coordination contract.

```yaml
schema_version: tuner-protocol-v1
packet_id: unique identifier
session_id: CollaborationSession.session_id
packet_revision: integer
status: COLLECTING | INCOMPLETE | CONTRADICTED | READY | FROZEN | STALE
repository_identity: canonical repository
branch: current branch
baseline_sha: exact baseline
collaboration_graph_id: graph reference
collaboration_graph_revision: integer

component_contracts:
  - contract_id
    specialist
    contract_revision
    contract_hash
    status

ownership_matrix:
  - output_or_decision
    owner
    supporting_roles
    validation_owner
    continuity_owner

integration_constraints:
  - constraint_id
    source_contract
    target_contracts
    statement
    validation_owner

acceptance_matrix:
  - criterion_id
    source_contract
    affected_layers
    validation_owner
    evidence_required
    status

prohibited_scope:
  - path_or_behavior
    source
    enforcement_owner

missing_owners:
  - output_or_decision
    reason
    recommended_route

contradictions:
  - contradiction_id
    status
    references

invalidation_matrix:
  - trigger
    invalidated_contracts
    invalidated_artifacts
    required_reentry

artifact_lifecycle_requirements:
  - artifact_id_or_type
    producer
    expected_path
    pre_existing_state_required
    inspection_owner
    cleanup_authority
    evidence_retention
    contract_binding_required

change_identity_requirements:
  tracked_patch_hash_required: boolean
  staged_patch_hash_required: boolean
  untracked_manifest_required: boolean
  added_blob_hashes_required: boolean
  working_tree_fingerprint_required: boolean

authority_references:
  manual_authorization_reference: nullable
  delegated_envelope_id: nullable
  external_action_flags: reference only

freeze:
  ready_at: nullable
  frozen_at: nullable
  frozen_by: nullable
  freeze_rule: MANUAL_CONFIRMATION | DELEGATED_DERIVATION
  contract_hash: nullable

tuner_assessment:
  status_token
  findings
  recommended_next_route
  assessed_at
```

### 7.5 SpecialistHandoffDelta

A handoff delta reports what changed between accepted contract state and the next stage.

```yaml
schema_version: tuner-protocol-v1
delta_id: unique identifier
session_id: CollaborationSession.session_id
from_role: specialist or implementation role
to_role: specialist, tuner, overseer, or arbiter
source_packet_revision: integer
source_contract_hash: frozen packet hash
source_state:
  baseline_sha
  current_commit_sha
  working_tree_fingerprint

changed_paths:
  tracked: [paths]
  staged: [paths]
  untracked: [paths]
  ignored_relevant: [paths]

change_identity:
  tracked_patch_hash: nullable
  staged_patch_hash: nullable
  untracked_file_manifest:
    - path
      content_hash
  added_blob_hashes:
    - path
      blob_hash

behavioral_deltas:
  - delta_type
    description
    affected_layers
    source_reference

contract_effects:
  unchanged_contracts: [contract references]
  potentially_invalidated_contracts: [contract references]
  definitely_invalidated_contracts: [contract references]

artifact_deltas:
  - path
    producer
    state_before
    state_after
    content_hash
    lifecycle_status

required_reentry:
  - specialist
    reason
    required_inputs

known_limitations:
  - statement

produced_by
produced_at
delta_hash
```

A file-list-only handoff is insufficient when the task creates or changes staged or untracked content.

### 7.6 InvalidationEvent

```yaml
schema_version: tuner-protocol-v1
event_id: unique identifier
session_id: CollaborationSession.session_id
trigger_source:
  role
  contract_id
  prior_revision
  new_revision
trigger_category: enum
description: exact material change

affected_contracts:
  - contract_id
    prior_revision
    invalidation_reason
    required_reentry_owner

affected_evidence:
  - evidence_id
    stale_reason

affected_artifacts:
  - artifact_reference
    stale_reason

affected_docs_and_diagrams:
  - path_or_reference
    owner
    stale_reason

status: OPEN | REENTRY_ROUTED | REVALIDATED | RESOLVED
detected_by: the-tuner
detected_at: ISO-8601
resolved_at: nullable
```

An invalidation event does not itself route a specialist. The Tuner returns a re-entry recommendation to Conductor.

### 7.7 CrossSpecialistContradiction

```yaml
schema_version: tuner-protocol-v1
contradiction_id: unique identifier
session_id: CollaborationSession.session_id

contract_a:
  contract_id
  specialist
  revision
  clause_reference

contract_b:
  contract_id
  specialist
  revision
  clause_reference

conflict_statement: exact reason both cannot currently be satisfied
severity: CRITICAL | MAJOR | MINOR
decision_type:
  DOMAIN_REVISION
  CROSS_DOMAIN_TRADEOFF
  SCOPE_DECISION
  ARCHITECTURE_DECISION
  SECURITY_DECISION
  GOVERNANCE_DECISION
  HUMAN_INTENT_REQUIRED

resolvable_by_specialist_revision: boolean
required_participants: [specialists]
human_review_required: boolean
status: OPEN | REVISION_REQUESTED | HUMAN_REVIEW | RESOLVED | STOPPED
resolution_reference: nullable
detected_by: the-tuner
detected_at
```

Rules:

- The Tuner identifies the conflict but never selects the winning requirement.
- Conductor routes affected specialists for revision when the conflict is resolvable without changing approved intent.
- Human review is required when the conflict requires a tradeoff, new intent, scope expansion, policy choice, or authority decision.
- Arbiter must not issue continuation while a blocking contradiction is open.

### 7.8 GeneratedArtifactLifecycleRecord

```yaml
schema_version: tuner-protocol-v1
artifact_id: unique identifier
session_id: CollaborationSession.session_id
contract_packet_revision: integer
producer_role
producing_command
path
artifact_type
state_before: ABSENT | PRESENT_TRACKED | PRESENT_UNTRACKED | PRESENT_IGNORED
state_after: enum
content_hash: nullable
inspection_required: boolean
inspection_owner
retention_required: boolean
cleanup_authority
cleanup_condition
cleanup_performed: boolean
cleanup_evidence
freshness_binding:
  baseline_sha
  current_commit_sha
  contract_hash
```

Required artifact classes include, when relevant:

```text
dist/
test-results/
playwright-report/
coverage/
.wrangler/
.cloudflare-build/
Python caches
test caches
adapter exports
validation reports
generated diagrams
```

Pre-existing artifacts must never be deleted merely because the current run also uses the same path.

---

## 8. Contract assembly rules

The Tuner may return `CROSS_LAYER_CONTRACT_READY` only if all checks pass.

### 8.1 Ownership completeness

Every architecture boundary, security rule, persistence rule, UI or interaction rule, implementation output, validation criterion, generated artifact lifecycle, documentation update, diagram semantics and notation, and continuity decision must have exactly one decision owner.

Supporting roles may be multiple. Decision ownership must be singular.

### 8.2 Dependency completeness

Every assumption that belongs to another specialist must reference the specialist, contract ID, revision, contract hash, and invalidation trigger.

### 8.3 Acceptance completeness

Every required behavior must have an acceptance criterion, validation owner, evidence type, and pass condition.

### 8.4 Prohibited-scope completeness

The packet must include prohibited paths, behaviors, external actions, protected repositories, and authority expansions.

### 8.5 Artifact completeness

When a command can create generated output, the lifecycle record must be declared before execution.

### 8.6 Revision completeness

All component contracts must be valid against the same graph revision and packet baseline.

### 8.7 Contradiction completeness

No blocking contradiction may remain open.

---

## 9. Contract freeze

### 9.1 Freeze purpose

Freeze creates an immutable contract identity that implementation and validation can reference.

### 9.2 Freeze conditions

```text
packet.status == READY
missing_owners is empty
blocking contradictions are empty
all required specialist contracts are ACCEPTED
all component contracts match current revisions
all acceptance criteria have validation owners
all artifact lifecycles are declared
authority reference is valid
prohibited scope is explicit
```

### 9.3 Freeze by progression mode

#### Manual mode

The Tuner returns `CROSS_LAYER_CONTRACT_READY`. A human or human-controlled process confirms freeze. Conductor records the frozen packet and may proceed only under separately granted implementation authority.

#### Delegated mode

Conductor may freeze the packet without a new approval only when all component decisions are strictly derived from approved envelope units, no envelope invalidation trigger occurred, no new product, architecture, policy, legal, privacy, security, licensing, or compliance choice was introduced, and the envelope explicitly permits the participating roles and paths.

Otherwise return `ESCALATE_HUMAN`.

### 9.4 Freeze output

```yaml
packet_status: FROZEN
contract_hash: immutable hash
frozen_packet_revision: integer
frozen_against:
  repository
  branch
  baseline_sha
  graph_revision
  component_contract_hashes
implementation_authority: separate reference or false
```

A frozen contract is not an implementation authorization by itself.

---

## 10. Implementation packet

Ponytail receives a reduced implementation packet, not the full project history.

```yaml
task
frozen_contract_hash
allowed_paths
prohibited_paths
allowed_operations
required_outputs
integration_constraints
acceptance_criteria
required_focused_validation
required_artifact_lifecycles
required_handoff_delta_fields
specialist_reentry_triggers
external_action_authority
```

Ponytail must stop and return `SPECIALIST_REROUTE_REQUIRED` when implementation requires a decision absent from the frozen contract, a change outside allowed paths, a new architecture choice, a new security rule, a new persistence decision, a new UI or UX decision, a new governance decision, an undeclared generated artifact, or an unauthorized external action.

---

## 11. Post-implementation reconciliation

### 11.1 Required input

Ponytail or the active implementation role produces a `SpecialistHandoffDelta`.

### 11.2 Tuner comparison

The Tuner compares the frozen contract packet, behavioral delta, change identity, and generated artifact records.

### 11.3 Outcomes

#### `NO_CONTRACT_CHANGE`

The implementation matches the frozen packet. Proceed to Overseer validation.

#### `SPECIALIST_REENTRY_REQUIRED`

One or more contracts are stale. Tuner lists exact specialists, contract clauses, and required evidence.

#### `CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED`

The delta reveals incompatible requirements.

#### `CROSS_LAYER_CONTRACT_STALE`

The change cannot be validated against the frozen packet until contract revisions are assembled and frozen again.

### 11.4 Re-entry rule

Conductor routes only affected specialists, not the full specialist set.

Example:

```text
Cipher changes CSP requirement
  -> Clockwork initialization contract stale
  -> Ponytail implementation delta stale
  -> Overseer browser/runtime criteria stale
  -> Weaver runtime diagram stale, if present
  -> Scribe technical documentation stale, if present
```

Tuner must produce the minimal re-entry set from the invalidation graph.

---

## 12. Contradiction handling

### 12.1 Detection

A contradiction exists when two required constraints cannot both be true, sequence dependencies form a cycle, two roles claim the same decision authority, an acceptance criterion conflicts with prohibited scope, an implementation requirement exceeds authority, a specialist contract relies on an obsolete dependency revision, a generated artifact contradicts source-based assumptions, or manual and delegated authority references conflict.

### 12.2 Resolution levels

#### Level 1: Specialist correction

Use when one output is incomplete, malformed, or outside its role's authority. Conductor routes the owning specialist to revise.

#### Level 2: Cross-specialist reconciliation

Use when affected specialists can reconcile without changing approved intent. Conductor routes all required participants. Tuner assembles the new revisions.

#### Level 3: Human decision

Use when resolution requires product or scope choice, architecture tradeoff not already authorized, security or privacy tradeoff, legal, licensing, or compliance interpretation, authority expansion, external action, or acceptance of residual risk.

Return:

```text
CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED
```

#### Level 4: Stop

Use when the conflict involves unsafe, prohibited, destructive, protected, secret-exposing, or authority-invalid behavior.

Arbiter must apply existing transition precedence.

---

## 13. Manual-mode re-entry

The protocol must provide the same semantic invalidation protection in manual workflows without pretending a delegated envelope exists.

### 13.1 Manual authorization reference

A manual session records the human-approved task, scope, branch, and baseline reference.

### 13.2 Manual handoff packet

Manual mode must still use CollaborationSession, CollaborationGraph, SpecialistDomainContract, CrossLayerContractPacket, SpecialistHandoffDelta, and InvalidationEvent.

### 13.3 Manual continuation

Arbiter may return `READY` only when the current packet is not stale, required specialist re-entry is complete, current evidence references the current contract hash, no contradiction remains, and current Git identity matches the reported delta.

This closes GAP-05 without changing manual mode into delegated mode.

---

## 14. Delegated-mode integration

The Tuner protocol supplements `DelegatedExecutionEnvelope`; it does not replace it.

### 14.1 Envelope extensions

A future implementation may add:

```yaml
collaboration_policy:
  tuner_activation: AUTO_ON_MULTI_DOMAIN
  permitted_specialists: [...]
  maximum_contract_revisions: integer
  automatic_freeze_allowed: boolean
  contradiction_escalation_required: true
  semantic_invalidation_required: true
```

### 14.2 Approved unit plan

A multi-domain unit may reference:

```yaml
collaboration_session_id
required_contract_packet_revision
required_contract_hash
required_specialist_nodes
```

### 14.3 ExecutionEvidencePacket extensions

To close GAP-04 and bind validation to coordination state:

```yaml
collaboration_session_id
cross_layer_contract_hash
cross_layer_contract_revision
tracked_patch_hash
staged_patch_hash
untracked_file_manifest
added_blob_hashes
artifact_lifecycle_records
specialist_reentry_completed
open_invalidation_events
```

### 14.4 Transition decision rule

Arbiter must never issue `AUTO_CONTINUE` when contract packet status is not `FROZEN`, evidence references an older contract hash, an invalidation event is open, a required specialist contract is stale, a blocking contradiction is open, or the staged or untracked change identity differs from evidence.

---

## 15. Role integration

### 15.1 Conductor

Conductor decides whether Tuner activates, opens and closes collaboration sessions, routes requested specialists, consumes Tuner readiness and re-entry recommendations, records freeze according to progression mode, never delegates routing authority to Tuner, and pauses on incomplete, contradicted, or stale packets.

### 15.2 Arbiter

Arbiter verifies session, packet, branch, SHA, and fingerprint freshness; verifies no open invalidation or contradiction blocks continuation; consumes Tuner status as coordination evidence; retains exclusive authority over continuity and transition decisions; and does not validate domain correctness itself.

### 15.3 Overseer

Overseer converts acceptance matrix entries into a validation plan, produces evidence bound to the frozen contract hash, inspects declared generated artifacts, reports skipped checks and limitations, and does not decide whether contracts are semantically consistent.

### 15.4 Domain specialists

Each specialist produces and revises its own immutable domain contract, declares assumptions, dependencies, invalidation triggers, and acceptance criteria, does not edit another specialist's contract, and responds to re-entry with a new contract revision.

### 15.5 Ponytail

Ponytail implements only against a frozen contract and separate implementation authority, produces complete handoff delta and change identity, and does not resolve missing or contradictory design decisions.

### 15.6 Weaver

Weaver consumes frozen domain semantics, binds diagrams to contract hash and source revision, marks diagrams stale when related contracts change, and does not decide semantics.

### 15.7 Scribe

Scribe consumes accepted or frozen source decisions, binds documentation updates to contract hash, and does not reconcile conflicting source material.

### 15.8 Steward and Governor

Governance contracts participate as immutable component contracts when triggered. Tuner may detect that they are missing or stale but cannot reinterpret or override them.

### 15.9 Dagger

Dagger remains excluded unless explicit destructive-path authorization exists. Tuner activation does not authorize Dagger.

---

## 16. Required validator behavior

A future implementation should include deterministic validators.

### 16.1 Registration and routing

Validate that The Tuner is registered consistently, `depends_on: conductor`, single-owner fixtures bypass Tuner, multi-domain fixtures activate Tuner, late boundary crossing activates Tuner, and Tuner never becomes primary implementation owner.

### 16.2 Contract schema

Reject missing owner, duplicate decision owner, missing acceptance owner, stale dependency revision, missing contract hash, inconsistent baseline, unresolved contradiction, undeclared artifact lifecycle, and invalid authority reference.

### 16.3 Invalidation

Prove that a security-rule change invalidates architecture and validation dependents, a schema change invalidates API and DB validation dependents, a UI flow change invalidates accessibility and security dependents, a generated artifact change invalidates source-only evidence, a contract revision change invalidates diagrams and documentation, and only affected specialists are re-entered.

### 16.4 Change identity

Reject evidence when untracked files are omitted, staged paths differ from reported paths, added-file hashes are absent, staged patch hash differs, working-tree fingerprint differs, or evidence references an older contract hash.

### 16.5 Contradiction

Prove that Tuner detects but does not resolve, Conductor routes correction, human review is required for material tradeoffs, and Arbiter blocks continuation while contradiction remains.

### 16.6 Manual and delegated parity

Prove that manual mode receives semantic invalidation protection, delegated mode binds evidence to packet hash, manual mode does not invent envelope authority, and delegated mode cannot freeze outside envelope scope.

### 16.7 Adapter parity

Validate canonical source against every supported adapter. Do not claim universal host reliability from one adapter test.

---

## 17. Required behavior scenarios

At minimum, future implementation tests must cover:

1. Direct Scribe typo bypass.
2. Direct Ponytail accepted-design bypass.
3. Frontend field requiring API and persistence owners.
4. CSP change invalidating initialization-order review.
5. Database constraint invalidating API validation.
6. UI flow invalidating security and accessibility reviews.
7. Generated build artifact contradicting source assumptions.
8. Weaver diagram bound to obsolete contract hash.
9. Scribe documentation bound to obsolete contract hash.
10. Missing implementation owner.
11. Missing validation owner.
12. Conflicting Cipher and Cloak constraints.
13. Cross-specialist conflict requiring human tradeoff.
14. Tuner attempting to resolve conflict, which must fail.
15. Post-implementation path crossing a new domain.
16. Untracked added file omitted from handoff.
17. Staged patch hash mismatch.
18. Pre-existing ignored artifact preserved.
19. Audit-created artifact lifecycle declared.
20. Manual-mode specialist re-entry.
21. Delegated-mode automatic re-entry within envelope.
22. Delegated-mode scope expansion escalation.
23. Dagger remains blocked.
24. External action remains default-deny.
25. Unknown Tuner status fails closed.

---

## 18. Proposed source change set for future implementation

This section plans likely source changes. It does not authorize them.

### 18.1 New canonical files

```text
skills/the-tuner/SKILL.md
skills/the-tuner/OUTPUT_FORMATS.md
docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md
tests/behavior/tuner-collaboration-fixtures.json
scripts/validate_tuner_collaboration_contract.py
```

### 18.2 Existing canonical files likely requiring scoped updates

```text
AGENTS.md
SKILL_INDEX.md
ROUTING_MAP.md
plugin.json
marketplace manifest
skills/conductor/SKILL.md
skills/arbiter/SKILL.md
skills/overseer/SKILL.md
skills/ponytail/SKILL.md
docs/governance/DELEGATED_EXECUTION_POLICY.md
docs/routing/MINIMAL_PROMPT_FORMAT.md
tests/behavior/test_router_contracts.py
tests/behavior/run_tests.py
scripts/validate_routing_contract.py
scripts/validate_governance_protocol_consistency.py
adapters/codex/*
README.md, only when public behavior is ready
CHANGELOG.md, only at accepted implementation closeout
DECISION_LOG.md, after design decision acceptance
```

### 18.3 Optional later typed-runtime phase

Separately authorized future work may add typed runtime models for CollaborationSession, CollaborationGraph, SpecialistDomainContract, CrossLayerContractPacket, InvalidationEvent, CrossSpecialistContradiction, and SpecialistHandoffDelta.

This design does not authorize SQLite, RPC, persistent runtime storage, or host-level orchestration changes.

---

## 19. Phased implementation proposal

### Phase 1: Canonical protocol and instruction contracts

Scope:

- canonical protocol document;
- The Tuner skill;
- routing and role references;
- prompt and output contracts;
- behavior fixtures;
- deterministic validators;
- adapter parity.

No typed runtime persistence.

### Phase 2: Evidence and continuity integration

Scope:

- evidence packet extensions;
- staged and untracked change identity;
- artifact lifecycle records;
- Arbiter freshness enforcement;
- Overseer evidence binding;
- manual-mode re-entry tests.

### Phase 3: Optional typed runtime enforcement

Scope only if separately approved:

- typed models;
- runtime state machine;
- lifecycle integration;
- adversarial tests;
- host reliability evaluation.

No phase implies commit, push, PR, merge, release, or deployment authority.

---

## 20. Design acceptance criteria

The design is ready for implementation planning only when human review confirms:

```text
The Tuner is subordinate to Conductor routing.
The Tuner does not own domain decisions.
The Tuner does not issue transition dispositions.
Overseer remains evidence owner.
Arbiter remains continuation owner.
Simple single-owner work bypasses Tuner.
Late boundary crossing activates Tuner.
Every affected layer has exactly one decision owner.
Specialist contracts are immutable and revisioned.
Cross-layer packets reference, not rewrite, domain decisions.
Contradictions are detected but never silently resolved.
Semantic invalidation creates minimal specialist re-entry.
Manual workflows receive re-entry protection.
Delegated workflows remain envelope-bounded.
Frozen contracts do not create implementation authority.
Evidence is bound to the current contract hash.
Staged and untracked identity is represented.
Generated artifacts have explicit lifecycles.
Diagrams and documentation bind to contract revisions.
Dagger and external actions remain separately authorized.
Unknown states fail closed.
```

---

## 21. Open design risks

### 21.1 Protocol weight

A full contract packet may be too heavy for moderate tasks. Implementation should support compact references and only material fields while retaining deterministic validation.

### 21.2 Semantic invalidation accuracy

Over-broad invalidation can cause unnecessary specialist reruns. Under-broad invalidation can preserve stale reviews. Initial implementation should prefer explicit specialist-declared triggers over heuristic inference.

### 21.3 Contract hashing

Canonical serialization must be defined before machine enforcement. Markdown prose alone is not a reliable hash input.

### 21.4 Manual workflow adoption

Manual mode needs enough structure to close GAP-05 without becoming a delegated envelope in disguise.

### 21.5 Host parity

Instruction-level parity does not prove all hosts preserve collaboration state. Host reliability remains a separate evaluation.

---

## 22. Recommended design decision

Adopt The Tuner as a registered coordination specialist invoked only by Conductor.

Use a mode-independent `CollaborationSession` and `CrossLayerContractPacket` so both manual and delegated workflows receive semantic coordination and invalidation protection.

Keep transition authority with Arbiter, validation ownership with Overseer, and domain authority with each specialist.

Implement the protocol in phases, beginning with canonical instructions, fixtures, validators, and adapter parity. Defer typed runtime persistence, SQLite, RPC, deployment, and host-level state management.

---

## 23. Final design gate

```text
READY_FOR_THE_TUNER_PROTOCOL_DESIGN_REVIEW
```

This gate authorizes human review of the proposed design only.

It does not authorize repository implementation, source edits, staging, commits, pushes, pull requests, merges, releases, deployment, marketplace publication, SQLite, RPC, consumer-repository changes, or protected-repository changes.

## 24. Phase 1 enforcement notes

Conductor remains the exclusive router.

The Tuner detects but never resolves a contradiction.

A frozen contract is not an implementation authorization by itself.

Full contract-hash, staged-patch, untracked-file, added-blob, and artifact-lifecycle enforcement is reserved for Phase 2.
