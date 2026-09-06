# Orchestra Documentation Map

This is the human navigation layer for the Orchestra framework.

For exact machine-readable state, identity, routing, governance, maturity, provenance, or release evidence, start with [`../README.json`](../README.json) and follow its references into `../machine/`. Human documentation explains those contracts; it does not override them.

## Architecture

Start with the current [Architecture Overview](architecture/README.md).

Primary machine and runtime surfaces:

- `../machine/governance/policy.v1.json` for governance policy.
- `../machine/specialists/registry.v1.json` for specialist identity.
- `../machine/routing/routes.v1.json` for deterministic routing.
- `../orchestra_runtime/` for runtime implementation.
- [Authority and Capability Runtime Architecture](project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md) for the detailed design history and implemented trust-boundary model.

Older phase documents may retain the status language of the phase in which they were written. Treat those status headers as historical evidence unless a current machine contract or this documentation map identifies the document as a live state source.

## Adaptive intelligence

- [Adaptive Memory A0/A1](architecture/ADAPTIVE_MEMORY_A0_A1.md): research boundary and machine-local adaptive-memory foundation.
- [Adaptive Specialist Context A2](architecture/ADAPTIVE_CONTEXT_A2.md): opt-in read-only specialist context after deterministic runtime gates.
- [Adaptive Behavioral Pattern Learning A3](architecture/ADAPTIVE_SHADOW_LEARNING_A3.md): A3.0 shadow-learning contract and non-authorizing signal/candidate/comparison model.
- [Portable Adaptive Memory](architecture/PORTABLE_ADAPTIVE_MEMORY.md): optional storage-agnostic export contract for user-selected memory backends.
- [Adaptive Agentic Workflow AWF](architecture/ADAPTIVE_AGENTIC_WORKFLOW_AWF.md): execution-effective authority-aware topology selection inside existing user/project authority, with topology changes separated from authority expansion.
- [Adaptive Agentic Workflow Intake N1-N5](architecture/ADAPTIVE_AGENTIC_WORKFLOW_INTAKE_N1.md): deterministic ordinary-prompt TaskProfile derivation, explainable selection traces, positive/negative routing calibration, and semantic robustness.
- [Adaptive Agentic Workflow N6 Advanced Adaptation Admission](architecture/ADAPTIVE_AGENTIC_WORKFLOW_N6.md): deterministic evidence gate for A5, learned routing, and OEE concurrency promotion with current no-promotion disposition.
- `../machine/adaptive/a1-memory-contract.v1.json`: A1 machine contract.
- `../machine/adaptive/a2-context-contract.v1.json`: A2 machine contract.
- `../machine/adaptive/a3-shadow-learning-contract.v1.json`: A3.0 machine contract.
- `../machine/adaptive/memory-backends.v1.json`: generic portable-memory backend classes and privacy boundaries.

A1 and A2 are canonical. The pre-A3 precedence/materialization hardening is canonical at `8402a5acbafe923c73904dcdb90f7faca90ced9c`. A3 shadow state is defined as separate from the A1 materialized profile and A2 specialist context; contract definition does not activate an A3 learner or grant execution authority.

Portable memory is optional. Orchestra does not require or identify a specific external repository, service, database, or user-selected backend. Backend identity, configuration, and credentials remain outside Orchestra's public source and portable learned-pattern payloads.

## Specialists, routing, and coordination

- [Skill Index](../SKILL_INDEX.md): lightweight human specialist-routing index.
- [Routing Map](../ROUTING_MAP.md): human routing and sequencing reference.
- `../machine/specialists/registry.v1.json`: compiled machine specialist registry.
- `../machine/routing/routes.v1.json`: canonical machine routing contract.
- [Tuner Protocol](governance/TUNER_PROTOCOL.md): cross-specialist coordination contract, including declared governance dependencies and minimal re-entry.
- [Cloak UI Reference Corpus Upgrade Plan](project/CLOAK_UI_REFERENCE_CORPUS_PLAN.md): canonical CUIR corpus, provenance, licensing, icon-reuse, evaluation, and phase-sequencing plan.
- [UI Execution Fidelity Plan](project/UI_EXECUTION_FIDELITY_PLAN.md): approved post-CUIR plan for fidelity-aware routing, Ponytail execution profiles, Cloak/Clockwork handoffs, rendered validation, and controlled comparative evaluation.

Specialist prose and progressive-disclosure knowledge remain under `../skills/*/`.

- [Chronicler Migration Risk Contract Guide](../skills/chronicler/MIGRATION_RISK_CONTRACT_GUIDE.md): evidence-bound production compatibility, migration patterns, rollback, and human-gate guidance.
- [Cipher Tenant-Security Governance Guide](../skills/cipher/TENANT_SECURITY_GOVERNANCE_GUIDE.md): evidence-bound tenant trust, authorization chains, default-deny boundaries, background execution, and specialist handoffs.
- [Conductor Architecture Governance Intake Guide](../skills/conductor/ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md): evidence-bound architecture classification, adaptive capacity routing, and minimum specialist route composition.
- [Arbiter Continuity and Evidence Freshness Evaluation Guide](../skills/arbiter/CONTINUITY_EVALUATION_GUIDE.md): evidence freshness taxonomy, six-tier transition precedence, exact commit and tree lineage binding, and non-authorizing constraints.
- [Ponytail Upstream-Contract Enforcement Guide](../skills/ponytail/UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md): deterministic upstream-contract consumption, minimal safe diff discipline, zero-invented-facts boundaries, and specialist handoffs.
- [Overseer Architecture Validation Contract Guide](../skills/overseer/ARCHITECTURE_VALIDATION_CONTRACT_GUIDE.md): contract-derived validation obligations, exact-bound proof states, and evidence limitations.
- [Scribe Specialist Upgrade SSU](project/SCRIBE_SPECIALIST_UPGRADE_SSU.md): adaptive domain narrative, traceability, research/capstone documentation, and documentation/system reconciliation guidance.
- [Scribe Post-SSU Governance Documentation Integration Guide](../skills/scribe/GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md): deterministic post-SSU governance documentation discipline, specialist contract matrices, bidirectional traceability, and evidence-bound claim verification.

## Governance and authority

Start with the current [Governance Overview](governance/README.md).

Constitutional and Development Lifecycle V2 surfaces:

- [Orchestra Prime Directive](governance/ORCHESTRA_PRIME_DIRECTIVE.md): stable constitutional authority/evidence boundary.
- [Feature Admission Policy](governance/FEATURE_ADMISSION_POLICY.md): separates proposal admission and permanent promotion from implementation authority.
- [Candidate Maturity and Feature Freeze](governance/CANDIDATE_MATURITY_FEATURE_FREEZE.md): exact development-candidate identity and maturity record.
- [Governed Autonomy Candidate Lifecycle Integration](governance/GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION.md): thin reuse of the existing autonomy evaluator for candidate transitions.
- [Qualification Gates, Evaluation, and Independent Audit](governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md): risk-proportional qualification and controlled-evaluation integrity.
- [Pre-state, Forward Recovery, and Branch Retirement](governance/PRESTATE_RECOVERY_BRANCH_RETIREMENT.md): forward-only recovery and non-authorizing retirement classification.
- [Prime Directive / Lifecycle V2 Realignment](governance/PRIME_DIRECTIVE_LIFECYCLE_V2_REALIGNMENT.md): current-main reconciliation and Campaign 0-5 provenance.
- [OR-GOV-9 Specialist Sufficiency Audit](governance/OR_GOV_9_SPECIALIST_SUFFICIENCY_AUDIT.md): conditional specialist governance sufficiency audit across The Governor, Weaver, Cloak, and Dagger.
- [OR-GOV-10 Integration Closeout](governance/OR_GOV_10_INTEGRATION_CLOSEOUT.md): final integration, parity, full regression, and program closeout across the complete OR-GOV architecture and governance program.

Existing governance/runtime surfaces remain subordinate and active:

- `../machine/governance/policy.v1.json`: machine governance policy and exact structured authority.
- [Governance Layer](governance/GOVERNANCE_LAYER.md): detailed human operating model, roles, modes, and risk scaling.
- [Governed Autonomy Modes](governance/GOVERNED_AUTONOMY_MODES.md): who may advance already-satisfied governance transitions.
- [Governed Autonomous Execution Protocol](governance/GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md): bounded autonomous development execution.
- [Autonomous Merge Readiness Protocol](governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md): exact-head merge-readiness rules.
- [Compliance Registry Integration](governance/COMPLIANCE_REGISTRY_INTEGRATION.md): registry boundary and evidence flow.
- [Authority and Capability Runtime Architecture](project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md): trusted runtime authority and capability design record.

Development Lifecycle V2 does not replace the runtime lifecycle controller, governance kernel, Arbiter, authority envelope, autonomy evaluator, or merge-readiness engine. Admission, implementation, validation, qualification, promotion, merge readiness, merge authority, and release/activation remain distinct.

Structured machine governance, runtime state, receipts, and evidence use JSON. Markdown remains the explanation, rationale, and instruction layer.

## Validation, evidence, and continuity

- [Validation Guide](setup/VALIDATION.md): local and CI validation entry points.
- `../machine/schemas/`: machine record schemas, including Feature Admission, Candidate Maturity, Qualification Gate, and Repository Recovery/Retirement contracts.
- `../machine/release-evidence/`: structured release and confidence evidence.
- [UIX-9C V3 post-study result](validation/uix9b-live-evidence-v2/v3-poststudy-result.v2.json): completed controlled UI study with terminal `NO_BENEFIT_ESTABLISHED`, zero primary improvements, and zero primary regressions.
- `../PROJECT_STATE.md`: human project-state chronology.
- `../SESSION_HANDOFF.md`: repository-local human continuity record.

Negative and inconclusive experimental results remain evidence. A no-benefit result must not be selectively discarded, retried until positive, or converted into a harm claim.

Cross-repository continuity may be supplied by a user-selected external continuity or memory backend. That backend is outside Orchestra's public source and does not supersede live Git state, validated source evidence, or Orchestra authority boundaries.

## Hosts, adapters, and integrations

- [Installation](setup/INSTALLATION.md): supported installation paths.
- [Compatibility](setup/COMPATIBILITY.md): host compatibility and maturity.
- [Host Updates](setup/HOST_UPDATES.md): governed read-only host update planning.
- [UAI Host Capability Contract](setup/HOST_CAPABILITY_CONTRACT.md): versioned host capability evidence and transport compatibility without authority expansion.
- [UAI Provider/Model Capability Contract](setup/PROVIDER_MODEL_CAPABILITY_CONTRACT.md): provider/model-neutral technical capability vocabulary and evidence boundaries without provider selection.
- [UAI Portable Projection Compiler](setup/PORTABLE_PROJECTION_COMPILER.md): canonical-source-backed host projection parity without installed-integration refresh or authority expansion.
- [UAI Transport and Fallback Integration](setup/TRANSPORT_FALLBACK_INTEGRATION.md): deterministic non-executing transport fallback planning without provider switching or routing authority.
- [Adapter SDK and PRAP v1](setup/ADAPTER_SDK_PRAP.md): stable adapter SDK and deterministic compatibility certification.
- [Developer Portal](developer/README.md): extension and integration discovery surface.
- [MCP stdio Transport](developer/MCP_STDIO_TRANSPORT.md): first bounded MCP tools transport.
- [GitHub Copilot Adapter](../adapters/github-copilot/README.md): decoupled integration architecture for GitHub Copilot.
- [GitHub Copilot Probe Guide](../adapters/github-copilot/probe-guide.md): live capability probe guide distinguishing canonical command invocation from native custom agents.
- `../machine/hosts/update-contract.v1.json`: host update/maturity contract.
- `../machine/hosts/capability-contract.v1.json`: UAI host capability and transport compatibility contract.
- `../machine/schemas/host-capability-contract.v1.schema.json`: UAI host capability contract schema.
- `../machine/providers/provider-model-capability-contract.v1.json`: UAI provider/model capability contract.
- `../machine/schemas/provider-model-capability-contract.v1.schema.json`: UAI provider/model capability contract schema.
- `../machine/projections/portable-projection-contract.v1.json`: canonical source and derived projection contract.
- `../machine/projections/portable-projection-index.v1.json`: generated machine-checkable projection parity index.
- `../machine/schemas/portable-projection-contract.v1.schema.json`: portable projection contract schema.
- `../machine/schemas/portable-projection-index.v1.schema.json`: generated parity index schema.
- `../machine/hosts/integration-strategy-policy.v1.json`: UAI transport selection and non-executing fallback policy.
- `../machine/protocol/prap-certification-contract.v1.json`: PRAP certification contract.
- `../machine/developer-portal/catalog.v1.json`: machine Developer Portal catalog.

MCP, adapters, PRAP certification, host maturity, and developer discovery are transport/integration surfaces. None is an authority source.

## Knowledge and provenance

- [Third-Party Provenance](THIRD_PARTY_PROVENANCE.md): human provenance guide.
- `../machine/provenance/third-party.v1.json`: machine third-party provenance.
- `../machine/knowledge/`: machine-readable specialist knowledge references.
- [Hybrid Context Formats](HYBRID_CONTEXT_FORMATS.md): Markdown/JSON/JSONL/TOON representation policy.

Current policy: JSON remains canonical for structured machine state. TOON is derived, validated, non-authoritative, and should be used only where bounded model-context compilation provides a measured benefit.

## Presentation and Murmurs

- [Murmurs Communication Budget](project/MURMURS_COMMUNICATION_BUDGET.md): human behavior and safety rationale.
- `../machine/presentation/murmurs-policy.v1.json`: machine presentation policy.
- `../machine/presentation/murmurs-vocabulary.v1.json`: deterministic vocabulary contract.

Murmurs changes presentation only. It does not alter authority, governance, validation truth, or machine state. Live-host token savings are not claimed without trustworthy comparable counters.

## Releases and history

- [Changelog](../CHANGELOG.md): human release/change history.
- `releases/`: release notes and release-candidate narratives.
- `validation/`: validation and publication evidence narratives.
- `../machine/release-evidence/`: structured release evidence.
- [Decision Log](../DECISION_LOG.md): architectural and governance decisions.

The current public release is immutable `v1.9.0`, tagged at signed canonical commit `7129a690b041bddbf8b58f41db0c4a680317fda1` with GitHub Release `RE_kwDOS_4UtM4W2pDC`. Its exact-head qualification, canonical merge, tag, and release identity were independently verified.

## Developer extension path

If your goal is to build an adapter, certify PRAP compatibility, understand host maturity, or inspect extension contracts, go directly to the [Developer Portal](developer/README.md).

If your goal is to understand Orchestra as a whole, use this map and [`../README.json`](../README.json) together.
