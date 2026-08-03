# Promotion Record: Cross-Run Event Correlation Protocol (OrchestraCorrelationID)

```text
Record ID: PROM-SPEC-KITTY-003
External source: https://github.com/Priivacy-ai/spec-kitty
External source commit: 8466727ebbbc01fcaf43575657c9b1b9553784d9 (v3.2.6)
External source paths reviewed: src/kernel/, spec-kitty-events
Concept name: Cross-Run Event Correlation Protocol (OrchestraCorrelationID)
External observation: Spec Kitty emits a structured JSONL event log using monotonically sortable event IDs to correlate operations across multiple agent sessions and work package executions.
Verified Orchestra gap: Orchestra's `EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md` and `scripts/evidence_identity.py` specify working tree fingerprints and collaboration session identity, but lack a standard time-ordered correlation identifier header linking root runs and continuation sessions across disconnected executions.
Why the current Orchestra contract is insufficient: Without a universal correlation identifier header, tracing a single high-level governance task across multi-stage handoffs requires manual log searching.
Proposed Orchestra-native adaptation: Rescope `OrchestraCorrelationID` to merge as an optional propagated correlation header field on `RuntimeAuditEvent`, `ExecutionEvidencePacket`, and `OrchestraRuntimeEnvelope`.
Canonical Orchestra owner: Chronicler (persistence)
Secondary consumers: Overseer (evidence), Conductor (routing)
Canonical specification document: docs/governance/CORRELATION_ID_PROTOCOL.md
Proposed future target placement: docs/governance/CORRELATION_ID_PROTOCOL.md & orchestra_runtime/models.py (proposed target placement for later implementation; no code added in Phase 1C/1C.1)
Affected specialists: Conductor, Arbiter, all specialists
Authority implications: None. Traceability identifier only.
Capability implications: Enables end-to-end tracing of multi-turn execution pipelines.
Governance implications: Enhances audit freshness verification and evidence linkage.
Delegation implications: Conductor propagates correlation header to all bounded delegated child runs.
Coordination implications: Allows The Tuner to verify complete execution histories across domain specialists.
Lifecycle implications: Continuous tracking across phase transitions.
Validation implications: Verification that correlation header is preserved in downstream evidence packets.
Audit and evidence implications: Direct correlation between human authorization, subagent runs, and final evidence packets.
Privacy and retention implications: Known metadata-disclosure risk (timestamp high bits disclosed). Managed via ACCEPTABLE_WITH_CONTROLS.
Compatibility implications: Backward-compatible addition of optional header/metadata field. DESIGN_COMPATIBILITY_ASSESSED.
Selected format: ADOPT_OPTIONAL_UUIDV7_WITH_IMPLEMENTATION_STRATEGY_UNRESOLVED (RFC 9562 UUIDv7 wire format; implementation generator strategy unresolved; Python stdlib uuid.uuid7() is in Python 3.14+; zero PyPI dependencies authorized).
Rejected elements: External `spec-kitty-events` PyPI dependency and ULID PyPI libraries are rejected to enforce zero external dependencies.
License and attribution requirements: Conceptual adaptation; no code copied.
Risks: None.
Non-goals: Adding an external PyPI dependency for event tracking. Replacing run_id, parent_run_id, or working_tree_fingerprint.
Phase 1C.1 evaluation result: Protocol updated with expanded identity inventory, timestamp privacy disclosure, and implementation strategy status at docs/governance/CORRELATION_ID_PROTOCOL.md.
Recommended next phase: Candidate Phase 1D (Phase Retrospective Protocol Specification)
Promotion recommendation: PROCEED_TO_PHASE_1D (Protocol Complete & Corrected)
Confidence: High (95%)
Open questions: None for Phase 1C.1.
```
