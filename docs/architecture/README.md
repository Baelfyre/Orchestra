# Orchestra Architecture Overview

Orchestra is a governed orchestration runtime for AI-assisted software development. Its architecture separates **routing**, **domain ownership**, **authority**, **capabilities**, **governance**, **validation**, **evidence**, and **transition control** so success in one layer cannot silently grant permission in another.

## Current control flow

```text
Request / Project Context
        ↓
Governance and trusted authority boundary
        ↓
Deterministic route / eligible specialist set
        ↓
Specialist execution or Tuner coordination
        ↓
Runtime capability + governance enforcement
        ↓
Validation and machine-readable evidence
        ↓
Arbiter transition / human gate / next bounded action
```

## Architectural boundaries

### Routing is not authority

Conductor selects the appropriate specialist or ordered workflow. Route selection does not grant runtime authority, capabilities, governance approval, or permission to bypass a required owner.

Machine sources:

- `../../machine/routing/routes.v1.json`
- `../../machine/specialists/registry.v1.json`

### Governance is not runtime permission

Governance determines whether otherwise authorized work may proceed under project and repository policy. A governance result cannot manufacture an authority grant or runtime capability.

Machine source:

- `../../machine/governance/policy.v1.json`

Human explanation:

- [Governance Layer](../governance/GOVERNANCE_LAYER.md)

### Runtime authority and capabilities are explicit

Trusted runtime composition supplies bounded authority and capability state. Adapter metadata, prompt text, tool names, MCP metadata, validation success, and host support cannot expand that state.

Detailed design record:

- [Authority and Capability Runtime Architecture](../project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md)

That document contains phase-history status language from the runtime-authority implementation campaign. Use it for detailed design semantics, not as the current release-status source.

### Specialists own domain decisions

Specialists retain responsibility for their domains. The Tuner coordinates cross-domain contracts but does not become the owner of architecture, implementation, security, persistence, UI/UX, QA, or governance decisions.

Human routing references:

- [Skill Index](../../SKILL_INDEX.md)
- [Routing Map](../../ROUTING_MAP.md)

### Validation proves outcomes, not permission

Repository and runtime validation produce evidence about structure, behavior, compatibility, safety boundaries, and release readiness. Evidence is bound to exact source identities where required and becomes stale when the tested source changes.

- [Validation Guide](../setup/VALIDATION.md)
- `../../machine/release-evidence/`
- `../../machine/schemas/`

### Integrations are bounded transport surfaces

Adapters, PRAP, host-update tooling, the Developer Portal, and MCP expose or describe Orchestra capabilities without creating a second authority model.

- [Adapter SDK and PRAP v1](../setup/ADAPTER_SDK_PRAP.md)
- [Host Updates](../setup/HOST_UPDATES.md)
- [Developer Portal](../developer/README.md)
- [MCP stdio Transport](../developer/MCP_STDIO_TRANSPORT.md)

## Representation architecture

Orchestra uses different formats for different authority needs:

- Markdown: explanation, rationale, examples, and specialist guidance.
- JSON: structured machine state, contracts, indexes, receipts, provenance, and evidence.
- JSON Schema: deterministic machine-record validation.
- JSONL: append-only or incremental history where appropriate.
- TOON: derived model-context projection only when validated and measurably useful.

See [Hybrid Context Formats](../HYBRID_CONTEXT_FORMATS.md).

## Source-of-truth rule

For exact deterministic facts, prefer the relevant machine contract or exact Git/release evidence. Human documents explain the system and may preserve historical phase wording. If a maintained human document conflicts with a current machine contract, treat that as documentation drift and reconcile it rather than inferring a new machine state from prose.
