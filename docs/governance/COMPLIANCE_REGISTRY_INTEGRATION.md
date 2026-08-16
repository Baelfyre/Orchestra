# Compliance Registry Integration

## Canonical registry

Orchestra's reusable compliance-intelligence source is `Baelfyre/Orchestra-Compliance-Registry`. Normal IDE governance uses a verified local snapshot managed by `scripts/compliance_registry.py`.

The public registry is readable by anyone. Canonical mutation authority is a separate repository-control concern. A fork, pull request, source-monitor result, arbitrary `main` snapshot, or self-consistent local ZIP is not a trusted registry release.

A trusted network distribution must come from a non-draft, non-prerelease, immutable GitHub Release in the canonical registry repository. An air-gapped or pre-downloaded ZIP must be bound to a separately verified release-manifest SHA-256 supplied out of band. Internal hashes prove content integrity; the immutable canonical release or external manifest digest supplies provenance.

The current trusted distribution is `registry-v0.1.0`, published as an immutable, non-draft, non-prerelease release. Canonical Registry `main` remains editable source state and may remain `DRAFT`; that source-state classification is distinct from the trust state of an immutable published distribution.

## Machine-first integration after control-plane re-foundation

At `LEGACY_RETIRED`, the versioned Orchestra machine contracts are authoritative for routing and compliance gate semantics. Compliance review is no longer allowed to rely on free-form downstream reconstruction of Registry results.

The current machine protocol is implemented in `orchestra_runtime/compliance_protocol.py` and represented by these schemas:

- `machine/schemas/compliance-query-receipt.schema.json`
- `machine/schemas/compliance-consumption-receipt.schema.json`
- `machine/schemas/steward-traceability-receipt.schema.json`
- `machine/schemas/compliance-set-equality-gate.schema.json`

A Registry query produces a deterministic query receipt bound to Registry identity, query filters, exact source IDs, exact obligation IDs, counts, and digest. Governor consumption and Steward traceability must reference the same query identity and canonical Registry IDs. Arbiter evaluates the machine gate and fails closed on unknown IDs, missing IDs, duplicate IDs, unjustified extra IDs, invalid exclusions, stale or mismatched evidence, or unsupported decision vocabulary.

For an ordinary governed review, the required set relationship is:

```text
SET(query source IDs)
=
SET(Governor consumed source IDs)
=
SET(Steward traced source IDs)

SET(query obligation IDs)
=
SET(Governor consumed obligation IDs + validated exclusions)
=
SET(Steward traced obligation IDs + validated exclusions)
```

The exact query digest binds the downstream receipts to the query that actually ran. Agent prose may explain the result, but it cannot replace these receipts or create Registry evidence.

## Canonical command surface

`/compliance-registry` and `/compliance-review` are explicit public Orchestra commands and must exist in all three relevant surfaces: `commands/`, `plugin.json`, and `machine/routing/routes.v1.json`.

`/compliance-registry` enters through Conductor but delegates Registry cache lifecycle and query operations to the deterministic `scripts/compliance_registry.py` path. Conductor does not reinterpret Registry contents and Registry lifecycle success does not create governance or execution authority.

`/compliance-review` enters through Conductor and follows the governed sequence:

```text
Conductor -> The Governor -> The Steward -> Arbiter
```

The Governor owns applicability and compliance interpretation, The Steward owns requirements and traceability, and Arbiter owns exact-state/freshness/set-equality transition enforcement. Unknown command fallback must not be used as the normal path for either compliance command.

## Local-first rule

Governor and Steward should use the verified active local registry for ordinary compliance review. Network access is reserved for synchronization, update checks, or authoritative-source verification when the registry cannot resolve a material currentness question.

Record these identities whenever a compliance decision relies on registry knowledge:

- canonical repository
- registry version
- release sequence
- release tag
- release manifest SHA-256
- selected jurisdictions and providers
- applicable source IDs and obligation IDs
- compliance query receipt identity and digest
- Governor consumption receipt identity
- Steward traceability receipt identity
- Arbiter compliance gate result

## Governor

Governor owns applicability, authoritative-source state, legal/regulatory/privacy/licensing/IP/provider-policy governance, and material interpretation escalation. Governor must not treat a registry record as legal advice or blanket compliance approval.

At Audit or Release boundaries, missing registry integrity, unresolved review-required source state, or materially stale applicable source evidence requires `REVISION_REQUIRED`, `WAIT_FOR_EVIDENCE`, or `human_review_required: true` as appropriate. Domain membership alone does not require escalation.

Governor consumption must use canonical Registry IDs from the current query receipt. Renamed, synthetic, unknown, missing, or duplicated IDs fail closed rather than being repaired in prose.

## Steward

Steward owns translating applicable registry obligations into project requirements and SDLC evidence. Compliance-derived requirements should remain traceable through:

`registry obligation -> project FR/NFR -> acceptance criterion -> implementation -> exact-state evidence`

An implementation reference is not compliance evidence by itself. Steward traceability must remain query-digest-bound and use the same canonical Registry ID set as the validated Governor consumption, subject only to explicit validated exclusions.

## Arbiter

Arbiter verifies that the compliance decision, registry identity, project state, and validation evidence are mutually current. A changed registry release does not automatically mean the project is non-compliant, but it invalidates prior compliance evidence when an applicable source or obligation changed materially or freshness can no longer be established.

Unknown or mismatched registry identity fails closed. Registry content never expands execution authority. Arbiter Kernel, not agent prose, owns the authoritative compliance set-equality and evidence-freshness transition result.

## Conductor

Conductor routes the applicable governance owners. It does not interpret compliance records and must not treat Governor approval as deployment, publication, or release authority. The explicit compliance command routes prevent the machine routing fallback from silently becoming the normal compliance integration path.

## Compatibility boundary

Registry v0.1.0 and Orchestra's current Registry client remain compatible through release schema version 1. Future Registry or Orchestra protocol revisions should negotiate explicit protocol/capability compatibility rather than infer compatibility from Orchestra SemVer alone. Broader Registry schema coverage and protocol-version negotiation are hardening work, not prerequisites for consuming the current immutable v0.1.0 distribution.
