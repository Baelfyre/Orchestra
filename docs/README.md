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
- [Tuner Protocol](governance/TUNER_PROTOCOL.md): cross-specialist coordination contract.

Specialist prose and progressive-disclosure knowledge remain under `../skills/*/`.

## Governance and authority

Start with the current [Governance Overview](governance/README.md).

- `../machine/governance/policy.v1.json`: machine governance policy and exact structured authority.
- [Governance Layer](governance/GOVERNANCE_LAYER.md): detailed human operating model, roles, modes, and risk scaling.
- [Autonomous Merge Readiness Protocol](governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md): exact-head merge-readiness rules.
- [Compliance Registry Integration](governance/COMPLIANCE_REGISTRY_INTEGRATION.md): registry boundary and evidence flow.
- [Authority and Capability Runtime Architecture](project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md): trusted runtime authority and capability design record.

Structured machine governance, runtime state, receipts, and evidence use JSON. Markdown remains the explanation, rationale, and instruction layer.

## Validation, evidence, and continuity

- [Validation Guide](setup/VALIDATION.md): local and CI validation entry points.
- `../machine/schemas/`: machine record schemas.
- `../machine/release-evidence/`: structured release and confidence evidence.
- `../PROJECT_STATE.md`: human project-state chronology.
- `../SESSION_HANDOFF.md`: repository-local human continuity record.

Cross-repository continuity may be supplied by a user-selected external continuity or memory backend. That backend is outside Orchestra's public source and does not supersede live Git state, validated source evidence, or Orchestra authority boundaries.

## Hosts, adapters, and integrations

- [Installation](setup/INSTALLATION.md): supported installation paths.
- [Compatibility](setup/COMPATIBILITY.md): host compatibility and maturity.
- [Host Updates](setup/HOST_UPDATES.md): governed read-only host update planning.
- [Adapter SDK and PRAP v1](setup/ADAPTER_SDK_PRAP.md): stable adapter SDK and deterministic compatibility certification.
- [Developer Portal](developer/README.md): extension and integration discovery surface.
- [MCP stdio Transport](developer/MCP_STDIO_TRANSPORT.md): first bounded MCP tools transport.
- `../machine/hosts/update-contract.v1.json`: host update/maturity contract.
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

The current public release is `v1.6.0`. Later canonical commits on `main` remain post-release work until a separately governed release is published.

## Developer extension path

If your goal is to build an adapter, certify PRAP compatibility, understand host maturity, or inspect extension contracts, go directly to the [Developer Portal](developer/README.md).

If your goal is to understand Orchestra as a whole, use this map and [`../README.json`](../README.json) together.
