# Promotion Record: Machine-Readable Runtime Envelope (OrchestraRuntimeEnvelope)

```text
Record ID: PROM-SPEC-KITTY-002
External source: https://github.com/Priivacy-ai/spec-kitty
External source commit: 8466727ebbbc01fcaf43575657c9b1b9553784d9 (v3.2.6)
External source paths reviewed: src/runtime/, src/specify_cli/
Concept name: Machine-Readable Response Envelopes (OrchestraRuntimeEnvelope)
External observation: Spec Kitty uses deterministic JSON response envelopes across CLI and runtime outputs, containing `contract_version`, `command`, `timestamp`, `correlation_id`, `success`, `error_code`, and `data`.
Verified Orchestra gap: Orchestra relies primarily on markdown text blocks (`TransitionDecisionRecord`, packet outputs) for specialist communication and Arbiter decisions, which can cause parsing fragility across diverse LLM hosts.
Why the current Orchestra contract is insufficient: Text/markdown parsing is non-deterministic and sensitive to minor formatting variations between model providers (e.g. Codex vs Gemini vs Claude).
Proposed Orchestra-native adaptation: Define `OrchestraRuntimeEnvelope` as a standalone UTF-8 JSON schema for structured specialist handoffs, execution responses, and Arbiter transition decisions. Markdown presentation remains an optional non-authoritative rendered copy for human display.
Canonical Orchestra owner: Clockwork (architecture)
Secondary consumers: Conductor, Arbiter, Overseer
Canonical specification document: docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md
Proposed future target placement: docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md & orchestra_runtime/models.py (proposed target placement for later implementation; no runtime model code added in Phase 1B/1B.1)
Affected specialists: Conductor, Arbiter, Ponytail, all specialists
Authority implications: None. Structured formatting does not grant capability or permission. AUTO_CONTINUE indicates Arbiter transition disposition under current delegated execution envelope, not authority or merge permission.
Capability implications: Improves deterministic parsing across adapters (Codex, Claude, Antigravity).
Governance implications: Ensures Arbiter decisions (`AUTO_CONTINUE`, `STOP`, `ESCALATE_HUMAN`) can be parsed unambiguously by automated execution hosts.
Delegation implications: Facilitates machine parsing in delegated execution envelopes.
Coordination implications: Allows The Tuner to parse specialist outputs deterministically.
Lifecycle implications: Non-breaking; human-readable markdown summary remains included alongside envelope for human display.
Validation implications: Automated JSON schema validation for all machine-facing packets.
Audit and evidence implications: Includes timestamp, schema version, and correlation ID in runtime payloads.
Privacy and retention implications: Enforces payload filtering to prevent secret exposure in JSON streams.
Compatibility implications: DESIGN_COMPATIBILITY_ASSESSED. The design permits additive adoption alongside current human-readable output, but actual host/adapter compatibility remains unverified until implementation tests exist.
Migration requirements: Adapters consume standalone JSON payload; Markdown presentation copy is optional.
Rejected copied elements: Spec Kitty's specific CLI response field names copied directly are rejected; use Orchestra-native naming (`schema_version`, `disposition`, `correlation_id`, `specialist`, `operation`, `status`).
License and attribution requirements: Conceptual adaptation; no code copied.
Risks: Minimal.
Non-goals: Replacing human-readable markdown summaries. Creating a new runtime state engine.
Phase 1B.1 design result: Specification updated with variant-specific field definitions, standalone transport model, and precise Arbiter terminology at docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md.
Recommended next phase: Candidate Phase 1C (Correlation Protocol Format Evaluation)
Promotion recommendation: PROCEED_TO_PHASE_1B (Specification Complete & Corrected)
Confidence: High (95%)
Open questions: None for Phase 1B.1.
```
