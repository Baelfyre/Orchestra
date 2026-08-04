# Promotion Record: Machine-Readable Unit Record Extension (OrchestraUnitRecord)

```text
Record ID: PROM-SPEC-KITTY-001
External source: https://github.com/Priivacy-ai/spec-kitty
External source commit: 8466727ebbbc01fcaf43575657c9b1b9553784d9 (v3.2.6)
External source paths reviewed: src/kernel/, spec-kitty-wps/
Concept name: Machine-Readable Work Package Extension (OrchestraUnitRecord)
External observation: Spec Kitty defines missions as explicit work package trees (`kitty-specs/<mission>/work-packages/`) with discrete lifecycle states (`planned`, `in_progress`, `for_review`, `approved`, `done`), dependency references, and explicit task boundaries.
Verified Orchestra gap: Orchestra defines delegated phase execution in `DELEGATED_EXECUTION_POLICY.md` (`ApprovedUnitPlan` and `ExecutionEvidencePacket`), and typed coordination contracts in `orchestra_runtime/coordination.py`, but lacks explicit per-unit machine-readable status file extensions.
Why the current Orchestra contract is insufficient: `ApprovedUnitPlan` is specified in a single document, while runtime coordination lives in memory; an explicit schema extension improves multi-turn unit tracking across subagent sessions.
Proposed Orchestra-native adaptation: Define `OrchestraUnitRecord` as an immutable JSON schema extension embedded inside `ApprovedUnitPlan`. Each unit carries explicit definition fields (`unit_id`, `unit_revision`, `scope_ref`, `responsible_specialist`, `allowed_paths`, `dependency_unit_ids`, `expected_outputs`, `validation_requirements`) without creating a second source of truth. Standalone competing unit-state files are strictly REJECTED. Non-file unit classes are explicitly supported.
Canonical Orchestra owner: The Steward (policy schema)
Secondary consumers: Conductor (execution routing), Clockwork, Overseer, Arbiter
Canonical specification document: docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md
Proposed future target placement: docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md & docs/governance/DELEGATED_EXECUTION_POLICY.md (Section 4 amendment plan)
Affected specialists: Conductor, Arbiter, Ponytail, Clockwork, Overseer
Authority implications: None. Describes immutable plan boundaries; execution authority binds strictly through DelegatedExecutionEnvelope; scope_ref binds canonical scope.
Capability implications: Enables fine-grained unit state query and deterministic routing by Conductor based on canonical predecessor acceptance.
Governance implications: Ensures unit plan boundaries and path restrictions are parseable by machine adapters without prose scraping.
Delegation implications: Embedded inside `ApprovedUnitPlan` for delegated execution envelopes.
Coordination implications: Allows Conductor and The Tuner to verify predecessor dependency acceptance (`dependency_unit_ids`) before starting dependent units.
Lifecycle implications: Non-breaking; extends `ApprovedUnitPlan` with an embedded JSON code block (`json:orchestra-unit-record`).
Validation implications: Overseer checks that unit record schema fields (`unit_id`, `scope_ref`, `validation_requirements`) are valid during plan review. Invalid schemas return reason_code: INVALID_UNIT_PLAN.
Audit and evidence implications: Unit boundaries and execution envelope references are recorded in the plan schema.
Privacy and retention implications: REPOSITORY_TRACKED_WHEN_SANITIZED / MIXED_RETENTION_MODEL; sanitized paths; secret redaction enforced.
Compatibility implications: COMPATIBILITY_INTENT_DOCUMENTED / DESIGN_COMPATIBILITY_ASSESSED.
Migration requirements: Update `ApprovedUnitPlan` template in future policy integration phase.
Rejected copied elements: Standalone `.orchestra/units/` files and task lane state machines copied from Spec Kitty are REJECTED to preserve single source of truth in `ApprovedUnitPlan` and `coordination.py`.
License and attribution requirements: Conceptual adaptation; no code copied.
Risks: Minimal.
Non-goals: Creating standalone unit state files. Absorbing mutable runtime state into the plan.
Phase 1E.2 design result: Extension specification corrected at docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md (15 fields: 11 universally required, 1 conditionally required, 3 optional; scope_ref restored; non-file unit classes supported; path validation contract tightened; REPOSITORY_TRACKED_WHEN_SANITIZED retention).
Recommended next phase: Candidate Phase 1F (Cross-Document Synchronization & Final Upgrade Roadmap Update)
Promotion recommendation: PROCEED_TO_PHASE_1F (Specification Corrected & Verified)
Confidence: High (95%)
Open questions: None for Phase 1E.2.
```
