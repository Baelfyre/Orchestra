# AQ-8 High-Risk Assurance Packs

AQ-8 provides deterministic, reusable, machine-verifiable assurance packs for
security, provenance, concurrency, state-machine behavior, and evidence
integrity. The packs evaluate an exact repository, source reference, candidate
SHA, tree SHA, work item, governance basis, and workflow run. They emit
evidence-only results. A case, pack, or aggregate decision never grants
transition, merge, release, provider, production, or other runtime authority.
Arbiter remains the transition owner.

The implementation is available through:

- orchestra_runtime/domain/adaptive/high_risk_assurance.py
- machine/adaptive/aq8-high-risk-assurance-packs.v1.json
- machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json
- scripts/validation/validate_aq8.py
- tests/runtime/test_adaptive_assurance_aq8.py

## Required packs and cases

### Security

- SECURITY_UNKNOWN_CREDENTIAL
- SECURITY_INACTIVE_PRINCIPAL
- SECURITY_MISSING_GRANT
- SECURITY_GUESSED_OBJECT_ID
- SECURITY_CROSS_TENANT_ID
- SECURITY_CROSS_WORKSPACE_ID
- SECURITY_PRIVILEGE_ESCALATION
- SECURITY_TENANT_ADMIN_GLOBAL_AUTHORITY_SEPARATION
- SECURITY_REVOCATION_BEFORE_REQUEST
- SECURITY_REVOCATION_DURING_REQUEST
- SECURITY_STALE_AUTHORIZATION_STATE

### Provenance

- PROVENANCE_CALLER_SUPPLIED_AUTHORITATIVE_VERSION
- PROVENANCE_FORGED_SOURCE_SHA
- PROVENANCE_REPORT_HASH_MISMATCH
- PROVENANCE_STALE_EVIDENCE
- PROVENANCE_WRONG_TENANT_WORKSPACE_EVIDENCE
- PROVENANCE_WRONG_CANDIDATE_EVIDENCE
- PROVENANCE_DUPLICATE_PROVENANCE_ID

### Concurrency

- CONCURRENCY_SAME_ROW_RACE
- CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE
- CONCURRENCY_LOST_UPDATE
- CONCURRENCY_DUPLICATE_SUBMIT
- CONCURRENCY_RETRY_AFTER_TIMEOUT
- CONCURRENCY_IDEMPOTENCY_COLLISION
- CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION
- CONCURRENCY_PARTIAL_WRITE_ROLLBACK
- CONCURRENCY_MULTI_PROCESS_SERVICE_INSTANCE

Concurrency PASS requires a controlled interleaving trace containing an
explicit synchronization or barrier marker. A sequential approximation is
reported as WAIT_FOR_EVIDENCE, not as concurrency proof. Shared aggregate
invariants require aggregate-level proof in addition to row-version evidence.

### State machine

- STATE_MACHINE_LEGAL_TRANSITION
- STATE_MACHINE_ILLEGAL_TRANSITION
- STATE_MACHINE_TERMINAL_MUTATION
- STATE_MACHINE_STALE_TRANSITION
- STATE_MACHINE_DUPLICATE_TRANSITION
- STATE_MACHINE_FAILED_VALIDATION_BEFORE_TRANSITION
- STATE_MACHINE_ROLLBACK_SEMANTICS

### Evidence integrity

- EVIDENCE_SELF_ASSERTED_PASS
- EVIDENCE_NONZERO_EXIT_LABELED_PASS
- EVIDENCE_MISMATCHED_CANDIDATE_HASH
- EVIDENCE_MISSING_VALIDATOR_IDENTITY
- EVIDENCE_UNSUPPORTED_EVIDENCE_TYPE
- EVIDENCE_STALE_WORKFLOW_RUN

Evidence PASS requires a supported evidence type, independent validator
identity, zero exit status, current workflow identity, exact repository/source
and candidate/tree binding, a valid digest, durable storage, and retrieval.
Caller-authored assertions, stale receipts, nonzero PASS labels, and duplicate
evidence IDs fail closed.

## Governance composition

PRAI and Covenant remain mandatory. PRAI_PASS is not COVENANT_PASS, and
neither result is authority. The AQ-8 state-bound Covenant adapter requires
Steward system-intent judgment, Governor protected-obligation judgment,
current candidate/tree identity, durable retrievable assurance references, and
the current AQ-8 pack decision. System contradictions outrank a PRAI PASS.
Protected-governance conflicts remain blocked and escalate through the
existing human/new-execution-context boundary. Reconciliation is accepted
only when it preserves the Prime Directive and project goals and both owning
judgments explicitly accept it.

Steward owns scope, project intent, critical-flow alignment, and system
coherence. Governor owns protected obligations, legal/compliance/privacy
governance, and human-review requirements. Covenant synthesizes these
state-bound inputs without voting or authority expansion. Arbiter alone owns
the transition decision.

## Scenario and regression coverage

The AQ-8 runtime suite executes COV-01 through COV-18, including constitutional
conflict, owner blocks, owner revision, unsafe and narrow privacy/audit
reconciliation, scope/compliance conflict, convenience/authorization,
deadlines and missing evidence, aggregate concurrency, privilege mutation
before durable audit, PRAI/system contradiction, missing durable evidence,
security/accessibility, telemetry/privacy purpose, unresolved cost/reliability,
unknown legal applicability, genuine Governor non-applicability, and unknown
Prime Directive alignment.

The suite also runs the AQ-7 regression anchors:

- concurrent last-admin aggregate invariant;
- privilege mutation before audit durability;
- missing durable assurance evidence.

Seeded controlled fixtures are reported separately from organic observations.
The implementation does not claim a generalized effectiveness percentage unless
a clear denominator is available. AQ-8 introduces no network, provider, or
production side effect and remains a source-candidate phase until independent
review and separately authorized later gates.