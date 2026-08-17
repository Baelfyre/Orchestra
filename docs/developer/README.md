# Orchestra Developer Portal

The Developer Portal is Orchestra's repository-native discovery surface for developers extending or integrating with the stabilized post-v1.5 contracts. It is documentation and indexing only. It is not a hosted service, marketplace, package registry, deployment plane, policy authority, or runtime permission source.

## Start here

| Goal | Canonical surfaces |
| --- | --- |
| Understand or build an adapter | `docs/setup/ADAPTER_SDK_PRAP.md`, `machine/protocol/prap-certification-contract.v1.json`, `machine/specialists/registry.v1.json` |
| Produce PRAP compatibility evidence | `scripts/certify_adapter.py`, `machine/protocol/prap-certification-contract.v1.json`, `machine/schemas/prap-certification-evidence.schema.json` |
| Check host maturity | `machine/hosts/update-contract.v1.json`, `docs/setup/HOST_UPDATES.md` |
| Understand specialist / Downstream Role boundaries | `machine/specialists/registry.v1.json`, `docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md` |
| Review governance | `machine/governance/policy.v1.json`, `docs/governance/GOVERNANCE_LAYER.md` |
| Validate changes | `docs/setup/VALIDATION.md` |

The machine-readable index for these entry points is `machine/developer-portal/catalog.v1.json`. Its schema is `machine/schemas/developer-portal-catalog.schema.json`.

## Adapter journey

1. Read `docs/setup/ADAPTER_SDK_PRAP.md` before introducing adapter metadata.
2. Use the stable SDK import surface `orchestra_runtime.protocol.sdk`; PRAP v1 remains the protocol authority.
3. Declare adapter identity and capabilities through the existing protocol model. Do not infer compatibility from a host name.
4. Use `python scripts/certify_adapter.py --adapter <id> --json` for deterministic read-only compatibility evidence.
5. Treat certification and host maturity as separate dimensions. Certification cannot promote a scaffold host.
6. Run repository validation before proposing a governed source change.

## Specialist extension journey

The machine specialist registry at `machine/specialists/registry.v1.json` owns specialist identity. The Developer Portal does not create new specialists, change ownership, or convert Downstream Roles into authority sources. Read the authority/capability/runtime architecture and governance policy before proposing a specialist extension.

Third-party discovery or publication is intentionally outside this phase. The Third-Party Specialist Marketplace remains a separately governed future phase and no listing, install, trust, reputation, package publication, or marketplace mutation behavior is implemented here.

## Governance and authority boundary

Portal links point to authoritative machine contracts where authority exists; the catalog does not duplicate or supersede those contracts. Portal discovery, documentation, validation success, certification success, packaging metadata, and GitHub mergeability do not grant runtime authority or capabilities.

The Developer Portal cannot activate policy, deploy or mutate production, refresh installed integrations, move releases or tags, promote host maturity, publish marketplace content, perform destructive cleanup, rewrite history, or implement MCP.

## Future transport boundary

MCP remains the final integration phase. If later implemented under separate authority, it must map to the stabilized Adapter SDK/PRAP boundary and existing governance contracts. The Developer Portal does not define an MCP transport, server, tool registry, or permission model.

## Public release boundary

The current public release remains `v1.5.0` at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`. This portal phase does not move or republish that release.
